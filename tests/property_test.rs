// C5-REAL EXERGY CERTIFIED — BABYLON-60 — PROPERTY-BASED TESTS (proptest)

#![cfg(not(loom))]

use babylon_60::manifest::{SharedManifest, RUNNING};
use babylon_60::seqlock::{publish, read};
use babylon_60::thermodynamics::{is_entelecheia, is_dynamis, is_valid_writer_transition};
use proptest::prelude::*;
use std::sync::atomic::{AtomicU32, AtomicU64};

fn new_manifest() -> &'static SharedManifest {
    let m = Box::new(SharedManifest {
        status_flag: AtomicU32::new(RUNNING),
        seq: AtomicU32::new(0),
        epoch_id: AtomicU64::new(0),
        payload_hash: [
            AtomicU64::new(0),
            AtomicU64::new(0),
            AtomicU64::new(0),
            AtomicU64::new(0),
        ],
        _padding: [0u8; 16],
    });
    Box::leak(m)
}

proptest! {
    #[test]
    fn prop_seqlock_publish_read_consistency(epoch in 0u64..10_000_000, h0 in any::<u64>(), h1 in any::<u64>(), h2 in any::<u64>(), h3 in any::<u64>()) {
        let m = new_manifest();
        let hash = [h0, h1, h2, h3];
        publish(m, epoch, &hash);
        let read_result = read(m);
        prop_assert!(read_result.is_some());
        let (read_epoch, read_hash) = read_result.unwrap();
        prop_assert_eq!(read_epoch, epoch);
        prop_assert_eq!(read_hash, hash);
    }

    #[test]
    fn prop_bisimulation_partitioning(seq in any::<u32>()) {
        let entelecheia = is_entelecheia(seq);
        let dynamis = is_dynamis(seq);
        prop_assert_ne!(entelecheia, dynamis);
    }

    #[test]
    fn prop_valid_writer_transitions(before in any::<u32>()) {
        let valid_after = before.wrapping_add(2);
        if is_entelecheia(valid_after) {
            prop_assert!(is_valid_writer_transition(before, valid_after));
        } else {
            prop_assert!(!is_valid_writer_transition(before, valid_after));
        }
        let invalid_after = before.wrapping_add(1);
        prop_assert!(!is_valid_writer_transition(before, invalid_after));
    }
}
