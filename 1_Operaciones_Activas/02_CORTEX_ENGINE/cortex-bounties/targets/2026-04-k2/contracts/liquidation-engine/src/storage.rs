use soroban_sdk::{symbol_short, Address, Env, Symbol, Vec};

use crate::types::LiquidationCall;
use k2_shared::*;

// TTL constants: 1 year = 365 days * 17280 ledgers/day ≈ 6,307,200 ledgers
// Extend TTL when remaining time falls below 30 days
const TTL_THRESHOLD: u32 = 30 * 17280; // 30 days in ledgers
const TTL_EXTENSION: u32 = 365 * 17280; // 1 year in ledgers

const INITIALIZED: Symbol = symbol_short!("INIT");
const ADMIN: Symbol = symbol_short!("ADMIN");
const KINETIC_ROUTER: Symbol = symbol_short!("KROUTER");
const PRICE_ORACLE: Symbol = symbol_short!("ORACLE");
const CLOSE_FACTOR: Symbol = symbol_short!("CFACTOR");
const PAUSED: Symbol = symbol_short!("PAUSED");

const TOTAL_LIQUIDATIONS: Symbol = symbol_short!("TLIQUID");
const USER_LIQUIDATED_THIS_TX: Symbol = symbol_short!("ULIQTX");

pub fn is_initialized(env: &Env) -> bool {
    let result = env.storage().instance().has(&INITIALIZED);
    if result {
        env.storage().instance().extend_ttl(TTL_THRESHOLD, TTL_EXTENSION);
    }
    result
}

pub fn set_initialized(env: &Env) {
    env.storage().instance().set(&INITIALIZED, &true);
    env.storage().instance().extend_ttl(TTL_THRESHOLD, TTL_EXTENSION);
}

pub fn get_admin(env: &Env) -> Option<Address> {
    let result = env.storage().instance().get(&ADMIN);
    if result.is_some() {
        env.storage().instance().extend_ttl(TTL_THRESHOLD, TTL_EXTENSION);
    }
    result
}

pub fn set_admin(env: &Env, admin: &Address) {
    env.storage().instance().set(&ADMIN, admin);
    env.storage().instance().extend_ttl(TTL_THRESHOLD, TTL_EXTENSION);
}

pub fn get_kinetic_router(env: &Env) -> Result<Address, KineticRouterError> {
    let result = env.storage()
        .instance()
        .get(&KINETIC_ROUTER)
        .ok_or(KineticRouterError::NotInitialized)?;
    env.storage().instance().extend_ttl(TTL_THRESHOLD, TTL_EXTENSION);
    Ok(result)
}

pub fn set_kinetic_router(env: &Env, router: &Address) {
    env.storage().instance().set(&KINETIC_ROUTER, router);
    env.storage().instance().extend_ttl(TTL_THRESHOLD, TTL_EXTENSION);
}

pub fn get_price_oracle(env: &Env) -> Result<Address, KineticRouterError> {
    let result = env.storage()
        .instance()
        .get(&PRICE_ORACLE)
        .ok_or(KineticRouterError::NotInitialized)?;
    env.storage().instance().extend_ttl(TTL_THRESHOLD, TTL_EXTENSION);
    Ok(result)
}

pub fn set_price_oracle(env: &Env, oracle: &Address) {
    env.storage().instance().set(&PRICE_ORACLE, oracle);
    env.storage().instance().extend_ttl(TTL_THRESHOLD, TTL_EXTENSION);
}

pub fn get_close_factor(env: &Env) -> u128 {
    let result = env.storage()
        .instance()
        .get(&CLOSE_FACTOR)
        .unwrap_or(DEFAULT_LIQUIDATION_CLOSE_FACTOR);
    env.storage().instance().extend_ttl(TTL_THRESHOLD, TTL_EXTENSION);
    result
}

pub fn set_close_factor(env: &Env, close_factor: u128) {
    env.storage().instance().set(&CLOSE_FACTOR, &close_factor);
    env.storage().instance().extend_ttl(TTL_THRESHOLD, TTL_EXTENSION);
}

pub fn is_paused(env: &Env) -> bool {
    let result = env.storage().instance().get(&PAUSED).unwrap_or(false);
    env.storage().instance().extend_ttl(TTL_THRESHOLD, TTL_EXTENSION);
    result
}

pub fn set_paused(env: &Env, paused: bool) {
    env.storage().instance().set(&PAUSED, &paused);
    env.storage().instance().extend_ttl(TTL_THRESHOLD, TTL_EXTENSION);
}

pub fn add_liquidation_record(env: &Env, liquidation: &LiquidationCall) {
    let liquidation_id = get_total_liquidations_count(env);

    let _base_key = (symbol_short!("LRECORD"), liquidation_id);

    let liquidator_key = (symbol_short!("LIQUID"), liquidation_id);
    let user_key = (symbol_short!("USER"), liquidation_id);
    let collateral_key = (symbol_short!("COLLAT"), liquidation_id);
    let debt_key = (symbol_short!("DEBT"), liquidation_id);
    let amount_key = (symbol_short!("AMOUNT"), liquidation_id);
    let bonus_key = (symbol_short!("BONUS"), liquidation_id);
    let timestamp_key = (symbol_short!("TIME"), liquidation_id);

    env.storage()
        .persistent()
        .set(&liquidator_key, &liquidation.liquidator);
    env.storage()
        .persistent()
        .extend_ttl(&liquidator_key, TTL_THRESHOLD, TTL_EXTENSION);
    env.storage().persistent().set(&user_key, &liquidation.user);
    env.storage()
        .persistent()
        .extend_ttl(&user_key, TTL_THRESHOLD, TTL_EXTENSION);
    env.storage()
        .persistent()
        .set(&collateral_key, &liquidation.collateral_asset);
    env.storage()
        .persistent()
        .extend_ttl(&collateral_key, TTL_THRESHOLD, TTL_EXTENSION);
    env.storage()
        .persistent()
        .set(&debt_key, &liquidation.debt_asset);
    env.storage()
        .persistent()
        .extend_ttl(&debt_key, TTL_THRESHOLD, TTL_EXTENSION);
    env.storage()
        .persistent()
        .set(&amount_key, &liquidation.debt_to_cover);
    env.storage()
        .persistent()
        .extend_ttl(&amount_key, TTL_THRESHOLD, TTL_EXTENSION);
    env.storage()
        .persistent()
        .set(&bonus_key, &liquidation.liquidation_bonus);
    env.storage()
        .persistent()
        .extend_ttl(&bonus_key, TTL_THRESHOLD, TTL_EXTENSION);
    env.storage()
        .persistent()
        .set(&timestamp_key, &liquidation.timestamp);
    env.storage()
        .persistent()
        .extend_ttl(&timestamp_key, TTL_THRESHOLD, TTL_EXTENSION);

    // Add to user's liquidation list (store just the ID)
    let mut user_liquidations = get_user_liquidation_ids(env, &liquidation.user);
    user_liquidations.push_back(liquidation_id);
    let user_list_key = (symbol_short!("ULIQUID"), liquidation.user.clone());
    env.storage()
        .persistent()
        .set(&user_list_key, &user_liquidations);
    env.storage()
        .persistent()
        .extend_ttl(&user_list_key, TTL_THRESHOLD, TTL_EXTENSION);

    // Increment total count (unbounded counter, but only increments on liquidations)
    set_total_liquidations_count(env, liquidation_id.checked_add(1).expect("Liquidation ID overflow"));
}

pub fn get_user_liquidation_ids(env: &Env, user: &Address) -> Vec<u32> {
    let user_key = (symbol_short!("ULIQUID"), user.clone());
    if env.storage().persistent().has(&user_key) {
        env.storage()
            .persistent()
            .extend_ttl(&user_key, TTL_THRESHOLD, TTL_EXTENSION);
    }
    env.storage()
        .persistent()
        .get(&user_key)
        .unwrap_or(Vec::new(env))
}

pub fn get_liquidation_record(env: &Env, liquidation_id: u32) -> Option<LiquidationCall> {
    // Reconstruct LiquidationCall from individual fields
    let liquidator_key = (symbol_short!("LIQUID"), liquidation_id);
    let user_key = (symbol_short!("USER"), liquidation_id);
    let collateral_key = (symbol_short!("COLLAT"), liquidation_id);
    let debt_key = (symbol_short!("DEBT"), liquidation_id);
    let amount_key = (symbol_short!("AMOUNT"), liquidation_id);
    let bonus_key = (symbol_short!("BONUS"), liquidation_id);
    let timestamp_key = (symbol_short!("TIME"), liquidation_id);

    // Extend TTL on read
    if env.storage().persistent().has(&liquidator_key) {
        env.storage()
            .persistent()
            .extend_ttl(&liquidator_key, TTL_THRESHOLD, TTL_EXTENSION);
        env.storage()
            .persistent()
            .extend_ttl(&user_key, TTL_THRESHOLD, TTL_EXTENSION);
        env.storage()
            .persistent()
            .extend_ttl(&collateral_key, TTL_THRESHOLD, TTL_EXTENSION);
        env.storage()
            .persistent()
            .extend_ttl(&debt_key, TTL_THRESHOLD, TTL_EXTENSION);
        env.storage()
            .persistent()
            .extend_ttl(&amount_key, TTL_THRESHOLD, TTL_EXTENSION);
        env.storage()
            .persistent()
            .extend_ttl(&bonus_key, TTL_THRESHOLD, TTL_EXTENSION);
        env.storage()
            .persistent()
            .extend_ttl(&timestamp_key, TTL_THRESHOLD, TTL_EXTENSION);
    }

    let liquidator = env.storage().persistent().get(&liquidator_key)?;
    let user = env.storage().persistent().get(&user_key)?;
    let collateral_asset = env.storage().persistent().get(&collateral_key)?;
    let debt_asset = env.storage().persistent().get(&debt_key)?;
    let debt_to_cover = env.storage().persistent().get(&amount_key)?;
    let liquidation_bonus = env.storage().persistent().get(&bonus_key)?;
    let timestamp = env.storage().persistent().get(&timestamp_key)?;

    Some(LiquidationCall {
        liquidator,
        user,
        collateral_asset,
        debt_asset,
        debt_to_cover,
        collateral_to_liquidate: 0, // This field wasn't stored, set to 0
        liquidation_bonus,
        timestamp,
    })
}

pub fn get_total_liquidations_count(env: &Env) -> u32 {
    if env.storage().persistent().has(&TOTAL_LIQUIDATIONS) {
        env.storage()
            .persistent()
            .extend_ttl(&TOTAL_LIQUIDATIONS, TTL_THRESHOLD, TTL_EXTENSION);
    }
    env.storage()
        .persistent()
        .get(&TOTAL_LIQUIDATIONS)
        .unwrap_or(0)
}

pub fn set_total_liquidations_count(env: &Env, count: u32) {
    env.storage().persistent().set(&TOTAL_LIQUIDATIONS, &count);
    env.storage()
        .persistent()
        .extend_ttl(&TOTAL_LIQUIDATIONS, TTL_THRESHOLD, TTL_EXTENSION);
}

/// Get cumulative liquidation amount for a user in the current transaction
pub fn get_user_liquidated_this_tx(env: &Env, user: &Address) -> u128 {
    let key = (USER_LIQUIDATED_THIS_TX, user.clone());
    env.storage()
        .temporary()
        .get(&key)
        .unwrap_or(0)
}

/// Add to cumulative liquidation amount for a user in the current transaction
pub fn add_user_liquidated_this_tx(env: &Env, user: &Address, amount: u128) {
    let key = (USER_LIQUIDATED_THIS_TX, user.clone());
    let current = get_user_liquidated_this_tx(env, user);
    env.storage()
        .temporary()
        .set(&key, &(current + amount));
}
