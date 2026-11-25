use eridu_infer::ipc::TelemetrySnapshot;
use eridu_infer::uma::{UmaAlignedBuffer, DARWIN_PAGE_SIZE};
use std::sync::{Arc, Barrier};

#[test]
fn allocation_boundaries_and_invalid_sizes() {
    for requested in [1, DARWIN_PAGE_SIZE - 1, DARWIN_PAGE_SIZE, DARWIN_PAGE_SIZE + 1] {
        let mut buffer = UmaAlignedBuffer::allocate(requested).unwrap();
        let capacity = buffer.len();
        assert!(capacity >= requested);
        assert_eq!(capacity % DARWIN_PAGE_SIZE, 0);
        assert_eq!(buffer.as_ptr() as usize % DARWIN_PAGE_SIZE, 0);
        assert_eq!(buffer.as_slice().len(), capacity);
        assert!(buffer.as_slice().iter().all(|byte| *byte == 0));
        buffer.as_mut_slice()[capacity - 1] = 42;
        assert_eq!(buffer.as_slice()[capacity - 1], 42);
    }
    for invalid in [0, usize::MAX, usize::MAX - DARWIN_PAGE_SIZE, isize::MAX as usize] {
        assert!(UmaAlignedBuffer::allocate(invalid).is_err());
    }
}

#[test]
fn concurrent_updates_preserve_counts_and_coherent_snapshots() {
    let snapshot = Arc::new(TelemetrySnapshot::new((0u64, 0u64)));
    // Warm the exact update/read path before the contended phase.
    for _ in 0..100 {
        snapshot.update(|value| { value.0 += 1; value.1 += 2; });
        let value = snapshot.read();
        assert_eq!(value.1, value.0 * 2);
    }
    snapshot.write((0, 0));
    let barrier = Arc::new(Barrier::new(8));
    std::thread::scope(|scope| {
        for worker in 0..8 {
            let snapshot = Arc::clone(&snapshot);
            let barrier = Arc::clone(&barrier);
            scope.spawn(move || {
                barrier.wait();
                for _ in 0..10_000 {
                    if worker < 4 {
                        snapshot.update(|value| { value.0 += 1; value.1 += 2; });
                    } else {
                        let value = snapshot.read();
                        assert_eq!(value.1, value.0 * 2);
                    }
                }
            });
        }
    });
    assert_eq!(snapshot.read(), (40_000, 80_000));
}
