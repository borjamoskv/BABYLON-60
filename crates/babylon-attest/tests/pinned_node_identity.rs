//! The ledger signer is pinned to `keys/node.pub` and the node identity is never regenerated
//! over existing state. Temporary fixtures only; `BABYLON_HOME` is process-global, so the tests
//! are serialised.
use babylon_attest::env;
use babylon_attest::ledger::{
    append_event, compute_blake3_256, compute_block_commitment, get_chain_blocks,
    get_or_create_node_keys, verify_chain, verify_chain_with_trusted_key, Block,
};
use ed25519_dalek::{Signer, SigningKey};
use std::fs;
use std::path::PathBuf;
use std::sync::atomic::{AtomicU64, Ordering};
use std::sync::{Mutex, MutexGuard};

static HOME_LOCK: Mutex<()> = Mutex::new(());

struct Home {
    dir: PathBuf,
    _guard: MutexGuard<'static, ()>,
}

impl Drop for Home {
    fn drop(&mut self) {
        let _ = fs::remove_dir_all(&self.dir);
    }
}

fn fresh_home() -> Home {
    static SEQ: AtomicU64 = AtomicU64::new(0);
    let guard = HOME_LOCK.lock().unwrap_or_else(|e| e.into_inner());
    let dir = std::env::temp_dir().join(format!(
        "b60-attest-pin-{}-{}",
        std::process::id(),
        SEQ.fetch_add(1, Ordering::Relaxed)
    ));
    let _ = fs::remove_dir_all(&dir);
    fs::create_dir_all(&dir).unwrap();
    std::env::set_var("BABYLON_HOME", &dir);
    Home { dir, _guard: guard }
}

/// A block built exactly as `append_event` builds it, signed with an arbitrary key.
fn forge_block(sk: &SigningKey, index: u64, prev_hash: &str, payload: serde_json::Value) -> Block {
    let timestamp = 1_700_000_000 + index;
    let payload_hash = compute_blake3_256(&serde_json::to_vec(&payload).unwrap());
    let signer_pubkey = hex::encode(sk.verifying_key().to_bytes());
    let commitment =
        compute_block_commitment(index, timestamp, prev_hash, &payload_hash, &signer_pubkey);
    Block {
        index,
        timestamp,
        prev_hash: prev_hash.to_string(),
        payload_hash,
        payload,
        signer_pubkey,
        signature: hex::encode(sk.sign(&commitment).to_bytes()),
        block_hash: compute_blake3_256(&commitment),
    }
}

fn write_chain(blocks: &[Block]) {
    let text: String = blocks
        .iter()
        .map(|b| serde_json::to_string(b).unwrap() + "\n")
        .collect();
    fs::write(env::ledger_file(), text).unwrap();
}

#[test]
fn history_rewritten_under_a_foreign_key_is_rejected() {
    let _home = fresh_home();
    append_event(serde_json::json!({"action": "approve", "amount": 10})).unwrap();
    append_event(serde_json::json!({"action": "log_out"})).unwrap();
    assert!(verify_chain().unwrap().valid);
    let (_, node_vk) = get_or_create_node_keys().unwrap();

    let attacker = SigningKey::from_bytes(&[0xA7; 32]);
    let b0 = forge_block(
        &attacker,
        0,
        &"0".repeat(64),
        serde_json::json!({"action": "approve", "amount": 1_000_000}),
    );
    let b1 = forge_block(
        &attacker,
        1,
        &b0.block_hash,
        serde_json::json!({"action": "log_out"}),
    );
    write_chain(&[b0, b1]);

    // The head anchor catches the rewrite first; without it, the signer pin still does.
    assert!(verify_chain().unwrap_err().contains("Ledger rewritten"));
    assert!(verify_chain_with_trusted_key(&node_vk).is_err());
    assert!(verify_chain_with_trusted_key(&attacker.verifying_key()).is_err());
    fs::remove_file(env::keys_dir().join("ledger.head")).unwrap();
    let err = append_event(serde_json::json!({"action": "next"})).unwrap_err();
    assert!(err.contains("Untrusted signer at block 0"), "{err}");
}

#[test]
fn non_empty_ledger_without_pin_is_not_verifiable() {
    let _home = fresh_home();
    append_event(serde_json::json!({"n": 1})).unwrap();
    fs::remove_file(env::keys_dir().join("node.pub")).unwrap();
    assert!(verify_chain().unwrap_err().contains("node.pub is missing"));
}

#[test]
fn node_does_not_extend_a_tip_signed_by_another_key() {
    let _home = fresh_home();
    append_event(serde_json::json!({"n": 0})).unwrap();
    let genuine = get_chain_blocks().unwrap();
    let attacker = SigningKey::from_bytes(&[0xA7; 32]);
    let forged = forge_block(
        &attacker,
        1,
        &genuine[0].block_hash,
        serde_json::json!({"n": 1}),
    );
    write_chain(&[genuine[0].clone(), forged]);

    let err = append_event(serde_json::json!({"n": 2})).unwrap_err();
    assert!(err.contains("Untrusted signer at block 1"), "{err}");
    assert_eq!(get_chain_blocks().unwrap().len(), 2);
}

#[test]
fn node_does_not_extend_a_tip_relabelled_with_its_own_public_key() {
    let _home = fresh_home();
    append_event(serde_json::json!({"n": 0})).unwrap();
    let genuine = get_chain_blocks().unwrap();
    // Forged by another key, then relabelled: `signer_pubkey` names the node, the commitment
    // and block hash are recomputed for that label, and the signature is the attacker's.
    let attacker = SigningKey::from_bytes(&[0xA7; 32]);
    let mut forged = forge_block(
        &attacker,
        1,
        &genuine[0].block_hash,
        serde_json::json!({"n": 1}),
    );
    forged.signer_pubkey = genuine[0].signer_pubkey.clone();
    let commitment = compute_block_commitment(
        forged.index,
        forged.timestamp,
        &forged.prev_hash,
        &forged.payload_hash,
        &forged.signer_pubkey,
    );
    forged.block_hash = compute_blake3_256(&commitment);
    forged.signature = hex::encode(attacker.sign(&commitment).to_bytes());
    write_chain(&[genuine[0].clone(), forged]);

    let err = append_event(serde_json::json!({"n": 2})).unwrap_err();
    assert!(
        err.contains("signature verification failed at block 1"),
        "{err}"
    );
    assert_eq!(get_chain_blocks().unwrap().len(), 2);
}

#[cfg(unix)]
#[test]
fn unreadable_ledger_location_does_not_mint_a_new_identity() {
    use std::os::unix::fs::PermissionsExt;
    let _home = fresh_home();
    env::ensure_dirs().unwrap();
    let ledger_dir = env::ledger_file().parent().unwrap().to_path_buf();
    fs::write(env::ledger_file(), "x\n").unwrap();
    fs::set_permissions(&ledger_dir, fs::Permissions::from_mode(0o000)).unwrap();
    // Root ignores directory permissions; the check is only meaningful when stat is refused.
    let refused = fs::metadata(env::ledger_file()).is_err();
    let result = get_or_create_node_keys();
    fs::set_permissions(&ledger_dir, fs::Permissions::from_mode(0o700)).unwrap();

    if refused {
        assert!(result.unwrap_err().contains("Failed to inspect ledger"));
        assert!(!env::keys_dir().join("node.key").exists());
    }
}

#[test]
fn provisioned_hex_key_with_trailing_newline_is_loaded_not_replaced() {
    let _home = fresh_home();
    env::ensure_dirs().unwrap();
    let provisioned = SigningKey::from_bytes(&[0x5A; 32]);
    let key_path = env::keys_dir().join("node.key");
    let content = format!("{}\n", hex::encode(provisioned.to_bytes()));
    fs::write(&key_path, &content).unwrap();

    let (_, vk) = get_or_create_node_keys().unwrap();
    assert_eq!(vk, provisioned.verifying_key());
    assert_eq!(fs::read_to_string(&key_path).unwrap(), content);
    assert_eq!(
        fs::read_to_string(env::keys_dir().join("node.pub")).unwrap(),
        hex::encode(vk.to_bytes())
    );
}

#[test]
fn malformed_node_key_is_fatal_and_left_untouched() {
    for content in [&b"not a key"[..], &[0u8; 31][..], &[b'a'; 66][..], &b""[..]] {
        let _home = fresh_home();
        env::ensure_dirs().unwrap();
        let key_path = env::keys_dir().join("node.key");
        fs::write(&key_path, content).unwrap();

        assert!(get_or_create_node_keys().is_err());
        assert!(append_event(serde_json::json!({"n": 0})).is_err());
        assert_eq!(fs::read(&key_path).unwrap(), content);
        assert!(!env::keys_dir().join("node.pub").exists());
        assert!(get_chain_blocks().unwrap().is_empty());
    }
}

#[test]
fn missing_node_key_is_not_regenerated_over_a_pin_or_a_ledger() {
    let _home = fresh_home();
    append_event(serde_json::json!({"n": 0})).unwrap();
    let key_path = env::keys_dir().join("node.key");
    let pub_path = env::keys_dir().join("node.pub");
    let pin = fs::read_to_string(&pub_path).unwrap();

    fs::remove_file(&key_path).unwrap();
    assert!(get_or_create_node_keys()
        .unwrap_err()
        .contains("node.pub is pinned"));
    assert!(!key_path.exists());
    assert_eq!(fs::read_to_string(&pub_path).unwrap(), pin);

    fs::remove_file(&pub_path).unwrap();
    assert!(get_or_create_node_keys()
        .unwrap_err()
        .contains("ledger is not empty"));
    assert!(!key_path.exists() && !pub_path.exists());
}

#[test]
fn node_key_that_disagrees_with_the_pin_is_fatal() {
    let _home = fresh_home();
    append_event(serde_json::json!({"n": 0})).unwrap();
    let key_path = env::keys_dir().join("node.key");
    fs::write(&key_path, hex::encode([0x11u8; 32])).unwrap();

    assert!(get_or_create_node_keys()
        .unwrap_err()
        .contains("does not match the pinned"));
    assert!(append_event(serde_json::json!({"n": 1})).is_err());
    assert_eq!(get_chain_blocks().unwrap().len(), 1);
}

fn truncate_ledger_to(lines: usize) {
    let text = fs::read_to_string(env::ledger_file()).unwrap();
    let kept: Vec<&str> = text.lines().take(lines).collect();
    fs::write(env::ledger_file(), kept.join("\n") + "\n").unwrap();
}

#[test]
fn tail_truncation_is_detected_and_not_extended() {
    let _home = fresh_home();
    for n in 0..3 {
        append_event(serde_json::json!({"seq": n})).unwrap();
    }
    truncate_ledger_to(2);

    assert!(verify_chain().unwrap_err().contains("Ledger truncated"));
    assert!(append_event(serde_json::json!({"seq": 3}))
        .unwrap_err()
        .contains("Ledger truncated"));
    assert_eq!(get_chain_blocks().unwrap().len(), 2);
}

#[test]
fn deleted_ledger_of_an_attesting_node_is_not_valid() {
    let _home = fresh_home();
    append_event(serde_json::json!({"seq": 0})).unwrap();
    fs::remove_file(env::ledger_file()).unwrap();
    assert!(verify_chain().unwrap_err().contains("Ledger truncated"));
}

#[test]
fn missing_head_anchor_is_not_reported_as_valid() {
    let _home = fresh_home();
    append_event(serde_json::json!({"seq": 0})).unwrap();
    fs::remove_file(env::keys_dir().join("ledger.head")).unwrap();
    assert!(verify_chain()
        .unwrap_err()
        .contains("ledger.head is missing"));

    // Deleting both the ledger and its anchor still leaves the pinned identity behind.
    fs::remove_file(env::ledger_file()).unwrap();
    assert!(verify_chain()
        .unwrap_err()
        .contains("ledger.head is missing"));
}

#[test]
fn head_anchor_not_signed_by_the_node_is_rejected() {
    let _home = fresh_home();
    append_event(serde_json::json!({"seq": 0})).unwrap();
    append_event(serde_json::json!({"seq": 1})).unwrap();
    truncate_ledger_to(1);
    let kept = get_chain_blocks().unwrap();
    let attacker = SigningKey::from_bytes(&[0xA7; 32]);
    let message = format!("B60_LEDGER_HEAD:1:{}", kept[0].block_hash);
    let forged = serde_json::json!({
        "count": 1,
        "head_hash": kept[0].block_hash,
        "signature": hex::encode(attacker.sign(message.as_bytes()).to_bytes()),
    });
    fs::write(env::keys_dir().join("ledger.head"), forged.to_string()).unwrap();

    assert!(verify_chain()
        .unwrap_err()
        .contains("not signed by the pinned node key"));
}

#[test]
fn ledger_predating_the_head_anchor_is_anchored_on_the_next_append() {
    let _home = fresh_home();
    append_event(serde_json::json!({"seq": 0})).unwrap();
    append_event(serde_json::json!({"seq": 1})).unwrap();
    fs::remove_file(env::keys_dir().join("ledger.head")).unwrap();

    append_event(serde_json::json!({"seq": 2})).unwrap();
    let report = verify_chain().unwrap();
    assert!(report.valid);
    assert_eq!(report.total_blocks, 3);
}

#[test]
fn block_appended_before_a_crash_re_anchoring_still_verifies() {
    let _home = fresh_home();
    append_event(serde_json::json!({"seq": 0})).unwrap();
    let stale_head = fs::read(env::keys_dir().join("ledger.head")).unwrap();
    append_event(serde_json::json!({"seq": 1})).unwrap();
    fs::write(env::keys_dir().join("ledger.head"), stale_head).unwrap();

    assert_eq!(verify_chain().unwrap().total_blocks, 2);
    append_event(serde_json::json!({"seq": 2})).unwrap();
    assert_eq!(verify_chain().unwrap().total_blocks, 3);
}

#[test]
fn initialised_node_without_records_verifies_as_pending() {
    let _home = fresh_home();
    get_or_create_node_keys().unwrap();
    let report = verify_chain().unwrap();
    assert_eq!(report.total_blocks, 0);
    assert_eq!(report.eu_ai_act_compliance, "PENDING_FIRST_RECORD");
}

#[test]
fn unsigned_fields_injected_into_a_block_are_rejected() {
    let _home = fresh_home();
    append_event(serde_json::json!({"action": "transfer", "approved": false})).unwrap();
    let line = fs::read_to_string(env::ledger_file()).unwrap();
    let mut record: serde_json::Value = serde_json::from_str(line.trim()).unwrap();
    record["operator_approved"] = serde_json::json!(true);
    fs::write(env::ledger_file(), format!("{record}\n")).unwrap();

    assert!(verify_chain().unwrap_err().contains("unknown field"));
}
