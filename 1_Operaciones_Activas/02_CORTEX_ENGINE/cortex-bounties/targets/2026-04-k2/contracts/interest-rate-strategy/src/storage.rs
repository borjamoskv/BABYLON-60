use soroban_sdk::{contracttype, symbol_short, Address, Env, Symbol};
use k2_shared::KineticRouterError;

// TTL constants: 1 year = 365 days * 17280 ledgers/day ≈ 6,307,200 ledgers
// Extend TTL when remaining time falls below 30 days
const TTL_THRESHOLD: u32 = 30 * 17280; // 30 days in ledgers
const TTL_EXTENSION: u32 = 365 * 17280; // 1 year in ledgers

#[contracttype]
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct InterestRateParams {
    /// Base variable borrow rate (when utilization = 0)
    pub base_variable_borrow_rate: u128,
    /// Variable rate slope below optimal utilization
    pub variable_rate_slope1: u128,
    /// Variable rate slope above optimal utilization  
    pub variable_rate_slope2: u128,
    pub optimal_utilization_rate: u128,
}

const INITIALIZED: Symbol = symbol_short!("INIT");
const ADMIN: Symbol = symbol_short!("ADMIN");
const PENDING_ADMIN: Symbol = symbol_short!("PADMIN");

const BASE_VAR_RATE: Symbol = symbol_short!("BVR");
const VAR_SLOPE1: Symbol = symbol_short!("VS1");
const VAR_SLOPE2: Symbol = symbol_short!("VS2");
const OPT_UTIL: Symbol = symbol_short!("OU");

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

pub fn get_admin(env: &Env) -> Result<Address, KineticRouterError> {
    env.storage().instance().extend_ttl(TTL_THRESHOLD, TTL_EXTENSION);
    env.storage()
        .instance()
        .get(&ADMIN)
        .ok_or(KineticRouterError::NotInitialized)
}

pub fn set_admin(env: &Env, admin: &Address) {
    env.storage().instance().set(&ADMIN, admin);
    env.storage().instance().extend_ttl(TTL_THRESHOLD, TTL_EXTENSION);
}

pub fn get_pending_admin(env: &Env) -> Result<Address, KineticRouterError> {
    env.storage().instance().extend_ttl(TTL_THRESHOLD, TTL_EXTENSION);
    env.storage()
        .instance()
        .get(&PENDING_ADMIN)
        .ok_or(KineticRouterError::NoPendingAdmin)
}

pub fn set_pending_admin(env: &Env, pending_admin: &Address) {
    env.storage().instance().set(&PENDING_ADMIN, pending_admin);
    env.storage().instance().extend_ttl(TTL_THRESHOLD, TTL_EXTENSION);
}

pub fn clear_pending_admin(env: &Env) {
    if env.storage().instance().has(&PENDING_ADMIN) {
        env.storage().instance().remove(&PENDING_ADMIN);
    }
}

pub fn validate_admin(env: &Env, caller: &Address) -> Result<(), KineticRouterError> {
    let admin = get_admin(env)?;
    if caller != &admin {
        return Err(KineticRouterError::Unauthorized);
    }
    Ok(())
}

pub fn get_interest_rate_params(env: &Env) -> InterestRateParams {
    env.storage().instance().extend_ttl(TTL_THRESHOLD, TTL_EXTENSION);
    InterestRateParams {
        base_variable_borrow_rate: env.storage().instance().get(&BASE_VAR_RATE).unwrap_or(0),
        variable_rate_slope1: env.storage().instance().get(&VAR_SLOPE1).unwrap_or(0),
        variable_rate_slope2: env.storage().instance().get(&VAR_SLOPE2).unwrap_or(0),
        optimal_utilization_rate: env.storage().instance().get(&OPT_UTIL).unwrap_or(0),
    }
}

pub fn set_interest_rate_params(env: &Env, params: &InterestRateParams) {
    env.storage()
        .instance()
        .set(&BASE_VAR_RATE, &params.base_variable_borrow_rate);
    env.storage()
        .instance()
        .set(&VAR_SLOPE1, &params.variable_rate_slope1);
    env.storage()
        .instance()
        .set(&VAR_SLOPE2, &params.variable_rate_slope2);
    env.storage()
        .instance()
        .set(&OPT_UTIL, &params.optimal_utilization_rate);
    env.storage().instance().extend_ttl(TTL_THRESHOLD, TTL_EXTENSION);
}

pub fn set_asset_interest_rate_params(env: &Env, asset: &Address, params: &InterestRateParams) {
    let key = (symbol_short!("APARAMS"), asset.clone());
    env.storage().persistent().set(&key, params);
    env.storage()
        .persistent()
        .extend_ttl(&key, TTL_THRESHOLD, TTL_EXTENSION);
}

pub fn get_asset_interest_rate_params(
    env: &Env,
    asset: &Address,
) -> Option<InterestRateParams> {
    let key = (symbol_short!("APARAMS"), asset.clone());
    if env.storage().persistent().has(&key) {
        env.storage()
            .persistent()
            .extend_ttl(&key, TTL_THRESHOLD, TTL_EXTENSION);
    }
    env.storage().persistent().get(&key)
}
