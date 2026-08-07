// C5-REAL EXERGY CERTIFIED

use std::fmt;
use std::ops::{Add, Sub};

/// A Sexagesimal Exact Scheduler representation (`F60`).
/// Avoids catastrophic drift of f64 when calculating intervals.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord)]
pub struct F60 {
    ticks: u64,
}

impl F60 {
    pub const TICKS_PER_UNIT: u64 = 60;

    pub fn new(ticks: u64) -> Self {
        F60 { ticks }
    }

    pub fn from_fraction(numerator: u64, denominator: u64) -> Option<Self> {
        if denominator == 0 || (numerator * Self::TICKS_PER_UNIT) % denominator != 0 {
            return None; // Non-exact representation in base 60
        }
        Some(F60 {
            ticks: (numerator * Self::TICKS_PER_UNIT) / denominator,
        })
    }

    pub fn as_ticks(&self) -> u64 {
        self.ticks
    }
}

impl Add for F60 {
    type Output = Self;
    fn add(self, other: Self) -> Self::Output {
        F60 { ticks: self.ticks + other.ticks }
    }
}

impl Sub for F60 {
    type Output = Self;
    fn sub(self, other: Self) -> Self::Output {
        F60 { ticks: self.ticks.saturating_sub(other.ticks) }
    }
}

impl fmt::Display for F60 {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "{};{}", self.ticks / Self::TICKS_PER_UNIT, self.ticks % Self::TICKS_PER_UNIT)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_f60_exactness() {
        // 1/3 of an hour is exactly 0;20
        let third = F60::from_fraction(1, 3).unwrap();
        assert_eq!(third.as_ticks(), 20);
        assert_eq!(format!("{}", third), "0;20");
    }
}
