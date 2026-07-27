#![cfg(test)]

//! Integration tests for flash liquidation functionality.
//! 
//! Tests the router's two-step liquidation process (prepare_liquidation + execute_liquidation).

use crate::gas_tracking::{CPU_LIMIT, MEM_LIMIT, READ_BYTES_LIMIT};
use crate::price_oracle;
use crate::setup::{create_test_env_with_budget_limits, deploy_test_protocol_two_assets};
use k2_shared::WAD;
use soroban_sdk::{testutils::MockAuthInvoke, Address, IntoVal};

#[test]
fn test_flash_liquidation_atomic() {
    // Use realistic budget limits to verify the optimization works on mainnet
    let env = create_test_env_with_budget_limits();

    let protocol = deploy_test_protocol_two_assets(&env);

    let usdc_supply = 100_000_000_000u128; // 100 USDC (7 decimals)
    let usdt_liquidity = 150_000_000_000u128; // 150 USDT (7 decimals)
    let borrow_amount = 70_000_000_000u128; // 70 USDT (7 decimals)

    // Setup: LP provides USDT liquidity
    protocol.kinetic_router.supply(
        &protocol.liquidity_provider,
        &protocol.usdt_asset,
        &usdt_liquidity,
        &protocol.liquidity_provider,
        &0u32,
    );

    // User supplies USDC as collateral
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

    // User borrows USDT
    protocol.kinetic_router.borrow(
        &protocol.user,
        &protocol.usdt_asset,
        &borrow_amount,
        &1u32, // Variable rate
        &0u32,
        &protocol.user,
    );

    let account_data_after_borrow = protocol
        .kinetic_router
        .get_user_account_data(&protocol.user);
    assert!(
        account_data_after_borrow.health_factor >= WAD,
        "Health factor should be >= 1.0 (WAD). HF: {}",
        account_data_after_borrow.health_factor
    );

    // Crash USDC price to make position liquidatable
    // H-04: Use $0.80 (not $0.70) so post-liquidation HF improves with 5% bonus
    let crashed_price = 800_000_000_000_000u128; // 0.80 with 14 decimals
    let usdc_asset_enum = price_oracle::Asset::Stellar(protocol.usdc_asset.clone());

    protocol
        .price_oracle
        .reset_circuit_breaker(&protocol.admin, &usdc_asset_enum);
    let expiry = env.ledger().timestamp() + 86400; // 24 hours
    protocol.price_oracle.set_manual_override(
        &protocol.admin,
        &usdc_asset_enum,
        &Some(crashed_price),
        &Some(expiry),
    );

    let account_data_after_crash = protocol
        .kinetic_router
        .get_user_account_data(&protocol.user);
    assert!(
        account_data_after_crash.health_factor < WAD,
        "Health factor should be unhealthy after crash (< 1.0 WAD). HF: {}",
        account_data_after_crash.health_factor
    );

    let current_timestamp = env.ledger().timestamp();
    let deadline_ts = current_timestamp + 3600;
    let debt_to_cover = borrow_amount / 2;
    let min_swap_out = 0u128;

    // Get user debt before liquidation
    let user_debt_before = protocol.usdt_debt_token.balance(&protocol.user);

    // Track gas before liquidation
    let before_liquidation =
        crate::gas_tracking::check_limits_return_info(&env, "Before Liquidation");

    // Step 1: Prepare liquidation
    env.mock_auths(&[soroban_sdk::testutils::MockAuth {
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
        &protocol.usdt_asset, // debt
        &protocol.usdc_asset, // collateral
        &debt_to_cover,
        &min_swap_out,
        &None, // Use default DEX router
    );

    // Step 2: Execute liquidation
    env.mock_auths(&[soroban_sdk::testutils::MockAuth {
        address: &protocol.liquidator,
        invoke: &MockAuthInvoke {
            contract: &protocol.kinetic_router.address,
            fn_name: "execute_liquidation",
            args: (
                &protocol.liquidator,
                &protocol.user,
                &protocol.usdt_asset,
                &protocol.usdc_asset,
                &deadline_ts,
            )
                .into_val(&env),
            sub_invokes: &[],
        },
    }]);

    protocol.kinetic_router.execute_liquidation(
        &protocol.liquidator,
        &protocol.user,
        &protocol.usdt_asset, // debt
        &protocol.usdc_asset, // collateral
        &deadline_ts,
    );

    // Track gas after liquidation
    let after_liquidation =
        crate::gas_tracking::check_limits_return_info(&env, "After Flash Liquidation");

    // Calculate gas used for liquidation operation only
    let liquidation_cpu = after_liquidation.1.saturating_sub(before_liquidation.1);
    let liquidation_mem = after_liquidation.2.saturating_sub(before_liquidation.2);
    let liquidation_read_entries = after_liquidation.3.saturating_sub(before_liquidation.3);
    let liquidation_write_entries = after_liquidation.4.saturating_sub(before_liquidation.4);
    let liquidation_read_bytes = after_liquidation.5.saturating_sub(before_liquidation.5);
    let liquidation_write_bytes = after_liquidation.6.saturating_sub(before_liquidation.6);

    // Print resource usage for flash liquidation operation (informational)
    println!("\n=== Flash Liquidation Resource Usage ===");
    println!("CPU Instructions: {}", liquidation_cpu);
    println!("Memory: {}", liquidation_mem);
    println!("Read Entries: {}", liquidation_read_entries);
    println!("Write Entries: {}", liquidation_write_entries);
    println!("Read Bytes: {}", liquidation_read_bytes);
    println!("Write Bytes: {}", liquidation_write_bytes);
    println!("Limits - CPU: {}, Memory: {}, Read bytes: {}", 
        CPU_LIMIT, 
        MEM_LIMIT, 
        READ_BYTES_LIMIT);

    // Verify CPU and memory stayed within limits (primary budget concerns)
    assert!(
        liquidation_cpu <= CPU_LIMIT,
        "Flash liquidation should stay within CPU limit. Used: {}, Limit: {}",
        liquidation_cpu, CPU_LIMIT
    );
    assert!(
        liquidation_mem <= MEM_LIMIT,
        "Flash liquidation should stay within memory limit. Used: {}, Limit: {}",
        liquidation_mem, MEM_LIMIT
    );

    // Verify read_bytes is within limit (router's flash_liquidation should be optimized)
    assert!(
        liquidation_read_bytes <= READ_BYTES_LIMIT,
        "Flash liquidation read bytes should be under limit. Used: {}, Limit: {}",
        liquidation_read_bytes, READ_BYTES_LIMIT
    );

    // Verify liquidation succeeded by checking user's debt decreased
    let account_data_after = protocol
        .kinetic_router
        .get_user_account_data(&protocol.user);
    
    assert!(
        account_data_after.total_debt_base < account_data_after_crash.total_debt_base,
        "User's debt should decrease after liquidation. Before: {}, After: {}",
        account_data_after_crash.total_debt_base,
        account_data_after.total_debt_base
    );
    
    // Verify debt was repaid
    let user_debt_after = protocol.usdt_debt_token.balance(&protocol.user);
    assert!(
        user_debt_after < user_debt_before,
        "User's debt token balance should decrease. Before: {}, After: {}",
        user_debt_before, user_debt_after
    );

}

#[test]
fn test_flash_liquidation_rejects_healthy_position() {
    let env = crate::setup::create_test_env_with_budget_limits();
    let protocol = deploy_test_protocol_two_assets(&env);

    let usdc_supply = 100_000_000_000u128;
    let usdt_liquidity = 150_000_000_000u128;
    let borrow_amount = 50_000_000_000u128; // Lower borrow to stay healthy

    // Setup position
    protocol.kinetic_router.supply(
        &protocol.liquidity_provider,
        &protocol.usdt_asset,
        &usdt_liquidity,
        &protocol.liquidity_provider,
        &0u32,
    );

    protocol.kinetic_router.supply(
        &protocol.user,
        &protocol.usdc_asset,
        &usdc_supply,
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

    // Verify position is healthy
    let account_data = protocol.kinetic_router.get_user_account_data(&protocol.user);
    assert!(
        account_data.health_factor >= WAD,
        "Position should be healthy"
    );

    // Attempt liquidation should fail (healthy position)
    let result = protocol.kinetic_router.try_prepare_liquidation(
        &protocol.liquidator,
        &protocol.user,
        &protocol.usdt_asset,
        &protocol.usdc_asset,
        &(borrow_amount / 2),
        &0u128,
        &None, // Use default DEX router
    );

    assert!(
        result.is_err(),
        "Prepare liquidation should fail for healthy position"
    );
}

#[test]
fn test_flash_liquidation_legitimate_liquidation() {
    // Test that legitimate liquidation works with two-step process
    let env = crate::setup::create_test_env_with_budget_limits();
    let protocol = deploy_test_protocol_two_assets(&env);

    // Seed liquidity and borrow
    let usdc_supply = 100_000_000_000_000u128; // 10,000,000 USDC (7 decimals)
    let usdt_liquidity = 100_000_000_000_000u128; // 10,000,000 USDT (7 decimals)
    let borrow_amount = 80_000_000_000_000u128; // 8,000,000 USDT (7 decimals)

    protocol.kinetic_router.supply(
        &protocol.liquidity_provider,
        &protocol.usdt_asset,
        &usdt_liquidity,
        &protocol.liquidity_provider,
        &0u32,
    );
    protocol.kinetic_router.supply(
        &protocol.user,
        &protocol.usdc_asset,
        &usdc_supply,
        &protocol.user,
        &0u32,
    );
    protocol
        .kinetic_router
        .set_user_use_reserve_as_coll(&protocol.user, &protocol.usdc_asset, &true);
    protocol.kinetic_router.borrow(
        &protocol.user,
        &protocol.usdt_asset,
        &borrow_amount,
        &1u32,
        &0u32,
        &protocol.user,
    );

    // Make the position liquidatable
    let crashed_price = 900_000_000_000_000u128; // 0.90 with 14 decimals
    let usdc_asset_enum = price_oracle::Asset::Stellar(protocol.usdc_asset.clone());
    protocol
        .price_oracle
        .reset_circuit_breaker(&protocol.admin, &usdc_asset_enum);
    let expiry = env.ledger().timestamp() + 86400;
    protocol.price_oracle.set_manual_override(
        &protocol.admin,
        &usdc_asset_enum,
        &Some(crashed_price),
        &Some(expiry),
    );
    let account_data_after_crash = protocol
        .kinetic_router
        .get_user_account_data(&protocol.user);
    assert!(
        account_data_after_crash.health_factor < WAD,
        "Position must be unhealthy for liquidation"
    );

    let debt_to_cover = borrow_amount / 20; // 5% slice
    let current_timestamp = env.ledger().timestamp();
    let deadline_ts = current_timestamp + 3600;

    // Step 1: Prepare liquidation (calculates collateral_to_seize internally)
    env.mock_auths(&[soroban_sdk::testutils::MockAuth {
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
                &0u128, // min_swap_out
                &None::<Address>, // Use default DEX router
            )
                .into_val(&env),
            sub_invokes: &[],
        },
    }]);

    let legit_result = protocol.kinetic_router.try_prepare_liquidation(
        &protocol.liquidator,
        &protocol.user,
        &protocol.usdt_asset,
        &protocol.usdc_asset,
        &debt_to_cover,
        &0u128,
        &None, // Use default DEX router
    );

    assert!(
        legit_result.is_ok(),
        "Legitimate prepare_liquidation should succeed"
    );

    // Step 2: Execute liquidation
    env.mock_auths(&[soroban_sdk::testutils::MockAuth {
        address: &protocol.liquidator,
        invoke: &MockAuthInvoke {
            contract: &protocol.kinetic_router.address,
            fn_name: "execute_liquidation",
            args: (
                &protocol.liquidator,
                &protocol.user,
                &protocol.usdt_asset,
                &protocol.usdc_asset,
                &deadline_ts,
            )
                .into_val(&env),
            sub_invokes: &[],
        },
    }]);

    let execute_result = protocol.kinetic_router.try_execute_liquidation(
        &protocol.liquidator,
        &protocol.user,
        &protocol.usdt_asset,
        &protocol.usdc_asset,
        &deadline_ts,
    );

    assert!(
        execute_result.is_ok(),
        "Legitimate execute_liquidation should succeed"
    );
}
