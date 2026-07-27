use k2_shared::*;
use soroban_sdk::{panic_with_error, symbol_short, Address, BytesN, Env, IntoVal, String, Vec};

use crate::storage;

pub fn init_reserve(
    env: &Env,
    caller: &Address,
    underlying_asset: &Address,
    a_token_impl: &Address,
    variable_debt_impl: &Address,
    interest_rate_strategy: &Address,
    treasury: &Address,
    params: InitReserveParams,
) -> Result<(), KineticRouterError> {
    storage::validate_admin(env, caller)?;
    caller.require_auth();

    // Emergency pause mechanism: block new reserve deployments during incidents.
    // Allows emergency admin to halt protocol expansion without code changes.
    if storage::is_reserve_deployment_paused(env) {
        return Err(KineticRouterError::AssetPaused);
    }

    // Validate parameters before passing to router to prevent silent truncation
    // These validations match those in kinetic-router/src/reserve.rs::init_reserve
    if params.ltv > BASIS_POINTS_MULTIPLIER as u32 {
        return Err(KineticRouterError::InvalidAmount);
    }
    if params.liquidation_threshold > BASIS_POINTS_MULTIPLIER as u32 {
        return Err(KineticRouterError::InvalidAmount);
    }
    // Require liquidation_threshold > ltv with minimum 50 bps buffer to prevent hair-trigger liquidations
    const MIN_LIQUIDATION_BUFFER_BPS: u32 = 50;
    if params.liquidation_threshold <= params.ltv {
        env.events().publish(
            (
                symbol_short!("cfg"),
                symbol_short!("reject"),
                underlying_asset.clone(),
            ),
            (params.ltv, params.liquidation_threshold),
        );
        return Err(KineticRouterError::InvalidAmount);
    }
    if params.liquidation_threshold < params.ltv + MIN_LIQUIDATION_BUFFER_BPS {
        env.events().publish(
            (
                symbol_short!("cfg"),
                symbol_short!("reject"),
                underlying_asset.clone(),
            ),
            (params.ltv, params.liquidation_threshold),
        );
        return Err(KineticRouterError::InvalidAmount);
    }
    if params.reserve_factor > BASIS_POINTS_MULTIPLIER as u32 {
        return Err(KineticRouterError::InvalidAmount);
    }
    // Validate liquidation_bonus is within basis points range (0-10,000)
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
    if 10_u128.checked_pow(params.decimals as u32).is_none() {
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

    let kinetic_router_address = storage::get_kinetic_router(env)?;
    let _price_oracle_address = storage::get_price_oracle(env)?;

    let lending_pool_params = InitReserveParams {
        decimals: params.decimals,
        ltv: params.ltv,
        liquidation_threshold: params.liquidation_threshold,
        liquidation_bonus: params.liquidation_bonus,
        reserve_factor: params.reserve_factor,
        supply_cap: params.supply_cap,
        borrow_cap: params.borrow_cap,
        borrowing_enabled: params.borrowing_enabled,
        flashloan_enabled: params.flashloan_enabled,
    };

    env.events().publish(
        (symbol_short!("cfg_init"), underlying_asset),
        (
            a_token_impl.clone(),
            variable_debt_impl.clone(),
            interest_rate_strategy.clone(),
            treasury.clone(),
            lending_pool_params.clone(),
        ),
    );

    let configurator_address = env.current_contract_address();
    env.invoke_contract::<Result<(), KineticRouterError>>(
        &kinetic_router_address,
        &soroban_sdk::Symbol::new(env, "init_reserve"),
        soroban_sdk::vec![
            env,
            configurator_address.into_val(env),
            underlying_asset.into_val(env),
            a_token_impl.into_val(env),
            variable_debt_impl.into_val(env),
            interest_rate_strategy.into_val(env),
            treasury.into_val(env),
            lending_pool_params.into_val(env),
        ],
    )
    ?;

    Ok(())
}

pub fn configure_reserve_as_collateral(
    env: &Env,
    caller: &Address,
    asset: &Address,
    ltv: u32,
    liquidation_threshold: u32,
    liquidation_bonus: u32,
) -> Result<(), KineticRouterError> {
    storage::validate_admin(env, caller)?;
    caller.require_auth();

    if ltv > BASIS_POINTS_MULTIPLIER as u32 {
        return Err(KineticRouterError::InvalidAmount);
    }
    if liquidation_threshold > BASIS_POINTS_MULTIPLIER as u32 {
        return Err(KineticRouterError::InvalidAmount);
    }
    // Require liquidation_threshold > ltv with minimum 50 bps buffer to prevent hair-trigger liquidations
    const MIN_LIQUIDATION_BUFFER_BPS: u32 = 50;
    if liquidation_threshold <= ltv {
        env.events().publish(
            (
                symbol_short!("cfg"),
                symbol_short!("reject"),
                asset.clone(),
            ),
            (ltv, liquidation_threshold),
        );
        return Err(KineticRouterError::InvalidAmount);
    }
    if liquidation_threshold < ltv + MIN_LIQUIDATION_BUFFER_BPS {
        env.events().publish(
            (
                symbol_short!("cfg"),
                symbol_short!("reject"),
                asset.clone(),
            ),
            (ltv, liquidation_threshold),
        );
        return Err(KineticRouterError::InvalidAmount);
    }
    // Validate liquidation_bonus is within basis points range (0-10,000)
    // This prevents silent truncation of values > 10,000 to 14-bit range
    if liquidation_bonus > BASIS_POINTS_MULTIPLIER as u32 {
        return Err(KineticRouterError::InvalidAmount);
    }
    let reserve_data: ReserveData = env.invoke_contract(
        &storage::get_kinetic_router(env)?,
        &soroban_sdk::Symbol::new(env, "get_reserve_data"),
        soroban_sdk::vec![env, asset.into_val(env)],
    );

    let mut configuration = ReserveConfiguration {
        data_low: reserve_data.configuration.data_low,
        data_high: reserve_data.configuration.data_high,
    };

    configuration.set_ltv(ltv).map_err(|_| k2_shared::KineticRouterError::MathOverflow)?;
    configuration.set_liquidation_threshold(liquidation_threshold).map_err(|_| k2_shared::KineticRouterError::MathOverflow)?;
    configuration.set_liquidation_bonus(liquidation_bonus).map_err(|_| k2_shared::KineticRouterError::MathOverflow)?;

    env.invoke_contract::<Result<(), KineticRouterError>>(
        &storage::get_kinetic_router(env)?,
        &soroban_sdk::Symbol::new(env, "update_reserve_configuration"),
        soroban_sdk::vec![
            env,
            env.current_contract_address().into_val(env),
            asset.into_val(env),
            configuration.into_val(env),
        ],
    )
    ?;

    Ok(())
}

pub fn enable_borrowing_on_reserve(
    env: &Env,
    caller: &Address,
    asset: &Address,
    _stable_rate_enabled: bool,
) -> Result<(), KineticRouterError> {
    storage::validate_admin(env, caller)?;
    caller.require_auth();

    let reserve_data: ReserveData = env.invoke_contract(
        &storage::get_kinetic_router(env)?,
        &soroban_sdk::Symbol::new(env, "get_reserve_data"),
        soroban_sdk::vec![env, asset.into_val(env)],
    );

    let mut configuration = ReserveConfiguration {
        data_low: reserve_data.configuration.data_low,
        data_high: reserve_data.configuration.data_high,
    };

    configuration.set_borrowing_enabled(true);

    env.invoke_contract::<Result<(), KineticRouterError>>(
        &storage::get_kinetic_router(env)?,
        &soroban_sdk::Symbol::new(env, "update_reserve_configuration"),
        soroban_sdk::vec![
            env,
            env.current_contract_address().into_val(env),
            asset.into_val(env),
            configuration.into_val(env),
        ],
    )
    ?;

    Ok(())
}

pub fn set_reserve_active(
    env: &Env,
    caller: &Address,
    asset: &Address,
    active: bool,
) -> Result<(), KineticRouterError> {
    storage::validate_admin(env, caller)?;
    caller.require_auth();

    let reserve_data: ReserveData = env.invoke_contract(
        &storage::get_kinetic_router(env)?,
        &soroban_sdk::Symbol::new(env, "get_reserve_data"),
        soroban_sdk::vec![env, asset.into_val(env)],
    );

    let mut configuration = ReserveConfiguration {
        data_low: reserve_data.configuration.data_low,
        data_high: reserve_data.configuration.data_high,
    };

    configuration.set_active(active);

    env.invoke_contract::<Result<(), KineticRouterError>>(
        &storage::get_kinetic_router(env)?,
        &soroban_sdk::Symbol::new(env, "update_reserve_configuration"),
        soroban_sdk::vec![
            env,
            env.current_contract_address().into_val(env),
            asset.into_val(env),
            configuration.into_val(env),
        ],
    )
    ?;

    env.events().publish(
        (
            symbol_short!("reserve"),
            symbol_short!("active"),
            asset.clone(),
        ),
        active,
    );

    Ok(())
}

pub fn set_reserve_freeze(
    env: &Env,
    caller: &Address,
    asset: &Address,
    freeze: bool,
) -> Result<(), KineticRouterError> {
    storage::validate_admin(env, caller)?;
    caller.require_auth();

    let reserve_data: ReserveData = env.invoke_contract(
        &storage::get_kinetic_router(env)?,
        &soroban_sdk::Symbol::new(env, "get_reserve_data"),
        soroban_sdk::vec![env, asset.into_val(env)],
    );

    let mut configuration = ReserveConfiguration {
        data_low: reserve_data.configuration.data_low,
        data_high: reserve_data.configuration.data_high,
    };

    configuration.set_frozen(freeze);

    env.invoke_contract::<Result<(), KineticRouterError>>(
        &storage::get_kinetic_router(env)?,
        &soroban_sdk::Symbol::new(env, "update_reserve_configuration"),
        soroban_sdk::vec![
            env,
            env.current_contract_address().into_val(env),
            asset.into_val(env),
            configuration.into_val(env),
        ],
    )
    ?;

    env.events().publish(
        (
            symbol_short!("reserve"),
            symbol_short!("freeze"),
            asset.clone(),
        ),
        freeze,
    );

    Ok(())
}

pub fn set_reserve_pause(
    env: &Env,
    caller: &Address,
    asset: &Address,
    paused: bool,
) -> Result<(), KineticRouterError> {
    storage::validate_emergency_admin(env, caller)?;
    caller.require_auth();

    let reserve_data: ReserveData = env.invoke_contract(
        &storage::get_kinetic_router(env)?,
        &soroban_sdk::Symbol::new(env, "get_reserve_data"),
        soroban_sdk::vec![env, asset.into_val(env)],
    );

    let mut configuration = ReserveConfiguration {
        data_low: reserve_data.configuration.data_low,
        data_high: reserve_data.configuration.data_high,
    };

    configuration.set_paused(paused);

    let lending_pool_config = ReserveConfiguration {
        data_low: configuration.data_low,
        data_high: configuration.data_high,
    };

    env.invoke_contract::<Result<(), KineticRouterError>>(
        &storage::get_kinetic_router(env)?,
        &soroban_sdk::Symbol::new(env, "update_reserve_configuration"),
        soroban_sdk::vec![
            env,
            env.current_contract_address().into_val(env),
            asset.into_val(env),
            lending_pool_config.into_val(env),
        ],
    )
    ?;

    env.events().publish(
        (
            symbol_short!("reserve"),
            symbol_short!("pause"),
            asset.clone(),
        ),
        paused,
    );

    Ok(())
}

pub fn set_reserve_factor(
    env: &Env,
    caller: &Address,
    asset: &Address,
    reserve_factor: u32,
) -> Result<(), KineticRouterError> {
    storage::validate_admin(env, caller)?;
    caller.require_auth();

    if reserve_factor > BASIS_POINTS_MULTIPLIER as u32 {
        return Err(KineticRouterError::InvalidAmount);
    }

    let reserve_data: ReserveData = env.invoke_contract(
        &storage::get_kinetic_router(env)?,
        &soroban_sdk::Symbol::new(env, "get_reserve_data"),
        soroban_sdk::vec![env, asset.into_val(env)],
    );

    // Create a new configuration with updated values using shared types
    let mut configuration = ReserveConfiguration {
        data_low: reserve_data.configuration.data_low,
        data_high: reserve_data.configuration.data_high,
    };

    configuration.set_reserve_factor(reserve_factor);

    let lending_pool_config = ReserveConfiguration {
        data_low: configuration.data_low,
        data_high: configuration.data_high,
    };

    env.invoke_contract::<Result<(), KineticRouterError>>(
        &storage::get_kinetic_router(env)?,
        &soroban_sdk::Symbol::new(env, "update_reserve_configuration"),
        soroban_sdk::vec![
            env,
            env.current_contract_address().into_val(env),
            asset.into_val(env),
            lending_pool_config.into_val(env),
        ],
    )
    ?;

    env.events().publish(
        (
            symbol_short!("reserve"),
            symbol_short!("factor"),
            asset.clone(),
        ),
        reserve_factor,
    );

    Ok(())
}

pub fn set_reserve_interest_rate(
    env: &Env,
    caller: &Address,
    asset: &Address,
    rate_strategy: &Address,
) -> Result<(), KineticRouterError> {
    storage::validate_admin(env, caller)?;
    caller.require_auth();

    env.invoke_contract::<Result<(), KineticRouterError>>(
        &storage::get_kinetic_router(env)?,
        &soroban_sdk::Symbol::new(env, "update_reserve_rate_strategy"),
        soroban_sdk::vec![
            env,
            env.current_contract_address().into_val(env),
            asset.into_val(env),
            rate_strategy.into_val(env),
        ],
    )
    ?;

    env.events().publish(
        (
            symbol_short!("reserve"),
            symbol_short!("rate"),
            asset.clone(),
        ),
        rate_strategy.clone(),
    );

    Ok(())
}

pub fn set_supply_cap(
    env: &Env,
    caller: &Address,
    asset: &Address,
    supply_cap: u128,
) -> Result<(), KineticRouterError> {
    storage::validate_admin(env, caller)?;
    caller.require_auth();
    
    // Validate supply_cap fits in 64 bits to prevent silent truncation
    // This ensures the stored value matches the input value
    const U64_MAX: u128 = u64::MAX as u128;
    if supply_cap > U64_MAX {
        return Err(KineticRouterError::InvalidAmount);
    }
    
    env.invoke_contract::<Result<(), KineticRouterError>>(
        &storage::get_kinetic_router(env)?,
        &soroban_sdk::Symbol::new(env, "set_reserve_supply_cap"),
        soroban_sdk::vec![
            env,
            caller.into_val(env),
            asset.into_val(env),
            supply_cap.into_val(env),
        ],
    )
    ?;

    env.events().publish(
        (symbol_short!("supply"), symbol_short!("cap"), asset.clone()),
        supply_cap,
    );

    Ok(())
}

pub fn set_borrow_cap(
    env: &Env,
    caller: &Address,
    asset: &Address,
    borrow_cap: u128,
) -> Result<(), KineticRouterError> {
    storage::validate_admin(env, caller)?;
    caller.require_auth();
    
    // Validate borrow_cap fits in 64 bits to prevent silent truncation
    // This ensures the stored value matches the input value
    const U64_MAX: u128 = u64::MAX as u128;
    if borrow_cap > U64_MAX {
        return Err(KineticRouterError::InvalidAmount);
    }
    
    env.invoke_contract::<Result<(), KineticRouterError>>(
        &storage::get_kinetic_router(env)?,
        &soroban_sdk::Symbol::new(env, "set_reserve_borrow_cap"),
        soroban_sdk::vec![
            env,
            caller.into_val(env),
            asset.into_val(env),
            borrow_cap.into_val(env),
        ],
    )
    ?;

    env.events().publish(
        (symbol_short!("borrow"), symbol_short!("cap"), asset.clone()),
        borrow_cap,
    );

    Ok(())
}

pub fn set_debt_ceiling(
    env: &Env,
    caller: &Address,
    asset: &Address,
    debt_ceiling: u128,
) -> Result<(), KineticRouterError> {
    storage::validate_admin(env, caller)?;
    caller.require_auth();
    
    // Validate debt_ceiling fits in 64 bits to prevent silent truncation
    // Debt ceiling uses the same storage pattern as caps
    const U64_MAX: u128 = u64::MAX as u128;
    if debt_ceiling > U64_MAX {
        return Err(KineticRouterError::InvalidAmount);
    }
    
    env.invoke_contract::<Result<(), KineticRouterError>>(
        &storage::get_kinetic_router(env)?,
        &soroban_sdk::Symbol::new(env, "set_reserve_debt_ceiling"),
        soroban_sdk::vec![
            env,
            caller.into_val(env),
            asset.into_val(env),
            debt_ceiling.into_val(env),
        ],
    )
    ?;

    env.events()
        .publish((symbol_short!("debt_ceil"), asset.clone()), debt_ceiling);

    Ok(())
}

pub fn set_reserve_flashloaning(
    env: &Env,
    caller: &Address,
    asset: &Address,
    enabled: bool,
) -> Result<(), KineticRouterError> {
    storage::validate_admin(env, caller)?;
    caller.require_auth();

    let reserve_data: ReserveData = env.invoke_contract(
        &storage::get_kinetic_router(env)?,
        &soroban_sdk::Symbol::new(env, "get_reserve_data"),
        soroban_sdk::vec![env, asset.into_val(env)],
    );

    let mut configuration = ReserveConfiguration {
        data_low: reserve_data.configuration.data_low,
        data_high: reserve_data.configuration.data_high,
    };

    configuration.set_flashloan_enabled(enabled);

    let lending_pool_config = ReserveConfiguration {
        data_low: configuration.data_low,
        data_high: configuration.data_high,
    };

    env.invoke_contract::<Result<(), KineticRouterError>>(
        &storage::get_kinetic_router(env)?,
        &soroban_sdk::Symbol::new(env, "update_reserve_configuration"),
        soroban_sdk::vec![
            env,
            env.current_contract_address().into_val(env),
            asset.into_val(env),
            lending_pool_config.into_val(env),
        ],
    )
    ?;

    env.events().publish(
        (
            symbol_short!("flashloan"),
            symbol_short!("enabled"),
            asset.clone(),
        ),
        enabled,
    );

    Ok(())
}

pub fn update_atoken(
    env: &Env,
    caller: &Address,
    asset: &Address,
    implementation: &soroban_sdk::BytesN<32>,
) -> Result<(), KineticRouterError> {
    storage::validate_admin(env, caller)?;
    caller.require_auth();
    env.invoke_contract::<Result<(), KineticRouterError>>(
        &storage::get_kinetic_router(env)?,
        &soroban_sdk::Symbol::new(env, "update_atoken_implementation"),
        soroban_sdk::vec![
            env,
            caller.into_val(env),
            asset.into_val(env),
            implementation.into_val(env),
        ],
    )
    ?;

    env.events().publish(
        (
            symbol_short!("atoken"),
            symbol_short!("update"),
            asset.clone(),
        ),
        implementation.clone(),
    );

    Ok(())
}

pub fn update_variable_debt_token(
    env: &Env,
    caller: &Address,
    asset: &Address,
    implementation: &soroban_sdk::BytesN<32>,
) -> Result<(), KineticRouterError> {
    storage::validate_admin(env, caller)?;
    caller.require_auth();
    env.invoke_contract::<Result<(), KineticRouterError>>(
        &storage::get_kinetic_router(env)?,
        &soroban_sdk::Symbol::new(env, "update_debt_token_implementation"),
        soroban_sdk::vec![
            env,
            caller.into_val(env),
            asset.into_val(env),
            implementation.into_val(env),
        ],
    )
    ?;

    env.events().publish(
        (
            symbol_short!("debt"),
            symbol_short!("var"),
            symbol_short!("upd"),
            asset.clone(),
        ),
        implementation.clone(),
    );

    Ok(())
}

pub fn drop_reserve(
    env: &Env,
    caller: &Address,
    asset: &Address,
) -> Result<(), KineticRouterError> {
    storage::validate_admin(env, caller)?;
    caller.require_auth();
    env.invoke_contract::<Result<(), KineticRouterError>>(
        &storage::get_kinetic_router(env)?,
        &soroban_sdk::Symbol::new(env, "drop_reserve"),
        soroban_sdk::vec![
            env,
            env.current_contract_address().into_val(env),
            asset.into_val(env)
        ],
    )
    ?;

    Ok(())
}

/// Deploy aToken and debt token, initialize them, and register the reserve atomically.
/// Salts are generated using a counter with type markers ('A' for aToken, 'D' for debtToken).
/// Returns (aToken_address, debt_token_address).
pub fn deploy_and_init_reserve(
    env: &Env,
    caller: &Address,
    underlying_asset: &Address,
    interest_rate_strategy: &Address,
    treasury: &Address,
    a_token_name: String,
    a_token_symbol: String,
    debt_token_name: String,
    debt_token_symbol: String,
    params: InitReserveParams,
) -> Result<(Address, Address), KineticRouterError> {
    storage::validate_admin(env, caller)?;
    caller.require_auth();

    // Emergency pause mechanism: allows administrators to halt new reserve deployments
    // during incidents without affecting existing reserves or user operations.
    if storage::is_reserve_deployment_paused(env) {
        return Err(KineticRouterError::AssetPaused);
    }

    let a_token_wasm_hash =
        storage::get_a_token_wasm_hash(env).ok_or(KineticRouterError::WASMHashNotSet)?;
    let debt_token_wasm_hash =
        storage::get_debt_token_wasm_hash(env).ok_or(KineticRouterError::WASMHashNotSet)?;
    let kinetic_router_address = storage::get_kinetic_router(env)?;
    let deploy_id = storage::get_next_deploy_id(env);

    let mut salt_a_bytes = [0u8; 32];
    let mut salt_d_bytes = [0u8; 32];
    let counter_bytes = deploy_id.to_be_bytes();
    salt_a_bytes[0..4].copy_from_slice(&counter_bytes);
    salt_d_bytes[0..4].copy_from_slice(&counter_bytes);
    salt_a_bytes[4] = b'A';
    salt_d_bytes[4] = b'D';

    let salt_a = BytesN::from_array(env, &salt_a_bytes);
    let salt_d = BytesN::from_array(env, &salt_d_bytes);

    let constructor_args: Vec<soroban_sdk::Val> = Vec::new(env);
    let a_token_address = env
        .deployer()
        .with_current_contract(salt_a)
        .deploy_v2(a_token_wasm_hash, constructor_args.clone());

    let debt_token_address = env
        .deployer()
        .with_current_contract(salt_d)
        .deploy_v2(debt_token_wasm_hash, constructor_args);

    let configurator_address = env.current_contract_address();
    env.invoke_contract::<Result<(), TokenError>>(
        &a_token_address,
        &soroban_sdk::Symbol::new(env, "initialize"),
        soroban_sdk::vec![
            env,
            configurator_address.into_val(env),
            underlying_asset.into_val(env),
            kinetic_router_address.into_val(env),
            a_token_name.into_val(env),
            a_token_symbol.into_val(env),
            params.decimals.into_val(env),
        ],
    )
    .unwrap_or_else(|e| panic_with_error!(env, e));

    env.invoke_contract::<Result<(), TokenError>>(
        &debt_token_address,
        &soroban_sdk::Symbol::new(env, "initialize"),
        soroban_sdk::vec![
            env,
            configurator_address.into_val(env),
            underlying_asset.into_val(env),
            kinetic_router_address.into_val(env),
            debt_token_name.into_val(env),
            debt_token_symbol.into_val(env),
            params.decimals.into_val(env),
        ],
    )
    .unwrap_or_else(|e| panic_with_error!(env, e));

    let lending_pool_params = InitReserveParams {
        decimals: params.decimals,
        ltv: params.ltv,
        liquidation_threshold: params.liquidation_threshold,
        liquidation_bonus: params.liquidation_bonus,
        reserve_factor: params.reserve_factor,
        supply_cap: params.supply_cap,
        borrow_cap: params.borrow_cap,
        borrowing_enabled: params.borrowing_enabled,
        flashloan_enabled: params.flashloan_enabled,
    };

    env.events().publish(
        (symbol_short!("cfg_fact"), underlying_asset),
        (
            deploy_id,
            a_token_address.clone(),
            debt_token_address.clone(),
            interest_rate_strategy.clone(),
            treasury.clone(),
            lending_pool_params.clone(),
        ),
    );

    let configurator_address = env.current_contract_address();
    env.invoke_contract::<Result<(), KineticRouterError>>(
        &kinetic_router_address,
        &soroban_sdk::Symbol::new(env, "init_reserve"),
        soroban_sdk::vec![
            env,
            configurator_address.into_val(env),
            underlying_asset.into_val(env),
            a_token_address.into_val(env),
            debt_token_address.into_val(env),
            interest_rate_strategy.into_val(env),
            treasury.into_val(env),
            lending_pool_params.into_val(env),
        ],
    )
    ?;

    let incentives_contract: Option<Address> = env.invoke_contract(
        &kinetic_router_address,
        &soroban_sdk::Symbol::new(env, "get_incentives_contract"),
        soroban_sdk::Vec::new(env),
    );
    if let Some(incentives) = incentives_contract {
        // Update aToken incentives contract
        let a_token_result = env.try_invoke_contract::<Result<(), TokenError>, KineticRouterError>(
            &a_token_address,
            &soroban_sdk::Symbol::new(env, "set_incentives_contract"),
            soroban_sdk::vec![env, kinetic_router_address.clone().into_val(env), incentives.clone().into_val(env)],
        );
        
        match a_token_result {
            Ok(Ok(Ok(()))) => {}
            Ok(Ok(Err(_))) | Ok(Err(_)) | Err(_) => {
                return Err(KineticRouterError::TokenInitializationFailed);
            }
        }
        
        // Update debt token incentives contract
        let debt_token_result = env.try_invoke_contract::<Result<(), TokenError>, KineticRouterError>(
            &debt_token_address,
            &soroban_sdk::Symbol::new(env, "set_incentives_contract"),
            soroban_sdk::vec![env, kinetic_router_address.clone().into_val(env), incentives.into_val(env)],
        );
        
        match debt_token_result {
            Ok(Ok(Ok(()))) => {}
            Ok(Ok(Err(_))) | Ok(Err(_)) | Err(_) => {
                return Err(KineticRouterError::TokenInitializationFailed);
            }
        }
    }

    Ok((a_token_address, debt_token_address))
}
