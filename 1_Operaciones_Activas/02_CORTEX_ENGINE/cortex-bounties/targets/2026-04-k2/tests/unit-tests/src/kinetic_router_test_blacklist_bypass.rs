#![cfg(test)]
//! HIGH-003 Blacklist Bypass Regression Tests
//!
//! Validates that blacklist enforcement applies to ALL participants in delegated
//! operations, not just the caller. Tests the 6 architectural gaps:
//!   Gap 1: supply on_behalf_of blacklisted user
//!   Gap 2: aToken transfer from blacklisted sender (tested in a_token_test module)
//!   Gap 3: borrow on_behalf_of blacklisted user
//!   Gap 4: withdraw to blacklisted recipient
//!   Gap 5: repay on_behalf_of blacklisted user
//!   Gap 6: set_user_use_reserve_as_coll by blacklisted user

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

fn create_test_addresses(env: &Env) -> (Address, Address, Address, Address) {
    let admin = Address::generate(env);
    let emergency_admin = Address::generate(env);
    let proxy = Address::generate(env); // non-blacklisted caller
    let blacklisted = Address::generate(env);
    (admin, emergency_admin, proxy, blacklisted)
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

fn setup_blacklist(env: &Env, client: &kinetic_router::Client, asset: &Address, blacklisted: &Address) {
    let mut blacklist = Vec::new(env);
    blacklist.push_back(blacklisted.clone());
    client.set_reserve_blacklist(asset, &blacklist);
}

// =============================================================================
// Gap 1: supply on_behalf_of blacklisted user
// =============================================================================

#[test]
fn test_supply_on_behalf_of_blacklisted_user_rejected() {
    let env = create_test_env();
    let (admin, emergency_admin, proxy, blacklisted) = create_test_addresses(&env);

    let kinetic_router = initialize_kinetic_router(&env, &admin, &emergency_admin);
    let client = kinetic_router::Client::new(&env, &kinetic_router);
    let (asset, _) = create_and_init_test_reserve(&env, &kinetic_router, &admin);

    setup_blacklist(&env, &client, &asset, &blacklisted);

    // Non-blacklisted proxy tries to supply on behalf of blacklisted user
    let result = client.try_supply(&proxy, &asset, &100_000u128, &blacklisted, &0u32);
    assert!(result.is_err(), "Supply on behalf of blacklisted user must be rejected");

    match result {
        Err(Ok(err)) => assert_eq!(err, kinetic_router::KineticRouterError::Unauthorized),
        _ => panic!("Expected Unauthorized error for blacklisted beneficiary"),
    }
}

#[test]
fn test_supply_on_behalf_of_self_still_works_when_not_blacklisted() {
    let env = create_test_env();
    let (admin, emergency_admin, proxy, blacklisted) = create_test_addresses(&env);

    let kinetic_router = initialize_kinetic_router(&env, &admin, &emergency_admin);
    let client = kinetic_router::Client::new(&env, &kinetic_router);
    let (asset, _) = create_and_init_test_reserve(&env, &kinetic_router, &admin);

    setup_blacklist(&env, &client, &asset, &blacklisted);

    // Non-blacklisted proxy supplying for themselves should NOT get Unauthorized
    let result = client.try_supply(&proxy, &asset, &100_000u128, &proxy, &0u32);
    match result {
        Err(Ok(kinetic_router::KineticRouterError::Unauthorized)) => {
            panic!("Non-blacklisted user should not get Unauthorized when supplying for self");
        }
        _ => {} // Other errors (e.g., insufficient balance) or success are fine
    }
}

// =============================================================================
// Gap 3: borrow on_behalf_of blacklisted user
// =============================================================================

#[test]
fn test_borrow_on_behalf_of_blacklisted_user_rejected() {
    let env = create_test_env();
    let (admin, emergency_admin, proxy, blacklisted) = create_test_addresses(&env);

    let kinetic_router = initialize_kinetic_router(&env, &admin, &emergency_admin);
    let client = kinetic_router::Client::new(&env, &kinetic_router);
    let (asset, _) = create_and_init_test_reserve(&env, &kinetic_router, &admin);

    setup_blacklist(&env, &client, &asset, &blacklisted);

    // Non-blacklisted proxy tries to borrow on behalf of blacklisted user
    let result = client.try_borrow(&proxy, &asset, &1000u128, &1u32, &0u32, &blacklisted);
    assert!(result.is_err(), "Borrow on behalf of blacklisted user must be rejected");

    match result {
        Err(Ok(err)) => assert_eq!(err, kinetic_router::KineticRouterError::Unauthorized),
        _ => panic!("Expected Unauthorized error for blacklisted beneficiary"),
    }
}

#[test]
fn test_borrow_on_behalf_of_self_still_works_when_not_blacklisted() {
    let env = create_test_env();
    let (admin, emergency_admin, proxy, blacklisted) = create_test_addresses(&env);

    let kinetic_router = initialize_kinetic_router(&env, &admin, &emergency_admin);
    let client = kinetic_router::Client::new(&env, &kinetic_router);
    let (asset, _) = create_and_init_test_reserve(&env, &kinetic_router, &admin);

    setup_blacklist(&env, &client, &asset, &blacklisted);

    // Non-blacklisted proxy borrowing for themselves should NOT get Unauthorized
    let result = client.try_borrow(&proxy, &asset, &1000u128, &1u32, &0u32, &proxy);
    match result {
        Err(Ok(kinetic_router::KineticRouterError::Unauthorized)) => {
            panic!("Non-blacklisted user should not get Unauthorized when borrowing for self");
        }
        _ => {} // Other errors (e.g., no collateral) or success are fine
    }
}

// =============================================================================
// Gap 4: withdraw to blacklisted recipient
// =============================================================================

#[test]
fn test_withdraw_to_blacklisted_recipient_rejected() {
    let env = create_test_env();
    let (admin, emergency_admin, proxy, blacklisted) = create_test_addresses(&env);

    let kinetic_router = initialize_kinetic_router(&env, &admin, &emergency_admin);
    let client = kinetic_router::Client::new(&env, &kinetic_router);
    let (asset, _) = create_and_init_test_reserve(&env, &kinetic_router, &admin);

    setup_blacklist(&env, &client, &asset, &blacklisted);

    // Non-blacklisted proxy tries to withdraw TO a blacklisted address
    let result = client.try_withdraw(&proxy, &asset, &1000u128, &blacklisted);
    assert!(result.is_err(), "Withdraw to blacklisted recipient must be rejected");

    match result {
        Err(Ok(err)) => assert_eq!(err, kinetic_router::KineticRouterError::Unauthorized),
        _ => panic!("Expected Unauthorized error for blacklisted recipient"),
    }
}

#[test]
fn test_withdraw_to_self_still_works_when_not_blacklisted() {
    let env = create_test_env();
    let (admin, emergency_admin, proxy, blacklisted) = create_test_addresses(&env);

    let kinetic_router = initialize_kinetic_router(&env, &admin, &emergency_admin);
    let client = kinetic_router::Client::new(&env, &kinetic_router);
    let (asset, _) = create_and_init_test_reserve(&env, &kinetic_router, &admin);

    setup_blacklist(&env, &client, &asset, &blacklisted);

    // Non-blacklisted proxy withdrawing to self should NOT get Unauthorized
    let result = client.try_withdraw(&proxy, &asset, &1000u128, &proxy);
    match result {
        Err(Ok(kinetic_router::KineticRouterError::Unauthorized)) => {
            panic!("Non-blacklisted user should not get Unauthorized when withdrawing to self");
        }
        _ => {} // Other errors (e.g., no balance) or success are fine
    }
}

// =============================================================================
// Gap 5: repay on_behalf_of blacklisted user
// =============================================================================

#[test]
fn test_repay_on_behalf_of_blacklisted_user_allowed() {
    let env = create_test_env();
    let (admin, emergency_admin, proxy, blacklisted) = create_test_addresses(&env);

    let kinetic_router = initialize_kinetic_router(&env, &admin, &emergency_admin);
    let client = kinetic_router::Client::new(&env, &kinetic_router);
    let (asset, _) = create_and_init_test_reserve(&env, &kinetic_router, &admin);

    setup_blacklist(&env, &client, &asset, &blacklisted);

    // MEDIUM-003: Third-party repay on behalf of blacklisted user must NOT be blocked.
    // AML compliance freezes outbound transfers but permits debt reduction to prevent
    // bad debt accumulation on positions that can't be liquidated yet.
    let result = client.try_repay(&proxy, &asset, &1000u128, &1u32, &blacklisted);
    match result {
        Err(Ok(kinetic_router::KineticRouterError::Unauthorized)) => {
            panic!("Repay on behalf of blacklisted user must not be blocked by blacklist");
        }
        _ => {} // Other errors (e.g., no debt) or success are fine
    }
}

#[test]
fn test_repay_on_behalf_of_self_still_works_when_not_blacklisted() {
    let env = create_test_env();
    let (admin, emergency_admin, proxy, blacklisted) = create_test_addresses(&env);

    let kinetic_router = initialize_kinetic_router(&env, &admin, &emergency_admin);
    let client = kinetic_router::Client::new(&env, &kinetic_router);
    let (asset, _) = create_and_init_test_reserve(&env, &kinetic_router, &admin);

    setup_blacklist(&env, &client, &asset, &blacklisted);

    // Non-blacklisted proxy repaying for themselves should NOT get Unauthorized
    let result = client.try_repay(&proxy, &asset, &1000u128, &1u32, &proxy);
    match result {
        Err(Ok(kinetic_router::KineticRouterError::Unauthorized)) => {
            panic!("Non-blacklisted user should not get Unauthorized when repaying for self");
        }
        _ => {} // Other errors (e.g., no debt) or success are fine
    }
}

// =============================================================================
// Gap 6: set_user_use_reserve_as_coll by blacklisted user
// =============================================================================

#[test]
fn test_set_collateral_by_blacklisted_user_rejected() {
    let env = create_test_env();
    let (admin, emergency_admin, _proxy, blacklisted) = create_test_addresses(&env);

    let kinetic_router = initialize_kinetic_router(&env, &admin, &emergency_admin);
    let client = kinetic_router::Client::new(&env, &kinetic_router);
    let (asset, _) = create_and_init_test_reserve(&env, &kinetic_router, &admin);

    setup_blacklist(&env, &client, &asset, &blacklisted);

    // Blacklisted user tries to enable collateral
    let result = client.try_set_user_use_reserve_as_coll(&blacklisted, &asset, &true);
    assert!(result.is_err(), "Blacklisted user must not modify collateral settings");

    match result {
        Err(Ok(err)) => assert_eq!(err, kinetic_router::KineticRouterError::Unauthorized),
        _ => panic!("Expected Unauthorized error for blacklisted user"),
    }
}

#[test]
fn test_set_collateral_by_non_blacklisted_user_not_rejected_by_blacklist() {
    let env = create_test_env();
    let (admin, emergency_admin, proxy, blacklisted) = create_test_addresses(&env);

    let kinetic_router = initialize_kinetic_router(&env, &admin, &emergency_admin);
    let client = kinetic_router::Client::new(&env, &kinetic_router);
    let (asset, _) = create_and_init_test_reserve(&env, &kinetic_router, &admin);

    setup_blacklist(&env, &client, &asset, &blacklisted);

    // Non-blacklisted user should NOT get Unauthorized from blacklist
    let result = client.try_set_user_use_reserve_as_coll(&proxy, &asset, &true);
    match result {
        Err(Ok(kinetic_router::KineticRouterError::Unauthorized)) => {
            panic!("Non-blacklisted user should not get Unauthorized from blacklist");
        }
        _ => {} // Other errors or success are fine
    }
}

// =============================================================================
// Whitelist symmetry: same gaps apply to whitelist
// =============================================================================

#[test]
fn test_supply_on_behalf_of_non_whitelisted_user_rejected() {
    let env = create_test_env();
    let (admin, emergency_admin, proxy, non_whitelisted) = create_test_addresses(&env);

    let kinetic_router = initialize_kinetic_router(&env, &admin, &emergency_admin);
    let client = kinetic_router::Client::new(&env, &kinetic_router);
    let (asset, _) = create_and_init_test_reserve(&env, &kinetic_router, &admin);

    // Set whitelist that includes proxy but NOT non_whitelisted
    let mut whitelist = Vec::new(&env);
    whitelist.push_back(proxy.clone());
    client.set_reserve_whitelist(&asset, &whitelist);

    // Whitelisted proxy tries to supply on behalf of non-whitelisted user
    let result = client.try_supply(&proxy, &asset, &100_000u128, &non_whitelisted, &0u32);
    assert!(result.is_err(), "Supply on behalf of non-whitelisted user must be rejected");

    match result {
        Err(Ok(err)) => assert_eq!(err, kinetic_router::KineticRouterError::AddressNotWhitelisted),
        _ => panic!("Expected AddressNotWhitelisted error for non-whitelisted beneficiary"),
    }
}

#[test]
fn test_withdraw_to_non_whitelisted_recipient_rejected() {
    let env = create_test_env();
    let (admin, emergency_admin, proxy, non_whitelisted) = create_test_addresses(&env);

    let kinetic_router = initialize_kinetic_router(&env, &admin, &emergency_admin);
    let client = kinetic_router::Client::new(&env, &kinetic_router);
    let (asset, _) = create_and_init_test_reserve(&env, &kinetic_router, &admin);

    // Set whitelist that includes proxy but NOT non_whitelisted
    let mut whitelist = Vec::new(&env);
    whitelist.push_back(proxy.clone());
    client.set_reserve_whitelist(&asset, &whitelist);

    // Whitelisted proxy tries to withdraw TO non-whitelisted address
    let result = client.try_withdraw(&proxy, &asset, &1000u128, &non_whitelisted);
    assert!(result.is_err(), "Withdraw to non-whitelisted recipient must be rejected");

    match result {
        Err(Ok(err)) => assert_eq!(err, kinetic_router::KineticRouterError::AddressNotWhitelisted),
        _ => panic!("Expected AddressNotWhitelisted error for non-whitelisted recipient"),
    }
}

#[test]
fn test_borrow_on_behalf_of_non_whitelisted_user_rejected() {
    let env = create_test_env();
    let (admin, emergency_admin, proxy, non_whitelisted) = create_test_addresses(&env);

    let kinetic_router = initialize_kinetic_router(&env, &admin, &emergency_admin);
    let client = kinetic_router::Client::new(&env, &kinetic_router);
    let (asset, _) = create_and_init_test_reserve(&env, &kinetic_router, &admin);

    // Set whitelist that includes proxy but NOT non_whitelisted
    let mut whitelist = Vec::new(&env);
    whitelist.push_back(proxy.clone());
    client.set_reserve_whitelist(&asset, &whitelist);

    // Whitelisted proxy tries to borrow on behalf of non-whitelisted user
    let result = client.try_borrow(&proxy, &asset, &1000u128, &1u32, &0u32, &non_whitelisted);
    assert!(result.is_err(), "Borrow on behalf of non-whitelisted user must be rejected");

    match result {
        Err(Ok(err)) => assert_eq!(err, kinetic_router::KineticRouterError::AddressNotWhitelisted),
        _ => panic!("Expected AddressNotWhitelisted error for non-whitelisted beneficiary"),
    }
}

#[test]
fn test_repay_on_behalf_of_non_whitelisted_user_rejected() {
    let env = create_test_env();
    let (admin, emergency_admin, proxy, non_whitelisted) = create_test_addresses(&env);

    let kinetic_router = initialize_kinetic_router(&env, &admin, &emergency_admin);
    let client = kinetic_router::Client::new(&env, &kinetic_router);
    let (asset, _) = create_and_init_test_reserve(&env, &kinetic_router, &admin);

    // Set whitelist that includes proxy but NOT non_whitelisted
    let mut whitelist = Vec::new(&env);
    whitelist.push_back(proxy.clone());
    client.set_reserve_whitelist(&asset, &whitelist);

    // Whitelisted proxy tries to repay on behalf of non-whitelisted user
    let result = client.try_repay(&proxy, &asset, &1000u128, &1u32, &non_whitelisted);
    assert!(result.is_err(), "Repay on behalf of non-whitelisted user must be rejected");

    match result {
        Err(Ok(err)) => assert_eq!(err, kinetic_router::KineticRouterError::AddressNotWhitelisted),
        _ => panic!("Expected AddressNotWhitelisted error for non-whitelisted beneficiary"),
    }
}
