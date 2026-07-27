use crate::calculation;
use crate::storage;
use k2_shared::*;
use soroban_sdk::{Address, Env, U256, Vec};

/// Validate caller has access to reserve
///
/// Empty whitelist allows all addresses
/// Non-empty whitelist restricts to listed addresses only
pub fn validate_reserve_whitelist_access(
    env: &Env,
    asset: &Address,
    caller: &Address,
) -> Result<(), KineticRouterError> {
    if !storage::is_address_whitelisted_for_reserve(env, asset, caller) {
        return Err(KineticRouterError::AddressNotWhitelisted);
    }
    Ok(())
}

/// Validate caller has access to perform liquidation.
/// Empty whitelist allows all addresses.
/// Non-empty whitelist restricts to listed addresses only.
pub fn validate_liquidation_whitelist_access(
    env: &Env,
    caller: &Address,
) -> Result<(), KineticRouterError> {
    if !storage::is_address_whitelisted_for_liquidation(env, caller) {
        return Err(KineticRouterError::AddressNotWhitelisted);
    }
    Ok(())
}

/// Validate caller is not blacklisted for reserve.
/// Empty blacklist allows all addresses.
/// Non-empty blacklist blocks listed addresses.
pub fn validate_reserve_blacklist_access(
    env: &Env,
    asset: &Address,
    caller: &Address,
) -> Result<(), KineticRouterError> {
    if storage::is_address_blacklisted_for_reserve(env, asset, caller) {
        return Err(KineticRouterError::Unauthorized);
    }
    Ok(())
}

/// Validate caller is not blacklisted for liquidation.
/// Empty blacklist allows all addresses.
/// Non-empty blacklist blocks listed addresses.
pub fn validate_liquidation_blacklist_access(
    env: &Env,
    caller: &Address,
) -> Result<(), KineticRouterError> {
    if storage::is_address_blacklisted_for_liquidation(env, caller) {
        return Err(KineticRouterError::Unauthorized);
    }
    Ok(())
}

/// F-01/F-03
/// The caller (operations.rs) reads reserve data once and passes it through.
pub fn validate_supply(env: &Env, amount: u128, reserve_data: &k2_shared::ReserveData) -> Result<(), KineticRouterError> {
    if storage::is_paused(env) {
        return Err(KineticRouterError::AssetPaused);
    }

    validate_amount(amount)?;

    if !reserve_data.configuration.is_active() {
        return Err(KineticRouterError::AssetNotActive);
    }

    if reserve_data.configuration.is_paused() {
        return Err(KineticRouterError::AssetPaused);
    }

    if reserve_data.configuration.is_frozen() {
        return Err(KineticRouterError::AssetFrozen);
    }

    // F-12
    // calls verify_oracle_price_exists_and_nonzero before enabling collateral.
    // On subsequent supply, oracle validation isn't needed for deposits.
    // F-13
    // (validate_supply_cap_after_interest) is strictly more restrictive since
    // interest accrual can only increase total supply.

    Ok(())
}

/// F-01/F-03
pub fn validate_withdraw(
    env: &Env,
    _asset: &Address,
    amount: u128,
    reserve_data: &k2_shared::ReserveData,
) -> Result<(), KineticRouterError> {
    if storage::is_paused(env) {
        return Err(KineticRouterError::AssetPaused);
    }

    // u128::MAX signals max withdrawal
    if amount != u128::MAX {
        validate_amount(amount)?;
    }

    if !reserve_data.configuration.is_active() {
        return Err(KineticRouterError::AssetNotActive);
    }

    if reserve_data.configuration.is_paused() {
        return Err(KineticRouterError::AssetPaused);
    }

    Ok(())
}

/// F-01/F-03
pub fn validate_borrow(
    env: &Env,
    amount: u128,
    interest_rate_mode: u32,
    reserve_data: &k2_shared::ReserveData,
) -> Result<(), KineticRouterError> {
    if storage::is_paused(env) {
        return Err(KineticRouterError::AssetPaused);
    }

    validate_amount(amount)?;

    // Only variable rate (mode 1) supported
    if interest_rate_mode != 1 {
        return Err(KineticRouterError::BorrowingNotEnabled);
    }

    if !reserve_data.configuration.is_active() {
        return Err(KineticRouterError::AssetNotActive);
    }

    if reserve_data.configuration.is_paused() {
        return Err(KineticRouterError::AssetPaused);
    }

    if reserve_data.configuration.is_frozen() {
        return Err(KineticRouterError::AssetFrozen);
    }

    if !reserve_data.configuration.is_borrowing_enabled() {
        return Err(KineticRouterError::BorrowingNotEnabled);
    }

    // F-12

    Ok(())
}

/// NEW-01
/// The caller (operations::borrow) already has both values.
pub fn validate_user_can_borrow(
    env: &Env,
    user: &Address,
    asset: &Address,
    amount: u128,
    reserve_data: &k2_shared::ReserveData,
    oracle_to_wad: u128,
) -> Result<(), KineticRouterError> {
    let (user_account_data, price_map) = crate::calculation::calculate_user_account_data_with_prices(env, user, Some(asset))?;

    let asset_price = price_map
        .try_get(asset.clone())
        .ok()
        .flatten()
        .ok_or(KineticRouterError::PriceOracleNotFound)?;
    if asset_price == 0 {
        return Err(KineticRouterError::PriceOracleNotFound);
    }

    // NEW-01
    let asset_decimals = reserve_data.configuration.get_decimals() as u32;

    // Multiply before divide to preserve precision
    let decimals_pow = 10_u128
        .checked_pow(asset_decimals)
        .ok_or(KineticRouterError::MathOverflow)?;

    if decimals_pow == 0 {
        return Err(KineticRouterError::MathOverflow);
    }

    // M-2
    let borrow_amount_in_base_currency = crate::calculation::value_in_base(
        env, amount, asset_price, oracle_to_wad, decimals_pow,
    )?;

    if borrow_amount_in_base_currency > user_account_data.available_borrows_base {
        return Err(KineticRouterError::InsufficientCollateral);
    }

    // Calculate what the health factor would be AFTER this borrow
    let new_total_debt = user_account_data
        .total_debt_base
        .checked_add(borrow_amount_in_base_currency)
        .ok_or(KineticRouterError::MathOverflow)?;

    // Calculate new health factor: (collateral * liquidation_threshold) / new_debt
    // S-02
    let new_health_factor = crate::calculation::calculate_health_factor_u256(
        env,
        user_account_data.total_collateral_base,
        user_account_data.current_liquidation_threshold,
        new_total_debt,
    );

    // Reject if the new health factor would be below the liquidation threshold
    let liquidation_threshold = crate::storage::get_health_factor_liquidation_threshold(env);
    if new_health_factor < liquidation_threshold {
        return Err(KineticRouterError::HealthFactorTooLow);
    }

    Ok(())
}

/// Validate withdrawal won't violate health factor liquidation threshold.
/// Simulates the health factor after collateral reduction to prevent unsafe positions.
/// F-15
/// NEW-02
pub fn validate_user_can_withdraw(
    env: &Env,
    user: &Address,
    asset: &Address,
    amount: u128,
    reserve_data: &k2_shared::ReserveData,
    oracle_to_wad: u128,
) -> Result<(), KineticRouterError> {
    // F-15
    let user_config = storage::get_user_configuration(env, user);

    // F-15
    if !user_config.is_using_as_collateral(k2_shared::safe_reserve_id(env, reserve_data.id)) {
        return Ok(());
    }

    // F-15
    let extra_assets = {
        let mut v = soroban_sdk::Vec::new(env);
        v.push_back(asset.clone());
        v
    };
    let params = crate::calculation::AccountDataParams {
        user_config: Some(&user_config),
        extra_assets: Some(&extra_assets),
        return_prices: true,
        ..Default::default()
    };
    let result = crate::calculation::calculate_user_account_data_unified(env, user, params)?;
    let user_account_data = result.account_data;
    let price_map = result.prices.unwrap_or_else(|| soroban_sdk::Map::new(env));

    // If user has no debt, they can withdraw freely
    if user_account_data.total_debt_base == 0 {
        return Ok(());
    }

    // Get withdrawal asset price from the cached price_map
    let asset_price = price_map
        .try_get(asset.clone())
        .ok()
        .flatten()
        .ok_or(KineticRouterError::PriceOracleNotFound)?;
    if asset_price == 0 {
        return Err(KineticRouterError::PriceOracleNotFound);
    }

    let asset_decimals = reserve_data.configuration.get_decimals() as u32;

    // Multiply before divide to preserve precision
    let decimals_pow = 10_u128
        .checked_pow(asset_decimals)
        .ok_or(KineticRouterError::MathOverflow)?;

    if decimals_pow == 0 {
        return Err(KineticRouterError::MathOverflow);
    }

    // Recalculate weighted threshold sum after removing the withdrawn asset's contribution.
    // Must match the accumulator's U256 chain: amount * price * oracle_to_wad * threshold / decimals_pow
    let asset_liquidation_threshold =
        reserve_data.configuration.get_liquidation_threshold() as u128;

    let withdraw_threshold_contribution = {
        let amount_u256 = U256::from_u128(env, amount);
        let price_u256 = U256::from_u128(env, asset_price);
        let oracle_to_wad_u256 = U256::from_u128(env, oracle_to_wad);
        let threshold_u256 = U256::from_u128(env, asset_liquidation_threshold);
        let decimals_pow_u256 = U256::from_u128(env, decimals_pow);
        amount_u256.mul(&price_u256).mul(&oracle_to_wad_u256).mul(&threshold_u256).div(&decimals_pow_u256)
            .to_u128()
            .ok_or(KineticRouterError::MathOverflow)?
    };

    let new_weighted_threshold_sum = result
        .weighted_threshold_sum
        .checked_sub(withdraw_threshold_contribution)
        .unwrap_or(0);

    // HF = weighted_threshold_sum * WAD / (10000 * debt)
    let new_health_factor = {
        let weighted_sum_u256 = U256::from_u128(env, new_weighted_threshold_sum);
        let wad_u256 = U256::from_u128(env, WAD);
        let bps_u256 = U256::from_u128(env, 10000u128);
        let debt_u256 = U256::from_u128(env, user_account_data.total_debt_base);
        weighted_sum_u256.mul(&wad_u256)
            .div(&bps_u256)
            .div(&debt_u256)
            .to_u128()
            .unwrap_or(0)
    };

    let liquidation_threshold = crate::storage::get_health_factor_liquidation_threshold(env);
    if new_health_factor < liquidation_threshold {
        return Err(KineticRouterError::HealthFactorTooLow);
    }

    Ok(())
}


/// Validate supply cap after interest accrual
/// Ensures caps are enforced even when interest accrual increases total supply
pub fn validate_supply_cap_after_interest(
    env: &Env,
    amount: u128,
    reserve_data: &k2_shared::ReserveData,
    liquidity_index: u128,
) -> Result<(), KineticRouterError> {
    let supply_cap = reserve_data.configuration.get_supply_cap();
    if supply_cap > 0 {
        // Use get_total_supply_with_index
        let current_supply = calculation::get_total_supply_with_index(
            env,
            &reserve_data.a_token_address,
            liquidity_index,
        )?;
        let decimals = reserve_data.configuration.get_decimals();

        let multiplier = 10u128
            .checked_pow(decimals as u32)
            .ok_or(KineticRouterError::MathOverflow)?;
        let cap_in_smallest_units = supply_cap
            .checked_mul(multiplier)
            .ok_or(KineticRouterError::MathOverflow)?;

        let new_total_supply = current_supply
            .checked_add(amount)
            .ok_or(KineticRouterError::MathOverflow)?;
        if new_total_supply > cap_in_smallest_units {
            return Err(KineticRouterError::SupplyCapExceeded);
        }
    }

    Ok(())
}

/// Validate borrow cap after interest accrual
/// Ensures caps are enforced even when interest accrual increases total debt
pub fn validate_borrow_cap_after_interest(
    env: &Env,
    amount: u128,
    reserve_data: &k2_shared::ReserveData,
    asset: &Address,
    variable_borrow_index: u128,
) -> Result<(), KineticRouterError> {
    let borrow_cap = reserve_data.configuration.get_borrow_cap();
    let debt_ceiling = storage::get_reserve_debt_ceiling(env, asset);

    // F-14
    if borrow_cap > 0 || debt_ceiling > 0 {
        let current_debt = calculation::get_total_supply_with_index(
            env,
            &reserve_data.debt_token_address,
            variable_borrow_index,
        )?;
        let decimals = reserve_data.configuration.get_decimals();
        let multiplier = 10u128
            .checked_pow(decimals as u32)
            .ok_or(KineticRouterError::MathOverflow)?;
        let new_total_debt = current_debt
            .checked_add(amount)
            .ok_or(KineticRouterError::MathOverflow)?;

        if borrow_cap > 0 {
            let cap_in_smallest_units = borrow_cap
                .checked_mul(multiplier)
                .ok_or(KineticRouterError::MathOverflow)?;
            if new_total_debt > cap_in_smallest_units {
                return Err(KineticRouterError::BorrowCapExceeded);
            }
        }

        if debt_ceiling > 0 {
            let ceiling_in_smallest_units = debt_ceiling
                .checked_mul(multiplier)
                .ok_or(KineticRouterError::MathOverflow)?;
            if new_total_debt > ceiling_in_smallest_units {
                return Err(KineticRouterError::DebtCeilingExceeded);
            }
        }
    }

    Ok(())
}

/// Validate repay operation parameters
/// F-01/F-03
pub fn validate_repay(
    env: &Env,
    _asset: &Address,
    amount: u128,
    rate_mode: u32,
    reserve_data: &k2_shared::ReserveData,
) -> Result<(), KineticRouterError> {
    if storage::is_paused(env) {
        return Err(KineticRouterError::AssetPaused);
    }

    // Validate amount (u128::MAX signals full repayment, 0 is invalid)
    if amount == 0 {
        return Err(KineticRouterError::InvalidAmount);
    }
    if amount != u128::MAX {
        validate_amount(amount)?;
    }

    // Validate interest rate mode (only variable rate supported)
    if rate_mode != 1 {
        return Err(KineticRouterError::BorrowingNotEnabled);
    }

    // Check if reserve is active
    if !reserve_data.configuration.is_active() {
        return Err(KineticRouterError::AssetNotActive);
    }

    if reserve_data.configuration.is_paused() {
        return Err(KineticRouterError::AssetPaused);
    }

    Ok(())
}

/// Validate liquidation call parameters
/// Reserve data should be provided to avoid duplicate storage reads
pub fn validate_liquidation(
    env: &Env,
    collateral_asset: &Address,
    debt_asset: &Address,
    _user: &Address,
    debt_to_cover: u128,
    collateral_reserve: Option<&ReserveData>,
    debt_reserve: Option<&ReserveData>,
) -> Result<(), KineticRouterError> {
    if storage::is_paused(env) {
        return Err(KineticRouterError::AssetPaused);
    }

    // Validate amount is greater than zero
    validate_amount(debt_to_cover)?;

    // Get reserve data - use provided or fetch (for backward compatibility)
    let collateral_reserve_data = if let Some(data) = collateral_reserve {
        data
    } else {
        // Fetch if not provided (backward compatibility)
        let reserve = storage::get_reserve_data(env, collateral_asset)?;
        if !reserve.configuration.is_active() {
            return Err(KineticRouterError::AssetNotActive);
        }
        if reserve.configuration.is_paused() {
            return Err(KineticRouterError::AssetPaused);
        }
        // Check asset mismatch
        if collateral_asset == debt_asset {
            return Err(KineticRouterError::InvalidLiquidation);
        }
        // For debt reserve, fetch if needed
        if debt_reserve.is_none() {
            let debt_reserve_data = storage::get_reserve_data(env, debt_asset)?;
            if !debt_reserve_data.configuration.is_active() {
                return Err(KineticRouterError::AssetNotActive);
            }
            if debt_reserve_data.configuration.is_paused() {
                return Err(KineticRouterError::AssetPaused);
            }
        }
        return Ok(());
    };

    let debt_reserve_data = if let Some(data) = debt_reserve {
        data
    } else {
        // Fetch if not provided
        let reserve = storage::get_reserve_data(env, debt_asset)?;
        if !reserve.configuration.is_active() {
            return Err(KineticRouterError::AssetNotActive);
        }
        if reserve.configuration.is_paused() {
            return Err(KineticRouterError::AssetPaused);
        }
        // Both reserves are fetched, validate mismatch
        if collateral_asset == debt_asset {
            return Err(KineticRouterError::InvalidLiquidation);
        }
        return Ok(());
    };

    // Check if reserves are active
    if !collateral_reserve_data.configuration.is_active()
        || !debt_reserve_data.configuration.is_active()
    {
        return Err(KineticRouterError::AssetNotActive);
    }

    // Check if reserves are paused
    if collateral_reserve_data.configuration.is_paused()
        || debt_reserve_data.configuration.is_paused()
    {
        return Err(KineticRouterError::AssetPaused);
    }

    // Check if assets are different
    if collateral_asset == debt_asset {
        return Err(KineticRouterError::InvalidLiquidation);
    }

    Ok(())
}
