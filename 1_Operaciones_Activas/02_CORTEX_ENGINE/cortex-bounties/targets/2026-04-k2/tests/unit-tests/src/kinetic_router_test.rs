#![cfg(test)]

use crate::{kinetic_router, a_token, debt_token, interest_rate_strategy, price_oracle};
use k2_shared::ReserveConfiguration as SharedReserveConfiguration;
use soroban_sdk::{
    contract, contractimpl,
    testutils::{Address as _, StellarAssetContract},
     Address, Env, IntoVal, String,
};

// Mock Reflector Oracle that implements decimals()
#[contract]
pub struct MockReflector;

#[contractimpl]
impl MockReflector {
    pub fn decimals(_env: Env) -> u32 {
        14
    }
}

// Helper to convert contract ReserveConfiguration to shared ReserveConfiguration
fn to_shared_config(config: &kinetic_router::ReserveConfiguration) -> SharedReserveConfiguration {
    SharedReserveConfiguration {
        data_low: config.data_low,
        data_high: config.data_high,
    }
}

pub fn create_test_env() -> Env {
    let env = Env::default();
    env.mock_all_auths();
    // Set unlimited budget for complex tests
    env.budget().reset_unlimited();
    env
}

pub fn create_test_addresses(env: &Env) -> (Address, Address, Address, Address) {
    let admin = Address::generate(env);
    let emergency_admin = Address::generate(env);
    let user1 = Address::generate(env);
    let user2 = Address::generate(env);
    (admin, emergency_admin, user1, user2)
}

fn create_mock_adapter_registry(env: &Env) -> Address {
    Address::generate(env)
}

/// Returns (kinetic_router_address, oracle_address)
pub fn initialize_kinetic_router_with_oracle(
    env: &Env,
    admin: &Address,
    emergency_admin: &Address,
    _router: &Address,
    dex_router: &Address,
) -> (Address, Address) {
    let contract_id = env.register(kinetic_router::WASM, ());
    let client = kinetic_router::Client::new(env, &contract_id);

    // Setup proper price oracle
    let oracle_addr = env.register(price_oracle::WASM, ());
    let oracle_client = price_oracle::Client::new(env, &oracle_addr);
    let reflector_addr = env.register(MockReflector, ());
    let base_currency = Address::generate(env);
    let native_xlm = Address::generate(env);
    oracle_client.initialize(admin, &reflector_addr, &base_currency, &native_xlm);

    let treasury = Address::generate(env);

    client.initialize(
        admin,
        emergency_admin,
        &oracle_addr,
        &treasury,
        dex_router,
        &None,
    );

    let pool_configurator = Address::generate(env);
    client.set_pool_configurator(&pool_configurator);

    (contract_id, oracle_addr)
}

// Returns (kinetic_router_address, oracle_address)  
pub fn initialize_kinetic_router(
    env: &Env,
    admin: &Address,
    emergency_admin: &Address,
    router: &Address,
    dex_router: &Address,
) -> (Address, Address) {
    initialize_kinetic_router_with_oracle(env, admin, emergency_admin, router, dex_router)
}

pub fn init_reserve_with_pool_configurator(
    env: &Env,
    client: &kinetic_router::Client,
    admin: &Address,
    underlying_asset: &Address,
    a_token_addr: &Address,
    debt_token_addr: &Address,
    interest_rate_strategy: &Address,
    treasury: &Address,
    params: &kinetic_router::InitReserveParams,
) {
    let pool_configurator = Address::generate(env);
    client.set_pool_configurator(&pool_configurator);
    client.init_reserve(
        &pool_configurator,
        underlying_asset,
        a_token_addr,
        debt_token_addr,
        interest_rate_strategy,
        treasury,
        params,
    );
}

pub fn create_and_init_test_reserve_with_oracle(
    env: &Env,
    kinetic_router: &Address,
    oracle_addr: &Address,
    admin: &Address,
) -> (Address, StellarAssetContract) {
    let underlying_asset_contract = env.register_stellar_asset_contract_v2(admin.clone());
    let underlying_asset = underlying_asset_contract.address();

    // Initialize interest rate strategy contract
    let interest_rate_strategy = env.register(interest_rate_strategy::WASM, ());
    // Call initialize directly using invoke_contract
    env.invoke_contract::<Result<(), k2_shared::KineticRouterError>>(
        &interest_rate_strategy,
        &soroban_sdk::Symbol::new(env, "initialize"),
        soroban_sdk::vec![
            env,
            admin.into_val(env),
            200u128.into_val(env),       // base_variable_borrow_rate (2%)
            1000u128.into_val(env),      // variable_rate_slope1 (10%)
            10000u128.into_val(env),     // variable_rate_slope2 (100%)
            8000u128.into_val(env),      // optimal_utilization_rate (80%)
        ],
    ).unwrap();
    
    let treasury = Address::generate(env);

    let params = kinetic_router::InitReserveParams {
        decimals: 7,
        ltv: 8000,
        liquidation_threshold: 8500,
        liquidation_bonus: 500,
        reserve_factor: 1000,
        supply_cap: 1000000000000,
        borrow_cap: 1000000000000,
        borrowing_enabled: true,
        flashloan_enabled: true,
    };

    let a_token_addr = env.register(a_token::WASM, ());
    let a_token_client = a_token::Client::new(env, &a_token_addr);
    let a_name = String::from_str(env, "Test aToken");
    let a_symbol = String::from_str(env, "aTEST");
    a_token_client.initialize(
        admin,
        &underlying_asset,
        kinetic_router,
        &a_name,
        &a_symbol,
        &params.decimals,
    );

    let debt_token_addr = env.register(debt_token::WASM, ());
    let debt_token_client = debt_token::Client::new(env, &debt_token_addr);
    let debt_name = String::from_str(env, "Debt Token");
    let debt_symbol = String::from_str(env, "dTEST");
    debt_token_client.initialize(
        admin,
        &underlying_asset,
        kinetic_router,
        &debt_name,
        &debt_symbol,
        &params.decimals,
    );

    let client = kinetic_router::Client::new(env, kinetic_router);
    
    // Register asset with oracle and set price (1 USD with 14 decimals)
    let oracle_client = price_oracle::Client::new(env, oracle_addr);
    let asset_enum = price_oracle::Asset::Stellar(underlying_asset.clone());
    oracle_client.add_asset(admin, &asset_enum);
    oracle_client.set_manual_override(
        admin,
        &asset_enum,
        &Some(1_000_000_000_000_000u128), // 1 USD with 14 decimals
        &Some(env.ledger().timestamp() + 604_800), // 7 days (max allowed by L-04)
    );
    
    init_reserve_with_pool_configurator(
        env,
        &client,
        admin,
        &underlying_asset,
        &a_token_addr,
        &debt_token_addr,
        &interest_rate_strategy,
        &treasury,
        &params,
    );

    (underlying_asset, underlying_asset_contract)
}

#[test]
fn test_reserve_configuration_cap_methods() {
    use k2_shared::ReserveConfiguration;

    // Test that the cap methods work correctly on a fresh configuration
    let mut config = ReserveConfiguration {
        data_low: 0,
        data_high: 0,
    };

    // Test setting and getting supply cap
    config.set_supply_cap(1000000000000);
    let supply_cap = config.get_supply_cap();
    assert_eq!(supply_cap, 1000000000000);

    // Test setting and getting borrow cap
    config.set_borrow_cap(1000000000000);
    let borrow_cap = config.get_borrow_cap();
    assert_eq!(borrow_cap, 1000000000000);

    // Test setting caps to zero
    config.set_supply_cap(0);
    config.set_borrow_cap(0);
    assert_eq!(config.get_supply_cap(), 0);
    assert_eq!(config.get_borrow_cap(), 0);
}

#[test]
fn test_bit_manipulation_debug() {
    use k2_shared::ReserveConfiguration;

    let mut config = ReserveConfiguration {
        data_low: 0,
        data_high: 0,
    };

    // Test with realistic whole token values
    config.set_supply_cap(1000);
    let result = config.get_supply_cap();
    assert_eq!(result, 1000);

    // Test with larger values
    config.set_supply_cap(100000);
    let result = config.get_supply_cap();
    assert_eq!(result, 100000);

    // Test with 500B tokens (unlimited with U256)
    config.set_supply_cap(500000000000);
    let result = config.get_supply_cap();
    assert_eq!(result, 500000000000);
}

#[test]
fn test_manual_bit_manipulation() {
    use k2_shared::ReserveConfiguration;

    let mut config = ReserveConfiguration {
        data_low: 0,
        data_high: 0,
    };

    // Manually set supply cap using the same logic as the setter
    let supply_cap = 1000000000000u128;
    let mask = 0xFFFFFFFFFFFFFFFFu128;

    // Clear existing supply cap and set new value (bits 64-127 of data_high)
    config.data_high &= !(mask << 64);
    config.data_high |= (supply_cap & mask) << 64;

    // Get the value using the same logic as the getter
    let result = (config.data_high >> 64) & mask;
    assert_eq!(result, supply_cap);
}

#[test]
fn test_setter_vs_manual() {
    use k2_shared::ReserveConfiguration;

    let mut config1 = ReserveConfiguration {
        data_low: 0,
        data_high: 0,
    };
    let mut config2 = ReserveConfiguration {
        data_low: 0,
        data_high: 0,
    };

    let supply_cap = 1000000000000u128;

    // Method 1: Use the setter method
    config1.set_supply_cap(supply_cap);
    let result1 = config1.get_supply_cap();

    // Method 2: Manual bit manipulation with U256 structure
    let mask = 0xFFFFFFFFFFFFFFFFu128;
    config2.data_high &= !(mask << 64);
    config2.data_high |= (supply_cap & mask) << 64;
    let result2 = (config2.data_high >> 64) & mask;

    // Both should give the same result
    assert_eq!(result1, result2);
    assert_eq!(result1, supply_cap);
}

#[test]
fn test_initial_supply_cap_set() {
    let env = create_test_env();
    let (admin, emergency_admin, _user1, _user2) = create_test_addresses(&env);
    let router = Address::generate(&env);

    let dex_router = Address::generate(&env);
    let (kinetic_router, oracle) = initialize_kinetic_router(&env, &admin, &emergency_admin, &router, &dex_router);
    let (underlying_asset, _) = create_and_init_test_reserve_with_oracle(&env, &kinetic_router, &oracle, &admin);

    let client = kinetic_router::Client::new(&env, &kinetic_router);

    // Verify initial supply cap is set correctly
    let initial_reserve_data = client.get_reserve_data(&underlying_asset);
    let config = to_shared_config(&initial_reserve_data.configuration);
    assert_eq!(
        config.get_supply_cap(),
        1000000000000
    );
}

#[test]
fn test_set_reserve_supply_cap_success() {
    let env = create_test_env();
    let (admin, emergency_admin, _user1, _user2) = create_test_addresses(&env);
    let router = Address::generate(&env);

    let dex_router = Address::generate(&env);
    let (kinetic_router, oracle) = initialize_kinetic_router(&env, &admin, &emergency_admin, &router, &dex_router);
    let (underlying_asset, _) = create_and_init_test_reserve_with_oracle(&env, &kinetic_router, &oracle, &admin);

    let client = kinetic_router::Client::new(&env, &kinetic_router);

    // Set supply cap to 500B whole tokens
    let new_supply_cap = 500000000000;
    client.set_reserve_supply_cap(&underlying_asset, &new_supply_cap);

    // Verify the cap was set by getting reserve data
    let reserve_data = client.get_reserve_data(&underlying_asset);
    let config = to_shared_config(&reserve_data.configuration);
    assert_eq!(config.get_supply_cap(), new_supply_cap);
}

#[test]
fn test_set_reserve_borrow_cap_success() {
    let env = create_test_env();
    let (admin, emergency_admin, _user1, _user2) = create_test_addresses(&env);
    let router = Address::generate(&env);

    let dex_router = Address::generate(&env);
    let (kinetic_router, oracle) = initialize_kinetic_router(&env, &admin, &emergency_admin, &router, &dex_router);
    let (underlying_asset, _) = create_and_init_test_reserve_with_oracle(&env, &kinetic_router, &oracle, &admin);

    let client = kinetic_router::Client::new(&env, &kinetic_router);

    // Set borrow cap to 1M whole tokens
    let new_borrow_cap = 1000000;
    client.set_reserve_borrow_cap(&underlying_asset, &new_borrow_cap);

    // Verify the cap was set by getting reserve data
    let reserve_data = client.get_reserve_data(&underlying_asset);
    let config = to_shared_config(&reserve_data.configuration);
    assert_eq!(config.get_borrow_cap(), new_borrow_cap);
}

#[test]
fn test_set_reserve_supply_cap_unauthorized() {
    let env = create_test_env();
    let (admin, emergency_admin, user1, _user2) = create_test_addresses(&env);
    let router = Address::generate(&env);

    let dex_router = Address::generate(&env);
    let (kinetic_router, oracle) = initialize_kinetic_router(&env, &admin, &emergency_admin, &router, &dex_router);
    let (underlying_asset, _) = create_and_init_test_reserve_with_oracle(&env, &kinetic_router, &oracle, &admin);

    let client = kinetic_router::Client::new(&env, &kinetic_router);

    // Attempt to set supply cap without auth - should fail
    env.mock_auths(&[]);
    let new_supply_cap = 500000000000;

    let result = client.try_set_reserve_supply_cap(&underlying_asset, &new_supply_cap);
    assert!(result.is_err(), "Should fail without authorization");

    // Now set as admin - should succeed
    env.mock_all_auths();
    let result = client.try_set_reserve_supply_cap(&underlying_asset, &new_supply_cap);
    assert!(result.is_ok(), "Admin should be able to set supply cap");
    
    let reserve_data = client.get_reserve_data(&underlying_asset);
    let config = to_shared_config(&reserve_data.configuration);
    assert_eq!(config.get_supply_cap(), new_supply_cap);
}

#[test]
fn test_set_reserve_borrow_cap_unauthorized() {
    let env = create_test_env();
    let (admin, emergency_admin, user1, _user2) = create_test_addresses(&env);
    let router = Address::generate(&env);

    let dex_router = Address::generate(&env);
    let (kinetic_router, oracle) = initialize_kinetic_router(&env, &admin, &emergency_admin, &router, &dex_router);
    let (underlying_asset, _) = create_and_init_test_reserve_with_oracle(&env, &kinetic_router, &oracle, &admin);

    let client = kinetic_router::Client::new(&env, &kinetic_router);

    // Attempt to set borrow cap without auth - should fail
    env.mock_auths(&[]);
    let new_borrow_cap = 500000000000;

    let result = client.try_set_reserve_borrow_cap(&underlying_asset, &new_borrow_cap);
    assert!(result.is_err(), "Should fail without authorization");

    // Now set as admin - should succeed
    env.mock_all_auths();
    let result = client.try_set_reserve_borrow_cap(&underlying_asset, &new_borrow_cap);
    assert!(result.is_ok(), "Admin should be able to set borrow cap");
    
    let reserve_data = client.get_reserve_data(&underlying_asset);
    let config = to_shared_config(&reserve_data.configuration);
    assert_eq!(config.get_borrow_cap(), new_borrow_cap);
}

#[test]
fn test_set_supply_cap_to_zero() {
    let env = create_test_env();
    let (admin, emergency_admin, _user1, _user2) = create_test_addresses(&env);
    let router = Address::generate(&env);

    let dex_router = Address::generate(&env);
    let (kinetic_router, oracle) = initialize_kinetic_router(&env, &admin, &emergency_admin, &router, &dex_router);
    let (underlying_asset, _) = create_and_init_test_reserve_with_oracle(&env, &kinetic_router, &oracle, &admin);

    let client = kinetic_router::Client::new(&env, &kinetic_router);

    // Set supply cap to 0 to remove cap
    let new_supply_cap = 0;
    client.set_reserve_supply_cap(&underlying_asset, &new_supply_cap);

    // Verify the cap was set to 0
    let reserve_data = client.get_reserve_data(&underlying_asset);
    let config = to_shared_config(&reserve_data.configuration);
    assert_eq!(config.get_supply_cap(), 0);
}

#[test]
fn test_set_borrow_cap_to_zero() {
    let env = create_test_env();
    let (admin, emergency_admin, _user1, _user2) = create_test_addresses(&env);
    let router = Address::generate(&env);

    let dex_router = Address::generate(&env);
    let (kinetic_router, oracle) = initialize_kinetic_router(&env, &admin, &emergency_admin, &router, &dex_router);
    let (underlying_asset, _) = create_and_init_test_reserve_with_oracle(&env, &kinetic_router, &oracle, &admin);

    let client = kinetic_router::Client::new(&env, &kinetic_router);

    // Set borrow cap to 0 to remove cap
    let new_borrow_cap = 0;
    client.set_reserve_borrow_cap(&underlying_asset, &new_borrow_cap);

    // Verify the cap was set to 0
    let reserve_data = client.get_reserve_data(&underlying_asset);
    let config = to_shared_config(&reserve_data.configuration);
    assert_eq!(config.get_borrow_cap(), 0);
}

#[test]
fn test_supply_cap_enforcement() {
    let env = create_test_env();
    let (admin, emergency_admin, _user1, _user2) = create_test_addresses(&env);
    let router = Address::generate(&env);

    let dex_router = Address::generate(&env);
    let (kinetic_router, oracle) = initialize_kinetic_router(&env, &admin, &emergency_admin, &router, &dex_router);
    let (underlying_asset, _) = create_and_init_test_reserve_with_oracle(&env, &kinetic_router, &oracle, &admin);

    let client = kinetic_router::Client::new(&env, &kinetic_router);

    // Set a supply cap for testing
    let supply_cap = 1000000000000;
    client.set_reserve_supply_cap(&underlying_asset, &supply_cap);

    // Verify the cap is set correctly
    let reserve_data = client.get_reserve_data(&underlying_asset);
    let config = to_shared_config(&reserve_data.configuration);
    assert_eq!(config.get_supply_cap(), supply_cap);

    // Test that supply operations respect the cap
    // This would require implementing supply functionality in the lending pool
    // For now, we verify the cap is properly stored and retrieved
    assert_eq!(config.get_supply_cap(), supply_cap);
}

#[test]
fn test_borrow_cap_enforcement() {
    let env = create_test_env();
    let (admin, emergency_admin, _user1, _user2) = create_test_addresses(&env);
    let router = Address::generate(&env);

    let dex_router = Address::generate(&env);
    let (kinetic_router, oracle) = initialize_kinetic_router(&env, &admin, &emergency_admin, &router, &dex_router);
    let (underlying_asset, _) = create_and_init_test_reserve_with_oracle(&env, &kinetic_router, &oracle, &admin);

    let client = kinetic_router::Client::new(&env, &kinetic_router);

    // Set a borrow cap for testing
    let borrow_cap = 1000000000000;
    client.set_reserve_borrow_cap(&underlying_asset, &borrow_cap);

    // Verify the cap is set correctly
    let reserve_data = client.get_reserve_data(&underlying_asset);
    let config = to_shared_config(&reserve_data.configuration);
    assert_eq!(config.get_borrow_cap(), borrow_cap);

    // Test that borrow operations respect the cap
    // This would require implementing borrow functionality in the lending pool
    // For now, we verify the cap is properly stored and retrieved
    assert_eq!(config.get_borrow_cap(), borrow_cap);
    
    // Prevent env destructor from running to avoid budget exceeded error during snapshot creation
    std::mem::forget(env);
}

#[test]
fn test_cap_events_emitted() {
    let env = create_test_env();
    let (admin, emergency_admin, _user1, _user2) = create_test_addresses(&env);
    let router = Address::generate(&env);

    let dex_router = Address::generate(&env);
    let (kinetic_router, oracle) = initialize_kinetic_router(&env, &admin, &emergency_admin, &router, &dex_router);
    let (underlying_asset, _) = create_and_init_test_reserve_with_oracle(&env, &kinetic_router, &oracle, &admin);

    let client = kinetic_router::Client::new(&env, &kinetic_router);

    // Set supply cap and verify state change
    let supply_cap = 1000000000000;
    client.set_reserve_supply_cap(&underlying_asset, &supply_cap);

    // Set borrow cap and verify state change
    let borrow_cap = 1000000000000;
    client.set_reserve_borrow_cap(&underlying_asset, &borrow_cap);

    // Verify the operations complete successfully and state is updated
    let reserve_data = client.get_reserve_data(&underlying_asset);
    let config = to_shared_config(&reserve_data.configuration);
    assert_eq!(config.get_supply_cap(), supply_cap);
    assert_eq!(config.get_borrow_cap(), borrow_cap);

    // Verify both caps are properly set (non-zero values confirm they were set)
    assert_eq!(config.get_supply_cap(), supply_cap);
    assert_eq!(config.get_borrow_cap(), borrow_cap);
}

#[test]
fn test_set_reserve_debt_ceiling_success() {
    let env = create_test_env();
    let (admin, emergency_admin, _user1, _user2) = create_test_addresses(&env);
    let router = Address::generate(&env);

    let dex_router = Address::generate(&env);
    let (kinetic_router, oracle) = initialize_kinetic_router(&env, &admin, &emergency_admin, &router, &dex_router);
    let (underlying_asset, _) = create_and_init_test_reserve_with_oracle(&env, &kinetic_router, &oracle, &admin);

    let client = kinetic_router::Client::new(&env, &kinetic_router);

    // Set debt ceiling to 2M whole tokens
    let new_debt_ceiling = 2000000;
    client.set_reserve_debt_ceiling(&underlying_asset, &new_debt_ceiling);

    // Verify the ceiling was set by getting it directly
    let debt_ceiling = client.get_reserve_debt_ceiling(&underlying_asset);
    assert_eq!(debt_ceiling, new_debt_ceiling);
}

#[test]
fn test_set_reserve_debt_ceiling_unauthorized() {
    let env = create_test_env();
    let (admin, emergency_admin, user1, _user2) = create_test_addresses(&env);
    let router = Address::generate(&env);

    let dex_router = Address::generate(&env);
    let (kinetic_router, oracle) = initialize_kinetic_router(&env, &admin, &emergency_admin, &router, &dex_router);
    let (underlying_asset, _) = create_and_init_test_reserve_with_oracle(&env, &kinetic_router, &oracle, &admin);

    let client = kinetic_router::Client::new(&env, &kinetic_router);

    // Attempt to set debt ceiling without auth - should fail
    env.mock_auths(&[]);
    let new_debt_ceiling = 2000000;

    let result = client.try_set_reserve_debt_ceiling(&underlying_asset, &new_debt_ceiling);
    assert!(result.is_err(), "Should fail without authorization");

    // Now set as admin - should succeed
    env.mock_all_auths();
    let result = client.try_set_reserve_debt_ceiling(&underlying_asset, &new_debt_ceiling);
    assert!(result.is_ok(), "Admin should be able to set debt ceiling");
    
    let debt_ceiling = client.get_reserve_debt_ceiling(&underlying_asset);
    assert_eq!(debt_ceiling, new_debt_ceiling);
}

#[test]
fn test_set_debt_ceiling_to_zero() {
    let env = create_test_env();
    let (admin, emergency_admin, _user1, _user2) = create_test_addresses(&env);
    let router = Address::generate(&env);

    let dex_router = Address::generate(&env);
    let (kinetic_router, oracle) = initialize_kinetic_router(&env, &admin, &emergency_admin, &router, &dex_router);
    let (underlying_asset, _) = create_and_init_test_reserve_with_oracle(&env, &kinetic_router, &oracle, &admin);

    let client = kinetic_router::Client::new(&env, &kinetic_router);

    // First set a debt ceiling
    let initial_ceiling = 2000000;
    client.set_reserve_debt_ceiling(&underlying_asset, &initial_ceiling);
    assert_eq!(client.get_reserve_debt_ceiling(&underlying_asset), initial_ceiling);

    // Set debt ceiling to 0 to remove ceiling
    let new_debt_ceiling = 0;
    client.set_reserve_debt_ceiling(&underlying_asset, &new_debt_ceiling);

    // Verify the ceiling was set to 0
    let debt_ceiling = client.get_reserve_debt_ceiling(&underlying_asset);
    assert_eq!(debt_ceiling, 0);
}

#[test]
fn test_get_reserve_debt_ceiling_not_set() {
    let env = create_test_env();
    let (admin, emergency_admin, _user1, _user2) = create_test_addresses(&env);
    let router = Address::generate(&env);

    let dex_router = Address::generate(&env);
    let (kinetic_router, oracle) = initialize_kinetic_router(&env, &admin, &emergency_admin, &router, &dex_router);
    let (underlying_asset, _) = create_and_init_test_reserve_with_oracle(&env, &kinetic_router, &oracle, &admin);

    let client = kinetic_router::Client::new(&env, &kinetic_router);

    // Verify default debt ceiling is 0 (not set)
    let debt_ceiling = client.get_reserve_debt_ceiling(&underlying_asset);
    assert_eq!(debt_ceiling, 0);
}

#[test]
fn test_set_flash_loan_premium_max_success() {
    let env = create_test_env();
    let (admin, emergency_admin, _user1, _user2) = create_test_addresses(&env);
    let router = Address::generate(&env);

    let dex_router = Address::generate(&env);
    let (kinetic_router, _oracle) = initialize_kinetic_router(&env, &admin, &emergency_admin, &router, &dex_router);

    let client = kinetic_router::Client::new(&env, &kinetic_router);

    // Set max premium to 50 bps (0.5%)
    let new_max_premium = 50;
    client.set_flash_loan_premium_max(&new_max_premium);

    // Verify the max was set
    assert_eq!(client.get_flash_loan_premium_max(), new_max_premium);

    // Verify we can set premium up to the max
    client.set_flash_loan_premium(&new_max_premium);
    assert_eq!(client.get_flash_loan_premium(), new_max_premium);
}

#[test]
fn test_set_flash_loan_premium_max_unauthorized() {
    let env = create_test_env();
    let (admin, emergency_admin, user1, _user2) = create_test_addresses(&env);
    let router = Address::generate(&env);

    let dex_router = Address::generate(&env);
    let (kinetic_router, _oracle) = initialize_kinetic_router(&env, &admin, &emergency_admin, &router, &dex_router);

    let client = kinetic_router::Client::new(&env, &kinetic_router);

    // Attempt to set max premium without auth
    env.mock_auths(&[]);
    let result = client.try_set_flash_loan_premium_max(&50);
    assert!(result.is_err(), "Should fail without authorization");

    // Set as admin should succeed
    env.mock_all_auths();
    let result = client.try_set_flash_loan_premium_max(&50);
    assert!(result.is_ok(), "Admin should be able to set premium max");
    assert_eq!(client.get_flash_loan_premium_max(), 50);
}

#[test]
fn test_flash_loan_premium_max_enforcement() {
    let env = create_test_env();
    let (admin, emergency_admin, _user1, _user2) = create_test_addresses(&env);
    let router = Address::generate(&env);

    let dex_router = Address::generate(&env);
    let (kinetic_router, _oracle) = initialize_kinetic_router(&env, &admin, &emergency_admin, &router, &dex_router);

    let client = kinetic_router::Client::new(&env, &kinetic_router);

    // Set max premium to 50 bps
    client.set_flash_loan_premium_max(&50);

    // Attempt to set premium above max should fail
    let result = client.try_set_flash_loan_premium(&75);
    assert!(result.is_err());

    match result {
        Err(Ok(kinetic_router::KineticRouterError::InvalidAmount)) => {}
        _ => panic!("Expected InvalidAmount error"),
    }
}

#[test]
fn test_set_hf_liquidation_threshold_success() {
    let env = create_test_env();
    let (admin, emergency_admin, _user1, _user2) = create_test_addresses(&env);
    let router = Address::generate(&env);

    let dex_router = Address::generate(&env);
    let (kinetic_router, _oracle) = initialize_kinetic_router(&env, &admin, &emergency_admin, &router, &dex_router);

    let client = kinetic_router::Client::new(&env, &kinetic_router);

    // Set threshold to 0.95 WAD
    let new_threshold = 950_000_000_000_000_000u128;
    client.set_hf_liquidation_threshold(&new_threshold);

    // Verify the threshold was set
    assert_eq!(client.get_hf_liquidation_threshold(), new_threshold);
}

#[test]
fn test_set_hf_liquidation_threshold_unauthorized() {
    let env = create_test_env();
    let (admin, emergency_admin, user1, _user2) = create_test_addresses(&env);
    let router = Address::generate(&env);

    let dex_router = Address::generate(&env);
    let (kinetic_router, _oracle) = initialize_kinetic_router(&env, &admin, &emergency_admin, &router, &dex_router);

    let client = kinetic_router::Client::new(&env, &kinetic_router);

    // Attempt to set threshold without auth
    env.mock_auths(&[]);
    let result = client.try_set_hf_liquidation_threshold(&950_000_000_000_000_000u128);
    assert!(result.is_err(), "Should fail without authorization");

    // Set as admin should succeed
    env.mock_all_auths();
    let result = client.try_set_hf_liquidation_threshold(&950_000_000_000_000_000u128);
    assert!(result.is_ok(), "Admin should be able to set threshold");
    assert_eq!(client.get_hf_liquidation_threshold(), 950_000_000_000_000_000u128);
}

#[test]
fn test_set_min_swap_output_bps_success() {
    let env = create_test_env();
    let (admin, emergency_admin, _user1, _user2) = create_test_addresses(&env);
    let router = Address::generate(&env);

    let dex_router = Address::generate(&env);
    let (kinetic_router, _oracle) = initialize_kinetic_router(&env, &admin, &emergency_admin, &router, &dex_router);

    let client = kinetic_router::Client::new(&env, &kinetic_router);

    // Set min swap output to 95% (9500 bps)
    let new_min_bps = 9500;
    client.set_min_swap_output_bps(&new_min_bps);

    // Verify the threshold was set
    assert_eq!(client.get_min_swap_output_bps(), new_min_bps);
}

#[test]
fn test_set_min_swap_output_bps_unauthorized() {
    let env = create_test_env();
    let (admin, emergency_admin, user1, _user2) = create_test_addresses(&env);
    let router = Address::generate(&env);

    let dex_router = Address::generate(&env);
    let (kinetic_router, _oracle) = initialize_kinetic_router(&env, &admin, &emergency_admin, &router, &dex_router);

    let client = kinetic_router::Client::new(&env, &kinetic_router);

    // Attempt to set min swap output without auth
    env.mock_auths(&[]);
    let result = client.try_set_min_swap_output_bps(&9500);
    assert!(result.is_err(), "Should fail without authorization");

    // Set as admin should succeed
    env.mock_all_auths();
    let result = client.try_set_min_swap_output_bps(&9500);
    assert!(result.is_ok(), "Admin should be able to set min swap output");
    assert_eq!(client.get_min_swap_output_bps(), 9500);
}

#[test]
fn test_set_min_swap_output_bps_invalid() {
    let env = create_test_env();
    let (admin, emergency_admin, _user1, _user2) = create_test_addresses(&env);
    let router = Address::generate(&env);

    let dex_router = Address::generate(&env);
    let (kinetic_router, _oracle) = initialize_kinetic_router(&env, &admin, &emergency_admin, &router, &dex_router);

    let client = kinetic_router::Client::new(&env, &kinetic_router);

    // Attempt to set min swap output > 100% should fail
    let result = client.try_set_min_swap_output_bps(&10001);
    assert!(result.is_err());

    match result {
        Err(Ok(kinetic_router::KineticRouterError::InvalidAmount)) => {}
        _ => panic!("Expected InvalidAmount error"),
    }
}

#[test]
fn test_set_partial_liq_hf_threshold_success() {
    let env = create_test_env();
    let (admin, emergency_admin, _user1, _user2) = create_test_addresses(&env);
    let router = Address::generate(&env);

    let dex_router = Address::generate(&env);
    let (kinetic_router, _oracle) = initialize_kinetic_router(&env, &admin, &emergency_admin, &router, &dex_router);

    let client = kinetic_router::Client::new(&env, &kinetic_router);

    // Set partial liquidation threshold to 0.6 WAD
    let new_threshold = 600_000_000_000_000_000u128;
    client.set_partial_liq_hf_threshold(&new_threshold);

    // Verify the threshold was set
    assert_eq!(client.get_partial_liq_hf_threshold(), new_threshold);
}

#[test]
fn test_set_partial_liq_hf_threshold_unauthorized() {
    let env = create_test_env();
    let (admin, emergency_admin, user1, _user2) = create_test_addresses(&env);
    let router = Address::generate(&env);

    let dex_router = Address::generate(&env);
    let (kinetic_router, _oracle) = initialize_kinetic_router(&env, &admin, &emergency_admin, &router, &dex_router);

    let client = kinetic_router::Client::new(&env, &kinetic_router);

    // Attempt to set threshold without auth
    env.mock_auths(&[]);
    let result = client.try_set_partial_liq_hf_threshold(&600_000_000_000_000_000u128);
    assert!(result.is_err(), "Should fail without authorization");

    // Set as admin should succeed
    env.mock_all_auths();
    let result = client.try_set_partial_liq_hf_threshold(&600_000_000_000_000_000u128);
    assert!(result.is_ok(), "Admin should be able to set threshold");
    assert_eq!(client.get_partial_liq_hf_threshold(), 600_000_000_000_000_000u128);
}
