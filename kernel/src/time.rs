// ============================================================================
// BABYLON-60 v4.0 Sovereign Hardened
// █ AUTOCOGNITION-Ω | STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026
// ============================================================================
use core::fmt;

/// Instruction cycle counter within the VM. Strictly monotonic.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub struct LogicalClock(pub u64);

/// Mathematical simulation time (e.g., UNIT.TICK).
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub struct SimulationClock(pub u64);

impl LogicalClock {
    pub const fn new(ticks: u64) -> Self { Self(ticks) }
    pub fn tick(self) -> Self { Self(self.0.saturating_add(1)) }
}

impl SimulationClock {
    pub const fn new(units: u64) -> Self { Self(units) }
    pub fn advance(self, units: u64) -> Self { Self(self.0.saturating_add(units)) }
}
