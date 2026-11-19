//! Perfil CBOR determinista restringido del kernel (`src/acs_bridge.rs`, módulo `authenticated`):
//! arrays de longitud definida, enteros sin signo, cadenas de bytes y de texto, cabeceras en su
//! forma más corta. Sin mapas, coma flotante, negativos ni valores simples.
//!
//! Las funciones replican las de `acs_bridge` (privadas allí) y se contrastan con los vectores
//! dorados de `tests/acs_cbor_golden.txt` en `tests/kernel_vectors.rs`.

fn head(major: u8, n: u64) -> Vec<u8> {
    let mut out = Vec::new();
    match n {
        0..=23 => out.push((major << 5) | n as u8),
        24..=255 => out.extend_from_slice(&[(major << 5) | 24, n as u8]),
        256..=65535 => {
            out.push((major << 5) | 25);
            out.extend_from_slice(&(n as u16).to_be_bytes());
        }
        65536..=4294967295 => {
            out.push((major << 5) | 26);
            out.extend_from_slice(&(n as u32).to_be_bytes());
        }
        _ => {
            out.push((major << 5) | 27);
            out.extend_from_slice(&n.to_be_bytes());
        }
    }
    out
}

/// Entero sin signo.
pub fn uint(n: u64) -> Vec<u8> {
    head(0, n)
}

/// Cadena de bytes.
pub fn bytes(b: &[u8]) -> Vec<u8> {
    let mut v = head(2, b.len() as u64);
    v.extend_from_slice(b);
    v
}

/// Cadena de texto (UTF-8).
pub fn text(s: &str) -> Vec<u8> {
    let mut v = head(3, s.len() as u64);
    v.extend_from_slice(s.as_bytes());
    v
}

/// Array de longitud definida a partir de elementos ya codificados.
pub fn array(items: Vec<Vec<u8>>) -> Vec<u8> {
    let mut v = head(4, items.len() as u64);
    for item in items {
        v.extend(item);
    }
    v
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn heads_use_the_shortest_form() {
        assert_eq!(uint(0), [0x00]);
        assert_eq!(uint(23), [0x17]);
        assert_eq!(uint(24), [0x18, 24]);
        assert_eq!(uint(255), [0x18, 255]);
        assert_eq!(uint(256), [0x19, 1, 0]);
        assert_eq!(uint(65536), [0x1a, 0, 1, 0, 0]);
        assert_eq!(uint(4294967296), [0x1b, 0, 0, 0, 1, 0, 0, 0, 0]);
        assert_eq!(text("a"), [0x61, 0x61]);
        assert_eq!(bytes(&[]), [0x40]);
        assert_eq!(array(vec![]), [0x80]);
    }
}
