//! Isolated filesystem witnesses; no hardware authorization or production effects.
use babylon60::secure_fs::{
    AuthorityContext, EffectBudgetPolicy, EffectTxOrchestrator, EffectTxState, EffectType,
    NativeSecureFs, ObjectIdentity, SecureFsBackend, SecureFsError,
};
use std::fs::File;
use std::os::fd::AsRawFd;
use std::path::PathBuf;

struct Lab {
    path: PathBuf,
    dir: File,
    broker: EffectTxOrchestrator,
    identity: ObjectIdentity,
}
impl Lab {
    fn new() -> Self {
        let path = std::env::temp_dir().join(format!(
            "a02_auth_{}_{}",
            std::process::id(),
            rand::random::<u64>()
        ));
        std::fs::create_dir(&path).unwrap();
        std::fs::write(path.join("target"), b"before").unwrap();
        let dir = File::open(&path).unwrap();
        let (fd, identity) =
            NativeSecureFs::pin_object(dir.as_raw_fd(), "target", [7; 32]).unwrap();
        unsafe {
            libc::close(fd);
        }
        let broker = EffectTxOrchestrator::new(&path).unwrap();
        Self {
            path,
            dir,
            broker,
            identity,
        }
    }
    fn permit(&self) {
        self.broker
            .set_budget_policy(
                [7; 32],
                EffectBudgetPolicy {
                    max_effects: 2,
                    max_total_bytes: 64,
                    allowed_targets: vec![(self.identity.locator.dev, self.identity.locator.ino)],
                },
            )
            .unwrap();
    }
    fn auth(&self, effect: EffectType, nonce: [u8; 32]) -> AuthorityContext {
        AuthorityContext {
            authority_id: [7; 32],
            epoch: self.broker.get_epoch(),
            effect,
            nonce,
        }
    }
    fn unchanged(&self) {
        assert_eq!(std::fs::read(self.path.join("target")).unwrap(), b"before");
    }
}
impl Drop for Lab {
    fn drop(&mut self) {
        std::fs::remove_dir_all(&self.path).unwrap();
    }
}

#[test]
fn zero_nonce_cannot_mutate_or_delete_even_with_policy() {
    for effect in [EffectType::Mutate, EffectType::Delete] {
        let lab = Lab::new();
        lab.permit();
        let auth = lab.auth(effect, [0; 32]);
        let denied = match effect {
            EffectType::Mutate => lab
                .broker
                .secure_mutate_scoped(
                    lab.dir.as_raw_fd(),
                    "target",
                    &auth,
                    &lab.identity,
                    b"unauthorized",
                )
                .is_err(),
            _ => lab
                .broker
                .secure_delete_scoped(
                    lab.dir.as_raw_fd(),
                    "target",
                    &auth,
                    &lab.identity,
                    &[9; 32],
                )
                .is_err(),
        };
        assert!(
            denied,
            "zero nonce must never disable authorization accounting"
        );
        lab.unchanged();
    }
}

#[test]
fn missing_policy_cannot_mutate_or_delete() {
    for effect in [EffectType::Mutate, EffectType::Delete] {
        let lab = Lab::new();
        let auth = lab.auth(effect, [8; 32]);
        let denied = match effect {
            EffectType::Mutate => lab
                .broker
                .secure_mutate_scoped(
                    lab.dir.as_raw_fd(),
                    "target",
                    &auth,
                    &lab.identity,
                    b"unauthorized",
                )
                .is_err(),
            _ => lab
                .broker
                .secure_delete_scoped(
                    lab.dir.as_raw_fd(),
                    "target",
                    &auth,
                    &lab.identity,
                    &[8; 32],
                )
                .is_err(),
        };
        assert!(denied, "missing policy is not authority");
        lab.unchanged();
    }
}

#[test]
fn legacy_wrappers_cannot_invent_authority() {
    let lab = Lab::new();
    lab.permit();
    assert!(lab
        .broker
        .secure_mutate(
            lab.dir.as_raw_fd(),
            "target",
            &lab.identity,
            b"unauthorized"
        )
        .is_err());
    assert!(lab
        .broker
        .secure_delete(lab.dir.as_raw_fd(), "target", &lab.identity, &[8; 32])
        .is_err());
    lab.unchanged();
}

#[test]
fn explicit_authorization_commits_and_replay_preserves_witness() {
    // Warmup followed by repeated independent transactions, including broker restart.
    for _ in 0..9 {
        let lab = Lab::new();
        lab.permit();
        let auth = lab.auth(EffectType::Mutate, [8; 32]);
        assert_eq!(
            lab.broker
                .secure_mutate_scoped(
                    lab.dir.as_raw_fd(),
                    "target",
                    &auth,
                    &lab.identity,
                    b"after"
                )
                .unwrap()
                .0,
            EffectTxState::Committed
        );
        let reopened = EffectTxOrchestrator::<NativeSecureFs>::new(&lab.path).unwrap();
        assert!(matches!(
            reopened.secure_mutate_scoped(
                lab.dir.as_raw_fd(),
                "target",
                &auth,
                &lab.identity,
                b"replay"
            ),
            Err(SecureFsError::NonceReplayDetected { .. })
        ));
        assert_eq!(std::fs::read(lab.path.join("target")).unwrap(), b"after");
    }
}
