#![cfg(test)]

//! # Phase 4: Integration Regression Tests
//!
//! End-to-end tests validating critical multi-step flows across contracts.
//! These tests verify that the full protocol behaves correctly under realistic
//! scenarios involving multiple operations, time passage, and price changes.

use crate::price_oracle;
use crate::setup::{
    advance_ledger, deploy_test_protocol, deploy_test_protocol_two_assets, set_default_ledger,
};
use k2_shared::WAD;
use soroban_sdk::{token, Env};

/// Helper: refresh oracle override and token approvals after time advance.
/// The oracle override set by deploy_test_protocol expires after 604,800s,
/// and token approvals expire at sequence 200,000.
fn refresh_oracle_and_approvals(
    env: &Env,
    protocol: &crate::setup::TestProtocol,
) {
    // Refresh oracle price override
    let asset_enum = price_oracle::Asset::Stellar(protocol.underlying_asset.clone());
    let far_expiry = env.ledger().timestamp() + 604_800; // +7 days (max allowed)
    protocol.price_oracle.set_manual_override(
        &protocol.admin,
        &asset_enum,
        &Some(1_000_000_000_000_000u128), // $1.00 at 14 decimals
        &Some(far_expiry),
    );

    // Refresh token approvals
    let far_seq = env.ledger().sequence() + 1_000_000;
    protocol.underlying_asset_client.approve(
        &protocol.liquidity_provider,
        &protocol.kinetic_router_address,
        &i128::MAX,
        &far_seq,
    );
    protocol.underlying_asset_client.approve(
        &protocol.user,
        &protocol.kinetic_router_address,
        &i128::MAX,
        &far_seq,
    );
}

// =============================================================================
// Test 1: Full Lifecycle — Supply → Borrow → Accrue Interest → Repay → Withdraw
// =============================================================================

#[test]
fn test_full_lifecycle_supply_borrow_repay_withdraw() {
    let env = Env::default();
    env.mock_all_auths();
    set_default_ledger(&env);

    let protocol = deploy_test_protocol(&env);

    let liquidity_amount = 50_000_000_000u128; // 5,000 tokens (7 decimals)
    let collateral_amount = 20_000_000_000u128; // 2,000 tokens
    let borrow_amount = 5_000_000_000u128; // 500 tokens

    // Step 1: Liquidity provider seeds the pool
    protocol.kinetic_router.supply(
        &protocol.liquidity_provider,
        &protocol.underlying_asset,
        &liquidity_amount,
        &protocol.liquidity_provider,
        &0u32,
    );

    // Step 2: User supplies collateral
    protocol.kinetic_router.supply(
        &protocol.user,
        &protocol.underlying_asset,
        &collateral_amount,
        &protocol.user,
        &0u32,
    );

    protocol.kinetic_router.set_user_use_reserve_as_coll(
        &protocol.user,
        &protocol.underlying_asset,
        &true,
    );

    // Step 3: User borrows
    let balance_before_borrow = protocol.underlying_asset_client.balance(&protocol.user);
    protocol.kinetic_router.borrow(
        &protocol.user,
        &protocol.underlying_asset,
        &borrow_amount,
        &1u32,
        &0u32,
        &protocol.user,
    );

    let balance_after_borrow = protocol.underlying_asset_client.balance(&protocol.user);
    assert_eq!(
        balance_after_borrow,
        balance_before_borrow + borrow_amount as i128,
        "User should receive exact borrow amount"
    );

    // Capture indices and HF before time passes
    let reserve_before = protocol
        .kinetic_router
        .get_reserve_data(&protocol.underlying_asset);
    let liquidity_index_before = reserve_before.liquidity_index;
    let borrow_index_before = reserve_before.variable_borrow_index;
    let hf_before = protocol
        .kinetic_router
        .get_user_account_data(&protocol.user)
        .health_factor;

    // Step 4: Advance time — 5 days (within oracle expiry window)
    advance_ledger(&env, 5 * 86_400);
    refresh_oracle_and_approvals(&env, &protocol);

    // Trigger state update to accrue interest
    protocol
        .kinetic_router
        .update_reserve_state(&protocol.underlying_asset);

    let reserve_after = protocol
        .kinetic_router
        .get_reserve_data(&protocol.underlying_asset);
    assert!(
        reserve_after.liquidity_index > liquidity_index_before,
        "Liquidity index must increase after 5 days with borrows"
    );
    assert!(
        reserve_after.variable_borrow_index > borrow_index_before,
        "Borrow index must increase after 5 days"
    );

    // HF should decrease slightly (debt grew from interest)
    let hf_after_interest = protocol
        .kinetic_router
        .get_user_account_data(&protocol.user)
        .health_factor;
    assert!(
        hf_after_interest < hf_before,
        "HF should decrease as debt accrues interest. Before: {}, After: {}",
        hf_before,
        hf_after_interest
    );
    assert!(
        hf_after_interest >= WAD,
        "Position should still be healthy after 5 days"
    );

    // Step 5: User repays full debt (u128::MAX = repay all)
    let debt_before_repay = protocol.debt_token.balance(&protocol.user);
    assert!(debt_before_repay > borrow_amount as i128, "Debt should have grown from interest");

    protocol.kinetic_router.repay(
        &protocol.user,
        &protocol.underlying_asset,
        &u128::MAX,
        &1u32,
        &protocol.user,
    );

    let debt_after_repay = protocol.debt_token.balance(&protocol.user);
    assert_eq!(debt_after_repay, 0, "All debt should be repaid");

    // Step 6: User withdraws all collateral (u128::MAX = withdraw all)
    let a_token_balance = protocol.a_token.balance(&protocol.user);
    assert!(a_token_balance > 0, "User should have aTokens");

    protocol.kinetic_router.withdraw(
        &protocol.user,
        &protocol.underlying_asset,
        &u128::MAX,
        &protocol.user,
    );

    let a_token_after = protocol.a_token.balance(&protocol.user);
    assert_eq!(a_token_after, 0, "All aTokens should be burned after full withdraw");

    // Verify user is fully cleared
    let account_final = protocol
        .kinetic_router
        .get_user_account_data(&protocol.user);
    assert_eq!(account_final.total_debt_base, 0, "No debt remaining");
    assert_eq!(
        account_final.total_collateral_base, 0,
        "No collateral remaining"
    );
}

// =============================================================================
// Test 2: Multi-User Liquidation Cascade
// =============================================================================

#[test]
fn test_multi_user_liquidation_cascade() {
    let env = Env::default();
    env.mock_all_auths();
    set_default_ledger(&env);

    let protocol = deploy_test_protocol_two_assets(&env);

    // User 1: Borrows near max LTV
    let user1_collateral = 10_000_000_000u128; // 1,000 USDC
    let user1_borrow = 7_500_000_000u128; // 750 USDT (75% of 80% LTV)

    protocol.kinetic_router.supply(
        &protocol.user,
        &protocol.usdc_asset,
        &user1_collateral,
        &protocol.user,
        &0u32,
    );
    protocol.kinetic_router.set_user_use_reserve_as_coll(
        &protocol.user,
        &protocol.usdc_asset,
        &true,
    );

    // Liquidity provider seeds USDT liquidity
    protocol.kinetic_router.supply(
        &protocol.liquidity_provider,
        &protocol.usdt_asset,
        &50_000_000_000u128,
        &protocol.liquidity_provider,
        &0u32,
    );

    protocol.kinetic_router.borrow(
        &protocol.user,
        &protocol.usdt_asset,
        &user1_borrow,
        &1u32,
        &0u32,
        &protocol.user,
    );

    // Verify healthy before crash
    let hf_before = protocol
        .kinetic_router
        .get_user_account_data(&protocol.user)
        .health_factor;
    assert!(
        hf_before >= WAD,
        "User should be healthy before price crash"
    );

    // Price crash: USDC drops 20%
    let usdc_asset_enum = price_oracle::Asset::Stellar(protocol.usdc_asset.clone());
    protocol
        .price_oracle
        .reset_circuit_breaker(&protocol.admin, &usdc_asset_enum);

    let crashed_price = 800_000_000_000_000u128; // $0.80 (14 decimals)
    let expiry = env.ledger().timestamp() + 86400;
    protocol.price_oracle.set_manual_override(
        &protocol.admin,
        &usdc_asset_enum,
        &Some(crashed_price),
        &Some(expiry),
    );

    // Verify user is now liquidatable
    let hf_after_crash = protocol
        .kinetic_router
        .get_user_account_data(&protocol.user)
        .health_factor;
    assert!(
        hf_after_crash < WAD,
        "User should be unhealthy after 20% price drop. HF: {}",
        hf_after_crash
    );

    // First liquidation: partial (50% close factor)
    let debt_to_cover_1 = user1_borrow / 2;
    protocol.kinetic_router.liquidation_call(
        &protocol.liquidator,
        &protocol.usdc_asset,
        &protocol.usdt_asset,
        &protocol.user,
        &debt_to_cover_1,
        &false,
    );

    let hf_after_first = protocol
        .kinetic_router
        .get_user_account_data(&protocol.user)
        .health_factor;
    assert!(
        hf_after_first > hf_after_crash,
        "HF must improve after liquidation. Before: {}, After: {}",
        hf_after_crash,
        hf_after_first
    );

    // If still unhealthy, second liquidation should be possible
    if hf_after_first < WAD {
        let remaining_debt = protocol.usdt_debt_token.balance(&protocol.user) as u128;
        let debt_to_cover_2 = remaining_debt / 2;
        if debt_to_cover_2 > 0 {
            protocol.kinetic_router.liquidation_call(
                &protocol.liquidator,
                &protocol.usdc_asset,
                &protocol.usdt_asset,
                &protocol.user,
                &debt_to_cover_2,
                &false,
            );

            let hf_after_second = protocol
                .kinetic_router
                .get_user_account_data(&protocol.user)
                .health_factor;
            assert!(
                hf_after_second > hf_after_first,
                "HF must improve on second liquidation. Before: {}, After: {}",
                hf_after_first,
                hf_after_second
            );
        }
    }

    // Verify liquidator received collateral (USDC)
    let liquidator_usdc = protocol.usdc_client.balance(&protocol.liquidator);
    // Liquidator started with 100_000_000_000_000 USDC
    assert!(
        liquidator_usdc > 100_000_000_000_000i128,
        "Liquidator should have gained USDC collateral. Balance: {}",
        liquidator_usdc
    );
}

// =============================================================================
// Test 3: Interest Accrual Across Multiple Operations
// =============================================================================

#[test]
fn test_interest_accrual_across_multiple_operations() {
    let env = Env::default();
    env.mock_all_auths();
    set_default_ledger(&env);

    let protocol = deploy_test_protocol(&env);
    let ray = 1_000_000_000_000_000_000_000_000_000u128;

    // Initial supply from LP
    protocol.kinetic_router.supply(
        &protocol.liquidity_provider,
        &protocol.underlying_asset,
        &50_000_000_000u128,
        &protocol.liquidity_provider,
        &0u32,
    );

    // User supplies collateral and borrows
    protocol.kinetic_router.supply(
        &protocol.user,
        &protocol.underlying_asset,
        &20_000_000_000u128,
        &protocol.user,
        &0u32,
    );
    protocol.kinetic_router.set_user_use_reserve_as_coll(
        &protocol.user,
        &protocol.underlying_asset,
        &true,
    );
    protocol.kinetic_router.borrow(
        &protocol.user,
        &protocol.underlying_asset,
        &5_000_000_000u128,
        &1u32,
        &0u32,
        &protocol.user,
    );

    // Checkpoint 1: indices at t=0
    let idx0 = protocol
        .kinetic_router
        .get_reserve_data(&protocol.underlying_asset);
    assert_eq!(idx0.liquidity_index, ray, "Initial liquidity index = RAY");
    assert_eq!(
        idx0.variable_borrow_index, ray,
        "Initial borrow index = RAY"
    );

    // Advance 2 days, supply more (triggers state update)
    advance_ledger(&env, 2 * 86_400);
    refresh_oracle_and_approvals(&env, &protocol);
    protocol.kinetic_router.supply(
        &protocol.liquidity_provider,
        &protocol.underlying_asset,
        &10_000_000_000u128,
        &protocol.liquidity_provider,
        &0u32,
    );

    let idx1 = protocol
        .kinetic_router
        .get_reserve_data(&protocol.underlying_asset);
    assert!(
        idx1.liquidity_index > ray,
        "Liquidity index must grow after 2 days with borrow. Got: {}",
        idx1.liquidity_index
    );
    assert!(
        idx1.variable_borrow_index > ray,
        "Borrow index must grow after 2 days. Got: {}",
        idx1.variable_borrow_index
    );

    // Advance another 2 days, user partially repays (triggers state update)
    advance_ledger(&env, 2 * 86_400);
    refresh_oracle_and_approvals(&env, &protocol);
    protocol.kinetic_router.repay(
        &protocol.user,
        &protocol.underlying_asset,
        &2_000_000_000u128,
        &1u32,
        &protocol.user,
    );

    let idx2 = protocol
        .kinetic_router
        .get_reserve_data(&protocol.underlying_asset);
    assert!(
        idx2.liquidity_index > idx1.liquidity_index,
        "Liquidity index must be monotonically increasing. t1: {}, t2: {}",
        idx1.liquidity_index,
        idx2.liquidity_index
    );
    assert!(
        idx2.variable_borrow_index > idx1.variable_borrow_index,
        "Borrow index must be monotonically increasing. t1: {}, t2: {}",
        idx1.variable_borrow_index,
        idx2.variable_borrow_index
    );

    // Advance another 2 days, user withdraws some (triggers state update)
    advance_ledger(&env, 2 * 86_400);
    refresh_oracle_and_approvals(&env, &protocol);
    protocol.kinetic_router.withdraw(
        &protocol.user,
        &protocol.underlying_asset,
        &5_000_000_000u128,
        &protocol.user,
    );

    let idx3 = protocol
        .kinetic_router
        .get_reserve_data(&protocol.underlying_asset);
    assert!(
        idx3.liquidity_index > idx2.liquidity_index,
        "Liquidity index must keep growing. t2: {}, t3: {}",
        idx2.liquidity_index,
        idx3.liquidity_index
    );
    assert!(
        idx3.variable_borrow_index > idx2.variable_borrow_index,
        "Borrow index must keep growing. t2: {}, t3: {}",
        idx2.variable_borrow_index,
        idx3.variable_borrow_index
    );

    // Borrow index grows faster than liquidity index (compound vs linear)
    let liq_growth = idx3.liquidity_index - ray;
    let borrow_growth = idx3.variable_borrow_index - ray;
    assert!(
        borrow_growth > liq_growth,
        "Borrow index (compound) must grow faster than liquidity index (linear). Borrow growth: {}, Liq growth: {}",
        borrow_growth,
        liq_growth
    );
}

// =============================================================================
// Test 4: Conservation of Value Through Full Cycle
// =============================================================================

#[test]
fn test_conservation_of_value_single_user() {
    let env = Env::default();
    env.mock_all_auths();
    set_default_ledger(&env);

    let protocol = deploy_test_protocol(&env);

    let supply_amount = 10_000_000_000u128;
    let initial_balance = protocol
        .underlying_asset_client
        .balance(&protocol.user) as u128;

    // Supply
    protocol.kinetic_router.supply(
        &protocol.user,
        &protocol.underlying_asset,
        &supply_amount,
        &protocol.user,
        &0u32,
    );

    // Verify aTokens match
    let a_balance = protocol.a_token.balance(&protocol.user) as u128;
    assert_eq!(a_balance, supply_amount, "aTokens = supply amount (no interest yet)");

    // Withdraw everything
    protocol.kinetic_router.withdraw(
        &protocol.user,
        &protocol.underlying_asset,
        &u128::MAX,
        &protocol.user,
    );

    let final_balance = protocol
        .underlying_asset_client
        .balance(&protocol.user) as u128;
    assert_eq!(
        final_balance, initial_balance,
        "Supply + full withdraw (no interest) must return exact original balance"
    );

    let a_final = protocol.a_token.balance(&protocol.user);
    assert_eq!(a_final, 0, "No aTokens should remain");
}

// =============================================================================
// Test 5: Liquidation Cannot Make Position Worse (H-04 Regression)
// =============================================================================

#[test]
fn test_liquidation_improves_health_factor() {
    let env = Env::default();
    env.mock_all_auths();
    set_default_ledger(&env);

    let protocol = deploy_test_protocol_two_assets(&env);

    // Setup position
    protocol.kinetic_router.supply(
        &protocol.liquidity_provider,
        &protocol.usdt_asset,
        &50_000_000_000u128,
        &protocol.liquidity_provider,
        &0u32,
    );

    protocol.kinetic_router.supply(
        &protocol.user,
        &protocol.usdc_asset,
        &10_000_000_000u128,
        &protocol.user,
        &0u32,
    );
    protocol.kinetic_router.set_user_use_reserve_as_coll(
        &protocol.user,
        &protocol.usdc_asset,
        &true,
    );
    protocol.kinetic_router.borrow(
        &protocol.user,
        &protocol.usdt_asset,
        &7_000_000_000u128,
        &1u32,
        &0u32,
        &protocol.user,
    );

    // Crash price
    let usdc_asset_enum = price_oracle::Asset::Stellar(protocol.usdc_asset.clone());
    protocol
        .price_oracle
        .reset_circuit_breaker(&protocol.admin, &usdc_asset_enum);
    protocol.price_oracle.set_manual_override(
        &protocol.admin,
        &usdc_asset_enum,
        &Some(750_000_000_000_000u128), // $0.75
        &Some(env.ledger().timestamp() + 86400),
    );

    let hf_before_liq = protocol
        .kinetic_router
        .get_user_account_data(&protocol.user)
        .health_factor;
    assert!(hf_before_liq < WAD, "Must be unhealthy for liquidation");

    // Liquidate
    protocol.kinetic_router.liquidation_call(
        &protocol.liquidator,
        &protocol.usdc_asset,
        &protocol.usdt_asset,
        &protocol.user,
        &3_500_000_000u128,
        &false,
    );

    let hf_after_liq = protocol
        .kinetic_router
        .get_user_account_data(&protocol.user)
        .health_factor;
    assert!(
        hf_after_liq > hf_before_liq,
        "H-04 regression: HF must improve after liquidation. Before: {}, After: {}",
        hf_before_liq,
        hf_after_liq
    );
}

// =============================================================================
// Test 6: Healthy Position Cannot Be Liquidated
// =============================================================================

#[test]
fn test_healthy_position_not_liquidatable() {
    let env = Env::default();
    env.mock_all_auths();
    set_default_ledger(&env);

    let protocol = deploy_test_protocol_two_assets(&env);

    // Setup a healthy position
    protocol.kinetic_router.supply(
        &protocol.liquidity_provider,
        &protocol.usdt_asset,
        &50_000_000_000u128,
        &protocol.liquidity_provider,
        &0u32,
    );

    protocol.kinetic_router.supply(
        &protocol.user,
        &protocol.usdc_asset,
        &10_000_000_000u128,
        &protocol.user,
        &0u32,
    );
    protocol.kinetic_router.set_user_use_reserve_as_coll(
        &protocol.user,
        &protocol.usdc_asset,
        &true,
    );
    protocol.kinetic_router.borrow(
        &protocol.user,
        &protocol.usdt_asset,
        &2_000_000_000u128, // Very conservative borrow
        &1u32,
        &0u32,
        &protocol.user,
    );

    let hf = protocol
        .kinetic_router
        .get_user_account_data(&protocol.user)
        .health_factor;
    assert!(hf > WAD, "Position should be healthy. HF: {}", hf);

    // Attempt liquidation — should fail
    let result = protocol.kinetic_router.try_liquidation_call(
        &protocol.liquidator,
        &protocol.usdc_asset,
        &protocol.usdt_asset,
        &protocol.user,
        &1_000_000_000u128,
        &false,
    );
    assert!(
        result.is_err(),
        "Liquidating a healthy position must fail"
    );
}

// =============================================================================
// Test 7: Supply → Borrow → Time → Repay More Than Original (Interest)
// =============================================================================

#[test]
fn test_repay_includes_accrued_interest() {
    let env = Env::default();
    env.mock_all_auths();
    set_default_ledger(&env);

    let protocol = deploy_test_protocol(&env);

    // Setup
    protocol.kinetic_router.supply(
        &protocol.liquidity_provider,
        &protocol.underlying_asset,
        &50_000_000_000u128,
        &protocol.liquidity_provider,
        &0u32,
    );
    protocol.kinetic_router.supply(
        &protocol.user,
        &protocol.underlying_asset,
        &20_000_000_000u128,
        &protocol.user,
        &0u32,
    );
    protocol.kinetic_router.set_user_use_reserve_as_coll(
        &protocol.user,
        &protocol.underlying_asset,
        &true,
    );

    let borrow_amount = 5_000_000_000u128;
    protocol.kinetic_router.borrow(
        &protocol.user,
        &protocol.underlying_asset,
        &borrow_amount,
        &1u32,
        &0u32,
        &protocol.user,
    );

    // Advance 5 days (within oracle expiry window of 604,800s ~= 7 days)
    advance_ledger(&env, 5 * 86_400);

    // Debt should be more than original borrow
    let debt_after_5_days = protocol.debt_token.balance(&protocol.user) as u128;
    assert!(
        debt_after_5_days > borrow_amount,
        "Debt must grow with interest. Original: {}, After 5 days: {}",
        borrow_amount,
        debt_after_5_days
    );

    // Repay exactly the original borrow amount — should leave residual debt
    protocol.kinetic_router.repay(
        &protocol.user,
        &protocol.underlying_asset,
        &borrow_amount,
        &1u32,
        &protocol.user,
    );

    let remaining_debt = protocol.debt_token.balance(&protocol.user);
    assert!(
        remaining_debt > 0,
        "Repaying original amount should leave interest as remaining debt. Remaining: {}",
        remaining_debt
    );

    // Repay the rest
    protocol.kinetic_router.repay(
        &protocol.user,
        &protocol.underlying_asset,
        &u128::MAX,
        &1u32,
        &protocol.user,
    );

    let final_debt = protocol.debt_token.balance(&protocol.user);
    assert_eq!(final_debt, 0, "Full repay should clear all debt");
}
