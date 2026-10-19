//! # BABYLON-60 · ITERACIÓN Ω — Campaña de 5 Pruebas y Alcanzabilidad NEMESIS
//!
//! Demuestra en silicio las dos propiedades del invariante raíz `INV-Ω`:
//! 1. **Autorización Correcta ($\text{INV-}\Omega_1$):**
//!    $$\forall e \in E_{\text{protegidos}}: \operatorname{Executed}(e) \implies \operatorname{Authorized}(e) \land \operatorname{SignatureValid}(e) \land \operatorname{PolicyValid}(e) \land \operatorname{Fresh}(e)$$
//! 2. **Mediación Completa ($\text{INV-}\Omega_2$):**
//!    $$\forall p \in \text{Processes}_{\text{agente}}, \forall e \in E_{\text{protegidos}}: \operatorname{Execute}(p, e) \implies \operatorname{MediatedByBABYLON}(p, e)$$
//!
//! Campaña experimental de 5 pruebas exigidas por la Iteración Ω:
//! - `BYPASS-001`: El proceso del agente intenta modificar/borrar directamente un recurso protegido
//!   y el ledger SQLite sin pasar por BABYLON -> Denegación efectiva del SO (`Operation not permitted` / `EPERM`).
//! - `AUTH-002`: Se modifica el efecto después de la autorización -> Firma/Digest inválido, denegación.
//! - `RACE-003`: Se sustituye el recurso entre comprobación y uso (TOCTOU) -> Ningún efecto no autorizado.
//! - `CRASH-004`: Muere el broker durante una operación -> Estado recuperable (`UNKNOWN`), sin autorización reutilizable.
//! - `REVOCATION-005`: Se revoca el permiso antes de ejecutar (`AuthorityEpochGate`) -> Ningún efecto posterior a la revocación.
//! - `NEMESIS-REACHABILITY`: Verificador de grafo $G=(V,A)$ probando $\forall \pi: a \leadsto r, b \in \pi$.

#![cfg(feature = "cortex-persist")]

use std::fs;
use std::path::{Path, PathBuf};
use std::sync::Arc;

use ed25519_dalek::SigningKey;
use rand::rngs::OsRng;

use babylon60::executor::{
    AdmittedAuthority, AuthorityAlgorithm, AuthorizationPayload, CrashAction, CrashPoint,
    DurableExecutionStore, EffectAdapter, ExecutionError, IdempotencyContract, ProposedIntent,
    ReservationState, SecurityPolicy, SignedAuthorization, SovereignExecutor, PROTOCOL_VERSION,
};
use babylon60::omega_mediation::{
    AuthorityGraph, AuthorityNode, EvidenceLevel, MacOsAgentConfinement,
};
use babylon60::receipt::Ed25519Signer;
use babylon60::secure_fs::{EffectTxOrchestrator, NativeSecureFs, SecureFsBackend};
use sha2::{Digest, Sha256};

struct OmegaSandboxDir {
    path: PathBuf,
}

impl OmegaSandboxDir {
    fn new(label: &str) -> Self {
        let base = if cfg!(unix) {
            PathBuf::from("/tmp")
        } else {
            std::env::temp_dir()
        };
        let path = base.join(format!(
            "b60_om_{}_{}_{:x}",
            label,
            std::process::id(),
            rand::random::<u32>()
        ));
        fs::create_dir_all(&path).expect("failed to create OmegaSandboxDir");
        Self { path }
    }

    fn path(&self) -> &Path {
        &self.path
    }
}

impl Drop for OmegaSandboxDir {
    fn drop(&mut self) {
        let _ = fs::remove_dir_all(&self.path);
    }
}

/// Adaptador real de archivos protegidos en el sistema operativo.
/// Opera directamente sobre un archivo físico en disco dentro del perímetro del Broker.
struct RealFileEffectAdapter;

impl EffectAdapter for RealFileEffectAdapter {
    type Resource = PathBuf;
    type Effect = Vec<u8>;
    type Output = [u8; 32];
    type Error = String;

    fn parse_intent(&self, intent: &ProposedIntent) -> Result<Self::Effect, Self::Error> {
        if intent.action_name != "WRITE_PROTECTED_FILE" {
            return Err(format!("unsupported action: {}", intent.action_name));
        }
        Ok(intent.parameters.clone())
    }

    fn compute_precondition(&self, resource_path: &Self::Resource) -> Result<[u8; 32], Self::Error> {
        let bytes = fs::read(resource_path).map_err(|e| format!("read error: {e}"))?;
        let mut h = Sha256::new();
        h.update(b"BABYLON60/real-file-precondition/v1");
        h.update((bytes.len() as u64).to_be_bytes());
        h.update(&bytes);
        Ok(h.finalize().into())
    }

    fn apply_effect(
        &mut self,
        resource_path: &mut Self::Resource,
        expected_precondition: &[u8; 32],
        _nonce: &[u8; 32],
        effect: &Self::Effect,
    ) -> Result<Self::Output, Self::Error> {
        let current = self.compute_precondition(resource_path)?;
        if &current != expected_precondition {
            return Err("precondition mismatch on real OS file".to_string());
        }
        fs::write(&*resource_path, effect).map_err(|e| format!("write error: {e}"))?;
        self.compute_precondition(resource_path)
    }

    fn idempotency_contract(&self) -> IdempotencyContract {
        IdempotencyContract::NonIdempotentExplicitIntervention
    }
}

struct OmegaFixture {
    inst_id: [u8; 32],
    exec_id: [u8; 32],
    signer: Ed25519Signer,
    pk: Vec<u8>,
    policy: SecurityPolicy,
}

impl OmegaFixture {
    fn new() -> Self {
        let sk = SigningKey::generate(&mut OsRng);
        let pk = sk.verifying_key().to_bytes().to_vec();
        let signer = Ed25519Signer::from_signing_key(sk);
        let policy = SecurityPolicy {
            policy_id: [0x99; 32],
            allowed_action: "WRITE_PROTECTED_FILE".to_string(),
            max_allowed_uses: 1,
            admitted_authority_key: pk.clone(),
        };
        Self {
            inst_id: [0x11; 32],
            exec_id: [0x22; 32],
            signer,
            pk,
            policy,
        }
    }

    fn sign_intent(
        &self,
        intent: &ProposedIntent,
        precondition: [u8; 32],
        nonce_byte: u8,
        epoch: u64,
        expires_at: u64,
    ) -> SignedAuthorization {
        let payload = AuthorizationPayload {
            protocol_version: PROTOCOL_VERSION,
            installation_id: self.inst_id,
            executor_id: self.exec_id,
            intent_digest: intent.compute_digest(),
            policy_digest: self.policy.compute_digest(),
            resource_precondition_digest: precondition,
            nonce: [nonce_byte; 32],
            authority_epoch: epoch,
            expires_at,
            max_uses: 1,
        };
        SignedAuthorization::new_cose(&payload, &self.signer).expect("COSE signing must succeed")
    }
}

// ============================================================================
// PRUEBA 1: BYPASS-001 — El agente intenta acceder directamente a un recurso protegido
// Resultado exigido: Denegación efectiva del SO (no solo DENIED en un log)
// ============================================================================
#[test]
#[allow(unreachable_code)]
fn test_omega_bypass_001_os_blocks_direct_agent_access_and_broker_executes_authorized() {
    #[cfg(not(target_os = "macos"))]
    {
        eprintln!("BYPASS-001: Skipped on non-macOS (Seatbelt sandbox-exec requires Darwin)");
        return;
    }

    let sb = OmegaSandboxDir::new("bypass_001");
    let protected_dir = sb.path().join("protected_vault");
    let ledger_dir = sb.path().join("cortex_ledger");
    fs::create_dir_all(&protected_dir).unwrap();
    fs::create_dir_all(&ledger_dir).unwrap();

    let mut protected_file = protected_dir.join("critical_asset.dat");
    let initial_bytes = b"SOVEREIGN_INITIAL_STATE_V1";
    fs::write(&protected_file, initial_bytes).unwrap();

    let ledger_db_path = ledger_dir.join("executor.db");
    let store = DurableExecutionStore::open(ledger_db_path.to_str().unwrap()).unwrap();

    // 1. Confinamiento del proceso del agente a nivel de sistema operativo (macOS sandbox-exec)
    let socket_path = sb.path().join("babylon_broker.sock");
    let confinement = MacOsAgentConfinement::new(
        &[&protected_dir, &ledger_dir],
        Some(&socket_path),
    );

    // 2. El agente intenta SOBRESCRIBIR directamente el recurso protegido sin pasar por BABYLON
    let direct_write_attempt = confinement
        .spawn_confined_command(
            "/bin/sh",
            &[
                "-c",
                &format!(
                    "echo 'PWNED_BY_AGENT' > '{}'",
                    protected_file.display()
                ),
            ],
        )
        .expect("sandbox-exec must execute");

    assert!(
        !direct_write_attempt.status.success(),
        "BYPASS-001 FAIL: El SO permitió al agente escribir directamente en el recurso protegido"
    );
    let stderr_write = String::from_utf8_lossy(&direct_write_attempt.stderr);
    assert!(
        stderr_write.contains("Operation not permitted") || stderr_write.contains("Permission denied"),
        "BYPASS-001: Se esperaba denegación real del kernel XNU (Operation not permitted), obtenido: {stderr_write}"
    );

    // 3. El agente intenta BORRAR directamente el recurso protegido (`rm -f`)
    let direct_unlink_attempt = confinement
        .spawn_confined_command(
            "/bin/rm",
            &["-f", &protected_file.to_string_lossy()],
        )
        .expect("sandbox-exec must execute");

    assert!(
        !direct_unlink_attempt.status.success(),
        "BYPASS-001 FAIL: El SO permitió al agente borrar directamente el recurso protegido"
    );

    // 4. El agente intenta CORROMPER directamente el ledger SQLite WAL del Broker
    let direct_ledger_tamper = confinement
        .spawn_confined_command(
            "/bin/sh",
            &[
                "-c",
                &format!("echo 'CORRUPT' >> '{}'", ledger_db_path.display()),
            ],
        )
        .expect("sandbox-exec must execute");

    assert!(
        !direct_ledger_tamper.status.success(),
        "BYPASS-001 FAIL: El SO permitió al agente alterar directamente el archivo SQLite del ledger"
    );

    // Verificar en el sistema de archivos real que los bytes permanecen intactos tras los 3 ataques OS
    let observed_after_bypass = fs::read(&protected_file).unwrap();
    assert_eq!(
        observed_after_bypass.as_slice(),
        initial_bytes,
        "El archivo físico en APFS debe permanecer bit a bit idéntico tras el bloqueo del SO"
    );

    // 5. Ahora el efecto se solicita y autoriza criptográficamente a través del Broker BABYLON
    let fx = OmegaFixture::new();
    let adapter = RealFileEffectAdapter;
    let pre = adapter.compute_precondition(&protected_file).unwrap();
    let authorized_intent = ProposedIntent {
        intent_id: [0xA1; 32],
        action_name: "WRITE_PROTECTED_FILE".to_string(),
        target_resource: protected_file.to_string_lossy().into_owned(),
        parameters: b"AUTHORIZED_MUTATION_VIA_BABYLON_BROKER".to_vec(),
    };
    let auth = fx.sign_intent(&authorized_intent, pre, 0x01, 1, 2000);

    let mut executor = SovereignExecutor::new(
        fx.inst_id,
        fx.exec_id,
        1,
        vec![AdmittedAuthority {
            public_key: fx.pk.clone(),
            algorithm: AuthorityAlgorithm::Ed25519,
        }],
        store,
        RealFileEffectAdapter,
    );

    let _post_digest = executor
        .execute_action(&auth, &authorized_intent, &fx.policy, &mut protected_file, 1500)
        .expect("El Broker con privilegios debe ejecutar el efecto autorizado");

    // 6. Verificar que el efecto real ocurrió en el SO y quedó registrado en el ledger durable
    let observed_after_broker = fs::read(&protected_file).unwrap();
    assert_eq!(
        observed_after_broker.as_slice(),
        b"AUTHORIZED_MUTATION_VIA_BABYLON_BROKER"
    );
    let rec = executor
        .store
        .get_record(&[0x01; 32])
        .unwrap()
        .expect("El registro debe existir en el ledger");
    assert_eq!(rec.state, ReservationState::Executed);
}

// ============================================================================
// PRUEBA 2: AUTH-002 — Se modifica el efecto después de la autorización
// Resultado exigido: Firma/Digest inválido, denegación y cero mutación en el SO
// ============================================================================
#[test]
fn test_omega_auth_002_tampered_effect_after_authorization_is_denied() {
    let sb = OmegaSandboxDir::new("auth_002");
    let mut protected_file = sb.path().join("account_limits.conf");
    let initial = b"MAX_WITHDRAWAL=1000";
    fs::write(&protected_file, initial).unwrap();

    let fx = OmegaFixture::new();
    let adapter = RealFileEffectAdapter;
    let pre = adapter.compute_precondition(&protected_file).unwrap();

    // El humano autoriza un cambio benigno: MAX_WITHDRAWAL=1500
    let benign_intent = ProposedIntent {
        intent_id: [0xA2; 32],
        action_name: "WRITE_PROTECTED_FILE".to_string(),
        target_resource: protected_file.to_string_lossy().into_owned(),
        parameters: b"MAX_WITHDRAWAL=1500".to_vec(),
    };
    let auth = fx.sign_intent(&benign_intent, pre, 0x02, 1, 2000);

    // Después de firmar, el agente modifica el efecto propuesto a MAX_WITHDRAWAL=9999999
    let tampered_intent = ProposedIntent {
        intent_id: [0xA2; 32],
        action_name: "WRITE_PROTECTED_FILE".to_string(),
        target_resource: protected_file.to_string_lossy().into_owned(),
        parameters: b"MAX_WITHDRAWAL=9999999".to_vec(),
    };

    let ledger_path = sb.path().join("ledger.db");
    let store = DurableExecutionStore::open(ledger_path.to_str().unwrap()).unwrap();
    let mut executor = SovereignExecutor::new(
        fx.inst_id,
        fx.exec_id,
        1,
        vec![AdmittedAuthority {
            public_key: fx.pk.clone(),
            algorithm: AuthorityAlgorithm::Ed25519,
        }],
        store,
        RealFileEffectAdapter,
    );

    let err = executor
        .execute_action(&auth, &tampered_intent, &fx.policy, &mut protected_file, 1500)
        .expect_err("AUTH-002 FAIL: Un efecto modificado tras la firma debe ser rechazado");
    assert_eq!(err, ExecutionError::IntentDigestMismatch);

    // Además, si un atacante altera directamente un byte de la firma dentro del sobre COSE_Sign1:
    let mut forged_cose = auth.clone();
    let last_idx = forged_cose.cose_bytes.len() - 1;
    forged_cose.cose_bytes[last_idx] ^= 0xFF;
    let err_sig = executor
        .execute_action(&forged_cose, &benign_intent, &fx.policy, &mut protected_file, 1500)
        .expect_err("AUTH-002 FAIL: Un sobre COSE alterado debe fallar por firma inválida");
    assert!(matches!(err_sig, ExecutionError::InvalidSignature(_)));

    // El recurso real en el SO permanece intacto y ningún nonce fue consumido
    assert_eq!(fs::read(&protected_file).unwrap().as_slice(), initial);
    assert!(executor.store.get_record(&[0x02; 32]).unwrap().is_none());
}

// ============================================================================
// PRUEBA 3: RACE-003 — Se sustituye el recurso entre comprobación y uso (TOCTOU)
// Resultado exigido: Ningún efecto no autorizado en el SO real
// ============================================================================
#[test]
fn test_omega_race_003_resource_swapped_between_check_and_use_is_aborted() {
    let sb = OmegaSandboxDir::new("race_003");
    let mut protected_file = sb.path().join("deploy_target.sh");
    fs::write(&protected_file, b"echo 'SAFE_V1'").unwrap();

    let fx = OmegaFixture::new();
    let adapter = RealFileEffectAdapter;
    let pre_at_authorization = adapter.compute_precondition(&protected_file).unwrap();

    let intent = ProposedIntent {
        intent_id: [0xA3; 32],
        action_name: "WRITE_PROTECTED_FILE".to_string(),
        target_resource: protected_file.to_string_lossy().into_owned(),
        parameters: b"echo 'PATCHED_SAFE_V1'".to_vec(),
    };
    let auth = fx.sign_intent(&intent, pre_at_authorization, 0x03, 1, 2000);

    // Carrera TOCTOU: Entre la autorización y la ejecución, el recurso subyacente cambia en disco
    let concurrent_state = b"echo 'CONCURRENT_EXTERNAL_CHANGE_DO_NOT_OVERWRITE'";
    fs::write(&protected_file, concurrent_state).unwrap();

    let ledger_path = sb.path().join("ledger.db");
    let store = DurableExecutionStore::open(ledger_path.to_str().unwrap()).unwrap();
    let mut executor = SovereignExecutor::new(
        fx.inst_id,
        fx.exec_id,
        1,
        vec![AdmittedAuthority {
            public_key: fx.pk.clone(),
            algorithm: AuthorityAlgorithm::Ed25519,
        }],
        store,
        RealFileEffectAdapter,
    );

    let err = executor
        .execute_action(&auth, &intent, &fx.policy, &mut protected_file, 1500)
        .expect_err("RACE-003 FAIL: Sustitución TOCTOU entre autorización y uso debe abortar");
    assert_eq!(err, ExecutionError::PreconditionMismatch);

    // El archivo sustituido NO fue sobrescrito por la operación obsoleta
    assert_eq!(
        fs::read(&protected_file).unwrap().as_slice(),
        concurrent_state
    );

    // Verificación adicional con cuarentena atómica de inodo en SecureFs (DELETE_FILE):
    let orch = EffectTxOrchestrator::<NativeSecureFs>::new(sb.path()).unwrap();
    let victim_keep = sb.path().join("keep_secret.key");
    let temp_delete = sb.path().join("temp_scratch.tmp");
    fs::write(&victim_keep, b"ROOT_PRIVATE_KEY_DO_NOT_DELETE").unwrap();
    fs::write(&temp_delete, b"DISPOSABLE_SCRATCH").unwrap();

    let dir_c = std::ffi::CString::new(sb.path().to_str().unwrap()).unwrap();
    let root_fd = unsafe {
        libc::open(
            dir_c.as_ptr(),
            libc::O_RDONLY | libc::O_DIRECTORY | libc::O_CLOEXEC,
        )
    };
    assert!(root_fd >= 0);

    // Se fija la identidad (dev, ino, sha256) de temp_scratch.tmp
    let (pinned_fd, pinned_id) =
        NativeSecureFs::pin_object(root_fd, "temp_scratch.tmp", [0xAA; 32]).unwrap();
    unsafe { libc::close(pinned_fd) };

    // Atacante intercambia temp_scratch.tmp por keep_secret.key antes del aislamiento en cuarentena
    fs::remove_file(&temp_delete).unwrap();
    fs::hard_link(&victim_keep, &temp_delete).unwrap();

    let tx_res = orch.secure_delete(root_fd, "temp_scratch.tmp", &pinned_id, &[0x33; 32]);
    unsafe { libc::close(root_fd) };

    assert_eq!(
        tx_res.unwrap(),
        babylon60::secure_fs::EffectTxState::SecurityAbort,
        "RACE-003 FAIL: El swap de inodo tras el secuestro en cuarentena debe producir SecurityAbort sin destruir el recurso"
    );
    assert_eq!(
        fs::read(&victim_keep).unwrap().as_slice(),
        b"ROOT_PRIVATE_KEY_DO_NOT_DELETE",
        "RACE-003: El recurso protegido intercambiado jamás debe ser destruido"
    );
}

// ============================================================================
// PRUEBA 4: CRASH-004 — Muere el broker durante una operación
// Resultado exigido: Estado recuperable (`UNKNOWN`), sin autorización reutilizable
// ============================================================================
#[test]
fn test_omega_crash_004_broker_death_leaves_recoverable_unknown_and_blocks_replay() {
    let sb = OmegaSandboxDir::new("crash_004");
    let mut protected_file = sb.path().join("wire_transfer.dat");
    fs::write(&protected_file, b"BALANCE=10000").unwrap();
    let ledger_path = sb.path().join("crash_ledger.db");

    let fx = OmegaFixture::new();
    let adapter = RealFileEffectAdapter;
    let pre = adapter.compute_precondition(&protected_file).unwrap();

    let intent = ProposedIntent {
        intent_id: [0xA4; 32],
        action_name: "WRITE_PROTECTED_FILE".to_string(),
        target_resource: protected_file.to_string_lossy().into_owned(),
        parameters: b"BALANCE=9000".to_vec(),
    };
    let nonce_byte = 0x04;
    let auth = fx.sign_intent(&intent, pre, nonce_byte, 1, 2000);

    // 1. Primera instancia del Broker muere tras registrar DISPATCHED pero antes de aplicar el efecto
    {
        let store = DurableExecutionStore::open(ledger_path.to_str().unwrap()).unwrap();
        let mut broker_v1 = SovereignExecutor::new(
            fx.inst_id,
            fx.exec_id,
            1,
            vec![AdmittedAuthority {
                public_key: fx.pk.clone(),
                algorithm: AuthorityAlgorithm::Ed25519,
            }],
            store,
            RealFileEffectAdapter,
        )
        .with_crash(CrashPoint::AfterDispatchBeforeEffect, CrashAction::ReturnError);

        let crash_err = broker_v1
            .execute_action(&auth, &intent, &fx.policy, &mut protected_file, 1500)
            .expect_err("El broker debe simular interrupción en AfterDispatchBeforeEffect");
        assert_eq!(
            crash_err,
            ExecutionError::Interrupted(CrashPoint::AfterDispatchBeforeEffect)
        );
    }

    // 2. El broker se reinicia reabriendo el archivo SQLite WAL en disco y reclasificando DISPATCHED -> UNKNOWN
    let mut store_reopened = DurableExecutionStore::open(ledger_path.to_str().unwrap()).unwrap();
    let reclassified = store_reopened.reconcile_on_startup().unwrap();
    assert_eq!(
        reclassified.len(),
        1,
        "CRASH-004: Exactamente 1 registro DISPATCHED debe ser reclasificado a UNKNOWN al reiniciar"
    );

    let mut broker_v2 = SovereignExecutor::new(
        fx.inst_id,
        fx.exec_id,
        1,
        vec![AdmittedAuthority {
            public_key: fx.pk.clone(),
            algorithm: AuthorityAlgorithm::Ed25519,
        }],
        store_reopened,
        RealFileEffectAdapter,
    );

    // 3. El estado en el ledger es UNKNOWN
    let record = broker_v2
        .store
        .get_record(&[nonce_byte; 32])
        .unwrap()
        .expect("El nonce debe existir tras reiniciar el broker");
    assert_eq!(
        record.state,
        ReservationState::Unknown,
        "CRASH-004: Todo DISPATCHED incompleto debe pasar a UNKNOWN tras reiniciar"
    );

    // 4. Intentar reutilizar (replay) la misma autorización es denegado con NonceAlreadyConsumed
    let replay_err = broker_v2
        .execute_action(&auth, &intent, &fx.policy, &mut protected_file, 1505)
        .expect_err("CRASH-004 FAIL: La autorización interrumpida nunca debe poder reutilizarse");
    assert!(matches!(
        replay_err,
        ExecutionError::NonceAlreadyConsumed(_)
    ));

    // El archivo en disco nunca sufrió el efecto porque el crash ocurrió antes del efecto
    assert_eq!(
        fs::read(&protected_file).unwrap().as_slice(),
        b"BALANCE=10000"
    );
}

// ============================================================================
// PRUEBA 5: REVOCATION-005 — Se revoca el permiso antes de ejecutar
// Resultado exigido: Ningún efecto posterior a la revocación
// ============================================================================
#[test]
fn test_omega_revocation_005_epoch_and_key_revocation_prevent_execution() {
    let sb = OmegaSandboxDir::new("revocation_005");
    let mut protected_file = sb.path().join("production_secrets.env");
    let initial = b"API_STATE=ACTIVE";
    fs::write(&protected_file, initial).unwrap();

    let fx = OmegaFixture::new();
    let adapter = RealFileEffectAdapter;
    let pre = adapter.compute_precondition(&protected_file).unwrap();

    let intent = ProposedIntent {
        intent_id: [0xA5; 32],
        action_name: "WRITE_PROTECTED_FILE".to_string(),
        target_resource: protected_file.to_string_lossy().into_owned(),
        parameters: b"API_STATE=ROTATED_BY_STALE_AUTH".to_vec(),
    };

    // Autorización emitida legítimamente bajo la época de autoridad 1
    let auth_epoch_1 = fx.sign_intent(&intent, pre, 0x05, 1, 2000);

    let ledger_path = sb.path().join("ledger.db");
    let store = DurableExecutionStore::open(ledger_path.to_str().unwrap()).unwrap();
    let mut executor = SovereignExecutor::new(
        fx.inst_id,
        fx.exec_id,
        1,
        vec![AdmittedAuthority {
            public_key: fx.pk.clone(),
            algorithm: AuthorityAlgorithm::Ed25519,
        }],
        store,
        RealFileEffectAdapter,
    );

    // Se revoca el permiso avanzando la época de autoridad (1 -> 2) ANTES de que el broker ejecute
    let epoch_gate = Arc::clone(&executor.authority_epoch_gate);
    epoch_gate
        .revoke_to(2)
        .expect("La revocación monótona de época (1 -> 2) debe completarse");

    let err = executor
        .execute_action(&auth_epoch_1, &intent, &fx.policy, &mut protected_file, 1500)
        .expect_err("REVOCATION-005 FAIL: Una autorización de época revocada no debe ejecutarse");
    assert_eq!(err, ExecutionError::AuthorityEpochRevoked);

    // Verificar que ni el recurso en el SO cambió ni el nonce fue reservado
    assert_eq!(fs::read(&protected_file).unwrap().as_slice(), initial);
    assert!(executor.store.get_record(&[0x05; 32]).unwrap().is_none());
}

// ============================================================================
// PRUEBA 6: NEMESIS REACHABILITY FALSIFIER — Grafo G=(V,A)
// Propiedad: \forall \pi: a \leadsto r, b \in \pi
// ============================================================================
#[test]
fn test_omega_nemesis_reachability_falsifier_detects_bypass_and_certifies_cut() {
    let sb = OmegaSandboxDir::new("nemesis_graph");
    let protected_dir = sb.path().join("protected");
    let ledger_dir = sb.path().join("ledger");
    let sock_path = sb.path().join("broker.sock");
    fs::create_dir_all(&protected_dir).unwrap();
    fs::create_dir_all(&ledger_dir).unwrap();

    // 1. Construcción del grafo de autoridad bajo confinamiento correcto (Mediación Completa)
    let confinement = MacOsAgentConfinement::new(
        &[&protected_dir, &ledger_dir],
        Some(&sock_path),
    );
    let mediated_graph = confinement.build_authority_graph("agent_edin", "babylon_broker");
    let verdict_ok = mediated_graph.verify_complete_mediation();

    assert!(
        verdict_ok.complete_mediation_holds,
        "El grafo confinado debe satisfacer la propiedad de corte (b \\in \\pi)"
    );
    assert!(verdict_ok.bypass_paths.is_empty());
    assert!(verdict_ok.mediated_paths_count >= 2);

    // 2. Ahora inyectamos una ruta alternativa no mediada (ej. descriptor heredado o directorio writable)
    let mut leaky_graph: AuthorityGraph = mediated_graph.clone();
    let agent = AuthorityNode::AgentProcess("agent_edin".to_string());
    let leaked_cap = AuthorityNode::CapabilityHandle("leaked_writable_fd_7".to_string());
    let target_res = AuthorityNode::ProtectedResource(protected_dir.to_string_lossy().into_owned());

    leaky_graph.add_edge(agent.clone(), leaked_cap.clone(), "inherited_fd_without_cloexec");
    leaky_graph.add_edge(leaked_cap.clone(), target_res.clone(), "direct_write_syscall");

    let verdict_refuted = leaky_graph.verify_complete_mediation();
    assert!(
        !verdict_refuted.complete_mediation_holds,
        "NEMESIS debe refutar el invariante en cuanto exista un camino que no atraviese BABYLON"
    );
    assert_eq!(verdict_refuted.bypass_paths.len(), 1);
    assert_eq!(
        verdict_refuted.bypass_paths[0],
        vec![agent, leaked_cap, target_res]
    );

    // Verificar etiquetas de los 4 niveles de evidencia L1-L4
    assert_eq!(EvidenceLevel::L1Formal.as_str(), "L1_FORMAL");
    assert_eq!(EvidenceLevel::L2Implementation.as_str(), "L2_IMPLEMENTATION");
    assert_eq!(EvidenceLevel::L3Isolation.as_str(), "L3_ISOLATION");
    assert_eq!(EvidenceLevel::L4Experimental.as_str(), "L4_EXPERIMENTAL");

    // 3. Verificar que el perfil Seatbelt bloquea la superficie Computer Use directa (N-08)
    let profile = confinement.to_seatbelt_profile();
    assert!(profile.contains("(deny hid-control)"));
    assert!(profile.contains("(deny appleevent-send)"));
    for svc in MacOsAgentConfinement::DENIED_COMPUTER_USE_MACH_SERVICES {
        assert!(
            profile.contains(&format!("(deny mach-lookup (global-name \"{}\"))", svc)),
            "El perfil Seatbelt debe denegar mach-lookup a {}",
            svc
        );
    }
}

// ============================================================================
// CAMPAÑA SHADOW-EDGE-DIFF (#5): 5 PRUEBAS ADVERSARIALES (SD-001 .. SD-005)
// Objetivo: Falsar INV-Ω descubriendo aristas de autoridad a nivel de SO
//           ausentes del AuthorityGraph declarado.
// ============================================================================

use babylon60::omega_mediation::{
    ObservationModality, OsResourceObserver, PhysicalResourceWitness,
    ProcessResourceSnapshot, SecurityMechanismPlane, ShadowDiffVerdict, ShadowEdgeDiff,
};

// ----------------------------------------------------------------------------
// SD-001: Descriptor heredado mediante fork/exec (sin FD_CLOEXEC)
// Vector: El proceso padre abre un descriptor de escritura hacia un recurso
//         protegido, limpia FD_CLOEXEC y ejecuta fork/exec hacia el subproceso
//         del agente, que escribe directamente sin pasar por el broker BABYLON.
// ----------------------------------------------------------------------------
#[test]
fn test_shadow_diff_sd_001_inherited_fd_across_fork_exec_falsifies_isolation() {
    use std::io::{BufRead, BufReader, Write};
    use std::os::unix::io::AsRawFd;
    use std::process::{Command, Stdio};

    let sb = OmegaSandboxDir::new("sd_001_fork_exec_fd");
    let protected_dir = sb.path().join("protected_vault");
    let evidence_dir = sb.path().join("cortex_evidence");
    let broker_sock = sb.path().join("broker.sock");
    fs::create_dir_all(&protected_dir).unwrap();

    let secret_file = protected_dir.join("vault_state.dat");
    fs::write(&secret_file, b"INITIAL_MEDIATED_STATE_V1").unwrap();

    let pre_witness = PhysicalResourceWitness::capture_pre_state(&secret_file).unwrap();

    // El AuthorityGraph declarado afirma que todo camino pasa por babylon_broker
    let confinement = MacOsAgentConfinement::new(&[&protected_dir], Some(&broker_sock));
    let declared_graph = confinement.build_authority_graph("agent_edin", "babylon_broker");
    assert!(
        declared_graph.verify_complete_mediation().complete_mediation_holds,
        "Precondición SD-001: el AuthorityGraph declarado debe afirmar mediación completa"
    );

    // Abrir descriptor con permiso de escritura y desactivar explícitamente FD_CLOEXEC
    let leaked_file = fs::OpenOptions::new()
        .read(true)
        .write(true)
        .open(&secret_file)
        .unwrap();
    let raw_fd = leaked_file.as_raw_fd();
    let flags = unsafe { libc::fcntl(raw_fd, libc::F_GETFD) };
    assert!(flags >= 0, "fcntl(F_GETFD) debe tener éxito");
    let rc = unsafe { libc::fcntl(raw_fd, libc::F_SETFD, flags & !libc::FD_CLOEXEC) };
    assert_eq!(rc, 0, "fcntl(F_SETFD, ~FD_CLOEXEC) debe limpiar FD_CLOEXEC");

    // El subproceso hijo hereda raw_fd tras fork/exec, muta el archivo sin tocar el broker
    // y permanece vivo hasta que OsResourceObserver inspecciona su tabla de descriptores.
    let cmd_str = format!(
        "printf 'SD001_BYPASS_VIA_INHERITED_FD' >&{raw_fd}; echo READY; read _line"
    );
    let mut child = Command::new("/bin/sh")
        .arg("-c")
        .arg(&cmd_str)
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .spawn()
        .expect("fallo al lanzar subproceso hijo con descriptor heredado");

    let mut child_stdout = BufReader::new(child.stdout.take().unwrap());
    let mut line = String::new();
    child_stdout.read_line(&mut line).unwrap();
    assert_eq!(line.trim(), "READY");

    // 1. Observador de solo lectura inspecciona los recursos reales del subproceso hijo
    let snapshot = OsResourceObserver::observe_pid(child.id());

    // Cerrar el subproceso limpiamente
    if let Some(mut stdin) = child.stdin.take() {
        let _ = writeln!(stdin, "DONE");
    }
    let _ = child.wait();
    drop(leaked_file);

    let post_witness = pre_witness.observe_post_state(false).unwrap();
    assert!(
        post_witness.unmediated_mutation_occurred(),
        "SD-001: el descriptor heredado mutó físicamente el recurso sin recibo del broker"
    );

    // 2. Motor determinista ShadowEdgeDiff compara AuthorityGraph vs realidad OS
    let agent_node = AuthorityNode::AgentProcess("agent_edin".to_string());
    let report = ShadowEdgeDiff::evaluate(
        &declared_graph,
        &agent_node,
        std::slice::from_ref(&protected_dir),
        std::slice::from_ref(&broker_sock),
        &snapshot,
        &[post_witness],
        1001,
    );

    assert_eq!(report.verdict, ShadowDiffVerdict::Falsified);
    assert_eq!(report.verdict.as_str(), "FALSIFIED");
    assert!(report.declared_mediation_verdict.complete_mediation_holds);
    assert!(
        !report.augmented_mediation_verdict.complete_mediation_holds,
        "El grafo aumentado con la arista sombra descubierta debe refutar INV-Ω"
    );
    assert!(!report.shadow_edges.is_empty());

    // 3. Emitir y persistir artefacto de evidencia compatible con CORTEX
    let evidence = report.to_cortex_evidence("SD-001");
    let saved_path = evidence.persist_json_sync(&evidence_dir).unwrap();
    assert!(saved_path.is_file());
    assert_ne!(evidence.evidence_digest_sha256, [0u8; 32]);
}

// ----------------------------------------------------------------------------
// SD-002: Socket AF_UNIX directo fuera del canal autorizado del broker
// Vector: El proceso del agente establece comunicación mediante un socket
//         AF_UNIX no declarado en AuthorityGraph.
// ----------------------------------------------------------------------------
#[test]
fn test_shadow_diff_sd_002_direct_af_unix_socket_bypass_falsifies_isolation() {
    use std::io::{Read, Write};
    use std::os::unix::net::{UnixListener, UnixStream};

    let sb = OmegaSandboxDir::new("sd_002_unix_socket");
    let protected_dir = sb.path().join("protected_vault");
    let evidence_dir = sb.path().join("cortex_evidence");
    let authorized_broker_sock = sb.path().join("broker.sock");
    let rogue_peer_sock = sb.path().join("shadow_peer.sock");
    fs::create_dir_all(&protected_dir).unwrap();

    let confinement =
        MacOsAgentConfinement::new(&[&protected_dir], Some(&authorized_broker_sock));
    let declared_graph = confinement.build_authority_graph("agent_edin", "babylon_broker");
    assert!(declared_graph.verify_complete_mediation().complete_mediation_holds);

    // Canal AF_UNIX no declarado abierto dentro del perímetro
    let listener = UnixListener::bind(&rogue_peer_sock).unwrap();
    let mut client = UnixStream::connect(&rogue_peer_sock).unwrap();
    let (mut accepted, _) = listener.accept().unwrap();

    client.write_all(b"SD002_UNMEDIATED_IPC_FRAME").unwrap();
    let mut buf = [0u8; 26];
    accepted.read_exact(&mut buf).unwrap();
    assert_eq!(&buf, b"SD002_UNMEDIATED_IPC_FRAME");

    // Observar el proceso mientras el socket AF_UNIX directo permanece activo
    let snapshot = OsResourceObserver::observe_pid(std::process::id());
    assert!(snapshot.visibility.is_complete());

    let agent_node = AuthorityNode::AgentProcess("agent_edin".to_string());
    let report = ShadowEdgeDiff::evaluate(
        &declared_graph,
        &agent_node,
        std::slice::from_ref(&protected_dir),
        std::slice::from_ref(&authorized_broker_sock),
        &snapshot,
        &[],
        2001,
    );

    drop(accepted);
    drop(client);
    drop(listener);

    assert_eq!(report.verdict, ShadowDiffVerdict::Falsified);
    assert_eq!(report.verdict.as_str(), "FALSIFIED");
    assert!(
        report.shadow_edges.iter().any(|e| matches!(
            &e.to,
            AuthorityNode::IpcChannel(ch) if ch.contains("shadow_peer.sock")
        )),
        "ShadowEdgeDiff debe descubrir el canal IpcChannel(shadow_peer.sock) no declarado"
    );
    assert!(!report.augmented_mediation_verdict.complete_mediation_holds);

    let evidence = report.to_cortex_evidence("SD-002");
    let saved_path = evidence.persist_json_sync(&evidence_dir).unwrap();
    assert!(saved_path.is_file());
}

// ----------------------------------------------------------------------------
// SD-003: Escritura mediante mmap compartido tras cerrar el descriptor (close(fd))
// Vector: El recurso se proyecta en memoria con MAP_SHARED, se cierra el
//         descriptor numérico (desapareciendo de /dev/fd), y se muta la memoria.
// ----------------------------------------------------------------------------
#[test]
fn test_shadow_diff_sd_003_shared_mmap_mutation_after_close_fd_falsifies_isolation() {
    use std::os::unix::io::IntoRawFd;

    let sb = OmegaSandboxDir::new("sd_003_mmap_shared");
    let protected_dir = sb.path().join("protected_vault");
    let evidence_dir = sb.path().join("cortex_evidence");
    let broker_sock = sb.path().join("broker.sock");
    fs::create_dir_all(&protected_dir).unwrap();

    let mmapped_file = protected_dir.join("shared_region.bin");
    let initial_payload = b"CLEAN_MMAP_REGION_00000000000000";
    fs::write(&mmapped_file, initial_payload).unwrap();

    let pre_witness = PhysicalResourceWitness::capture_pre_state(&mmapped_file).unwrap();

    let confinement = MacOsAgentConfinement::new(&[&protected_dir], Some(&broker_sock));
    let declared_graph = confinement.build_authority_graph("agent_edin", "babylon_broker");
    assert!(declared_graph.verify_complete_mediation().complete_mediation_holds);

    let file = fs::OpenOptions::new()
        .read(true)
        .write(true)
        .open(&mmapped_file)
        .unwrap();
    let raw_fd = file.into_raw_fd();
    let map_len = initial_payload.len();

    let map_ptr = unsafe {
        libc::mmap(
            std::ptr::null_mut(),
            map_len,
            libc::PROT_READ | libc::PROT_WRITE,
            libc::MAP_SHARED,
            raw_fd,
            0,
        )
    };
    assert_ne!(map_ptr, libc::MAP_FAILED, "mmap(MAP_SHARED) debe tener éxito");

    // Cerrar el descriptor numérico ANTES de mutar y observar: ya no existe fd en /dev/fd
    let close_rc = unsafe { libc::close(raw_fd) };
    assert_eq!(close_rc, 0, "close(raw_fd) debe cerrar el descriptor dejando viva la región mmap");

    // Mutar directamente a través de la proyección en memoria y sincronizar con el vnode
    let mutation = b"SD003_SHADOW_MMAP_WRITE_BYPASS!!";
    unsafe {
        std::ptr::copy_nonoverlapping(mutation.as_ptr(), map_ptr as *mut u8, map_len);
        libc::msync(map_ptr, map_len, libc::MS_SYNC);
    }

    // Observar el proceso mientras la región MAP_SHARED (ftxt/fmem) sigue mapeada en el VFS
    let snapshot = OsResourceObserver::observe_pid(std::process::id());

    unsafe {
        libc::munmap(map_ptr, map_len);
    }

    let post_witness = pre_witness.observe_post_state(false).unwrap();
    assert!(post_witness.unmediated_mutation_occurred());

    let agent_node = AuthorityNode::AgentProcess("agent_edin".to_string());
    let report = ShadowEdgeDiff::evaluate(
        &declared_graph,
        &agent_node,
        std::slice::from_ref(&protected_dir),
        std::slice::from_ref(&broker_sock),
        &snapshot,
        &[post_witness],
        3001,
    );

    assert_eq!(report.verdict, ShadowDiffVerdict::Falsified);
    assert_eq!(report.verdict.as_str(), "FALSIFIED");
    assert!(
        report
            .shadow_edges
            .iter()
            .any(|e| e.mechanism.contains("mmap") || e.mechanism.contains("unmediated")),
        "ShadowEdgeDiff debe capturar la arista de memoria compartida MAP_SHARED"
    );
    assert!(!report.augmented_mediation_verdict.complete_mediation_holds);

    let evidence = report.to_cortex_evidence("SD-003");
    let saved_path = evidence.persist_json_sync(&evidence_dir).unwrap();
    assert!(saved_path.is_file());
}

// ----------------------------------------------------------------------------
// SD-004: Descriptor abierto y cerrado rápidamente (invisible al sondeo puntual)
// Vector: Una operación efímera open -> write -> close finaliza antes de que
//         el observador por sondeo (lsof) tome su instantánea.
//         1) El sondeo puntual por sí solo NO ve anomalías y DEBE devolver
//            INCONCLUSIVE (nunca SUPPORTED_WITHIN_DOMAIN).
//         2) Al incorporar el testigo físico independiente del recurso,
//            ShadowEdgeDiff descubre la mutación efímera y emite FALSIFIED.
// ----------------------------------------------------------------------------
#[test]
fn test_shadow_diff_sd_004_ephemeral_open_write_close_race_inconclusive_then_falsified() {
    let sb = OmegaSandboxDir::new("sd_004_ephemeral_fd");
    let protected_dir = sb.path().join("protected_vault");
    let evidence_dir = sb.path().join("cortex_evidence");
    let broker_sock = sb.path().join("broker.sock");
    fs::create_dir_all(&protected_dir).unwrap();

    let target_file = protected_dir.join("ephemeral_target.dat");
    fs::write(&target_file, b"STATE_BEFORE_EPHEMERAL_RACE").unwrap();

    let pre_witness = PhysicalResourceWitness::capture_pre_state(&target_file).unwrap();

    let confinement = MacOsAgentConfinement::new(&[&protected_dir], Some(&broker_sock));
    let declared_graph = confinement.build_authority_graph("agent_edin", "babylon_broker");

    // Operación ultrarrápida open -> write -> close ANTES del sondeo de OsResourceObserver
    {
        use std::io::Write;
        let mut f = fs::OpenOptions::new()
            .write(true)
            .truncate(true)
            .open(&target_file)
            .unwrap();
        f.write_all(b"SD004_TRANSIENT_FD_ALREADY_CLOSED").unwrap();
        f.sync_all().unwrap();
    } // Descriptor cerrado aquí

    // Cuando el observador por sondeo toma la muestra, el descriptor ya no existe en la tabla
    let snapshot = OsResourceObserver::observe_pid(std::process::id());
    assert_eq!(snapshot.modality, ObservationModality::PointInTimePolling);

    let agent_node = AuthorityNode::AgentProcess("agent_edin".to_string());

    // Parte A: Solo sondeo puntual (sin testigo físico). Cero anomalías en la tabla de FDs,
    // pero un sondeo puntual sin anomalías NO demuestra aislamiento -> INCONCLUSIVE.
    let report_polling_only = ShadowEdgeDiff::evaluate(
        &declared_graph,
        &agent_node,
        std::slice::from_ref(&protected_dir),
        std::slice::from_ref(&broker_sock),
        &snapshot,
        &[],
        4001,
    );
    assert!(
        report_polling_only.shadow_edges.is_empty(),
        "El sondeo puntual después de close() no ve el descriptor efímero en la tabla OS"
    );
    assert_eq!(
        report_polling_only.verdict,
        ShadowDiffVerdict::Inconclusive,
        "SD-004: NO ANOMALY en un observador por sondeo sin testigo físico debe ser INCONCLUSIVE"
    );
    assert_eq!(report_polling_only.verdict.as_str(), "INCONCLUSIVE");

    // Parte B: Sondeo puntual + testigo físico independiente -> FALSIFIED
    let post_witness = pre_witness.observe_post_state(false).unwrap();
    let report_with_witness = ShadowEdgeDiff::evaluate(
        &declared_graph,
        &agent_node,
        std::slice::from_ref(&protected_dir),
        std::slice::from_ref(&broker_sock),
        &snapshot,
        &[post_witness],
        4002,
    );
    assert_eq!(report_with_witness.verdict, ShadowDiffVerdict::Falsified);
    assert_eq!(report_with_witness.verdict.as_str(), "FALSIFIED");
    assert_eq!(report_with_witness.unmediated_mutations.len(), 1);
    assert!(!report_with_witness.shadow_edges.is_empty());

    let evidence = report_with_witness.to_cortex_evidence("SD-004");
    let saved_path = evidence.persist_json_sync(&evidence_dir).unwrap();
    assert!(saved_path.is_file());
}

// ----------------------------------------------------------------------------
// SD-005: Fallo de permisos del observador (visibilidad incompleta != seguridad)
// Vector: El observador intenta inspeccionar un proceso sin permisos suficientes
//         (ej. PID 1 launchd en macOS o error EPERM). La lista vacía devuelta por
//         el fallo del observador NUNCA debe interpretarse como SUPPORTED_WITHIN_DOMAIN.
// ----------------------------------------------------------------------------
#[test]
fn test_shadow_diff_sd_005_observer_permission_failure_returns_inconclusive() {
    let sb = OmegaSandboxDir::new("sd_005_observer_perm");
    let protected_dir = sb.path().join("protected_vault");
    let evidence_dir = sb.path().join("cortex_evidence");
    let broker_sock = sb.path().join("broker.sock");
    fs::create_dir_all(&protected_dir).unwrap();

    let target_file = protected_dir.join("asset.dat");
    fs::write(&target_file, b"INTACT_ASSET").unwrap();
    let intact_witness = PhysicalResourceWitness::capture_pre_state(&target_file)
        .unwrap()
        .observe_post_state(false)
        .unwrap();

    let confinement = MacOsAgentConfinement::new(&[&protected_dir], Some(&broker_sock));
    let declared_graph = confinement.build_authority_graph("agent_edin", "babylon_broker");

    // En macOS no-root, inspeccionar PID 1 (launchd) o PID 0 falla por permisos en proc_pidinfo/lsof
    let mut snapshot = OsResourceObserver::observe_pid(1);
    if snapshot.visibility.is_complete() {
        // Fallback determinista si el runner de pruebas se ejecutara como root
        snapshot = ProcessResourceSnapshot::permission_denied(
            1,
            "EPERM: simulated unprivileged proc_pidinfo rejection",
        );
    }
    assert!(
        !snapshot.visibility.is_complete(),
        "SD-005: la visibilidad sobre un proceso restringido debe marcarse como incompleta/denegada"
    );
    assert!(snapshot.entries.is_empty());

    let agent_node = AuthorityNode::AgentProcess("agent_edin".to_string());
    // Incluso con un testigo físico intacto y cero aristas sombra observadas, la visibilidad
    // incompleta del observador fuerza deterministamente el veredicto INCONCLUSIVE.
    let report = ShadowEdgeDiff::evaluate(
        &declared_graph,
        &agent_node,
        std::slice::from_ref(&protected_dir),
        std::slice::from_ref(&broker_sock),
        &snapshot,
        &[intact_witness],
        5001,
    );

    assert_eq!(
        report.verdict,
        ShadowDiffVerdict::Inconclusive,
        "SD-005: el fallo de permisos del observador jamás debe clasificarse como SUPPORTED_WITHIN_DOMAIN"
    );
    assert_eq!(report.verdict.as_str(), "INCONCLUSIVE");
    assert!(
        SecurityMechanismPlane::EmpiricalObservation.can_falsify_isolation()
    );
    assert!(
        !SecurityMechanismPlane::EmpiricalObservation.can_prevent_effect()
    );

    let evidence = report.to_cortex_evidence("SD-005");
    let saved_path = evidence.persist_json_sync(&evidence_dir).unwrap();
    assert!(saved_path.is_file());
}

// ----------------------------------------------------------------------------
// CONTROL POSITIVO, ESTADO UNTESTED Y MICRO-BENCHMARK DETERMINISTA
// Verifica que los 4 veredictos (SUPPORTED_WITHIN_DOMAIN, FALSIFIED,
// INCONCLUSIVE, UNTESTED) sean alcanzables bajo sus precondiciones exactas.
// ----------------------------------------------------------------------------
#[test]
fn test_shadow_diff_verdict_completeness_and_benchmark() {
    use std::time::Instant;

    let sb = OmegaSandboxDir::new("sd_control_and_bench");
    let protected_dir = sb.path().join("protected_vault");
    let broker_sock = sb.path().join("broker.sock");
    fs::create_dir_all(&protected_dir).unwrap();

    let protected_file = protected_dir.join("guarded.dat");
    fs::write(&protected_file, b"SOVEREIGN_GUARDED_PAYLOAD").unwrap();
    let pre_witness = PhysicalResourceWitness::capture_pre_state(&protected_file).unwrap();

    let confinement = MacOsAgentConfinement::new(&[&protected_dir], Some(&broker_sock));
    let declared_graph = confinement.build_authority_graph("agent_edin", "babylon_broker");
    let agent_node = AuthorityNode::AgentProcess("agent_edin".to_string());

    // 1. Verificar estado UNTESTED
    let untested_snap = ProcessResourceSnapshot::untested(std::process::id());
    let untested_report = ShadowEdgeDiff::evaluate(
        &declared_graph,
        &agent_node,
        std::slice::from_ref(&protected_dir),
        std::slice::from_ref(&broker_sock),
        &untested_snap,
        &[],
        6001,
    );
    assert_eq!(untested_report.verdict, ShadowDiffVerdict::Untested);
    assert_eq!(untested_report.verdict.as_str(), "UNTESTED");

    // 2. Verificar SUPPORTED_WITHIN_DOMAIN cuando:
    //    - Visibilidad del observador es Complete
    //    - Cero aristas sombra hacia protected_dir
    //    - Testigo físico independiente confirma ausencia de mutación no mediada
    let clean_snap = OsResourceObserver::observe_pid(std::process::id());
    let post_witness = pre_witness.observe_post_state(false).unwrap();
    let supported_report = ShadowEdgeDiff::evaluate(
        &declared_graph,
        &agent_node,
        std::slice::from_ref(&protected_dir),
        std::slice::from_ref(&broker_sock),
        &clean_snap,
        std::slice::from_ref(&post_witness),
        6002,
    );
    assert_eq!(
        supported_report.verdict,
        ShadowDiffVerdict::SupportedWithinDomain
    );
    assert_eq!(supported_report.verdict.as_str(), "SUPPORTED_WITHIN_DOMAIN");
    assert_eq!(
        supported_report.mechanism_plane,
        SecurityMechanismPlane::EmpiricalObservation
    );

    // 3. Micro-benchmark con warmup previo (PoC & Stress Testing Invariant) sobre 1000 iteraciones de ShadowEdgeDiff
    for warmup_tick in 0..50u64 {
        let rep = ShadowEdgeDiff::evaluate(
            &declared_graph,
            &agent_node,
            std::slice::from_ref(&protected_dir),
            std::slice::from_ref(&broker_sock),
            &clean_snap,
            std::slice::from_ref(&post_witness),
            6900 + warmup_tick,
        );
        std::hint::black_box(rep);
    }
    let t0 = Instant::now();
    for tick in 0..1_000u64 {
        let rep = ShadowEdgeDiff::evaluate(
            &declared_graph,
            &agent_node,
            std::slice::from_ref(&protected_dir),
            std::slice::from_ref(&broker_sock),
            &clean_snap,
            std::slice::from_ref(&post_witness),
            7000 + tick,
        );
        std::hint::black_box(rep);
    }
    let elapsed_diff_1k = t0.elapsed();
    assert!(
        elapsed_diff_1k.as_millis() < 3_500,
        "1000 evaluaciones de ShadowEdgeDiff deben completarse dentro del presupuesto (observado: {:?})",
        elapsed_diff_1k
    );
}

