#![cfg(test)]

//! # MEDIUM-1 FIX: aToken transfer bitmap sync via finalize_transfer
//!
//! These tests verify the fix for the bitmap desync vulnerability identified
//! in PR #83. The fix adds `finalize_transfer()` to the KineticRouter, called
//! by aToken.transfer_internal() after balance updates, which:
//!
//! 1. **Clears sender's collateral bit** when their balance reaches 0
//! 2. **Sets receiver's collateral bit** when they receive a new position
//!
//! This mirrors Aave V3's `Pool.finalizeTransfer()` pattern.

use crate::{a_token, debt_token, interest_rate_strategy, kinetic_router, price_oracle};
use soroban_sdk::{
    contract, contractimpl,
    testutils::{Address as _, Ledger, LedgerInfo},
    token, Address, Env, IntoVal, String, Symbol, Vec,
};

// =============================================================================
// Bitmap helpers (mirrors k2_shared::UserConfiguration methods)
// =============================================================================

fn is_using_as_collateral(config: &kinetic_router::UserConfiguration, reserve_index: u8) -> bool {
    if reserve_index >= 64 {
        return false;
    }
    let shift = (reserve_index as u32) * 2;
    (config.data >> shift) & 1 == 1
}

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

fn setup_full_protocol(
    env: &Env,
) -> (
    kinetic_router::Client,
    Address,
    Address,
    Address,
    Address,
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
    router.initialize(
        &admin,
        &emergency_admin,
        &oracle_id,
        &pool_treasury,
        &dex_router,
        &None,
    );

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

fn approve_token(env: &Env, asset: &Address, user: &Address, router_id: &Address, amount: i128) {
    let token_client = token::Client::new(env, asset);
    let expiration = env.ledger().sequence() + 1_000_000;
    token_client.approve(user, router_id, &amount, &expiration);
}

// =============================================================================
// MEDIUM-1 FIX VERIFICATION: Bitmap correctly synced after aToken transfer
// =============================================================================

/// After transferring ALL aTokens, sender's collateral bit should be CLEARED.
#[test]
fn test_sender_bitmap_cleared_after_full_transfer() {
    let env = Env::default();
    env.mock_all_auths();
    setup_ledger(&env);

    let (router, router_id, oracle_id, admin, pool_configurator) = setup_full_protocol(&env);

    let (asset, a_token_id, _debt_token_id) = deploy_reserve_with_oracle(
        &env,
        &router,
        &router_id,
        &oracle_id,
        &admin,
        &pool_configurator,
        100_000_000_000_000u128, // $1.00 at 14 decimals
        7500,
        8000,
        500,
    );

    let user_a = Address::generate(&env);
    let user_b = Address::generate(&env);

    let underlying_token = token::StellarAssetClient::new(&env, &asset);
    underlying_token.mint(&user_a, &10_000_0000000i128);
    approve_token(&env, &asset, &user_a, &router_id, 10_000_0000000i128);

    router.supply(&user_a, &asset, &10_000_0000000u128, &user_a, &0);
    router.set_user_use_reserve_as_coll(&user_a, &asset, &true);

    // Pre-condition: sender has collateral bit ON
    let user_a_config_before = router.get_user_configuration(&user_a);
    assert!(
        is_using_as_collateral(&user_a_config_before, 0),
        "PRE-CONDITION: User A should have collateral bit ON after supply"
    );

    let a_token_client = a_token::Client::new(&env, &a_token_id);
    let user_a_atoken_balance = a_token_client.balance_of(&user_a);
    assert!(user_a_atoken_balance > 0);

    // Transfer ALL aTokens
    a_token_client.transfer(&user_a, &user_b, &user_a_atoken_balance);

    assert_eq!(a_token_client.balance_of(&user_a), 0);
    assert!(a_token_client.balance_of(&user_b) > 0);

    // FIX VERIFIED: Sender's collateral bit is now CLEARED
    let user_a_config_after = router.get_user_configuration(&user_a);
    assert!(
        !is_using_as_collateral(&user_a_config_after, 0),
        "FIX: User A's collateral bit should be cleared after transferring all aTokens"
    );
}

/// After receiving aTokens via transfer, receiver's collateral bit should be SET.
#[test]
fn test_receiver_bitmap_set_after_transfer() {
    let env = Env::default();
    env.mock_all_auths();
    setup_ledger(&env);

    let (router, router_id, oracle_id, admin, pool_configurator) = setup_full_protocol(&env);

    let (asset, a_token_id, _debt_token_id) = deploy_reserve_with_oracle(
        &env,
        &router,
        &router_id,
        &oracle_id,
        &admin,
        &pool_configurator,
        100_000_000_000_000u128,
        7500,
        8000,
        500,
    );

    let user_a = Address::generate(&env);
    let user_b = Address::generate(&env);

    let underlying_token = token::StellarAssetClient::new(&env, &asset);
    underlying_token.mint(&user_a, &10_000_0000000i128);
    approve_token(&env, &asset, &user_a, &router_id, 10_000_0000000i128);
    router.supply(&user_a, &asset, &10_000_0000000u128, &user_a, &0);
    router.set_user_use_reserve_as_coll(&user_a, &asset, &true);

    // Pre-condition: receiver has no collateral bits
    let user_b_config_before = router.get_user_configuration(&user_b);
    assert!(!is_using_as_collateral(&user_b_config_before, 0));

    let a_token_client = a_token::Client::new(&env, &a_token_id);
    let transfer_amount = a_token_client.balance_of(&user_a);
    a_token_client.transfer(&user_a, &user_b, &transfer_amount);

    assert!(a_token_client.balance_of(&user_b) > 0);

    // FIX VERIFIED: Receiver's collateral bit is now SET
    let user_b_config_after = router.get_user_configuration(&user_b);
    assert!(
        is_using_as_collateral(&user_b_config_after, 0),
        "FIX: User B's collateral bit should be set after receiving aTokens"
    );
}

/// Receiver's aTokens should now be visible to get_user_account_data as collateral.
#[test]
fn test_receiver_account_data_shows_collateral() {
    let env = Env::default();
    env.mock_all_auths();
    setup_ledger(&env);

    let (router, router_id, oracle_id, admin, pool_configurator) = setup_full_protocol(&env);

    let (asset, a_token_id, _debt_token_id) = deploy_reserve_with_oracle(
        &env,
        &router,
        &router_id,
        &oracle_id,
        &admin,
        &pool_configurator,
        100_000_000_000_000u128,
        7500,
        8000,
        500,
    );

    let user_a = Address::generate(&env);
    let user_b = Address::generate(&env);

    let underlying_token = token::StellarAssetClient::new(&env, &asset);
    underlying_token.mint(&user_a, &10_000_0000000i128);
    approve_token(&env, &asset, &user_a, &router_id, 10_000_0000000i128);
    router.supply(&user_a, &asset, &10_000_0000000u128, &user_a, &0);
    router.set_user_use_reserve_as_coll(&user_a, &asset, &true);

    let user_a_data_before = router.get_user_account_data(&user_a);
    assert!(user_a_data_before.total_collateral_base > 0);

    let a_token_client = a_token::Client::new(&env, &a_token_id);
    let transfer_amount = a_token_client.balance_of(&user_a);
    a_token_client.transfer(&user_a, &user_b, &transfer_amount);

    // FIX VERIFIED: Receiver's account data shows collateral
    let user_b_data = router.get_user_account_data(&user_b);
    assert!(
        user_b_data.total_collateral_base > 0,
        "FIX: User B's account data should show collateral after receiving aTokens"
    );

    // Sender shows 0 collateral (correct — transferred everything)
    let user_a_data_after = router.get_user_account_data(&user_a);
    assert_eq!(user_a_data_after.total_collateral_base, 0);
}

/// Partial transfer: sender keeps collateral bit, receiver gets collateral bit.
#[test]
fn test_partial_transfer_bitmap_sync() {
    let env = Env::default();
    env.mock_all_auths();
    setup_ledger(&env);

    let (router, router_id, oracle_id, admin, pool_configurator) = setup_full_protocol(&env);

    let (asset, a_token_id, _debt_token_id) = deploy_reserve_with_oracle(
        &env,
        &router,
        &router_id,
        &oracle_id,
        &admin,
        &pool_configurator,
        100_000_000_000_000u128,
        7500,
        8000,
        500,
    );

    let user_a = Address::generate(&env);
    let user_b = Address::generate(&env);

    let underlying_token = token::StellarAssetClient::new(&env, &asset);
    underlying_token.mint(&user_a, &10_000_0000000i128);
    approve_token(&env, &asset, &user_a, &router_id, 10_000_0000000i128);
    router.supply(&user_a, &asset, &10_000_0000000u128, &user_a, &0);
    router.set_user_use_reserve_as_coll(&user_a, &asset, &true);

    let a_token_client = a_token::Client::new(&env, &a_token_id);
    let half_balance = a_token_client.balance_of(&user_a) / 2;
    a_token_client.transfer(&user_a, &user_b, &half_balance);

    assert!(a_token_client.balance_of(&user_a) > 0);
    assert!(a_token_client.balance_of(&user_b) > 0);

    // Sender keeps collateral bit (still has balance)
    let user_a_config = router.get_user_configuration(&user_a);
    assert!(
        is_using_as_collateral(&user_a_config, 0),
        "User A should retain collateral bit (partial transfer)"
    );

    // FIX VERIFIED: Receiver now has collateral bit set
    let user_b_config = router.get_user_configuration(&user_b);
    assert!(
        is_using_as_collateral(&user_b_config, 0),
        "FIX: User B should have collateral bit set after partial transfer"
    );

    // Both should show collateral in account data
    let user_b_data = router.get_user_account_data(&user_b);
    assert!(
        user_b_data.total_collateral_base > 0,
        "FIX: User B should show collateral after receiving partial aTokens"
    );
}

// =============================================================================
// WP-C20: Sender HF must block unsafe collateral transfers (K2 #1 / note 20)
// =============================================================================

/// Transferring aTokens away when sender is a borrower near liquidation must revert.
#[test]
fn test_wp_c20_transfer_blocked_when_sender_hf_too_low() {
    let env = Env::default();
    env.mock_all_auths();
    setup_ledger(&env);

    let (router, router_id, oracle_id, admin, pool_configurator) = setup_full_protocol(&env);

    // Deploy two reserves: collateral asset and borrow asset
    let (collateral_asset, collateral_atoken_id, _) = deploy_reserve_with_oracle(
        &env,
        &router,
        &router_id,
        &oracle_id,
        &admin,
        &pool_configurator,
        100_000_000_000_000u128, // $1.00
        7500,  // 75% LTV
        8000,  // 80% liquidation threshold
        500,   // 5% bonus
    );

    let (borrow_asset, _borrow_atoken_id, _borrow_debt_id) = deploy_reserve_with_oracle(
        &env,
        &router,
        &router_id,
        &oracle_id,
        &admin,
        &pool_configurator,
        100_000_000_000_000u128, // $1.00
        7500,
        8000,
        500,
    );

    let borrower = Address::generate(&env);
    let recipient = Address::generate(&env);
    let liquidity_provider = Address::generate(&env);

    // Setup: fund and supply
    let underlying_collateral = token::StellarAssetClient::new(&env, &collateral_asset);
    let underlying_borrow = token::StellarAssetClient::new(&env, &borrow_asset);

    underlying_collateral.mint(&borrower, &10_000_0000000i128);
    underlying_borrow.mint(&liquidity_provider, &100_000_0000000i128);

    approve_token(&env, &collateral_asset, &borrower, &router_id, 10_000_0000000i128);
    approve_token(&env, &borrow_asset, &liquidity_provider, &router_id, 100_000_0000000i128);

    // Supply collateral and enable as collateral
    router.supply(&borrower, &collateral_asset, &10_000_0000000u128, &borrower, &0);
    router.set_user_use_reserve_as_coll(&borrower, &collateral_asset, &true);

    // Provide liquidity for borrowing
    router.supply(&liquidity_provider, &borrow_asset, &100_000_0000000u128, &liquidity_provider, &0);

    // Borrow near the LTV limit (75% of $10,000 = $7,500)
    router.borrow(&borrower, &borrow_asset, &7_000_0000000u128, &1, &0, &borrower);

    // Verify borrower has debt
    let account_data = router.get_user_account_data(&borrower);
    assert!(account_data.total_debt_base > 0, "borrower has debt");
    assert!(account_data.health_factor > 0, "HF above 0");

    // Try to transfer all collateral aTokens away — should fail (HF would drop below 1)
    let a_token_client = a_token::Client::new(&env, &collateral_atoken_id);
    let atoken_balance = a_token_client.balance_of(&borrower);
    assert!(atoken_balance > 0, "borrower has aTokens");

    let result = a_token_client.try_transfer(&borrower, &recipient, &atoken_balance);
    assert!(
        result.is_err(),
        "WP-C20: transfer must be blocked when it would make sender's HF < 1"
    );

    // Verify borrower still has their collateral
    assert_eq!(
        a_token_client.balance_of(&borrower), atoken_balance,
        "borrower retains collateral after failed transfer"
    );
    assert_eq!(
        a_token_client.balance_of(&recipient), 0,
        "recipient received nothing"
    );
}
