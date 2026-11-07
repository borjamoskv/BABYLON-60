//! Compatibility API backed by the canonical SPSC storage.
pub use crate::spsc_ring::{Consumer, Producer, SpscRingBuffer};

/// Legacy name; ownership and memory ordering live in one implementation.
pub struct HardenedSpsc<T, const CAP: usize>(SpscRingBuffer<T, CAP>);

impl<T, const CAP: usize> HardenedSpsc<T, CAP> {
    /// Construct storage with a power-of-two capacity greater than one.
    pub const fn new() -> Self {
        assert!(CAP > 1, "CAP must be greater than one");
        Self(SpscRingBuffer::new())
    }
    /// Insert using exclusive sequential access.
    pub fn try_push(&mut self, value: T) -> Result<(), T> {
        self.0.push(value)
    }
    /// Remove using exclusive sequential access.
    pub fn try_pop(&mut self) -> Option<T> {
        self.0.pop()
    }
    /// Borrow one unique producer and one unique consumer.
    pub fn split(&mut self) -> (Producer<'_, T, CAP>, Consumer<'_, T, CAP>) {
        self.0.split()
    }
}
impl<T, const CAP: usize> Default for HardenedSpsc<T, CAP> {
    fn default() -> Self {
        Self::new()
    }
}
