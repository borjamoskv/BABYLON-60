//! FL-REC-01 regressions: recovery cannot turn missing evidence into success.
//! All effects and witnesses are confined to independently inspected test files.

use babylon60::secure_fs::{
    EffectTxOrchestrator, EffectTxState, EffectType, NativeSecureFs, ObjectIdentity,
    ReconciledRecovery, SecureFsBackend, SecureFsError, VerifiedTx, WalRecord, WalRecordState,
};
use std::fs::{self, File};
use std::os::fd::{AsRawFd, FromRawFd, RawFd};
use std::path::{Path, PathBuf};

const PAYLOAD: &[u8] = b"independently-observed-original";
const NONCE: [u8; 32] = [0x81; 32];

struct Lab {
    path: PathBuf,
    root: File,
    identity: ObjectIdentity,
}

impl Lab {
    fn new() -> Self {
        let path = std::env::temp_dir().join(format!(
            "b60-fl-rec01-{}-{}",
            std::process::id(),
            rand::random::<u64>()
        ));
        fs::create_dir(&path).unwrap();
        fs::write(path.join("target"), PAYLOAD).unwrap();
        let root = File::open(&path).unwrap();
        let (fd, identity) =
            NativeSecureFs::pin_object(root.as_raw_fd(), "target", [0x71; 32]).unwrap();
        drop(unsafe { File::from_raw_fd(fd) });
        Self {
            path,
            root,
            identity,
        }
    }

    fn orchestrator(&self) -> EffectTxOrchestrator<NativeSecureFs> {
        EffectTxOrchestrator::new(&self.path).unwrap()
    }

    fn record(&self, state: WalRecordState) -> WalRecord {
        WalRecord::new(
            state,
            EffectType::Delete,
            1,
            NONCE,
            self.identity.locator.dev,
            self.identity.locator.ino,
            self.identity.state.hash,
            [0; 32],
        )
    }

    fn assert_original(&self, path: &Path) {
        assert_eq!(fs::read(path).unwrap(), PAYLOAD);
        use std::os::unix::fs::MetadataExt;
        let metadata = fs::metadata(path).unwrap();
        assert_eq!(metadata.dev(), self.identity.locator.dev);
        assert_eq!(metadata.ino(), self.identity.locator.ino);
    }
}

impl Drop for Lab {
    fn drop(&mut self) {
        let _ = fs::remove_dir_all(&self.path);
    }
}

#[test]
fn missing_quarantine_without_intent_never_confirms_an_intact_target() {
    let lab = Lab::new();
    let orch = lab.orchestrator();
    let result = orch.recover_quarantined(&NONCE, &lab.identity);
    lab.assert_original(&lab.path.join("target"));
    assert!(orch.get_wal_record(&NONCE).is_none());
    assert!(
        matches!(result, Err(SecureFsError::InvalidStateTransition(_))),
        "{result:?}"
    );
}

#[test]
fn missing_quarantine_keeps_pending_intent_ambiguous_and_durable() {
    for state in [
        WalRecordState::AttemptReserved,
        WalRecordState::OutcomeUnknown,
    ] {
        let lab = Lab::new();
        let orch = lab.orchestrator();
        let pending = lab.record(state);
        orch.append_wal_record(pending.clone()).unwrap();
        let result = orch.recover_quarantined(&NONCE, &lab.identity);
        lab.assert_original(&lab.path.join("target"));
        assert_eq!(orch.get_wal_record(&NONCE), Some(pending.clone()));
        assert!(
            matches!(
                result,
                Err(SecureFsError::AmbiguousOutcomeRequiresReconciliation { nonce: NONCE, state: observed }) if observed == state
            ),
            "{result:?}"
        );
        drop(orch);
        assert_eq!(lab.orchestrator().get_wal_record(&NONCE), Some(pending));
    }
}

#[test]
fn absent_original_after_external_rename_or_unlink_is_not_a_delete_receipt() {
    for state in [
        WalRecordState::AttemptReserved,
        WalRecordState::OutcomeUnknown,
    ] {
        for rename_only in [true, false] {
            let lab = Lab::new();
            let orch = lab.orchestrator();
            let pending = lab.record(state);
            orch.append_wal_record(pending.clone()).unwrap();
            if rename_only {
                fs::rename(lab.path.join("target"), lab.path.join("relocated")).unwrap();
            } else {
                fs::remove_file(lab.path.join("target")).unwrap();
            }
            drop(orch);
            let recovered = lab.orchestrator();
            let result = recovered
                .reconcile_wal_entry(lab.root.as_raw_fd(), "target", &NONCE)
                .unwrap();
            if rename_only {
                lab.assert_original(&lab.path.join("relocated"));
            }
            assert!(!lab.path.join("target").exists());
            assert!(
                matches!(result, ReconciledRecovery::OutcomeRemainsAmbiguous { .. }),
                "{result:?}"
            );
            assert_eq!(recovered.get_wal_record(&NONCE), Some(pending.clone()));
            drop(recovered);
            assert_eq!(lab.orchestrator().get_wal_record(&NONCE), Some(pending));
        }
    }
}

#[test]
fn known_receipt_must_match_delete_effect_identity_and_both_hashes() {
    for mismatch in 0..5 {
        let lab = Lab::new();
        let orch = lab.orchestrator();
        let effect = if mismatch == 0 {
            EffectType::Mutate
        } else {
            EffectType::Delete
        };
        let record = WalRecord::new(
            WalRecordState::OutcomeKnown,
            effect,
            1,
            NONCE,
            lab.identity
                .locator
                .dev
                .wrapping_add(u64::from(mismatch == 1)),
            lab.identity
                .locator
                .ino
                .wrapping_add(u64::from(mismatch == 2)),
            if mismatch == 3 {
                [0xEE; 32]
            } else {
                lab.identity.state.hash
            },
            if mismatch == 4 { [0xDD; 32] } else { [0; 32] },
        );
        orch.append_wal_record(record.clone()).unwrap();
        let result = orch.recover_quarantined(&NONCE, &lab.identity);
        lab.assert_original(&lab.path.join("target"));
        assert!(
            matches!(result, Err(SecureFsError::InvalidStateTransition(_))),
            "mismatch {mismatch}: {result:?}"
        );
        assert_eq!(orch.get_wal_record(&NONCE), Some(record));
    }
}

#[test]
fn verified_quarantine_recovers_once_and_reuses_the_durable_receipt() {
    let lab = Lab::new();
    let orch = lab.orchestrator();
    orch.append_wal_record(lab.record(WalRecordState::AttemptReserved))
        .unwrap();
    let name = format!("del_{}", hex::encode(NONCE));
    NativeSecureFs::quarantine(
        lab.root.as_raw_fd(),
        "target",
        orch.quarantine.dir_fd,
        &name,
    )
    .unwrap();
    lab.assert_original(&orch.quarantine.dir_path.join(&name));
    assert_eq!(
        orch.recover_quarantined(&NONCE, &lab.identity).unwrap(),
        EffectTxState::Committed
    );
    assert!(!lab.path.join("target").exists());
    assert!(!orch.quarantine.dir_path.join(&name).exists());
    let receipt = orch.get_wal_record(&NONCE).unwrap();
    assert_eq!(receipt.state, WalRecordState::OutcomeKnown);
    assert_eq!(receipt.target_ino, lab.identity.locator.ino);
    drop(orch);
    let recovered = lab.orchestrator();
    assert_eq!(
        recovered
            .recover_quarantined(&NONCE, &lab.identity)
            .unwrap(),
        EffectTxState::Committed
    );
    assert_eq!(recovered.get_wal_record(&NONCE), Some(receipt));
    assert!(!lab.path.join("target").exists());
}

#[test]
fn unresolved_quarantine_symlink_does_not_confirm_or_destroy_its_target() {
    for destination in ["target", "nonexistent"] {
        let lab = Lab::new();
        let orch = lab.orchestrator();
        let pending = lab.record(WalRecordState::AttemptReserved);
        orch.append_wal_record(pending.clone()).unwrap();
        let name = format!("del_{}", hex::encode(NONCE));
        let link = orch.quarantine.dir_path.join(name);
        std::os::unix::fs::symlink(lab.path.join(destination), &link).unwrap();
        let result = orch.recover_quarantined(&NONCE, &lab.identity);
        assert!(
            matches!(result, Err(SecureFsError::SymlinkEscapeAttempt)),
            "{destination}: {result:?}"
        );
        assert!(fs::symlink_metadata(&link)
            .unwrap()
            .file_type()
            .is_symlink());
        lab.assert_original(&lab.path.join("target"));
        assert_eq!(orch.get_wal_record(&NONCE), Some(pending));
    }
}

#[test]
fn unchanged_preimage_reconciles_as_not_applied_without_confirmation() {
    let lab = Lab::new();
    let orch = lab.orchestrator();
    let pending = lab.record(WalRecordState::AttemptReserved);
    orch.append_wal_record(pending.clone()).unwrap();
    let result = orch
        .reconcile_wal_entry(lab.root.as_raw_fd(), "target", &NONCE)
        .unwrap();
    assert_eq!(
        result,
        ReconciledRecovery::ReconciledNotApplied {
            prior_wal_state: WalRecordState::AttemptReserved
        }
    );
    lab.assert_original(&lab.path.join("target"));
    assert_eq!(orch.get_wal_record(&NONCE), Some(pending));
}

#[test]
fn receipt_persistence_failure_never_reports_committed() {
    let lab = Lab::new();
    let orch = lab.orchestrator();
    let pending = lab.record(WalRecordState::AttemptReserved);
    orch.append_wal_record(pending.clone()).unwrap();
    let name = format!("del_{}", hex::encode(NONCE));
    NativeSecureFs::quarantine(
        lab.root.as_raw_fd(),
        "target",
        orch.quarantine.dir_fd,
        &name,
    )
    .unwrap();
    let wal_path = orch.quarantine.dir_path.join(".effect_wal.bin");
    fs::remove_file(&wal_path).unwrap();
    fs::create_dir(&wal_path).unwrap();
    let result = orch.recover_quarantined(&NONCE, &lab.identity);
    assert!(
        matches!(
            result,
            Err(SecureFsError::LedgerError(_)) | Err(SecureFsError::IoError(_))
        ),
        "{result:?}"
    );
    assert_eq!(orch.get_wal_record(&NONCE), Some(pending));
    assert!(wal_path.is_dir());
}

#[test]
fn bounded_recovery_stress_has_no_unwitnessed_confirmations() {
    const WARMUP: usize = 10;
    const MEASURED: usize = 128;
    let mut false_recoveries = 0;
    let mut false_delete_receipts = 0;
    for cycle in 0..WARMUP + MEASURED {
        let lab = Lab::new();
        let orch = lab.orchestrator();
        let recovery = orch.recover_quarantined(&NONCE, &lab.identity);
        lab.assert_original(&lab.path.join("target"));
        orch.append_wal_record(lab.record(WalRecordState::AttemptReserved))
            .unwrap();
        fs::rename(lab.path.join("target"), lab.path.join("relocated")).unwrap();
        let reconciliation = orch
            .reconcile_wal_entry(lab.root.as_raw_fd(), "target", &NONCE)
            .unwrap();
        lab.assert_original(&lab.path.join("relocated"));
        if cycle >= WARMUP {
            false_recoveries += usize::from(matches!(recovery, Ok(EffectTxState::Committed)));
            false_delete_receipts += usize::from(matches!(
                reconciliation,
                ReconciledRecovery::ReconciledCommitted { .. }
                    | ReconciledRecovery::AlreadyKnown { .. }
            ));
        }
    }
    eprintln!("FL-REC-01: warmup={WARMUP} measured={MEASURED} false_recoveries={false_recoveries} false_delete_receipts={false_delete_receipts}");
    assert_eq!((false_recoveries, false_delete_receipts), (0, 0));
}

#[test]
fn quarantined_object_without_intent_is_preserved_without_confirmation() {
    let lab = Lab::new();
    let orch = lab.orchestrator();
    let name = format!("del_{}", hex::encode(NONCE));
    NativeSecureFs::quarantine(
        lab.root.as_raw_fd(),
        "target",
        orch.quarantine.dir_fd,
        &name,
    )
    .unwrap();
    let quarantined = orch.quarantine.dir_path.join(name);
    let result = orch.recover_quarantined(&NONCE, &lab.identity);
    assert!(
        matches!(result, Err(SecureFsError::InvalidStateTransition(_))),
        "{result:?}"
    );
    lab.assert_original(&quarantined);
    assert!(!lab.path.join("target").exists());
    assert!(orch.get_wal_record(&NONCE).is_none());
}

/// Test-only fault injection after a real unlink and physical observation.
/// Replacing only the owned directory descriptor makes its next fsync fail.
struct DirectorySyncFailure;

impl SecureFsBackend for DirectorySyncFailure {
    fn pin_object(
        root_fd: RawFd,
        rel_path: &str,
        capability_root_id: [u8; 32],
    ) -> Result<(RawFd, ObjectIdentity), SecureFsError> {
        NativeSecureFs::pin_object(root_fd, rel_path, capability_root_id)
    }

    fn quarantine(
        parent_fd: RawFd,
        basename: &str,
        quarantine_fd: RawFd,
        nonce_name: &str,
    ) -> Result<(), SecureFsError> {
        NativeSecureFs::quarantine(parent_fd, basename, quarantine_fd, nonce_name)
    }

    fn verify_quarantined(
        quarantine_fd: RawFd,
        nonce_name: &str,
        expected: &ObjectIdentity,
    ) -> Result<VerifiedTx, SecureFsError> {
        NativeSecureFs::verify_quarantined(quarantine_fd, nonce_name, expected)
    }

    fn destroy_quarantined(quarantine_fd: RawFd, vtx: VerifiedTx) -> Result<(), SecureFsError> {
        NativeSecureFs::destroy_quarantined(quarantine_fd, vtx)?;
        let mut pipe = [-1; 2];
        assert_eq!(unsafe { libc::pipe(pipe.as_mut_ptr()) }, 0);
        let read = unsafe { File::from_raw_fd(pipe[0]) };
        let write = unsafe { File::from_raw_fd(pipe[1]) };
        // dup2 atomically replaces this orchestrator's descriptor, without a
        // close/reuse window that could close another concurrently allocated fd.
        assert_eq!(
            unsafe { libc::dup2(read.as_raw_fd(), quarantine_fd) },
            quarantine_fd
        );
        drop((read, write));
        Ok(())
    }

    fn secure_mutate(
        root_fd: RawFd,
        rel_path: &str,
        authorized_identity: &ObjectIdentity,
        payload: &[u8],
    ) -> Result<[u8; 32], SecureFsError> {
        NativeSecureFs::secure_mutate(root_fd, rel_path, authorized_identity, payload)
    }
}

#[test]
fn directory_sync_failure_cannot_persist_a_known_receipt_before_effect_durability() {
    let lab = Lab::new();
    let orch = EffectTxOrchestrator::<DirectorySyncFailure>::new(&lab.path).unwrap();
    let pending = lab.record(WalRecordState::AttemptReserved);
    orch.append_wal_record(pending.clone()).unwrap();
    let name = format!("del_{}", hex::encode(NONCE));
    NativeSecureFs::quarantine(
        lab.root.as_raw_fd(),
        "target",
        orch.quarantine.dir_fd,
        &name,
    )
    .unwrap();
    let quarantined = orch.quarantine.dir_path.join(name);
    let result = orch.recover_quarantined(&NONCE, &lab.identity);
    assert!(
        matches!(result, Err(SecureFsError::IoError(_))),
        "{result:?}"
    );
    assert!(!lab.path.join("target").exists());
    assert!(!quarantined.exists());
    drop(orch);
    // Inspect the reloaded durable record, not merely the old in-memory map.
    let recovered = lab.orchestrator();
    assert_eq!(recovered.get_wal_record(&NONCE), Some(pending));
}
