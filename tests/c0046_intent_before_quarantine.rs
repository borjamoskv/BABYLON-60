//! C0046 reproduction: a stage failure after quarantine must conserve or recover the file.
//! Injects a failure in the budget-charge stage (after quarantine, before the durable
//! AttemptReserved intent) by making .budget_usage.bin read-only. Public APIs only.
//! Isolated temporary fixture; no production effects.
use babylon60::secure_fs::{
    AuthorityContext, EffectBudgetPolicy, EffectTxOrchestrator, EffectType, NativeSecureFs,
    ObjectIdentity, SecureFsBackend,
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
        let budget = self.path.join(".babylon/quarantine/.budget_usage.bin");
        let _ = std::fs::set_permissions(&budget, std::fs::Permissions::from_mode(0o600));
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
fn stage_failure_after_quarantine_conserves_or_recovers_file() {
    let path = std::env::temp_dir().join(format!(
        "c0046_intent_{}_{}",
        std::process::id(),
        std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .unwrap()
            .as_nanos()
    ));
    std::fs::create_dir(&path).unwrap();
    let _guard = Root { path: path.clone() };
    std::fs::write(path.join("target"), b"precious").unwrap();
    let dir = File::open(&path).unwrap();
    let identity = pin(&dir);

    // Crear la cuarentena con su contenedor de presupuesto ya existente y de solo lectura.
    let broker = EffectTxOrchestrator::<NativeSecureFs>::new(&path).unwrap();
    let budget = path.join(".babylon/quarantine/.budget_usage.bin");
    std::fs::write(&budget, b"").unwrap();
    std::fs::set_permissions(&budget, std::fs::Permissions::from_mode(0o400)).unwrap();
    drop(broker);
    let broker = EffectTxOrchestrator::<NativeSecureFs>::new(&path).unwrap();
    broker
        .set_budget_policy(
            [7; 32],
            EffectBudgetPolicy {
                max_effects: 2,
                max_total_bytes: 1024,
                allowed_targets: vec![(identity.locator.dev, identity.locator.ino)],
            },
        )
        .unwrap();

    let nonce = [5; 32];
    let auth = AuthorityContext {
        authority_id: [7; 32],
        epoch: broker.get_epoch(),
        effect: EffectType::Delete,
        nonce,
    };
    let result = broker.secure_delete_scoped(dir.as_raw_fd(), "target", &auth, &identity, &nonce);
    assert!(
        matches!(
            result,
            Err(babylon60::secure_fs::SecureFsError::LedgerError(_))
        ),
        "precondición: la etapa de cargo debe fallar antes de la cuarentena: {:?}",
        result
    );

    let conserved = path.join("target").exists();
    let recovered = broker.recover_quarantined(&nonce, &identity).is_ok();
    assert!(
        conserved || recovered,
        "C0046: fallo tras cuarentena sin intención durable: el archivo no está en su sitio ni es recuperable"
    );
}

#[test]
fn mismatched_tx_nonce_is_rejected_before_any_effect() {
    // La cuarentena se nombra con tx_nonce y la intención durable con auth.nonce; si difieren,
    // recover_quarantined no puede enlazarlas. Debe rechazarse antes de mover nada.
    let path = std::env::temp_dir().join(format!(
        "c0046_nonce_{}_{}",
        std::process::id(),
        std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .unwrap()
            .as_nanos()
    ));
    std::fs::create_dir(&path).unwrap();
    let _guard = Root { path: path.clone() };
    std::fs::write(path.join("target"), b"precious").unwrap();
    let dir = File::open(&path).unwrap();
    let identity = pin(&dir);
    let broker = EffectTxOrchestrator::<NativeSecureFs>::new(&path).unwrap();
    broker
        .set_budget_policy(
            [7; 32],
            EffectBudgetPolicy {
                max_effects: 2,
                max_total_bytes: 1024,
                allowed_targets: vec![(identity.locator.dev, identity.locator.ino)],
            },
        )
        .unwrap();
    let auth = AuthorityContext {
        authority_id: [7; 32],
        epoch: broker.get_epoch(),
        effect: EffectType::Delete,
        nonce: [5; 32],
    };
    let result = broker.secure_delete_scoped(dir.as_raw_fd(), "target", &auth, &identity, &[9; 32]);
    assert!(
        result.is_err(),
        "C0046: tx_nonce distinto de auth.nonce aceptado: {:?}",
        result
    );
    assert_eq!(std::fs::read(path.join("target")).unwrap(), b"precious");
}
