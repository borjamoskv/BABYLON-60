#![cfg(test)]
//! Blacklist tests
//!
//! Tests blacklist access control for core functions and liquidation operations.
//! Empty blacklist allows all addresses (backward compatible).
//! Non-empty blacklist blocks listed addresses.

use crate::kinetic_router;
use soroban_sdk::{
    testutils::{Address as _, StellarAssetContract},
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
    let user1 = Address::generate(env);
    let user2 = Address::generate(env);
    let blacklisted_user = Address::generate(env);
    (admin, emergency_admin, user1, user2, blacklisted_user)
}

fn initialize_kinetic_router(env: &Env, admin: &Address, emergency_admin: &Address) -> Address {
    let contract_id = env.register(kinetic_router::WASM, ());
    let client = kinetic_router::Client::new(env, &contract_id);

    let price_oracle = Address::generate(env);
    let treasury = Address::generate(env);
    let dex_router = Address::generate(env);

    client.initialize(admin, emergency_admin, &price_oracle, &treasury, &dex_router, &None);
    
    let pool_configurator = Address::generate(env);
    client.set_pool_configurator(&pool_configurator);

    contract_id
}

fn create_and_init_test_reserve(
    env: &Env,
    kinetic_router: &Address,
    admin: &Address,
) -> (Address, StellarAssetContract) {
    let underlying_asset_contract = env.register_stellar_asset_contract_v2(admin.clone());
    let underlying_asset = underlying_asset_contract.address();

    let a_token_impl = Address::generate(env);
    let debt_token_impl = Address::generate(env);
    let interest_rate_strategy = Address::generate(env);
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

    let client = kinetic_router::Client::new(env, kinetic_router);
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

    (underlying_asset, underlying_asset_contract)
}

#[test]
fn test_set_reserve_blacklist_as_admin() {
    let env = create_test_env();
    let (admin, emergency_admin, user1, user2, _) = create_test_addresses(&env);

    let kinetic_router = initialize_kinetic_router(&env, &admin, &emergency_admin);
    let client = kinetic_router::Client::new(&env, &kinetic_router);

    let (asset, _) = create_and_init_test_reserve(&env, &kinetic_router, &admin);

    // Set blacklist with two users
    let mut blacklist = Vec::new(&env);
    blacklist.push_back(user1.clone());
    blacklist.push_back(user2.clone());

    client.set_reserve_blacklist(&asset, &blacklist);

    // Verify blacklist was set
    let retrieved_blacklist = client.get_reserve_blacklist(&asset);
    assert_eq!(retrieved_blacklist.len(), 2);
    assert_eq!(retrieved_blacklist.get(0).unwrap(), user1);
    assert_eq!(retrieved_blacklist.get(1).unwrap(), user2);
}

#[test]
fn test_set_reserve_blacklist_as_non_admin_fails() {
    let env = create_test_env();
    let (admin, emergency_admin, user1, user2, non_admin) = create_test_addresses(&env);

    let kinetic_router = initialize_kinetic_router(&env, &admin, &emergency_admin);
    let client = kinetic_router::Client::new(&env, &kinetic_router);

    let (asset, _) = create_and_init_test_reserve(&env, &kinetic_router, &admin);

    // Try to set blacklist as non-admin
    let mut blacklist = Vec::new(&env);
    blacklist.push_back(user1.clone());
    blacklist.push_back(user2.clone());

    // Clear auth mocking to test unauthorized access
    env.mock_auths(&[]);
    
    let result = client.try_set_reserve_blacklist(&asset, &blacklist);
    assert!(result.is_err(), "Non-admin should not be able to set blacklist");

    // Set as admin should succeed
    env.mock_all_auths();
    let result = client.try_set_reserve_blacklist(&asset, &blacklist);
    assert!(result.is_ok(), "Admin should be able to set blacklist");
}

#[test]
fn test_empty_reserve_blacklist_allows_all() {
    let env = create_test_env();
    let (admin, emergency_admin, user1, _, blacklisted) = create_test_addresses(&env);

    let kinetic_router = initialize_kinetic_router(&env, &admin, &emergency_admin);
    let client = kinetic_router::Client::new(&env, &kinetic_router);

    let (asset, _) = create_and_init_test_reserve(&env, &kinetic_router, &admin);

    // Empty blacklist should allow all addresses
    let empty_blacklist = Vec::new(&env);
    client.set_reserve_blacklist(&asset, &empty_blacklist);

    // All addresses should be considered not blacklisted
    assert!(!client.is_blacklisted_for_reserve(&asset, &user1));
    assert!(!client.is_blacklisted_for_reserve(&asset, &blacklisted));
    assert!(!client.is_blacklisted_for_reserve(&asset, &admin));
}

#[test]
fn test_non_empty_reserve_blacklist_blocks_access() {
    let env = create_test_env();
    let (admin, emergency_admin, user1, _user2, blacklisted) = create_test_addresses(&env);

    let kinetic_router = initialize_kinetic_router(&env, &admin, &emergency_admin);
    let client = kinetic_router::Client::new(&env, &kinetic_router);

    let (asset, _) = create_and_init_test_reserve(&env, &kinetic_router, &admin);

    // Set blacklist with only blacklisted user
    let mut blacklist = Vec::new(&env);
    blacklist.push_back(blacklisted.clone());
    client.set_reserve_blacklist(&asset, &blacklist);

    // user1 should not be blacklisted
    assert!(!client.is_blacklisted_for_reserve(&asset, &user1));

    // blacklisted user should be blocked
    assert!(client.is_blacklisted_for_reserve(&asset, &blacklisted));
}

#[test]
fn test_reserve_blacklist_blocks_supply() {
    let env = create_test_env();
    let (admin, emergency_admin, _user1, _, blacklisted) = create_test_addresses(&env);

    let kinetic_router = initialize_kinetic_router(&env, &admin, &emergency_admin);
    let client = kinetic_router::Client::new(&env, &kinetic_router);

    let (asset, _) = create_and_init_test_reserve(&env, &kinetic_router, &admin);

    // Set blacklist with blacklisted user
    let mut blacklist = Vec::new(&env);
    blacklist.push_back(blacklisted.clone());
    client.set_reserve_blacklist(&asset, &blacklist);

    // Blacklisted user should NOT be able to supply
    let result = client.try_supply(&blacklisted, &asset, &100_000u128, &blacklisted, &0u32);
    assert!(result.is_err(), "Blacklisted user should not be able to supply");

    match result {
        Err(Ok(err)) => assert_eq!(err, kinetic_router::KineticRouterError::Unauthorized),
        _ => panic!("Expected Blacklisted error"),
    }
}

#[test]
fn test_reserve_blacklist_blocks_withdraw() {
    let env = create_test_env();
    let (admin, emergency_admin, _user1, _, blacklisted) = create_test_addresses(&env);

    let kinetic_router = initialize_kinetic_router(&env, &admin, &emergency_admin);
    let client = kinetic_router::Client::new(&env, &kinetic_router);

    let (asset, _) = create_and_init_test_reserve(&env, &kinetic_router, &admin);

    // Set blacklist with blacklisted user
    let mut blacklist = Vec::new(&env);
    blacklist.push_back(blacklisted.clone());
    client.set_reserve_blacklist(&asset, &blacklist);

    // Blacklisted user should NOT be able to withdraw
    let result = client.try_withdraw(&blacklisted, &asset, &1000u128, &blacklisted);
    assert!(result.is_err(), "Blacklisted user should not be able to withdraw");

    match result {
        Err(Ok(err)) => assert_eq!(err, kinetic_router::KineticRouterError::Unauthorized),
        _ => panic!("Expected Blacklisted error"),
    }
}

#[test]
fn test_reserve_blacklist_blocks_borrow() {
    let env = create_test_env();
    let (admin, emergency_admin, _user1, _, blacklisted) = create_test_addresses(&env);

    let kinetic_router = initialize_kinetic_router(&env, &admin, &emergency_admin);
    let client = kinetic_router::Client::new(&env, &kinetic_router);

    let (asset, _) = create_and_init_test_reserve(&env, &kinetic_router, &admin);

    // Set blacklist with blacklisted user
    let mut blacklist = Vec::new(&env);
    blacklist.push_back(blacklisted.clone());
    client.set_reserve_blacklist(&asset, &blacklist);

    // Blacklisted user should NOT be able to borrow
    let result = client.try_borrow(&blacklisted, &asset, &1000u128, &1u32, &0u32, &blacklisted);
    assert!(result.is_err(), "Blacklisted user should not be able to borrow");

    match result {
        Err(Ok(err)) => assert_eq!(err, kinetic_router::KineticRouterError::Unauthorized),
        _ => panic!("Expected Blacklisted error"),
    }
}

#[test]
fn test_reserve_blacklist_blocks_repay() {
    let env = create_test_env();
    let (admin, emergency_admin, _user1, _, blacklisted) = create_test_addresses(&env);

    let kinetic_router = initialize_kinetic_router(&env, &admin, &emergency_admin);
    let client = kinetic_router::Client::new(&env, &kinetic_router);

    let (asset, _) = create_and_init_test_reserve(&env, &kinetic_router, &admin);

    // Set blacklist with blacklisted user
    let mut blacklist = Vec::new(&env);
    blacklist.push_back(blacklisted.clone());
    client.set_reserve_blacklist(&asset, &blacklist);

    // Blacklisted user should NOT be able to repay
    let result = client.try_repay(&blacklisted, &asset, &1000u128, &1u32, &blacklisted);
    assert!(result.is_err(), "Blacklisted user should not be able to repay");

    match result {
        Err(Ok(err)) => assert_eq!(err, kinetic_router::KineticRouterError::Unauthorized),
        _ => panic!("Expected Blacklisted error"),
    }
}

#[test]
fn test_set_liquidation_blacklist_as_admin() {
    let env = create_test_env();
    let (admin, emergency_admin, liquidator1, liquidator2, _) = create_test_addresses(&env);

    let kinetic_router = initialize_kinetic_router(&env, &admin, &emergency_admin);
    let client = kinetic_router::Client::new(&env, &kinetic_router);

    // Set blacklist with two liquidators
    let mut blacklist = Vec::new(&env);
    blacklist.push_back(liquidator1.clone());
    blacklist.push_back(liquidator2.clone());

    client.set_liquidation_blacklist(&blacklist);

    // Verify blacklist was set
    let retrieved_blacklist = client.get_liquidation_blacklist();
    assert_eq!(retrieved_blacklist.len(), 2);
    assert_eq!(retrieved_blacklist.get(0).unwrap(), liquidator1);
    assert_eq!(retrieved_blacklist.get(1).unwrap(), liquidator2);
}

#[test]
fn test_empty_liquidation_blacklist_allows_all() {
    let env = create_test_env();
    let (admin, emergency_admin, liquidator1, _, blacklisted) = create_test_addresses(&env);

    let kinetic_router = initialize_kinetic_router(&env, &admin, &emergency_admin);
    let client = kinetic_router::Client::new(&env, &kinetic_router);

    // Empty blacklist should allow all addresses
    let empty_blacklist = Vec::new(&env);
    client.set_liquidation_blacklist(&empty_blacklist);

    // All addresses should be considered not blacklisted
    assert!(!client.is_blacklisted_for_liquidation(&liquidator1));
    assert!(!client.is_blacklisted_for_liquidation(&blacklisted));
    assert!(!client.is_blacklisted_for_liquidation(&admin));
}

#[test]
fn test_non_empty_liquidation_blacklist_blocks_access() {
    let env = create_test_env();
    let (admin, emergency_admin, liquidator1, _liquidator2, blacklisted) = create_test_addresses(&env);

    let kinetic_router = initialize_kinetic_router(&env, &admin, &emergency_admin);
    let client = kinetic_router::Client::new(&env, &kinetic_router);

    // Set blacklist with only blacklisted user
    let mut blacklist = Vec::new(&env);
    blacklist.push_back(blacklisted.clone());
    client.set_liquidation_blacklist(&blacklist);

    // liquidator1 should not be blacklisted
    assert!(!client.is_blacklisted_for_liquidation(&liquidator1));

    // blacklisted user should be blocked
    assert!(client.is_blacklisted_for_liquidation(&blacklisted));
}

#[test]
fn test_liquidation_blacklist_blocks_liquidation_call() {
    let env = create_test_env();
    let (admin, emergency_admin, _liquidator1, _, blacklisted) = create_test_addresses(&env);

    let kinetic_router = initialize_kinetic_router(&env, &admin, &emergency_admin);
    let client = kinetic_router::Client::new(&env, &kinetic_router);

    // Create test reserve
    let (asset, _) = create_and_init_test_reserve(&env, &kinetic_router, &admin);

    // Set blacklist with blacklisted liquidator
    let mut blacklist = Vec::new(&env);
    blacklist.push_back(blacklisted.clone());
    client.set_liquidation_blacklist(&blacklist);

    // Create a user with a position to liquidate
    let user = Address::generate(&env);

    // Blacklisted liquidator should NOT be able to liquidate
    let result = client.try_liquidation_call(
        &blacklisted,
        &asset,
        &asset,
        &user,
        &1000u128,
        &false,
    );
    assert!(result.is_err(), "Blacklisted liquidator should not be able to liquidate");

    match result {
        Err(Ok(err)) => assert_eq!(err, kinetic_router::KineticRouterError::Unauthorized),
        _ => panic!("Expected Blacklisted error"),
    }
}

#[test]
fn test_liquidation_blacklist_allows_non_blacklisted_liquidator() {
    let env = create_test_env();
    let (admin, emergency_admin, liquidator1, _, blacklisted) = create_test_addresses(&env);

    let kinetic_router = initialize_kinetic_router(&env, &admin, &emergency_admin);
    let client = kinetic_router::Client::new(&env, &kinetic_router);

    // Create test reserve
    let (asset, _) = create_and_init_test_reserve(&env, &kinetic_router, &admin);

    // Set blacklist with only blacklisted user
    let mut blacklist = Vec::new(&env);
    blacklist.push_back(blacklisted.clone());
    client.set_liquidation_blacklist(&blacklist);

    // Create a user with a position to liquidate
    let user = Address::generate(&env);

    // Non-blacklisted liquidator should be able to call liquidation (though it may fail for other reasons)
    let result = client.try_liquidation_call(
        &liquidator1,
        &asset,
        &asset,
        &user,
        &1000u128,
        &false,
    );

    // The call should NOT fail with Blacklisted
    // It may fail for other reasons (invalid liquidation, etc.) but not blacklist
    match result {
        Err(Ok(kinetic_router::KineticRouterError::Unauthorized)) => {
            panic!("Non-blacklisted liquidator should not get Blacklisted error");
        }
        _ => {} // Other errors or success are acceptable
    }
}
