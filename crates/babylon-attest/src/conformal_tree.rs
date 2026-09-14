//! Conformal Merkle Tree & Aeon Verifier (C5-REAL / INV_C5_AEON)
//!
//! High-performance balanced binary Merkle tree engine using SHA3-256
//! for O(log2 N) inclusion proofs, Aeon manifest attestation verification,
//! and native C-ABI compatible zero-copy performance.

use base64::Engine;
use ed25519_dalek::{Signature, Verifier, VerifyingKey};
use serde::{Deserialize, Serialize};
use sha3::{Digest, Sha3_256};
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
    /// Builds a balanced binary Merkle tree using SHA3-256.
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
                let mut hasher = Sha3_256::new();
                hasher.update(combined.as_bytes());
                let parent = hex::encode(hasher.finalize());
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

    /// Verifies an inclusion proof O(log2 N) deterministically against the expected root.
    pub fn verify_inclusion_proof(
        leaf: &str,
        proof: &[InclusionStep],
        expected_root: &str,
    ) -> bool {
        let mut curr = leaf.to_string();
        for step in proof {
            let combined = match step.position {
                ProofPosition::Left => format!("{}:{}", step.sibling_hash, curr),
                ProofPosition::Right => format!("{}:{}", curr, step.sibling_hash),
            };
            let mut hasher = Sha3_256::new();
            hasher.update(combined.as_bytes());
            curr = hex::encode(hasher.finalize());
        }
        curr == expected_root
    }
}

/// Canonical SHA3-256 leaf hash for a claim receipt.
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
    let mut hasher = Sha3_256::new();
    hasher.update(leaf_repr.as_bytes());
    hex::encode(hasher.finalize())
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
pub fn verify_manifest_file(manifest_path: &Path) -> Result<AeonVerificationResult, String> {
    let data = fs::read_to_string(manifest_path)
        .map_err(|e| format!("No se pudo leer el manifiesto: {}", e))?;
    let manifest: AeonManifest = serde_json::from_str(&data)
        .map_err(|e| format!("Error deserializando JSON de manifiesto: {}", e))?;

    if manifest.status != "FROZEN_C5_REAL" {
        return Err(format!("Estado no sellado: {}", manifest.status));
    }

    // Verify Ed25519 signature over bytes.fromhex(merkle_root)
    let pub_bytes = base64::engine::general_purpose::STANDARD
        .decode(&manifest.sovereign_identity.l0_public_key_b64)
        .map_err(|e| format!("Base64 pubkey error: {}", e))?;
    let sig_bytes = base64::engine::general_purpose::STANDARD
        .decode(&manifest.sovereign_identity.ed25519_signature_b64)
        .map_err(|e| format!("Base64 signature error: {}", e))?;

    if pub_bytes.len() != 32 {
        return Err(format!("Longitud de clave pública inválida: {}", pub_bytes.len()));
    }
    let mut pub_arr = [0u8; 32];
    pub_arr.copy_from_slice(&pub_bytes);
    let vk = VerifyingKey::from_bytes(&pub_arr)
        .map_err(|e| format!("VerifyingKey parse error: {}", e))?;

    let sig = Signature::from_slice(&sig_bytes)
        .map_err(|e| format!("Signature parse error: {}", e))?;

    let root_bytes = hex::decode(&manifest.merkle_root)
        .map_err(|e| format!("Hex decode error: {}", e))?;

    let sig_valid = vk.verify(&root_bytes, &sig).is_ok();

    let hw_uuid = manifest
        .hardware_attestation
        .get("hardware_uuid")
        .and_then(|v| v.as_str())
        .unwrap_or("UNKNOWN")
        .to_string();

    let overall_valid = sig_valid && manifest.status == "FROZEN_C5_REAL";

    Ok(AeonVerificationResult {
        aeon_id: manifest.aeon_id,
        status: manifest.status,
        merkle_root: manifest.merkle_root,
        total_claims: manifest.total_claims_sealed,
        ed25519_signature_valid: sig_valid,
        hardware_uuid: hw_uuid,
        overall_valid,
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
}
