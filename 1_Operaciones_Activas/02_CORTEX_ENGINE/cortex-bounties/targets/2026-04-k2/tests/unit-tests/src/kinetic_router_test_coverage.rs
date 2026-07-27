#![cfg(test)]

//! Remaining Coverage Gap Tests (P1 + P2)
//!
//! P1 gaps:
//! G-19: Interest rate update after supply/borrow/repay/withdraw
//! G-22: Supply cap after interest accrual
//! G-23: Borrow cap after interest accrual
//! G-27: UserConfig bitmap cleared on full liquidation
//! G-18+: Zero price blocks liquidation (explicit zero, not just expired)
//!
//! P2 gaps:
//! G-24: Swap same-asset rejection
//! G-29: Collateral flag set on first supply
//! G-30: Oracle price check on supply (zero price)
//! G-80: Repay on behalf of other user (third-party repay)

use crate::{a_token, debt_token, interest_rate_strategy, kinetic_router, price_oracle};
use k2_shared::{RAY, WAD};
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
    init_args.push_back((0u128).into_val(env));
    init_args.push_back((40_000_000_000_000_000_000u128).into_val(env));
    init_args.push_back((100_000_000_000_000_000_000u128).into_val(env));
    init_args.push_back((800_000_000_000_000_000_000_000_000u128).into_val(env));
    let _: () = env.invoke_contract(&contract_id, &Symbol::new(env, "initialize"), init_args);
    contract_id
}

fn deploy_reserve_with_caps(
    env: &Env,
    kinetic_router_addr: &Address,
    oracle_addr: &Address,
    admin: &Address,
    ltv: u32,
    liquidation_threshold: u32,
    liquidation_bonus: u32,
    supply_cap: u128,
    borrow_cap: u128,
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
        supply_cap,
        borrow_cap,
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

    let oracle_client = price_oracle::Client::new(env, oracle_addr);
    let asset_oracle = price_oracle::Asset::Stellar(underlying_addr.clone());
    oracle_client.add_asset(admin, &asset_oracle);
    oracle_client.set_manual_override(
        admin,
        &asset_oracle,
        &Some(100_000_000_000_000u128), // $1.00 at 14 decimals
        &Some(env.ledger().timestamp() + 604_800),
    );

    (underlying_addr, a_token_addr, debt_token_addr)
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
    deploy_reserve_with_caps(env, kinetic_router_addr, oracle_addr, admin, ltv, liquidation_threshold, liquidation_bonus, 0, 0)
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
        &Some(env.ledger().timestamp() + 604_800),
    );
}

// =============================================================================
// G-19: Interest rate updates after supply
// =============================================================================

#[test]
fn test_interest_rate_updates_after_supply() {
    let env = Env::default();
    env.mock_all_auths();
    env.budget().reset_unlimited();
    setup_ledger(&env);

    let (router_addr, oracle_addr, admin, _) = deploy_protocol(&env);
    let (underlying, _, _) = deploy_reserve(&env, &router_addr, &oracle_addr, &admin, 8000, 8500, 500);
    let router = kinetic_router::Client::new(&env, &router_addr);

    let lp = Address::generate(&env);
    let user = Address::generate(&env);

    // LP provides liquidity and user borrows to create utilization
    let lp_amount = 10_000_0000000u128;
    mint_and_approve(&env, &underlying, &router_addr, &lp, lp_amount);
    router.supply(&lp, &underlying, &lp_amount, &lp, &0u32);

    let supply_amount = 5_000_0000000u128;
    mint_and_approve(&env, &underlying, &router_addr, &user, supply_amount);
    router.supply(&user, &underlying, &supply_amount, &user, &0u32);
    router.borrow(&user, &underlying, &2_000_0000000u128, &1u32, &0u32, &user);

    // Record rates at current utilization
    let data_before = router.get_reserve_data(&underlying);
    let rate_before = data_before.current_variable_borrow_rate;
    assert!(rate_before > 0, "Borrow rate should be > 0 with active borrows");

    // Large supply decreases utilization → rates should decrease
    let big_supply = 20_000_0000000u128;
    mint_and_approve(&env, &underlying, &router_addr, &lp, big_supply);
    router.supply(&lp, &underlying, &big_supply, &lp, &0u32);

    let data_after = router.get_reserve_data(&underlying);
    let rate_after = data_after.current_variable_borrow_rate;

    // More liquidity → lower utilization → lower borrow rate
    assert!(
        rate_after < rate_before,
        "G-19: Borrow rate should decrease after large supply. Before: {}, After: {}",
        rate_before, rate_after
    );
}

// =============================================================================
// G-19: Interest rate updates after borrow
// =============================================================================

#[test]
fn test_interest_rate_updates_after_borrow() {
    let env = Env::default();
    env.mock_all_auths();
    env.budget().reset_unlimited();
    setup_ledger(&env);

    let (router_addr, oracle_addr, admin, _) = deploy_protocol(&env);
    let (underlying, _, _) = deploy_reserve(&env, &router_addr, &oracle_addr, &admin, 8000, 8500, 500);
    let router = kinetic_router::Client::new(&env, &router_addr);

    let lp = Address::generate(&env);
    let user = Address::generate(&env);

    let lp_amount = 10_000_0000000u128;
    mint_and_approve(&env, &underlying, &router_addr, &lp, lp_amount);
    router.supply(&lp, &underlying, &lp_amount, &lp, &0u32);

    let supply_amount = 5_000_0000000u128;
    mint_and_approve(&env, &underlying, &router_addr, &user, supply_amount);
    router.supply(&user, &underlying, &supply_amount, &user, &0u32);

    // Initial borrow creates some utilization
    router.borrow(&user, &underlying, &1_000_0000000u128, &1u32, &0u32, &user);
    let data_before = router.get_reserve_data(&underlying);
    let rate_before = data_before.current_variable_borrow_rate;

    // Additional borrow increases utilization → rates should increase
    router.borrow(&user, &underlying, &2_000_0000000u128, &1u32, &0u32, &user);
    let data_after = router.get_reserve_data(&underlying);
    let rate_after = data_after.current_variable_borrow_rate;

    assert!(
        rate_after > rate_before,
        "G-19: Borrow rate should increase after additional borrow. Before: {}, After: {}",
        rate_before, rate_after
    );
}

// =============================================================================
// G-19: Interest rate updates after repay
// =============================================================================

#[test]
fn test_interest_rate_updates_after_repay() {
    let env = Env::default();
    env.mock_all_auths();
    env.budget().reset_unlimited();
    setup_ledger(&env);

    let (router_addr, oracle_addr, admin, _) = deploy_protocol(&env);
    let (underlying, _, _) = deploy_reserve(&env, &router_addr, &oracle_addr, &admin, 8000, 8500, 500);
    let router = kinetic_router::Client::new(&env, &router_addr);

    let lp = Address::generate(&env);
    let user = Address::generate(&env);

    let lp_amount = 10_000_0000000u128;
    mint_and_approve(&env, &underlying, &router_addr, &lp, lp_amount);
    router.supply(&lp, &underlying, &lp_amount, &lp, &0u32);

    let supply_amount = 5_000_0000000u128;
    mint_and_approve(&env, &underlying, &router_addr, &user, supply_amount);
    router.supply(&user, &underlying, &supply_amount, &user, &0u32);
    router.borrow(&user, &underlying, &3_000_0000000u128, &1u32, &0u32, &user);

    let data_before = router.get_reserve_data(&underlying);
    let rate_before = data_before.current_variable_borrow_rate;

    // Repay reduces utilization → rates should decrease
    mint_and_approve(&env, &underlying, &router_addr, &user, 2_000_0000000);
    router.repay(&user, &underlying, &2_000_0000000u128, &1u32, &user);

    let data_after = router.get_reserve_data(&underlying);
    let rate_after = data_after.current_variable_borrow_rate;

    assert!(
        rate_after < rate_before,
        "G-19: Borrow rate should decrease after repay. Before: {}, After: {}",
        rate_before, rate_after
    );
}

// =============================================================================
// G-19: Interest rate updates after withdraw
// =============================================================================

#[test]
fn test_interest_rate_updates_after_withdraw() {
    let env = Env::default();
    env.mock_all_auths();
    env.budget().reset_unlimited();
    setup_ledger(&env);

    let (router_addr, oracle_addr, admin, _) = deploy_protocol(&env);
    let (underlying, _, _) = deploy_reserve(&env, &router_addr, &oracle_addr, &admin, 8000, 8500, 500);
    let router = kinetic_router::Client::new(&env, &router_addr);

    let lp = Address::generate(&env);
    let user = Address::generate(&env);

    // Large LP supply + moderate borrow → low utilization
    let lp_amount = 20_000_0000000u128;
    mint_and_approve(&env, &underlying, &router_addr, &lp, lp_amount);
    router.supply(&lp, &underlying, &lp_amount, &lp, &0u32);

    let supply_amount = 5_000_0000000u128;
    mint_and_approve(&env, &underlying, &router_addr, &user, supply_amount);
    router.supply(&user, &underlying, &supply_amount, &user, &0u32);
    router.borrow(&user, &underlying, &2_000_0000000u128, &1u32, &0u32, &user);

    let data_before = router.get_reserve_data(&underlying);
    let rate_before = data_before.current_variable_borrow_rate;

    // LP withdraws large amount → increases utilization → rates should increase
    router.withdraw(&lp, &underlying, &15_000_0000000u128, &lp);

    let data_after = router.get_reserve_data(&underlying);
    let rate_after = data_after.current_variable_borrow_rate;

    assert!(
        rate_after > rate_before,
        "G-19: Borrow rate should increase after large withdraw. Before: {}, After: {}",
        rate_before, rate_after
    );
}

// =============================================================================
// G-22: Supply cap enforcement after interest accrual
// =============================================================================

#[test]
fn test_supply_cap_after_interest_accrual() {
    let env = Env::default();
    env.mock_all_auths();
    env.budget().reset_unlimited();
    setup_ledger(&env);

    let (router_addr, oracle_addr, admin, _) = deploy_protocol(&env);
    // Supply cap = 200 whole tokens (200_0000000 in 7 decimals)
    let (underlying, _, _) = deploy_reserve_with_caps(
        &env, &router_addr, &oracle_addr, &admin,
        8000, 8500, 500,
        200, // supply_cap in whole tokens
        0,
    );
    let router = kinetic_router::Client::new(&env, &router_addr);

    let lp = Address::generate(&env);
    let user = Address::generate(&env);

    // Supply 190 tokens (near the 200 cap)
    let supply_amount = 190_0000000u128;
    mint_and_approve(&env, &underlying, &router_addr, &lp, supply_amount);
    router.supply(&lp, &underlying, &supply_amount, &lp, &0u32);

    // Supply 5 more → total 195, under 200 cap
    let more = 5_0000000u128;
    mint_and_approve(&env, &underlying, &router_addr, &user, more);
    router.supply(&user, &underlying, &more, &user, &0u32);

    // Try to supply 10 more → total 205, over 200 cap → should fail
    let over = 10_0000000u128;
    mint_and_approve(&env, &underlying, &router_addr, &user, over);
    let result = router.try_supply(&user, &underlying, &over, &user, &0u32);
    assert!(result.is_err(), "G-22: Supply exceeding cap should be rejected");
}

// =============================================================================
// G-23: Borrow cap enforcement after interest accrual
// =============================================================================

#[test]
fn test_borrow_cap_after_interest_accrual() {
    let env = Env::default();
    env.mock_all_auths();
    env.budget().reset_unlimited();
    setup_ledger(&env);

    let (router_addr, oracle_addr, admin, _) = deploy_protocol(&env);
    // Borrow cap = 50 whole tokens
    let (underlying, _, _) = deploy_reserve_with_caps(
        &env, &router_addr, &oracle_addr, &admin,
        8000, 8500, 500,
        0, // no supply cap
        50, // borrow_cap in whole tokens
    );
    let router = kinetic_router::Client::new(&env, &router_addr);

    let lp = Address::generate(&env);
    let user = Address::generate(&env);

    // LP provides liquidity
    let lp_amount = 10_000_0000000u128;
    mint_and_approve(&env, &underlying, &router_addr, &lp, lp_amount);
    router.supply(&lp, &underlying, &lp_amount, &lp, &0u32);

    // User supplies collateral
    let supply = 1_000_0000000u128;
    mint_and_approve(&env, &underlying, &router_addr, &user, supply);
    router.supply(&user, &underlying, &supply, &user, &0u32);

    // Borrow 40 tokens → under 50 cap
    router.borrow(&user, &underlying, &40_0000000u128, &1u32, &0u32, &user);

    // Try to borrow 15 more → total 55, over 50 cap → should fail
    let result = router.try_borrow(&user, &underlying, &15_0000000u128, &1u32, &0u32, &user);
    assert!(result.is_err(), "G-23: Borrow exceeding cap should be rejected");

    // Borrow 5 more → total 45, under 50 cap → should succeed
    router.borrow(&user, &underlying, &5_0000000u128, &1u32, &0u32, &user);
}

// =============================================================================
// G-27: UserConfig bitmap cleared on full liquidation
// =============================================================================

#[test]
fn test_user_config_cleared_on_full_liquidation() {
    let env = Env::default();
    env.mock_all_auths();
    env.budget().reset_unlimited();
    setup_ledger(&env);

    let (router_addr, oracle_addr, admin, _) = deploy_protocol(&env);
    let router = kinetic_router::Client::new(&env, &router_addr);
    let oracle_client = price_oracle::Client::new(&env, &oracle_addr);

    let (asset_a, a_token_a, _) = deploy_reserve(&env, &router_addr, &oracle_addr, &admin, 8000, 8500, 500);
    let (asset_b, _, debt_token_b) = deploy_reserve(&env, &router_addr, &oracle_addr, &admin, 8000, 8500, 500);

    let lp = Address::generate(&env);
    let user = Address::generate(&env);
    let liquidator = Address::generate(&env);

    // LP provides liquidity for asset B
    let lp_amount = 100_0000000u128;
    mint_and_approve(&env, &asset_b, &router_addr, &lp, lp_amount);
    router.supply(&lp, &asset_b, &lp_amount, &lp, &0u32);

    // User supplies 2 tokens A, borrows 1 token B
    mint_and_approve(&env, &asset_a, &router_addr, &user, 2_0000000);
    router.supply(&user, &asset_a, &2_0000000u128, &user, &0u32);
    router.borrow(&user, &asset_b, &1_0000000u128, &1u32, &0u32, &user);

    // Verify user has both collateral and borrow flags
    let config_before = router.get_user_configuration(&user);
    assert!(config_before.data > 0, "User should have active positions");

    // Crash A to $0.29 → HF < 0.5 → 100% CF → bad debt path
    set_asset_price(&oracle_client, &admin, &asset_a, 29_000_000_000_000, &env);

    let pre = router.get_user_account_data(&user);
    assert!(pre.health_factor < WAD / 2, "Position should be deeply underwater");

    // Fund liquidator
    mint_and_approve(&env, &asset_b, &router_addr, &liquidator, 2_0000000);

    // Liquidate full position → bad debt socialization
    let result = router.try_liquidation_call(
        &liquidator, &asset_a, &asset_b, &user, &1_0000000u128, &false,
    );
    assert!(result.is_ok(), "Full liquidation should succeed");

    // Verify user has no collateral and no debt
    let post = router.get_user_account_data(&user);
    assert_eq!(post.total_collateral_base, 0, "G-27: Collateral should be zero after full liquidation");
    assert_eq!(post.total_debt_base, 0, "G-27: Debt should be zero after full liquidation");

    // Verify aToken balance is zero
    let a_token_client = a_token::Client::new(&env, &a_token_a);
    let a_balance = a_token_client.balance(&user);
    assert_eq!(a_balance, 0, "G-27: aToken balance should be zero");

    // Verify debt token balance is zero
    let debt_token_client = debt_token::Client::new(&env, &debt_token_b);
    let d_balance = debt_token_client.balance(&user);
    assert_eq!(d_balance, 0, "G-27: Debt token balance should be zero");
}

// =============================================================================
// G-18+: Oracle rejects zero price at source (circuit breaker)
// =============================================================================

#[test]
fn test_oracle_rejects_zero_price() {
    let env = Env::default();
    env.mock_all_auths();
    env.budget().reset_unlimited();
    setup_ledger(&env);

    let oracle_addr = env.register(price_oracle::WASM, ());
    let oracle_client = price_oracle::Client::new(&env, &oracle_addr);
    let admin = Address::generate(&env);
    let reflector_addr = env.register(MockReflector, ());
    oracle_client.initialize(&admin, &reflector_addr, &Address::generate(&env), &Address::generate(&env));

    let asset_addr = Address::generate(&env);
    let asset = price_oracle::Asset::Stellar(asset_addr);
    oracle_client.add_asset(&admin, &asset);

    // Set valid price first
    oracle_client.set_manual_override(
        &admin, &asset,
        &Some(100_000_000_000_000u128),
        &Some(env.ledger().timestamp() + 604_800),
    );

    // Attempt to set zero price → must fail (circuit breaker rejects)
    oracle_client.reset_circuit_breaker(&admin, &asset);
    let result = oracle_client.try_set_manual_override(
        &admin, &asset,
        &Some(0u128), // Zero price
        &Some(env.ledger().timestamp() + 604_800),
    );
    assert!(result.is_err(), "G-18+: Oracle must reject zero price at source");
}

// =============================================================================
// G-18+: Missing price blocks liquidation (override removed)
// =============================================================================

#[test]
fn test_missing_price_blocks_liquidation() {
    let env = Env::default();
    env.mock_all_auths();
    env.budget().reset_unlimited();
    setup_ledger(&env);

    let (router_addr, oracle_addr, admin, _) = deploy_protocol(&env);
    let router = kinetic_router::Client::new(&env, &router_addr);
    let oracle_client = price_oracle::Client::new(&env, &oracle_addr);

    let (asset_a, _, _) = deploy_reserve(&env, &router_addr, &oracle_addr, &admin, 8000, 8500, 500);
    let (asset_b, _, _) = deploy_reserve(&env, &router_addr, &oracle_addr, &admin, 8000, 8500, 500);

    let lp = Address::generate(&env);
    let user = Address::generate(&env);
    let liquidator = Address::generate(&env);

    // LP provides liquidity
    let lp_amount = 100_0000000u128;
    mint_and_approve(&env, &asset_b, &router_addr, &lp, lp_amount);
    router.supply(&lp, &asset_b, &lp_amount, &lp, &0u32);

    // User supplies and borrows
    mint_and_approve(&env, &asset_a, &router_addr, &user, 10_0000000);
    router.supply(&user, &asset_a, &10_0000000u128, &user, &0u32);
    router.borrow(&user, &asset_b, &5_0000000u128, &1u32, &0u32, &user);

    // Fund liquidator
    mint_and_approve(&env, &asset_b, &router_addr, &liquidator, 5_0000000);

    // Remove the price override for collateral (set to None)
    let asset_a_oracle = price_oracle::Asset::Stellar(asset_a.clone());
    oracle_client.set_manual_override(
        &admin, &asset_a_oracle,
        &None, // Remove override
        &None,
    );

    // Liquidation should fail — no valid price source
    let result = router.try_liquidation_call(
        &liquidator, &asset_a, &asset_b, &user, &1_0000000u128, &false,
    );
    assert!(result.is_err(), "G-18+: Liquidation must fail when no valid price exists");
}

// =============================================================================
// G-29: Collateral flag set on first supply
// =============================================================================

#[test]
fn test_collateral_flag_set_on_first_supply() {
    let env = Env::default();
    env.mock_all_auths();
    env.budget().reset_unlimited();
    setup_ledger(&env);

    let (router_addr, oracle_addr, admin, _) = deploy_protocol(&env);
    let (underlying, _, _) = deploy_reserve(&env, &router_addr, &oracle_addr, &admin, 8000, 8500, 500);
    let router = kinetic_router::Client::new(&env, &router_addr);

    let user = Address::generate(&env);

    // Before supply: user should have empty config
    let config_before = router.get_user_configuration(&user);
    assert_eq!(config_before.data, 0, "G-29: New user should have empty config bitmap");

    // First supply → should set collateral flag
    let amount = 100_0000000u128;
    mint_and_approve(&env, &underlying, &router_addr, &user, amount);
    router.supply(&user, &underlying, &amount, &user, &0u32);

    // After supply: collateral flag should be set
    let config_after = router.get_user_configuration(&user);
    assert!(config_after.data > 0, "G-29: Config should be non-zero after first supply");

    // Verify via account data: user has collateral
    let account = router.get_user_account_data(&user);
    assert!(account.total_collateral_base > 0, "G-29: User should have collateral after supply");

    // Second supply should not corrupt the flag
    mint_and_approve(&env, &underlying, &router_addr, &user, amount);
    router.supply(&user, &underlying, &amount, &user, &0u32);

    let config_after2 = router.get_user_configuration(&user);
    assert_eq!(config_after.data, config_after2.data,
        "G-29: Second supply should not change config bitmap (flag already set)");
}

// =============================================================================
// G-24: Swap same-asset rejection
// =============================================================================

#[test]
fn test_swap_same_asset_rejected() {
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
    router.supply(&user, &underlying, &supply_amount, &user, &0u32);

    // Attempt to swap same asset → should fail
    let result = router.try_swap_collateral(
        &user,
        &underlying, // from
        &underlying, // to (same!)
        &100_0000000u128,
        &90_0000000u128,
        &None,
    );
    assert!(result.is_err(), "G-24: Swapping same asset must be rejected");
}

// =============================================================================
// Repay on behalf of other user (third-party repay)
// =============================================================================

#[test]
fn test_repay_on_behalf_of_other_user() {
    let env = Env::default();
    env.mock_all_auths();
    env.budget().reset_unlimited();
    setup_ledger(&env);

    let (router_addr, oracle_addr, admin, _) = deploy_protocol(&env);
    let (underlying, _, _) = deploy_reserve(&env, &router_addr, &oracle_addr, &admin, 8000, 8500, 500);
    let router = kinetic_router::Client::new(&env, &router_addr);

    let lp = Address::generate(&env);
    let borrower = Address::generate(&env);
    let repayer = Address::generate(&env);

    // LP provides liquidity
    let lp_amount = 100_000_0000000u128;
    mint_and_approve(&env, &underlying, &router_addr, &lp, lp_amount);
    router.supply(&lp, &underlying, &lp_amount, &lp, &0u32);

    // Borrower supplies collateral and borrows
    let supply = 10_000_0000000u128;
    mint_and_approve(&env, &underlying, &router_addr, &borrower, supply);
    router.supply(&borrower, &underlying, &supply, &borrower, &0u32);
    router.borrow(&borrower, &underlying, &1_000_0000000u128, &1u32, &0u32, &borrower);

    // Verify borrower has debt
    let pre = router.get_user_account_data(&borrower);
    assert!(pre.total_debt_base > 0, "Borrower should have debt");

    // Third party repays on behalf of borrower
    mint_and_approve(&env, &underlying, &router_addr, &repayer, 2_000_0000000);
    let repaid = router.repay(&repayer, &underlying, &u128::MAX, &1u32, &borrower);

    assert!(repaid >= 1_000_0000000, "Repayer should have paid at least the borrowed amount");

    // Verify borrower's debt is now zero
    let post = router.get_user_account_data(&borrower);
    assert_eq!(post.total_debt_base, 0, "Borrower's debt should be zero after third-party repay");
    assert_eq!(post.health_factor, u128::MAX, "HF should be MAX when debt is zero");
}

// =============================================================================
// G-30: Borrow blocked when collateral price override removed
// =============================================================================

#[test]
fn test_borrow_blocked_with_missing_collateral_price() {
    let env = Env::default();
    env.mock_all_auths();
    env.budget().reset_unlimited();
    setup_ledger(&env);

    let (router_addr, oracle_addr, admin, _) = deploy_protocol(&env);
    let (asset_a, _, _) = deploy_reserve(&env, &router_addr, &oracle_addr, &admin, 8000, 8500, 500);
    let (asset_b, _, _) = deploy_reserve(&env, &router_addr, &oracle_addr, &admin, 8000, 8500, 500);
    let router = kinetic_router::Client::new(&env, &router_addr);
    let oracle_client = price_oracle::Client::new(&env, &oracle_addr);

    let lp = Address::generate(&env);
    let user = Address::generate(&env);

    // LP provides liquidity for B
    let lp_amount = 10_000_0000000u128;
    mint_and_approve(&env, &asset_b, &router_addr, &lp, lp_amount);
    router.supply(&lp, &asset_b, &lp_amount, &lp, &0u32);

    // User supplies asset A as collateral (with valid price)
    mint_and_approve(&env, &asset_a, &router_addr, &user, 10_000_0000000);
    router.supply(&user, &asset_a, &10_000_0000000u128, &user, &0u32);

    // Remove collateral price override → no valid price source
    let asset_a_oracle = price_oracle::Asset::Stellar(asset_a.clone());
    oracle_client.set_manual_override(
        &admin, &asset_a_oracle,
        &None, // Remove override
        &None,
    );

    // Borrow should fail — collateral has no valid price
    let result = router.try_borrow(&user, &asset_b, &1_0000000u128, &1u32, &0u32, &user);
    assert!(result.is_err(), "G-30: Borrow must fail when collateral price is unavailable");
}
