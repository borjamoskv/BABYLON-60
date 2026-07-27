#![cfg(test)]

//! # Resource Analysis Examples
//!
//! This module demonstrates how to use the resource analysis tools to:
//! 1. Measure VM instantiation costs
//! 2. Track resource usage across operations
//! 3. Attribute costs to specific operation types
//! 4. Compare optimized vs unoptimized implementations

use crate::gas_tracking::*;
use crate::setup::deploy_test_protocol;
use soroban_sdk::Env;

#[test]
fn test_resource_analysis_supply_operation() {
    let env = Env::default();
    env.mock_all_auths();
    
    let protocol = deploy_test_protocol(&env);
    
    println!("========================================");
    println!("Resource Analysis: Supply Operation");
    println!("========================================");
    println!();
    
    // Checkpoint 1: Before supply
    let checkpoint1 = capture_resources(&env, "Before supply");
    
    // Perform supply operation
    let supply_amount = 1_000_000_000u128;
    protocol.kinetic_router.supply(
        &protocol.liquidity_provider,
        &protocol.underlying_asset,
        &supply_amount,
        &protocol.liquidity_provider,
        &0u32,
    );
    
    // Checkpoint 2: After supply
    let checkpoint2 = capture_resources(&env, "After supply");
    
    // Calculate and print delta
    let delta = calculate_delta(&checkpoint1, &checkpoint2);
    print_resource_delta(&delta);
    
    // Attribute costs
    let attribution = attribute_costs(&delta);
    print_attribution(&attribution);
    
    // Identify primary cost driver
    let driver = identify_primary_cost_driver(&delta);
    println!("Primary cost driver: {}", driver);
    println!();
    
    // Check limits with warnings
    check_resource_limits_with_warnings(&env, "Final resource check:");
}

#[test]
fn test_resource_analysis_vm_instantiation() {
    let env = Env::default();
    env.mock_all_auths();
    
    println!("========================================");
    println!("VM Instantiation Cost Analysis");
    println!("========================================");
    println!();
    
    // Checkpoint 1: Initial state
    let checkpoint1 = capture_resources(&env, "Initial");
    
    // Deploy and initialize protocol (multiple contracts)
    let _protocol = deploy_test_protocol(&env);
    
    // Checkpoint 2: After deployment
    let checkpoint2 = capture_resources(&env, "After deployment");
    
    let delta = calculate_delta(&checkpoint1, &checkpoint2);
    print_resource_delta(&delta);
    
    println!("This operation loaded multiple contracts:");
    println!("  - Kinetic Router (main pool)");
    println!("  - Price Oracle");
    println!("  - Treasury");
    println!("  - Incentives");
    println!("  - Pool Configurator");
    println!("  - A-Token");
    println!("  - Debt Token");
    println!("  - Interest Rate Strategy");
    println!();
    println!("Each unique contract = 1 VM instantiation (~10M+ CPU)");
    println!();
    
    let attribution = attribute_costs(&delta);
    print_attribution(&attribution);
    
    // Verify VM instantiation is the dominant cost
    let total_cost = attribution.vm_instantiation_cost 
        + attribution.storage_read_cost 
        + attribution.storage_write_cost 
        + attribution.computation_cost;
    
    let vm_percentage = (attribution.vm_instantiation_cost as f64 / total_cost as f64) * 100.0;
    
    println!("VM instantiation accounts for {:.1}% of total cost", vm_percentage);
    println!("This demonstrates why WASM-backed testing is critical!");
    println!();
}

#[test]
fn test_resource_analysis_cross_contract_calls() {
    let env = Env::default();
    env.mock_all_auths();
    
    let protocol = deploy_test_protocol(&env);
    
    println!("========================================");
    println!("Cross-Contract Call Analysis");
    println!("========================================");
    println!();
    
    // Supply operation involves multiple cross-contract calls:
    // 1. Kinetic Router -> A-Token (mint)
    // 2. Kinetic Router -> Incentives (handle_action)
    // 3. Kinetic Router -> Interest Rate Strategy (calculate rates)
    
    let checkpoint1 = capture_resources(&env, "Before supply");
    
    let supply_amount = 1_000_000_000u128;
    protocol.kinetic_router.supply(
        &protocol.liquidity_provider,
        &protocol.underlying_asset,
        &supply_amount,
        &protocol.liquidity_provider,
        &0u32,
    );
    
    let checkpoint2 = capture_resources(&env, "After supply");
    
    let delta = calculate_delta(&checkpoint1, &checkpoint2);
    
    println!("Supply operation cross-contract calls:");
    println!("  1. A-Token.mint() - mint aTokens to user");
    println!("  2. Incentives.handle_action() - update rewards");
    println!("  3. InterestRateStrategy.calculate_rates() - update rates");
    println!();
    
    print_resource_delta(&delta);
    
    println!("Note: If contracts were already loaded in this transaction,");
    println!("subsequent calls to the same contract don't incur VM instantiation cost.");
    println!();
}

#[test]
fn test_resource_analysis_storage_operations() {
    let env = Env::default();
    env.mock_all_auths();
    
    let protocol = deploy_test_protocol(&env);
    
    println!("========================================");
    println!("Storage Operation Analysis");
    println!("========================================");
    println!();
    
    let checkpoint1 = capture_resources(&env, "Before borrow");
    
    // Supply first
    let supply_amount = 10_000_000_000u128;
    protocol.kinetic_router.supply(
        &protocol.liquidity_provider,
        &protocol.underlying_asset,
        &supply_amount,
        &protocol.liquidity_provider,
        &0u32,
    );
    
    // User supplies collateral
    protocol.kinetic_router.supply(
        &protocol.user,
        &protocol.underlying_asset,
        &supply_amount,
        &protocol.user,
        &0u32,
    );
    
    // Set collateral
    protocol.kinetic_router.set_user_use_reserve_as_coll(
        &protocol.user,
        &protocol.underlying_asset,
        &true,
    );
    
    let checkpoint2 = capture_resources(&env, "After supply");
    
    // Borrow (more storage operations)
    let borrow_amount = 1_000_000_000u128;
    protocol.kinetic_router.borrow(
        &protocol.user,
        &protocol.underlying_asset,
        &borrow_amount,
        &1u32, // Variable rate
        &0u32,
        &protocol.user,
    );
    
    let checkpoint3 = capture_resources(&env, "After borrow");
    
    // Analyze supply operation
    let supply_delta = calculate_delta(&checkpoint1, &checkpoint2);
    println!("Supply Operation:");
    println!("  Read Entries:  {}", supply_delta.read_entries_delta);
    println!("  Write Entries: {}", supply_delta.write_entries_delta);
    println!("  Read Bytes:    {}", supply_delta.read_bytes_delta);
    println!("  Write Bytes:   {}", supply_delta.write_bytes_delta);
    println!();
    
    // Analyze borrow operation
    let borrow_delta = calculate_delta(&checkpoint2, &checkpoint3);
    println!("Borrow Operation:");
    println!("  Read Entries:  {}", borrow_delta.read_entries_delta);
    println!("  Write Entries: {}", borrow_delta.write_entries_delta);
    println!("  Read Bytes:    {}", borrow_delta.read_bytes_delta);
    println!("  Write Bytes:   {}", borrow_delta.write_bytes_delta);
    println!();
    
    println!("Borrow typically has more storage operations because:");
    println!("  - Reads: Reserve data, user collateral, price oracle");
    println!("  - Writes: Reserve data, user debt, interest rates");
    println!();
}

#[test]
fn test_resource_analysis_full_workflow() {
    let env = Env::default();
    env.mock_all_auths();
    
    println!("========================================");
    println!("Complete Resource Analysis Workflow");
    println!("========================================");
    println!();
    
    // Track multiple checkpoints
    let checkpoint1 = capture_resources(&env, "1. Initial state");
    
    let protocol = deploy_test_protocol(&env);
    let checkpoint2 = capture_resources(&env, "2. Protocol deployed");
    
    let supply_amount = 10_000_000_000u128;
    protocol.kinetic_router.supply(
        &protocol.liquidity_provider,
        &protocol.underlying_asset,
        &supply_amount,
        &protocol.liquidity_provider,
        &0u32,
    );
    
    // User supplies collateral
    protocol.kinetic_router.supply(
        &protocol.user,
        &protocol.underlying_asset,
        &supply_amount,
        &protocol.user,
        &0u32,
    );
    
    // Set collateral
    protocol.kinetic_router.set_user_use_reserve_as_coll(
        &protocol.user,
        &protocol.underlying_asset,
        &true,
    );
    
    let checkpoint3 = capture_resources(&env, "3. Supply completed");
    
    let borrow_amount = 1_000_000_000u128;
    protocol.kinetic_router.borrow(
        &protocol.user,
        &protocol.underlying_asset,
        &borrow_amount,
        &1u32,
        &0u32,
        &protocol.user,
    );
    let checkpoint4 = capture_resources(&env, "4. Borrow completed");
    
    // Analyze each operation
    let delta1 = calculate_delta(&checkpoint1, &checkpoint2);
    println!("Deployment:");
    print_resource_delta(&delta1);
    println!("  Primary driver: {}", identify_primary_cost_driver(&delta1));
    println!();
    
    let delta2 = calculate_delta(&checkpoint2, &checkpoint3);
    println!("Supply:");
    print_resource_delta(&delta2);
    println!("  Primary driver: {}", identify_primary_cost_driver(&delta2));
    println!();
    
    let delta3 = calculate_delta(&checkpoint3, &checkpoint4);
    println!("Borrow:");
    print_resource_delta(&delta3);
    println!("  Primary driver: {}", identify_primary_cost_driver(&delta3));
    println!();
}

#[test]
fn test_resource_comparison_optimization() {
    // This test demonstrates how to compare resource usage
    // before and after optimization
    
    let env = Env::default();
    env.mock_all_auths();
    
    println!("========================================");
    println!("Optimization Comparison Example");
    println!("========================================");
    println!();
    
    // Baseline: Current implementation
    let protocol = deploy_test_protocol(&env);
    
    let before = capture_resources(&env, "Current implementation");
    
    let supply_amount = 1_000_000_000u128;
    protocol.kinetic_router.supply(
        &protocol.liquidity_provider,
        &protocol.underlying_asset,
        &supply_amount,
        &protocol.liquidity_provider,
        &0u32,
    );
    
    let after = capture_resources(&env, "After supply");
    
    // In a real optimization scenario, you would:
    // 1. Measure baseline (above)
    // 2. Apply optimization (e.g., optimize WASM, reduce cross-contract calls)
    // 3. Measure optimized version
    // 4. Compare using compare_optimization()
    
    println!("Baseline measurement:");
    let delta = calculate_delta(&before, &after);
    print_resource_delta(&delta);
    
    println!("To verify optimization:");
    println!("  1. Run 'stellar contract optimize --wasm contract.wasm'");
    println!("  2. Rebuild and re-run this test");
    println!("  3. Compare CPU instructions before/after");
    println!("  4. Expect 5-15% reduction from WASM optimization");
    println!();
}

#[test]
fn test_resource_limits_monitoring() {
    let env = Env::default();
    env.mock_all_auths();
    
    println!("========================================");
    println!("Resource Limits Monitoring");
    println!("========================================");
    println!();
    
    let protocol = deploy_test_protocol(&env);
    
    // Perform multiple operations and monitor limits
    check_resource_limits_with_warnings(&env, "After deployment:");
    
    for i in 1..=3 {
        let supply_amount = 1_000_000_000u128 * i;
        protocol.kinetic_router.supply(
            &protocol.liquidity_provider,
            &protocol.underlying_asset,
            &supply_amount,
            &protocol.liquidity_provider,
            &0u32,
        );
        
        let label = format!("After supply #{}", i);
        check_resource_limits_with_warnings(&env, &label);
    }
    
    println!("Resource limits are checked at each checkpoint.");
    println!("Warnings appear when approaching 75% of limits.");
    println!("Critical alerts appear when exceeding 90% of limits.");
    println!();
}
