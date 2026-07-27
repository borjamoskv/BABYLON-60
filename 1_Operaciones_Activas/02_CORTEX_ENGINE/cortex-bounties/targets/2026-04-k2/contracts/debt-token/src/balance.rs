use crate::storage;
use k2_shared::{ray_mul, safe_i128_to_u128, KineticRouterError, TokenError};
use soroban_sdk::{Address, Env, Symbol, Vec};

pub fn balance_of(env: &Env, id: &Address) -> Result<i128, TokenError> {
    let state = storage::get_state(env)?;

    let mut args = Vec::new(env);
    args.push_back(state.borrowed_asset.to_val());

    let borrow_index = match env.try_invoke_contract::<u128, KineticRouterError>(
        &state.pool_address,
        &Symbol::new(env, "get_current_var_borrow_idx"),
        args,
    ) {
        Ok(Ok(index)) => index,
        Ok(Err(_)) | Err(_) => return Err(TokenError::InvalidIndex),
    };

    Ok(balance_of_with_index(env, id, borrow_index))
}

pub fn balance_of_with_index(env: &Env, id: &Address, borrow_index: u128) -> i128 {
    let scaled_debt = storage::get_scaled_debt(env, id);
    let result = ray_mul(env, scaled_debt, borrow_index)
        .unwrap_or_else(|_| {
            soroban_sdk::panic_with_error!(env, KineticRouterError::MathOverflow)
        });
    i128::try_from(result).unwrap_or_else(|_| {
        soroban_sdk::panic_with_error!(env, KineticRouterError::MathOverflow)
    })
}

pub fn total_supply(env: &Env) -> Result<i128, TokenError> {
    let state = storage::get_state(env)?;

    let mut args = Vec::new(env);
    args.push_back(state.borrowed_asset.to_val());

    let borrow_index = match env.try_invoke_contract::<u128, KineticRouterError>(
        &state.pool_address,
        &Symbol::new(env, "get_current_var_borrow_idx"),
        args,
    ) {
        Ok(Ok(index)) => index,
        Ok(Err(_)) | Err(_) => return Err(TokenError::InvalidIndex),
    };

    // S-04
    let total_debt_u128 = safe_i128_to_u128(env, state.total_debt_scaled);
    let result = ray_mul(env, total_debt_u128, borrow_index)
        .unwrap_or_else(|_| {
            soroban_sdk::panic_with_error!(env, KineticRouterError::MathOverflow)
        });
    Ok(i128::try_from(result).unwrap_or_else(|_| {
        soroban_sdk::panic_with_error!(env, KineticRouterError::MathOverflow)
    }))
}

pub fn total_supply_with_index(env: &Env, borrow_index: u128) -> Result<i128, TokenError> {
    let state = storage::get_state(env)?;
    // S-04
    let total_debt_u128 = safe_i128_to_u128(env, state.total_debt_scaled);
    let result = ray_mul(env, total_debt_u128, borrow_index)
        .unwrap_or_else(|_| {
            soroban_sdk::panic_with_error!(env, KineticRouterError::MathOverflow)
        });
    Ok(i128::try_from(result).unwrap_or_else(|_| {
        soroban_sdk::panic_with_error!(env, KineticRouterError::MathOverflow)
    }))
}
