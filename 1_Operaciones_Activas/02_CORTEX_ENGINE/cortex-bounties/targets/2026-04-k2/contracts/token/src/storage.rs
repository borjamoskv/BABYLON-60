use soroban_sdk::{contracttype, Address, Env, String};
use crate::types::AllowanceData;
use crate::error::TokenError;

// TTL constants: 1 year = 365 days * 17280 ledgers/day ≈ 6,307,200 ledgers
// Extend TTL when remaining time falls below 30 days
const TTL_THRESHOLD: u32 = 30 * 17280; // 30 days in ledgers
const TTL_EXTENSION: u32 = 365 * 17280; // 1 year in ledgers

#[contracttype]
#[derive(Clone, Debug, Eq, PartialEq)]
pub enum DataKey {
    Admin,
    Name,
    Symbol,
    Decimals,
    Balance(Address),
    Allowance(Address, Address),
}

// Admin
pub fn get_admin(env: &Env) -> Result<Address, TokenError> {
    let result = env.storage()
        .instance()
        .get(&DataKey::Admin)
        .ok_or(TokenError::Unauthorized)?;
    env.storage().instance().extend_ttl(TTL_THRESHOLD, TTL_EXTENSION);
    Ok(result)
}

pub fn set_admin(env: &Env, admin: &Address) {
    env.storage().instance().set(&DataKey::Admin, admin);
    env.storage().instance().extend_ttl(TTL_THRESHOLD, TTL_EXTENSION);
}

pub fn has_admin(env: &Env) -> bool {
    let result = env.storage().instance().has(&DataKey::Admin);
    if result {
        env.storage().instance().extend_ttl(TTL_THRESHOLD, TTL_EXTENSION);
    }
    result
}

// Metadata
pub fn get_name(env: &Env) -> Result<String, TokenError> {
    let result = env.storage()
        .instance()
        .get(&DataKey::Name)
        .ok_or(TokenError::TokenNotFound)?;
    env.storage().instance().extend_ttl(TTL_THRESHOLD, TTL_EXTENSION);
    Ok(result)
}

pub fn set_name(env: &Env, name: &String) {
    env.storage().instance().set(&DataKey::Name, name);
    env.storage().instance().extend_ttl(TTL_THRESHOLD, TTL_EXTENSION);
}

pub fn get_symbol(env: &Env) -> Result<String, TokenError> {
    let result = env.storage()
        .instance()
        .get(&DataKey::Symbol)
        .ok_or(TokenError::TokenNotFound)?;
    env.storage().instance().extend_ttl(TTL_THRESHOLD, TTL_EXTENSION);
    Ok(result)
}

/// Set token symbol (small, fixed-size string set once during initialization)
/// Safe for instance storage as symbols are typically 3-10 characters
pub fn set_symbol(env: &Env, symbol: &String) {
    env.storage().instance().set(&DataKey::Symbol, symbol);
    env.storage().instance().extend_ttl(TTL_THRESHOLD, TTL_EXTENSION);
}

pub fn get_decimals(env: &Env) -> Result<u32, TokenError> {
    let result = env.storage()
        .instance()
        .get(&DataKey::Decimals)
        .ok_or(TokenError::TokenNotFound)?;
    env.storage().instance().extend_ttl(TTL_THRESHOLD, TTL_EXTENSION);
    Ok(result)
}

pub fn set_decimals(env: &Env, decimals: u32) {
    env.storage().instance().set(&DataKey::Decimals, &decimals);
    env.storage().instance().extend_ttl(TTL_THRESHOLD, TTL_EXTENSION);
}


// Balance
pub fn get_balance(env: &Env, id: &Address) -> i128 {
    let key = DataKey::Balance(id.clone());
    if env.storage().persistent().has(&key) {
        env.storage()
            .persistent()
            .extend_ttl(&key, TTL_THRESHOLD, TTL_EXTENSION);
    }
    env.storage().persistent().get(&key).unwrap_or(0)
}

pub fn set_balance(env: &Env, id: &Address, balance: &i128) {
    let key = DataKey::Balance(id.clone());
    env.storage().persistent().set(&key, balance);
    env.storage()
        .persistent()
        .extend_ttl(&key, TTL_THRESHOLD, TTL_EXTENSION);
}

// Allowance
pub fn get_allowance(env: &Env, from: &Address, spender: &Address) -> AllowanceData {
    let key = DataKey::Allowance(from.clone(), spender.clone());
    if env.storage().persistent().has(&key) {
        env.storage()
            .persistent()
            .extend_ttl(&key, TTL_THRESHOLD, TTL_EXTENSION);
    }
    env.storage()
        .persistent()
        .get(&key)
        .unwrap_or(AllowanceData {
            amount: 0,
            expiration_ledger: 0,
        })
}

pub fn set_allowance(env: &Env, from: &Address, spender: &Address, allowance: &AllowanceData) {
    let key = DataKey::Allowance(from.clone(), spender.clone());
    env.storage().persistent().set(&key, allowance);
    env.storage()
        .persistent()
        .extend_ttl(&key, TTL_THRESHOLD, TTL_EXTENSION);
}
