//! # BABYLON-60 v5 — Executor: autorización determinada, reserva durable, UNKNOWN
//!
//! ## Qué garantiza este módulo (y qué NO)
//!
//! Garantiza, para efectos despachados por este executor:
//! - Una autorización sólo se acepta si está firmada por una clave admitida **y** ligada
//!   a la política evaluada, la instalación, el executor, la intención, la precondición,
//!   la época de autoridad y una ventana de vigencia.
//! - El nonce se consume en una transacción SQLite (`BEGIN IMMEDIATE`, WAL,
//!   `synchronous=FULL`, `fullfsync=ON`) **antes** de registrar el dispatch.
//! - Un dispatch sin resultado se reclasifica como `UNKNOWN` al reiniciar y nunca se
//!   repite automáticamente.
//! - Errores de almacenamiento son fail-closed (nunca se interpretan como "nonce libre").
//!
//! NO garantiza:
//! - **Aislamiento de privilegios (AX-0 a nivel de SO).** Que EDIN no pueda llamar
//!   directamente a `os.remove()` depende de procesos, usuarios, sandbox y descriptores,
//!   no de este código. Un campo "dominio del proponente" autodeclarado no constituye
//!   separación de autoridad y por eso no existe aquí.
//! - Exactly-once frente a destinos externos (requiere idempotencia del destino).
//! - Durabilidad ante pérdida de energía: el arnés `poc_v5_crash_harness` prueba
//!   muerte de proceso (SIGKILL); la caché de páginas del SO sobrevive a eso.
//! - Reanudación de reservas `RESERVED` sin dispatch: hoy quedan bloqueadas
//!   (más restrictivo que el contrato; la autorización completa queda almacenada
//!   para habilitar esa reanudación en una iteración posterior).

extern crate alloc;
use core::sync::atomic::{AtomicBool, AtomicU64, Ordering};
use std::sync::{Arc, RwLock, RwLockReadGuard};

use rusqlite::{params, Connection, OptionalExtension};
use sha2::{Digest, Sha256};

// ---------------------------------------------------------------------------
// Constantes de perfil
// ---------------------------------------------------------------------------

/// Única versión de protocolo aceptada por este executor.
pub const PROTOCOL_VERSION: u16 = 5;

/// Tamaño exacto del payload canónico (big-endian, sin padding).
pub const AUTHORIZATION_PAYLOAD_CANONICAL_SIZE: usize = 214;

/// Etiqueta de separación de dominio para la firma de autorizaciones.
pub const AUTH_SIGNING_CONTEXT: &[u8] = b"BABYLON60/authorization/v5";

// ---------------------------------------------------------------------------
// Digests con separación de dominio y prefijo de longitud
// ---------------------------------------------------------------------------

/// Hasher canónico: etiqueta de dominio + campos con prefijo de longitud u64 BE.
/// Evita ambigüedad de concatenación: ("ab","c") ≠ ("a","bc").
pub(crate) struct CanonicalHasher(Sha256);

impl CanonicalHasher {
    pub(crate) fn new(domain: &[u8]) -> Self {
        let mut h = Sha256::new();
        h.update((domain.len() as u64).to_be_bytes());
        h.update(domain);
        Self(h)
    }
    pub(crate) fn field(mut self, bytes: &[u8]) -> Self {
        self.0.update((bytes.len() as u64).to_be_bytes());
        self.0.update(bytes);
        self
    }
    pub(crate) fn finish(self) -> [u8; 32] {
        self.0.finalize().into()
    }
}

// ---------------------------------------------------------------------------
// Payload de autorización
// ---------------------------------------------------------------------------

/// Operación completamente determinada que una autoridad firma.
#[derive(Debug, Clone, PartialEq, Eq)]
#[cfg_attr(feature = "cortex-persist", derive(serde::Serialize, serde::Deserialize))]
pub struct AuthorizationPayload {
    /// Versión de protocolo (debe ser [`PROTOCOL_VERSION`]).
    pub protocol_version: u16,
    /// Identidad de la instalación.
    pub installation_id: [u8; 32],
    /// Identidad del executor destinatario.
    pub executor_id: [u8; 32],
    /// Digest de la intención propuesta.
    pub intent_digest: [u8; 32],
    /// Digest de la política evaluada.
    pub policy_digest: [u8; 32],
    /// Digest del estado del recurso en el momento de autorizar.
    pub resource_precondition_digest: [u8; 32],
    /// Nonce de un solo uso.
    pub nonce: [u8; 32],
    /// Época de autoridad (revocación monótona).
    pub authority_epoch: u64,
    /// Fin exclusivo de vigencia (segundos Unix).
    pub expires_at: u64,
    /// Usos máximos. Este executor sólo admite 1.
    pub max_uses: u32,
}

impl AuthorizationPayload {
    /// Serialización canónica de 214 bytes (big-endian, orden fijo de campos).
    pub fn to_canonical_bytes(&self) -> [u8; AUTHORIZATION_PAYLOAD_CANONICAL_SIZE] {
        let mut buf = [0u8; AUTHORIZATION_PAYLOAD_CANONICAL_SIZE];
        let mut o = 0usize;
        let mut put = |src: &[u8]| {
            buf[o..o + src.len()].copy_from_slice(src);
            o += src.len();
        };
        put(&self.protocol_version.to_be_bytes());
        put(&self.installation_id);
        put(&self.executor_id);
        put(&self.intent_digest);
        put(&self.policy_digest);
        put(&self.resource_precondition_digest);
        put(&self.nonce);
        put(&self.authority_epoch.to_be_bytes());
        put(&self.expires_at.to_be_bytes());
        put(&self.max_uses.to_be_bytes());
        buf
    }

    /// Deserialización estricta: longitud exacta, sin bytes sobrantes.
    pub fn from_canonical_bytes(bytes: &[u8]) -> Result<Self, ExecutionError> {
        if bytes.len() != AUTHORIZATION_PAYLOAD_CANONICAL_SIZE {
            return Err(ExecutionError::MalformedAuthorization(format!(
                "expected {} bytes, got {}",
                AUTHORIZATION_PAYLOAD_CANONICAL_SIZE,
                bytes.len()
            )));
        }
        let mut o = 0usize;
        let mut take = |n: usize| {
            let s = &bytes[o..o + n];
            o += n;
            s
        };
        let arr32 = |s: &[u8]| {
            let mut a = [0u8; 32];
            a.copy_from_slice(s);
            a
        };
        let protocol_version = u16::from_be_bytes(take(2).try_into().unwrap());
        let installation_id = arr32(take(32));
        let executor_id = arr32(take(32));
        let intent_digest = arr32(take(32));
        let policy_digest = arr32(take(32));
        let resource_precondition_digest = arr32(take(32));
        let nonce = arr32(take(32));
        let authority_epoch = u64::from_be_bytes(take(8).try_into().unwrap());
        let expires_at = u64::from_be_bytes(take(8).try_into().unwrap());
        let max_uses = u32::from_be_bytes(take(4).try_into().unwrap());
        Ok(Self {
            protocol_version,
            installation_id,
            executor_id,
            intent_digest,
            policy_digest,
            resource_precondition_digest,
            nonce,
            authority_epoch,
            expires_at,
            max_uses,
        })
    }

    /// Bytes efectivamente firmados: contexto de dominio ‖ payload canónico.
    pub fn signing_input(&self) -> Vec<u8> {
        let mut v = Vec::with_capacity(AUTH_SIGNING_CONTEXT.len() + AUTHORIZATION_PAYLOAD_CANONICAL_SIZE);
        v.extend_from_slice(AUTH_SIGNING_CONTEXT);
        v.extend_from_slice(&self.to_canonical_bytes());
        v
    }
}

/// Algoritmo de la autoridad.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
#[cfg_attr(feature = "cortex-persist", derive(serde::Serialize, serde::Deserialize))]
pub enum AuthorityAlgorithm {
    /// Ed25519 (RFC 8032), verificación estricta.
    Ed25519,
    /// ECDSA P-256 (Secure Enclave). Firma DER; clave SEC1.
    P256,
}

impl AuthorityAlgorithm {
    #[allow(dead_code)]
    fn tag(self) -> u8 {
        match self {
            AuthorityAlgorithm::Ed25519 => 1,
            AuthorityAlgorithm::P256 => 2,
        }
    }
}

/// Autorización firmada encapsulada en formato COSE_Sign1.
#[derive(Debug, Clone, PartialEq, Eq)]
#[cfg_attr(feature = "cortex-persist", derive(serde::Serialize, serde::Deserialize))]
pub struct SignedAuthorization {
    /// Bytes serializados de la estructura COSE_Sign1 RFC 9052 / RFC 9942.
    pub cose_bytes: Vec<u8>,
}

impl SignedAuthorization {
    /// Construye una nueva autorización firmada a partir de un payload y un firmante criptográfico.
    pub fn new_cose<S: crate::receipt::Signer>(
        payload: &AuthorizationPayload,
        signer: &S,
    ) -> Result<Self, ExecutionError> {
        use coset::{HeaderBuilder, CoseSign1Builder};
        let public_key = signer.get_public_key();
        if public_key.is_empty() {
            return Err(ExecutionError::InvalidAuthorityKey(
                "Configure the admitted public key before signing".into()));
        }
        let protected = HeaderBuilder::new()
            .algorithm(signer.algorithm())
            .key_id(public_key)
            .build();
        let payload_bytes = payload.to_canonical_bytes().to_vec();
        let sign1 = CoseSign1Builder::new()
            .protected(protected)
            .payload(payload_bytes)
            .try_create_signature(&[], |data| signer.sign(data))
            .map_err(|e| ExecutionError::InvalidSignature(alloc::format!("{:?}", e)))?
            .build();
        
        use coset::CborSerializable;
        Ok(Self {
            cose_bytes: sign1.to_vec().unwrap(),
        })
    }

    /// Deserializa y extrae el payload canónico, el ID de clave y el algoritmo de la autorización.
    pub fn parse(&self) -> Result<(AuthorizationPayload, Vec<u8>, AuthorityAlgorithm), ExecutionError> {
        use coset::CborSerializable;
        use coset::CoseSign1;
        let sign1 = CoseSign1::from_slice(&self.cose_bytes)
            .map_err(|_| ExecutionError::MalformedAuthorization("Invalid COSE".into()))?;
        let alg = match sign1.protected.header.alg {
            Some(coset::Algorithm::Assigned(a)) => a,
            _ => return Err(ExecutionError::MalformedAuthorization("Missing alg".into())),
        };
        let auth_alg = match alg {
            coset::iana::Algorithm::EdDSA => AuthorityAlgorithm::Ed25519,
            coset::iana::Algorithm::ES256 => AuthorityAlgorithm::P256,
            _ => return Err(ExecutionError::UnsupportedProtocolVersion(999)),
        };
        if sign1.protected.header.key_id.is_empty()
            || !sign1.unprotected.key_id.is_empty()
            || sign1.unprotected.alg.is_some()
            || !sign1.protected.header.crit.is_empty()
            || !sign1.unprotected.crit.is_empty()
        {
            return Err(ExecutionError::MalformedAuthorization(
                "unsupported COSE header profile".into(),
            ));
        }
        let kid = sign1.protected.header.key_id.clone();
        let payload_bytes = sign1.payload.as_ref().ok_or(ExecutionError::MalformedAuthorization("Missing payload".into()))?;
        let payload = AuthorizationPayload::from_canonical_bytes(payload_bytes)?;
        Ok((payload, kid, auth_alg))
    }

    /// Valida criptográficamente la firma COSE_Sign1 contra el payload canónico.
    pub fn verify_signature(&self) -> Result<(), ExecutionError> {
        use coset::CborSerializable;
        use coset::CoseSign1;
        let (_, kid, auth_alg) = self.parse()?;
        let sign1 = CoseSign1::from_slice(&self.cose_bytes).unwrap();
        sign1.verify_signature(&[], |sig, data| {
            match auth_alg {
                AuthorityAlgorithm::Ed25519 => {
                    let pk: [u8; 32] = kid.as_slice().try_into().map_err(|_| "ed25519 key must be 32 bytes")?;
                    let sig_arr: [u8; 64] = sig.try_into().map_err(|_| "ed25519 sig must be 64 bytes")?;
                    let vk = ed25519_dalek::VerifyingKey::from_bytes(&pk).map_err(|_| "invalid ed25519 key")?;
                    vk.verify_strict(data, &ed25519_dalek::Signature::from_bytes(&sig_arr)).map_err(|_| "verification failed")
                }
                AuthorityAlgorithm::P256 => {
                    use p256::ecdsa::{signature::Verifier, Signature, VerifyingKey};
                    use p256::pkcs8::DecodePublicKey;
                    let vk = VerifyingKey::from_sec1_bytes(&kid)
                        .or_else(|_| VerifyingKey::from_public_key_der(&kid))
                        .map_err(|_| "invalid p256 key")?;
                    let sig = Signature::from_slice(sig)
                        .or_else(|_| Signature::from_der(sig))
                        .map_err(|_| "invalid p256 signature format")?;
                    vk.verify(data, &sig).map_err(|_| "p256 verification failed")
                }
            }
        }).map_err(|e| ExecutionError::InvalidSignature(alloc::format!("{:?}", e)))
    }

    fn archive_blob(&self) -> Vec<u8> {
        self.cose_bytes.clone()
    }
}

// ---------------------------------------------------------------------------
// Intención, política, autoridad admitida
// ---------------------------------------------------------------------------

/// Intención propuesta. No lleva identidad del proponente: la identidad no se
/// autodeclara; la impone el límite de proceso que entrega la intención.
#[derive(Debug, Clone, PartialEq, Eq)]
#[cfg_attr(feature = "cortex-persist", derive(serde::Serialize, serde::Deserialize))]
pub struct ProposedIntent {
    /// Identificador único.
    pub intent_id: [u8; 32],
    /// Recurso destino.
    pub target_resource: String,
    /// Acción solicitada.
    pub action_name: String,
    /// Parámetros serializados.
    pub parameters: Vec<u8>,
}

impl ProposedIntent {
    /// Digest canónico con separación de dominio.
    pub fn compute_digest(&self) -> [u8; 32] {
        CanonicalHasher::new(b"BABYLON60/intent/v1")
            .field(&self.intent_id)
            .field(self.target_resource.as_bytes())
            .field(self.action_name.as_bytes())
            .field(&self.parameters)
            .finish()
    }
}

/// Política evaluada por KISH.
#[derive(Debug, Clone, PartialEq, Eq)]
#[cfg_attr(feature = "cortex-persist", derive(serde::Serialize, serde::Deserialize))]
pub struct SecurityPolicy {
    /// Identificador.
    pub policy_id: [u8; 32],
    /// Única acción que esta política permite.
    pub allowed_action: String,
    /// Usos máximos permitidos por la política.
    pub max_allowed_uses: u32,
    /// Clave de autoridad que esta política reconoce.
    pub admitted_authority_key: Vec<u8>,
}

impl SecurityPolicy {
    /// Digest canónico con separación de dominio.
    pub fn compute_digest(&self) -> [u8; 32] {
        CanonicalHasher::new(b"BABYLON60/policy/v1")
            .field(&self.policy_id)
            .field(self.allowed_action.as_bytes())
            .field(&self.max_allowed_uses.to_be_bytes())
            .field(&self.admitted_authority_key)
            .finish()
    }
}

/// Autoridad admitida: clave + algoritmo fijado (el algoritmo no lo elige el firmante).
#[derive(Debug, Clone, PartialEq, Eq)]
#[cfg_attr(feature = "cortex-persist", derive(serde::Serialize, serde::Deserialize))]
pub struct AdmittedAuthority {
    /// Clave pública.
    pub public_key: Vec<u8>,
    /// Algoritmo obligatorio para esta clave.
    pub algorithm: AuthorityAlgorithm,
}

// ---------------------------------------------------------------------------
// Adaptadores de efectos (TOCTOU se resuelve aquí, por adaptador)
// ---------------------------------------------------------------------------

/// Garantía de idempotencia que publica cada adaptador.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum IdempotencyContract {
    /// Reintento seguro con la misma clave; el destino deduplica.
    VerifiableIdempotent,
    /// Sin idempotencia ni consulta fiable: UNKNOWN exige intervención.
    NonIdempotentExplicitIntervention,
}

/// Adaptador de efectos. Debe aplicar la precondición de forma atómica respecto al recurso.
pub trait EffectAdapter {
    /// Recurso gestionado.
    type Resource;
    /// Efecto a aplicar.
    type Effect;
    /// Resultado.
    type Output;
    /// Error del adaptador.
    type Error: core::fmt::Display;
    /// Transducción Causal: deriva inyectivamente el efecto desde la intención autorizada.
    fn parse_intent(&self, intent: &ProposedIntent) -> Result<Self::Effect, Self::Error>;
    /// Digest del estado actual del recurso.
    fn compute_precondition(&self, resource: &Self::Resource) -> Result<[u8; 32], Self::Error>;
    /// Aplica el efecto si y sólo si el recurso coincide con `expected_precondition`.
    fn apply_effect(
        &mut self,
        resource: &mut Self::Resource,
        expected_precondition: &[u8; 32],
        nonce: &[u8; 32],
        effect: &Self::Effect,
    ) -> Result<Self::Output, Self::Error>;
    /// Contrato de idempotencia publicado.
    fn idempotency_contract(&self) -> IdempotencyContract;
}


// ---------------------------------------------------------------------------
// Almacén durable
// ---------------------------------------------------------------------------


fn storage<E: core::fmt::Display>(ctx: &'static str) -> impl Fn(E) -> ExecutionError {
    move |e| ExecutionError::StorageError(format!("{}: {}", ctx, e))
}

/// Ledger de reservas sobre SQLite.
pub struct DurableExecutionStore {
    conn: Connection,
}

impl DurableExecutionStore {
    /// Abre (o crea) el ledger en `path`. Exige WAL efectivo en disco.
    pub fn open(path: &str) -> Result<Self, ExecutionError> {
        let conn = Connection::open(path).map_err(storage("open"))?;
        conn.busy_timeout(std::time::Duration::from_secs(30)).map_err(storage("busy_timeout"))?;
        let mode: String = conn
            .query_row("PRAGMA journal_mode = WAL", [], |r| r.get(0))
            .map_err(storage("journal_mode"))?;
        if !mode.eq_ignore_ascii_case("wal") {
            return Err(ExecutionError::StorageError(format!("journal_mode is '{}', WAL required", mode)));
        }
        Self::init(conn)
    }

    /// Ledger en memoria: **sin durabilidad**. Sólo para tests de lógica.
    pub fn open_in_memory_non_durable() -> Result<Self, ExecutionError> {
        Self::init(Connection::open_in_memory().map_err(storage("open"))?)
    }

    fn init(conn: Connection) -> Result<Self, ExecutionError> {
        conn.busy_timeout(std::time::Duration::from_secs(30)).map_err(storage("busy_timeout"))?;
        // fullfsync: en macOS, fsync() no vacía la caché del disco; F_FULLFSYNC sí.
        conn.execute_batch(
            "PRAGMA synchronous = FULL;
             PRAGMA fullfsync = ON;
             PRAGMA checkpoint_fullfsync = ON;
             PRAGMA busy_timeout = 30000;
             CREATE TABLE IF NOT EXISTS durable_reservations (
                 nonce BLOB PRIMARY KEY CHECK (length(nonce) = 32),
                 intent_digest BLOB NOT NULL,
                 policy_digest BLOB NOT NULL,
                 precondition_digest BLOB NOT NULL,
                 authorization_blob BLOB NOT NULL,
                 state TEXT NOT NULL CHECK (state IN ('RESERVED','DISPATCHED','EXECUTED','FAILED','UNKNOWN')),
                 created_at INTEGER NOT NULL,
                 dispatched_at INTEGER,
                 completed_at INTEGER,
                 result_payload BLOB,
                 error_message TEXT
             );
             CREATE TRIGGER IF NOT EXISTS reservation_identity_immutable
             BEFORE UPDATE OF nonce, intent_digest, policy_digest, precondition_digest,
                 authorization_blob, created_at ON durable_reservations
             BEGIN SELECT RAISE(ABORT, 'immutable reservation identity'); END;
             CREATE TRIGGER IF NOT EXISTS reservation_no_delete
             BEFORE DELETE ON durable_reservations
             BEGIN SELECT RAISE(ABORT, 'replay history cannot be deleted'); END;
             CREATE TRIGGER IF NOT EXISTS reservation_state_guard
             BEFORE UPDATE OF state ON durable_reservations
             WHEN NOT ((OLD.state = 'RESERVED' AND NEW.state = 'DISPATCHED')
                 OR (OLD.state = 'DISPATCHED' AND NEW.state IN ('EXECUTED','FAILED','UNKNOWN'))
                 OR (OLD.state = 'UNKNOWN' AND NEW.state = 'RESERVED'))
             BEGIN SELECT RAISE(ABORT, 'invalid reservation transition'); END;
             CREATE TRIGGER IF NOT EXISTS reservation_terminal_immutable
             BEFORE UPDATE ON durable_reservations WHEN OLD.state IN ('EXECUTED','FAILED')
             BEGIN SELECT RAISE(ABORT, 'terminal reservation'); END;",
        )
        .map_err(storage("schema"))?;
        Ok(Self { conn })
    }

    /// ¿Existe ya una reserva para este nonce? Errores se propagan (fail-closed).
    pub fn is_nonce_consumed(&self, nonce: &[u8; 32], allow_unknown: bool) -> Result<bool, ExecutionError> {
        let q = if allow_unknown {
            "SELECT 1 FROM durable_reservations WHERE nonce = ?1 AND state != 'UNKNOWN'"
        } else {
            "SELECT 1 FROM durable_reservations WHERE nonce = ?1"
        };
        Ok(self
            .conn
            .query_row(q, params![&nonce[..]], |_| Ok(()))
            .optional()
            .map_err(storage("nonce lookup"))?
            .is_some())
    }

    /// Reinicio: todo `DISPATCHED` pasa a `UNKNOWN`. Devuelve los nonces afectados.
    pub fn reconcile_on_startup(&mut self) -> Result<Vec<[u8; 32]>, ExecutionError> {
        let tx = self
            .conn
            .transaction_with_behavior(rusqlite::TransactionBehavior::Immediate)
            .map_err(storage("reconcile begin"))?;
        let nonces: Vec<[u8; 32]> = {
            let mut stmt = tx
                .prepare("SELECT nonce FROM durable_reservations WHERE state = 'DISPATCHED'")
                .map_err(storage("reconcile select"))?;
            let rows = stmt
                .query_map([], |r| r.get::<_, Vec<u8>>(0))
                .map_err(storage("reconcile query"))?;
            let mut out = Vec::new();
            for r in rows {
                let b = r.map_err(storage("reconcile row"))?;
                out.push(b.as_slice().try_into().map_err(|_| ExecutionError::StorageError("nonce length".into()))?);
            }
            out
        };
        tx.execute(
            "UPDATE durable_reservations SET state = 'UNKNOWN',
                 error_message = 'dispatch without durable result at restart'
             WHERE state = 'DISPATCHED'",
            [],
        )
        .map_err(storage("reconcile update"))?;
        tx.commit().map_err(storage("reconcile commit"))?;
        Ok(nonces)
    }

    /// Reserva + consumo del nonce en una única transacción. Replay → `NonceAlreadyConsumed`.
    pub fn reserve_and_consume_nonce(&mut self, auth: &SignedAuthorization, allow_unknown: bool, now: u64) -> Result<(), ExecutionError> {
        self.reserve_with_clock(auth, allow_unknown, &mut || Ok(now)).map(|_| ())
    }

    fn reserve_with_clock(&mut self, auth: &SignedAuthorization, allow_unknown: bool,
        clock: &mut impl FnMut() -> Result<u64, ExecutionError>) -> Result<u64, ExecutionError> {
        let p = &auth.parse()?.0;
        let tx = self
            .conn
            .transaction_with_behavior(rusqlite::TransactionBehavior::Immediate)
            .map_err(storage("reserve begin"))?;
        let now = clock()?;
        if now >= p.expires_at { return Err(ExecutionError::AuthorizationExpired); }
            
        let existing_row = tx.query_row(
            "SELECT state, intent_digest, policy_digest, precondition_digest FROM durable_reservations WHERE nonce = ?1",
            params![&p.nonce[..]],
            |row| Ok((
                row.get::<_, String>(0)?,
                row.get::<_, Vec<u8>>(1)?,
                row.get::<_, Vec<u8>>(2)?,
                row.get::<_, Vec<u8>>(3)?,
            ))
        ).optional().map_err(storage("reserve lookup"))?;
        
        if let Some((state, intent_db, policy_db, precond_db)) = existing_row {
            // Solo adaptadores VerifiableIdempotent pueden reanudar desde UNKNOWN tras restart
            if allow_unknown && state == "UNKNOWN" {
                if intent_db != p.intent_digest || policy_db != p.policy_digest || precond_db != p.resource_precondition_digest {
                    return Err(ExecutionError::NonceAlreadyConsumed(hex::encode(p.nonce)));
                }

                tx.execute(
                    "UPDATE durable_reservations SET state = 'RESERVED' WHERE nonce = ?1",
                    params![&p.nonce[..]],
                ).map_err(storage("reserve update state"))?;
                tx.commit().map_err(storage("reserve commit resume"))?;
                return Ok(now);
            } else {
                return Err(ExecutionError::NonceAlreadyConsumed(hex::encode(p.nonce)));
            }
        }
        
        tx.execute(
            "INSERT INTO durable_reservations
                 (nonce, intent_digest, policy_digest, precondition_digest, authorization_blob, state, created_at)
             VALUES (?1, ?2, ?3, ?4, ?5, 'RESERVED', ?6)",
            params![
                &p.nonce[..],
                &p.intent_digest[..],
                &p.policy_digest[..],
                &p.resource_precondition_digest[..],
                auth.archive_blob(),
                now as i64
            ],
        )
        .map_err(storage("reserve insert"))?;
        tx.commit().map_err(storage("reserve commit"))?;
        Ok(now)
    }

    fn transition(&mut self, nonce: &[u8; 32], sql: &str, args: &[&dyn rusqlite::ToSql]) -> Result<(), ExecutionError> {
        let mut all: Vec<&dyn rusqlite::ToSql> = args.to_vec();
        let n = &nonce[..];
        all.push(&n);
        let changed = self.conn.execute(sql, all.as_slice()).map_err(storage("transition"))?;
        if changed != 1 {
            return Err(ExecutionError::InvalidStateTransition(sql.split_whitespace().take(6).collect::<Vec<_>>().join(" ")));
        }
        Ok(())
    }

    /// RESERVED → DISPATCHED (durable antes de tocar el recurso).
    pub fn record_dispatch(&mut self, nonce: &[u8; 32], now: u64) -> Result<(), ExecutionError> {
        self.transition(
            nonce,
            "UPDATE durable_reservations SET state='DISPATCHED', dispatched_at=?1 WHERE state='RESERVED' AND nonce=?2",
            &[&(now as i64)],
        )
    }

    /// DISPATCHED → EXECUTED.
    pub fn record_completion(&mut self, nonce: &[u8; 32], result: &[u8], now: u64) -> Result<(), ExecutionError> {
        self.transition(
            nonce,
            "UPDATE durable_reservations SET state='EXECUTED', completed_at=?1, result_payload=?2 WHERE state='DISPATCHED' AND nonce=?3",
            &[&(now as i64), &result],
        )
    }

    /// DISPATCHED → FAILED (sólo cuando el adaptador garantiza que no aplicó el efecto).
    pub fn record_failure(&mut self, nonce: &[u8; 32], msg: &str, now: u64) -> Result<(), ExecutionError> {
        self.transition(
            nonce,
            "UPDATE durable_reservations SET state='FAILED', completed_at=?1, error_message=?2 WHERE state='DISPATCHED' AND nonce=?3",
            &[&(now as i64), &msg],
        )
    }

    /// Lectura de una fila.
    pub fn get_record(&self, nonce: &[u8; 32]) -> Result<Option<DurableRecord>, ExecutionError> {
        self.conn
            .query_row(
                "SELECT state, created_at, dispatched_at, completed_at, error_message
                 FROM durable_reservations WHERE nonce = ?1",
                params![&nonce[..]],
                |r| {
                    Ok((
                        r.get::<_, String>(0)?,
                        r.get::<_, i64>(1)?,
                        r.get::<_, Option<i64>>(2)?,
                        r.get::<_, Option<i64>>(3)?,
                        r.get::<_, Option<String>>(4)?,
                    ))
                },
            )
            .optional()
            .map_err(storage("get_record"))?
            .map(|(s, c, d, k, e)| {
                Ok(DurableRecord {
                    nonce: *nonce,
                    state: ReservationState::parse(&s)
                        .ok_or_else(|| ExecutionError::StorageError(format!("unknown state {}", s)))?,
                    created_at: c as u64,
                    dispatched_at: d.map(|x| x as u64),
                    completed_at: k.map(|x| x as u64),
                    error_message: e,
                })
            })
            .transpose()
    }

    /// Recuento por estado (auditoría del arnés).
    pub fn count_by_state(&self, state: ReservationState) -> Result<u64, ExecutionError> {
        self.conn
            .query_row(
                "SELECT COUNT(*) FROM durable_reservations WHERE state = ?1",
                params![state.as_str()],
                |r| r.get::<_, i64>(0),
            )
            .map(|n| n as u64)
            .map_err(storage("count"))
    }

    /// Nonces en un estado dado (auditoría del arnés).
    pub fn nonces_in_state(&self, state: ReservationState) -> Result<Vec<[u8; 32]>, ExecutionError> {
        let mut stmt = self
            .conn
            .prepare("SELECT nonce FROM durable_reservations WHERE state = ?1")
            .map_err(storage("nonces_in_state"))?;
        let rows = stmt
            .query_map(params![state.as_str()], |r| r.get::<_, Vec<u8>>(0))
            .map_err(storage("nonces_in_state"))?;
        let mut out = Vec::new();
        for r in rows {
            let b = r.map_err(storage("nonces_in_state"))?;
            out.push(b.as_slice().try_into().map_err(|_| ExecutionError::StorageError("nonce length".into()))?);
        }
        Ok(out)
    }
}


// ---------------------------------------------------------------------------
// Errores
// ---------------------------------------------------------------------------

/// Errores del ciclo autorización → efecto.
#[derive(Debug, Clone, PartialEq, Eq)]
#[cfg_attr(feature = "cortex-persist", derive(serde::Serialize, serde::Deserialize))]
pub enum ExecutionError {
    /// Payload malformado.
    MalformedAuthorization(String),
    /// Versión de protocolo no soportada.
    UnsupportedProtocolVersion(u16),
    /// `max_uses` distinto de 1 (no soportado).
    UnsupportedMaxUses(u32),
    /// Clave no admitida o algoritmo distinto del fijado.
    InvalidAuthorityKey(String),
    /// Firma inválida.
    InvalidSignature(String),
    /// Instalación distinta.
    InstallationMismatch,
    /// Executor distinto.
    ExecutorMismatch,
    /// Época revocada.
    AuthorityEpochRevoked,
    /// La época nueva no supera estrictamente la época vigente.
    AuthorityEpochNotMonotonic {
        /// Época vigente al rechazar la actualización.
        current: u64,
        /// Época solicitada.
        requested: u64,
    },
    /// El cerrojo de autoridad quedó envenenado; el efecto se rechaza.
    AuthorityGateUnavailable,
    /// Intención distinta de la autorizada.
    IntentDigestMismatch,
    /// Política distinta de la evaluada.
    PolicyDigestMismatch,
    /// La política no permite esa acción.
    PolicyActionMismatch,
    /// La política no reconoce esa autoridad.
    PolicyAuthorityMismatch,
    /// La política no permite ese número de usos.
    PolicyUsesExceeded,
    /// Recurso distinto del autorizado.
    PreconditionMismatch,
    /// Autorización expirada.
    AuthorizationExpired,
    /// El reloj del anfitrión no ofrece una fecha Unix válida.
    ClockUnavailable,
    /// Nonce ya reservado (replay).
    NonceAlreadyConsumed(String),
    /// Admisión cerrada.
    ExecutorPoisoned,
    /// Error de almacenamiento (fail-closed).
    StorageError(String),
    /// Transición ilegal en el ledger.
    InvalidStateTransition(String),
    /// El adaptador rechazó el efecto.
    EffectExecutionFailed(String),
    /// Interrupción lógica de prueba (no es un crash).
    Interrupted(CrashPoint),
}

fn unix_seconds_from_host_time(time: std::time::SystemTime) -> Result<u64, ExecutionError> {
    time.duration_since(std::time::UNIX_EPOCH)
        .map(|duration| duration.as_secs())
        .map_err(|_| ExecutionError::ClockUnavailable)
}

impl core::fmt::Display for ExecutionError {
    fn fmt(&self, f: &mut core::fmt::Formatter<'_>) -> core::fmt::Result {
        write!(f, "{:?}", self)
    }
}

impl std::error::Error for ExecutionError {}

// ---------------------------------------------------------------------------
// Executor
// ---------------------------------------------------------------------------

/// Serializa la revocación de autoridad con el tramo irreversible de un efecto.
///
/// Una revocación toma el cerrojo de escritura. El executor mantiene un cerrojo
/// de lectura desde la última comprobación de época hasta el resultado durable:
/// o la revocación gana y el efecto se rechaza, o el efecto gana y la revocación
/// queda ordenada después de su commit.
#[derive(Debug)]
pub struct AuthorityEpochGate {
    epoch: AtomicU64,
    effect_commit: RwLock<()>,
}

impl AuthorityEpochGate {
    /// Crea el gate con la época inicial autorizada.
    #[must_use]
    pub fn new(initial_epoch: u64) -> Self {
        Self {
            epoch: AtomicU64::new(initial_epoch),
            effect_commit: RwLock::new(()),
        }
    }

    /// Devuelve la época vigente publicada por el gate.
    #[must_use]
    pub fn current_epoch(&self) -> u64 {
        self.epoch.load(Ordering::Acquire)
    }

    /// Avanza monotonamente la época y espera a que terminen los efectos ya admitidos.
    /// La nueva época queda activa antes de que este método retorne.
    pub fn revoke_to(&self, next_epoch: u64) -> Result<(), ExecutionError> {
        let _writer = self
            .effect_commit
            .write()
            .map_err(|_| ExecutionError::AuthorityGateUnavailable)?;
        let current = self.current_epoch();
        if next_epoch <= current {
            return Err(ExecutionError::AuthorityEpochNotMonotonic {
                current,
                requested: next_epoch,
            });
        }
        self.epoch.store(next_epoch, Ordering::Release);
        Ok(())
    }

    fn lock_for_effect(
        &self,
        authorized_epoch: u64,
    ) -> Result<RwLockReadGuard<'_, ()>, ExecutionError> {
        let reader = self
            .effect_commit
            .read()
            .map_err(|_| ExecutionError::AuthorityGateUnavailable)?;
        if self.current_epoch() != authorized_epoch {
            return Err(ExecutionError::AuthorityEpochRevoked);
        }
        Ok(reader)
    }
}

/// Executor con verificación fail-closed y reserva durable.
pub struct SovereignExecutor<A: EffectAdapter> {
    /// Instalación local.
    pub installation_id: [u8; 32],
    /// Identidad de este executor.
    pub executor_id: [u8; 32],
    /// Gate compartido para revocación causal en caliente.
    pub authority_epoch_gate: Arc<AuthorityEpochGate>,
    /// Autoridades admitidas (clave + algoritmo fijado).
    pub admitted_authorities: Vec<AdmittedAuthority>,
    /// Admisión cerrada.
    pub is_poisoned: Arc<AtomicBool>,
    /// Ledger.
    pub store: DurableExecutionStore,
    /// Adaptador.
    pub adapter: A,
    /// Punto de interrupción de prueba.
    pub crash_point: CrashPoint,
    /// Comportamiento en el punto de interrupción.
    pub crash_action: CrashAction,
}

impl<A: EffectAdapter> SovereignExecutor<A> {
    /// Construye un executor.
    pub fn new(
        installation_id: [u8; 32],
        executor_id: [u8; 32],
        current_authority_epoch: u64,
        admitted_authorities: Vec<AdmittedAuthority>,
        store: DurableExecutionStore,
        adapter: A,
    ) -> Self {
        Self {
            installation_id,
            executor_id,
            authority_epoch_gate: Arc::new(AuthorityEpochGate::new(current_authority_epoch)),
            admitted_authorities,
            is_poisoned: Arc::new(AtomicBool::new(false)),
            store,
            adapter,
            crash_point: CrashPoint::None,
            crash_action: CrashAction::ReturnError,
        }
    }

    /// Configura interrupción de prueba.
    pub fn with_crash(mut self, point: CrashPoint, action: CrashAction) -> Self {
        self.crash_point = point;
        self.crash_action = action;
        self
    }

    /// Cierra admisión.
    pub fn poison(&self) {
        self.is_poisoned.store(true, Ordering::Release);
    }

    fn maybe_crash(&self, here: CrashPoint) -> Result<(), ExecutionError> {
        if self.crash_point != here || here == CrashPoint::None {
            return Ok(());
        }
        match self.crash_action {
            CrashAction::ReturnError => Err(ExecutionError::Interrupted(here)),
            CrashAction::SignalAndAwaitKill => {
                use std::io::Write;
                println!("CRASHPOINT {}", here.name());
                let _ = std::io::stdout().flush();
                loop {
                    std::thread::sleep(std::time::Duration::from_secs(3600));
                }
            }
        }
    }

    /// Verificación completa previa a la reserva. `now` debe provenir del anfitrión
    /// de confianza, en segundos Unix, nunca de un cliente IPC.
    /// Orden: estado → nonce → perfil →
    /// autoridad → firma → ligaduras → política → precondición → vigencia.
    pub fn verify_authorization(
        &self,
        auth: &SignedAuthorization,
        intent: &ProposedIntent,
        policy: &SecurityPolicy,
        current_precondition: &[u8; 32],
        now: u64,
    ) -> Result<(), ExecutionError> {
        let (p, kid, auth_alg) = auth.parse()?;
        if self.is_poisoned.load(Ordering::Acquire) {
            return Err(ExecutionError::ExecutorPoisoned);
        }
        let allow_unknown = self.adapter.idempotency_contract() == IdempotencyContract::VerifiableIdempotent;
        if self.store.is_nonce_consumed(&p.nonce, allow_unknown)? {
            return Err(ExecutionError::NonceAlreadyConsumed(hex::encode(p.nonce)));
        }
        if p.protocol_version != PROTOCOL_VERSION {
            return Err(ExecutionError::UnsupportedProtocolVersion(p.protocol_version));
        }
        if p.max_uses != 1 {
            return Err(ExecutionError::UnsupportedMaxUses(p.max_uses));
        }
        let admitted = self
            .admitted_authorities
            .iter()
            .find(|a| a.public_key == kid)
            .ok_or_else(|| ExecutionError::InvalidAuthorityKey("key not admitted".into()))?;
        if admitted.algorithm != auth_alg {
            return Err(ExecutionError::InvalidAuthorityKey("algorithm not pinned for this key".into()));
        }
        auth.verify_signature()?;
        if p.installation_id != self.installation_id {
            return Err(ExecutionError::InstallationMismatch);
        }
        if p.executor_id != self.executor_id {
            return Err(ExecutionError::ExecutorMismatch);
        }
        if p.authority_epoch != self.authority_epoch_gate.current_epoch() {
            return Err(ExecutionError::AuthorityEpochRevoked);
        }
        if p.intent_digest != intent.compute_digest() {
            return Err(ExecutionError::IntentDigestMismatch);
        }
        if p.policy_digest != policy.compute_digest() {
            return Err(ExecutionError::PolicyDigestMismatch);
        }
        if intent.action_name != policy.allowed_action {
            return Err(ExecutionError::PolicyActionMismatch);
        }
        if policy.admitted_authority_key != kid {
            return Err(ExecutionError::PolicyAuthorityMismatch);
        }
        if p.max_uses > policy.max_allowed_uses {
            return Err(ExecutionError::PolicyUsesExceeded);
        }
        if p.resource_precondition_digest != *current_precondition {
            return Err(ExecutionError::PreconditionMismatch);
        }
        if now >= p.expires_at {
            return Err(ExecutionError::AuthorizationExpired);
        }
        Ok(())
    }

    /// Ejecuta con el reloj del anfitrión, en segundos Unix. La entrada del cliente
    /// no puede determinar la vigencia ni las marcas temporales del ledger.
    pub fn execute_action_with_host_clock(
        &mut self,
        auth: &SignedAuthorization,
        intent: &ProposedIntent,
        policy: &SecurityPolicy,
        resource: &mut A::Resource,
    ) -> Result<A::Output, ExecutionError> {
        self.execute_with_clock(auth, intent, policy, resource, &mut ||
            unix_seconds_from_host_time(std::time::SystemTime::now()))
    }

    /// Verificación → reserva durable → dispatch durable → efecto → resultado durable.
    /// `now` es una entrada del anfitrión de confianza en segundos Unix; los
    /// transportes remotos deben utilizar [`Self::execute_action_with_host_clock`].
    pub fn execute_action(
        &mut self,
        auth: &SignedAuthorization,
        intent: &ProposedIntent,
        policy: &SecurityPolicy,
        resource: &mut A::Resource,
        now: u64,
    ) -> Result<A::Output, ExecutionError> {
        self.execute_with_clock(auth, intent, policy, resource, &mut || Ok(now))
    }

    fn execute_with_clock(&mut self, auth: &SignedAuthorization, intent: &ProposedIntent,
        policy: &SecurityPolicy, resource: &mut A::Resource,
        clock: &mut impl FnMut() -> Result<u64, ExecutionError>) -> Result<A::Output, ExecutionError> {
        let now = clock()?;
        let effect = self
            .adapter
            .parse_intent(intent)
            .map_err(|e| ExecutionError::EffectExecutionFailed(e.to_string()))?;
        let pre = self
            .adapter
            .compute_precondition(resource)
            .map_err(|e| ExecutionError::EffectExecutionFailed(e.to_string()))?;
        self.verify_authorization(auth, intent, policy, &pre, now)?;
        let (p, _, _) = auth.parse()?;
        let allow_unknown = self.adapter.idempotency_contract() == IdempotencyContract::VerifiableIdempotent;

        let now = self.store.reserve_with_clock(auth, allow_unknown, clock)?;
        self.maybe_crash(CrashPoint::AfterReservationBeforeDispatch)?;

        self.store.record_dispatch(&p.nonce, now)?;
        // Dispatch can itself wait for another SQLite writer after reservation.
        let now = clock()?;
        if now >= p.expires_at {
            self.store.record_failure(&p.nonce, "authorization expired before effect", now)?;
            return Err(ExecutionError::AuthorizationExpired);
        }
        self.maybe_crash(CrashPoint::AfterDispatchBeforeEffect)?;

        // Esta lectura se linealiza con las revocaciones. Una época revocada
        // después de la reserva no puede alcanzar el adaptador de efectos.
        let authority_gate = Arc::clone(&self.authority_epoch_gate);
        let _authority_guard = match authority_gate.lock_for_effect(p.authority_epoch) {
            Ok(guard) => guard,
            Err(error) => {
                let failed_at = clock()?;
                self.store.record_failure(&p.nonce, "authority epoch revoked before effect", failed_at)?;
                return Err(error);
            }
        };
        let now = clock()?;
        if now >= p.expires_at {
            self.store.record_failure(&p.nonce, "authorization expired before effect", now)?;
            return Err(ExecutionError::AuthorizationExpired);
        }
        let current_precondition = match self.adapter.compute_precondition(resource) {
            Ok(precondition) => precondition,
            Err(error) => {
                let message = error.to_string();
                self.store.record_failure(&p.nonce, &message, now)?;
                return Err(ExecutionError::EffectExecutionFailed(message));
            }
        };
        if current_precondition != p.resource_precondition_digest {
            self.store.record_failure(
                &p.nonce,
                "resource precondition changed before effect",
                now,
            )?;
            return Err(ExecutionError::PreconditionMismatch);
        }

        let out = match self.adapter.apply_effect(resource, &p.resource_precondition_digest, &p.nonce, &effect) {
            Ok(o) => o,
            Err(e) => {
                let msg = e.to_string();
                self.store.record_failure(&p.nonce, &msg, now)?;
                return Err(ExecutionError::EffectExecutionFailed(msg));
            }
        };
        self.maybe_crash(CrashPoint::AfterEffectBeforeCompletion)?;

        self.store.record_completion(&p.nonce, b"OK", now)?;
        Ok(out)
    }
}

#[path = "executor_ipc.rs"]
mod executor_ipc;
pub use executor_ipc::*;

#[cfg(test)]
#[path = "executor_tests.rs"]
pub(crate) mod tests;

/// Tests de aislamiento IPC y capacidades (AUTH_002)
#[cfg(all(test, feature = "cortex-persist"))]
#[path = "executor_ipc_tests.rs"]
pub mod ipc_tests;
