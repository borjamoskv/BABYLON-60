//! # NEMESIS Wave IV — Adversarial Falsification Suite (`FL-013` / `FL-014` / `FL-015` + ECP v2)
//!
//! Implementa los 10 vectores adversariales de la Iteración II:
//! 1. `FL014_RECEIPT_LOSS`       — SIGKILL entre efecto físico y recibo; cero reintentos automáticos ambiguos.
//! 2. `FL014_FENCING_RACE`       — Revocación concurrente y worker suspendido; ningún efecto obsoleto tras ACK.
//! 3. `FL014_HIDDEN_BRANCH`      — Artefacto verificado intenta `WRITE_PROTECTED` fuera del target permitido.
//! 4. `FL014_COMPOSITION`        — Dos efectos permitidos individualmente violan el presupuesto conjunto.
//! 5. `FL013_SAME_INODE_WRITER`  — Escritor concurrente sobre el inodo original; snapshot aislado preserva digest.
//! 6. `FL013_WEAK_SEAL`          — Mapeo compartido previo o sellado insuficiente; rechazo de garantía fuerte.
//! 7. `FL013_DARWIN_IMMUTABLE`   — Propietario intenta depender de `UF_IMMUTABLE` / `mprotect`; degradación explícita.
//! 8. `FL015_TRANSITIVE_DRIFT`   — Dependencia transitiva cambia tras atestación; despliegue rechazado.
//! 9. `FL015_POLICY_ROLLBACK`    — Política antigua o excepción caducada; rechazo del permiso obsoleto.
//! 10. `FL015_RUNTIME_LOAD`      — Carga dinámica (`dlopen`) fuera de clausura autorizada; bloqueo o degradación explícita.

use std::ffi::CString;
use std::os::unix::ffi::OsStrExt;
use std::os::unix::io::RawFd;
use std::path::{Path, PathBuf};
use std::sync::{Arc, Barrier};

use babylon60::secure_fs::{
    AuthorityContext, DeploymentPermit, EffectBudgetPolicy, EffectTxOrchestrator, EffectTxState,
    EffectType, IsolatedSnapshot, IsolationStrength, NativeSecureFs, ObjectIdentity,
    ReconciledRecovery, SecureFsBackend, SecureFsError, VerifiedTx, WalRecord, WalRecordState,
};
use sha2::{Digest, Sha256};

struct Wave4Lab {
    path: PathBuf,
    root_fd: RawFd,
}

impl Wave4Lab {
    fn new(tag: &str) -> Self {
        let p = std::env::temp_dir().join(format!(
            "b60_wave4_{}_{}_{}",
            tag,
            std::process::id(),
            rand::random::<u64>()
        ));
        std::fs::create_dir_all(&p).unwrap();
        let c = CString::new(p.as_os_str().as_bytes()).unwrap();
        let fd =
            unsafe { libc::open(c.as_ptr(), libc::O_RDONLY | libc::O_DIRECTORY | libc::O_CLOEXEC) };
        assert!(fd >= 0, "open Wave4Lab dir failed");
        Self {
            path: p,
            root_fd: fd,
        }
    }

    fn path(&self) -> &Path {
        &self.path
    }
}

impl Drop for Wave4Lab {
    fn drop(&mut self) {
        if self.root_fd >= 0 {
            unsafe { libc::close(self.root_fd) };
            self.root_fd = -1;
        }
        let _ = std::fs::remove_dir_all(&self.path);
    }
}

// ===========================================================================
// 1. FL014_RECEIPT_LOSS (P0): SIGKILL entre efecto y recibo; cero reintentos ciegos
// ===========================================================================

#[test]
fn fl014_receipt_loss_forbids_blind_retry_and_reconciles() {
    let lab = Wave4Lab::new("fl014_receipt_loss");
    let target = lab.path().join("ledger_critical.dat");
    let initial_bytes = b"pre_state_v1";
    let mutated_bytes = b"mutated_post_state_v2";
    std::fs::write(&target, initial_bytes).unwrap();

    let cap = [0x41; 32];
    let (fd, id) = NativeSecureFs::pin_object(lab.root_fd, "ledger_critical.dat", cap).unwrap();
    unsafe { libc::close(fd) };

    let nonce = [0x91; 32];
    let expected_post_hash: [u8; 32] = Sha256::digest(mutated_bytes).into();

    // Simulamos exactamente la frontera de fallo SIGKILL después de persistir ATTEMPT_RESERVED
    // y después de que la syscall física escribió el archivo, pero ANTES de persistir OUTCOME_KNOWN:
    {
        let orch_before_crash = EffectTxOrchestrator::<NativeSecureFs>::new(lab.path()).unwrap();
        let reserved = WalRecord::new(
            WalRecordState::AttemptReserved,
            EffectType::Mutate,
            1,
            nonce,
            id.locator.dev,
            id.locator.ino,
            id.state.hash,
            expected_post_hash,
        );
        orch_before_crash.append_wal_record(reserved).unwrap();
        // La syscall física ocurre antes del SIGKILL:
        let actual_post =
            NativeSecureFs::secure_mutate(lab.root_fd, "ledger_critical.dat", &id, mutated_bytes)
                .unwrap();
        assert_eq!(actual_post, expected_post_hash);
        // <--- SIGKILL ocurre aquí antes de escribir WalRecordState::OutcomeKnown
    }

    // Tras reiniciar el proceso, un nuevo orquestador recarga `.effect_wal.bin`
    let orch_recovered = EffectTxOrchestrator::<NativeSecureFs>::new(lab.path()).unwrap();
    let auth = AuthorityContext {
        authority_id: [0x77; 32],
        epoch: 1,
        effect: EffectType::Mutate,
        nonce,
    };

    // Un reintento automático a ciegas DEBE ser rechazado con AmbiguousOutcomeRequiresReconciliation
    let blind_retry = orch_recovered.secure_mutate_scoped(
        lab.root_fd,
        "ledger_critical.dat",
        &auth,
        &id,
        mutated_bytes,
    );
    assert!(
        matches!(
            blind_retry,
            Err(SecureFsError::AmbiguousOutcomeRequiresReconciliation {
                state: WalRecordState::AttemptReserved,
                ..
            })
        ),
        "FL014_RECEIPT_LOSS: blind retry on ATTEMPT_RESERVED must be rejected, got: {:?}",
        blind_retry
    );

    // La reconciliación explícita inspecciona el inodo físico, comprueba que `post_hash` coincide
    // y consolida el recibo a `OUTCOME_KNOWN` sin duplicar la operación.
    let rec_state = orch_recovered
        .reconcile_wal_entry(lab.root_fd, "ledger_critical.dat", &nonce)
        .unwrap();
    assert_eq!(
        rec_state,
        ReconciledRecovery::ReconciledCommitted {
            observed_post_hash: expected_post_hash
        }
    );
    assert_eq!(
        orch_recovered.get_wal_record(&nonce).unwrap().state,
        WalRecordState::OutcomeKnown
    );
}

// ===========================================================================
// 2. FL014_FENCING_RACE (P0): Revocación concurrente y worker suspendido
// ===========================================================================

struct SlowWorkerBackend;

static SLOW_WORKER_ENTERED: std::sync::atomic::AtomicBool =
    std::sync::atomic::AtomicBool::new(false);

impl SecureFsBackend for SlowWorkerBackend {
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
        NativeSecureFs::destroy_quarantined(quarantine_fd, vtx)
    }

    fn secure_mutate(
        root_fd: RawFd,
        rel_path: &str,
        authorized_identity: &ObjectIdentity,
        payload: &[u8],
    ) -> Result<[u8; 32], SecureFsError> {
        SLOW_WORKER_ENTERED.store(true, std::sync::atomic::Ordering::SeqCst);
        std::thread::sleep(std::time::Duration::from_millis(40));
        NativeSecureFs::secure_mutate(root_fd, rel_path, authorized_identity, payload)
    }
}

#[test]
fn fl014_fencing_race_guarantees_no_stale_commit_after_ack() {
    SLOW_WORKER_ENTERED.store(false, std::sync::atomic::Ordering::SeqCst);
    let lab = Wave4Lab::new("fl014_fencing_race");
    let target = lab.path().join("fenced.dat");
    std::fs::write(&target, b"epoch1_initial").unwrap();

    let orch = Arc::new(EffectTxOrchestrator::<SlowWorkerBackend>::new(lab.path()).unwrap());
    let cap = [0x42; 32];
    let (fd, id1) = SlowWorkerBackend::pin_object(lab.root_fd, "fenced.dat", cap).unwrap();
    unsafe { libc::close(fd) };

    let barrier = Arc::new(Barrier::new(2));
    let orch_w1 = Arc::clone(&orch);
    let b_w1 = Arc::clone(&barrier);
    let root_fd = lab.root_fd;
    let id1_clone = id1.clone();

    // Worker 1 entra en época 1 y mantiene el cerrojo de recurso durante la operación en vuelo
    let w1 = std::thread::spawn(move || {
        let auth_e1 = AuthorityContext {
            authority_id: [0x88; 32],
            epoch: 1,
            effect: EffectType::Mutate,
            nonce: [0x11; 32],
        };
        b_w1.wait();
        orch_w1.secure_mutate_scoped(root_fd, "fenced.dat", &auth_e1, &id1_clone, b"epoch1_in_flight")
    });

    barrier.wait();
    while !SLOW_WORKER_ENTERED.load(std::sync::atomic::Ordering::SeqCst) {
        std::thread::yield_now();
    }

    // `revoke_and_fence(2)` DEBE bloquearse hasta que la operación en vuelo de época 1 drene,
    // y sólo entonces persistir época 2 y devolver ACK.
    let acked_epoch = orch.revoke_and_fence(2).unwrap();
    assert_eq!(acked_epoch, 2);

    // Una vez emitido `AckRevocation(r, 2)`, cualquier worker rezagado con `epoch = 1`
    // que intente adquirir el gate de recurso es rechazado inexorablemente (`AuthorityStale`).
    let w1_res = w1.join().unwrap();
    assert!(w1_res.is_ok(), "In-flight op drained before ACK must complete cleanly");

    let (fd2, id2) = SlowWorkerBackend::pin_object(lab.root_fd, "fenced.dat", cap).unwrap();
    unsafe { libc::close(fd2) };
    let stale_worker_auth = AuthorityContext {
        authority_id: [0x88; 32],
        epoch: 1,
        effect: EffectType::Mutate,
        nonce: [0x12; 32],
    };
    let post_ack_attempt = orch.secure_mutate_scoped(
        lab.root_fd,
        "fenced.dat",
        &stale_worker_auth,
        &id2,
        b"illegal_stale_write_after_ack",
    );
    assert!(
        matches!(
            post_ack_attempt,
            Err(SecureFsError::AuthorityStale {
                expected_epoch: 1,
                current_epoch: 2
            })
        ),
        "FL014_FENCING_RACE: no effect with epoch < 2 may commit after AckRevocation(r, 2)"
    );
    assert_eq!(std::fs::read(&target).unwrap(), b"epoch1_in_flight");
}

// ===========================================================================
// 3. FL014_HIDDEN_BRANCH (P0): Artefacto verificado intenta WRITE_PROTECTED
// ===========================================================================

#[test]
fn fl014_hidden_branch_verified_artifact_blocked_on_protected_target() {
    let lab = Wave4Lab::new("fl014_hidden_branch");
    let allowed_file = lab.path().join("sandbox_scratch.dat");
    let protected_file = lab.path().join("write_protected_config.dat");
    std::fs::write(&allowed_file, b"scratch_ok").unwrap();
    std::fs::write(&protected_file, b"immutable_root_config").unwrap();

    let orch = EffectTxOrchestrator::<NativeSecureFs>::new(lab.path()).unwrap();
    let cap = [0x43; 32];
    let (fd_ok, id_ok) =
        NativeSecureFs::pin_object(lab.root_fd, "sandbox_scratch.dat", cap).unwrap();
    unsafe { libc::close(fd_ok) };
    let (fd_prot, id_prot) =
        NativeSecureFs::pin_object(lab.root_fd, "write_protected_config.dat", cap).unwrap();
    unsafe { libc::close(fd_prot) };

    let agent_principal = [0x55; 32];
    orch.set_budget_policy(
        agent_principal,
        EffectBudgetPolicy {
            max_effects: 5,
            max_total_bytes: 4096,
            allowed_targets: vec![(id_ok.locator.dev, id_ok.locator.ino)],
        },
    )
    .unwrap();

    // Rama oculta post-verificación intenta mutar `write_protected_config.dat`
    let hidden_branch_auth = AuthorityContext {
        authority_id: agent_principal,
        epoch: 1,
        effect: EffectType::Mutate,
        nonce: [0x21; 32],
    };
    let res = orch.secure_mutate_scoped(
        lab.root_fd,
        "write_protected_config.dat",
        &hidden_branch_auth,
        &id_prot,
        b"pwned_by_hidden_branch",
    );
    assert!(
        matches!(res, Err(SecureFsError::TargetNotAllowed { .. })),
        "FL014_HIDDEN_BRANCH: write to non-whitelisted protected target must be blocked: {:?}",
        res
    );
    assert_eq!(
        std::fs::read(&protected_file).unwrap(),
        b"immutable_root_config"
    );
}

// ===========================================================================
// 4. FL014_COMPOSITION: Dos efectos permitidos individualmente violan presupuesto conjunto
// ===========================================================================

#[test]
fn fl014_composition_rejects_sequence_exceeding_cumulative_budget() {
    let lab = Wave4Lab::new("fl014_composition");
    let target = lab.path().join("budgeted.dat");
    std::fs::write(&target, b"0123456789").unwrap();

    let orch = EffectTxOrchestrator::<NativeSecureFs>::new(lab.path()).unwrap();
    let cap = [0x44; 32];
    let (fd1, id1) = NativeSecureFs::pin_object(lab.root_fd, "budgeted.dat", cap).unwrap();
    unsafe { libc::close(fd1) };

    let principal = [0x66; 32];
    // Cada efecto individual de 10 bytes es <= 15 bytes, pero la composición de dos (20 bytes) excede 15.
    orch.set_budget_policy(
        principal,
        EffectBudgetPolicy {
            max_effects: 2,
            max_total_bytes: 15,
            allowed_targets: vec![(id1.locator.dev, id1.locator.ino)],
        },
    )
    .unwrap();

    let auth1 = AuthorityContext {
        authority_id: principal,
        epoch: 1,
        effect: EffectType::Mutate,
        nonce: [0x31; 32],
    };
    let (s1, _) = orch
        .secure_mutate_scoped(lab.root_fd, "budgeted.dat", &auth1, &id1, b"AAAAAAAAAA")
        .unwrap();
    assert_eq!(s1, EffectTxState::Committed);

    let (fd2, id2) = NativeSecureFs::pin_object(lab.root_fd, "budgeted.dat", cap).unwrap();
    unsafe { libc::close(fd2) };
    let auth2 = AuthorityContext {
        authority_id: principal,
        epoch: 1,
        effect: EffectType::Mutate,
        nonce: [0x32; 32],
    };
    let second_res =
        orch.secure_mutate_scoped(lab.root_fd, "budgeted.dat", &auth2, &id2, b"BBBBBBBBBB");
    assert!(
        matches!(second_res, Err(SecureFsError::BudgetExceeded(_))),
        "FL014_COMPOSITION: cumulative payload exceeding budget must be rejected: {:?}",
        second_res
    );

    // Incluso tras reiniciar el proceso (nuevo EffectTxOrchestrator recargando .budget_usage.bin),
    // el presupuesto consumido en la época 1 persiste y bloquea la segunda mutación:
    let orch_restarted = EffectTxOrchestrator::<NativeSecureFs>::new(lab.path()).unwrap();
    orch_restarted
        .set_budget_policy(
            principal,
            EffectBudgetPolicy {
                max_effects: 2,
                max_total_bytes: 15,
                allowed_targets: vec![(id1.locator.dev, id1.locator.ino)],
            },
        )
        .unwrap();
    let post_restart_res = orch_restarted.secure_mutate_scoped(
        lab.root_fd,
        "budgeted.dat",
        &auth2,
        &id2,
        b"BBBBBBBBBB",
    );
    assert!(
        matches!(post_restart_res, Err(SecureFsError::BudgetExceeded(_))),
        "FL014_COMPOSITION: budget usage must survive orchestrator restart: {:?}",
        post_restart_res
    );
    assert_eq!(std::fs::read(&target).unwrap(), b"AAAAAAAAAA");
}

// ===========================================================================
// 5. FL013_SAME_INODE_WRITER: Escritor concurrente sobre el inodo original
// ===========================================================================

#[test]
fn fl013_same_inode_writer_isolated_snapshot_preserves_authorized_bytes() {
    let lab = Wave4Lab::new("fl013_same_inode");
    let src_file = lab.path().join("module.wasm");
    let authorized_bytes = b"trusted_verified_wasm_bytecode_v1";
    std::fs::write(&src_file, authorized_bytes).unwrap();

    let orch = EffectTxOrchestrator::<NativeSecureFs>::new(lab.path()).unwrap();
    let cap = [0x45; 32];
    let (fd, id) = NativeSecureFs::pin_object(lab.root_fd, "module.wasm", cap).unwrap();
    unsafe { libc::close(fd) };

    let snap_tag = [0xA1; 32];
    let snapshot = orch
        .create_isolated_snapshot(lab.root_fd, "module.wasm", &id, &snap_tag)
        .unwrap();

    // Un escritor externo sobre el MISMO inodo muta `module.wasm` después de crear el snapshot
    std::fs::write(&src_file, b"HOSTILE_OVERWRITE_ON_SAME_INODE!!").unwrap();

    // El consumidor lee exclusivamente desde `snapshot.read_trusted_bytes()` (descriptor inmovilizado)
    let consumed = snapshot.read_trusted_bytes().unwrap();
    assert_eq!(consumed, authorized_bytes);
    assert_eq!(snapshot.verified_sha256, id.state.hash);
    assert_eq!(
        snapshot.strength,
        IsolationStrength::BrokerQuarantinedSnapshot
    );
}

// ===========================================================================
// 6. FL013_WEAK_SEAL: Mapeo compartido previo o sellado insuficiente
// ===========================================================================

#[test]
fn fl013_weak_seal_rejects_unverified_or_shared_writable_mappings() {
    // Mapeo compartido escribible previo -> rechazado
    let res_writable_map = IsolatedSnapshot::evaluate_seal_guarantees(true, true, false, false);
    assert!(matches!(
        res_writable_map,
        Err(SecureFsError::WeakIsolationRejected(_))
    ));

    // F_GET_SEALS no verificado -> rechazado
    let res_unverified = IsolatedSnapshot::evaluate_seal_guarantees(false, false, false, false);
    assert!(matches!(
        res_unverified,
        Err(SecureFsError::WeakIsolationRejected(_))
    ));

    // Sin mapeo compartido escribible y con F_GET_SEALS verificado -> KernelSealedMemfd
    let res_strong = IsolatedSnapshot::evaluate_seal_guarantees(false, true, false, false).unwrap();
    assert_eq!(res_strong, IsolationStrength::KernelSealedMemfd);
}

// ===========================================================================
// 7. FL013_DARWIN_IMMUTABLE: Propietario intenta retirar UF_IMMUTABLE / mprotect
// ===========================================================================

#[test]
fn fl013_darwin_immutable_and_mprotect_never_claim_absolute_isolation() {
    // Depender de `UF_IMMUTABLE` bajo el mismo UID o `mprotect(PROT_READ)` en el mismo proceso
    // degrada explícitamente la garantía a `DegradedSameUidOrInProcess`.
    let strength_uf = IsolatedSnapshot::evaluate_seal_guarantees(false, true, false, true).unwrap();
    assert_eq!(
        strength_uf,
        IsolationStrength::DegradedSameUidOrInProcess,
        "FL013_DARWIN_IMMUTABLE: UF_IMMUTABLE under same effective UID must not claim strong isolation"
    );

    let strength_mprotect =
        IsolatedSnapshot::evaluate_seal_guarantees(false, true, true, false).unwrap();
    assert_eq!(
        strength_mprotect,
        IsolationStrength::DegradedSameUidOrInProcess,
        "FL013_DARWIN_IMMUTABLE: in-process mprotect(PROT_READ) must not claim strong isolation"
    );
}

// ===========================================================================
// 8. FL015_TRANSITIVE_DRIFT: Dependencia transitiva cambia tras atestación
// ===========================================================================

#[test]
fn fl015_transitive_drift_rejects_deployment_when_closure_mutates() {
    let attested_closure = DeploymentPermit::compute_closure_root(&[
        ("core-engine", [0x10; 32]),
        ("transitive-tls", [0x20; 32]),
    ]);
    let drifted_closure = DeploymentPermit::compute_closure_root(&[
        ("core-engine", [0x10; 32]),
        ("transitive-tls", [0x99; 32]), // Sustitución transitiva post-PR
    ]);

    let permit = DeploymentPermit {
        artifact_digest: [0xAA; 32],
        dependency_closure_root: attested_closure,
        profile_digest: [0xBB; 32],
        policy_digest: [0xCC; 32],
        policy_epoch: 5,
        principal_identity: [0xDD; 32],
        authorization_scope: vec![EffectType::Mutate],
        expires_at: 1000,
        nonce: [0xEE; 32],
    };

    let validation =
        permit.validate_for_deployment(&[0xAA; 32], &drifted_closure, &[0xCC; 32], 5, 500);
    assert!(
        matches!(
            validation,
            Err(SecureFsError::DeploymentClosureViolation(_))
        ),
        "FL015_TRANSITIVE_DRIFT: transitive dependency substitution must reject deployment"
    );
}

// ===========================================================================
// 9. FL015_POLICY_ROLLBACK: Política antigua o excepción caducada
// ===========================================================================

#[test]
fn fl015_policy_rollback_and_expired_permit_rejected() {
    let closure = DeploymentPermit::compute_closure_root(&[("core-engine", [0x10; 32])]);
    let permit = DeploymentPermit {
        artifact_digest: [0xAA; 32],
        dependency_closure_root: closure,
        profile_digest: [0xBB; 32],
        policy_digest: [0xCC; 32],
        policy_epoch: 3,
        principal_identity: [0xDD; 32],
        authorization_scope: vec![EffectType::Read],
        expires_at: 100,
        nonce: [0xEF; 32],
    };

    // Política actualizada a época 4 invalida el permiso emitido bajo época 3
    let rollback_res =
        permit.validate_for_deployment(&[0xAA; 32], &closure, &[0xCC; 32], 4, 50);
    assert!(matches!(
        rollback_res,
        Err(SecureFsError::DeploymentClosureViolation(_))
    ));

    // Reloj lógico alcanza `expires_at` (100) -> excepción caducada
    let expired_res =
        permit.validate_for_deployment(&[0xAA; 32], &closure, &[0xCC; 32], 3, 100);
    assert!(matches!(
        expired_res,
        Err(SecureFsError::DeploymentClosureViolation(_))
    ));
}

// ===========================================================================
// 10. FL015_RUNTIME_LOAD: Carga dinámica fuera de clausura autorizada
// ===========================================================================

#[test]
fn fl015_runtime_load_blocks_or_degrades_unverified_dylib() {
    let closure = DeploymentPermit::compute_closure_root(&[("core-engine", [0x10; 32])]);
    let permit = DeploymentPermit {
        artifact_digest: [0xAA; 32],
        dependency_closure_root: closure,
        profile_digest: [0xBB; 32],
        policy_digest: [0xCC; 32],
        policy_epoch: 1,
        principal_identity: [0xDD; 32],
        authorization_scope: vec![EffectType::Read],
        expires_at: 500,
        nonce: [0xF0; 32],
    };

    let authorized_dylibs = [[0x11; 32], [0x22; 32]];
    let rogue_plugin_digest = [0xFF; 32];

    // En modo estricto (`allow_degraded_unverified_plugin = false`), bloquea la carga dinámica
    let strict_res =
        permit.verify_dynamic_library_load(&rogue_plugin_digest, &authorized_dylibs, false);
    assert!(matches!(
        strict_res,
        Err(SecureFsError::DeploymentClosureViolation(_))
    ));

    // Si la política permite continuar degradando, devuelve explícitamente `DegradedSameUidOrInProcess`
    let degraded_res = permit
        .verify_dynamic_library_load(&rogue_plugin_digest, &authorized_dylibs, true)
        .unwrap();
    assert_eq!(degraded_res, IsolationStrength::DegradedSameUidOrInProcess);

    // Una dylib dentro de la clausura conserva `BrokerQuarantinedSnapshot`
    let verified_res = permit
        .verify_dynamic_library_load(&[0x11; 32], &authorized_dylibs, false)
        .unwrap();
    assert_eq!(verified_res, IsolationStrength::BrokerQuarantinedSnapshot);
}
