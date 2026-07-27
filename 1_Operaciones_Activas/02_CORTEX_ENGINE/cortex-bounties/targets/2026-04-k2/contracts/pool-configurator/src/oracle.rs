use crate::storage;
use k2_shared::{Asset, KineticRouterError, OracleError};
use soroban_sdk::{symbol_short, Address, Env, IntoVal, Symbol};

pub fn add_oracle_asset(
    env: &Env,
    caller: &Address,
    asset: &Asset,
) -> Result<(), KineticRouterError> {
    storage::validate_admin(env, caller)?;
    caller.require_auth();

    let price_oracle_address = storage::get_price_oracle(env)?;
    let res: Result<(), OracleError> = env.invoke_contract(
        &price_oracle_address,
        &symbol_short!("add_asset"),
        soroban_sdk::vec![env, caller.into_val(env), asset.into_val(env)],
    );

    res.map_err(|_| KineticRouterError::PriceOracleNotFound)
}

pub fn remove_oracle_asset(
    env: &Env,
    caller: &Address,
    asset: &Asset,
) -> Result<(), KineticRouterError> {
    storage::validate_admin(env, caller)?;
    caller.require_auth();

    let price_oracle_address = storage::get_price_oracle(env)?;
    let res: Result<(), OracleError> = env.invoke_contract(
        &price_oracle_address,
        &Symbol::new(env, "remove_asset"),
        soroban_sdk::vec![env, asset.into_val(env)],
    );

    res.map_err(|_| KineticRouterError::PriceOracleNotFound)
}

pub fn set_oracle_asset_enabled(
    env: &Env,
    caller: &Address,
    asset: &Asset,
    enabled: bool,
) -> Result<(), KineticRouterError> {
    storage::validate_admin(env, caller)?;
    caller.require_auth();

    let price_oracle_address = storage::get_price_oracle(env)?;
    let res: Result<(), OracleError> = env.invoke_contract(
        &price_oracle_address,
        &Symbol::new(env, "set_asset_enabled"),
        soroban_sdk::vec![env, caller.into_val(env), asset.into_val(env), enabled.into_val(env)],
    );

    res.map_err(|_| KineticRouterError::PriceOracleNotFound)?;

    env.events().publish(
        (symbol_short!("oracle"), symbol_short!("asset"), symbol_short!("enabled")),
        (asset.clone(), enabled),
    );

    Ok(())
}

pub fn set_oracle_manual_override(
    env: &Env,
    caller: &Address,
    asset: &Asset,
    price: Option<i128>,
    expiry_timestamp: Option<u64>,
) -> Result<(), KineticRouterError> {
    storage::validate_admin(env, caller)?;
    caller.require_auth();

    // Convert Option<i128> to Option<u128> for oracle ABI
        // S-04
        let price_u128: Option<u128> = price.map(|p| k2_shared::safe_i128_to_u128(&env, p));

    let price_oracle_address = storage::get_price_oracle(env)?;
    let res: Result<(), OracleError> = env.invoke_contract(
        &price_oracle_address,
        &Symbol::new(env, "set_manual_override"),
        soroban_sdk::vec![env, caller.into_val(env), asset.into_val(env), price_u128.into_val(env), expiry_timestamp.into_val(env)],
    );

    res.map_err(|_| KineticRouterError::PriceOracleNotFound)
}
