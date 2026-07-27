#![cfg(test)]

use k2_shared::{
    Asset, TEST_PRICE_BTC, TEST_PRICE_DEFAULT, TEST_PRICE_ETH, TEST_PRICE_USD,
};
use soroban_sdk::{contract, contractimpl, contracttype, Env, Symbol};

/// PriceData matching the Reflector Oracle's interface (uses i128 for price)
/// This is different from k2_shared::PriceData which uses u128
#[contracttype]
#[derive(Clone, Debug)]
pub struct ReflectorPriceData {
    pub price: i128,    // Reflector uses signed i128
    pub timestamp: u64,
}

#[contract]
pub struct ReflectorStub;

#[contractimpl]
impl ReflectorStub {
    pub fn lastprice(env: Env, asset: Asset) -> Option<ReflectorPriceData> {
        let price = match asset {
            Asset::Stellar(_) => TEST_PRICE_DEFAULT,
            Asset::Other(symbol) => {
                if symbol == Symbol::new(&env, "BTC") {
                    TEST_PRICE_BTC
                } else if symbol == Symbol::new(&env, "ETH") {
                    TEST_PRICE_ETH
                } else if symbol == Symbol::new(&env, "USD") {
                    TEST_PRICE_USD
                } else {
                    TEST_PRICE_DEFAULT
                }
            }
        };

        let timestamp = env.ledger().timestamp();
        
        Some(ReflectorPriceData {
            price: price as i128,  // Convert u128 to i128 for Reflector compatibility
            timestamp,
        })
    }

    pub fn twap(env: Env, asset: Asset, _periods: u32) -> Option<i128> {
        let price = match asset {
            Asset::Stellar(_) => TEST_PRICE_DEFAULT as i128,
            Asset::Other(symbol) => {
                if symbol == Symbol::new(&env, "BTC") {
                    TEST_PRICE_BTC as i128
                } else if symbol == Symbol::new(&env, "ETH") {
                    TEST_PRICE_ETH as i128
                } else if symbol == Symbol::new(&env, "USD") {
                    TEST_PRICE_USD as i128
                } else {
                    TEST_PRICE_DEFAULT as i128
                }
            }
        };

        Some(price)
    }

    pub fn decimals(_env: Env) -> u32 {
        14
    }

    pub fn base(env: Env) -> Asset {
        Asset::Other(Symbol::new(&env, "USD"))
    }
}

/// Mock Custom Oracle that implements the k2_shared interface expected by query_custom_oracle:
///   - decimals() -> u32
///   - lastprice(asset: Asset) -> Option<k2_shared::PriceData>
///
/// Custom oracles use k2_shared::PriceData (u128 price), NOT ReflectorPriceData (i128 price).
/// The Reflector interface is only used by the Reflector Wrapper, not by custom oracle queries.
#[contract]
pub struct CustomOracleStub;

#[contractimpl]
impl CustomOracleStub {
    /// Returns price decimals (e.g., 8 for RedStone)
    pub fn decimals(_env: Env) -> u32 {
        8
    }

    /// Returns price data using k2_shared::PriceData (u128 price)
    /// Returns a test price of 100_000_000 (1.00 with 8 decimals)
    pub fn lastprice(env: Env, _asset: Asset) -> Option<k2_shared::PriceData> {
        Some(k2_shared::PriceData {
            price: 100_000_000u128,
            timestamp: env.ledger().timestamp(),
        })
    }
}

/// Mock Custom Oracle that returns a specific configurable price
#[contract]
pub struct ConfigurableCustomOracleStub;

// Storage key for the configurable oracle
const PRICE_KEY: &str = "price";
const DECIMALS_KEY: &str = "decimals";
const TIMESTAMP_OFFSET_KEY: &str = "ts_offset";

#[contractimpl]
impl ConfigurableCustomOracleStub {
    /// Initialize with a specific price and decimals
    pub fn init(env: Env, price: u128, decimals: u32) {
        env.storage().instance().set(&Symbol::new(&env, PRICE_KEY), &price);
        env.storage().instance().set(&Symbol::new(&env, DECIMALS_KEY), &decimals);
        env.storage().instance().set(&Symbol::new(&env, TIMESTAMP_OFFSET_KEY), &0i64);
    }

    /// Set timestamp offset (negative = stale price)
    pub fn set_timestamp_offset(env: Env, offset_seconds: i64) {
        env.storage().instance().set(&Symbol::new(&env, TIMESTAMP_OFFSET_KEY), &offset_seconds);
    }

    pub fn decimals(env: Env) -> u32 {
        env.storage().instance().get(&Symbol::new(&env, DECIMALS_KEY)).unwrap_or(8u32)
    }

    /// Returns price data using k2_shared::PriceData (u128 price)
    pub fn lastprice(env: Env, _asset: Asset) -> Option<k2_shared::PriceData> {
        let price: u128 = env.storage().instance().get(&Symbol::new(&env, PRICE_KEY)).unwrap_or(100_000_000);
        let offset: i64 = env.storage().instance().get(&Symbol::new(&env, TIMESTAMP_OFFSET_KEY)).unwrap_or(0);

        let base_ts = env.ledger().timestamp() as i64;
        let adjusted_ts = (base_ts + offset) as u64;

        Some(k2_shared::PriceData {
            price,
            timestamp: adjusted_ts,
        })
    }
}
