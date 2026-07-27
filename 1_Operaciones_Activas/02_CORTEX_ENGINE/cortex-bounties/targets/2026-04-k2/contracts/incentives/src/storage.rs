use crate::error::IncentivesError;
use k2_shared::KineticRouterError;
use soroban_sdk::{contracttype, symbol_short, Address, Env, Symbol, Vec};

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

/// Extend persistent key TTL only if remaining lifetime is below threshold.
fn extend_persistent_ttl_if_needed<K: soroban_sdk::IntoVal<soroban_sdk::Env, soroban_sdk::Val>>(env: &Env, key: &K) {
    env.storage().persistent().extend_ttl(key, TTL_THRESHOLD, TTL_EXTENSION);
}

/// Reward type constants
pub const REWARD_TYPE_SUPPLY: u32 = 0;
pub const REWARD_TYPE_BORROW: u32 = 1;

/// Asset reward configuration
#[contracttype]
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct AssetRewardConfig {
    /// Emission rate in reward tokens per second
    pub emission_per_second: u128,
    /// Distribution end timestamp (0 = no end)
    pub distribution_end: u64,
    /// Whether rewards are currently active
    pub is_active: bool,
}

/// Asset reward index tracking global reward accumulation
#[contracttype]
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct AssetRewardIndex {
    /// Current reward index (scaled by RAY)
    pub index: u128,
    /// Last time the index was updated
    pub last_update_timestamp: u64,
}

/// User reward data tracking individual user rewards
#[contracttype]
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct UserRewardData {
    /// Total accrued rewards (not yet claimed)
    pub accrued: u128,
    /// Index snapshot when user last interacted
    pub index_snapshot: u128,
    /// Balance snapshot when user last interacted (prevents front-running)
    pub balance_snapshot: u128,
}

// Instance storage keys
const INITIALIZED: Symbol = symbol_short!("INIT");
const EMISSION_MANAGER: Symbol = symbol_short!("EMGR");
const LENDING_POOL: Symbol = symbol_short!("LPOL");
const PAUSED: Symbol = symbol_short!("PAUSED");

// Persistent storage key prefixes
const ASSET_REWARD_CONFIG: Symbol = symbol_short!("ARC");
const ASSET_REWARD_INDEX: Symbol = symbol_short!("ARI");
const USER_REWARD_DATA: Symbol = symbol_short!("URD");
const ASSET_REGISTERED: Symbol = symbol_short!("AREG");
const REWARD_TOKEN_REGISTERED: Symbol = symbol_short!("RTREG");
const ASSETS_LIST: Symbol = symbol_short!("ALST"); // Bounded list for enumeration
const REWARD_TOKENS_LIST: Symbol = symbol_short!("RTL"); // Bounded list for enumeration

// Maximum number of assets (prevents unbounded growth)
const MAX_ASSETS: u32 = 100;
// Maximum number of reward tokens per asset (prevents unbounded growth)
const MAX_REWARD_TOKENS_PER_ASSET: u32 = 20;

/// Check if contract is initialized
pub fn is_initialized(env: &Env) -> bool {
    let result = env.storage().instance().has(&INITIALIZED);
    if result {
        extend_instance_ttl_if_needed(env);
    }
    result
}

/// Set initialized flag
pub fn set_initialized(env: &Env) {
    env.storage().instance().set(&INITIALIZED, &true);
    extend_instance_ttl_if_needed(env);
}

/// Get emission manager address
pub fn get_emission_manager(env: &Env) -> Result<Address, KineticRouterError> {
    extend_instance_ttl_if_needed(env);
    env.storage()
        .instance()
        .get(&EMISSION_MANAGER)
        .ok_or(KineticRouterError::NotInitialized)
}

/// Set emission manager address
pub fn set_emission_manager(env: &Env, manager: &Address) {
    env.storage().instance().set(&EMISSION_MANAGER, manager);
    extend_instance_ttl_if_needed(env);
}

/// Validate emission manager
pub fn validate_emission_manager(env: &Env, caller: &Address) -> Result<(), IncentivesError> {
    let manager = get_emission_manager(env)?;
    if caller != &manager {
        return Err(IncentivesError::Unauthorized);
    }
    Ok(())
}

/// Get lending pool address
pub fn get_lending_pool(env: &Env) -> Option<Address> {
    let result = env.storage().instance().get(&LENDING_POOL);
    if result.is_some() {
        extend_instance_ttl_if_needed(env);
    }
    result
}

/// Set lending pool address
pub fn set_lending_pool(env: &Env, pool: &Address) {
    env.storage().instance().set(&LENDING_POOL, pool);
    extend_instance_ttl_if_needed(env);
}

/// Check if contract is paused
pub fn is_paused(env: &Env) -> bool {
    extend_instance_ttl_if_needed(env);
    env.storage().instance().get(&PAUSED).unwrap_or(false)
}

/// Set paused state
pub fn set_paused(env: &Env, paused: bool) {
    env.storage().instance().set(&PAUSED, &paused);
    extend_instance_ttl_if_needed(env);
}

/// Get asset reward configuration
pub fn get_asset_reward_config(
    env: &Env,
    asset: &Address,
    reward_token: &Address,
    reward_type: u32,
) -> Option<AssetRewardConfig> {
    let key = (
        ASSET_REWARD_CONFIG,
        asset.clone(),
        reward_token.clone(),
        reward_type,
    );
    if env.storage().persistent().has(&key) {
        extend_persistent_ttl_if_needed(env, &key);
    }
    env.storage().persistent().get(&key)
}

/// Set asset reward configuration
pub fn set_asset_reward_config(
    env: &Env,
    asset: &Address,
    reward_token: &Address,
    reward_type: u32,
    config: &AssetRewardConfig,
) -> Result<(), IncentivesError> {
    let key = (
        ASSET_REWARD_CONFIG,
        asset.clone(),
        reward_token.clone(),
        reward_type,
    );
    env.storage().persistent().set(&key, config);
    extend_persistent_ttl_if_needed(env, &key);

    // Track asset and reward token
    add_asset(env, asset)?;
    add_reward_token(env, asset, reward_token)?;

    Ok(())
}

/// Check if asset reward index exists
pub fn has_asset_reward_index(
    env: &Env,
    asset: &Address,
    reward_token: &Address,
    reward_type: u32,
) -> bool {
    let key = (
        ASSET_REWARD_INDEX,
        asset.clone(),
        reward_token.clone(),
        reward_type,
    );
    let result = env.storage().persistent().has(&key);
    if result {
        extend_persistent_ttl_if_needed(env, &key);
    }
    result
}

/// Get asset reward index
pub fn get_asset_reward_index(
    env: &Env,
    asset: &Address,
    reward_token: &Address,
    reward_type: u32,
) -> AssetRewardIndex {
    let key = (
        ASSET_REWARD_INDEX,
        asset.clone(),
        reward_token.clone(),
        reward_type,
    );
    if env.storage().persistent().has(&key) {
        extend_persistent_ttl_if_needed(env, &key);
    }
    env.storage()
        .persistent()
        .get(&key)
        .unwrap_or(AssetRewardIndex {
            index: k2_shared::RAY,
            last_update_timestamp: env.ledger().timestamp(),
        })
}

/// Set asset reward index
pub fn set_asset_reward_index(
    env: &Env,
    asset: &Address,
    reward_token: &Address,
    reward_type: u32,
    index: &AssetRewardIndex,
) {
    let key = (
        ASSET_REWARD_INDEX,
        asset.clone(),
        reward_token.clone(),
        reward_type,
    );
    env.storage().persistent().set(&key, index);
    extend_persistent_ttl_if_needed(env, &key);
}

/// Get user reward data
pub fn get_user_reward_data(
    env: &Env,
    asset: &Address,
    reward_token: &Address,
    user: &Address,
    reward_type: u32,
) -> UserRewardData {
    let key = (
        USER_REWARD_DATA,
        asset.clone(),
        reward_token.clone(),
        user.clone(),
        reward_type,
    );
    if env.storage().persistent().has(&key) {
        extend_persistent_ttl_if_needed(env, &key);
    }
    env.storage()
        .persistent()
        .get(&key)
        .unwrap_or(UserRewardData {
            accrued: 0,
            index_snapshot: k2_shared::RAY,
            balance_snapshot: 0,
        })
}

/// Set user reward data
pub fn set_user_reward_data(
    env: &Env,
    asset: &Address,
    reward_token: &Address,
    user: &Address,
    reward_type: u32,
    data: &UserRewardData,
) {
    let key = (
        USER_REWARD_DATA,
        asset.clone(),
        reward_token.clone(),
        user.clone(),
        reward_type,
    );
    env.storage().persistent().set(&key, data);
    extend_persistent_ttl_if_needed(env, &key);
}

/// Check if asset is registered
pub fn is_asset_registered(env: &Env, asset: &Address) -> bool {
    let key = (ASSET_REGISTERED, asset.clone());
    if env.storage().persistent().has(&key) {
        env.storage()
            .persistent()
            .extend_ttl(&key, TTL_THRESHOLD, TTL_EXTENSION);
        true
    } else {
        false
    }
}

/// Register asset (sharded storage - each asset stored as separate key)
/// Uses sharded storage for efficient existence checks and a bounded list for enumeration.
fn add_asset(env: &Env, asset: &Address) -> Result<(), IncentivesError> {
    // Check if already registered using sharded key
    if is_asset_registered(env, asset) {
        return Ok(());
    }

    // Get current list
    let mut assets = get_assets(env);

    // Check if we've reached the limit
    if assets.len() >= MAX_ASSETS as u32 {
        return Err(IncentivesError::MaxAssetsExceeded);
    }

    // Add to sharded storage (for efficient existence checks)
    let sharded_key = (ASSET_REGISTERED, asset.clone());
    env.storage().persistent().set(&sharded_key, &true);
    extend_persistent_ttl_if_needed(env, &sharded_key);

    // Add to bounded list (for enumeration)
    assets.push_back(asset.clone());
    let list_key = ASSETS_LIST;
    env.storage().persistent().set(&list_key, &assets);
    extend_persistent_ttl_if_needed(env, &list_key);

    Ok(())
}

/// Get all configured assets
/// Returns a bounded list (max MAX_ASSETS) for enumeration.
/// Each asset is also stored as a sharded key for efficient existence checks.
pub fn get_assets(env: &Env) -> Vec<Address> {
    let key = ASSETS_LIST;
    if env.storage().persistent().has(&key) {
        extend_persistent_ttl_if_needed(env, &key);
    }
    env.storage()
        .persistent()
        .get(&key)
        .unwrap_or(Vec::new(env))
}

/// Check if reward token is registered for an asset
pub fn is_reward_token_registered(env: &Env, asset: &Address, reward_token: &Address) -> bool {
    let key = (REWARD_TOKEN_REGISTERED, asset.clone(), reward_token.clone());
    if env.storage().persistent().has(&key) {
        env.storage()
            .persistent()
            .extend_ttl(&key, TTL_THRESHOLD, TTL_EXTENSION);
        true
    } else {
        false
    }
}

/// Get reward tokens for an asset
/// Returns a bounded list (max MAX_REWARD_TOKENS_PER_ASSET) for enumeration.
/// Each reward token is also stored as a sharded key for efficient existence checks.
pub fn get_reward_tokens(env: &Env, asset: &Address) -> Vec<Address> {
    let key = (REWARD_TOKENS_LIST, asset.clone());
    if env.storage().persistent().has(&key) {
        extend_persistent_ttl_if_needed(env, &key);
    }
    env.storage()
        .persistent()
        .get(&key)
        .unwrap_or(Vec::new(env))
}

/// Remove a reward token from an asset's registered list and sharded key.
pub fn remove_reward_token(env: &Env, asset: &Address, reward_token: &Address) {
    // Remove sharded existence key
    let sharded_key = (REWARD_TOKEN_REGISTERED, asset.clone(), reward_token.clone());
    if env.storage().persistent().has(&sharded_key) {
        env.storage().persistent().remove(&sharded_key);
    }

    // Remove from enumeration list
    let list_key = (REWARD_TOKENS_LIST, asset.clone());
    let tokens = get_reward_tokens(env, asset);
    let mut new_tokens: Vec<Address> = Vec::new(env);
    for i in 0..tokens.len() {
        if let Some(t) = tokens.get(i) {
            if t != *reward_token {
                new_tokens.push_back(t);
            }
        }
    }
    env.storage().persistent().set(&list_key, &new_tokens);
    extend_persistent_ttl_if_needed(env, &list_key);
}

/// Remove an asset from the global assets list and sharded key.
pub fn remove_asset(env: &Env, asset: &Address) {
    // Remove sharded existence key
    let sharded_key = (ASSET_REGISTERED, asset.clone());
    if env.storage().persistent().has(&sharded_key) {
        env.storage().persistent().remove(&sharded_key);
    }

    // Remove from enumeration list
    let list_key = ASSETS_LIST;
    let assets = get_assets(env);
    let mut new_assets: Vec<Address> = Vec::new(env);
    for i in 0..assets.len() {
        if let Some(a) = assets.get(i) {
            if a != *asset {
                new_assets.push_back(a);
            }
        }
    }
    env.storage().persistent().set(&list_key, &new_assets);
    extend_persistent_ttl_if_needed(env, &list_key);
}

/// Register reward token for an asset
/// Uses sharded storage (per-key) for efficient existence checks and a bounded list for enumeration.
/// The list is bounded to MAX_REWARD_TOKENS_PER_ASSET to prevent unbounded growth.
pub fn add_reward_token(env: &Env, asset: &Address, reward_token: &Address) -> Result<(), IncentivesError> {
    // Check if already registered using sharded key
    if is_reward_token_registered(env, asset, reward_token) {
        return Ok(());
    }

    // Get current list
    let mut tokens = get_reward_tokens(env, asset);

    // Check if we've reached the limit
    if tokens.len() >= MAX_REWARD_TOKENS_PER_ASSET as u32 {
        return Err(IncentivesError::MaxRewardTokensExceeded);
    }

    // Add to sharded storage (for efficient existence checks)
    let sharded_key = (REWARD_TOKEN_REGISTERED, asset.clone(), reward_token.clone());
    env.storage().persistent().set(&sharded_key, &true);
    env.storage()
        .persistent()
        .extend_ttl(&sharded_key, TTL_THRESHOLD, TTL_EXTENSION);

    // Add to bounded list (for enumeration)
    tokens.push_back(reward_token.clone());
    let list_key = (REWARD_TOKENS_LIST, asset.clone());
    env.storage().persistent().set(&list_key, &tokens);
    extend_persistent_ttl_if_needed(env, &list_key);

    Ok(())
}
