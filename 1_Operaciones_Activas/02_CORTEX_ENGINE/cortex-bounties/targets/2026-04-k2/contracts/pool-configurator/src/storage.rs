use k2_shared::KineticRouterError;
use soroban_sdk::{symbol_short, Address, BytesN, Env, Symbol};

// TTL constants: 1 year = 365 days * 17280 ledgers/day ≈ 6,307,200 ledgers
// Threshold: extend TTL only when remaining lifetime falls below 4 weeks
// This prevents unnecessary fee overhead from bumping TTL on every read
const TTL_THRESHOLD: u32 = 28 * 17280; // 4 weeks in ledgers (483,840)
const TTL_EXTENSION: u32 = 365 * 17280; // 1 year in ledgers

/// Extend instance TTL only if remaining lifetime is below threshold.
/// This reduces fee overhead by avoiding unnecessary TTL bumps.
fn extend_instance_ttl_if_needed(env: &Env) {
    env.storage().instance().extend_ttl(TTL_THRESHOLD, TTL_EXTENSION);
}

const INITIALIZED: Symbol = symbol_short!("INIT");
const POOL_ADMIN: Symbol = symbol_short!("PADMIN");
const PENDING_POOL_ADMIN: Symbol = symbol_short!("PPADMIN");
const EMERGENCY_ADMIN: Symbol = symbol_short!("EADMIN");
const KINETIC_ROUTER: Symbol = symbol_short!("KROUTER");
const PRICE_ORACLE: Symbol = symbol_short!("ORACLE");
const DEPLOY_COUNTER: Symbol = symbol_short!("COUNTER");
const A_TOKEN_WASM_HASH: Symbol = symbol_short!("ATWH");
const DEBT_TOKEN_WASM_HASH: Symbol = symbol_short!("DTWH");
const RESERVE_DEPLOYMENT_PAUSED: Symbol = symbol_short!("RDPAUSE");

pub fn is_initialized(env: &Env) -> bool {
    extend_instance_ttl_if_needed(env);
    env.storage().instance().has(&INITIALIZED)
}

pub fn set_initialized(env: &Env) {
    env.storage().instance().set(&INITIALIZED, &true);
    extend_instance_ttl_if_needed(env);
}

pub fn get_pool_admin(env: &Env) -> Result<Address, KineticRouterError> {
    extend_instance_ttl_if_needed(env);
    env.storage()
        .instance()
        .get(&POOL_ADMIN)
        .ok_or(KineticRouterError::NotInitialized)
}

pub fn set_pool_admin(env: &Env, admin: &Address) {
    env.storage().instance().set(&POOL_ADMIN, admin);
    extend_instance_ttl_if_needed(env);
}

pub fn get_pending_pool_admin(env: &Env) -> Result<Address, KineticRouterError> {
    extend_instance_ttl_if_needed(env);
    env.storage()
        .instance()
        .get(&PENDING_POOL_ADMIN)
        .ok_or(KineticRouterError::NoPendingAdmin)
}

pub fn set_pending_pool_admin(env: &Env, pending_admin: &Address) {
    env.storage().instance().set(&PENDING_POOL_ADMIN, pending_admin);
    extend_instance_ttl_if_needed(env);
}

pub fn clear_pending_pool_admin(env: &Env) {
    if env.storage().instance().has(&PENDING_POOL_ADMIN) {
        env.storage().instance().remove(&PENDING_POOL_ADMIN);
    }
}

pub fn get_emergency_admin(env: &Env) -> Option<Address> {
    extend_instance_ttl_if_needed(env);
    env.storage().instance().get(&EMERGENCY_ADMIN)
}

pub fn set_emergency_admin(env: &Env, admin: &Address) {
    env.storage().instance().set(&EMERGENCY_ADMIN, admin);
    extend_instance_ttl_if_needed(env);
}

pub fn get_kinetic_router(env: &Env) -> Result<Address, KineticRouterError> {
    extend_instance_ttl_if_needed(env);
    env.storage()
        .instance()
        .get(&KINETIC_ROUTER)
        .ok_or(KineticRouterError::NotInitialized)
}

pub fn set_kinetic_router(env: &Env, router: &Address) {
    env.storage().instance().set(&KINETIC_ROUTER, router);
    extend_instance_ttl_if_needed(env);
}

pub fn get_price_oracle(env: &Env) -> Result<Address, KineticRouterError> {
    extend_instance_ttl_if_needed(env);
    env.storage()
        .instance()
        .get(&PRICE_ORACLE)
        .ok_or(KineticRouterError::NotInitialized)
}

pub fn set_price_oracle(env: &Env, oracle: &Address) {
    env.storage().instance().set(&PRICE_ORACLE, oracle);
    extend_instance_ttl_if_needed(env);
}

pub fn validate_admin(env: &Env, caller: &Address) -> Result<(), KineticRouterError> {
    let admin = get_pool_admin(env)?;
    if caller != &admin {
        return Err(KineticRouterError::Unauthorized);
    }
    Ok(())
}

pub fn validate_emergency_admin(env: &Env, caller: &Address) -> Result<(), KineticRouterError> {
    let pool_admin = get_pool_admin(env)?;

    if let Some(emergency_admin) = get_emergency_admin(env) {
        if caller != &emergency_admin && caller != &pool_admin {
            return Err(KineticRouterError::Unauthorized);
        }
    } else {
        if caller != &pool_admin {
            return Err(KineticRouterError::Unauthorized);
        }
    }

    Ok(())
}

pub fn get_next_deploy_id(env: &Env) -> u32 {
    let counter: u32 = env.storage().instance().get(&DEPLOY_COUNTER).unwrap_or(0);
    let next = counter + 1;
    env.storage().instance().set(&DEPLOY_COUNTER, &next);
    extend_instance_ttl_if_needed(env);
    counter
}

pub fn get_a_token_wasm_hash(env: &Env) -> Option<BytesN<32>> {
    extend_instance_ttl_if_needed(env);
    env.storage().instance().get(&A_TOKEN_WASM_HASH)
}

pub fn set_a_token_wasm_hash(env: &Env, hash: &BytesN<32>) {
    env.storage().instance().set(&A_TOKEN_WASM_HASH, hash);
    extend_instance_ttl_if_needed(env);
}

pub fn get_debt_token_wasm_hash(env: &Env) -> Option<BytesN<32>> {
    extend_instance_ttl_if_needed(env);
    env.storage().instance().get(&DEBT_TOKEN_WASM_HASH)
}

pub fn set_debt_token_wasm_hash(env: &Env, hash: &BytesN<32>) {
    env.storage().instance().set(&DEBT_TOKEN_WASM_HASH, hash);
    extend_instance_ttl_if_needed(env);
}

pub fn is_reserve_deployment_paused(env: &Env) -> bool {
    extend_instance_ttl_if_needed(env);
    env.storage().instance().get(&RESERVE_DEPLOYMENT_PAUSED).unwrap_or(false)
}

pub fn set_reserve_deployment_paused(env: &Env, paused: bool) {
    env.storage().instance().set(&RESERVE_DEPLOYMENT_PAUSED, &paused);
    extend_instance_ttl_if_needed(env);
}
