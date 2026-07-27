pub const PRICE_PRECISION: u32 = 14;
pub const WAD_PRECISION: u32 = 18;
pub const LTV_PRECISION: u128 = 1_000_000_000_000_000_000;
pub const BASIS_POINTS: u128 = 10_000;

pub const WAD: u128 = 1_000_000_000_000_000_000;
pub const HALF_WAD: u128 = 500_000_000_000_000_000;
pub const RAY: u128 = 1_000_000_000_000_000_000_000_000_000;
pub const HALF_RAY: u128 = 500_000_000_000_000_000_000_000_000;
pub const RAY_WAD_RATIO: u128 = 1_000_000_000; // RAY / WAD
pub const HALF_RAY_WAD_RATIO: u128 = 500_000_000; // (RAY / WAD) / 2

pub const SECONDS_PER_YEAR: u64 = 31_536_000;
pub const BLOCKS_PER_YEAR: u64 = 2_102_400;

pub const BASIS_POINTS_MULTIPLIER: u128 = 10_000;
pub const HALF_BASIS_POINTS: u128 = 5_000; // BASIS_POINTS_MULTIPLIER / 2

pub const HEALTH_FACTOR_LIQUIDATION_THRESHOLD: u128 = 1_000_000_000_000_000_000;

pub const DEFAULT_REFERRAL_CODE: u16 = 0;

pub const FLASHLOAN_PREMIUM_TOTAL: u128 = 9;

pub const FLASHLOAN_PREMIUM_TO_PROTOCOL: u128 = 0;

pub const OPTIMAL_UTILIZATION_RATE: u128 = 800_000_000_000_000_000_000_000_000;

pub const MAX_EXCESS_STABLE_TO_TOTAL_DEBT_RATIO: u128 = RAY;

pub const MAX_UTILIZATION_RATE: u128 = RAY;

pub const DEFAULT_LIQUIDATION_CLOSE_FACTOR: u128 = 5000;
pub const MAX_LIQUIDATION_CLOSE_FACTOR: u128 = 10000;

/// WP-M2: Positions below $2000 in base currency use 100% close factor
pub const MIN_CLOSE_FACTOR_THRESHOLD: u128 = 2_000_000_000_000_000_000_000; // 2000 * WAD

/// WP-L7: Min remaining value (debt or collateral) after partial liquidation
pub const MIN_LEFTOVER_BASE: u128 = 1_000_000_000_000_000_000_000; // 1000 * WAD

pub const MAX_RESERVES: u32 = 64;
pub const MAX_ASSETS_PER_TX: u32 = 32;
pub const MAX_REWARD_TOKENS: u32 = 16;
pub const MAX_SIGNERS: u32 = 32;
pub const MAX_FEED_IDS: u32 = 32;
pub const MAX_CONVERSION_BYTES: u32 = 256;

/// Calculate dynamic conversion factor from oracle precision to WAD (18 decimals)
/// Example: oracle_precision=14 -> 10^(18-14) = 10^4 = 10_000
pub const fn calculate_oracle_to_wad_factor(oracle_precision: u32) -> u128 {
    if oracle_precision >= WAD_PRECISION {
        1
    } else {
        10_u128.pow(WAD_PRECISION - oracle_precision)
    }
}

/// Calculate dynamic conversion factor from WAD (18 decimals) to oracle precision
pub const fn calculate_wad_to_oracle_factor(oracle_precision: u32) -> u128 {
    if oracle_precision >= WAD_PRECISION {
        10_u128.pow(oracle_precision - WAD_PRECISION)
    } else {
        1
    }
}

/// M-05: Minimum allowed value for min_swap_output_bps (90%).
/// Prevents admin from setting dangerously low slippage tolerance.
pub const MIN_SWAP_OUTPUT_FLOOR_BPS: u128 = 9000;

/// M-04: Minimum first deposit to mitigate share inflation attacks.
pub const MIN_FIRST_DEPOSIT: u128 = 1_000;

/// H-05: Post-liquidation HF tolerance in basis points (0.01%).
/// Allows tiny HF degradation from rounding noise during token burns.
pub const LIQUIDATION_HF_TOLERANCE_BPS: u128 = 1;

pub const DEFAULT_PRICE_STALENESS_THRESHOLD: u64 = 3600;
pub const MAX_PRICE_STALENESS_THRESHOLD: u64 = 86400;
pub const MIN_PRICE_STALENESS_THRESHOLD: u64 = 60;

/// Circuit breaker threshold: maximum allowed price change between consecutive queries.
/// 
/// Default: 2000 basis points (20%). Protects against oracle failures and manipulation
/// attacks that could cause extreme price jumps leading to incorrect liquidations.
/// Set to 0 to disable circuit breaker entirely.
/// 
pub const DEFAULT_MAX_PRICE_CHANGE_BPS: u32 = 2000;

pub const DEFAULT_ORACLE_CONFIG: OracleConfig = OracleConfig {
    price_staleness_threshold: DEFAULT_PRICE_STALENESS_THRESHOLD,
    price_precision: PRICE_PRECISION,
    wad_precision: WAD_PRECISION,
    conversion_factor: calculate_oracle_to_wad_factor(PRICE_PRECISION),
    ltv_precision: LTV_PRECISION,
    basis_points: BASIS_POINTS,
    max_price_change_bps: DEFAULT_MAX_PRICE_CHANGE_BPS,
};

pub const TEST_PRICE_DEFAULT: u128 = 1_000_000_000_000_000;
pub const TEST_PRICE_BTC: u128 = 45_000_000_000_000_000;
pub const TEST_PRICE_ETH: u128 = 3_000_000_000_000_000;
pub const TEST_PRICE_USD: u128 = 1_000_000_000_000_000;

// F-04: Removed dead SOROSWAP_ROUTER and SOROSWAP_FACTORY constants
// These were never referenced at runtime (zero usages found across entire codebase).
// DEX router and factory addresses are stored via storage::set_dex_router/factory
// and read from storage at runtime, not from these constants.

use crate::types::OracleConfig;
