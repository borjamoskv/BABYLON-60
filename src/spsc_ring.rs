//! Bounded SPSC storage with unique producer and consumer capabilities.
use core::cell::{Cell, UnsafeCell};
use core::marker::PhantomData;
use core::mem::MaybeUninit;
use core::sync::atomic::{AtomicUsize, Ordering};

/// Storage for a non-zero power-of-two number of owned values.
/// Indices cannot be forged by safe callers.
/// ```compile_fail
/// let ring = babylon60::SpscRingBuffer::<u64, 8>::new();
/// ring.head.store(1, std::sync::atomic::Ordering::Release);
/// ```
/// Endpoints cannot be shared to create additional producers.
/// ```compile_fail
/// let mut ring = babylon60::SpscRingBuffer::<u64, 8>::new();
/// let (producer, _) = ring.split();
/// std::thread::scope(|s| { s.spawn(|| { let _ = &producer; }); });
/// ```
#[repr(C, align(64))]
pub struct SpscRingBuffer<T, const CAP: usize = 1024> {
    head: AtomicUsize,
    _pad1: [u8; 56],
    tail: AtomicUsize,
    _pad2: [u8; 56],
    ring: [UnsafeCell<MaybeUninit<T>>; CAP],
}

// SAFETY: only unique endpoints access slots. Release/acquire transfers payload
// ownership; no reference to T escapes. Hence T: Send, not T: Sync, is required.
unsafe impl<T: Send, const CAP: usize> Sync for SpscRingBuffer<T, CAP> {}

/// Non-cloneable producer, movable between threads but not shareable.
pub struct Producer<'a, T, const CAP: usize = 1024> {
    queue: &'a SpscRingBuffer<T, CAP>,
    _not_sync: PhantomData<Cell<()>>,
}
/// Non-cloneable consumer, which cannot outlive storage.
pub struct Consumer<'a, T, const CAP: usize = 1024> {
    queue: &'a SpscRingBuffer<T, CAP>,
    _not_sync: PhantomData<Cell<()>>,
}

impl<T, const CAP: usize> SpscRingBuffer<T, CAP> {
    /// Construct fixed storage; reject capacities incompatible with counter wrap.
    pub const fn new() -> Self {
        assert!(
            CAP.is_power_of_two(),
            "SPSC capacity must be a non-zero power of two"
        );
        Self {
            head: AtomicUsize::new(0),
            _pad1: [0; 56],
            tail: AtomicUsize::new(0),
            _pad2: [0; 56],
            ring: [const { UnsafeCell::new(MaybeUninit::uninit()) }; CAP],
        }
    }

    /// Create exactly one endpoint of each kind.
    ///
    /// ~~~compile_fail
    /// use babylon60::SpscRingBuffer;
    /// let mut queue = SpscRingBuffer::<u64, 8>::new();
    /// let (mut producer, _) = queue.split();
    /// let _second_pair = queue.split();
    /// producer.push(1).unwrap();
    /// ~~~
    pub fn split(&mut self) -> (Producer<'_, T, CAP>, Consumer<'_, T, CAP>) {
        (
            Producer {
                queue: self,
                _not_sync: PhantomData,
            },
            Consumer {
                queue: self,
                _not_sync: PhantomData,
            },
        )
    }
    /// Observational length; remains bounded during concurrent sampling.
    pub fn len(&self) -> usize {
        let tail = self.tail.load(Ordering::Acquire);
        let head = self.head.load(Ordering::Acquire);
        head.wrapping_sub(tail).min(CAP)
    }
    /// Observational empty state.
    pub fn is_empty(&self) -> bool {
        self.len() == 0
    }
    /// Observational full state.
    pub fn is_full(&self) -> bool {
        self.len() == CAP
    }
    /// Fixed capacity.
    pub const fn capacity(&self) -> usize {
        CAP
    }

    /// Exclusive sequential push. Shared references cannot mutate storage.
    ///
    /// ~~~compile_fail
    /// use babylon60::SpscRingBuffer;
    /// let queue = SpscRingBuffer::<String, 8>::new();
    /// (&queue).push(String::from("shared mutation is forbidden"));
    /// ~~~
    pub fn push(&mut self, value: T) -> Result<(), T> {
        // SAFETY: exclusive borrow excludes all other endpoints.
        unsafe { self.push_unique(value) }
    }
    /// Exclusive sequential pop.
    pub fn pop(&mut self) -> Option<T> {
        // SAFETY: exclusive borrow excludes all other endpoints.
        unsafe { self.pop_unique() }
    }
    // Caller must own the unique producer capability.
    unsafe fn push_unique(&self, value: T) -> Result<(), T> {
        let _probe_start = crate::probe_start!();
        let head = self.head.load(Ordering::Relaxed);
        let tail = self.tail.load(Ordering::Acquire);
        if head.wrapping_sub(tail) >= CAP {
            return Err(value);
        }
        // SAFETY: slot is vacant and owned by the sole producer. Acquire of
        // tail observes completion of the previous consumer read.
        unsafe {
            (*self.ring[head & (CAP - 1)].get()).write(value);
        }
        self.head.store(head.wrapping_add(1), Ordering::Release);
        crate::probe_end!("spsc_push", _probe_start);
        Ok(())
    }
    // Caller must own the unique consumer capability.
    unsafe fn pop_unique(&self) -> Option<T> {
        let _probe_start = crate::probe_start!();
        let tail = self.tail.load(Ordering::Relaxed);
        let head = self.head.load(Ordering::Acquire);
        if tail == head {
            return None;
        }
        // SAFETY: acquire observes initialization. This consumer alone moves
        // the payload, then publishes vacancy for reuse.
        let value = unsafe { (*self.ring[tail & (CAP - 1)].get()).assume_init_read() };
        self.tail.store(tail.wrapping_add(1), Ordering::Release);
        crate::probe_end!("spsc_pop", _probe_start);
        Some(value)
    }
}
impl<T, const CAP: usize> Producer<'_, T, CAP> {
    /// Publish or return ownership if full.
    pub fn push(&mut self, value: T) -> Result<(), T> {
        // SAFETY: this non-cloneable capability is borrowed exclusively.
        unsafe { self.queue.push_unique(value) }
    }
}
impl<T, const CAP: usize> Consumer<'_, T, CAP> {
    /// Move the next initialized value out.
    pub fn pop(&mut self) -> Option<T> {
        // SAFETY: this non-cloneable capability is borrowed exclusively.
        unsafe { self.queue.pop_unique() }
    }
}
impl<T, const CAP: usize> Default for SpscRingBuffer<T, CAP> {
    fn default() -> Self {
        Self::new()
    }
}
impl<T, const CAP: usize> Drop for SpscRingBuffer<T, CAP> {
    fn drop(&mut self) {
        // Endpoint borrows ended; each remaining slot is exclusively owned.
        let head = *self.head.get_mut();
        let mut tail = *self.tail.get_mut();
        while tail != head {
            unsafe {
                self.ring[tail & (CAP - 1)].get_mut().assume_init_drop();
            }
            tail = tail.wrapping_add(1);
        }
    }
}
#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn counter_wrap_keeps_fifo() {
        let mut queue = SpscRingBuffer::<String, 4>::new();
        *queue.head.get_mut() = usize::MAX - 1;
        *queue.tail.get_mut() = usize::MAX - 1;
        for index in 0..4 {
            queue.push(index.to_string()).unwrap();
        }
        assert_eq!(queue.len(), 4);
        for index in 0..4 {
            assert_eq!(queue.pop(), Some(index.to_string()));
        }
        assert!(queue.pop().is_none());
    }
}
