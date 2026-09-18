// ============================================================================
// BABYLON-60 v4.0 Sovereign Hardened
// █ AUTOCOGNITION-Ω | STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026
// ============================================================================

/// Instruction cycle counter within the VM. Strictly monotonic.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub struct LogicalClock(pub u64);

/// Exact Q32.32 Fixed-Point Time representation (F60 domain).
/// Higher 32 bits represent integer seconds/units, lower 32 bits represent fractional units.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub struct SimulationClock(pub u64);

impl LogicalClock {
    pub const fn new(ticks: u64) -> Self { Self(ticks) }
    pub fn tick(self) -> Self { Self(self.0.saturating_add(1)) }
}

impl SimulationClock {
    pub const SCALE: u64 = 1 << 32;

    pub const fn new(units: u64) -> Self { Self(units) }
    
    /// Constructs SimulationClock from whole integer seconds/units.
    pub const fn from_secs(secs: u64) -> Self {
        Self(secs.saturating_mul(Self::SCALE))
    }

    /// Constructs SimulationClock from a raw Q32.32 fixed-point value.
    pub const fn from_raw(raw: u64) -> Self {
        Self(raw)
    }

    pub fn advance(self, units: u64) -> Self { Self(self.0.saturating_add(units)) }

    /// Returns the integer part (seconds).
    pub fn as_secs(self) -> u64 {
        self.0 / Self::SCALE
    }

    /// Returns fractional part as strictly integer milliseconds (0..999) to avoid FPU contamination.
    pub fn subsec_millis(self) -> u64 {
        let fraction = self.0 % Self::SCALE;
        (fraction * 1000) / Self::SCALE
    }

    /// Adds two fixed point clocks with saturation.
    pub fn add_fixed(self, rhs: SimulationClock) -> Self {
        Self(self.0.saturating_add(rhs.0))
    }

    /// Subtracts two fixed point clocks with saturation.
    pub fn sub_fixed(self, rhs: SimulationClock) -> Self {
        Self(self.0.saturating_sub(rhs.0))
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_simulation_clock_fixed_point() {
        let t1 = SimulationClock::from_secs(10);
        let t2 = SimulationClock::from_secs(5);
        let sum = t1.add_fixed(t2);
        assert_eq!(sum.as_secs(), 15);
        assert_eq!(sum.sub_fixed(t2).as_secs(), 10);
    }
}

