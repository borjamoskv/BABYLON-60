//! Dependency-free Miri probe of the actual production module, not a replica.
//! Instrumentation is disabled, as in the default production feature profile.
#[macro_export]
macro_rules! probe_start {
    () => {
        ()
    };
}
#[macro_export]
macro_rules! probe_end {
    ($label:expr, $start:expr) => {
        ()
    };
}

#[path = "../../../src/spsc_ring.rs"]
pub mod spsc_ring;
pub use spsc_ring::SpscRingBuffer;

#[path = "../../../src/spsc.rs"]
pub mod spsc;
