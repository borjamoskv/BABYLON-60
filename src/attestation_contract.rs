use core::sync::atomic::{AtomicU32, AtomicU64, Ordering};

/// Estado en ejecución normal.
pub const RUNNING: u32 = 0x0000_0001;
/// Estado envenenado (fail-stop).
pub const POISONED: u32 = 0xDEAD_6060;
/// Umbral máximo de reintentos antes de considerar estado envenenado.
pub const MAX_RETRIES: usize = 10_000;

/// Contrato SPMC Seqlock de 64 bytes para evitar Torn Reads en Attestation (Nivel 1).
/// Protege lecturas concurrentes de `count` y `payload_hash`.
#[repr(C, align(64))]
pub struct AttestationContract {
    /// Estado actual (RUNNING o POISONED).
    pub status_flag: AtomicU32,     // 0x00
    /// Número de secuencia del seqlock.
    pub seq: AtomicU32,             // 0x04
    /// Contador monótono de atestaciones.
    pub count: AtomicU64,           // 0x08
    /// Hash criptográfico de la atestación (256 bits).
    pub payload_hash: [AtomicU64; 4],// 0x10
    /// Padding para alinear a 64 bytes exactos.
    pub _padding: [u8; 16],         // 0x30
}

impl Default for AttestationContract {
    fn default() -> Self {
        Self::new()
    }
}

impl AttestationContract {
    /// Crea una nueva instancia del contrato.
    pub const fn new() -> Self {
        Self {
            status_flag: AtomicU32::new(RUNNING),
            seq: AtomicU32::new(0),
            count: AtomicU64::new(0),
            payload_hash: [
                AtomicU64::new(0),
                AtomicU64::new(0),
                AtomicU64::new(0),
                AtomicU64::new(0),
            ],
            _padding: [0; 16],
        }
    }

    /// Publica un nuevo conteo y hash atómicamente.
    pub fn publish(&self, new_count: u64, hash: &[u64; 4]) -> Result<(), &'static str> {
        if self.status_flag.load(Ordering::Relaxed) == POISONED {
            return Err("POISONED_STATE");
        }
        let s = self.seq.fetch_add(1, Ordering::Release);
        core::sync::atomic::fence(Ordering::Release);
        
        self.count.store(new_count, Ordering::Relaxed);
        for (slot, &val) in self.payload_hash.iter().zip(hash.iter()) {
            slot.store(val, Ordering::Relaxed);
        }
        
        self.seq.store(s.wrapping_add(2), Ordering::Release);
        Ok(())
    }

    /// Lee atómicamente el conteo y el hash.
    pub fn read(&self) -> Option<(u64, [u64; 4])> {
        let mut retries = 0;
        while retries < MAX_RETRIES {
            if self.status_flag.load(Ordering::Relaxed) == POISONED {
                return None;
            }
            let s1 = self.seq.load(Ordering::Acquire);
            if !s1.is_multiple_of(2) {
                retries += 1;
                core::hint::spin_loop();
                continue;
            }
            
            let current_count = self.count.load(Ordering::Relaxed);
            let mut hash = [0u64; 4];
            for (slot, val) in self.payload_hash.iter().zip(hash.iter_mut()) {
                *val = slot.load(Ordering::Relaxed);
            }
            
            core::sync::atomic::fence(Ordering::Acquire);
            let s2 = self.seq.load(Ordering::Acquire);
            if s1 == s2 {
                return Some((current_count, hash));
            }
            retries += 1;
            core::hint::spin_loop();
        }
        None
    }

    /// Fuerzan un estado envenenado irreversible.
    pub fn epistemic_halt(&self) {
        self.status_flag.store(POISONED, Ordering::SeqCst);
        self.seq.fetch_add(1, Ordering::SeqCst);
    }
}
