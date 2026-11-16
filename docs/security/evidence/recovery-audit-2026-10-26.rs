//! Isolated diagnostic for two recovery confirmation counterexamples.
//! A successful run confirms the observed defects, not the recovery invariant.
use babylon60::secure_fs::{
    EffectTxOrchestrator, EffectTxState, EffectType, NativeSecureFs, ReconciledRecovery,
    SecureFsBackend, WalRecord, WalRecordState,
};
use std::fs::{self, File};
use std::os::fd::{AsRawFd, FromRawFd};

struct Lab(std::path::PathBuf);

impl Lab {
    fn new() -> Self {
        let base = std::env::temp_dir();
        for sequence in 0..1000 {
            let path = base.join(format!(
                "b60-recovery-audit-{}-{sequence}",
                std::process::id()
            ));
            match fs::create_dir(&path) {
                Ok(()) => return Self(path),
                Err(error) if error.kind() == std::io::ErrorKind::AlreadyExists => continue,
                Err(error) => panic!("cannot create isolated lab: {error}"),
            }
        }
        panic!("cannot allocate isolated lab");
    }
}

impl Drop for Lab {
    fn drop(&mut self) {
        let _ = fs::remove_dir_all(&self.0);
    }
}

fn main() {
    let lab = Lab::new();
    let target = lab.0.join("target.txt");
    fs::write(&target, b"untouched-original").unwrap();
    let root_handle = File::open(&lab.0).unwrap();
    let (fd, identity) =
        NativeSecureFs::pin_object(root_handle.as_raw_fd(), "target.txt", [0x71; 32]).unwrap();
    drop(unsafe { File::from_raw_fd(fd) });
    let orchestrator = EffectTxOrchestrator::<NativeSecureFs>::new(&lab.0).unwrap();

    // No durable intent and no delete attempt; the original bytes remain intact.
    let unknown_nonce = [0x81; 32];
    assert!(orchestrator.get_wal_record(&unknown_nonce).is_none());
    let status = orchestrator
        .recover_quarantined(&unknown_nonce, &identity)
        .unwrap();
    let original = fs::read(&target).unwrap();
    println!(
        "REC_NO_INTENT status={status:?} wal_present={} original_bytes_unchanged={}",
        orchestrator.get_wal_record(&unknown_nonce).is_some(),
        original == b"untouched-original"
    );
    assert_eq!(status, EffectTxState::Committed);
    assert_eq!(original, b"untouched-original");

    // Reserve only; a different actor renames the object without executing Delete.
    let reserved_nonce = [0x82; 32];
    orchestrator
        .append_wal_record(WalRecord::new(
            WalRecordState::AttemptReserved,
            EffectType::Delete,
            orchestrator.get_epoch(),
            reserved_nonce,
            identity.dev,
            identity.ino,
            identity.pre_hash,
            [0; 32],
        ))
        .unwrap();
    let relocated = lab.0.join("renamed-not-deleted.txt");
    fs::rename(&target, &relocated).unwrap();
    let reconciled = orchestrator
        .reconcile_wal_entry(root_handle.as_raw_fd(), "target.txt", &reserved_nonce)
        .unwrap();
    println!(
        "REC_RENAME_ONLY status={reconciled:?} original_object_exists={} original_bytes_unchanged={}",
        relocated.exists(),
        fs::read(&relocated).unwrap() == b"untouched-original"
    );
    assert!(matches!(
        reconciled,
        ReconciledRecovery::ReconciledCommitted { .. }
    ));
    assert_eq!(fs::read(&relocated).unwrap(), b"untouched-original");
}
