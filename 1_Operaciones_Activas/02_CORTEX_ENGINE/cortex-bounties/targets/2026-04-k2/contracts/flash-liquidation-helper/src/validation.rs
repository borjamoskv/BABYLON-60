use k2_shared::{
    calculate_oracle_to_wad_factor, FlashLiquidationValidationParams,
    FlashLiquidationValidationResult, KineticRouterError, BASIS_POINTS_MULTIPLIER,
    DEFAULT_LIQUIDATION_CLOSE_FACTOR,
};
use soroban_sdk::{Env, U256};

/// Compute `amount * price * oracle_to_wad / decimals_pow` using U256 intermediates
/// to match the main router's overflow-safe pattern.
fn to_base_currency(
    env: &Env,
    amount: u128,
    price: u128,
    oracle_to_wad: u128,
    decimals_pow: u128,
) -> Result<u128, KineticRouterError> {
    U256::from_u128(env, amount)
        .mul(&U256::from_u128(env, price))
        .mul(&U256::from_u128(env, oracle_to_wad))
        .div(&U256::from_u128(env, decimals_pow))
        .to_u128()
        .ok_or(KineticRouterError::MathOverflow)
}

/// Validate flash liquidation parameters
pub fn validate_flash_liquidation(
    env: &Env,
    params: &FlashLiquidationValidationParams,
) -> Result<FlashLiquidationValidationResult, KineticRouterError> {
    let debt_to_cover = params.debt_to_cover;
    let collateral_to_seize = params.collateral_to_seize;
    let collateral_price = params.collateral_price;
    let debt_price = params.debt_price;

    // L-01: Reject zero prices to prevent division-by-zero
    if collateral_price == 0 || debt_price == 0 {
        return Err(KineticRouterError::PriceOracleError);
    }
    let debt_reserve = &params.debt_reserve;
    let collateral_reserve = &params.collateral_reserve;
    let min_swap_out = params.min_swap_out;
    let debt_balance = params.debt_balance;
    let min_output_bps = params.min_output_bps;

    // Get dynamic oracle to WAD conversion factor
    let oracle_to_wad = calculate_oracle_to_wad_factor(params.oracle_price_precision);

    // Cache decimal power calculations (using helper method)
    let collateral_decimals_pow = collateral_reserve.configuration.get_decimals_pow()?;
    let debt_decimals_pow = debt_reserve.configuration.get_decimals_pow()?;

    // -------- DEBT → BASE (U256 to match main router pattern) --------
    let debt_to_cover_base =
        to_base_currency(env, debt_to_cover, debt_price, oracle_to_wad, debt_decimals_pow)?;

    let total_debt_base =
        to_base_currency(env, debt_balance, debt_price, oracle_to_wad, debt_decimals_pow)?;

    // -------- CLOSE FACTOR CHECK --------
    let max_liquidatable = total_debt_base
        .checked_mul(DEFAULT_LIQUIDATION_CLOSE_FACTOR)
        .ok_or(KineticRouterError::MathOverflow)?
        .checked_div(BASIS_POINTS_MULTIPLIER)
        .ok_or(KineticRouterError::MathOverflow)?;

    if debt_to_cover_base > max_liquidatable {
        return Err(KineticRouterError::LiquidationAmountTooHigh);
    }

    // -------- VALIDATE COLLATERAL TO SEIZE --------
    let bonus = collateral_reserve.configuration.get_liquidation_bonus() as u128;

    let expected_collateral_base = debt_to_cover_base
        .checked_mul(BASIS_POINTS_MULTIPLIER + bonus)
        .ok_or(KineticRouterError::MathOverflow)?
        .checked_div(BASIS_POINTS_MULTIPLIER)
        .ok_or(KineticRouterError::MathOverflow)?;

    let expected_collateral_units = {
        let num = U256::from_u128(env, expected_collateral_base)
            .mul(&U256::from_u128(env, collateral_decimals_pow));
        let den = U256::from_u128(env, collateral_price)
            .mul(&U256::from_u128(env, oracle_to_wad));
        num.div(&den)
            .to_u128()
            .ok_or(KineticRouterError::MathOverflow)?
    };

    // I-01: 0.01% tolerance for rounding differences (matches debt balance precision)
    let min_expected = expected_collateral_units.checked_mul(BASIS_POINTS_MULTIPLIER - 1).ok_or(KineticRouterError::MathOverflow)?.checked_div(BASIS_POINTS_MULTIPLIER).ok_or(KineticRouterError::MathOverflow)?;
    let max_expected = expected_collateral_units.checked_mul(BASIS_POINTS_MULTIPLIER + 1).ok_or(KineticRouterError::MathOverflow)?.checked_div(BASIS_POINTS_MULTIPLIER).ok_or(KineticRouterError::MathOverflow)?;
    if collateral_to_seize < min_expected || collateral_to_seize > max_expected {
        return Err(KineticRouterError::InvalidAmount);
    }

    // Use the computed amount instead of the caller's value to prevent over-seizure
    let collateral_amount_to_seize = expected_collateral_units;

    // -------- EXPECTED DEBT OUT (U256) --------
    let expected_debt_out = {
        let num = U256::from_u128(env, collateral_amount_to_seize)
            .mul(&U256::from_u128(env, collateral_price))
            .mul(&U256::from_u128(env, debt_decimals_pow));
        let den = U256::from_u128(env, debt_price)
            .mul(&U256::from_u128(env, collateral_decimals_pow));
        num.div(&den)
            .to_u128()
            .ok_or(KineticRouterError::MathOverflow)?
    };

    // -------- SLIPPAGE --------
    let pool_min_out = expected_debt_out.checked_mul(min_output_bps).ok_or(KineticRouterError::MathOverflow)?.checked_div(10000).ok_or(KineticRouterError::MathOverflow)?;
    let effective_min_out = core::cmp::max(pool_min_out, min_swap_out);

    Ok(FlashLiquidationValidationResult {
        collateral_amount_to_seize,
        expected_debt_out,
        effective_min_out,
        debt_to_cover_base,
        total_debt_base,
    })
}

