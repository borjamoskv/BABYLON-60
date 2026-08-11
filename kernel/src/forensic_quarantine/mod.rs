// ============================================================================
// BABYLON-60 v4.0 | FORENSIC QUARANTINE (WORM)
// ============================================================================
//! The Write Once Read Many (WORM) black box quarantine system.
//! In the event of a CRITICAL HALT (e.g., Causal Inversion attack detection),
//! the kernel freezes the state here rather than purging it, preserving
//! a cryptographic snapshot of the failure for regulatory auditing.

use alloc::vec::Vec;
use crate::scheduler::time::SimulationClock;

/// Frozen state of the kernel at the moment of halt.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct QuarantineSnapshot {
    pub timestamp: SimulationClock,
    pub causal_hash: [u8; 32],
    pub memory_dump: Vec<u8>,
    pub snapshot_checksum: u64,
}

impl QuarantineSnapshot {
    /// Freezes state immutably into a QuarantineSnapshot.
    pub fn freeze(timestamp: SimulationClock, causal_hash: [u8; 32], memory_dump: Vec<u8>) -> Self {
        let checksum = Self::compute_checksum(timestamp.0, &causal_hash, &memory_dump);
        Self {
            timestamp,
            causal_hash,
            memory_dump,
            snapshot_checksum: checksum,
        }
    }

    /// Verifies the cryptographic integrity of the frozen snapshot.
    pub fn verify_integrity(&self) -> bool {
        let expected = Self::compute_checksum(self.timestamp.0, &self.causal_hash, &self.memory_dump);
        expected == self.snapshot_checksum
    }

    fn compute_checksum(ts: u64, hash: &[u8; 32], dump: &[u8]) -> u64 {
        let mut s = 0xcbf29ce484222325u64;
        let prime = 0x100000001b3u64;

        for byte in ts.to_le_bytes() {
            s ^= byte as u64;
            s = s.wrapping_mul(prime);
        }
        for byte in hash {
            s ^= *byte as u64;
            s = s.wrapping_mul(prime);
        }
        for byte in dump {
            s ^= *byte as u64;
            s = s.wrapping_mul(prime);
        }
        s
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use alloc::vec;

    #[test]
    fn test_quarantine_snapshot_integrity() {
        let ts = SimulationClock::from_secs(100);
        let hash = [7u8; 32];
        let dump = vec![1, 2, 3, 4, 5];
        let snapshot = QuarantineSnapshot::freeze(ts, hash, dump);

        assert!(snapshot.verify_integrity());
        
        let mut tampered = snapshot.clone();
        tampered.memory_dump[0] = 99;
        assert!(!tampered.verify_integrity());
    }
}

