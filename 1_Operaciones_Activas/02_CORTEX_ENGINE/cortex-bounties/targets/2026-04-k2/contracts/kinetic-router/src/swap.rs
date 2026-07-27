use crate::calculation;
use crate::storage;
use crate::validation;
use k2_shared::*;
use soroban_sdk::{symbol_short, Address, Env, IntoVal, Symbol, Vec};

use k2_shared::safe_u128_to_i128;

/// Swap collateral from one asset to another in a single transaction
///
/// This function allows users to atomically:
/// 1. Unlock their collateral (withdraw from lending pool)
/// 2. Swap the collateral to another asset via DEX
/// 3. Deposit the new asset back as collateral
///
/// # Arguments
/// * `env` - The Soroban environment
/// * `caller` - The address calling this function (must own the collateral)
/// * `from_asset` - The address of the collateral asset to swap from
/// * `to_asset` - The address of the asset to swap to and deposit as collateral
/// * `amount` - The amount of from_asset to withdraw and swap (in underlying units)
/// * `min_amount_out` - Minimum amount of to_asset to receive from swap (slippage protection)
///
/// # Returns
/// * `Ok(u128)` - Amount of to_asset received and deposited as collateral
/// * `Err(KineticRouterError)` - Operation failed due to validation, swap, or deposit failure
///
/// # Security Features
/// * Health factor validation before and after operation
/// * Slippage protection via min_amount_out
/// * Atomic execution - all steps succeed or none do
///
/// # Errors
/// * `KineticRouterError::InsufficientCollateral` - User doesn't have enough collateral
/// * `KineticRouterError::InsufficientSwapOut` - Swap output below minimum
/// * `KineticRouterError::UnauthorizedAMM` - DEX router not configured
/// * `KineticRouterError::UnderlyingTransferFailed` - Token transfer failed
pub fn swap_collateral(
    env: Env,
    caller: Address,
    from_asset: Address,
    to_asset: Address,
    amount: u128,
    min_amount_out: u128,
    swap_handler: Option<Address>,
) -> Result<u128, KineticRouterError> {
    caller.require_auth();

    // Validate inputs
    if from_asset == to_asset {
        return Err(KineticRouterError::InvalidAmount);
    }
    if amount == 0 {
        return Err(KineticRouterError::InvalidAmount);
    }
    if min_amount_out == 0 {
        return Err(KineticRouterError::InvalidAmount);
    }

    // Check global pause
    if storage::is_paused(&env) {
        return Err(KineticRouterError::AssetPaused);
    }

    // Validate access controls
    validation::validate_reserve_whitelist_access(&env, &from_asset, &caller)?;
    validation::validate_reserve_blacklist_access(&env, &from_asset, &caller)?;
    validation::validate_reserve_whitelist_access(&env, &to_asset, &caller)?;
    validation::validate_reserve_blacklist_access(&env, &to_asset, &caller)?;

    let from_reserve_data = storage::get_reserve_data(&env, &from_asset)?;
    let to_reserve_data = storage::get_reserve_data(&env, &to_asset)?;
    let mut user_config = storage::get_user_configuration(&env, &caller);

    if !from_reserve_data.configuration.is_active() {
        return Err(KineticRouterError::AssetNotActive);
    }
    if !to_reserve_data.configuration.is_active() {
        return Err(KineticRouterError::AssetNotActive);
    }

    // Check reserve-level pause
    if from_reserve_data.configuration.is_paused() {
        return Err(KineticRouterError::AssetPaused);
    }
    if to_reserve_data.configuration.is_paused() {
        return Err(KineticRouterError::AssetPaused);
    }

    // F-6
    if to_reserve_data.configuration.is_frozen() {
        return Err(KineticRouterError::AssetFrozen);
    }

    // M-05 — use update_state_without_store to skip set_reserve_data() writes and event
    let updated_from_reserve_data =
        calculation::update_state_without_store(&env, &from_reserve_data)?;
    let updated_to_reserve_data =
        calculation::update_state_without_store(&env, &to_reserve_data)?;

    let pool_address = env.current_contract_address();

    // WP-L2: Support u128::MAX as "swap all" sentinel.
    // The upfront balance check (WP-L6) is redundant: burn_scaled_and_transfer_to already caps
    // amount_scaled to current_scaled_balance and returns actual_amount.  However, ray_div_up
    // overflows for u128::MAX, so resolve the sentinel to the real balance before the burn.
    let amount = if amount == u128::MAX {
        let mut bal_args = Vec::new(&env);
        bal_args.push_back(caller.to_val());
        bal_args.push_back(updated_from_reserve_data.liquidity_index.into_val(&env));
        let bal_result = env.try_invoke_contract::<i128, KineticRouterError>(
            &updated_from_reserve_data.a_token_address,
            &Symbol::new(&env, "balance_of_with_index"),
            bal_args,
        );
        match bal_result {
            Ok(Ok(b)) if b > 0 => safe_i128_to_u128(&env, b),
            _ => return Err(KineticRouterError::InsufficientCollateral),
        }
    } else {
        amount
    };

    let mut burn_transfer_args = Vec::new(&env);
    burn_transfer_args.push_back(pool_address.to_val());
    burn_transfer_args.push_back(caller.to_val());
    burn_transfer_args.push_back(amount.into_val(&env));
    burn_transfer_args.push_back(updated_from_reserve_data.liquidity_index.into_val(&env));
    burn_transfer_args.push_back(pool_address.to_val()); // transfer target = router

    let burn_transfer_result = env.try_invoke_contract::<(i128, i128, u128), KineticRouterError>(
        &updated_from_reserve_data.a_token_address,
        &Symbol::new(&env, "burn_scaled_and_transfer_to"),
        burn_transfer_args,
    );

    let (new_user_scaled_balance, from_supply_scaled, actual_amount) = match burn_transfer_result {
        Ok(Ok(result)) => result,
        Ok(Err(_)) | Err(_) => {
            return Err(KineticRouterError::ATokenBurnFailed)
        }
    };

    // Step 3: Execute swap via DEX or custom handler
    let swap_config = storage::get_swap_config(&env);
    let sym_transfer = symbol_short!("transfer");
    
    // WP-C1: Use actual_amount (capped by aToken) for DEX swap, not raw user-provided amount
    let actual_amount_i128 = safe_u128_to_i128(&env, actual_amount);
    let to_amount_received_i128 = if let Some(handler) = swap_handler {
        // M-01
        if !storage::is_swap_handler_whitelisted(&env, &handler) {
            return Err(KineticRouterError::UnauthorizedAMM);
        }
        // Use custom swap handler (supports any DEX)
        k2_shared::dex::swap_via_handler(
            &env,
            &handler,
            &from_asset,
            &to_asset,
            actual_amount_i128,
            safe_u128_to_i128(&env, min_amount_out),
            &pool_address,
        )?
    } else if let Some(ref factory) = swap_config.dex_factory {
        // Use Soroswap direct swap (optimized)
        k2_shared::dex::swap_exact_tokens_direct(
            &env,
            factory,
            &from_asset,
            &to_asset,
            actual_amount_i128,
            safe_u128_to_i128(&env, min_amount_out),
            &pool_address,
        )?
    } else {
        // Use Soroswap router (fallback)
        let dex_router = swap_config.dex_router.ok_or(KineticRouterError::UnauthorizedAMM)?;
        k2_shared::dex::swap_exact_tokens(
            &env,
            &dex_router,
            &from_asset,
            &to_asset,
            actual_amount_i128,
            safe_u128_to_i128(&env, min_amount_out),
            &pool_address,
            None,
        )?
    };
    let to_amount_received = safe_i128_to_u128(&env, to_amount_received_i128);

    if to_amount_received < min_amount_out {
        return Err(KineticRouterError::InsufficientSwapOut);
    }

    // Calculate protocol fee from swap output
    let protocol_fee = k2_shared::utils::percent_mul(to_amount_received, swap_config.flash_loan_premium_bps)?;

    // Ensure fee doesn't exceed swap output
    let amount_to_supply = if to_amount_received > protocol_fee {
        to_amount_received - protocol_fee
    } else {
        return Err(KineticRouterError::MathOverflow);
    };

    // F-3: Validate supply cap on destination reserve before minting aTokens
    crate::validation::validate_supply_cap_after_interest(
        &env,
        amount_to_supply,
        &updated_to_reserve_data,
        updated_to_reserve_data.liquidity_index,
    )?;

    // Transfer protocol fee to treasury if configured
    if protocol_fee > 0 {
        if let Some(treasury) = swap_config.treasury {
            let protocol_fee_i128 = safe_u128_to_i128(&env, protocol_fee);
            // Authorize router contract to transfer fee to treasury
            // Note: authorize_as_current_contract only authorizes the contract itself, not the EOA caller
            env.authorize_as_current_contract(soroban_sdk::vec![
                &env,
                soroban_sdk::auth::InvokerContractAuthEntry::Contract(
                    soroban_sdk::auth::SubContractInvocation {
                        context: soroban_sdk::auth::ContractContext {
                            contract: to_asset.clone(),
                            fn_name: sym_transfer.clone(),
                            args: soroban_sdk::vec![
                                &env,
                                pool_address.to_val(),
                                treasury.to_val(),
                                protocol_fee_i128.into_val(&env),
                            ],
                        },
                        sub_invocations: soroban_sdk::vec![&env],
                    },
                ),
            ]);

            let mut fee_transfer_args = Vec::new(&env);
            fee_transfer_args.push_back(pool_address.to_val());
            fee_transfer_args.push_back(treasury.to_val());
            fee_transfer_args.push_back(protocol_fee_i128.into_val(&env));

            let fee_transfer_result = env.try_invoke_contract::<(), KineticRouterError>(
                &to_asset,
                &sym_transfer,
                fee_transfer_args,
            );

            match fee_transfer_result {
                Ok(Ok(_)) => {}
                Ok(Err(_)) | Err(_) => {
                    return Err(KineticRouterError::UnderlyingTransferFailed);
                }
            }
        }
    }

    // Step 4: Supply the swapped asset back as collateral (minus protocol fee)
    // Authorize router contract to transfer tokens to aToken contract
    // Note: authorize_as_current_contract only authorizes the contract itself, not the EOA caller
    let amount_to_supply_i128 = safe_u128_to_i128(&env, amount_to_supply);
    env.authorize_as_current_contract(soroban_sdk::vec![
        &env,
        soroban_sdk::auth::InvokerContractAuthEntry::Contract(
            soroban_sdk::auth::SubContractInvocation {
                context: soroban_sdk::auth::ContractContext {
                    contract: to_asset.clone(),
                    fn_name: sym_transfer.clone(),
                    args: soroban_sdk::vec![
                        &env,
                        pool_address.to_val(),
                        updated_to_reserve_data.a_token_address.to_val(),
                        amount_to_supply_i128.into_val(&env),
                    ],
                },
                sub_invocations: soroban_sdk::vec![&env],
            },
        ),
    ]);

    let mut supply_transfer_args = Vec::new(&env);
    supply_transfer_args.push_back(pool_address.to_val());
    supply_transfer_args.push_back(updated_to_reserve_data.a_token_address.to_val());
    supply_transfer_args.push_back(amount_to_supply_i128.into_val(&env));

    let supply_transfer_result = env.try_invoke_contract::<(), KineticRouterError>(
        &to_asset,
        &sym_transfer,
        supply_transfer_args,
    );

    match supply_transfer_result {
        Ok(Ok(_)) => {}
        Ok(Err(_)) | Err(_) => return Err(KineticRouterError::UnderlyingTransferFailed),
    }

    // Mint aTokens for the new collateral (amount after fee deduction)
    let mut mint_args = Vec::new(&env);
    mint_args.push_back(pool_address.to_val());
    mint_args.push_back(caller.to_val());
    mint_args.push_back(amount_to_supply.into_val(&env));
    mint_args.push_back(updated_to_reserve_data.liquidity_index.into_val(&env));

    let mint_result = env.try_invoke_contract::<(bool, i128, i128), KineticRouterError>(
        &updated_to_reserve_data.a_token_address,
        &Symbol::new(&env, "mint_scaled"),
        mint_args,
    );

    let (to_user_new_scaled_balance, to_supply_scaled) = match mint_result {
        Ok(Ok((_is_first, user_scaled_bal, total_supply_scaled))) => (user_scaled_bal, total_supply_scaled),
        Ok(Err(_)) | Err(_) => {
            return Err(KineticRouterError::ATokenMintFailed)
        }
    };

    // Update user configuration to use new asset as collateral
    // Price validation moved into validate_swap_health_factor (saves 1 oracle cross-contract call)
    user_config.set_using_as_collateral(k2_shared::safe_reserve_id(&env, updated_to_reserve_data.id), true);

    // If user withdrew entire position from from_asset, disable it as collateral.
    // Use new_user_scaled_balance from burn return (more accurate than subtraction, no rounding drift).
    if new_user_scaled_balance == 0 {
        user_config.set_using_as_collateral(k2_shared::safe_reserve_id(&env, updated_from_reserve_data.id), false);
    }
    // Compute remaining underlying balance for HF validation
    let remaining_balance = if new_user_scaled_balance > 0 {
        k2_shared::ray_mul(
            &env,
            safe_i128_to_u128(&env, new_user_scaled_balance),
            updated_from_reserve_data.liquidity_index,
        )?
    } else {
        0u128
    };

    // Compute to_asset underlying balance from mint return (saves 1 balance_of_with_index CC call)
    let to_underlying_balance = if to_user_new_scaled_balance > 0 {
        k2_shared::ray_mul(
            &env,
            safe_i128_to_u128(&env, to_user_new_scaled_balance),
            updated_to_reserve_data.liquidity_index,
        )?
    } else {
        0u128
    };

    storage::set_user_configuration(&env, &caller, &user_config);

    calculation::validate_swap_health_factor(
        &env,
        &caller,
        &from_asset,
        &to_asset,
        actual_amount,
        amount_to_supply,
        &updated_from_reserve_data,
        &updated_to_reserve_data,
        &user_config,
        Some(remaining_balance),
        Some(to_underlying_balance),
    )?;

    // Update interest rates for both reserves
    calculation::update_interest_rates_and_store(&env, &from_asset, &updated_from_reserve_data, None, None)?;
    calculation::update_interest_rates_and_store(&env, &to_asset, &updated_to_reserve_data, None, None)?;

    // N-09
    Ok(amount_to_supply)
}

