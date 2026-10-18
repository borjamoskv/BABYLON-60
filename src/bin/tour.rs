//! # BABYLON-60 — Tour Interactivo / Quickstart Determinista
//!
//! Demostración en 4 pasos del contrato central de BABYLON-60:
//! «El agente propone, pero no se autoriza a sí mismo».
//!
//! 1. Proposición: El agente genera una intención (`ProposedIntent`).
//! 2. Control de Acceso: El runtime exige una autorización criptográfica (`SignedAuthorization`).
//! 3. Ejecución Ligada: El executor deriva el efecto inyectivamente de la intención (`parse_intent`).
//! 4. Crash Recovery: Auditoría durable tras un fallo forzado (prevención de replay).

use std::path::PathBuf;
use std::time::{SystemTime, UNIX_EPOCH};

use babylon60::executor::{
    AdmittedAuthority, AuthorityAlgorithm, AuthorizationPayload,
    DurableExecutionStore, EffectAdapter, ExecutionError, IdempotencyContract, ProposedIntent,
    SecurityPolicy, SignedAuthorization, SovereignExecutor, PROTOCOL_VERSION,
};
use sha2::{Digest, Sha256};

const INSTALLATION_ID: [u8; 32] = [0x42; 32];
const EXECUTOR_ID: [u8; 32] = [0x60; 32];

// Adaptador de Recurso: Archivo de Balance Protegido
struct BalanceAdapter;

#[derive(Debug)]
struct BalanceError(String);
impl std::fmt::Display for BalanceError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        f.write_str(&self.0)
    }
}

impl EffectAdapter for BalanceAdapter {
    type Resource = (PathBuf, u64); // (Ruta, Balance)
    type Effect = u64;              // Cantidad a transferir
    type Output = u64;              // Nuevo balance
    type Error = BalanceError;

    // AX-0: El efecto se deriva OBLIGATORIAMENTE de los parámetros de la intención
    fn parse_intent(&self, intent: &ProposedIntent) -> Result<Self::Effect, Self::Error> {
        if intent.parameters.len() != 8 {
            return Err(BalanceError("Parámetros inválidos (se requiere u64 de 8 bytes)".into()));
        }
        let mut buf = [0u8; 8];
        buf.copy_from_slice(&intent.parameters);
        Ok(u64::from_be_bytes(buf))
    }

    fn compute_precondition(&self, resource: &Self::Resource) -> Result<[u8; 32], BalanceError> {
        let mut h = Sha256::new();
        h.update(b"BABYLON60/balance/precondition");
        h.update(resource.1.to_be_bytes());
        Ok(h.finalize().into())
    }

    fn apply_effect(
        &mut self,
        resource: &mut Self::Resource,
        expected: &[u8; 32],
        _nonce: &[u8; 32],
        amount: &u64,
    ) -> Result<u64, BalanceError> {
        if &self.compute_precondition(resource)? != expected {
            return Err(BalanceError("Precondición rota (concurrencia detectada)".into()));
        }
        resource.1 += amount;
        Ok(resource.1)
    }

    fn idempotency_contract(&self) -> IdempotencyContract {
        IdempotencyContract::NonIdempotentExplicitIntervention
    }
}

fn now() -> u64 {
    SystemTime::now().duration_since(UNIX_EPOCH).unwrap().as_secs()
}

fn main() {
    println!("\n╔══════════════════════════════════════════════════════════════════════╗");
    println!("║       BABYLON-60 · DEMOSTRACIÓN DE GARANTÍAS DE RING-0 (AX-0)        ║");
    println!("╚══════════════════════════════════════════════════════════════════════╝\n");

    let tmp_dir = std::env::temp_dir().join(format!("b60_demo_{}", now()));
    std::fs::create_dir_all(&tmp_dir).unwrap();
    let db_path = tmp_dir.join("ledger.sqlite");

    // 1. Configurar Autoridad Externa (Oráculo Frío / Fuera de la IA)
    let sk = ed25519_dalek::SigningKey::generate(&mut rand::rngs::OsRng);
    let pk = sk.verifying_key().to_bytes().to_vec();
    let signer = babylon60::receipt::Ed25519Signer::from_signing_key(sk);

    let store = DurableExecutionStore::open(db_path.to_str().unwrap()).unwrap();
    let mut executor = SovereignExecutor::new(
        INSTALLATION_ID,
        EXECUTOR_ID,
        1,
        vec![AdmittedAuthority {
            public_key: pk.clone(),
            algorithm: AuthorityAlgorithm::Ed25519,
        }],
        store,
        BalanceAdapter,
    );

    let mut resource = (tmp_dir.join("vault.dat"), 1000u64);
    println!("▸ Estado Inicial del Recurso Protegido: Balance = {} créditos", resource.1);

    // ──────────────────────────────────────────────────────────────────────────
    // PASO 1: El agente propone una operación (Intent)
    // ──────────────────────────────────────────────────────────────────────────
    println!("\n[PASO 1] El Agente de IA propone una mutación de estado...");
    let transfer_amount = 500u64;
    let intent = ProposedIntent {
        intent_id: [0x11; 32],
        target_resource: "vault.dat".into(),
        action_name: "DEPOSIT".into(),
        parameters: transfer_amount.to_be_bytes().to_vec(),
    };
    println!("  ✓ Intención generada: Acción='{}', Monto={} créditos", intent.action_name, transfer_amount);

    let policy = SecurityPolicy {
        policy_id: [0x99; 32],
        allowed_action: "DEPOSIT".into(),
        max_allowed_uses: 1,
        admitted_authority_key: pk.clone(),
    };

    // ──────────────────────────────────────────────────────────────────────────
    // PASO 2: Intento de auto-autorización o ataque de falsificación
    // ──────────────────────────────────────────────────────────────────────────
    println!("\n[PASO 2] Prueba Adversarial: ¿Puede el agente ejecutar sin la Autoridad externa?");
    let rogue_sk = ed25519_dalek::SigningKey::generate(&mut rand::rngs::OsRng);
    let rogue_signer = babylon60::receipt::Ed25519Signer::from_signing_key(rogue_sk);
    let pre = executor.adapter.compute_precondition(&resource).unwrap();

    let rogue_payload = AuthorizationPayload {
        protocol_version: PROTOCOL_VERSION,
        installation_id: INSTALLATION_ID,
        executor_id: EXECUTOR_ID,
        intent_digest: intent.compute_digest(),
        policy_digest: policy.compute_digest(),
        resource_precondition_digest: pre,
        nonce: [0xAA; 32],
        authority_epoch: 1,
        expires_at: now() + 300,
        max_uses: 1,
    };
    let rogue_auth = SignedAuthorization::new_cose(&rogue_payload, &rogue_signer).unwrap();

    match executor.execute_action(&rogue_auth, &intent, &policy, &mut resource, now()) {
        Err(ExecutionError::InvalidAuthorityKey(_)) => {
            println!("  🛡️ BLOQUEO DETERMINISTA (AX-0): La clave del agente NO está admitida en el silicio.");
        }
        other => panic!("Fallo de seguridad inesperado: {:?}", other),
    }

    // ──────────────────────────────────────────────────────────────────────────
    // PASO 3: Autorización legítima y ejecución causalmente ligada
    // ──────────────────────────────────────────────────────────────────────────
    println!("\n[PASO 3] Flujo Nominal: La Autoridad Legítima firma la autorización...");
    let legitimate_payload = AuthorizationPayload {
        protocol_version: PROTOCOL_VERSION,
        installation_id: INSTALLATION_ID,
        executor_id: EXECUTOR_ID,
        intent_digest: intent.compute_digest(),
        policy_digest: policy.compute_digest(),
        resource_precondition_digest: pre,
        nonce: [0xBB; 32],
        authority_epoch: 1,
        expires_at: now() + 300,
        max_uses: 1,
    };
    let valid_auth = SignedAuthorization::new_cose(&legitimate_payload, &signer).unwrap();

    let new_balance = executor
        .execute_action(&valid_auth, &intent, &policy, &mut resource, now())
        .expect("La ejecución autorizada debe ser exitosa");

    println!("  ✓ Transducción exitosa: Efecto derivado inyectivamente de la Intención.");
    println!("  ✓ Nuevo Balance en el Recurso: {} créditos", new_balance);

    // ──────────────────────────────────────────────────────────────────────────
    // PASO 4: Auditoría y Crash Consistency (Replay Attack Post-Fallo)
    // ──────────────────────────────────────────────────────────────────────────
    println!("\n[PASO 4] Resiliencia de Protocolo (En Memoria): Intento de re-ejecución (Replay Attack)...");
    match executor.execute_action(&valid_auth, &intent, &policy, &mut resource, now()) {
        Err(ExecutionError::NonceAlreadyConsumed(_)) => {
            println!("  🛡️ PROTECCIÓN LÓGICA: El nonce fue marcado como consumido en la instancia.");
            println!("  🛡️ Replay bloqueado con éxito: La gramática del protocolo evita duplicar mutaciones.");
        }
        other => panic!("Fallo en detección de replay: {:?}", other),
    }

    println!("\n========================================================================");
    println!("  VEREDICTO FINAL: Secuencia lógica y gramática de autorización (AX-0) verificada con éxito.");
    println!("  Nota: Esta es una simulación en un mismo proceso de SO (in-memory resource).");
    println!("  Las pruebas de aislamiento, persistencia física y recuperación de crash");
    println!("  se auditan en tests de integración separados en el framework C5-REAL.");
    println!("========================================================================\n");
}
