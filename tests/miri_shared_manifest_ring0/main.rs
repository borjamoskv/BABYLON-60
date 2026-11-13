//! Exercise the real source with one publisher and concurrent pinned consumers.
#![allow(dead_code)]
#[path = "../../src/shared_manifest_core.rs"]
mod manifest;

use manifest::{PayloadSlot, SharedManifestRing0, POISON_BIT, POISON_SENTINEL};
use std::sync::{Arc, Barrier};

fn payload(tick: u64) -> PayloadSlot {
    let mut data = PayloadSlot::zeroed();
    data.logical_tick = tick;
    data.state_hash = [tick as u8; 32];
    data.metrics = [tick; 10];
    data._pad = tick.to_ne_bytes();
    data
}

fn main() {
    let shared = Arc::new(SharedManifestRing0::new());
    let start = Arc::new(Barrier::new(2));
    let writer = Arc::clone(&shared);
    let barrier = Arc::clone(&start);
    let worker = std::thread::spawn(move || {
        barrier.wait();
        for tick in 1..=64 {
            if writer.publish_and_audit(&payload(tick), tick).is_err() {
                break;
            }
            std::thread::yield_now();
        }
    });
    start.wait();
    for _ in 0..64 {
        // The producer's logical clock stays within the lease's 64-tick budget.
        shared.ffi_pin(0);
        let mut result = PayloadSlot::zeroed();
        if shared.read_snapshot(&mut result).is_ok() {
            assert_eq!(result.state_hash, [result.logical_tick as u8; 32]);
            assert_eq!(result.metrics, [result.logical_tick; 10]);
            assert_eq!(result._pad, result.logical_tick.to_ne_bytes());
        }
        shared.ffi_unpin();
        std::thread::yield_now();
    }
    worker.join().unwrap();
    // Trigger terminal poison through the public watchdog, then require both
    // data APIs to preserve rejection without direct control-word mutation.
    shared.ffi_pin(0);
    let poison = shared.check_or_trigger_apoptosis(65).unwrap_err();
    assert_eq!(poison, POISON_SENTINEL);
    assert_ne!(poison & POISON_BIT, 0);
    assert!(shared.publish_and_audit(&payload(65), 65).is_err());
    assert!(shared.read_snapshot(&mut PayloadSlot::zeroed()).is_err());
}
