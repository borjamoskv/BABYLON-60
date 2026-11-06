#![cfg(feature = "larsa-bft")]

use babylon60::ffi_oracle::{b60_eval_trace, b60_register_z3_callback};
use babylon60::manifest::{POISONED, RUNNING};
use std::sync::atomic::{AtomicU32, Ordering};

// Isolated C callback fixture for routing/error tests, not solver certification.
static Z3_RESULT: AtomicU32 = AtomicU32::new(0);
extern "C" fn z3_result(_: *const u8, _: usize) -> u32 {
    Z3_RESULT.load(Ordering::Relaxed)
}
#[allow(clippy::identity_op)]
fn trace(second_action: u8) -> Vec<u8> {
    [
        0_u64 | (1 << 8) | (1 << 32),
        u64::from(second_action) | (1 << 8) | (2 << 32),
    ]
    .into_iter()
    .flat_map(u64::to_le_bytes)
    .collect()
}
fn evaluate(bytes: &[u8]) -> u32 {
    unsafe { b60_eval_trace(bytes.as_ptr(), bytes.len()) }
}

#[test]
fn c_api_rejections_do_not_validate_or_block_later_requests() {
    b60_register_z3_callback(z3_result);
    let valid = trace(1);
    let invalid_state = trace(0);
    assert_eq!(evaluate(&valid), RUNNING);
    // Lean/native state verifier rejects after Z3 accepts.
    assert_eq!(evaluate(&invalid_state), POISONED);
    assert_eq!(evaluate(&valid), RUNNING);
    for failure in [2, 1, u32::MAX] {
        Z3_RESULT.store(failure, Ordering::Relaxed);
        assert_eq!(evaluate(&valid), POISONED);
        Z3_RESULT.store(0, Ordering::Relaxed);
        assert_eq!(evaluate(&valid), RUNNING);
    }
    assert_eq!(unsafe { b60_eval_trace(std::ptr::null(), 8) }, POISONED);
    assert_eq!(unsafe { b60_eval_trace(valid.as_ptr(), 0) }, POISONED);
    assert_eq!(evaluate(&valid), RUNNING);

    // Warmup before same-length calls overlap on the actual C entrypoint.
    for _ in 0..32 {
        assert_eq!(evaluate(&valid), RUNNING);
        assert_eq!(evaluate(&invalid_state), POISONED);
    }
    std::thread::scope(|scope| {
        for _ in 0..4 {
            let valid = &valid;
            let invalid_state = &invalid_state;
            scope.spawn(move || {
                for _ in 0..128 {
                    assert_eq!(evaluate(valid), RUNNING);
                    assert_eq!(evaluate(invalid_state), POISONED);
                }
            });
        }
    });
    assert_eq!(evaluate(&valid), RUNNING);
}
