//! CLI de referencia. Lee solo de la entrada estándar; no abre archivos.
//!
//! ```text
//! b60-exec-receipt verify --policy '<json>'  < recibo.json   # 0 aceptado, 1 rechazado, 2 uso o E/S
//! b60-exec-receipt batch                      < casos.jsonl   # una respuesta JSON por línea
//! ```
//!
//! Formato de `batch`, una petición por línea:
//! `{"op":"verify","receipt_hex":"<bytes UTF-8 en hex minúsculas>","policy":{...}}` o
//! `{"op":"seal","unsealed":{...},"test_seed_hex":"<64 hex>"}` (semilla de prueba, no secreta).
//! `policy` puede ser un objeto JSON o un texto con el ancla. Un ancla que no se puede
//! interpretar produce un veredicto `TRUST_POLICY_INVALID`, igual que en la CLI y en wasm.
//! Una línea que no es UTF-8, que no es JSON, que repite una clave o que supera
//! `MAX_BATCH_LINE_BYTES` recibe una respuesta `{"error": ...}`; el lote sigue.

use std::io::{self, BufRead, Read, Write};
use std::process::ExitCode;

use babylon60_exec_receipt::canonical::from_hex_strict;
use babylon60_exec_receipt::json_text::first_repeated_key;
use babylon60_exec_receipt::seal::{parse_unsealed, seal_with_test_seed};
use babylon60_exec_receipt::verify::{
    rejection, verdict_json, verify_execution_payload_utf8, verify_with_anchor_text, Verdict,
};
use serde_json::{json, Value};

const USAGE: &str =
    "uso: b60-exec-receipt verify --policy '<json>' < recibo.json | b60-exec-receipt batch < casos.jsonl";
/// Cota de la entrada de `verify`. Por encima, el recibo se rechaza sin interpretarlo.
const MAX_STDIN_BYTES: u64 = 16 * 1024 * 1024;
/// Cota de una línea de `batch`, medida antes de decodificarla. Holgada para un recibo en hex.
const MAX_BATCH_LINE_BYTES: usize = 64 * 1024 * 1024;

fn hex_nibble(c: u8) -> Option<u8> {
    match c {
        b'0'..=b'9' => Some(c - b'0'),
        b'a'..=b'f' => Some(c - b'a' + 10),
        _ => None,
    }
}

/// Decodifica hex en minúsculas, par a par. Rechaza signos, mayúsculas y longitud impar,
/// igual que `from_hex_strict` del crate.
fn from_hex_vec(hex: &str) -> Option<Vec<u8>> {
    let digits = hex.as_bytes();
    if !digits.len().is_multiple_of(2) {
        return None;
    }
    digits
        .chunks_exact(2)
        .map(|pair| Some((hex_nibble(pair[0])? << 4) | hex_nibble(pair[1])?))
        .collect()
}

fn verify_cmd(args: &[String]) -> ExitCode {
    let [flag, policy_text] = args else {
        eprintln!("{USAGE}");
        return ExitCode::from(2);
    };
    if flag != "--policy" {
        eprintln!("{USAGE}");
        return ExitCode::from(2);
    }
    // Se leen MAX_STDIN_BYTES + 1 bytes para distinguir «exactamente en el límite» de «por encima».
    let mut input = Vec::new();
    if io::stdin()
        .take(MAX_STDIN_BYTES + 1)
        .read_to_end(&mut input)
        .is_err()
    {
        eprintln!("no se pudo leer la entrada estándar");
        return ExitCode::from(2);
    }
    let verdict = if input.len() as u64 > MAX_STDIN_BYTES {
        // No se conoce la longitud real sin leer todo: el diagnóstico dice solo lo que se sabe.
        rejection(
            "SCHEMA_INVALID",
            &format!("la entrada supera {MAX_STDIN_BYTES} bytes y no se interpreta"),
        )
    } else {
        verify_with_anchor_text(&input, policy_text)
    };
    let stdout = io::stdout();
    let mut out = stdout.lock();
    if writeln!(out, "{}", verdict_json(&verdict))
        .and_then(|()| out.flush())
        .is_err()
    {
        eprintln!("no se pudo escribir el veredicto en la salida estándar");
        return ExitCode::from(2);
    }
    if verdict.is_accepted() {
        ExitCode::SUCCESS
    } else {
        ExitCode::from(1)
    }
}

fn batch_line(line: &str) -> Value {
    if let Some(key) = first_repeated_key(line) {
        return json!({ "error": format!("clave duplicada: {key}") });
    }
    let Ok(request) = serde_json::from_str::<Value>(line) else {
        return json!({ "error": "línea que no es JSON" });
    };
    match request.get("op").and_then(Value::as_str) {
        Some("verify") => {
            let Some(bytes) = request
                .get("receipt_hex")
                .and_then(Value::as_str)
                .and_then(from_hex_vec)
            else {
                return json!({ "op": "verify", "error": "receipt_hex ausente o inválido" });
            };
            let verdict = match request.get("policy") {
                Some(Value::String(anchor)) => verify_with_anchor_text(&bytes, anchor),
                other => {
                    let policy = other.cloned().unwrap_or(Value::Null);
                    verify_execution_payload_utf8(&bytes, &policy)
                }
            };
            let mut out = verdict_json(&verdict);
            out["op"] = json!("verify");
            out["codes"] = json!(verdict.codes());
            if let Verdict::Accepted(_) = verdict {
                out["accepted"] = json!(true);
            }
            out
        }
        Some("seal") => {
            let Some(seed) = request
                .get("test_seed_hex")
                .and_then(Value::as_str)
                .and_then(from_hex_strict::<32>)
            else {
                return json!({ "op": "seal", "error": "test_seed_hex ausente o inválido" });
            };
            match parse_unsealed(request.get("unsealed").unwrap_or(&Value::Null)) {
                Ok(u) => json!({ "op": "seal", "receipt": seal_with_test_seed(&u, &seed) }),
                Err(failures) => json!({
                    "op": "seal",
                    "error": failures.iter().map(|f| json!({ "code": f.code, "detail": f.detail })).collect::<Vec<_>>(),
                }),
            }
        }
        _ => json!({ "error": "op desconocida" }),
    }
}

/// Resultado de leer una línea con cota.
enum Line {
    Eof,
    Text,
    TooLong,
}

/// Lee una línea sin superar `cap` bytes de contenido. Si la línea es más larga, la descarta
/// hasta su salto de línea y devuelve `TooLong`: la memoria usada no depende de la entrada.
fn read_line_capped<R: BufRead>(input: &mut R, buf: &mut Vec<u8>, cap: usize) -> io::Result<Line> {
    buf.clear();
    let mut too_long = false;
    let mut read_any = false;
    loop {
        let chunk = input.fill_buf()?;
        if chunk.is_empty() {
            return Ok(match (read_any, too_long) {
                (false, _) => Line::Eof,
                (true, true) => Line::TooLong,
                (true, false) => Line::Text,
            });
        }
        read_any = true;
        let newline = chunk.iter().position(|&b| b == b'\n');
        let content_len = newline.unwrap_or(chunk.len());
        let consumed = newline.map_or(chunk.len(), |i| i + 1);
        if !too_long {
            if buf.len() + content_len > cap {
                too_long = true;
                buf.clear();
            } else {
                buf.extend_from_slice(&chunk[..content_len]);
            }
        }
        input.consume(consumed);
        if newline.is_some() {
            return Ok(if too_long { Line::TooLong } else { Line::Text });
        }
    }
}

/// Procesa peticiones línea a línea. Un problema de una línea no detiene el lote: solo un error
/// de entrada o de salida lo hace, porque entonces ya no hay forma de responder.
fn run_batch<R: BufRead, W: Write>(input: &mut R, out: &mut W, cap: usize) -> io::Result<()> {
    let mut buf = Vec::new();
    loop {
        let reply = match read_line_capped(input, &mut buf, cap)? {
            Line::Eof => break,
            Line::TooLong => json!({ "error": "línea mayor que el máximo admitido" }),
            Line::Text => match std::str::from_utf8(&buf) {
                Err(_) => json!({ "error": "línea que no es UTF-8" }),
                Ok(text) if text.trim().is_empty() => continue,
                Ok(text) => batch_line(text),
            },
        };
        writeln!(out, "{reply}")?;
    }
    out.flush()
}

fn batch_cmd() -> ExitCode {
    let stdin = io::stdin();
    let stdout = io::stdout();
    match run_batch(&mut stdin.lock(), &mut stdout.lock(), MAX_BATCH_LINE_BYTES) {
        Ok(()) => ExitCode::SUCCESS,
        Err(_) => {
            eprintln!("no se pudo completar la entrada o la salida estándar");
            ExitCode::from(2)
        }
    }
}

fn main() -> ExitCode {
    // Los argumentos se leen como `OsString`: uno que no es UTF-8 es un uso incorrecto, no un pánico.
    let Some(args) = std::env::args_os()
        .skip(1)
        .map(|arg| arg.into_string().ok())
        .collect::<Option<Vec<String>>>()
    else {
        eprintln!("{USAGE}");
        return ExitCode::from(2);
    };
    match args.first().map(String::as_str) {
        Some("verify") => verify_cmd(&args[1..]),
        Some("batch") if args.len() == 1 => batch_cmd(),
        _ => {
            eprintln!("{USAGE}");
            ExitCode::from(2)
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn hex_is_lowercase_and_even_only() {
        assert_eq!(from_hex_vec("7b0a"), Some(vec![0x7b, 0x0a]));
        assert_eq!(from_hex_vec(""), Some(Vec::new()));
        for bad in ["7b+a", "7b0A", "7b-a", "7bzz", "7b0"] {
            assert_eq!(from_hex_vec(bad), None, "{bad}");
        }
    }

    #[test]
    fn capped_reader_keeps_short_lines_and_discards_long_ones() {
        let input = b"uno\ndos-demasiado-largo\ntres\n";
        let mut reader = &input[..];
        let mut buf = Vec::new();
        assert!(matches!(
            read_line_capped(&mut reader, &mut buf, 8).unwrap(),
            Line::Text
        ));
        assert_eq!(buf, b"uno");
        assert!(matches!(
            read_line_capped(&mut reader, &mut buf, 8).unwrap(),
            Line::TooLong
        ));
        assert!(matches!(
            read_line_capped(&mut reader, &mut buf, 8).unwrap(),
            Line::Text
        ));
        assert_eq!(buf, b"tres");
        assert!(matches!(
            read_line_capped(&mut reader, &mut buf, 8).unwrap(),
            Line::Eof
        ));
    }

    #[test]
    fn batch_keeps_answering_after_a_line_that_is_not_utf8() {
        let request = json!({ "op": "verify", "receipt_hex": "7b7d", "policy": {} }).to_string();
        let mut input = Vec::new();
        input.extend_from_slice(request.as_bytes());
        input.extend_from_slice(b"\n\xff\xfe\n");
        input.extend_from_slice(request.as_bytes());
        input.push(b'\n');
        let mut out = Vec::new();
        run_batch(&mut &input[..], &mut out, 1 << 20).unwrap();
        let lines: Vec<&str> = std::str::from_utf8(&out).unwrap().lines().collect();
        assert_eq!(lines.len(), 3, "{lines:?}");
        assert!(lines[0].contains("\"op\":\"verify\""), "{}", lines[0]);
        assert_eq!(lines[1], r#"{"error":"línea que no es UTF-8"}"#);
        assert!(lines[2].contains("\"op\":\"verify\""), "{}", lines[2]);
    }

    #[test]
    fn batch_answers_an_oversize_line_with_an_error_and_continues() {
        let mut out = Vec::new();
        run_batch(&mut &b"0123456789abcdef\n{}\n"[..], &mut out, 8).unwrap();
        let lines: Vec<&str> = std::str::from_utf8(&out).unwrap().lines().collect();
        assert_eq!(lines.len(), 2, "{lines:?}");
        assert_eq!(
            lines[0],
            r#"{"error":"línea mayor que el máximo admitido"}"#
        );
        assert_eq!(lines[1], r#"{"error":"op desconocida"}"#);
    }
}
