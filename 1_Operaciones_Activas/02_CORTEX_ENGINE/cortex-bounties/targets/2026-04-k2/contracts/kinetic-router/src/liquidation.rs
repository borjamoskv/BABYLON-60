use crate::{calculation, storage, validation};
use k2_shared::*;
use soroban_sdk::{contracterror, panic_with_error, symbol_short, Address, Env, IntoVal, Map, Symbol, U256, Vec};

use k2_shared::safe_u128_to_i128;

const EV_EVENT: u32 = 1;

/// WP-M2: Validate close factor and check debt_to_cover doesn't exceed max liquidatable amount.
/// Shared by: internal_liquidation_call, prepare_liquidation, execute_liquidation.
pub(crate) fn validate_close_factor(
    env: &Env,
    user: &Address,
    health_factor: u128,
    individual_debt_base: u128,
    individual_collateral_base: u128,
    debt_to_cover_base: u128,
) -> Result<(), KineticRouterError> {
    let partial_liq_threshold = storage::get_partial_liquidation_hf_threshold(env);
    let close_factor = if individual_debt_base < MIN_CLOSE_FACTOR_THRESHOLD
        || individual_collateral_base < MIN_CLOSE_FACTOR_THRESHOLD
        || health_factor < partial_liq_threshold {
        MAX_LIQUIDATION_CLOSE_FACTOR
    } else {
        DEFAULT_LIQUIDATION_CLOSE_FACTOR
    };

    let previously_liquidated = storage::get_user_liquidation_amount(env, user);
    
    // Initial debt = current debt + amount already liquidated in this ledger
    let initial_debt_base = individual_debt_base
        .checked_add(previously_liquidated)
        .ok_or(KineticRouterError::MathOverflow)?;

    let max_liquidatable_debt = initial_debt_base
        .checked_mul(close_factor)
        .ok_or(KineticRouterError::MathOverflow)?
        .checked_div(BASIS_POINTS_MULTIPLIER)
        .ok_or(KineticRouterError::MathOverflow)?;

    // Cumulative liquidation must not exceed close factor limit
    let total_liquidated_base = previously_liquidated
        .checked_add(debt_to_cover_base)
        .ok_or(KineticRouterError::MathOverflow)?;

    if total_liquidated_base > max_liquidatable_debt {
        return Err(KineticRouterError::LiquidationAmountTooHigh);
    }

    Ok(())
}

/// F-09: Liquidation-specific errors
#[contracterror]
#[derive(Copy, Clone, Debug, Eq, PartialEq, PartialOrd, Ord)]
#[repr(u32)]
pub enum LiquidationError {
    LeavesTooLittleDebt = 1,  // Partial liquidation would leave dust debt below minimum threshold
}

fn address_to_asset(_env: &Env, address: &Address) -> Asset {
    Asset::Stellar(address.clone())
}

pub fn get_asset_prices_batch(
    env: &Env,
    debt_asset: &Address,
    collateral_asset: &Address,
) -> Result<(PriceData, PriceData), KineticRouterError> {
    let price_oracle_address = storage::get_price_oracle_opt(env)
        .ok_or(KineticRouterError::PriceOracleNotFound)?;

    let debt_asset_type = address_to_asset(env, debt_asset);
    let collateral_asset_type = address_to_asset(env, collateral_asset);

    let mut assets_vec = Vec::new(env);
    assets_vec.push_back(debt_asset_type.clone());
    assets_vec.push_back(collateral_asset_type.clone());

    let mut args = Vec::new(env);
    args.push_back(assets_vec.into_val(env));

    let sym_get_prices = Symbol::new(env, "get_asset_prices_vec");
    let price_result = env.try_invoke_contract::<Vec<PriceData>, KineticRouterError>(
        &price_oracle_address,
        &sym_get_prices,
        args,
    );

    let prices_vec = match price_result {
        Ok(Ok(pv)) => pv,
        Ok(Err(_)) => return Err(KineticRouterError::PriceOracleError),
        Err(_) => return Err(KineticRouterError::PriceOracleInvocationFailed),
    };

    if prices_vec.len() != 2 {
        return Err(KineticRouterError::PriceOracleError);
    }

    let debt_price_data = prices_vec
        .get(0)
        .ok_or(KineticRouterError::PriceOracleError)?;
    let collateral_price_data = prices_vec
        .get(1)
        .ok_or(KineticRouterError::PriceOracleError)?;

    // N-04
    crate::price::validate_price_freshness(env, debt_price_data.timestamp, Some(debt_asset))?;
    crate::price::validate_price_freshness(env, collateral_price_data.timestamp, Some(collateral_asset))?;

    Ok((debt_price_data, collateral_price_data))
}

pub fn liquidation_call(
    env: Env,
    liquidator: Address,
    collateral_asset: Address,
    debt_asset: Address,
    user: Address,
    debt_to_cover: u128,
    _receive_a_token: bool,
) -> Result<(), KineticRouterError> {
    liquidator.require_auth();

    internal_liquidation_call(
        &env,
        liquidator,
        collateral_asset,
        debt_asset,
        user,
        debt_to_cover,
        _receive_a_token,
    )
}

fn internal_liquidation_call(
    env: &Env,
    liquidator: Address,
    collateral_asset: Address,
    debt_asset: Address,
    user: Address,
    debt_to_cover: u128,
    _receive_a_token: bool,
) -> Result<(), KineticRouterError> {
    validation::validate_liquidation_whitelist_access(env, &liquidator)?;
    validation::validate_liquidation_blacklist_access(env, &liquidator)?;

    // Get fresh prices for health factor calculation
    let (debt_price_data, collateral_price_data) =
        get_asset_prices_batch(env, &debt_asset, &collateral_asset)?;
    let debt_price = debt_price_data.price;
    let collateral_price = collateral_price_data.price;

    if collateral_price == 0 || debt_price == 0 {
        return Err(KineticRouterError::PriceOracleError);
    }

    // Fetch reserve data BEFORE calculating health factor to avoid duplicate reads
    let debt_reserve_data = storage::get_reserve_data(env, &debt_asset)?;
    let collateral_reserve_data = storage::get_reserve_data(env, &collateral_asset)?;

    // Update state at the beginning (consistent with supply/withdraw/borrow)
    let updated_debt_reserve_data =
        calculation::update_state(env, &debt_asset, &debt_reserve_data)?;
    let updated_collateral_reserve_data =
        calculation::update_state(env, &collateral_asset, &collateral_reserve_data)?;

    // Calculate health factor with fresh prices using unified function
    // Pass pre-fetched prices and updated reserve data to avoid duplicate reads
    let mut known_prices = Map::new(env);
    known_prices.set(collateral_asset.clone(), collateral_price);
    known_prices.set(debt_asset.clone(), debt_price);
    
    let mut known_reserves = Map::new(env);
    known_reserves.set(collateral_asset.clone(), updated_collateral_reserve_data.clone());
    known_reserves.set(debt_asset.clone(), updated_debt_reserve_data.clone());
    
    // NEW-03
    let oracle_to_wad = crate::calculation::get_oracle_precision_factor(env)?;

    let params = calculation::AccountDataParams {
        known_prices: Some(&known_prices),
        known_reserves: Some(&known_reserves),
        user_config: None,
        extra_assets: None,
        return_prices: false,
        known_balances: None,
    };

    let result = calculation::calculate_user_account_data_unified(env, &user, params)?;
    let user_account_data = result.account_data;
    let balance_cache = result.balance_cache;

    if user_account_data.health_factor >= WAD {
        return Err(KineticRouterError::InvalidLiquidation);
    }

    validation::validate_liquidation(
        env,
        &collateral_asset,
        &debt_asset,
        &user,
        debt_to_cover,
        Some(&updated_collateral_reserve_data),
        Some(&updated_debt_reserve_data),
    )?;

    let user_collateral_balance = balance_cache
        .try_get(collateral_asset.clone())
        .ok()
        .flatten()
        .map(|(coll, _)| coll)
        .ok_or(KineticRouterError::InsufficientCollateral)?;

    let debt_balance = {
        let (_, debt_u128) = balance_cache
            .try_get(debt_asset.clone())
            .ok()
            .flatten()
            .ok_or(KineticRouterError::NoDebtOfRequestedType)?;
        safe_u128_to_i128(env, debt_u128)
    };

    // Get decimals for close factor validation and protocol fee calculation
    let debt_decimals = updated_debt_reserve_data.configuration.get_decimals() as u32;
    let collateral_decimals = updated_collateral_reserve_data.configuration.get_decimals() as u32;

    let debt_decimals_pow = 10_u128
        .checked_pow(debt_decimals)
        .ok_or(KineticRouterError::MathOverflow)?;
    let collateral_decimals_pow = 10_u128
        .checked_pow(collateral_decimals)
        .ok_or(KineticRouterError::MathOverflow)?;

    // C-01 / WP-M2: Close factor validation
    let individual_debt_base = calculation::value_in_base(
        env, safe_i128_to_u128(env, debt_balance), debt_price, oracle_to_wad, debt_decimals_pow,
    )?;
    let individual_collateral_base = calculation::value_in_base(
        env, user_collateral_balance, collateral_price, oracle_to_wad, collateral_decimals_pow,
    )?;
    let debt_to_cover_base = calculation::value_in_base(
        env, debt_to_cover, debt_price, oracle_to_wad, debt_decimals_pow,
    )?;
    validate_close_factor(
        env, &user, user_account_data.health_factor,
        individual_debt_base, individual_collateral_base, debt_to_cover_base,
    )?;

    let debt_to_cover = {
        let dtc_i128 = safe_u128_to_i128(env, debt_to_cover);
        let remaining = debt_balance
            .checked_sub(dtc_i128)
            .ok_or(KineticRouterError::MathOverflow)?;
        if remaining > 0 {
            let remaining_u128 = safe_i128_to_u128(env, remaining);
            let min_remaining_whole = updated_debt_reserve_data.configuration.get_min_remaining_debt();
            if min_remaining_whole > 0 {
                let min_remaining_debt_val = (min_remaining_whole as u128)
                    .checked_mul(debt_decimals_pow)
                    .ok_or(KineticRouterError::MathOverflow)?;
                if remaining_u128 < min_remaining_debt_val {
                    safe_i128_to_u128(env, debt_balance)
                } else {
                    debt_to_cover
                }
            } else {
                debt_to_cover
            }
        } else {
            debt_to_cover
        }
    };

    // Calculate collateral to seize using the correct liquidation calculation function
    // This includes the liquidation bonus (e.g., 5%) and proper price conversions
    let (_collateral_amount, collateral_amount_to_transfer) =
        calculation::calculate_liquidation_amounts_with_reserves(
            env,
            &updated_collateral_reserve_data,
            &updated_debt_reserve_data,
            debt_to_cover,
            collateral_price,
            debt_price,
            oracle_to_wad,
        )?;

    // M-08
    // H-05
    let collateral_cap_triggered;
    let (debt_to_cover, collateral_amount_to_transfer) = if collateral_amount_to_transfer > user_collateral_balance {
        collateral_cap_triggered = true;
        // N-08
        // Formula: ceil(dtc * ucb / cat) = (dtc * ucb + cat - 1) / cat
        let adjusted_debt = {
            let dtc = U256::from_u128(&env, debt_to_cover);
            let ucb = U256::from_u128(&env, user_collateral_balance);
            let cat = U256::from_u128(&env, collateral_amount_to_transfer);
            let one = U256::from_u128(&env, 1u128);
            dtc.mul(&ucb).add(&cat).sub(&one).div(&cat)
                .to_u128()
                .ok_or(KineticRouterError::MathOverflow)?
        };
        (adjusted_debt, user_collateral_balance)
    } else {
        collateral_cap_triggered = false;
        (debt_to_cover, collateral_amount_to_transfer)
    };

    // Liquidator transfers debt asset directly to aToken contract
    // (Debt must be fully repaid to maintain proper aToken accounting)
    let mut liquidation_transfer_args = Vec::new(env);
    liquidation_transfer_args.push_back(IntoVal::into_val(&env.current_contract_address(), env));
    liquidation_transfer_args.push_back(liquidator.to_val());
    liquidation_transfer_args.push_back(updated_debt_reserve_data.a_token_address.to_val());
        liquidation_transfer_args.push_back(IntoVal::into_val(&safe_u128_to_i128(env, debt_to_cover), env));

    let transfer_result = env.try_invoke_contract::<(), KineticRouterError>(
        &debt_asset,
        &Symbol::new(env, "transfer_from"),
        liquidation_transfer_args,
    );

    match transfer_result {
        Ok(Ok(_)) => {}
        Ok(Err(_)) | Err(_) => {
            return Err(KineticRouterError::UnderlyingTransferFailed);
        }
    }

    // State already updated at the beginning, no need to update again

    // Burn debtToken
    let mut args = Vec::new(env);
    args.push_back(IntoVal::into_val(&env.current_contract_address(), env));
    args.push_back(user.to_val());
    args.push_back(IntoVal::into_val(&debt_to_cover, env));
    args.push_back(IntoVal::into_val(
        &updated_debt_reserve_data.variable_borrow_index,
        env,
    ));

    let debt_burn_result = env.try_invoke_contract::<(bool, i128, i128), KineticRouterError>(
        &updated_debt_reserve_data.debt_token_address,
        &Symbol::new(env, "burn_scaled"),
        args,
    );

    let mut debt_token_scaled_total: Option<u128>;
    match debt_burn_result {
        Ok(Ok((_is_zero, total_scaled, _user_remaining))) => {
            debt_token_scaled_total = Some(safe_i128_to_u128(env, total_scaled));
        }
        Ok(Err(_)) | Err(_) => {
            return Err(KineticRouterError::InsufficientCollateral)
        }
    }

    // Incentives are now handled directly in the token contract's burn_scaled function

    // Calculate protocol fee from liquidation premium.
    // Fee is taken from collateral bonus (not debt repayment) to maintain proper accounting.
    let protocol_fee_bps = storage::get_flash_loan_premium(env);

    let (protocol_fee_collateral, liquidator_collateral) = if protocol_fee_bps == 0 {
        (0u128, collateral_amount_to_transfer)
    } else {
        // M-07: Round UP to favor protocol
        let protocol_fee_debt = percent_mul_up(debt_to_cover, protocol_fee_bps)?;

        let protocol_fee_collateral = {
            let pfd = U256::from_u128(&env, protocol_fee_debt);
            let dp = U256::from_u128(&env, debt_price);
            let cdp = U256::from_u128(&env, collateral_decimals_pow);
            let cp = U256::from_u128(&env, collateral_price);
            let ddp = U256::from_u128(&env, debt_decimals_pow);
            pfd.mul(&dp).mul(&cdp).div(&cp).div(&ddp)
                .to_u128()
                .ok_or(KineticRouterError::MathOverflow)?
        };

        let liquidator_collateral = if collateral_amount_to_transfer > protocol_fee_collateral {
            collateral_amount_to_transfer.checked_sub(protocol_fee_collateral).ok_or(KineticRouterError::MathOverflow)?
        } else {
            return Err(KineticRouterError::MathOverflow);
        };

        (protocol_fee_collateral, liquidator_collateral)
    };

    let collateral_reserve_id = k2_shared::safe_reserve_id(env, updated_collateral_reserve_data.id);
    let mut a_token_scaled_total: Option<u128>;

    // MEDIUM-1: Track how much collateral was actually removed from the user's balance.
    // In the receive_a_token path, if no treasury is configured the fee stays with the borrower.
    let effective_collateral_removed;

    if _receive_a_token {
        // WP-M3: Transfer aTokens from borrower to liquidator (no underlying movement)
        let mut xfer_args = Vec::new(env);
        xfer_args.push_back(IntoVal::into_val(&env.current_contract_address(), env));
        xfer_args.push_back(user.to_val());
        xfer_args.push_back(liquidator.to_val());
        xfer_args.push_back(IntoVal::into_val(&liquidator_collateral, env));
        xfer_args.push_back(IntoVal::into_val(
            &updated_collateral_reserve_data.liquidity_index,
            env,
        ));

        let xfer_result = env.try_invoke_contract::<bool, KineticRouterError>(
            &updated_collateral_reserve_data.a_token_address,
            &Symbol::new(env, "transfer_on_liquidation"),
            xfer_args,
        );

        let is_first_balance = match xfer_result {
            Ok(Ok(is_first)) => is_first,
            Ok(Err(_)) | Err(_) => {
                return Err(KineticRouterError::InsufficientCollateral)
            }
        };

        // Update liquidator UserConfiguration after receiving aTokens
        if is_first_balance {
            let mut liq_config = storage::get_user_configuration(env, &liquidator);
            if !liq_config.is_using_as_collateral(collateral_reserve_id) {
                let active = liq_config.count_active_reserves();
                if active >= storage::MAX_USER_RESERVES {
                    return Err(KineticRouterError::InvalidLiquidation);
                }
                liq_config.set_using_as_collateral(collateral_reserve_id, true);
                storage::set_user_configuration(env, &liquidator, &liq_config);
            }
        }

        // WP-O7: Protocol fee collected as aTokens (not underlying) when receive_a_token=true.
        // Burning + transfer_underlying_to can fail if aToken holds insufficient underlying.
        // Instead, transfer aTokens from borrower to treasury (no underlying movement needed).
        // MEDIUM-1: Track whether fee was actually transferred away from borrower.
        let actually_transferred_fee = if protocol_fee_collateral > 0 {
            if let Some(treasury) = storage::get_treasury(env) {
                let mut fee_xfer_args = Vec::new(env);
                fee_xfer_args.push_back(IntoVal::into_val(&env.current_contract_address(), env));
                fee_xfer_args.push_back(user.to_val());
                fee_xfer_args.push_back(treasury.to_val());
                fee_xfer_args.push_back(IntoVal::into_val(&protocol_fee_collateral, env));
                fee_xfer_args.push_back(IntoVal::into_val(
                    &updated_collateral_reserve_data.liquidity_index,
                    env,
                ));

                let fee_xfer_result = env.try_invoke_contract::<bool, KineticRouterError>(
                    &updated_collateral_reserve_data.a_token_address,
                    &Symbol::new(env, "transfer_on_liquidation"),
                    fee_xfer_args,
                );

                match fee_xfer_result {
                    Ok(Ok(is_first_treasury)) => {
                        // LOW-1: Update treasury UserConfiguration if this is its first aToken balance
                        if is_first_treasury {
                            let mut treasury_config = storage::get_user_configuration(env, &treasury);
                            if !treasury_config.is_using_as_collateral(collateral_reserve_id) {
                                let active = treasury_config.count_active_reserves();
                                if active < storage::MAX_USER_RESERVES {
                                    treasury_config.set_using_as_collateral(collateral_reserve_id, true);
                                    storage::set_user_configuration(env, &treasury, &treasury_config);
                                } else {
                                    // Emit monitoring event — treasury bitmap full
                                    env.events().publish(
                                        (symbol_short!("trs_skip"), treasury.clone()),
                                        collateral_reserve_id as u32,
                                    );
                                }
                            }
                        }
                    }
                    Ok(Err(_)) | Err(_) => {
                        return Err(KineticRouterError::InsufficientCollateral)
                    }
                }
                protocol_fee_collateral
            } else {
                // No treasury configured — fee stays with borrower
                0u128
            }
        } else {
            0u128
        };
        // transfer_on_liquidation doesn't change total supply, so query it once
        // to avoid an extra cross-contract call in update_interest_rates_and_store.
        a_token_scaled_total = Some(calculation::get_scaled_total_supply(
            env,
            &updated_collateral_reserve_data.a_token_address,
        )?);
        effective_collateral_removed = liquidator_collateral
            .checked_add(actually_transferred_fee)
            .ok_or(KineticRouterError::MathOverflow)?;
    } else {
        // Original path: burn aTokens + transfer underlying to liquidator
        let mut burn_args = Vec::new(env);
        burn_args.push_back(IntoVal::into_val(&env.current_contract_address(), env));
        burn_args.push_back(user.to_val());
        burn_args.push_back(IntoVal::into_val(&collateral_amount_to_transfer, env));
        burn_args.push_back(IntoVal::into_val(
            &updated_collateral_reserve_data.liquidity_index,
            env,
        ));

        let burn_result = env.try_invoke_contract::<(bool, i128), KineticRouterError>(
            &updated_collateral_reserve_data.a_token_address,
            &Symbol::new(env, "burn_scaled"),
            burn_args,
        );

        match burn_result {
            Ok(Ok((_is_zero, total_scaled))) => {
                a_token_scaled_total = Some(safe_i128_to_u128(env, total_scaled));
            }
            Ok(Err(_)) | Err(_) => {
                return Err(KineticRouterError::InsufficientCollateral)
            }
        }

        // Transfer protocol fee to treasury if configured.
        if protocol_fee_collateral > 0 {
            if let Some(treasury) = storage::get_treasury(env) {
                let mut fee_transfer_args = Vec::new(env);
                fee_transfer_args.push_back(IntoVal::into_val(&env.current_contract_address(), env));
                fee_transfer_args.push_back(treasury.to_val());
                fee_transfer_args.push_back(IntoVal::into_val(&protocol_fee_collateral, env));

                let fee_transfer_result = env.try_invoke_contract::<bool, KineticRouterError>(
                    &updated_collateral_reserve_data.a_token_address,
                    &Symbol::new(env, "transfer_underlying_to"),
                    fee_transfer_args,
                );

                match fee_transfer_result {
                    Ok(Ok(true)) => {}
                    Ok(Ok(false)) | Ok(Err(_)) | Err(_) => {
                        return Err(KineticRouterError::UnderlyingTransferFailed);
                    }
                }
            }
        }

        // Transfer remaining collateral (with bonus minus protocol fee) to liquidator.
        let mut transfer_args = Vec::new(env);
        transfer_args.push_back(IntoVal::into_val(&env.current_contract_address(), env));
        transfer_args.push_back(liquidator.to_val());
        transfer_args.push_back(IntoVal::into_val(&liquidator_collateral, env));

        let transfer_result = env.try_invoke_contract::<bool, KineticRouterError>(
            &updated_collateral_reserve_data.a_token_address,
            &Symbol::new(env, "transfer_underlying_to"),
            transfer_args,
        );

        match transfer_result {
            Ok(Ok(true)) => {}
            Ok(Ok(false)) | Ok(Err(_)) | Err(_) => {
                return Err(KineticRouterError::UnderlyingTransferFailed);
            }
        }
        // In burn path, full collateral_amount_to_transfer is always burned from user
        effective_collateral_removed = collateral_amount_to_transfer;
    }

    // MEDIUM-1: Use effective_collateral_removed instead of collateral_amount_to_transfer.
    // In receive_a_token path, if treasury is None the fee stays with borrower so
    // only liquidator_collateral was actually removed from the user's balance.
    let remaining_collateral_balance = user_collateral_balance
        .checked_sub(effective_collateral_removed)
        .ok_or(KineticRouterError::InsufficientCollateral)?;
    if remaining_collateral_balance == 0 {
        let mut user_config = storage::get_user_configuration(env, &user);
        user_config.set_using_as_collateral(collateral_reserve_id, false);
        storage::set_user_configuration(env, &user, &user_config);
    }

    let debt_to_cover_i128 = safe_u128_to_i128(env, debt_to_cover);
    let mut remaining_debt_balance = debt_balance
        .checked_sub(debt_to_cover_i128)
        .ok_or(KineticRouterError::MathOverflow)?;
    
    // H-02: Post-burn bad debt socialization.
    // When collateral_cap_triggered, ALL remaining debt is unrecoverable (no collateral left
    // for another liquidation). Socialize unconditionally — threshold is irrelevant here.
    let min_remaining_whole = updated_debt_reserve_data.configuration.get_min_remaining_debt();
    if remaining_debt_balance > 0 {
        let remaining_debt_u128 = safe_i128_to_u128(env, remaining_debt_balance);
        if collateral_cap_triggered {
            // H-05: All collateral seized — remaining debt is unrecoverable bad debt.
            let mut bad_debt_burn_args = Vec::new(env);
            bad_debt_burn_args.push_back(IntoVal::into_val(&env.current_contract_address(), env));
            bad_debt_burn_args.push_back(user.to_val());
            bad_debt_burn_args.push_back(IntoVal::into_val(&remaining_debt_u128, env));
            bad_debt_burn_args.push_back(IntoVal::into_val(
                &updated_debt_reserve_data.variable_borrow_index,
                env,
            ));

            let bad_debt_burn_result = env.try_invoke_contract::<(bool, i128, i128), KineticRouterError>(
                &updated_debt_reserve_data.debt_token_address,
                &Symbol::new(env, "burn_scaled"),
                bad_debt_burn_args,
            );

            match bad_debt_burn_result {
                Ok(Ok((_is_zero, total_scaled, _user_remaining))) => {
                    // Use the LAST burn's return value (supersedes first burn)
                    debt_token_scaled_total = Some(safe_i128_to_u128(env, total_scaled));
                }
                Ok(Err(_)) | Err(_) => {
                    return Err(KineticRouterError::InsufficientCollateral);
                }
            }

            // Track bad debt as deficit instead of socializing to depositors
            storage::add_reserve_deficit(env, &debt_asset, remaining_debt_u128);

            remaining_debt_balance = 0;

            // I-03: Structured deficit event with collateral context
            env.events().publish(
                (symbol_short!("deficit"), symbol_short!("bad_debt")),
                (user.clone(), collateral_asset.clone(), debt_asset.clone(), remaining_debt_u128, storage::get_reserve_deficit(env, &debt_asset)),
            );
        } else if min_remaining_whole > 0 {
            // Normal dust revert: match repay behavior (skip when min_remaining_whole == 0)
            let min_remaining_debt = (min_remaining_whole as u128)
                .checked_mul(debt_decimals_pow)
                .ok_or(KineticRouterError::MathOverflow)?;
            if remaining_debt_u128 < min_remaining_debt {
                panic_with_error!(env, LiquidationError::LeavesTooLittleDebt);
            }
        }
    }

    // WP-L7: Check min leftover value for both debt and collateral
    // When partial liquidation leaves tiny remaining positions, they become
    // uneconomical to liquidate further. Revert to force full liquidation.
    if remaining_debt_balance > 0 && remaining_collateral_balance > 0 {
        let remaining_debt_u128_l7 = safe_i128_to_u128(env, remaining_debt_balance);
        let remaining_debt_value = {
            let rd = U256::from_u128(&env, remaining_debt_u128_l7);
            let dp = U256::from_u128(&env, debt_price);
            let otw = U256::from_u128(&env, oracle_to_wad);
            let ddp = U256::from_u128(&env, debt_decimals_pow);
            rd.mul(&dp).mul(&otw).div(&ddp)
                .to_u128()
                .ok_or(KineticRouterError::MathOverflow)?
        };
        let remaining_collateral_value = {
            let rc = U256::from_u128(&env, remaining_collateral_balance);
            let cp = U256::from_u128(&env, collateral_price);
            let otw = U256::from_u128(&env, oracle_to_wad);
            let cdp = U256::from_u128(&env, collateral_decimals_pow);
            rc.mul(&cp).mul(&otw).div(&cdp)
                .to_u128()
                .ok_or(KineticRouterError::MathOverflow)?
        };
        if remaining_debt_value < MIN_LEFTOVER_BASE || remaining_collateral_value < MIN_LEFTOVER_BASE {
            panic_with_error!(env, LiquidationError::LeavesTooLittleDebt);
        }
    }

    if remaining_debt_balance == 0 {
        let mut user_config = storage::get_user_configuration(env, &user);
        user_config.set_borrowing(k2_shared::safe_reserve_id(env, updated_debt_reserve_data.id), false);
        storage::set_user_configuration(env, &user, &user_config);
    }

    let post_burn_debt_reserve = storage::get_reserve_data(env, &debt_asset)?;
    let post_burn_collateral_reserve = storage::get_reserve_data(env, &collateral_asset)?;
    if collateral_asset == debt_asset {
        // Same asset: both a-token and debt-token totals known
        calculation::update_interest_rates_and_store(
            env, &debt_asset, &post_burn_debt_reserve,
            a_token_scaled_total, debt_token_scaled_total,
        )?;
    } else {
        // Debt reserve: debt_token total known from burn, a_token unknown
        calculation::update_interest_rates_and_store(
            env, &debt_asset, &post_burn_debt_reserve,
            None, debt_token_scaled_total,
        )?;
        // Collateral reserve: a_token total known from burn, debt_token unknown
        calculation::update_interest_rates_and_store(
            env, &collateral_asset, &post_burn_collateral_reserve,
            a_token_scaled_total, None,
        )?;
    }

    // Emit liquidation event with fee information.
    // LOW-2: Use effective_collateral_removed to derive the actual fee transferred,
    // not the computed protocol_fee_collateral (which may not have been transferred
    // if no treasury is configured in the receive_a_token path).
    let actual_protocol_fee = effective_collateral_removed
        .checked_sub(liquidator_collateral)
        .unwrap_or(0);
    env.events().publish(
        (symbol_short!("liquidate"), EV_EVENT),
        LiquidationCallEvent {
            collateral_asset,
            debt_asset,
            user: user.clone(),
            debt_to_cover,
            liquidated_collateral_amount: collateral_amount_to_transfer,
            liquidator,
            receive_a_token: _receive_a_token,
            protocol_fee: actual_protocol_fee,
            liquidator_collateral,
        },
    );

    // WP-M2: Track liquidation amount to prevent bypass
    storage::add_user_liquidation_amount(env, &user, debt_to_cover_base);

    Ok(())
}

