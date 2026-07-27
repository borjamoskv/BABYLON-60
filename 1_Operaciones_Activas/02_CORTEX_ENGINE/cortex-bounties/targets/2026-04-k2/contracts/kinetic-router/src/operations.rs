use crate::{calculation, storage, validation};
use k2_shared::*;
use soroban_sdk::{panic_with_error, symbol_short, Address, Env, IntoVal, Symbol, Vec};

use k2_shared::safe_u128_to_i128;

const EV_SUPPLY: Symbol = symbol_short!("supply");
const EV_WITHDRAW: Symbol = symbol_short!("withdraw");
const EV_EVENT: Symbol = symbol_short!("event");

pub fn supply(
    env: Env,
    caller: Address,
    asset: Address,
    amount: u128,
    on_behalf_of: Address,
    _referral_code: u32,
) -> Result<(), KineticRouterError> {
    caller.require_auth();

    // Prevent unauthorized actions on behalf of other users
    if caller != on_behalf_of {
        on_behalf_of.require_auth();
    }

    validation::validate_reserve_whitelist_access(&env, &asset, &caller)?;
    validation::validate_reserve_blacklist_access(&env, &asset, &caller)?;
    // HIGH-003: Also validate beneficiary when delegated supply
    if caller != on_behalf_of {
        validation::validate_reserve_whitelist_access(&env, &asset, &on_behalf_of)?;
        validation::validate_reserve_blacklist_access(&env, &asset, &on_behalf_of)?;
    }

    // F-01/F-03
    let reserve_data = storage::get_reserve_data(&env, &asset)?;
    validation::validate_supply(&env, amount, &reserve_data)?;
    let updated_reserve_data = calculation::update_state(&env, &asset, &reserve_data)?;

    // Prevent supply to aToken contract to avoid circular ownership and accounting confusion
    if on_behalf_of == updated_reserve_data.a_token_address {
        panic_with_error!(&env, OperationError::RecipientIsAToken);
    }
    
    // Prevent supply to debt token contract
    if on_behalf_of == updated_reserve_data.debt_token_address {
        panic_with_error!(&env, OperationError::RecipientIsDebtToken);
    }

    // Re-validate cap after interest accrual (interest increases total supply)
    validation::validate_supply_cap_after_interest(&env, amount, &updated_reserve_data, updated_reserve_data.liquidity_index)?;

    let mut transfer_args = Vec::new(&env);
    transfer_args.push_back(env.current_contract_address().into_val(&env));
    transfer_args.push_back(caller.to_val());
    transfer_args.push_back(updated_reserve_data.a_token_address.to_val());
    transfer_args.push_back(safe_u128_to_i128(&env, amount).into_val(&env));

    let transfer_result = env.try_invoke_contract::<(), KineticRouterError>(
        &asset,
        &Symbol::new(&env, "transfer_from"),
        transfer_args,
    );

    match transfer_result {
        Ok(Ok(_)) => {}
        Ok(Err(_)) | Err(_) => return Err(KineticRouterError::UnderlyingTransferFailed),
    }

    // Mint aToken
    let mut args = Vec::new(&env);
    args.push_back(env.current_contract_address().into_val(&env));
    args.push_back(on_behalf_of.to_val());
    args.push_back(amount.into_val(&env));
    args.push_back(updated_reserve_data.liquidity_index.into_val(&env));

    let mint_result = env.try_invoke_contract::<(bool, i128, i128), KineticRouterError>(
        &updated_reserve_data.a_token_address,
        &Symbol::new(&env, "mint_scaled"),
        args,
    );

    let is_first_supply = match mint_result {
        Ok(Ok((is_first, _, _))) => is_first,
        Ok(Err(_)) | Err(_) => return Err(KineticRouterError::ATokenMintFailed),
    };

    // Incentives are now handled directly in the token contract's mint_scaled function

    // M-04: Enforce minimum first deposit to prevent share inflation attacks
    if is_first_supply && amount < k2_shared::MIN_FIRST_DEPOSIT {
        return Err(KineticRouterError::InvalidAmount);
    }

    // Update user configuration only if first time using this reserve
    // Preserve user's existing collateral preference for subsequent supplies
    if is_first_supply {
        let mut user_config = storage::get_user_configuration(&env, &on_behalf_of);
        let reserve_id = k2_shared::safe_reserve_id(&env, updated_reserve_data.id);
        
        // Check if this is a new reserve position (not already using as collateral)
        if !user_config.is_using_as_collateral(reserve_id) {
            let active_count = user_config.count_active_reserves();
            if active_count >= storage::MAX_USER_RESERVES {
                panic_with_error!(&env, UserReserveError::MaxUserReservesExceeded);
            }
        }
        
        crate::price::verify_oracle_price_exists_and_nonzero(&env, &asset)?;
        user_config.set_using_as_collateral(reserve_id, true);
        storage::set_user_configuration(&env, &on_behalf_of, &user_config);
    }

    // WP-M2: Reset liquidation tracker if user is now healthy.
    calculation::update_liquidation_tracker_if_healthy(&env, &on_behalf_of)?;

    // After supply action, recalculate interest rates based on NEW utilization
    // F-01
    calculation::update_interest_rates_and_store(&env, &asset, &updated_reserve_data, None, None)?;

    // Emit supply event
    env.events().publish(
        (EV_SUPPLY, EV_EVENT),
        SupplyEvent {
            reserve: asset,
            user: caller,
            on_behalf_of,
            amount,
            referral_code: _referral_code,
        },
    );

    Ok(())
}

pub fn withdraw(
    env: Env,
    caller: Address,
    asset: Address,
    amount: u128,
    to: Address,
) -> Result<u128, KineticRouterError> {
    caller.require_auth();

    validation::validate_reserve_whitelist_access(&env, &asset, &caller)?;
    validation::validate_reserve_blacklist_access(&env, &asset, &caller)?;
    // HIGH-003: Also validate recipient when withdrawing to different address
    if caller != to {
        validation::validate_reserve_whitelist_access(&env, &asset, &to)?;
        validation::validate_reserve_blacklist_access(&env, &asset, &to)?;
    }

    // F-01/F-03
    let reserve_data = storage::get_reserve_data(&env, &asset)?;
    validation::validate_withdraw(&env, &asset, amount, &reserve_data)?;
    let updated_reserve_data = calculation::update_state(&env, &asset, &reserve_data)?;

    // Prevent withdrawals to aToken contract to avoid fund loss
    if to == updated_reserve_data.a_token_address {
        panic_with_error!(&env, OperationError::RecipientIsAToken);
    }
    
    // Prevent withdrawals to debt token contract
    if to == updated_reserve_data.debt_token_address {
        panic_with_error!(&env, OperationError::RecipientIsDebtToken);
    }

    let mut args = Vec::new(&env);
    args.push_back(caller.to_val());
    args.push_back(updated_reserve_data.liquidity_index.into_val(&env));

    let balance_result = env.try_invoke_contract::<i128, KineticRouterError>(
        &updated_reserve_data.a_token_address,
        &Symbol::new(&env, "balance_of_with_index"),
        args,
    );

    let user_balance = match balance_result {
        Ok(Ok(value)) => value,
        Ok(Err(_)) | Err(_) => return Err(KineticRouterError::TokenCallFailed),
    };

    let user_balance_u128 = safe_i128_to_u128(&env, user_balance);

    let amount_to_withdraw = if amount == u128::MAX {
        user_balance_u128
    } else {
        amount
    };

    if user_balance_u128 < amount_to_withdraw {
        return Err(KineticRouterError::InsufficientCollateral);
    }

    let total_supply = calculation::get_total_supply_with_index(
        &env,
        &updated_reserve_data.a_token_address,
        updated_reserve_data.liquidity_index,
    )?;
    let underlying_balance = calculation::get_atoken_underlying_balance(
        &env,
        &asset,
        &updated_reserve_data.a_token_address,
    )?;

    // Check total_supply (not underlying_balance) to exclude protocol reserves
    // This prevents reserve accumulation from blocking withdrawals
    if total_supply < amount_to_withdraw {
        return Err(KineticRouterError::InsufficientLiquidity);
    }

    if underlying_balance < amount_to_withdraw {
        return Err(KineticRouterError::InsufficientLiquidity);
    }

    // Validate health factor before withdrawal to prevent unsafe positions
    // F-15
    // NEW-02
    let oracle_to_wad = calculation::get_oracle_precision_factor(&env)?;
    validation::validate_user_can_withdraw(&env, &caller, &asset, amount_to_withdraw, &updated_reserve_data, oracle_to_wad)?;
    let mut args = Vec::new(&env);
    args.push_back(env.current_contract_address().into_val(&env));
    args.push_back(caller.to_val());
    args.push_back(amount_to_withdraw.into_val(&env));
    args.push_back(updated_reserve_data.liquidity_index.into_val(&env));

    let burn_result = env.try_invoke_contract::<(bool, i128), KineticRouterError>(
        &updated_reserve_data.a_token_address,
        &Symbol::new(&env, "burn_scaled"),
        args,
    );

    match burn_result {
        Ok(Ok(_)) => {}
        Ok(Err(_)) | Err(_) => return Err(KineticRouterError::ATokenBurnFailed),
    }

    // Incentives are now handled directly in the token contract's burn_scaled function

    // Transfer underlying asset from aToken contract to user wallet
    let mut transfer_args = Vec::new(&env);
    transfer_args.push_back(env.current_contract_address().into_val(&env));
    transfer_args.push_back(to.to_val());
    transfer_args.push_back(amount_to_withdraw.into_val(&env));

    let transfer_result = env.try_invoke_contract::<bool, KineticRouterError>(
        &updated_reserve_data.a_token_address,
        &Symbol::new(&env, "transfer_underlying_to"),
        transfer_args,
    );

    match transfer_result {
        Ok(Ok(true)) => {}
        Ok(Ok(false)) | Ok(Err(_)) | Err(_) => {
            return Err(KineticRouterError::UnderlyingTransferFailed)
        }
    }

    // Disable collateral usage if user withdrew entire position
    let remaining_balance = user_balance_u128
        .checked_sub(amount_to_withdraw)
        .ok_or(KineticRouterError::MathOverflow)?;
    if remaining_balance == 0 {
        let mut user_config = storage::get_user_configuration(&env, &caller);
        user_config.set_using_as_collateral(k2_shared::safe_reserve_id(&env, updated_reserve_data.id), false);
        storage::set_user_configuration(&env, &caller, &user_config);
    }

    // Clone asset before moving it into the event
    let asset_clone = asset.clone();
    env.events().publish(
        (EV_WITHDRAW, EV_EVENT),
        WithdrawEvent {
            reserve: asset,
            user: caller,
            to,
            amount: amount_to_withdraw,
        },
    );

    // After withdraw action, recalculate interest rates based on NEW utilization
    // F-01
    calculation::update_interest_rates_and_store(&env, &asset_clone, &updated_reserve_data, None, None)?;

    Ok(amount_to_withdraw)
}

pub fn borrow(
    env: Env,
    caller: Address,
    asset: Address,
    amount: u128,
    interest_rate_mode: u32,
    _referral_code: u32,
    on_behalf_of: Address,
) -> Result<(), KineticRouterError> {
    caller.require_auth();

    // Prevent unauthorized borrowing on behalf of other users
    if caller != on_behalf_of {
        on_behalf_of.require_auth();
    }

    validation::validate_reserve_whitelist_access(&env, &asset, &caller)?;
    validation::validate_reserve_blacklist_access(&env, &asset, &caller)?;
    // HIGH-003: Also validate beneficiary when delegated borrow
    if caller != on_behalf_of {
        validation::validate_reserve_whitelist_access(&env, &asset, &on_behalf_of)?;
        validation::validate_reserve_blacklist_access(&env, &asset, &on_behalf_of)?;
    }

    // F-01/F-03
    let reserve_data = storage::get_reserve_data(&env, &asset)?;
    validation::validate_borrow(&env, amount, interest_rate_mode, &reserve_data)?;
    let updated_reserve_data = calculation::update_state(&env, &asset, &reserve_data)?;

    // Prevent borrowing to aToken contract to avoid fund loss
    if on_behalf_of == updated_reserve_data.a_token_address {
        panic_with_error!(&env, OperationError::RecipientIsAToken);
    }
    
    // Prevent borrowing to debt token contract
    if on_behalf_of == updated_reserve_data.debt_token_address {
        panic_with_error!(&env, OperationError::RecipientIsDebtToken);
    }

    // Re-validate cap after interest accrual (interest increases total debt)
    validation::validate_borrow_cap_after_interest(&env, amount, &updated_reserve_data, &asset, updated_reserve_data.variable_borrow_index)?;

    // NEW-01
    let oracle_to_wad = calculation::get_oracle_precision_factor(&env)?;
    validation::validate_user_can_borrow(&env, &on_behalf_of, &asset, amount, &updated_reserve_data, oracle_to_wad)?;

    let a_token_liquidity = calculation::get_atoken_underlying_balance(
        &env,
        &asset,
        &updated_reserve_data.a_token_address,
    )?;
    if a_token_liquidity < amount {
        return Err(KineticRouterError::InsufficientLiquidity);
    }

    let debt_token_address = updated_reserve_data.debt_token_address.clone();

    // Mint debtToken
    let mut args = Vec::new(&env);
    args.push_back(env.current_contract_address().into_val(&env));
    args.push_back(on_behalf_of.to_val());
    args.push_back(amount.into_val(&env));
    args.push_back(updated_reserve_data.variable_borrow_index.into_val(&env));

    let mint_result = env.try_invoke_contract::<(bool, i128, i128), KineticRouterError>(
        &debt_token_address,
        &Symbol::new(&env, "mint_scaled"),
        args,
    );

    match mint_result {
        Ok(Ok(_)) => {}
        Ok(Err(_)) | Err(_) => return Err(KineticRouterError::DebtTokenMintFailed),
    }

    // Incentives are now handled directly in the token contract's mint_scaled function

    // WP-L5: Enforce minimum debt after borrow to prevent dust positions.
    // Only enforced when admin has explicitly configured a minimum (val > 0).
    {
        let min_remaining_whole = updated_reserve_data.configuration.get_min_remaining_debt();
        if min_remaining_whole > 0 {
            let debt_decimals = updated_reserve_data.configuration.get_decimals() as u32;
            let debt_decimals_pow = 10_u128
                .checked_pow(debt_decimals)
                .ok_or(KineticRouterError::MathOverflow)?;
            let min_debt = (min_remaining_whole as u128)
                .checked_mul(debt_decimals_pow)
                .ok_or(KineticRouterError::MathOverflow)?;

            // Query user's total debt balance after mint
            let mut debt_bal_args = Vec::new(&env);
            debt_bal_args.push_back(on_behalf_of.to_val());
            debt_bal_args.push_back(updated_reserve_data.variable_borrow_index.into_val(&env));
            let total_debt = match env.try_invoke_contract::<i128, KineticRouterError>(
                &debt_token_address,
                &Symbol::new(&env, "balance_of_with_index"),
                debt_bal_args,
            ) {
                Ok(Ok(bal)) => safe_i128_to_u128(&env, bal),
                Ok(Err(_)) | Err(_) => return Err(KineticRouterError::TokenCallFailed),
            };

            if total_debt < min_debt {
                return Err(KineticRouterError::InvalidAmount);
            }
        }
    }

    // Transfer underlying asset from aToken contract to borrower via cross-contract invocation
    // Funds are stored in aToken contract (Aave pattern)
    let mut transfer_args = Vec::new(&env);
    transfer_args.push_back(env.current_contract_address().into_val(&env));
    transfer_args.push_back(on_behalf_of.to_val());
    transfer_args.push_back(amount.into_val(&env));

    let transfer_result = env.try_invoke_contract::<bool, KineticRouterError>(
        &updated_reserve_data.a_token_address,
        &Symbol::new(&env, "transfer_underlying_to"),
        transfer_args,
    );

    match transfer_result {
        Ok(Ok(true)) => {}
        Ok(Ok(false)) | Ok(Err(_)) | Err(_) => {
            return Err(KineticRouterError::UnderlyingTransferFailed)
        }
    }

    let mut user_config = storage::get_user_configuration(&env, &on_behalf_of);
    let reserve_id = k2_shared::safe_reserve_id(&env, updated_reserve_data.id);
    
    // Check if this is a new reserve position (not already borrowing from this reserve)
    if !user_config.is_borrowing(reserve_id) {
        // Enforce MAX_USER_RESERVES limit to prevent reserve fragmentation attacks
        let active_count = user_config.count_active_reserves();
        if active_count >= storage::MAX_USER_RESERVES {
            panic_with_error!(&env, UserReserveError::MaxUserReservesExceeded);
        }
    }
    
    user_config.set_borrowing(reserve_id, true);
    storage::set_user_configuration(&env, &on_behalf_of, &user_config);

    // After borrow action, recalculate interest rates based on NEW utilization
    // F-01
    calculation::update_interest_rates_and_store(&env, &asset, &updated_reserve_data, None, None)?;

    env.events().publish(
        (symbol_short!("borrow"), EV_EVENT),
        BorrowEvent {
            reserve: asset,
            user: caller,
            on_behalf_of,
            amount,
            borrow_rate_mode: interest_rate_mode,
            borrow_rate: updated_reserve_data.current_variable_borrow_rate,
            referral_code: _referral_code,
        },
    );

    Ok(())
}

pub fn repay(
    env: Env,
    caller: Address,
    asset: Address,
    amount: u128,
    rate_mode: u32,
    on_behalf_of: Address,
) -> Result<u128, KineticRouterError> {
    caller.require_auth();

    validation::validate_reserve_whitelist_access(&env, &asset, &caller)?;
    validation::validate_reserve_blacklist_access(&env, &asset, &caller)?;
    // MEDIUM-003: Only check whitelist (not blacklist) on on_behalf_of for repay.
    // Blacklisted borrowers must still be able to have their debt repaid by third parties
    // to prevent bad debt accumulation on positions that can't be liquidated yet.
    if caller != on_behalf_of {
        validation::validate_reserve_whitelist_access(&env, &asset, &on_behalf_of)?;
    }

    // F-01/F-03
    let reserve_data = storage::get_reserve_data(&env, &asset)?;
    validation::validate_repay(&env, &asset, amount, rate_mode, &reserve_data)?;
    let updated_reserve_data = calculation::update_state(&env, &asset, &reserve_data)?;

    let debt_token_address = updated_reserve_data.debt_token_address.clone();

    // Use balance_of_with_index with the updated borrow index to get accurate debt balance
    // The stored index in the debt token contract may be stale, so we use the updated index
    // from the reserve data which was just calculated in update_state
    let mut args = Vec::new(&env);
    args.push_back(on_behalf_of.to_val());
    args.push_back(updated_reserve_data.variable_borrow_index.into_val(&env));

    let debt_result = env.try_invoke_contract::<i128, KineticRouterError>(
        &debt_token_address,
        &Symbol::new(&env, "balance_of_with_index"),
        args,
    );

    let debt_balance = match debt_result {
        Ok(Ok(value)) => safe_i128_to_u128(&env, value),
        Ok(Err(_)) | Err(_) => return Err(KineticRouterError::TokenCallFailed),
    };

    if debt_balance == 0 {
        return Err(KineticRouterError::NoDebtOfRequestedType);
    }

    let amount_to_repay = if amount == u128::MAX {
        debt_balance
    } else {
        let tentative = amount.min(debt_balance);
        // WP-L2: If partial repay would leave dust below min_remaining_debt, revert.
        // Caller should explicitly use u128::MAX for full repay instead of being surprised.
        let remaining = debt_balance.checked_sub(tentative)
            .ok_or(KineticRouterError::MathOverflow)?;
        if remaining > 0 {
            let min_remaining_whole = updated_reserve_data.configuration.get_min_remaining_debt();
            if min_remaining_whole > 0 {
                let debt_decimals = updated_reserve_data.configuration.get_decimals() as u32;
                let debt_decimals_pow = 10_u128
                    .checked_pow(debt_decimals)
                    .ok_or(KineticRouterError::MathOverflow)?;
                let min_debt = (min_remaining_whole as u128)
                    .checked_mul(debt_decimals_pow)
                    .ok_or(KineticRouterError::MathOverflow)?;
                if remaining < min_debt {
                    panic_with_error!(&env, OperationError::RepayWouldLeaveDust);
                }
            }
        }
        tentative
    };

    let mut repay_transfer_args = Vec::new(&env);
    repay_transfer_args.push_back(env.current_contract_address().into_val(&env));
    repay_transfer_args.push_back(caller.to_val());
    repay_transfer_args.push_back(updated_reserve_data.a_token_address.to_val());
    repay_transfer_args.push_back(safe_u128_to_i128(&env, amount_to_repay).into_val(&env));

    let transfer_result = env.try_invoke_contract::<(), KineticRouterError>(
        &asset,
        &Symbol::new(&env, "transfer_from"),
        repay_transfer_args,
    );

    match transfer_result {
        Ok(Ok(_)) => {}
        Ok(Err(_)) | Err(_) => return Err(KineticRouterError::UnderlyingTransferFailed),
    }

    // Burn debtToken
    let mut args = Vec::new(&env);
    args.push_back(env.current_contract_address().into_val(&env));
    args.push_back(on_behalf_of.to_val());
    args.push_back(amount_to_repay.into_val(&env));
    args.push_back(updated_reserve_data.variable_borrow_index.into_val(&env));

    let burn_result = env.try_invoke_contract::<(bool, i128, i128), KineticRouterError>(
        &debt_token_address,
        &Symbol::new(&env, "burn_scaled"),
        args,
    );

    match burn_result {
        Ok(Ok(_)) => {}
        Ok(Err(_)) | Err(_) => {
            panic_with_error!(&env, OperationError::DebtTokenBurnFailed);
        }
    }

    // Incentives are now handled directly in the token contract's burn_scaled function

    // Update user configuration if debt is fully repaid
    let remaining_debt = debt_balance.checked_sub(amount_to_repay)
        .ok_or(KineticRouterError::MathOverflow)?;
    if remaining_debt == 0 {
        let mut user_config = storage::get_user_configuration(&env, &on_behalf_of);
        user_config.set_borrowing(k2_shared::safe_reserve_id(&env, updated_reserve_data.id), false);
        storage::set_user_configuration(&env, &on_behalf_of, &user_config);
    }

    // After repay action, recalculate interest rates based on NEW utilization
    // F-01
    calculation::update_interest_rates_and_store(&env, &asset, &updated_reserve_data, None, None)?;

    // WP-M2: Reset liquidation tracker if user is now healthy or has no more debt.
    calculation::update_liquidation_tracker_if_healthy(&env, &on_behalf_of)?;

    env.events().publish(
        (symbol_short!("repay"), EV_EVENT),
        RepayEvent {
            reserve: asset,
            user: on_behalf_of,
            repayer: caller,
            amount: amount_to_repay,
            use_a_tokens: false, // Repays use underlying asset, not aTokens
        },
    );

    Ok(amount_to_repay)
}
