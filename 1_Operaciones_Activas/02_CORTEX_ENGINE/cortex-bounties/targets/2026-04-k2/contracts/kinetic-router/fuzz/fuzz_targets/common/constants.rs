pub const BASIS_POINTS: u32 = 10_000;
#[allow(dead_code)]
pub const WAD: u128 = 1_000_000_000_000_000_000;
pub const RAY: u128 = 1_000_000_000_000_000_000_000_000_000;
pub const DECIMALS: u32 = 7;
pub const INITIAL_BALANCE: i128 = 1_000_000_000_000_000;
pub const SECONDS_PER_YEAR: u128 = 31_536_000;

pub const MAX_SAFE_AMOUNT: u128 = u128::MAX / (RAY * 1000);
pub const MIN_AMOUNT: u128 = 1;
pub const MAX_PRICE: u128 = 1_000_000_000_000_000_000;
pub const MIN_PRICE: u128 = 1_000_000_000;
pub const ZERO_PRICE: u128 = 0;
pub const DEFAULT_LIQUIDATION_CLOSE_FACTOR: u128 = 5000;

pub const FLASH_LOAN_PREMIUM_BPS: u128 = 9;

pub const MAX_ROUNDING_PER_OP: i128 = 5;
pub const BASE_TOLERANCE: i128 = 50;
pub const TOLERANCE_PER_OP: i128 = MAX_ROUNDING_PER_OP;
pub const MAX_CUMULATIVE_ROUNDING: i128 = 5_000;
pub const DUST_THRESHOLD: u128 = 50;
pub const MIN_MEANINGFUL_AMOUNT: u128 = 10;
pub const ROUNDING_TRACK_MULTIPLIER: i128 = 5;

#[inline]
pub fn calculate_tolerance(operation_count: u64) -> i128 {
    BASE_TOLERANCE + (operation_count as i128 * TOLERANCE_PER_OP)
}

#[inline]
pub fn calculate_rounding_tolerance(amount: u128, operation_count: u64) -> i128 {
    let amount_factor = ((amount / 10u128.pow(DECIMALS)) as i128).max(1).min(100);
    let scaled_tolerance = (amount_factor * MAX_ROUNDING_PER_OP) / 100;
    BASE_TOLERANCE + (operation_count as i128 * TOLERANCE_PER_OP) + scaled_tolerance
}
