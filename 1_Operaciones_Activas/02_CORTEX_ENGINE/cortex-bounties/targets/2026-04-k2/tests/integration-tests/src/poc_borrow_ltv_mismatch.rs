#![cfg(test)]

//! Test for FIND-043: Borrow-limit inconsistency fix
//! 
//! Verifies that available_borrows_base is calculated correctly as:
//! (collateral * LTV) - debt
//! 

use crate::setup::{create_test_env_with_budget_limits, deploy_test_protocol_two_assets};

#[test]
fn poc_borrow_exceeds_ltv_due_to_available_formula() {
    let env = create_test_env_with_budget_limits();
    let protocol = deploy_test_protocol_two_assets(&env);

    // Setup: LP provides 200 USDT liquidity
    let lp_supply = 200_000_000_000u128;
    protocol.kinetic_router.supply(
        &protocol.liquidity_provider,
        &protocol.usdt_asset,
        &lp_supply,
        &protocol.liquidity_provider,
        &0u32,
    );

    // User supplies 100 USDC collateral (80% LTV, 85% liquidation threshold)
    let coll_supply = 100_000_000_000u128;
    protocol.kinetic_router.supply(
        &protocol.user,
        &protocol.usdc_asset,
        &coll_supply,
        &protocol.user,
        &0u32,
    );
    protocol
        .kinetic_router
        .set_user_use_reserve_as_coll(&protocol.user, &protocol.usdc_asset, &true);

    // Verify initial available borrows: 100 * 0.80 = 80
    let data_before = protocol
        .kinetic_router
        .get_user_account_data(&protocol.user);
    let expected_max_borrow_no_debt = data_before.total_collateral_base * 8000 / 10000;
    assert_eq!(
        data_before.available_borrows_base, expected_max_borrow_no_debt,
        "Initial available borrows should equal collateral * LTV"
    );

    // Borrow 60 USDT (within LTV)
    protocol.kinetic_router.borrow(
        &protocol.user,
        &protocol.usdt_asset,
        &60_000_000_000u128,
        &1u32,
        &0u32,
        &protocol.user,
    );

    let data_after = protocol
        .kinetic_router
        .get_user_account_data(&protocol.user);

    // Verify correct formula: (100 * 0.80) - 60 = 20 available
    let expected_max_debt = data_after.total_collateral_base * 8000 / 10000;
    let expected_available = expected_max_debt.saturating_sub(data_after.total_debt_base);
    
    assert_eq!(
        data_after.available_borrows_base, 
        expected_available,
        "available_borrows_base should be (collateral * LTV) - debt"
    );

    // Verify wrong formula would give different result: (100 - 60) * 0.80 = 32
    let collateral_minus_debt = data_after
        .total_collateral_base
        .saturating_sub(data_after.total_debt_base);
    let wrong_available = (collateral_minus_debt * 8000) / 10000;

    assert!(
        wrong_available > expected_available,
        "Wrong formula would report higher available borrows"
    );

    // Attempt borrow between correct and wrong limits (should fail)
    let amount_between = (expected_available + wrong_available) / 2;
    let amount_in_asset_units = (amount_between * 10_000_000) / 1_000_000_000_000_000_000;
    
    if amount_in_asset_units > 0 {
        let result = protocol.kinetic_router.try_borrow(
            &protocol.user,
            &protocol.usdt_asset,
            &amount_in_asset_units,
            &1u32,
            &0u32,
            &protocol.user,
        );

        assert!(
            result.is_err(),
            "Borrow exceeding available_borrows_base should be rejected"
        );
    }
}
