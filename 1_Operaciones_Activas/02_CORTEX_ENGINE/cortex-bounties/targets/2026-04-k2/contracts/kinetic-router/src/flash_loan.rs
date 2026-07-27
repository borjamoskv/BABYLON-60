use crate::storage;
use k2_shared::*;
use soroban_sdk::{panic_with_error, token, Address, Bytes, Env, IntoVal, Symbol, Vec};

use k2_shared::{safe_i128_to_u128, safe_u128_to_i128};

pub use k2_shared::LiquidationCallbackParams;

macro_rules! require {
    ($cond:expr, $err:expr) => {
        if !$cond {
            return Err($err);
        }
    };
}

/// Follows checks-effects-interactions pattern:
/// 1. Validate parameters
/// 2. Calculate debts before transfers
/// 3. Transfer funds
/// 4. Invoke callback
/// 5. Verify repayment and transfer premium
pub fn internal_flash_loan(
    env: &Env,
    initiator: Address,
    receiver: Address,
    assets: Vec<Address>,
    amounts: Vec<u128>,
    params: Bytes,
    charge_premium: bool,
) -> Result<(), KineticRouterError> {
    internal_flash_loan_with_reserve_data(env, initiator, receiver, assets, amounts, params, charge_premium, None)
}

/// Internal flash loan with optional pre-fetched reserve data
pub fn internal_flash_loan_with_reserve_data(
    env: &Env,
    initiator: Address,
    receiver: Address,
    assets: Vec<Address>,
    amounts: Vec<u128>,
    params: Bytes,
    charge_premium: bool,
    prefetched_reserve: Option<&ReserveData>,
) -> Result<(), KineticRouterError> {
    // F-05
    let len = assets.len();
    require!(len > 0, KineticRouterError::InvalidFlashLoanParams);
    require!(amounts.len() == len, KineticRouterError::InvalidFlashLoanParams);

    let flash_loan_premium_bps = storage::get_flash_loan_premium(env);
    let treasury = storage::get_treasury(env).ok_or(KineticRouterError::TreasuryNotSet)?;

    // Calculate debts before any transfers (checks-effects-interactions pattern)
    let mut debts: Vec<FlashLoanDebt> = Vec::new(env);
    let mut premiums: Vec<u128> = Vec::new(env);

    for i in 0..assets.len().min(MAX_RESERVES) {
        let asset = assets.get(i).ok_or(KineticRouterError::InvalidFlashLoanParams)?;
        let amount = amounts.get(i).ok_or(KineticRouterError::InvalidFlashLoanParams)?;

        require!(amount > 0, KineticRouterError::InvalidAmount);

        let reserve_data = if i == 0 && prefetched_reserve.is_some() {
            prefetched_reserve.ok_or(KineticRouterError::ReserveNotFound)?.clone()
        } else {
            storage::get_reserve_data(env, &asset)?
        };

        // Validation checks (previously in validate_flash_loan_simple)
        require!(
            reserve_data.configuration.is_flashloan_enabled(),
            KineticRouterError::FlashLoanNotAuthorized
        );
        require!(
            reserve_data.configuration.is_active(),
            KineticRouterError::AssetNotActive
        );
        require!(
            !reserve_data.configuration.is_paused(),
            KineticRouterError::AssetPaused
        );

        let premium = if charge_premium {
            // L-10
            percent_mul_up(amount, flash_loan_premium_bps)?
        } else {
            0
        };

        premiums.push_back(premium);

        let underlying_balance = get_underlying_balance(env, &asset, &reserve_data.a_token_address);

        require!(
            underlying_balance >= amount,
            KineticRouterError::InsufficientFlashLoanLiquidity
        );

        debts.push_back(FlashLoanDebt {
            asset: asset.clone(),
            atoken_address: reserve_data.a_token_address.clone(),
            total_owed: amount.checked_add(premium).ok_or(KineticRouterError::MathOverflow)?,
            premium,
            initial_balance: underlying_balance,
        });
    }

    for i in 0..assets.len().min(MAX_RESERVES) {
        let asset = assets.get(i).ok_or(KineticRouterError::InvalidFlashLoanParams)?;
        let amount = amounts.get(i).ok_or(KineticRouterError::InvalidFlashLoanParams)?;
        let debt = debts.get(i).ok_or(KineticRouterError::InvalidFlashLoanParams)?;

        transfer_from_atoken(env, &asset, &debt.atoken_address, &receiver, amount)?;
    }

    // Check if receiver is the pool itself (internal flash liquidation)
    let pool_address = env.current_contract_address();
    
    // Mark flash loan state (used by update_interest_rates_and_store to skip rate recalc)
    storage::set_flash_loan_active(env, true);

    let success = if receiver == pool_address {
        // Internal execution - directly execute the callback without external invocation
        execute_operation(
            env.clone(),
            assets.clone(),
            amounts.clone(),
            premiums.clone(),
            initiator.clone(),
            params.clone(),
        )
    } else {
        // External receiver - invoke execute_operation on the receiver contract
        invoke_execute_operation(
            env,
            &receiver,
            &assets,
            &amounts,
            &premiums,
            &initiator,
            &params,
        )?
    };

    storage::set_flash_loan_active(env, false);

    require!(success, KineticRouterError::FlashLoanExecutionFailed);

    for i in 0..debts.len() {
        let debt = debts.get(i).ok_or(KineticRouterError::InvalidFlashLoanParams)?;
        
        // OPTIMIZATION: Use pre-fetched reserve data if available
        let reserve_data = if i == 0 && prefetched_reserve.is_some() {
            prefetched_reserve.ok_or(KineticRouterError::ReserveNotFound)?.clone()
        } else {
            storage::get_reserve_data(env, &debt.asset)?
        };

        verify_repayment(env, &debt.asset, &reserve_data.a_token_address, &debt)?;

        if debt.premium > 0 {
            transfer_premium_to_treasury(
                env,
                &debt.asset,
                &reserve_data.a_token_address,
                &treasury,
                debt.premium,
            )?;
        }
    }

    emit_flash_loan_event(env, &initiator, &receiver, &assets, &amounts, &premiums);

    Ok(())
}

fn get_underlying_balance(env: &Env, underlying_asset: &Address, atoken_address: &Address) -> u128 {
    let token_client = token::Client::new(env, underlying_asset);
    let balance = token_client.balance(atoken_address);
    // S-04
    safe_i128_to_u128(env, balance)
}

fn transfer_from_atoken(
    env: &Env,
    _underlying_asset: &Address,
    atoken_address: &Address,
    to: &Address,
    amount: u128,
) -> Result<(), KineticRouterError> {
    let mut args = Vec::new(env);
    args.push_back(env.current_contract_address().into_val(env));
    args.push_back(to.into_val(env));
    args.push_back(amount.into_val(env));

    let transfer_result = env.try_invoke_contract::<bool, KineticRouterError>(
        atoken_address,
        &Symbol::new(env, "transfer_underlying_to"),
        args,
    );

    match transfer_result {
        Ok(Ok(true)) => Ok(()),
        Ok(Ok(false)) | Ok(Err(_)) | Err(_) => Err(KineticRouterError::FlashLoanTransferFailed),
    }
}

fn invoke_execute_operation(
    env: &Env,
    receiver: &Address,
    assets: &Vec<Address>,
    amounts: &Vec<u128>,
    premiums: &Vec<u128>,
    initiator: &Address,
    params: &Bytes,
) -> Result<bool, KineticRouterError> {
    let mut args = Vec::new(env);
    args.push_back(assets.into_val(env));
    args.push_back(amounts.into_val(env));
    args.push_back(premiums.into_val(env));
    args.push_back(initiator.into_val(env));
    args.push_back(params.into_val(env));

    let result = env.try_invoke_contract::<bool, KineticRouterError>(
        receiver,
        &Symbol::new(env, "execute_operation"),
        args,
    );

    match result {
        Ok(Ok(success)) => Ok(success),
        Ok(Err(_)) | Err(_) => Ok(false),
    }
}

fn verify_repayment(
    env: &Env,
    underlying_asset: &Address,
    atoken_address: &Address,
    debt: &FlashLoanDebt,
) -> Result<(), KineticRouterError> {
    let current_balance = get_underlying_balance(env, underlying_asset, atoken_address);
    let expected_balance = debt.initial_balance
        .checked_add(debt.premium)
        .ok_or(KineticRouterError::MathOverflow)?;

    require!(
        current_balance >= expected_balance,
        KineticRouterError::FlashLoanNotRepaid
    );

    Ok(())
}

fn transfer_premium_to_treasury(
    env: &Env,
    _underlying_asset: &Address,
    atoken_address: &Address,
    treasury: &Address,
    premium: u128,
) -> Result<(), KineticRouterError> {
    let mut args = Vec::new(env);
    args.push_back(env.current_contract_address().into_val(env));
    args.push_back(treasury.into_val(env));
    args.push_back(premium.into_val(env));

    let transfer_result = env.try_invoke_contract::<bool, KineticRouterError>(
        atoken_address,
        &Symbol::new(env, "transfer_underlying_to"),
        args,
    );

    match transfer_result {
        Ok(Ok(true)) => Ok(()),
        Ok(Ok(false)) | Ok(Err(_)) | Err(_) => Err(KineticRouterError::FlashLoanTransferFailed),
    }
}

fn emit_flash_loan_event(
    env: &Env,
    initiator: &Address,
    receiver: &Address,
    assets: &Vec<Address>,
    amounts: &Vec<u128>,
    premiums: &Vec<u128>,
) {
    // All three vectors are built in the same loop and always have the same length.
    // Emit one event per asset so indexers can track every asset and premium.
    for i in 0..assets.len() {
        if let (Some(asset), Some(amount), Some(premium)) =
            (assets.get(i), amounts.get(i), premiums.get(i))
        {
            env.events().publish(
                (Symbol::new(env, "flash_loan"), initiator, asset),
                (receiver.clone(), amount, premium),
            );
        }
    }
}

/// Internal flash loan callback for liquidations
pub fn execute_operation(
    env: Env,
    _assets: Vec<Address>,
    _amounts: Vec<u128>,
    premiums: Vec<u128>,
    initiator: Address,
    _params: soroban_sdk::Bytes,
) -> bool {
    if !storage::is_flash_loan_active(&env) {
        return false;
    }
    
    let pool_address = env.current_contract_address();

    if initiator != pool_address {
        return false;
    }

    // Internal liquidation flash loans must have zero premiums
    for i in 0..premiums.len() {
        match premiums.get(i) {
            Some(0) => continue,
            _ => return false, // non-zero premium or missing entry → reject
        }
    }

    let callback_params = match storage::get_liquidation_callback_params(&env) {
        Some(p) => p,
        None => return false,
    };

    let result = execute_liquidation_callback(env.clone(), callback_params);
    
    // Always clear params to prevent replay
    storage::remove_liquidation_callback_params(&env);
    
    match result {
        Ok(_) => true,
        Err(_) => false,
    }
}

fn execute_liquidation_callback(
    env: Env,
    params: LiquidationCallbackParams,
) -> Result<(), KineticRouterError> {
    use soroban_sdk::symbol_short;
    
    let pool_address = env.current_contract_address();

    // Cache symbols once (reused multiple times)
    let sym_transfer = symbol_short!("transfer");
    let sym_burn_scaled = Symbol::new(&env, "burn_scaled");
    let sym_burn_scaled_and_transfer = Symbol::new(&env, "burn_scaled_and_transfer_to");

    let debt_reserve_data = &params.debt_reserve_data;
    let collateral_reserve_data = &params.collateral_reserve_data;
    
    if params.debt_to_cover == 0 || params.collateral_to_seize == 0 {
        return Err(KineticRouterError::InvalidAmount);
    }
    
    if params.debt_price == 0 || params.collateral_price == 0 {
        return Err(KineticRouterError::PriceOracleNotFound);
    }

    // Burn debt token
    let burn_debt_args = soroban_sdk::vec![
        &env,
        pool_address.to_val(),
        params.user.to_val(),
        params.debt_to_cover.into_val(&env),
        debt_reserve_data.variable_borrow_index.into_val(&env),
    ];

    let burn_result = env.try_invoke_contract::<(bool, i128, i128), KineticRouterError>(
        &debt_reserve_data.debt_token_address,
        &sym_burn_scaled,
        burn_debt_args,
    );

    let (_burn_ok, debt_total_scaled, user_remaining_debt_scaled) =
        invoke_or_err(burn_result, KineticRouterError::DebtTokenMintFailed)?;

    // Burn aTokens and transfer collateral to pool
    // params.collateral_to_seize is already validated by router
    let burn_and_transfer_args = soroban_sdk::vec![
        &env,
        pool_address.to_val(),
        params.user.to_val(),
        params.collateral_to_seize.into_val(&env),
        collateral_reserve_data.liquidity_index.into_val(&env),
        pool_address.to_val(),
    ];

    let burn_and_transfer_result = env.try_invoke_contract::<(i128, i128, u128), KineticRouterError>(
        &collateral_reserve_data.a_token_address,
        &sym_burn_scaled_and_transfer,
        burn_and_transfer_args,
    );

    let (user_remaining_collateral_scaled, collateral_total_scaled, actual_collateral) = invoke_or_err(
        burn_and_transfer_result,
        KineticRouterError::ATokenBurnFailed,
    )?;

    // Store scaled supplies + user remaining balances for optimization (avoids cross-contract calls)
    storage::set_liquidation_scaled_supplies(
        &env, debt_total_scaled, collateral_total_scaled,
        user_remaining_collateral_scaled, user_remaining_debt_scaled,
    );

    // Execute swap via DEX router or custom handler
    // WP-C1: Use actual_collateral (returned from burn) instead of params.collateral_to_seize
    // to prevent swap amount desync when rounding causes actual < requested
    let debt_received_i128 = if let Some(handler) = &params.swap_handler {
        // M-01
        if !storage::is_swap_handler_whitelisted(&env, handler) {
            return Err(KineticRouterError::UnauthorizedAMM);
        }
        // Use custom swap handler (supports any DEX)
        k2_shared::dex::swap_via_handler(
            &env,
            handler,
            &params.collateral_asset,
            &params.debt_asset,
            safe_u128_to_i128(&env, actual_collateral),
            safe_u128_to_i128(&env, params.min_swap_out),
            &pool_address,
        )?
    } else if let Some(factory) = storage::get_dex_factory(&env) {
        k2_shared::dex::swap_exact_tokens_direct(
            &env,
            &factory,
            &params.collateral_asset,
            &params.debt_asset,
            safe_u128_to_i128(&env, actual_collateral),
            safe_u128_to_i128(&env, params.min_swap_out),
            &pool_address,
        )?
    } else {
        let router = storage::get_dex_router(&env)
            .ok_or(KineticRouterError::UnauthorizedAMM)?;
        k2_shared::dex::swap_exact_tokens(
            &env,
            &router,
            &params.collateral_asset,
            &params.debt_asset,
            safe_u128_to_i128(&env, actual_collateral),
            safe_u128_to_i128(&env, params.min_swap_out),
            &pool_address,
            None,
        )?
    };
    
    let debt_received = u128::try_from(debt_received_i128)
        .map_err(|_| KineticRouterError::InvalidAmount)?;

    if debt_received < params.min_swap_out {
        return Err(KineticRouterError::InsufficientSwapOut);
    }

    // M-05: Enforce oracle-based slippage minimum
    // Convert collateral value to expected debt units, accounting for decimal differences.
    // Formula: actual_collateral * collateral_price * debt_decimals_pow * min_swap_bps
    //          / (debt_price * collateral_decimals_pow * BASIS_POINTS_MULTIPLIER)
    let min_swap_bps = storage::get_min_swap_output_bps(&env);
    let collateral_decimals_pow = collateral_reserve_data.configuration.get_decimals_pow()?;
    let debt_decimals_pow = debt_reserve_data.configuration.get_decimals_pow()?;
    let oracle_min_out = {
        let cs = soroban_sdk::U256::from_u128(&env, actual_collateral);
        let cp = soroban_sdk::U256::from_u128(&env, params.collateral_price);
        let ddp = soroban_sdk::U256::from_u128(&env, debt_decimals_pow);
        let bps = soroban_sdk::U256::from_u128(&env, min_swap_bps);
        let dp = soroban_sdk::U256::from_u128(&env, params.debt_price);
        let cdp = soroban_sdk::U256::from_u128(&env, collateral_decimals_pow);
        let bps_mult = soroban_sdk::U256::from_u128(&env, BASIS_POINTS_MULTIPLIER);
        cs.mul(&cp).mul(&ddp).mul(&bps).div(&dp).div(&cdp).div(&bps_mult)
            .to_u128().ok_or(KineticRouterError::MathOverflow)?
    };
    if debt_received < oracle_min_out {
        return Err(KineticRouterError::InsufficientSwapOut);
    }

    // Protocol fee = base flash loan premium + optional flash liquidation surcharge
    let base_fee_bps = storage::get_flash_loan_premium(&env);
    let liq_surcharge_bps = storage::get_flash_liquidation_premium(&env);
    let protocol_fee_bps = base_fee_bps.checked_add(liq_surcharge_bps).ok_or(KineticRouterError::MathOverflow)?;
    // L-10: round fee UP to favor protocol (consistent with regular flash loan premium)
    let protocol_fee = percent_mul_up(params.debt_to_cover, protocol_fee_bps)?;
    let liquidator_repayment = params.debt_to_cover.checked_add(protocol_fee).ok_or(KineticRouterError::MathOverflow)?;

    let profit_in_debt = debt_received
        .checked_sub(liquidator_repayment)
        .ok_or(KineticRouterError::MinProfitNotMet)?;

    // Repay debt: transfer debt asset to aToken
    let repay_transfer_args = soroban_sdk::vec![
        &env,
        pool_address.to_val(),
        debt_reserve_data.a_token_address.to_val(),
        safe_u128_to_i128(&env, params.debt_to_cover).into_val(&env),
    ];

    let repay_transfer_result = env.try_invoke_contract::<(), KineticRouterError>(
        &params.debt_asset,
        &sym_transfer,
        repay_transfer_args,
    );

    invoke_or_err(
        repay_transfer_result,
        KineticRouterError::UnderlyingTransferFailed,
    )?;

    if protocol_fee > 0 {
        if let Some(treasury) = storage::get_treasury(&env) {
            let fee_transfer_args = soroban_sdk::vec![
                &env,
                pool_address.to_val(),
                treasury.to_val(),
                safe_u128_to_i128(&env, protocol_fee).into_val(&env),
            ];

            let fee_transfer_result = env.try_invoke_contract::<(), KineticRouterError>(
                &params.debt_asset,
                &sym_transfer,
                fee_transfer_args,
            );

            invoke_or_err(
                fee_transfer_result,
                KineticRouterError::UnderlyingTransferFailed,
            )?;
        }
    }

    if profit_in_debt > 0 {
        let profit_transfer_args = soroban_sdk::vec![
            &env,
            pool_address.to_val(),
            params.liquidator.to_val(),
            safe_u128_to_i128(&env, profit_in_debt).into_val(&env),
        ];

        let profit_transfer_result = env.try_invoke_contract::<(), KineticRouterError>(
            &params.debt_asset,
            &sym_transfer,
            profit_transfer_args,
        );

        invoke_or_err(
            profit_transfer_result,
            KineticRouterError::UnderlyingTransferFailed,
        )?;
    }

    Ok(())
}

#[inline(always)]
fn invoke_or_err<T, E>(
    result: Result<Result<T, E>, Result<KineticRouterError, soroban_sdk::InvokeError>>,
    error: KineticRouterError,
) -> Result<T, KineticRouterError> {
    match result {
        Ok(Ok(val)) => Ok(val),
        _ => Err(error),
    }
}

