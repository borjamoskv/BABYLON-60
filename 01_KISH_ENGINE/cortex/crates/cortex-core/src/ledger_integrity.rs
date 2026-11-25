//! Fixed-size ledger snapshots protected against concurrent mutation.
//! Verification fails closed on contention or poisoning; it never spins.
use sha2::{Digest, Sha256};
use std::sync::Mutex;

pub const LEDGER_TX_SIZE: usize = 64;

#[derive(Clone, Copy)]
struct LedgerSnapshot {
    timestamp_ns: u64,
    causal_hash: [u8; 32],
    payload: [u8; LEDGER_TX_SIZE],
}

/// In-process storage. This is not a shared-memory ABI or a lock-free seqlock.
pub struct CortexLedgerManifest {
    snapshot: Mutex<LedgerSnapshot>,
}

impl CortexLedgerManifest {
    pub fn new(timestamp_ns: u64, causal_hash: [u8; 32], payload: [u8; LEDGER_TX_SIZE]) -> Self {
        Self {
            snapshot: Mutex::new(LedgerSnapshot {
                timestamp_ns,
                causal_hash,
                payload,
            }),
        }
    }

    /// Publish a whole snapshot, or fail closed if another operation owns the guard.
    /// No mutable reference or unfinished-write token escapes this method.
    pub fn try_replace(
        &self,
        timestamp_ns: u64,
        causal_hash: [u8; 32],
        payload: [u8; LEDGER_TX_SIZE],
    ) -> bool {
        let Ok(mut snapshot) = self.snapshot.try_lock() else {
            return false;
        };
        *snapshot = LedgerSnapshot {
            timestamp_ns,
            causal_hash,
            payload,
        };
        true
    }

    /// Copy under exclusion, then hash outside the critical section.
    /// Contention and poisoning return false instead of waiting for a writer.
    pub fn verify_integrity(&self, expected_hash: &[u8; 32]) -> bool {
        let snapshot = match self.snapshot.try_lock() {
            Ok(snapshot) => *snapshot,
            Err(_) => return false,
        };
        let mut hasher = Sha256::new();
        hasher.update(snapshot.timestamp_ns.to_le_bytes());
        hasher.update(snapshot.payload);
        let computed = hasher.finalize();
        let mut difference = 0u8;
        for i in 0..32 {
            difference |= computed[i] ^ snapshot.causal_hash[i];
            difference |= snapshot.causal_hash[i] ^ expected_hash[i];
        }
        difference == 0
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::sync::{Arc, Barrier};

    fn digest(timestamp: u64, payload: [u8; LEDGER_TX_SIZE]) -> [u8; 32] {
        let mut hasher = Sha256::new();
        hasher.update(timestamp.to_le_bytes());
        hasher.update(payload);
        hasher.finalize().into()
    }

    #[test]
    fn held_writer_and_poison_fail_closed_without_waiting() {
        let manifest = CortexLedgerManifest::new(1, [0; 32], [0; LEDGER_TX_SIZE]);
        let guard = manifest.snapshot.lock().unwrap();
        assert!(!manifest.verify_integrity(&[0; 32]));
        assert!(!manifest.try_replace(2, [0; 32], [0; LEDGER_TX_SIZE]));
        drop(guard);
        let _ = std::panic::catch_unwind(|| {
            let _guard = manifest.snapshot.lock().unwrap();
            panic!("isolated writer failure");
        });
        assert!(!manifest.verify_integrity(&[0; 32]));
    }

    #[test]
    fn mismatched_payload_hash_and_timestamp_are_rejected() {
        let payload = [7; LEDGER_TX_SIZE];
        let hash = digest(1, payload);
        let manifest = CortexLedgerManifest::new(1, hash, payload);
        assert!(manifest.verify_integrity(&hash));
        assert!(!manifest.verify_integrity(&[0; 32]));
        assert!(manifest.try_replace(2, hash, payload));
        assert!(!manifest.verify_integrity(&hash));
        assert!(manifest.try_replace(1, hash, [8; LEDGER_TX_SIZE]));
        assert!(!manifest.verify_integrity(&hash));
    }

    #[test]
    fn concurrent_snapshot_stress() {
        let payload = [9; LEDGER_TX_SIZE];
        let hash = digest(1, payload);
        let manifest = Arc::new(CortexLedgerManifest::new(1, hash, payload));
        for _ in 0..100 {
            assert!(manifest.try_replace(1, hash, payload));
            assert!(manifest.verify_integrity(&hash));
        }
        let barrier = Arc::new(Barrier::new(8));
        std::thread::scope(|scope| {
            for worker in 0..8 {
                let manifest = Arc::clone(&manifest);
                let barrier = Arc::clone(&barrier);
                scope.spawn(move || {
                    barrier.wait();
                    for _ in 0..10_000 {
                        if worker < 4 {
                            manifest.try_replace(1, hash, payload);
                        } else {
                            // A contended read may fail, but no invalid hash may pass.
                            manifest.verify_integrity(&hash);
                            assert!(!manifest.verify_integrity(&[0; 32]));
                        }
                    }
                });
            }
        });
        assert!(manifest.verify_integrity(&hash));
    }
}
