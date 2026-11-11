//! Criterio estricto para claves públicas y firmas Ed25519, idéntico al del verificador
//! TypeScript (`src/crypto/ed25519Point.ts`):
//!
//! - codificación canónica (y < p; con x = 0 el bit de signo es 0) y punto en la curva;
//! - el punto no es de orden pequeño ([8]P ≠ identidad);
//! - el escalar S de la firma es canónico (S < ℓ).
//!
//! `verify_strict` de ed25519-dalek ya rechaza R y A de orden pequeño y S no canónico; este
//! módulo añade la exigencia de codificación canónica de A y R para que Rust y TypeScript acepten
//! exactamente las mismas claves y firmas.

use curve25519_dalek::edwards::CompressedEdwardsY;
use curve25519_dalek::scalar::Scalar;

/// Clasificación de una codificación de 32 bytes como clave pública o componente R.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum PointVerdict {
    /// Canónica, en la curva y fuera del subgrupo de torsión.
    Ok,
    /// No canónica o fuera de la curva.
    NonCanonicalOrOffCurve,
    /// Punto de orden pequeño (divide a 8).
    SmallOrder,
}

/// Clasifica `bytes` según el criterio estricto.
pub fn classify_point(bytes: &[u8; 32]) -> PointVerdict {
    let Some(point) = CompressedEdwardsY(*bytes).decompress() else {
        return PointVerdict::NonCanonicalOrOffCurve;
    };
    // decompress reduce y módulo p e ignora un signo inválido para x = 0: recomprimir y comparar
    // rechaza toda codificación que no sea la canónica.
    if point.compress().to_bytes() != *bytes {
        return PointVerdict::NonCanonicalOrOffCurve;
    }
    if point.is_small_order() {
        PointVerdict::SmallOrder
    } else {
        PointVerdict::Ok
    }
}

/// `true` si la firma tiene R aceptable y S canónico. No verifica la firma.
pub fn is_strict_signature_encoding(signature: &[u8; 64]) -> bool {
    let mut r = [0u8; 32];
    let mut s = [0u8; 32];
    r.copy_from_slice(&signature[..32]);
    s.copy_from_slice(&signature[32..]);
    if classify_point(&r) != PointVerdict::Ok {
        return false;
    }
    bool::from(Scalar::from_canonical_bytes(s).is_some())
}

#[cfg(test)]
mod tests {
    use super::*;

    fn h(s: &str) -> [u8; 32] {
        let mut out = [0u8; 32];
        for (i, chunk) in s.as_bytes().chunks(2).enumerate() {
            out[i] = u8::from_str_radix(std::str::from_utf8(chunk).unwrap(), 16).unwrap();
        }
        out
    }

    const F: &str = "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff";
    const Z: &str = "000000000000000000000000000000000000000000000000000000000000";

    #[test]
    fn small_order_points_and_non_canonical_encodings_are_rejected() {
        let small = [
            format!("01{Z}00"),
            format!("ec{F}7f"),
            format!("00{Z}00"),
            format!("00{Z}80"),
            "26e8958fc2b227b045c3f489f2ef98f0d5dfac05d3c63339b13802886d53fc05".to_string(), // pragma: allowlist secret
            "26e8958fc2b227b045c3f489f2ef98f0d5dfac05d3c63339b13802886d53fc85".to_string(), // pragma: allowlist secret
            "c7176a703d4dd84fba3c0b760d10670f2a2053fa2c39ccc64ec7fd7792ac037a".to_string(), // pragma: allowlist secret
            "c7176a703d4dd84fba3c0b760d10670f2a2053fa2c39ccc64ec7fd7792ac03fa".to_string(), // pragma: allowlist secret
        ];
        for p in &small {
            assert_eq!(classify_point(&h(p)), PointVerdict::SmallOrder, "{p}");
        }
        let non_canonical = [
            format!("01{Z}80"),
            format!("ec{F}ff"),
            format!("ed{F}7f"),
            format!("ed{F}ff"),
            format!("ee{F}7f"),
            format!("ee{F}ff"),
        ];
        for p in &non_canonical {
            assert_eq!(
                classify_point(&h(p)),
                PointVerdict::NonCanonicalOrOffCurve,
                "{p}"
            );
        }
    }

    #[test]
    fn rfc8032_keys_and_the_base_point_are_accepted() {
        for p in [
            "d75a980182b10ab7d54bfed3c964073a0ee172f3daa62325af021a68f707511a", // pragma: allowlist secret
            "3d4017c3e843895a92b70aa74d1b7ebc9c982ccf2ec4968cc0cd55f12af4660c", // pragma: allowlist secret
            "5866666666666666666666666666666666666666666666666666666666666666", // pragma: allowlist secret
        ] {
            assert_eq!(classify_point(&h(p)), PointVerdict::Ok, "{p}");
        }
    }

    #[test]
    fn trivial_and_malleated_signatures_are_not_strict() {
        let mut trivial = [0u8; 64];
        trivial[0] = 1; // R = identidad, S = 0
        assert!(!is_strict_signature_encoding(&trivial));
        // S = ℓ (no canónico) con R válido.
        let mut sig = [0u8; 64];
        sig[..32].copy_from_slice(&h(
            "5866666666666666666666666666666666666666666666666666666666666666",
        )); // pragma: allowlist secret
        let l = h("edd3f55c1a631258d69cf7a2def9de1400000000000000000000000000000010"); // pragma: allowlist secret
        sig[32..].copy_from_slice(&l);
        assert!(!is_strict_signature_encoding(&sig));
    }
}
