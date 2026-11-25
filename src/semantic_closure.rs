use core::sync::atomic::Ordering;
use crate::manifest::{SharedManifest, MAX_RETRIES};

#[cfg(target_arch = "aarch64")]
#[inline(always)]
fn memory_barrier_acquire_read() {
    unsafe {
        core::arch::asm!("dmb ishld", options(nostack, preserves_flags));
    }
}

#[cfg(not(target_arch = "aarch64"))]
#[inline(always)]
fn memory_barrier_acquire_read() {
    core::sync::atomic::fence(Ordering::Acquire);
}

#[cfg(target_arch = "aarch64")]
#[inline(always)]
fn cpu_spin_yield() {
    unsafe {
        core::arch::asm!("yield", options(nomem, nostack, preserves_flags));
    }
}

#[cfg(not(target_arch = "aarch64"))]
#[inline(always)]
fn cpu_spin_yield() {
    core::hint::spin_loop();
}

/// Implementación de Semantic Closure (Nivel 5) para la lógica de persistencia.
/// Garantiza que todos los campos del manifiesto se lean de forma consistente,
/// evitando guardar estados intermedios inconsistentes.
#[inline]
pub fn read_consistent_state(m: &SharedManifest) -> Option<(u32, u32, u64, [u64; 4])> {
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

        let status = m.status_flag.load(Ordering::Relaxed);
        let epoch = m.epoch_id.load(Ordering::Relaxed);
        let h0 = m.payload_hash[0].load(Ordering::Relaxed);
        let h1 = m.payload_hash[1].load(Ordering::Relaxed);
        let h2 = m.payload_hash[2].load(Ordering::Relaxed);
        let h3 = m.payload_hash[3].load(Ordering::Relaxed);

        memory_barrier_acquire_read();
        let s2 = m.seq.load(Ordering::Acquire);

        if s1 == s2 {
            return Some((status, s1, epoch, [h0, h1, h2, h3]));
        }
        cpu_spin_yield();
        retries += 1;
    }
}
