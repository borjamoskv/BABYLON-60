// Certified Specification — BABYLON-60 — INV-1 (layout)
// SharedManifest: 64 B, align(64), C-ABI, AArch64/ARMv9
//
// NOTA DE DISEÑO — Zero-Split Coherence:
//   Con align(64)==size(64) y línea física de 64 B, ninguna instancia
//   cruza frontera de línea de caché en arquitecturas con CWG=64 B.
//   En Apple M1 Ultra (CWG=128 B del SoC, línea de núcleo 64 B per CTR_EL0),
//   dos manifiestos contiguos de 64 B pueden compartir línea de coherencia
//   de SoC → false sharing. Para portabilidad total usar align(64).
//   Ref: Fürst et al., «Analyzing the memory ordering models of the Apple M1»,
//   J. of Systems Architecture.
//
// NOTA DE DISEÑO — payload_hash como [AtomicU64; 4]:
//   Misma ABI que [u8;32] (32 B, align 8), pero evita UB por data race
//   (lectura no-atómica concurrente con store = data race en C11/Rust).
//   Las cargas Relaxed encajan correctamente en el protocolo seqlock.

use core::mem::{align_of, size_of};
use core::sync::atomic::{AtomicU32, AtomicU64};

// ---------------------------------------------------------------------------
// Constantes de estado del status_flag
// ---------------------------------------------------------------------------

/// Estado operativo normal del sistema.
pub const RUNNING: u32 = 0x0000_0001;

/// Estado envenenado (fail-stop). Una vez almacenado, ninguna transición
/// puede devolverlo a `RUNNING` en el mismo proceso.
/// Valor mnemónico: 0xDEAD_6060 (BABYLON-60 halt marker).
pub const POISONED: u32 = 0xDEAD_6060;

/// Alias canónico de envenenamiento por confabulación estocástica (H_sem > tau, UNSAT).
pub const POISONED_CONFABULATION: u32 = 0xDEAD_6060;

/// Estado envenenado por creencia errónea sistemática memorizada (H_sem <= tau, UNSAT).
/// Interceptado deterministamente por el Firewall Neurosimbólico Z3 SMT en Ring-0.
pub const POISONED_INCORRECT_BELIEF: u32 = 0xDEAD_6061;

// ---------------------------------------------------------------------------
// Umbral de reintentos del lector
// ---------------------------------------------------------------------------

/// Número máximo de reintentos del lector antes de disparar `epistemic_halt`.
/// Con frecuencias de publicación reales del escritor, 16 reintentos equivalen
/// a O(microsegundo) en spin antes de escalar al mecanismo de halt.
pub const MAX_RETRIES: usize = 10_000;

// ---------------------------------------------------------------------------
// INV-1: SharedManifest — C-ABI layout, 64 B, align(64)
// ---------------------------------------------------------------------------

/// Slot IPC lock-free residente en `mmap`/`static`.
///
/// ## Layout C-ABI (repr C + align 64)
/// ```text
/// Offset  Size  Field
/// 0x00    4     status_flag  (AtomicU32)
/// 0x04    4     seq          (AtomicU32) — contador de secuencia seqlock
/// 0x08    8     epoch_id     (AtomicU64) — contador monótono, ABA-imposible
/// 0x10   32     payload_hash ([AtomicU64; 4]) — hash SHAKE256/256 del estado
/// 0x30   16     _padding     ([u8; 16])  — completa hasta 64 B
/// ```
///
/// ## SPMC — Single Producer Multiple Consumer
/// Un único escritor (producer) llama a [`publish`](crate::seqlock::publish).
/// Múltiples lectores (consumers) llaman a [`read`](crate::seqlock::read).
///
/// ## Prohibición de Arc en ruta caliente
/// El refcount de `Arc` reintroduce el RMW contencioso eliminado por el
/// diseño seqlock. Usar `mmap`, `Box::leak`, o pool estático.
#[repr(C, align(64))]
pub struct SharedManifest {
    /// Flag de estado del manifiesto compartido.
    pub status_flag: AtomicU32,
    /// Número de secuencia para sincronización seqlock.
    pub seq: AtomicU32,
    /// Identificador de época (epoch).
    pub epoch_id: AtomicU64,
    /// Hash del payload compuesto por 4 palabras de 64 bits.
    pub payload_hash: [AtomicU64; 4],
    /// Padding para alineamiento de línea de caché (64 bytes).
    pub _padding: [u8; 16],
}

impl SharedManifest {
    /// Crea una nueva instancia de `SharedManifest` inicializada.
    #[must_use]
    pub const fn new() -> Self {
        Self {
            status_flag: AtomicU32::new(RUNNING),
            seq: AtomicU32::new(0),
            epoch_id: AtomicU64::new(0),
            payload_hash: [
                AtomicU64::new(0),
                AtomicU64::new(0),
                AtomicU64::new(0),
                AtomicU64::new(0),
            ],
            _padding: [0; 16],
        }
    }

    /// Crea una instancia de `SharedManifest` con todos los campos en cero.
    #[must_use]
    pub const fn zeroed() -> Self {
        Self::new()
    }
}

impl Default for SharedManifest {
    fn default() -> Self {
        Self::new()
    }
}

impl core::fmt::Debug for SharedManifest {
    fn fmt(&self, f: &mut core::fmt::Formatter<'_>) -> core::fmt::Result {
        f.debug_struct("SharedManifest")
            .field("status_flag", &self.status_flag)
            .field("seq", &self.seq)
            .field("epoch_id", &self.epoch_id)
            .finish()
    }
}

const _LAYOUT_ASSERTS: () = {
    assert!(size_of::<SharedManifest>() == 64, "SharedManifest debe ser exactamente 64 B");
    assert!(align_of::<SharedManifest>() == 64, "SharedManifest debe alinearse a 64 B");
};

// ---------------------------------------------------------------------------
// Variantes de motivo de halt (compartidas por halt.rs y receipt.rs)
// ---------------------------------------------------------------------------

/// Motivo del halt epistémico. Valor contenido en el recibo COSE_Sign1.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
#[non_exhaustive]
pub enum HaltReason {
    /// El lector agotó `MAX_RETRIES` sin obtener una lectura consistente.
    SeqRetryExhausted,
    /// El hash recibido no verifica contra la cadena de atestación.
    HashMismatch,
    /// `epoch_id` no es estrictamente monótono — violación del invariante.
    EpochNonMonotonic,
    /// `status_flag` ya contenía `POISONED` al iniciarse una operación.
    AlreadyPoisoned,
    /// Señal externa de interrupción (Art. 14(4) EU AI Act — botón de parada).
    ExternalSignal,
    /// Confabulación estocástica detectada por alta entropía semántica (H_sem > tau, UNSAT).
    Confabulation,
    /// Creencia errónea sistemática interceptada por el oráculo SMT (H_sem <= tau, UNSAT).
    IncorrectBelief,
}

impl HaltReason {
    /// Representación textual para el campo `motivo` del recibo COSE_Sign1.
    #[must_use]
    pub fn as_str(self) -> &'static str {
        match self {
            HaltReason::SeqRetryExhausted  => "SEQ_RETRY_EXHAUSTED",
            HaltReason::HashMismatch        => "HASH_MISMATCH",
            HaltReason::EpochNonMonotonic   => "EPOCH_NON_MONOTONIC",
            HaltReason::AlreadyPoisoned     => "ALREADY_POISONED",
            HaltReason::ExternalSignal      => "EXTERNAL_SIGNAL",
            HaltReason::Confabulation       => "CONFABULATION",
            HaltReason::IncorrectBelief     => "INCORRECT_BELIEF",
        }
    }
}

impl core::fmt::Display for HaltReason {
    fn fmt(&self, f: &mut core::fmt::Formatter<'_>) -> core::fmt::Result {
        f.write_str(self.as_str())
    }
}

#[cfg(feature = "std")]
impl std::error::Error for HaltReason {}
