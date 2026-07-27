use crate::oracle;
use crate::storage;
use k2_shared::{upgradeable::admin, *};
use soroban_sdk::{contract, contractimpl, symbol_short, Address, BytesN, Env, Map, String, Vec};

#[contract]
pub struct PriceOracleContract;

#[contractimpl]
impl PriceOracleContract {
    pub fn __constructor(
        env: Env,
        admin: Address,
        reflector_contract: Address,
        base_currency_address: Address,
        native_xlm_address: Address,
    ) {
        if env.storage().instance().has(&ADMIN_KEY) {
            panic!("Already initialized");
        }

        crate::upgrade::initialize_admin(&env, &admin);

        storage::set_reflector_contract(&env, &reflector_contract);

        let reflector_precision = oracle::query_reflector_decimals(&env, &reflector_contract).unwrap();
        storage::set_reflector_precision(&env, reflector_precision);

        let base_currency = Asset::Stellar(base_currency_address);
        env.storage()
            .instance()
            .set(&storage::InstanceKey::BaseCurrency, &base_currency);
        env.storage().instance().extend_ttl(storage::TTL_THRESHOLD, storage::TTL_EXTENSION);

        storage::set_native_xlm_address(&env, &native_xlm_address);

        let whitelist: Map<Asset, AssetConfig> = Map::new(&env);
        storage::set_whitelisted_assets(&env, &whitelist);

        let asset_list: Vec<Asset> = Vec::new(&env);
        storage::set_asset_list(&env, &asset_list);

        env.storage().instance().set(&storage::InstanceKey::Paused, &false);
        env.storage()
            .instance()
            .set(&storage::InstanceKey::FallbackOracle, &Option::<Address>::None);
        env.storage().instance().extend_ttl(storage::TTL_THRESHOLD, storage::TTL_EXTENSION);
    }

    pub fn initialize(
        _env: Env,
        _admin: Address,
        _reflector_contract: Address,
        _base_currency_address: Address,
        _native_xlm_address: Address,
    ) -> Result<(), OracleError> {
        panic!("Initialization is atomic at deployment. Use __constructor.");
    }

    pub fn add_asset(env: Env, caller: Address, asset: Asset) -> Result<(), OracleError> {
        admin::require_admin(&env, &caller).map_err(|_| OracleError::Unauthorized)?;
        caller.require_auth();

        if storage::get_asset_config(&env, &asset).is_some() {
            return Err(OracleError::AssetAlreadyWhitelisted);
        }

        let config = AssetConfig {
            asset: asset.clone(),
            enabled: true,
            manual_override_price: None,
            override_expiry_timestamp: None,
            override_set_timestamp: None,
            custom_oracle: None,
            max_age: None,
            oracle_decimals: None,
            batch_adapter: None,
            feed_id: None,
        };
        storage::set_asset_config(&env, &asset, &config);
        storage::add_to_asset_list(&env, &asset)?;

        env.events().publish(
            (symbol_short!("asset"), symbol_short!("added")),
            asset,
        );

        Ok(())
    }

    pub fn remove_asset(env: Env, asset: Asset) -> Result<(), OracleError> {
        let admin: Address = admin::get_admin(&env).map_err(|_| OracleError::Unauthorized)?;
        admin.require_auth();

        storage::remove_asset_config(&env, &asset);
        storage::remove_from_asset_list(&env, &asset);
        // M-07
        storage::clear_last_price(&env, &asset);

        env.events().publish(
            (symbol_short!("asset"), symbol_short!("removed")),
            asset,
        );

        Ok(())
    }

    /// Sets a manual price override for emergency situations.
    /// Requires an expiry timestamp to prevent permanent mispricing.
    /// 
    /// # Arguments
    /// * `caller` - Admin address (must be authorized)
    /// * `asset` - Asset to override price for
    /// * `price` - Override price (None to remove override)
    /// * `expiry_timestamp` - Expiry timestamp in seconds (None to remove override, required when setting price)
    pub fn set_manual_override(
        env: Env,
        caller: Address,
        asset: Asset,
        price: Option<u128>,
        expiry_timestamp: Option<u64>,
    ) -> Result<(), OracleError> {
        admin::require_admin(&env, &caller).map_err(|_| OracleError::Unauthorized)?;
        caller.require_auth();

        let mut config = storage::get_asset_config(&env, &asset)
            .ok_or(OracleError::AssetNotWhitelisted)?;
        
        // If setting a price, expiry timestamp is required
        if let Some(new_price) = price {
            let expiry = expiry_timestamp.ok_or(OracleError::InvalidCalculation)?;
            let current_time = env.ledger().timestamp();
            
            // Validate expiry is in the future
            if expiry <= current_time {
                return Err(OracleError::InvalidCalculation);
            }

            // L-04
            const MAX_MANUAL_OVERRIDE_DURATION: u64 = 604_800; // 7 days in seconds
            if (expiry - current_time) > MAX_MANUAL_OVERRIDE_DURATION {
                return Err(OracleError::OverrideDurationTooLong);
            }
            
            // Validate price change against circuit breaker before setting override
            let oracle_config = storage::get_oracle_config(&env)?;
            Self::validate_price_change(&env, &asset, &new_price, &oracle_config)?;
            
            config.manual_override_price = Some(new_price);
            config.override_expiry_timestamp = Some(expiry);
            // H-01: Store the observation timestamp so downstream staleness checks work
            config.override_set_timestamp = Some(current_time);
            // WP-H7: Bust TTL cache so batch query honours override immediately
            storage::clear_last_price_data(&env, &asset);
        } else {
            // Removing override
            config.manual_override_price = None;
            config.override_expiry_timestamp = None;
            config.override_set_timestamp = None;
            // M-07
            storage::clear_last_price(&env, &asset);
        }
        
        storage::set_asset_config(&env, &asset, &config);

        env.events().publish(
            (symbol_short!("manual"), symbol_short!("override"), symbol_short!("set")),
            (asset.clone(), price, expiry_timestamp),
        );

        Ok(())
    }

    pub fn add_asset_by_address(env: Env, caller: Address, asset_address: Address) -> Result<(), OracleError> {
        let asset = Asset::Stellar(asset_address);
        Self::add_asset(env, caller, asset)
    }


    pub fn set_asset_enabled(env: Env, caller: Address, asset: Asset, enabled: bool) -> Result<(), OracleError> {
        admin::require_admin(&env, &caller).map_err(|_| OracleError::Unauthorized)?;
        caller.require_auth();

        let mut config = storage::get_asset_config(&env, &asset)
            .ok_or(OracleError::AssetNotWhitelisted)?;
        config.enabled = enabled;
        storage::set_asset_config(&env, &asset, &config);

        env.events().publish(
            (symbol_short!("asset"), symbol_short!("enabled")),
            (asset, enabled),
        );

        Ok(())
    }

    pub fn update_reflector_contract(env: Env, caller: Address, new_contract: Address) -> Result<(), OracleError> {
        admin::require_admin(&env, &caller).map_err(|_| OracleError::Unauthorized)?;
        caller.require_auth();
        storage::set_reflector_contract(&env, &new_contract);
        
        let reflector_precision = oracle::query_reflector_decimals(&env, &new_contract)?;
        storage::set_reflector_precision(&env, reflector_precision);
        
        env.events().publish(
            (symbol_short!("oracle"), symbol_short!("address"), symbol_short!("set")),
            new_contract,
        );
        
        Ok(())
    }

    /// Set a custom oracle for an asset. The oracle must implement:
    ///   - lastprice(asset: Asset) -> Option<PriceData>
    ///   - decimals() -> u32  (skipped if `decimals` param is provided)
    pub fn set_custom_oracle(
        env: Env,
        caller: Address,
        asset: Asset,
        oracle: Option<Address>,
        max_age_seconds: Option<u64>,
        decimals: Option<u32>,
    ) -> Result<(), OracleError> {
        admin::require_admin(&env, &caller).map_err(|_| OracleError::Unauthorized)?;
        caller.require_auth();

        // Validate decimals range if provided
        if let Some(d) = decimals {
            if d > 18 {
                return Err(OracleError::InvalidConfig);
            }
        }

        let mut config = storage::get_asset_config(&env, &asset)
            .ok_or(OracleError::AssetNotWhitelisted)?;
        config.custom_oracle = oracle.clone();
        config.max_age = max_age_seconds;
        config.oracle_decimals = decimals;
        storage::set_asset_config(&env, &asset, &config);

        env.events().publish(
            (symbol_short!("oracle"), symbol_short!("set")),
            (asset, oracle, max_age_seconds),
        );

        Ok(())
    }

    /// Get custom oracle address for a specific asset
    pub fn get_custom_oracle(env: Env, asset: Asset) -> Option<Address> {
        storage::get_asset_config(&env, &asset)
            .and_then(|config| config.custom_oracle)
    }

    pub fn set_fallback_oracle(
        env: Env,
        caller: Address,
        fallback_contract: Option<Address>,
    ) -> Result<(), OracleError> {
        admin::require_admin(&env, &caller).map_err(|_| OracleError::Unauthorized)?;
        caller.require_auth();
        
        // Clone for event emission
        let fallback_contract_clone = fallback_contract.clone();
        
        if let Some(fallback) = fallback_contract {
            storage::set_fallback_oracle(&env, &fallback);
        } else {
            // Clear fallback oracle by setting to None
            env.storage()
                .instance()
                .set(&storage::InstanceKey::FallbackOracle, &Option::<Address>::None);
            env.storage().instance().extend_ttl(storage::TTL_THRESHOLD, storage::TTL_EXTENSION);
        }
        
        env.events().publish(
            (symbol_short!("fallback"), symbol_short!("oracle"), symbol_short!("set")),
            fallback_contract_clone,
        );
        
        Ok(())
    }

    pub fn pause(env: Env, caller: Address) -> Result<(), OracleError> {
        admin::require_admin(&env, &caller).map_err(|_| OracleError::Unauthorized)?;
        caller.require_auth();
        env.storage().instance().set(&storage::InstanceKey::Paused, &true);
        env.storage().instance().extend_ttl(storage::TTL_THRESHOLD, storage::TTL_EXTENSION);
        Ok(())
    }

    pub fn unpause(env: Env, caller: Address) -> Result<(), OracleError> {
        admin::require_admin(&env, &caller).map_err(|_| OracleError::Unauthorized)?;
        caller.require_auth();
        env.storage().instance().set(&storage::InstanceKey::Paused, &false);
        env.storage().instance().extend_ttl(storage::TTL_THRESHOLD, storage::TTL_EXTENSION);
        Ok(())
    }

    pub fn is_paused(env: Env) -> bool {
        let result = env.storage()
            .instance()
            .get(&storage::InstanceKey::Paused)
            .unwrap_or(false);
        env.storage().instance().extend_ttl(storage::TTL_THRESHOLD, storage::TTL_EXTENSION);
        result
    }

    pub fn get_asset_price(env: Env, asset: Asset) -> Result<u128, OracleError> {
        let price_data = Self::get_asset_price_data(env, asset)?;
        Ok(price_data.price)
    }

    pub fn get_asset_price_data(env: Env, asset: Asset) -> Result<PriceData, OracleError> {
        if Self::is_paused(env.clone()) {
            return Err(OracleError::OracleQueryFailed);
        }
        let oracle_config = storage::get_oracle_config(&env)?;
        Self::get_asset_price_data_with_config(env, asset, &oracle_config)
    }

    /// N-05: Internal helper that accepts pre-fetched oracle_config to avoid redundant reads in batch loops.
    fn get_asset_price_data_with_config(env: Env, asset: Asset, oracle_config: &OracleConfig) -> Result<PriceData, OracleError> {
        let config = storage::get_asset_config(&env, &asset)
            .ok_or(OracleError::AssetNotWhitelisted)?;
        if !config.enabled {
            return Err(OracleError::AssetDisabled);
        }

        if let Some(override_price) = config.manual_override_price {
            if oracle_config.price_staleness_threshold == 0 {
                return Err(OracleError::PriceSourceNotSet);
            }

            let current_time = env.ledger().timestamp();
            let expiry_timestamp = config.override_expiry_timestamp
                .ok_or(OracleError::OverrideExpired)?;

            if current_time >= expiry_timestamp {
                let mut expired_config = config.clone();
                expired_config.manual_override_price = None;
                expired_config.override_expiry_timestamp = None;
                expired_config.override_set_timestamp = None;
                storage::set_asset_config(&env, &asset, &expired_config);
                storage::set_last_price(&env, &asset, override_price);
                env.events().publish(
                    (symbol_short!("ovr_exp"),),
                    (asset.clone(), override_price, expiry_timestamp),
                );
            } else {
                let time_until_expiry = expiry_timestamp.checked_sub(current_time)
                    .ok_or(OracleError::MathOverflow)?;
                if time_until_expiry <= 3600 {
                    env.events().publish(
                        (symbol_short!("ovr_near"),),
                        (asset.clone(), override_price, expiry_timestamp, time_until_expiry),
                    );
                }
                Self::validate_price_change(&env, &asset, &override_price, oracle_config)?;
                storage::set_last_price(&env, &asset, override_price);
                let override_ts = config.override_set_timestamp.unwrap_or(current_time);
                return Ok(PriceData {
                    price: override_price,
                    timestamp: override_ts,
                });
            }
        }

        // TTL-based cache: return cached price if fresh enough
        let cache_ttl = storage::get_price_cache_ttl(&env);
        if cache_ttl > 0 {
            if let Some(cached) = storage::get_last_price_data(&env, &asset) {
                let current_time = env.ledger().timestamp();
                let cache_age = current_time.saturating_sub(cached.cached_at);
                let price_age = current_time.saturating_sub(cached.timestamp);
                // Check both cache freshness AND underlying oracle staleness
                if cache_age <= cache_ttl && price_age <= oracle_config.price_staleness_threshold {
                    let price_data = PriceData { price: cached.price, timestamp: cached.timestamp };
                    Self::validate_price_change(&env, &asset, &price_data.price, oracle_config)?;
                    return Ok(price_data);
                }
            }
        }

        // Resolution: batch adapter → custom oracle → Reflector (with fallback)
        // All paths enforce staleness. Batch adapter and custom oracle use per-asset
        // max_age (falling back to global threshold). Reflector uses global threshold directly.
        let price_data = if let (Some(adapter), Some(feed_id)) =
            (config.batch_adapter.clone(), config.feed_id.clone())
        {
            let decimals = config.oracle_decimals.unwrap_or(8);
            oracle::query_batch_adapter_direct(
                &env, &adapter, &feed_id, decimals,
                config.max_age,
                oracle_config.price_precision,
                oracle_config.price_staleness_threshold,
            )?
        } else if let Some(custom_oracle_addr) = config.custom_oracle.clone() {
            match oracle::query_custom_oracle(&env, &custom_oracle_addr, &asset, config.max_age, config.oracle_decimals) {
                Ok(data) => data,
                Err(e) => {
                    env.events().publish(
                        (symbol_short!("custom"), symbol_short!("failed")),
                        (asset.clone(), custom_oracle_addr),
                    );
                    return Err(e);
                }
            }
        } else {
            let reflector_addr = storage::get_reflector_contract(&env)?;
            let data = match oracle::get_price_with_protection(&env, &reflector_addr, &asset, oracle_config) {
                Ok(data) => data,
                Err(_) => {
                    if let Some(fallback_addr) = storage::get_fallback_oracle(&env) {
                        let fallback_data = oracle::get_price_with_protection_fallback(
                            &env,
                            &fallback_addr,
                            &asset,
                            oracle_config,
                        )?;
                        env.events().publish(
                            (symbol_short!("fallback"), symbol_short!("used")),
                            (asset.clone(), fallback_addr),
                        );
                        fallback_data
                    } else {
                        return oracle::get_price_with_protection(&env, &reflector_addr, &asset, oracle_config);
                    }
                }
            };
            // Global staleness check only for Reflector path
            Self::validate_price_staleness(&env, &data, oracle_config)?;
            data
        };

        Self::validate_price_change(&env, &asset, &price_data.price, oracle_config)?;
        storage::set_last_price(&env, &asset, price_data.price);
        storage::set_last_price_data(&env, &asset, &price_data);
        Ok(price_data)
    }

    pub fn get_asset_prices_vec(env: Env, assets: Vec<Asset>) -> Result<Vec<PriceData>, OracleError> {
        // N-05: Hoist is_paused + oracle_config outside the loop
        if Self::is_paused(env.clone()) {
            return Err(OracleError::OracleQueryFailed);
        }
        let oracle_config = storage::get_oracle_config(&env)?;
        let cache_ttl = storage::get_price_cache_ttl(&env);
        let current_time = env.ledger().timestamp();

        // Phase 1: Classify assets and resolve cached/manual overrides
        let mut results: Vec<Option<PriceData>> = Vec::new(&env);
        // Collect batch-adapter assets grouped by adapter for batch fetch
        let mut batch_adapter_addr: Option<Address> = None;
        let mut batch_feed_ids: Vec<String> = Vec::new(&env);
        let mut batch_decimals: Vec<u32> = Vec::new(&env);
        let mut batch_max_ages: Vec<Option<u64>> = Vec::new(&env);
        let mut batch_indices: Vec<u32> = Vec::new(&env);

        for (idx, asset) in assets.iter().enumerate() {
            // Try cache first — check both cache freshness and underlying oracle staleness
            if cache_ttl > 0 {
                if let Some(cached) = storage::get_last_price_data(&env, &asset) {
                    let cache_age = current_time.saturating_sub(cached.cached_at);
                    let price_age = current_time.saturating_sub(cached.timestamp);
                    if cache_age <= cache_ttl && price_age <= oracle_config.price_staleness_threshold {
                        let price_data = PriceData { price: cached.price, timestamp: cached.timestamp };
                        Self::validate_price_change(&env, &asset, &price_data.price, &oracle_config)?;
                        results.push_back(Some(price_data));
                        continue;
                    }
                }
            }

            let config = storage::get_asset_config(&env, &asset)
                .ok_or(OracleError::AssetNotWhitelisted)?;
            if !config.enabled {
                return Err(OracleError::AssetDisabled);
            }

            // Check manual override
            if let Some(override_price) = config.manual_override_price {
                if let Some(expiry) = config.override_expiry_timestamp {
                    if current_time < expiry {
                        Self::validate_price_change(&env, &asset, &override_price, &oracle_config)?;
                        storage::set_last_price(&env, &asset, override_price);
                        let override_ts = config.override_set_timestamp.unwrap_or(current_time);
                        results.push_back(Some(PriceData { price: override_price, timestamp: override_ts }));
                        continue;
                    }
                }
            }

            // Classify: batch adapter vs other
            if let (Some(adapter), Some(feed_id)) = (config.batch_adapter.clone(), config.feed_id.clone()) {
                if batch_adapter_addr.is_none() {
                    batch_adapter_addr = Some(adapter.clone());
                }
                // Batch if same adapter
                if batch_adapter_addr.as_ref() == Some(&adapter) {
                    batch_feed_ids.push_back(feed_id);
                    batch_decimals.push_back(config.oracle_decimals.unwrap_or(8));
                    batch_max_ages.push_back(config.max_age);
                    batch_indices.push_back(idx as u32);
                    results.push_back(None); // placeholder
                    continue;
                }
                // Different adapter — resolve individually
            }

            // Fall through: resolve individually via standard path
            let price_data = Self::get_asset_price_data_with_config(env.clone(), asset.clone(), &oracle_config)?;
            results.push_back(Some(price_data));
        }

        // Phase 2: Batch-fetch adapter prices
        if batch_feed_ids.len() > 0 {
            if let Some(adapter_addr) = &batch_adapter_addr {
                let batch_results = if batch_feed_ids.len() == 1 {
                    // Single feed — use direct call (no batch overhead)
                    let feed_id = batch_feed_ids.get(0).ok_or(OracleError::OracleQueryFailed)?;
                    let decimals = batch_decimals.get(0).unwrap_or(8);
                    let max_age = batch_max_ages.get(0).unwrap_or(None);
                    let pd = oracle::query_batch_adapter_direct(
                        &env, adapter_addr, &feed_id, decimals, max_age,
                        oracle_config.price_precision, oracle_config.price_staleness_threshold,
                    )?;
                    let mut v = Vec::new(&env);
                    v.push_back(pd);
                    v
                } else {
                    oracle::batch_query_adapter(
                        &env, adapter_addr, &batch_feed_ids,
                        &batch_decimals, oracle_config.price_precision,
                        oracle_config.price_staleness_threshold, &batch_max_ages,
                    )?
                };

                // Phase 3: Distribute batch results
                for i in 0..batch_indices.len() {
                    let result_idx = batch_indices.get(i).ok_or(OracleError::OracleQueryFailed)?;
                    let price_data = batch_results.get(i).ok_or(OracleError::OracleQueryFailed)?;
                    let asset = assets.get(result_idx).ok_or(OracleError::AssetNotWhitelisted)?;

                    Self::validate_price_change(&env, &asset, &price_data.price, &oracle_config)?;
                    storage::set_last_price(&env, &asset, price_data.price);
                    storage::set_last_price_data(&env, &asset, &price_data);

                    results.set(result_idx, Some(price_data));
                }
            }
        }

        // Phase 4: Assemble final output
        let mut out = Vec::new(&env);
        for i in 0..results.len() {
            let price_data = results.get(i)
                .ok_or(OracleError::OracleQueryFailed)?
                .ok_or(OracleError::OracleQueryFailed)?;
            out.push_back(price_data);
        }
        Ok(out)
    }

    pub fn get_oracle_config(env: Env) -> Result<OracleConfig, OracleError> {
        storage::get_oracle_config(&env)
    }

    pub fn set_oracle_config(env: Env, caller: Address, config: OracleConfig) -> Result<(), OracleError> {
        admin::require_admin(&env, &caller).map_err(|_| OracleError::Unauthorized)?;
        caller.require_auth();

        // M-05
        if config.price_precision > 18 {
            return Err(OracleError::InvalidConfig);
        }

        storage::set_oracle_config(&env, &config);

        // L-05
        let asset_list = storage::get_asset_list(&env);
        for i in 0..asset_list.len() {
            if let Some(asset) = asset_list.get(i) {
                storage::clear_last_price(&env, &asset);
            }
        }

        env.events().publish(
            (symbol_short!("oracle"), symbol_short!("config"), symbol_short!("set")),
            config.price_staleness_threshold,
        );

        Ok(())
    }

    pub fn get_whitelisted_assets(env: Env) -> Vec<Asset> {
        storage::get_asset_list(&env)
    }

    pub fn get_asset_config(env: Env, asset: Asset) -> Option<AssetConfig> {
        storage::get_asset_config(&env, &asset)
    }

    pub fn admin(env: Env) -> Result<Address, OracleError> {
        admin::get_admin(&env).map_err(|_| OracleError::Unauthorized)
    }

    pub fn get_reflector_contract(env: Env) -> Option<Address> {
        storage::get_reflector_contract(&env).ok()
    }

    /// Reset circuit breaker for a specific asset (admin only).
    /// 
    /// Clears the stored last known price, allowing the next price query to bypass
    /// the circuit breaker check. Use this when legitimate large price movements
    /// occur (e.g., major market events, token migrations, or oracle upgrades).
    pub fn reset_circuit_breaker(env: Env, caller: Address, asset: Asset) -> Result<(), OracleError> {
        admin::require_admin(&env, &caller).map_err(|_| OracleError::Unauthorized)?;
        caller.require_auth();
        storage::clear_last_price(&env, &asset);
        Ok(())
    }

    /// Reset circuit breaker for all assets (admin only).
    /// 
    /// Emergency function to clear all stored last known prices. Use sparingly
    /// and only when necessary, as it temporarily disables circuit breaker protection
    /// for all assets until new prices are queried.
    pub fn reset_all_circuit_breakers(env: Env, caller: Address) -> Result<(), OracleError> {
        admin::require_admin(&env, &caller).map_err(|_| OracleError::Unauthorized)?;
        caller.require_auth();
        let asset_list = storage::get_asset_list(&env);
        for i in 0..asset_list.len() {
            let asset = asset_list.get(i).ok_or(OracleError::AssetPriceNotFound)?;
            storage::clear_last_price(&env, &asset);
        }
        Ok(())
    }

    /// Get last known price for an asset (for debugging and monitoring).
    /// 
    /// Returns the stored price used for circuit breaker validation, or None
    /// if no price has been recorded yet for this asset.
    pub fn get_last_price(env: Env, asset: Asset) -> Option<u128> {
        storage::get_last_price(&env, &asset)
    }

    /// Configure a batch-capable oracle adapter for direct queries.
    /// The adapter must implement: read_price_data_for_feed(String) and read_price_data(Vec<String>)
    /// returning {price: U256, package_timestamp: u64, write_timestamp: u64}.
    pub fn set_batch_oracle(
        env: Env,
        caller: Address,
        asset: Asset,
        adapter: Option<Address>,
        feed_id: Option<String>,
        decimals: Option<u32>,
        max_age_seconds: Option<u64>,
    ) -> Result<(), OracleError> {
        admin::require_admin(&env, &caller).map_err(|_| OracleError::Unauthorized)?;
        caller.require_auth();

        if let Some(d) = decimals {
            if d > 18 {
                return Err(OracleError::InvalidConfig);
            }
        }

        let mut config = storage::get_asset_config(&env, &asset)
            .ok_or(OracleError::AssetNotWhitelisted)?;
        config.batch_adapter = adapter.clone();
        config.feed_id = feed_id.clone();
        config.oracle_decimals = decimals;
        config.max_age = max_age_seconds;
        storage::set_asset_config(&env, &asset, &config);

        env.events().publish(
            (symbol_short!("batch_orc"), symbol_short!("set")),
            (asset, adapter, feed_id),
        );

        Ok(())
    }

    /// Set the TTL (in seconds) for the price cache. 0 = disabled.
    pub fn set_price_cache_ttl(
        env: Env,
        caller: Address,
        ttl: u64,
    ) -> Result<(), OracleError> {
        admin::require_admin(&env, &caller).map_err(|_| OracleError::Unauthorized)?;
        caller.require_auth();
        // Cap at 3600s (1 hour) to prevent stale prices being served indefinitely
        if ttl > 3600 {
            return Err(OracleError::InvalidConfig);
        }
        storage::set_price_cache_ttl(&env, ttl);
        Ok(())
    }

    /// Force-refresh cached prices for specific assets.
    /// Clears cached price data and fetches fresh prices from external sources.
    /// Use this before budget-sensitive operations (liquidation, swap_collateral)
    /// to ensure the cache is warm and subsequent calls hit the cache.
    pub fn refresh_prices(env: Env, assets: Vec<Asset>) -> Result<Vec<PriceData>, OracleError> {
        if Self::is_paused(env.clone()) {
            return Err(OracleError::OracleQueryFailed);
        }

        // Clear cache for requested assets so fetch is forced
        for asset in assets.iter() {
            storage::clear_last_price_data(&env, &asset);
        }

        // Fetch fresh prices (will bypass cache since we just cleared it)
        Self::get_asset_prices_vec(env, assets)
    }

    pub fn upgrade(env: Env, new_wasm_hash: BytesN<32>) -> Result<(), OracleError> {
        crate::upgrade::upgrade(env, new_wasm_hash).map_err(|_| OracleError::Unauthorized)
    }

    pub fn version(_env: Env) -> u32 {
        crate::upgrade::version()
    }

    /// Get current admin address
    pub fn get_admin(env: Env) -> Result<Address, OracleError> {
        crate::upgrade::get_admin(&env).map_err(|_| OracleError::Unauthorized)
    }

    /// Propose a new admin address (two-step transfer, step 1).
    /// Only the current admin can propose a new admin.
    /// The proposed admin must call `accept_admin` to complete the transfer.
    ///
    /// # Arguments
    /// * `caller` - Current admin address (must be authorized)
    /// * `pending_admin` - Proposed new admin address
    ///
    /// # Errors
    /// * `Unauthorized` - Caller is not current admin
    pub fn propose_admin(
        env: Env,
        caller: Address,
        pending_admin: Address,
    ) -> Result<(), OracleError> {
        use k2_shared::upgradeable::admin;
        admin::propose_admin(&env, &caller, &pending_admin)
            .map_err(|e| match e {
                k2_shared::upgradeable::UpgradeError::Unauthorized => OracleError::Unauthorized,
                k2_shared::upgradeable::UpgradeError::NoPendingAdmin => OracleError::InvalidCalculation,
                k2_shared::upgradeable::UpgradeError::InvalidPendingAdmin => OracleError::InvalidCalculation,
                _ => OracleError::Unauthorized,
            })
    }

    /// Accept admin role (two-step transfer, step 2).
    /// Only the pending admin can call this to finalize the transfer.
    ///
    /// # Arguments
    /// * `caller` - Pending admin address (must be authorized)
    ///
    /// # Errors
    /// * `InvalidCalculation` - No pending admin proposal or caller is not the pending admin
    pub fn accept_admin(env: Env, caller: Address) -> Result<(), OracleError> {
        use k2_shared::upgradeable::admin;
        admin::accept_admin(&env, &caller)
            .map_err(|e| match e {
                k2_shared::upgradeable::UpgradeError::NoPendingAdmin => OracleError::InvalidCalculation,
                k2_shared::upgradeable::UpgradeError::InvalidPendingAdmin => OracleError::InvalidCalculation,
                _ => OracleError::Unauthorized,
            })
    }

    /// Cancel a pending admin proposal.
    /// Only the current admin can cancel a pending proposal.
    ///
    /// # Arguments
    /// * `caller` - Current admin address (must be authorized)
    ///
    /// # Errors
    /// * `Unauthorized` - Caller is not current admin
    /// * `InvalidCalculation` - No pending admin proposal exists
    pub fn cancel_admin_proposal(env: Env, caller: Address) -> Result<(), OracleError> {
        use k2_shared::upgradeable::admin;
        admin::cancel_admin_proposal(&env, &caller)
            .map_err(|e| match e {
                k2_shared::upgradeable::UpgradeError::Unauthorized => OracleError::Unauthorized,
                k2_shared::upgradeable::UpgradeError::NoPendingAdmin => OracleError::InvalidCalculation,
                _ => OracleError::Unauthorized,
            })
    }

    /// Get the pending admin address, if any.
    ///
    /// # Returns
    /// * `Ok(Address)` - Pending admin address
    /// * `Err(InvalidCalculation)` - No pending admin proposal exists
    pub fn get_pending_admin(env: Env) -> Result<Address, OracleError> {
        use k2_shared::upgradeable::admin;
        admin::get_pending_admin(&env)
            .map_err(|_| OracleError::InvalidCalculation)
    }

    /// Validates that price data is recent enough to be trustworthy.
    /// 
    /// Rejects prices older than `price_staleness_threshold` to ensure calculations
    /// use current market data. Also rejects future timestamps as a defensive check
    /// against corrupted oracle data.
    fn validate_price_staleness(
        env: &Env,
        price_data: &PriceData,
        oracle_config: &k2_shared::OracleConfig,
    ) -> Result<(), OracleError> {
        let current_timestamp = env.ledger().timestamp();
        
        // Defensive check: future timestamps indicate corrupted oracle data
        if price_data.timestamp > current_timestamp {
            return Err(OracleError::PriceTooOld);
        }
        
        // Stale prices can cause incorrect calculations, so reject if too old
        let age = current_timestamp - price_data.timestamp;
        if age > oracle_config.price_staleness_threshold {
            return Err(OracleError::PriceTooOld);
        }
        
        Ok(())
    }

    /// Circuit breaker: validates price changes are within acceptable bounds.
    /// 
    /// Rejects prices that deviate more than `max_price_change_bps` from the last known
    /// price to protect against:
    /// - Oracle failures causing extreme price spikes/drops
    /// - Flash crashes triggering incorrect liquidations
    /// - Price manipulation attacks
    /// 
    /// Returns `PriceChangeTooLarge` if threshold exceeded. Admin can reset via
    /// `reset_circuit_breaker()` for legitimate large movements (market events, migrations).
    /// 
    /// Edge cases handled:
    /// - First query (no last price): always allowed
    /// - Zero last price: treated as uninitialized, allowed
    /// - Disabled (max_price_change_bps = 0): validation skipped
    fn validate_price_change(
        env: &Env,
        asset: &k2_shared::Asset,
        new_price: &u128,
        oracle_config: &k2_shared::OracleConfig,
    ) -> Result<(), OracleError> {
        // M-10
        if *new_price == 0 {
            return Err(OracleError::InvalidPrice);
        }

        // Disabled when threshold is 0 (useful for testing or emergency situations)
        if oracle_config.max_price_change_bps == 0 {
            return Ok(());
        }

        if let Some(last_price) = storage::get_last_price(env, asset) {
            // Defensive check: zero price indicates uninitialized state
            if last_price == 0 {
                return Ok(());
            }

            let deviation = oracle::calculate_price_deviation_bps(*new_price, last_price)?;

            if deviation > oracle_config.max_price_change_bps {
                return Err(OracleError::PriceChangeTooLarge);
            }
        }
        // First query: no baseline exists yet, so any price is acceptable
        
        Ok(())
    }
}
