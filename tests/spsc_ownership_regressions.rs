use babylon60::SpscRingBuffer;
use std::sync::{
    atomic::{AtomicUsize, Ordering},
    Arc,
};

struct Tracked(Arc<AtomicUsize>);
impl Drop for Tracked {
    fn drop(&mut self) {
        self.0.fetch_add(1, Ordering::SeqCst);
    }
}
#[test]
fn pending_values_drop_once() {
    let count = Arc::new(AtomicUsize::new(0));
    let mut queue = SpscRingBuffer::<Tracked, 4>::new();
    for _ in 0..4 {
        assert!(queue.push(Tracked(count.clone())).is_ok());
    }
    drop(queue.pop().unwrap());
    assert_eq!(count.load(Ordering::SeqCst), 1);
    drop(queue);
    assert_eq!(count.load(Ordering::SeqCst), 4);
}
#[test]
fn full_returns_ownership() {
    let count = Arc::new(AtomicUsize::new(0));
    let mut queue = SpscRingBuffer::<Tracked, 1>::new();
    assert!(queue.pop().is_none());
    assert!(queue.push(Tracked(count.clone())).is_ok());
    drop(queue.push(Tracked(count.clone())).err().unwrap());
    assert_eq!(count.load(Ordering::SeqCst), 1);
    drop(queue);
    assert_eq!(count.load(Ordering::SeqCst), 2);
}
#[test]
fn endpoints_release_to_sequential_access() {
    let count = Arc::new(AtomicUsize::new(0));
    let mut queue = SpscRingBuffer::<Tracked, 2>::new();
    {
        let (mut producer, mut consumer) = queue.split();
        assert!(producer.push(Tracked(count.clone())).is_ok());
        drop(consumer.pop().unwrap());
        assert!(producer.push(Tracked(count.clone())).is_ok());
    }
    assert!(queue.push(Tracked(count.clone())).is_ok());
    drop(queue);
    assert_eq!(count.load(Ordering::SeqCst), 3);
}
#[test]
fn transfer_non_sync_payload_after_warmup() {
    use std::cell::Cell;
    let mut queue = SpscRingBuffer::<Cell<u64>, 8>::new();
    for index in 0..if cfg!(miri) { 16 } else { 512 } {
        assert!(queue.push(Cell::new(index)).is_ok());
        assert_eq!(queue.pop().unwrap().get(), index);
    }
    let count = if cfg!(miri) { 128 } else { 100_000 };
    let (mut producer, mut consumer) = queue.split();
    std::thread::scope(|scope| {
        scope.spawn(move || {
            for index in 0..count {
                let mut value = Cell::new(index);
                loop {
                    match producer.push(value) {
                        Ok(()) => break,
                        Err(returned) => {
                            value = returned;
                            std::thread::yield_now();
                        }
                    }
                }
            }
        });
        scope.spawn(move || {
            for index in 0..count {
                loop {
                    if let Some(value) = consumer.pop() {
                        assert_eq!(value.get(), index);
                        break;
                    }
                    std::thread::yield_now();
                }
            }
            assert!(consumer.pop().is_none());
        });
    });
    assert!(queue.is_empty());
}
#[test]
#[should_panic(expected = "non-zero power of two")]
fn zero_capacity_rejects() {
    let _ = SpscRingBuffer::<String, 0>::new();
}
#[test]
#[should_panic(expected = "non-zero power of two")]
fn non_power_of_two_capacity_rejects() {
    let _ = SpscRingBuffer::<String, 3>::new();
}

#[test]
fn legacy_wrapper_preserves_fifo_and_drops() {
    use babylon60::spsc::HardenedSpsc;
    let count = Arc::new(AtomicUsize::new(0));
    let mut queue = HardenedSpsc::<Tracked, 2>::new();
    assert!(queue.try_push(Tracked(count.clone())).is_ok());
    {
        let (mut producer, mut consumer) = queue.split();
        std::thread::scope(|scope| {
            scope.spawn(move || {
                assert!(producer.push(Tracked(count.clone())).is_ok());
            });
            drop(consumer.pop().unwrap());
        });
    }
    drop(queue.try_pop().unwrap());
    assert!(queue.try_pop().is_none());
}
