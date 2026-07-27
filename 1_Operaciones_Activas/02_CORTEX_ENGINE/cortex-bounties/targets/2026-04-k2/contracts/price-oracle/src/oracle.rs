use k2_shared::{Asset, PriceData};
use soroban_sdk::{contracttype, Address, Env, IntoVal, String, Symbol, U256, Vec};

#[cfg(not(any(test, feature = "testutils")))]
mod reflector_oracle_wasm {
    soroban_sdk::contractimport!(file = "../../external/reflector_oracle.wasm");
}

#[cfg(not(any(test, feature = "testutils")))]
pub use reflector_oracle_wasm::{Asset as ReflectorAsset, Client};

#[cfg(any(test, feature = "testutils"))]
mod reflector_oracle_test {
    use k2_shared::{Asset, PriceData};
    use soroban_sdk::{Address, Env, Symbol, IntoVal};

    pub struct Wrapper<'a> {
        env: &'a Env,
        contract_id: Address,
    }

    impl<'a> Wrapper<'a> {
        pub fn new(env: &'a Env, contract_id: &Address) -> Self {
            Self {
                env,
                contract_id: contract_id.clone(),
            }
        }

        pub fn lastprice(&self, asset: &Asset) -> Option<PriceData> {
            let result: Option<PriceData> = self.env.invoke_contract(
                &self.contract_id,
                &Symbol::new(self.env, "lastprice"),
                (asset.clone(),).into_val(self.env),
            );
            result
        }

        pub fn decimals(&self) -> Option<u32> {
            let result: Option<u32> = self.env.invoke_contract(
                &self.contract_id,
                &Symbol::new(self.env, "decimals"),
                ().into_val(self.env),
            );
            result
        }
    }
}

#[cfg(any(test, feature = "testutils"))]
pub use reflector_oracle_test::Wrapper;

#[cfg(not(any(test, feature = "testutils")))]
pub struct Wrapper<'a> {
    env: &'a Env,
    client: Client<'a>,
}

#[cfg(not(any(test, feature = "testutils")))]
impl<'a> Wrapper<'a> {
    pub fn new(env: &'a Env, contract_id: &Address) -> Self {
        Self {
            env,
            client: Client::new(env, contract_id),
        }
    }

    pub fn lastprice(&self, asset: &Asset) -> Option<PriceData> {
        // Convert our Asset to the Reflector's Asset type and query.
        // Reflector implementations vary: mainnet uses Stellar(address) for all assets,
        // testnet uses Other("XLM") for native. We try the direct format first, then
        // fall back to Other(symbol) for native XLM if no result.
        let reflector_asset = match asset {
            Asset::Stellar(addr) => ReflectorAsset::Stellar(addr.clone()),
            Asset::Other(symbol) => ReflectorAsset::Other(symbol.clone()),
        };

        if let Some(price) = self.try_lastprice(&reflector_asset) {
            return Some(price);
        }

        // Fallback: if the asset is native XLM (Stellar address), try Other("XLM")
        // to support Reflector versions that use symbol-based asset keys.
        if let Asset::Stellar(_) = asset {
            if let Ok(native_addr) = crate::storage::get_native_xlm_address(self.env) {
                if let Asset::Stellar(addr) = asset {
                    if *addr == native_addr {
                        let xlm_symbol = ReflectorAsset::Other(
                            soroban_sdk::Symbol::new(self.env, "XLM"),
                        );
                        return self.try_lastprice(&xlm_symbol);
                    }
                }
            }
        }

        None
    }

    fn try_lastprice(&self, reflector_asset: &ReflectorAsset) -> Option<PriceData> {
        if let Some(reflector_data) = self.client.lastprice(reflector_asset) {
            if reflector_data.price >= 0 {
                // S-04
                let price_u128 = k2_shared::safe_i128_to_u128(self.env, reflector_data.price);
                Some(PriceData {
                    price: price_u128,
                    timestamp: reflector_data.timestamp,
                })
            } else {
                None
            }
        } else {
            None
        }
    }

    pub fn decimals(&self) -> Option<u32> {
        Some(self.client.decimals())
    }
}

pub fn query_reflector(
    env: &Env,
    reflector_addr: &Address,
    asset: &Asset,
) -> Result<PriceData, crate::OracleError> {
    let reflector_wrapper = Wrapper::new(env, reflector_addr);
    let reflector_price_data = reflector_wrapper
        .lastprice(asset)
        .ok_or(crate::OracleError::OracleQueryFailed)?;
    let config = crate::storage::get_oracle_config(env)?;
    let current_timestamp = env.ledger().timestamp();
    
    // Defensive check: future timestamps indicate corrupted oracle data
    // This prevents underflow panic when subtracting timestamps
    if reflector_price_data.timestamp > current_timestamp {
        return Err(crate::OracleError::PriceTooOld);
    }
    
    if current_timestamp.checked_sub(reflector_price_data.timestamp)
        .ok_or(crate::OracleError::MathOverflow)? > config.price_staleness_threshold
    {
        return Err(crate::OracleError::PriceTooOld);
    }

    // Use cached Reflector precision from instance storage instead of cross-contract
    // decimals() call. Saves 1 CC call per Reflector asset resolution.
    let oracle_decimals = match crate::storage::get_reflector_precision(env) {
        Some(p) => p,
        None => reflector_wrapper.decimals()
            .ok_or(crate::OracleError::OracleQueryFailed)?,
    };
    let normalized_price = normalize_price(
        reflector_price_data.price,
        oracle_decimals,
        config.price_precision,
    )?;
    
    Ok(PriceData {
        price: normalized_price,
        timestamp: reflector_price_data.timestamp,
    })
}

/// Query fallback oracle for spot price
pub fn query_fallback_oracle(
    env: &Env,
    fallback_addr: &Address,
    asset: &Asset,
) -> Result<PriceData, crate::OracleError> {
    let fallback_wrapper = Wrapper::new(env, fallback_addr);
    let fallback_price_data = fallback_wrapper
        .lastprice(asset)
        .ok_or(crate::OracleError::OracleQueryFailed)?;
    let config = crate::storage::get_oracle_config(env)?;
    let current_timestamp = env.ledger().timestamp();
    
    // Defensive check: future timestamps indicate corrupted oracle data
    // This prevents underflow panic when subtracting timestamps
    if fallback_price_data.timestamp > current_timestamp {
        return Err(crate::OracleError::PriceTooOld);
    }
    
    if current_timestamp.checked_sub(fallback_price_data.timestamp)
        .ok_or(crate::OracleError::MathOverflow)? > config.price_staleness_threshold
    {
        return Err(crate::OracleError::PriceTooOld);
    }

    // Fallback oracle may have different precision than Reflector — always query its own decimals
    let oracle_decimals = fallback_wrapper.decimals()
        .ok_or(crate::OracleError::OracleQueryFailed)?;
    let normalized_price = normalize_price(
        fallback_price_data.price,
        oracle_decimals,
        config.price_precision,
    )?;
    
    Ok(PriceData {
        price: normalized_price,
        timestamp: fallback_price_data.timestamp,
    })
}

fn normalize_price(
    price: u128,
    source_decimals: u32,
    target_decimals: u32,
) -> Result<u128, crate::OracleError> {
    if source_decimals == target_decimals {
        return Ok(price);
    }
    
    if source_decimals > target_decimals {
        let scale_down = 10_u128.checked_pow(
            source_decimals.checked_sub(target_decimals)
                .ok_or(crate::OracleError::MathOverflow)?
        ).ok_or(crate::OracleError::MathOverflow)?;
        price.checked_div(scale_down).ok_or(crate::OracleError::InvalidCalculation)
    } else {
        let scale_up = 10_u128.checked_pow(
            target_decimals.checked_sub(source_decimals)
                .ok_or(crate::OracleError::MathOverflow)?
        ).ok_or(crate::OracleError::MathOverflow)?;
        price.checked_mul(scale_up)
            .ok_or(crate::OracleError::InvalidCalculation)
    }
}

/// Calculate price deviation between two prices in basis points
/// Returns deviation as basis points (e.g., 500 = 5%)
/// Returns Err on invalid inputs (zero prices) or arithmetic overflow
pub fn calculate_price_deviation_bps(price1: u128, price2: u128) -> Result<u32, crate::OracleError> {
    if price1 == 0 || price2 == 0 {
        return Err(crate::OracleError::InvalidPrice);
    }

    let diff = price1.abs_diff(price2);

    let scaled_diff = diff
        .checked_mul(10_000)
        .ok_or(crate::OracleError::MathOverflow)?;

    // price2 != 0 is guaranteed by the guard above
    let deviation = scaled_diff / price2;

    u32::try_from(deviation).map_err(|_| crate::OracleError::MathOverflow)
}

/// Get price with circuit breaker protection.
/// Queries Reflector oracle. Fallback logic is handled in the contract layer.
pub fn get_price_with_protection(
    env: &Env,
    reflector_addr: &Address,
    asset: &Asset,
    _config: &k2_shared::OracleConfig,
) -> Result<PriceData, crate::OracleError> {
    query_reflector(env, reflector_addr, asset)
}

/// Get price with circuit breaker protection from fallback oracle.
pub fn get_price_with_protection_fallback(
    env: &Env,
    fallback_addr: &Address,
    asset: &Asset,
    _config: &k2_shared::OracleConfig,
) -> Result<PriceData, crate::OracleError> {
    query_fallback_oracle(env, fallback_addr, asset)
}

/// Query Reflector contract for its decimals/precision value.
pub fn query_reflector_decimals(
    env: &Env,
    reflector_addr: &Address,
) -> Result<u32, crate::OracleError> {
    let reflector_wrapper = Wrapper::new(env, reflector_addr);
    reflector_wrapper
        .decimals()
        .ok_or(crate::OracleError::OracleQueryFailed)
}

/// Query a custom oracle that implements the standard price oracle interface:
///   - decimals() -> u32
///   - lastprice(asset: Asset) -> Option<PriceData>
///
/// This works with any oracle implementing this interface.
pub fn query_custom_oracle(
    env: &Env,
    oracle_addr: &Address,
    asset: &Asset,
    max_age: Option<u64>,
    cached_decimals: Option<u32>,
) -> Result<PriceData, crate::OracleError> {
    let price_result = env.try_invoke_contract::<Option<PriceData>, soroban_sdk::Error>(
        oracle_addr,
        &Symbol::new(env, "lastprice"),
        (asset.clone(),).into_val(env),
    );
    let price_data = match price_result {
        Ok(Ok(Some(data))) => data,
        _ => return Err(crate::OracleError::OracleQueryFailed),
    };

    let config = crate::storage::get_oracle_config(env)?;
    let current_timestamp = env.ledger().timestamp();

    // Validate timestamp staleness
    // Use custom max_age if provided, otherwise use global staleness threshold
    let max_age_seconds = max_age.unwrap_or(config.price_staleness_threshold);

    // Check if timestamp is in the future (invalid)
    if price_data.timestamp > current_timestamp {
        return Err(crate::OracleError::PriceTooOld);
    }

    // Check if price is too stale
    let age = current_timestamp.saturating_sub(price_data.timestamp);
    if age > max_age_seconds {
        return Err(crate::OracleError::PriceTooOld);
    }

    // Use cached decimals if available, otherwise call decimals() cross-contract
    let oracle_decimals = if let Some(d) = cached_decimals {
        d
    } else {
        let decimals_result = env.try_invoke_contract::<u32, soroban_sdk::Error>(
            oracle_addr,
            &Symbol::new(env, "decimals"),
            ().into_val(env),
        );
        match decimals_result {
            Ok(Ok(d)) => d,
            _ => return Err(crate::OracleError::OracleQueryFailed),
        }
    };

    // Validate decimals range (matches M-05 validation on config.price_precision)
    if oracle_decimals > 18 {
        return Err(crate::OracleError::InvalidPrice);
    }

    // S-04 NOTE: price_data.price is already u128 (from k2_shared::PriceData)
    // Original 'as u128' cast was unnecessary
    let normalized_price = normalize_price(
        price_data.price,
        oracle_decimals,
        config.price_precision,
    )?;

    // M-10
    if normalized_price == 0 {
        return Err(crate::OracleError::InvalidPrice);
    }

    Ok(PriceData {
        price: normalized_price,
        timestamp: price_data.timestamp,
    })
}

// --- Batch-capable adapter integration ---
// Standard interface: any adapter implementing read_price_data_for_feed(String) and
// read_price_data(Vec<String>) returning AdapterPriceData slots in with zero code changes.

/// Price data returned from batch-capable adapters (RedStone, Pyth, Switchboard, etc.)
#[contracttype]
#[derive(Clone)]
pub struct AdapterPriceData {
    pub price: U256,
    pub package_timestamp: u64,
    pub write_timestamp: u64,
}

/// Query a batch-capable adapter directly for a single feed.
/// Bypasses wrapper contracts, saving ~2 cross-contract calls.
pub fn query_batch_adapter_direct(
    env: &Env,
    adapter_addr: &Address,
    feed_id: &String,
    decimals: u32,
    max_age: Option<u64>,
    price_precision: u32,
    staleness_threshold: u64,
) -> Result<PriceData, crate::OracleError> {
    let result = env.try_invoke_contract::<AdapterPriceData, soroban_sdk::Error>(
        adapter_addr,
        &Symbol::new(env, "read_price_data_for_feed"),
        (feed_id.clone(),).into_val(env),
    );
    let adapter_data = match result {
        Ok(Ok(data)) => data,
        _ => return Err(crate::OracleError::OracleQueryFailed),
    };

    let price_u128 = adapter_data.price.to_u128()
        .ok_or(crate::OracleError::MathOverflow)?;

    // Convert milliseconds to seconds
    let timestamp_secs = adapter_data.package_timestamp / 1000;

    let current_timestamp = env.ledger().timestamp();
    if timestamp_secs > current_timestamp {
        return Err(crate::OracleError::PriceTooOld);
    }
    let max_age_seconds = max_age.unwrap_or(staleness_threshold);
    let age = current_timestamp.saturating_sub(timestamp_secs);
    if age > max_age_seconds {
        return Err(crate::OracleError::PriceTooOld);
    }

    let normalized_price = normalize_price(price_u128, decimals, price_precision)?;
    if normalized_price == 0 {
        return Err(crate::OracleError::InvalidPrice);
    }

    Ok(PriceData {
        price: normalized_price,
        timestamp: timestamp_secs,
    })
}

/// Batch-query an adapter for multiple feeds in one cross-contract call.
/// Returns PriceData vec in the same order as feed_ids.
pub fn batch_query_adapter(
    env: &Env,
    adapter_addr: &Address,
    feed_ids: &Vec<String>,
    decimals_list: &Vec<u32>,
    price_precision: u32,
    staleness_threshold: u64,
    max_ages: &Vec<Option<u64>>,
) -> Result<Vec<PriceData>, crate::OracleError> {
    let result = env.try_invoke_contract::<Vec<AdapterPriceData>, soroban_sdk::Error>(
        adapter_addr,
        &Symbol::new(env, "read_price_data"),
        (feed_ids.clone(),).into_val(env),
    );
    let batch = match result {
        Ok(Ok(data)) => data,
        _ => return Err(crate::OracleError::OracleQueryFailed),
    };

    if batch.len() != feed_ids.len() {
        return Err(crate::OracleError::OracleQueryFailed);
    }

    let current_timestamp = env.ledger().timestamp();
    let mut out = Vec::new(env);

    for i in 0..batch.len() {
        let data = batch.get(i).ok_or(crate::OracleError::OracleQueryFailed)?;
        let decimals = decimals_list.get(i).unwrap_or(8);
        let max_age = max_ages.get(i).unwrap_or(None);

        let price_u128 = data.price.to_u128()
            .ok_or(crate::OracleError::MathOverflow)?;

        let timestamp_secs = data.package_timestamp / 1000;

        if timestamp_secs > current_timestamp {
            return Err(crate::OracleError::PriceTooOld);
        }
        let max_age_seconds = max_age.unwrap_or(staleness_threshold);
        let age = current_timestamp.saturating_sub(timestamp_secs);
        if age > max_age_seconds {
            return Err(crate::OracleError::PriceTooOld);
        }

        let normalized_price = normalize_price(price_u128, decimals, price_precision)?;
        if normalized_price == 0 {
            return Err(crate::OracleError::InvalidPrice);
        }

        out.push_back(PriceData {
            price: normalized_price,
            timestamp: timestamp_secs,
        });
    }

    Ok(out)
}
