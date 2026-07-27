use crate::storage;
use k2_shared::{calculate_linear_interest, get_current_timestamp, ray_mul, safe_i128_to_u128, KineticRouterError, TokenError};
use soroban_sdk::{Address, Env, IntoVal, Symbol, Vec};

pub fn balance_of(env: &Env, id: &Address) -> Result<i128, TokenError> {
    let state = storage::get_state(env)?;

    // Get current liquidity index from router (always up-to-date)
    // This ensures balance is accurate even if stored index is stale
    let mut args = Vec::new(env);
    args.push_back(state.underlying_asset.to_val());

    let liquidity_index = match env.try_invoke_contract::<u128, KineticRouterError>(
        &state.pool_address,
        &Symbol::new(env, "get_current_liquidity_index"),
        args,
    ) {
        Ok(Ok(index)) => index,
        // WP-I3: fail closed — match debt-token behaviour
        Ok(Err(_)) | Err(_) => return Err(TokenError::InvalidIndex),
    };

    Ok(balance_of_with_index(env, id, liquidity_index))
}

pub fn balance_of_with_index(env: &Env, id: &Address, liquidity_index: u128) -> i128 {
    let scaled_balance = storage::get_scaled_balance(env, id);
    // S-04
    let scaled_balance_u128 = safe_i128_to_u128(env, scaled_balance);
    let result = ray_mul(env, scaled_balance_u128, liquidity_index)
        .unwrap_or_else(|_| {
            soroban_sdk::panic_with_error!(env, KineticRouterError::MathOverflow)
        });
    i128::try_from(result).unwrap_or_else(|_| {
        soroban_sdk::panic_with_error!(env, KineticRouterError::MathOverflow)
    })
}

pub fn total_supply(env: &Env) -> Result<i128, TokenError> {
    let state = storage::get_state(env)?;

    // Get current liquidity index from router (always up-to-date)
    // This ensures total supply is accurate even if stored index is stale
    let mut args = Vec::new(env);
    args.push_back(state.underlying_asset.to_val());

    let liquidity_index = match env.try_invoke_contract::<u128, KineticRouterError>(
        &state.pool_address,
        &Symbol::new(env, "get_current_liquidity_index"),
        args,
    ) {
        Ok(Ok(index)) => index,
        // WP-I3: fail closed — match debt-token behaviour
        Ok(Err(_)) | Err(_) => return Err(TokenError::InvalidIndex),
    };

    // S-04
    let total_supply_u128 = safe_i128_to_u128(env, state.total_supply_scaled);
    let result = ray_mul(env, total_supply_u128, liquidity_index)
        .unwrap_or_else(|_| {
            soroban_sdk::panic_with_error!(env, KineticRouterError::MathOverflow)
        });
    Ok(i128::try_from(result).unwrap_or_else(|_| {
        soroban_sdk::panic_with_error!(env, KineticRouterError::MathOverflow)
    }))
}

pub fn total_supply_with_index(env: &Env, index: u128) -> Result<u128, TokenError> {
    let state = storage::get_state(env)?;
    // S-04
    let total_supply_u128 = safe_i128_to_u128(env, state.total_supply_scaled);
    ray_mul(env, total_supply_u128, index)
        .map_err(|_| TokenError::InvalidIndex)
}

pub fn balance_of_with_timestamp(env: &Env, user: &Address, last_update_timestamp: u64) -> Result<u128, TokenError> {
    let scaled_balance = storage::get_scaled_balance(env, user);
    if scaled_balance == 0 {
        return Ok(0);
    }

    let current_timestamp = get_current_timestamp(env);
    if current_timestamp == last_update_timestamp {
        // S-04
        return Ok(safe_i128_to_u128(env, scaled_balance));
    }

    let state = storage::get_state(env)?;
    let mut args = soroban_sdk::Vec::new(env);
    args.push_back(state.underlying_asset.into_val(env));
    let reserve_data: k2_shared::ReserveData = env.invoke_contract(
        &state.pool_address,
        &soroban_sdk::Symbol::new(env, "get_reserve_data"),
        args,
    );
    let liquidity_rate = reserve_data.current_liquidity_rate;

    let cumulated_interest =
        calculate_linear_interest(liquidity_rate, last_update_timestamp, current_timestamp)
            .map_err(|_| TokenError::InvalidIndex)?;

    // S-04
    let scaled_balance_u128 = safe_i128_to_u128(env, scaled_balance);
    ray_mul(env, scaled_balance_u128, cumulated_interest)
        .map_err(|_| TokenError::InvalidIndex)
}
