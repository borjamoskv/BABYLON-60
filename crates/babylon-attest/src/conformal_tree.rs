//! Conformal Merkle Tree & Aeon Verifier (C5-REAL / INV_C5_AEON)
//!
//! High-performance balanced binary Merkle tree engine using BLAKE3
//! for O(log2 N) inclusion proofs, Aeon manifest attestation verification,
//! and native C-ABI compatible zero-copy performance.

use base64::Engine;
use ed25519_dalek::{Signature, Verifier, VerifyingKey};
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use std::fs;
use std::path::Path;

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum ProofPosition {
    #[serde(rename = "LEFT")]
    Left,
    #[serde(rename = "RIGHT")]
    Right,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct InclusionStep {
    pub position: ProofPosition,
    pub sibling_hash: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ConformalMerkleTree {
    pub leaves: Vec<String>,
    pub tree_levels: Vec<Vec<String>>,
}

impl ConformalMerkleTree {
    /// Builds a balanced binary Merkle tree using BLAKE3 (256-bit hex).
    /// If a level has an odd number of nodes, the last node is paired with itself.
    pub fn new(leaves: Vec<String>) -> Result<Self, String> {
        if leaves.is_empty() {
            return Err("El árbol de Merkle requiere al menos una hoja.".to_string());
        }

        let mut tree_levels = Vec::new();
        tree_levels.push(leaves.clone());

        let mut current_level = leaves.clone();
        while current_level.len() > 1 {
            let mut next_level = Vec::new();
            for i in (0..current_level.len()).step_by(2) {
                let left = &current_level[i];
                let right = if i + 1 < current_level.len() {
                    &current_level[i + 1]
                } else {
                    left
                };

                let combined = format!("{}:{}", left, right);
                let parent = blake3::hash(combined.as_bytes()).to_hex().to_string();
                next_level.push(parent);
            }
            tree_levels.push(next_level.clone());
            current_level = next_level;
        }

        Ok(Self {
            leaves,
            tree_levels,
        })
    }

    /// Returns the root hash of the Merkle tree.
    pub fn root(&self) -> &str {
        &self.tree_levels.last().expect("Tree levels cannot be empty")[0]
    }

    /// Returns the number of levels (depth) of the tree.
    pub fn depth(&self) -> usize {
        self.tree_levels.len()
    }

    /// Generates an O(log2 N) inclusion proof for the leaf at `index`.
    pub fn get_inclusion_proof(&self, index: usize) -> Result<Vec<InclusionStep>, String> {
        if index >= self.leaves.len() {
            return Err(format!(
                "Índice de hoja fuera de rango: {} (total: {})",
                index,
                self.leaves.len()
            ));
        }

        let mut proof = Vec::new();
        let mut curr_idx = index;

        for level in &self.tree_levels[..self.tree_levels.len() - 1] {
            let is_right = curr_idx % 2 == 1;
            let (pos, sibling_idx) = if is_right {
                (ProofPosition::Left, curr_idx - 1)
            } else {
                let sib = if curr_idx + 1 < level.len() {
                    curr_idx + 1
                } else {
                    curr_idx
                };
                (ProofPosition::Right, sib)
            };

            proof.push(InclusionStep {
                position: pos,
                sibling_hash: level[sibling_idx].clone(),
            });
            curr_idx /= 2;
        }

        Ok(proof)
    }

    /// Verifies an inclusion proof O(log2 N) deterministically against the expected root (BLAKE3 primary, SHA-256 legacy fallback).
    pub fn verify_inclusion_proof(
        leaf: &str,
        proof: &[InclusionStep],
        expected_root: &str,
    ) -> bool {
        let mut curr_b3 = leaf.to_string();
        for step in proof {
            let combined = match step.position {
                ProofPosition::Left => format!("{}:{}", step.sibling_hash, curr_b3),
                ProofPosition::Right => format!("{}:{}", curr_b3, step.sibling_hash),
            };
            curr_b3 = blake3::hash(combined.as_bytes()).to_hex().to_string();
        }
        if curr_b3 == expected_root {
            return true;
        }

        let mut curr_sha2 = leaf.to_string();
        for step in proof {
            let combined = match step.position {
                ProofPosition::Left => format!("{}:{}", step.sibling_hash, curr_sha2),
                ProofPosition::Right => format!("{}:{}", curr_sha2, step.sibling_hash),
            };
            let mut hasher = Sha256::new();
            hasher.update(combined.as_bytes());
            curr_sha2 = hex::encode(hasher.finalize());
        }
        curr_sha2 == expected_root
    }
}

/// Canonical BLAKE3 (256-bit) leaf hash for a claim receipt.
pub fn compute_claim_leaf_hash(
    claim_id: &str,
    advisory_id: &str,
    domain: &str,
    payload_hash: &str,
    attestation_merkle_root: &str,
) -> String {
    let leaf_repr = format!(
        "{}:{}:{}:{}:{}",
        claim_id, advisory_id, domain, payload_hash, attestation_merkle_root
    );
    blake3::hash(leaf_repr.as_bytes()).to_hex().to_string()
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SovereignIdentitySection {
    pub l0_public_key_b64: String,
    pub ed25519_signature_b64: String,
    #[serde(default)]
    pub signed_payload: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AeonManifest {
    pub aeon_id: String,
    pub status: String,
    pub timestamp_utc: String,
    pub total_claims_sealed: u64,
    pub merkle_root: String,
    pub op_return_hex: Option<String>,
    pub hardware_attestation: serde_json::Value,
    pub sovereign_identity: SovereignIdentitySection,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AeonVerificationResult {
    pub aeon_id: String,
    pub status: String,
    pub merkle_root: String,
    pub total_claims: u64,
    pub ed25519_signature_valid: bool,
    pub hardware_uuid: String,
    pub overall_valid: bool,
}

/// Verifies the cryptographic integrity and Ed25519 signature of an L1 Aeon manifest file.
/// Formato v2 producido por `scripts/c5_l1_ledger/seal_bounty_aeon.py` y verificado en Python por
/// `babylon60.attestation.conformal_tree`. La firma cubre el manifiesto completo.
pub const AEON_SCHEMA_V2: &str = "babylon60.aeon-manifest.v2";
pub const AEON_SIGNED_PAYLOAD_V2: &str = "manifest-canonical-json-v2";

/// Representación de un `f64` idéntica a `repr(float)` de Python, que usa `json.dumps`.
fn python_float_repr(v: f64) -> Result<String, String> {
    if !v.is_finite() {
        return Err("Manifiesto no canónico: número no finito".into());
    }
    if v == 0.0 {
        return Ok(if v.is_sign_negative() { "-0.0" } else { "0.0" }.into());
    }
    let sci = format!("{:e}", v); // dígitos mínimos que reconstruyen el valor
    let (mantissa, exp) = sci.split_once('e').ok_or("formato de float inesperado")?;
    let exp: i32 = exp.parse().map_err(|_| "exponente de float inválido")?;
    let negative = mantissa.starts_with('-');
    let digits: String = mantissa
        .trim_start_matches('-')
        .chars()
        .filter(|c| *c != '.')
        .collect();
    let n = digits.len() as i32;
    let body = if (-4..16).contains(&exp) {
        if exp >= 0 {
            if n <= exp + 1 {
                format!("{}{}.0", digits, "0".repeat((exp + 1 - n) as usize))
            } else {
                format!(
                    "{}.{}",
                    &digits[..(exp + 1) as usize],
                    &digits[(exp + 1) as usize..]
                )
            }
        } else {
            format!("0.{}{}", "0".repeat((-exp - 1) as usize), digits)
        }
    } else {
        let m = if n == 1 {
            digits.clone()
        } else {
            format!("{}.{}", &digits[..1], &digits[1..])
        };
        format!("{}e{}{:02}", m, if exp < 0 { '-' } else { '+' }, exp.abs())
    };
    Ok(if negative { format!("-{body}") } else { body })
}

/// Equivalente a `json.dumps(v, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
/// allow_nan=False)`.
fn write_canonical_json(v: &serde_json::Value, out: &mut String) -> Result<(), String> {
    use serde_json::Value;
    match v {
        Value::Null => out.push_str("null"),
        Value::Bool(b) => out.push_str(if *b { "true" } else { "false" }),
        Value::Number(n) => {
            if let Some(i) = n.as_i64() {
                out.push_str(&i.to_string());
            } else if let Some(u) = n.as_u64() {
                out.push_str(&u.to_string());
            } else {
                out.push_str(&python_float_repr(
                    n.as_f64().ok_or("número no representable")?,
                )?);
            }
        }
        Value::String(text) => {
            out.push_str(&serde_json::to_string(text).map_err(|e| e.to_string())?);
        }
        Value::Array(items) => {
            out.push('[');
            for (i, item) in items.iter().enumerate() {
                if i > 0 {
                    out.push(',');
                }
                write_canonical_json(item, out)?;
            }
            out.push(']');
        }
        Value::Object(map) => {
            let mut keys: Vec<&String> = map.keys().collect();
            keys.sort();
            out.push('{');
            for (i, key) in keys.iter().enumerate() {
                if i > 0 {
                    out.push(',');
                }
                out.push_str(&serde_json::to_string(key).map_err(|e| e.to_string())?);
                out.push(':');
                write_canonical_json(&map[*key], out)?;
            }
            out.push('}');
        }
    }
    Ok(())
}

/// Bytes firmados de un manifiesto v2: el manifiesto completo en JSON canónico, sin el campo
/// de la propia firma. Mismo contrato que `canonical_aeon_manifest_bytes` en Python.
pub fn canonical_aeon_manifest_bytes(raw: &serde_json::Value) -> Result<Vec<u8>, String> {
    let mut body = raw.clone();
    let identity = body
        .get_mut("sovereign_identity")
        .and_then(|v| v.as_object_mut())
        .ok_or("Manifest sovereign identity must be an object")?;
    identity.remove("ed25519_signature_b64");
    let mut out = String::new();
    write_canonical_json(&body, &mut out)?;
    Ok(out.into_bytes())
}

/// C0341: verifica un manifiesto Aeon v2 contra un ancla externa. La clave que trae el
/// manifiesto debe coincidir con `trusted_pubkey_b64`, y la firma cubre el manifiesto completo
/// (`canonical_aeon_manifest_bytes`), así que alterar cualquier campo invalida la verificación.
pub fn verify_manifest_file(
    manifest_path: &Path,
    trusted_pubkey_b64: &str,
) -> Result<AeonVerificationResult, String> {
    let data = fs::read_to_string(manifest_path)
        .map_err(|e| format!("No se pudo leer el manifiesto: {}", e))?;
    let raw: serde_json::Value = serde_json::from_str(&data)
        .map_err(|e| format!("Error deserializando JSON de manifiesto: {}", e))?;
    let manifest: AeonManifest = serde_json::from_value(raw.clone())
        .map_err(|e| format!("Error deserializando JSON de manifiesto: {}", e))?;

    if manifest.status != "FROZEN_C5_REAL" {
        return Err(format!("Estado no sellado: {}", manifest.status));
    }

    let b64 = base64::engine::general_purpose::STANDARD;
    let embedded = b64
        .decode(&manifest.sovereign_identity.l0_public_key_b64)
        .map_err(|e| format!("Base64 pubkey error: {}", e))?;
    let trusted = b64
        .decode(trusted_pubkey_b64)
        .map_err(|e| format!("Ancla externa: base64 inválido: {}", e))?;
    if trusted.len() != 32 {
        return Err(format!(
            "Ancla externa: longitud de clave inválida: {}",
            trusted.len()
        ));
    }
    let anchored = embedded == trusted;
    let mut trusted_arr = [0u8; 32];
    trusted_arr.copy_from_slice(&trusted);
    let vk = VerifyingKey::from_bytes(&trusted_arr)
        .map_err(|e| format!("VerifyingKey parse error: {}", e))?;
    let sig_bytes = b64
        .decode(&manifest.sovereign_identity.ed25519_signature_b64)
        .map_err(|e| format!("Base64 signature error: {}", e))?;
    let sig =
        Signature::from_slice(&sig_bytes).map_err(|e| format!("Signature parse error: {}", e))?;

    let total_claims_ok = raw
        .get("total_claims_sealed")
        .and_then(|v| v.as_u64())
        .is_some_and(|n| n > 0);
    let schema_valid = raw.get("schema").and_then(|v| v.as_str()) == Some(AEON_SCHEMA_V2)
        && manifest.sovereign_identity.signed_payload == AEON_SIGNED_PAYLOAD_V2
        && total_claims_ok
        && !manifest.aeon_id.is_empty()
        && manifest.merkle_root.len() == 64
        && manifest.merkle_root.bytes().all(|c| c.is_ascii_hexdigit());

    let sig_valid = anchored
        && schema_valid
        && canonical_aeon_manifest_bytes(&raw)
            .map(|signed| vk.verify(&signed, &sig).is_ok())
            .unwrap_or(false);

    let hw_uuid = manifest
        .hardware_attestation
        .get("hardware_uuid")
        .and_then(|v| v.as_str())
        .unwrap_or("UNKNOWN")
        .to_string();

    Ok(AeonVerificationResult {
        aeon_id: manifest.aeon_id,
        status: manifest.status,
        merkle_root: manifest.merkle_root,
        total_claims: manifest.total_claims_sealed,
        ed25519_signature_valid: sig_valid,
        hardware_uuid: hw_uuid,
        overall_valid: sig_valid,
    })
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_merkle_tree_basic_and_odd_leaves() {
        let leaves = vec![
            "leaf_0".to_string(),
            "leaf_1".to_string(),
            "leaf_2".to_string(),
        ];
        let tree = ConformalMerkleTree::new(leaves.clone()).expect("Failed to build tree");
        assert_eq!(tree.depth(), 3);
        assert!(!tree.root().is_empty());

        for (i, leaf) in leaves.iter().enumerate() {
            let proof = tree.get_inclusion_proof(i).expect("Failed to get proof");
            assert!(ConformalMerkleTree::verify_inclusion_proof(
                leaf,
                &proof,
                tree.root()
            ));
        }

        // Falsification check
        let proof_0 = tree.get_inclusion_proof(0).unwrap();
        assert!(!ConformalMerkleTree::verify_inclusion_proof(
            "tampered_leaf",
            &proof_0,
            tree.root()
        ));
    }

    #[test]
    fn test_claim_leaf_hash_computation() {
        let h = compute_claim_leaf_hash(
            "CLAIM-1",
            "GHSA-1",
            "DOMAIN_EVM",
            "payload123",
            "merkle_root_attest",
        );
        assert_eq!(h.len(), 64);
    }

    fn signed_v2_manifest(sk: &ed25519_dalek::SigningKey) -> serde_json::Value {
        use base64::Engine;
        use ed25519_dalek::Signer;
        let b64 = base64::engine::general_purpose::STANDARD;
        let mut manifest = serde_json::json!({
            "schema": AEON_SCHEMA_V2,
            "$schema": "https://babylon60.org/schemas/l1_aeon_seal_v4.json",
            "aeon_id": "AEON-TEST",
            "status": "FROZEN_C5_REAL",
            "timestamp_utc": "2026-01-01T00:00:00Z",
            "total_claims_sealed": 3,
            "merkle_root": "ab".repeat(32),
            "op_return_hex": null,
            "hardware_attestation": {"hardware_uuid": "fixture"},
            "thermodynamics": {"landauer_bound_300k_joules": 1.2345e-19, "ratio": 100.0},
            "sovereign_identity": {
                "l0_public_key_b64": b64.encode(sk.verifying_key().to_bytes()),
                "ed25519_signature_b64": "",
                "signed_payload": AEON_SIGNED_PAYLOAD_V2
            }
        });
        let signature = sk.sign(&canonical_aeon_manifest_bytes(&manifest).unwrap());
        manifest["sovereign_identity"]["ed25519_signature_b64"] =
            serde_json::Value::String(b64.encode(signature.to_bytes()));
        manifest
    }

    fn verify_value(manifest: &serde_json::Value, anchor: &str) -> AeonVerificationResult {
        let path = std::env::temp_dir().join(format!(
            "c0341-{}-{}.json",
            std::process::id(),
            std::thread::current()
                .name()
                .unwrap_or("t")
                .replace("::", "_")
        ));
        std::fs::write(&path, manifest.to_string()).unwrap();
        let result = verify_manifest_file(&path, anchor).unwrap();
        let _ = std::fs::remove_file(&path);
        result
    }

    #[test]
    fn c0341_self_signed_manifest_without_external_anchor_is_rejected() {
        use base64::Engine;
        use ed25519_dalek::SigningKey;
        let b64 = base64::engine::general_purpose::STANDARD;
        let sk = SigningKey::from_bytes(&[7u8; 32]);
        let manifest = signed_v2_manifest(&sk);
        let foreign = b64.encode(
            SigningKey::from_bytes(&[9u8; 32])
                .verifying_key()
                .to_bytes(),
        );
        assert!(
            !verify_value(&manifest, &foreign).overall_valid,
            "C0341: ancla ajena aceptada"
        );
        let own = b64.encode(sk.verifying_key().to_bytes());
        assert!(
            verify_value(&manifest, &own).overall_valid,
            "sanity: firma v2 válida rechazada"
        );
    }

    #[test]
    fn c0341_altered_fields_invalidate_the_signature() {
        use base64::Engine;
        let b64 = base64::engine::general_purpose::STANDARD;
        let sk = ed25519_dalek::SigningKey::from_bytes(&[7u8; 32]);
        let own = b64.encode(sk.verifying_key().to_bytes());
        for (field, value) in [
            ("total_claims_sealed", serde_json::json!(4)),
            ("aeon_id", serde_json::json!("AEON-OTHER")),
            ("timestamp_utc", serde_json::json!("2027-01-01T00:00:00Z")),
            (
                "hardware_attestation",
                serde_json::json!({"hardware_uuid": "other"}),
            ),
        ] {
            let mut manifest = signed_v2_manifest(&sk);
            manifest[field] = value;
            assert!(
                !verify_value(&manifest, &own).overall_valid,
                "C0341: campo {field} alterado aceptado"
            );
        }
    }

    #[test]
    fn python_float_repr_matches_cpython() {
        for (v, expected) in [
            (1.2345e-19, "1.2345e-19"),
            (1e-05, "1e-05"),
            (0.0001, "0.0001"),
            (1e16, "1e+16"),
            (1.5e16, "1.5e+16"),
            (1e15, "1000000000000000.0"),
            (100.0, "100.0"),
            (0.1, "0.1"),
            (-2.5, "-2.5"),
            (123.456, "123.456"),
            (0.0, "0.0"),
        ] {
            assert_eq!(python_float_repr(v).unwrap(), expected, "repr({v})");
        }
    }
}
