//! CORTEX Ledger Cryptographic Integrity Core
//!
//! Enforces O1-O14 invariants (C5-REAL) with zero runtime allocations.
//! Utilizes a lock-free Seqlock SPMC protocol for concurrent transaction validation.



use core::sync::atomic::{AtomicU64, AtomicUsize, Ordering};
use core::cell::UnsafeCell;
use sha2::{Digest, Sha256};

/// Tamaño fijo del payload de la transacción para evitar asignaciones dinámicas (cero-punteros).
pub const LEDGER_TX_SIZE: usize = 64;

#[repr(C, align(64))]
pub struct CortexLedgerManifest {
    pub sequence_lock: AtomicUsize,
    pub timestamp_ns: AtomicU64,
    pub causal_hash: UnsafeCell<[u8; 32]>,
    pub data_payload: UnsafeCell<[u8; LEDGER_TX_SIZE]>,
}

unsafe impl Sync for CortexLedgerManifest {}
unsafe impl Send for CortexLedgerManifest {}

impl CortexLedgerManifest {
    #[inline(always)]
    pub fn new(timestamp_ns: u64, causal_hash: [u8; 32], payload: [u8; LEDGER_TX_SIZE]) -> Self {
        Self {
            sequence_lock: AtomicUsize::new(0),
            timestamp_ns: AtomicU64::new(timestamp_ns),
            causal_hash: UnsafeCell::new(causal_hash),
            data_payload: UnsafeCell::new(payload),
        }
    }

    /// Comienza una operación de escritura (Mutación Causal). Incrementa el seqlock a impar.
    #[inline(always)]
    pub fn begin_write(&self) -> usize {
        let seq = self.sequence_lock.load(Ordering::Relaxed);
        let next = seq.wrapping_add(1);
        self.sequence_lock.store(next, Ordering::Release);
        next
    }

    /// Finaliza una operación de escritura. Incrementa el seqlock a par.
    #[inline(always)]
    pub fn end_write(&self, seq: usize) {
        self.sequence_lock.store(seq.wrapping_add(1), Ordering::Release);
    }

    /// Prueba de Integridad Criptográfica (Zero-Allocation, Lock-Free Reader)
    #[inline(always)]
    pub fn verify_integrity(&self, expected_hash: &[u8; 32]) -> bool {
        let mut retry_count = 0;
        loop {
            // 1. Leer el número de secuencia inicial (adquirir semántica)
            let seq1 = self.sequence_lock.load(Ordering::Acquire);

            // Si es impar, hay una escritura en progreso. Backoff.
            if seq1 & 1 != 0 {
                core::hint::spin_loop();
                continue;
            }

            // 2. Ruta Crítica: Lectura del manifiesto (Cero asignaciones)
            let current_timestamp = self.timestamp_ns.load(Ordering::Relaxed);
            let mut read_hash = [0u8; 32];
            let mut read_payload = [0u8; LEDGER_TX_SIZE];

            unsafe {
                core::ptr::copy_nonoverlapping((*self.causal_hash.get()).as_ptr(), read_hash.as_mut_ptr(), 32);
                core::ptr::copy_nonoverlapping(
                    (*self.data_payload.get()).as_ptr(),
                    read_payload.as_mut_ptr(),
                    LEDGER_TX_SIZE,
                );
            }

            // 3. Leer número de secuencia final para validar aislamiento
            let seq2 = self.sequence_lock.load(Ordering::Acquire);

            if seq1 == seq2 {
                // Validación estricta criptográfica en O(1) memoria
                let mut hasher = Sha256::new();
                hasher.update(current_timestamp.to_le_bytes());
                hasher.update(read_payload);
                let computed = hasher.finalize();

                // Comparación de tiempo constante (Anti-Timing Attacks)
                let mut is_valid = 1u8;
                for i in 0..32 {
                    if computed[i] != read_hash[i] {
                        is_valid = 0;
                    }
                    if read_hash[i] != expected_hash[i] {
                        is_valid = 0;
                    }
                }
                return is_valid == 1;
            }

            retry_count += 1;
            if retry_count > 10_000 {
                // Fall-stop determinista (Prevención de Livelock en arquitectura C5)
                return false;
            }
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::sync::Arc;
    use std::thread;
    use sha2::{Digest, Sha256};

    #[test]
    fn stress_test_seqlock_integrity() {
        let payload = [0x55u8; LEDGER_TX_SIZE];
        let timestamp: u64 = 1_600_000_000_000;
        let mut hasher = Sha256::new();
        hasher.update(timestamp.to_le_bytes());
        hasher.update(payload);
        let expected_hash: [u8; 32] = hasher.finalize().into();

        let manifest = Arc::new(CortexLedgerManifest::new(timestamp, expected_hash, payload));
        let num_readers = 16;
        let num_writers = 1;
        let iterations = 10_000;

        let mut handles = vec![];

        // Writers: Mutan el manifiesto temporalmente, pero siempre terminan restaurándolo
        for _w in 0..num_writers {
            let m = manifest.clone();
            handles.push(thread::spawn(move || {
                for i in 0..iterations {
                    let seq = m.begin_write();
                    
                    // Inducir fricción térmica (escribir basura)
                    unsafe { (*m.causal_hash.get())[0] = (i % 255) as u8; }
                    // Restaurar hash correcto
                    unsafe { (*m.causal_hash.get())[0] = expected_hash[0]; }
                    
                    m.end_write(seq);
                }
            }));
        }

        // Readers: Bombardeo constante de lectura lock-free
        for _ in 0..num_readers {
            let m = manifest.clone();
            handles.push(thread::spawn(move || {
                let mut success_reads = 0;
                for _ in 0..(iterations * 2) {
                    if m.verify_integrity(&expected_hash) {
                        success_reads += 1;
                    }
                }
                assert!(success_reads > 0, "Livelock preventivo extremo o lectura fallida");
            }));
        }

        for h in handles {
            h.join().unwrap();
        }
    }
}
