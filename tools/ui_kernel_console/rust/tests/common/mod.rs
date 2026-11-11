//! Carga de los vectores compartidos: los del kernel (`tests/acs_cbor_golden.txt` en la raíz del
//! repositorio) y el recibo dorado que genera la implementación TypeScript.
#![allow(dead_code)]

use std::path::PathBuf;

use serde_json::Value;

fn manifest_dir() -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR"))
}

/// Bytes de un vector del archivo dorado ACS del kernel.
pub fn kernel_vector(name: &str) -> Vec<u8> {
    let path = manifest_dir().join("../../../tests/acs_cbor_golden.txt");
    let text = std::fs::read_to_string(&path).expect("archivo dorado ACS del kernel");
    let hex = text
        .lines()
        .find_map(|line| {
            line.split_once(' ')
                .filter(|(key, _)| *key == name)
                .map(|(_, v)| v.to_string())
        })
        .unwrap_or_else(|| panic!("vector {name} ausente"));
    decode_hex(&hex)
}

/// Hex (minúsculas, sin prefijo) a bytes.
pub fn decode_hex(hex: &str) -> Vec<u8> {
    assert!(hex.len().is_multiple_of(2), "hex de longitud impar");
    (0..hex.len())
        .step_by(2)
        .map(|i| u8::from_str_radix(&hex[i..i + 2], 16).expect("hex"))
        .collect()
}

/// Constantes del recibo dorado escrito por `tests/fixtures/writeGolden.ts`.
pub struct Golden {
    /// Ancla de confianza.
    pub policy: Value,
    /// Recibo sellado.
    pub receipt: Value,
    /// Preimágenes y hashes intermedios.
    pub intermediate: Value,
}

fn exported_object(source: &str, name: &str) -> Value {
    let start_marker = format!("export const {name} = ");
    let start = source
        .find(&start_marker)
        .unwrap_or_else(|| panic!("{name} ausente"))
        + start_marker.len();
    let end = start + source[start..].find("\n};").expect("cierre del objeto") + 2;
    serde_json::from_str(&source[start..end]).unwrap_or_else(|e| panic!("{name} no es JSON: {e}"))
}

/// Lee el recibo dorado de TypeScript (las marcas `pragma` son comentarios de detect-secrets).
pub fn golden() -> Golden {
    let path = manifest_dir().join("../tests/fixtures/goldenReceipt.ts");
    let source = std::fs::read_to_string(&path)
        .expect("recibo dorado TypeScript")
        .replace(" // pragma: allowlist secret", "");
    Golden {
        policy: exported_object(&source, "GOLDEN_POLICY"),
        receipt: exported_object(&source, "GOLDEN_RECEIPT"),
        intermediate: exported_object(&source, "GOLDEN_INTERMEDIATE"),
    }
}

/// Forma sin sellar de un recibo (lo que `unsealedOf` produce en TypeScript).
pub fn unsealed_of(receipt: &Value) -> Value {
    let mut nodes = receipt["execution_dag"].clone();
    for node in nodes.as_array_mut().expect("execution_dag") {
        node.as_object_mut().expect("nodo").remove("state_hash");
    }
    serde_json::json!({
        "execution_id": receipt["execution_id"],
        "causal_clock": receipt["causal_clock"],
        "manifest_version": receipt["manifest_version"],
        "ingress": receipt["ingress"],
        "nodes": nodes,
        "larsa_commit": receipt["cryptographic_seal"]["larsa_commit"],
        "lean4_proof": receipt["cryptographic_seal"]["lean4_proof"],
        "audit_metrics": receipt["audit_metrics"],
    })
}
