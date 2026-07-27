use crate::error::TreasuryError;
use k2_shared::upgradeable;
use soroban_sdk::{contracttype, Address, Env, Map, Vec};

// TTL constants: 1 year = 365 days * 17280 ledgers/day ≈ 6,307,200 ledgers
// Extend TTL when remaining time falls below 30 days
const TTL_THRESHOLD: u32 = 30 * 17280; // 30 days in ledgers
const TTL_EXTENSION: u32 = 365 * 17280; // 1 year in ledgers

/// Storage keys for treasury contract.
///
/// Instance storage is used only for bounded configuration data (initialized flag).
/// Dynamic per-asset data (balances) is stored in persistent storage with per-key TTL
/// to avoid size cap issues and shared archival problems.
#[contracttype]
#[derive(Clone, Debug, Eq, PartialEq)]
pub enum InstanceKey {
    /// Flag indicating whether the contract has been initialized
    Initialized,
}

/// Persistent storage keys for per-asset balances.
#[contracttype]
#[derive(Clone, Debug, Eq, PartialEq)]
pub enum PersistentKey {
    /// Balance for a specific asset
    Balance(Address),
    /// List of assets that have balances (for iteration)
    AssetList,
}

/// Check if the treasury contract has been initialized.
///
/// Returns true if initialize() has been called successfully, false otherwise.
pub fn is_initialized(env: &Env) -> bool {
    let result = env.storage().instance().has(&InstanceKey::Initialized);
    if result {
        env.storage().instance().extend_ttl(TTL_THRESHOLD, TTL_EXTENSION);
    }
    result
}

/// Mark the treasury contract as initialized.
///
/// This should only be called once during contract initialization to prevent
/// reinitialization attacks.
pub fn set_initialized(env: &Env) {
    env.storage().instance().set(&InstanceKey::Initialized, &true);
    env.storage().instance().extend_ttl(TTL_THRESHOLD, TTL_EXTENSION);
}

/// Get the tracked balance for a specific asset.
///
/// Returns 0 if the asset has never been deposited.
pub fn get_balance(env: &Env, asset: &Address) -> u128 {
    let key = PersistentKey::Balance(asset.clone());
    if env.storage().persistent().has(&key) {
        env.storage()
            .persistent()
            .extend_ttl(&key, TTL_THRESHOLD, TTL_EXTENSION);
    }
    env.storage().persistent().get(&key).unwrap_or(0)
}

/// Set the balance for a specific asset.
///
/// This overwrites any existing balance for the asset. Use add_balance() or
/// subtract_balance() for safer operations that check for overflow/underflow.
pub fn set_balance(env: &Env, asset: &Address, amount: u128) -> Result<(), TreasuryError> {
    let key = PersistentKey::Balance(asset.clone());
    
    // Update balance
    if amount == 0 {
        // Remove balance entry if zero
        if env.storage().persistent().has(&key) {
            env.storage().persistent().remove(&key);
        }
        // Remove from asset list if zero
        remove_from_asset_list(env, asset);
    } else {
        env.storage().persistent().set(&key, &amount);
        env.storage()
            .persistent()
            .extend_ttl(&key, TTL_THRESHOLD, TTL_EXTENSION);
        // Add to asset list if not already present
        add_to_asset_list(env, asset)?;
    }
    Ok(())
}

/// Add to the balance of a specific asset.
///
/// Uses checked arithmetic to prevent overflow. Returns the new balance on success.
pub fn add_balance(env: &Env, asset: &Address, amount: u128) -> Result<u128, TreasuryError> {
    let current = get_balance(env, asset);
    let new_balance = current
        .checked_add(amount)
        .ok_or(TreasuryError::InvalidAmount)?;
    set_balance(env, asset, new_balance)?;
    Ok(new_balance)
}

/// Subtract from the balance of a specific asset.
///
/// Checks for underflow before subtracting. Returns the new balance on success.
pub fn subtract_balance(
    env: &Env,
    asset: &Address,
    amount: u128,
) -> Result<u128, TreasuryError> {
    let current = get_balance(env, asset);
    if current < amount {
        return Err(TreasuryError::InsufficientBalance);
    }
    let new_balance = current - amount;
    set_balance(env, asset, new_balance)?;
    Ok(new_balance)
}

/// Verify that the caller has admin privileges.
///
/// Supports single-admin configurations.
pub fn require_admin(env: &Env, caller: &Address) -> Result<(), TreasuryError> {
    upgradeable::admin::require_admin(env, caller)
        .map_err(|_| TreasuryError::Unauthorized)
}

/// Get all tracked balances in the treasury.
///
/// Returns an empty map if no assets have been deposited yet.
pub fn get_all_balances(env: &Env) -> Result<Map<Address, u128>, TreasuryError> {
    let asset_list_key = PersistentKey::AssetList;
    let asset_list = if env.storage().persistent().has(&asset_list_key) {
        env.storage()
            .persistent()
            .extend_ttl(&asset_list_key, TTL_THRESHOLD, TTL_EXTENSION);
        env.storage()
            .persistent()
            .get(&asset_list_key)
            .ok_or(TreasuryError::AssetNotFound)?
    } else {
        Vec::new(env)
    };
    
    let mut balances = Map::new(env);
    for i in 0..asset_list.len() {
        if let Some(asset) = asset_list.get(i) {
            let balance = get_balance(env, &asset);
            if balance > 0 {
                balances.set(asset, balance);
            }
        }
    }
    Ok(balances)
}

/// Add an asset to the asset list if not already present.
fn add_to_asset_list(env: &Env, asset: &Address) -> Result<(), TreasuryError> {
    let key = PersistentKey::AssetList;
    let mut asset_list = if env.storage().persistent().has(&key) {
        env.storage()
            .persistent()
            .extend_ttl(&key, TTL_THRESHOLD, TTL_EXTENSION);
        env.storage()
            .persistent()
            .get(&key)
            .ok_or(TreasuryError::AssetNotFound)?
    } else {
        Vec::new(env)
    };
    
    // Check if asset is already in list
    let mut found = false;
    for i in 0..asset_list.len() {
        if asset_list.get(i).ok_or(TreasuryError::AssetNotFound)? == *asset {
            found = true;
            break;
        }
    }
    
    if !found {
        asset_list.push_back(asset.clone());
        env.storage().persistent().set(&key, &asset_list);
        env.storage()
            .persistent()
            .extend_ttl(&key, TTL_THRESHOLD, TTL_EXTENSION);
    }
    Ok(())
}

/// Remove an asset from the asset list.
fn remove_from_asset_list(env: &Env, asset: &Address) {
    let key = PersistentKey::AssetList;
    if !env.storage().persistent().has(&key) {
        return;
    }
    
    env.storage()
        .persistent()
        .extend_ttl(&key, TTL_THRESHOLD, TTL_EXTENSION);
    let asset_list: Vec<Address> = match env.storage().persistent().get::<PersistentKey, Vec<Address>>(&key) {
        Some(list) => list,
        None => return,
    };
    
    let mut new_list = Vec::new(env);
    for i in 0..asset_list.len() {
        if let Some(a) = asset_list.get(i) {
            if a != *asset {
                new_list.push_back(a);
            }
        }
    }
    
    if new_list.len() == 0 {
        env.storage().persistent().remove(&key);
    } else {
        env.storage().persistent().set(&key, &new_list);
        env.storage()
            .persistent()
            .extend_ttl(&key, TTL_THRESHOLD, TTL_EXTENSION);
    }
}

