use soroban_sdk::{contracttype, Address, Env, String};
use k2_shared::TokenError;

// TTL constants: 1 year = 365 days * 17280 ledgers/day ≈ 6,307,200 ledgers
// Extend TTL when remaining time falls below 30 days
const TTL_THRESHOLD: u32 = 30 * 17280; // 30 days in ledgers
const TTL_EXTENSION: u32 = 365 * 17280; // 1 year in ledgers

#[contracttype]
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct DebtTokenState {
    pub borrowed_asset: Address,
    pub pool_address: Address,
    pub total_debt_scaled: i128,
    pub name: String,
    pub symbol: String,
    pub decimals: u32,
}

#[contracttype]
#[derive(Clone, Debug, Eq, PartialEq)]
pub enum DataKey {
    State,
    Debt(Address),
    IncentivesContract,
}

pub fn get_state(env: &Env) -> Result<DebtTokenState, TokenError> {
    env.storage().instance().extend_ttl(TTL_THRESHOLD, TTL_EXTENSION);
    env.storage()
        .instance()
        .get(&DataKey::State)
        .ok_or(TokenError::TokenNotFound)
}

pub fn set_state(env: &Env, state: &DebtTokenState) {
    env.storage().instance().set(&DataKey::State, state);
    env.storage().instance().extend_ttl(TTL_THRESHOLD, TTL_EXTENSION);
}

pub fn has_state(env: &Env) -> bool {
    let result = env.storage().instance().has(&DataKey::State);
    if result {
        env.storage().instance().extend_ttl(TTL_THRESHOLD, TTL_EXTENSION);
    }
    result
}

pub fn get_scaled_debt(env: &Env, user: &Address) -> u128 {
    let key = DataKey::Debt(user.clone());
    if env.storage().persistent().has(&key) {
        env.storage()
            .persistent()
            .extend_ttl(&key, TTL_THRESHOLD, TTL_EXTENSION);
    }
    env.storage().persistent().get(&key).unwrap_or(0)
}

pub fn set_scaled_debt(env: &Env, user: &Address, debt: u128) {
    let key = DataKey::Debt(user.clone());
    env.storage().persistent().set(&key, &debt);
    env.storage()
        .persistent()
        .extend_ttl(&key, TTL_THRESHOLD, TTL_EXTENSION);
}

/// Get cached incentives contract address
pub fn get_incentives_contract(env: &Env) -> Option<Address> {
    let result = env.storage().instance().get(&DataKey::IncentivesContract);
    if result.is_some() {
        env.storage().instance().extend_ttl(TTL_THRESHOLD, TTL_EXTENSION);
    }
    result
}

/// Set cached incentives contract address
pub fn set_incentives_contract(env: &Env, incentives: &Address) {
    env.storage().instance().set(&DataKey::IncentivesContract, incentives);
    env.storage().instance().extend_ttl(TTL_THRESHOLD, TTL_EXTENSION);
}

/// Check if caller is authorized (only pool)
pub fn is_authorized_caller(_env: &Env, caller: &Address, pool: &Address) -> bool {
    caller == pool
}
