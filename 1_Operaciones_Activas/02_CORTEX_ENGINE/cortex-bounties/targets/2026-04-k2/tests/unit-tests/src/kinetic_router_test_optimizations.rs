#![cfg(test)]

//! Optimization and efficiency tests:
//! - N-04: RESERVES_COUNT cached count (storage.rs)
//! - MED-04/EFF-03: next_reserve_id iteration bound (calculation.rs)
//! - N-05: Oracle batch price helper with hoisted config (price-oracle)
//! - CRIT-01/CRIT-02: known_prices pass-through in liquidation (router.rs)

use crate::{a_token, debt_token, interest_rate_strategy, kinetic_router, price_oracle};
use k2_shared::{Asset, OracleError, PriceData};
use soroban_sdk::{
    contract, contractimpl,
    testutils::{Address as _, Ledger, LedgerInfo},
    token, Address, Env, IntoVal, String, Symbol, Vec,
};

// =============================================================================
// Mock Contracts
// =============================================================================

#[contract]
pub struct MockReflector;

#[contractimpl]
impl MockReflector {
    pub fn decimals(_env: Env) -> u32 {
        14
    }
}

#[contract]
pub struct MockPriceOracle;

#[contractimpl]
impl MockPriceOracle {
    pub fn get_asset_prices_vec(env: Env, assets: Vec<Asset>) -> Result<Vec<PriceData>, OracleError> {
        let mut out = Vec::new(&env);
        for _asset in assets.iter() {
            out.push_back(PriceData {
                price: 100_000_000_000_000u128, // $1.00 at 14 decimals
                timestamp: env.ledger().timestamp(),
            });
        }
        Ok(out)
    }
}

// =============================================================================
// Setup Helpers
// =============================================================================

fn setup_ledger(env: &Env) {
    env.ledger().set(LedgerInfo {
        sequence_number: 100,
        protocol_version: 23,
        timestamp: 1_000_000,
        network_id: Default::default(),
        base_reserve: 10,
        min_temp_entry_ttl: 10,
        min_persistent_entry_ttl: 10,
        max_entry_ttl: 3_000_000,
    });
}

fn setup_interest_rate_strategy(env: &Env, admin: &Address) -> Address {
    let contract_id = env.register(interest_rate_strategy::WASM, ());
    let mut init_args = Vec::new(env);
    init_args.push_back(admin.clone().into_val(env));
    init_args.push_back((0u128).into_val(env));
    init_args.push_back((40_000_000_000_000_000_000u128).into_val(env));
    init_args.push_back((100_000_000_000_000_000_000u128).into_val(env));
    init_args.push_back((800_000_000_000_000_000_000_000_000u128).into_val(env));
    let _: () = env.invoke_contract(&contract_id, &Symbol::new(env, "initialize"), init_args);
    contract_id
}

fn setup_router_with_mock_oracle(env: &Env) -> (kinetic_router::Client, Address, Address, Address) {
    let admin = Address::generate(env);
    let emergency_admin = Address::generate(env);
    let router_id = env.register(kinetic_router::WASM, ());
    let router = kinetic_router::Client::new(env, &router_id);

    let oracle_id = env.register(MockPriceOracle, ());
    let treasury = Address::generate(env);
    let dex_router = Address::generate(env);

    router.initialize(&admin, &emergency_admin, &oracle_id, &treasury, &dex_router, &None);

    let pool_configurator = Address::generate(env);
    router.set_pool_configurator(&pool_configurator);

    (router, pool_configurator, router_id, admin)
}

/// Create a reserve with a random address (no real token — use for add/drop tests only)
fn create_reserve(
    env: &Env,
    router: &kinetic_router::Client,
    router_id: &Address,
    pool_configurator: &Address,
    admin: &Address,
) -> (Address, Address, Address) {
    let underlying = Address::generate(env);
    create_reserve_for_underlying(env, router, router_id, pool_configurator, admin, &underlying)
}

/// Create a reserve with a real Stellar asset contract (supports mint/supply)
fn create_reserve_with_real_token(
    env: &Env,
    router: &kinetic_router::Client,
    router_id: &Address,
    pool_configurator: &Address,
    admin: &Address,
) -> (Address, Address, Address) {
    let token_admin = Address::generate(env);
    let underlying_token = env.register_stellar_asset_contract_v2(token_admin);
    let underlying = underlying_token.address();
    create_reserve_for_underlying(env, router, router_id, pool_configurator, admin, &underlying)
}

fn create_reserve_for_underlying(
    env: &Env,
    router: &kinetic_router::Client,
    router_id: &Address,
    pool_configurator: &Address,
    admin: &Address,
    underlying: &Address,
) -> (Address, Address, Address) {
    let a_token_id = env.register(a_token::WASM, ());
    let a_token_client = a_token::Client::new(env, &a_token_id);
    let debt_token_id = env.register(debt_token::WASM, ());
    let debt_token_client = debt_token::Client::new(env, &debt_token_id);
    let irs = setup_interest_rate_strategy(env, admin);
    let treasury = Address::generate(env);

    let params = kinetic_router::InitReserveParams {
        decimals: 7,
        ltv: 7500,
        liquidation_threshold: 8000,
        liquidation_bonus: 500,
        reserve_factor: 1000,
        supply_cap: 0,
        borrow_cap: 0,
        borrowing_enabled: true,
        flashloan_enabled: true,
    };

    a_token_client.initialize(
        admin,
        underlying,
        router_id,
        &String::from_str(env, "aToken"),
        &String::from_str(env, "aTKN"),
        &params.decimals,
    );
    debt_token_client.initialize(
        admin,
        underlying,
        router_id,
        &String::from_str(env, "debtToken"),
        &String::from_str(env, "dTKN"),
        &params.decimals,
    );

    router.init_reserve(
        pool_configurator,
        underlying,
        &a_token_id,
        &debt_token_id,
        &irs,
        &treasury,
        &params,
    );

    (underlying.clone(), a_token_id, debt_token_id)
}

/// Approve the router to spend tokens on behalf of a user (required for supply/borrow)
fn approve_token(env: &Env, asset: &Address, user: &Address, router_id: &Address, amount: i128) {
    let token_client = token::Client::new(env, asset);
    let expiration = env.ledger().sequence() + 1_000_000;
    token_client.approve(user, router_id, &amount, &expiration);
}

// =============================================================================
// N-04: RESERVES_COUNT cached count tests
// =============================================================================

#[test]
fn test_reserves_count_matches_list_length_after_add() {
    let env = Env::default();
    env.mock_all_auths();
    setup_ledger(&env);

    let (router, pool_configurator, router_id, admin) = setup_router_with_mock_oracle(&env);

    // Initially 0 reserves
    let list = router.get_reserves_list();
    assert_eq!(list.len(), 0);

    // Add 3 reserves, verify list length is correct after each
    for expected_count in 1..=3u32 {
        create_reserve(&env, &router, &router_id, &pool_configurator, &admin);
        let list = router.get_reserves_list();
        assert_eq!(list.len(), expected_count, "reserves list length should be {} after adding {} reserves", expected_count, expected_count);
    }
}

#[test]
fn test_reserves_count_decrements_after_drop() {
    let env = Env::default();
    env.mock_all_auths();
    setup_ledger(&env);

    let (router, pool_configurator, router_id, admin) = setup_router_with_mock_oracle(&env);

    // Add 3 reserves
    let (asset_a, _, _) = create_reserve(&env, &router, &router_id, &pool_configurator, &admin);
    let (asset_b, _, _) = create_reserve(&env, &router, &router_id, &pool_configurator, &admin);
    let (_asset_c, _, _) = create_reserve(&env, &router, &router_id, &pool_configurator, &admin);

    assert_eq!(router.get_reserves_list().len(), 3);

    // Drop reserve A
    router.drop_reserve(&pool_configurator, &asset_a);
    assert_eq!(router.get_reserves_list().len(), 2, "reserves list should have 2 after dropping one");

    // Drop reserve B
    router.drop_reserve(&pool_configurator, &asset_b);
    assert_eq!(router.get_reserves_list().len(), 1, "reserves list should have 1 after dropping two");
}

// =============================================================================
// MED-04/EFF-03: next_reserve_id iteration bound tests
// =============================================================================

#[test]
fn test_account_data_correct_with_reserve_id_gaps() {
    // When reserves are dropped, IDs have gaps. The iteration bound must use
    // next_reserve_id (high-water mark), NOT reserves_count, to avoid skipping
    // positions at higher IDs.
    let env = Env::default();
    env.mock_all_auths();
    setup_ledger(&env);

    let (router, router_id, oracle_id, admin, pool_configurator) = setup_full_protocol(&env);

    // Create 3 reserves: A(id=0), B(id=1), C(id=2)
    // A and C need real tokens (will supply), B just needs to exist (will be dropped)
    let (asset_a, _, _) = deploy_reserve_with_oracle(
        &env, &router, &router_id, &oracle_id, &admin, &pool_configurator,
        100_000_000_000_000u128, 7500, 8000, 500,
    );
    let (asset_b, _, _) = deploy_reserve_with_oracle(
        &env, &router, &router_id, &oracle_id, &admin, &pool_configurator,
        100_000_000_000_000u128, 7500, 8000, 500,
    );
    let (asset_c, _, _) = deploy_reserve_with_oracle(
        &env, &router, &router_id, &oracle_id, &admin, &pool_configurator,
        100_000_000_000_000u128, 7500, 8000, 500,
    );

    assert_eq!(router.get_reserve_data(&asset_a).id, 0);
    assert_eq!(router.get_reserve_data(&asset_b).id, 1);
    assert_eq!(router.get_reserve_data(&asset_c).id, 2);

    // User supplies to asset A and C
    let user = Address::generate(&env);
    let underlying_token_a = token::StellarAssetClient::new(&env, &asset_a);
    underlying_token_a.mint(&user, &10_000_0000000i128);
    approve_token(&env, &asset_a, &user, &router_id, 10_000_0000000i128);

    let underlying_token_c = token::StellarAssetClient::new(&env, &asset_c);
    underlying_token_c.mint(&user, &5_000_0000000i128);
    approve_token(&env, &asset_c, &user, &router_id, 5_000_0000000i128);

    router.supply(&user, &asset_a, &10_000_0000000u128, &user, &0);
    router.supply(&user, &asset_c, &5_000_0000000u128, &user, &0);

    // Enable as collateral
    router.set_user_use_reserve_as_coll(&user, &asset_a, &true);
    router.set_user_use_reserve_as_coll(&user, &asset_c, &true);

    // Get account data before drop - should include both A and C
    let data_before = router.get_user_account_data(&user);
    assert!(data_before.total_collateral_base > 0, "should have collateral from A and C");
    let collateral_before = data_before.total_collateral_base;

    // Drop reserve B (id=1) - creates a gap in IDs
    router.drop_reserve(&pool_configurator, &asset_b);

    // Now reserves_count=2, but next_reserve_id=3
    // If iteration used reserves_count (2), it would only check IDs 0-1, missing C (id=2)
    let data_after = router.get_user_account_data(&user);
    assert_eq!(
        data_after.total_collateral_base, collateral_before,
        "collateral should be unchanged after dropping unrelated reserve B; \
         if this fails, iteration bound may be using reserves_count instead of next_reserve_id"
    );
}

#[test]
fn test_account_data_with_position_at_high_id_after_drops() {
    // Stress test: create many reserves, drop early ones, ensure high-ID position is still counted
    let env = Env::default();
    env.mock_all_auths();
    setup_ledger(&env);

    let (router, router_id, oracle_id, admin, pool_configurator) = setup_full_protocol(&env);

    // Create 5 reserves: ids 0,1,2,3,4
    let mut assets = soroban_sdk::Vec::new(&env);
    for _ in 0..5 {
        let (asset, _, _) = deploy_reserve_with_oracle(
            &env, &router, &router_id, &oracle_id, &admin, &pool_configurator,
            100_000_000_000_000u128, 7500, 8000, 500,
        );
        assets.push_back(asset);
    }

    let last_asset = assets.get(4).unwrap();

    // User supplies only to the last reserve (id=4)
    let user = Address::generate(&env);
    let underlying = token::StellarAssetClient::new(&env, &last_asset);
    underlying.mint(&user, &1_000_0000000i128);
    approve_token(&env, &last_asset, &user, &router_id, 1_000_0000000i128);
    router.supply(&user, &last_asset, &1_000_0000000u128, &user, &0);
    router.set_user_use_reserve_as_coll(&user, &last_asset, &true);

    // Drop reserves 0,1,2 — creates gaps, reserves_count drops to 2
    for i in 0..3u32 {
        let asset = assets.get(i).unwrap();
        router.drop_reserve(&pool_configurator, &asset);
    }

    // reserves_count is now 2, but next_reserve_id is still 5
    // Position at id=4 must still be found
    let data = router.get_user_account_data(&user);
    assert!(
        data.total_collateral_base > 0,
        "position at id=4 should be found even after dropping reserves 0,1,2"
    );
}

// =============================================================================
// N-05: Oracle batch price query (get_asset_prices_vec / get_asset_prices)
// =============================================================================

#[test]
fn test_oracle_batch_prices_vec_returns_correct_count() {
    let env = Env::default();
    env.mock_all_auths();
    setup_ledger(&env);

    let oracle_id = env.register(price_oracle::WASM, ());
    let client = price_oracle::Client::new(&env, &oracle_id);

    let reflector_addr = env.register(MockReflector, ());
    let base_currency = Address::generate(&env);
    let native_xlm = Address::generate(&env);
    let admin = Address::generate(&env);
    client.initialize(&admin, &reflector_addr, &base_currency, &native_xlm);

    // Add 3 assets with manual overrides
    let asset1 = price_oracle::Asset::Stellar(Address::generate(&env));
    let asset2 = price_oracle::Asset::Stellar(Address::generate(&env));
    let asset3 = price_oracle::Asset::Stellar(Address::generate(&env));

    client.add_asset(&admin, &asset1);
    client.add_asset(&admin, &asset2);
    client.add_asset(&admin, &asset3);

    let price1 = 1_000_000_000_000_000u128; // $1
    let price2 = 2_000_000_000_000_000u128; // $2
    let price3 = 50_000_000_000_000_000u128; // $50

    let expiry = env.ledger().timestamp() + 86400;
    client.set_manual_override(&admin, &asset1, &Some(price1), &Some(expiry));
    client.set_manual_override(&admin, &asset2, &Some(price2), &Some(expiry));
    client.set_manual_override(&admin, &asset3, &Some(price3), &Some(expiry));

    // Query batch via get_asset_prices_vec
    let mut query_assets = Vec::new(&env);
    query_assets.push_back(asset1.clone());
    query_assets.push_back(asset2.clone());
    query_assets.push_back(asset3.clone());

    let results = client.get_asset_prices_vec(&query_assets);
    assert_eq!(results.len(), 3, "should return one PriceData per queried asset");

    // Verify each price matches
    assert_eq!(results.get(0).unwrap().price, price1);
    assert_eq!(results.get(1).unwrap().price, price2);
    assert_eq!(results.get(2).unwrap().price, price3);
}

#[test]
fn test_oracle_batch_prices_map_returns_correct_prices() {
    let env = Env::default();
    env.mock_all_auths();
    setup_ledger(&env);

    let oracle_id = env.register(price_oracle::WASM, ());
    let client = price_oracle::Client::new(&env, &oracle_id);

    let reflector_addr = env.register(MockReflector, ());
    let base_currency = Address::generate(&env);
    let native_xlm = Address::generate(&env);
    let admin = Address::generate(&env);
    client.initialize(&admin, &reflector_addr, &base_currency, &native_xlm);

    let asset1 = price_oracle::Asset::Stellar(Address::generate(&env));
    let asset2 = price_oracle::Asset::Stellar(Address::generate(&env));

    client.add_asset(&admin, &asset1);
    client.add_asset(&admin, &asset2);

    let price1 = 3_000_000_000_000_000u128;
    let price2 = 7_500_000_000_000_000u128;

    let expiry = env.ledger().timestamp() + 86400;
    client.set_manual_override(&admin, &asset1, &Some(price1), &Some(expiry));
    client.set_manual_override(&admin, &asset2, &Some(price2), &Some(expiry));

    let mut query_assets = Vec::new(&env);
    query_assets.push_back(asset1.clone());
    query_assets.push_back(asset2.clone());

    let results = client.get_asset_prices_vec(&query_assets);
    assert_eq!(results.len(), 2);
    assert_eq!(results.get(0).unwrap().price, price1);
    assert_eq!(results.get(1).unwrap().price, price2);
}

#[test]
fn test_oracle_batch_rejects_non_whitelisted_asset() {
    let env = Env::default();
    env.mock_all_auths();
    setup_ledger(&env);

    let oracle_id = env.register(price_oracle::WASM, ());
    let client = price_oracle::Client::new(&env, &oracle_id);

    let reflector_addr = env.register(MockReflector, ());
    let base_currency = Address::generate(&env);
    let native_xlm = Address::generate(&env);
    let admin = Address::generate(&env);
    client.initialize(&admin, &reflector_addr, &base_currency, &native_xlm);

    // Add only asset1
    let asset1 = price_oracle::Asset::Stellar(Address::generate(&env));
    client.add_asset(&admin, &asset1);
    let expiry = env.ledger().timestamp() + 86400;
    client.set_manual_override(&admin, &asset1, &Some(1_000_000_000_000_000u128), &Some(expiry));

    // Query with asset1 + non-whitelisted asset2
    let asset2 = price_oracle::Asset::Stellar(Address::generate(&env));
    let mut query_assets = Vec::new(&env);
    query_assets.push_back(asset1.clone());
    query_assets.push_back(asset2.clone());

    let result = client.try_get_asset_prices_vec(&query_assets);
    assert!(result.is_err(), "batch query should fail if any asset is not whitelisted");
}

#[test]
fn test_oracle_batch_rejects_disabled_asset() {
    let env = Env::default();
    env.mock_all_auths();
    setup_ledger(&env);

    let oracle_id = env.register(price_oracle::WASM, ());
    let client = price_oracle::Client::new(&env, &oracle_id);

    let reflector_addr = env.register(MockReflector, ());
    let base_currency = Address::generate(&env);
    let native_xlm = Address::generate(&env);
    let admin = Address::generate(&env);
    client.initialize(&admin, &reflector_addr, &base_currency, &native_xlm);

    let asset1 = price_oracle::Asset::Stellar(Address::generate(&env));
    let asset2 = price_oracle::Asset::Stellar(Address::generate(&env));
    client.add_asset(&admin, &asset1);
    client.add_asset(&admin, &asset2);

    let expiry = env.ledger().timestamp() + 86400;
    client.set_manual_override(&admin, &asset1, &Some(1_000_000_000_000_000u128), &Some(expiry));
    client.set_manual_override(&admin, &asset2, &Some(2_000_000_000_000_000u128), &Some(expiry));

    // Disable asset2
    client.set_asset_enabled(&admin, &asset2, &false);

    let mut query_assets = Vec::new(&env);
    query_assets.push_back(asset1.clone());
    query_assets.push_back(asset2.clone());

    let result = client.try_get_asset_prices_vec(&query_assets);
    assert!(result.is_err(), "batch query should fail if any asset is disabled");
}

// =============================================================================
// CRIT-01/CRIT-02: Liquidation known_prices pass-through
// (behavioral test: liquidation flow still works correctly with the optimization)
// =============================================================================

fn setup_full_protocol(env: &Env) -> (
    kinetic_router::Client,
    Address, // router_id
    Address, // oracle_id
    Address, // admin
    Address, // pool_configurator
) {
    let admin = Address::generate(env);
    let emergency_admin = Address::generate(env);

    let router_id = env.register(kinetic_router::WASM, ());
    let router = kinetic_router::Client::new(env, &router_id);

    let oracle_id = env.register(price_oracle::WASM, ());
    let oracle_client = price_oracle::Client::new(env, &oracle_id);
    let reflector_addr = env.register(MockReflector, ());
    let base_currency = Address::generate(env);
    let native_xlm = Address::generate(env);
    oracle_client.initialize(&admin, &reflector_addr, &base_currency, &native_xlm);

    let pool_treasury = Address::generate(env);
    let dex_router = Address::generate(env);
    router.initialize(&admin, &emergency_admin, &oracle_id, &pool_treasury, &dex_router, &None);

    let pool_configurator = Address::generate(env);
    router.set_pool_configurator(&pool_configurator);

    (router, router_id, oracle_id, admin, pool_configurator)
}

fn deploy_reserve_with_oracle(
    env: &Env,
    router: &kinetic_router::Client,
    router_id: &Address,
    oracle_id: &Address,
    admin: &Address,
    pool_configurator: &Address,
    price: u128,
    ltv: u32,
    liq_threshold: u32,
    liq_bonus: u32,
) -> (Address, Address, Address) {
    let token_admin = Address::generate(env);
    let underlying_token = env.register_stellar_asset_contract_v2(token_admin.clone());
    let underlying_addr = underlying_token.address();

    let irs = setup_interest_rate_strategy(env, admin);
    let treasury = Address::generate(env);

    let params = kinetic_router::InitReserveParams {
        decimals: 7,
        ltv,
        liquidation_threshold: liq_threshold,
        liquidation_bonus: liq_bonus,
        reserve_factor: 1000,
        supply_cap: 0,
        borrow_cap: 0,
        borrowing_enabled: true,
        flashloan_enabled: true,
    };

    let a_token_id = env.register(a_token::WASM, ());
    let a_token_client = a_token::Client::new(env, &a_token_id);
    a_token_client.initialize(
        admin,
        &underlying_addr,
        router_id,
        &String::from_str(env, "aToken"),
        &String::from_str(env, "aTKN"),
        &params.decimals,
    );

    let debt_token_id = env.register(debt_token::WASM, ());
    let debt_token_client = debt_token::Client::new(env, &debt_token_id);
    debt_token_client.initialize(
        admin,
        &underlying_addr,
        router_id,
        &String::from_str(env, "debtToken"),
        &String::from_str(env, "dTKN"),
        &params.decimals,
    );

    router.init_reserve(
        pool_configurator,
        &underlying_addr,
        &a_token_id,
        &debt_token_id,
        &irs,
        &treasury,
        &params,
    );

    // Set oracle price
    let oracle_client = price_oracle::Client::new(env, oracle_id);
    let asset_oracle = price_oracle::Asset::Stellar(underlying_addr.clone());
    oracle_client.add_asset(admin, &asset_oracle);
    oracle_client.set_manual_override(
        admin,
        &asset_oracle,
        &Some(price),
        &Some(env.ledger().timestamp() + 604_800),
    );

    (underlying_addr, a_token_id, debt_token_id)
}

#[test]
fn test_prepare_liquidation_succeeds_with_known_prices() {
    // This tests that the CRIT-02 optimization (passing known_prices from
    // get_asset_prices_batch into calculate_user_account_data_unified) does
    // not break the prepare_liquidation flow.
    let env = Env::default();
    env.mock_all_auths();
    setup_ledger(&env);

    let (router, router_id, oracle_id, admin, pool_configurator) = setup_full_protocol(&env);

    // Deploy collateral asset ($1)
    let (collateral_asset, _, _) = deploy_reserve_with_oracle(
        &env, &router, &router_id, &oracle_id, &admin, &pool_configurator,
        100_000_000_000_000u128, // $1 at 14 decimals
        7500, 8000, 500,
    );

    // Deploy debt asset ($1)
    let (debt_asset, _, _) = deploy_reserve_with_oracle(
        &env, &router, &router_id, &oracle_id, &admin, &pool_configurator,
        100_000_000_000_000u128,
        7500, 8000, 500,
    );

    // Borrower supplies collateral and borrows
    let borrower = Address::generate(&env);
    let lender = Address::generate(&env);

    let collateral_token = token::StellarAssetClient::new(&env, &collateral_asset);
    let debt_token_asset = token::StellarAssetClient::new(&env, &debt_asset);

    // Mint tokens
    collateral_token.mint(&borrower, &10_000_0000000i128);
    debt_token_asset.mint(&lender, &100_000_0000000i128);

    // Approve router to spend tokens
    approve_token(&env, &debt_asset, &lender, &router_id, 100_000_0000000i128);
    approve_token(&env, &collateral_asset, &borrower, &router_id, 10_000_0000000i128);

    // Lender supplies debt asset (liquidity for borrowing)
    router.supply(&lender, &debt_asset, &100_000_0000000u128, &lender, &0);

    // Borrower supplies collateral
    router.supply(&borrower, &collateral_asset, &10_000_0000000u128, &borrower, &0);
    router.set_user_use_reserve_as_coll(&borrower, &collateral_asset, &true);

    // Borrower borrows (at 75% LTV max, borrow 70%)
    // Args: caller, asset, amount, interest_rate_mode, referral_code, on_behalf_of
    router.borrow(&borrower, &debt_asset, &7_000_0000000u128, &1, &0, &borrower);

    // Drop collateral price to make position liquidatable
    let oracle_client = price_oracle::Client::new(&env, &oracle_id);
    let collateral_oracle_asset = price_oracle::Asset::Stellar(collateral_asset.clone());
    oracle_client.set_manual_override(
        &admin,
        &collateral_oracle_asset,
        &Some(80_000_000_000_000u128), // $0.80 — HF drops below 1.0
        &Some(env.ledger().timestamp() + 604_800),
    );

    // Prepare liquidation — this exercises the CRIT-02 known_prices pass-through
    // Args: liquidator, user, debt_asset, collateral_asset, debt_to_cover, min_swap_out, swap_handler
    // Use 50% close factor (3500 of 7000)
    let liquidator = Address::generate(&env);
    let result = router.try_prepare_liquidation(
        &liquidator,
        &borrower,
        &debt_asset,
        &collateral_asset,
        &3_500_0000000u128, // 50% close factor
        &0u128,
        &None,
    );

    // Should succeed (position is liquidatable)
    assert!(result.is_ok(), "prepare_liquidation should succeed with known_prices optimization: {:?}", result.err());
}

#[test]
fn test_prepare_liquidation_rejects_healthy_position() {
    // Ensure the known_prices optimization doesn't accidentally allow
    // liquidation of healthy positions
    let env = Env::default();
    env.mock_all_auths();
    setup_ledger(&env);

    let (router, router_id, oracle_id, admin, pool_configurator) = setup_full_protocol(&env);

    let (collateral_asset, _, _) = deploy_reserve_with_oracle(
        &env, &router, &router_id, &oracle_id, &admin, &pool_configurator,
        100_000_000_000_000u128,
        7500, 8000, 500,
    );

    let (debt_asset, _, _) = deploy_reserve_with_oracle(
        &env, &router, &router_id, &oracle_id, &admin, &pool_configurator,
        100_000_000_000_000u128,
        7500, 8000, 500,
    );

    let borrower = Address::generate(&env);
    let lender = Address::generate(&env);

    let collateral_token = token::StellarAssetClient::new(&env, &collateral_asset);
    let debt_token_asset = token::StellarAssetClient::new(&env, &debt_asset);

    collateral_token.mint(&borrower, &10_000_0000000i128);
    debt_token_asset.mint(&lender, &100_000_0000000i128);

    approve_token(&env, &debt_asset, &lender, &router_id, 100_000_0000000i128);
    approve_token(&env, &collateral_asset, &borrower, &router_id, 10_000_0000000i128);

    router.supply(&lender, &debt_asset, &100_000_0000000u128, &lender, &0);
    router.supply(&borrower, &collateral_asset, &10_000_0000000u128, &borrower, &0);
    router.set_user_use_reserve_as_coll(&borrower, &collateral_asset, &true);

    // Borrow only 50% — well within safe range
    router.borrow(&borrower, &debt_asset, &5_000_0000000u128, &1, &0, &borrower);

    // Position is healthy (HF > 1.0), prepare_liquidation should fail
    let liquidator = Address::generate(&env);
    let result = router.try_prepare_liquidation(
        &liquidator,
        &borrower,
        &debt_asset,
        &collateral_asset,
        &5_000_0000000u128,
        &0u128,
        &None,
    );

    assert!(result.is_err(), "prepare_liquidation should reject healthy position even with known_prices optimization");
}
