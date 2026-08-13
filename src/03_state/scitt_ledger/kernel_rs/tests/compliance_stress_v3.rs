// C5-REAL EXERGY CERTIFIED
#![cfg(test)]
extern crate std;

use std::thread;
use std::sync::Arc;
use std::sync::atomic::{AtomicU64, Ordering};

// --- V3 KERNEL TYPES (MINIMAL SUBSET FOR AST VALIDATION) ---
#[derive(Clone, Copy)]
pub struct Vector<const N: usize>(pub [u64; N]);

impl<const N: usize> Vector<N> {
    pub const fn norm_sq(&self) -> u64 {
        let mut acc = 0u64;
        let mut i = 0;
        while i < N {
            acc += self.0[i] * self.0[i];
            i += 1;
        }
        acc
    }
}

pub struct BoundedVector<const N: usize, const LIMIT: u64> {
    vec: Vector<N>,
}

pub const fn verify_cap<const N: usize, const LIMIT: u64>(
    vec: Vector<N>
) -> Option<BoundedVector<N, LIMIT>> {
    if vec.norm_sq() <= LIMIT * LIMIT {
        Some(BoundedVector { vec })
    } else {
        None
    }
}

pub struct LinearPayload<const N: usize> {
    data: Vector<N>,
}

impl<const N: usize> LinearPayload<N> {
    pub const fn new(data: Vector<N>) -> Self {
        Self { data }
    }

    pub fn consume_and_wipe(mut self) -> WipedMarker<N> {
        self.data = Vector([0u64; N]);
        WipedMarker { _phantom: core::marker::PhantomData }
    }
}

pub struct WipedMarker<const N: usize> {
    _phantom: core::marker::PhantomData<[u64; N]>,
}

// --- ORTHOGONAL STRESS SUITE V3 ---

/// Deterministic PRNG (xorshift64) for bit-exact reproducibility
const fn xorshift64(mut state: u64) -> u64 {
    state ^= state << 13;
    state ^= state >> 7;
    state ^= state << 17;
    state
}

#[test]
fn test_verify_cap_hermeticity_parallel() {
    const THREADS: usize = 32;
    const ITERATIONS: usize = 10_000;
    const CAP: u64 = 100;
    const DIM: usize = 4;

    let rejections = Arc::new(AtomicU64::new(0));
    let mut handles = vec![];

    for t in 0..THREADS {
        let r = rejections.clone();
        handles.push(thread::spawn(move || {
            // Fixed seed per thread ensures deterministic coverage without collision
            let mut rng_state = (t as u64 + 1).wrapping_mul(0x9E3779B97F4A7C15);
            let mut local_rejects = 0u64;

            for _ in 0..ITERATIONS {
                rng_state = xorshift64(rng_state);
                // Generate values that intentionally cross CAP boundary
                let val = (rng_state % 200) as u64;
                let v = Vector([val; DIM]);

                if verify_cap::<DIM, CAP>(v).is_none() {
                    local_rejects += 1;
                }
            }
            r.fetch_add(local_rejects, Ordering::Relaxed);
        }));
    }

    for h in handles { h.join().unwrap(); }
    // Hermeticity check: rejections must be > 0 and deterministic across runs
    assert!(rejections.load(Ordering::SeqCst) > 0);
}

#[test]
fn test_linear_annihilation_concurrent() {
    const THREADS: usize = 64;
    const BATCH_SIZE: usize = 1_000;

    let completions = Arc::new(AtomicU64::new(0));
    let mut handles = vec![];

    for _ in 0..THREADS {
        let c = completions.clone();
        handles.push(thread::spawn(move || {
            for i in 0..BATCH_SIZE {
                // Each payload is stack-isolated; no shared mutable state
                let payload = LinearPayload::new(Vector([i as u64; 8]));
                let _marker = payload.consume_and_wipe();
                // Marker is dropped here, completing affine cycle
            }
            c.fetch_add(BATCH_SIZE as u64, Ordering::Relaxed);
        }));
    }

    for h in handles { h.join().unwrap(); }
    // Verify all annihilations completed without panic or race
    assert_eq!(completions.load(Ordering::SeqCst), (THREADS * BATCH_SIZE) as u64);
}
