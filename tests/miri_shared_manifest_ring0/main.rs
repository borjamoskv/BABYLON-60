//! Exercise the real source with one publisher and concurrent pinned consumers.
#![allow(dead_code)]
#[path = "../../src/shared_manifest_core.rs"]
mod manifest;

use manifest::{PayloadSlot, SharedManifestRing0, POISON_BIT};
use std::sync::atomic::Ordering;
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
        shared.ffi_pin(shared.writer_ctl.control_word.load(Ordering::Acquire) >> 1);
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
    // A poison observation must remain terminal for both APIs.
    shared
        .writer_ctl
        .control_word
        .fetch_or(POISON_BIT, Ordering::AcqRel);
    assert!(shared.publish_and_audit(&payload(65), 65).is_err());
    assert!(shared.read_snapshot(&mut PayloadSlot::zeroed()).is_err());
}
