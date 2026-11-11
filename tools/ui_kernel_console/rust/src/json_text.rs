//! Comprobaciones sobre el texto JSON antes de interpretarlo, idénticas a las de
//! `src/crypto/jsonText.ts`. Fijan una única forma aceptable del recibo en texto, de modo que
//! este crate (`serde_json`) y el cliente TypeScript (`JSON.parse`) acepten exactamente los
//! mismos textos:
//!
//! - números: solo enteros en forma canónica (sin fracción, sin exponente, sin `-0`);
//! - anidamiento: como máximo 127 contenedores (límite de recursión de `serde_json`);
//! - sustitutos UTF-16 escapados: solo en pares válidos (`serde_json` rechaza los sueltos).
//!
//! En Rust las dos últimas reglas las impone ya el propio analizador; la primera se comprueba
//! aquí sobre el texto, porque `serde_json` sí acepta `1.0` o `1e3` como números.

/// Tamaño máximo del texto, en unidades UTF-16 (como `String.length` en JavaScript).
pub const MAX_JSON_TEXT_UTF16: usize = 4 * 1024 * 1024;
/// Profundidad máxima de anidamiento admitida.
pub const MAX_JSON_DEPTH: usize = 127;

/// Primer número del texto que no es un entero canónico, o `None`.
/// Precondición: `text` es JSON válido (ya analizado).
pub fn first_non_integer_number(text: &str) -> Option<String> {
    let b = text.as_bytes();
    let mut i = 0;
    let mut in_string = false;
    while i < b.len() {
        let c = b[i];
        if in_string {
            if c == b'\\' {
                i += 2;
                continue;
            }
            if c == b'"' {
                in_string = false;
            }
            i += 1;
            continue;
        }
        if c == b'"' {
            in_string = true;
            i += 1;
            continue;
        }
        if c == b'-' || c.is_ascii_digit() {
            let start = i;
            i += 1;
            while i < b.len() && matches!(b[i], b'0'..=b'9' | b'.' | b'e' | b'E' | b'+' | b'-') {
                i += 1;
            }
            let token = &text[start..i];
            if token.contains(['.', 'e', 'E']) || token == "-0" {
                return Some(token.to_string());
            }
            continue;
        }
        i += 1;
    }
    None
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn only_canonical_integers_pass() {
        assert_eq!(
            first_non_integer_number(r#"{"a":[0,1,23,-5,9007199254740991]}"#),
            None
        );
        assert_eq!(
            first_non_integer_number(r#"{"a":1.0}"#).as_deref(),
            Some("1.0")
        );
        assert_eq!(
            first_non_integer_number(r#"{"a":1e3}"#).as_deref(),
            Some("1e3")
        );
        assert_eq!(
            first_non_integer_number(r#"{"a":2E-1}"#).as_deref(),
            Some("2E-1")
        );
        assert_eq!(
            first_non_integer_number(r#"{"a":-0}"#).as_deref(),
            Some("-0")
        );
        assert_eq!(
            first_non_integer_number(r#"{"a":"1.0 \" -0","b":true}"#),
            None
        );
    }
}

/// Clave repetida dentro de un mismo objeto, o `None`. Precondición: `text` es JSON válido (ya
/// analizado). Las claves se comparan decodificadas, así que `"\u0061"` y `"a"` coinciden.
/// Claves repetidas en objetos distintos no cuentan.
pub fn first_repeated_key(text: &str) -> Option<String> {
    let b = text.as_bytes();
    // Pila de contenedores: `Some(claves vistas)` para un objeto, `None` para un array.
    let mut stack: Vec<Option<std::collections::HashSet<String>>> = Vec::new();
    let mut i = 0;
    while i < b.len() {
        match b[i] {
            b'{' => {
                stack.push(Some(std::collections::HashSet::new()));
                i += 1;
            }
            b'[' => {
                stack.push(None);
                i += 1;
            }
            b'}' | b']' => {
                stack.pop();
                i += 1;
            }
            b'"' => {
                let (decoded, end) = decode_string(b, i)?;
                i = end;
                if let Some(Some(keys)) = stack.last_mut() {
                    if next_significant(b, i) == Some(b':') && !keys.insert(decoded.clone()) {
                        return Some(decoded);
                    }
                }
            }
            _ => i += 1,
        }
    }
    None
}

/// Primer byte que no es espacio JSON desde `at`.
fn next_significant(b: &[u8], at: usize) -> Option<u8> {
    b[at..]
        .iter()
        .copied()
        .find(|c| !matches!(c, b' ' | b'\t' | b'\n' | b'\r'))
}

fn hex4(b: &[u8], at: usize) -> Option<u32> {
    let digits = std::str::from_utf8(b.get(at..at + 4)?).ok()?;
    u32::from_str_radix(digits, 16).ok()
}

/// Decodifica el literal de cadena que empieza en `start`. Devuelve el texto y la posición tras
/// la comilla de cierre. El texto ya está validado por `serde_json`, así que aquí no hay errores
/// de forma: un `None` solo indicaría una precondición rota.
fn decode_string(b: &[u8], start: usize) -> Option<(String, usize)> {
    let mut out: Vec<u8> = Vec::new();
    let mut i = start + 1;
    loop {
        let c = *b.get(i)?;
        match c {
            b'"' => return String::from_utf8(out).ok().map(|s| (s, i + 1)),
            b'\\' => {
                let e = *b.get(i + 1)?;
                let simple = match e {
                    b'"' | b'\\' | b'/' => Some(e),
                    b'b' => Some(8),
                    b'f' => Some(12),
                    b'n' => Some(b'\n'),
                    b'r' => Some(b'\r'),
                    b't' => Some(b'\t'),
                    _ => None,
                };
                if let Some(byte) = simple {
                    out.push(byte);
                    i += 2;
                } else if e == b'u' {
                    let hi = hex4(b, i + 2)?;
                    let (ch, next) = if (0xD800..0xDC00).contains(&hi) {
                        if b.get(i + 6) != Some(&b'\\') || b.get(i + 7) != Some(&b'u') {
                            return None;
                        }
                        let lo = hex4(b, i + 8)?;
                        if !(0xDC00..0xE000).contains(&lo) {
                            return None;
                        }
                        let cp = 0x10000 + ((hi - 0xD800) << 10) + (lo - 0xDC00);
                        (char::from_u32(cp)?, i + 12)
                    } else {
                        (char::from_u32(hi)?, i + 6)
                    };
                    let mut buf = [0u8; 4];
                    out.extend_from_slice(ch.encode_utf8(&mut buf).as_bytes());
                    i = next;
                } else {
                    return None;
                }
            }
            _ => {
                out.push(c);
                i += 1;
            }
        }
    }
}

#[cfg(test)]
mod repeated_key_tests {
    use super::first_repeated_key;

    #[test]
    fn a_repeated_key_in_one_object_is_found() {
        assert_eq!(first_repeated_key(r#"{"a":1,"a":2}"#).as_deref(), Some("a"));
        assert_eq!(
            first_repeated_key(r#"{"x":[{"k":1,"k":2}]}"#).as_deref(),
            Some("k")
        );
    }

    #[test]
    fn escaped_and_plain_spellings_of_one_key_count_as_repeated() {
        assert_eq!(
            first_repeated_key(r#"{"\u0061":1,"a":2}"#).as_deref(),
            Some("a")
        );
        assert_eq!(
            first_repeated_key(r#"{"\ud83d\ude00":1,"😀":2}"#).as_deref(),
            Some("😀")
        );
    }

    #[test]
    fn same_names_in_different_objects_or_as_values_are_fine() {
        assert_eq!(first_repeated_key(r#"[{"k":1},{"k":2}]"#), None);
        assert_eq!(first_repeated_key(r#"{"a":{"a":1}}"#), None);
        assert_eq!(first_repeated_key(r#"{"a":"a","b":"b"}"#), None);
        assert_eq!(first_repeated_key(r#"{"a":"x:\"a\":1"}"#), None);
    }
}
