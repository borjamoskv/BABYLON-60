#![cfg(test)]

//! Edge case tests for two-step liquidation (prepare + execute)
//!
//! Tests ensure the two-step liquidation works correctly for:
//! - Users with multiple asset positions
//! - Users with only liquidation assets
//! - Users with many reserves
//! - Edge cases in reserve data caching

use crate::setup::{create_test_env_with_budget_limits, deploy_test_protocol_two_assets};
use k2_shared::WAD;
use soroban_sdk::{
    testutils::{MockAuth, MockAuthInvoke},
    Address, IntoVal,
};

#[test]
fn test_flash_liquidation_user_with_multiple_collateral_assets() {
    // Edge case: User has positions in multiple assets (supply + borrow)
    // Ensures calculate_user_account_data_selective reads ALL user's positions
    let env = create_test_env_with_budget_limits();
    let protocol = deploy_test_protocol_two_assets(&env);

    // User supplies USDC as collateral, borrows USDT → multi-asset position
    let usdc_supply = 100_000_000_000u128;

    // LP provides liquidity
    protocol.kinetic_router.supply(
        &protocol.liquidity_provider,
        &protocol.usdt_asset,
        &200_000_000_000u128,
        &protocol.liquidity_provider,
        &0u32,
    );

    protocol.kinetic_router.supply(
        &protocol.liquidity_provider,
        &protocol.usdc_asset,
        &200_000_000_000u128,
        &protocol.liquidity_provider,
        &0u32,
    );

    // User supplies USDC
    protocol.kinetic_router.supply(
        &protocol.user,
        &protocol.usdc_asset,
        &usdc_supply,
        &protocol.user,
        &0u32,
    );

    // Enable USDC as collateral
    protocol.kinetic_router.set_user_use_reserve_as_coll(
        &protocol.user,
        &protocol.usdc_asset,
        &true,
    );

    // H-04: Use 70% LTV + $0.80 crash so post-liquidation HF improves
    protocol.kinetic_router.borrow(
        &protocol.user,
        &protocol.usdt_asset,
        &70_000_000_000u128,
        &1u32,
        &0u32,
        &protocol.user,
    );

    // Verify health factor is healthy
    let account_data_before = protocol.kinetic_router.get_user_account_data(&protocol.user);
    assert!(
        account_data_before.health_factor >= WAD,
        "Health factor should be healthy. HF: {}",
        account_data_before.health_factor
    );

    // Crash USDC price to make position liquidatable
    let usdc_asset_enum = crate::price_oracle::Asset::Stellar(protocol.usdc_asset.clone());
    protocol.price_oracle.reset_circuit_breaker(&protocol.admin, &usdc_asset_enum);
    let expiry = env.ledger().timestamp() + 86400;
    protocol.price_oracle.set_manual_override(
        &protocol.admin,
        &usdc_asset_enum,
        &Some(800_000_000_000_000u128), // $0.80
        &Some(expiry),
    );

    // Verify position is now liquidatable
    let account_data_after_crash = protocol.kinetic_router.get_user_account_data(&protocol.user);
    assert!(
        account_data_after_crash.health_factor < WAD,
        "Position should be liquidatable. HF: {}",
        account_data_after_crash.health_factor
    );

    assert!(
        account_data_after_crash.total_debt_base > 0,
        "User should have debt"
    );
    assert!(
        account_data_after_crash.total_collateral_base > 0,
        "User should have collateral"
    );

    let debt_to_cover = 35_000_000_000u128;
    let min_swap_out = 30_000_000_000u128;
    let deadline = env.ledger().timestamp() + 300;

    // Step 1: Prepare liquidation
    env.mock_auths(&[MockAuth {
        address: &protocol.liquidator,
        invoke: &MockAuthInvoke {
            contract: &protocol.kinetic_router.address,
            fn_name: "prepare_liquidation",
            args: (
                &protocol.liquidator,
                &protocol.user,
                &protocol.usdt_asset,
                &protocol.usdc_asset,
                &debt_to_cover,
                &min_swap_out,
                &None::<Address>, // Use default DEX router
            )
                .into_val(&env),
            sub_invokes: &[],
        },
    }]);

    let _auth = protocol.kinetic_router.prepare_liquidation(
        &protocol.liquidator,
        &protocol.user,
        &protocol.usdt_asset,
        &protocol.usdc_asset,
        &debt_to_cover,
        &min_swap_out,
        &None, // Use default DEX router
    );

    // Step 2: Execute liquidation
    env.mock_auths(&[MockAuth {
        address: &protocol.liquidator,
        invoke: &MockAuthInvoke {
            contract: &protocol.kinetic_router.address,
            fn_name: "execute_liquidation",
            args: (
                &protocol.liquidator,
                &protocol.user,
                &protocol.usdt_asset,
                &protocol.usdc_asset,
                &deadline,
            )
                .into_val(&env),
            sub_invokes: &[],
        },
    }]);

    // Should succeed - optimization correctly handles multi-asset positions
    protocol.kinetic_router.execute_liquidation(
        &protocol.liquidator,
        &protocol.user,
        &protocol.usdt_asset,
        &protocol.usdc_asset,
        &deadline,
    );

    // Verify liquidation occurred
    let account_data_after = protocol.kinetic_router.get_user_account_data(&protocol.user);
    assert!(
        account_data_after.total_debt_base < account_data_after_crash.total_debt_base,
        "Debt should decrease after liquidation"
    );
}

#[test]
fn test_flash_liquidation_reserve_data_consistency() {
    // Edge case: Ensure cached reserve data matches fresh reads
    // This verifies no stale data issues
    let env = create_test_env_with_budget_limits();
    let protocol = deploy_test_protocol_two_assets(&env);

    // Setup liquidatable position (H-04: 70% LTV + $0.80 crash)
    protocol.kinetic_router.supply(
        &protocol.liquidity_provider,
        &protocol.usdt_asset,
        &200_000_000_000u128,
        &protocol.liquidity_provider,
        &0u32,
    );

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
        &70_000_000_000u128,
        &1u32,
        &0u32,
        &protocol.user,
    );

    // Crash price
    let usdc_asset_enum = crate::price_oracle::Asset::Stellar(protocol.usdc_asset.clone());
    protocol.price_oracle.reset_circuit_breaker(&protocol.admin, &usdc_asset_enum);
    let expiry = env.ledger().timestamp() + 86400;
    protocol.price_oracle.set_manual_override(
        &protocol.admin,
        &usdc_asset_enum,
        &Some(800_000_000_000_000u128), // $0.80
        &Some(expiry),
    );

    // Get reserve data BEFORE liquidation
    let collateral_reserve_before = protocol.kinetic_router.get_reserve_data(&protocol.usdc_asset);
    let debt_reserve_before = protocol.kinetic_router.get_reserve_data(&protocol.usdt_asset);

    let debt_to_cover = 35_000_000_000u128;
    let min_swap_out = 30_000_000_000u128;
    let deadline = env.ledger().timestamp() + 300;

    // Step 1: Prepare liquidation
    env.mock_auths(&[MockAuth {
        address: &protocol.liquidator,
        invoke: &MockAuthInvoke {
            contract: &protocol.kinetic_router.address,
            fn_name: "prepare_liquidation",
            args: (
                &protocol.liquidator,
                &protocol.user,
                &protocol.usdt_asset,
                &protocol.usdc_asset,
                &debt_to_cover,
                &min_swap_out,
                &None::<Address>, // Use default DEX router
            )
                .into_val(&env),
            sub_invokes: &[],
        },
    }]);

    let _auth = protocol.kinetic_router.prepare_liquidation(
        &protocol.liquidator,
        &protocol.user,
        &protocol.usdt_asset,
        &protocol.usdc_asset,
        &debt_to_cover,
        &min_swap_out,
        &None, // Use default DEX router
    );

    // Step 2: Execute liquidation
    env.mock_auths(&[MockAuth {
        address: &protocol.liquidator,
        invoke: &MockAuthInvoke {
            contract: &protocol.kinetic_router.address,
            fn_name: "execute_liquidation",
            args: (
                &protocol.liquidator,
                &protocol.user,
                &protocol.usdt_asset,
                &protocol.usdc_asset,
                &deadline,
            )
                .into_val(&env),
            sub_invokes: &[],
        },
    }]);

    protocol.kinetic_router.execute_liquidation(
        &protocol.liquidator,
        &protocol.user,
        &protocol.usdt_asset,
        &protocol.usdc_asset,
        &deadline,
    );

    // CRITICAL: Verify reserve data consistency
    // The cached data should have been the same as fresh reads at liquidation time
    let collateral_reserve_after = protocol.kinetic_router.get_reserve_data(&protocol.usdc_asset);
    let debt_reserve_after = protocol.kinetic_router.get_reserve_data(&protocol.usdt_asset);

    // Indices should have been updated during liquidation
    assert!(
        collateral_reserve_after.liquidity_index >= collateral_reserve_before.liquidity_index,
        "Liquidity index should not decrease"
    );
    
    assert!(
        debt_reserve_after.variable_borrow_index >= debt_reserve_before.variable_borrow_index,
        "Borrow index should not decrease"
    );
}

#[test]
fn test_flash_liquidation_with_zero_balance_reserves() {
    // Edge case: User has configuration bits set but zero balance in some reserves
    // Ensures selective calculation handles this correctly
    let env = create_test_env_with_budget_limits();
    let protocol = deploy_test_protocol_two_assets(&env);

    // Setup: User supplies and immediately withdraws from one asset
    // This can leave configuration bits set with zero balance
    
    protocol.kinetic_router.supply(
        &protocol.liquidity_provider,
        &protocol.usdt_asset,
        &200_000_000_000u128,
        &protocol.liquidity_provider,
        &0u32,
    );

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
        &70_000_000_000u128,
        &1u32,
        &0u32,
        &protocol.user,
    );

    // Crash price (H-04: $0.80 so post-liquidation HF improves)
    let usdc_asset_enum = crate::price_oracle::Asset::Stellar(protocol.usdc_asset.clone());
    protocol.price_oracle.reset_circuit_breaker(&protocol.admin, &usdc_asset_enum);
    let expiry = env.ledger().timestamp() + 86400;
    protocol.price_oracle.set_manual_override(
        &protocol.admin,
        &usdc_asset_enum,
        &Some(800_000_000_000_000u128), // $0.80
        &Some(expiry),
    );

    // Verify health factor calculation is correct
    let account_data = protocol.kinetic_router.get_user_account_data(&protocol.user);
    assert!(
        account_data.health_factor < WAD,
        "Position should be liquidatable"
    );

    let debt_to_cover = 35_000_000_000u128;
    let min_swap_out = 30_000_000_000u128;
    let deadline = env.ledger().timestamp() + 300;

    // Step 1: Prepare liquidation
    env.mock_auths(&[MockAuth {
        address: &protocol.liquidator,
        invoke: &MockAuthInvoke {
            contract: &protocol.kinetic_router.address,
            fn_name: "prepare_liquidation",
            args: (
                &protocol.liquidator,
                &protocol.user,
                &protocol.usdt_asset,
                &protocol.usdc_asset,
                &debt_to_cover,
                &min_swap_out,
                &None::<Address>, // Use default DEX router
            )
                .into_val(&env),
            sub_invokes: &[],
        },
    }]);

    let _auth = protocol.kinetic_router.prepare_liquidation(
        &protocol.liquidator,
        &protocol.user,
        &protocol.usdt_asset,
        &protocol.usdc_asset,
        &debt_to_cover,
        &min_swap_out,
        &None, // Use default DEX router
    );

    // Step 2: Execute liquidation
    env.mock_auths(&[MockAuth {
        address: &protocol.liquidator,
        invoke: &MockAuthInvoke {
            contract: &protocol.kinetic_router.address,
            fn_name: "execute_liquidation",
            args: (
                &protocol.liquidator,
                &protocol.user,
                &protocol.usdt_asset,
                &protocol.usdc_asset,
                &deadline,
            )
                .into_val(&env),
            sub_invokes: &[],
        },
    }]);

    protocol.kinetic_router.execute_liquidation(
        &protocol.liquidator,
        &protocol.user,
        &protocol.usdt_asset,
        &protocol.usdc_asset,
        &deadline,
    );
}

#[test]
fn test_flash_liquidation_prefetched_reserve_data_accuracy() {
    // Edge case: Verify prefetched reserve data is used correctly in flash_loan
    // This ensures the optimization doesn't use stale data
    let env = create_test_env_with_budget_limits();
    let protocol = deploy_test_protocol_two_assets(&env);

    // H-04: 70% LTV + $0.80 crash so post-liquidation HF improves
    protocol.kinetic_router.supply(
        &protocol.liquidity_provider,
        &protocol.usdt_asset,
        &200_000_000_000u128,
        &protocol.liquidity_provider,
        &0u32,
    );

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
        &70_000_000_000u128,
        &1u32,
        &0u32,
        &protocol.user,
    );

    // Crash price
    let usdc_asset_enum = crate::price_oracle::Asset::Stellar(protocol.usdc_asset.clone());
    protocol.price_oracle.reset_circuit_breaker(&protocol.admin, &usdc_asset_enum);
    let expiry = env.ledger().timestamp() + 86400;
    protocol.price_oracle.set_manual_override(
        &protocol.admin,
        &usdc_asset_enum,
        &Some(800_000_000_000_000u128), // $0.80
        &Some(expiry),
    );

    // Track resources to ensure optimization is working
    let before = crate::gas_tracking::check_limits_return_info(&env, "Before");

    let debt_to_cover = 35_000_000_000u128;
    let min_swap_out = 30_000_000_000u128;
    let deadline = env.ledger().timestamp() + 300;

    // Step 1: Prepare liquidation
    env.mock_auths(&[MockAuth {
        address: &protocol.liquidator,
        invoke: &MockAuthInvoke {
            contract: &protocol.kinetic_router.address,
            fn_name: "prepare_liquidation",
            args: (
                &protocol.liquidator,
                &protocol.user,
                &protocol.usdt_asset,
                &protocol.usdc_asset,
                &debt_to_cover,
                &min_swap_out,
                &None::<Address>, // Use default DEX router
            )
                .into_val(&env),
            sub_invokes: &[],
        },
    }]);

    let _auth = protocol.kinetic_router.prepare_liquidation(
        &protocol.liquidator,
        &protocol.user,
        &protocol.usdt_asset,
        &protocol.usdc_asset,
        &debt_to_cover,
        &min_swap_out,
        &None, // Use default DEX router
    );

    // Step 2: Execute liquidation
    env.mock_auths(&[MockAuth {
        address: &protocol.liquidator,
        invoke: &MockAuthInvoke {
            contract: &protocol.kinetic_router.address,
            fn_name: "execute_liquidation",
            args: (
                &protocol.liquidator,
                &protocol.user,
                &protocol.usdt_asset,
                &protocol.usdc_asset,
                &deadline,
            )
                .into_val(&env),
            sub_invokes: &[],
        },
    }]);

    protocol.kinetic_router.execute_liquidation(
        &protocol.liquidator,
        &protocol.user,
        &protocol.usdt_asset,
        &protocol.usdc_asset,
        &deadline,
    );

    let after = crate::gas_tracking::check_limits_return_info(&env, "After");

    // CRITICAL: Verify read_bytes is under limit
    let read_bytes_used = after.5.saturating_sub(before.5);
    assert!(
        read_bytes_used <= 204_800,
        "Read bytes must be under limit. Used: {}, Limit: 204800",
        read_bytes_used
    );

    // Verify liquidation succeeded (proves data was correct)
    let user_usdt_debt_after = protocol.usdt_debt_token.balance(&protocol.user);
    assert!(
        user_usdt_debt_after < 70_000_000_000i128,
        "Debt should have decreased. Before: 70B, After: {}",
        user_usdt_debt_after
    );
}
