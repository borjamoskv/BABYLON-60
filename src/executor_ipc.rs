//! Transporte IPC Unix Socket y adaptadores sintéticos/puntos de crash del Executor v5.

use super::*;

/// Estados de una reserva.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum ReservationState {
    /// Nonce consumido; aún sin dispatch.
    Reserved,
    /// Dispatch registrado; el efecto puede o no haber ocurrido.
    Dispatched,
    /// Resultado registrado.
    Executed,
    /// El adaptador rechazó el efecto antes de aplicarlo.
    Failed,
    /// Dispatch sin resultado tras reinicio. No se repite automáticamente.
    Unknown,
}

impl ReservationState {
    /// Representación en base de datos.
    pub fn as_str(&self) -> &'static str {
        match self {
            ReservationState::Reserved => "RESERVED",
            ReservationState::Dispatched => "DISPATCHED",
            ReservationState::Executed => "EXECUTED",
            ReservationState::Failed => "FAILED",
            ReservationState::Unknown => "UNKNOWN",
        }
    }

    /// Parseo estricto.
    pub fn parse(s: &str) -> Option<Self> {
        Some(match s {
            "RESERVED" => ReservationState::Reserved,
            "DISPATCHED" => ReservationState::Dispatched,
            "EXECUTED" => ReservationState::Executed,
            "FAILED" => ReservationState::Failed,
            "UNKNOWN" => ReservationState::Unknown,
            _ => return None,
        })
    }

    /// Morfismo exhaustivo hacia `ReceiptStage` (INV_C5_PARASITIC_DOF_QUOTIENT / D4).
    /// Devuelve `Some(stage)` para los estados que emiten recibo ontológico activo y
    /// `None` para fallos terminales o estados indeterminados (`FAILED`/`UNKNOWN`).
    ///
    /// Nota VOP-1: `ReservationState::Unknown` no emite un recibo de etapa activa; su incertidumbre
    /// queda capturada en `EffectState::UnknownOutcomeRequiresReconciliation`.
    pub const fn to_receipt_stage(&self) -> Option<crate::ontology::babylon::ReceiptStage> {
        use crate::ontology::babylon::ReceiptStage;
        match self {
            ReservationState::Reserved => Some(ReceiptStage::Authorized),
            ReservationState::Dispatched => Some(ReceiptStage::Dispatched),
            ReservationState::Executed => Some(ReceiptStage::Committed),
            ReservationState::Failed | ReservationState::Unknown => None,
        }
    }

    /// Morfismo exhaustivo hacia `EffectState` (fases canónicas de `ontology.rs`).
    /// Preserva explícitamente la incertidumbre física (`UNKNOWN != NOT_APPLIED`) sin colapsarla a `Failed`.
    pub fn to_effect_state(&self, detail: Option<&str>) -> crate::ontology::babylon::EffectState {
        use crate::ontology::babylon::{EffectState, FailureReason};
        match self {
            ReservationState::Reserved => EffectState::Durable,
            ReservationState::Dispatched => EffectState::Executing,
            ReservationState::Executed => EffectState::Executed,
            ReservationState::Failed => EffectState::Failed(FailureReason::IoError(
                detail.unwrap_or("adapter rejected effect").to_string(),
            )),
            ReservationState::Unknown => EffectState::UnknownOutcomeRequiresReconciliation,
        }
    }
}

impl core::convert::TryFrom<ReservationState> for crate::ontology::babylon::ReceiptStage {
    type Error = ReservationState;

    fn try_from(state: ReservationState) -> Result<Self, Self::Error> {
        state.to_receipt_stage().ok_or(state)
    }
}

impl From<crate::ontology::babylon::ReceiptStage> for ReservationState {
    fn from(stage: crate::ontology::babylon::ReceiptStage) -> Self {
        use crate::ontology::babylon::ReceiptStage;
        match stage {
            ReceiptStage::Requested | ReceiptStage::Authorized => ReservationState::Reserved,
            ReceiptStage::Dispatched => ReservationState::Dispatched,
            ReceiptStage::Observed | ReceiptStage::Committed => ReservationState::Executed,
        }
    }
}

/// Fila del ledger de reservas.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct DurableRecord {
    /// Nonce.
    pub nonce: [u8; 32],
    /// Estado.
    pub state: ReservationState,
    /// Momento de la reserva.
    pub created_at: u64,
    /// Momento del dispatch.
    pub dispatched_at: Option<u64>,
    /// Momento de cierre.
    pub completed_at: Option<u64>,
    /// Mensaje de error / reconciliación.
    pub error_message: Option<String>,
}

/// Recurso sintético en memoria (contador versionado). Sólo válido en un proceso.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct SyntheticResource {
    /// Identificador.
    pub resource_id: String,
    /// Valor protegido.
    pub state_counter: u64,
    /// Versión monótona.
    pub version: u64,
}

impl SyntheticResource {
    /// Crea un recurso con versión 1.
    pub fn new(resource_id: &str, initial_counter: u64) -> Self {
        Self { resource_id: resource_id.to_string(), state_counter: initial_counter, version: 1 }
    }
}

/// Adaptador del recurso sintético (compare-and-swap sobre la versión).
#[derive(Debug, Default)]
pub struct SyntheticEffectAdapter;

/// Errores del adaptador sintético.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum SyntheticError {
    /// El recurso cambió entre autorización y ejecución.
    PreconditionMismatch,
    /// Desbordamiento.
    Overflow,
}

impl core::fmt::Display for SyntheticError {
    fn fmt(&self, f: &mut core::fmt::Formatter<'_>) -> core::fmt::Result {
        match self {
            SyntheticError::PreconditionMismatch => f.write_str("resource precondition mismatch"),
            SyntheticError::Overflow => f.write_str("counter overflow"),
        }
    }
}

impl EffectAdapter for SyntheticEffectAdapter {
    type Resource = SyntheticResource;
    type Effect = u64;
    type Output = u64;
    type Error = SyntheticError;

    fn parse_intent(&self, intent: &ProposedIntent) -> Result<Self::Effect, Self::Error> {
        if intent.parameters.len() != 8 {
            return Err(SyntheticError::Overflow);
        }
        let mut buf = [0u8; 8];
        buf.copy_from_slice(&intent.parameters);
        Ok(u64::from_be_bytes(buf))
    }

    fn compute_precondition(&self, r: &SyntheticResource) -> Result<[u8; 32], SyntheticError> {
        Ok(CanonicalHasher::new(b"BABYLON60/synthetic-resource/v1")
            .field(r.resource_id.as_bytes())
            .field(&r.state_counter.to_be_bytes())
            .field(&r.version.to_be_bytes())
            .finish())
    }

    fn apply_effect(
        &mut self,
        r: &mut SyntheticResource,
        expected: &[u8; 32],
        _nonce: &[u8; 32],
        delta: &u64,
    ) -> Result<u64, SyntheticError> {
        if &self.compute_precondition(r)? != expected {
            return Err(SyntheticError::PreconditionMismatch);
        }
        r.state_counter = r.state_counter.checked_add(*delta).ok_or(SyntheticError::Overflow)?;
        r.version += 1;
        Ok(r.state_counter)
    }

    fn idempotency_contract(&self) -> IdempotencyContract {
        IdempotencyContract::NonIdempotentExplicitIntervention
    }
}

/// Puntos donde el executor puede interrumpirse para pruebas.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
#[cfg_attr(feature = "cortex-persist", derive(serde::Serialize, serde::Deserialize))]
pub enum CrashPoint {
    /// Sin interrupción.
    None,
    /// Tras commit de la reserva, antes del dispatch.
    AfterReservationBeforeDispatch,
    /// Tras commit del dispatch, antes de aplicar el efecto.
    AfterDispatchBeforeEffect,
    /// Tras aplicar el efecto, antes de registrar el resultado.
    AfterEffectBeforeCompletion,
}

impl CrashPoint {
    /// Nombre estable para protocolos de arnés.
    pub fn name(self) -> &'static str {
        match self {
            CrashPoint::None => "None",
            CrashPoint::AfterReservationBeforeDispatch => "AfterReservationBeforeDispatch",
            CrashPoint::AfterDispatchBeforeEffect => "AfterDispatchBeforeEffect",
            CrashPoint::AfterEffectBeforeCompletion => "AfterEffectBeforeCompletion",
        }
    }
    /// Parseo desde nombre.
    pub fn parse(s: &str) -> Option<Self> {
        [
            CrashPoint::None,
            CrashPoint::AfterReservationBeforeDispatch,
            CrashPoint::AfterDispatchBeforeEffect,
            CrashPoint::AfterEffectBeforeCompletion,
        ]
        .into_iter()
        .find(|c| c.name() == s)
    }
}

/// Qué hace el executor al alcanzar el punto configurado.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum CrashAction {
    /// Devuelve `Err(Interrupted)`. Simula interrupción lógica en el mismo proceso;
    /// NO es un crash (la conexión y la caché siguen vivas).
    ReturnError,
    /// Imprime `CRASHPOINT <name>` en stdout y se bloquea hasta recibir SIGKILL del arnés.
    SignalAndAwaitKill,
}

/// Módulo IPC de separación de privilegios (Frontera OS / Socket Unix)
#[cfg(feature = "cortex-persist")]
pub mod ipc {
    use super::*;
    use std::io::{Read, Write};
    use std::os::unix::net::UnixStream;
    use std::path::Path;

    /// Petición IPC estructurada sobre socket de dominio Unix.
    #[allow(clippy::large_enum_variant)]
    #[derive(Debug, serde::Serialize, serde::Deserialize)]
    pub enum IpcRequest {
        /// Petición de ejecución de acción protegida con autorización COSE.
        ExecuteAction {
            /// Autorización firmada.
            auth: SignedAuthorization,
            /// Intención propuesta.
            intent: ProposedIntent,
            /// Política de seguridad.
            policy: SecurityPolicy,
            /// Campo de compatibilidad: el servidor ignora esta hora del cliente.
            #[serde(default)]
            timestamp: u64,
        },
        /// Sonda de liveness.
        Ping,
    }

    /// Versión canónica del envelope IPC on-wire (`INV_C5_ONWIRE_CANON`).
    pub const IPC_ENVELOPE_VERSION: u8 = 6;

    /// Códigos de error tipados para el transporte IPC (`INV_C5_ONWIRE_CANON`).
    #[derive(Debug, Clone, Copy, PartialEq, Eq, serde::Serialize, serde::Deserialize)]
    #[repr(u16)]
    pub enum IpcErrorCode {
        /// Sin error (0).
        Ok = 0,
        /// Autorización o firma inválida (1001).
        Unauthorized = 1001,
        /// Nonce ya consumido o replay detectado (1002).
        ReplayDetected = 1002,
        /// Precondición o política violada (1003).
        PolicyOrPreconditionViolation = 1003,
        /// Executor en estado POISONED fail-stop (1004).
        ExecutorPoisoned = 1004,
        /// Error de almacenamiento o ejecución de efecto (1005).
        ExecutionOrStorageFailure = 1005,
    }

    /// Respuesta IPC estructurada devuelta por el executor.
    #[derive(Debug, serde::Serialize, serde::Deserialize)]
    pub enum IpcResponse {
        /// Ejecución completada con resultado en bytes.
        Ok(Vec<u8>),
        /// Error de verificación, autorización o persistencia (fail-closed).
        Err(ExecutionError),
        /// Respuesta a sonda de liveness.
        Pong,
    }

    impl IpcResponse {
        /// Devuelve el código numérico tipado asociado a la respuesta IPC.
        pub fn error_code(&self) -> IpcErrorCode {
            match self {
                IpcResponse::Ok(_) | IpcResponse::Pong => IpcErrorCode::Ok,
                IpcResponse::Err(ExecutionError::ExecutorPoisoned) => IpcErrorCode::ExecutorPoisoned,
                IpcResponse::Err(ExecutionError::NonceAlreadyConsumed(_)) => IpcErrorCode::ReplayDetected,
                IpcResponse::Err(
                    ExecutionError::InvalidSignature(_)
                    | ExecutionError::InvalidAuthorityKey(_)
                    | ExecutionError::MalformedAuthorization(_)
                    | ExecutionError::AuthorizationExpired
                    | ExecutionError::AuthorityEpochRevoked,
                ) => IpcErrorCode::Unauthorized,
                IpcResponse::Err(
                    ExecutionError::PolicyActionMismatch
                    | ExecutionError::PolicyAuthorityMismatch
                    | ExecutionError::PolicyDigestMismatch
                    | ExecutionError::PolicyUsesExceeded
                    | ExecutionError::PreconditionMismatch
                    | ExecutionError::IntentDigestMismatch
                    | ExecutionError::InstallationMismatch
                    | ExecutionError::ExecutorMismatch,
                ) => IpcErrorCode::PolicyOrPreconditionViolation,
                IpcResponse::Err(_) => IpcErrorCode::ExecutionOrStorageFailure,
            }
        }
    }

    /// Explicit transport identity. Transport keys are separate from effect authority keys.
    #[derive(Clone)]
    pub struct IpcIdentity {
        signing_key: ed25519_dalek::SigningKey,
        trusted_peer: ed25519_dalek::VerifyingKey,
        expected_uid: u32,
    }

    fn denied(message: &str) -> std::io::Error {
        std::io::Error::new(std::io::ErrorKind::PermissionDenied, message)
    }

    impl IpcIdentity {
        /// Configure a local signing key, pinned peer key and kernel peer UID.
        pub fn new(signing_key: ed25519_dalek::SigningKey,
                   trusted_peer: ed25519_dalek::VerifyingKey, expected_uid: u32) -> Self {
            Self { signing_key, trusted_peer, expected_uid }
        }

        /// Required hex seed, hex peer public key and decimal peer UID; no trust defaults.
        pub fn from_env() -> std::io::Result<Self> {
            fn key(name: &str) -> std::io::Result<[u8; 32]> {
                let text = std::env::var(name).map_err(|_| denied("IPC identity not configured"))?;
                let bytes = hex::decode(text).map_err(|_| denied("invalid IPC key encoding"))?;
                let key: [u8; 32] = bytes.try_into().map_err(|_| denied("IPC key must be 32 bytes"))?;
                if key == [0; 32] { return Err(denied("placeholder IPC key forbidden")); }
                Ok(key)
            }
            let seed = key("BABYLON_IPC_SIGNING_SEED")?;
            let peer = ed25519_dalek::VerifyingKey::from_bytes(&key("BABYLON_IPC_PEER_PUBLIC_KEY")?)
                .map_err(|_| denied("invalid IPC peer key"))?;
            let uid = std::env::var("BABYLON_IPC_PEER_UID")
                .map_err(|_| denied("IPC peer UID not configured"))?
                .parse().map_err(|_| denied("invalid IPC peer UID"))?;
            Ok(Self::new(ed25519_dalek::SigningKey::from_bytes(&seed), peer, uid))
        }

        /// Authenticate kernel credentials before consuming any frame.
        pub fn verify_peer(&self, stream: &UnixStream) -> std::io::Result<()> {
            use std::os::fd::AsRawFd;
            #[cfg(target_os = "linux")]
            let uid = {
                let mut cred: libc::ucred = unsafe { std::mem::zeroed() };
                let mut len = std::mem::size_of::<libc::ucred>() as libc::socklen_t;
                let rc = unsafe { libc::getsockopt(stream.as_raw_fd(), libc::SOL_SOCKET,
                    libc::SO_PEERCRED, std::ptr::from_mut(&mut cred).cast(), &mut len) };
                if rc != 0 || len as usize != std::mem::size_of::<libc::ucred>() {
                    return Err(denied("cannot authenticate IPC peer"));
                }
                cred.uid
            };
            #[cfg(not(target_os = "linux"))]
            let uid = {
                let mut uid = u32::MAX;
                let mut gid = u32::MAX;
                if unsafe { libc::getpeereid(stream.as_raw_fd(), &mut uid, &mut gid) } != 0 {
                    return Err(denied("cannot authenticate IPC peer"));
                }
                uid
            };
            if uid != self.expected_uid { return Err(denied("IPC peer UID mismatch")); }
            Ok(())
        }
    }

    /// Send a genuinely signed frame using explicitly provisioned environment trust.
    pub fn send_frame<W: Write, T: serde::Serialize>(writer: &mut W, msg: &T) -> std::io::Result<()> {
        send_authenticated_frame(writer, msg, &IpcIdentity::from_env()?, rand::random())
    }

    /// Receive only a correctly signed frame from the explicitly pinned environment key.
    pub fn recv_frame<R: Read, T: serde::de::DeserializeOwned>(reader: &mut R) -> std::io::Result<T> {
        recv_authenticated_frame(reader, &IpcIdentity::from_env()?, None).map(|(msg, _)| msg)
    }

    /// Signed CBOR frame. The authenticated challenge binds an executor reply to its request.
    pub fn send_authenticated_frame<W: Write, T: serde::Serialize>(
        writer: &mut W, msg: &T, identity: &IpcIdentity, challenge: [u8; 32],
    ) -> std::io::Result<()> {
        use coset::{CborSerializable, CoseSign1Builder, HeaderBuilder};
        use ed25519_dalek::Signer as _;
        let mut payload = Vec::new();
        ciborium::into_writer(msg, &mut payload)
            .map_err(|e| std::io::Error::new(std::io::ErrorKind::InvalidData, e.to_string()))?;
        let envelope = CoseSign1Builder::new()
            .protected(HeaderBuilder::new().algorithm(coset::iana::Algorithm::EdDSA)
                .key_id(challenge.to_vec()).build())
            .payload(payload)
            .create_signature(b"BABYLON60-IPC-v6", |bytes| identity.signing_key.sign(bytes).to_bytes().to_vec())
            .build().to_vec().map_err(|_| denied("cannot encode IPC signature"))?;
        if envelope.len() > 16 * 1024 * 1024 {
            return Err(std::io::Error::new(std::io::ErrorKind::InvalidData, "frame too large"));
        }
        writer.write_all(&[IPC_ENVELOPE_VERSION])?;
        writer.write_all(&(envelope.len() as u32).to_be_bytes())?;
        writer.write_all(&envelope)?;
        writer.flush()
    }

    /// Verify pinned key, algorithm, challenge and size before deserializing the message.
    pub fn recv_authenticated_frame<R: Read, T: serde::de::DeserializeOwned>(
        reader: &mut R, identity: &IpcIdentity, expected_challenge: Option<[u8; 32]>,
    ) -> std::io::Result<(T, [u8; 32])> {
        use coset::{CborSerializable, CoseSign1};
        let mut header = [0u8; 5];
        reader.read_exact(&mut header)?;
        if header[0] != IPC_ENVELOPE_VERSION { return Err(denied("unsupported IPC envelope version")); }
        let len = u32::from_be_bytes(header[1..].try_into().unwrap()) as usize;
        if len > 16 * 1024 * 1024 {
            return Err(std::io::Error::new(std::io::ErrorKind::InvalidData, "frame too large"));
        }
        let mut bytes = vec![0; len];
        reader.read_exact(&mut bytes)?;
        let sign1 = CoseSign1::from_slice(&bytes).map_err(|_| denied("invalid COSE frame"))?;
        if sign1.protected.header.alg != Some(coset::Algorithm::Assigned(coset::iana::Algorithm::EdDSA)) {
            return Err(denied("IPC signature algorithm mismatch"));
        }
        let challenge: [u8; 32] = sign1.protected.header.key_id.as_slice().try_into()
            .map_err(|_| denied("invalid IPC challenge"))?;
        if expected_challenge.is_some_and(|expected| expected != challenge) {
            return Err(denied("IPC response challenge mismatch"));
        }
        sign1.verify_signature(b"BABYLON60-IPC-v6", |signature, signed| {
            let signature = ed25519_dalek::Signature::from_slice(signature)
                .map_err(|_| denied("invalid IPC signature"))?;
            identity.trusted_peer.verify_strict(signed, &signature)
                .map_err(|_| denied("untrusted IPC signature"))
        })?;
        let payload = sign1.payload.ok_or_else(|| denied("missing IPC payload"))?;
        let msg = ciborium::from_reader(payload.as_slice())
            .map_err(|e| std::io::Error::new(std::io::ErrorKind::InvalidData, e.to_string()))?;
        Ok((msg, challenge))
    }

    /// Servidor de ejecución que retiene las capacidades del SO y atiende clientes por socket.
    pub struct IpcExecutorServer<A: EffectAdapter<Effect = Vec<u8>, Output = Vec<u8>>> {
        executor: SovereignExecutor<A>,
        identity: Option<IpcIdentity>,
    }

    impl<A: EffectAdapter<Effect = Vec<u8>, Output = Vec<u8>>> IpcExecutorServer<A> {
        /// Construye un nuevo servidor IPC envolviendo el executor soberano.
        pub fn new(executor: SovereignExecutor<A>) -> Self {
            Self { executor, identity: IpcIdentity::from_env().ok() }
        }

        /// Configure transport trust independently from effect authorization.
        pub fn with_identity(executor: SovereignExecutor<A>, identity: IpcIdentity) -> Self {
            Self { executor, identity: Some(identity) }
        }

        /// Procesa peticiones de un stream Unix de forma síncrona hasta desconexión.
        pub fn handle_client(&mut self, mut stream: UnixStream, resource: &mut A::Resource) -> std::io::Result<()> {
            let identity = self.identity.as_ref().ok_or_else(|| denied("IPC identity not configured"))?;
            identity.verify_peer(&stream)?;
            stream.set_read_timeout(Some(std::time::Duration::from_secs(30)))?;
            stream.set_write_timeout(Some(std::time::Duration::from_secs(30)))?;
            loop {
                let (req, challenge): (IpcRequest, _) = match recv_authenticated_frame(&mut stream, identity, None) {
                    Ok(r) => r,
                    Err(e) if e.kind() == std::io::ErrorKind::UnexpectedEof => break,
                    Err(e) => return Err(e),
                };
                let resp = match req {
                    IpcRequest::Ping => IpcResponse::Pong,
                    IpcRequest::ExecuteAction { auth, intent, policy, timestamp: _ } => {
                        match self.executor.execute_action_with_host_clock(&auth, &intent, &policy, resource) {
                            Ok(out) => IpcResponse::Ok(out),
                            Err(e) => IpcResponse::Err(e),
                        }
                    }
                };
                send_authenticated_frame(&mut stream, &resp, identity, challenge)?;
            }
            Ok(())
        }
    }

    /// Cliente IPC utilizado por agentes desprivilegiados (EDIN) para solicitar efectos protegidos.
    pub struct IpcExecutorClient {
        stream: UnixStream,
        identity: Option<IpcIdentity>,
    }

    impl IpcExecutorClient {
        /// Conecta a un socket Unix local del executor.
        pub fn connect<P: AsRef<Path>>(path: P) -> std::io::Result<Self> {
            let stream = UnixStream::connect(path)?;
            Self::from_stream_with_identity(stream, IpcIdentity::from_env()?)
        }

        /// Crea un cliente a partir de un stream Unix ya conectado.
        pub fn from_stream(stream: UnixStream) -> Self {
            Self { stream, identity: IpcIdentity::from_env().ok() }
        }

        #[cfg(test)]
        pub(crate) fn without_identity_for_test(stream: UnixStream) -> Self {
            Self { stream, identity: None }
        }

        /// Verify the peer before constructing an authenticated client.
        pub fn from_stream_with_identity(stream: UnixStream, identity: IpcIdentity) -> std::io::Result<Self> {
            identity.verify_peer(&stream)?;
            stream.set_read_timeout(Some(std::time::Duration::from_secs(30)))?;
            stream.set_write_timeout(Some(std::time::Duration::from_secs(30)))?;
            Ok(Self { stream, identity: Some(identity) })
        }

        fn exchange(&mut self, request: &IpcRequest) -> std::io::Result<IpcResponse> {
            let identity = self.identity.as_ref().ok_or_else(|| denied("IPC identity not configured"))?;
            identity.verify_peer(&self.stream)?;
            self.stream.set_read_timeout(Some(std::time::Duration::from_secs(30)))?;
            self.stream.set_write_timeout(Some(std::time::Duration::from_secs(30)))?;
            let challenge = rand::random();
            send_authenticated_frame(&mut self.stream, request, identity, challenge)?;
            recv_authenticated_frame(&mut self.stream, identity, Some(challenge)).map(|(response, _)| response)
        }

        /// Envía sonda de liveness.
        pub fn ping(&mut self) -> std::io::Result<()> {
            match self.exchange(&IpcRequest::Ping)? {
                IpcResponse::Pong => Ok(()),
                other => Err(std::io::Error::other(format!("unexpected response: {:?}", other))),
            }
        }

        /// Solicita ejecución de una acción protegida a través del canal IPC.
        /// `timestamp` se conserva por compatibilidad y no determina la vigencia.
        pub fn execute_action(
            &mut self,
            auth: &SignedAuthorization,
            intent: &ProposedIntent,
            policy: &SecurityPolicy,
            timestamp: u64,
        ) -> Result<Vec<u8>, ExecutionError> {
            let req = IpcRequest::ExecuteAction {
                auth: auth.clone(),
                intent: intent.clone(),
                policy: policy.clone(),
                timestamp,
            };
            let resp = self.exchange(&req).map_err(|e| ExecutionError::StorageError(e.to_string()))?;
            match resp {
                IpcResponse::Ok(bytes) => Ok(bytes),
                IpcResponse::Err(error) => Err(error),
                IpcResponse::Pong => Err(ExecutionError::EffectExecutionFailed("unexpected pong".into())),
            }
        }
    }
}
