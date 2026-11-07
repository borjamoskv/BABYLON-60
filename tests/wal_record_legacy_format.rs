//! Compatibility contract for the existing unversioned 154-byte effect WAL.

use babylon60::secure_fs::{
    EffectTxOrchestrator, EffectType, NativeSecureFs, SecureFsError, WalRecord, WalRecordState,
};
use std::fs;
use std::path::PathBuf;

// Independent vector, produced with Python struct.pack("<BBQ", 2, 2, epoch),
// bytes(range(32)), struct.pack("<QQ", dev, ino), [0xa5; 32], [0x5a; 32],
// and hashlib.sha256(payload).digest(). No WalRecord code produced this fixture.
const LEGACY_HEX: &str = concat!(
    "02020807060504030201",
    "000102030405060708090a0b0c0d0e0f101112131415161718191a1b1c1d1e1f",
    "88776655443322111122334455667788",
    "a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5",
    "5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a",
    "bc795c8237e5ce1c099f1739c7cab2c41eb1220643af151e9781f1f62e2c6870",
);

fn legacy_bytes() -> Vec<u8> {
    hex::decode(LEGACY_HEX).unwrap()
}

fn nonce() -> [u8; 32] {
    std::array::from_fn(|i| i as u8)
}

#[test]
fn writer_preserves_independent_sha256_vector_byte_for_byte() {
    let record = WalRecord::new(
        WalRecordState::OutcomeUnknown,
        EffectType::Delete,
        0x0102_0304_0506_0708,
        nonce(),
        0x1122_3344_5566_7788,
        0x8877_6655_4433_2211,
        [0xa5; 32],
        [0x5a; 32],
    );
    assert_eq!(WalRecord::RECORD_SIZE, 154);
    assert_eq!(record.to_bytes().as_slice(), legacy_bytes());
}

#[test]
fn reader_accepts_independent_legacy_sha256_bytes() {
    let bytes = legacy_bytes();
    let record = WalRecord::from_bytes(&bytes).unwrap();
    assert_eq!(record.state, WalRecordState::OutcomeUnknown);
    assert_eq!(record.effect, EffectType::Delete);
    assert_eq!(record.epoch, 0x0102_0304_0506_0708);
    assert_eq!(record.nonce, nonce());
    assert_eq!(record.target_dev, 0x1122_3344_5566_7788);
    assert_eq!(record.target_ino, 0x8877_6655_4433_2211);
    assert_eq!(record.expected_pre_hash, [0xa5; 32]);
    assert_eq!(record.post_hash, [0x5a; 32]);
    assert_eq!(record.to_bytes().as_slice(), bytes);
}

#[test]
fn every_single_byte_corruption_is_rejected() {
    let bytes = legacy_bytes();
    for position in 0..bytes.len() {
        let mut corrupted = bytes.clone();
        corrupted[position] ^= 1;
        assert!(
            matches!(
                WalRecord::from_bytes(&corrupted),
                Err(SecureFsError::WalCorrupted(_))
            ),
            "accepted corruption at byte {position}"
        );
    }
}

#[test]
fn truncated_and_oversized_records_are_rejected() {
    let mut bytes = legacy_bytes();
    for length in 0..bytes.len() {
        assert!(matches!(
            WalRecord::from_bytes(&bytes[..length]),
            Err(SecureFsError::WalCorrupted(_))
        ));
    }
    bytes.push(0);
    assert!(matches!(
        WalRecord::from_bytes(&bytes),
        Err(SecureFsError::WalCorrupted(_))
    ));
}

#[test]
fn blake3_checksum_cannot_silently_reinterpret_unversioned_legacy_bytes() {
    let mut bytes = legacy_bytes();
    let digest = *blake3::hash(&bytes[..122]).as_bytes();
    assert_ne!(digest.as_slice(), &bytes[122..]);
    bytes[122..].copy_from_slice(&digest);
    assert!(matches!(
        WalRecord::from_bytes(&bytes),
        Err(SecureFsError::WalCorrupted(_))
    ));
}

struct ScratchDir(PathBuf);

impl ScratchDir {
    fn new() -> Self {
        let path = std::env::temp_dir().join(format!(
            "b60-legacy-wal-{}-{}",
            std::process::id(),
            rand::random::<u64>()
        ));
        fs::create_dir(&path).unwrap();
        Self(path)
    }
}

impl Drop for ScratchDir {
    fn drop(&mut self) {
        let _ = fs::remove_dir_all(&self.0);
    }
}

#[test]
fn orchestrator_reopens_legacy_fixture_without_rewriting_it() {
    let lab = ScratchDir::new();
    let initial = EffectTxOrchestrator::<NativeSecureFs>::new(&lab.0).unwrap();
    let wal = initial.quarantine.dir_path.join(".effect_wal.bin");
    drop(initial);
    let bytes = legacy_bytes();
    fs::write(&wal, &bytes).unwrap();
    for _ in 0..2 {
        let reopened = EffectTxOrchestrator::<NativeSecureFs>::new(&lab.0).unwrap();
        let record = reopened.get_wal_record(&nonce()).unwrap();
        assert_eq!(record.to_bytes().as_slice(), bytes);
        assert_eq!(fs::read(&wal).unwrap(), bytes);
    }
}
