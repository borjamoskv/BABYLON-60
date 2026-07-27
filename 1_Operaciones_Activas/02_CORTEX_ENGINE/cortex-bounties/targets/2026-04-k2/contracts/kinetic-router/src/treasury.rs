use crate::{calculation, storage};
use k2_shared::*;
use soroban_sdk::{symbol_short, Address, Env, IntoVal, Symbol, Vec};

pub fn collect_protocol_reserves(
    env: Env,
    asset: Address,
) -> Result<u128, KineticRouterError> {
    // Validate admin
    let admin = storage::get_pool_admin(&env)?;
    admin.require_auth();

    // Get current reserve data
    let current_reserve_data = storage::get_reserve_data(&env, &asset)?;

    // Update state first to ensure latest interest accrual
    let reserve_data = calculation::update_state(&env, &asset, &current_reserve_data)?;

    // Calculate available reserves
    let underlying_balance =
        calculation::get_atoken_underlying_balance(&env, &asset, &reserve_data.a_token_address)?;

    // Use get_total_supply_with_index to avoid re-entry
    // We already have the liquidity_index from update_state, so no need to call back to router
    let total_supply = calculation::get_total_supply_with_index(
        &env,
        &reserve_data.a_token_address,
        reserve_data.liquidity_index,
    )?;

    // Get total borrows to account for tokens that are borrowed out
    // When tokens are borrowed, they leave the contract, so we need to account for that
    let total_borrow = calculation::get_total_supply_with_index(
        &env,
        &reserve_data.debt_token_address,
        reserve_data.variable_borrow_index,
    )?;

    // Available liquidity = what should be in the contract (total_supply - total_borrow)
    // This is the amount that suppliers can claim minus what borrowers owe
    // Reserves = actual balance - available liquidity
    
    if total_borrow > total_supply {
        return Err(KineticRouterError::InvalidAmount);
    }
    
    let available_liquidity = total_supply - total_borrow;
    let available_reserves = if underlying_balance > available_liquidity {
        underlying_balance - available_liquidity
    } else {
        return Ok(0); // No reserves available
    };

    // Subtract any uncovered deficit to prevent draining liquidity depositors need
    let deficit = storage::get_reserve_deficit(&env, &asset);
    let collectible_reserves = available_reserves.saturating_sub(deficit);

    if collectible_reserves == 0 {
        return Ok(0);
    }

    // Get treasury address
    let treasury = storage::get_treasury(&env).ok_or(KineticRouterError::TreasuryNotSet)?;

    // Transfer reserves from aToken to treasury
    // Use same pattern as liquidation_call for consistency
    let mut transfer_args = Vec::new(&env);
    transfer_args.push_back(env.current_contract_address().into_val(&env));
    transfer_args.push_back(treasury.to_val());
    transfer_args.push_back(collectible_reserves.into_val(&env));

    let transfer_result = env.try_invoke_contract::<bool, KineticRouterError>(
        &reserve_data.a_token_address,
        &Symbol::new(&env, "transfer_underlying_to"),
        transfer_args,
    );

    match transfer_result {
        Ok(Ok(true)) => {
            // Emit event to enable off-chain monitoring of reserve transfers to treasury
            env.events().publish(
                (symbol_short!("reserve"), asset.clone()),
                (collectible_reserves, treasury),
            );
            Ok(collectible_reserves)
        }
        _ => Err(KineticRouterError::UnderlyingTransferFailed),
    }
}

/// Cover accumulated bad debt deficit for a reserve.
/// Permissionless: anyone can call this to inject tokens into the pool.
/// Transfers underlying from caller to the aToken contract (replenishes pool liquidity).
/// Returns the actual amount covered (capped at current deficit).
pub fn cover_deficit(
    env: Env,
    caller: Address,
    asset: Address,
    amount: u128,
) -> Result<u128, KineticRouterError> {
    caller.require_auth();

    if amount == 0 {
        return Err(KineticRouterError::InvalidAmount);
    }

    let current_deficit = storage::get_reserve_deficit(&env, &asset);
    if current_deficit == 0 {
        return Err(KineticRouterError::InvalidAmount);
    }

    // Cover at most the current deficit
    let cover_amount = amount.min(current_deficit);

    // Get the reserve's aToken address
    let reserve_data = storage::get_reserve_data(&env, &asset)?;

    // Transfer underlying tokens from caller to aToken contract (replenishes pool liquidity)
    let transfer_args = soroban_sdk::vec![
        &env,
        caller.to_val(),
        reserve_data.a_token_address.to_val(),
        IntoVal::into_val(&safe_u128_to_i128(&env, cover_amount), &env),
    ];

    let transfer_result = env.try_invoke_contract::<(), KineticRouterError>(
        &asset,
        &Symbol::new(&env, "transfer"),
        transfer_args,
    );

    match transfer_result {
        Ok(Ok(_)) => {}
        Ok(Err(_)) | Err(_) => {
            return Err(KineticRouterError::UnderlyingTransferFailed);
        }
    }

    // Reduce the tracked deficit
    storage::reduce_reserve_deficit(&env, &asset, cover_amount);

    let remaining_deficit = storage::get_reserve_deficit(&env, &asset);

    env.events().publish(
        (symbol_short!("def_covr"), asset.clone()),
        (caller.clone(), cover_amount, remaining_deficit),
    );

    Ok(cover_amount)
}
