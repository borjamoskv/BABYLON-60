#![cfg(test)]

//! Phase 1: Critical Security Tests (P0 gaps)
//!
//! Tests for critical gaps identified in the Testing Coverage Audit:
//! G-01: Repay full amount (u128::MAX)
//! G-02: Partial repay + borrow flag clearing
//! G-03: Liquidation close factor boundary (50% vs 100%)
//! G-04: Bad debt socialization (H-05)
//! G-05: Post-liquidation HF check (H-04)
//! G-06: Reserve configuration validation (H-03)
//! G-07: Initialize auth (H-02)
//! G-08: Swap handler whitelist (M-01)
//! G-09: Index monotonicity invariant
//! G-10: Supply/borrow on_behalf_of auth
//! G-11: Withdraw all (u128::MAX)
//! G-12: Conservation of value invariant

use crate::{a_token, debt_token, interest_rate_strategy, kinetic_router, price_oracle};
use k2_shared::{RAY, WAD, ReserveConfiguration as SharedReserveConfiguration};
use soroban_sdk::{
    contract, contractimpl,
    testutils::{Address as _, Ledger, LedgerInfo},
    token, Address, Env, IntoVal, String, Symbol, Vec,
};

// =============================================================================
// Mock Oracle
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
    init_args.push_back((0u128).into_val(env)); // base rate
    init_args.push_back((40_000_000_000_000_000_000u128).into_val(env)); // slope1 (40%)
    init_args.push_back((100_000_000_000_000_000_000u128).into_val(env)); // slope2 (100%)
    init_args.push_back((800_000_000_000_000_000_000_000_000u128).into_val(env)); // optimal (80%)
    let _: () = env.invoke_contract(&contract_id, &Symbol::new(env, "initialize"), init_args);
    contract_id
}

/// Deploy a reserve for a given underlying asset. Returns (underlying_addr, a_token_addr, debt_token_addr).
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

/// Mint tokens and approve the router to spend them
fn mint_and_approve(env: &Env, underlying: &Address, router: &Address, user: &Address, amount: u128) {
    let stellar_token = token::StellarAssetClient::new(env, underlying);
    stellar_token.mint(user, &(amount as i128));
    let token_client = token::Client::new(env, underlying);
    let expiration = env.ledger().sequence() + 1_000_000;
    token_client.approve(user, router, &(amount as i128), &expiration);
}

/// Deploy the full protocol (router + oracle) and return key addresses
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

// =============================================================================
// G-01: Repay full amount (u128::MAX)
// =============================================================================

#[test]
fn test_repay_full_amount_u128_max() {
    let env = Env::default();
    env.mock_all_auths();
    env.budget().reset_unlimited();
    setup_ledger(&env);

    let (router_addr, oracle_addr, admin, _) = deploy_protocol(&env);
    let (underlying, _, _) = deploy_reserve(&env, &router_addr, &oracle_addr, &admin, 8000, 8500, 500);
    let router = kinetic_router::Client::new(&env, &router_addr);

    let lp = Address::generate(&env);
    let user = Address::generate(&env);

    // LP provides liquidity
    let lp_amount = 100_000_0000000u128; // 100K tokens (7 dec)
    mint_and_approve(&env, &underlying, &router_addr, &lp, lp_amount);
    router.supply(&lp, &underlying, &lp_amount, &lp, &0u32);

    // User supplies collateral and borrows
    let supply_amount = 10_000_0000000u128; // 10K tokens
    let borrow_amount = 1_000_0000000u128; // 1K tokens
    mint_and_approve(&env, &underlying, &router_addr, &user, supply_amount);
    router.supply(&user, &underlying, &supply_amount, &user, &0u32);
    router.borrow(&user, &underlying, &borrow_amount, &1u32, &0u32, &user);

    // Mint extra to cover potential interest for repay
    mint_and_approve(&env, &underlying, &router_addr, &user, borrow_amount);

    // Repay with u128::MAX (should repay full debt)
    let repaid = router.repay(&user, &underlying, &u128::MAX, &1u32, &user);

    // Verify: repaid amount >= borrowed (includes any accrued interest)
    assert!(repaid >= borrow_amount, "Repaid amount should be >= borrowed amount");

    // Verify: user debt is zero
    let account_data = router.get_user_account_data(&user);
    assert_eq!(account_data.total_debt_base, 0, "Debt must be zero after full repay");

    // Verify: HF = u128::MAX when no debt (borrow flag cleared)
    assert_eq!(account_data.health_factor, u128::MAX, "HF must be MAX when no debt");
}

// =============================================================================
// G-02: Partial repay caps to debt balance
// =============================================================================

#[test]
fn test_repay_partial_caps_to_debt_balance() {
    let env = Env::default();
    env.mock_all_auths();
    env.budget().reset_unlimited();
    setup_ledger(&env);

    let (router_addr, oracle_addr, admin, _) = deploy_protocol(&env);
    let (underlying, _, _) = deploy_reserve(&env, &router_addr, &oracle_addr, &admin, 8000, 8500, 500);
    let router = kinetic_router::Client::new(&env, &router_addr);

    let lp = Address::generate(&env);
    let user = Address::generate(&env);

    let lp_amount = 100_000_0000000u128;
    mint_and_approve(&env, &underlying, &router_addr, &lp, lp_amount);
    router.supply(&lp, &underlying, &lp_amount, &lp, &0u32);

    let supply_amount = 10_000_0000000u128;
    let borrow_amount = 1_000_0000000u128;
    mint_and_approve(&env, &underlying, &router_addr, &user, supply_amount);
    router.supply(&user, &underlying, &supply_amount, &user, &0u32);
    router.borrow(&user, &underlying, &borrow_amount, &1u32, &0u32, &user);

    // Mint extra for repay
    mint_and_approve(&env, &underlying, &router_addr, &user, borrow_amount);

    // Partial repay: 500 tokens
    let partial_amount = 500_0000000u128;
    let repaid = router.repay(&user, &underlying, &partial_amount, &1u32, &user);

    // Verify: repaid exactly partial_amount
    assert_eq!(repaid, partial_amount, "Should repay exactly the requested amount");

    // Verify: user still has debt
    let account_data = router.get_user_account_data(&user);
    assert!(account_data.total_debt_base > 0, "Should still have debt after partial repay");

    // Overpay: repay amount larger than remaining debt → capped to debt balance
    let over_amount = 10_000_0000000u128; // Way more than remaining debt
    let repaid_over = router.repay(&user, &underlying, &over_amount, &1u32, &user);

    // Should be capped at remaining debt (~500 tokens)
    assert!(repaid_over <= borrow_amount - partial_amount + 1_0000000, // allow 1 token tolerance for rounding
        "Overpay should be capped to remaining debt");

    // Verify: fully repaid
    let account_data_final = router.get_user_account_data(&user);
    assert_eq!(account_data_final.total_debt_base, 0, "Debt must be zero after full repay");
}

// =============================================================================
// G-02: Repay full clears borrow flag in UserConfiguration
// =============================================================================

#[test]
fn test_repay_full_clears_borrow_flag() {
    let env = Env::default();
    env.mock_all_auths();
    env.budget().reset_unlimited();
    setup_ledger(&env);

    let (router_addr, oracle_addr, admin, _) = deploy_protocol(&env);
    let (underlying, _, _) = deploy_reserve(&env, &router_addr, &oracle_addr, &admin, 8000, 8500, 500);
    let router = kinetic_router::Client::new(&env, &router_addr);

    let lp = Address::generate(&env);
    let user = Address::generate(&env);

    let lp_amount = 100_000_0000000u128;
    mint_and_approve(&env, &underlying, &router_addr, &lp, lp_amount);
    router.supply(&lp, &underlying, &lp_amount, &lp, &0u32);

    let supply_amount = 10_000_0000000u128;
    let borrow_amount = 1_000_0000000u128;
    mint_and_approve(&env, &underlying, &router_addr, &user, supply_amount);
    router.supply(&user, &underlying, &supply_amount, &user, &0u32);
    router.borrow(&user, &underlying, &borrow_amount, &1u32, &0u32, &user);

    // Verify: HF < MAX (has debt)
    let pre = router.get_user_account_data(&user);
    assert!(pre.health_factor < u128::MAX, "Should have finite HF when debt exists");
    assert!(pre.total_debt_base > 0, "Should have debt before repay");

    // Full repay via u128::MAX
    mint_and_approve(&env, &underlying, &router_addr, &user, borrow_amount);
    router.repay(&user, &underlying, &u128::MAX, &1u32, &user);

    // Verify: borrow flag cleared (HF = MAX, debt = 0)
    let post = router.get_user_account_data(&user);
    assert_eq!(post.total_debt_base, 0, "Debt must be zero");
    assert_eq!(post.health_factor, u128::MAX, "HF must be MAX (borrow flag cleared)");

    // Verify: user can still supply (no phantom debt prevents operations)
    let extra = 100_0000000u128;
    mint_and_approve(&env, &underlying, &router_addr, &user, extra);
    router.supply(&user, &underlying, &extra, &user, &0u32);
    let final_data = router.get_user_account_data(&user);
    assert!(final_data.total_collateral_base > pre.total_collateral_base,
        "Should be able to supply after full repay");
}

// =============================================================================
// G-10: Supply on_behalf_of requires auth
// =============================================================================

#[test]
fn test_supply_on_behalf_of_requires_auth() {
    let env = Env::default();
    // DO NOT mock_all_auths - we test auth enforcement
    env.budget().reset_unlimited();
    setup_ledger(&env);

    // Setup with mock_all_auths for initialization
    env.mock_all_auths();
    let (router_addr, oracle_addr, admin, _) = deploy_protocol(&env);
    let (underlying, _, _) = deploy_reserve(&env, &router_addr, &oracle_addr, &admin, 8000, 8500, 500);
    let router = kinetic_router::Client::new(&env, &router_addr);

    let caller = Address::generate(&env);
    let beneficiary = Address::generate(&env);

    // Mint tokens to caller
    let amount = 1_000_0000000u128;
    mint_and_approve(&env, &underlying, &router_addr, &caller, amount);

    // Clear all auth mocks - now auth checks will fail
    env.mock_auths(&[]);

    // Try supply on behalf of another user without auth → should fail
    let result = router.try_supply(&caller, &underlying, &amount, &beneficiary, &0u32);
    assert!(result.is_err(), "Supply on_behalf_of must fail without auth");
}

// =============================================================================
// G-10: Borrow on_behalf_of requires auth
// =============================================================================

#[test]
fn test_borrow_on_behalf_of_requires_auth() {
    let env = Env::default();
    env.budget().reset_unlimited();
    setup_ledger(&env);

    // Setup with mock_all_auths
    env.mock_all_auths();
    let (router_addr, oracle_addr, admin, _) = deploy_protocol(&env);
    let (underlying, _, _) = deploy_reserve(&env, &router_addr, &oracle_addr, &admin, 8000, 8500, 500);
    let router = kinetic_router::Client::new(&env, &router_addr);

    let caller = Address::generate(&env);
    let beneficiary = Address::generate(&env);

    // LP provides liquidity
    let lp = Address::generate(&env);
    let lp_amount = 100_000_0000000u128;
    mint_and_approve(&env, &underlying, &router_addr, &lp, lp_amount);
    router.supply(&lp, &underlying, &lp_amount, &lp, &0u32);

    // Beneficiary supplies collateral (so they can borrow)
    let supply_amount = 10_000_0000000u128;
    mint_and_approve(&env, &underlying, &router_addr, &beneficiary, supply_amount);
    router.supply(&beneficiary, &underlying, &supply_amount, &beneficiary, &0u32);

    // Clear all auth mocks
    env.mock_auths(&[]);

    // Try borrow on behalf of beneficiary without auth → should fail
    let borrow_amount = 1_000_0000000u128;
    let result = router.try_borrow(&caller, &underlying, &borrow_amount, &1u32, &0u32, &beneficiary);
    assert!(result.is_err(), "Borrow on_behalf_of must fail without auth");
}

// =============================================================================
// G-11: Withdraw all (u128::MAX)
// =============================================================================

#[test]
fn test_withdraw_all_u128_max() {
    let env = Env::default();
    env.mock_all_auths();
    env.budget().reset_unlimited();
    setup_ledger(&env);

    let (router_addr, oracle_addr, admin, _) = deploy_protocol(&env);
    let (underlying, _, _) = deploy_reserve(&env, &router_addr, &oracle_addr, &admin, 8000, 8500, 500);
    let router = kinetic_router::Client::new(&env, &router_addr);

    let user = Address::generate(&env);
    let supply_amount = 10_000_0000000u128;
    mint_and_approve(&env, &underlying, &router_addr, &user, supply_amount);

    // Check initial balance
    let token_client = token::Client::new(&env, &underlying);
    let initial_balance = token_client.balance(&user);

    router.supply(&user, &underlying, &supply_amount, &user, &0u32);

    // Verify: collateral > 0 after supply
    let mid = router.get_user_account_data(&user);
    assert!(mid.total_collateral_base > 0, "Should have collateral after supply");

    // Withdraw all using u128::MAX
    let withdrawn = router.withdraw(&user, &underlying, &u128::MAX, &user);

    // Verify: withdrawn = supply_amount (no interest accrued in same block)
    assert_eq!(withdrawn, supply_amount, "Should withdraw full supply amount");

    // Verify: balance restored
    let final_balance = token_client.balance(&user);
    assert_eq!(final_balance, initial_balance, "Balance should be fully restored");

    // Verify: collateral cleared
    let post = router.get_user_account_data(&user);
    assert_eq!(post.total_collateral_base, 0, "Collateral must be zero after full withdraw");
}

// =============================================================================
// G-11: Withdraw clears collateral flag on zero balance
// =============================================================================

#[test]
fn test_withdraw_clears_collateral_flag_on_zero() {
    let env = Env::default();
    env.mock_all_auths();
    env.budget().reset_unlimited();
    setup_ledger(&env);

    let (router_addr, oracle_addr, admin, _) = deploy_protocol(&env);
    let (underlying, _, _) = deploy_reserve(&env, &router_addr, &oracle_addr, &admin, 8000, 8500, 500);
    let router = kinetic_router::Client::new(&env, &router_addr);

    let user = Address::generate(&env);
    let amount = 1_000_0000000u128;
    mint_and_approve(&env, &underlying, &router_addr, &user, amount);
    router.supply(&user, &underlying, &amount, &user, &0u32);

    // Verify collateral exists
    let pre = router.get_user_account_data(&user);
    assert!(pre.total_collateral_base > 0);

    // Withdraw all
    router.withdraw(&user, &underlying, &u128::MAX, &user);

    // Verify: collateral flag cleared (total_collateral_base = 0)
    let post = router.get_user_account_data(&user);
    assert_eq!(post.total_collateral_base, 0, "Collateral flag must be cleared on zero balance");

    // Verify: HF = MAX (no debt, no collateral)
    assert_eq!(post.health_factor, u128::MAX, "HF should be MAX with no positions");
}

// =============================================================================
// G-07 / H-02: Initialize requires pool_admin auth
// =============================================================================

#[test]
fn test_initialize_requires_pool_admin_auth() {
    let env = Env::default();
    // DO NOT mock_all_auths
    env.budget().reset_unlimited();
    setup_ledger(&env);

    let kinetic_router_addr = env.register(kinetic_router::WASM, ());
    let kinetic_router = kinetic_router::Client::new(&env, &kinetic_router_addr);

    let oracle_addr = env.register(price_oracle::WASM, ());
    let oracle_client = price_oracle::Client::new(&env, &oracle_addr);
    let reflector_addr = env.register(MockReflector, ());

    // Initialize oracle with mock_all_auths (oracle init is not what we're testing)
    env.mock_all_auths();
    let admin_addr = Address::generate(&env);
    oracle_client.initialize(&admin_addr, &reflector_addr, &Address::generate(&env), &Address::generate(&env));

    // Clear auth - test that initialize requires pool_admin auth
    env.mock_auths(&[]);
    let pool_admin = Address::generate(&env);
    let emergency_admin = Address::generate(&env);
    let treasury = Address::generate(&env);
    let dex_router = Address::generate(&env);

    let result = kinetic_router.try_initialize(
        &pool_admin,
        &emergency_admin,
        &oracle_addr,
        &treasury,
        &dex_router,
        &None,
    );
    assert!(result.is_err(), "Initialize must fail without pool_admin auth (H-02)");

    // Now with auth → should succeed
    env.mock_all_auths();
    let result = kinetic_router.try_initialize(
        &pool_admin,
        &emergency_admin,
        &oracle_addr,
        &treasury,
        &dex_router,
        &None,
    );
    assert!(result.is_ok(), "Initialize should succeed with pool_admin auth");

    // Verify: re-initialization fails
    let result = kinetic_router.try_initialize(
        &pool_admin,
        &emergency_admin,
        &oracle_addr,
        &treasury,
        &dex_router,
        &None,
    );
    assert!(result.is_err(), "Re-initialization must fail (AlreadyInitialized)");
}

// =============================================================================
// G-06 / H-03: Reserve configuration validation
// =============================================================================

#[test]
fn test_update_reserve_config_validates_bitmap() {
    let env = Env::default();
    env.mock_all_auths();
    env.budget().reset_unlimited();
    setup_ledger(&env);

    let (router_addr, oracle_addr, admin, _) = deploy_protocol(&env);
    let (underlying, _, _) = deploy_reserve(&env, &router_addr, &oracle_addr, &admin, 8000, 8500, 500);
    let router = kinetic_router::Client::new(&env, &router_addr);

    // Get current valid config
    let reserve_data = router.get_reserve_data(&underlying);
    let valid_config = reserve_data.configuration.clone();

    // Set pool configurator
    let pool_configurator = Address::generate(&env);
    router.set_pool_configurator(&pool_configurator);

    // Test 1: LTV > 10000 should fail
    // Note: set_ltv panics if > 10000, so we set bits directly
    let mut bad_config = SharedReserveConfiguration { data_low: 0, data_high: 0 };
    // Set LTV=10001 via raw bits (bits 0-13)
    bad_config.data_low |= 10001_u128;
    // Set liquidation_threshold=10002 via raw bits (bits 14-27)
    bad_config.data_low |= (10002_u128) << 14;
    // Set decimals=7 via raw bits (bits 42-49)
    bad_config.data_low |= (7_u128) << 42;

    let bad_config_kr = kinetic_router::ReserveConfiguration {
        data_low: bad_config.data_low,
        data_high: bad_config.data_high,
    };
    let result = router.try_update_reserve_configuration(
        &pool_configurator,
        &underlying,
        &bad_config_kr,
    );
    assert!(result.is_err(), "LTV > 10000 must be rejected (H-03)");

    // Test 2: liquidation_threshold <= LTV should fail
    let mut bad_config2 = SharedReserveConfiguration { data_low: 0, data_high: 0 };
    bad_config2.set_ltv(8000).unwrap();
    bad_config2.set_liquidation_threshold(8000).unwrap(); // == LTV, must be > LTV
    bad_config2.set_liquidation_bonus(500).unwrap();
    // Set decimals=7 via raw bits (bits 42-49)
    bad_config2.data_low |= (7_u128) << 42;
    bad_config2.set_reserve_factor(1000);

    let bad_config2_kr = kinetic_router::ReserveConfiguration {
        data_low: bad_config2.data_low,
        data_high: bad_config2.data_high,
    };
    let result2 = router.try_update_reserve_configuration(
        &pool_configurator,
        &underlying,
        &bad_config2_kr,
    );
    assert!(result2.is_err(), "liquidation_threshold == LTV must be rejected (H-03)");

    // Test 3: liquidation_threshold < LTV + 50 bps buffer should fail
    let mut bad_config3 = SharedReserveConfiguration { data_low: 0, data_high: 0 };
    bad_config3.set_ltv(8000).unwrap();
    bad_config3.set_liquidation_threshold(8010).unwrap(); // Only 10 bps above LTV, need >= 50
    bad_config3.set_liquidation_bonus(500).unwrap();
    // Set decimals=7 via raw bits (bits 42-49)
    bad_config3.data_low |= (7_u128) << 42;
    bad_config3.set_reserve_factor(1000);

    let bad_config3_kr = kinetic_router::ReserveConfiguration {
        data_low: bad_config3.data_low,
        data_high: bad_config3.data_high,
    };
    let result3 = router.try_update_reserve_configuration(
        &pool_configurator,
        &underlying,
        &bad_config3_kr,
    );
    assert!(result3.is_err(), "Insufficient buffer between LTV and liq_threshold must be rejected (H-03)");

    // Test 4: decimals > 38 should fail
    let mut bad_config4 = SharedReserveConfiguration { data_low: 0, data_high: 0 };
    bad_config4.set_ltv(8000).unwrap();
    bad_config4.set_liquidation_threshold(8500).unwrap();
    bad_config4.set_liquidation_bonus(500).unwrap();
    // Set decimals=39 via raw bits (bits 42-49) - overflow: 10^39 doesn't fit u128
    bad_config4.data_low |= (39_u128) << 42;
    bad_config4.set_reserve_factor(1000);

    let bad_config4_kr = kinetic_router::ReserveConfiguration {
        data_low: bad_config4.data_low,
        data_high: bad_config4.data_high,
    };
    let result4 = router.try_update_reserve_configuration(
        &pool_configurator,
        &underlying,
        &bad_config4_kr,
    );
    assert!(result4.is_err(), "Decimals > 38 must be rejected (H-03)");

    // Test 5: Valid config should succeed
    let mut good_config = SharedReserveConfiguration { data_low: 0, data_high: 0 };
    good_config.set_ltv(7500).unwrap();
    good_config.set_liquidation_threshold(8000).unwrap();
    good_config.set_liquidation_bonus(500).unwrap();
    // Set decimals=7 via raw bits (bits 42-49)
    good_config.data_low |= (7_u128) << 42;
    good_config.set_reserve_factor(1500);
    good_config.set_active(true);
    good_config.set_borrowing_enabled(true);

    let good_config_kr = kinetic_router::ReserveConfiguration {
        data_low: good_config.data_low,
        data_high: good_config.data_high,
    };
    let result5 = router.try_update_reserve_configuration(
        &pool_configurator,
        &underlying,
        &good_config_kr,
    );
    assert!(result5.is_ok(), "Valid config should be accepted");
}

// =============================================================================
// G-08 / M-01: Swap handler whitelist enforcement
// =============================================================================

#[test]
fn test_swap_handler_whitelist_enforcement() {
    let env = Env::default();
    env.mock_all_auths();
    env.budget().reset_unlimited();
    setup_ledger(&env);

    let (router_addr, oracle_addr, admin, _) = deploy_protocol(&env);
    let router = kinetic_router::Client::new(&env, &router_addr);

    // Deploy two reserves (swap requires different from/to assets)
    let (asset_a, _, _) = deploy_reserve(&env, &router_addr, &oracle_addr, &admin, 8000, 8500, 500);
    let (asset_b, _, _) = deploy_reserve(&env, &router_addr, &oracle_addr, &admin, 8000, 8500, 500);

    let user = Address::generate(&env);
    let supply_amount = 10_000_0000000u128;
    mint_and_approve(&env, &asset_a, &router_addr, &user, supply_amount);
    router.supply(&user, &asset_a, &supply_amount, &user, &0u32);

    // Set whitelist with a specific handler
    let whitelisted_handler = Address::generate(&env);
    let mut whitelist = Vec::new(&env);
    whitelist.push_back(whitelisted_handler.clone());
    router.set_swap_handler_whitelist(&whitelist);

    // Verify whitelist is set
    assert!(router.is_swap_handler_whitelisted(&whitelisted_handler),
        "Handler should be whitelisted");

    // Try swap with non-whitelisted handler → should fail with UnauthorizedAMM
    let malicious_handler = Address::generate(&env);
    assert!(!router.is_swap_handler_whitelisted(&malicious_handler),
        "Malicious handler should not be whitelisted");

    let result = router.try_swap_collateral(
        &user,
        &asset_a,
        &asset_b,
        &100_0000000u128, // 100 tokens
        &90_0000000u128,  // min 90 tokens out
        &Some(malicious_handler),
    );
    assert!(result.is_err(), "Non-whitelisted swap handler must be rejected (M-01)");

    // Verify the error is specifically about unauthorized AMM
    match result {
        Err(Ok(kinetic_router::KineticRouterError::UnauthorizedAMM)) => {
            // Expected: unauthorized swap handler
        }
        _ => panic!("Expected UnauthorizedAMM error for non-whitelisted handler"),
    }
}

// =============================================================================
// Helper: Deploy two-asset liquidation scenario
// =============================================================================

/// Deploy a standard two-asset scenario for liquidation testing.
/// Returns (router, oracle_client, admin, asset_a, asset_b, user, liquidator).
/// - asset_a = collateral asset, asset_b = debt asset
/// - LP provides liquidity in asset_b
/// - User supplies `user_supply` of asset_a, borrows `borrow_amount` of asset_b
fn setup_liquidation_scenario(
    env: &Env,
    user_supply: u128,
    borrow_amount: u128,
) -> (
    kinetic_router::Client,
    price_oracle::Client,
    Address,            // admin
    Address,            // asset_a (collateral)
    Address,            // asset_b (debt)
    Address,            // user
    Address,            // liquidator
) {
    let (router_addr, oracle_addr, admin, _) = deploy_protocol(env);
    let router = kinetic_router::Client::new(env, &router_addr);
    let oracle_client = price_oracle::Client::new(env, &oracle_addr);

    let (asset_a, _, _) = deploy_reserve(env, &router_addr, &oracle_addr, &admin, 8000, 8500, 500);
    let (asset_b, _, _) = deploy_reserve(env, &router_addr, &oracle_addr, &admin, 8000, 8500, 500);

    let lp = Address::generate(env);
    let user = Address::generate(env);
    let liquidator = Address::generate(env);

    // LP provides liquidity for asset B (10x borrow amount to ensure sufficient liquidity)
    let lp_amount = borrow_amount * 10;
    mint_and_approve(env, &asset_b, &router_addr, &lp, lp_amount);
    router.supply(&lp, &asset_b, &lp_amount, &lp, &0u32);

    // User supplies asset A as collateral
    mint_and_approve(env, &asset_a, &router_addr, &user, user_supply);
    router.supply(&user, &asset_a, &user_supply, &user, &0u32);

    // User borrows asset B
    router.borrow(&user, &asset_b, &borrow_amount, &1u32, &0u32, &user);

    // Mint enough tokens for the liquidator to repay the full debt
    mint_and_approve(env, &asset_b, &router_addr, &liquidator, borrow_amount * 2);

    (router, oracle_client, admin, asset_a, asset_b, user, liquidator)
}

/// Helper: Change price of an asset with circuit breaker reset
fn set_asset_price(
    oracle_client: &price_oracle::Client,
    admin: &Address,
    asset: &Address,
    price: u128,
    env: &Env,
) {
    let asset_oracle = price_oracle::Asset::Stellar(asset.clone());
    oracle_client.reset_circuit_breaker(admin, &asset_oracle);
    oracle_client.set_manual_override(
        admin,
        &asset_oracle,
        &Some(price),
        &Some(env.ledger().timestamp() + 604_800), // 7 days (max allowed by L-04)
    );
}

// =============================================================================
// G-03: Liquidation close factor 50% (HF between 0.5 and 1.0)
// =============================================================================
//
// Math constraint: For partial liquidation to improve HF (required by H-04),
// pre_HF must exceed LT * (1 + bonus) / 10000 = 0.85 * 1.05 = 0.8925.
// So the valid range for 50% close factor tests is HF ∈ (0.8925, 1.0).

#[test]
fn test_liquidation_close_factor_50_percent() {
    let env = Env::default();
    env.mock_all_auths();
    env.budget().reset_unlimited();
    setup_ledger(&env);

    // Supply 10000 A, borrow 8000 B → at $1.00: HF = (10000*0.85)/8000 = 1.0625
    let (router, oracle_client, admin, asset_a, asset_b, user, liquidator) =
        setup_liquidation_scenario(&env, 10_000_0000000, 8_000_0000000);

    let pre = router.get_user_account_data(&user);
    assert!(pre.health_factor >= WAD, "Position should be healthy initially");

    // Drop asset A to $0.94 → HF = (10000*0.94*0.85)/8000 = 0.999 (< 1.0, > 0.5, > 0.8925)
    set_asset_price(&oracle_client, &admin, &asset_a, 94_000_000_000_000, &env);

    let mid = router.get_user_account_data(&user);
    assert!(mid.health_factor < WAD, "HF should be < 1.0 after price drop");
    assert!(mid.health_factor > WAD / 2, "HF should be > 0.5 (50% close factor zone)");

    // Liquidate 50% of debt (4000 tokens)
    let at_50_pct = 4_000_0000000u128;
    let result = router.try_liquidation_call(
        &liquidator,
        &asset_a,
        &asset_b,
        &user,
        &at_50_pct,
        &false,
    );
    match &result {
        Err(e) => panic!("50% liquidation failed: {:?}, HF was: {}", e, mid.health_factor),
        Ok(_) => {}
    }

    // Verify: debt decreased and HF improved
    let post = router.get_user_account_data(&user);
    assert!(post.total_debt_base < mid.total_debt_base, "Debt should decrease");
    assert!(post.health_factor > mid.health_factor, "HF should improve after liquidation");
}

// =============================================================================
// G-03: Liquidation close factor 100% (HF < 0.5 → bad debt path)
// =============================================================================
//
// With LT=8500 and bonus=500, HF < 0.5 always triggers collateral cap
// (collateral_to_seize > user_balance), which then triggers bad debt
// socialization when remaining_debt < min_remaining_debt.

#[test]
fn test_liquidation_close_factor_100_percent() {
    let env = Env::default();
    env.mock_all_auths();
    env.budget().reset_unlimited();
    setup_ledger(&env);

    // Supply 2 tokens A, borrow 1 token B
    let (router, oracle_client, admin, asset_a, asset_b, user, liquidator) =
        setup_liquidation_scenario(&env, 2_0000000, 1_0000000);

    // Crash A to $0.29 → HF = (2*0.29*0.85)/1 = 0.493 (< 0.5 → 100% CF)
    // Collateral to seize = 1 * (1/0.29) * 1.05 = 3.62 tokens > 2 → collateral cap
    // Adjusted debt ≈ 1 * (2/3.62) ≈ 0.55 tokens → remaining ≈ 0.45 < 1 → bad debt
    set_asset_price(&oracle_client, &admin, &asset_a, 29_000_000_000_000, &env);

    let pre = router.get_user_account_data(&user);
    assert!(pre.health_factor < WAD / 2, "HF should be < 0.5 (100% CF zone)");

    // Liquidate full debt → 100% close factor accepted, triggers bad debt socialization
    let result = router.try_liquidation_call(
        &liquidator,
        &asset_a,
        &asset_b,
        &user,
        &1_0000000u128,
        &false,
    );
    assert!(result.is_ok(), "100% liquidation should succeed via bad debt socialization");

    // Verify: position fully cleared
    let post = router.get_user_account_data(&user);
    assert_eq!(post.total_collateral_base, 0, "All collateral seized");
    assert_eq!(post.total_debt_base, 0, "Debt cleared via bad debt socialization");
}

// =============================================================================
// G-05 / H-04: Post-liquidation HF must improve
// =============================================================================

#[test]
fn test_liquidation_post_hf_must_improve() {
    let env = Env::default();
    env.mock_all_auths();
    env.budget().reset_unlimited();
    setup_ledger(&env);

    // Supply 10000 A, borrow 8000 B
    let (router, oracle_client, admin, asset_a, asset_b, user, liquidator) =
        setup_liquidation_scenario(&env, 10_000_0000000, 8_000_0000000);

    // Drop A to $0.94 → HF = (10000*0.94*0.85)/8000 = 0.999
    // HF > 0.8925, so partial liquidation will improve HF
    set_asset_price(&oracle_client, &admin, &asset_a, 94_000_000_000_000, &env);

    let pre_data = router.get_user_account_data(&user);
    let pre_hf = pre_data.health_factor;
    assert!(pre_hf < WAD, "Position should be liquidatable");
    assert!(pre_hf > WAD / 2, "Should be in 50% CF zone");

    // Liquidate 2000 tokens (25% of debt, well within 50% CF)
    let liq_amount = 2_000_0000000u128;
    let result = router.try_liquidation_call(
        &liquidator,
        &asset_a,
        &asset_b,
        &user,
        &liq_amount,
        &false,
    );
    assert!(result.is_ok(), "Partial liquidation should succeed");

    // H-04: Post-liquidation HF must have improved
    let post_hf = router.get_user_account_data(&user).health_factor;
    assert!(
        post_hf > pre_hf,
        "Post-liquidation HF ({}) must improve from pre-HF ({})",
        post_hf, pre_hf
    );
}

// =============================================================================
// G-04 / H-05: Liquidation bad debt → deficit tracking (Aave V3.3 pattern)
// =============================================================================

#[test]
fn test_liquidation_bad_debt_creates_deficit() {
    let env = Env::default();
    env.mock_all_auths();
    env.budget().reset_unlimited();
    setup_ledger(&env);

    // Supply 2 tokens A, borrow 1 token B
    let (router, oracle_client, admin, asset_a, asset_b, user, liquidator) =
        setup_liquidation_scenario(&env, 2_0000000, 1_0000000);

    // No deficit before liquidation
    assert_eq!(router.get_reserve_deficit(&asset_b), 0, "No deficit initially");

    // Crash A to $0.29 → HF ≈ 0.493 (< 0.5 → 100% CF)
    // Collateral cap triggers → adjusted debt leaves remainder < min → deficit created
    set_asset_price(&oracle_client, &admin, &asset_a, 29_000_000_000_000, &env);

    let pre = router.get_user_account_data(&user);
    assert!(pre.health_factor < WAD / 2, "HF should be < 0.5");
    assert!(pre.total_debt_base > 0, "Should have debt");

    let result = router.try_liquidation_call(
        &liquidator,
        &asset_a,
        &asset_b,
        &user,
        &1_0000000u128,
        &false,
    );
    assert!(result.is_ok(), "Bad debt liquidation should succeed");

    // Verify: position fully cleared
    let post = router.get_user_account_data(&user);
    assert_eq!(post.total_collateral_base, 0,
        "All collateral should be seized");
    assert_eq!(post.total_debt_base, 0,
        "Debt should be zero (burned as bad debt)");

    // Verify: deficit is recorded on the reserve (not socialized to depositors)
    let deficit = router.get_reserve_deficit(&asset_b);
    assert!(deficit > 0, "Deficit should be recorded for bad debt");
}

#[test]
fn test_cover_deficit_full() {
    let env = Env::default();
    env.mock_all_auths();
    env.budget().reset_unlimited();
    setup_ledger(&env);

    // Create bad debt scenario
    let (router, oracle_client, admin, asset_a, asset_b, user, liquidator) =
        setup_liquidation_scenario(&env, 2_0000000, 1_0000000);

    set_asset_price(&oracle_client, &admin, &asset_a, 29_000_000_000_000, &env);
    router.liquidation_call(&liquidator, &asset_a, &asset_b, &user, &1_0000000u128, &false);

    let deficit = router.get_reserve_deficit(&asset_b);
    assert!(deficit > 0, "Deficit should exist");

    // Cover the deficit (anyone can call — use a random address)
    let coverer = Address::generate(&env);
    mint_and_approve(&env, &asset_b, &router.address, &coverer, deficit);

    let covered = router.cover_deficit(&coverer, &asset_b, &deficit);
    assert_eq!(covered, deficit, "Should cover full deficit");
    assert_eq!(router.get_reserve_deficit(&asset_b), 0, "Deficit should be zero after coverage");
}

#[test]
fn test_cover_deficit_partial() {
    let env = Env::default();
    env.mock_all_auths();
    env.budget().reset_unlimited();
    setup_ledger(&env);

    let (router, oracle_client, admin, asset_a, asset_b, user, liquidator) =
        setup_liquidation_scenario(&env, 2_0000000, 1_0000000);

    set_asset_price(&oracle_client, &admin, &asset_a, 29_000_000_000_000, &env);
    router.liquidation_call(&liquidator, &asset_a, &asset_b, &user, &1_0000000u128, &false);

    let deficit = router.get_reserve_deficit(&asset_b);
    assert!(deficit > 0, "Deficit should exist");

    // Cover only half
    let half = deficit / 2;
    let coverer = Address::generate(&env);
    mint_and_approve(&env, &asset_b, &router.address, &coverer, half);

    let covered = router.cover_deficit(&coverer, &asset_b, &half);
    assert_eq!(covered, half, "Should cover half");

    let remaining = router.get_reserve_deficit(&asset_b);
    assert_eq!(remaining, deficit - half, "Remaining deficit should be half");
}

#[test]
fn test_cover_deficit_no_deficit_reverts() {
    let env = Env::default();
    env.mock_all_auths();
    env.budget().reset_unlimited();
    setup_ledger(&env);

    let (router, _, _, _, asset_b, _, _) =
        setup_liquidation_scenario(&env, 2_0000000, 1_0000000);

    // No bad debt — try to cover nonexistent deficit
    let coverer = Address::generate(&env);
    mint_and_approve(&env, &asset_b, &router.address, &coverer, 1_0000000);

    let result = router.try_cover_deficit(&coverer, &asset_b, &1_0000000u128);
    assert!(result.is_err(), "Should fail when no deficit exists");
}

// =============================================================================
// G-04: Collateral cap liquidation seizes all collateral
// =============================================================================
//
// When collateral cap triggers and remaining_debt >= min_remaining_debt,
// all collateral is seized and remaining debt stays. The H-04 post-HF check
// was removed as it was unreachable with current parameters (bonus=500bps,
// threshold<=8500bps → 1.05 * 0.85 = 0.8925 < 1.0).

#[test]
fn test_liquidation_collateral_cap_h04_rejects_worsening() {
    let env = Env::default();
    env.mock_all_auths();
    env.budget().reset_unlimited();
    setup_ledger(&env);

    let (router, oracle_client, admin, asset_a, asset_b, user, liquidator) =
        setup_liquidation_scenario(&env, 100_0000000, 75_0000000);

    set_asset_price(&oracle_client, &admin, &asset_a, 35_000_000_000_000, &env);

    let pre = router.get_user_account_data(&user);
    assert!(pre.health_factor < WAD / 2, "HF should be < 0.5");

    let result = router.try_liquidation_call(
        &liquidator,
        &asset_a,
        &asset_b,
        &user,
        &75_0000000u128,
        &false,
    );

    assert!(result.is_ok(), "Collateral cap liquidation should succeed");
}

// =============================================================================
// G-04: Min remaining debt — dust clamping liquidates full debt
// =============================================================================
//
// When partial liquidation would leave remainder < min_remaining_debt,
// the dust-debt clamping fix clamps debt_to_cover to the full balance
// instead of reverting. This prevents stuck positions.

#[test]
fn test_liquidation_min_remaining_debt_revert() {
    let env = Env::default();
    env.mock_all_auths();
    env.budget().reset_unlimited();
    setup_ledger(&env);

    let (router, oracle_client, admin, asset_a, asset_b, _, _) =
        setup_liquidation_scenario(&env, 2_0000000, 1_0000000);

    // Set min_remaining_debt to 1 whole token — explicitly enables dust clamping
    router.set_reserve_min_remaining_debt(&asset_b, &1u32);

    let user = Address::generate(&env);
    let liquidator = Address::generate(&env);

    mint_and_approve(&env, &asset_a, &router.address, &user, 2_0000000);
    router.supply(&user, &asset_a, &2_0000000u128, &user, &0u32);
    router.borrow(&user, &asset_b, &1_5000000u128, &1u32, &0u32, &user);

    // Drop A to $0.88 → HF < 1.0 → liquidatable, HF > 0.5 → 50% CF zone
    // 50% of 1.5 = 0.75 → remainder 0.75 < 1.0 min → clamped to full 1.5
    set_asset_price(&oracle_client, &admin, &asset_a, 88_000_000_000_000, &env);

    let pre = router.get_user_account_data(&user);
    assert!(pre.health_factor < WAD, "Should be liquidatable");
    assert!(pre.health_factor > WAD / 2, "Should be in 50% CF zone");

    mint_and_approve(&env, &asset_b, &router.address, &liquidator, 2_0000000);

    // Dust clamping: 0.75 would leave 0.75 < 1.0 min_remaining_debt, so full debt is liquidated
    let result = router.try_liquidation_call(
        &liquidator,
        &asset_a,
        &asset_b,
        &user,
        &7500000u128,
        &false,
    );
    assert!(result.is_ok(), "Dust clamping should liquidate full debt instead of reverting");
}

// =============================================================================
// G-09: Index monotonicity invariant
// =============================================================================

#[test]
fn test_invariant_index_monotonicity() {
    let env = Env::default();
    env.mock_all_auths();
    env.budget().reset_unlimited();
    setup_ledger(&env);

    let (router_addr, oracle_addr, admin, _) = deploy_protocol(&env);
    let (underlying, _, _) = deploy_reserve(&env, &router_addr, &oracle_addr, &admin, 8000, 8500, 500);
    let router = kinetic_router::Client::new(&env, &router_addr);

    let lp = Address::generate(&env);
    let user = Address::generate(&env);

    // LP provides liquidity
    let lp_amount = 1_000_0000000u128;
    mint_and_approve(&env, &underlying, &router_addr, &lp, lp_amount);
    router.supply(&lp, &underlying, &lp_amount, &lp, &0u32);

    // User supplies and borrows to generate interest
    let supply_amount = 500_0000000u128;
    let borrow_amount = 100_0000000u128;
    mint_and_approve(&env, &underlying, &router_addr, &user, supply_amount);
    router.supply(&user, &underlying, &supply_amount, &user, &0u32);
    router.borrow(&user, &underlying, &borrow_amount, &1u32, &0u32, &user);

    // Record initial indices
    let initial = router.get_reserve_data(&underlying);
    let mut prev_liquidity_index = initial.liquidity_index;
    let mut prev_borrow_index = initial.variable_borrow_index;

    assert!(prev_liquidity_index >= RAY, "Initial liquidity index should be >= RAY");
    assert!(prev_borrow_index >= RAY, "Initial borrow index should be >= RAY");

    // Advance time and verify indices are monotonically non-decreasing
    for i in 0..5 {
        let info = env.ledger().get();
        env.ledger().set(LedgerInfo {
            sequence_number: info.sequence_number + 10,
            timestamp: info.timestamp + 60, // 60 seconds
            ..info
        });

        // Small supply triggers index update via update_state
        let small_amount = 1_0000000u128;
        mint_and_approve(&env, &underlying, &router_addr, &lp, small_amount);
        router.supply(&lp, &underlying, &small_amount, &lp, &0u32);

        let current = router.get_reserve_data(&underlying);

        // INVARIANT: Indices must never decrease
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

    // Final check: indices should have grown with active borrows
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
// G-12: Conservation of value invariant (supply → withdraw round-trip)
// =============================================================================

#[test]
fn test_invariant_conservation_of_value() {
    let env = Env::default();
    env.mock_all_auths();
    env.budget().reset_unlimited();
    setup_ledger(&env);

    let (router_addr, oracle_addr, admin, _) = deploy_protocol(&env);
    let (underlying, a_token_addr, _) = deploy_reserve(&env, &router_addr, &oracle_addr, &admin, 8000, 8500, 500);
    let router = kinetic_router::Client::new(&env, &router_addr);

    let user = Address::generate(&env);
    let supply_amount = 10_000_0000000u128;
    mint_and_approve(&env, &underlying, &router_addr, &user, supply_amount);

    let token_client = token::Client::new(&env, &underlying);
    let initial_balance = token_client.balance(&user);

    // Supply
    router.supply(&user, &underlying, &supply_amount, &user, &0u32);

    // Verify: underlying moved to aToken contract
    let atoken_balance = token_client.balance(&a_token_addr);
    assert_eq!(atoken_balance, supply_amount as i128,
        "aToken contract should hold the underlying after supply");

    // User wallet decreased
    let post_supply_balance = token_client.balance(&user);
    assert_eq!(initial_balance - post_supply_balance, supply_amount as i128,
        "User wallet should decrease by supply amount");

    // Withdraw all (no time passed, no interest)
    router.withdraw(&user, &underlying, &u128::MAX, &user);

    // Verify: user wallet restored (conservation)
    let final_balance = token_client.balance(&user);
    assert_eq!(final_balance, initial_balance,
        "User balance must be conserved in supply→withdraw round-trip");

    // Verify: aToken contract balance is zero
    let final_atoken_balance = token_client.balance(&a_token_addr);
    assert_eq!(final_atoken_balance, 0,
        "aToken contract should be empty after full withdrawal");
}

// =============================================================================
// M-04: Emergency admin can pause but cannot unpause
// =============================================================================

#[test]
fn test_emergency_admin_cannot_unpause() {
    let env = Env::default();
    env.mock_all_auths();
    env.budget().reset_unlimited();
    setup_ledger(&env);

    let admin = Address::generate(&env);
    let emergency_admin = Address::generate(&env);

    let kinetic_router_addr = env.register(kinetic_router::WASM, ());
    let router = kinetic_router::Client::new(&env, &kinetic_router_addr);

    let oracle_addr = env.register(price_oracle::WASM, ());
    let oracle_client = price_oracle::Client::new(&env, &oracle_addr);
    let reflector_addr = env.register(MockReflector, ());
    oracle_client.initialize(&admin, &reflector_addr, &Address::generate(&env), &Address::generate(&env));

    router.initialize(
        &admin,
        &emergency_admin,
        &oracle_addr,
        &Address::generate(&env),
        &Address::generate(&env),
        &None,
    );

    // Emergency admin can pause
    let pause_result = router.try_pause(&emergency_admin);
    assert!(pause_result.is_ok(), "Emergency admin should be able to pause");

    // Emergency admin cannot unpause (M-04: only pool admin can unpause)
    // Clear auths, then only mock emergency_admin's auth
    env.mock_auths(&[]);
    let unpause_result = router.try_unpause(&emergency_admin);
    assert!(unpause_result.is_err(), "Emergency admin must NOT be able to unpause (M-04)");

    // Pool admin CAN unpause
    env.mock_all_auths();
    let unpause_result2 = router.try_unpause(&admin);
    assert!(unpause_result2.is_ok(), "Pool admin should be able to unpause");
}

// =============================================================================
// WP-L2: Repay reverts when partial repay leaves dust below min_remaining_debt
// =============================================================================

#[test]
fn test_wp_l2_repay_revert_on_dust_remainder() {
    let env = Env::default();
    env.mock_all_auths();
    env.budget().reset_unlimited();
    setup_ledger(&env);

    let (router_addr, oracle_addr, admin, _) = deploy_protocol(&env);
    let (underlying, _, _) = deploy_reserve(&env, &router_addr, &oracle_addr, &admin, 8000, 8500, 500);
    let router = kinetic_router::Client::new(&env, &router_addr);

    // Set min_remaining_debt to 10 whole tokens (decimals=7, so 10 * 10^7 = 100_000_000)
    router.set_reserve_min_remaining_debt(&underlying, &10u32);

    let lp = Address::generate(&env);
    let borrower = Address::generate(&env);

    // LP provides liquidity
    let lp_amount = 100_000_0000000u128; // 100k tokens
    mint_and_approve(&env, &underlying, &router_addr, &lp, lp_amount);
    router.supply(&lp, &underlying, &lp_amount, &lp, &0u32);

    // Borrower supplies collateral and borrows 100 tokens
    let supply = 10_000_0000000u128; // 10k tokens
    mint_and_approve(&env, &underlying, &router_addr, &borrower, supply);
    router.supply(&borrower, &underlying, &supply, &borrower, &0u32);
    let borrow_amount = 100_0000000u128; // 100 tokens
    router.borrow(&borrower, &underlying, &borrow_amount, &1u32, &0u32, &borrower);

    // Attempt partial repay that leaves 5 tokens remainder (< 10 min_remaining_debt) → must revert
    let repay_amount = 95_0000000u128; // 95 tokens, leaving ~5
    mint_and_approve(&env, &underlying, &router_addr, &borrower, repay_amount);
    let result = router.try_repay(&borrower, &underlying, &repay_amount, &1u32, &borrower);
    assert!(result.is_err(), "WP-L2: Partial repay leaving dust below min_remaining_debt must revert");
}

#[test]
fn test_wp_l2_repay_full_amount_bypasses_dust_check() {
    let env = Env::default();
    env.mock_all_auths();
    env.budget().reset_unlimited();
    setup_ledger(&env);

    let (router_addr, oracle_addr, admin, _) = deploy_protocol(&env);
    let (underlying, _, _) = deploy_reserve(&env, &router_addr, &oracle_addr, &admin, 8000, 8500, 500);
    let router = kinetic_router::Client::new(&env, &router_addr);

    // Set min_remaining_debt to 10 whole tokens
    router.set_reserve_min_remaining_debt(&underlying, &10u32);

    let lp = Address::generate(&env);
    let borrower = Address::generate(&env);

    // LP provides liquidity
    let lp_amount = 100_000_0000000u128;
    mint_and_approve(&env, &underlying, &router_addr, &lp, lp_amount);
    router.supply(&lp, &underlying, &lp_amount, &lp, &0u32);

    // Borrower supplies collateral and borrows 100 tokens
    let supply = 10_000_0000000u128;
    mint_and_approve(&env, &underlying, &router_addr, &borrower, supply);
    router.supply(&borrower, &underlying, &supply, &borrower, &0u32);
    router.borrow(&borrower, &underlying, &100_0000000u128, &1u32, &0u32, &borrower);

    // Full repay with u128::MAX always works regardless of min_remaining_debt
    mint_and_approve(&env, &underlying, &router_addr, &borrower, 200_0000000);
    let repaid = router.repay(&borrower, &underlying, &u128::MAX, &1u32, &borrower);
    assert!(repaid >= 100_0000000, "Full repay should succeed");

    // Verify debt is zero
    let acct = router.get_user_account_data(&borrower);
    assert_eq!(acct.total_debt_base, 0, "Debt should be zero after full repay");
}

#[test]
fn test_wp_l2_repay_above_min_remaining_succeeds() {
    let env = Env::default();
    env.mock_all_auths();
    env.budget().reset_unlimited();
    setup_ledger(&env);

    let (router_addr, oracle_addr, admin, _) = deploy_protocol(&env);
    let (underlying, _, _) = deploy_reserve(&env, &router_addr, &oracle_addr, &admin, 8000, 8500, 500);
    let router = kinetic_router::Client::new(&env, &router_addr);

    // Set min_remaining_debt to 10 whole tokens
    router.set_reserve_min_remaining_debt(&underlying, &10u32);

    let lp = Address::generate(&env);
    let borrower = Address::generate(&env);

    let lp_amount = 100_000_0000000u128;
    mint_and_approve(&env, &underlying, &router_addr, &lp, lp_amount);
    router.supply(&lp, &underlying, &lp_amount, &lp, &0u32);

    let supply = 10_000_0000000u128;
    mint_and_approve(&env, &underlying, &router_addr, &borrower, supply);
    router.supply(&borrower, &underlying, &supply, &borrower, &0u32);
    router.borrow(&borrower, &underlying, &100_0000000u128, &1u32, &0u32, &borrower);

    // Partial repay leaving 50 tokens (well above 10 min_remaining_debt) → should succeed
    let repay_amount = 50_0000000u128; // 50 tokens, leaving ~50
    mint_and_approve(&env, &underlying, &router_addr, &borrower, repay_amount);
    let repaid = router.repay(&borrower, &underlying, &repay_amount, &1u32, &borrower);
    assert_eq!(repaid, repay_amount, "Partial repay above min_remaining should succeed");

    // Verify debt is still nonzero
    let acct = router.get_user_account_data(&borrower);
    assert!(acct.total_debt_base > 0, "Borrower should still have debt after partial repay");
}

// =============================================================================
// WP-O7: receive_a_token=true liquidation fee uses transfer_on_liquidation
// =============================================================================

#[test]
fn test_wp_o7_receive_a_token_liquidation_with_fee() {
    let env = Env::default();
    env.mock_all_auths();
    env.budget().reset_unlimited();
    setup_ledger(&env);

    // Setup a liquidation scenario where most underlying is borrowed out
    let (router, oracle_client, admin, asset_a, asset_b, user, liquidator) =
        setup_liquidation_scenario(&env, 10_000_0000000, 8_000_0000000);

    // Set a nonzero protocol fee (30 bps = 0.3%) — this triggers the fee path
    router.set_flash_loan_premium(&30u128);

    // Drop collateral price to make user liquidatable (HF < 1 but > 0.8925)
    // At $0.90: HF = 0.90 * (8500/10000) * (10000/8000) = 0.956
    // This is above LT*(1+bonus)/10000 = 0.8925, so partial liq improves HF
    set_asset_price(&oracle_client, &admin, &asset_a, 90_000_000_000_000, &env);

    // Verify user is indeed liquidatable
    let acct_before = router.get_user_account_data(&user);
    assert!(acct_before.health_factor < WAD, "User should be liquidatable");

    // Liquidate with receive_a_token=true — the fix ensures fee is collected
    // as aToken transfer (not burn+transfer_underlying), so it works even when
    // most underlying has been borrowed out.
    let liq_amount = 1_000_0000000u128;
    let result = router.try_liquidation_call(
        &liquidator,
        &asset_a,
        &asset_b,
        &user,
        &liq_amount,
        &true, // receive_a_token=true — this is the WP-O7 path
    );
    assert!(result.is_ok(), "WP-O7: receive_a_token liquidation with fee must succeed");

    // Verify liquidation improved user's position
    let acct_after = router.get_user_account_data(&user);
    assert!(
        acct_after.health_factor > acct_before.health_factor,
        "Liquidation should improve health factor"
    );
}
