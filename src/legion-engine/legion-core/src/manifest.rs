// C5-REAL EXERGY CERTIFIED
// Zero-Split Cache-Line Coherence: Exact 64-byte alignment
use std::sync::atomic::{AtomicU32, AtomicU64, Ordering};

pub const MANIFEST_ALIGNMENT: usize = 64;
pub const MANIFEST_SIZE: usize = 64;

#[repr(u32)]
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum ManifestStatus {
    Idle = 0,
    Writing = 1,
    Ready = 2,
    Validating = 3,
    Active = 4,
    Retired = 5,
    Quarantine = 6,
}

impl From<u32> for ManifestStatus {
    fn from(val: u32) -> Self {
        match val {
            0 => ManifestStatus::Idle,
            1 => ManifestStatus::Writing,
            2 => ManifestStatus::Ready,
            3 => ManifestStatus::Validating,
            4 => ManifestStatus::Active,
            5 => ManifestStatus::Retired,
            6 => ManifestStatus::Quarantine,
            _ => ManifestStatus::Quarantine,
        }
    }
}

/// Header de 64 bytes con alineación estricta de línea de caché L1/L2
#[repr(C, align(64))]
pub struct SharedManifest {
    pub magic: [u8; 8],              // 0x00 - "EXERGY01"
    pub epoch_id: AtomicU64,         // 0x08 - Epoch actual
    pub status_flag: AtomicU32,      // 0x10 - Status flag (ManifestStatus)
    pub active_readers: AtomicU32,   // 0x14 - Conteo atómico de lectores
    pub sha256_digest: [u8; 32],     // 0x18 - Payload Hash (32 bytes)
    pub timestamp_ns: AtomicU64,     // 0x38 - Nanosegundos UTC (8 bytes)
}                                    // Total: 8 + 8 + 4 + 4 + 32 + 8 = 64 bytes

impl SharedManifest {
    pub const MAGIC: [u8; 8] = *b"EXERGY01";

    pub fn new(epoch_id: u64) -> Self {
        Self {
            magic: Self::MAGIC,
            epoch_id: AtomicU64::new(epoch_id),
            status_flag: AtomicU32::new(ManifestStatus::Idle as u32),
            active_readers: AtomicU32::new(0),
            sha256_digest: [0u8; 32],
            timestamp_ns: AtomicU64::new(0),
        }
    }

    #[inline(always)]
    pub fn get_status(&self) -> ManifestStatus {
        ManifestStatus::from(self.status_flag.load(Ordering::Acquire))
    }

    #[inline(always)]
    pub fn set_status(&self, status: ManifestStatus) {
        self.status_flag.store(status as u32, Ordering::Release);
    }

    #[inline(always)]
    pub fn try_acquire_reader(&self) -> bool {
        loop {
            let status = self.get_status();
            if status != ManifestStatus::Active {
                return false;
            }
            let current = self.active_readers.load(Ordering::Relaxed);
            if self.active_readers.compare_exchange_weak(
                current,
                current + 1,
                Ordering::Acquire,
                Ordering::Relaxed,
            ).is_ok() {
                return true;
            }
        }
    }

    #[inline(always)]
    pub fn release_reader(&self) {
        self.active_readers.fetch_sub(1, Ordering::Release);
    }

    #[inline(always)]
    pub fn active_readers_count(&self) -> u32 {
        self.active_readers.load(Ordering::Acquire)
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::mem::{align_of, size_of};

    #[test]
    fn test_manifest_64byte_cache_alignment() {
        assert_eq!(size_of::<SharedManifest>(), 64);
        assert_eq!(align_of::<SharedManifest>(), 64);
    }

    #[test]
    fn test_lock_free_reader_transitions() {
        let manifest = SharedManifest::new(1);
        manifest.set_status(ManifestStatus::Active);
        assert!(manifest.try_acquire_reader());
        assert_eq!(manifest.active_readers_count(), 1);
        manifest.release_reader();
        assert_eq!(manifest.active_readers_count(), 0);
    }
}
