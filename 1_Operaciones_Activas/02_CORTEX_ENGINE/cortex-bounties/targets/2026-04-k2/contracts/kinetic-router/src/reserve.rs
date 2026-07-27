use crate::storage;
use k2_shared::*;
use soroban_sdk::{symbol_short, panic_with_error, Address, BytesN, Env, IntoVal, Symbol};

pub fn init_reserve(
    env: Env,
    caller: Address,
    underlying_asset: Address,
    a_token_impl: Address,
    variable_debt_impl: Address,
    interest_rate_strategy: Address,
    _treasury: Address,
    params: InitReserveParams,
) -> Result<(), KineticRouterError> {
    storage::validate_pool_configurator(&env, &caller)?;
    caller.require_auth();

    if storage::get_reserve_data(&env, &underlying_asset).is_ok() {
        return Err(KineticRouterError::ReserveAlreadyInitialized);
    }

    // Enforce 64-reserve hard cap (UserConfiguration bitmap limit)
    let next_id = storage::get_next_reserve_id(&env);
    if next_id >= MAX_RESERVES {
        panic_with_error!(&env, ReserveManagementError::MaxReservesReached);
    }
    if params.ltv > BASIS_POINTS_MULTIPLIER as u32 {
        return Err(KineticRouterError::InvalidAmount);
    }
    if params.liquidation_threshold > BASIS_POINTS_MULTIPLIER as u32 {
        return Err(KineticRouterError::InvalidAmount);
    }
    // Require liquidation_threshold > ltv with minimum 50 bps buffer to prevent hair-trigger liquidations
    const MIN_LIQUIDATION_BUFFER_BPS: u32 = 50;
    if params.liquidation_threshold <= params.ltv {
        return Err(KineticRouterError::InvalidAmount);
    }
    if params.liquidation_threshold < params.ltv + MIN_LIQUIDATION_BUFFER_BPS {
        return Err(KineticRouterError::InvalidAmount);
    }
    if params.reserve_factor > BASIS_POINTS_MULTIPLIER as u32 {
        return Err(KineticRouterError::InvalidAmount);
    }
    // Validate liquidation_bonus is within basis points range (0-10,000)
    // This prevents silent truncation of values > 10,000 to 14-bit range
    if params.liquidation_bonus > BASIS_POINTS_MULTIPLIER as u32 {
        return Err(KineticRouterError::InvalidAmount);
    }
    // Validate decimals to prevent overflow in get_decimals_pow()
    // 10^38 fits in u128, but 10^39 would overflow
    const MAX_SAFE_DECIMALS: u32 = 38;
    if params.decimals > MAX_SAFE_DECIMALS {
        return Err(KineticRouterError::InvalidAmount);
    }
    // Validate that 10^decimals doesn't overflow (double-check)
    if 10_u128.checked_pow(params.decimals).is_none() {
        return Err(KineticRouterError::MathOverflow);
    }
    // Validate supply_cap and borrow_cap fit in 64 bits to prevent silent truncation
    const U64_MAX: u128 = u64::MAX as u128;
    if params.supply_cap > U64_MAX {
        return Err(KineticRouterError::InvalidAmount);
    }
    if params.borrow_cap > U64_MAX {
        return Err(KineticRouterError::InvalidAmount);
    }

    // Create reserve configuration bitmap (U256: data_low + data_high)
    let mut config_data_low = 0u128;
    config_data_low |= (params.ltv as u128) & 0x3FFF;
    config_data_low |= ((params.liquidation_threshold as u128) & 0x3FFF) << 14;
    config_data_low |= ((params.liquidation_bonus as u128) & 0x3FFF) << 28;
    config_data_low |= ((params.decimals as u128) & 0xFF) << 42;
    config_data_low |= 1u128 << 50; // active
    if params.borrowing_enabled {
        config_data_low |= 1u128 << 52;
    }
    if params.flashloan_enabled {
        config_data_low |= 1u128 << 56;
    }
    config_data_low |= ((params.reserve_factor as u128) & 0x3FFF) << 57;
    let mut config_data_high = 0u128;
    config_data_high |= params.borrow_cap & 0xFFFFFFFFFFFFFFFF;
    config_data_high |= (params.supply_cap & 0xFFFFFFFFFFFFFFFF) << 64;

    let configuration = ReserveConfiguration {
        data_low: config_data_low,
        data_high: config_data_high,
    };
    let reserve_id = storage::increment_and_get_reserve_id(&env);
    let reserve_data = ReserveData {
        liquidity_index: RAY,       // Start with 1.0
        variable_borrow_index: RAY, // Start with 1.0
        current_liquidity_rate: 0,
        current_variable_borrow_rate: 0,
        last_update_timestamp: env.ledger().timestamp(),
        a_token_address: a_token_impl.clone(),
        debt_token_address: variable_debt_impl.clone(), // Variable debt token
        interest_rate_strategy_address: interest_rate_strategy,
        id: reserve_id,
        configuration,
    };

    storage::set_reserve_data(&env, &underlying_asset, &reserve_data);
    storage::add_reserve_to_list(&env, &underlying_asset);
    // Store ID to address mapping for O(1) lookup optimization
    storage::set_reserve_address_by_id(&env, reserve_id, &underlying_asset);
    env.events().publish(
        (symbol_short!("init_res"), underlying_asset.clone()),
        (params.supply_cap, params.borrow_cap),
    );

    // Set incentives contract on tokens if configured
    if let Some(incentives) = storage::get_incentives_contract(&env) {
        propagate_incentives_to_tokens(&env, &a_token_impl, &variable_debt_impl, &incentives)?;
    }

    Ok(())
}

/// Propagate incentives contract to both a-token and debt-token.
/// Shared by: init_reserve, set_incentives_contract (params.rs).
pub(crate) fn propagate_incentives_to_tokens(
    env: &Env,
    a_token: &Address,
    debt_token: &Address,
    incentives: &Address,
) -> Result<(), KineticRouterError> {
    let pool_address = env.current_contract_address();
    let sym = Symbol::new(env, "set_incentives_contract");

    for token in [a_token, debt_token] {
        let mut args = soroban_sdk::Vec::new(env);
        args.push_back(IntoVal::into_val(&pool_address, env));
        args.push_back(IntoVal::into_val(incentives, env));
        let result = env.try_invoke_contract::<Result<(), TokenError>, KineticRouterError>(
            token, &sym, args,
        );
        match result {
            Ok(Ok(Ok(()))) => {}
            Ok(Ok(Err(_))) | Ok(Err(_)) | Err(_) => {
                return Err(KineticRouterError::TokenInitializationFailed);
            }
        }
    }
    Ok(())
}

pub fn set_reserve_supply_cap(
    env: Env,
    asset: Address,
    supply_cap: u128,
) -> Result<(), KineticRouterError> {
    let admin = storage::get_pool_admin(&env)?;
    admin.require_auth();

    // Validate supply_cap fits in 64 bits to prevent silent truncation
    // This ensures the stored value matches the input value
    const U64_MAX: u128 = u64::MAX as u128;
    if supply_cap > U64_MAX {
        return Err(KineticRouterError::InvalidAmount);
    }

    let mut reserve_data = storage::get_reserve_data(&env, &asset)?;
    reserve_data.configuration.set_supply_cap(supply_cap);
    storage::set_reserve_data(&env, &asset, &reserve_data);
    
    const EVENT_SET_CAP: Symbol = symbol_short!("set_cap");
    const EVENT_SUPPLY: Symbol = symbol_short!("supply");
    env.events()
        .publish((EVENT_SET_CAP, asset.clone()), (EVENT_SUPPLY, supply_cap));

    Ok(())
}

pub fn set_reserve_borrow_cap(
    env: Env,
    asset: Address,
    borrow_cap: u128,
) -> Result<(), KineticRouterError> {
    let admin = storage::get_pool_admin(&env)?;
    admin.require_auth();

    // Validate borrow_cap fits in 64 bits to prevent silent truncation
    // This ensures the stored value matches the input value
    const U64_MAX: u128 = u64::MAX as u128;
    if borrow_cap > U64_MAX {
        return Err(KineticRouterError::InvalidAmount);
    }

    let mut reserve_data = storage::get_reserve_data(&env, &asset)?;
    reserve_data.configuration.set_borrow_cap(borrow_cap);
    storage::set_reserve_data(&env, &asset, &reserve_data);
    
    const EVENT_SET_CAP: Symbol = symbol_short!("set_cap");
    const EVENT_BORROW: Symbol = symbol_short!("borrow");
    env.events()
        .publish((EVENT_SET_CAP, asset.clone()), (EVENT_BORROW, borrow_cap));

    Ok(())
}

pub fn set_reserve_debt_ceiling(
    env: Env,
    asset: Address,
    debt_ceiling: u128,
) -> Result<(), KineticRouterError> {
    let admin = storage::get_pool_admin(&env)?;
    admin.require_auth();

    // Verify reserve exists
    storage::get_reserve_data(&env, &asset)?;
    
    // Validate debt_ceiling fits in 64 bits to prevent silent truncation
    // Debt ceiling uses the same storage pattern as caps
    const U64_MAX: u128 = u64::MAX as u128;
    if debt_ceiling > U64_MAX {
        return Err(KineticRouterError::InvalidAmount);
    }
    
    storage::set_reserve_debt_ceiling(&env, &asset, debt_ceiling);
    
    const EVENT_SET_CAP: Symbol = symbol_short!("set_cap");
    const EVENT_DEBT_CEIL: Symbol = symbol_short!("debt_ceil");
    env.events()
        .publish((EVENT_SET_CAP, asset.clone()), (EVENT_DEBT_CEIL, debt_ceiling));

    Ok(())
}

pub fn get_reserve_debt_ceiling(
    env: Env,
    asset: Address,
) -> Result<u128, KineticRouterError> {
    // Verify reserve exists
    storage::get_reserve_data(&env, &asset)?;
    Ok(storage::get_reserve_debt_ceiling(&env, &asset))
}

/// H-02
/// Value is in whole tokens (same convention as borrow/supply caps).
pub fn set_reserve_min_remaining_debt(
    env: Env,
    asset: Address,
    min_remaining_debt: u32,
) -> Result<(), KineticRouterError> {
    let admin = storage::get_pool_admin(&env)?;
    admin.require_auth();

    let mut reserve_data = storage::get_reserve_data(&env, &asset)?;
    reserve_data.configuration.set_min_remaining_debt(min_remaining_debt);
    storage::set_reserve_data(&env, &asset, &reserve_data);

    env.events().publish(
        (symbol_short!("set_cfg"), asset.clone()),
        (symbol_short!("min_dbt"), min_remaining_debt),
    );

    Ok(())
}

/// H-03
/// Mirrors the same invariants enforced in `init_reserve` so that
/// `update_reserve_configuration` cannot bypass parameter constraints.
fn validate_reserve_configuration(
    config: &ReserveConfiguration,
) -> Result<(), KineticRouterError> {
    let ltv = config.get_ltv() as u32;
    let liquidation_threshold = config.get_liquidation_threshold() as u32;
    let liquidation_bonus = config.get_liquidation_bonus() as u32;
    let decimals = config.get_decimals() as u32;
    let reserve_factor = config.get_reserve_factor() as u32;
    let borrow_cap = config.get_borrow_cap();
    let supply_cap = config.get_supply_cap();

    // LTV must not exceed 100% (10 000 bps)
    if ltv > BASIS_POINTS_MULTIPLIER as u32 {
        return Err(KineticRouterError::InvalidAmount);
    }

    // Liquidation threshold must not exceed 100% (10 000 bps)
    if liquidation_threshold > BASIS_POINTS_MULTIPLIER as u32 {
        return Err(KineticRouterError::InvalidAmount);
    }

    // Liquidation threshold must strictly exceed LTV
    if liquidation_threshold <= ltv {
        return Err(KineticRouterError::InvalidAmount);
    }

    // Minimum 50 bps buffer between LTV and liquidation threshold
    const MIN_LIQUIDATION_BUFFER_BPS: u32 = 50;
    if liquidation_threshold < ltv + MIN_LIQUIDATION_BUFFER_BPS {
        return Err(KineticRouterError::InvalidAmount);
    }

    // Reserve factor must not exceed 100%
    if reserve_factor > BASIS_POINTS_MULTIPLIER as u32 {
        return Err(KineticRouterError::InvalidAmount);
    }

    // Liquidation bonus must not exceed 100%
    if liquidation_bonus > BASIS_POINTS_MULTIPLIER as u32 {
        return Err(KineticRouterError::InvalidAmount);
    }

    // Decimals must not exceed 38 (10^38 fits in u128, 10^39 overflows)
    const MAX_SAFE_DECIMALS: u32 = 38;
    if decimals > MAX_SAFE_DECIMALS {
        return Err(KineticRouterError::InvalidAmount);
    }

    // Double-check that 10^decimals does not overflow u128
    if 10_u128.checked_pow(decimals).is_none() {
        return Err(KineticRouterError::MathOverflow);
    }

    // Supply cap and borrow cap must fit in 64 bits (prevents silent truncation)
    const U64_MAX: u128 = u64::MAX as u128;
    if supply_cap > U64_MAX {
        return Err(KineticRouterError::InvalidAmount);
    }
    if borrow_cap > U64_MAX {
        return Err(KineticRouterError::InvalidAmount);
    }

    Ok(())
}

pub fn update_reserve_configuration(
    env: Env,
    caller: Address,
    asset: Address,
    configuration: ReserveConfiguration,
) -> Result<(), KineticRouterError> {
    storage::validate_pool_configurator(&env, &caller)?;
    caller.require_auth();

    // H-03
    validate_reserve_configuration(&configuration)?;

    let mut reserve_data = storage::get_reserve_data(&env, &asset)?;
    reserve_data.configuration = configuration;

    // Save the updated reserve data
    storage::set_reserve_data(&env, &asset, &reserve_data);

    // Emit event to enable off-chain monitoring of reserve configuration changes
    env.events().publish(
        (symbol_short!("config"), asset.clone()),
        (symbol_short!("updated"), true),
    );

    Ok(())
}

pub fn update_reserve_rate_strategy(
    env: Env,
    caller: Address,
    asset: Address,
    interest_rate_strategy: Address,
) -> Result<(), KineticRouterError> {
    storage::validate_pool_configurator(&env, &caller)?;
    caller.require_auth();

    let mut reserve_data = storage::get_reserve_data(&env, &asset)?;
    reserve_data.interest_rate_strategy_address = interest_rate_strategy.clone();

    // Save the updated reserve data
    storage::set_reserve_data(&env, &asset, &reserve_data);

    // Emit event
    env.events().publish(
        (symbol_short!("strategy"), asset.clone()),
        (symbol_short!("updated"), true),
    );

    Ok(())
}

fn update_token_implementation(
    env: &Env,
    caller: &Address,
    asset: &Address,
    new_wasm_hash: &BytesN<32>,
    token_address: &Address,
    event_topic: Symbol,
) -> Result<(), KineticRouterError> {
    storage::validate_pool_configurator(env, caller)?;
    caller.require_auth();

    let upgrade_result = env.try_invoke_contract::<(), KineticRouterError>(
        token_address,
        &Symbol::new(env, "upgrade"),
        soroban_sdk::vec![env, IntoVal::into_val(new_wasm_hash, env)],
    );

    match upgrade_result {
        Ok(Ok(())) => {}
        Ok(Err(_)) | Err(_) => {
            return Err(KineticRouterError::TokenDeploymentFailed);
        }
    }

    env.events()
        .publish((event_topic, asset.clone()), new_wasm_hash.clone());

    Ok(())
}

pub fn update_atoken_implementation(
    env: Env,
    caller: Address,
    asset: Address,
    a_token_impl: BytesN<32>,
) -> Result<(), KineticRouterError> {
    let reserve_data = storage::get_reserve_data(&env, &asset)?;
    update_token_implementation(
        &env, &caller, &asset, &a_token_impl,
        &reserve_data.a_token_address, symbol_short!("atoken"),
    )
}

pub fn update_debt_token_implementation(
    env: Env,
    caller: Address,
    asset: Address,
    debt_token_impl: BytesN<32>,
) -> Result<(), KineticRouterError> {
    let reserve_data = storage::get_reserve_data(&env, &asset)?;
    update_token_implementation(
        &env, &caller, &asset, &debt_token_impl,
        &reserve_data.debt_token_address, symbol_short!("debt"),
    )
}

pub fn drop_reserve(
    env: Env,
    caller: Address,
    asset: Address,
) -> Result<(), KineticRouterError> {
    storage::validate_pool_configurator(&env, &caller)?;
    caller.require_auth();

    let _reserve_data = storage::get_reserve_data(&env, &asset)?;
    let a_token_scaled_supply: i128 = match env.try_invoke_contract::<i128, KineticRouterError>(
        &_reserve_data.a_token_address,
        &Symbol::new(&env, "scaled_total_supply"),
        soroban_sdk::vec![&env],
    ) {
        Ok(Ok(supply)) => supply,
        Ok(Err(_)) | Err(_) => return Err(KineticRouterError::TokenCallFailed),
    };
    if a_token_scaled_supply != 0 {
        panic_with_error!(&env, ReserveManagementError::CannotDropActiveReserve);
    }

    // Check total debt - must be zero before dropping
    let debt_token_scaled_supply: i128 = match env.try_invoke_contract::<i128, KineticRouterError>(
        &_reserve_data.debt_token_address,
        &Symbol::new(&env, "scaled_total_supply"),
        soroban_sdk::vec![&env],
    ) {
        Ok(Ok(supply)) => supply,
        Ok(Err(_)) | Err(_) => return Err(KineticRouterError::TokenCallFailed),
    };
    if debt_token_scaled_supply != 0 {
        panic_with_error!(&env, ReserveManagementError::CannotDropActiveReserve);
    }

    // Reserve can be dropped but ID is permanently retired (never reused)
    let reserve_id = _reserve_data.id;
    storage::remove_reserve_data(&env, &asset);
    storage::remove_reserve_from_list(&env, &asset)?;
    storage::remove_reserve_address_by_id(&env, reserve_id);

    // AC-02
    let rwlf_key = (symbol_short!("RWLF"), asset.clone());
    let rblf_key = (symbol_short!("RBLF"), asset.clone());
    if env.storage().instance().has(&rwlf_key) {
        env.storage().instance().remove(&rwlf_key);
    }
    if env.storage().instance().has(&rblf_key) {
        env.storage().instance().remove(&rblf_key);
    }
    let wl_key = (symbol_short!("WLIST"), asset.clone());
    if env.storage().persistent().has(&wl_key) {
        env.storage().persistent().remove(&wl_key);
    }
    let bl_key = (symbol_short!("RBLACK"), asset.clone());
    if env.storage().persistent().has(&bl_key) {
        env.storage().persistent().remove(&bl_key);
    }

    // Clean up any tracked deficit for the dropped reserve
    let deficit_key = (symbol_short!("RDEFICIT"), asset.clone());
    if env.storage().persistent().has(&deficit_key) {
        env.storage().persistent().remove(&deficit_key);
    }

    env.events().publish(
        (symbol_short!("drop_res"), asset.clone()),
        (symbol_short!("removed"), true),
    );

    Ok(())
}

