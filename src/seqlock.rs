// C5-REAL EXERGY CERTIFIED — BABYLON-60 — INV-2 (concurrencia)
// Seqlock escritor-único / SPMC para AArch64/ARMv9 (memoria débil)
//
// MODELO DE MEMORIA
// ─────────────────
// AArch64 es multicopy-atomic pero NO TSO: las cargas independientes pueden
// reordenarse entre sí. Las elecciones de ordenamiento son conservadoras y
// correctas también en x86-TSO (Acquire/Release compilan a MOV en x86).
//
// MAPEO C11 → AArch64 (verbatim ISA ARMv9)
// ─────────────────────────────────────────
//   load(Acquire)        → LDAR  (o LDAPR con FEAT_LRCPC)
//   store(Release)       → STLR
//   fence(Acquire)       → DMB ISHLD   ← imprescindible para reorden carga-carga
//   fence(Release)       → DMB ISH
//   RMW con FEAT_LSE     → LDADD / SWP / CAS
//
// BISIMULACIÓN (INV-3 termódinámica / Dynamis-Entelecheia):
//   seq impar  = Dynamis    (estado en potencia, inobservable, lectores rechazan)
//   seq par    = Entelecheia (acto validado, observable)
//   El cociente observable contiene únicamente estados pares →
//   especificación y ejecución observacionalmente bisimilares.
//
// PRUEBA DE AUSENCIA DE CARRERAS (C11):
//   store(Release, s+2) / load(Acquire, s1) establece happens-before.
//   Las cargas Relaxed del hash quedan encajonadas entre s1 y s2.
//   Si el escritor intervino, seq cambió (par→impar→par distinto) y s1≠s2
//   fuerza reintento. Ningún acceso es no-atómico → no hay data race.
//
// IMPOSIBILIDAD DE ABA:
//   epoch_id es contador estrictamente monótono (monoide (ℕ,+), no invertible).
//   Cota de envolvimiento: 2⁶⁴ ÷ 10⁹ s⁻¹ ≈ 584.5 años.

use core::sync::atomic::{fence, Ordering};
use core::hint::spin_loop;

use crate::manifest::{SharedManifest, MAX_RETRIES};

// ---------------------------------------------------------------------------
// Escritor (único) — INV-2
// ---------------------------------------------------------------------------

/// Publica un nuevo (epoch, hash) de forma atómica sobre el seqlock.
///
/// **Garantías de ordenamiento (AArch64):**
/// 1. `seq.store(s+1, Relaxed)` → marca impar (Dynamis).
/// 2. `fence(Release)` → `DMB ISH`: hash/epoch no suben antes del impar.
/// 3. Stores Relaxed del hash y epoch (encajonados por la barrera).
/// 4. `seq.store(s+2, Release)` → `STLR`: par, publicación visible.
///
/// # Ejemplo
/// ```
/// use babylon_60::manifest::SharedManifest;
/// use babylon_60::seqlock::{publish, read};
///
/// let manifest = SharedManifest::new();
/// let hash = [0xA, 0xB, 0xC, 0xD];
/// publish(&manifest, 42, &hash);
/// assert_eq!(read(&manifest), Some((42, hash)));
/// ```
///
/// # Safety
/// Debe ser invocada por **un único hilo escritor** en todo momento.
/// La invocación concurrente desde múltiples hilos es UB.
#[inline]
pub fn publish(m: &SharedManifest, epoch: u64, hash: &[u64; 4]) {
    // Paso 1: leer seq actual con Relaxed (solo el escritor toca seq pares→impares)
    let s = m.seq.load(Ordering::Relaxed);

    // Paso 2: seq impar → escritura en curso (Dynamis)
    m.seq.store(s.wrapping_add(1), Ordering::Relaxed);

    // Paso 3: barrera Release (DMB ISH) — los stores de hash/epoch no pueden
    // subir por encima de la transición par→impar de seq.
    fence(Ordering::Release);

    // Paso 4: almacenar payload (Relaxed; la barrera del paso 3 y del paso 5
    // encajan correctamente el happens-before con el lector)
    for (i, val) in hash.iter().enumerate() {
        m.payload_hash[i].store(*val, Ordering::Relaxed);
    }
    m.epoch_id.store(epoch, Ordering::Relaxed);

    // Paso 5: seq par → publicación validada (Entelecheia). STLR en AArch64.
    // Release garantiza que todos los stores anteriores son visibles antes
    // de que el lector pueda ver el nuevo valor par de seq.
    m.seq.store(s.wrapping_add(2), Ordering::Release);
}

// ---------------------------------------------------------------------------
// Lector (puro-de-carga) — INV-2
// ---------------------------------------------------------------------------

/// Lee (epoch, hash) del slot de forma consistente.
///
/// El lector es **puro-de-carga**: cero stores, cero RMW, cero RFO.
/// La línea de caché permanece en estado **Shared** en todas las cachés
/// lectoras → colapso de anergía O(tasa_lectura) a cero (INV-3).
///
/// Retorna `None` si se agotan `MAX_RETRIES` sin lectura consistente.
/// El llamante DEBE invocar [`epistemic_halt`](crate::halt::epistemic_halt)
/// ante un `None` (protocolo fail-stop, INV-4).
///
/// **Barrera carga-carga — por qué NO es gratis en AArch64:**
/// En x86 (TSO) las cargas ya están ordenadas; `fence(Acquire)` compila a
/// no-op. En AArch64, la ISA permite reordenar cargas independientes: sin
/// `DMB ISHLD`, la relectura de `seq` (s2) podría satisfacerse desde caché
/// **antes** de leer el hash, colapsando la ventana de detección y
/// produciendo una lectura rasgada indetectable. La barrera es obligatoria.
#[inline]
#[must_use]
pub fn read(m: &SharedManifest) -> Option<(u64, [u64; 4])> {
    for _ in 0..MAX_RETRIES {
        // Paso 1: leer seq con Acquire (LDAR) — establece la mitad
        // "load-acquire" del par happens-before con store(Release, s+2)
        let s1 = m.seq.load(Ordering::Acquire); // AArch64: LDAR

        // Paso 2: si impar → escritura en curso; spin y reintento
        if s1 & 1 != 0 {
            spin_loop(); // AArch64: YIELD / WFE hint
            continue;
        }

        // Paso 3: cargar payload con Relaxed (puro-de-carga; sin RFO)
        let mut h = [0u64; 4];
        for (i, slot) in m.payload_hash.iter().enumerate() {
            h[i] = slot.load(Ordering::Relaxed);
        }
        let e = m.epoch_id.load(Ordering::Relaxed);

        // Paso 4: barrera Acquire (DMB ISHLD) — impide que la carga de s2
        // se reordene por delante de las cargas Relaxed del hash/epoch.
        // Obligatoria en AArch64; no-op en x86-TSO.
        fence(Ordering::Acquire); // AArch64: DMB ISHLD

        // Paso 5: verificar consistencia — si seq no cambió, la lectura es válida
        let s2 = m.seq.load(Ordering::Relaxed);
        if s1 == s2 {
            return Some((e, h));
        }
        // s1 ≠ s2 → escritor intervino; la anergía del retry es acotada
        spin_loop();
    }

    None // agotados MAX_RETRIES → el llamante debe invocar epistemic_halt
}
