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

// Included by the standalone kernel too; no second protocol implementation.
include!("shared_manifest_core.rs");

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

#[cfg(test)]
mod tests {
    use super::SharedManifest;
    use core::mem::{align_of, offset_of, size_of};

    /// Runtime mirror of `_LAYOUT_ASSERTS` plus field offsets from the C-ABI table.
    #[test]
    fn layout_is_64_bytes_aligned_with_documented_offsets() {
        assert_eq!(size_of::<SharedManifest>(), 64);
        assert_eq!(align_of::<SharedManifest>(), 64);
        assert_eq!(offset_of!(SharedManifest, status_flag), 0x00);
        assert_eq!(offset_of!(SharedManifest, seq), 0x04);
        assert_eq!(offset_of!(SharedManifest, epoch_id), 0x08);
        assert_eq!(offset_of!(SharedManifest, payload_hash), 0x10);
        assert_eq!(offset_of!(SharedManifest, _padding), 0x30);
    }
}
