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
//
// FIX (audit 2026-09-10): el store de POISONED estaba comentado
// («Adaptado para ABI»), de modo que el proceso abortaba SIN envenenar el
// slot compartido: ningún observador IPC llegaba a ver el estado POISONED y
// `is_halted()` jamás retornaba true en la ruta de halt. Restaurado como
// Paso 1, antes del recibo COSE y del abort, tal como documenta la spec.

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
/// Transiciona el slot al estado `POISONED` y termina el proceso.
/// ## Clave operativa
/// Sin signer inyectado se usa [`crate::receipt::NoOperationalKey`]: el halt registra
/// evidencia `UnsignedDurable`. Generar una clave Ed25519 efímera por halt produciría
/// una firma que ningún verificador puede anclar a una autoridad (firma sintética).
#[inline(never)]
#[allow(unused_variables)]
pub fn epistemic_halt(m: &SharedManifest, motivo: HaltReason) -> ! {
    #[cfg(feature = "halt-receipt")]
    {
        epistemic_halt_with_signer(m, motivo, &crate::receipt::NoOperationalKey)
    }
    #[cfg(not(feature = "halt-receipt"))]
    {
        epistemic_halt_raw(m)
    }
}

/// Resultado de persistencia de evidencia forense durante el halt epistémico (presupuesto acotado).
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum EvidenceOutcome {
    /// Recibo firmado por la clave operativa, escrito y sincronizado (`fsync`) dentro del presupuesto.
    SignedDurable,
    /// Firma no disponible o snapshot no coherente; volcado no firmado sincronizado dentro del presupuesto.
    UnsignedDurable,
    /// Escritura fallida o presupuesto agotado (disco lleno, I/O colgada, ruta inválida).
    PersistenceFailed,
}

/// Presupuesto por defecto para persistir evidencia de halt.
pub const DEFAULT_HALT_EVIDENCE_BUDGET_MS: u64 = 250;

/// Escribe `bytes` en `path`, ejecuta `fsync` sobre el archivo y su directorio padre,
/// en un hilo desacoplado. Devuelve `true` sólo si todo terminó dentro de `budget`.
/// Si el presupuesto se agota, el hilo queda huérfano y el halt continúa: la
/// terminación del proceso no espera al disco.
#[cfg(feature = "std")]
fn write_durable_bounded(path: std::string::String, bytes: std::vec::Vec<u8>, budget: std::time::Duration) -> bool {
    use std::io::Write;
    let (tx, rx) = std::sync::mpsc::channel();
    let spawned = std::thread::Builder::new()
        .name("halt-evidence-writer".into())
        .spawn(move || {
            let result = (|| -> std::io::Result<()> {
                let mut f = std::fs::File::create(&path)?;
                f.write_all(&bytes)?;
                f.sync_all()?;
                if let Some(parent) = std::path::Path::new(&path).parent() {
                    let dir = if parent.as_os_str().is_empty() { std::path::Path::new(".") } else { parent };
                    std::fs::File::open(dir)?.sync_all()?;
                }
                Ok(())
            })();
            let _ = tx.send(result.is_ok());
        });
    if spawned.is_err() {
        return false;
    }
    matches!(rx.recv_timeout(budget), Ok(true))
}

/// Registra la evidencia forense del halt con presupuesto acotado.
///
/// Secuencia: cerrar admisión (`POISONED`) → snapshot coherente o `UNAVAILABLE` →
/// intentar firma con la clave operativa → escritura sincronizada acotada.
/// Nunca sustituye una firma fallida por bytes sintéticos.
///
/// **Requisito del signer:** debe ser no interactivo (sin Touch ID). La firma no
/// está acotada por el presupuesto; sólo la persistencia lo está.
#[cfg(all(feature = "std", feature = "halt-receipt"))]
#[inline(never)]
pub fn record_halt_evidence<S: crate::receipt::Signer>(
    m: &SharedManifest,
    motivo: HaltReason,
    signer: &S,
    receipt_path: Option<&str>,
    budget: std::time::Duration,
) -> EvidenceOutcome {
    // ── Paso 1: cierre de admisión ────────────────────────────────────────
    m.status_flag.store(POISONED, Ordering::Release);
    fence(Ordering::SeqCst);

    let base = receipt_path.unwrap_or("babylon60_halt_receipt.cose").to_string();

    // ── Paso 2: recibo firmado ────────────────────────────────────────────
    let failure = match crate::receipt::emit_halt_receipt(m, motivo, signer) {
        Ok(receipt_bytes) => {
            return if write_durable_bounded(base, receipt_bytes, budget) {
                EvidenceOutcome::SignedDurable
            } else {
                EvidenceOutcome::PersistenceFailed
            };
        }
        Err(e) => e,
    };

    // ── Paso 3: volcado no firmado, declarado como tal ────────────────────
    let snapshot = match crate::seqlock::read(m) {
        Some((epoch, h)) => format!(
            "SNAPSHOT:COHERENT\nEPOCH:{}\nPAYLOAD_HASH:{:016x}{:016x}{:016x}{:016x}\n",
            epoch, h[0], h[1], h[2], h[3]
        ),
        None => "SNAPSHOT:UNAVAILABLE\n".to_string(),
    };
    let dump = format!(
        "BABYLON60-HALT-UNSIGNED/1\nSTATUS:POISONED\nREASON:{}\n{}SIGNATURE:NONE\nSIGNING_ERROR:{}\n",
        motivo.as_str(),
        snapshot,
        failure
    );
    if write_durable_bounded(format!("{}.unsigned", base), dump.into_bytes(), budget) {
        EvidenceOutcome::UnsignedDurable
    } else {
        EvidenceOutcome::PersistenceFailed
    }
}

/// Variante de `epistemic_halt` con inyección explícita del signer operativo (no interactivo).
#[inline(never)]
#[allow(unused_variables)]
pub fn epistemic_halt_with_signer<S: crate::receipt::Signer>(
    m: &SharedManifest,
    motivo: HaltReason,
    signer: &S,
) -> ! {
    #[cfg(all(feature = "std", feature = "halt-receipt"))]
    {
        let receipt_path = std::env::var("BABYLON_HALT_RECEIPT_PATH").ok();
        let budget_ms = std::env::var("BABYLON_HALT_EVIDENCE_BUDGET_MS")
            .ok()
            .and_then(|v| v.parse().ok())
            .unwrap_or(DEFAULT_HALT_EVIDENCE_BUDGET_MS);
        let outcome = record_halt_evidence(
            m,
            motivo,
            signer,
            receipt_path.as_deref(),
            std::time::Duration::from_millis(budget_ms),
        );
        eprintln!("[HALT] evidence_outcome={:?}", outcome);
    }

    epistemic_halt_raw(m)
}

/// Ejecución de bajo nivel de la barrera SeqCst y abort in-process.
#[inline(never)]
fn epistemic_halt_raw(m: &SharedManifest) -> ! {
    // Asegurar que POISONED esté sellado
    m.status_flag.store(POISONED, Ordering::Release);

    // ── Paso 3: barrera total ──────────────────────────────────────────────
    fence(Ordering::SeqCst);

    // ── Paso 4: abort sin recuperación in-process ──────────────────────────
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

// ---------------------------------------------------------------------------
// Tests de evidencia de halt (no abortan: ejercitan record_halt_evidence)
// ---------------------------------------------------------------------------

#[cfg(all(test, feature = "std", feature = "halt-receipt"))]
mod tests {
    use super::*;
    use crate::receipt::{verify_and_parse_halt_receipt, Ed25519Signer, NoOperationalKey};
    use std::time::Duration;

    fn tmp_path(tag: &str) -> std::path::PathBuf {
        let nanos = std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .unwrap()
            .as_nanos();
        let dir = std::env::temp_dir().join(format!("b60_halt_{}_{}_{}", tag, std::process::id(), nanos));
        std::fs::create_dir_all(&dir).unwrap();
        dir.join("receipt.cose")
    }

    #[test]
    fn halt_signed_durable_receipt_verifies() {
        let m = SharedManifest::new();
        crate::seqlock::publish(&m, 7, &[1, 2, 3, 4]);
        let signer = Ed25519Signer::new();
        let path = tmp_path("signed");
        let out = record_halt_evidence(&m, HaltReason::HashMismatch, &signer, path.to_str(), Duration::from_secs(5));
        assert_eq!(out, EvidenceOutcome::SignedDurable);
        assert!(is_halted(&m));
        let bytes = std::fs::read(&path).unwrap();
        let summary = verify_and_parse_halt_receipt(&bytes, &signer).unwrap();
        assert_eq!(summary.epoch, 7);
    }

    #[test]
    fn halt_without_operational_key_is_unsigned_never_synthetic() {
        let m = SharedManifest::new();
        crate::seqlock::publish(&m, 9, &[5, 6, 7, 8]);
        let path = tmp_path("unsigned");
        let out = record_halt_evidence(&m, HaltReason::ExternalSignal, &NoOperationalKey, path.to_str(), Duration::from_secs(5));
        assert_eq!(out, EvidenceOutcome::UnsignedDurable);
        assert!(!path.exists(), "no signed receipt may exist when signing failed");
        let dump = std::fs::read_to_string(format!("{}.unsigned", path.display())).unwrap();
        assert!(dump.contains("SIGNATURE:NONE"));
        assert!(dump.contains("SNAPSHOT:COHERENT"));
        assert!(dump.contains("EPOCH:9"));
    }

    #[test]
    fn halt_with_writer_mid_publication_declares_snapshot_unavailable() {
        let m = SharedManifest::new();
        // seq impar persistente = escritor muerto a mitad de publicación
        m.seq.store(1, Ordering::Release);
        let signer = Ed25519Signer::new();
        let path = tmp_path("torn");
        let out = record_halt_evidence(&m, HaltReason::SeqRetryExhausted, &signer, path.to_str(), Duration::from_secs(5));
        assert_eq!(out, EvidenceOutcome::UnsignedDurable);
        let dump = std::fs::read_to_string(format!("{}.unsigned", path.display())).unwrap();
        assert!(dump.contains("SNAPSHOT:UNAVAILABLE"));
        assert!(!dump.contains("EPOCH:"));
    }

    #[test]
    fn halt_unwritable_path_reports_persistence_failed() {
        let m = SharedManifest::new();
        let signer = Ed25519Signer::new();
        let out = record_halt_evidence(
            &m,
            HaltReason::HashMismatch,
            &signer,
            Some("/nonexistent_b60_dir/sub/receipt.cose"),
            Duration::from_secs(5),
        );
        assert_eq!(out, EvidenceOutcome::PersistenceFailed);
        assert!(is_halted(&m), "admission must be closed even if evidence fails");
    }
}
