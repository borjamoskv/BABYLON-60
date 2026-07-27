#![cfg(test)]
//! Gated pool whitelist tests
//!
//! Tests per-reserve whitelist access control for lending pool operations.
//! Empty whitelist allows all users (backward compatible).
//! Non-empty whitelist restricts access to listed addresses only.

use crate::kinetic_router;
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
    let user1 = Address::generate(env);
    let user2 = Address::generate(env);
    let non_whitelisted_user = Address::generate(env);
    (admin, emergency_admin, user1, user2, non_whitelisted_user)
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

    (underlying_asset, asset_client)
}

#[test]
fn test_set_reserve_whitelist_as_admin() {
    let env = create_test_env();
    let (admin, emergency_admin, user1, user2, _) = create_test_addresses(&env);

    let kinetic_router = initialize_kinetic_router(&env, &admin, &emergency_admin);
    let client = kinetic_router::Client::new(&env, &kinetic_router);

    let (asset, _) = create_and_init_test_reserve(&env, &kinetic_router, &admin);

    // Set whitelist with two users
    let mut whitelist = Vec::new(&env);
    whitelist.push_back(user1.clone());
    whitelist.push_back(user2.clone());

    client.set_reserve_whitelist(&asset, &whitelist);

    // Verify whitelist was set
    let retrieved_whitelist = client.get_reserve_whitelist(&asset);
    assert_eq!(retrieved_whitelist.len(), 2);
    assert_eq!(retrieved_whitelist.get(0).unwrap(), user1);
    assert_eq!(retrieved_whitelist.get(1).unwrap(), user2);
}

#[test]
fn test_set_reserve_whitelist_as_non_admin() {
    let env = create_test_env();
    let (admin, emergency_admin, user1, user2, _) = create_test_addresses(&env);

    let kinetic_router = initialize_kinetic_router(&env, &admin, &emergency_admin);
    let client = kinetic_router::Client::new(&env, &kinetic_router);

    let (asset, _) = create_and_init_test_reserve(&env, &kinetic_router, &admin);

    let mut whitelist = Vec::new(&env);
    whitelist.push_back(user1.clone());

    // Clear auth mocking to test unauthorized access
    env.mock_auths(&[]);
    
    // Non-admin should not be able to set whitelist
    let result = client.try_set_reserve_whitelist(&asset, &whitelist);
    assert!(result.is_err());
}

#[test]
fn test_empty_whitelist_allows_all() {
    let env = create_test_env();
    let (admin, emergency_admin, _, _, non_whitelisted) = create_test_addresses(&env);

    let kinetic_router = initialize_kinetic_router(&env, &admin, &emergency_admin);
    let client = kinetic_router::Client::new(&env, &kinetic_router);

    let (asset, _asset_contract) = create_and_init_test_reserve(&env, &kinetic_router, &admin);

    // Verify whitelist is empty
    let whitelist = client.get_reserve_whitelist(&asset);
    assert_eq!(whitelist.len(), 0, "Whitelist should be empty initially");
    
    // Verify is_whitelisted returns true for empty whitelist
    assert!(
        client.is_whitelisted_for_reserve(&asset, &non_whitelisted),
        "Empty whitelist should allow all addresses"
    );
    
    // With empty whitelist, the whitelist check should pass
    let result = client.try_supply(&non_whitelisted, &asset, &100_000u128, &non_whitelisted, &0u32);
    
    // Should NOT fail with AddressNotWhitelisted error
    match result {
        Err(Ok(kinetic_router::KineticRouterError::AddressNotWhitelisted)) => {
            panic!("Empty whitelist should not block access - whitelist validation failed");
        }
        _ => {} // Other errors are expected (no token setup)
    }
}

#[test]
fn test_whitelisted_user_can_supply() {
    let env = create_test_env();
    let (admin, emergency_admin, user1, _, _) = create_test_addresses(&env);

    let kinetic_router = initialize_kinetic_router(&env, &admin, &emergency_admin);
    let client = kinetic_router::Client::new(&env, &kinetic_router);

    let (asset, _asset_contract) = create_and_init_test_reserve(&env, &kinetic_router, &admin);

    // Set whitelist with user1
    let mut whitelist = Vec::new(&env);
    whitelist.push_back(user1.clone());
    client.set_reserve_whitelist(&asset, &whitelist);

    // Verify whitelist was set correctly
    let retrieved_whitelist = client.get_reserve_whitelist(&asset);
    assert_eq!(retrieved_whitelist.len(), 1, "Whitelist should have 1 address");
    assert_eq!(retrieved_whitelist.get(0).unwrap(), user1, "user1 should be in whitelist");
    
    // Verify is_whitelisted returns true for whitelisted user
    assert!(
        client.is_whitelisted_for_reserve(&asset, &user1),
        "user1 should be whitelisted"
    );

    // Whitelisted user should pass the whitelist check
    let result = client.try_supply(&user1, &asset, &100_000u128, &user1, &0u32);
    
    // Should NOT fail with AddressNotWhitelisted error
    match result {
        Err(Ok(kinetic_router::KineticRouterError::AddressNotWhitelisted)) => {
            panic!("Whitelisted user should not be blocked by whitelist - validation failed");
        }
        _ => {} // Other errors are expected (no token setup)
    }
}

#[test]
fn test_non_whitelisted_user_cannot_supply() {
    let env = create_test_env();
    let (admin, emergency_admin, user1, _, non_whitelisted) = create_test_addresses(&env);

    let kinetic_router = initialize_kinetic_router(&env, &admin, &emergency_admin);
    let client = kinetic_router::Client::new(&env, &kinetic_router);

    let (asset, _asset_contract) = create_and_init_test_reserve(&env, &kinetic_router, &admin);

    // Set whitelist with only user1
    let mut whitelist = Vec::new(&env);
    whitelist.push_back(user1.clone());
    client.set_reserve_whitelist(&asset, &whitelist);

    // Verify non_whitelisted is NOT in the whitelist
    assert!(
        !client.is_whitelisted_for_reserve(&asset, &non_whitelisted),
        "non_whitelisted should NOT be whitelisted"
    );
    
    // Verify user1 IS in the whitelist (sanity check)
    assert!(
        client.is_whitelisted_for_reserve(&asset, &user1),
        "user1 should be whitelisted"
    );

    // Non-whitelisted user should NOT be able to supply
    let result = client.try_supply(&non_whitelisted, &asset, &100_000u128, &non_whitelisted, &0u32);
    assert!(result.is_err(), "Non-whitelisted user should not be able to supply");
    
    // Verify it's specifically the AddressNotWhitelisted error
    match result {
        Err(Ok(err)) => assert_eq!(
            err,
            kinetic_router::KineticRouterError::AddressNotWhitelisted,
            "Should fail with AddressNotWhitelisted error"
        ),
        _ => panic!("Expected AddressNotWhitelisted error"),
    }
}

#[test]
fn test_whitelisted_user_can_withdraw() {
    let env = create_test_env();

    let (admin, emergency_admin, user1, _, _) = create_test_addresses(&env);

    let kinetic_router = initialize_kinetic_router(&env, &admin, &emergency_admin);
    let client = kinetic_router::Client::new(&env, &kinetic_router);

    let (asset, _asset_contract) = create_and_init_test_reserve(&env, &kinetic_router, &admin);

    // Set whitelist with user1
    let mut whitelist = Vec::new(&env);
    whitelist.push_back(user1.clone());
    client.set_reserve_whitelist(&asset, &whitelist);

    // Verify user1 is whitelisted
    assert!(
        client.is_whitelisted_for_reserve(&asset, &user1),
        "user1 should be whitelisted"
    );

    // Whitelisted user should pass the whitelist check
    let result = client.try_withdraw(&user1, &asset, &50_000u128, &user1);
    
    // Should NOT fail with AddressNotWhitelisted error
    match result {
        Err(Ok(kinetic_router::KineticRouterError::AddressNotWhitelisted)) => {
            panic!("Whitelisted user should not be blocked by whitelist - validation failed");
        }
        _ => {} // Other errors are expected (insufficient collateral, etc.)
    }
}

#[test]
fn test_non_whitelisted_user_cannot_withdraw() {
    let env = create_test_env();

    let (admin, emergency_admin, user1, _, non_whitelisted) = create_test_addresses(&env);

    let kinetic_router = initialize_kinetic_router(&env, &admin, &emergency_admin);
    let client = kinetic_router::Client::new(&env, &kinetic_router);

    let (asset, _asset_contract) = create_and_init_test_reserve(&env, &kinetic_router, &admin);

    // Set whitelist with only user1
    let mut whitelist = Vec::new(&env);
    whitelist.push_back(user1.clone());
    client.set_reserve_whitelist(&asset, &whitelist);

    // Non-whitelisted user should NOT be able to withdraw
    let result = client.try_withdraw(&non_whitelisted, &asset, &50_000u128, &non_whitelisted);
    
    // Should fail specifically with AddressNotWhitelisted error
    match result {
        Err(Ok(err)) => assert_eq!(err, kinetic_router::KineticRouterError::AddressNotWhitelisted),
        _ => panic!("Expected AddressNotWhitelisted error"),
    }
}

#[test]
fn test_whitelisted_user_can_borrow() {
    let env = create_test_env();

    let (admin, emergency_admin, user1, _, _) = create_test_addresses(&env);

    let kinetic_router = initialize_kinetic_router(&env, &admin, &emergency_admin);
    let client = kinetic_router::Client::new(&env, &kinetic_router);

    let (asset, _asset_contract) = create_and_init_test_reserve(&env, &kinetic_router, &admin);

    // Set whitelist with user1
    let mut whitelist = Vec::new(&env);
    whitelist.push_back(user1.clone());
    client.set_reserve_whitelist(&asset, &whitelist);

    // Verify user1 is whitelisted
    assert!(
        client.is_whitelisted_for_reserve(&asset, &user1),
        "user1 should be whitelisted"
    );

    // Whitelisted user should pass the whitelist check
    let result = client.try_borrow(&user1, &asset, &10_000u128, &1u32, &0u32, &user1);
    
    // Should NOT fail with AddressNotWhitelisted error
    match result {
        Err(Ok(kinetic_router::KineticRouterError::AddressNotWhitelisted)) => {
            panic!("Whitelisted user should not be blocked by whitelist - validation failed");
        }
        _ => {} // Other errors are expected (insufficient collateral, etc.)
    }
}

#[test]
fn test_non_whitelisted_user_cannot_borrow() {
    let env = create_test_env();

    let (admin, emergency_admin, user1, _, non_whitelisted) = create_test_addresses(&env);

    let kinetic_router = initialize_kinetic_router(&env, &admin, &emergency_admin);
    let client = kinetic_router::Client::new(&env, &kinetic_router);

    let (asset, _asset_contract) = create_and_init_test_reserve(&env, &kinetic_router, &admin);



    // Now set whitelist with only user1
    let mut whitelist = Vec::new(&env);
    whitelist.push_back(user1.clone());
    client.set_reserve_whitelist(&asset, &whitelist);

    // Non-whitelisted user should NOT be able to borrow
    let result = client.try_borrow(&non_whitelisted, &asset, &10_000u128, &1u32, &0u32, &non_whitelisted);
    assert!(result.is_err(), "Non-whitelisted user should not be able to borrow");
    
    match result {
        Err(Ok(err)) => assert_eq!(err, kinetic_router::KineticRouterError::AddressNotWhitelisted),
        _ => panic!("Expected AddressNotWhitelisted error"),
    }
}

#[test]
fn test_whitelisted_user_can_repay() {
    let env = create_test_env();

    let (admin, emergency_admin, user1, _, _) = create_test_addresses(&env);

    let kinetic_router = initialize_kinetic_router(&env, &admin, &emergency_admin);
    let client = kinetic_router::Client::new(&env, &kinetic_router);

    let (asset, _asset_contract) = create_and_init_test_reserve(&env, &kinetic_router, &admin);

    // Set whitelist with user1
    let mut whitelist = Vec::new(&env);
    whitelist.push_back(user1.clone());
    client.set_reserve_whitelist(&asset, &whitelist);

    // Verify user1 is whitelisted
    assert!(
        client.is_whitelisted_for_reserve(&asset, &user1),
        "user1 should be whitelisted"
    );

    // Whitelisted user should pass the whitelist check
    let result = client.try_repay(&user1, &asset, &5_000u128, &1u32, &user1);
    
    // Should NOT fail with AddressNotWhitelisted error
    match result {
        Err(Ok(kinetic_router::KineticRouterError::AddressNotWhitelisted)) => {
            panic!("Whitelisted user should not be blocked by whitelist - validation failed");
        }
        _ => {} // Other errors are expected (no debt to repay, etc.)
    }
}

#[test]
fn test_non_whitelisted_user_cannot_repay() {
    let env = create_test_env();

    let (admin, emergency_admin, user1, _, non_whitelisted) = create_test_addresses(&env);

    let kinetic_router = initialize_kinetic_router(&env, &admin, &emergency_admin);
    let client = kinetic_router::Client::new(&env, &kinetic_router);

    let (asset, _asset_contract) = create_and_init_test_reserve(&env, &kinetic_router, &admin);



    // Now set whitelist with only user1
    let mut whitelist = Vec::new(&env);
    whitelist.push_back(user1.clone());
    client.set_reserve_whitelist(&asset, &whitelist);

    // Non-whitelisted user should NOT be able to repay
    let result = client.try_repay(&non_whitelisted, &asset, &5_000u128, &1u32, &non_whitelisted);
    assert!(result.is_err(), "Non-whitelisted user should not be able to repay");
    
    match result {
        Err(Ok(err)) => assert_eq!(err, kinetic_router::KineticRouterError::AddressNotWhitelisted),
        _ => panic!("Expected AddressNotWhitelisted error"),
    }
}

#[test]
fn test_multiple_reserves_independent_whitelists() {
    let env = create_test_env();

    let (admin, emergency_admin, user1, user2, _) = create_test_addresses(&env);

    let kinetic_router = initialize_kinetic_router(&env, &admin, &emergency_admin);
    let client = kinetic_router::Client::new(&env, &kinetic_router);

    // Create two reserves
    let (asset1, _) = create_and_init_test_reserve(&env, &kinetic_router, &admin);
    let (asset2, _) = create_and_init_test_reserve(&env, &kinetic_router, &admin);

    // Set whitelist for asset1 with user1
    let mut whitelist1 = Vec::new(&env);
    whitelist1.push_back(user1.clone());
    client.set_reserve_whitelist(&asset1, &whitelist1);

    // Set whitelist for asset2 with user2
    let mut whitelist2 = Vec::new(&env);
    whitelist2.push_back(user2.clone());
    client.set_reserve_whitelist(&asset2, &whitelist2);

    // user1 should NOT get AddressNotWhitelisted for asset1, but should for asset2
    let result1 = client.try_supply(&user1, &asset1, &100_000u128, &user1, &0u32);
    match result1 {
        Err(Ok(kinetic_router::KineticRouterError::AddressNotWhitelisted)) => {
            panic!("user1 should be whitelisted for asset1");
        }
        _ => {} // Other errors or success are fine
    }
    
    let result2 = client.try_supply(&user1, &asset2, &100_000u128, &user1, &0u32);
    match result2 {
        Err(Ok(kinetic_router::KineticRouterError::AddressNotWhitelisted)) => {} // Expected
        _ => panic!("user1 should NOT be whitelisted for asset2"),
    }

    // user2 should access asset2 but not asset1
    let result3 = client.try_supply(&user2, &asset2, &100_000u128, &user2, &0u32);
    match result3 {
        Err(Ok(kinetic_router::KineticRouterError::AddressNotWhitelisted)) => {
            panic!("user2 should be whitelisted for asset2");
        }
        _ => {} // Other errors or success are fine
    }
    
    let result4 = client.try_supply(&user2, &asset1, &100_000u128, &user2, &0u32);
    match result4 {
        Err(Ok(kinetic_router::KineticRouterError::AddressNotWhitelisted)) => {} // Expected
        _ => panic!("user2 should NOT be whitelisted for asset1"),
    }
}

#[test]
fn test_is_address_whitelisted_for_reserve() {
    let env = create_test_env();

    let (admin, emergency_admin, user1, user2, non_whitelisted) = create_test_addresses(&env);

    let kinetic_router = initialize_kinetic_router(&env, &admin, &emergency_admin);
    let client = kinetic_router::Client::new(&env, &kinetic_router);

    let (asset, _) = create_and_init_test_reserve(&env, &kinetic_router, &admin);

    // Initially, everyone should be whitelisted (empty whitelist)
    assert!(client.is_whitelisted_for_reserve(&asset, &user1));
    assert!(client.is_whitelisted_for_reserve(&asset, &non_whitelisted));

    // Set whitelist with user1 and user2
    let mut whitelist = Vec::new(&env);
    whitelist.push_back(user1.clone());
    whitelist.push_back(user2.clone());
    client.set_reserve_whitelist(&asset, &whitelist);

    // Check whitelist status
    assert!(client.is_whitelisted_for_reserve(&asset, &user1));
    assert!(client.is_whitelisted_for_reserve(&asset, &user2));
    assert!(!client.is_whitelisted_for_reserve(&asset, &non_whitelisted));
}

#[test]
fn test_clear_whitelist() {
    let env = create_test_env();

    let (admin, emergency_admin, user1, _, non_whitelisted) = create_test_addresses(&env);

    let kinetic_router = initialize_kinetic_router(&env, &admin, &emergency_admin);
    let client = kinetic_router::Client::new(&env, &kinetic_router);

    let (asset, _asset_contract) = create_and_init_test_reserve(&env, &kinetic_router, &admin);

    // Set whitelist with only user1
    let mut whitelist = Vec::new(&env);
    whitelist.push_back(user1.clone());
    client.set_reserve_whitelist(&asset, &whitelist);

    // Verify whitelist has 1 entry
    assert_eq!(client.get_reserve_whitelist(&asset).len(), 1, "Whitelist should have 1 entry");
    
    // Verify non_whitelisted is NOT whitelisted
    assert!(
        !client.is_whitelisted_for_reserve(&asset, &non_whitelisted),
        "non_whitelisted should NOT be whitelisted"
    );

    // Verify non_whitelisted gets AddressNotWhitelisted error
    let result1 = client.try_supply(&non_whitelisted, &asset, &100_000u128, &non_whitelisted, &0u32);
    match result1 {
        Err(Ok(kinetic_router::KineticRouterError::AddressNotWhitelisted)) => {} // Expected
        _ => panic!("Non-whitelisted user should be blocked when whitelist is active"),
    }

    // Clear whitelist (set to empty)
    let empty_whitelist = Vec::new(&env);
    client.set_reserve_whitelist(&asset, &empty_whitelist);

    // Verify whitelist is now empty
    assert_eq!(client.get_reserve_whitelist(&asset).len(), 0, "Whitelist should be empty");
    
    // Verify non_whitelisted IS now whitelisted (because empty whitelist allows all)
    assert!(
        client.is_whitelisted_for_reserve(&asset, &non_whitelisted),
        "Empty whitelist should allow all addresses"
    );

    // Now non_whitelisted should NOT get AddressNotWhitelisted error
    let result2 = client.try_supply(&non_whitelisted, &asset, &100_000u128, &non_whitelisted, &0u32);
    match result2 {
        Err(Ok(kinetic_router::KineticRouterError::AddressNotWhitelisted)) => {
            panic!("Clearing whitelist should allow all users - validation failed");
        }
        _ => {} // Other errors are expected
    }
}

