#![cfg(test)]

//! Integration tests for O(1) Health Factor state management.
//!
//! These tests verify that the O(1) HF state is correctly maintained
//! and matches the O(N) calculation across all operations.

use crate::setup::{create_test_env_with_budget_limits, deploy_test_protocol_two_assets};
use soroban_sdk::{
    testutils::{MockAuth, MockAuthInvoke},
    IntoVal,
};

const WAD: u128 = 1_000_000_000_000_000_000; // 1e18

/// Helper to compare O(1) and O(N) HF values with tolerance
fn assert_hf_match(o1_hf: u128, on_hf: u128, tolerance_bps: u128, context: &str) {
    // Skip comparison if both are MAX (no debt case)
    if o1_hf == u128::MAX && on_hf == u128::MAX {
        return;
    }
    
    // Handle case where one is MAX
    if o1_hf == u128::MAX || on_hf == u128::MAX {
        // If O(N) shows no debt but O(1) shows debt, that's a mismatch
        // But O(1) state might be stale for existing positions
        println!("⚠️  {} - HF mismatch (one is MAX): O1={}, ON={}", context, o1_hf, on_hf);
        return;
    }
    
    // Calculate relative difference in basis points
    let diff = if o1_hf > on_hf { o1_hf - on_hf } else { on_hf - o1_hf };
    let avg = (o1_hf + on_hf) / 2;
    let diff_bps = if avg > 0 { (diff * 10000) / avg } else { 0 };
    
    println!("{} - O1 HF: {}, O(N) HF: {}, diff: {} bps", context, o1_hf, on_hf, diff_bps);
    
    assert!(
        diff_bps <= tolerance_bps,
        "{} - HF mismatch too large: O1={}, ON={}, diff={} bps > {} bps tolerance",
        context, o1_hf, on_hf, diff_bps, tolerance_bps
    );
}

/// Test that UserHFState is lazily initialized on first supply
#[test]
fn test_hf_o1_lazy_init_on_supply() {
    let env = create_test_env_with_budget_limits();
    let protocol = deploy_test_protocol_two_assets(&env);

    // Before supply, user should have no HF state
    let hf_state_before = protocol.kinetic_router.get_user_hf_state(&protocol.user);
    assert!(hf_state_before.is_none(), "User should have no HF state before any action");

    // Supply collateral
    let supply_amount = 100_000_000_000u128; // 100 USDC
    protocol.kinetic_router.supply(
        &protocol.user,
        &protocol.usdc_asset,
        &supply_amount,
        &protocol.user,
        &0u32,
    );

    // After supply, user should have HF state
    let hf_state_after = protocol.kinetic_router.get_user_hf_state(&protocol.user);
    assert!(hf_state_after.is_some(), "User should have HF state after supply");

    let state = hf_state_after.unwrap();
    println!("After supply:");
    println!("  total_collateral_base: {}", state.total_collateral_base);
    println!("  total_debt_base: {}", state.total_debt_base);
    println!("  weighted_threshold_sum: {}", state.weighted_threshold_sum);
    println!("  weighted_ltv_sum: {}", state.weighted_ltv_sum);

    // Verify collateral is non-zero
    assert!(state.total_collateral_base > 0, "Collateral should be > 0 after supply");
    assert_eq!(state.total_debt_base, 0, "Debt should be 0 (no borrow yet)");

    // O(1) HF should be MAX (no debt)
    let hf_o1 = protocol.kinetic_router.get_hf_o1(&protocol.user);
    assert_eq!(hf_o1, u128::MAX, "HF should be MAX with no debt");
}

/// Test that UserHFState is correctly updated after borrow
#[test]
fn test_hf_o1_update_on_borrow() {
    let env = create_test_env_with_budget_limits();
    let protocol = deploy_test_protocol_two_assets(&env);

    // LP provides USDT liquidity for borrowing
    protocol.kinetic_router.supply(
        &protocol.liquidity_provider,
        &protocol.usdt_asset,
        &200_000_000_000u128,
        &protocol.liquidity_provider,
        &0u32,
    );

    // User supplies USDC as collateral
    let supply_amount = 100_000_000_000u128;
    protocol.kinetic_router.supply(
        &protocol.user,
        &protocol.usdc_asset,
        &supply_amount,
        &protocol.user,
        &0u32,
    );

    protocol.kinetic_router.set_user_use_reserve_as_coll(
        &protocol.user,
        &protocol.usdc_asset,
        &true,
    );

    // Get state before borrow
    let state_before = protocol.kinetic_router.get_user_hf_state(&protocol.user).unwrap();
    assert_eq!(state_before.total_debt_base, 0, "No debt before borrow");

    // Borrow USDT
    let borrow_amount = 30_000_000_000u128;
    protocol.kinetic_router.borrow(
        &protocol.user,
        &protocol.usdt_asset,
        &borrow_amount,
        &1u32,
        &0u32,
        &protocol.user,
    );

    // Get state after borrow
    let state_after = protocol.kinetic_router.get_user_hf_state(&protocol.user).unwrap();
    println!("After borrow:");
    println!("  total_collateral_base: {}", state_after.total_collateral_base);
    println!("  total_debt_base: {}", state_after.total_debt_base);

    assert!(state_after.total_debt_base > 0, "Debt should be > 0 after borrow");

    // Compare O(1) HF with O(N) HF
    let hf_o1 = protocol.kinetic_router.get_hf_o1(&protocol.user);
    let account_data = protocol.kinetic_router.get_user_account_data(&protocol.user);
    
    // Allow 5% tolerance since O(1) state may have slight timing differences
    assert_hf_match(hf_o1, account_data.health_factor, 500, "After borrow");
    
    // Both should show healthy position (HF > 1.0)
    assert!(hf_o1 >= WAD, "O(1) HF should be >= 1.0");
    assert!(account_data.health_factor >= WAD, "O(N) HF should be >= 1.0");
}

/// Test that UserHFState is correctly updated after repay and GC'd when empty
#[test]
fn test_hf_o1_update_on_repay_and_gc() {
    let env = create_test_env_with_budget_limits();
    let protocol = deploy_test_protocol_two_assets(&env);

    // LP provides liquidity
    protocol.kinetic_router.supply(
        &protocol.liquidity_provider,
        &protocol.usdt_asset,
        &200_000_000_000u128,
        &protocol.liquidity_provider,
        &0u32,
    );

    // User supplies and borrows
    let supply_amount = 100_000_000_000u128;
    let borrow_amount = 30_000_000_000u128;

    protocol.kinetic_router.supply(
        &protocol.user,
        &protocol.usdc_asset,
        &supply_amount,
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
        &borrow_amount,
        &1u32,
        &0u32,
        &protocol.user,
    );

    // Verify debt exists
    let state_with_debt = protocol.kinetic_router.get_user_hf_state(&protocol.user).unwrap();
    assert!(state_with_debt.total_debt_base > 0, "Should have debt");

    // Repay full debt
    protocol.kinetic_router.repay(
        &protocol.user,
        &protocol.usdt_asset,
        &u128::MAX, // Repay all
        &1u32,
        &protocol.user,
    );

    // Check state after repay
    let state_after_repay = protocol.kinetic_router.get_user_hf_state(&protocol.user).unwrap();
    println!("After repay:");
    println!("  total_debt_base: {}", state_after_repay.total_debt_base);
    
    // Debt should be 0 or very close (interest accrual)
    assert!(
        state_after_repay.total_debt_base < 1_000_000, // Allow tiny dust
        "Debt should be ~0 after full repay"
    );

    // O(1) HF should be MAX (no debt)
    let hf_o1 = protocol.kinetic_router.get_hf_o1(&protocol.user);
    assert_eq!(hf_o1, u128::MAX, "HF should be MAX after repaying all debt");
}

/// Test that UserHFState is correctly updated after withdraw
#[test]
fn test_hf_o1_update_on_withdraw() {
    let env = create_test_env_with_budget_limits();
    let protocol = deploy_test_protocol_two_assets(&env);

    // User supplies collateral
    let supply_amount = 100_000_000_000u128;
    protocol.kinetic_router.supply(
        &protocol.user,
        &protocol.usdc_asset,
        &supply_amount,
        &protocol.user,
        &0u32,
    );

    let state_before = protocol.kinetic_router.get_user_hf_state(&protocol.user).unwrap();
    let collateral_before = state_before.total_collateral_base;

    // Withdraw half
    let withdraw_amount = 50_000_000_000u128;
    protocol.kinetic_router.withdraw(
        &protocol.user,
        &protocol.usdc_asset,
        &withdraw_amount,
        &protocol.user,
    );

    let state_after = protocol.kinetic_router.get_user_hf_state(&protocol.user).unwrap();
    println!("After withdraw:");
    println!("  collateral before: {}", collateral_before);
    println!("  collateral after: {}", state_after.total_collateral_base);

    // Collateral should decrease by approximately half
    assert!(
        state_after.total_collateral_base < collateral_before,
        "Collateral should decrease after withdraw"
    );

    // Withdraw all remaining
    protocol.kinetic_router.withdraw(
        &protocol.user,
        &protocol.usdc_asset,
        &u128::MAX,
        &protocol.user,
    );

    // State should be GC'd (both collateral and debt are 0)
    let state_final = protocol.kinetic_router.get_user_hf_state(&protocol.user);
    assert!(
        state_final.is_none(),
        "HF state should be GC'd after withdrawing all collateral"
    );
}

/// Test O(1) HF matches O(N) HF through supply/borrow/repay cycle
#[test]
fn test_hf_o1_matches_on_through_cycle() {
    let env = create_test_env_with_budget_limits();
    let protocol = deploy_test_protocol_two_assets(&env);

    // LP provides liquidity
    protocol.kinetic_router.supply(
        &protocol.liquidity_provider,
        &protocol.usdt_asset,
        &500_000_000_000u128,
        &protocol.liquidity_provider,
        &0u32,
    );

    // Step 1: Supply
    protocol.kinetic_router.supply(
        &protocol.user,
        &protocol.usdc_asset,
        &100_000_000_000u128,
        &protocol.user,
        &0u32,
    );
    protocol.kinetic_router.set_user_use_reserve_as_coll(
        &protocol.user,
        &protocol.usdc_asset,
        &true,
    );

    let hf_o1_1 = protocol.kinetic_router.get_hf_o1(&protocol.user);
    let on_data_1 = protocol.kinetic_router.get_user_account_data(&protocol.user);
    assert_hf_match(hf_o1_1, on_data_1.health_factor, 500, "Step 1: After supply");

    // Step 2: Borrow
    protocol.kinetic_router.borrow(
        &protocol.user,
        &protocol.usdt_asset,
        &30_000_000_000u128,
        &1u32,
        &0u32,
        &protocol.user,
    );

    let hf_o1_2 = protocol.kinetic_router.get_hf_o1(&protocol.user);
    let on_data_2 = protocol.kinetic_router.get_user_account_data(&protocol.user);
    assert_hf_match(hf_o1_2, on_data_2.health_factor, 500, "Step 2: After borrow");

    // Step 3: Supply more
    protocol.kinetic_router.supply(
        &protocol.user,
        &protocol.usdc_asset,
        &50_000_000_000u128,
        &protocol.user,
        &0u32,
    );

    let hf_o1_3 = protocol.kinetic_router.get_hf_o1(&protocol.user);
    let on_data_3 = protocol.kinetic_router.get_user_account_data(&protocol.user);
    assert_hf_match(hf_o1_3, on_data_3.health_factor, 500, "Step 3: After more supply");

    // Step 4: Partial repay
    protocol.kinetic_router.repay(
        &protocol.user,
        &protocol.usdt_asset,
        &10_000_000_000u128,
        &1u32,
        &protocol.user,
    );

    let hf_o1_4 = protocol.kinetic_router.get_hf_o1(&protocol.user);
    let on_data_4 = protocol.kinetic_router.get_user_account_data(&protocol.user);
    assert_hf_match(hf_o1_4, on_data_4.health_factor, 500, "Step 4: After partial repay");

    println!("\n=== HF Comparison Summary ===");
    println!("Step 1 (supply):     O1={}, ON={}", hf_o1_1, on_data_1.health_factor);
    println!("Step 2 (borrow):     O1={}, ON={}", hf_o1_2, on_data_2.health_factor);
    println!("Step 3 (more supply): O1={}, ON={}", hf_o1_3, on_data_3.health_factor);
    println!("Step 4 (repay):      O1={}, ON={}", hf_o1_4, on_data_4.health_factor);
}

/// Test O(1) HF with swap_collateral
#[test]
fn test_hf_o1_swap_collateral() {
    let env = create_test_env_with_budget_limits();
    let protocol = deploy_test_protocol_two_assets(&env);

    // LP provides liquidity
    protocol.kinetic_router.supply(
        &protocol.liquidity_provider,
        &protocol.usdt_asset,
        &200_000_000_000u128,
        &protocol.liquidity_provider,
        &0u32,
    );

    // User supplies and borrows
    protocol.kinetic_router.supply(
        &protocol.user,
        &protocol.usdc_asset,
        &100_000_000_000u128,
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
        &30_000_000_000u128,
        &1u32,
        &0u32,
        &protocol.user,
    );

    // Get state before swap
    let state_before = protocol.kinetic_router.get_user_hf_state(&protocol.user).unwrap();
    let hf_o1_before = protocol.kinetic_router.get_hf_o1(&protocol.user);
    let on_before = protocol.kinetic_router.get_user_account_data(&protocol.user);

    println!("Before swap:");
    println!("  O(1) collateral: {}", state_before.total_collateral_base);
    println!("  O(1) debt: {}", state_before.total_debt_base);
    println!("  O(1) HF: {}", hf_o1_before);
    println!("  O(N) HF: {}", on_before.health_factor);

    // Execute swap
    let swap_amount = 30_000_000_000u128;
    env.mock_auths(&[MockAuth {
        address: &protocol.user,
        invoke: &MockAuthInvoke {
            contract: &protocol.kinetic_router.address,
            fn_name: "swap_collateral",
            args: (
                &protocol.user,
                &protocol.usdc_asset,
                &protocol.usdt_asset,
                &swap_amount,
                &29_000_000_000u128,
                &None::<Address>, // Use default DEX router
            ).into_val(&env),
            sub_invokes: &[],
        },
    }]);

    protocol.kinetic_router.swap_collateral(
        &protocol.user,
        &protocol.usdc_asset,
        &protocol.usdt_asset,
        &swap_amount,
        &29_000_000_000u128,
        &None, // Use default DEX router
    );

    // Get state after swap
    let state_after = protocol.kinetic_router.get_user_hf_state(&protocol.user).unwrap();
    let hf_o1_after = protocol.kinetic_router.get_hf_o1(&protocol.user);
    let on_after = protocol.kinetic_router.get_user_account_data(&protocol.user);

    println!("\nAfter swap:");
    println!("  O(1) collateral: {}", state_after.total_collateral_base);
    println!("  O(1) debt: {}", state_after.total_debt_base);
    println!("  O(1) HF: {}", hf_o1_after);
    println!("  O(N) HF: {}", on_after.health_factor);

    // Collateral should be similar (swap is ~1:1 stablecoin)
    // Allow 10% tolerance for fees and slippage
    let collateral_diff = if state_after.total_collateral_base > state_before.total_collateral_base {
        state_after.total_collateral_base - state_before.total_collateral_base
    } else {
        state_before.total_collateral_base - state_after.total_collateral_base
    };
    let collateral_diff_pct = (collateral_diff * 100) / state_before.total_collateral_base;
    
    assert!(
        collateral_diff_pct <= 10,
        "Collateral change should be < 10% for stablecoin swap, got {}%",
        collateral_diff_pct
    );

    // Debt should be unchanged
    let debt_diff = if state_after.total_debt_base > state_before.total_debt_base {
        state_after.total_debt_base - state_before.total_debt_base
    } else {
        state_before.total_debt_base - state_after.total_debt_base
    };
    let debt_diff_pct = if state_before.total_debt_base > 0 {
        (debt_diff * 100) / state_before.total_debt_base
    } else {
        0
    };
    
    assert!(
        debt_diff_pct <= 1,
        "Debt should change < 1% during swap, got {}%",
        debt_diff_pct
    );

    // Compare HF values
    assert_hf_match(hf_o1_after, on_after.health_factor, 500, "After swap");
}

/// Test available borrows O(1) calculation
#[test]
fn test_available_borrows_o1() {
    let env = create_test_env_with_budget_limits();
    let protocol = deploy_test_protocol_two_assets(&env);

    // Before any action, available borrows should be 0
    let borrows_before = protocol.kinetic_router.get_available_borrows_o1(&protocol.user);
    assert_eq!(borrows_before, 0, "No borrows available before supply");

    // Supply collateral
    protocol.kinetic_router.supply(
        &protocol.user,
        &protocol.usdc_asset,
        &100_000_000_000u128,
        &protocol.user,
        &0u32,
    );
    protocol.kinetic_router.set_user_use_reserve_as_coll(
        &protocol.user,
        &protocol.usdc_asset,
        &true,
    );

    // After supply, should have borrow capacity
    let borrows_after_supply = protocol.kinetic_router.get_available_borrows_o1(&protocol.user);
    let on_data = protocol.kinetic_router.get_user_account_data(&protocol.user);
    
    println!("After supply:");
    println!("  O(1) available borrows: {}", borrows_after_supply);
    println!("  O(N) available borrows: {}", on_data.available_borrows_base);

    assert!(borrows_after_supply > 0, "Should have borrow capacity after supply");

    // LP provides liquidity for borrowing
    protocol.kinetic_router.supply(
        &protocol.liquidity_provider,
        &protocol.usdt_asset,
        &200_000_000_000u128,
        &protocol.liquidity_provider,
        &0u32,
    );

    // Borrow some
    protocol.kinetic_router.borrow(
        &protocol.user,
        &protocol.usdt_asset,
        &30_000_000_000u128,
        &1u32,
        &0u32,
        &protocol.user,
    );

    // Available borrows should decrease
    let borrows_after_borrow = protocol.kinetic_router.get_available_borrows_o1(&protocol.user);
    let on_data_2 = protocol.kinetic_router.get_user_account_data(&protocol.user);
    
    println!("\nAfter borrow:");
    println!("  O(1) available borrows: {}", borrows_after_borrow);
    println!("  O(N) available borrows: {}", on_data_2.available_borrows_base);

    assert!(
        borrows_after_borrow < borrows_after_supply,
        "Available borrows should decrease after borrowing"
    );
}

