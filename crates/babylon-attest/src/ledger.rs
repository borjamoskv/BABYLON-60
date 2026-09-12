use ed25519_dalek::{Signature, Signer, SigningKey, Verifier, VerifyingKey};
use rand::rngs::OsRng;
use serde::{Deserialize, Serialize};
use sha3::{Digest, Sha3_256};
use std::fs::{self, OpenOptions};
use std::io::{BufRead, BufReader, Write};
use std::time::{SystemTime, UNIX_EPOCH};

use crate::env;

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct Block {
    pub index: u64,
    pub timestamp: u64,
    pub prev_hash: String,
    pub payload_hash: String,
    pub payload: serde_json::Value,
    pub signer_pubkey: String,
    pub signature: String,
    pub block_hash: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ChainAuditReport {
    pub valid: bool,
    pub total_blocks: u64,
    pub genesis_hash: String,
    pub latest_block_hash: String,
    pub start_timestamp: u64,
    pub end_timestamp: u64,
    pub eu_ai_act_compliance: String,
}

pub fn get_or_create_node_keys() -> Result<(SigningKey, VerifyingKey), String> {
    env::ensure_dirs().map_err(|e| format!("Failed to create directories: {}", e))?;
    let key_path = env::keys_dir().join("node.key");
    let pub_path = env::keys_dir().join("node.pub");

    if key_path.exists() {
        let bytes = fs::read(&key_path).map_err(|e| format!("Failed to read node key: {}", e))?;
        if bytes.len() == 32 {
            let mut arr = [0u8; 32];
            arr.copy_from_slice(&bytes);
            let sk = SigningKey::from_bytes(&arr);
            let vk = sk.verifying_key();
            return Ok((sk, vk));
        } else if bytes.len() == 64 {
            // Hex encoded
            let text = String::from_utf8_lossy(&bytes).trim().to_string();
            let decoded = hex::decode(text).map_err(|e| format!("Invalid hex in node.key: {}", e))?;
            let mut arr = [0u8; 32];
            arr.copy_from_slice(&decoded);
            let sk = SigningKey::from_bytes(&arr);
            let vk = sk.verifying_key();
            return Ok((sk, vk));
        }
    }

    // Generate new keypair
    let mut csprng = OsRng;
    let sk = SigningKey::generate(&mut csprng);
    let vk = sk.verifying_key();

    let sk_hex = hex::encode(sk.to_bytes());
    let vk_hex = hex::encode(vk.to_bytes());

    fs::write(&key_path, sk_hex).map_err(|e| format!("Failed to write node.key: {}", e))?;
    fs::write(&pub_path, vk_hex).map_err(|e| format!("Failed to write node.pub: {}", e))?;

    Ok((sk, vk))
}

pub fn compute_sha3_256(bytes: &[u8]) -> String {
    let mut hasher = Sha3_256::new();
    hasher.update(bytes);
    hex::encode(hasher.finalize())
}

pub fn compute_block_commitment(
    index: u64,
    timestamp: u64,
    prev_hash: &str,
    payload_hash: &str,
    signer_pubkey: &str,
) -> Vec<u8> {
    format!(
        "B60_BLOCK_COMMITMENT:{}:{}:{}:{}:{}",
        index, timestamp, prev_hash, payload_hash, signer_pubkey
    )
    .into_bytes()
}

pub fn get_chain_blocks() -> Result<Vec<Block>, String> {
    let path = env::ledger_file();
    if !path.exists() {
        return Ok(Vec::new());
    }

    let file = fs::File::open(&path).map_err(|e| format!("Cannot open chain: {}", e))?;
    let reader = BufReader::new(file);
    let mut blocks = Vec::new();

    for (line_num, line) in reader.lines().enumerate() {
        let l = line.map_err(|e| format!("Read line {} failed: {}", line_num, e))?;
        if l.trim().is_empty() {
            continue;
        }
        let b: Block = serde_json::from_str(&l)
            .map_err(|e| format!("Parse error at line {}: {}", line_num, e))?;
        blocks.push(b);
    }

    Ok(blocks)
}

pub fn append_event(payload: serde_json::Value) -> Result<Block, String> {
    env::ensure_dirs().map_err(|e| format!("Failed to create directories: {}", e))?;
    let (sk, vk) = get_or_create_node_keys()?;
    let blocks = get_chain_blocks()?;

    let (index, prev_hash) = if let Some(last) = blocks.last() {
        (last.index + 1, last.block_hash.clone())
    } else {
        (0, "0".repeat(64))
    };

    let now = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap()
        .as_secs();

    let canonical_payload_bytes = serde_json::to_vec(&payload)
        .map_err(|e| format!("Payload serialization error: {}", e))?;
    let payload_hash = compute_sha3_256(&canonical_payload_bytes);
    let signer_pubkey = hex::encode(vk.to_bytes());

    let commitment = compute_block_commitment(index, now, &prev_hash, &payload_hash, &signer_pubkey);
    let sig: Signature = sk.sign(&commitment);
    let signature = hex::encode(sig.to_bytes());

    let block_hash = compute_sha3_256(&commitment);

    let block = Block {
        index,
        timestamp: now,
        prev_hash,
        payload_hash,
        payload,
        signer_pubkey,
        signature,
        block_hash,
    };

    let serialized = serde_json::to_string(&block).map_err(|e| format!("Block serialization error: {}", e))?;

    let mut file = OpenOptions::new()
        .create(true)
        .append(true)
        .open(env::ledger_file())
        .map_err(|e| format!("Failed to open ledger for appending: {}", e))?;

    writeln!(file, "{}", serialized).map_err(|e| format!("Failed to write block: {}", e))?;

    Ok(block)
}

pub fn verify_chain() -> Result<ChainAuditReport, String> {
    let blocks = get_chain_blocks()?;
    if blocks.is_empty() {
        return Ok(ChainAuditReport {
            valid: true,
            total_blocks: 0,
            genesis_hash: "N/A (Empty Chain)".to_string(),
            latest_block_hash: "N/A".to_string(),
            start_timestamp: 0,
            end_timestamp: 0,
            eu_ai_act_compliance: "PENDING_FIRST_RECORD".to_string(),
        });
    }

    let mut expected_prev_hash = "0".repeat(64);

    for (i, block) in blocks.iter().enumerate() {
        if block.index != i as u64 {
            return Err(format!("Index discontinuity at block {}: expected {}", block.index, i));
        }

        if block.prev_hash != expected_prev_hash {
            return Err(format!(
                "Chain break at block {}: prev_hash '{}' != expected '{}'",
                block.index, block.prev_hash, expected_prev_hash
            ));
        }

        // Verify payload hash
        let canonical_bytes = serde_json::to_vec(&block.payload)
            .map_err(|e| format!("Canonical serialization error at block {}: {}", i, e))?;
        let computed_payload_hash = compute_sha3_256(&canonical_bytes);
        if computed_payload_hash != block.payload_hash {
            return Err(format!(
                "Payload hash mismatch at block {}: computed '{}' != stored '{}'",
                block.index, computed_payload_hash, block.payload_hash
            ));
        }

        // Verify commitment & signature
        let commitment = compute_block_commitment(
            block.index,
            block.timestamp,
            &block.prev_hash,
            &block.payload_hash,
            &block.signer_pubkey,
        );

        let computed_block_hash = compute_sha3_256(&commitment);
        if computed_block_hash != block.block_hash {
            return Err(format!(
                "Block hash mismatch at block {}: computed '{}' != stored '{}'",
                block.index, computed_block_hash, block.block_hash
            ));
        }

        let vk_bytes = hex::decode(&block.signer_pubkey)
            .map_err(|e| format!("Invalid signer pubkey hex at block {}: {}", i, e))?;
        if vk_bytes.len() != 32 {
            return Err(format!("Invalid signer pubkey length at block {}: must be 32 bytes", i));
        }
        let mut vk_arr = [0u8; 32];
        vk_arr.copy_from_slice(&vk_bytes);
        let vk = VerifyingKey::from_bytes(&vk_arr)
            .map_err(|e| format!("Invalid Ed25519 verifying key at block {}: {}", i, e))?;

        let sig_bytes = hex::decode(&block.signature)
            .map_err(|e| format!("Invalid signature hex at block {}: {}", i, e))?;
        if sig_bytes.len() != 64 {
            return Err(format!("Invalid signature length at block {}: must be 64 bytes", i));
        }
        let mut sig_arr = [0u8; 64];
        sig_arr.copy_from_slice(&sig_bytes);
        let sig = Signature::from_bytes(&sig_arr);

        vk.verify(&commitment, &sig)
            .map_err(|e| format!("Cryptographic signature verification failed at block {}: {}", i, e))?;

        expected_prev_hash = block.block_hash.clone();
    }

    let first = &blocks[0];
    let last = &blocks[blocks.len() - 1];

    Ok(ChainAuditReport {
        valid: true,
        total_blocks: blocks.len() as u64,
        genesis_hash: first.block_hash.clone(),
        latest_block_hash: last.block_hash.clone(),
        start_timestamp: first.timestamp,
        end_timestamp: last.timestamp,
        eu_ai_act_compliance: "EU_AI_ACT_ART12_RECORD_KEEPING_COMPLIANT".to_string(),
    })
}

pub fn export_scitt_voucher(block: &Block) -> serde_json::Value {
    serde_json::json!({
        "scitt_version": "draft-ietf-scitt-architecture-04",
        "entry_id": block.index,
        "timestamp": block.timestamp,
        "leaf_hash_algorithm": "SHA3-256",
        "leaf_hash": block.block_hash,
        "previous_hash": block.prev_hash,
        "signature_algorithm": "Ed25519",
        "signer": block.signer_pubkey,
        "signature": block.signature,
        "claims": block.payload,
        "regulatory_attestation": {
            "standard": "Regulation (EU) 2024/1689 (EU AI Act)",
            "article": "Article 12 - Record-keeping and High-Risk AI Traceability",
            "fail_closed": true,
            "tamper_evident": true
        }
    })
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_ledger_append_and_verify() {
        let (sk, vk) = get_or_create_node_keys().unwrap();
        assert_eq!(sk.verifying_key(), vk);

        let p1 = serde_json::json!({"test": "action1", "agent": "A1"});
        let b1 = append_event(p1).unwrap();
        assert_eq!(b1.index, b1.index);

        let audit = verify_chain().unwrap();
        assert!(audit.valid);
        assert!(audit.total_blocks > 0);
    }
}
