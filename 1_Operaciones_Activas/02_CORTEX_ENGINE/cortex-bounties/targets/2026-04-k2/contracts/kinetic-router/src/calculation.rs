use crate::storage;
use k2_shared::{
    calculate_compound_interest, calculate_linear_interest, get_current_timestamp, ray_div,
    ray_mul, calculate_oracle_to_wad_factor, safe_i128_to_u128, CalculatedRates,
    KineticRouterError, ReserveData, UserAccountData, BASIS_POINTS_MULTIPLIER,
    WAD, MAX_RESERVES,
};
use soroban_sdk::{panic_with_error, Address, Env, IntoVal, Map, Symbol, Vec, U256};

/// Convert an amount to its base currency value using U256 math.
/// Shared helper for: close-factor validation, collateral/debt value views,
/// liquidation amount checks. Replaces ~8 inline U256 blocks.
pub(crate) fn value_in_base(
    env: &Env,
    amount: u128,
    price: u128,
    oracle_to_wad: u128,
    decimals_pow: u128,
) -> Result<u128, KineticRouterError> {
    let a = U256::from_u128(env, amount);
    let p = U256::from_u128(env, price);
    let otw = U256::from_u128(env, oracle_to_wad);
    let d = U256::from_u128(env, decimals_pow);
    a.mul(&p).mul(&otw).div(&d)
        .to_u128()
        .ok_or(KineticRouterError::MathOverflow)
}

/// F-05
/// Returns u128::MAX if debt is zero (infinitely healthy), otherwise computes:
pub(crate) fn calculate_health_factor_u256(
    env: &Env,
    total_collateral_base: u128,
    current_liquidation_threshold: u128,
    total_debt_base: u128,
) -> u128 {
    if total_debt_base == 0 {
        return u128::MAX; // No debt = infinitely healthy (correct)
    }
    let collateral = U256::from_u128(env, total_collateral_base);
    let threshold = U256::from_u128(env, current_liquidation_threshold);
    let wad = U256::from_u128(env, WAD);
    let bps = U256::from_u128(env, 10000u128);
    let debt = U256::from_u128(env, total_debt_base);

    // collateral * threshold * WAD / 10000 / debt
    // U256 division never overflows. If to_u128() fails (result > u128::MAX),
    // panic with error rather than silently returning u128::MAX sentinel.
    collateral.mul(&threshold).mul(&wad).div(&bps).div(&debt)
        .to_u128()
        .unwrap_or_else(|| panic_with_error!(env, KineticRouterError::MathOverflow))
}

/// Helper to fetch oracle config and return the oracle_to_wad factor
pub(crate) fn get_oracle_precision_factor(env: &Env) -> Result<u128, KineticRouterError> {
    let oracle_config = crate::price::get_oracle_config(env)?;
    Ok(calculate_oracle_to_wad_factor(oracle_config.price_precision))
}

/// Helper to reset liquidation tracker if the user is healthy
pub(crate) fn update_liquidation_tracker_if_healthy(
    env: &Env,
    user: &Address,
) -> Result<(), KineticRouterError> {
    if storage::get_user_liquidation_amount(env, user) > 0 {
        let user_config = storage::get_user_configuration(env, user);
        if user_config.has_any_borrowing() {
            let account_data = calculate_user_account_data_unified(env, user, AccountDataParams {
                known_prices: None,
                known_reserves: None,
                user_config: Some(&user_config),
                extra_assets: None,
                return_prices: false,
                known_balances: None,
            })?.account_data;
            
            if account_data.health_factor >= WAD {
                storage::clear_user_liquidation_amount(env, user);
            }
        } else {
            storage::clear_user_liquidation_amount(env, user);
        }
    }
    Ok(())
}

/// Parameters for unified account data calculation
pub(crate) struct AccountDataParams<'a> {
    /// Pre-fetched prices for specific assets (avoids re-fetching)
    pub known_prices: Option<&'a Map<Address, u128>>,
    /// Pre-read reserve data for specific assets (avoids re-reading)
    pub known_reserves: Option<&'a Map<Address, ReserveData>>,
    /// Pre-read user config (avoids storage read)
    pub user_config: Option<&'a k2_shared::UserConfiguration>,
    /// Extra assets to include in batch price fetch
    pub extra_assets: Option<&'a Vec<Address>>,
    /// Whether to return the price map
    pub return_prices: bool,
    /// Cached balances: asset -> (collateral_balance, debt_balance).
    /// Entries present here skip cross-contract calls entirely.
    /// First call seeds with known values; returned cache includes all queried balances.
    pub known_balances: Option<&'a Map<Address, (u128, u128)>>,
}

impl<'a> Default for AccountDataParams<'a> {
    fn default() -> Self {
        Self {
            known_prices: None,
            known_reserves: None,
            user_config: None,
            extra_assets: None,
            return_prices: false,
            known_balances: None,
        }
    }
}

/// Result from unified account data calculation, including optional caches for reuse
pub(crate) struct AccountDataResult {
    pub account_data: UserAccountData,
    pub prices: Option<Map<Address, u128>>,
    /// All balance lookups performed: asset -> (collateral_balance, debt_balance).
    /// Pass back as known_balances to skip cross-contract calls on subsequent calls.
    pub balance_cache: Map<Address, (u128, u128)>,
    /// Raw sum of (collateral_value_i * liquidation_threshold_i) across all positions.
    /// Used by validate_user_can_withdraw to correctly recompute the weighted-average
    /// threshold after removing one asset's contribution.
    pub weighted_threshold_sum: u128,
}

/// Unified user account data calculation with optional pre-cached inputs
pub(crate) fn calculate_user_account_data_unified(
    env: &Env,
    user: &Address,
    params: AccountDataParams,
) -> Result<AccountDataResult, KineticRouterError> {
    let oracle_to_wad = get_oracle_precision_factor(env)?;

    // Use provided user_config or read from storage
    let user_config = match params.user_config {
        Some(config) => config.clone(),
        None => storage::get_user_configuration(env, user),
    };

    // Collect assets and reserve data for active positions only
    let mut all_assets = Vec::new(env);
    let mut active_positions = Vec::new(env); // Store (asset, reserve_data) tuples
    
    // Add extra assets first if provided (e.g., borrow asset, swap assets)
    if let Some(extras) = params.extra_assets {
        for i in 0..extras.len() {
            if let Some(asset) = extras.get(i) {
                all_assets.push_back(asset);
            }
        }
    }
    
    // MED-04: Bound iteration to next_reserve_id (high-water mark) instead of MAX_RESERVES (64)
    // EFF-03: Must use next_reserve_id, NOT reserves_count, because reserve IDs are never
    // reused after drop_reserve. Using count would skip higher IDs when gaps exist.
    let next_reserve_id = storage::get_next_reserve_id(env);
    let iteration_bound = next_reserve_id.min(MAX_RESERVES as u32) as u8;
    for reserve_id in 0..iteration_bound {
        if user_config.is_using_as_collateral(reserve_id) || user_config.is_borrowing(reserve_id) {
            // Get asset address from reserve ID
            if let Some(asset) = storage::get_reserve_address_by_id(env, reserve_id as u32) {
                // Use known_reserves if available, fallback to storage for cache misses
                // (liquidation.rs passes partial maps — missing entries must not be skipped)
                let reserve_data = if let Some(known) = params.known_reserves {
                    match known.try_get(asset.clone()).ok().flatten() {
                        Some(data) => Some(data),
                        None => storage::get_reserve_data(env, &asset).ok(),
                    }
                } else {
                    storage::get_reserve_data(env, &asset).ok()
                };

                if let Some(reserve_data) = reserve_data {
                    // Avoid duplicates if asset is already in extra_assets
                    let mut is_duplicate = false;
                    if let Some(extras) = params.extra_assets {
                        for i in 0..extras.len() {
                            if let Some(extra) = extras.get(i) {
                                if asset == extra {
                                    is_duplicate = true;
                                    break;
                                }
                            }
                        }
                    }
                    if !is_duplicate {
                        all_assets.push_back(asset.clone());
                    }
                    active_positions.push_back((asset, reserve_data));
                }
            }
        }
    }

    // Fetch prices - use known_prices if available, otherwise batch fetch
    let price_map = if let Some(known) = params.known_prices {
        // If we have known prices, still need to fetch any missing ones
        let mut missing_assets = Vec::new(env);
        for i in 0..all_assets.len() {
            if let Some(asset) = all_assets.get(i) {
                if known.try_get(asset.clone()).ok().flatten().is_none() {
                    missing_assets.push_back(asset);
                }
            }
        }
        
        if missing_assets.is_empty() {
            known.clone()
        } else {
            // Fetch missing prices and merge with known
            let missing_prices = crate::price::get_prices_for_assets(env, &missing_assets)?;
            let mut merged = known.clone();
            for i in 0..missing_assets.len() {
                if let Some(asset) = missing_assets.get(i) {
                    if let Some(price) = missing_prices.try_get(asset.clone()).ok().flatten() {
                        merged.set(asset, price);
                    }
                }
            }
            merged
        }
    } else {
        crate::price::get_prices_for_assets(env, &all_assets)?
    };

    let sym_balance = Symbol::new(env, "balance_of_with_index");
    let mut total_collateral_base = 0u128;
    let mut total_debt_base = 0u128;
    let mut weighted_threshold_sum = 0u128;
    let mut weighted_ltv_sum = 0u128;

    // Balance cache: tracks all queried balances for reuse across HF calculations
    let mut balance_cache: Map<Address, (u128, u128)> = if let Some(known) = params.known_balances {
        known.clone()
    } else {
        Map::new(env)
    };

    // F-11
    let oracle_to_wad_u256 = U256::from_u128(env, oracle_to_wad);

    // Only iterate through active positions
    for i in 0..active_positions.len() {
        let (asset, reserve_data) = active_positions.get(i).ok_or(KineticRouterError::ReserveNotFound)?;

        // F-10
        let decimals_pow = reserve_data.configuration.get_decimals_pow()?;
        let decimals_pow_u256 = U256::from_u128(env, decimals_pow);

        let is_collateral = user_config.is_using_as_collateral(k2_shared::safe_reserve_id(env, reserve_data.id));
        let is_borrowing = user_config.is_borrowing(k2_shared::safe_reserve_id(env, reserve_data.id));

        // Look up cached balances for this asset (populated from prior HF call or caller-provided)
        let cached = balance_cache.try_get(asset.clone()).ok().flatten();

        // Query or reuse collateral balance
        let collateral_balance: u128 = if is_collateral {
            if let Some((coll_bal, _)) = cached {
                coll_bal
            } else {
                let args = soroban_sdk::vec![
                    env,
                    user.clone().into_val(env),
                    reserve_data.liquidity_index.into_val(env)
                ];
                match env.try_invoke_contract::<i128, KineticRouterError>(
                    &reserve_data.a_token_address,
                    &sym_balance,
                    args,
                ) {
                    Ok(Ok(bal)) => safe_i128_to_u128(env, bal),
                    Ok(Err(_)) | Err(_) => {
                        return Err(KineticRouterError::TokenCallFailed);
                    }
                }
            }
        } else {
            0
        };

        if is_collateral && collateral_balance > 0 {
            let asset_price = price_map
                .try_get(asset.clone())
                .ok()
                .flatten()
                .ok_or(KineticRouterError::PriceOracleNotFound)?;

            if asset_price == 0 {
                return Err(KineticRouterError::PriceOracleNotFound);
            }

            let liquidation_threshold =
                reserve_data.configuration.get_liquidation_threshold() as u128;
            let ltv = reserve_data.configuration.get_ltv() as u128;

            let balance_u256 = U256::from_u128(env, collateral_balance);
            let price_u256 = U256::from_u128(env, asset_price);

            let value_base = balance_u256
                .mul(&price_u256)
                .mul(&oracle_to_wad_u256)
                .div(&decimals_pow_u256)
                .to_u128()
                .ok_or(KineticRouterError::MathOverflow)?;

            total_collateral_base = total_collateral_base
                .checked_add(value_base)
                .ok_or(KineticRouterError::MathOverflow)?;

            let threshold_u256 = U256::from_u128(env, liquidation_threshold);
            let weighted_threshold_value = balance_u256
                .mul(&price_u256)
                .mul(&oracle_to_wad_u256)
                .mul(&threshold_u256)
                .div(&decimals_pow_u256)
                .to_u128()
                .ok_or(KineticRouterError::MathOverflow)?;

            weighted_threshold_sum = weighted_threshold_sum
                .checked_add(weighted_threshold_value)
                .ok_or(KineticRouterError::MathOverflow)?;

            let ltv_u256 = U256::from_u128(env, ltv);
            let weighted_ltv_value = balance_u256
                .mul(&price_u256)
                .mul(&oracle_to_wad_u256)
                .mul(&ltv_u256)
                .div(&decimals_pow_u256)
                .to_u128()
                .ok_or(KineticRouterError::MathOverflow)?;

            weighted_ltv_sum = weighted_ltv_sum
                .checked_add(weighted_ltv_value)
                .ok_or(KineticRouterError::MathOverflow)?;
        }

        // Query or reuse debt balance
        let debt_balance: u128 = if is_borrowing {
            if let Some((_, debt_bal)) = cached {
                debt_bal
            } else {
                let current_borrow_index =
                    get_current_variable_borrow_index_with_data(env, &reserve_data)?;
                let mut args = soroban_sdk::vec![env, user.clone().into_val(env)];
                args.push_back(current_borrow_index.into_val(env));
                match env.try_invoke_contract::<i128, KineticRouterError>(
                    &reserve_data.debt_token_address,
                    &sym_balance,
                    args,
                ) {
                    Ok(Ok(bal)) => safe_i128_to_u128(env, bal),
                    Ok(Err(_)) | Err(_) => {
                        return Err(KineticRouterError::TokenCallFailed);
                    }
                }
            }
        } else {
            0
        };

        // Populate balance cache for this asset (enables reuse by subsequent HF calls)
        if cached.is_none() && (is_collateral || is_borrowing) {
            balance_cache.set(asset.clone(), (collateral_balance, debt_balance));
        }

        if is_borrowing && debt_balance > 0 {
            let asset_price = price_map
                .try_get(asset)
                .ok()
                .flatten()
                .ok_or(KineticRouterError::PriceOracleNotFound)?;

            if asset_price == 0 {
                return Err(KineticRouterError::PriceOracleNotFound);
            }

            let balance_u256 = U256::from_u128(env, debt_balance);
            let price_u256 = U256::from_u128(env, asset_price);

            let value_base = balance_u256
                .mul(&price_u256)
                .mul(&oracle_to_wad_u256)
                .div(&decimals_pow_u256)
                .to_u128()
                .ok_or(KineticRouterError::MathOverflow)?;

            total_debt_base = total_debt_base
                .checked_add(value_base)
                .ok_or(KineticRouterError::MathOverflow)?;
        }
    }

    // M-09
    // Integer division truncates, reducing user borrowing power by ~1 bps per collateral asset.
    let current_liquidation_threshold = if total_collateral_base == 0 {
        0
    } else {
        // H-06: Ceiling division so threshold is never understated (favors borrower safety)
        let wts_u256 = U256::from_u128(env, weighted_threshold_sum);
        let tcb_u256 = U256::from_u128(env, total_collateral_base);
        let one = U256::from_u128(env, 1u128);
        wts_u256.add(&tcb_u256).sub(&one).div(&tcb_u256)
            .to_u128()
            .ok_or(KineticRouterError::MathOverflow)?
    };

    let ltv = if total_collateral_base == 0 {
        0
    } else {
        let wls_u256 = U256::from_u128(env, weighted_ltv_sum);
        let tcb_u256 = U256::from_u128(env, total_collateral_base);
        wls_u256.div(&tcb_u256)
            .to_u128()
            .ok_or(KineticRouterError::MathOverflow)?
    };

    // Use unified health factor calculation
    let health_factor = calculate_health_factor_u256(
        env,
        total_collateral_base,
        current_liquidation_threshold,
        total_debt_base,
    );

    let available_borrows_base = if total_debt_base == 0 {
        match total_collateral_base.checked_mul(ltv) {
            Some(val) => val.checked_div(10000).ok_or(KineticRouterError::MathOverflow)?,
            None => return Err(KineticRouterError::MathOverflow),
        }
    } else {
        match total_collateral_base.checked_mul(ltv) {
            Some(val) => {
                let max_borrow = val.checked_div(10000).ok_or(KineticRouterError::MathOverflow)?;
                // Clamp to 0: negative available borrows means undercollateralized
                if max_borrow >= total_debt_base {
                    max_borrow.checked_sub(total_debt_base).ok_or(KineticRouterError::MathOverflow)?
                } else {
                    0
                }
            },
            None => return Err(KineticRouterError::MathOverflow),
        }
    };

    let account_data = UserAccountData {
        total_collateral_base,
        total_debt_base,
        available_borrows_base,
        current_liquidation_threshold,
        ltv,
        health_factor,
    };
    
    // Return price map only if requested
    let prices = if params.return_prices {
        Some(price_map)
    } else {
        None
    };

    Ok(AccountDataResult {
        account_data,
        prices,
        balance_cache,
        weighted_threshold_sum,
    })
}

pub fn update_state(
    env: &Env,
    asset: &Address,
    reserve_data: &ReserveData,
) -> Result<ReserveData, KineticRouterError> {
    let current_timestamp = get_current_timestamp(env);

    // Reject backwards timestamps to prevent manipulation of interest calculations.
    // A future timestamp would cause underflow in time-delta calculations.
    if current_timestamp < reserve_data.last_update_timestamp {
        return Err(KineticRouterError::MathOverflow);
    }

    // L-02: Same-block re-entry — no interest has accrued, indices are already current.
    if current_timestamp == reserve_data.last_update_timestamp {
        return Ok(reserve_data.clone());
    }

    let mut updated_data = reserve_data.clone();

    let cumulated_liquidity_interest = calculate_linear_interest(
        reserve_data.current_liquidity_rate,
        reserve_data.last_update_timestamp,
        current_timestamp,
    )?;

    let cumulated_variable_borrow_interest = calculate_compound_interest(
        env,
        reserve_data.current_variable_borrow_rate,
        reserve_data.last_update_timestamp,
        current_timestamp,
    )?;

    updated_data.liquidity_index = ray_mul(
        env,
        reserve_data.liquidity_index,
        cumulated_liquidity_interest,
    )?;

    updated_data.variable_borrow_index = ray_mul(
        env,
        reserve_data.variable_borrow_index,
        cumulated_variable_borrow_interest,
    )?;

    updated_data.last_update_timestamp = current_timestamp;

    // Note: Interest rates are NOT updated here. They will be recalculated after user actions
    // (supply, withdraw, borrow, repay) based on the NEW utilization. This follows the
    // Aave/Compound pattern where rates are updated after the user action changes utilization.

    storage::set_reserve_data(env, asset, &updated_data);

    // Emit borrow index update event (moved from debt-token)
    env.events().publish(
        (soroban_sdk::symbol_short!("index_up"), asset.clone(), updated_data.variable_borrow_index),
        current_timestamp,
    );

    Ok(updated_data)
}

/// Update reserve state in memory without writing to storage
/// Use this to defer storage writes until end of transaction
pub fn update_state_without_store(
    env: &Env,
    reserve_data: &ReserveData,
) -> Result<ReserveData, KineticRouterError> {
    let current_timestamp = get_current_timestamp(env);

    if current_timestamp <= reserve_data.last_update_timestamp {
        return Ok(reserve_data.clone());
    }

    let mut updated_data = reserve_data.clone();

    let cumulated_liquidity_interest = calculate_linear_interest(
        reserve_data.current_liquidity_rate,
        reserve_data.last_update_timestamp,
        current_timestamp,
    )?;

    let cumulated_variable_borrow_interest = calculate_compound_interest(
        env,
        reserve_data.current_variable_borrow_rate,
        reserve_data.last_update_timestamp,
        current_timestamp,
    )?;

    updated_data.liquidity_index = ray_mul(
        env,
        reserve_data.liquidity_index,
        cumulated_liquidity_interest,
    )?;

    updated_data.variable_borrow_index = ray_mul(
        env,
        reserve_data.variable_borrow_index,
        cumulated_variable_borrow_interest,
    )?;

    updated_data.last_update_timestamp = current_timestamp;

    Ok(updated_data)
}

pub fn calculate_user_account_data(
    env: &Env,
    user: &Address,
) -> Result<UserAccountData, KineticRouterError> {
    let params = AccountDataParams::default();
    let result = calculate_user_account_data_unified(env, user, params)?;
    Ok(result.account_data)
}

pub fn calculate_user_account_data_with_prices(
    env: &Env,
    user: &Address,
    extra_asset: Option<&Address>,
) -> Result<(UserAccountData, Map<Address, u128>), KineticRouterError> {
    // Convert single extra_asset to Vec for compatibility
    let extra_assets = if let Some(asset) = extra_asset {
        let mut vec = Vec::new(env);
        vec.push_back(asset.clone());
        Some(vec)
    } else {
        None
    };
    
    let params = AccountDataParams {
        extra_assets: extra_assets.as_ref(),
        return_prices: true,
        ..Default::default()
    };

    let result = calculate_user_account_data_unified(env, user, params)?;
    Ok((result.account_data, result.prices.unwrap_or_else(|| Map::new(env))))
}


/// Phase 2 swap HF validation: single inline loop, O(1) extra memory regardless of reserve count.
/// Eliminates all intermediate Vec/Map allocations from the previous split fast-path/full-path design.
pub fn validate_swap_health_factor(
    env: &Env,
    caller: &Address,
    from_asset: &Address,
    to_asset: &Address,
    _from_amount: u128,
    _to_amount: u128,
    from_reserve: &ReserveData,
    to_reserve: &ReserveData,
    user_config: &k2_shared::UserConfiguration,
    from_known_balance: Option<u128>,
    to_known_balance: Option<u128>,
) -> Result<(), KineticRouterError> {
    if !user_config.has_any_borrowing() {
        // No debt → verify to_asset price exists (replaces removed verify_oracle_price call)
        let mut assets = Vec::new(env);
        assets.push_back(to_asset.clone());
        let price_map = crate::price::get_prices_for_assets(env, &assets)?;
        let to_price = price_map
            .try_get(to_asset.clone())
            .ok()
            .flatten()
            .ok_or(KineticRouterError::PriceOracleNotFound)?;
        if to_price == 0 {
            return Err(KineticRouterError::PriceOracleNotFound);
        }
        return Ok(());
    }

    let from_id = k2_shared::safe_reserve_id(env, from_reserve.id);
    let to_id = k2_shared::safe_reserve_id(env, to_reserve.id);

    // Build asset list for a SINGLE batch oracle call — includes swap assets + any other active positions
    let mut assets = Vec::new(env);
    assets.push_back(from_asset.clone());
    assets.push_back(to_asset.clone());

    let next_reserve_id = storage::get_next_reserve_id(env);
    let bound = next_reserve_id.min(MAX_RESERVES as u32) as u8;
    for rid in 0..bound {
        if user_config.is_using_as_collateral(rid) || user_config.is_borrowing(rid) {
            if rid != from_id && rid != to_id {
                if let Some(asset) = storage::get_reserve_address_by_id(env, rid as u32) {
                    assets.push_back(asset);
                }
            }
        }
    }

    let price_map = crate::price::get_prices_for_assets(env, &assets)?; // ONE oracle call

    let from_price = price_map
        .try_get(from_asset.clone())
        .ok()
        .flatten()
        .ok_or(KineticRouterError::PriceOracleNotFound)?;
    let to_price = price_map
        .try_get(to_asset.clone())
        .ok()
        .flatten()
        .ok_or(KineticRouterError::PriceOracleNotFound)?;

    // OPT-H2: Check both prices for zero to prevent HF manipulation
    if from_price == 0 || to_price == 0 {
        return Err(KineticRouterError::PriceOracleNotFound);
    }

    let from_threshold = from_reserve.configuration.get_liquidation_threshold() as u128;
    let to_threshold = to_reserve.configuration.get_liquidation_threshold() as u128;
    let from_decimals = from_reserve.configuration.get_decimals_pow()?;
    let to_decimals = to_reserve.configuration.get_decimals_pow()?;

    // Always perform full HF calculation when user has debt.
    // A fast-path that only checks delta (to_weighted >= from_weighted) is unsafe:
    // an underwater user could swap to a higher-LT asset and escape liquidation
    // without repaying debt, since the delta check proves HF improved but not HF >= 1.
    let oracle_to_wad = get_oracle_precision_factor(env)?;
    let oracle_to_wad_u256 = U256::from_u128(env, oracle_to_wad);

    let sym_balance = Symbol::new(env, "balance_of_with_index");
    let mut total_collateral_weighted = 0u128;
    let mut total_debt_base = 0u128;

    // Iterate all active reserves inline — use known swap reserves, query others
    for rid in 0..bound {
        let is_collateral = user_config.is_using_as_collateral(rid);
        let is_borrowing = user_config.is_borrowing(rid);
        if !is_collateral && !is_borrowing {
            continue;
        }

        // Resolve reserve data + price + decimals without cloning into collections
        let (reserve_ref_a_token, reserve_ref_debt_token, reserve_liq_index, reserve_var_borrow_rate,
             reserve_var_borrow_index, reserve_last_update, price, threshold, decimals_pow) =
            if rid == from_id {
                (
                    from_reserve.a_token_address.clone(),
                    from_reserve.debt_token_address.clone(),
                    from_reserve.liquidity_index,
                    from_reserve.current_variable_borrow_rate,
                    from_reserve.variable_borrow_index,
                    from_reserve.last_update_timestamp,
                    from_price,
                    from_threshold,
                    from_decimals,
                )
            } else if rid == to_id {
                (
                    to_reserve.a_token_address.clone(),
                    to_reserve.debt_token_address.clone(),
                    to_reserve.liquidity_index,
                    to_reserve.current_variable_borrow_rate,
                    to_reserve.variable_borrow_index,
                    to_reserve.last_update_timestamp,
                    to_price,
                    to_threshold,
                    to_decimals,
                )
            } else {
                // OPT-M6: Other reserve — a missing reserve for an active position
                // is critical state corruption; fail loudly rather than silently
                // skipping it (which would inflate the health factor).
                let asset_addr = match storage::get_reserve_address_by_id(env, rid as u32) {
                    Some(a) => a,
                    None => return Err(KineticRouterError::ReserveNotFound),
                };
                let rd = match storage::get_reserve_data(env, &asset_addr) {
                    Ok(d) => d,
                    Err(_) => return Err(KineticRouterError::ReserveNotFound),
                };
                let p = price_map
                    .try_get(asset_addr)
                    .ok()
                    .flatten()
                    .ok_or(KineticRouterError::PriceOracleNotFound)?;
                if p == 0 {
                    return Err(KineticRouterError::PriceOracleNotFound);
                }
                let t = rd.configuration.get_liquidation_threshold() as u128;
                let d = rd.configuration.get_decimals_pow()?;
                (
                    rd.a_token_address,
                    rd.debt_token_address,
                    rd.liquidity_index,
                    rd.current_variable_borrow_rate,
                    rd.variable_borrow_index,
                    rd.last_update_timestamp,
                    p,
                    t,
                    d,
                )
            };

        let price_u256 = U256::from_u128(env, price);
        let decimals_u256 = U256::from_u128(env, decimals_pow);

        // Accumulate collateral (weighted by liquidation threshold)
        if is_collateral {
            // Use known balances for from/to assets (saves 1-2 cross-contract calls)
            let balance = if rid == from_id && from_known_balance.is_some() {
                k2_shared::safe_u128_to_i128(env, from_known_balance.unwrap())
            } else if rid == to_id && to_known_balance.is_some() {
                k2_shared::safe_u128_to_i128(env, to_known_balance.unwrap())
            } else {
                let balance_result = env.try_invoke_contract::<i128, KineticRouterError>(
                    &reserve_ref_a_token,
                    &sym_balance,
                    soroban_sdk::vec![
                        env,
                        caller.clone().into_val(env),
                        reserve_liq_index.into_val(env)
                    ],
                );
                match balance_result {
                    Ok(Ok(v)) => v,
                    Ok(Err(_)) | Err(_) => return Err(KineticRouterError::TokenCallFailed),
                }
            };
            if balance > 0 {
                let bal_u256 = U256::from_u128(env, safe_i128_to_u128(env, balance));
                let threshold_u256 = U256::from_u128(env, threshold);
                let value = bal_u256
                    .mul(&price_u256)
                    .mul(&oracle_to_wad_u256)
                    .mul(&threshold_u256)
                    .div(&decimals_u256)
                    .to_u128()
                    .ok_or(KineticRouterError::MathOverflow)?;
                total_collateral_weighted = total_collateral_weighted
                    .checked_add(value)
                    .ok_or(KineticRouterError::MathOverflow)?;
            }
        }

        // Accumulate debt
        if is_borrowing {
            // Compute current borrow index inline (avoids reading ReserveData again)
            let current_borrow_index = {
                let current_ts = k2_shared::get_current_timestamp(env);
                if current_ts <= reserve_last_update {
                    reserve_var_borrow_index
                } else {
                    let compound = k2_shared::calculate_compound_interest(
                        env,
                        reserve_var_borrow_rate,
                        reserve_last_update,
                        current_ts,
                    )?;
                    k2_shared::ray_mul(env, reserve_var_borrow_index, compound)?
                }
            };

            let balance_result = env.try_invoke_contract::<i128, KineticRouterError>(
                &reserve_ref_debt_token,
                &sym_balance,
                soroban_sdk::vec![
                    env,
                    caller.clone().into_val(env),
                    current_borrow_index.into_val(env)
                ],
            );
            let balance = match balance_result {
                Ok(Ok(v)) => v,
                Ok(Err(_)) | Err(_) => return Err(KineticRouterError::TokenCallFailed),
            };
            if balance > 0 {
                let bal_u256 = U256::from_u128(env, safe_i128_to_u128(env, balance));
                let value = bal_u256
                    .mul(&price_u256)
                    .mul(&oracle_to_wad_u256)
                    .div(&decimals_u256)
                    .to_u128()
                    .ok_or(KineticRouterError::MathOverflow)?;
                total_debt_base = total_debt_base
                    .checked_add(value)
                    .ok_or(KineticRouterError::MathOverflow)?;
            }
        }
    }

    // H-01: Final HF check — collateral * WAD / (10000 * debt) >= WAD
    if total_debt_base > 0 {
        let collateral_u256 = U256::from_u128(env, total_collateral_weighted);
        let wad_u256 = U256::from_u128(env, WAD);
        let bps_u256 = U256::from_u128(env, 10000u128);
        let debt_u256 = U256::from_u128(env, total_debt_base);
        let hf = collateral_u256
            .mul(&wad_u256)
            .div(&bps_u256)
            .div(&debt_u256)
            .to_u128()
            .ok_or(KineticRouterError::MathOverflow)?;

        if hf < WAD {
            return Err(KineticRouterError::InvalidLiquidation);
        }
    }

    Ok(())
}

/// Calculate liquidation amounts and bonuses
/// This version accepts reserve data to avoid duplicate storage reads
pub fn calculate_liquidation_amounts_with_reserves(
    env: &Env,
    collateral_reserve: &ReserveData,
    debt_reserve: &ReserveData,
    debt_to_cover: u128,
    collateral_price: u128,
    debt_price: u128,
    oracle_to_wad: u128,
) -> Result<(u128, u128), KineticRouterError> {
    // Get decimals for proper price scaling
    let collateral_decimals = collateral_reserve.configuration.get_decimals() as u32;
    let debt_decimals = debt_reserve.configuration.get_decimals() as u32;

    // Step 1: Convert debt amount from asset units to base currency (WAD)
    // debt_to_cover is in asset units (e.g., 70 USDT = 70000000000 with 9 decimals)
    // debt_price is from oracle (precision determined by oracle config)
    // Calculate: (amount * price * oracle_to_wad) / 10^decimals = value in WAD (1e18)

    let debt_decimals_pow = 10_u128
        .checked_pow(debt_decimals)
        .ok_or(KineticRouterError::MathOverflow)?;
    
    // N-05
    let debt_to_cover_base = {
        let dtc = U256::from_u128(env, debt_to_cover);
        let dp = U256::from_u128(env, debt_price);
        let otw = U256::from_u128(env, oracle_to_wad);
        let ddp = U256::from_u128(env, debt_decimals_pow);
        dtc.mul(&dp).mul(&otw).div(&ddp)
            .to_u128()
            .ok_or(KineticRouterError::MathOverflow)?
    };

    // Step 2: Convert debt value to collateral units (without bonus)
    let decimals_pow = 10_u128
        .checked_pow(collateral_decimals)
        .ok_or(KineticRouterError::MathOverflow)?;

    // N-05
    let collateral_amount_without_bonus = {
        let dtcb = U256::from_u128(env, debt_to_cover_base);
        let dp = U256::from_u128(env, decimals_pow);
        let cp = U256::from_u128(env, collateral_price);
        let otw = U256::from_u128(env, oracle_to_wad);
        let denominator = cp.mul(&otw);
        dtcb.mul(&dp).div(&denominator)
            .to_u128()
            .ok_or(KineticRouterError::MathOverflow)?
    };

    // Step 3: Apply liquidation bonus
    // Formula: collateral_to_seize = debt_value * (1 + liquidation_bonus)
    // Example: debt = 10, bonus = 500 bps (5%) → collateral = 10 * 1.05 = 10.5
    let liquidation_bonus_bps = collateral_reserve.configuration.get_liquidation_bonus() as u128;

    // N-05
    let bonus_amount = {
        let dtcb = U256::from_u128(env, debt_to_cover_base);
        let lbb = U256::from_u128(env, liquidation_bonus_bps);
        let bpm = U256::from_u128(env, BASIS_POINTS_MULTIPLIER);
        dtcb.mul(&lbb).div(&bpm)
            .to_u128()
            .ok_or(KineticRouterError::MathOverflow)?
    };

    // Total collateral with bonus
    let collateral_amount_base_with_bonus = debt_to_cover_base
        .checked_add(bonus_amount)
        .ok_or(KineticRouterError::MathOverflow)?;

    // N-05
    let collateral_amount_to_seize = {
        let cabwb = U256::from_u128(env, collateral_amount_base_with_bonus);
        let dp = U256::from_u128(env, decimals_pow);
        let cp = U256::from_u128(env, collateral_price);
        let otw = U256::from_u128(env, oracle_to_wad);
        let denominator = cp.mul(&otw);
        cabwb.mul(&dp).div(&denominator)
            .to_u128()
            .ok_or(KineticRouterError::MathOverflow)?
    };

    // Return (collateral_without_bonus, collateral_with_bonus_to_seize)
    Ok((collateral_amount_without_bonus, collateral_amount_to_seize))
}

/// Calculate interest rates for a reserve based on current utilization
/// Uses scaled supplies with indices to avoid re-entry when called from within the router
/// Accepts optional pre-known scaled totals to skip cross-contract `scaled_total_supply()` calls.
pub fn calculate_interest_rates_for_reserve(
    env: &Env,
    asset: &Address,
    reserve_data: &ReserveData,
    known_a_scaled_total: Option<u128>,
    known_debt_scaled_total: Option<u128>,
) -> Result<(u128, u128), KineticRouterError> {
    let total_supply = match known_a_scaled_total {
        Some(scaled) => ray_mul(env, scaled, reserve_data.liquidity_index)?,
        None => get_total_supply_with_index(
            env,
            &reserve_data.a_token_address,
            reserve_data.liquidity_index,
        )?,
    };
    let total_debt = match known_debt_scaled_total {
        Some(scaled) => ray_mul(env, scaled, reserve_data.variable_borrow_index)?,
        None => get_total_debt_with_index(
            env,
            &reserve_data.debt_token_address,
            reserve_data.variable_borrow_index,
        )?,
    };

    // Calculate available liquidity
    let available_liquidity = if total_supply > total_debt {
        total_supply.checked_sub(total_debt).ok_or(KineticRouterError::MathOverflow)?
    } else {
        // F-24: Emit event for insolvency monitoring when debt >= supply
        env.events().publish(
            (soroban_sdk::symbol_short!("insolvent"), asset.clone()),
            (total_debt, total_supply),
        );
        0
    };

    // Get reserve factor from configuration
    let reserve_factor = reserve_data.configuration.get_reserve_factor() as u128;

    // Call interest rate strategy contract via cross-contract invocation
    let mut args = Vec::new(env);
    args.push_back(asset.clone().into_val(env));
    args.push_back(available_liquidity.into_val(env));
    args.push_back(total_debt.into_val(env));
    args.push_back(reserve_factor.into_val(env));

    let rates_result = env.try_invoke_contract::<CalculatedRates, KineticRouterError>(
        &reserve_data.interest_rate_strategy_address,
        &Symbol::new(env, "calculate_interest_rates"),
        args,
    );

    let rates = match rates_result {
        Ok(Ok(r)) => r,
        Ok(Err(_)) | Err(_) => return Err(KineticRouterError::InvalidAmount),
    };

    Ok((rates.liquidity_rate, rates.variable_borrow_rate))
}

/// Update interest rates based on current utilization and store state
/// This is called after user actions (borrow, repay, supply, withdraw) to reflect new utilization
pub fn update_interest_rates_and_store(
    env: &Env,
    asset: &Address,
    reserve_data: &ReserveData,
    known_a_scaled_total: Option<u128>,
    known_debt_scaled_total: Option<u128>,
) -> Result<(), KineticRouterError> {
    // Skip interest rate updates during flash loans to prevent manipulation
    if storage::is_flash_loan_active(env) {
        // During flash loans, just store the current state without updating rates
        storage::set_reserve_data(env, asset, reserve_data);
        return Ok(());
    }

    // Recalculate interest rates based on NEW utilization (after user action)
    let (new_liquidity_rate, new_variable_borrow_rate) =
        calculate_interest_rates_for_reserve(env, asset, reserve_data, known_a_scaled_total, known_debt_scaled_total)?;

    // Create updated reserve data with new rates
    let mut updated_data = reserve_data.clone();
    updated_data.current_liquidity_rate = new_liquidity_rate;
    updated_data.current_variable_borrow_rate = new_variable_borrow_rate;

    // Store the updated state with new rates
    storage::set_reserve_data(env, asset, &updated_data);

    Ok(())
}

/// Update a specific reserve's state (lazy computation)
/// This function is called only when needed, not every timestamp
pub fn update_reserve_state(env: &Env, asset: &Address) -> Result<ReserveData, KineticRouterError> {
    let reserve_data = storage::get_reserve_data(env, asset)?;
    update_state(env, asset, &reserve_data)
}

/// Get current reserve data with lazy computation
/// Only updates if the reserve hasn't been updated in the current timestamp
pub fn get_current_reserve_data(
    env: &Env,
    asset: &Address,
) -> Result<ReserveData, KineticRouterError> {
    let reserve_data = storage::get_reserve_data(env, asset)?;
    let current_timestamp = get_current_timestamp(env);

    // Reject backwards timestamps to prevent manipulation of interest calculations.
    // A future timestamp would cause underflow in time-delta calculations.
    if current_timestamp < reserve_data.last_update_timestamp {
        return Err(KineticRouterError::MathOverflow);
    }

    // If already updated in current timestamp, return as-is
    if current_timestamp == reserve_data.last_update_timestamp {
        return Ok(reserve_data);
    }

    // Otherwise, update the state
    update_state(env, asset, &reserve_data)
}

/// Get current liquidity index without forcing an update
/// This is useful for read-only operations
pub fn get_current_liquidity_index(env: &Env, asset: &Address) -> Result<u128, KineticRouterError> {
    let reserve_data = storage::get_reserve_data(env, asset)?;
    let current_timestamp = get_current_timestamp(env);

    // Reject backwards timestamps to prevent manipulation of interest calculations.
    // A future timestamp would cause underflow in time-delta calculations.
    if current_timestamp < reserve_data.last_update_timestamp {
        return Err(KineticRouterError::MathOverflow);
    }

    // If already updated in current timestamp, return current index
    if current_timestamp == reserve_data.last_update_timestamp {
        return Ok(reserve_data.liquidity_index);
    }

    // Calculate what the index would be without updating storage
    let cumulated_liquidity_interest = calculate_linear_interest(
        reserve_data.current_liquidity_rate,
        reserve_data.last_update_timestamp,
        current_timestamp,
    )?;

    let calculated_index = ray_mul(
        env,
        reserve_data.liquidity_index,
        cumulated_liquidity_interest,
    )?;

    Ok(calculated_index)
}

/// Get current variable borrow index using already-read reserve data
/// This avoids redundant storage reads when reserve_data is already available
pub fn get_current_variable_borrow_index_with_data(
    env: &Env,
    reserve_data: &ReserveData,
) -> Result<u128, KineticRouterError> {
    let current_timestamp = get_current_timestamp(env);

    // Reject backwards timestamps to prevent manipulation of interest calculations.
    // A future timestamp would cause underflow in time-delta calculations.
    if current_timestamp < reserve_data.last_update_timestamp {
        return Err(KineticRouterError::MathOverflow);
    }

    // If already updated in current timestamp, return current index
    if current_timestamp == reserve_data.last_update_timestamp {
        return Ok(reserve_data.variable_borrow_index);
    }

    // Calculate what the index would be without updating storage
    let cumulated_variable_borrow_interest = calculate_compound_interest(
        env,
        reserve_data.current_variable_borrow_rate,
        reserve_data.last_update_timestamp,
        current_timestamp,
    )?;

    ray_mul(
        env,
        reserve_data.variable_borrow_index,
        cumulated_variable_borrow_interest,
    )
}

/// Get current variable borrow index without forcing an update
/// This is useful for read-only operations
///
/// Note: If you already have `ReserveData`, use `get_current_variable_borrow_index_with_data`
/// to avoid redundant storage reads.
pub fn get_current_variable_borrow_index(
    env: &Env,
    asset: &Address,
) -> Result<u128, KineticRouterError> {
    let reserve_data = storage::get_reserve_data(env, asset)?;
    get_current_variable_borrow_index_with_data(env, &reserve_data)
}

/// Get total supply from a token contract via cross-contract invocation
/// Works for both aToken and debt token contracts
pub fn get_total_supply(env: &Env, token_address: &Address) -> Result<u128, KineticRouterError> {
    let sym_total_supply = Symbol::new(env, "total_supply");
    let supply_result = env.try_invoke_contract::<i128, KineticRouterError>(
        token_address,
        &sym_total_supply,
        Vec::new(env),
    );
    let total_supply = match supply_result {
        Ok(Ok(value)) => value,
        Ok(Err(_)) | Err(_) => return Err(KineticRouterError::TokenCallFailed),
    };
    if total_supply < 0 {
        return Err(KineticRouterError::MathOverflow);
    }
    // S-04
    Ok(safe_i128_to_u128(env, total_supply))
}

pub fn get_scaled_total_supply(
    env: &Env,
    token_address: &Address,
) -> Result<u128, KineticRouterError> {
    let sym_scaled_total_supply = Symbol::new(env, "scaled_total_supply");
    let supply_result = env.try_invoke_contract::<i128, KineticRouterError>(
        token_address,
        &sym_scaled_total_supply,
        Vec::new(env),
    );
    let scaled_total_supply = match supply_result {
        Ok(Ok(value)) => value,
        Ok(Err(_)) | Err(_) => return Err(KineticRouterError::TokenCallFailed),
    };
    if scaled_total_supply < 0 {
        return Err(KineticRouterError::MathOverflow);
    }
    // S-04
    Ok(safe_i128_to_u128(env, scaled_total_supply))
}

pub fn get_total_supply_with_index(
    env: &Env,
    token_address: &Address,
    index: u128,
) -> Result<u128, KineticRouterError> {
    let scaled = get_scaled_total_supply(env, token_address)?;
    ray_mul(env, scaled, index)
}

fn get_total_debt_with_index(
    env: &Env,
    debt_token_address: &Address,
    borrow_index: u128,
) -> Result<u128, KineticRouterError> {
    get_total_supply_with_index(env, debt_token_address, borrow_index)
}

/// Get underlying asset balance held by an aToken contract
/// This checks the actual underlying asset balance in the aToken contract
pub fn get_atoken_underlying_balance(
    env: &Env,
    underlying_asset: &Address,
    a_token_address: &Address,
) -> Result<u128, KineticRouterError> {
    // Get underlying asset balance from the aToken contract via cross-contract invocation
    let balance_args = soroban_sdk::vec![env, a_token_address.clone().into_val(env)];
    let sym_balance = Symbol::new(env, "balance");

    let balance_result = env.try_invoke_contract::<i128, KineticRouterError>(
        underlying_asset,
        &sym_balance,
        balance_args,
    );

    match balance_result {
        Ok(Ok(bal)) => Ok(safe_i128_to_u128(env, bal)),
        Ok(Err(_)) | Err(_) => Err(KineticRouterError::UnderlyingTransferFailed),
    }
}

/// Get available protocol reserves for an asset
///
/// Protocol reserves accumulate due to the reserve factor, which reduces supplier APY.
/// Reserves = underlying_balance_in_atoken - total_withdrawable_supply
pub fn get_protocol_reserves(env: &Env, asset: &Address) -> Result<u128, KineticRouterError> {
    let reserve_data = crate::storage::get_reserve_data(env, asset)?;

    // Update state first to ensure latest interest accrual
    let updated_reserve_data = update_state(env, asset, &reserve_data)?;

    // Get actual underlying balance in aToken contract
    let underlying_balance =
        get_atoken_underlying_balance(env, asset, &updated_reserve_data.a_token_address)?;

    // Use get_total_supply_with_index to avoid re-entry
    // We already have the liquidity_index from update_state, so no need to call back to router
    let total_supply = get_total_supply_with_index(
        env,
        &updated_reserve_data.a_token_address,
        updated_reserve_data.liquidity_index,
    )?;

    // Get total borrows to account for tokens that are borrowed out
    // When tokens are borrowed, they leave the contract, so we need to account for that
    let total_borrow = get_total_supply_with_index(
        env,
        &updated_reserve_data.debt_token_address,
        updated_reserve_data.variable_borrow_index,
    )?;

    // Available liquidity = what should be in the contract (total_supply - total_borrow)
    // This is the amount that suppliers can claim minus what borrowers owe
    // Reserves = actual balance - available liquidity
    
    if total_borrow > total_supply {
        return Err(KineticRouterError::InvalidAmount);
    }
    
    let available_liquidity = total_supply.checked_sub(total_borrow).ok_or(KineticRouterError::MathOverflow)?;
    let raw_reserves = if underlying_balance > available_liquidity {
        underlying_balance.checked_sub(available_liquidity).ok_or(KineticRouterError::MathOverflow)?
    } else {
        0
    };

    // Subtract deficit to show only truly collectible reserves
    let deficit = crate::storage::get_reserve_deficit(env, asset);
    Ok(raw_reserves.saturating_sub(deficit))
}
