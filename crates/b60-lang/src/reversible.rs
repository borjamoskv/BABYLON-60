// ============================================================================
// B60 REVERSIBLE COMPUTATION ENGINE (LIOUVILLE PRESERVING: DELTA S = 0)
// ============================================================================

pub const FRACTION_MOD: u32 = 60 * 60 * 60 * 60; // 12,960,000

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
#[repr(C, align(8))]
pub struct ReversibleRegister {
    pub seconds: u32,
    pub sexa_fraction: u32,
}

impl ReversibleRegister {
    pub fn new(seconds: u32, sexa_fraction: u32) -> Self {
        Self { seconds, sexa_fraction: sexa_fraction % FRACTION_MOD }
    }

    pub fn zero() -> Self {
        Self { seconds: 0, sexa_fraction: 0 }
    }
}

pub struct SexaToffoliGate;

impl SexaToffoliGate {
    #[inline(always)]
    pub fn apply(
        control_a: &ReversibleRegister,
        control_b: &ReversibleRegister,
        target_c: &mut ReversibleRegister,
    ) {
        let f_sec = (control_a.seconds.rotate_left(3) ^ control_b.seconds.rotate_right(5)) % 60;
        let f_frac = (control_a.sexa_fraction ^ control_b.sexa_fraction.rotate_left(7)) % FRACTION_MOD;

        target_c.seconds ^= f_sec;
        target_c.sexa_fraction ^= f_frac;
    }

    #[inline(always)]
    pub fn reverse(
        control_a: &ReversibleRegister,
        control_b: &ReversibleRegister,
        target_c: &mut ReversibleRegister,
    ) {
        Self::apply(control_a, control_b, target_c);
    }
}
