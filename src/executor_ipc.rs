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
    pub const IPC_ENVELOPE_VERSION: u8 = 5;

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

    /// Envía una trama con byte de versión `IPC_ENVELOPE_VERSION`, longitud u32 BE y envelope `CBOR + COSE_Sign1`.
    pub fn send_frame<W: Write, T: serde::Serialize>(writer: &mut W, msg: &T) -> std::io::Result<()> {
        use coset::{CborSerializable, CoseSign1Builder, HeaderBuilder};
        let mut cbor_payload = Vec::new();
        ciborium::into_writer(msg, &mut cbor_payload)
            .map_err(|e| std::io::Error::new(std::io::ErrorKind::InvalidData, e.to_string()))?;
        let protected = HeaderBuilder::new()
            .key_id(vec![IPC_ENVELOPE_VERSION])
            .build();
        let envelope = CoseSign1Builder::new()
            .protected(protected)
            .payload(cbor_payload)
            .build()
            .to_vec()
            .map_err(|e| std::io::Error::new(std::io::ErrorKind::InvalidData, format!("{:?}", e)))?;
        writer.write_all(&[IPC_ENVELOPE_VERSION])?;
        let len = (envelope.len() as u32).to_be_bytes();
        writer.write_all(&len)?;
        writer.write_all(&envelope)?;
        writer.flush()
    }

    /// Recibe una trama verificando el byte de versión `IPC_ENVELOPE_VERSION` y desencapsulando `CBOR + COSE_Sign1`.
    pub fn recv_frame<R: Read, T: serde::de::DeserializeOwned>(reader: &mut R) -> std::io::Result<T> {
        use coset::{CborSerializable, CoseSign1};
        let mut ver = [0u8; 1];
        reader.read_exact(&mut ver)?;
        if ver[0] != IPC_ENVELOPE_VERSION {
            return Err(std::io::Error::new(
                std::io::ErrorKind::InvalidData,
                format!("unsupported IPC envelope version: {}", ver[0]),
            ));
        }
        let mut len_bytes = [0u8; 4];
        reader.read_exact(&mut len_bytes)?;
        let len = u32::from_be_bytes(len_bytes) as usize;
        if len > 16 * 1024 * 1024 {
            return Err(std::io::Error::new(std::io::ErrorKind::InvalidData, "frame too large"));
        }
        let mut buf = vec![0u8; len];
        reader.read_exact(&mut buf)?;
        let sign1 = CoseSign1::from_slice(&buf)
            .map_err(|e| std::io::Error::new(std::io::ErrorKind::InvalidData, format!("invalid COSE_Sign1 frame: {:?}", e)))?;
        let payload = sign1
            .payload
            .ok_or_else(|| std::io::Error::new(std::io::ErrorKind::InvalidData, "missing COSE_Sign1 payload"))?;
        ciborium::from_reader(payload.as_slice())
            .map_err(|e| std::io::Error::new(std::io::ErrorKind::InvalidData, e.to_string()))
    }

    /// Servidor de ejecución que retiene las capacidades del SO y atiende clientes por socket.
    pub struct IpcExecutorServer<A: EffectAdapter<Effect = Vec<u8>, Output = Vec<u8>>> {
        executor: SovereignExecutor<A>,
    }

    impl<A: EffectAdapter<Effect = Vec<u8>, Output = Vec<u8>>> IpcExecutorServer<A> {
        /// Construye un nuevo servidor IPC envolviendo el executor soberano.
        pub fn new(executor: SovereignExecutor<A>) -> Self {
            Self { executor }
        }

        /// Procesa peticiones de un stream Unix de forma síncrona hasta desconexión.
        pub fn handle_client(&mut self, mut stream: UnixStream, resource: &mut A::Resource) -> std::io::Result<()> {
            loop {
                let req: IpcRequest = match recv_frame(&mut stream) {
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
                send_frame(&mut stream, &resp)?;
            }
            Ok(())
        }
    }

    /// Cliente IPC utilizado por agentes desprivilegiados (EDIN) para solicitar efectos protegidos.
    pub struct IpcExecutorClient {
        stream: UnixStream,
    }

    impl IpcExecutorClient {
        /// Conecta a un socket Unix local del executor.
        pub fn connect<P: AsRef<Path>>(path: P) -> std::io::Result<Self> {
            let stream = UnixStream::connect(path)?;
            Ok(Self { stream })
        }

        /// Crea un cliente a partir de un stream Unix ya conectado.
        pub fn from_stream(stream: UnixStream) -> Self {
            Self { stream }
        }

        /// Envía sonda de liveness.
        pub fn ping(&mut self) -> std::io::Result<()> {
            send_frame(&mut self.stream, &IpcRequest::Ping)?;
            match recv_frame::<_, IpcResponse>(&mut self.stream)? {
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
            send_frame(&mut self.stream, &req).map_err(|e| ExecutionError::StorageError(e.to_string()))?;
            let resp = recv_frame::<_, IpcResponse>(&mut self.stream).map_err(|e| ExecutionError::StorageError(e.to_string()))?;
            match resp {
                IpcResponse::Ok(bytes) => Ok(bytes),
                IpcResponse::Err(error) => Err(error),
                IpcResponse::Pong => Err(ExecutionError::EffectExecutionFailed("unexpected pong".into())),
            }
        }
    }
}
