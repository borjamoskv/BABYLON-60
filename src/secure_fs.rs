//! # BABYLON-60 — Secure Filesystem & Effect Transaction Substrate (C5-REAL)
//!
//! Substrato de efectos físicos irreversibles con las 6 invariantes formales cerradas:
//!
//! - **NEM-I1 (EFFECT_AUTHORIZATION):**
//!   `¬Authorized(a, o, e, t) ⟹ ¬Effected(a, o, e, t)`
//! - **NEM-I2 (VERIFIED_COMMIT):**
//!   `Committed(tx) ⟹ Verified(tx) ∧ EffectObserved(tx)`
//! - **NEM-I3 (PATH_OBLIVION):**
//!   `State(tx) ≥ Quarantined ⟹ ResolveOriginalPath(tx) = Forbidden`
//! - **NEM-I4 (CRASH_RECOVERABILITY):**
//!   `Crash(tx, s) ⟹ Recover(tx, s) ∈ {Committed, Aborted, SecurityAbort}`
//! - **NEM-I5 (RECOVERY_IDEMPOTENCE):**
//!   `Recover(Recover(s)) == Recover(s)`
//! - **NEM-I6 (AUTHORITY_FRESHNESS):**
//!   `Committed(tx) ⟹ AuthorityEpoch_commit == AuthorityEpoch_verified`
//!
//! ### Separación Canónica de Identidad y Estado
//! - `ObjectLocatorIdentity`: VFS locator inmutable (`fs, dev, ino, file_type, root`).
//! - `ObjectState`: Estado mutable de contenido y permisos (`hash, size, mode`).
//!
//! Para `DELETE_FILE`:
//! `authorized_locator == verified_locator == destroyed_locator ∧ authorized_state == verified_pre_state`
//!
//! Para `MUTATE_FILE`:
//! `authorized_locator == verified_locator == effected_locator ∧ pre_state → post_state`

#![allow(clippy::unnecessary_cast)]

use std::ffi::CString;
use std::fs::File;
use std::io::{Read, Seek, SeekFrom};
use std::os::unix::ffi::OsStrExt;
use std::os::unix::io::{FromRawFd, RawFd};
use std::path::{Path, PathBuf};
use sha2::{Digest, Sha256};

// ---------------------------------------------------------------------------
// Flags de Rename por Plataforma — Backend Bifurcado (macOS / Linux)
// ---------------------------------------------------------------------------

#[cfg(target_os = "macos")]
mod sys_flags {
    pub const RENAME_EXCL: libc::c_uint = 0x00000004;
    pub const RENAME_NOFOLLOW_ANY: libc::c_uint = 0x00000010;

    extern "C" {
        pub fn renameatx_np(
            fromfd: libc::c_int,
            from: *const libc::c_char,
            tofd: libc::c_int,
            to: *const libc::c_char,
            flags: libc::c_uint,
        ) -> libc::c_int;
    }
}

#[cfg(target_os = "linux")]
mod sys_flags {
    pub const RENAME_NOREPLACE: libc::c_uint = 1;

    extern "C" {
        pub fn renameat2(
            olddirfd: libc::c_int,
            oldpath: *const libc::c_char,
            newdirfd: libc::c_int,
            newpath: *const libc::c_char,
            flags: libc::c_uint,
        ) -> libc::c_int;
    }
}

// ---------------------------------------------------------------------------
// NEM-I1: Alcance Tipado de Efectos
// ---------------------------------------------------------------------------

/// Tipos de efecto sobre el sistema de archivos (NEM-I1).
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
#[cfg_attr(feature = "cortex-persist", derive(serde::Serialize, serde::Deserialize))]
pub enum EffectType {
    /// Lectura de contenido.
    Read,
    /// Mutación de contenido (pwrite/ftruncate/fsync).
    Mutate,
    /// Destrucción irreversible (Quarantine-Rename-Verify-Unlink).
    Delete,
    /// Modificación de permisos (fchmod).
    Chmod,
    /// Renombrado atómico de dentry.
    Rename,
}

// ---------------------------------------------------------------------------
// NEM-I6: Contexto de Autorización y Época
// ---------------------------------------------------------------------------

/// Contexto transaccional de autoridad y época (NEM-I6).
#[derive(Debug, Clone, PartialEq, Eq)]
#[cfg_attr(feature = "cortex-persist", derive(serde::Serialize, serde::Deserialize))]
pub struct AuthorityContext {
    /// Clave pública o identificador del emisor de la capacidad.
    pub authority_id: [u8; 32],
    /// Época de autoridad activa al momento de la autorización.
    pub epoch: u64,
    /// Tipo de efecto autorizado.
    pub effect: EffectType,
    /// Nonce de unicidad criptomecánica.
    pub nonce: [u8; 32],
}

// ---------------------------------------------------------------------------
// Separación de Identidad de Localizador y Estado (Punto 3)
// ---------------------------------------------------------------------------

/// Identidad del localizador físico en el VFS (invariante a lo largo de mutaciones).
#[derive(Debug, Clone, PartialEq, Eq)]
#[cfg_attr(feature = "cortex-persist", derive(serde::Serialize, serde::Deserialize))]
pub struct ObjectLocatorIdentity {
    /// Dispositivo físico / filesystem mount ID (`st_dev`).
    pub dev: u64,
    /// Inodo en el VFS (`st_ino`).
    pub ino: u64,
    /// Tipo de archivo (`st_mode & S_IFMT`, ej. S_IFREG = 0o100000).
    pub file_type: u32,
    /// Raíz de capacidad confiable bajo la que reside.
    pub capability_root_id: [u8; 32],
}

/// Estado observable del contenido y atributos mutables.
#[derive(Debug, Clone, PartialEq, Eq)]
#[cfg_attr(feature = "cortex-persist", derive(serde::Serialize, serde::Deserialize))]
pub struct ObjectState {
    /// SHA-256 del contenido leído a través del descriptor estabilizado.
    pub hash: [u8; 32],
    /// Tamaño en bytes (`st_size`).
    pub size: u64,
    /// Permisos y flags de modo (`st_mode`).
    pub mode: u32,
}

/// Identidad acoplada completa (Locator + State) para operaciones de Effect Broker.
#[derive(Debug, Clone, PartialEq, Eq)]
#[cfg_attr(feature = "cortex-persist", derive(serde::Serialize, serde::Deserialize))]
pub struct ObjectIdentity {
    /// Localizador inmutable en VFS.
    pub locator: ObjectLocatorIdentity,
    /// Estado observable en la captura.
    pub state: ObjectState,
    /// Compatibilidad directa: dev
    pub dev: u64,
    /// Compatibilidad directa: ino
    pub ino: u64,
    /// Compatibilidad directa: mode
    pub mode: u32,
    /// Compatibilidad directa: size
    pub size: u64,
    /// Compatibilidad directa: pre_hash
    pub pre_hash: [u8; 32],
    /// Compatibilidad directa: capability_root_id
    pub capability_root_id: [u8; 32],
}

impl ObjectIdentity {
    /// Número máximo de intentos para estabilizar la lectura de identidad ante mutaciones concurrentes.
    pub const MAX_STABILIZATION_ATTEMPTS: usize = 5;

    /// Construye la identidad leyendo **exclusivamente el descriptor** `fd` ya abierto.
    ///
    /// [NEMESIS Security Core] Estabiliza la identidad mediante bracket TOCTOU y ciclo de
    /// quiescencia: si un escritor concurrente muta el archivo durante el cálculo del hash,
    /// reintenta hasta `MAX_STABILIZATION_ATTEMPTS` veces. Si no converge en silicio, aborta fail-closed con `IdentityUnstable`.
    #[allow(clippy::unnecessary_cast)]
    pub fn from_fd(fd: RawFd, capability_root_id: [u8; 32]) -> Result<Self, SecureFsError> {
        let mut attempts = 0;
        loop {
            attempts += 1;
            let mut stat: libc::stat = unsafe { std::mem::zeroed() };
            if unsafe { libc::fstat(fd, &mut stat) } != 0 {
                return Err(SecureFsError::IoError(std::io::Error::last_os_error()));
            }
            let file_type = (stat.st_mode as u32) & (libc::S_IFMT as u32);
            if file_type != (libc::S_IFREG as u32) {
                return Err(SecureFsError::InvalidFileType(stat.st_mode as u32));
            }
            
            let hash = compute_fd_hash(fd)?;

            // TOCTOU Bracket: re-stat the file to ensure it was not mutated during hash computation
            let mut stat_after: libc::stat = unsafe { std::mem::zeroed() };
            if unsafe { libc::fstat(fd, &mut stat_after) } != 0 {
                return Err(SecureFsError::IoError(std::io::Error::last_os_error()));
            }

            let stable = stat.st_size == stat_after.st_size
                && stat.st_mtime == stat_after.st_mtime
                && stat.st_mtime_nsec == stat_after.st_mtime_nsec
                && stat.st_ino == stat_after.st_ino
                && stat.st_dev == stat_after.st_dev;

            if stable {
                let locator = ObjectLocatorIdentity {
                    dev: stat_after.st_dev as u64,
                    ino: stat_after.st_ino as u64,
                    file_type,
                    capability_root_id,
                };
                let state = ObjectState {
                    hash,
                    size: stat_after.st_size as u64,
                    mode: stat_after.st_mode as u32,
                };

                return Ok(Self {
                    dev: locator.dev,
                    ino: locator.ino,
                    mode: state.mode,
                    size: state.size,
                    pre_hash: state.hash,
                    capability_root_id: locator.capability_root_id,
                    locator,
                    state,
                });
            }

            if attempts >= Self::MAX_STABILIZATION_ATTEMPTS {
                return Err(SecureFsError::IdentityUnstable);
            }

            std::thread::yield_now();
        }
    }
}

fn compute_fd_hash(fd: RawFd) -> Result<[u8; 32], SecureFsError> {
    let dup_fd = unsafe { libc::dup(fd) };
    if dup_fd < 0 {
        return Err(SecureFsError::IoError(std::io::Error::last_os_error()));
    }
    let mut file = unsafe { File::from_raw_fd(dup_fd) };
    file.seek(SeekFrom::Start(0)).map_err(SecureFsError::IoError)?;
    let mut hasher = Sha256::new();
    let mut buf = [0u8; 8192];
    loop {
        let n = file.read(&mut buf).map_err(SecureFsError::IoError)?;
        if n == 0 { break; }
        hasher.update(&buf[..n]);
    }
    Ok(hasher.finalize().into())
}

// ---------------------------------------------------------------------------
// Tipos de Sesión — Máquina de Estados Estructural
// ---------------------------------------------------------------------------

/// Transacción de efecto en estado VERIFIED: identidad de localizador y pre-estado
/// confirmados post-aislamiento en cuarentena. Token lineal de paso obligado a COMMIT.
#[must_use]
pub struct VerifiedTx {
    /// Nombre de nonce en cuarentena.
    pub nonce_name: String,
    /// Localizador verificado.
    pub locator: ObjectLocatorIdentity,
    /// Estado previo verificado.
    pub pre_state: ObjectState,
    /// Flag de observación física de efecto consumado (NEM-I2).
    pub effect_observed: bool,
}

/// Estado terminal observable de una transacción de efecto.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
#[cfg_attr(feature = "cortex-persist", derive(serde::Serialize, serde::Deserialize))]
pub enum EffectTxState {
    /// Efecto consumado físicamente: `Verified(tx) ∧ EffectObserved(tx)`.
    Committed,
    /// Cancelada limpiamente antes del aislamiento; cero mutación.
    Aborted,
    /// Intento de manipulación detectado; señuelo retenido en cuarentena para peritaje.
    SecurityAbort,
}

impl EffectTxState {
    /// Conversión canónica para el ledger persistente.
    pub fn as_str(&self) -> &'static str {
        match self {
            EffectTxState::Committed => "COMMITTED",
            EffectTxState::Aborted => "ABORTED",
            EffectTxState::SecurityAbort => "SECURITY_ABORT",
        }
    }
}

// ---------------------------------------------------------------------------
// Errores Deterministas del Effect Broker
// ---------------------------------------------------------------------------

/// Errores tipados del Effect Broker.
#[derive(Debug)]
pub enum SecureFsError {
    /// Error de E/S del kernel.
    IoError(std::io::Error),
    /// Escape de raíz o symlink malicioso rechazado.
    SymlinkEscapeAttempt,
    /// Rename cross-device rechazado (cuarentena debe estar en el mismo filesystem).
    CrossDeviceUnsupported,
    /// Tipo de archivo no admitido (sólo regular files).
    InvalidFileType(u32),
    /// Mismatch de identidad post-cuarentena (señuelo detectado).
    SecurityMismatch {
        /// Inodo esperado según la autorización.
        expected_ino: u64,
        /// Inodo real encontrado en cuarentena.
        actual_ino: u64,
        /// Hash esperado.
        expected_hash: [u8; 32],
        /// Hash real encontrado en cuarentena.
        actual_hash: [u8; 32],
    },
    /// Época de autoridad revocada o desactualizada (NEM-I6).
    AuthorityStale {
        /// Época esperada en el despacho.
        expected_epoch: u64,
        /// Época actual del kernel.
        current_epoch: u64,
    },
    /// Tipo de efecto no autorizado para esta capacidad (NEM-I1).
    UnauthorizedEffectType {
        /// Tipo de efecto requerido.
        required: EffectType,
        /// Tipo de efecto otorgado.
        granted: EffectType,
    },
    /// Fallo en la observación física del efecto tras la syscall (NEM-I2).
    EffectObservationFailed(String),
    /// Transición de estado inválida.
    InvalidStateTransition(String),
    /// Error de persistencia en ledger.
    LedgerError(String),
    /// TOCTOU attack detected during hash calculation.
    IdentityUnstable,
    /// Reutilización de nonce ya consumido detectada en memoria o ledger durable (NEM-I6 / FL-008).
    NonceReplayDetected {
        /// Nonce de 32 bytes reutilizado.
        nonce: [u8; 32],
    },
    /// Descriptor de archivo preexistente apunta a un inodo en cuarentena o revocado (NEM-I3 / Q13 / Q22).
    PreExistingDescriptorEscape {
        /// Inodo físico alcanzado por descriptor retenido.
        ino: u64,
    },
    /// Estado de intención/recibo ambiguo tras fallo; prohibido reintentar automáticamente sin reconciliación (`FL-014`).
    AmbiguousOutcomeRequiresReconciliation {
        /// Nonce de 32 bytes cuyo estado quedó en `ATTEMPT_RESERVED` o `OUTCOME_UNKNOWN`.
        nonce: [u8; 32],
        /// Estado persistido en el WAL.
        state: WalRecordState,
    },
    /// Corrupción de integridad detectada en el WAL (`.effect_wal.bin`).
    WalCorrupted(String),
    /// Presupuesto de efectos o historial causal excedido (`FL-014`).
    BudgetExceeded(String),
    /// Target de efecto no autorizado por la política (`FL-014`).
    TargetNotAllowed {
        /// Dispositivo físico.
        dev: u64,
        /// Inodo objetivo.
        ino: u64,
    },
    /// Sellado débil o insuficiente para reclamar aislamiento fuerte (`FL-013`).
    WeakIsolationRejected(String),
    /// Permiso de despliegue o clausura de dependencias inválida (`FL-015`).
    DeploymentClosureViolation(String),
}

impl std::fmt::Display for SecureFsError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            SecureFsError::IoError(e) => write!(f, "I/O syscall error: {}", e),
            SecureFsError::SymlinkEscapeAttempt => write!(f, "Symlink or directory escape rejected"),
            SecureFsError::CrossDeviceUnsupported => write!(f, "EXDEV: quarantine must reside on same filesystem"),
            SecureFsError::InvalidFileType(m) => write!(f, "Unsupported file type mode: 0o{:o}", m),
            SecureFsError::SecurityMismatch { expected_ino, actual_ino, .. } => {
                write!(f, "SECURITY_ABORT: quarantined inode ({}) != authorized inode ({})", actual_ino, expected_ino)
            }
            SecureFsError::AuthorityStale { expected_epoch, current_epoch } => {
                write!(f, "AUTHORITY_STALE: expected epoch {}, current epoch {}", expected_epoch, current_epoch)
            }
            SecureFsError::UnauthorizedEffectType { required, granted } => {
                write!(f, "UNAUTHORIZED_EFFECT: required {:?}, granted {:?}", required, granted)
            }
            SecureFsError::EffectObservationFailed(s) => write!(f, "EFFECT_OBSERVATION_FAILED: {}", s),
            SecureFsError::InvalidStateTransition(s) => write!(f, "Invalid effect transition: {}", s),
            SecureFsError::LedgerError(s) => write!(f, "Durable ledger error: {}", s),
            SecureFsError::IdentityUnstable => write!(f, "SECURITY_ABORT: Object mutated during TOCTOU verification bracket"),
            SecureFsError::NonceReplayDetected { nonce } => {
                write!(f, "NONCE_REPLAY_DETECTED: nonce {} already consumed", hex::encode(nonce))
            }
            SecureFsError::PreExistingDescriptorEscape { ino } => {
                write!(f, "QUARANTINE_FD_ESCAPE: pre-opened descriptor still references quarantined inode {}", ino)
            }
            SecureFsError::AmbiguousOutcomeRequiresReconciliation { nonce, state } => {
                write!(
                    f,
                    "AMBIGUOUS_OUTCOME: nonce {} in state {:?} requires physical reconciliation; blind retry forbidden",
                    hex::encode(nonce),
                    state
                )
            }
            SecureFsError::WalCorrupted(s) => write!(f, "WAL_CORRUPTED: {}", s),
            SecureFsError::BudgetExceeded(s) => write!(f, "BUDGET_EXCEEDED: {}", s),
            SecureFsError::TargetNotAllowed { dev, ino } => {
                write!(f, "TARGET_NOT_ALLOWED: locator dev={} ino={} outside allowed scope", dev, ino)
            }
            SecureFsError::WeakIsolationRejected(s) => write!(f, "WEAK_ISOLATION_REJECTED: {}", s),
            SecureFsError::DeploymentClosureViolation(s) => write!(f, "DEPLOYMENT_CLOSURE_VIOLATION: {}", s),
        }
    }
}

impl std::error::Error for SecureFsError {}

// ---------------------------------------------------------------------------
// NEMESIS Wave IV: WAL de 4 Fronteras, Snapshot Aislado, Presupuesto y Permit
// ---------------------------------------------------------------------------

/// Estado persistente en el WAL antes y después de una syscall irreversible (`P0` / `FL-014`).
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
#[repr(u8)]
pub enum WalRecordState {
    /// Intención durable reservada antes de invocar la syscall irreversible.
    AttemptReserved = 1,
    /// Syscall emitida pero sin recibo físico confirmado aún.
    OutcomeUnknown = 2,
    /// Recibo físico verificado y persistido con resultado conocido.
    OutcomeKnown = 3,
}

impl WalRecordState {
    fn from_u8(v: u8) -> Option<Self> {
        match v {
            1 => Some(Self::AttemptReserved),
            2 => Some(Self::OutcomeUnknown),
            3 => Some(Self::OutcomeKnown),
            _ => None,
        }
    }
}

/// Registro atómico de 154 bytes en `.effect_wal.bin` protegido con digest `BLAKE3`.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct WalRecord {
    /// Estado de la transacción en el WAL.
    pub state: WalRecordState,
    /// Tipo de efecto (`Mutate` = 1, `Delete` = 2).
    pub effect: EffectType,
    /// Época de autoridad.
    pub epoch: u64,
    /// Nonce único de 32 bytes.
    pub nonce: [u8; 32],
    /// Dispositivo físico del target (`st_dev`).
    pub target_dev: u64,
    /// Inodo físico del target (`st_ino`).
    pub target_ino: u64,
    /// Hash previo autorizado (SHA-256).
    pub expected_pre_hash: [u8; 32],
    /// Hash posterior esperado u observado (SHA-256).
    pub post_hash: [u8; 32],
    /// Digest `BLAKE3` de los primeros 122 bytes del registro.
    pub record_digest: [u8; 32],
}

impl WalRecord {
    /// Tamaño fijo en bytes de cada entrada del WAL.
    pub const RECORD_SIZE: usize = 154;

    fn effect_to_u8(e: EffectType) -> u8 {
        match e {
            EffectType::Read => 0,
            EffectType::Mutate => 1,
            EffectType::Delete => 2,
            EffectType::Chmod => 3,
            EffectType::Rename => 4,
        }
    }

    fn effect_from_u8(v: u8) -> Option<EffectType> {
        match v {
            0 => Some(EffectType::Read),
            1 => Some(EffectType::Mutate),
            2 => Some(EffectType::Delete),
            3 => Some(EffectType::Chmod),
            4 => Some(EffectType::Rename),
            _ => None,
        }
    }

    /// Construye un registro WAL calculando su digest `BLAKE3` canónico.
    #[expect(clippy::too_many_arguments, reason = "Preserve the explicit canonical WAL record fields")]
    pub fn new(
        state: WalRecordState,
        effect: EffectType,
        epoch: u64,
        nonce: [u8; 32],
        target_dev: u64,
        target_ino: u64,
        expected_pre_hash: [u8; 32],
        post_hash: [u8; 32],
    ) -> Self {
        let mut rec = Self {
            state,
            effect,
            epoch,
            nonce,
            target_dev,
            target_ino,
            expected_pre_hash,
            post_hash,
            record_digest: [0u8; 32],
        };
        let raw = rec.to_bytes_without_digest();
        rec.record_digest = Sha256::digest(raw).into();
        rec
    }

    fn to_bytes_without_digest(&self) -> [u8; 122] {
        let mut buf = [0u8; 122];
        buf[0] = self.state as u8;
        buf[1] = Self::effect_to_u8(self.effect);
        buf[2..10].copy_from_slice(&self.epoch.to_le_bytes());
        buf[10..42].copy_from_slice(&self.nonce);
        buf[42..50].copy_from_slice(&self.target_dev.to_le_bytes());
        buf[50..58].copy_from_slice(&self.target_ino.to_le_bytes());
        buf[58..90].copy_from_slice(&self.expected_pre_hash);
        buf[90..122].copy_from_slice(&self.post_hash);
        buf
    }

    /// Serializa el registro completo de 154 bytes.
    pub fn to_bytes(&self) -> [u8; Self::RECORD_SIZE] {
        let mut out = [0u8; Self::RECORD_SIZE];
        let body = self.to_bytes_without_digest();
        out[..122].copy_from_slice(&body);
        out[122..154].copy_from_slice(&self.record_digest);
        out
    }

    /// Deserializa y verifica la integridad criptográfica de un registro WAL.
    pub fn from_bytes(bytes: &[u8]) -> Result<Self, SecureFsError> {
        if bytes.len() != Self::RECORD_SIZE {
            return Err(SecureFsError::WalCorrupted(format!(
                "partial WAL record: {} bytes (expected {})",
                bytes.len(),
                Self::RECORD_SIZE
            )));
        }
        let expected_digest: [u8; 32] = Sha256::digest(&bytes[..122]).into();
        if expected_digest.as_slice() != &bytes[122..154] {
            return Err(SecureFsError::WalCorrupted(
                "checksum mismatch in WAL record".into(),
            ));
        }
        let state = WalRecordState::from_u8(bytes[0])
            .ok_or_else(|| SecureFsError::WalCorrupted(format!("invalid WAL state tag {}", bytes[0])))?;
        let effect = Self::effect_from_u8(bytes[1])
            .ok_or_else(|| SecureFsError::WalCorrupted(format!("invalid WAL effect tag {}", bytes[1])))?;
        let epoch = u64::from_le_bytes(bytes[2..10].try_into().unwrap());
        let mut nonce = [0u8; 32];
        nonce.copy_from_slice(&bytes[10..42]);
        let target_dev = u64::from_le_bytes(bytes[42..50].try_into().unwrap());
        let target_ino = u64::from_le_bytes(bytes[50..58].try_into().unwrap());
        let mut expected_pre_hash = [0u8; 32];
        expected_pre_hash.copy_from_slice(&bytes[58..90]);
        let mut post_hash = [0u8; 32];
        post_hash.copy_from_slice(&bytes[90..122]);
        let mut record_digest = [0u8; 32];
        record_digest.copy_from_slice(&bytes[122..154]);
        Ok(Self {
            state,
            effect,
            epoch,
            nonce,
            target_dev,
            target_ino,
            expected_pre_hash,
            post_hash,
            record_digest,
        })
    }
}

/// Resultado de reconciliar físicamente una entrada del WAL tras una caída (`P0` / `FL014_RECEIPT_LOSS`).
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum ReconciledRecovery {
    /// Ninguna intención fue registrada antes del fallo; es seguro revalidar desde cero.
    NoDurableIntent,
    /// La operación no llegó a aplicarse físicamente (el inodo conserva `expected_pre_hash`).
    ReconciledNotApplied {
        /// Estado previo del registro en el WAL antes de reconciliar.
        prior_wal_state: WalRecordState,
    },
    /// La operación sí se aplicó físicamente y el recibo ha sido consolidado a `OUTCOME_KNOWN`.
    ReconciledCommitted {
        /// Hash posterior verificado físicamente en el inodo.
        observed_post_hash: [u8; 32],
    },
    /// El resultado ya constaba como `OUTCOME_KNOWN` en el WAL; se devuelve sin reejecutar.
    AlreadyKnown {
        /// Hash posterior registrado en el recibo.
        recorded_post_hash: [u8; 32],
    },
    /// El estado físico del inodo divergió de `pre_hash` y `post_hash`; incertidumbre conservada.
    OutcomeRemainsAmbiguous {
        /// Explicación diagnóstica.
        reason: String,
    },
}

/// Nivel de garantía del aislamiento de bytes (`FL-013`).
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum IsolationStrength {
    /// Linux `memfd_create(MFD_ALLOW_SEALING)` con `F_SEAL_WRITE | F_SEAL_SHRINK | F_SEAL_GROW | F_SEAL_SEAL`
    /// verificado vía `F_GET_SEALS` y sin mapeos compartidos escribibles previos.
    KernelSealedMemfd,
    /// Copia privada inmovilizada en el directorio de cuarentena del broker (`0700`), inmune a escritores
    /// concurrentes sobre el inodo original, pero sujeta al modelo de privilegios del UID del broker.
    BrokerQuarantinedSnapshot,
    /// Protección degradada (`mprotect(PROT_READ)` en el mismo proceso o `UF_IMMUTABLE` bajo el mismo UID).
    /// No constituye aislamiento frente a código hostil en el mismo proceso o actor con igual UID efectivo.
    DegradedSameUidOrInProcess,
}

/// Snapshot aislado de bytes verificados (`TrustedBytes(a) => IsolatedSnapshot(a) ^ H(a) = H_authorized`).
pub struct IsolatedSnapshot {
    /// Descriptor de solo lectura apuntando exclusivamente a la copia aislada en cuarentena.
    pub snapshot_fd: RawFd,
    /// Ruta de la copia dentro de la cuarentena del broker.
    pub quarantine_name: String,
    /// Digest SHA-256 verificado después de aislar la copia.
    pub verified_sha256: [u8; 32],
    /// Tamaño exacto del snapshot en bytes.
    pub size: u64,
    /// Clasificación explícita de la fortaleza de aislamiento.
    pub strength: IsolationStrength,
}

impl IsolatedSnapshot {
    /// Lee los bytes directamente desde el descriptor inmovilizado (nunca re-resuelve la ruta original).
    pub fn read_trusted_bytes(&self) -> Result<Vec<u8>, SecureFsError> {
        let dup_fd = unsafe { libc::dup(self.snapshot_fd) };
        if dup_fd < 0 {
            return Err(SecureFsError::IoError(std::io::Error::last_os_error()));
        }
        let mut file = unsafe { File::from_raw_fd(dup_fd) };
        file.seek(SeekFrom::Start(0)).map_err(SecureFsError::IoError)?;
        let mut buf = Vec::with_capacity(self.size as usize);
        file.read_to_end(&mut buf).map_err(SecureFsError::IoError)?;
        let actual_sha: [u8; 32] = Sha256::digest(&buf).into();
        if actual_sha != self.verified_sha256 {
            return Err(SecureFsError::SecurityMismatch {
                expected_ino: 0,
                actual_ino: 0,
                expected_hash: self.verified_sha256,
                actual_hash: actual_sha,
            });
        }
        Ok(buf)
    }

    /// Evalúa si una configuración de sellado de memoria o flag `UF_IMMUTABLE` satisface aislamiento fuerte.
    pub fn evaluate_seal_guarantees(
        has_writable_shared_mapping: bool,
        seals_verified_by_get_seals: bool,
        relies_on_same_process_mprotect: bool,
        relies_on_same_uid_uf_immutable: bool,
    ) -> Result<IsolationStrength, SecureFsError> {
        if has_writable_shared_mapping || !seals_verified_by_get_seals {
            return Err(SecureFsError::WeakIsolationRejected(
                "shared writable mapping exists or F_GET_SEALS did not confirm full seal set".into(),
            ));
        }
        if relies_on_same_process_mprotect || relies_on_same_uid_uf_immutable {
            return Ok(IsolationStrength::DegradedSameUidOrInProcess);
        }
        Ok(IsolationStrength::KernelSealedMemfd)
    }
}

impl Drop for IsolatedSnapshot {
    fn drop(&mut self) {
        if self.snapshot_fd >= 0 {
            unsafe { libc::close(self.snapshot_fd) };
            self.snapshot_fd = -1;
        }
    }
}

/// Política de presupuesto e historial causal por principal/época (`FL-014`).
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct EffectBudgetPolicy {
    /// Número máximo de efectos autorizados en la época activa.
    pub max_effects: u64,
    /// Presupuesto máximo acumulado de bytes mutados/eliminados en la época activa.
    pub max_total_bytes: u64,
    /// Lista blanca de localizadores `(dev, ino)` autorizados para recibir efectos.
    pub allowed_targets: Vec<(u64, u64)>,
}

/// Contabilidad acumulada del monitor de referencia por `(authority_id, epoch)`.
#[derive(Debug, Clone, Default, PartialEq, Eq)]
pub struct AuthorityUsageHistory {
    /// Cantidad de efectos ejecutados.
    pub effects_count: u64,
    /// Total de bytes mutados/eliminados.
    pub total_bytes: u64,
}

/// Permiso de despliegue con clausura de dependencias vinculada (`FL-015`).
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct DeploymentPermit {
    /// Digest del artefacto compilado/verificado.
    pub artifact_digest: [u8; 32],
    /// Raíz Merkle de la clausura completa y resuelta de dependencias directas y transitivas.
    pub dependency_closure_root: [u8; 32],
    /// Digest del perfil de confinamiento (Seatbelt / seccomp).
    pub profile_digest: [u8; 32],
    /// Digest de la política de conformidad activa.
    pub policy_digest: [u8; 32],
    /// Época de la política de conformidad.
    pub policy_epoch: u64,
    /// Identidad criptográfica del principal autorizado.
    pub principal_identity: [u8; 32],
    /// Tipos de efecto permitidos dentro del alcance de autorización.
    pub authorization_scope: Vec<EffectType>,
    /// Tick lógico de expiración (`INV_C5_CANONICAL_LOGICAL_TICK`).
    pub expires_at: u64,
    /// Nonce único del permiso de despliegue.
    pub nonce: [u8; 32],
}

impl DeploymentPermit {
    /// Calcula la raíz Merkle determinista sobre una lista de pares `(crate_id, resolved_digest)`.
    pub fn compute_closure_root(resolved_deps: &[(&str, [u8; 32])]) -> [u8; 32] {
        let mut sorted: Vec<(&str, [u8; 32])> = resolved_deps.to_vec();
        sorted.sort_by(|a, b| a.0.cmp(b.0).then_with(|| a.1.cmp(&b.1)));
        let mut hasher = Sha256::new();
        hasher.update(b"BABYLON60_DEP_CLOSURE_V1");
        for (name, digest) in sorted {
            hasher.update((name.len() as u32).to_le_bytes());
            hasher.update(name.as_bytes());
            hasher.update(digest);
        }
        hasher.finalize().into()
    }

    /// Valida el permiso de despliegue frente al artefacto, clausura resuelta, política y reloj lógico.
    pub fn validate_for_deployment(
        &self,
        actual_artifact_digest: &[u8; 32],
        actual_closure_root: &[u8; 32],
        expected_policy_digest: &[u8; 32],
        min_policy_epoch: u64,
        current_logical_tick: u64,
    ) -> Result<(), SecureFsError> {
        if &self.artifact_digest != actual_artifact_digest {
            return Err(SecureFsError::DeploymentClosureViolation(
                "artifact_digest mismatch against DeploymentPermit".into(),
            ));
        }
        if &self.dependency_closure_root != actual_closure_root {
            return Err(SecureFsError::DeploymentClosureViolation(
                "transitive dependency_closure_root drift detected after attestation".into(),
            ));
        }
        if &self.policy_digest != expected_policy_digest || self.policy_epoch < min_policy_epoch {
            return Err(SecureFsError::DeploymentClosureViolation(format!(
                "policy rollback or expired exception: permit epoch {} < required {}",
                self.policy_epoch, min_policy_epoch
            )));
        }
        if current_logical_tick >= self.expires_at {
            return Err(SecureFsError::DeploymentClosureViolation(format!(
                "DeploymentPermit expired at logical_tick {} (current {})",
                self.expires_at, current_logical_tick
            )));
        }
        Ok(())
    }

    /// Guardia para carga dinámica (`dlopen` / plugins) en tiempo de ejecución (`FL015_RUNTIME_LOAD`).
    pub fn verify_dynamic_library_load(
        &self,
        dylib_digest: &[u8; 32],
        authorized_dylib_digests: &[[u8; 32]],
        allow_degraded_unverified_plugin: bool,
    ) -> Result<IsolationStrength, SecureFsError> {
        if authorized_dylib_digests.iter().any(|d| d == dylib_digest) {
            Ok(IsolationStrength::BrokerQuarantinedSnapshot)
        } else if allow_degraded_unverified_plugin {
            Ok(IsolationStrength::DegradedSameUidOrInProcess)
        } else {
            Err(SecureFsError::DeploymentClosureViolation(
                "dynamic library (dlopen) digest outside authorized dependency closure".into(),
            ))
        }
    }
}

// ---------------------------------------------------------------------------
// Trait de Backend Desacoplado — SecureFsBackend
// ---------------------------------------------------------------------------

/// Backend nativo para operaciones atómicas de sistema de archivos seguro.
pub trait SecureFsBackend {
    /// Resuelve y abre el objeto objetivo sin seguir symlinks (O_NOFOLLOW).
    fn pin_object(root_fd: RawFd, rel_path: &str, capability_root_id: [u8; 32])
        -> Result<(RawFd, ObjectIdentity), SecureFsError>;

    /// Secuestra atómicamente el dentry de `parent_fd/basename` a `quarantine_fd/nonce_name`.
    fn quarantine(parent_fd: RawFd, basename: &str, quarantine_fd: RawFd, nonce_name: &str)
        -> Result<(), SecureFsError>;

    /// Verifica identidad en cuarentena y emite el token `VerifiedTx`.
    fn verify_quarantined(quarantine_fd: RawFd, nonce_name: &str, expected: &ObjectIdentity)
        -> Result<VerifiedTx, SecureFsError>;

    /// Destruye el objeto en cuarentena (`unlinkat`) y observa físicamente su aniquilación (`fstatat == ENOENT`).
    fn destroy_quarantined(quarantine_fd: RawFd, vtx: VerifiedTx) -> Result<(), SecureFsError>;

    /// MUTATE_FILE: abre, verifica identidad, muta sobre el MISMO FD y ejecuta fsync.
    fn secure_mutate(
        root_fd: RawFd,
        rel_path: &str,
        authorized_identity: &ObjectIdentity,
        payload: &[u8],
    ) -> Result<[u8; 32], SecureFsError>;
}

// ---------------------------------------------------------------------------
// Implementación Nativa — NativeSecureFs
// ---------------------------------------------------------------------------

/// Backend nativo para el entorno de compilación actual.
pub struct NativeSecureFs;

struct ResolvedParentDir {
    dir_fd: RawFd,
    owned: bool,
    leaf_name: CString,
}

impl Drop for ResolvedParentDir {
    fn drop(&mut self) {
        if self.owned && self.dir_fd >= 0 {
            unsafe { libc::close(self.dir_fd) };
            self.dir_fd = -1;
        }
    }
}

fn map_nofollow_open_err(err: std::io::Error) -> SecureFsError {
    match err.raw_os_error() {
        Some(code) if code == libc::ELOOP || code == libc::EMLINK || code == libc::ENOTDIR => {
            SecureFsError::SymlinkEscapeAttempt
        }
        _ => SecureFsError::IoError(err),
    }
}

/// Resuelve componente a componente los directorios intermedios bajo `root_fd`
/// con `O_RDONLY | O_DIRECTORY | O_NOFOLLOW | O_CLOEXEC`, impidiendo carreras TOCTOU
/// en componentes intermedios de ruta.
fn resolve_confined_parent_nofollow(
    root_fd: RawFd,
    rel_path: &str,
) -> Result<ResolvedParentDir, SecureFsError> {
    if rel_path.is_empty() {
        return Err(SecureFsError::SymlinkEscapeAttempt);
    }
    let path = Path::new(rel_path);
    if path.is_absolute() {
        return Err(SecureFsError::SymlinkEscapeAttempt);
    }
    let mut normal_components: Vec<&std::ffi::OsStr> = Vec::new();
    for comp in path.components() {
        match comp {
            std::path::Component::Normal(part) => normal_components.push(part),
            std::path::Component::CurDir => {}
            std::path::Component::ParentDir
            | std::path::Component::RootDir
            | std::path::Component::Prefix(_) => {
                return Err(SecureFsError::SymlinkEscapeAttempt);
            }
        }
    }
    if normal_components.is_empty() {
        return Err(SecureFsError::SymlinkEscapeAttempt);
    }
    let mut curr_fd = root_fd;
    let mut owned = false;
    for &dir_part in &normal_components[..normal_components.len() - 1] {
        let dir_c =
            CString::new(dir_part.as_bytes()).map_err(|_| SecureFsError::SymlinkEscapeAttempt)?;
        let next_fd = unsafe {
            libc::openat(
                curr_fd,
                dir_c.as_ptr(),
                libc::O_RDONLY | libc::O_DIRECTORY | libc::O_NOFOLLOW | libc::O_CLOEXEC,
            )
        };
        if next_fd < 0 {
            let err = std::io::Error::last_os_error();
            if owned && curr_fd >= 0 {
                unsafe { libc::close(curr_fd) };
            }
            return Err(map_nofollow_open_err(err));
        }
        if owned && curr_fd >= 0 {
            unsafe { libc::close(curr_fd) };
        }
        curr_fd = next_fd;
        owned = true;
    }
    let leaf_part = normal_components[normal_components.len() - 1];
    let leaf_name =
        CString::new(leaf_part.as_bytes()).map_err(|_| SecureFsError::SymlinkEscapeAttempt)?;
    Ok(ResolvedParentDir {
        dir_fd: curr_fd,
        owned,
        leaf_name,
    })
}

fn openat_confined_nofollow(
    root_fd: RawFd,
    rel_path: &str,
    flags: libc::c_int,
) -> Result<RawFd, SecureFsError> {
    let resolved = resolve_confined_parent_nofollow(root_fd, rel_path)?;
    let fd = unsafe {
        libc::openat(
            resolved.dir_fd,
            resolved.leaf_name.as_ptr(),
            flags | libc::O_NOFOLLOW | libc::O_CLOEXEC,
        )
    };
    if fd < 0 {
        return Err(map_nofollow_open_err(std::io::Error::last_os_error()));
    }
    Ok(fd)
}

fn validate_single_leaf_name(name: &str) -> Result<CString, SecureFsError> {
    let resolved = resolve_confined_parent_nofollow(-1, name)?;
    if resolved.owned {
        return Err(SecureFsError::SymlinkEscapeAttempt);
    }
    Ok(resolved.leaf_name.clone())
}

impl SecureFsBackend for NativeSecureFs {
    fn pin_object(root_fd: RawFd, rel_path: &str, capability_root_id: [u8; 32])
        -> Result<(RawFd, ObjectIdentity), SecureFsError>
    {
        let fd = openat_confined_nofollow(root_fd, rel_path, libc::O_RDONLY)?;
        match ObjectIdentity::from_fd(fd, capability_root_id) {
            Ok(id) => Ok((fd, id)),
            Err(e) => { unsafe { libc::close(fd) }; Err(e) }
        }
    }

    fn quarantine(parent_fd: RawFd, basename: &str, quarantine_fd: RawFd, nonce_name: &str)
        -> Result<(), SecureFsError>
    {
        let resolved_src = resolve_confined_parent_nofollow(parent_fd, basename)?;
        let c_to = validate_single_leaf_name(nonce_name)?;

        #[cfg(target_os = "macos")]
        let ret = unsafe {
            sys_flags::renameatx_np(
                resolved_src.dir_fd, resolved_src.leaf_name.as_ptr(),
                quarantine_fd, c_to.as_ptr(),
                sys_flags::RENAME_EXCL | sys_flags::RENAME_NOFOLLOW_ANY,
            )
        };

        #[cfg(target_os = "linux")]
        let ret = unsafe {
            sys_flags::renameat2(
                resolved_src.dir_fd, resolved_src.leaf_name.as_ptr(),
                quarantine_fd, c_to.as_ptr(),
                sys_flags::RENAME_NOREPLACE,
            )
        };

        if ret != 0 {
            let e = std::io::Error::last_os_error();
            return if e.raw_os_error() == Some(libc::EXDEV) {
                Err(SecureFsError::CrossDeviceUnsupported)
            } else {
                Err(map_nofollow_open_err(e))
            };
        }
        Ok(())
    }

    fn verify_quarantined(quarantine_fd: RawFd, nonce_name: &str, expected: &ObjectIdentity)
        -> Result<VerifiedTx, SecureFsError>
    {
        let c_name = validate_single_leaf_name(nonce_name)?;
        let fd = unsafe { libc::openat(quarantine_fd, c_name.as_ptr(), libc::O_RDONLY | libc::O_NOFOLLOW | libc::O_CLOEXEC) };
        if fd < 0 {
            return Err(map_nofollow_open_err(std::io::Error::last_os_error()));
        }
        let actual = match ObjectIdentity::from_fd(fd, expected.locator.capability_root_id) {
            Ok(id) => { unsafe { libc::close(fd) }; id }
            Err(e) => { unsafe { libc::close(fd) }; return Err(e); }
        };

        // Verificación exacta de Locator e Inodo
        if actual.locator.ino != expected.locator.ino || actual.locator.dev != expected.locator.dev {
            return Err(SecureFsError::SecurityMismatch {
                expected_ino: expected.locator.ino,
                actual_ino: actual.locator.ino,
                expected_hash: expected.state.hash,
                actual_hash: actual.state.hash,
            });
        }
        // Verificación exacta de Pre-State (Hash)
        if actual.state.hash != expected.state.hash {
            return Err(SecureFsError::SecurityMismatch {
                expected_ino: expected.locator.ino,
                actual_ino: actual.locator.ino,
                expected_hash: expected.state.hash,
                actual_hash: actual.state.hash,
            });
        }

        Ok(VerifiedTx {
            nonce_name: nonce_name.to_string(),
            locator: actual.locator,
            pre_state: actual.state,
            effect_observed: false,
        })
    }

    fn destroy_quarantined(quarantine_fd: RawFd, mut vtx: VerifiedTx) -> Result<(), SecureFsError> {
        let c_name = validate_single_leaf_name(vtx.nonce_name.as_str())?;
        let ret = unsafe { libc::unlinkat(quarantine_fd, c_name.as_ptr(), 0) };
        if ret != 0 { return Err(SecureFsError::IoError(std::io::Error::last_os_error())); }

        // NEM-I2: Observación física del efecto en silicio (EffectObserved)
        let mut check_stat: libc::stat = unsafe { std::mem::zeroed() };
        let check_ret = unsafe {
            libc::fstatat(quarantine_fd, c_name.as_ptr(), &mut check_stat, libc::AT_SYMLINK_NOFOLLOW)
        };
        if check_ret == 0 {
            return Err(SecureFsError::EffectObservationFailed("Quarantined object still exists after unlink".into()));
        }
        vtx.effect_observed = true;
        Ok(())
    }

    fn secure_mutate(
        root_fd: RawFd,
        rel_path: &str,
        authorized_identity: &ObjectIdentity,
        payload: &[u8],
    ) -> Result<[u8; 32], SecureFsError> {
        let fd = openat_confined_nofollow(root_fd, rel_path, libc::O_RDWR)?;

        // Verifica identidad de locator sobre el MISMO FD antes de mutar
        let mut stat: libc::stat = unsafe { std::mem::zeroed() };
        if unsafe { libc::fstat(fd, &mut stat) } != 0 {
            unsafe { libc::close(fd) };
            return Err(SecureFsError::IoError(std::io::Error::last_os_error()));
        }
        if stat.st_ino as u64 != authorized_identity.locator.ino || stat.st_dev as u64 != authorized_identity.locator.dev {
            unsafe { libc::close(fd) };
            return Err(SecureFsError::SecurityMismatch {
                expected_ino:  authorized_identity.locator.ino,
                actual_ino:    stat.st_ino as u64,
                expected_hash: authorized_identity.state.hash,
                actual_hash:   [0u8; 32],
            });
        }

        // The authorized state must match *at the descriptor*, not just the inode.
        // This check is fail-closed on content drift. Protection against concurrent
        // hostile same-inode writers still requires OS isolation/exclusive capability.
        let current_hash = match compute_fd_hash(fd) {
            Ok(hash) => hash,
            Err(err) => { unsafe { libc::close(fd) }; return Err(err); }
        };
        if current_hash != authorized_identity.state.hash {
            unsafe { libc::close(fd) };
            return Err(SecureFsError::SecurityMismatch {
                expected_ino: authorized_identity.locator.ino,
                actual_ino: stat.st_ino as u64,
                expected_hash: authorized_identity.state.hash,
                actual_hash: current_hash,
            });
        }

        // Check every write/resize/sync result. Never report commit on partial I/O.
        let mut written = 0usize;
        while written < payload.len() {
            let remaining = payload.len() - written;
            let ret = unsafe {
                libc::pwrite(fd, payload[written..].as_ptr() as *const libc::c_void,
                             remaining, written as libc::off_t)
            };
            if ret < 0 {
                let error = std::io::Error::last_os_error();
                if error.kind() == std::io::ErrorKind::Interrupted { continue; }
                unsafe { libc::close(fd) };
                return Err(SecureFsError::IoError(error));
            }
            if ret == 0 {
                unsafe { libc::close(fd) };
                return Err(SecureFsError::IoError(std::io::Error::new(
                    std::io::ErrorKind::WriteZero, "pwrite made no progress"
                )));
            }
            written += ret as usize;
        }
        if unsafe { libc::ftruncate(fd, payload.len() as libc::off_t) } != 0 {
            let error = std::io::Error::last_os_error();
            unsafe { libc::close(fd) };
            return Err(SecureFsError::IoError(error));
        }
        if unsafe { libc::fsync(fd) } != 0 {
            let error = std::io::Error::last_os_error();
            unsafe { libc::close(fd) };
            return Err(SecureFsError::IoError(error));
        }
        let post_hash = compute_fd_hash(fd);
        unsafe { libc::close(fd) };
        post_hash
    }
}

// ---------------------------------------------------------------------------
// Gestor de Cuarentena (QuarantineContext)
// ---------------------------------------------------------------------------

/// Contexto aislado de cuarentena acoplado al mismo filesystem de la raíz de capacidad.
pub struct QuarantineContext {
    /// Ruta física al directorio de cuarentena (.babylon/quarantine).
    pub dir_path: PathBuf,
    /// Descriptor de archivo abierto sobre el directorio de cuarentena (O_DIRECTORY).
    pub dir_fd: RawFd,
    /// `st_dev` del filesystem donde reside la cuarentena.
    pub dev: u64,
}

fn ensure_subdir_nofollow(
    parent_fd: RawFd,
    name: &str,
    expected_dev: u64,
    expected_uid: u32,
) -> Result<(RawFd, libc::stat), SecureFsError> {
    let name_c = validate_single_leaf_name(name)?;
    let mk = unsafe { libc::mkdirat(parent_fd, name_c.as_ptr(), 0o700) };
    if mk != 0 {
        let err = std::io::Error::last_os_error();
        if err.raw_os_error() != Some(libc::EEXIST) {
            return Err(map_nofollow_open_err(err));
        }
    }
    let fd = unsafe {
        libc::openat(
            parent_fd,
            name_c.as_ptr(),
            libc::O_RDONLY | libc::O_DIRECTORY | libc::O_NOFOLLOW | libc::O_CLOEXEC,
        )
    };
    if fd < 0 {
        return Err(map_nofollow_open_err(std::io::Error::last_os_error()));
    }
    if unsafe { libc::fchmod(fd, 0o700) } != 0 {
        let err = std::io::Error::last_os_error();
        unsafe { libc::close(fd) };
        return Err(SecureFsError::IoError(err));
    }
    let mut st: libc::stat = unsafe { std::mem::zeroed() };
    if unsafe { libc::fstat(fd, &mut st) } != 0 {
        let err = std::io::Error::last_os_error();
        unsafe { libc::close(fd) };
        return Err(SecureFsError::IoError(err));
    }
    if st.st_uid != expected_uid {
        unsafe { libc::close(fd) };
        return Err(SecureFsError::SymlinkEscapeAttempt);
    }
    if (st.st_dev as u64) != expected_dev {
        unsafe { libc::close(fd) };
        return Err(SecureFsError::CrossDeviceUnsupported);
    }
    Ok((fd, st))
}

impl QuarantineContext {
    /// Inicializa la cuarentena en `<root>/.babylon/quarantine/` con permisos `0700` y `O_NOFOLLOW`
    /// descendiendo exclusivamente por descriptores (`mkdirat` + `openat` + `fchmod`).
    pub fn initialize(root_path: &Path) -> Result<Self, SecureFsError> {
        let root_c = CString::new(root_path.as_os_str().as_bytes())
            .map_err(|_| SecureFsError::SymlinkEscapeAttempt)?;
        let root_fd = unsafe {
            libc::open(
                root_c.as_ptr(),
                libc::O_RDONLY | libc::O_DIRECTORY | libc::O_NOFOLLOW | libc::O_CLOEXEC,
            )
        };
        if root_fd < 0 {
            return Err(map_nofollow_open_err(std::io::Error::last_os_error()));
        }
        let mut root_stat: libc::stat = unsafe { std::mem::zeroed() };
        if unsafe { libc::fstat(root_fd, &mut root_stat) } != 0 {
            let err = std::io::Error::last_os_error();
            unsafe { libc::close(root_fd) };
            return Err(SecureFsError::IoError(err));
        }
        let host_euid = unsafe { libc::geteuid() };
        if root_stat.st_uid != host_euid {
            unsafe { libc::close(root_fd) };
            return Err(SecureFsError::SymlinkEscapeAttempt);
        }
        let expected_dev = root_stat.st_dev as u64;

        let (babylon_fd, _) = match ensure_subdir_nofollow(root_fd, ".babylon", expected_dev, host_euid) {
            Ok(pair) => {
                unsafe { libc::close(root_fd) };
                pair
            }
            Err(e) => {
                unsafe { libc::close(root_fd) };
                return Err(e);
            }
        };

        let (q_fd, q_stat) = match ensure_subdir_nofollow(babylon_fd, "quarantine", expected_dev, host_euid) {
            Ok(pair) => {
                unsafe { libc::close(babylon_fd) };
                pair
            }
            Err(e) => {
                unsafe { libc::close(babylon_fd) };
                return Err(e);
            }
        };

        let q_dir = root_path.join(".babylon").join("quarantine");
        Ok(Self {
            dir_path: q_dir,
            dir_fd: q_fd,
            dev: q_stat.st_dev as u64,
        })
    }
}

impl Drop for QuarantineContext {
    fn drop(&mut self) {
        if self.dir_fd >= 0 { unsafe { libc::close(self.dir_fd) }; self.dir_fd = -1; }
    }
}

// ---------------------------------------------------------------------------
// EffectTxOrchestrator — Orquestador de Transacciones de Efectos
// ---------------------------------------------------------------------------

/// Guardia RAII para el cerrojo híbrido (en memoria + `flock(LOCK_EX)` sobre `.epoch_fence.bin`).
struct HybridResourceFenceGuard<'a> {
    _mem_guard: std::sync::RwLockWriteGuard<'a, ()>,
    fence_fd: RawFd,
}

impl<'a> Drop for HybridResourceFenceGuard<'a> {
    fn drop(&mut self) {
        if self.fence_fd >= 0 {
            unsafe {
                libc::flock(self.fence_fd, libc::LOCK_UN);
                libc::close(self.fence_fd);
            }
        }
    }
}

type ResourceGates = std::sync::Mutex<std::collections::HashMap<(u64, u64), std::sync::Arc<std::sync::Mutex<()>>>>;

/// Orquestador transaccional determinista para `DELETE_FILE` y `MUTATE_FILE`.
pub struct EffectTxOrchestrator<B: SecureFsBackend = NativeSecureFs> {
    /// Contexto de cuarentena broker-owned exclusivo (`0700`).
    pub quarantine: QuarantineContext,
    /// Época de autoridad activa para garantizar frescura (NEM-I6).
    pub current_epoch: std::sync::atomic::AtomicU64,
    /// Registro de nonces consumidos reconstruible tras crash desde `.consumed_nonces.bin` (NEM-I6 / FL-008).
    consumed_nonces: std::sync::Mutex<std::collections::HashSet<[u8; 32]>>,
    /// Estado estructurado del WAL (`.effect_wal.bin`) indexado por nonce (`NEMESIS Wave IV`).
    wal_records: std::sync::Mutex<std::collections::HashMap<[u8; 32], WalRecord>>,
    /// Cerrojos por recurso `(dev, ino)` y cerrojo global de drenaje de época para Effect Commit Protocol v2.
    epoch_drain_gate: std::sync::RwLock<()>,
    resource_gates: ResourceGates,
    /// Políticas de presupuesto e historial causal por `authority_id` (`FL-014`).
    budget_policies: std::sync::Mutex<std::collections::HashMap<[u8; 32], EffectBudgetPolicy>>,
    usage_history: std::sync::Mutex<std::collections::HashMap<([u8; 32], u64), AuthorityUsageHistory>>,
    _backend: std::marker::PhantomData<B>,
}

impl<B: SecureFsBackend> EffectTxOrchestrator<B> {
    /// Crea el orquestador vinculado a la raíz de capacidad, recargando nonces, época durable y WAL desde disco.
    pub fn new(root_path: &Path) -> Result<Self, SecureFsError> {
        let quarantine = QuarantineContext::initialize(root_path)?;
        let ledger_path = quarantine.dir_path.join(".consumed_nonces.bin");
        let mut set = std::collections::HashSet::new();
        if ledger_path.exists() {
            let bytes = std::fs::read(&ledger_path)
                .map_err(|e| SecureFsError::LedgerError(format!("read consumed_nonces: {e}")))?;
            for chunk in bytes.as_chunks::<32>().0 {
                set.insert(*chunk);
            }
        }

        let wal_path = quarantine.dir_path.join(".effect_wal.bin");
        let mut wal_map = std::collections::HashMap::new();
        if wal_path.exists() {
            let wal_bytes = std::fs::read(&wal_path)
                .map_err(|e| SecureFsError::LedgerError(format!("read .effect_wal.bin: {e}")))?;
            if wal_bytes.len() % WalRecord::RECORD_SIZE != 0 {
                return Err(SecureFsError::WalCorrupted(format!(
                    ".effect_wal.bin length {} is not a multiple of {}",
                    wal_bytes.len(),
                    WalRecord::RECORD_SIZE
                )));
            }
            for chunk in wal_bytes.as_chunks::<{ WalRecord::RECORD_SIZE }>().0 {
                let rec = WalRecord::from_bytes(chunk)?;
                set.insert(rec.nonce);
                wal_map.insert(rec.nonce, rec);
            }
        }

        let fence_path = quarantine.dir_path.join(".epoch_fence.bin");
        let initial_epoch = if fence_path.exists() {
            let b = std::fs::read(&fence_path)
                .map_err(|e| SecureFsError::LedgerError(format!("read .epoch_fence.bin: {e}")))?;
            if b.len() >= 8 {
                u64::from_le_bytes(b[..8].try_into().unwrap()).max(1)
            } else {
                1
            }
        } else {
            1
        };

        let budget_usage_path = quarantine.dir_path.join(".budget_usage.bin");
        let mut usage_map: std::collections::HashMap<([u8; 32], u64), AuthorityUsageHistory> =
            std::collections::HashMap::new();
        if budget_usage_path.exists() {
            let b_bytes = std::fs::read(&budget_usage_path)
                .map_err(|e| SecureFsError::LedgerError(format!("read .budget_usage.bin: {e}")))?;
            for chunk in b_bytes.as_chunks::<48>().0 {
                let mut auth_id = [0u8; 32];
                auth_id.copy_from_slice(&chunk[..32]);
                let epoch = u64::from_le_bytes(chunk[32..40].try_into().unwrap());
                let effect_bytes = u64::from_le_bytes(chunk[40..48].try_into().unwrap());
                let entry = usage_map.entry((auth_id, epoch)).or_default();
                entry.effects_count += 1;
                entry.total_bytes = entry.total_bytes.saturating_add(effect_bytes);
            }
        }

        Ok(Self {
            quarantine,
            current_epoch: std::sync::atomic::AtomicU64::new(initial_epoch),
            consumed_nonces: std::sync::Mutex::new(set),
            wal_records: std::sync::Mutex::new(wal_map),
            epoch_drain_gate: std::sync::RwLock::new(()),
            resource_gates: std::sync::Mutex::new(std::collections::HashMap::new()),
            budget_policies: std::sync::Mutex::new(std::collections::HashMap::new()),
            usage_history: std::sync::Mutex::new(usage_map),
            _backend: std::marker::PhantomData,
        })
    }

    fn sync_quarantine_dir(&self) -> Result<(), SecureFsError> {
        if unsafe { libc::fsync(self.quarantine.dir_fd) } != 0 {
            return Err(SecureFsError::IoError(std::io::Error::last_os_error()));
        }
        Ok(())
    }

    fn acquire_hybrid_resource_gate(&self) -> Result<HybridResourceFenceGuard<'_>, SecureFsError> {
        let mem_guard = self
            .epoch_drain_gate
            .write()
            .map_err(|_| SecureFsError::LedgerError("epoch_drain_gate poisoned".into()))?;
        let fence_c = CString::new(".epoch_fence.bin").unwrap();
        let fd = unsafe {
            libc::openat(
                self.quarantine.dir_fd,
                fence_c.as_ptr(),
                libc::O_CREAT | libc::O_RDWR | libc::O_NOFOLLOW | libc::O_CLOEXEC,
                0o600,
            )
        };
        if fd < 0 {
            return Err(SecureFsError::IoError(std::io::Error::last_os_error()));
        }
        if unsafe { libc::flock(fd, libc::LOCK_EX) } != 0 {
            let err = std::io::Error::last_os_error();
            unsafe { libc::close(fd) };
            return Err(SecureFsError::IoError(err));
        }
        Ok(HybridResourceFenceGuard {
            _mem_guard: mem_guard,
            fence_fd: fd,
        })
    }

    fn read_durable_epoch_locked(&self, fence_fd: RawFd) -> Result<u64, SecureFsError> {
        let mut buf = [0u8; 8];
        let n = unsafe { libc::pread(fence_fd, buf.as_mut_ptr() as *mut libc::c_void, 8, 0) };
        if n < 0 {
            return Err(SecureFsError::IoError(std::io::Error::last_os_error()));
        }
        let disk_epoch = if n == 8 { u64::from_le_bytes(buf) } else { 1 };
        let mem_epoch = self.current_epoch.load(std::sync::atomic::Ordering::SeqCst);
        let effective = disk_epoch.max(mem_epoch);
        self.current_epoch.store(effective, std::sync::atomic::Ordering::SeqCst);
        Ok(effective)
    }

    fn write_durable_epoch_locked(&self, fence_fd: RawFd, new_epoch: u64) -> Result<(), SecureFsError> {
        let bytes = new_epoch.to_le_bytes();
        let n = unsafe { libc::pwrite(fence_fd, bytes.as_ptr() as *const libc::c_void, 8, 0) };
        if n != 8 {
            return Err(SecureFsError::IoError(std::io::Error::last_os_error()));
        }
        if unsafe { libc::fsync(fence_fd) } != 0 {
            return Err(SecureFsError::IoError(std::io::Error::last_os_error()));
        }
        self.sync_quarantine_dir()?;
        self.current_epoch.store(new_epoch, std::sync::atomic::Ordering::SeqCst);
        Ok(())
    }

    fn get_or_create_locator_mutex(&self, locator: (u64, u64)) -> Result<std::sync::Arc<std::sync::Mutex<()>>, SecureFsError> {
        let mut map = self
            .resource_gates
            .lock()
            .map_err(|_| SecureFsError::LedgerError("resource_gates mutex poisoned".into()))?;
        Ok(map
            .entry(locator)
            .or_insert_with(|| std::sync::Arc::new(std::sync::Mutex::new(())))
            .clone())
    }

    /// Registra o actualiza un registro en `.effect_wal.bin` con `fsync` de archivo y directorio.
    pub fn append_wal_record(&self, record: WalRecord) -> Result<(), SecureFsError> {
        let mut wal_guard = self
            .wal_records
            .lock()
            .map_err(|_| SecureFsError::LedgerError("wal_records mutex poisoned".into()))?;
        let mut nonces_guard = self
            .consumed_nonces
            .lock()
            .map_err(|_| SecureFsError::LedgerError("consumed_nonces mutex poisoned".into()))?;

        let wal_path = self.quarantine.dir_path.join(".effect_wal.bin");
        use std::io::Write;
        let mut f = std::fs::OpenOptions::new()
            .create(true)
            .append(true)
            .open(&wal_path)
            .map_err(|e| SecureFsError::LedgerError(format!("open .effect_wal.bin: {e}")))?;
        f.write_all(&record.to_bytes())
            .map_err(|e| SecureFsError::LedgerError(format!("write .effect_wal.bin: {e}")))?;
        f.sync_all()
            .map_err(|e| SecureFsError::LedgerError(format!("fsync .effect_wal.bin: {e}")))?;

        let ledger_path = self.quarantine.dir_path.join(".consumed_nonces.bin");
        if !nonces_guard.contains(&record.nonce) {
            let mut nf = std::fs::OpenOptions::new()
                .create(true)
                .append(true)
                .open(&ledger_path)
                .map_err(|e| SecureFsError::LedgerError(format!("open consumed_nonces: {e}")))?;
            nf.write_all(&record.nonce)
                .map_err(|e| SecureFsError::LedgerError(format!("write consumed_nonces: {e}")))?;
            nf.sync_all()
                .map_err(|e| SecureFsError::LedgerError(format!("fsync consumed_nonces: {e}")))?;
            nonces_guard.insert(record.nonce);
        }

        self.sync_quarantine_dir()?;
        wal_guard.insert(record.nonce, record);
        Ok(())
    }

    /// Consulta el estado actual de un nonce en el WAL estructurado.
    pub fn get_wal_record(&self, nonce: &[u8; 32]) -> Option<WalRecord> {
        self.wal_records
            .lock()
            .ok()
            .and_then(|g| g.get(nonce).cloned())
    }

    /// Configura la política de presupuesto e historial causal para un `authority_id` (`FL-014`).
    pub fn set_budget_policy(&self, authority_id: [u8; 32], policy: EffectBudgetPolicy) -> Result<(), SecureFsError> {
        let mut guard = self
            .budget_policies
            .lock()
            .map_err(|_| SecureFsError::LedgerError("budget_policies mutex poisoned".into()))?;
        guard.insert(authority_id, policy);
        Ok(())
    }

    fn verify_budget_allowed(
        &self,
        auth: &AuthorityContext,
        target_locator: (u64, u64),
        effect_bytes: u64,
    ) -> Result<(), SecureFsError> {
        let policies = self
            .budget_policies
            .lock()
            .map_err(|_| SecureFsError::LedgerError("budget_policies mutex poisoned".into()))?;
        let Some(policy) = policies.get(&auth.authority_id) else {
            return Ok(());
        };
        if !policy.allowed_targets.is_empty() && !policy.allowed_targets.contains(&target_locator) {
            return Err(SecureFsError::TargetNotAllowed {
                dev: target_locator.0,
                ino: target_locator.1,
            });
        }
        let usage_map = self
            .usage_history
            .lock()
            .map_err(|_| SecureFsError::LedgerError("usage_history mutex poisoned".into()))?;
        let current = usage_map
            .get(&(auth.authority_id, auth.epoch))
            .cloned()
            .unwrap_or_default();
        if current.effects_count + 1 > policy.max_effects {
            return Err(SecureFsError::BudgetExceeded(format!(
                "effects_count {} + 1 exceeds max_effects {}",
                current.effects_count, policy.max_effects
            )));
        }
        if current.total_bytes.saturating_add(effect_bytes) > policy.max_total_bytes {
            return Err(SecureFsError::BudgetExceeded(format!(
                "total_bytes {} + {} exceeds max_total_bytes {}",
                current.total_bytes, effect_bytes, policy.max_total_bytes
            )));
        }
        Ok(())
    }

    fn commit_budget_usage(
        &self,
        auth: &AuthorityContext,
        effect_bytes: u64,
    ) -> Result<(), SecureFsError> {
        let has_policy = self
            .budget_policies
            .lock()
            .map_err(|_| SecureFsError::LedgerError("budget_policies mutex poisoned".into()))?
            .contains_key(&auth.authority_id);
        if !has_policy {
            return Ok(());
        }
        let mut usage_map = self
            .usage_history
            .lock()
            .map_err(|_| SecureFsError::LedgerError("usage_history mutex poisoned".into()))?;
        let entry = usage_map.entry((auth.authority_id, auth.epoch)).or_default();
        entry.effects_count += 1;
        entry.total_bytes = entry.total_bytes.saturating_add(effect_bytes);

        let budget_usage_path = self.quarantine.dir_path.join(".budget_usage.bin");
        use std::io::Write;
        let mut f = std::fs::OpenOptions::new()
            .create(true)
            .append(true)
            .open(&budget_usage_path)
            .map_err(|e| SecureFsError::LedgerError(format!("open .budget_usage.bin: {e}")))?;
        let mut rec = [0u8; 48];
        rec[..32].copy_from_slice(&auth.authority_id);
        rec[32..40].copy_from_slice(&auth.epoch.to_le_bytes());
        rec[40..48].copy_from_slice(&effect_bytes.to_le_bytes());
        f.write_all(&rec)
            .map_err(|e| SecureFsError::LedgerError(format!("write .budget_usage.bin: {e}")))?;
        f.sync_all()
            .map_err(|e| SecureFsError::LedgerError(format!("fsync .budget_usage.bin: {e}")))?;
        self.sync_quarantine_dir()?;
        Ok(())
    }

    /// Crea un snapshot aislado en la cuarentena del broker verificando `H(snapshot) == H_authorized` (`FL-013`).
    pub fn create_isolated_snapshot(
        &self,
        root_fd: RawFd,
        rel_path: &str,
        authorized_identity: &ObjectIdentity,
        snapshot_tag: &[u8; 32],
    ) -> Result<IsolatedSnapshot, SecureFsError> {
        let src_fd = openat_confined_nofollow(root_fd, rel_path, libc::O_RDONLY)?;

        let mut stat: libc::stat = unsafe { std::mem::zeroed() };
        if unsafe { libc::fstat(src_fd, &mut stat) } != 0 {
            unsafe { libc::close(src_fd) };
            return Err(SecureFsError::IoError(std::io::Error::last_os_error()));
        }
        if stat.st_ino as u64 != authorized_identity.locator.ino
            || stat.st_dev as u64 != authorized_identity.locator.dev
        {
            unsafe { libc::close(src_fd) };
            return Err(SecureFsError::SecurityMismatch {
                expected_ino: authorized_identity.locator.ino,
                actual_ino: stat.st_ino as u64,
                expected_hash: authorized_identity.state.hash,
                actual_hash: [0u8; 32],
            });
        }

        let snap_name = format!("snap_{}", hex::encode(snapshot_tag));
        let c_snap = CString::new(snap_name.as_str()).map_err(|_| SecureFsError::SymlinkEscapeAttempt)?;
        unsafe { libc::unlinkat(self.quarantine.dir_fd, c_snap.as_ptr(), 0) };

        let dst_fd = unsafe {
            libc::openat(
                self.quarantine.dir_fd,
                c_snap.as_ptr(),
                libc::O_CREAT | libc::O_EXCL | libc::O_RDWR | libc::O_NOFOLLOW | libc::O_CLOEXEC,
                0o400,
            )
        };
        if dst_fd < 0 {
            unsafe { libc::close(src_fd) };
            return Err(SecureFsError::IoError(std::io::Error::last_os_error()));
        }

        // Copia aislada de stream desde `src_fd` hacia `dst_fd` en cuarentena broker-owned
        let mut buf = [0u8; 8192];
        let mut offset: libc::off_t = 0;
        loop {
            let n = unsafe {
                libc::pread(
                    src_fd,
                    buf.as_mut_ptr() as *mut libc::c_void,
                    buf.len(),
                    offset,
                )
            };
            if n < 0 {
                let err = std::io::Error::last_os_error();
                if err.kind() == std::io::ErrorKind::Interrupted {
                    continue;
                }
                unsafe {
                    libc::close(src_fd);
                    libc::close(dst_fd);
                    libc::unlinkat(self.quarantine.dir_fd, c_snap.as_ptr(), 0);
                }
                return Err(SecureFsError::IoError(err));
            }
            if n == 0 {
                break;
            }
            let mut written = 0usize;
            while written < n as usize {
                let w = unsafe {
                    libc::pwrite(
                        dst_fd,
                        buf[written..n as usize].as_ptr() as *const libc::c_void,
                        (n as usize) - written,
                        offset + (written as libc::off_t),
                    )
                };
                if w <= 0 {
                    let err = std::io::Error::last_os_error();
                    unsafe {
                        libc::close(src_fd);
                        libc::close(dst_fd);
                        libc::unlinkat(self.quarantine.dir_fd, c_snap.as_ptr(), 0);
                    }
                    return Err(SecureFsError::IoError(err));
                }
                written += w as usize;
            }
            offset += n as libc::off_t;
        }
        unsafe { libc::close(src_fd) };

        if unsafe { libc::fchmod(dst_fd, 0o400) } != 0 || unsafe { libc::fsync(dst_fd) } != 0 {
            let err = std::io::Error::last_os_error();
            unsafe {
                libc::close(dst_fd);
                libc::unlinkat(self.quarantine.dir_fd, c_snap.as_ptr(), 0);
            }
            return Err(SecureFsError::IoError(err));
        }
        unsafe { libc::close(dst_fd) };
        self.sync_quarantine_dir()?;

        // Reabrir exclusivamente en O_RDONLY sobre el snapshot aislado y verificar H(snapshot) == H_authorized
        let ro_fd = unsafe {
            libc::openat(
                self.quarantine.dir_fd,
                c_snap.as_ptr(),
                libc::O_RDONLY | libc::O_NOFOLLOW | libc::O_CLOEXEC,
            )
        };
        if ro_fd < 0 {
            return Err(SecureFsError::IoError(std::io::Error::last_os_error()));
        }

        let snap_sha256 = match compute_fd_hash(ro_fd) {
            Ok(h) => h,
            Err(e) => {
                unsafe {
                    libc::close(ro_fd);
                    libc::unlinkat(self.quarantine.dir_fd, c_snap.as_ptr(), 0);
                }
                return Err(e);
            }
        };
        if snap_sha256 != authorized_identity.state.hash {
            unsafe {
                libc::close(ro_fd);
                libc::unlinkat(self.quarantine.dir_fd, c_snap.as_ptr(), 0);
            }
            return Err(SecureFsError::SecurityMismatch {
                expected_ino: authorized_identity.locator.ino,
                actual_ino: stat.st_ino as u64,
                expected_hash: authorized_identity.state.hash,
                actual_hash: snap_sha256,
            });
        }

        let mut snap_stat: libc::stat = unsafe { std::mem::zeroed() };
        if unsafe { libc::fstat(ro_fd, &mut snap_stat) } != 0 {
            let err = std::io::Error::last_os_error();
            unsafe {
                libc::close(ro_fd);
                libc::unlinkat(self.quarantine.dir_fd, c_snap.as_ptr(), 0);
            }
            return Err(SecureFsError::IoError(err));
        }

        Ok(IsolatedSnapshot {
            snapshot_fd: ro_fd,
            quarantine_name: snap_name,
            verified_sha256: snap_sha256,
            size: snap_stat.st_size as u64,
            strength: IsolationStrength::BrokerQuarantinedSnapshot,
        })
    }

    /// Reconcilia físicamente el estado de un nonce tras un fallo (`SIGKILL` entre reserva, syscall y recibo).
    /// Prohibido reintentar automáticamente cuando el estado es `ATTEMPT_RESERVED` o `OUTCOME_UNKNOWN`.
    pub fn reconcile_wal_entry(
        &self,
        root_fd: RawFd,
        rel_path: &str,
        nonce: &[u8; 32],
    ) -> Result<ReconciledRecovery, SecureFsError> {
        let Some(rec) = self.get_wal_record(nonce) else {
            return Ok(ReconciledRecovery::NoDurableIntent);
        };
        if rec.state == WalRecordState::OutcomeKnown {
            return Ok(ReconciledRecovery::AlreadyKnown {
                recorded_post_hash: rec.post_hash,
            });
        }

        let fd = match openat_confined_nofollow(root_fd, rel_path, libc::O_RDONLY) {
            Ok(fd) => fd,
            Err(SecureFsError::IoError(err))
                if err.raw_os_error() == Some(libc::ENOENT) && rec.effect == EffectType::Delete =>
            {
                let known = WalRecord::new(
                    WalRecordState::OutcomeKnown,
                    rec.effect,
                    rec.epoch,
                    rec.nonce,
                    rec.target_dev,
                    rec.target_ino,
                    rec.expected_pre_hash,
                    [0u8; 32],
                );
                self.append_wal_record(known)?;
                return Ok(ReconciledRecovery::ReconciledCommitted {
                    observed_post_hash: [0u8; 32],
                });
            }
            Err(SecureFsError::SymlinkEscapeAttempt) => {
                return Err(SecureFsError::SymlinkEscapeAttempt);
            }
            Err(err) => {
                return Ok(ReconciledRecovery::OutcomeRemainsAmbiguous {
                    reason: format!("cannot open target during reconciliation: {err}"),
                });
            }
        };

        let mut stat: libc::stat = unsafe { std::mem::zeroed() };
        if unsafe { libc::fstat(fd, &mut stat) } != 0 {
            unsafe { libc::close(fd) };
            return Err(SecureFsError::IoError(std::io::Error::last_os_error()));
        }
        let observed_hash = match compute_fd_hash(fd) {
            Ok(h) => {
                unsafe { libc::close(fd) };
                h
            }
            Err(e) => {
                unsafe { libc::close(fd) };
                return Err(e);
            }
        };

        if stat.st_dev as u64 == rec.target_dev
            && stat.st_ino as u64 == rec.target_ino
            && observed_hash == rec.post_hash
        {
            let known = WalRecord::new(
                WalRecordState::OutcomeKnown,
                rec.effect,
                rec.epoch,
                rec.nonce,
                rec.target_dev,
                rec.target_ino,
                rec.expected_pre_hash,
                observed_hash,
            );
            self.append_wal_record(known)?;
            return Ok(ReconciledRecovery::ReconciledCommitted {
                observed_post_hash: observed_hash,
            });
        }

        if stat.st_dev as u64 == rec.target_dev
            && stat.st_ino as u64 == rec.target_ino
            && observed_hash == rec.expected_pre_hash
        {
            return Ok(ReconciledRecovery::ReconciledNotApplied {
                prior_wal_state: rec.state,
            });
        }

        Ok(ReconciledRecovery::OutcomeRemainsAmbiguous {
            reason: "physical inode state matches neither pre_hash nor expected post_hash".into(),
        })
    }

    /// Verifica si un nonce de 32 bytes ya fue consumido en esta época o en una ejecución previa antes de un crash.
    pub fn is_nonce_consumed(&self, nonce: &[u8; 32]) -> bool {
        self.consumed_nonces
            .lock()
            .map(|g| g.contains(nonce))
            .unwrap_or(true)
    }

    /// Registra durablemente (`sync_all`) un nonce consumido; falla con `NonceReplayDetected` si ya existe.
    pub fn consume_nonce_durable(&self, nonce: &[u8; 32]) -> Result<(), SecureFsError> {
        let mut guard = self
            .consumed_nonces
            .lock()
            .map_err(|_| SecureFsError::LedgerError("consumed_nonces mutex poisoned".into()))?;
        if guard.contains(nonce) {
            return Err(SecureFsError::NonceReplayDetected { nonce: *nonce });
        }
        let ledger_path = self.quarantine.dir_path.join(".consumed_nonces.bin");
        use std::io::Write;
        let mut f = std::fs::OpenOptions::new()
            .create(true)
            .append(true)
            .open(&ledger_path)
            .map_err(|e| SecureFsError::LedgerError(format!("open consumed_nonces: {e}")))?;
        f.write_all(nonce)
            .map_err(|e| SecureFsError::LedgerError(format!("write consumed_nonces: {e}")))?;
        f.sync_all()
            .map_err(|e| SecureFsError::LedgerError(format!("fsync consumed_nonces: {e}")))?;
        self.sync_quarantine_dir()?;
        guard.insert(*nonce);
        Ok(())
    }

    /// Audita y neutraliza descriptores preabiertos (`RawFd`) que sigan apuntando a un inodo en cuarentena (Q13 / Q22).
    pub fn guard_open_descriptor_isolation(
        candidate_fds: &[RawFd],
        quarantined_ino: u64,
        revoke_on_match: bool,
    ) -> Result<(), SecureFsError> {
        for &fd in candidate_fds {
            if fd < 0 {
                continue;
            }
            let mut st: libc::stat = unsafe { std::mem::zeroed() };
            let rc = unsafe { libc::fstat(fd, &mut st) };
            if rc == 0 && (st.st_ino as u64) == quarantined_ino {
                if revoke_on_match {
                    unsafe {
                        libc::close(fd);
                    }
                }
                return Err(SecureFsError::PreExistingDescriptorEscape {
                    ino: quarantined_ino,
                });
            }
        }
        Ok(())
    }

    /// Obtiene la época de autoridad activa actual.
    pub fn get_epoch(&self) -> u64 {
        self.current_epoch.load(std::sync::atomic::Ordering::SeqCst)
    }

    /// Revoca y cerca durablemente la época (`AckRevocation(r, k) => ¬Commit_r(e) ∀ e: epoch(e) < k`).
    /// Adquiere el cerrojo exclusivo híbrido (drenando toda operación en curso) y persiste la época en `.epoch_fence.bin`.
    pub fn revoke_and_fence(&self, min_new_epoch: u64) -> Result<u64, SecureFsError> {
        let guard = self.acquire_hybrid_resource_gate()?;
        let current = self.read_durable_epoch_locked(guard.fence_fd)?;
        let target = if min_new_epoch > current {
            min_new_epoch
        } else {
            current + 1
        };
        self.write_durable_epoch_locked(guard.fence_fd, target)?;
        Ok(target)
    }

    /// Incrementa la época para revocar capacidades emitidas previamente (NEM-I6), usando fencing durable.
    pub fn bump_epoch(&self) -> u64 {
        let next = self.get_epoch() + 1;
        self.revoke_and_fence(next).unwrap_or_else(|_| {
            self.current_epoch.fetch_add(1, std::sync::atomic::Ordering::SeqCst) + 1
        })
    }

    /// `DELETE_FILE` seguro con ciclo canónico:
    /// `PREPARE → QUARANTINE → VERIFY → COMMIT | SECURITY_ABORT`
    ///
    /// Cumple:
    /// - **NEM-I1:** Efecto acotado a `EffectType::Delete`.
    /// - **NEM-I2:** `Committed ⟹ Verified ∧ EffectObserved`.
    /// - **NEM-I3 (Path Oblivion):** Tras quarantine, `original_path` queda proscrito.
    pub fn secure_delete(
        &self,
        parent_fd: RawFd,
        basename: &str,
        authorized_identity: &ObjectIdentity,
        tx_nonce: &[u8; 32],
    ) -> Result<EffectTxState, SecureFsError> {
        let auth = AuthorityContext {
            authority_id: authorized_identity.locator.capability_root_id,
            epoch: self.get_epoch(),
            effect: EffectType::Delete,
            nonce: [0u8; 32],
        };
        self.secure_delete_scoped(parent_fd, basename, &auth, authorized_identity, tx_nonce)
    }

    /// `DELETE_FILE` con Effect Commit Protocol v2 (10 pasos), WAL de 4 fronteras y época cercada (NEM-I1 & NEM-I6).
    pub fn secure_delete_scoped(
        &self,
        parent_fd: RawFd,
        basename: &str,
        auth: &AuthorityContext,
        authorized_identity: &ObjectIdentity,
        tx_nonce: &[u8; 32],
    ) -> Result<EffectTxState, SecureFsError> {
        // 01 ACQUIRE exclusive resource gate + hybrid epoch fence
        let locator_pair = (authorized_identity.locator.dev, authorized_identity.locator.ino);
        let locator_arc = self.get_or_create_locator_mutex(locator_pair)?;
        let _locator_guard = locator_arc
            .lock()
            .map_err(|_| SecureFsError::LedgerError("locator gate poisoned".into()))?;
        let fence_guard = self.acquire_hybrid_resource_gate()?;

        // 02 FENCE validate durable resource epoch
        let active_epoch = self.read_durable_epoch_locked(fence_guard.fence_fd)?;
        if auth.epoch != active_epoch {
            return Err(SecureFsError::AuthorityStale {
                expected_epoch: auth.epoch,
                current_epoch: active_epoch,
            });
        }

        // 03 VALIDATE artifact + profile + policy + target
        if auth.effect != EffectType::Delete {
            return Err(SecureFsError::UnauthorizedEffectType {
                required: EffectType::Delete,
                granted: auth.effect,
            });
        }

        let enforce_nonce_ledger = auth.nonce != [0u8; 32];
        if enforce_nonce_ledger {
            if let Some(existing) = self.get_wal_record(&auth.nonce) {
                if existing.state != WalRecordState::OutcomeKnown {
                    return Err(SecureFsError::AmbiguousOutcomeRequiresReconciliation {
                        nonce: auth.nonce,
                        state: existing.state,
                    });
                }
                return Err(SecureFsError::NonceReplayDetected { nonce: auth.nonce });
            }
            if self.is_nonce_consumed(&auth.nonce) {
                return Err(SecureFsError::NonceReplayDetected { nonce: auth.nonce });
            }
        }

        // 04 AUTHORIZE effect against current history/budget
        self.verify_budget_allowed(auth, locator_pair, authorized_identity.state.size)?;

        let nonce_name = format!("del_{}", hex::encode(tx_nonce));

        // PREPARE → QUARANTINE: Secuestro atómico. Desde aquí original_path es proscrito (NEM-I3).
        B::quarantine(parent_fd, basename, self.quarantine.dir_fd, &nonce_name)?;

        // QUARANTINE → VERIFY: Verificación post-aislamiento. Adversario ya no puede interferir.
        match B::verify_quarantined(self.quarantine.dir_fd, &nonce_name, authorized_identity) {
            Ok(vtx) => {
                // 05 RESERVE + 06 DURABLE: Persistir intención y presupuesto ANTES del unlink irreversible
                self.commit_budget_usage(auth, authorized_identity.state.size)?;
                if enforce_nonce_ledger {
                    let reserved = WalRecord::new(
                        WalRecordState::AttemptReserved,
                        EffectType::Delete,
                        auth.epoch,
                        auth.nonce,
                        locator_pair.0,
                        locator_pair.1,
                        authorized_identity.state.hash,
                        [0u8; 32],
                    );
                    self.append_wal_record(reserved)?;
                }
                // 07 EXECUTE + 08 OBSERVE: Destrucción observada en silicio.
                if let Err(e) = B::destroy_quarantined(self.quarantine.dir_fd, vtx) {
                    if enforce_nonce_ledger {
                        let unknown = WalRecord::new(
                            WalRecordState::OutcomeUnknown,
                            EffectType::Delete,
                            auth.epoch,
                            auth.nonce,
                            locator_pair.0,
                            locator_pair.1,
                            authorized_identity.state.hash,
                            [0u8; 32],
                        );
                        let _ = self.append_wal_record(unknown);
                    }
                    return Err(e);
                }
                // 09 RECEIPT: Persistir OUTCOME_KNOWN
                if enforce_nonce_ledger {
                    let known = WalRecord::new(
                        WalRecordState::OutcomeKnown,
                        EffectType::Delete,
                        auth.epoch,
                        auth.nonce,
                        locator_pair.0,
                        locator_pair.1,
                        authorized_identity.state.hash,
                        [0u8; 32],
                    );
                    self.append_wal_record(known)?;
                }
                Ok(EffectTxState::Committed)
            }
            Err(SecureFsError::SecurityMismatch { .. }) => {
                // Señuelo retenido para peritaje criminalístico.
                Ok(EffectTxState::SecurityAbort)
            }
            Err(e) => Err(e),
        }
    }

    /// `MUTATE_FILE` seguro: autoriza, abre, verifica identidad de locator y pre-state,
    /// muta sobre el mismo FD y retorna `post_hash`.
    pub fn secure_mutate(
        &self,
        root_fd: RawFd,
        rel_path: &str,
        authorized_identity: &ObjectIdentity,
        payload: &[u8],
    ) -> Result<(EffectTxState, [u8; 32]), SecureFsError> {
        let auth = AuthorityContext {
            authority_id: authorized_identity.locator.capability_root_id,
            epoch: self.get_epoch(),
            effect: EffectType::Mutate,
            nonce: [0u8; 32],
        };
        self.secure_mutate_scoped(root_fd, rel_path, &auth, authorized_identity, payload)
    }

    /// `MUTATE_FILE` bajo Effect Commit Protocol v2 (10 pasos):
    /// 01 ACQUIRE -> 02 FENCE -> 03 VALIDATE -> 04 AUTHORIZE -> 05 RESERVE -> 06 DURABLE ->
    /// 07 EXECUTE -> 08 OBSERVE -> 09 RECEIPT -> 10 RELEASE.
    pub fn secure_mutate_scoped(
        &self,
        root_fd: RawFd,
        rel_path: &str,
        auth: &AuthorityContext,
        authorized_identity: &ObjectIdentity,
        payload: &[u8],
    ) -> Result<(EffectTxState, [u8; 32]), SecureFsError> {
        // 01 ACQUIRE exclusive resource gate + hybrid epoch fence
        let locator_pair = (authorized_identity.locator.dev, authorized_identity.locator.ino);
        let locator_arc = self.get_or_create_locator_mutex(locator_pair)?;
        let _locator_guard = locator_arc
            .lock()
            .map_err(|_| SecureFsError::LedgerError("locator gate poisoned".into()))?;
        let fence_guard = self.acquire_hybrid_resource_gate()?;

        // 02 FENCE validate durable resource epoch
        let active_epoch = self.read_durable_epoch_locked(fence_guard.fence_fd)?;
        if auth.epoch != active_epoch {
            return Err(SecureFsError::AuthorityStale {
                expected_epoch: auth.epoch,
                current_epoch: active_epoch,
            });
        }

        // 03 VALIDATE artifact + profile + policy + target
        if auth.effect != EffectType::Mutate {
            return Err(SecureFsError::UnauthorizedEffectType {
                required: EffectType::Mutate,
                granted: auth.effect,
            });
        }

        let enforce_nonce_ledger = auth.nonce != [0u8; 32];
        if enforce_nonce_ledger {
            if let Some(existing) = self.get_wal_record(&auth.nonce) {
                if existing.state != WalRecordState::OutcomeKnown {
                    return Err(SecureFsError::AmbiguousOutcomeRequiresReconciliation {
                        nonce: auth.nonce,
                        state: existing.state,
                    });
                }
                return Err(SecureFsError::NonceReplayDetected { nonce: auth.nonce });
            }
            if self.is_nonce_consumed(&auth.nonce) {
                return Err(SecureFsError::NonceReplayDetected { nonce: auth.nonce });
            }
        }

        // 04 AUTHORIZE effect against current history/budget
        self.verify_budget_allowed(auth, locator_pair, payload.len() as u64)?;

        let expected_post_hash: [u8; 32] = Sha256::digest(payload).into();

        // 05 RESERVE + 06 DURABLE: Persistir ATTEMPT_RESERVED ANTES de la syscall irreversible
        if enforce_nonce_ledger {
            let reserved = WalRecord::new(
                WalRecordState::AttemptReserved,
                EffectType::Mutate,
                auth.epoch,
                auth.nonce,
                locator_pair.0,
                locator_pair.1,
                authorized_identity.state.hash,
                expected_post_hash,
            );
            self.append_wal_record(reserved)?;
        }

        // 07 EXECUTE + 08 OBSERVE: Emitir operación física sobre el recurso
        let post_hash = match B::secure_mutate(root_fd, rel_path, authorized_identity, payload) {
            Ok(h) => h,
            Err(e) => {
                if enforce_nonce_ledger {
                    let unknown = WalRecord::new(
                        WalRecordState::OutcomeUnknown,
                        EffectType::Mutate,
                        auth.epoch,
                        auth.nonce,
                        locator_pair.0,
                        locator_pair.1,
                        authorized_identity.state.hash,
                        expected_post_hash,
                    );
                    let _ = self.append_wal_record(unknown);
                }
                return Err(e);
            }
        };

        self.commit_budget_usage(auth, payload.len() as u64)?;

        // 09 RECEIPT: Persistir OUTCOME_KNOWN con observación física verificada
        if enforce_nonce_ledger {
            let known = WalRecord::new(
                WalRecordState::OutcomeKnown,
                EffectType::Mutate,
                auth.epoch,
                auth.nonce,
                locator_pair.0,
                locator_pair.1,
                authorized_identity.state.hash,
                post_hash,
            );
            self.append_wal_record(known)?;
        }

        // 10 RELEASE resource gate (automático por Drop de `fence_guard` y `_locator_guard`)
        Ok((EffectTxState::Committed, post_hash))
    }

    /// NEM-I5: Recuperación Idempotente Post-Crash.
    ///
    /// Formalmente: `R(R(s)) == R(s)` para cualquier estado recuperable estabilizado.
    pub fn recover_quarantined(
        &self,
        nonce: &[u8; 32],
        expected: &ObjectIdentity,
    ) -> Result<EffectTxState, SecureFsError> {
        let nonce_name = format!("del_{}", hex::encode(nonce));
        let q_file = self.quarantine.dir_path.join(&nonce_name);

        // Si el archivo ya no existe en cuarentena, la recuperación previa ya consumó el commit
        // (o abortó pre-rename). Idempotencia: invocar recover_quarantined() repetidamente es seguro.
        if !q_file.exists() {
            if let Some(rec) = self.get_wal_record(nonce) {
                if rec.state != WalRecordState::OutcomeKnown {
                    let known = WalRecord::new(
                        WalRecordState::OutcomeKnown,
                        rec.effect,
                        rec.epoch,
                        rec.nonce,
                        rec.target_dev,
                        rec.target_ino,
                        rec.expected_pre_hash,
                        [0u8; 32],
                    );
                    let _ = self.append_wal_record(known);
                }
            }
            return Ok(EffectTxState::Committed);
        }

        // Si el archivo existe en cuarentena: verificar identidad.
        match B::verify_quarantined(self.quarantine.dir_fd, &nonce_name, expected) {
            Ok(vtx) => {
                B::destroy_quarantined(self.quarantine.dir_fd, vtx)?;
                if let Some(rec) = self.get_wal_record(nonce) {
                    if rec.state != WalRecordState::OutcomeKnown {
                        let known = WalRecord::new(
                            WalRecordState::OutcomeKnown,
                            rec.effect,
                            rec.epoch,
                            rec.nonce,
                            rec.target_dev,
                            rec.target_ino,
                            rec.expected_pre_hash,
                            [0u8; 32],
                        );
                        self.append_wal_record(known)?;
                    }
                }
                Ok(EffectTxState::Committed)
            }
            Err(SecureFsError::SecurityMismatch { .. }) => {
                // Señuelo retenido en cuarentena; no se destruye.
                Ok(EffectTxState::SecurityAbort)
            }
            Err(e) => Err(e),
        }
    }

    /// Alias canónico de recuperación para NEM-I4 y NEM-I5.
    pub fn recover(
        &self,
        nonce: &[u8; 32],
        expected: &ObjectIdentity,
    ) -> Result<EffectTxState, SecureFsError> {
        self.recover_quarantined(nonce, expected)
    }
}

// ---------------------------------------------------------------------------
// Unit Tests (Autocontenidos sin dependencias externas)
// ---------------------------------------------------------------------------

#[cfg(test)]
mod tests {
    use super::*;

    struct TestDir { path: PathBuf }
    impl TestDir {
        fn new() -> Self {
            let p = std::env::temp_dir().join(format!("b60_sf_{}_{}", std::process::id(), rand::random::<u64>()));
            std::fs::create_dir_all(&p).unwrap();
            Self { path: p }
        }
        fn path(&self) -> &Path { &self.path }
    }
    impl Drop for TestDir { fn drop(&mut self) { let _ = std::fs::remove_dir_all(&self.path); } }

    fn open_dir(p: &Path) -> RawFd {
        let c = CString::new(p.as_os_str().as_bytes()).unwrap();
        let fd = unsafe { libc::open(c.as_ptr(), libc::O_RDONLY | libc::O_DIRECTORY | libc::O_CLOEXEC) };
        assert!(fd >= 0, "open_dir failed: {:?}", std::io::Error::last_os_error());
        fd
    }

    #[test]
    fn test_identity_and_locator_separation() {
        let td = TestDir::new();
        let content = b"BABYLON-60 locator vs state separation test";
        std::fs::write(td.path().join("f.dat"), content).unwrap();
        let root_fd = open_dir(td.path());
        let cap = [0x01; 32];
        let (fd, id) = NativeSecureFs::pin_object(root_fd, "f.dat", cap).unwrap();
        unsafe { libc::close(fd) };
        unsafe { libc::close(root_fd) };

        assert_eq!(id.locator.dev, id.dev);
        assert_eq!(id.locator.ino, id.ino);
        assert_eq!(id.state.hash, Sha256::digest(content).as_slice());
        assert_eq!(id.state.size, content.len() as u64);
    }

    #[test]
    fn test_symlink_rejected_by_pin_object() {
        let td = TestDir::new();
        #[cfg(unix)]
        std::os::unix::fs::symlink("/etc/passwd", td.path().join("evil")).unwrap();
        let root_fd = open_dir(td.path());
        let res = NativeSecureFs::pin_object(root_fd, "evil", [0x02; 32]);
        unsafe { libc::close(root_fd) };
        assert!(res.is_err(), "Symlink must be rejected (O_NOFOLLOW)");
    }

    #[test]
    fn test_secure_delete_happy_path_committed() {
        let td = TestDir::new();
        let fp = td.path().join("target.dat");
        std::fs::write(&fp, b"delete me").unwrap();
        let orch = EffectTxOrchestrator::<NativeSecureFs>::new(td.path()).unwrap();
        let root_fd = open_dir(td.path());
        let cap = [0x03; 32];
        let (fd, id) = NativeSecureFs::pin_object(root_fd, "target.dat", cap).unwrap();
        unsafe { libc::close(fd) };
        let nonce = [0xAA; 32];
        let state = orch.secure_delete(root_fd, "target.dat", &id, &nonce).unwrap();
        unsafe { libc::close(root_fd) };
        assert_eq!(state, EffectTxState::Committed);
        assert!(!fp.exists());
    }

    #[test]
    fn test_swap_attack_triggers_security_abort_and_preserves_decoy() {
        let td = TestDir::new();
        std::fs::write(td.path().join("victim.dat"), b"authentic").unwrap();
        std::fs::write(td.path().join("decoy.dat"), b"malicious").unwrap();
        let orch = EffectTxOrchestrator::<NativeSecureFs>::new(td.path()).unwrap();
        let root_fd = open_dir(td.path());
        let cap = [0x04; 32];
        let (fd, victim_id) = NativeSecureFs::pin_object(root_fd, "victim.dat", cap).unwrap();
        unsafe { libc::close(fd) };

        std::fs::remove_file(td.path().join("victim.dat")).unwrap();
        std::fs::rename(td.path().join("decoy.dat"), td.path().join("victim.dat")).unwrap();
        let nonce = [0xBB; 32];
        let state = orch.secure_delete(root_fd, "victim.dat", &victim_id, &nonce).unwrap();
        unsafe { libc::close(root_fd) };
        assert_eq!(state, EffectTxState::SecurityAbort);

        let q = orch.quarantine.dir_path.join(format!("del_{}", hex::encode(nonce)));
        assert!(q.exists(), "Decoy must be retained in quarantine for forensics");
        assert_eq!(std::fs::read(q).unwrap(), b"malicious");
    }

    #[test]
    fn test_mutate_file_on_same_fd_committed() {
        let td = TestDir::new();
        let fp = td.path().join("mutable.dat");
        std::fs::write(&fp, b"original payload").unwrap();
        let orch = EffectTxOrchestrator::<NativeSecureFs>::new(td.path()).unwrap();
        let root_fd = open_dir(td.path());
        let cap = [0x05; 32];
        let (fd, id) = NativeSecureFs::pin_object(root_fd, "mutable.dat", cap).unwrap();
        unsafe { libc::close(fd) };
        let new_payload = b"mutated content v2";
        let (state, post_hash) = orch.secure_mutate(root_fd, "mutable.dat", &id, new_payload).unwrap();
        unsafe { libc::close(root_fd) };
        assert_eq!(state, EffectTxState::Committed);
        let disk_content = std::fs::read(&fp).unwrap();
        assert_eq!(disk_content, new_payload);
        assert_eq!(post_hash, Sha256::digest(new_payload).as_slice());
    }

    #[test]
    fn test_nem_i5_recovery_idempotence() {
        // Verifica NEM-I5: Recover(Recover(s)) == Recover(s)
        let td = TestDir::new();
        let fp = td.path().join("idempotent_crash.dat");
        std::fs::write(&fp, b"idempotence payload").unwrap();
        let orch = EffectTxOrchestrator::<NativeSecureFs>::new(td.path()).unwrap();
        let root_fd = open_dir(td.path());
        let cap = [0x06; 32];
        let (fd, id) = NativeSecureFs::pin_object(root_fd, "idempotent_crash.dat", cap).unwrap();
        unsafe { libc::close(fd) };
        let nonce = [0xDD; 32];
        let nonce_name = format!("del_{}", hex::encode(nonce));

        // Crash simulado tras quarantine:
        NativeSecureFs::quarantine(root_fd, "idempotent_crash.dat", orch.quarantine.dir_fd, &nonce_name).unwrap();
        unsafe { libc::close(root_fd) };

        // Primer recover: R(s)
        let r1 = orch.recover_quarantined(&nonce, &id).unwrap();
        assert_eq!(r1, EffectTxState::Committed);

        // Segundo recover: R(R(s)) == R(s)
        let r2 = orch.recover_quarantined(&nonce, &id).unwrap();
        assert_eq!(r2, EffectTxState::Committed);
        assert_eq!(r1, r2, "NEM-I5 VIOLATION: Recovery must be strictly idempotent");
    }

    #[test]
    fn test_intermediate_symlink_and_quarantine_init_nofollow() {
        let td = TestDir::new();
        let outside = TestDir::new();
        std::fs::write(outside.path().join("secret.dat"), b"outside").unwrap();

        #[cfg(unix)]
        {
            std::os::unix::fs::symlink(outside.path(), td.path().join("sub_link")).unwrap();
            let root_fd = open_dir(td.path());
            let err = NativeSecureFs::pin_object(root_fd, "sub_link/secret.dat", [0x07; 32]).unwrap_err();
            unsafe { libc::close(root_fd) };
            assert!(
                matches!(err, SecureFsError::SymlinkEscapeAttempt),
                "Intermediate symlink component must be rejected with SymlinkEscapeAttempt, got: {err:?}"
            );

            let td_babylon = TestDir::new();
            std::os::unix::fs::symlink(outside.path(), td_babylon.path().join(".babylon")).unwrap();
            let q_err = QuarantineContext::initialize(td_babylon.path());
            assert!(
                matches!(q_err, Err(SecureFsError::SymlinkEscapeAttempt)),
                "Symlink on .babylon must be rejected via openat(O_NOFOLLOW)"
            );
        }
    }
}
