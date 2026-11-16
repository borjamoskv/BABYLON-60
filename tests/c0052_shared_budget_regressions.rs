//! C0052 regression: two broker instances over one capability root must share the
//! effect budget. Isolated temporary fixture; no production effects.
use babylon60::secure_fs::{
    AuthorityContext, EffectBudgetPolicy, EffectTxOrchestrator, EffectTxState, EffectType,
    NativeSecureFs, ObjectIdentity, SecureFsBackend, SecureFsError,
};
use std::fs::File;
use std::os::fd::AsRawFd;
use std::path::PathBuf;

struct Root {
    path: PathBuf,
}
impl Drop for Root {
    fn drop(&mut self) {
        let _ = std::fs::remove_dir_all(&self.path);
    }
}

fn pin(dir: &File) -> ObjectIdentity {
    let (fd, identity) = NativeSecureFs::pin_object(dir.as_raw_fd(), "target", [7; 32]).unwrap();
    unsafe {
        libc::close(fd);
    }
    identity
}

#[test]
fn two_instances_share_effect_budget() {
    let path = std::env::temp_dir().join(format!(
        "c0052_budget_{}_{}",
        std::process::id(),
        std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .unwrap()
            .as_nanos()
    ));
    std::fs::create_dir(&path).unwrap();
    let _guard = Root { path: path.clone() };
    std::fs::write(path.join("target"), b"before").unwrap();
    let dir = File::open(&path).unwrap();

    let a = EffectTxOrchestrator::<NativeSecureFs>::new(&path).unwrap();
    let b = EffectTxOrchestrator::<NativeSecureFs>::new(&path).unwrap();
    let policy = |identity: &ObjectIdentity| EffectBudgetPolicy {
        max_effects: 1,
        max_total_bytes: 1024,
        allowed_targets: vec![(identity.locator.dev, identity.locator.ino)],
    };
    let identity = pin(&dir);
    a.set_budget_policy([7; 32], policy(&identity)).unwrap();
    b.set_budget_policy([7; 32], policy(&identity)).unwrap();

    // Primer efecto por A: consume el único presupuesto de la época.
    let auth_a = AuthorityContext {
        authority_id: [7; 32],
        epoch: a.get_epoch(),
        effect: EffectType::Mutate,
        nonce: [1; 32],
    };
    let first = a
        .secure_mutate_scoped(dir.as_raw_fd(), "target", &auth_a, &identity, b"one")
        .unwrap();
    assert_eq!(first.0, EffectTxState::Committed);

    // Segundo efecto por B, con identidad re-pineada al estado actual.
    // Debe rechazarse por presupuesto agotado (max_effects = 1).
    let identity_now = pin(&dir);
    let auth_b = AuthorityContext {
        authority_id: [7; 32],
        epoch: b.get_epoch(),
        effect: EffectType::Mutate,
        nonce: [2; 32],
    };
    let second = b.secure_mutate_scoped(dir.as_raw_fd(), "target", &auth_b, &identity_now, b"two");
    assert!(
        matches!(second, Err(SecureFsError::BudgetExceeded(_))),
        "C0052: la segunda instancia excedió el presupuesto compartido: {:?}",
        second.map(|r| r.0)
    );
    assert_eq!(std::fs::read(path.join("target")).unwrap(), b"one");
}
