use crate::constants::*;
use crate::errors::ConfigurationError;
use crate::types::*;
use soroban_sdk::{panic_with_error, Address, Env, U256};

/// Uses U256 for overflow safety
pub fn wad_mul(env: &Env, a: u128, b: u128) -> Result<u128, crate::KineticRouterError> {
    let a_u256 = U256::from_u128(env, a);
    let b_u256 = U256::from_u128(env, b);
    let half_wad_u256 = U256::from_u128(env, HALF_WAD);
    let wad_u256 = U256::from_u128(env, WAD);

    let product = a_u256.mul(&b_u256);
    let numerator = product.add(&half_wad_u256);
    let result = numerator.div(&wad_u256);

    result.to_u128().ok_or(crate::KineticRouterError::MathOverflow)
}

pub fn wad_div(env: &Env, a: u128, b: u128) -> Result<u128, crate::KineticRouterError> {
    if b == 0 {
        return Err(crate::KineticRouterError::MathOverflow);
    }

    let a_u256 = U256::from_u128(env, a);
    let b_u256 = U256::from_u128(env, b);
    let wad_u256 = U256::from_u128(env, WAD);
    let half_b_u256 = b_u256.div(&U256::from_u32(env, 2));

    let numerator = a_u256.mul(&wad_u256).add(&half_b_u256);
    let result = numerator.div(&b_u256);

    result.to_u128().ok_or(crate::KineticRouterError::MathOverflow)
}

/// Uses U256 for overflow safety
pub fn ray_mul(env: &Env, a: u128, b: u128) -> Result<u128, crate::KineticRouterError> {
    let a_u256 = U256::from_u128(env, a);
    let b_u256 = U256::from_u128(env, b);
    let half_ray_u256 = U256::from_u128(env, HALF_RAY);
    let ray_u256 = U256::from_u128(env, RAY);

    let product = a_u256.mul(&b_u256);
    let numerator = product.add(&half_ray_u256);
    let result = numerator.div(&ray_u256);

    result.to_u128().ok_or(crate::KineticRouterError::MathOverflow)
}

/// WP-C1: Floor-rounding ray_mul (truncation, no HALF_RAY bias).
/// Use when the protocol must never overpay (e.g. token transfers out).
pub fn ray_mul_down(env: &Env, a: u128, b: u128) -> Result<u128, crate::KineticRouterError> {
    let a_u256 = U256::from_u128(env, a);
    let b_u256 = U256::from_u128(env, b);
    let ray_u256 = U256::from_u128(env, RAY);

    let result = a_u256.mul(&b_u256).div(&ray_u256);

    result.to_u128().ok_or(crate::KineticRouterError::MathOverflow)
}

pub fn ray_div(env: &Env, a: u128, b: u128) -> Result<u128, crate::KineticRouterError> {
    if b == 0 {
        return Err(crate::KineticRouterError::MathOverflow);
    }

    let a_u256 = U256::from_u128(env, a);
    let b_u256 = U256::from_u128(env, b);
    let ray_u256 = U256::from_u128(env, RAY);
    let half_b_u256 = b_u256.div(&U256::from_u32(env, 2));

    let numerator = a_u256.mul(&ray_u256).add(&half_b_u256);
    let result = numerator.div(&b_u256);

    result.to_u128().ok_or(crate::KineticRouterError::MathOverflow)
}

/// M-14
pub fn ray_div_down(env: &Env, a: u128, b: u128) -> Result<u128, crate::KineticRouterError> {
    if b == 0 {
        return Err(crate::KineticRouterError::MathOverflow);
    }

    let a_u256 = U256::from_u128(env, a);
    let b_u256 = U256::from_u128(env, b);
    let ray_u256 = U256::from_u128(env, RAY);

    // No rounding bias: pure truncation
    let result = a_u256.mul(&ray_u256).div(&b_u256);

    result.to_u128().ok_or(crate::KineticRouterError::MathOverflow)
}

/// M-14
pub fn ray_div_up(env: &Env, a: u128, b: u128) -> Result<u128, crate::KineticRouterError> {
    if b == 0 {
        return Err(crate::KineticRouterError::MathOverflow);
    }

    let a_u256 = U256::from_u128(env, a);
    let b_u256 = U256::from_u128(env, b);
    let ray_u256 = U256::from_u128(env, RAY);
    let one = U256::from_u128(env, 1u128);

    // Ceiling division: (a * RAY + b - 1) / b
    let numerator = a_u256.mul(&ray_u256).add(&b_u256).sub(&one);
    let result = numerator.div(&b_u256);

    result.to_u128().ok_or(crate::KineticRouterError::MathOverflow)
}

pub fn wad_to_ray(a: u128) -> Result<u128, crate::KineticRouterError> {
    a.checked_mul(RAY_WAD_RATIO).ok_or(crate::KineticRouterError::MathOverflow)
}

pub fn ray_to_wad(a: u128) -> Result<u128, crate::KineticRouterError> {
    a.checked_add(HALF_RAY_WAD_RATIO)
        .and_then(|sum| sum.checked_div(RAY_WAD_RATIO))
        .ok_or(crate::KineticRouterError::MathOverflow)
}

pub fn percent_mul(value: u128, percentage: u128) -> Result<u128, crate::KineticRouterError> {
    value
        .checked_mul(percentage)
        .and_then(|prod| prod.checked_add(HALF_BASIS_POINTS))
        .and_then(|sum| sum.checked_div(BASIS_POINTS_MULTIPLIER))
        .ok_or(crate::KineticRouterError::MathOverflow)
}

/// L-10
pub fn percent_mul_up(value: u128, percentage: u128) -> Result<u128, crate::KineticRouterError> {
    value
        .checked_mul(percentage)
        .and_then(|prod| prod.checked_add(BASIS_POINTS_MULTIPLIER - 1))
        .and_then(|sum| sum.checked_div(BASIS_POINTS_MULTIPLIER))
        .ok_or(crate::KineticRouterError::MathOverflow)
}

pub fn percent_div(value: u128, percentage: u128) -> Result<u128, crate::KineticRouterError> {
    if percentage == 0 {
        return Err(crate::KineticRouterError::MathOverflow);
    }
    let half_percentage = percentage / 2; // Safe: percentage > 0 guaranteed
    value
        .checked_mul(BASIS_POINTS_MULTIPLIER)
        .and_then(|prod| prod.checked_add(half_percentage))
        .and_then(|sum| sum.checked_div(percentage))
        .ok_or(crate::KineticRouterError::MathOverflow)
}

pub fn calculate_compound_interest(
    env: &Env,
    rate: u128,
    last_update_timestamp: u64,
    current_timestamp: u64,
) -> Result<u128, crate::KineticRouterError> {
    let exp = current_timestamp.checked_sub(last_update_timestamp)
        .ok_or(crate::KineticRouterError::MathOverflow)?;
    if exp == 0 {
        return Ok(RAY);
    }

    // Taylor series terms: higher-order terms vanish when exp < order
    let exp_minus_one = if exp > 0 { exp - 1 } else { 0 };
    let exp_minus_two = if exp > 1 { exp - 2 } else { 0 };

    // First term: rate * exp / SECONDS_PER_YEAR (matches Aave V3)
    let first_term = {
        let rate_u256 = U256::from_u128(env, rate);
        let exp_u256 = U256::from_u128(env, u128::from(exp));
        let spy_u256 = U256::from_u128(env, u128::from(SECONDS_PER_YEAR));
        rate_u256.mul(&exp_u256).div(&spy_u256)
            .to_u128()
            .ok_or(crate::KineticRouterError::MathOverflow)?
    };

    let seconds_per_year_squared = u128::from(SECONDS_PER_YEAR)
        .checked_mul(u128::from(SECONDS_PER_YEAR))
        .ok_or(crate::KineticRouterError::MathOverflow)?;

    let base_power_two = ray_mul(env, rate, rate)?
        .checked_div(seconds_per_year_squared)
        .ok_or(crate::KineticRouterError::MathOverflow)?;

    let base_power_three = ray_mul(env, base_power_two, rate)?
        .checked_div(u128::from(SECONDS_PER_YEAR))
        .ok_or(crate::KineticRouterError::MathOverflow)?;

    // M-02
    let second_term = {
        let exp_u256 = U256::from_u128(env, u128::from(exp));
        let exp_m1_u256 = U256::from_u128(env, u128::from(exp_minus_one));
        let bp2_u256 = U256::from_u128(env, base_power_two);
        let two = U256::from_u128(env, 2);
        exp_u256.mul(&exp_m1_u256).mul(&bp2_u256).div(&two)
            .to_u128()
            .ok_or(crate::KineticRouterError::MathOverflow)?
    };

    let third_term = {
        let exp_u256 = U256::from_u128(env, u128::from(exp));
        let exp_m1_u256 = U256::from_u128(env, u128::from(exp_minus_one));
        let exp_m2_u256 = U256::from_u128(env, u128::from(exp_minus_two));
        let bp3_u256 = U256::from_u128(env, base_power_three);
        let six = U256::from_u128(env, 6);
        exp_u256.mul(&exp_m1_u256).mul(&exp_m2_u256).mul(&bp3_u256).div(&six)
            .to_u128()
            .ok_or(crate::KineticRouterError::MathOverflow)?
    };

    RAY.checked_add(first_term)
        .and_then(|sum| sum.checked_add(second_term))
        .and_then(|sum| sum.checked_add(third_term))
        .ok_or(crate::KineticRouterError::MathOverflow)
}

/// Despite the name "linear", this uses linear approximation (1 + r)^t ≈ 1 + r*t
/// for computational efficiency. Compound effect comes from repeatedly multiplying
/// the index: Index_t+1 = Index_t × (1 + rate × Δt)
pub fn calculate_linear_interest(
    rate: u128,
    last_update_timestamp: u64,
    current_timestamp: u64,
) -> Result<u128, crate::KineticRouterError> {
    let time_difference = current_timestamp.checked_sub(last_update_timestamp)
        .ok_or(crate::KineticRouterError::MathOverflow)?;
    let interest = rate
        .checked_mul(u128::from(time_difference))
        .and_then(|prod| prod.checked_div(u128::from(SECONDS_PER_YEAR)))
        .ok_or(crate::KineticRouterError::MathOverflow)?;
    RAY.checked_add(interest).ok_or(crate::KineticRouterError::MathOverflow)
}

pub fn validate_address(_env: &Env, _address: &Address) {}

pub fn validate_amount(amount: u128) -> Result<(), crate::KineticRouterError> {
    if amount == 0 {
        return Err(crate::KineticRouterError::InvalidAmount);
    }
    Ok(())
}

/// L-07: Uses MathOverflow for all numeric conversion failures.
#[inline]
pub fn safe_u128_to_i128(env: &soroban_sdk::Env, amount: u128) -> i128 {
    if amount > i128::MAX as u128 {
        panic_with_error!(env, crate::KineticRouterError::MathOverflow);
    }
    amount as i128
}

/// Safely convert i128 to u128 with negativity check.
/// L-07: Uses MathOverflow for all numeric conversion failures.
#[inline]
pub fn safe_i128_to_u128(env: &soroban_sdk::Env, value: i128) -> u128 {
    if value < 0 {
        panic_with_error!(env, crate::KineticRouterError::MathOverflow);
    }
    value as u128
}

/// M-03: Safely convert reserve_data.id (u32) to u8 for bitmap operations.
/// Panics if id >= 64 (MAX_RESERVES), which would corrupt the UserConfiguration bitmap.
#[inline]
pub fn safe_reserve_id(env: &soroban_sdk::Env, id: u32) -> u8 {
    if id >= 64 {
        panic_with_error!(env, crate::KineticRouterError::MathOverflow);
    }
    id as u8
}

pub fn get_current_timestamp(env: &Env) -> u64 {
    env.ledger().timestamp()
}

pub fn is_liquidatable(health_factor: u128) -> bool {
    health_factor < HEALTH_FACTOR_LIQUIDATION_THRESHOLD
}

/// Bit-packed reserve configuration using two u128 fields.
/// All bit-shift operations are intentional and safe by design - they extract
/// specific bit ranges from fixed-size fields and cannot overflow.
///
/// I-02: Bit layout in data_low (128 bits total):
/// - Bits 0-13: LTV (14 bits)
/// - Bits 14-27: Liquidation Threshold (14 bits)
/// - Bits 28-41: Liquidation Bonus (14 bits)
/// - Bits 42-49: Decimals (8 bits)
/// - Bit 50: Active flag
/// - Bit 51: Frozen flag
/// - Bit 52: Borrowing Enabled flag
/// - Bit 53: Paused flag
/// - Bits 54-55: **Reserved for future use** (2-bit gap)
/// - Bit 56: Flashloan Enabled flag
/// - Bits 57-70: Reserve Factor (14 bits)
/// - Bits 71-102: Min Remaining Debt (32 bits, H-02 fix)
/// - Bits 103-127: Available for future expansion
#[allow(clippy::arithmetic_side_effects)]
impl ReserveConfiguration {
    pub fn get_ltv(&self) -> u16 {
        (self.data_low & 0x3FFF) as u16
    }

    pub fn get_liquidation_threshold(&self) -> u16 {
        ((self.data_low >> 14) & 0x3FFF) as u16
    }

    pub fn get_liquidation_bonus(&self) -> u16 {
        ((self.data_low >> 28) & 0x3FFF) as u16
    }

    pub fn get_decimals(&self) -> u8 {
        ((self.data_low >> 42) & 0xFF) as u8
    }

    pub fn get_decimals_pow(&self) -> Result<u128, crate::KineticRouterError> {
        let decimals = self.get_decimals() as u32;
        10_u128
            .checked_pow(decimals)
            .ok_or(crate::KineticRouterError::MathOverflow)
    }

    pub fn is_active(&self) -> bool {
        (self.data_low >> 50) & 1 == 1
    }

    pub fn is_frozen(&self) -> bool {
        (self.data_low >> 51) & 1 == 1
    }

    pub fn is_borrowing_enabled(&self) -> bool {
        (self.data_low >> 52) & 1 == 1
    }

    pub fn is_paused(&self) -> bool {
        (self.data_low >> 53) & 1 == 1
    }

    pub fn is_flashloan_enabled(&self) -> bool {
        (self.data_low >> 56) & 1 == 1
    }

    pub fn get_reserve_factor(&self) -> u16 {
        ((self.data_low >> 57) & 0x3FFF) as u16
    }

    /// H-02 / WP-L5: Stored as whole tokens (same convention as borrow/supply caps).
    /// Multiply by 10^decimals when enforcing. Returns 0 if not set (no enforcement).
    /// Uses bits 71-102 (32 bits) in data_low.
    ///
    /// Post-liquidation bad debt callers socialize unconditionally (no threshold needed —
    /// all remaining debt is unrecoverable when collateral is fully seized).
    /// Enforcement and pre-clamp callers should guard with `if val > 0`.
    pub fn get_min_remaining_debt(&self) -> u32 {
        ((self.data_low >> 71) & 0xFFFFFFFF) as u32
    }

    /// Stored as whole tokens (not smallest units). Multiply by 10^decimals when enforcing.
    pub fn get_borrow_cap(&self) -> u128 {
        self.data_high & 0xFFFFFFFFFFFFFFFF
    }

    /// Stored as whole tokens (not smallest units). Multiply by 10^decimals when enforcing.
    pub fn get_supply_cap(&self) -> u128 {
        (self.data_high >> 64) & 0xFFFFFFFFFFFFFFFF
    }

    pub fn set_borrow_cap(&mut self, borrow_cap: u128) {
        self.data_high &= !(0xFFFFFFFFFFFFFFFFu128);
        self.data_high |= borrow_cap & 0xFFFFFFFFFFFFFFFF;
    }

    pub fn set_supply_cap(&mut self, supply_cap: u128) {
        self.data_high &= !(0xFFFFFFFFFFFFFFFFu128 << 64);
        self.data_high |= (supply_cap & 0xFFFFFFFFFFFFFFFF) << 64;
    }

    /// I-03
    /// L-13
    pub fn set_ltv(&mut self, ltv: u32) -> Result<(), ConfigurationError> {
        // Values > 10000 bps are invalid but representable in 14 bits (max 16383)
        if ltv > 10000 {
            return Err(ConfigurationError::InvalidLTV);
        }
        self.data_low &= !0x3FFF;
        self.data_low |= (ltv as u128) & 0x3FFF;
        Ok(())
    }

    /// I-03
    /// L-13
    pub fn set_liquidation_threshold(&mut self, liquidation_threshold: u32) -> Result<(), ConfigurationError> {
        if liquidation_threshold > 10000 {
            return Err(ConfigurationError::InvalidLiquidationThreshold);
        }
        self.data_low &= !(0x3FFF << 14);
        self.data_low |= ((liquidation_threshold as u128) & 0x3FFF) << 14;
        Ok(())
    }

    /// I-03
    /// L-13
    pub fn set_liquidation_bonus(&mut self, liquidation_bonus: u32) -> Result<(), ConfigurationError> {
        if liquidation_bonus > 10000 {
            return Err(ConfigurationError::InvalidLiquidationBonus);
        }
        self.data_low &= !(0x3FFF << 28);
        self.data_low |= ((liquidation_bonus as u128) & 0x3FFF) << 28;
        Ok(())
    }

    pub fn set_reserve_factor(&mut self, reserve_factor: u32) {
        self.data_low &= !(0x3FFF << 57);
        self.data_low |= ((reserve_factor as u128) & 0x3FFF) << 57;
    }

    /// H-02
    pub fn set_min_remaining_debt(&mut self, min_remaining_debt: u32) {
        self.data_low &= !(0xFFFFFFFFu128 << 71);
        self.data_low |= ((min_remaining_debt as u128) & 0xFFFFFFFF) << 71;
    }

    pub fn set_active(&mut self, active: bool) {
        if active {
            self.data_low |= 1u128 << 50;
        } else {
            self.data_low &= !(1u128 << 50);
        }
    }

    pub fn set_frozen(&mut self, frozen: bool) {
        if frozen {
            self.data_low |= 1u128 << 51;
        } else {
            self.data_low &= !(1u128 << 51);
        }
    }

    pub fn set_borrowing_enabled(&mut self, borrowing_enabled: bool) {
        if borrowing_enabled {
            self.data_low |= 1u128 << 52;
        } else {
            self.data_low &= !(1u128 << 52);
        }
    }

    pub fn set_paused(&mut self, paused: bool) {
        if paused {
            self.data_low |= 1u128 << 53;
        } else {
            self.data_low &= !(1u128 << 53);
        }
    }

    pub fn set_flashloan_enabled(&mut self, flashloan_enabled: bool) {
        if flashloan_enabled {
            self.data_low |= 1u128 << 56;
        } else {
            self.data_low &= !(1u128 << 56);
        }
    }
}

/// Bit-packed user configuration using a single u128 field.
/// All bit-shift and multiplication operations are intentional and safe - they manipulate
/// specific bit positions within the fixed-size field and cannot overflow.
/// L-14
#[allow(clippy::arithmetic_side_effects)]
impl UserConfiguration {
    pub fn is_using_as_collateral(&self, reserve_index: u8) -> bool {
        if reserve_index >= 64 { return false; }
        let shift = (reserve_index as u32) * 2;
        (self.data >> shift) & 1 == 1
    }

    pub fn is_borrowing(&self, reserve_index: u8) -> bool {
        if reserve_index >= 64 { return false; }
        let shift = (reserve_index as u32) * 2 + 1;
        (self.data >> shift) & 1 == 1
    }

    pub fn set_using_as_collateral(&mut self, reserve_index: u8, using: bool) {
        if reserve_index >= 64 { return; }
        let shift = (reserve_index as u32) * 2;
        let mask = 1u128 << shift;
        if using {
            self.data |= mask;
        } else {
            self.data &= !mask;
        }
    }

    pub fn set_borrowing(&mut self, reserve_index: u8, borrowing: bool) {
        if reserve_index >= 64 { return; }
        let shift = (reserve_index as u32) * 2 + 1;
        let mask = 1u128 << shift;
        if borrowing {
            self.data |= mask;
        } else {
            self.data &= !mask;
        }
    }

    pub fn is_empty(&self) -> bool {
        self.data == 0
    }

    /// Check if user has any debt positions
    pub fn has_any_borrowing(&self) -> bool {
        // odd bits (1,3,5...) = borrowing flags
        // Even bits (0,2,4...) = collateral flags
        const BORROW_MASK: u128 = 0xAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA;
        (self.data & BORROW_MASK) != 0
    }

    pub fn count_active_reserves(&self) -> u8 {
        let mut count = 0u8;
        let mut data = self.data;
        // Each reserve uses 2 bits (collateral + borrowing)
        // Max 64 reserves, so max 128 bits (full u128)
        for _ in 0..64 {
            // Check if either collateral (bit 0) or borrowing (bit 1) is set
            if (data & 0b11) != 0 {
                count += 1;
            }
            data >>= 2;
            if data == 0 {
                break;
            }
        }
        count
    }

    pub fn get_active_reserve_ids(&self, env: &soroban_sdk::Env) -> soroban_sdk::Vec<u32> {
        let mut result = soroban_sdk::Vec::new(env);
        let mut data = self.data;
        for reserve_id in 0u32..64u32 {
            // Check if either collateral (bit 0) or borrowing (bit 1) is set
            if (data & 0b11) != 0 {
                result.push_back(reserve_id);
            }
            data >>= 2;
            if data == 0 {
                break;
            }
        }
        result
    }
}
