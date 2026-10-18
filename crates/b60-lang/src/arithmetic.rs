// ============================================================================
// B60 EXACT SEXAGESIMAL ARITHMETIC (Q60)
// ============================================================================

pub const FRACTION_BASE: u64 = 60 * 60 * 60 * 60; // 12,960,000 subdivisiones (0.077 µs)

#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord)]
pub struct Tick60 {
    pub seconds: u64,
    pub sexa_units: u64,
}

impl Tick60 {
    pub fn zero() -> Self {
        Tick60 { seconds: 0, sexa_units: 0 }
    }

    pub fn new(seconds: u64, sexa_units: u64) -> Self {
        let carry = sexa_units / FRACTION_BASE;
        Tick60 {
            seconds: seconds + carry,
            sexa_units: sexa_units % FRACTION_BASE,
        }
    }

    pub fn from_rational(seconds: u64, num: u64, denom: u64) -> Self {
        assert!(FRACTION_BASE.is_multiple_of(denom), "Denominador no admisible en Q60");
        let factor = FRACTION_BASE / denom;
        Tick60 {
            seconds,
            sexa_units: num * factor,
        }
    }

    pub fn add(&self, other: &Tick60) -> Self {
        let total_units = self.sexa_units + other.sexa_units;
        let carry_secs = total_units / FRACTION_BASE;
        let rem_units = total_units % FRACTION_BASE;
        Tick60 {
            seconds: self.seconds + other.seconds + carry_secs,
            sexa_units: rem_units,
        }
    }

    pub fn sub(&self, other: &Tick60) -> Result<Self, &'static str> {
        if self.seconds < other.seconds || (self.seconds == other.seconds && self.sexa_units < other.sexa_units) {
            return Err("Underflow sexagesimal: el tiempo no puede ser negativo");
        }
        let (secs, units) = if self.sexa_units >= other.sexa_units {
            (self.seconds - other.seconds, self.sexa_units - other.sexa_units)
        } else {
            (self.seconds - other.seconds - 1, (FRACTION_BASE + self.sexa_units) - other.sexa_units)
        };
        Ok(Tick60 { seconds: secs, sexa_units: units })
    }
}
