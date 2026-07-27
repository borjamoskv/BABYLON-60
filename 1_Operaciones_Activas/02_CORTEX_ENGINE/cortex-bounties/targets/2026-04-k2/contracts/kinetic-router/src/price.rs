use crate::storage;
use k2_shared::{Asset, KineticRouterError, OracleConfig, PriceData, MAX_RESERVES};
use soroban_sdk::{Address, Env, IntoVal, Map, Symbol, Vec};

fn address_to_asset(_env: &Env, address: &Address) -> Asset {
    Asset::Stellar(address.clone())
}

/// Validate that a price timestamp is not stale.
/// M-07
/// Returns `PriceOracleError` on stale or future-dated prices.
/// N-04
pub(crate) fn validate_price_freshness(env: &Env, price_timestamp: u64, asset: Option<&Address>) -> Result<(), KineticRouterError> {
    let current_time = env.ledger().timestamp();

    // Reject prices from the future (clock skew / manipulation)
    if price_timestamp > current_time {
        return Err(KineticRouterError::PriceOracleError);
    }

    // M-07
    let staleness_threshold = asset
        .and_then(|a| storage::get_asset_staleness_threshold(env, a))
        .unwrap_or_else(|| storage::get_price_staleness_threshold(env));

    let age = current_time.checked_sub(price_timestamp)
        .ok_or(KineticRouterError::PriceOracleError)?;
    if age > staleness_threshold {
        return Err(KineticRouterError::PriceOracleError);
    }

    Ok(())
}


/// Batch fetches prices to reduce oracle calls
pub fn get_prices_for_assets(
    env: &Env,
    assets: &Vec<Address>,
) -> Result<Map<Address, u128>, KineticRouterError> {
    if assets.len() == 0 {
        return Ok(Map::new(env));
    }

    let price_oracle_address = storage::get_price_oracle_opt(env)
        .ok_or(KineticRouterError::PriceOracleNotFound)?;

    let mut assets_vec = Vec::new(env);
    for i in 0..assets.len().min(MAX_RESERVES) {
        let asset = assets.get(i).ok_or(KineticRouterError::ReserveNotFound)?;
        let asset_type = address_to_asset(env, &asset);
        assets_vec.push_back(asset_type);
    }

    let args = soroban_sdk::vec![env, assets_vec.into_val(env)];
    
    let price_result = env.try_invoke_contract::<Vec<PriceData>, KineticRouterError>(
        &price_oracle_address,
        &Symbol::new(env, "get_asset_prices_vec"),
        args,
    );

    let prices_vec = match price_result {
        Ok(Ok(pv)) => pv,
        Ok(Err(_)) => return Err(KineticRouterError::PriceOracleError),
        Err(_) => return Err(KineticRouterError::PriceOracleInvocationFailed),
    };

    if prices_vec.len() != assets.len() {
        return Err(KineticRouterError::PriceOracleError);
    }

    let mut price_map = Map::new(env);
    for i in 0..assets.len().min(MAX_RESERVES) {
        let asset = assets.get(i).ok_or(KineticRouterError::ReserveNotFound)?;
        let price_data = prices_vec.get(i).ok_or(KineticRouterError::PriceOracleError)?;
        
        // Validate price freshness for each price in batch (M-07: per-asset threshold)
        validate_price_freshness(env, price_data.timestamp, Some(&asset))?;
        
        price_map.set(asset, price_data.price);
    }

    Ok(price_map)
}

/// Verify that an oracle price exists and is non-zero for a single asset
pub fn verify_oracle_price_exists_and_nonzero(
    env: &Env,
    asset: &Address,
) -> Result<u128, KineticRouterError> {
    let price_oracle_address = storage::get_price_oracle_opt(env)
        .ok_or(KineticRouterError::PriceOracleNotFound)?;

    let asset_type = address_to_asset(env, asset);
    let mut assets_vec = Vec::new(env);
    assets_vec.push_back(asset_type);

    let args = soroban_sdk::vec![env, assets_vec.into_val(env)];
    
    let price_result = env.try_invoke_contract::<Vec<PriceData>, KineticRouterError>(
        &price_oracle_address,
        &Symbol::new(env, "get_asset_prices_vec"),
        args,
    );

    let prices_vec = match price_result {
        Ok(Ok(pv)) => pv,
        Ok(Err(_)) => return Err(KineticRouterError::PriceOracleError),
        Err(_) => return Err(KineticRouterError::PriceOracleInvocationFailed),
    };

    if prices_vec.len() != 1 {
        return Err(KineticRouterError::PriceOracleError);
    }

    let price_data = prices_vec
        .get(0)
        .ok_or(KineticRouterError::PriceOracleError)?;

    if price_data.price == 0 {
        return Err(KineticRouterError::PriceOracleNotFound);
    }

    // M-01
    validate_price_freshness(env, price_data.timestamp, Some(asset))?;

    Ok(price_data.price)
}

/// Get oracle configuration including current price precision.
/// F-02
pub fn get_oracle_config(env: &Env) -> Result<OracleConfig, KineticRouterError> {
    // F-02
    if let Some(cached) = storage::get_cached_oracle_config(env) {
        return Ok(cached);
    }

    let price_oracle_address = storage::get_price_oracle_opt(env)
        .ok_or(KineticRouterError::PriceOracleNotFound)?;

    let config_result = env.try_invoke_contract::<OracleConfig, KineticRouterError>(
        &price_oracle_address,
        &Symbol::new(env, "get_oracle_config"),
        soroban_sdk::vec![env],
    );

    match config_result {
        Ok(Ok(config)) => {
            // Cache for subsequent calls in this and future transactions
            storage::set_cached_oracle_config(env, &config);
            Ok(config)
        }
        Ok(Err(_)) => Err(KineticRouterError::PriceOracleError),
        Err(_) => Err(KineticRouterError::PriceOracleInvocationFailed),
    }
}
