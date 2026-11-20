//! C0053 regression: the effect budget must be charged before the irreversible syscall.
//! If execution fails after reservation, the attempt still consumes the budget (fail-closed),
//! so a crash-interrupted effect can never run without a durable charge.
//! Isolated temporary fixture; no production effects.
use babylon60::secure_fs::{
    AuthorityContext, EffectBudgetPolicy, EffectTxOrchestrator, EffectType, NativeSecureFs,
    ObjectIdentity, SecureFsBackend, SecureFsError,
};
use std::fs::File;
use std::os::fd::AsRawFd;
use std::os::unix::fs::PermissionsExt;
use std::path::PathBuf;

struct Root {
    path: PathBuf,
}
impl Drop for Root {
    fn drop(&mut self) {
        let _ = std::fs::set_permissions(
            self.path.join("target"),
            std::fs::Permissions::from_mode(0o644),
        );
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
fn failed_execution_after_reservation_still_consumes_budget() {
    let path = std::env::temp_dir().join(format!(
        "c0053_budget_{}_{}",
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
    let identity = pin(&dir);

    let broker = EffectTxOrchestrator::<NativeSecureFs>::new(&path).unwrap();
    broker
        .set_budget_policy(
            [7; 32],
            EffectBudgetPolicy {
                max_effects: 1,
                max_total_bytes: 1024,
                allowed_targets: vec![(identity.locator.dev, identity.locator.ino)],
            },
        )
        .unwrap();

    // Forzar que la ejecución falle tras la reserva: el objeto no admite escritura.
    std::fs::set_permissions(path.join("target"), std::fs::Permissions::from_mode(0o400)).unwrap();
    let first_auth = AuthorityContext {
        authority_id: [7; 32],
        epoch: broker.get_epoch(),
        effect: EffectType::Mutate,
        nonce: [3; 32],
    };
    let first = broker.secure_mutate_scoped(dir.as_raw_fd(), "target", &first_auth, &identity, b"x");
    assert!(first.is_err(), "precondición: la ejecución debe fallar tras la reserva");

    // Restaurar escritura: el intento fallido ya consumió el único presupuesto.
    std::fs::set_permissions(path.join("target"), std::fs::Permissions::from_mode(0o644)).unwrap();
    let now = pin(&dir);
    let second_auth = AuthorityContext {
        authority_id: [7; 32],
        epoch: broker.get_epoch(),
        effect: EffectType::Mutate,
        nonce: [4; 32],
    };
    let second = broker.secure_mutate_scoped(dir.as_raw_fd(), "target", &second_auth, &now, b"next");
    assert!(
        matches!(second, Err(SecureFsError::BudgetExceeded(_))),
        "C0053: ejecución fallida tras reserva no consumió presupuesto: {:?}",
        second.map(|r| r.0)
    );
}
