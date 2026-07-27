#![cfg(test)]

//! PoC: dropping a reserve causes `RESERVES_COUNT` (list length) to decrease,
//! which can lead to `ReserveData.id` reuse and collisions. Because `UserConfiguration`
//! uses `reserve_data.id` as the bitmap index, an id collision makes collateral/borrow
//! flags ambiguous across multiple reserves.

use k2_shared::{Asset, OracleError, PriceData};
use crate::kinetic_router::InitReserveParams;
use soroban_sdk::{
    contract, contractimpl,
    testutils::Address as _,
    Address, Env, Vec,
};

/// Minimal oracle stub for router tests:
/// - Implements the exact method the router calls (`get_asset_prices_vec`)
/// - Returns a fixed non-zero price for every requested asset.
#[contract]
pub struct MockPriceOracle;

#[contractimpl]
impl MockPriceOracle {
    pub fn get_asset_prices_vec(env: Env, assets: Vec<Asset>) -> Result<Vec<PriceData>, OracleError> {
        let mut out = Vec::new(&env);
        for _asset in assets.iter() {
            out.push_back(PriceData {
                // 1.0 with 14 decimals
                price: 100_000_000_000_000u128,
                timestamp: env.ledger().timestamp(),
            });
        }
        Ok(out)
    }
}

#[test]
#[should_panic(expected = "Error(Contract, #53)")]
fn poc_drop_reserve_now_requires_zero_balances() {
    let env = Env::default();
    env.mock_all_auths();

    let admin = Address::generate(&env);
    let emergency_admin = Address::generate(&env);

    // Deploy router + oracle
    let router_id = env.register(crate::kinetic_router::WASM, ());
    let router = crate::kinetic_router::Client::new(&env, &router_id);

    let oracle_id = env.register(MockPriceOracle, ());
    let treasury = Address::generate(&env);
    let dex_router = Address::generate(&env);
    router.initialize(&admin, &emergency_admin, &oracle_id, &treasury, &dex_router, &None);

    let pool_configurator = Address::generate(&env);
    router.set_pool_configurator(&pool_configurator);

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

    // Helper: initialize a reserve with dummy token/strategy addresses
    let init_reserve = || -> Address {
        let underlying = Address::generate(&env);
        let a_token = Address::generate(&env);
        let debt_token = Address::generate(&env);
        let rate_strategy = Address::generate(&env);
        router.init_reserve(
            &pool_configurator,
            &underlying,
            &a_token,
            &debt_token,
            &rate_strategy,
            &treasury,
            &params,
        );
        underlying
    };

    // Create reserve A
    let asset_a = init_reserve();

    // Try to drop reserve A - should fail because we haven't checked balances
    // (In a real scenario with actual token contracts, this would check aToken/debt token supplies)
    router.drop_reserve(&pool_configurator, &asset_a);
}

#[test]
fn test_reserve_id_monotonic_after_drop() {
    let env = Env::default();
    env.mock_all_auths();

    let admin = Address::generate(&env);
    let emergency_admin = Address::generate(&env);

    // Deploy router + oracle
    let router_id = env.register(crate::kinetic_router::WASM, ());
    let router = crate::kinetic_router::Client::new(&env, &router_id);

    let oracle_id = env.register(MockPriceOracle, ());
    let treasury = Address::generate(&env);
    let dex_router = Address::generate(&env);
    router.initialize(&admin, &emergency_admin, &oracle_id, &treasury, &dex_router, &None);

    let pool_configurator = Address::generate(&env);
    router.set_pool_configurator(&pool_configurator);

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

    // Create reserves with proper token contracts
    let underlying_a = Address::generate(&env);
    let a_token_a_id = env.register(crate::a_token::WASM, ());
    let a_token_a = crate::a_token::Client::new(&env, &a_token_a_id);
    let debt_token_a_id = env.register(crate::debt_token::WASM, ());
    let debt_token_a = crate::debt_token::Client::new(&env, &debt_token_a_id);
    let rate_strategy = Address::generate(&env);

    // Initialize aToken and debt token for reserve A
    a_token_a.initialize(
        &router_id,
        &underlying_a,
        &treasury,
        &soroban_sdk::String::from_str(&env, "aToken A"),
        &soroban_sdk::String::from_str(&env, "aA"),
        &7u32,
    );
    debt_token_a.initialize(
        &router_id,
        &underlying_a,
        &treasury,
        &soroban_sdk::String::from_str(&env, "Debt A"),
        &soroban_sdk::String::from_str(&env, "dA"),
        &7u32,
    );

    router.init_reserve(
        &pool_configurator,
        &underlying_a,
        &a_token_a_id,
        &debt_token_a_id,
        &rate_strategy,
        &treasury,
        &params,
    );

    let reserve_a = router.get_reserve_data(&underlying_a);
    assert_eq!(reserve_a.id, 0);

    // Create reserve B
    let underlying_b = Address::generate(&env);
    let a_token_b_id = env.register(crate::a_token::WASM, ());
    let a_token_b = crate::a_token::Client::new(&env, &a_token_b_id);
    let debt_token_b_id = env.register(crate::debt_token::WASM, ());
    let debt_token_b = crate::debt_token::Client::new(&env, &debt_token_b_id);

    a_token_b.initialize(
        &router_id,
        &underlying_b,
        &treasury,
        &soroban_sdk::String::from_str(&env, "aToken B"),
        &soroban_sdk::String::from_str(&env, "aB"),
        &7u32,
    );
    debt_token_b.initialize(
        &router_id,
        &underlying_b,
        &treasury,
        &soroban_sdk::String::from_str(&env, "Debt B"),
        &soroban_sdk::String::from_str(&env, "dB"),
        &7u32,
    );

    router.init_reserve(
        &pool_configurator,
        &underlying_b,
        &a_token_b_id,
        &debt_token_b_id,
        &rate_strategy,
        &treasury,
        &params,
    );

    let reserve_b = router.get_reserve_data(&underlying_b);
    assert_eq!(reserve_b.id, 1);

    // Drop reserve A (now allowed because aToken and debt token have zero supply)
    router.drop_reserve(&pool_configurator, &underlying_a);

    // Create reserve C - should get ID 2, NOT reuse ID 0
    let underlying_c = Address::generate(&env);
    let a_token_c_id = env.register(crate::a_token::WASM, ());
    let a_token_c = crate::a_token::Client::new(&env, &a_token_c_id);
    let debt_token_c_id = env.register(crate::debt_token::WASM, ());
    let debt_token_c = crate::debt_token::Client::new(&env, &debt_token_c_id);

    a_token_c.initialize(
        &router_id,
        &underlying_c,
        &treasury,
        &soroban_sdk::String::from_str(&env, "aToken C"),
        &soroban_sdk::String::from_str(&env, "aC"),
        &7u32,
    );
    debt_token_c.initialize(
        &router_id,
        &underlying_c,
        &treasury,
        &soroban_sdk::String::from_str(&env, "Debt C"),
        &soroban_sdk::String::from_str(&env, "dC"),
        &7u32,
    );

    router.init_reserve(
        &pool_configurator,
        &underlying_c,
        &a_token_c_id,
        &debt_token_c_id,
        &rate_strategy,
        &treasury,
        &params,
    );

    let reserve_c = router.get_reserve_data(&underlying_c);
    
    // FIXED: Reserve C should get ID 2 (monotonic), not reuse ID 1
    assert_eq!(reserve_c.id, 2, "Reserve IDs must be monotonic and never reused");
    
    // Reserve B should still have ID 1
    let reserve_b_after = router.get_reserve_data(&underlying_b);
    assert_eq!(reserve_b_after.id, 1, "Existing reserve IDs must not change");
}
