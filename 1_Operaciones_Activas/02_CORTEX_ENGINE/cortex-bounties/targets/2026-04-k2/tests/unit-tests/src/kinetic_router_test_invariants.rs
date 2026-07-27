#![cfg(test)]

//! Phase 2: Protocol Invariant Tests
//!
//! Validates fundamental protocol invariants that must hold across all operations:
//! - Index monotonicity under supply-only vs borrow activity
//! - UserConfiguration bitmap consistency with token balances
//! - Protocol solvency (total supply >= total debt)
//! - Health factor remains >= 1.0 after all standard operations

use crate::{a_token, debt_token, interest_rate_strategy, kinetic_router, price_oracle};
use k2_shared::{RAY, WAD, ReserveConfiguration as SharedReserveConfiguration};
use soroban_sdk::{
    contract, contractimpl,
    testutils::{Address as _, Ledger, LedgerInfo},
    token, Address, Env, IntoVal, String, Symbol, Vec,
};

// =============================================================================
// Mock Oracle (same as Phase 1)
// =============================================================================

#[contract]
pub struct MockReflector;

#[contractimpl]
impl MockReflector {
    pub fn decimals(_env: Env) -> u32 {
        14
    }
}

// =============================================================================
// Setup Helpers (reused pattern from Phase 1)
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
    init_args.push_back((0u128).into_val(env)); // base rate
    init_args.push_back((40_000_000_000_000_000_000u128).into_val(env)); // slope1 (40%)
    init_args.push_back((100_000_000_000_000_000_000u128).into_val(env)); // slope2 (100%)
    init_args.push_back((800_000_000_000_000_000_000_000_000u128).into_val(env)); // optimal (80%)
    let _: () = env.invoke_contract(&contract_id, &Symbol::new(env, "initialize"), init_args);
    contract_id
}

fn deploy_reserve(
    env: &Env,
    kinetic_router_addr: &Address,
    oracle_addr: &Address,
    admin: &Address,
    ltv: u32,
    liquidation_threshold: u32,
    liquidation_bonus: u32,
) -> (Address, Address, Address) {
    let token_admin = Address::generate(env);
    let underlying_token = env.register_stellar_asset_contract_v2(token_admin.clone());
    let underlying_addr = underlying_token.address();

    let irs_addr = setup_interest_rate_strategy(env, admin);
    let treasury = Address::generate(env);

    let params = kinetic_router::InitReserveParams {
        decimals: 7,
        ltv,
        liquidation_threshold,
        liquidation_bonus,
        reserve_factor: 1000,
        supply_cap: 0,
        borrow_cap: 0,
        borrowing_enabled: true,
        flashloan_enabled: true,
    };

    let a_token_addr = env.register(a_token::WASM, ());
    let a_token_client = a_token::Client::new(env, &a_token_addr);
    a_token_client.initialize(
        admin,
        &underlying_addr,
        kinetic_router_addr,
        &String::from_str(env, "aToken"),
        &String::from_str(env, "aTKN"),
        &params.decimals,
    );

    let debt_token_addr = env.register(debt_token::WASM, ());
    let debt_token_client = debt_token::Client::new(env, &debt_token_addr);
    debt_token_client.initialize(
        admin,
        &underlying_addr,
        kinetic_router_addr,
        &String::from_str(env, "debtToken"),
        &String::from_str(env, "dTKN"),
        &params.decimals,
    );

    let pool_configurator = Address::generate(env);
    let router_client = kinetic_router::Client::new(env, kinetic_router_addr);
    router_client.set_pool_configurator(&pool_configurator);
    router_client.init_reserve(
        &pool_configurator,
        &underlying_addr,
        &a_token_addr,
        &debt_token_addr,
        &irs_addr,
        &treasury,
        &params,
    );

    // Register asset in oracle and set $1.00 price
    let oracle_client = price_oracle::Client::new(env, oracle_addr);
    let asset_oracle = price_oracle::Asset::Stellar(underlying_addr.clone());
    oracle_client.add_asset(admin, &asset_oracle);
    oracle_client.set_manual_override(
        admin,
        &asset_oracle,
        &Some(100_000_000_000_000u128), // $1.00 at 14 decimals
        &Some(env.ledger().timestamp() + 604_800), // 7 days (max allowed by L-04)
    );

    (underlying_addr, a_token_addr, debt_token_addr)
}

fn deploy_protocol(env: &Env) -> (Address, Address, Address, Address) {
    let admin = Address::generate(env);
    let emergency_admin = Address::generate(env);

    let kinetic_router_addr = env.register(kinetic_router::WASM, ());
    let kinetic_router = kinetic_router::Client::new(env, &kinetic_router_addr);

    let oracle_addr = env.register(price_oracle::WASM, ());
    let oracle_client = price_oracle::Client::new(env, &oracle_addr);
    let reflector_addr = env.register(MockReflector, ());
    let base_currency = Address::generate(env);
    let native_xlm = Address::generate(env);
    oracle_client.initialize(&admin, &reflector_addr, &base_currency, &native_xlm);

    let pool_treasury = Address::generate(env);
    let dex_router = Address::generate(env);
    kinetic_router.initialize(
        &admin,
        &emergency_admin,
        &oracle_addr,
        &pool_treasury,
        &dex_router,
        &None,
    );

    (kinetic_router_addr, oracle_addr, admin, emergency_admin)
}

fn mint_and_approve(env: &Env, underlying: &Address, router: &Address, user: &Address, amount: u128) {
    let stellar_token = token::StellarAssetClient::new(env, underlying);
    stellar_token.mint(user, &(amount as i128));
    let token_client = token::Client::new(env, underlying);
    let expiration = env.ledger().sequence() + 1_000_000;
    token_client.approve(user, router, &(amount as i128), &expiration);
}

fn advance_time(env: &Env, seconds: u64) {
    let info = env.ledger().get();
    env.ledger().set(LedgerInfo {
        sequence_number: info.sequence_number + 10,
        timestamp: info.timestamp + seconds,
        ..info
    });
}

// =============================================================================
// Test 17: Index monotonicity under supply-only (no borrows)
// =============================================================================

#[test]
fn test_invariant_index_monotonicity_supply() {
    let env = Env::default();
    env.mock_all_auths();
    env.budget().reset_unlimited();
    setup_ledger(&env);

    let (router_addr, oracle_addr, admin, _) = deploy_protocol(&env);
    let (underlying, _, _) = deploy_reserve(&env, &router_addr, &oracle_addr, &admin, 8000, 8500, 500);
    let router = kinetic_router::Client::new(&env, &router_addr);

    let user = Address::generate(&env);
    let supply_amount = 1_000_0000000u128;
    mint_and_approve(&env, &underlying, &router_addr, &user, supply_amount);
    router.supply(&user, &underlying, &supply_amount, &user, &0u32);

    // Record initial index
    let initial = router.get_reserve_data(&underlying);
    let mut prev_liquidity_index = initial.liquidity_index;

    assert!(prev_liquidity_index >= RAY, "Initial liquidity index should be >= RAY");

    // With no borrows, liquidity index should remain constant (no interest to distribute)
    for i in 0..3 {
        advance_time(&env, 3600); // 1 hour

        // Small supply to trigger state update
        let small = 1_0000000u128;
        mint_and_approve(&env, &underlying, &router_addr, &user, small);
        router.supply(&user, &underlying, &small, &user, &0u32);

        let current = router.get_reserve_data(&underlying);

        // INVARIANT: Liquidity index must never decrease
        assert!(
            current.liquidity_index >= prev_liquidity_index,
            "Liquidity index decreased in supply-only! iteration={}, prev={}, current={}",
            i, prev_liquidity_index, current.liquidity_index
        );

        prev_liquidity_index = current.liquidity_index;
    }

    // With no borrows, index should stay at RAY (no interest accrued)
    assert_eq!(
        prev_liquidity_index, RAY,
        "Liquidity index should remain at RAY with no borrows"
    );
}

// =============================================================================
// Test 18: Index monotonicity under borrow activity
// =============================================================================

#[test]
fn test_invariant_index_monotonicity_borrow() {
    let env = Env::default();
    env.mock_all_auths();
    env.budget().reset_unlimited();
    setup_ledger(&env);

    let (router_addr, oracle_addr, admin, _) = deploy_protocol(&env);
    let (underlying, _, _) = deploy_reserve(&env, &router_addr, &oracle_addr, &admin, 8000, 8500, 500);
    let router = kinetic_router::Client::new(&env, &router_addr);

    let lp = Address::generate(&env);
    let borrower = Address::generate(&env);

    // LP provides liquidity
    let lp_amount = 1_000_0000000u128;
    mint_and_approve(&env, &underlying, &router_addr, &lp, lp_amount);
    router.supply(&lp, &underlying, &lp_amount, &lp, &0u32);

    // Borrower supplies collateral and borrows
    let collateral = 500_0000000u128;
    let borrow = 100_0000000u128;
    mint_and_approve(&env, &underlying, &router_addr, &borrower, collateral);
    router.supply(&borrower, &underlying, &collateral, &borrower, &0u32);
    router.borrow(&borrower, &underlying, &borrow, &1u32, &0u32, &borrower);

    // Record initial indices
    let initial = router.get_reserve_data(&underlying);
    let mut prev_liquidity_index = initial.liquidity_index;
    let mut prev_borrow_index = initial.variable_borrow_index;

    // Advance time repeatedly and verify monotonicity
    for i in 0..5 {
        advance_time(&env, 3600); // 1 hour

        // Small supply to trigger state update
        let small = 1_0000000u128;
        mint_and_approve(&env, &underlying, &router_addr, &lp, small);
        router.supply(&lp, &underlying, &small, &lp, &0u32);

        let current = router.get_reserve_data(&underlying);

        // INVARIANT: Both indices must never decrease
        assert!(
            current.liquidity_index >= prev_liquidity_index,
            "Liquidity index decreased! iteration={}, prev={}, current={}",
            i, prev_liquidity_index, current.liquidity_index
        );
        assert!(
            current.variable_borrow_index >= prev_borrow_index,
            "Borrow index decreased! iteration={}, prev={}, current={}",
            i, prev_borrow_index, current.variable_borrow_index
        );

        prev_liquidity_index = current.liquidity_index;
        prev_borrow_index = current.variable_borrow_index;
    }

    // With active borrows, both indices should have grown
    assert!(
        prev_liquidity_index > initial.liquidity_index,
        "Liquidity index should grow with active borrows"
    );
    assert!(
        prev_borrow_index > initial.variable_borrow_index,
        "Borrow index should grow with active borrows"
    );
}

// =============================================================================
// Test 19: UserConfiguration bitmap matches token balances
// =============================================================================

#[test]
fn test_invariant_user_config_matches_balances() {
    let env = Env::default();
    env.mock_all_auths();
    env.budget().reset_unlimited();
    setup_ledger(&env);

    let (router_addr, oracle_addr, admin, _) = deploy_protocol(&env);
    let (asset_a, a_token_a, debt_token_a) =
        deploy_reserve(&env, &router_addr, &oracle_addr, &admin, 8000, 8500, 500);
    let (asset_b, a_token_b, debt_token_b) =
        deploy_reserve(&env, &router_addr, &oracle_addr, &admin, 8000, 8500, 500);
    let router = kinetic_router::Client::new(&env, &router_addr);

    let lp = Address::generate(&env);
    let user = Address::generate(&env);

    // LP provides liquidity in both assets
    let lp_amount = 10_000_0000000u128;
    mint_and_approve(&env, &asset_a, &router_addr, &lp, lp_amount);
    router.supply(&lp, &asset_a, &lp_amount, &lp, &0u32);
    mint_and_approve(&env, &asset_b, &router_addr, &lp, lp_amount);
    router.supply(&lp, &asset_b, &lp_amount, &lp, &0u32);

    // Get reserve IDs
    let reserve_a = router.get_reserve_data(&asset_a);
    let reserve_b = router.get_reserve_data(&asset_b);
    let id_a = reserve_a.id as u8;
    let id_b = reserve_b.id as u8;

    // === State 1: User has no positions ===
    let config_0 = router.get_user_configuration(&user);
    assert!(config_0.data == 0, "New user should have empty config");

    // === State 2: User supplies asset A (becomes collateral) ===
    let supply_a = 500_0000000u128;
    mint_and_approve(&env, &asset_a, &router_addr, &user, supply_a);
    router.supply(&user, &asset_a, &supply_a, &user, &0u32);

    let config_1 = router.get_user_configuration(&user);
    let a_token_client_a = a_token::Client::new(&env, &a_token_a);
    let a_bal_a = a_token_client_a.balance(&user);

    // Collateral flag should be set for asset A
    let collateral_flag_a = (config_1.data >> ((id_a as u32) * 2)) & 1;
    assert!(a_bal_a > 0, "User should have aToken A balance");
    assert_eq!(collateral_flag_a, 1, "Collateral flag should be set for asset A (id={})", id_a);

    // No borrowing flag for asset A
    let borrow_flag_a = (config_1.data >> ((id_a as u32) * 2 + 1)) & 1;
    assert_eq!(borrow_flag_a, 0, "Borrow flag should not be set for asset A");

    // === State 3: User borrows asset B ===
    let borrow_b = 100_0000000u128;
    router.borrow(&user, &asset_b, &borrow_b, &1u32, &0u32, &user);

    let config_2 = router.get_user_configuration(&user);
    let debt_token_client_b = debt_token::Client::new(&env, &debt_token_b);
    let debt_bal_b = debt_token_client_b.balance(&user);

    // Borrow flag should be set for asset B
    let borrow_flag_b = (config_2.data >> ((id_b as u32) * 2 + 1)) & 1;
    assert!(debt_bal_b > 0, "User should have debt token B balance");
    assert_eq!(borrow_flag_b, 1, "Borrow flag should be set for asset B (id={})", id_b);

    // Collateral flag for asset A should still be set
    let collateral_flag_a_2 = (config_2.data >> ((id_a as u32) * 2)) & 1;
    assert_eq!(collateral_flag_a_2, 1, "Collateral flag should still be set for asset A");

    // === State 4: User repays all debt → borrow flag should clear ===
    mint_and_approve(&env, &asset_b, &router_addr, &user, borrow_b * 2); // extra for interest
    router.repay(&user, &asset_b, &u128::MAX, &1u32, &user);

    let config_3 = router.get_user_configuration(&user);
    let debt_bal_b_post = debt_token_client_b.balance(&user);

    assert_eq!(debt_bal_b_post, 0, "Debt should be fully repaid");
    let borrow_flag_b_post = (config_3.data >> ((id_b as u32) * 2 + 1)) & 1;
    assert_eq!(borrow_flag_b_post, 0, "Borrow flag should clear after full repay (id={})", id_b);

    // === State 5: User withdraws all collateral → collateral flag should clear ===
    router.withdraw(&user, &asset_a, &u128::MAX, &user);

    let config_4 = router.get_user_configuration(&user);
    let a_bal_a_post = a_token_client_a.balance(&user);

    assert_eq!(a_bal_a_post, 0, "aToken A balance should be zero after full withdraw");
    let collateral_flag_a_post = (config_4.data >> ((id_a as u32) * 2)) & 1;
    assert_eq!(collateral_flag_a_post, 0, "Collateral flag should clear after full withdraw (id={})", id_a);

    // Config should be empty
    assert_eq!(config_4.data, 0, "User config should be empty after closing all positions");
}

// =============================================================================
// Test 20: Protocol solvency — total supply >= total debt per reserve
// =============================================================================

#[test]
fn test_invariant_total_supply_ge_total_debt() {
    let env = Env::default();
    env.mock_all_auths();
    env.budget().reset_unlimited();
    setup_ledger(&env);

    let (router_addr, oracle_addr, admin, _) = deploy_protocol(&env);
    let (underlying, a_token_addr, debt_token_addr) =
        deploy_reserve(&env, &router_addr, &oracle_addr, &admin, 8000, 8500, 500);
    let router = kinetic_router::Client::new(&env, &router_addr);

    let lp = Address::generate(&env);
    let borrower = Address::generate(&env);

    // LP provides initial liquidity
    let lp_amount = 10_000_0000000u128;
    mint_and_approve(&env, &underlying, &router_addr, &lp, lp_amount);
    router.supply(&lp, &underlying, &lp_amount, &lp, &0u32);

    // Borrower supplies collateral and borrows
    let collateral = 5_000_0000000u128;
    let borrow = 2_000_0000000u128;
    mint_and_approve(&env, &underlying, &router_addr, &borrower, collateral);
    router.supply(&borrower, &underlying, &collateral, &borrower, &0u32);
    router.borrow(&borrower, &underlying, &borrow, &1u32, &0u32, &borrower);

    let a_token_client = a_token::Client::new(&env, &a_token_addr);
    let debt_token_client = debt_token::Client::new(&env, &debt_token_addr);
    let underlying_client = token::Client::new(&env, &underlying);

    // INVARIANT check immediately after operations
    let reserve = router.get_reserve_data(&underlying);
    let a_supply = a_token_client.total_supply();
    let d_supply = debt_token_client.total_supply();

    assert!(
        (a_supply as i128) >= d_supply,
        "Solvency violated! aToken supply ({}) < debt supply ({})",
        a_supply, d_supply
    );

    // Underlying held by aToken contract should cover available liquidity
    let underlying_in_pool = underlying_client.balance(&a_token_addr);
    assert!(
        underlying_in_pool > 0,
        "Pool should hold underlying tokens"
    );

    // Advance time to accrue interest and re-check
    for _ in 0..3 {
        advance_time(&env, 86_400); // 1 day

        // Trigger state update with small supply
        let small = 1_0000000u128;
        mint_and_approve(&env, &underlying, &router_addr, &lp, small);
        router.supply(&lp, &underlying, &small, &lp, &0u32);

        let reserve_updated = router.get_reserve_data(&underlying);
        let a_supply_updated = a_token_client.total_supply();
        let d_supply_updated = debt_token_client.total_supply();

        // INVARIANT: Supply must always >= debt (interest accrues to both but debt faster)
        // Note: In Aave-style protocols, debt grows faster than supply (reserve factor takes a cut),
        // but total_supply of aTokens includes the reserve factor portion.
        assert!(
            (a_supply_updated as i128) >= d_supply_updated,
            "Solvency violated after time advance! aToken supply ({}) < debt supply ({})",
            a_supply_updated, d_supply_updated
        );
    }
}

// =============================================================================
// Test 21: Health factor >= 1.0 after standard operations
// =============================================================================

#[test]
fn test_invariant_health_factor_after_operation() {
    let env = Env::default();
    env.mock_all_auths();
    env.budget().reset_unlimited();
    setup_ledger(&env);

    let (router_addr, oracle_addr, admin, _) = deploy_protocol(&env);
    let (asset_a, _, _) = deploy_reserve(&env, &router_addr, &oracle_addr, &admin, 8000, 8500, 500);
    let (asset_b, _, _) = deploy_reserve(&env, &router_addr, &oracle_addr, &admin, 8000, 8500, 500);
    let router = kinetic_router::Client::new(&env, &router_addr);

    let lp = Address::generate(&env);
    let user = Address::generate(&env);

    // LP provides liquidity for asset B
    let lp_amount = 10_000_0000000u128;
    mint_and_approve(&env, &asset_b, &router_addr, &lp, lp_amount);
    router.supply(&lp, &asset_b, &lp_amount, &lp, &0u32);

    // === Operation 1: Supply → HF should be very high (no debt) ===
    let supply_amount = 1_000_0000000u128;
    mint_and_approve(&env, &asset_a, &router_addr, &user, supply_amount);
    router.supply(&user, &asset_a, &supply_amount, &user, &0u32);

    let data_after_supply = router.get_user_account_data(&user);
    assert_eq!(data_after_supply.total_debt_base, 0, "No debt after supply");
    assert!(
        data_after_supply.health_factor >= WAD,
        "HF should be >= 1.0 (WAD) after supply. HF: {}",
        data_after_supply.health_factor
    );

    // === Operation 2: Borrow (within LTV) → HF should remain >= 1.0 ===
    // Max borrow at LTV 80%: 1000 * 0.80 = 800, borrow 400 (safe)
    let borrow_amount = 400_0000000u128;
    router.borrow(&user, &asset_b, &borrow_amount, &1u32, &0u32, &user);

    let data_after_borrow = router.get_user_account_data(&user);
    assert!(
        data_after_borrow.health_factor >= WAD,
        "HF should be >= 1.0 after safe borrow. HF: {}",
        data_after_borrow.health_factor
    );
    // HF = (1000 * 0.85) / 400 = 2.125 → 2.125e18 in WAD
    assert!(
        data_after_borrow.health_factor > WAD * 2,
        "HF should be > 2.0 for this conservative borrow. HF: {}",
        data_after_borrow.health_factor
    );

    // === Operation 3: Partial repay → HF should improve ===
    let hf_before_repay = data_after_borrow.health_factor;
    let repay_amount = 100_0000000u128;
    mint_and_approve(&env, &asset_b, &router_addr, &user, repay_amount);
    router.repay(&user, &asset_b, &repay_amount, &1u32, &user);

    let data_after_repay = router.get_user_account_data(&user);
    assert!(
        data_after_repay.health_factor >= WAD,
        "HF should be >= 1.0 after repay. HF: {}",
        data_after_repay.health_factor
    );
    assert!(
        data_after_repay.health_factor > hf_before_repay,
        "HF should improve after repay. Before: {}, After: {}",
        hf_before_repay, data_after_repay.health_factor
    );

    // === Operation 4: Additional supply → HF should improve ===
    let hf_before_extra_supply = data_after_repay.health_factor;
    let extra_supply = 500_0000000u128;
    mint_and_approve(&env, &asset_a, &router_addr, &user, extra_supply);
    router.supply(&user, &asset_a, &extra_supply, &user, &0u32);

    let data_after_extra_supply = router.get_user_account_data(&user);
    assert!(
        data_after_extra_supply.health_factor >= WAD,
        "HF should be >= 1.0 after additional supply. HF: {}",
        data_after_extra_supply.health_factor
    );
    assert!(
        data_after_extra_supply.health_factor > hf_before_extra_supply,
        "HF should improve after additional supply. Before: {}, After: {}",
        hf_before_extra_supply, data_after_extra_supply.health_factor
    );

    // === Operation 5: Safe partial withdraw → HF should still be >= 1.0 ===
    // Current: 1500 collateral, ~300 debt → HF ≈ 4.25
    // Withdraw 200 → 1300 collateral, ~300 debt → HF ≈ 3.68
    let withdraw_amount = 200_0000000u128;
    router.withdraw(&user, &asset_a, &withdraw_amount, &user);

    let data_after_withdraw = router.get_user_account_data(&user);
    assert!(
        data_after_withdraw.health_factor >= WAD,
        "HF should be >= 1.0 after safe withdraw. HF: {}",
        data_after_withdraw.health_factor
    );

    // === Operation 6: Full repay → HF should be very high ===
    mint_and_approve(&env, &asset_b, &router_addr, &user, 500_0000000u128); // extra for interest
    router.repay(&user, &asset_b, &u128::MAX, &1u32, &user);

    let data_after_full_repay = router.get_user_account_data(&user);
    assert_eq!(data_after_full_repay.total_debt_base, 0, "Debt should be zero after full repay");
    assert!(
        data_after_full_repay.health_factor >= WAD,
        "HF should be >= 1.0 (near max) after full repay. HF: {}",
        data_after_full_repay.health_factor
    );
}

// =============================================================================
// Test 22: Borrow rejects when it would bring HF below 1.0
// =============================================================================

#[test]
fn test_invariant_borrow_rejects_below_ltv() {
    let env = Env::default();
    env.mock_all_auths();
    env.budget().reset_unlimited();
    setup_ledger(&env);

    let (router_addr, oracle_addr, admin, _) = deploy_protocol(&env);
    let (asset_a, _, _) = deploy_reserve(&env, &router_addr, &oracle_addr, &admin, 8000, 8500, 500);
    let (asset_b, _, _) = deploy_reserve(&env, &router_addr, &oracle_addr, &admin, 8000, 8500, 500);
    let router = kinetic_router::Client::new(&env, &router_addr);

    let lp = Address::generate(&env);
    let user = Address::generate(&env);

    // LP provides liquidity
    let lp_amount = 10_000_0000000u128;
    mint_and_approve(&env, &asset_b, &router_addr, &lp, lp_amount);
    router.supply(&lp, &asset_b, &lp_amount, &lp, &0u32);

    // User supplies 100 tokens of asset A as collateral
    let supply_amount = 100_0000000u128;
    mint_and_approve(&env, &asset_a, &router_addr, &user, supply_amount);
    router.supply(&user, &asset_a, &supply_amount, &user, &0u32);

    // At LTV 80%: max borrow = 100 * 0.80 = 80
    // Attempt to borrow 81 → should fail (exceeds LTV)
    let result = router.try_borrow(&user, &asset_b, &81_0000000u128, &1u32, &0u32, &user);
    assert!(result.is_err(), "Borrow exceeding LTV should be rejected");

    // Borrow 79 → should succeed (within LTV)
    router.borrow(&user, &asset_b, &79_0000000u128, &1u32, &0u32, &user);
    let data = router.get_user_account_data(&user);
    assert!(
        data.health_factor >= WAD,
        "HF should be >= 1.0 after borrow within LTV. HF: {}",
        data.health_factor
    );
}

// =============================================================================
// Test 23: Withdraw rejects when it would bring HF below 1.0
// =============================================================================

#[test]
fn test_invariant_withdraw_rejects_below_hf() {
    let env = Env::default();
    env.mock_all_auths();
    env.budget().reset_unlimited();
    setup_ledger(&env);

    let (router_addr, oracle_addr, admin, _) = deploy_protocol(&env);
    let (asset_a, _, _) = deploy_reserve(&env, &router_addr, &oracle_addr, &admin, 8000, 8500, 500);
    let (asset_b, _, _) = deploy_reserve(&env, &router_addr, &oracle_addr, &admin, 8000, 8500, 500);
    let router = kinetic_router::Client::new(&env, &router_addr);

    let lp = Address::generate(&env);
    let user = Address::generate(&env);

    // LP provides liquidity
    let lp_amount = 10_000_0000000u128;
    mint_and_approve(&env, &asset_b, &router_addr, &lp, lp_amount);
    router.supply(&lp, &asset_b, &lp_amount, &lp, &0u32);

    // User supplies 100 tokens and borrows 70 (LTV 80%, HF = 100*0.85/70 = 1.214)
    let supply_amount = 100_0000000u128;
    mint_and_approve(&env, &asset_a, &router_addr, &user, supply_amount);
    router.supply(&user, &asset_a, &supply_amount, &user, &0u32);
    router.borrow(&user, &asset_b, &70_0000000u128, &1u32, &0u32, &user);

    let data = router.get_user_account_data(&user);
    assert!(data.health_factor >= WAD, "Should be healthy initially");

    // Attempt to withdraw too much → HF would drop below 1.0
    // If we withdraw 20 → 80 collateral, 70 debt → HF = 80*0.85/70 = 0.971 → reject
    let result = router.try_withdraw(&user, &asset_a, &20_0000000u128, &user);
    assert!(result.is_err(), "Withdraw that breaks HF should be rejected");

    // Small withdraw should succeed → 95 collateral, 70 debt → HF = 95*0.85/70 = 1.154
    router.withdraw(&user, &asset_a, &5_0000000u128, &user);
    let data_after = router.get_user_account_data(&user);
    assert!(
        data_after.health_factor >= WAD,
        "HF should be >= 1.0 after safe partial withdraw. HF: {}",
        data_after.health_factor
    );
}
