use k2_shared::{Asset, AssetConfig, OracleConfig, OracleError, DEFAULT_ORACLE_CONFIG, MAX_RESERVES};
use soroban_sdk::{contracttype, Address, Env, Map, Vec};

// TTL constants: 1 year = 365 days * 17280 ledgers/day ≈ 6,307,200 ledgers
// Extend TTL when remaining time falls below 30 days
pub const TTL_THRESHOLD: u32 = 30 * 17280; // 30 days in ledgers
pub const TTL_EXTENSION: u32 = 365 * 17280; // 1 year in ledgers

/// Instance storage keys for bounded configuration data.
/// 
/// Instance storage is used only for bounded configuration that doesn't grow
/// with the number of assets. Dynamic per-asset data is stored in persistent storage.
#[contracttype]
#[derive(Clone, Debug, Eq, PartialEq)]
pub enum InstanceKey {
    ReflectorContract,
    ReflectorPrecision,
    FallbackOracle,
    OracleConfig,
    BaseCurrency,
    Paused,
    NativeXlmAddress,
    /// TTL in seconds for cached price data. 0 = disabled.
    PriceCacheTtl,
}

/// Persistent storage keys for dynamic per-asset data.
/// 
/// Persistent storage is used for unbounded data that grows with the number of assets,
/// with per-key TTL to avoid size cap issues and shared archival problems.
#[contracttype]
#[derive(Clone, Debug, Eq, PartialEq)]
pub enum PersistentKey {
    /// Asset configuration for a specific asset
    AssetConfig(Asset),
    /// List of all whitelisted assets (for iteration)
    AssetList,
    /// Circuit breaker: stores last validated price per asset to detect anomalous price movements
    LastPrice(Asset),
    /// Cached full PriceData per asset for TTL-based cache
    LastPriceData(Asset),
}

#[allow(dead_code)]
pub fn get_reflector_contract(env: &Env) -> Result<Address, OracleError> {
    let result = env.storage()
        .instance()
        .get(&InstanceKey::ReflectorContract)
        .ok_or(OracleError::NotInitialized);
    if result.is_ok() {
        env.storage().instance().extend_ttl(TTL_THRESHOLD, TTL_EXTENSION);
    }
    result
}

#[allow(dead_code)]
pub fn set_reflector_contract(env: &Env, reflector: &Address) {
    env.storage()
        .instance()
        .set(&InstanceKey::ReflectorContract, reflector);
    env.storage().instance().extend_ttl(TTL_THRESHOLD, TTL_EXTENSION);
}

#[allow(dead_code)]
pub fn get_fallback_oracle(env: &Env) -> Option<Address> {
    let result = env.storage().instance().get(&InstanceKey::FallbackOracle);
    if result.is_some() {
        env.storage().instance().extend_ttl(TTL_THRESHOLD, TTL_EXTENSION);
    }
    result
}

#[allow(dead_code)]
pub fn set_fallback_oracle(env: &Env, fallback: &Address) {
    env.storage()
        .instance()
        .set(&InstanceKey::FallbackOracle, fallback);
    env.storage().instance().extend_ttl(TTL_THRESHOLD, TTL_EXTENSION);
}

pub fn get_oracle_config(env: &Env) -> Result<OracleConfig, OracleError> {
    env.storage().instance().extend_ttl(TTL_THRESHOLD, TTL_EXTENSION);
    let mut config = env
        .storage()
        .instance()
        .get(&InstanceKey::OracleConfig)
        .unwrap_or(DEFAULT_ORACLE_CONFIG);
    
    if let Some(stored_precision) = env.storage().instance().get(&InstanceKey::ReflectorPrecision) {
        config.price_precision = stored_precision;
    }
    
    Ok(config)
}

/// Get the stored Reflector precision (decimals from the Reflector contract).
/// Returns None if not yet initialized.
#[allow(dead_code)]
pub fn get_reflector_precision(env: &Env) -> Option<u32> {
    let result = env.storage().instance().get(&InstanceKey::ReflectorPrecision);
    if result.is_some() {
        env.storage().instance().extend_ttl(TTL_THRESHOLD, TTL_EXTENSION);
    }
    result
}

/// Set the Reflector precision (decimals from the Reflector contract).
/// This should be called whenever the Reflector contract address is set or updated.
pub fn set_reflector_precision(env: &Env, precision: u32) {
    env.storage()
        .instance()
        .set(&InstanceKey::ReflectorPrecision, &precision);
    env.storage().instance().extend_ttl(TTL_THRESHOLD, TTL_EXTENSION);
}

pub fn set_oracle_config(env: &Env, config: &OracleConfig) {
    let mut config_to_store = config.clone();
    if let Some(stored_precision) = env.storage().instance().get(&InstanceKey::ReflectorPrecision) {
        config_to_store.price_precision = stored_precision;
    }
    env.storage().instance().set(&InstanceKey::OracleConfig, &config_to_store);
    env.storage().instance().extend_ttl(TTL_THRESHOLD, TTL_EXTENSION);
}

/// Get asset configuration for a specific asset from persistent storage.
pub fn get_asset_config(env: &Env, asset: &Asset) -> Option<AssetConfig> {
    let key = PersistentKey::AssetConfig(asset.clone());
    if env.storage().persistent().has(&key) {
        env.storage()
            .persistent()
            .extend_ttl(&key, TTL_THRESHOLD, TTL_EXTENSION);
    }
    env.storage().persistent().get(&key)
}

/// Set asset configuration for a specific asset in persistent storage.
pub fn set_asset_config(env: &Env, asset: &Asset, config: &AssetConfig) {
    let key = PersistentKey::AssetConfig(asset.clone());
    env.storage().persistent().set(&key, config);
    env.storage()
        .persistent()
        .extend_ttl(&key, TTL_THRESHOLD, TTL_EXTENSION);
}

/// Remove asset configuration for a specific asset from persistent storage.
#[allow(dead_code)]
pub fn remove_asset_config(env: &Env, asset: &Asset) {
    let key = PersistentKey::AssetConfig(asset.clone());
    env.storage().persistent().remove(&key);
}

/// Get all whitelisted assets as a map (for backward compatibility).
/// 
/// Note: This iterates through the asset list, so it may be expensive for large numbers of assets.
#[allow(dead_code)]
pub fn get_whitelisted_assets(env: &Env) -> Map<Asset, AssetConfig> {
    let asset_list = get_asset_list(env);
    let mut whitelist = Map::new(env);
    let len = asset_list.len().min(MAX_RESERVES);
    for i in 0..len {
        if let Some(asset) = asset_list.get(i) {
            if let Some(config) = get_asset_config(env, &asset) {
                whitelist.set(asset, config);
            }
        }
    }
    whitelist
}

/// Set whitelisted assets from a map (for backward compatibility during migration).
/// 
/// This function is used during initialization and migration.
#[allow(dead_code)]
pub fn set_whitelisted_assets(env: &Env, assets: &Map<Asset, AssetConfig>) {
    // Clear existing asset list
    let list_key = PersistentKey::AssetList;
    if env.storage().persistent().has(&list_key) {
        env.storage().persistent().remove(&list_key);
    }
    
    // Set each asset config individually
    let mut asset_list = Vec::new(env);
    let mut iter = assets.iter();
    while let Some((asset, config)) = iter.next() {
        set_asset_config(env, &asset, &config);
        asset_list.push_back(asset);
    }
    
    // Set asset list
    if asset_list.len() > 0 {
        env.storage().persistent().set(&list_key, &asset_list);
        env.storage()
            .persistent()
            .extend_ttl(&list_key, TTL_THRESHOLD, TTL_EXTENSION);
    }
}

/// Get the list of all whitelisted assets from persistent storage.
pub fn get_asset_list(env: &Env) -> Vec<Asset> {
    let key = PersistentKey::AssetList;
    if env.storage().persistent().has(&key) {
        env.storage()
            .persistent()
            .extend_ttl(&key, TTL_THRESHOLD, TTL_EXTENSION);
        env.storage().persistent().get(&key).unwrap_or_else(|| Vec::new(env))
    } else {
        Vec::new(env)
    }
}

/// Set the list of all whitelisted assets in persistent storage.
/// Bounded by MAX_RESERVES (64) - enforced in add_to_asset_list
pub fn set_asset_list(env: &Env, assets: &Vec<Asset>) {
    let key = PersistentKey::AssetList;
    if assets.len() == 0 {
        if env.storage().persistent().has(&key) {
            env.storage().persistent().remove(&key);
        }
    } else {
        env.storage().persistent().set(&key, assets);
        env.storage()
            .persistent()
            .extend_ttl(&key, TTL_THRESHOLD, TTL_EXTENSION);
    }
}

/// Add an asset to the asset list if not already present.
#[allow(dead_code)]
pub fn add_to_asset_list(env: &Env, asset: &Asset) -> Result<(), OracleError> {
    let mut asset_list = get_asset_list(env);
    
    // Check if asset is already in list
    let mut found = false;
    let len = asset_list.len().min(MAX_RESERVES);
    for i in 0..len {
        if asset_list.get(i).ok_or(OracleError::AssetNotWhitelisted)? == *asset {
            found = true;
            break;
        }
    }
    
    if !found {
        asset_list.push_back(asset.clone());
        set_asset_list(env, &asset_list);
    }
    Ok(())
}

/// Remove an asset from the asset list.
#[allow(dead_code)]
pub fn remove_from_asset_list(env: &Env, asset: &Asset) {
    let asset_list = get_asset_list(env);
    let mut new_list = Vec::new(env);
    let len = asset_list.len().min(MAX_RESERVES);
    for i in 0..len {
        if let Some(a) = asset_list.get(i) {
            if a != *asset {
                new_list.push_back(a);
            }
        }
    }
    set_asset_list(env, &new_list);
}

/// Retrieves the last validated price stored for circuit breaker validation.
/// 
/// Returns None if no price has been recorded yet for this asset (first query scenario).
pub fn get_last_price(env: &Env, asset: &Asset) -> Option<u128> {
    let key = PersistentKey::LastPrice(asset.clone());
    if env.storage().persistent().has(&key) {
        env.storage()
            .persistent()
            .extend_ttl(&key, TTL_THRESHOLD, TTL_EXTENSION);
    }
    env.storage().persistent().get(&key)
}

/// Stores the validated price for future circuit breaker comparisons.
/// 
/// Called after price validation passes to enable change detection on subsequent queries.
pub fn set_last_price(env: &Env, asset: &Asset, price: u128) {
    let key = PersistentKey::LastPrice(asset.clone());
    env.storage().persistent().set(&key, &price);
    env.storage()
        .persistent()
        .extend_ttl(&key, TTL_THRESHOLD, TTL_EXTENSION);
}

/// Clears the stored price, resetting circuit breaker for this asset.
/// 
/// Used by admin reset functions to allow legitimate large price movements after
/// major market events or oracle upgrades.
pub fn clear_last_price(env: &Env, asset: &Asset) {
    let key = PersistentKey::LastPrice(asset.clone());
    env.storage().persistent().remove(&key);
    // Also clear the TTL cache to prevent stale cached prices surviving config changes
    clear_last_price_data(env, asset);
}

/// Clears only the TTL-cached price data for an asset.
pub fn clear_last_price_data(env: &Env, asset: &Asset) {
    let key = PersistentKey::LastPriceData(asset.clone());
    if env.storage().persistent().has(&key) {
        env.storage().persistent().remove(&key);
    }
}

/// Get the native XLM address for this network.
/// Used to convert XLM address to "XLM" symbol for reflector oracle.
pub fn get_native_xlm_address(env: &Env) -> Result<Address, OracleError> {
    let result = env.storage()
        .instance()
        .get(&InstanceKey::NativeXlmAddress)
        .ok_or(OracleError::NotInitialized);
    if result.is_ok() {
        env.storage().instance().extend_ttl(TTL_THRESHOLD, TTL_EXTENSION);
    }
    result
}

/// Set the native XLM address for this network.
/// Should be called during initialization.
pub fn set_native_xlm_address(env: &Env, xlm_address: &Address) {
    env.storage()
        .instance()
        .set(&InstanceKey::NativeXlmAddress, xlm_address);
    env.storage().instance().extend_ttl(TTL_THRESHOLD, TTL_EXTENSION);
}

// --- Price cache helpers ---

/// Cached price data with the ledger timestamp when it was cached.
#[contracttype]
#[derive(Clone, Debug)]
pub struct CachedPriceData {
    pub price: u128,
    pub timestamp: u64,
    /// Ledger timestamp when this entry was cached
    pub cached_at: u64,
}

/// Get cached PriceData for an asset (used for TTL-based cache).
pub fn get_last_price_data(env: &Env, asset: &Asset) -> Option<CachedPriceData> {
    let key = PersistentKey::LastPriceData(asset.clone());
    if env.storage().persistent().has(&key) {
        env.storage()
            .persistent()
            .extend_ttl(&key, TTL_THRESHOLD, TTL_EXTENSION);
    }
    env.storage().persistent().get(&key)
}

/// Store PriceData for an asset with current ledger time as cached_at.
pub fn set_last_price_data(env: &Env, asset: &Asset, data: &k2_shared::PriceData) {
    let cached = CachedPriceData {
        price: data.price,
        timestamp: data.timestamp,
        cached_at: env.ledger().timestamp(),
    };
    let key = PersistentKey::LastPriceData(asset.clone());
    env.storage().persistent().set(&key, &cached);
    env.storage()
        .persistent()
        .extend_ttl(&key, TTL_THRESHOLD, TTL_EXTENSION);
}

/// Get the price cache TTL in seconds. Returns 0 (disabled) if not set.
pub fn get_price_cache_ttl(env: &Env) -> u64 {
    env.storage()
        .instance()
        .get(&InstanceKey::PriceCacheTtl)
        .unwrap_or(0)
}

/// Set the price cache TTL in seconds. 0 = disabled.
pub fn set_price_cache_ttl(env: &Env, ttl: u64) {
    env.storage()
        .instance()
        .set(&InstanceKey::PriceCacheTtl, &ttl);
    env.storage().instance().extend_ttl(TTL_THRESHOLD, TTL_EXTENSION);
}
