//! CLI de referencia. Lee solo de la entrada estándar; no abre archivos.
//!
//! ```text
//! b60-exec-receipt verify --policy '<json>'  < recibo.json   # 0 aceptado, 1 rechazado, 2 uso
//! b60-exec-receipt batch                      < casos.jsonl   # una respuesta JSON por línea
//! ```
//!
//! Formato de `batch`, una petición por línea:
//! `{"op":"verify","receipt_hex":"<bytes UTF-8 en hex>","policy":{...}}` o
//! `{"op":"seal","unsealed":{...},"test_seed_hex":"<64 hex>"}` (semilla de prueba, no secreta).

use std::io::{self, BufRead, Read, Write};
use std::process::ExitCode;

use babylon60_exec_receipt::canonical::from_hex_strict;
use babylon60_exec_receipt::seal::{parse_unsealed, seal_with_test_seed};
use babylon60_exec_receipt::verify::{verdict_json, verify_execution_payload_utf8, Verdict};
use serde_json::{json, Value};

const USAGE: &str = "uso: b60-exec-receipt verify --policy '<json>' < recibo.json | b60-exec-receipt batch < casos.jsonl";
const MAX_STDIN_BYTES: u64 = 16 * 1024 * 1024;

fn from_hex_vec(hex: &str) -> Option<Vec<u8>> {
    if !hex.len().is_multiple_of(2) {
        return None;
    }
    hex.as_bytes()
        .chunks(2)
        .map(|pair| {
            std::str::from_utf8(pair)
                .ok()
                .and_then(|p| u8::from_str_radix(p, 16).ok())
        })
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
    let Ok(policy) = serde_json::from_str::<Value>(policy_text) else {
        eprintln!("el ancla de confianza no es JSON válido");
        return ExitCode::from(2);
    };
    let mut input = Vec::new();
    if io::stdin()
        .take(MAX_STDIN_BYTES)
        .read_to_end(&mut input)
        .is_err()
    {
        eprintln!("no se pudo leer la entrada estándar");
        return ExitCode::from(2);
    }
    let verdict = verify_execution_payload_utf8(&input, &policy);
    println!("{}", verdict_json(&verdict));
    if verdict.is_accepted() {
        ExitCode::SUCCESS
    } else {
        ExitCode::from(1)
    }
}

fn batch_line(line: &str) -> Value {
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
            let policy = request.get("policy").cloned().unwrap_or(Value::Null);
            let verdict = verify_execution_payload_utf8(&bytes, &policy);
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

fn batch_cmd() -> ExitCode {
    let stdin = io::stdin();
    let stdout = io::stdout();
    let mut out = stdout.lock();
    for line in stdin.lock().lines() {
        let Ok(line) = line else {
            eprintln!("no se pudo leer la entrada estándar");
            return ExitCode::from(2);
        };
        if line.trim().is_empty() {
            continue;
        }
        if writeln!(out, "{}", batch_line(&line)).is_err() {
            return ExitCode::from(2);
        }
    }
    ExitCode::SUCCESS
}

fn main() -> ExitCode {
    let args: Vec<String> = std::env::args().skip(1).collect();
    match args.first().map(String::as_str) {
        Some("verify") => verify_cmd(&args[1..]),
        Some("batch") if args.len() == 1 => batch_cmd(),
        _ => {
            eprintln!("{USAGE}");
            ExitCode::from(2)
        }
    }
}
