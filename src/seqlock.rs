// Certified Specification — BABYLON-60 — INV-2 (concurrency)
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
#[allow(unused_imports)]
use core::hint::spin_loop;

use crate::manifest::{SharedManifest, MAX_RETRIES};

// ---------------------------------------------------------------------------
// Helpers de microarquitectura AArch64 / ARMv9
// ---------------------------------------------------------------------------

/// Barrera de memoria de lectura-lectura física `dmb ishld` para AArch64.
#[inline(always)]
fn memory_barrier_acquire_read() {
    #[cfg(target_arch = "aarch64")]
    unsafe {
        core::arch::asm!("dmb ishld", options(nostack, preserves_flags));
    }
    #[cfg(not(target_arch = "aarch64"))]
    {
        fence(Ordering::Acquire);
    }
}

/// Pista de ahorro de energía y liberación de pipeline CPU (`yield` en AArch64).
#[inline(always)]
fn cpu_spin_yield() {
    #[cfg(target_arch = "aarch64")]
    unsafe {
        core::arch::asm!("yield", options(nomem, nostack, preserves_flags));
    }
    #[cfg(not(target_arch = "aarch64"))]
    {
        spin_loop();
    }
}

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
/// use babylon60::manifest::SharedManifest;
/// use babylon60::seqlock::{publish, read};
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
    let s = m.seq.load(Ordering::Relaxed);
    m.seq.store(s.wrapping_add(1), Ordering::Relaxed);
    fence(Ordering::Release);

    m.epoch_id.store(epoch, Ordering::Relaxed);
    m.payload_hash[0].store(hash[0], Ordering::Relaxed);
    m.payload_hash[1].store(hash[1], Ordering::Relaxed);
    m.payload_hash[2].store(hash[2], Ordering::Relaxed);
    m.payload_hash[3].store(hash[3], Ordering::Relaxed);

    m.seq.store(s.wrapping_add(2), Ordering::Release);
}

// ---------------------------------------------------------------------------
// Lector (puro-de-carga) — INV-2
// ---------------------------------------------------------------------------

#[inline]
#[must_use]
pub fn read(m: &SharedManifest) -> Option<(u64, [u64; 4])> {
    let mut retries = 0;
    loop {
        if retries > MAX_RETRIES {
            return None;
        }
        let s1 = m.seq.load(Ordering::Acquire);
        if s1 & 1 != 0 {
            cpu_spin_yield();
            retries += 1;
            continue;
        }

        let epoch = m.epoch_id.load(Ordering::Relaxed);
        let h0 = m.payload_hash[0].load(Ordering::Relaxed);
        let h1 = m.payload_hash[1].load(Ordering::Relaxed);
        let h2 = m.payload_hash[2].load(Ordering::Relaxed);
        let h3 = m.payload_hash[3].load(Ordering::Relaxed);

        memory_barrier_acquire_read();
        let s2 = m.seq.load(Ordering::Relaxed);

        if s1 == s2 {
            return Some((epoch, [h0, h1, h2, h3]));
        }
        cpu_spin_yield();
        retries += 1;
    }
}

