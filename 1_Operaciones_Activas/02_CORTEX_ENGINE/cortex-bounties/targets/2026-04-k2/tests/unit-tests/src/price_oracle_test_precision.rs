#![cfg(test)]

use crate::price_oracle;
use price_oracle::Asset as OracleAsset;
use k2_shared::TEST_PRICE_BTC;
use soroban_sdk::{contract, contractimpl, contracttype, testutils::Address as _, Address, Env, Symbol};

#[contracttype]
#[derive(Clone, Debug)]
pub struct ReflectorPriceData {
    pub price: i128,
    pub timestamp: u64,
}

#[contract]
pub struct OracleStub8Decimals;

#[contractimpl]
impl OracleStub8Decimals {
    pub fn lastprice(env: Env, _asset: OracleAsset) -> Option<ReflectorPriceData> {
        Some(ReflectorPriceData {
            price: 4500000000000i128,
            timestamp: env.ledger().timestamp(),
        })
    }

    pub fn decimals(_env: Env) -> u32 {
        8
    }
}

#[contract]
pub struct OracleStub14Decimals;

#[contractimpl]
impl OracleStub14Decimals {
    pub fn lastprice(env: Env, _asset: OracleAsset) -> Option<ReflectorPriceData> {
        Some(ReflectorPriceData {
            price: TEST_PRICE_BTC as i128,
            timestamp: env.ledger().timestamp(),
        })
    }

    pub fn decimals(_env: Env) -> u32 {
        14
    }
}

#[contract]
pub struct OracleStub18Decimals;

#[contractimpl]
impl OracleStub18Decimals {
    pub fn lastprice(env: Env, _asset: OracleAsset) -> Option<ReflectorPriceData> {
        Some(ReflectorPriceData {
            price: 45000000000000000000000i128,
            timestamp: env.ledger().timestamp(),
        })
    }

    pub fn decimals(_env: Env) -> u32 {
        18
    }
}

fn create_test_env() -> Env {
    use soroban_sdk::testutils::Ledger;
    
    let env = Env::default();
    env.mock_all_auths();
    
    env.ledger().with_mut(|li| {
        li.timestamp = 1704067200;
    });
    
    env
}

#[test]
fn test_precision_normalization_8_to_8_decimals() {
    let env = create_test_env();
    let admin = Address::generate(&env);
    
    let oracle_8_decimals = env.register(OracleStub8Decimals, ());
    let base_currency = Address::generate(&env);
    let native_xlm = Address::generate(&env);
    
    let oracle_contract = env.register(price_oracle::WASM, ());
    let client = price_oracle::Client::new(&env, &oracle_contract);
    
    client.initialize(&admin, &oracle_8_decimals, &base_currency, &native_xlm);
    
    let config = client.get_oracle_config();
    assert_eq!(config.price_precision, 8u32, "Precision should be 8 after init with 8-decimal oracle");
    
    let asset = OracleAsset::Stellar(Address::generate(&env));
    client.add_asset(&admin, &asset);
    
    let price = client.get_asset_price(&asset);
    
    let expected_price = 4500000000000i128;
    assert_eq!(
        price, expected_price as u128,
        "8-decimal price should remain in 8 decimals. Expected: {}, Got: {}",
        expected_price, price
    );
}

#[test]
fn test_precision_normalization_18_to_18_decimals() {
    let env = create_test_env();
    let admin = Address::generate(&env);
    
    let oracle_18_decimals = env.register(OracleStub18Decimals, ());
    let base_currency = Address::generate(&env);
    let native_xlm = Address::generate(&env);
    
    let oracle_contract = env.register(price_oracle::WASM, ());
    let client = price_oracle::Client::new(&env, &oracle_contract);
    
    client.initialize(&admin, &oracle_18_decimals, &base_currency, &native_xlm);
    
    let config = client.get_oracle_config();
    assert_eq!(config.price_precision, 18u32, "Precision should be 18 after init with 18-decimal oracle");
    
    let asset = OracleAsset::Stellar(Address::generate(&env));
    client.add_asset(&admin, &asset);
    
    let price = client.get_asset_price(&asset);
    
    let expected_price = 45000000000000000000000i128;
    assert_eq!(
        price, expected_price as u128,
        "18-decimal price should remain in 18 decimals. Expected: {}, Got: {}",
        expected_price, price
    );
}

#[test]
fn test_precision_normalization_14_to_14_decimals() {
    let env = create_test_env();
    let admin = Address::generate(&env);
    
    let oracle_14_decimals = env.register(OracleStub14Decimals, ());
    let base_currency = Address::generate(&env);
    let native_xlm = Address::generate(&env);
    
    let oracle_contract = env.register(price_oracle::WASM, ());
    let client = price_oracle::Client::new(&env, &oracle_contract);
    
    client.initialize(&admin, &oracle_14_decimals, &base_currency, &native_xlm);
    
    let asset = OracleAsset::Stellar(Address::generate(&env));
    client.add_asset(&admin, &asset);
    
    let price = client.get_asset_price(&asset);
    
    assert_eq!(
        price, TEST_PRICE_BTC,
        "14-decimal price should remain unchanged. Expected: {}, Got: {}",
        TEST_PRICE_BTC, price
    );
}

#[test]
fn test_update_reflector_contract_updates_precision() {
    let env = create_test_env();
    let admin = Address::generate(&env);
    
    let oracle_14_decimals = env.register(OracleStub14Decimals, ());
    let base_currency = Address::generate(&env);
    let native_xlm = Address::generate(&env);
    
    let oracle_contract = env.register(price_oracle::WASM, ());
    let client = price_oracle::Client::new(&env, &oracle_contract);
    
    client.initialize(&admin, &oracle_14_decimals, &base_currency, &native_xlm);
    
    let config = client.get_oracle_config();
    assert_eq!(config.price_precision, 14u32, "Initial precision should be 14");
    
    let oracle_8_decimals = env.register(OracleStub8Decimals, ());
    client.update_reflector_contract(&admin, &oracle_8_decimals);
    
    let updated_config = client.get_oracle_config();
    assert_eq!(
        updated_config.price_precision, 8u32,
        "Precision should update to 8 after changing reflector contract"
    );
    
    let asset = OracleAsset::Stellar(Address::generate(&env));
    client.add_asset(&admin, &asset);
    
    let price = client.get_asset_price(&asset);
    let expected_price = 4500000000000i128;
    assert_eq!(
        price, expected_price as u128,
        "Price should be in 8 decimals after oracle update. Expected: {}, Got: {}",
        expected_price, price
    );
}
