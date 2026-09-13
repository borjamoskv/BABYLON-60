use core::sync::atomic::{AtomicU32, AtomicU64, Ordering};

pub const RUNNING: u32 = 0x0000_0001;
pub const POISONED: u32 = 0xDEAD_6060;
pub const MAX_RETRIES: usize = 10_000;

/// SharedManifest: Estructura C-ABI hiper-optimizada a 64 Bytes exactos.
/// Garantiza cero false-sharing en cachés L1.
/// Utiliza un SPMC Seqlock para sincronización lock-free.
#[repr(C, align(64))]
pub struct SharedManifest {
    pub status_flag: AtomicU32,      // 0x00
    pub seq: AtomicU32,              // 0x04
    pub epoch_id: AtomicU64,         // 0x08
    pub payload_hash: [AtomicU64; 4],// 0x10
    pub _padding: [u8; 16],          // 0x30
}

impl SharedManifest {
    #[inline(always)]
    pub const fn new() -> Self {
        Self {
            status_flag: AtomicU32::new(RUNNING),
            seq: AtomicU32::new(0),
            epoch_id: AtomicU64::new(1),
            payload_hash: [
                AtomicU64::new(0),
                AtomicU64::new(0),
                AtomicU64::new(0),
                AtomicU64::new(0),
            ],
            _padding: [0; 16],
        }
    }

    /// Publica un nuevo estado en el manifest usando un Write Seqlock.
    #[inline(always)]
    pub fn publish(&self, epoch: u64, hash: &[u64; 4]) -> Result<(), &'static str> {
        if self.status_flag.load(Ordering::Relaxed) == POISONED {
            return Err("POISONED_STATE");
        }
        
        // 1. Writer Acquire: Incrementamos la secuencia a impar.
        let s = self.seq.fetch_add(1, Ordering::Release);
        
        // 2. Escritura de payload sin locks.
        self.epoch_id.store(epoch, Ordering::Relaxed);
        for (slot, &val) in self.payload_hash.iter().zip(hash.iter()) {
            slot.store(val, Ordering::Relaxed);
        }
        
        // 3. Writer Release: Incrementamos la secuencia a par.
        self.seq.store(s.wrapping_add(2), Ordering::Release);
        
        Ok(())
    }

    /// Lee de forma asíncrona y sin bloqueos el payload del manifest (SPMC Read).
    #[inline(always)]
    pub fn read(&self) -> Option<(u64, [u64; 4])> {
        let mut retries = 0;
        
        while retries < MAX_RETRIES {
            if self.status_flag.load(Ordering::Relaxed) == POISONED {
                return None;
            }
            
            // Acquire barrera para leer la secuencia de inicio
            let s1 = self.seq.load(Ordering::Acquire);
            if !s1.is_multiple_of(2) {
                // Escritura en progreso: Backoff exponencial para enfriamiento MESI
                let spins = 1 << retries.min(7);
                for _ in 0..spins {
                    core::hint::spin_loop();
                }
                retries += 1;
                continue;
            }
            
            let epoch = self.epoch_id.load(Ordering::Relaxed);
            let mut hash = [0u64; 4];
            for (slot, val) in self.payload_hash.iter().zip(hash.iter_mut()) {
                *val = slot.load(Ordering::Relaxed);
            }
            
            // Acquire barrera para verificar si hubo mutación durante la lectura
            let s2 = self.seq.load(Ordering::Acquire);
            if s1 == s2 {
                return Some((epoch, hash));
            }
            
            // Falla de consistencia: escritura concurrente. Backoff exponencial.
            let spins = 1 << retries.min(7);
            for _ in 0..spins {
                core::hint::spin_loop();
            }
            retries += 1;
        }
        None
    }

    /// Activa el protocolo de seguridad Fail-Stop (SCITT).
    /// Envenena el estado del IPC y emite una atestación criptográfica firmada.
    #[inline(always)]
    pub fn epistemic_halt(&self, secret_key_bytes: &[u8; 32]) -> crate::scitt::ScittReceipt {
        // [C5-REAL] Si ya está envenenado, retornar de forma inmediata en O(1) evitando re-firmar
        if self.status_flag.load(Ordering::Acquire) == POISONED {
            let epoch = self.epoch_id.load(Ordering::Relaxed);
            return crate::scitt::ScittReceipt {
                epoch_halted: epoch,
                signature: [0u8; 64],
            };
        }

        // Envenenamiento termodinámico irreversible
        self.status_flag.store(POISONED, Ordering::SeqCst);
        self.seq.fetch_add(1, Ordering::SeqCst);
        
        let epoch = self.epoch_id.load(Ordering::Relaxed);
        crate::scitt::ScittReceipt::new(epoch, secret_key_bytes)
    }
}

// Implementación Default para convención de Rust
impl Default for SharedManifest {
    fn default() -> Self {
        Self::new()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_shared_manifest_layout_invariants() {
        // [AX-2] TOPOLOGY: Garantizar isomorfismo estricto de caché L1
        assert_eq!(
            core::mem::size_of::<SharedManifest>(),
            64,
            "SharedManifest debe pesar exactamente 64 bytes para evitar False Sharing"
        );
        assert_eq!(
            core::mem::align_of::<SharedManifest>(),
            64,
            "SharedManifest debe estar alineado a 64 bytes"
        );
    }

    #[test]
    fn test_seqlock_publish_and_read() {
        let manifest = SharedManifest::new();
        
        // Estado inicial
        assert_eq!(manifest.status_flag.load(Ordering::SeqCst), RUNNING);
        
        // Publicar dato
        let test_hash = [0xAAAA, 0xBBBB, 0xCCCC, 0xDDDD];
        let epoch = 42;
        assert!(manifest.publish(epoch, &test_hash).is_ok());
        
        // Leer dato
        let read_result = manifest.read();
        assert!(read_result.is_some());
        let (read_epoch, read_hash) = read_result.expect("C5-REAL: Termodinámica forzada. Unwrap purgado.");
        
        assert_eq!(read_epoch, 42);
        assert_eq!(read_hash, test_hash);
    }

    #[test]
    fn test_epistemic_halt() {
        let manifest = SharedManifest::new();
        let secret_bytes = [0u8; 32];
        
        let receipt = manifest.epistemic_halt(&secret_bytes);
        assert_eq!(receipt.epoch_halted, 1); // El epoch_id inicial es 1
        
        // No se puede publicar
        assert!(manifest.publish(1, &[0; 4]).is_err());
        
        // Las lecturas devuelven None
        assert!(manifest.read().is_none());
        assert_eq!(manifest.status_flag.load(Ordering::SeqCst), POISONED);
    }
}
