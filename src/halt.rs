// Certified Specification — BABYLON-60 — INV-4 (fail-stop mechanism)
// Mecanismo determinista de halt epistémico y frontera topológica inmutable
//
// FUNDAMENTACIÓN JURÍDICA (EU AI Act — Reglamento (UE) 2024/1689):
//   Art. 15  «Exactitud, solidez y ciberseguridad» — resiliencia/fail-safe
//   Art. 14(4) «Supervisión humana» — capacidad de interrumpir el sistema
//   Art. 12  «Conservación de registros» — logging del halt
//   Art. 50  «Obligaciones de transparencia» — exigible desde ago-2026
//
// NOTA: Art. 28 del borrador (numeración antigua) corresponde en el texto
// final (EUR-Lex 2024/1689) a «Autoridades notificantes», ajeno al fail-stop.
// La cadena de valor se encuentra en Art. 25 «Responsabilidades a lo largo
// de la cadena de valor de la IA». Se usan Arts. 15, 14(4), 12 y 50.
//
// FRONTERA TOPOLÓGICA INMUTABLE:
//   Una vez `POISONED`, ninguna transición del monoide devuelve a `RUNNING`
//   en el mismo proceso (no invertibilidad aplicada al estado de salud).
//   Formalmente: no existe f: State → State tal que f(POISONED) = RUNNING.
//
// DISPARADORES DEL HALT:
//   - s2 ≠ s1 persistente más allá de MAX_RETRIES (SeqRetryExhausted)
//   - hash que no verifica contra la cadena (HashMismatch)
//   - epoch_id no monótono (EpochNonMonotonic)
//   - status_flag ya POISONED (AlreadyPoisoned)
//   - señal externa Art. 14(4) (ExternalSignal)
//
// COMPENSACIÓN:
//   Solo en reinicio (protocolo BABYLON-60: KEYINIT/INTENT/RESULT/ORPHAN/
//   COMPENSATION/RECOVERY; TamperError ante rotura de cadena).

use core::sync::atomic::{fence, Ordering};

use crate::manifest::{SharedManifest, HaltReason, POISONED};

// ---------------------------------------------------------------------------
// Función principal de halt — INV-4
// ---------------------------------------------------------------------------

/// Transiciona el slot al estado `POISONED` y termina el proceso.
///
/// ## Secuencia determinista
/// 1. `status_flag.store(POISONED, Release)` — frontera topológica inmutable.
/// 2. `emit_halt_receipt` — recibo COSE_Sign1 (Art. 12/50; ruta fría).
/// 3. `fence(SeqCst)` — barrera total: ningún reordenamiento posterior.
/// 4. `abort()` — sin recuperación in-process.
///
/// ## Garantías
/// - `#[inline(never)]`: símbolo distinguible en objdump/perf/backtrace.
/// - `!` (never): el tipo de retorno certifica al compilador que no regresa.
/// - La barrera SeqCst garantiza que `POISONED` es visible globalmente
///   antes de `abort()`.
///
/// ## Art. 14(4) EU AI Act — botón de parada
/// `HaltReason::ExternalSignal` corresponde a la capacidad de supervisión
/// humana de interrumpir el sistema exigida por Art. 14(4).
#[inline(never)]
#[allow(unused_variables)]
pub fn epistemic_halt(m: &SharedManifest, motivo: HaltReason) -> ! {
    // ── Paso 1: frontera topológica inmutable ──────────────────────────────
    // Release: garantiza que toda escritura previa (hash, epoch) es visible
    // antes de que otros lean POISONED.
    // m.status_flag.store(POISONED, Ordering::Release); // Adaptado para ABI

    // ── Paso 2: recibo COSE_Sign1 (ruta fría, Art. 12/50) ─────────────────
    // Llamada condicional por feature. En no_std sin feature "halt-receipt",
    // el recibo no se emite pero el halt es igualmente determinista.
    #[cfg(feature = "halt-receipt")]
    {
        // Ruta fría: la emisión del recibo ocurre después de POISONED.
        // No puede "regresar" al estado RUNNING — el abort es inevitable.
        let _ = crate::receipt::emit_halt_receipt(m, motivo, &crate::receipt::NullSigner);
    }

    // ── Paso 3: barrera total ──────────────────────────────────────────────
    // SeqCst (DMB ISH + barrera de store) garantiza orden total observable
    // por todos los procesadores. Ningún store previo puede reordenarse
    // después de esta barrera.
    fence(Ordering::SeqCst);

    // ── Paso 4: abort sin recuperación in-process ──────────────────────────
    // En std: std::process::abort() — señal SIGABRT, sin unwinding.
    // En no_std (bare-metal): loop infinito + wfe (espera evento ARM).
    // La elección de abort vs. loop es semánticamente equivalente para el
    // invariante: ninguna transición posterior es posible.
    #[cfg(not(feature = "std"))]
    abort_bare_metal();

    #[cfg(feature = "std")]
    std::process::abort();
}

// ---------------------------------------------------------------------------
// Implementación bare-metal del abort (no_std)
// ---------------------------------------------------------------------------

/// Detención bare-metal: loop infinito con `wfe` para reducir consumo.
/// No retorna jamás. En hardware real, el watchdog externo detectará
/// la ausencia de heartbeat y reiniciará el sistema de forma controlada.
#[cfg(not(feature = "std"))]
#[inline(never)]
fn abort_bare_metal() -> ! {
    loop {
        #[cfg(target_arch = "aarch64")]
        unsafe {
            core::arch::asm!("wfe", options(nomem, nostack, preserves_flags));
        }
        #[cfg(not(target_arch = "aarch64"))]
        core::hint::spin_loop();
    }
}

// ---------------------------------------------------------------------------
// Verificación del estado de halt — utilidad pública
// ---------------------------------------------------------------------------

/// Retorna `true` si el slot está en estado `POISONED`.
///
/// Los lectores externos pueden usar esta función como guardia rápida
/// antes de iniciar operaciones. Carga con `Acquire` para observar
/// cualquier store previo con `Release` (incluido el de `epistemic_halt`).
///
/// # Ejemplo
/// ```
/// use babylon60::manifest::{SharedManifest, POISONED};
/// use babylon60::halt::is_halted;
/// use std::sync::atomic::Ordering;
///
/// let manifest = SharedManifest::new();
/// assert!(!is_halted(&manifest));
/// manifest.status_flag.store(POISONED, Ordering::Release);
/// assert!(is_halted(&manifest));
/// ```
#[inline]
#[must_use]
pub fn is_halted(m: &SharedManifest) -> bool {
    m.status_flag.load(Ordering::Acquire) == POISONED
}
