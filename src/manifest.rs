// C5-REAL EXERGY CERTIFIED — BABYLON-60 — INV-1 (layout)
// SharedManifest: 64 B, align(64), C-ABI, AArch64/ARMv9
//
// NOTA DE DISEÑO — Zero-Split Coherence:
//   Con align(64)==size(64) y línea física de 64 B, ninguna instancia
//   cruza frontera de línea de caché en arquitecturas con CWG=64 B.
//   En Apple M1 Ultra (CWG=128 B del SoC, línea de núcleo 64 B per CTR_EL0),
//   dos manifiestos contiguos de 64 B pueden compartir línea de coherencia
//   de SoC → false sharing. Para portabilidad total usar align(128).
//   Ref: Fürst et al., «Analyzing the memory ordering models of the Apple M1»,
//   J. of Systems Architecture.
//
// NOTA DE DISEÑO — payload_hash como [AtomicU64; 4]:
//   Misma ABI que [u8;32] (32 B, align 8), pero evita UB por data race
//   (lectura no-atómica concurrente con store = data race en C11/Rust).
//   Las cargas Relaxed encajan correctamente en el protocolo seqlock.

use core::mem::{align_of, size_of};
use core::mem::offset_of;
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
    /// 0x00 — estado operativo: `RUNNING` o `POISONED`.
    pub status_flag: AtomicU32,
    /// 0x04 — contador de secuencia seqlock.
    /// Par → publicación válida (Entelecheia).
    /// Impar → escritura en curso (Dynamis), lectores rechazan.
    pub seq: AtomicU32,
    /// 0x08 — época monótona. Imposibilita ABA: 2⁶⁴ ÷ 10⁹ ≈ 584 años.
    pub epoch_id: AtomicU64,
    /// 0x10..0x30 — SHAKE256/256 del estado del ledger, como 4×u64 atómicos.
    /// Misma ABI que `[u8; 32]`. Evita data race en lecturas Relaxed del seqlock.
    pub payload_hash: [AtomicU64; 4],
    /// 0x30..0x40 — relleno para completar hasta 64 B.
    pub _padding: [u8; 16],
}

impl SharedManifest {
    /// Crea una nueva instancia de `SharedManifest` inicializada con estado `RUNNING` (const fn).
    ///
    /// ## Ejemplo
    /// ```rust
    /// use babylon_60::manifest::SharedManifest;
    /// static MANIFEST: SharedManifest = SharedManifest::new();
    /// ```
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
            _padding: [0u8; 16],
        }
    }

    /// Alias de `new()` para inicialización constante en `static`.
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
        let status = self.status_flag.load(core::sync::atomic::Ordering::Relaxed);
        let seq = self.seq.load(core::sync::atomic::Ordering::Relaxed);
        let epoch = self.epoch_id.load(core::sync::atomic::Ordering::Relaxed);
        let h0 = self.payload_hash[0].load(core::sync::atomic::Ordering::Relaxed);
        let h1 = self.payload_hash[1].load(core::sync::atomic::Ordering::Relaxed);
        let h2 = self.payload_hash[2].load(core::sync::atomic::Ordering::Relaxed);
        let h3 = self.payload_hash[3].load(core::sync::atomic::Ordering::Relaxed);
        f.debug_struct("SharedManifest")
            .field("status_flag", &format_args!("{:#010X}", status))
            .field("seq", &seq)
            .field("epoch_id", &epoch)
            .field("payload_hash", &[h0, h1, h2, h3])
            .finish()
    }
}

// ---------------------------------------------------------------------------
// INV-1: verificación estática del layout (tiempo de compilación)
// ---------------------------------------------------------------------------
const _LAYOUT_ASSERTS: () = {
    assert!(size_of::<SharedManifest>() == 64,    "SharedManifest debe ser exactamente 64 B");
    assert!(align_of::<SharedManifest>() == 64,   "SharedManifest debe alinearse a 64 B");
    assert!(offset_of!(SharedManifest, status_flag)  == 0x00);
    assert!(offset_of!(SharedManifest, seq)          == 0x04);
    assert!(offset_of!(SharedManifest, epoch_id)     == 0x08);
    assert!(offset_of!(SharedManifest, payload_hash) == 0x10);
    assert!(offset_of!(SharedManifest, _padding)     == 0x30);
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
