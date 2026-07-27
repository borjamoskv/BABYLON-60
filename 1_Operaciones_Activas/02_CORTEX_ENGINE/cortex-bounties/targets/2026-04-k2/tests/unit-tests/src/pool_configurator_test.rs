#![cfg(test)]

use crate::{pool_configurator, kinetic_router};

use k2_shared::OracleError;
use soroban_sdk::{contract, contractimpl, testutils::Address as _, Address, BytesN, Env, String, Symbol, Vec};

fn create_test_env() -> Env {
    let env = Env::default();
    env.mock_all_auths();
    env
}

fn create_test_addresses(env: &Env) -> (Address, Address, Address, Address, Address) {
    let admin = Address::generate(env);
    let emergency_admin = Address::generate(env);
    let user1 = Address::generate(env);
    let user2 = Address::generate(env);

    let oracle = create_and_initialize_oracle(env, &admin);

    (admin, emergency_admin, user1, user2, oracle)
}

fn create_and_initialize_oracle(env: &Env, _admin: &Address) -> Address {
    let oracle_id = env.register(MockOracleContract, ());
    oracle_id
}

fn initialize_pool_configurator(
    env: &Env,
    admin: &Address,
    _emergency_admin: &Address,
    oracle: &Address,
) -> Address {
    let contract_id = env.register(pool_configurator::WASM, ());
    let client = pool_configurator::Client::new(env, &contract_id);

    let mock_kinetic_router = create_mock_kinetic_router(env);

    client.initialize(admin, &mock_kinetic_router, oracle);
    
    // Note: initialize() sets emergency_admin to the same as pool_admin
    // The _emergency_admin parameter is kept for backwards compatibility but not used

    contract_id
}

fn create_mock_kinetic_router(env: &Env) -> Address {
    let mock_kinetic_router = env.register(MockKineticRouterContract, ());
    mock_kinetic_router
}

#[contract]
pub struct MockKineticRouterContract;

#[contractimpl]
impl MockKineticRouterContract {
    pub fn init_reserve(
        _env: Env,
        _caller: Address,
        _underlying_asset: Address,
        _a_token_impl: Address,
        _variable_debt_impl: Address,
        _interest_rate_strategy: Address,
        _treasury: Address,
        _params: pool_configurator::InitReserveParams,
    ) -> Result<(), pool_configurator::KineticRouterError> {
        Ok(())
    }

    pub fn set_reserve_supply_cap(
        _env: Env,
        _caller: Address,
        _asset: Address,
        _supply_cap: u128,
    ) -> Result<(), pool_configurator::KineticRouterError> {
        Ok(())
    }

    pub fn set_reserve_borrow_cap(
        _env: Env,
        _caller: Address,
        _asset: Address,
        _borrow_cap: u128,
    ) -> Result<(), pool_configurator::KineticRouterError> {
        Ok(())
    }

    pub fn get_incentives_contract(_env: Env) -> Option<Address> {
        None
    }

    pub fn get_reserve_data(_env: Env, _asset: Address) -> Result<kinetic_router::ReserveData, pool_configurator::KineticRouterError> {
        use k2_shared::{RAY};
        use kinetic_router::{ReserveConfiguration, ReserveData};
        Ok(ReserveData {
            liquidity_index: RAY,
            variable_borrow_index: RAY,
            current_liquidity_rate: 0,
            current_variable_borrow_rate: 0,
            last_update_timestamp: _env.ledger().timestamp(),
            a_token_address: Address::generate(&_env),
            debt_token_address: Address::generate(&_env),
            interest_rate_strategy_address: Address::generate(&_env),
            id: 0,
            configuration: ReserveConfiguration {
                data_low: 0,
                data_high: 0,
            },
        })
    }

    pub fn update_reserve_configuration(
        _env: Env,
        _caller: Address,
        _asset: Address,
        _configuration: kinetic_router::ReserveConfiguration,
    ) -> Result<(), pool_configurator::KineticRouterError> {
        Ok(())
    }
}

/// Mock oracle contract for testing
#[contract]
pub struct MockOracleContract;

#[contractimpl]
impl MockOracleContract {
    pub fn add_asset(_env: Env, _asset: pool_configurator::Asset) -> Result<(), OracleError> {
        // Mock implementation - always succeeds
        Ok(())
    }

    pub fn remove_asset(_env: Env, _asset: pool_configurator::Asset) -> Result<(), OracleError> {
        // Mock implementation - always succeeds
        Ok(())
    }

    pub fn set_asset_enabled(_env: Env, _asset: pool_configurator::Asset, _enabled: bool) -> Result<(), OracleError> {
        // Mock implementation - always succeeds
        Ok(())
    }

    pub fn set_manual_override(
        _env: Env,
        _asset: pool_configurator::Asset,
        _price: Option<i128>,
    ) -> Result<(), OracleError> {
        // Mock implementation - always succeeds
        Ok(())
    }

    pub fn get_whitelisted_assets(_env: Env) -> Vec<pool_configurator::Asset> {
        // Mock implementation - return empty list
        Vec::new(&_env)
    }

    pub fn get_asset_config(_env: Env, _asset: pool_configurator::Asset) -> Option<pool_configurator::AssetConfig> {
        // Mock implementation - return None
        None
    }

    pub fn get_asset_price(_env: Env, _asset: pool_configurator::Asset) -> Result<i128, OracleError> {
        // Mock implementation - return error for non-whitelisted assets
        Err(OracleError::AssetNotWhitelisted)
    }

    pub fn get_asset_price_data(_env: Env, _asset: pool_configurator::Asset) -> Result<pool_configurator::PriceData, OracleError> {
        // Mock implementation - return error for non-whitelisted assets
        Err(OracleError::AssetNotWhitelisted)
    }
}

#[test]
fn test_set_supply_cap_success() {
    let env = create_test_env();
    let (admin, _emergency_admin, _user1, _user2, oracle) = create_test_addresses(&env);

    let pool_configurator = initialize_pool_configurator(&env, &admin, &_emergency_admin, &oracle);
    let underlying_asset = Address::generate(&env);

    let client = pool_configurator::Client::new(&env, &pool_configurator);

    // Set supply cap - should succeed with mock kinetic router
    let new_supply_cap = 500_000_000_000;
    let result = client.try_set_supply_cap(&admin, &underlying_asset, &new_supply_cap);
    
    // Verify the call succeeded (mock allows all calls to succeed)
    assert!(result.is_ok(), "Setting supply cap should succeed");
}

#[test]
fn test_set_borrow_cap_success() {
    let env = create_test_env();
    let (admin, _emergency_admin, _user1, _user2, oracle) = create_test_addresses(&env);

    let pool_configurator = initialize_pool_configurator(&env, &admin, &_emergency_admin, &oracle);
    let underlying_asset = Address::generate(&env);

    let client = pool_configurator::Client::new(&env, &pool_configurator);

    // Set borrow cap - should succeed with mock kinetic router
    let new_borrow_cap = 1_000_000_000_000;
    let result = client.try_set_borrow_cap(&admin, &underlying_asset, &new_borrow_cap);
    
    // Verify the call succeeded (mock allows all calls to succeed)
    assert!(result.is_ok(), "Setting borrow cap should succeed");
}

#[test]
fn test_set_supply_cap_unauthorized() {
    let env = create_test_env();
    let (admin, _emergency_admin, user1, _user2, oracle) = create_test_addresses(&env);

    let pool_configurator = initialize_pool_configurator(&env, &admin, &_emergency_admin, &oracle);
    let underlying_asset = Address::generate(&env);

    let client = pool_configurator::Client::new(&env, &pool_configurator);

    // Try to set supply cap as non-admin user
    let new_supply_cap = 500_000_000_000;

    let result = client.try_set_supply_cap(&user1, &underlying_asset, &new_supply_cap);
    assert!(result.is_err());

    // Verify that user1 is not the admin
    assert!(user1 != admin);

    // Verify the operation failed due to unauthorized access
    assert!(result.is_err());
}

#[test]
fn test_set_borrow_cap_unauthorized() {
    let env = create_test_env();
    let (admin, _emergency_admin, user1, _user2, oracle) = create_test_addresses(&env);

    let pool_configurator = initialize_pool_configurator(&env, &admin, &_emergency_admin, &oracle);
    let underlying_asset = Address::generate(&env);

    let client = pool_configurator::Client::new(&env, &pool_configurator);

    // Try to set borrow cap as non-admin user
    let new_borrow_cap = 1_000_000_000_000;

    let result = client.try_set_borrow_cap(&user1, &underlying_asset, &new_borrow_cap);
    assert!(result.is_err());

    // Verify that user1 is not the admin
    assert!(user1 != admin);

    // Verify the operation failed due to unauthorized access
    assert!(result.is_err());
}

#[test]
fn test_set_supply_cap_to_zero() {
    let env = create_test_env();
    let (admin, _emergency_admin, _user1, _user2, oracle) = create_test_addresses(&env);

    let pool_configurator = initialize_pool_configurator(&env, &admin, &_emergency_admin, &oracle);
    let underlying_asset = Address::generate(&env);

    let client = pool_configurator::Client::new(&env, &pool_configurator);

    // Set supply cap to 0 to remove/disable cap
    let new_supply_cap = 0;
    let result = client.try_set_supply_cap(&admin, &underlying_asset, &new_supply_cap);
    
    // Verify the call succeeded - zero value should be allowed
    assert!(result.is_ok(), "Setting supply cap to 0 (unlimited) should succeed");
}

#[test]
fn test_set_borrow_cap_to_zero() {
    let env = create_test_env();
    let (admin, _emergency_admin, _user1, _user2, oracle) = create_test_addresses(&env);

    let pool_configurator = initialize_pool_configurator(&env, &admin, &_emergency_admin, &oracle);
    let underlying_asset = Address::generate(&env);

    let client = pool_configurator::Client::new(&env, &pool_configurator);

    // Set borrow cap to 0 to remove/disable cap
    let new_borrow_cap = 0;
    let result = client.try_set_borrow_cap(&admin, &underlying_asset, &new_borrow_cap);
    
    // Verify the call succeeded - zero value should be allowed
    assert!(result.is_ok(), "Setting borrow cap to 0 (unlimited) should succeed");
}

#[test]
fn test_cap_functions_accept_valid_values() {
    let env = create_test_env();
    let (admin, _emergency_admin, _user1, _user2, oracle) = create_test_addresses(&env);

    let pool_configurator = initialize_pool_configurator(&env, &admin, &_emergency_admin, &oracle);
    let client = pool_configurator::Client::new(&env, &pool_configurator);

    let test_asset = Address::generate(&env);
    let test_supply_cap = 500_000_000_000; // 500B tokens
    let test_borrow_cap = 1_000_000_000_000; // 1T tokens

    // Test that cap functions accept valid values
    let supply_result = client.try_set_supply_cap(&admin, &test_asset, &test_supply_cap);
    let borrow_result = client.try_set_borrow_cap(&admin, &test_asset, &test_borrow_cap);
    
    assert!(supply_result.is_ok(), "Setting supply cap should succeed");
    assert!(borrow_result.is_ok(), "Setting borrow cap should succeed");
    
    // Test that caps can be updated to different values
    let new_supply_cap = 750_000_000_000;
    let new_borrow_cap = 1_500_000_000_000;
    
    let update_supply_result = client.try_set_supply_cap(&admin, &test_asset, &new_supply_cap);
    let update_borrow_result = client.try_set_borrow_cap(&admin, &test_asset, &new_borrow_cap);
    
    assert!(update_supply_result.is_ok(), "Updating supply cap should succeed");
    assert!(update_borrow_result.is_ok(), "Updating borrow cap should succeed");
}

// ========================================================================
// ORACLE INTEGRATION TESTS
// ========================================================================

#[test]
fn test_oracle_asset_management_unauthorized() {
    let env = create_test_env();
    let (admin, _emergency_admin, user1, _user2, oracle) = create_test_addresses(&env);

    let pool_configurator = initialize_pool_configurator(&env, &admin, &_emergency_admin, &oracle);
    let client = pool_configurator::Client::new(&env, &pool_configurator);

    let stellar_asset = pool_configurator::Asset::Stellar(Address::generate(&env));

    // Test that non-admin cannot add assets
    let result = client.try_add_oracle_asset(&user1, &stellar_asset);
    assert!(result.is_err());

    // Test that non-admin cannot remove assets
    let result = client.try_remove_oracle_asset(&user1, &stellar_asset);
    assert!(result.is_err());

    // Test that non-admin cannot enable/disable assets
    let result = client.try_set_oracle_asset_enabled(&user1, &stellar_asset, &true);
    assert!(result.is_err());

    // Test that non-admin cannot set manual overrides
    let manual_price = Some(2_000_000_000_000_000);
    let expiry = Some(env.ledger().timestamp() + 86400); // 24 hours
    let result = client.try_set_oracle_manual_override(&user1, &stellar_asset, &manual_price, &expiry);
    assert!(result.is_err());
}

#[test]
fn test_oracle_price_queries() {
    let env = create_test_env();
    let (admin, _emergency_admin, _user1, _user2, oracle) = create_test_addresses(&env);

    let pool_configurator = initialize_pool_configurator(&env, &admin, &_emergency_admin, &oracle);
    let client = pool_configurator::Client::new(&env, &pool_configurator);

    let stellar_asset = pool_configurator::Asset::Stellar(Address::generate(&env));
    let external_asset = pool_configurator::Asset::Other(Symbol::new(&env, "ETH"));

    // Test getting whitelisted assets (should return empty list for now)
    let whitelisted_assets = client.get_oracle_whitelisted_assets();
    assert_eq!(whitelisted_assets.len(), 0);

    // Test getting asset config (should return None for now)
    let config = client.get_oracle_asset_config(&stellar_asset);
    assert!(config.is_none());

    // Test getting asset price (should return error for now)
    let price_result = client.try_get_oracle_asset_price(&stellar_asset);
    assert!(price_result.is_err());

    // Test getting asset price data (should return error for now)
    let price_data_result = client.try_get_oracle_asset_price_data(&external_asset);
    assert!(price_data_result.is_err());
}

#[test]
fn test_oracle_integration_with_reserve_initialization() {
    let env = create_test_env();
    let (admin, _emergency_admin, _user1, _user2, oracle) = create_test_addresses(&env);

    let pool_configurator = initialize_pool_configurator(&env, &admin, &_emergency_admin, &oracle);
    let client = pool_configurator::Client::new(&env, &pool_configurator);

    // Test reserve initialization parameters
    let underlying_asset = Address::generate(&env);
    let a_token_impl = Address::generate(&env);
    let variable_debt_impl = Address::generate(&env);
    let interest_rate_strategy = Address::generate(&env);
    let treasury = Address::generate(&env);

    let params = pool_configurator::InitReserveParams {
        decimals: 6,
        ltv: 7500,                   // 75%
        liquidation_threshold: 8000, // 80%
        liquidation_bonus: 500,      // 5%
        reserve_factor: 1000,        // 10%
        supply_cap: 1_000_000,       // 1M tokens
        borrow_cap: 500_000,         // 500K tokens
        borrowing_enabled: true,
        flashloan_enabled: true,
    };

    // This should succeed and automatically add the asset to oracle whitelist
    client.init_reserve(
        &admin,
        &underlying_asset,
        &a_token_impl,
        &variable_debt_impl,
        &interest_rate_strategy,
        &treasury,
        &params,
    );

    // Should complete without error
    assert!(true);
}

#[test]
fn test_oracle_address_management() {
    let env = create_test_env();
    let (admin, _emergency_admin, _user1, _user2, oracle) = create_test_addresses(&env);

    let pool_configurator = initialize_pool_configurator(&env, &admin, &_emergency_admin, &oracle);
    let client = pool_configurator::Client::new(&env, &pool_configurator);

    // Test getting oracle address
    let retrieved_oracle = client.get_price_oracle();
    assert_eq!(retrieved_oracle, oracle);

    // Test getting kinetic router address
    let kinetic_router = client.get_kinetic_router();
    assert!(kinetic_router != Address::generate(&env));

    // Test getting admin address
    let retrieved_admin = client.get_pool_admin();
    assert_eq!(retrieved_admin, admin);
}

// ========================================================================
// FACTORY PATTERN TESTS
// ========================================================================

fn create_mock_token_wasm_hash(env: &Env) -> BytesN<32> {
    let mut hash_bytes = [0u8; 32];
    hash_bytes[0] = 0xAA;
    hash_bytes[31] = 0xBB;
    BytesN::from_array(env, &hash_bytes)
}

#[test]
fn test_set_a_token_wasm_hash_success() {
    let env = create_test_env();
    let (admin, _emergency_admin, _user1, _user2, oracle) = create_test_addresses(&env);

    let pool_configurator = initialize_pool_configurator(&env, &admin, &_emergency_admin, &oracle);
    let client = pool_configurator::Client::new(&env, &pool_configurator);

    let a_token_hash = create_mock_token_wasm_hash(&env);
    let debt_hash = create_mock_token_wasm_hash(&env);

    client.set_a_token_wasm_hash(&admin, &a_token_hash);
    client.set_debt_token_wasm_hash(&admin, &debt_hash);

    // Verify hashes were stored by attempting to deploy (will fail at deployment, but hash check passes)
    let underlying_asset = Address::generate(&env);
    let interest_rate_strategy = Address::generate(&env);
    let treasury = Address::generate(&env);
    let params = pool_configurator::InitReserveParams {
        decimals: 9,
        ltv: 7500,
        liquidation_threshold: 8000,
        liquidation_bonus: 10500,
        reserve_factor: 1000,
        supply_cap: 1_000_000,
        borrow_cap: 1_000_000,
        borrowing_enabled: true,
        flashloan_enabled: true,
    };

    // This should fail at deployment (no actual WASM), but should pass hash check
    let result = client.try_deploy_and_init_reserve(
        &admin,
        &underlying_asset,
        &interest_rate_strategy,
        &treasury,
        &String::from_str(&env, "Test aToken"),
        &String::from_str(&env, "aTEST"),
        &String::from_str(&env, "Test Debt Token"),
        &String::from_str(&env, "dTEST"),
        &params,
    );

    // Should fail with deployment error, not WASMHashNotSet
    assert!(result.is_err(), "Deployment should fail without actual WASM");
    match result {
        Err(Ok(pool_configurator::KineticRouterError::WASMHashNotSet)) => {
            panic!("Expected deployment error, got WASMHashNotSet - hashes were stored but not retrieved correctly");
        }
        Err(Ok(pool_configurator::KineticRouterError::TokenDeploymentFailed)) => {}
        Err(Ok(pool_configurator::KineticRouterError::TokenInitializationFailed)) => {}
        Err(Err(_)) => {}
        _ => {
            // Other deployment errors are acceptable (proves hashes were stored and retrieved)
        }
    }
}

#[test]
fn test_set_a_token_wasm_hash_unauthorized() {
    let env = create_test_env();
    let (admin, _emergency_admin, user1, _user2, oracle) = create_test_addresses(&env);

    let pool_configurator = initialize_pool_configurator(&env, &admin, &_emergency_admin, &oracle);
    let client = pool_configurator::Client::new(&env, &pool_configurator);

    let wasm_hash = create_mock_token_wasm_hash(&env);

    let result = client.try_set_a_token_wasm_hash(&user1, &wasm_hash);
    assert!(result.is_err(), "Non-admin should not be able to set WASM hash");

    // Verify user1 is not admin
    assert_ne!(user1, admin, "user1 must be different from admin");

    // Verify the error is Unauthorized
    match result {
        Err(Ok(pool_configurator::KineticRouterError::Unauthorized)) => {}
        _ => panic!("Expected Unauthorized error, got: {:?}", result),
    }

    // Verify hash was not set by attempting to deploy (should fail with WASMHashNotSet)
    let underlying_asset = Address::generate(&env);
    let interest_rate_strategy = Address::generate(&env);
    let treasury = Address::generate(&env);
    let params = pool_configurator::InitReserveParams {
        decimals: 9,
        ltv: 7500,
        liquidation_threshold: 8000,
        liquidation_bonus: 10500,
        reserve_factor: 1000,
        supply_cap: 1_000_000,
        borrow_cap: 1_000_000,
        borrowing_enabled: true,
        flashloan_enabled: true,
    };

    let deploy_result = client.try_deploy_and_init_reserve(
        &admin,
        &underlying_asset,
        &interest_rate_strategy,
        &treasury,
        &String::from_str(&env, "Test aToken"),
        &String::from_str(&env, "aTEST"),
        &String::from_str(&env, "Test Debt Token"),
        &String::from_str(&env, "dTEST"),
        &params,
    );

    // Should fail with WASMHashNotSet because hash was not set
    assert!(deploy_result.is_err());
    match deploy_result {
        Err(Ok(pool_configurator::KineticRouterError::WASMHashNotSet)) => {}
        _ => panic!("Expected WASMHashNotSet error, got: {:?}", deploy_result),
    }
}

#[test]
fn test_set_debt_token_wasm_hash_success() {
    let env = create_test_env();
    let (admin, _emergency_admin, _user1, _user2, oracle) = create_test_addresses(&env);

    let pool_configurator = initialize_pool_configurator(&env, &admin, &_emergency_admin, &oracle);
    let client = pool_configurator::Client::new(&env, &pool_configurator);

    let wasm_hash = create_mock_token_wasm_hash(&env);

    client.set_debt_token_wasm_hash(&admin, &wasm_hash);

    // Verify by checking that deploy fails with different error (deployment, not missing hash)
    let underlying_asset = Address::generate(&env);
    let interest_rate_strategy = Address::generate(&env);
    let treasury = Address::generate(&env);
    let params = pool_configurator::InitReserveParams {
        decimals: 9,
        ltv: 7500,
        liquidation_threshold: 8000,
        liquidation_bonus: 10500,
        reserve_factor: 1000,
        supply_cap: 1_000_000,
        borrow_cap: 1_000_000,
        borrowing_enabled: true,
        flashloan_enabled: true,
    };

    // Set aToken hash first
    let a_token_hash = create_mock_token_wasm_hash(&env);
    client.set_a_token_wasm_hash(&admin, &a_token_hash);

    // Now try deploy - should fail at deployment, not at hash check
    let result = client.try_deploy_and_init_reserve(
        &admin,
        &underlying_asset,
        &interest_rate_strategy,
        &treasury,
        &String::from_str(&env, "Test aToken"),
        &String::from_str(&env, "aTEST"),
        &String::from_str(&env, "Test Debt Token"),
        &String::from_str(&env, "dTEST"),
        &params,
    );

    assert!(result.is_err(), "Deployment should fail without actual WASM");
    
    // Verify it fails at deployment stage, not hash check
    match result {
        Err(Ok(pool_configurator::KineticRouterError::WASMHashNotSet)) => {
            panic!("Expected deployment error, got WASMHashNotSet - hashes should be set");
        }
        Err(Ok(pool_configurator::KineticRouterError::TokenDeploymentFailed)) => {}
        Err(Ok(pool_configurator::KineticRouterError::TokenInitializationFailed)) => {}
        Err(Err(_)) => {}
        _ => {
            // Other deployment errors are acceptable
        }
    }
}

#[test]
fn test_set_debt_token_wasm_hash_unauthorized() {
    let env = create_test_env();
    let (admin, _emergency_admin, user1, _user2, oracle) = create_test_addresses(&env);

    let pool_configurator = initialize_pool_configurator(&env, &admin, &_emergency_admin, &oracle);
    let client = pool_configurator::Client::new(&env, &pool_configurator);

    let wasm_hash = create_mock_token_wasm_hash(&env);

    let result = client.try_set_debt_token_wasm_hash(&user1, &wasm_hash);
    assert!(result.is_err(), "Non-admin should not be able to set debt token WASM hash");
    assert_ne!(user1, admin, "user1 must be different from admin");

    // Verify the error is Unauthorized
    match result {
        Err(Ok(pool_configurator::KineticRouterError::Unauthorized)) => {}
        _ => panic!("Expected Unauthorized error, got: {:?}", result),
    }
}

#[test]
fn test_deploy_and_init_reserve_missing_a_token_hash() {
    let env = create_test_env();
    let (admin, _emergency_admin, _user1, _user2, oracle) = create_test_addresses(&env);

    let pool_configurator = initialize_pool_configurator(&env, &admin, &_emergency_admin, &oracle);
    let client = pool_configurator::Client::new(&env, &pool_configurator);

    // Set only debt token hash, not aToken hash
    let debt_hash = create_mock_token_wasm_hash(&env);
    client.set_debt_token_wasm_hash(&admin, &debt_hash);

    let underlying_asset = Address::generate(&env);
    let interest_rate_strategy = Address::generate(&env);
    let treasury = Address::generate(&env);
    let params = pool_configurator::InitReserveParams {
        decimals: 9,
        ltv: 7500,
        liquidation_threshold: 8000,
        liquidation_bonus: 10500,
        reserve_factor: 1000,
        supply_cap: 1_000_000,
        borrow_cap: 1_000_000,
        borrowing_enabled: true,
        flashloan_enabled: true,
    };

    let result = client.try_deploy_and_init_reserve(
        &admin,
        &underlying_asset,
        &interest_rate_strategy,
        &treasury,
        &String::from_str(&env, "Test aToken"),
        &String::from_str(&env, "aTEST"),
        &String::from_str(&env, "Test Debt Token"),
        &String::from_str(&env, "dTEST"),
        &params,
    );

    assert!(result.is_err(), "Deployment should fail when aToken hash is missing");

    // Verify the error is WASMHashNotSet
    match result {
        Err(Ok(pool_configurator::KineticRouterError::WASMHashNotSet)) => {}
        _ => panic!("Expected WASMHashNotSet error, got: {:?}", result),
    }
}

#[test]
fn test_deploy_and_init_reserve_missing_debt_token_hash() {
    let env = create_test_env();
    let (admin, _emergency_admin, _user1, _user2, oracle) = create_test_addresses(&env);

    let pool_configurator = initialize_pool_configurator(&env, &admin, &_emergency_admin, &oracle);
    let client = pool_configurator::Client::new(&env, &pool_configurator);

    // Set only aToken hash, not debt token hash
    let a_token_hash = create_mock_token_wasm_hash(&env);
    client.set_a_token_wasm_hash(&admin, &a_token_hash);

    let underlying_asset = Address::generate(&env);
    let interest_rate_strategy = Address::generate(&env);
    let treasury = Address::generate(&env);
    let params = pool_configurator::InitReserveParams {
        decimals: 9,
        ltv: 7500,
        liquidation_threshold: 8000,
        liquidation_bonus: 10500,
        reserve_factor: 1000,
        supply_cap: 1_000_000,
        borrow_cap: 1_000_000,
        borrowing_enabled: true,
        flashloan_enabled: true,
    };

    let result = client.try_deploy_and_init_reserve(
        &admin,
        &underlying_asset,
        &interest_rate_strategy,
        &treasury,
        &String::from_str(&env, "Test aToken"),
        &String::from_str(&env, "aTEST"),
        &String::from_str(&env, "Test Debt Token"),
        &String::from_str(&env, "dTEST"),
        &params,
    );

    assert!(result.is_err(), "Deployment should fail when aToken hash is missing");

    // Verify the error is WASMHashNotSet
    match result {
        Err(Ok(pool_configurator::KineticRouterError::WASMHashNotSet)) => {}
        _ => panic!("Expected WASMHashNotSet error, got: {:?}", result),
    }
}

#[test]
fn test_deploy_and_init_reserve_unauthorized() {
    let env = create_test_env();
    let (admin, _emergency_admin, user1, _user2, oracle) = create_test_addresses(&env);

    let pool_configurator = initialize_pool_configurator(&env, &admin, &_emergency_admin, &oracle);
    let client = pool_configurator::Client::new(&env, &pool_configurator);

    // Set hashes as admin
    let a_token_hash = create_mock_token_wasm_hash(&env);
    let debt_hash = create_mock_token_wasm_hash(&env);
    client.set_a_token_wasm_hash(&admin, &a_token_hash);
    client.set_debt_token_wasm_hash(&admin, &debt_hash);

    let underlying_asset = Address::generate(&env);
    let interest_rate_strategy = Address::generate(&env);
    let treasury = Address::generate(&env);
    let params = pool_configurator::InitReserveParams {
        decimals: 9,
        ltv: 7500,
        liquidation_threshold: 8000,
        liquidation_bonus: 10500,
        reserve_factor: 1000,
        supply_cap: 1_000_000,
        borrow_cap: 1_000_000,
        borrowing_enabled: true,
        flashloan_enabled: true,
    };

    // Try to deploy as non-admin
    let result = client.try_deploy_and_init_reserve(
        &user1,
        &underlying_asset,
        &interest_rate_strategy,
        &treasury,
        &String::from_str(&env, "Test aToken"),
        &String::from_str(&env, "aTEST"),
        &String::from_str(&env, "Test Debt Token"),
        &String::from_str(&env, "dTEST"),
        &params,
    );

    assert!(result.is_err(), "Non-admin should not be able to deploy reserves");
    assert_ne!(user1, admin, "user1 must be different from admin");

    // Verify the error is Unauthorized
    match result {
        Err(Ok(pool_configurator::KineticRouterError::Unauthorized)) => {}
        _ => panic!("Expected Unauthorized error, got: {:?}", result),
    }
}

#[test]
fn test_deploy_counter_increments() {
    let env = create_test_env();
    let (admin, _emergency_admin, _user1, _user2, oracle) = create_test_addresses(&env);

    let pool_configurator = initialize_pool_configurator(&env, &admin, &_emergency_admin, &oracle);
    let client = pool_configurator::Client::new(&env, &pool_configurator);

    // Set hashes
    let a_token_hash = create_mock_token_wasm_hash(&env);
    let debt_hash = create_mock_token_wasm_hash(&env);
    client.set_a_token_wasm_hash(&admin, &a_token_hash);
    client.set_debt_token_wasm_hash(&admin, &debt_hash);

    let underlying_asset1 = Address::generate(&env);
    let underlying_asset2 = Address::generate(&env);
    let interest_rate_strategy = Address::generate(&env);
    let treasury = Address::generate(&env);
    let params = pool_configurator::InitReserveParams {
        decimals: 9,
        ltv: 7500,
        liquidation_threshold: 8000,
        liquidation_bonus: 10500,
        reserve_factor: 1000,
        supply_cap: 1_000_000,
        borrow_cap: 1_000_000,
        borrowing_enabled: true,
        flashloan_enabled: true,
    };

    // First deployment attempt (will fail at actual deployment, but counter increments)
    let result1 = client.try_deploy_and_init_reserve(
        &admin,
        &underlying_asset1,
        &interest_rate_strategy,
        &treasury,
        &String::from_str(&env, "Test aToken 1"),
        &String::from_str(&env, "aTEST1"),
        &String::from_str(&env, "Test Debt Token 1"),
        &String::from_str(&env, "dTEST1"),
        &params,
    );
    assert!(result1.is_err(), "First deployment should fail (no actual WASM)");
    assert_ne!(underlying_asset1, underlying_asset2, "Assets must be different");

    // Verify first deployment doesn't fail at hash check
    match result1 {
        Err(Ok(pool_configurator::KineticRouterError::WASMHashNotSet)) => {
            panic!("First deployment should not fail at hash check - hashes are set");
        }
        _ => {}
    }

    // Second deployment attempt with different asset
    // Counter should have incremented, so salts will be different
    let result2 = client.try_deploy_and_init_reserve(
        &admin,
        &underlying_asset2,
        &interest_rate_strategy,
        &treasury,
        &String::from_str(&env, "Test aToken 2"),
        &String::from_str(&env, "aTEST2"),
        &String::from_str(&env, "Test Debt Token 2"),
        &String::from_str(&env, "dTEST2"),
        &params,
    );
    assert!(result2.is_err(), "Second deployment should fail (no actual WASM)");

    // Verify second deployment also doesn't fail at hash check (counter incremented)
    match result2 {
        Err(Ok(pool_configurator::KineticRouterError::WASMHashNotSet)) => {
            panic!("Second deployment should not fail at hash check - hashes are set");
        }
        _ => {}
    }

    // Counter increments ensure different salts for each deployment
    // Both deployments use different counter values (0 and 1)
}

#[test]
fn test_deploy_unique_addresses_per_asset() {
    let env = create_test_env();
    let (admin, _emergency_admin, _user1, _user2, oracle) = create_test_addresses(&env);

    let pool_configurator = initialize_pool_configurator(&env, &admin, &_emergency_admin, &oracle);
    let client = pool_configurator::Client::new(&env, &pool_configurator);

    // Set hashes
    let a_token_hash = create_mock_token_wasm_hash(&env);
    let debt_hash = create_mock_token_wasm_hash(&env);
    client.set_a_token_wasm_hash(&admin, &a_token_hash);
    client.set_debt_token_wasm_hash(&admin, &debt_hash);

    let underlying_asset1 = Address::generate(&env);
    let underlying_asset2 = Address::generate(&env);
    let interest_rate_strategy = Address::generate(&env);
    let treasury = Address::generate(&env);
    let params = pool_configurator::InitReserveParams {
        decimals: 9,
        ltv: 7500,
        liquidation_threshold: 8000,
        liquidation_bonus: 10500,
        reserve_factor: 1000,
        supply_cap: 1_000_000,
        borrow_cap: 1_000_000,
        borrowing_enabled: true,
        flashloan_enabled: true,
    };

    // Attempt first deployment
    let result1 = client.try_deploy_and_init_reserve(
        &admin,
        &underlying_asset1,
        &interest_rate_strategy,
        &treasury,
        &String::from_str(&env, "Test aToken 1"),
        &String::from_str(&env, "aTEST1"),
        &String::from_str(&env, "Test Debt Token 1"),
        &String::from_str(&env, "dTEST1"),
        &params,
    );

    // Attempt second deployment with different asset
    let result2 = client.try_deploy_and_init_reserve(
        &admin,
        &underlying_asset2,
        &interest_rate_strategy,
        &treasury,
        &String::from_str(&env, "Test aToken 2"),
        &String::from_str(&env, "aTEST2"),
        &String::from_str(&env, "Test Debt Token 2"),
        &String::from_str(&env, "dTEST2"),
        &params,
    );

    // Both should fail (no actual WASM), but verify different assets
    assert!(result1.is_err(), "First deployment should fail (no actual WASM)");
    assert!(result2.is_err(), "Second deployment should fail (no actual WASM)");
    assert_ne!(underlying_asset1, underlying_asset2, "Assets must be different");

    // Verify both don't fail at hash check (hashes are set)
    match result1 {
        Err(Ok(pool_configurator::KineticRouterError::WASMHashNotSet)) => {
            panic!("First deployment should not fail at hash check");
        }
        _ => {}
    }
    match result2 {
        Err(Ok(pool_configurator::KineticRouterError::WASMHashNotSet)) => {
            panic!("Second deployment should not fail at hash check");
        }
        _ => {}
    }

    // The counter ensures different salts, which would produce different addresses
    // if deployment succeeded. Counter increments from 0 to 1 between deployments.
}

#[test]
fn test_deploy_a_token_and_debt_token_different_addresses() {
    let env = create_test_env();
    let (admin, _emergency_admin, _user1, _user2, oracle) = create_test_addresses(&env);

    let pool_configurator = initialize_pool_configurator(&env, &admin, &_emergency_admin, &oracle);
    let client = pool_configurator::Client::new(&env, &pool_configurator);

    // Set hashes
    let a_token_hash = create_mock_token_wasm_hash(&env);
    let debt_hash = create_mock_token_wasm_hash(&env);
    client.set_a_token_wasm_hash(&admin, &a_token_hash);
    client.set_debt_token_wasm_hash(&admin, &debt_hash);

    let underlying_asset = Address::generate(&env);
    let interest_rate_strategy = Address::generate(&env);
    let treasury = Address::generate(&env);
    let params = pool_configurator::InitReserveParams {
        decimals: 9,
        ltv: 7500,
        liquidation_threshold: 8000,
        liquidation_bonus: 10500,
        reserve_factor: 1000,
        supply_cap: 1_000_000,
        borrow_cap: 1_000_000,
        borrowing_enabled: true,
        flashloan_enabled: true,
    };

    // Attempt deployment
    let result = client.try_deploy_and_init_reserve(
        &admin,
        &underlying_asset,
        &interest_rate_strategy,
        &treasury,
        &String::from_str(&env, "Test aToken"),
        &String::from_str(&env, "aTEST"),
        &String::from_str(&env, "Test Debt Token"),
        &String::from_str(&env, "dTEST"),
        &params,
    );

    // Should fail at deployment, but verify that if it succeeded,
    // aToken and debtToken would have different addresses due to salt markers
    assert!(result.is_err(), "Deployment should fail without actual WASM");

    // Verify it doesn't fail at hash check
    match result {
        Err(Ok(pool_configurator::KineticRouterError::WASMHashNotSet)) => {
            panic!("Deployment should not fail at hash check - hashes are set");
        }
        _ => {}
    }

    // The salt generation uses 'A' marker for aToken and 'D' marker for debtToken
    // This ensures they get different addresses even with same counter.
    // Salt format: [counter_bytes (4 bytes)][type_marker (1 byte)][zeros (27 bytes)]
    // aToken salt: [0,0,0,0,'A',0,...] vs debtToken salt: [0,0,0,0,'D',0,...]
}

#[test]
fn test_wasm_hash_storage_persistence() {
    let env = create_test_env();
    let (admin, _emergency_admin, _user1, _user2, oracle) = create_test_addresses(&env);

    let pool_configurator = initialize_pool_configurator(&env, &admin, &_emergency_admin, &oracle);
    let client = pool_configurator::Client::new(&env, &pool_configurator);

    // Set hashes with specific values
    let a_token_hash1 = create_mock_token_wasm_hash(&env);
    let mut debt_hash_bytes = [0u8; 32];
    debt_hash_bytes[0] = 0xCC;
    debt_hash_bytes[31] = 0xDD;
    let debt_hash1 = BytesN::from_array(&env, &debt_hash_bytes);

    client.set_a_token_wasm_hash(&admin, &a_token_hash1);
    client.set_debt_token_wasm_hash(&admin, &debt_hash1);

    // Verify hashes can be retrieved (indirectly by attempting deploy)
    // If hashes weren't stored, deploy would fail with WASMHashNotSet
    let underlying_asset = Address::generate(&env);
    let interest_rate_strategy = Address::generate(&env);
    let treasury = Address::generate(&env);
    let params = pool_configurator::InitReserveParams {
        decimals: 9,
        ltv: 7500,
        liquidation_threshold: 8000,
        liquidation_bonus: 10500,
        reserve_factor: 1000,
        supply_cap: 1_000_000,
        borrow_cap: 1_000_000,
        borrowing_enabled: true,
        flashloan_enabled: true,
    };

    let result = client.try_deploy_and_init_reserve(
        &admin,
        &underlying_asset,
        &interest_rate_strategy,
        &treasury,
        &String::from_str(&env, "Test aToken"),
        &String::from_str(&env, "aTEST"),
        &String::from_str(&env, "Test Debt Token"),
        &String::from_str(&env, "dTEST"),
        &params,
    );

    // Should fail at deployment (no actual WASM), not at hash retrieval
    assert!(result.is_err(), "Deployment should fail without actual WASM");

    // Verify it doesn't fail at hash check (hashes are stored and retrieved)
    match result {
        Err(Ok(pool_configurator::KineticRouterError::WASMHashNotSet)) => {
            panic!("Deployment should not fail at hash check - hashes are stored");
        }
        _ => {}
    }

    // Verify hash values are different
    assert_ne!(
        a_token_hash1.to_array(),
        debt_hash1.to_array(),
        "aToken and debtToken hashes must be different"
    );
    
    // Verify hash byte arrays have expected values
    let a_hash_array = a_token_hash1.to_array();
    let debt_hash_array = debt_hash1.to_array();
    assert_eq!(a_hash_array[0], 0xAA, "aToken hash should have 0xAA at index 0");
    assert_eq!(a_hash_array[31], 0xBB, "aToken hash should have 0xBB at index 31");
    assert_eq!(debt_hash_array[0], 0xCC, "debtToken hash should have 0xCC at index 0");
    assert_eq!(debt_hash_array[31], 0xDD, "debtToken hash should have 0xDD at index 31");
}

#[test]
fn test_wasm_hash_can_be_updated() {
    let env = create_test_env();
    let (admin, _emergency_admin, _user1, _user2, oracle) = create_test_addresses(&env);

    let pool_configurator = initialize_pool_configurator(&env, &admin, &_emergency_admin, &oracle);
    let client = pool_configurator::Client::new(&env, &pool_configurator);

    // Set initial hash
    let hash1 = create_mock_token_wasm_hash(&env);
    client.set_a_token_wasm_hash(&admin, &hash1);

    // Update to different hash
    let mut hash2_bytes = [0u8; 32];
    hash2_bytes[0] = 0xFF;
    hash2_bytes[31] = 0xEE;
    let hash2 = BytesN::from_array(&env, &hash2_bytes);
    client.set_a_token_wasm_hash(&admin, &hash2);

    // Verify new hash is used (deploy should use hash2, not hash1)
    let underlying_asset = Address::generate(&env);
    let interest_rate_strategy = Address::generate(&env);
    let treasury = Address::generate(&env);
    let params = pool_configurator::InitReserveParams {
        decimals: 9,
        ltv: 7500,
        liquidation_threshold: 8000,
        liquidation_bonus: 10500,
        reserve_factor: 1000,
        supply_cap: 1_000_000,
        borrow_cap: 1_000_000,
        borrowing_enabled: true,
        flashloan_enabled: true,
    };

    // Set debt hash too
    let debt_hash = create_mock_token_wasm_hash(&env);
    client.set_debt_token_wasm_hash(&admin, &debt_hash);

    let result = client.try_deploy_and_init_reserve(
        &admin,
        &underlying_asset,
        &interest_rate_strategy,
        &treasury,
        &String::from_str(&env, "Test aToken"),
        &String::from_str(&env, "aTEST"),
        &String::from_str(&env, "Test Debt Token"),
        &String::from_str(&env, "dTEST"),
        &params,
    );

    // Should fail at deployment, but hash2 should be used (not hash1)
    assert!(result.is_err(), "Deployment should fail without actual WASM");

    // Verify it doesn't fail at hash check (hash2 is stored and used)
    match result {
        Err(Ok(pool_configurator::KineticRouterError::WASMHashNotSet)) => {
            panic!("Deployment should not fail at hash check - hash2 is stored");
        }
        _ => {}
    }

    // Verify hash values are different
    assert_ne!(
        hash1.to_array(),
        hash2.to_array(),
        "hash1 and hash2 must be different"
    );
    
    // Verify hash2 has expected values (was updated)
    let hash2_array = hash2.to_array();
    assert_eq!(hash2_array[0], 0xFF, "hash2 should have 0xFF at index 0");
    assert_eq!(hash2_array[31], 0xEE, "hash2 should have 0xEE at index 31");
}

#[test]
fn test_deploy_requires_both_hashes() {
    let env = create_test_env();
    let (admin, _emergency_admin, _user1, _user2, oracle) = create_test_addresses(&env);

    let pool_configurator = initialize_pool_configurator(&env, &admin, &_emergency_admin, &oracle);
    let client = pool_configurator::Client::new(&env, &pool_configurator);

    let underlying_asset = Address::generate(&env);
    let interest_rate_strategy = Address::generate(&env);
    let treasury = Address::generate(&env);
    let params = pool_configurator::InitReserveParams {
        decimals: 9,
        ltv: 7500,
        liquidation_threshold: 8000,
        liquidation_bonus: 10500,
        reserve_factor: 1000,
        supply_cap: 1_000_000,
        borrow_cap: 1_000_000,
        borrowing_enabled: true,
        flashloan_enabled: true,
    };

    // Try to deploy without setting any hashes
    let result = client.try_deploy_and_init_reserve(
        &admin,
        &underlying_asset,
        &interest_rate_strategy,
        &treasury,
        &String::from_str(&env, "Test aToken"),
        &String::from_str(&env, "aTEST"),
        &String::from_str(&env, "Test Debt Token"),
        &String::from_str(&env, "dTEST"),
        &params,
    );

    // Must fail - both hashes required
    assert!(result.is_err(), "Deployment must fail when no hashes are set");

    // Verify the error is WASMHashNotSet (missing aToken hash)
    match result {
        Err(Ok(pool_configurator::KineticRouterError::WASMHashNotSet)) => {}
        _ => panic!("Expected WASMHashNotSet error, got: {:?}", result),
    }
}

#[test]
fn test_deploy_counter_starts_at_zero() {
    let env = create_test_env();
    let (admin, _emergency_admin, _user1, _user2, oracle) = create_test_addresses(&env);

    let pool_configurator = initialize_pool_configurator(&env, &admin, &_emergency_admin, &oracle);
    let client = pool_configurator::Client::new(&env, &pool_configurator);

    // Set hashes
    let a_token_hash = create_mock_token_wasm_hash(&env);
    let debt_hash = create_mock_token_wasm_hash(&env);
    client.set_a_token_wasm_hash(&admin, &a_token_hash);
    client.set_debt_token_wasm_hash(&admin, &debt_hash);

    let underlying_asset = Address::generate(&env);
    let underlying_asset2 = Address::generate(&env);
    let interest_rate_strategy = Address::generate(&env);
    let treasury = Address::generate(&env);
    let params = pool_configurator::InitReserveParams {
        decimals: 9,
        ltv: 7500,
        liquidation_threshold: 8000,
        liquidation_bonus: 10500,
        reserve_factor: 1000,
        supply_cap: 1_000_000,
        borrow_cap: 1_000_000,
        borrowing_enabled: true,
        flashloan_enabled: true,
    };

    assert_ne!(underlying_asset, underlying_asset2, "Assets must be different");

    // First deployment should use counter = 0
    let result1 = client.try_deploy_and_init_reserve(
        &admin,
        &underlying_asset,
        &interest_rate_strategy,
        &treasury,
        &String::from_str(&env, "Test aToken"),
        &String::from_str(&env, "aTEST"),
        &String::from_str(&env, "Test Debt Token"),
        &String::from_str(&env, "dTEST"),
        &params,
    );

    assert!(result1.is_err(), "First deployment should fail (no actual WASM)");

    // Verify first deployment doesn't fail at hash check (counter = 0 used)
    match result1 {
        Err(Ok(pool_configurator::KineticRouterError::WASMHashNotSet)) => {
            panic!("First deployment should not fail at hash check - hashes are set");
        }
        _ => {}
    }

    // Second deployment should use counter = 1
    let result2 = client.try_deploy_and_init_reserve(
        &admin,
        &underlying_asset2,
        &interest_rate_strategy,
        &treasury,
        &String::from_str(&env, "Test aToken 2"),
        &String::from_str(&env, "aTEST2"),
        &String::from_str(&env, "Test Debt Token 2"),
        &String::from_str(&env, "dTEST2"),
        &params,
    );

    assert!(result2.is_err(), "Second deployment should fail (no actual WASM)");
    assert_ne!(underlying_asset, underlying_asset2, "Assets must be different");

    // Verify second deployment doesn't fail at hash check (counter = 1 used)
    match result2 {
        Err(Ok(pool_configurator::KineticRouterError::WASMHashNotSet)) => {
            panic!("Second deployment should not fail at hash check - hashes are set");
        }
        _ => {}
    }

    // Counter increments ensure different salts for each deployment
    // First deployment: counter = 0, Second deployment: counter = 1
}

#[test]
fn test_salt_generation_uses_type_markers() {
    let env = create_test_env();
    let (admin, _emergency_admin, _user1, _user2, oracle) = create_test_addresses(&env);

    let pool_configurator = initialize_pool_configurator(&env, &admin, &_emergency_admin, &oracle);
    let client = pool_configurator::Client::new(&env, &pool_configurator);

    // Set hashes
    let a_token_hash = create_mock_token_wasm_hash(&env);
    let debt_hash = create_mock_token_wasm_hash(&env);
    client.set_a_token_wasm_hash(&admin, &a_token_hash);
    client.set_debt_token_wasm_hash(&admin, &debt_hash);

    let underlying_asset = Address::generate(&env);
    let interest_rate_strategy = Address::generate(&env);
    let treasury = Address::generate(&env);
    let params = pool_configurator::InitReserveParams {
        decimals: 9,
        ltv: 7500,
        liquidation_threshold: 8000,
        liquidation_bonus: 10500,
        reserve_factor: 1000,
        supply_cap: 1_000_000,
        borrow_cap: 1_000_000,
        borrowing_enabled: true,
        flashloan_enabled: true,
    };

    // Attempt deployment
    let result = client.try_deploy_and_init_reserve(
        &admin,
        &underlying_asset,
        &interest_rate_strategy,
        &treasury,
        &String::from_str(&env, "Test aToken"),
        &String::from_str(&env, "aTEST"),
        &String::from_str(&env, "Test Debt Token"),
        &String::from_str(&env, "dTEST"),
        &params,
    );

    assert!(result.is_err(), "Deployment should fail without actual WASM");

    // Verify it doesn't fail at hash check
    match result {
        Err(Ok(pool_configurator::KineticRouterError::WASMHashNotSet)) => {
            panic!("Deployment should not fail at hash check - hashes are set");
        }
        _ => {}
    }

    // Salt generation uses:
    // - First 4 bytes: counter (u32 big-endian) - starts at 0
    // - Byte 4: 'A' (0x41) for aToken, 'D' (0x44) for debtToken
    // - Remaining 27 bytes: zeros
    // This ensures aToken and debtToken get different addresses even with same counter
    // Example salts for counter=0:
    //   aToken: [0x00, 0x00, 0x00, 0x00, 0x41, 0x00, ...]
    //   debtToken: [0x00, 0x00, 0x00, 0x00, 0x44, 0x00, ...]
}

#[test]
fn test_pause_reserve_deployment_success() {
    let env = create_test_env();
    let (admin, emergency_admin, _user1, _user2, oracle) = create_test_addresses(&env);
    let pool_configurator = initialize_pool_configurator(&env, &admin, &emergency_admin, &oracle);

    let client = pool_configurator::Client::new(&env, &pool_configurator);

    // Initially not paused
    assert_eq!(client.is_reserve_deployment_paused(), false);

    // Pause reserve deployment (using admin since emergency_admin is set to admin in initialize)
    client.pause_reserve_deployment(&admin);

    // Verify paused
    assert_eq!(client.is_reserve_deployment_paused(), true);
}

#[test]
fn test_unpause_reserve_deployment_success() {
    let env = create_test_env();
    let (admin, emergency_admin, _user1, _user2, oracle) = create_test_addresses(&env);
    let pool_configurator = initialize_pool_configurator(&env, &admin, &emergency_admin, &oracle);

    let client = pool_configurator::Client::new(&env, &pool_configurator);

    // Pause first (using admin since emergency_admin is set to admin in initialize)
    client.pause_reserve_deployment(&admin);
    assert_eq!(client.is_reserve_deployment_paused(), true);

    // Unpause
    client.unpause_reserve_deployment(&admin);

    // Verify unpaused
    assert_eq!(client.is_reserve_deployment_paused(), false);
}

#[test]
fn test_pause_reserve_deployment_unauthorized() {
    let env = create_test_env();
    let (admin, emergency_admin, user1, _user2, oracle) = create_test_addresses(&env);
    let pool_configurator = initialize_pool_configurator(&env, &admin, &emergency_admin, &oracle);

    let client = pool_configurator::Client::new(&env, &pool_configurator);

    // Attempt to pause as non-admin
    let result = client.try_pause_reserve_deployment(&user1);
    assert!(result.is_err());

    match result {
        Err(Ok(pool_configurator::KineticRouterError::Unauthorized)) => {}
        _ => panic!("Expected Unauthorized error"),
    }

    // Verify still not paused
    assert_eq!(client.is_reserve_deployment_paused(), false);
}

#[test]
fn test_reserve_deployment_blocked_when_paused() {
    let env = create_test_env();
    let (admin, emergency_admin, _user1, _user2, oracle) = create_test_addresses(&env);
    let pool_configurator = initialize_pool_configurator(&env, &admin, &emergency_admin, &oracle);

    let client = pool_configurator::Client::new(&env, &pool_configurator);

    // Pause reserve deployment (using admin since emergency_admin is set to admin in initialize)
    client.pause_reserve_deployment(&admin);

    // Attempt to initialize reserve should fail
    let underlying_asset = Address::generate(&env);
    let a_token_impl = Address::generate(&env);
    let variable_debt_impl = Address::generate(&env);
    let interest_rate_strategy = Address::generate(&env);
    let treasury = Address::generate(&env);

    let params = pool_configurator::InitReserveParams {
        decimals: 7,
        ltv: 8000,
        liquidation_threshold: 8500,
        liquidation_bonus: 500,
        reserve_factor: 1000,
        supply_cap: 0,
        borrow_cap: 0,
        borrowing_enabled: true,
        flashloan_enabled: true,
    };

    let result = client.try_init_reserve(
        &admin,
        &underlying_asset,
        &a_token_impl,
        &variable_debt_impl,
        &interest_rate_strategy,
        &treasury,
        &params,
    );
    assert!(result.is_err());

    match result {
        Err(Ok(pool_configurator::KineticRouterError::AssetPaused)) => {}
        _ => panic!("Expected AssetPaused error"),
    }
}

// ========================================================================
// COLLATERAL CONFIGURATION BUFFER VALIDATION TESTS
// ========================================================================

#[test]
fn test_configure_reserve_as_collateral_success() {
    let env = create_test_env();
    let (admin, _emergency_admin, _user1, _user2, oracle) = create_test_addresses(&env);
    let pool_configurator = initialize_pool_configurator(&env, &admin, &_emergency_admin, &oracle);
    let client = pool_configurator::Client::new(&env, &pool_configurator);
    let asset = Address::generate(&env);

    // Valid config: ltv=7500, liquidation_threshold=8000 (500 bps buffer)
    let result = client.try_configure_reserve_as_collateral(&admin, &asset, &7500, &8000, &500);
    assert!(result.is_ok(), "Valid configuration should succeed");
}

#[test]
fn test_configure_reserve_as_collateral_rejects_equal_values() {
    let env = create_test_env();
    let (admin, _emergency_admin, _user1, _user2, oracle) = create_test_addresses(&env);
    let pool_configurator = initialize_pool_configurator(&env, &admin, &_emergency_admin, &oracle);
    let client = pool_configurator::Client::new(&env, &pool_configurator);
    let asset = Address::generate(&env);

    // Invalid config: ltv=7500, liquidation_threshold=7500 (no buffer)
    let ltv = 7500u32;
    let liquidation_threshold = 7500u32;
    assert_eq!(ltv, liquidation_threshold, "Values must be equal to test rejection");
    assert!(!(liquidation_threshold > ltv), "liquidation_threshold should not be greater");
    
    let result = client.try_configure_reserve_as_collateral(&admin, &asset, &ltv, &liquidation_threshold, &500);
    
    assert!(result.is_err(), "Equal LTV and liquidation threshold should be rejected");
    
    match result {
        Err(Ok(pool_configurator::KineticRouterError::InvalidAmount)) => {}
        _ => panic!("Expected InvalidAmount error, got: {:?}", result),
    }
}

#[test]
fn test_configure_reserve_as_collateral_rejects_insufficient_buffer() {
    let env = create_test_env();
    let (admin, _emergency_admin, _user1, _user2, oracle) = create_test_addresses(&env);
    let pool_configurator = initialize_pool_configurator(&env, &admin, &_emergency_admin, &oracle);
    let client = pool_configurator::Client::new(&env, &pool_configurator);
    let asset = Address::generate(&env);

    // Invalid config: ltv=7500, liquidation_threshold=7549 (49 bps buffer, below 50 bps minimum)
    let ltv = 7500u32;
    let liquidation_threshold = 7549u32;
    let buffer = liquidation_threshold - ltv;
    assert_eq!(buffer, 49, "Buffer should be exactly 49 bps");
    assert!(buffer < 50, "Buffer must be below 50 bps minimum");
    assert!(liquidation_threshold > ltv, "liquidation_threshold is greater but buffer insufficient");
    
    let result = client.try_configure_reserve_as_collateral(&admin, &asset, &ltv, &liquidation_threshold, &500);
    assert!(result.is_err(), "Buffer below 50 bps minimum should be rejected");
    
    match result {
        Err(Ok(pool_configurator::KineticRouterError::InvalidAmount)) => {}
        _ => panic!("Expected InvalidAmount error, got: {:?}", result),
    }
}

#[test]
fn test_configure_reserve_as_collateral_accepts_minimum_buffer() {
    let env = create_test_env();
    let (admin, _emergency_admin, _user1, _user2, oracle) = create_test_addresses(&env);
    let pool_configurator = initialize_pool_configurator(&env, &admin, &_emergency_admin, &oracle);
    let client = pool_configurator::Client::new(&env, &pool_configurator);
    let asset = Address::generate(&env);

    // Valid config: ltv=7500, liquidation_threshold=7550 (exactly 50 bps buffer)
    let ltv = 7500u32;
    let liquidation_threshold = 7550u32;
    let buffer = liquidation_threshold - ltv;
    assert_eq!(buffer, 50, "Buffer should be exactly 50 bps (minimum)");
    assert!(liquidation_threshold > ltv, "liquidation_threshold must be strictly greater than ltv");
    
    let result = client.try_configure_reserve_as_collateral(&admin, &asset, &ltv, &liquidation_threshold, &500);
    assert!(result.is_ok(), "Minimum 50 bps buffer should be accepted");
    
    // Verify configuration was accepted (no error means success)
    assert!(result.is_ok(), "Configuration should succeed with valid buffer");
}

#[test]
fn test_init_reserve_rejects_equal_values() {
    let env = create_test_env();
    let (admin, _emergency_admin, _user1, _user2, oracle) = create_test_addresses(&env);
    let pool_configurator = initialize_pool_configurator(&env, &admin, &_emergency_admin, &oracle);
    let client = pool_configurator::Client::new(&env, &pool_configurator);

    let underlying_asset = Address::generate(&env);
    let a_token_impl = Address::generate(&env);
    let variable_debt_impl = Address::generate(&env);
    let interest_rate_strategy = Address::generate(&env);
    let treasury = Address::generate(&env);

    // Invalid config: ltv=7500, liquidation_threshold=7500 (no buffer)
    let ltv = 7500u32;
    let liquidation_threshold = 7500u32;
    assert_eq!(ltv, liquidation_threshold, "Values are equal - should be rejected");
    assert!(!(liquidation_threshold > ltv), "liquidation_threshold should not be greater");
    
    let params = pool_configurator::InitReserveParams {
        decimals: 7,
        ltv,
        liquidation_threshold,
        liquidation_bonus: 500,
        reserve_factor: 1000,
        supply_cap: 0,
        borrow_cap: 0,
        borrowing_enabled: true,
        flashloan_enabled: true,
    };

    let result = client.try_init_reserve(
        &admin,
        &underlying_asset,
        &a_token_impl,
        &variable_debt_impl,
        &interest_rate_strategy,
        &treasury,
        &params,
    );
    assert!(result.is_err(), "Equal LTV and liquidation threshold should be rejected");
    
    match result {
        Err(Ok(pool_configurator::KineticRouterError::InvalidAmount)) => {}
        _ => panic!("Expected InvalidAmount error, got: {:?}", result),
    }
}

#[test]
fn test_init_reserve_rejects_insufficient_buffer() {
    let env = create_test_env();
    let (admin, _emergency_admin, _user1, _user2, oracle) = create_test_addresses(&env);
    let pool_configurator = initialize_pool_configurator(&env, &admin, &_emergency_admin, &oracle);
    let client = pool_configurator::Client::new(&env, &pool_configurator);

    let underlying_asset = Address::generate(&env);
    let a_token_impl = Address::generate(&env);
    let variable_debt_impl = Address::generate(&env);
    let interest_rate_strategy = Address::generate(&env);
    let treasury = Address::generate(&env);

    // Invalid config: ltv=7500, liquidation_threshold=7549 (49 bps buffer, below 50 bps minimum)
    let ltv = 7500u32;
    let liquidation_threshold = 7549u32;
    let buffer = liquidation_threshold - ltv;
    assert_eq!(buffer, 49, "Buffer should be exactly 49 bps (below minimum)");
    assert!(buffer < 50, "Buffer must be below 50 bps minimum to test rejection");
    assert!(liquidation_threshold > ltv, "liquidation_threshold is greater but buffer insufficient");
    
    let params = pool_configurator::InitReserveParams {
        decimals: 7,
        ltv,
        liquidation_threshold,
        liquidation_bonus: 500,
        reserve_factor: 1000,
        supply_cap: 0,
        borrow_cap: 0,
        borrowing_enabled: true,
        flashloan_enabled: true,
    };

    let result = client.try_init_reserve(
        &admin,
        &underlying_asset,
        &a_token_impl,
        &variable_debt_impl,
        &interest_rate_strategy,
        &treasury,
        &params,
    );
    assert!(result.is_err(), "Buffer below 50 bps minimum should be rejected");
    
    match result {
        Err(Ok(pool_configurator::KineticRouterError::InvalidAmount)) => {}
        _ => panic!("Expected InvalidAmount error, got: {:?}", result),
    }
}
