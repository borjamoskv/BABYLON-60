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
    let first =
        broker.secure_mutate_scoped(dir.as_raw_fd(), "target", &first_auth, &identity, b"x");
    assert!(
        first.is_err(),
        "precondición: la ejecución debe fallar tras la reserva"
    );

    // Restaurar escritura: el intento fallido ya consumió el único presupuesto.
    std::fs::set_permissions(path.join("target"), std::fs::Permissions::from_mode(0o644)).unwrap();
    let now = pin(&dir);
    let second_auth = AuthorityContext {
        authority_id: [7; 32],
        epoch: broker.get_epoch(),
        effect: EffectType::Mutate,
        nonce: [4; 32],
    };
    let second =
        broker.secure_mutate_scoped(dir.as_raw_fd(), "target", &second_auth, &now, b"next");
    assert!(
        matches!(second, Err(SecureFsError::BudgetExceeded(_))),
        "C0053: ejecución fallida tras reserva no consumió presupuesto: {:?}",
        second.map(|r| r.0)
    );
}

/// Número de cargos persistidos (registros de 48 bytes).
fn charges(path: &std::path::Path) -> usize {
    std::fs::read(path.join(".babylon/quarantine/.budget_usage.bin"))
        .map(|b| b.len() / 48)
        .unwrap_or(0)
}

#[test]
fn failed_reservation_then_same_nonce_retry_charges_once() {
    for effect in [EffectType::Mutate, EffectType::Delete] {
        let path = std::env::temp_dir().join(format!(
            "c0053_retry_{}_{:?}_{}",
            std::process::id(),
            effect,
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
                    max_effects: 5,
                    max_total_bytes: 1024,
                    allowed_targets: vec![(identity.locator.dev, identity.locator.ino)],
                },
            )
            .unwrap();
        let nonce = [6; 32];
        let auth = AuthorityContext {
            authority_id: [7; 32],
            epoch: broker.get_epoch(),
            effect,
            nonce,
        };
        let attempt = || match effect {
            EffectType::Mutate => broker
                .secure_mutate_scoped(dir.as_raw_fd(), "target", &auth, &identity, b"after")
                .map(|r| r.0),
            _ => broker.secure_delete_scoped(dir.as_raw_fd(), "target", &auth, &identity, &nonce),
        };

        // Fallo real en el paso de reserva: el WAL no admite escritura.
        let wal = path.join(".babylon/quarantine/.effect_wal.bin");
        if !wal.exists() {
            std::fs::write(&wal, b"").unwrap();
        }
        std::fs::set_permissions(&wal, std::fs::Permissions::from_mode(0o400)).unwrap();
        assert!(attempt().is_err(), "precondición: la reserva debe fallar");
        std::fs::set_permissions(&wal, std::fs::Permissions::from_mode(0o600)).unwrap();

        // Reintento con el mismo nonce: el efecto se aplica y se cobra una sola vez.
        assert!(
            attempt().is_ok(),
            "el reintento debe completarse: {:?}",
            effect
        );
        assert_eq!(
            charges(&path),
            1,
            "C0053: {:?} cobrado dos veces tras un fallo en la reserva",
            effect
        );
    }
}
