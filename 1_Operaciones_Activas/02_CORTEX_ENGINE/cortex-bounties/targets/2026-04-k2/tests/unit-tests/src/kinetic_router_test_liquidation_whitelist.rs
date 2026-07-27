#![cfg(test)]
//! Liquidation whitelist tests
//!
//! Tests liquidation whitelist access control for liquidation operations.
//! Empty whitelist allows all liquidators (backward compatible).
//! Non-empty whitelist restricts liquidation access to listed addresses only.

use k2_kinetic_router::router::KineticRouterContractClient;
use k2_kinetic_router::KineticRouterContract;

use k2_shared::{InitReserveParams, KineticRouterError};
use soroban_sdk::{
    testutils::Address as _,
    token::StellarAssetClient,
    Address, Env, Vec,
};

fn create_test_env() -> Env {
    let env = Env::default();
    env.mock_all_auths();
    env
}

fn create_test_addresses(env: &Env) -> (Address, Address, Address, Address, Address) {
    let admin = Address::generate(env);
    let emergency_admin = Address::generate(env);
    let liquidator1 = Address::generate(env);
    let liquidator2 = Address::generate(env);
    let non_whitelisted_liquidator = Address::generate(env);
    (admin, emergency_admin, liquidator1, liquidator2, non_whitelisted_liquidator)
}

fn initialize_kinetic_router(env: &Env, admin: &Address, emergency_admin: &Address) -> Address {
    let contract_id = env.register(KineticRouterContract, ());
    let client = KineticRouterContractClient::new(env, &contract_id);

    let price_oracle = Address::generate(env);
    let treasury = Address::generate(env);
    let dex_router = Address::generate(env);

    client.initialize(admin, emergency_admin, &price_oracle, &treasury, &dex_router, &None);
    
    let pool_configurator = Address::generate(env);
    client.set_pool_configurator(&pool_configurator);

    contract_id
}

fn create_and_init_test_reserve<'a>(
    env: &'a Env,
    kinetic_router: &Address,
    admin: &Address,
) -> (Address, StellarAssetClient<'a>) {
    let underlying_asset_contract = env.register_stellar_asset_contract_v2(admin.clone());
    let underlying_asset = underlying_asset_contract.address();
    let asset_client = StellarAssetClient::new(env, &underlying_asset);

    let a_token_impl = Address::generate(env);
    let debt_token_impl = Address::generate(env);
    let interest_rate_strategy = Address::generate(env);
    let treasury = Address::generate(env);

    let params = InitReserveParams {
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

    let client = KineticRouterContractClient::new(env, kinetic_router);
    let pool_configurator = Address::generate(env);
    client.set_pool_configurator(&pool_configurator);
    client.init_reserve(
        &pool_configurator,
        &underlying_asset,
        &a_token_impl,
        &debt_token_impl,
        &interest_rate_strategy,
        &treasury,
        &params,
    );

    (underlying_asset, asset_client)
}

#[test]
fn test_set_liquidation_whitelist_as_admin() {
    let env = create_test_env();
    let (admin, emergency_admin, liquidator1, liquidator2, _) = create_test_addresses(&env);

    let kinetic_router = initialize_kinetic_router(&env, &admin, &emergency_admin);
    let client = KineticRouterContractClient::new(&env, &kinetic_router);

    // Set whitelist with two liquidators
    let mut whitelist = Vec::new(&env);
    whitelist.push_back(liquidator1.clone());
    whitelist.push_back(liquidator2.clone());

    client.set_liquidation_whitelist(&whitelist);

    // Verify whitelist was set
    let retrieved_whitelist = client.get_liquidation_whitelist();
    assert_eq!(retrieved_whitelist.len(), 2);
    assert_eq!(retrieved_whitelist.get(0).unwrap(), liquidator1);
    assert_eq!(retrieved_whitelist.get(1).unwrap(), liquidator2);
}

#[test]
fn test_set_liquidation_whitelist_as_non_admin_fails() {
    let env = create_test_env();
    let (admin, emergency_admin, liquidator1, liquidator2, non_admin) = create_test_addresses(&env);

    let kinetic_router = initialize_kinetic_router(&env, &admin, &emergency_admin);
    let client = KineticRouterContractClient::new(&env, &kinetic_router);

    // Try to set whitelist as non-admin
    let mut whitelist = Vec::new(&env);
    whitelist.push_back(liquidator1.clone());
    whitelist.push_back(liquidator2.clone());

    // Clear auth mocking to test unauthorized access
    env.mock_auths(&[]);
    
    let result = client.try_set_liquidation_whitelist(&whitelist);
    assert!(result.is_err(), "Non-admin should not be able to set whitelist");

    // Set as admin should succeed
    env.mock_all_auths();
    let result = client.try_set_liquidation_whitelist(&whitelist);
    assert!(result.is_ok(), "Admin should be able to set whitelist");
}

#[test]
fn test_empty_liquidation_whitelist_allows_all() {
    let env = create_test_env();
    let (admin, emergency_admin, liquidator1, _, non_whitelisted) = create_test_addresses(&env);

    let kinetic_router = initialize_kinetic_router(&env, &admin, &emergency_admin);
    let client = KineticRouterContractClient::new(&env, &kinetic_router);

    // Empty whitelist should allow all addresses
    let empty_whitelist = Vec::new(&env);
    client.set_liquidation_whitelist(&empty_whitelist);

    // All addresses should be considered whitelisted
    assert!(client.is_whitelisted_for_liquidation(&liquidator1));
    assert!(client.is_whitelisted_for_liquidation(&non_whitelisted));
    assert!(client.is_whitelisted_for_liquidation(&admin));
}

#[test]
fn test_non_empty_liquidation_whitelist_restricts_access() {
    let env = create_test_env();
    let (admin, emergency_admin, liquidator1, liquidator2, non_whitelisted) = create_test_addresses(&env);

    let kinetic_router = initialize_kinetic_router(&env, &admin, &emergency_admin);
    let client = KineticRouterContractClient::new(&env, &kinetic_router);

    // Set whitelist with only liquidator1
    let mut whitelist = Vec::new(&env);
    whitelist.push_back(liquidator1.clone());
    client.set_liquidation_whitelist(&whitelist);

    // liquidator1 should be whitelisted
    assert!(client.is_whitelisted_for_liquidation(&liquidator1));

    // liquidator2 and non_whitelisted should NOT be whitelisted
    assert!(!client.is_whitelisted_for_liquidation(&liquidator2));
    assert!(!client.is_whitelisted_for_liquidation(&non_whitelisted));
}

#[test]
fn test_liquidation_whitelist_blocks_liquidation_call() {
    let env = create_test_env();
    let (admin, emergency_admin, liquidator1, _, non_whitelisted) = create_test_addresses(&env);

    let kinetic_router = initialize_kinetic_router(&env, &admin, &emergency_admin);
    let client = KineticRouterContractClient::new(&env, &kinetic_router);

    // Create test reserve
    let (asset, _) = create_and_init_test_reserve(&env, &kinetic_router, &admin);

    // Set whitelist with only liquidator1
    let mut whitelist = Vec::new(&env);
    whitelist.push_back(liquidator1.clone());
    client.set_liquidation_whitelist(&whitelist);

    // Create a user with a position to liquidate
    let user = Address::generate(&env);

    // Non-whitelisted liquidator should NOT be able to liquidate
    let result = client.try_liquidation_call(
        &non_whitelisted,
        &asset,
        &asset,
        &user,
        &1000u128,
        &false,
    );
    assert!(result.is_err(), "Non-whitelisted liquidator should not be able to liquidate");

    match result {
        Err(Ok(err)) => assert_eq!(err, KineticRouterError::AddressNotWhitelisted),
        _ => panic!("Expected AddressNotWhitelisted error"),
    }
}

#[test]
fn test_liquidation_whitelist_allows_whitelisted_liquidator() {
    let env = create_test_env();
    let (admin, emergency_admin, liquidator1, _, _non_whitelisted) = create_test_addresses(&env);

    let kinetic_router = initialize_kinetic_router(&env, &admin, &emergency_admin);
    let client = KineticRouterContractClient::new(&env, &kinetic_router);

    // Create test reserve
    let (asset, _) = create_and_init_test_reserve(&env, &kinetic_router, &admin);

    // Set whitelist with liquidator1
    let mut whitelist = Vec::new(&env);
    whitelist.push_back(liquidator1.clone());
    client.set_liquidation_whitelist(&whitelist);

    // Create a user with a position to liquidate
    let user = Address::generate(&env);

    // Whitelisted liquidator should be able to call liquidation (though it may fail for other reasons)
    let result = client.try_liquidation_call(
        &liquidator1,
        &asset,
        &asset,
        &user,
        &1000u128,
        &false,
    );

    // The call should NOT fail with AddressNotWhitelisted
    // It may fail for other reasons (invalid liquidation, etc.) but not whitelist
    match result {
        Err(Ok(KineticRouterError::AddressNotWhitelisted)) => {
            panic!("Whitelisted liquidator should not get AddressNotWhitelisted error");
        }
        _ => {} // Other errors or success are acceptable
    }
}
