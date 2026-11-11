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
