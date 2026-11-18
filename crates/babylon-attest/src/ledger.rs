use ed25519_dalek::{Signature, Signer, SigningKey, Verifier, VerifyingKey};
use rand::rngs::OsRng;
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use std::fs::{self, OpenOptions};
use std::io::{BufRead, BufReader, Write};
use std::sync::Mutex;
use std::time::{SystemTime, UNIX_EPOCH};

use crate::env;

static LEDGER_MUTEX: Mutex<()> = Mutex::new(());

struct FileLockGuard {
    #[cfg(unix)]
    file: fs::File,
}

impl FileLockGuard {
    fn acquire() -> Result<Self, String> {
        env::ensure_dirs().map_err(|e| format!("Failed to create directories: {}", e))?;
        #[cfg(unix)]
        {
            use std::os::unix::io::AsRawFd;
            let lock_path = env::keys_dir().join("ledger.lock");
            let file = OpenOptions::new()
                .create(true)
                .read(true)
                .write(true)
                .open(&lock_path)
                .map_err(|e| format!("Failed to open ledger lockfile: {}", e))?;
            let rc = unsafe { libc::flock(file.as_raw_fd(), libc::LOCK_EX) };
            if rc != 0 {
                return Err("Failed to acquire exclusive flock on ledger.lock".to_string());
            }
            Ok(Self { file })
        }
        #[cfg(not(unix))]
        {
            Ok(Self {})
        }
    }
}

#[cfg(unix)]
impl Drop for FileLockGuard {
    fn drop(&mut self) {
        use std::os::unix::io::AsRawFd;
        unsafe {
            let _ = libc::flock(self.file.as_raw_fd(), libc::LOCK_UN);
        }
    }
}

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

    #[cfg(unix)]
    {
        use std::os::unix::fs::{OpenOptionsExt, PermissionsExt};
        let mut key_file = OpenOptions::new()
            .write(true)
            .create(true)
            .truncate(true)
            .mode(0o600)
            .open(&key_path)
            .map_err(|e| format!("Failed to open node.key: {}", e))?;
        key_file
            .write_all(sk_hex.as_bytes())
            .map_err(|e| format!("Failed to write node.key: {}", e))?;
        key_file
            .sync_all()
            .map_err(|e| format!("Failed to sync node.key: {}", e))?;
        let _ = fs::set_permissions(&key_path, fs::Permissions::from_mode(0o600));
    }
    #[cfg(not(unix))]
    {
        fs::write(&key_path, sk_hex).map_err(|e| format!("Failed to write node.key: {}", e))?;
    }
    fs::write(&pub_path, vk_hex).map_err(|e| format!("Failed to write node.pub: {}", e))?;

    Ok((sk, vk))
}

pub fn compute_blake3_256(bytes: &[u8]) -> String {
    blake3::hash(bytes).to_hex().to_string()
}

pub fn compute_legacy_sha256(bytes: &[u8]) -> String {
    let mut hasher = Sha256::new();
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
    let _guard = LEDGER_MUTEX
        .lock()
        .map_err(|_| "Ledger mutex poisoned".to_string())?;
    let _file_lock = FileLockGuard::acquire()?;
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
        .map_err(|e| format!("BftCollisionError {{ kind: \"TemporalInversion\", details: \"{}\" }}", e))?
        .as_secs();

    let canonical_payload_bytes = serde_json::to_vec(&payload)
        .map_err(|e| format!("Payload serialization error: {}", e))?;
    let payload_hash = compute_blake3_256(&canonical_payload_bytes);
    let signer_pubkey = hex::encode(vk.to_bytes());

    let commitment = compute_block_commitment(index, now, &prev_hash, &payload_hash, &signer_pubkey);
    let sig: Signature = sk.sign(&commitment);
    let signature = hex::encode(sig.to_bytes());

    let block_hash = compute_blake3_256(&commitment);

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
    file.sync_all().map_err(|e| format!("Failed to sync ledger block: {}", e))?;

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

        // Verify payload hash (BLAKE3 canonical, legacy SHA-256 fallback)
        let canonical_bytes = serde_json::to_vec(&block.payload)
            .map_err(|e| format!("Canonical serialization error at block {}: {}", i, e))?;
        let computed_payload_b3 = compute_blake3_256(&canonical_bytes);
        let computed_payload_sha2 = compute_legacy_sha256(&canonical_bytes);
        if block.payload_hash != computed_payload_b3 && block.payload_hash != computed_payload_sha2 {
            return Err(format!(
                "Payload hash mismatch at block {}: computed '{}' != stored '{}'",
                block.index, computed_payload_b3, block.payload_hash
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

        let computed_block_b3 = compute_blake3_256(&commitment);
        let computed_block_sha2 = compute_legacy_sha256(&commitment);
        if block.block_hash != computed_block_b3 && block.block_hash != computed_block_sha2 {
            return Err(format!(
                "Block hash mismatch at block {}: computed '{}' != stored '{}'",
                block.index, computed_block_b3, block.block_hash
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
        eu_ai_act_compliance: "ART12_TECHNICAL_RECORD_VERIFIED_LEGAL_REVIEW_REQUIRED".to_string(),
    })
}

/// Computes a keyed/salted BLAKE3 commitment (`BLAKE3_DERIVE_KEY_SALTED`) over sensitive/PII bytes.
/// Per GDPR Arts. 5(1)(e)/17 and EDPB guidance on immutable ledgers, raw personal data and unsalted
/// hashes of personal data must not be persisted on an immutable ledger; destroying `subject_salt`
/// in the off-ledger erasable store after the statutory retention period (Arts. 19/26.6 >= 6 months)
/// achieves crypto-shredding without breaking the hash chain.
pub fn compute_salted_pii_commitment(subject_salt: &[u8], sensitive_bytes: &[u8]) -> Result<String, String> {
    if subject_salt.len() < 16 {
        return Err("GDPR salted commitment requires at least 16 bytes of entropy in subject_salt".to_string());
    }
    let derived_key = blake3::derive_key("BABYLON-60::GDPR::SALTED_PII_COMMITMENT::V1", subject_salt);
    let mut hasher = blake3::Hasher::new_keyed(&derived_key);
    hasher.update(sensitive_bytes);
    Ok(hasher.finalize().to_hex().to_string())
}

/// Appends an event to the ledger storing only `public_metadata` and a `BLAKE3_DERIVE_KEY_SALTED`
/// commitment over `sensitive_bytes`, keeping raw personal data off the immutable ledger.
pub fn append_salted_commitment_event(
    public_metadata: serde_json::Value,
    subject_salt: &[u8],
    sensitive_bytes: &[u8],
) -> Result<Block, String> {
    let commitment = compute_salted_pii_commitment(subject_salt, sensitive_bytes)?;
    let envelope_payload = serde_json::json!({
        "public_metadata": public_metadata,
        "salted_commitment": commitment,
        "commitment_scheme": "BLAKE3_DERIVE_KEY_SALTED",
        "raw_personal_data_on_immutable_ledger": false,
        "unsalted_pii_hash_on_ledger": false,
        "off_ledger_erasable_store": true,
    });
    append_event(envelope_payload)
}

pub fn export_scitt_voucher(block: &Block) -> serde_json::Value {
    serde_json::json!({
        "scitt_version": "draft-ietf-scitt-architecture-04",
        "entry_id": block.index,
        "timestamp": block.timestamp,
        "leaf_hash_algorithm": "SHA-256",
        "leaf_hash": block.block_hash,
        "previous_hash": block.prev_hash,
        "signature_algorithm": "Ed25519",
        "signer": block.signer_pubkey,
        "signature": block.signature,
        "claims": block.payload,
        "regulatory_attestation": {
            "standard": "Regulation (EU) 2024/1689 (EU AI Act)",
            "article": "Article 12 - Record-keeping and High-Risk AI Traceability",
            "technical_status": "SUPPORTED_WITHIN_DOMAIN",
            "legal_conformity": "NOT_DETERMINED",
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
        let tmp_dir = std::env::temp_dir().join(format!("babylon_attest_test_{}", std::process::id()));
        let _ = fs::remove_dir_all(&tmp_dir);
        std::env::set_var("BABYLON_HOME", &tmp_dir);

        let (sk, vk) = get_or_create_node_keys().expect("BFT Fallback");
        assert_eq!(sk.verifying_key(), vk);
        #[cfg(unix)]
        {
            use std::os::unix::fs::PermissionsExt;
            let key_mode = fs::metadata(env::keys_dir().join("node.key"))
                .expect("node.key metadata")
                .permissions()
                .mode()
                & 0o777;
            assert_eq!(key_mode, 0o600, "node.key must be confined to 0o600");
        }

        let p1 = serde_json::json!({"test": "action1", "agent": "A1"});
        let b1 = append_event(p1).expect("BFT Fallback");
        assert_eq!(b1.index, 0);

        let salt = b"ephemeral-subject-salt-0123456789";
        let secret_pii = b"applicant_id=99812;prompt=confidential_cv_content";
        let b2 = append_salted_commitment_event(
            serde_json::json!({"event_type": "hr_screening_decision", "retention_months": 6}),
            salt,
            secret_pii,
        )
        .expect("Salted append must succeed");
        assert_eq!(b2.index, 1);
        let serialized_b2 = serde_json::to_string(&b2.payload).expect("serialize");
        assert!(!serialized_b2.contains("confidential_cv_content"));
        assert_eq!(b2.payload["commitment_scheme"], "BLAKE3_DERIVE_KEY_SALTED");
        assert_eq!(b2.payload["raw_personal_data_on_immutable_ledger"], false);

        // Short salt (<16 bytes) must fail closed
        assert!(compute_salted_pii_commitment(b"short", secret_pii).is_err());

        let audit = verify_chain().expect("BFT Fallback");
        assert!(audit.valid);
        assert_eq!(audit.total_blocks, 2);
        assert_eq!(
            audit.eu_ai_act_compliance,
            "ART12_TECHNICAL_RECORD_VERIFIED_LEGAL_REVIEW_REQUIRED"
        );
        assert!(!audit.eu_ai_act_compliance.ends_with("_COMPLIANT"));

        let voucher = export_scitt_voucher(&b2);
        assert_eq!(voucher["regulatory_attestation"]["legal_conformity"], "NOT_DETERMINED");

        // Concurrent multi-threaded append must preserve strict linear hash chain
        let mut handles = Vec::new();
        for t in 0..4 {
            handles.push(std::thread::spawn(move || {
                for seq in 0..5 {
                    append_event(serde_json::json!({"thread": t, "seq": seq}))
                        .expect("concurrent append must succeed under lock");
                }
            }));
        }
        for h in handles {
            h.join().expect("thread join");
        }
        let audit_after_concurrency = verify_chain().expect("chain must remain valid after concurrency");
        assert!(audit_after_concurrency.valid);
        assert_eq!(audit_after_concurrency.total_blocks, 22);

        let _ = fs::remove_dir_all(&tmp_dir);
    }
}
