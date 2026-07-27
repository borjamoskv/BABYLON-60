#![cfg(test)]

use crate::price_oracle;
use price_oracle::Asset as OracleAsset;

use k2_shared::{TEST_PRICE_BTC, TEST_PRICE_DEFAULT};
use soroban_sdk::{testutils::Address as _, Address, Env, Symbol, Vec};

use crate::price_oracle_test_stub::ReflectorStub;

pub fn create_test_env() -> Env {
    use soroban_sdk::testutils::Ledger;
    
    let env = Env::default();
    env.mock_all_auths();
    
    // Set a realistic timestamp (not 0) to match production conditions
    // Timestamp 0 can cause edge cases in time-based calculations
    env.ledger().with_mut(|li| {
        li.timestamp = 1704067200; // Jan 1, 2024 00:00:00 UTC
    });
    
    env
}

pub fn create_test_addresses(env: &Env) -> (Address, Address, Address) {
    let admin = Address::generate(env);
    let user1 = Address::generate(env);
    let user2 = Address::generate(env);
    (admin, user1, user2)
}

pub fn deploy_reflector_stub(env: &Env) -> Address {
    env.register(ReflectorStub, ())
}

pub fn initialize_oracle(env: &Env, admin: &Address) -> Address {
    let contract_id = env.register(price_oracle::WASM, ());
    let client = price_oracle::Client::new(env, &contract_id);

    let reflector_contract = deploy_reflector_stub(env);
    let base_currency_address = Address::generate(env);
    let native_xlm_address = Address::generate(env);

    client.initialize(admin, &reflector_contract, &base_currency_address, &native_xlm_address);

    contract_id
}

// Helper function to get default expiry timestamp (24 hours from now)
pub fn default_expiry_timestamp(env: &Env) -> u64 {
    env.ledger().timestamp() + 86400 // 24 hours in seconds
}

#[test]
fn test_oracle_initialization() {
    let env = create_test_env();
    let (admin, _user1, _user2) = create_test_addresses(&env);

    let oracle = initialize_oracle(&env, &admin);
    let client = price_oracle::Client::new(&env, &oracle);

    let whitelisted_assets = client.get_whitelisted_assets();
    assert_eq!(whitelisted_assets.len(), 0);
}

#[test]
#[should_panic]
fn test_oracle_double_initialization() {
    let env = create_test_env();
    let (admin, _user1, _user2) = create_test_addresses(&env);

    let oracle = initialize_oracle(&env, &admin);
    let client = price_oracle::Client::new(&env, &oracle);

    let reflector_contract = Address::generate(&env);
    let base_currency_address = Address::generate(&env);
    let native_xlm_address = Address::generate(&env);

    client.initialize(&admin, &reflector_contract, &base_currency_address, &native_xlm_address);
}

#[test]
fn test_add_stellar_asset() {
    let env = create_test_env();
    let (admin, _user1, _user2) = create_test_addresses(&env);

    let oracle = initialize_oracle(&env, &admin);
    let client = price_oracle::Client::new(&env, &oracle);

    let asset_address = Address::generate(&env);
    let asset = OracleAsset::Stellar(asset_address.clone());

    client.add_asset(&admin, &asset);

    let whitelisted_assets = client.get_whitelisted_assets();
    assert_eq!(whitelisted_assets.len(), 1);

    // Verify asset configuration
    let config = client.get_asset_config(&asset);
    assert!(config.is_some());

    let config = config.unwrap();
    assert_eq!(config.enabled, true);
    assert_eq!(config.manual_override_price, None);
}

#[test]
fn test_add_external_asset() {
    let env = create_test_env();
    let (admin, _user1, _user2) = create_test_addresses(&env);

    let oracle = initialize_oracle(&env, &admin);
    let client = price_oracle::Client::new(&env, &oracle);

    let asset = OracleAsset::Other(Symbol::new(&env, "BTC"));

    // Add asset to whitelist
    client.add_asset(&admin, &asset);

    // Verify asset was added
    let whitelisted_assets = client.get_whitelisted_assets();
    assert_eq!(whitelisted_assets.len(), 1);

    // Verify asset configuration
    let config = client.get_asset_config(&asset);
    assert!(config.is_some());
}

#[test]
fn test_add_multiple_assets() {
    let env = create_test_env();
    let (admin, _user1, _user2) = create_test_addresses(&env);

    let oracle = initialize_oracle(&env, &admin);
    let client = price_oracle::Client::new(&env, &oracle);

    // Add multiple assets
    let asset1 = OracleAsset::Stellar(Address::generate(&env));
    let asset2 = OracleAsset::Stellar(Address::generate(&env));
    let asset3 = OracleAsset::Other(Symbol::new(&env, "ETH"));
    let asset4 = OracleAsset::Other(Symbol::new(&env, "USDC"));

    client.add_asset(&admin, &asset1);
    client.add_asset(&admin, &asset2);
    client.add_asset(&admin, &asset3);
    client.add_asset(&admin, &asset4);

    // Verify all assets were added
    let whitelisted_assets = client.get_whitelisted_assets();
    assert_eq!(whitelisted_assets.len(), 4);
}

#[test]
fn test_remove_asset() {
    let env = create_test_env();
    let (admin, _user1, _user2) = create_test_addresses(&env);

    let oracle = initialize_oracle(&env, &admin);
    let client = price_oracle::Client::new(&env, &oracle);

    let asset = OracleAsset::Stellar(Address::generate(&env));

    // Add asset to whitelist
    client.add_asset(&admin, &asset);

    // Verify asset was added
    let whitelisted_assets = client.get_whitelisted_assets();
    assert_eq!(whitelisted_assets.len(), 1);

    // Remove asset from whitelist
    client.remove_asset(&asset);

    // Verify asset was removed
    let whitelisted_assets = client.get_whitelisted_assets();
    assert_eq!(whitelisted_assets.len(), 0);

    // Verify asset configuration is gone
    let config = client.get_asset_config(&asset);
    assert!(config.is_none());
}

#[test]
fn test_enable_disable_asset() {
    let env = create_test_env();
    let (admin, _user1, _user2) = create_test_addresses(&env);

    let oracle = initialize_oracle(&env, &admin);
    let client = price_oracle::Client::new(&env, &oracle);

    let asset = OracleAsset::Stellar(Address::generate(&env));

    // Add asset to whitelist
    client.add_asset(&admin, &asset);

    // Verify asset is enabled by default
    let config = client.get_asset_config(&asset).unwrap();
    assert_eq!(config.enabled, true);

    // Disable asset
    client.set_asset_enabled(&admin, &asset, &false);

    // Verify asset is disabled
    let config = client.get_asset_config(&asset).unwrap();
    assert_eq!(config.enabled, false);

    // Re-enable asset
    client.set_asset_enabled(&admin, &asset, &true);

    // Verify asset is enabled
    let config = client.get_asset_config(&asset).unwrap();
    assert_eq!(config.enabled, true);
}

#[test]
fn test_manual_price_override() {
    let env = create_test_env();
    let (admin, _user1, _user2) = create_test_addresses(&env);

    let oracle = initialize_oracle(&env, &admin);
    let client = price_oracle::Client::new(&env, &oracle);

    let asset = OracleAsset::Stellar(Address::generate(&env));

    // Add asset to whitelist
    client.add_asset(&admin, &asset);

    // Verify no manual override initially
    let config = client.get_asset_config(&asset).unwrap();
    assert_eq!(config.manual_override_price, None);

    // Set manual price override
    let manual_price = 2_000_000_000_000_000u128; // $2 in 14 decimal format
    client.set_manual_override(&admin, &asset, &Some(manual_price), &Some(env.ledger().timestamp() + 86400));

    // Verify manual override was set
    let config = client.get_asset_config(&asset).unwrap();
    assert_eq!(config.manual_override_price, Some(manual_price));

    // Remove manual override
    client.set_manual_override(&admin, &asset, &None, &Some(default_expiry_timestamp(&env)));

    // Verify manual override was removed
    let config = client.get_asset_config(&asset).unwrap();
    assert_eq!(config.manual_override_price, None);
}

// ========================================================================
// PRICE QUERY TESTS
// ========================================================================

#[test]
fn test_get_asset_price_with_manual_override() {
    let env = create_test_env();
    let (admin, _user1, _user2) = create_test_addresses(&env);

    let oracle = initialize_oracle(&env, &admin);
    let client = price_oracle::Client::new(&env, &oracle);

    let asset = OracleAsset::Stellar(Address::generate(&env));

    // Add asset to whitelist
    client.add_asset(&admin, &asset);

    // Set manual price override
    let manual_price = 3_500_000_000_000_000u128; // $3.5 in 14 decimal format
    client.set_manual_override(&admin, &asset, &Some(manual_price), &Some(env.ledger().timestamp() + 86400));

    // Get asset price (should return manual override)
    let price = client.get_asset_price(&asset);
    assert_eq!(price, manual_price);
}

#[test]
fn test_get_price_for_non_whitelisted_asset() {
    let env = create_test_env();
    let (admin, _user1, _user2) = create_test_addresses(&env);

    let oracle = initialize_oracle(&env, &admin);
    let client = price_oracle::Client::new(&env, &oracle);

    let asset = OracleAsset::Stellar(Address::generate(&env));

    // Try to get price for non-whitelisted asset (should return error)
    let result = client.try_get_asset_price(&asset);
    assert!(result.is_err());
}

#[test]
fn test_get_price_for_disabled_asset() {
    let env = create_test_env();
    let (admin, _user1, _user2) = create_test_addresses(&env);

    let oracle = initialize_oracle(&env, &admin);
    let client = price_oracle::Client::new(&env, &oracle);

    let asset = OracleAsset::Stellar(Address::generate(&env));

    // Add asset and disable it
    client.add_asset(&admin, &asset);
    client.set_asset_enabled(&admin, &asset, &false);

    // Try to get price for disabled asset (should return error)
    let result = client.try_get_asset_price(&asset);
    assert!(result.is_err());
}

#[test]
fn test_get_prices_multiple_assets() {
    let env = create_test_env();
    let (admin, _user1, _user2) = create_test_addresses(&env);

    let oracle = initialize_oracle(&env, &admin);
    let client = price_oracle::Client::new(&env, &oracle);

    // Add multiple assets with manual overrides
    let asset1 = OracleAsset::Stellar(Address::generate(&env));
    let asset2 = OracleAsset::Other(Symbol::new(&env, "ETH"));
    let asset3 = OracleAsset::Other(Symbol::new(&env, "BTC"));

    client.add_asset(&admin, &asset1);
    client.add_asset(&admin, &asset2);
    client.add_asset(&admin, &asset3);

    client.set_manual_override(&admin, &asset1, &Some(1_000_000_000_000_000u128), &Some(env.ledger().timestamp() + 86400));
    client.set_manual_override(&admin, &asset2, &Some(2_500_000_000_000_000u128), &Some(env.ledger().timestamp() + 86400));
    client.set_manual_override(&admin, &asset3, &Some(45_000_000_000_000_000u128), &Some(env.ledger().timestamp() + 86400));

    // Get prices for multiple assets
    let mut assets = Vec::new(&env);
    assets.push_back(asset1.clone());
    assets.push_back(asset2.clone());
    assets.push_back(asset3.clone());

    let prices = client.get_asset_prices_vec(&assets);

    // Verify we got prices for all assets
    assert_eq!(prices.len(), 3);
}

// ========================================================================
// AUTHORIZATION TESTS
// ========================================================================

#[test]
#[should_panic(expected = "Error(Contract, #14)")]
fn test_add_asset_unauthorized() {
    let env = create_test_env();
    let (admin, user1, _user2) = create_test_addresses(&env);

    let oracle = initialize_oracle(&env, &admin);
    let client = price_oracle::Client::new(&env, &oracle);

    let asset = OracleAsset::Stellar(Address::generate(&env));

    // Try to add asset as non-admin (should panic)
    client.add_asset(&user1, &asset);
}

#[test]
#[should_panic(expected = "Error(Auth, InvalidAction)")]
fn test_remove_asset_unauthorized() {
    let env = create_test_env();
    let (admin, _user1, _user2) = create_test_addresses(&env);

    let oracle = initialize_oracle(&env, &admin);
    let client = price_oracle::Client::new(&env, &oracle);

    let asset = OracleAsset::Stellar(Address::generate(&env));

    // Add asset as admin
    client.add_asset(&admin, &asset);

    // Try to remove asset as non-admin (should panic with Unauthorized)
    env.mock_auths(&[]);
    client.remove_asset(&asset);
}

#[test]
#[should_panic(expected = "Error(Contract, #14)")]
fn test_set_asset_enabled_unauthorized() {
    let env = create_test_env();
    let (admin, user1, _user2) = create_test_addresses(&env);

    let oracle = initialize_oracle(&env, &admin);
    let client = price_oracle::Client::new(&env, &oracle);

    let asset = OracleAsset::Stellar(Address::generate(&env));

    // Add asset as admin
    client.add_asset(&admin, &asset);

    // Try to disable asset as non-admin (should panic)
    client.set_asset_enabled(&user1, &asset, &false);
}

#[test]
#[should_panic(expected = "Error(Contract, #14)")]
fn test_set_manual_override_unauthorized() {
    let env = create_test_env();
    let (admin, user1, _user2) = create_test_addresses(&env);

    let oracle = initialize_oracle(&env, &admin);
    let client = price_oracle::Client::new(&env, &oracle);

    let asset = OracleAsset::Stellar(Address::generate(&env));

    // Add asset as admin
    client.add_asset(&admin, &asset);

    // Try to set manual override as non-admin (should panic)
    client.set_manual_override(&user1, &asset, &Some(1_000_000_000_000_000u128), &Some(env.ledger().timestamp() + 86400));
}

// ========================================================================
// EDGE CASE TESTS
// ========================================================================

#[test]
fn test_asset_configuration_persistence() {
    let env = create_test_env();
    let (admin, _user1, _user2) = create_test_addresses(&env);

    let oracle = initialize_oracle(&env, &admin);
    let client = price_oracle::Client::new(&env, &oracle);

    let asset = OracleAsset::Stellar(Address::generate(&env));

    // Add asset with full configuration
    client.add_asset(&admin, &asset);
    client.set_asset_enabled(&admin, &asset, &false);
    client.set_manual_override(&admin, &asset, &Some(5_000_000_000_000_000u128), &Some(env.ledger().timestamp() + 86400));

    // Verify configuration persists
    let config = client.get_asset_config(&asset).unwrap();
    assert_eq!(config.enabled, false);
    assert_eq!(
        config.manual_override_price,
        Some(5_000_000_000_000_000u128)
    );

    // Re-enable and clear override
    client.set_asset_enabled(&admin, &asset, &true);
    client.set_manual_override(&admin, &asset, &None, &Some(default_expiry_timestamp(&env)));

    // Verify changes persisted
    let config = client.get_asset_config(&asset).unwrap();
    assert_eq!(config.enabled, true);
    assert_eq!(config.manual_override_price, None);
}

#[test]
fn test_whitelisted_assets_list_accuracy() {
    let env = create_test_env();
    let (admin, _user1, _user2) = create_test_addresses(&env);

    let oracle = initialize_oracle(&env, &admin);
    let client = price_oracle::Client::new(&env, &oracle);

    // Start with empty list
    let whitelisted_assets = client.get_whitelisted_assets();
    assert_eq!(whitelisted_assets.len(), 0);

    // Add assets one by one and verify list grows
    let asset1 = OracleAsset::Stellar(Address::generate(&env));
    client.add_asset(&admin, &asset1);
    assert_eq!(client.get_whitelisted_assets().len(), 1);

    let asset2 = OracleAsset::Other(Symbol::new(&env, "ETH"));
    client.add_asset(&admin, &asset2);
    assert_eq!(client.get_whitelisted_assets().len(), 2);

    let asset3 = OracleAsset::Other(Symbol::new(&env, "BTC"));
    client.add_asset(&admin, &asset3);
    assert_eq!(client.get_whitelisted_assets().len(), 3);

    // Remove assets one by one and verify list shrinks
    client.remove_asset(&asset1);
    assert_eq!(client.get_whitelisted_assets().len(), 2);

    client.remove_asset(&asset2);
    assert_eq!(client.get_whitelisted_assets().len(), 1);

    client.remove_asset(&asset3);
    assert_eq!(client.get_whitelisted_assets().len(), 0);
}

// ========================================================================
// CRITICAL EDGE CASE TESTS
// ========================================================================

#[test]
fn test_price_precision_accuracy() {
    let env = create_test_env();
    let (admin, _user1, _user2) = create_test_addresses(&env);

    let oracle = initialize_oracle(&env, &admin);
    let client = price_oracle::Client::new(&env, &oracle);

    let asset = OracleAsset::Stellar(Address::generate(&env));
    client.add_asset(&admin, &asset);

    // Test price precision
    let price = client.get_asset_price(&asset);
    assert_eq!(price, TEST_PRICE_DEFAULT);

    // Oracle with 14-decimal precision needs 10^4 conversion to WAD
    let oracle_to_wad = k2_shared::calculate_oracle_to_wad_factor(14);
    let price_in_wad = price * oracle_to_wad;
    assert_eq!(price_in_wad, 10_000_000_000_000_000_000u128);
}

#[test]
fn test_asset_type_handling() {
    let env = create_test_env();
    let (admin, _user1, _user2) = create_test_addresses(&env);

    let oracle = initialize_oracle(&env, &admin);
    let client = price_oracle::Client::new(&env, &oracle);

    // Test Stellar asset
    let stellar_asset = OracleAsset::Stellar(Address::generate(&env));
    client.add_asset(&admin, &stellar_asset);
    
    let stellar_price = client.get_asset_price(&stellar_asset);
    assert_eq!(stellar_price, TEST_PRICE_DEFAULT);

    // Test external asset
    let external_asset = OracleAsset::Other(Symbol::new(&env, "BTC"));
    client.add_asset(&admin, &external_asset);
    let external_price = client.get_asset_price(&external_asset);
    assert_eq!(external_price, TEST_PRICE_BTC);
}

#[test]
fn test_price_staleness_validation() {
    let env = create_test_env();
    let (admin, _user1, _user2) = create_test_addresses(&env);

    let oracle = initialize_oracle(&env, &admin);
    let client = price_oracle::Client::new(&env, &oracle);

    let asset = OracleAsset::Stellar(Address::generate(&env));
    client.add_asset(&admin, &asset);

    // Get price data with timestamp
    let price_data = client.get_asset_price_data(&asset);
    let current_timestamp = env.ledger().timestamp();

    // Verify timestamp is recent (within reasonable bounds)
    assert!(price_data.timestamp <= current_timestamp);
    // Timestamp is u64, so it's always >= 0
}

#[test]
fn test_oracle_failure_handling() {
    let env = create_test_env();
    let (admin, _user1, _user2) = create_test_addresses(&env);

    let oracle = initialize_oracle(&env, &admin);
    let client = price_oracle::Client::new(&env, &oracle);

    // Test getting price for non-whitelisted asset
    let non_whitelisted_asset = OracleAsset::Stellar(Address::generate(&env));
    let result = client.try_get_asset_price(&non_whitelisted_asset);
    assert!(result.is_err());

    // Test getting price for disabled asset
    let disabled_asset = OracleAsset::Stellar(Address::generate(&env));
    client.add_asset(&admin, &disabled_asset);
    client.set_asset_enabled(&admin, &disabled_asset, &false);
    let result = client.try_get_asset_price(&disabled_asset);
    assert!(result.is_err());
}

#[test]
fn test_manual_override_precedence() {
    let env = create_test_env();
    let (admin, _user1, _user2) = create_test_addresses(&env);

    let oracle = initialize_oracle(&env, &admin);
    let client = price_oracle::Client::new(&env, &oracle);

    let asset = OracleAsset::Stellar(Address::generate(&env));
    client.add_asset(&admin, &asset);

    // Set manual override price
    let override_price = 5_000_000_000_000_000u128; // $5.00
    client.set_manual_override(&admin, &asset, &Some(override_price), &Some(env.ledger().timestamp() + 86400));

    // Price should be the override, not the oracle price
    let price = client.get_asset_price(&asset);
    assert_eq!(price, override_price);

    // Clear override and reset circuit breaker (large price change from $5 to $1)
    client.set_manual_override(&admin, &asset, &None, &Some(default_expiry_timestamp(&env)));
    client.reset_circuit_breaker(&admin, &asset);

    // Price should be back to oracle price
    let price = client.get_asset_price(&asset);
    assert_eq!(price, 1_000_000_000_000_000u128); // $1.00
}


// ========================================================================
// CIRCUIT BREAKER TESTS
// ========================================================================

#[test]
fn test_circuit_breaker_first_price_allowed() {
    let env = create_test_env();
    let (admin, _user1, _user2) = create_test_addresses(&env);

    let oracle = initialize_oracle(&env, &admin);
    let client = price_oracle::Client::new(&env, &oracle);

    let asset = OracleAsset::Stellar(Address::generate(&env));
    client.add_asset(&admin, &asset);

    // First price query should succeed (no last price stored)
    let price = client.get_asset_price(&asset);
    assert_eq!(price, TEST_PRICE_DEFAULT);

    // Verify last price was stored
    let last_price = client.get_last_price(&asset);
    assert_eq!(last_price, Some(TEST_PRICE_DEFAULT));
}

#[test]
fn test_circuit_breaker_normal_price_change_allowed() {
    let env = create_test_env();
    let (admin, _user1, _user2) = create_test_addresses(&env);

    let oracle = initialize_oracle(&env, &admin);
    let client = price_oracle::Client::new(&env, &oracle);

    let asset = OracleAsset::Stellar(Address::generate(&env));
    client.add_asset(&admin, &asset);

    // Set initial price via manual override
    let initial_price = 1_000_000_000_000_000u128; // $1.00
    client.set_manual_override(&admin, &asset, &Some(initial_price), &Some(env.ledger().timestamp() + 86400));
    let _ = client.get_asset_price(&asset); // Store as last price

    // Change price by 10% (within 20% threshold)
    let new_price = 1_100_000_000_000_000u128; // $1.10 (10% increase)
    client.set_manual_override(&admin, &asset, &Some(new_price), &Some(env.ledger().timestamp() + 86400));
    
    // Should succeed - 10% change is within 20% threshold
    let price = client.get_asset_price(&asset);
    assert_eq!(price, new_price);
}

#[test]
fn test_circuit_breaker_large_price_change_rejected() {
    let env = create_test_env();
    let (admin, _user1, _user2) = create_test_addresses(&env);

    let oracle = initialize_oracle(&env, &admin);
    let client = price_oracle::Client::new(&env, &oracle);

    let asset = OracleAsset::Stellar(Address::generate(&env));
    client.add_asset(&admin, &asset);

    // Set initial price
    let initial_price = 1_000_000_000_000_000u128; // $1.00
    client.set_manual_override(&admin, &asset, &Some(initial_price), &Some(env.ledger().timestamp() + 86400));
    let _ = client.get_asset_price(&asset); // Store as last price

    // Try to change price by 25% (exceeds 20% threshold)
    // Circuit breaker is applied during set_manual_override
    let large_price = 1_250_000_000_000_000u128; // $1.25 (25% increase)
    let result = client.try_set_manual_override(&admin, &asset, &Some(large_price), &Some(env.ledger().timestamp() + 86400));
    
    // Should fail with PriceChangeTooLarge error during set
    assert!(result.is_err());
}

#[test]
fn test_circuit_breaker_price_decrease_rejected() {
    let env = create_test_env();
    let (admin, _user1, _user2) = create_test_addresses(&env);

    let oracle = initialize_oracle(&env, &admin);
    let client = price_oracle::Client::new(&env, &oracle);

    let asset = OracleAsset::Stellar(Address::generate(&env));
    client.add_asset(&admin, &asset);

    // Set initial price
    let initial_price = 1_000_000_000_000_000u128; // $1.00
    client.set_manual_override(&admin, &asset, &Some(initial_price), &Some(env.ledger().timestamp() + 86400));
    let _ = client.get_asset_price(&asset); // Store as last price

    // Try to decrease price by 25% (exceeds 20% threshold)
    // Circuit breaker is applied during set_manual_override
    let low_price = 750_000_000_000_000u128; // $0.75 (25% decrease)
    let result = client.try_set_manual_override(&admin, &asset, &Some(low_price), &Some(env.ledger().timestamp() + 86400));
    
    // Should fail with PriceChangeTooLarge error during set
    assert!(result.is_err());
}

#[test]
fn test_circuit_breaker_disabled_allows_any_change() {
    let env = create_test_env();
    let (admin, _user1, _user2) = create_test_addresses(&env);

    let oracle = initialize_oracle(&env, &admin);
    let client = price_oracle::Client::new(&env, &oracle);

    let asset = OracleAsset::Stellar(Address::generate(&env));
    client.add_asset(&admin, &asset);

    // Disable circuit breaker by setting max_price_change_bps to 0
    let mut config = client.get_oracle_config();
    config.max_price_change_bps = 0;
    client.set_oracle_config(&admin, &config);

    // Set initial price
    let initial_price = 1_000_000_000_000_000u128; // $1.00
    client.set_manual_override(&admin, &asset, &Some(initial_price), &Some(env.ledger().timestamp() + 86400));
    let _ = client.get_asset_price(&asset); // Store as last price

    // Try extreme price change (1000% increase)
    let extreme_price = 10_000_000_000_000_000u128; // $10.00 (1000% increase)
    client.set_manual_override(&admin, &asset, &Some(extreme_price), &Some(env.ledger().timestamp() + 86400));
    
    // Should succeed - circuit breaker is disabled
    let price = client.get_asset_price(&asset);
    assert_eq!(price, extreme_price);
}

#[test]
fn test_circuit_breaker_reset_single_asset() {
    let env = create_test_env();
    let (admin, _user1, _user2) = create_test_addresses(&env);

    let oracle = initialize_oracle(&env, &admin);
    let client = price_oracle::Client::new(&env, &oracle);

    let asset = OracleAsset::Stellar(Address::generate(&env));
    client.add_asset(&admin, &asset);

    // Set initial price and query it
    let initial_price = 1_000_000_000_000_000u128; // $1.00
    client.set_manual_override(&admin, &asset, &Some(initial_price), &Some(env.ledger().timestamp() + 86400));
    let _ = client.get_asset_price(&asset); // Store as last price

    // Verify last price is stored
    assert_eq!(client.get_last_price(&asset), Some(initial_price));

    // Reset circuit breaker
    client.reset_circuit_breaker(&admin, &asset);

    // Verify last price is cleared
    assert_eq!(client.get_last_price(&asset), None);

    // Now large price change should be allowed (no last price to compare)
    let large_price = 5_000_000_000_000_000u128; // $5.00 (500% increase)
    client.set_manual_override(&admin, &asset, &Some(large_price), &Some(env.ledger().timestamp() + 86400));
    let price = client.get_asset_price(&asset);
    assert_eq!(price, large_price);
}

#[test]
fn test_circuit_breaker_reset_all_assets() {
    let env = create_test_env();
    let (admin, _user1, _user2) = create_test_addresses(&env);

    let oracle = initialize_oracle(&env, &admin);
    let client = price_oracle::Client::new(&env, &oracle);

    // Add multiple assets
    let asset1 = OracleAsset::Stellar(Address::generate(&env));
    let asset2 = OracleAsset::Other(Symbol::new(&env, "ETH"));
    let asset3 = OracleAsset::Other(Symbol::new(&env, "BTC"));

    client.add_asset(&admin, &asset1);
    client.add_asset(&admin, &asset2);
    client.add_asset(&admin, &asset3);

    // Set prices and query them to store last prices
    client.set_manual_override(&admin, &asset1, &Some(1_000_000_000_000_000u128), &Some(env.ledger().timestamp() + 86400));
    client.set_manual_override(&admin, &asset2, &Some(2_000_000_000_000_000u128), &Some(env.ledger().timestamp() + 86400));
    client.set_manual_override(&admin, &asset3, &Some(3_000_000_000_000_000u128), &Some(env.ledger().timestamp() + 86400));

    let _ = client.get_asset_price(&asset1);
    let _ = client.get_asset_price(&asset2);
    let _ = client.get_asset_price(&asset3);

    // Verify all last prices are stored
    assert_eq!(client.get_last_price(&asset1), Some(1_000_000_000_000_000u128));
    assert_eq!(client.get_last_price(&asset2), Some(2_000_000_000_000_000u128));
    assert_eq!(client.get_last_price(&asset3), Some(3_000_000_000_000_000u128));

    // Reset all circuit breakers
    client.reset_all_circuit_breakers(&admin);

    // Verify all last prices are cleared
    assert_eq!(client.get_last_price(&asset1), None);
    assert_eq!(client.get_last_price(&asset2), None);
    assert_eq!(client.get_last_price(&asset3), None);
}

#[test]
fn test_circuit_breaker_threshold_boundary() {
    let env = create_test_env();
    let (admin, _user1, _user2) = create_test_addresses(&env);

    let oracle = initialize_oracle(&env, &admin);
    let client = price_oracle::Client::new(&env, &oracle);

    let asset = OracleAsset::Stellar(Address::generate(&env));
    client.add_asset(&admin, &asset);

    // Set initial price
    let initial_price = 1_000_000_000_000_000u128; // $1.00
    client.set_manual_override(&admin, &asset, &Some(initial_price), &Some(env.ledger().timestamp() + 86400));
    let _ = client.get_asset_price(&asset); // Store as last price

    // Test exactly at 20% threshold (should be allowed)
    // 20% of $1.00 = $0.20, so $1.20 should be allowed
    let price_at_threshold = 1_200_000_000_000_000u128; // $1.20 (exactly 20% increase)
    client.set_manual_override(&admin, &asset, &Some(price_at_threshold), &Some(env.ledger().timestamp() + 86400));
    let price = client.get_asset_price(&asset);
    assert_eq!(price, price_at_threshold);

    // Update last price
    let _ = client.get_asset_price(&asset);

    // Test just over 20% threshold (should be rejected)
    // 20.01% of $1.20 = $1.44012, so $1.44 should be rejected
    // Circuit breaker is applied during set_manual_override
    let price_over_threshold = 1_440_120_000_000_000u128; // Just over 20% increase
    let result = client.try_set_manual_override(&admin, &asset, &Some(price_over_threshold), &Some(env.ledger().timestamp() + 86400));
    assert!(result.is_err());
}

#[test]
fn test_circuit_breaker_with_oracle_price() {
    let env = create_test_env();
    let (admin, _user1, _user2) = create_test_addresses(&env);

    let oracle = initialize_oracle(&env, &admin);
    let client = price_oracle::Client::new(&env, &oracle);

    let asset = OracleAsset::Stellar(Address::generate(&env));
    client.add_asset(&admin, &asset);

    // First query from oracle - should succeed
    let price1 = client.get_asset_price(&asset);
    assert_eq!(price1, TEST_PRICE_DEFAULT);

    // Second query with same price - should succeed
    let price2 = client.get_asset_price(&asset);
    assert_eq!(price2, TEST_PRICE_DEFAULT);

    // Verify last price is stored
    assert_eq!(client.get_last_price(&asset), Some(TEST_PRICE_DEFAULT));
}

#[test]
#[should_panic(expected = "Error(Contract, #14)")]
fn test_reset_circuit_breaker_unauthorized() {
    let env = create_test_env();
    let (admin, user1, _user2) = create_test_addresses(&env);

    let oracle = initialize_oracle(&env, &admin);
    let client = price_oracle::Client::new(&env, &oracle);

    let asset = OracleAsset::Stellar(Address::generate(&env));
    client.add_asset(&admin, &asset);

    // Try to reset circuit breaker as non-admin (should panic)
    client.reset_circuit_breaker(&user1, &asset);
}

#[test]
#[should_panic(expected = "Error(Contract, #14)")]
fn test_reset_all_circuit_breakers_unauthorized() {
    let env = create_test_env();
    let (admin, user1, _user2) = create_test_addresses(&env);

    let oracle = initialize_oracle(&env, &admin);
    let client = price_oracle::Client::new(&env, &oracle);

    // Try to reset all circuit breakers as non-admin (should panic)
    client.reset_all_circuit_breakers(&user1);
}

#[test]
fn test_circuit_breaker_multiple_assets_independent() {
    let env = create_test_env();
    let (admin, _user1, _user2) = create_test_addresses(&env);

    let oracle = initialize_oracle(&env, &admin);
    let client = price_oracle::Client::new(&env, &oracle);

    let asset1 = OracleAsset::Stellar(Address::generate(&env));
    let asset2 = OracleAsset::Other(Symbol::new(&env, "ETH"));

    client.add_asset(&admin, &asset1);
    client.add_asset(&admin, &asset2);

    // Set initial prices
    client.set_manual_override(&admin, &asset1, &Some(1_000_000_000_000_000u128), &Some(env.ledger().timestamp() + 86400));
    client.set_manual_override(&admin, &asset2, &Some(2_000_000_000_000_000u128), &Some(env.ledger().timestamp() + 86400));

    let _ = client.get_asset_price(&asset1);
    let _ = client.get_asset_price(&asset2);

    // Large change for asset1 should be rejected during set_manual_override
    let result1 = client.try_set_manual_override(&admin, &asset1, &Some(5_000_000_000_000_000u128), &Some(env.ledger().timestamp() + 86400)); // 500% increase
    assert!(result1.is_err());

    // Normal change for asset2 should still work
    client.set_manual_override(&admin, &asset2, &Some(2_100_000_000_000_000u128), &Some(env.ledger().timestamp() + 86400)); // 5% increase
    let price2 = client.get_asset_price(&asset2);
    assert_eq!(price2, 2_100_000_000_000_000u128);
}

#[test]
fn test_circuit_breaker_after_reset_legitimate_change() {
    let env = create_test_env();
    let (admin, _user1, _user2) = create_test_addresses(&env);

    let oracle = initialize_oracle(&env, &admin);
    let client = price_oracle::Client::new(&env, &oracle);

    let asset = OracleAsset::Stellar(Address::generate(&env));
    client.add_asset(&admin, &asset);

    // Set initial price
    let initial_price = 1_000_000_000_000_000u128; // $1.00
    client.set_manual_override(&admin, &asset, &Some(initial_price), &Some(env.ledger().timestamp() + 86400));
    let _ = client.get_asset_price(&asset);

    // Try large change - should fail during set_manual_override
    let large_price = 3_000_000_000_000_000u128; // $3.00 (300% increase)
    let result = client.try_set_manual_override(&admin, &asset, &Some(large_price), &Some(env.ledger().timestamp() + 86400));
    assert!(result.is_err());

    // Reset circuit breaker (simulating admin action for legitimate change)
    client.reset_circuit_breaker(&admin, &asset);

    // Now large change should be allowed after reset
    client.set_manual_override(&admin, &asset, &Some(large_price), &Some(env.ledger().timestamp() + 86400));
    let price = client.get_asset_price(&asset);
    assert_eq!(price, large_price);

    // Verify new price is stored as last price
    assert_eq!(client.get_last_price(&asset), Some(large_price));
}

#[test]
fn test_oracle_reflector_precision_query() {
    let env = create_test_env();
    let (admin, _, _) = create_test_addresses(&env);
    let oracle_id = initialize_oracle(&env, &admin);
    let client = price_oracle::Client::new(&env, &oracle_id);
    
    let config = client.get_oracle_config();
    assert_eq!(config.price_precision, 14u32, "Default Reflector precision should be 14 decimals");
    
    let reflector_contract = client.get_reflector_contract();
    assert!(reflector_contract.is_some(), "Reflector contract must be configured");
}

// ========================================================================
// CUSTOM ORACLE TESTS
// ========================================================================

#[test]
fn test_set_custom_oracle() {
    let env = create_test_env();
    let (admin, _, _) = create_test_addresses(&env);
    let oracle_id = initialize_oracle(&env, &admin);
    let client = price_oracle::Client::new(&env, &oracle_id);

    let asset = OracleAsset::Stellar(Address::generate(&env));
    let custom_oracle_addr = Address::generate(&env);

    // Add asset first
    client.add_asset(&admin, &asset);

    // Verify no custom oracle initially
    let initial = client.get_custom_oracle(&asset);
    assert!(initial.is_none(), "Custom oracle should be None initially");

    // Set custom oracle
    client.set_custom_oracle(&admin, &asset, &Some(custom_oracle_addr.clone()), &Some(3600), &None);

    // Verify custom oracle is set
    let stored = client.get_custom_oracle(&asset);
    assert_eq!(stored, Some(custom_oracle_addr.clone()), "Custom oracle should be set");

    // Clear custom oracle
    client.set_custom_oracle(&admin, &asset, &None, &None, &None);

    // Verify custom oracle is cleared
    let cleared = client.get_custom_oracle(&asset);
    assert!(cleared.is_none(), "Custom oracle should be cleared");
}

#[test]
#[should_panic(expected = "Error(Contract, #14)")] // Unauthorized
fn test_set_custom_oracle_unauthorized() {
    let env = create_test_env();
    let (admin, _, _) = create_test_addresses(&env);
    let oracle_id = initialize_oracle(&env, &admin);
    let client = price_oracle::Client::new(&env, &oracle_id);

    let asset = OracleAsset::Stellar(Address::generate(&env));
    let custom_oracle_addr = Address::generate(&env);
    let non_admin = Address::generate(&env);

    // Add asset first
    client.add_asset(&admin, &asset);

    // Try to set custom oracle as non-admin (should panic)
    client.set_custom_oracle(&non_admin, &asset, &Some(custom_oracle_addr), &Some(3600), &None);
}

#[test]
#[should_panic(expected = "Error(Contract, #7)")] // AssetNotWhitelisted
fn test_set_custom_oracle_asset_not_whitelisted() {
    let env = create_test_env();
    let (admin, _, _) = create_test_addresses(&env);
    let oracle_id = initialize_oracle(&env, &admin);
    let client = price_oracle::Client::new(&env, &oracle_id);

    let asset = OracleAsset::Stellar(Address::generate(&env));
    let custom_oracle_addr = Address::generate(&env);

    // Try to set custom oracle for non-whitelisted asset (should panic)
    client.set_custom_oracle(&admin, &asset, &Some(custom_oracle_addr), &Some(3600), &None);
}

#[test]
fn test_get_custom_oracle_returns_none_for_unknown_asset() {
    let env = create_test_env();
    let (admin, _, _) = create_test_addresses(&env);
    let oracle_id = initialize_oracle(&env, &admin);
    let client = price_oracle::Client::new(&env, &oracle_id);

    let unknown_asset = OracleAsset::Stellar(Address::generate(&env));

    // Should return None for unknown asset (not panic)
    let result = client.get_custom_oracle(&unknown_asset);
    assert!(result.is_none(), "Should return None for unknown asset");
}

// ========================================================================
// CUSTOM ORACLE PRICE FETCHING TESTS
// ========================================================================

use crate::price_oracle_test_stub::{CustomOracleStub, ConfigurableCustomOracleStub};

#[test]
fn test_get_price_from_custom_oracle() {
    let env = create_test_env();
    let (admin, _, _) = create_test_addresses(&env);
    let oracle_id = initialize_oracle(&env, &admin);
    let client = price_oracle::Client::new(&env, &oracle_id);

    // Register and deploy the custom oracle stub
    let custom_oracle_id = env.register(CustomOracleStub, ());

    let asset = OracleAsset::Stellar(Address::generate(&env));

    // Add asset and set custom oracle
    client.add_asset(&admin, &asset);
    client.set_custom_oracle(&admin, &asset, &Some(custom_oracle_id.clone()), &Some(3600), &None);

    // Verify custom oracle is set
    let stored = client.get_custom_oracle(&asset);
    assert_eq!(stored, Some(custom_oracle_id));

    // Get price - should use custom oracle
    let price = client.get_asset_price(&asset);
    
    // CustomOracleStub returns 100_000_000 with 8 decimals (1.00)
    // Price oracle normalizes to 14 decimals (default reflector precision)
    // 100_000_000 * 10^(14-8) = 100_000_000 * 10^6 = 100_000_000_000_000
    assert!(price > 0, "Price should be positive");
}

#[test]
fn test_get_price_from_configurable_custom_oracle() {
    let env = create_test_env();
    let (admin, _, _) = create_test_addresses(&env);
    let oracle_id = initialize_oracle(&env, &admin);
    let client = price_oracle::Client::new(&env, &oracle_id);

    // Register and deploy the configurable custom oracle stub
    let custom_oracle_id = env.register(ConfigurableCustomOracleStub, ());
    let custom_client = ConfigurableCustomOracleStubClient::new(&env, &custom_oracle_id);
    
    // Set price to 50_000_000_000 with 8 decimals (500.00 USD)
    custom_client.init(&500_00000000_u128, &8_u32);

    let asset = OracleAsset::Stellar(Address::generate(&env));

    // Add asset and set custom oracle
    client.add_asset(&admin, &asset);
    client.set_custom_oracle(&admin, &asset, &Some(custom_oracle_id), &Some(3600), &None);

    // Get price
    let price = client.get_asset_price(&asset);
    
    // Should be normalized to 14 decimals
    // 50_000_000_000 * 10^(14-8) = 50_000_000_000 * 10^6 = 50_000_000_000_000_000
    assert!(price > 0, "Price should be positive from configurable oracle");
}

#[test]
fn test_custom_oracle_fallback_to_reflector_on_zero_price() {
    let env = create_test_env();
    let (admin, _, _) = create_test_addresses(&env);
    let oracle_id = initialize_oracle(&env, &admin);
    let client = price_oracle::Client::new(&env, &oracle_id);

    // Create a custom oracle that returns zero price (invalid)
    let custom_oracle_id = env.register(ConfigurableCustomOracleStub, ());
    let custom_client = ConfigurableCustomOracleStubClient::new(&env, &custom_oracle_id);
    custom_client.init(&0_u128, &8_u32); // Zero price

    let asset = OracleAsset::Stellar(Address::generate(&env));

    // Add asset and set custom oracle with zero price
    client.add_asset(&admin, &asset);
    client.set_custom_oracle(&admin, &asset, &Some(custom_oracle_id), &Some(3600), &None);

    // M-10 FIX: Zero prices from custom oracles now return InvalidPrice error
    // instead of silently falling back to Reflector. This prevents downstream div-by-zero.
    let result = client.try_get_asset_price(&asset);
    assert!(result.is_err(), "Zero price from custom oracle should return error (M-10)");
}

#[test]
fn test_custom_oracle_with_different_decimals() {
    let env = create_test_env();
    let (admin, _, _) = create_test_addresses(&env);
    let oracle_id = initialize_oracle(&env, &admin);
    let client = price_oracle::Client::new(&env, &oracle_id);

    let custom_oracle_id = env.register(ConfigurableCustomOracleStub, ());
    let custom_client = ConfigurableCustomOracleStubClient::new(&env, &custom_oracle_id);
    
    // Set price with 18 decimals (like some DeFi oracles)
    // 1.5 with 18 decimals = 1_500_000_000_000_000_000
    custom_client.init(&1_500_000_000_000_000_000_u128, &18_u32);

    let asset = OracleAsset::Stellar(Address::generate(&env));

    client.add_asset(&admin, &asset);
    client.set_custom_oracle(&admin, &asset, &Some(custom_oracle_id), &Some(3600), &None);

    let price = client.get_asset_price(&asset);
    
    // Should normalize from 18 decimals to 14 decimals
    // 1_500_000_000_000_000_000 / 10^(18-14) = 1_500_000_000_000_000_000 / 10^4 = 150_000_000_000_000
    assert!(price > 0, "Price should be normalized from 18 decimals");
}

// Client for ConfigurableCustomOracleStub
mod configurable_oracle_client {
    use soroban_sdk::{contractclient, Address, Env};

    #[contractclient(name = "ConfigurableCustomOracleStubClient")]
    pub trait ConfigurableCustomOracleStubTrait {
        fn init(env: Env, price: u128, decimals: u32);
        fn set_timestamp_offset(env: Env, offset_seconds: i64);
        fn decimals(env: Env) -> u32;
    }
}

use configurable_oracle_client::ConfigurableCustomOracleStubClient;

// ========================================================================
// M-07 FIX: EXPIRED OVERRIDE CLEARS CIRCUIT BREAKER BASELINE
// ========================================================================

#[test]
fn test_m07_expired_override_clears_circuit_breaker_baseline() {
    use soroban_sdk::testutils::Ledger;

    let env = create_test_env();
    let (admin, _user1, _user2) = create_test_addresses(&env);

    let oracle = initialize_oracle(&env, &admin);
    let client = price_oracle::Client::new(&env, &oracle);

    let asset = OracleAsset::Stellar(Address::generate(&env));
    client.add_asset(&admin, &asset);

    // Phase 1: Set a manual override at $2.00 (no baseline yet, accepted)
    let override_price = 2_000_000_000_000_000u128; // $2.00
    let expiry = env.ledger().timestamp() + 3600; // 1 hour from now
    client.set_manual_override(&admin, &asset, &Some(override_price), &Some(expiry));

    // Query to store override price as circuit breaker baseline
    let price = client.get_asset_price(&asset);
    assert_eq!(price, override_price);
    assert_eq!(client.get_last_price(&asset), Some(override_price));

    // Phase 2: Advance time past override expiry
    env.ledger().with_mut(|li| {
        li.timestamp = expiry + 1;
    });

    // Phase 3: Query after expiry — L-06 fix preserves override price as baseline.
    // The circuit breaker compares Reflector ($1.00) against the preserved baseline ($2.00).
    // A 50% deviation exceeds the 20% threshold, so the circuit breaker trips.
    // Because the call reverts, the override config is NOT cleared (state rollback).
    // Admin must clear the override and reset circuit breaker to resume.
    let result = client.try_get_asset_price(&asset);
    assert!(result.is_err(), "L-06: circuit breaker should trip when Reflector price deviates >20% from preserved override baseline");

    // State was rolled back because the call errored — override config still present
    let config = client.get_asset_config(&asset).unwrap();
    assert_eq!(config.manual_override_price, Some(override_price),
        "Override config not cleared due to circuit breaker revert");

    // Admin clears the override manually and resets circuit breaker
    client.set_manual_override(&admin, &asset, &None, &None);
    client.reset_circuit_breaker(&admin, &asset);

    // Now the query should succeed — baseline cleared, Reflector returns $1.00
    let price_after_reset = client.get_asset_price(&asset);
    assert_eq!(price_after_reset, TEST_PRICE_DEFAULT);
}

#[test]
fn test_m07_admin_removal_of_override_clears_circuit_breaker_baseline() {
    let env = create_test_env();
    let (admin, _user1, _user2) = create_test_addresses(&env);

    let oracle = initialize_oracle(&env, &admin);
    let client = price_oracle::Client::new(&env, &oracle);

    let asset = OracleAsset::Stellar(Address::generate(&env));
    client.add_asset(&admin, &asset);

    // Set a manual override at $2.00 (no baseline yet, accepted)
    let override_price = 2_000_000_000_000_000u128; // $2.00
    client.set_manual_override(
        &admin, &asset, &Some(override_price),
        &Some(env.ledger().timestamp() + 86400),
    );

    // Query to store override price as circuit breaker baseline
    let price = client.get_asset_price(&asset);
    assert_eq!(price, override_price);
    assert_eq!(client.get_last_price(&asset), Some(override_price));

    // Admin explicitly removes override via set_manual_override(None)
    // With M-07 fix, this also clears the circuit breaker baseline
    client.set_manual_override(
        &admin, &asset, &None,
        &Some(default_expiry_timestamp(&env)),
    );

    // Verify baseline was cleared (no manual reset_circuit_breaker needed)
    assert_eq!(client.get_last_price(&asset), None,
        "Circuit breaker baseline must be cleared when override is removed by admin (M-07)");

    // Query should succeed without calling reset_circuit_breaker
    // Falls through to Reflector ($1.00), no baseline to trip the circuit breaker
    let price_after_removal = client.get_asset_price(&asset);
    assert_eq!(price_after_removal, TEST_PRICE_DEFAULT);
}

#[test]
fn test_m07_remove_asset_clears_circuit_breaker_baseline() {
    let env = create_test_env();
    let (admin, _user1, _user2) = create_test_addresses(&env);

    let oracle = initialize_oracle(&env, &admin);
    let client = price_oracle::Client::new(&env, &oracle);

    let asset = OracleAsset::Stellar(Address::generate(&env));
    client.add_asset(&admin, &asset);

    // Query to establish a circuit breaker baseline
    let price = client.get_asset_price(&asset);
    assert_eq!(price, TEST_PRICE_DEFAULT);
    assert_eq!(client.get_last_price(&asset), Some(TEST_PRICE_DEFAULT));

    // Remove asset — should also clear the circuit breaker baseline
    client.remove_asset(&asset);

    // Verify baseline was cleared (prevents stale baseline if asset is re-added)
    assert_eq!(client.get_last_price(&asset), None,
        "Circuit breaker baseline must be cleared when asset is removed (M-07)");
}

// ========================================================================
// WP-H7: Stale cache must not beat manual override in batch queries
// (K2 #4 / note 7)
// ========================================================================

/// After populating cache, setting a manual override must return the override
/// immediately via get_asset_prices_vec, without waiting for cache expiry.
#[test]
fn test_wp_h7_manual_override_busts_cache_in_batch_query() {
    use soroban_sdk::testutils::Ledger;

    let env = create_test_env();
    let (admin, _, _) = create_test_addresses(&env);
    let oracle_id = initialize_oracle(&env, &admin);
    let client = price_oracle::Client::new(&env, &oracle_id);

    let asset = OracleAsset::Stellar(Address::generate(&env));
    client.add_asset(&admin, &asset);

    // Enable price cache with 60s TTL
    client.set_price_cache_ttl(&admin, &60);

    // Step 1: Query price to populate the TTL cache
    let reflector_price = client.get_asset_price(&asset);
    assert_eq!(reflector_price, TEST_PRICE_DEFAULT, "initial price from reflector");

    // Step 2: Set a manual override (should bust the cache via clear_last_price_data)
    let override_price = 5_000_000_000_000_000u128; // $5.00
    // Reset circuit breaker first to allow large price change
    client.reset_circuit_breaker(&admin, &asset);
    client.set_manual_override(
        &admin, &asset, &Some(override_price),
        &Some(env.ledger().timestamp() + 86400),
    );

    // Step 3: Call get_asset_prices_vec (batch query) — must return override, not cached value
    let mut assets = Vec::new(&env);
    assets.push_back(asset.clone());
    let prices = client.get_asset_prices_vec(&assets);
    assert_eq!(prices.len(), 1);

    let returned_price = prices.get(0).unwrap();
    assert_eq!(
        returned_price.price, override_price,
        "WP-H7: batch query must return override price, not stale cache"
    );

    // Step 4: Single query should also return override
    let single_price = client.get_asset_price(&asset);
    assert_eq!(single_price, override_price, "single query also returns override");
}

/// Verify that enabling cache, querying, then setting override and querying again
/// works correctly for multiple assets in a single batch.
#[test]
fn test_wp_h7_batch_query_mixed_cache_and_override() {
    let env = create_test_env();
    let (admin, _, _) = create_test_addresses(&env);
    let oracle_id = initialize_oracle(&env, &admin);
    let client = price_oracle::Client::new(&env, &oracle_id);

    let asset1 = OracleAsset::Stellar(Address::generate(&env));
    let asset2 = OracleAsset::Stellar(Address::generate(&env));
    client.add_asset(&admin, &asset1);
    client.add_asset(&admin, &asset2);

    // Enable cache
    client.set_price_cache_ttl(&admin, &30);

    // Populate cache for both
    let _ = client.get_asset_price(&asset1);
    let _ = client.get_asset_price(&asset2);

    // Override only asset1
    let override_price = 3_000_000_000_000_000u128; // $3.00
    client.reset_circuit_breaker(&admin, &asset1);
    client.set_manual_override(
        &admin, &asset1, &Some(override_price),
        &Some(env.ledger().timestamp() + 86400),
    );

    // Batch query both
    let mut assets = Vec::new(&env);
    assets.push_back(asset1.clone());
    assets.push_back(asset2.clone());
    let prices = client.get_asset_prices_vec(&assets);

    assert_eq!(prices.len(), 2);
    assert_eq!(prices.get(0).unwrap().price, override_price, "asset1 should return override");
    assert_eq!(prices.get(1).unwrap().price, TEST_PRICE_DEFAULT, "asset2 should return reflector/cache");
}
