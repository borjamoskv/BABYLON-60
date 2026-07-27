#![cfg(test)]

//! Regression tests for reserve ID collision fix (FIND-041)
//! 
//! Tests verify:
//! 1. Reserve IDs are monotonic and never reused
//! 2. 64-reserve hard cap is enforced
//! 3. drop_reserve requires zero liquidity and debt
//! 4. UserConfiguration bitmap integrity after reserve lifecycle operations

use k2_shared::{Asset, OracleError, PriceData, UserConfiguration as SharedUserConfiguration};
use crate::kinetic_router::InitReserveParams;
use soroban_sdk::{
    contract, contractimpl,
    testutils::Address as _,
    Address, Env, Vec,
};

#[contract]
pub struct MockPriceOracle;

#[contractimpl]
impl MockPriceOracle {
    pub fn get_asset_prices_vec(env: Env, assets: Vec<Asset>) -> Result<Vec<PriceData>, OracleError> {
        let mut out = Vec::new(&env);
        for _asset in assets.iter() {
            out.push_back(PriceData {
                price: 100_000_000_000_000u128,
                timestamp: env.ledger().timestamp(),
            });
        }
        Ok(out)
    }
}

fn setup_router(env: &Env) -> (crate::kinetic_router::Client, Address, Address) {
    let admin = Address::generate(&env);
    let emergency_admin = Address::generate(&env);

    let router_id = env.register(crate::kinetic_router::WASM, ());
    let router = crate::kinetic_router::Client::new(&env, &router_id);

    let oracle_id = env.register(MockPriceOracle, ());
    let treasury = Address::generate(&env);
    let dex_router = Address::generate(&env);
    
    router.initialize(&admin, &emergency_admin, &oracle_id, &treasury, &dex_router, &None);

    let pool_configurator = Address::generate(&env);
    router.set_pool_configurator(&pool_configurator);

    (router, pool_configurator, router_id)
}

fn create_reserve_with_tokens(
    env: &Env,
    router: &crate::kinetic_router::Client,
    router_id: &Address,
    pool_configurator: &Address,
    params: &InitReserveParams,
) -> Address {
    let underlying = Address::generate(&env);
    let a_token_id = env.register(crate::a_token::WASM, ());
    let a_token = crate::a_token::Client::new(&env, &a_token_id);
    let debt_token_id = env.register(crate::debt_token::WASM, ());
    let debt_token = crate::debt_token::Client::new(&env, &debt_token_id);
    let rate_strategy = Address::generate(&env);
    let treasury = Address::generate(&env);

    a_token.initialize(
        &router_id,
        &underlying,
        &treasury,
        &soroban_sdk::String::from_str(&env, "aToken"),
        &soroban_sdk::String::from_str(&env, "aT"),
        &params.decimals,
    );
    debt_token.initialize(
        &router_id,
        &underlying,
        &treasury,
        &soroban_sdk::String::from_str(&env, "Debt"),
        &soroban_sdk::String::from_str(&env, "dT"),
        &params.decimals,
    );

    router.init_reserve(
        &pool_configurator,
        &underlying,
        &a_token_id,
        &debt_token_id,
        &rate_strategy,
        &treasury,
        &params,
    );

    underlying
}

#[test]
fn test_reserve_ids_are_monotonic() {
    let env = Env::default();
    env.mock_all_auths();

    let (router, pool_configurator, router_id) = setup_router(&env);

    let params = InitReserveParams {
        decimals: 7,
        ltv: 8000,
        liquidation_threshold: 8500,
        liquidation_bonus: 500,
        reserve_factor: 1000,
        supply_cap: 1_000_000,
        borrow_cap: 1_000_000,
        borrowing_enabled: true,
        flashloan_enabled: true,
    };

    // Create 5 reserves
    let mut reserve_ids = Vec::new(&env);
    for _ in 0..5 {
        let asset = create_reserve_with_tokens(&env, &router, &router_id, &pool_configurator, &params);
        let reserve_data = router.get_reserve_data(&asset);
        reserve_ids.push_back(reserve_data.id);
    }

    // Verify IDs are 0, 1, 2, 3, 4
    for i in 0..5 {
        assert_eq!(reserve_ids.get(i).unwrap(), i);
    }
}

#[test]
fn test_reserve_ids_never_reused_after_drop() {
    let env = Env::default();
    env.mock_all_auths();

    let (router, pool_configurator, router_id) = setup_router(&env);

    let params = InitReserveParams {
        decimals: 7,
        ltv: 8000,
        liquidation_threshold: 8500,
        liquidation_bonus: 500,
        reserve_factor: 1000,
        supply_cap: 1_000_000,
        borrow_cap: 1_000_000,
        borrowing_enabled: true,
        flashloan_enabled: true,
    };

    // Create 3 reserves: A(0), B(1), C(2)
    let asset_a = create_reserve_with_tokens(&env, &router, &router_id, &pool_configurator, &params);
    let asset_b = create_reserve_with_tokens(&env, &router, &router_id, &pool_configurator, &params);
    let asset_c = create_reserve_with_tokens(&env, &router, &router_id, &pool_configurator, &params);

    assert_eq!(router.get_reserve_data(&asset_a).id, 0);
    assert_eq!(router.get_reserve_data(&asset_b).id, 1);
    assert_eq!(router.get_reserve_data(&asset_c).id, 2);

    // Drop reserve B (id=1)
    router.drop_reserve(&pool_configurator, &asset_b);

    // Create new reserve D - should get ID 3, NOT reuse ID 1
    let asset_d = create_reserve_with_tokens(&env, &router, &router_id, &pool_configurator, &params);
    assert_eq!(router.get_reserve_data(&asset_d).id, 3);

    // Drop reserve A (id=0)
    router.drop_reserve(&pool_configurator, &asset_a);

    // Create new reserve E - should get ID 4, NOT reuse ID 0
    let asset_e = create_reserve_with_tokens(&env, &router, &router_id, &pool_configurator, &params);
    assert_eq!(router.get_reserve_data(&asset_e).id, 4);
}

#[test]
#[should_panic(expected = "Error(Contract, #1)")]
fn test_max_64_reserves_enforced() {
    let env = Env::default();
    env.mock_all_auths();

    let (router, pool_configurator, router_id) = setup_router(&env);

    let params = InitReserveParams {
        decimals: 7,
        ltv: 8000,
        liquidation_threshold: 8500,
        liquidation_bonus: 500,
        reserve_factor: 1000,
        supply_cap: 1_000_000,
        borrow_cap: 1_000_000,
        borrowing_enabled: true,
        flashloan_enabled: true,
    };

    // Create 64 reserves - should succeed
    for _ in 0..64 {
        create_reserve_with_tokens(&env, &router, &router_id, &pool_configurator, &params);
    }

    // Try to create 65th reserve - should panic with MaxReservesReached
    create_reserve_with_tokens(&env, &router, &router_id, &pool_configurator, &params);
}

#[test]
fn test_exactly_64_reserves_allowed() {
    let env = Env::default();
    env.mock_all_auths();

    let (router, pool_configurator, router_id) = setup_router(&env);

    let params = InitReserveParams {
        decimals: 7,
        ltv: 8000,
        liquidation_threshold: 8500,
        liquidation_bonus: 500,
        reserve_factor: 1000,
        supply_cap: 1_000_000,
        borrow_cap: 1_000_000,
        borrowing_enabled: true,
        flashloan_enabled: true,
    };

    // Create exactly 64 reserves - should succeed
    for i in 0..64 {
        let asset = create_reserve_with_tokens(&env, &router, &router_id, &pool_configurator, &params);
        let reserve_data = router.get_reserve_data(&asset);
        assert_eq!(reserve_data.id, i);
    }
}

#[test]
#[should_panic(expected = "Error(Contract, #2)")]
fn test_cannot_drop_reserve_with_liquidity() {
    let env = Env::default();
    env.mock_all_auths();

    let (router, pool_configurator, router_id) = setup_router(&env);

    let params = InitReserveParams {
        decimals: 7,
        ltv: 8000,
        liquidation_threshold: 8500,
        liquidation_bonus: 500,
        reserve_factor: 1000,
        supply_cap: 1_000_000,
        borrow_cap: 1_000_000,
        borrowing_enabled: true,
        flashloan_enabled: true,
    };

    let underlying = Address::generate(&env);
    let a_token_id = env.register(crate::a_token::WASM, ());
    let a_token = crate::a_token::Client::new(&env, &a_token_id);
    let debt_token_id = env.register(crate::debt_token::WASM, ());
    let debt_token = crate::debt_token::Client::new(&env, &debt_token_id);
    let rate_strategy = Address::generate(&env);
    let treasury = Address::generate(&env);

    a_token.initialize(
        &router_id,
        &underlying,
        &treasury,
        &soroban_sdk::String::from_str(&env, "aToken"),
        &soroban_sdk::String::from_str(&env, "aT"),
        &params.decimals,
    );
    debt_token.initialize(
        &router_id,
        &underlying,
        &treasury,
        &soroban_sdk::String::from_str(&env, "Debt"),
        &soroban_sdk::String::from_str(&env, "dT"),
        &params.decimals,
    );

    router.init_reserve(
        &pool_configurator,
        &underlying,
        &a_token_id,
        &debt_token_id,
        &rate_strategy,
        &treasury,
        &params,
    );

    // Mint some aTokens to simulate liquidity (WP-L8: mint() disabled, use mint_scaled)
    // pool_address = treasury (third arg to initialize), so caller must be treasury
    let user = Address::generate(&env);
    a_token.mint_scaled(&treasury, &user, &1000u128, &k2_shared::RAY);

    // Try to drop - should fail with CannotDropActiveReserve
    router.drop_reserve(&pool_configurator, &underlying);
}

#[test]
#[should_panic(expected = "Error(Contract, #2)")]
fn test_cannot_drop_reserve_with_debt() {
    let env = Env::default();
    env.mock_all_auths();

    let (router, pool_configurator, router_id) = setup_router(&env);

    let params = InitReserveParams {
        decimals: 7,
        ltv: 8000,
        liquidation_threshold: 8500,
        liquidation_bonus: 500,
        reserve_factor: 1000,
        supply_cap: 1_000_000,
        borrow_cap: 1_000_000,
        borrowing_enabled: true,
        flashloan_enabled: true,
    };

    let underlying = Address::generate(&env);
    let a_token_id = env.register(crate::a_token::WASM, ());
    let a_token = crate::a_token::Client::new(&env, &a_token_id);
    let debt_token_id = env.register(crate::debt_token::WASM, ());
    let debt_token = crate::debt_token::Client::new(&env, &debt_token_id);
    let rate_strategy = Address::generate(&env);
    let treasury = Address::generate(&env);

    a_token.initialize(
        &router_id,
        &underlying,
        &treasury,
        &soroban_sdk::String::from_str(&env, "aToken"),
        &soroban_sdk::String::from_str(&env, "aT"),
        &params.decimals,
    );
    debt_token.initialize(
        &router_id,
        &underlying,
        &treasury,
        &soroban_sdk::String::from_str(&env, "Debt"),
        &soroban_sdk::String::from_str(&env, "dT"),
        &params.decimals,
    );

    router.init_reserve(
        &pool_configurator,
        &underlying,
        &a_token_id,
        &debt_token_id,
        &rate_strategy,
        &treasury,
        &params,
    );

    let user = Address::generate(&env);
    debt_token.mint_scaled(&treasury, &user, &5000u128, &k2_shared::RAY);

    // Try to drop - should fail with CannotDropActiveReserve
    router.drop_reserve(&pool_configurator, &underlying);
}

#[test]
fn test_can_drop_reserve_with_zero_balances() {
    let env = Env::default();
    env.mock_all_auths();

    let (router, pool_configurator, router_id) = setup_router(&env);

    let params = InitReserveParams {
        decimals: 7,
        ltv: 8000,
        liquidation_threshold: 8500,
        liquidation_bonus: 500,
        reserve_factor: 1000,
        supply_cap: 1_000_000,
        borrow_cap: 1_000_000,
        borrowing_enabled: true,
        flashloan_enabled: true,
    };

    let asset = create_reserve_with_tokens(&env, &router, &router_id, &pool_configurator, &params);

    // Verify reserve exists
    let reserve_data = router.get_reserve_data(&asset);
    assert_eq!(reserve_data.id, 0);

    // Drop should succeed (zero balances)
    router.drop_reserve(&pool_configurator, &asset);

    // Note: Reserve data is removed after drop. Attempting to access it would panic.
    // We've successfully dropped the reserve, which is what we're testing.
}

#[test]
fn test_user_configuration_integrity_after_reserve_lifecycle() {
    let env = Env::default();
    env.mock_all_auths();

    let (router, pool_configurator, router_id) = setup_router(&env);

    let params = InitReserveParams {
        decimals: 7,
        ltv: 8000,
        liquidation_threshold: 8500,
        liquidation_bonus: 500,
        reserve_factor: 1000,
        supply_cap: 1_000_000,
        borrow_cap: 1_000_000,
        borrowing_enabled: true,
        flashloan_enabled: true,
    };

    let user = Address::generate(&env);

    // Create reserves A(0), B(1), C(2)
    let asset_a = create_reserve_with_tokens(&env, &router, &router_id, &pool_configurator, &params);
    let asset_b = create_reserve_with_tokens(&env, &router, &router_id, &pool_configurator, &params);
    let asset_c = create_reserve_with_tokens(&env, &router, &router_id, &pool_configurator, &params);

    // Mark reserve B as collateral for user
    router.set_user_use_reserve_as_coll(&user, &asset_b, &true);

    let config_before = router.get_user_configuration(&user);
    let config_before_shared = SharedUserConfiguration { data: config_before.data };
    assert!(config_before_shared.is_using_as_collateral(1)); // Reserve B has id=1

    // Drop reserve A (id=0)
    router.drop_reserve(&pool_configurator, &asset_a);

    // Create new reserve D - gets id=3 (NOT id=0)
    let asset_d = create_reserve_with_tokens(&env, &router, &router_id, &pool_configurator, &params);
    let reserve_d = router.get_reserve_data(&asset_d);
    assert_eq!(reserve_d.id, 3);

    // User config for reserve B should be unchanged
    let config_after = router.get_user_configuration(&user);
    let config_after_shared = SharedUserConfiguration { data: config_after.data };
    assert!(config_after_shared.is_using_as_collateral(1)); // Reserve B still has id=1
    assert!(!config_after_shared.is_using_as_collateral(3)); // Reserve D (id=3) not set

    // Set reserve D as collateral - should not affect reserve B
    router.set_user_use_reserve_as_coll(&user, &asset_d, &true);
    let config_final = router.get_user_configuration(&user);
    let config_final_shared = SharedUserConfiguration { data: config_final.data };
    assert!(config_final_shared.is_using_as_collateral(1)); // Reserve B unchanged
    assert!(config_final_shared.is_using_as_collateral(3)); // Reserve D now set
}
