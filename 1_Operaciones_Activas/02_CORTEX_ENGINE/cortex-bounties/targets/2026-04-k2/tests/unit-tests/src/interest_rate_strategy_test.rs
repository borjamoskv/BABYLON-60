#![cfg(test)]
use crate::interest_rate_strategy;
use k2_shared::*;
use soroban_sdk::{testutils::Address as _, Address, Env};

fn create_test_env() -> Env {
    let env = Env::default();
    env.mock_all_auths();
    env
}

fn create_test_addresses(env: &Env) -> (Address, Address, Address) {
    let admin = Address::generate(env);
    let user1 = Address::generate(env);
    let user2 = Address::generate(env);
    (admin, user1, user2)
}

fn initialize_contract(env: &Env, admin: &Address) -> Address {
    let contract_id = env.register(interest_rate_strategy::WASM, ());
    let client = interest_rate_strategy::Client::new(env, &contract_id);

    client.initialize(
        admin,
        &(1_000_000_000_000_000_000u128),
        &(4_000_000_000_000_000_000u128),
        &(60_000_000_000_000_000_000u128),
        &(800_000_000_000_000_000_000_000_000u128),
    );

    contract_id
}

#[test]
fn test_initialization_success() {
    let env = create_test_env();
    let (admin, _, _) = create_test_addresses(&env);
    let contract_id = initialize_contract(&env, &admin);

    let client = interest_rate_strategy::Client::new(&env, &contract_id);

    assert_eq!(client.admin(), admin);

    assert_eq!(
        client.get_base_variable_borrow_rate(),
        1_000_000_000_000_000_000u128
    );
    assert_eq!(
        client.get_variable_rate_slope1(),
        4_000_000_000_000_000_000u128
    );
    assert_eq!(
        client.get_variable_rate_slope2(),
        60_000_000_000_000_000_000u128
    );
    assert_eq!(
        client.get_optimal_utilization_rate(),
        800_000_000_000_000_000_000_000_000u128
    );
}

#[test]
#[should_panic(expected = "Error(Contract, #27)")]
fn test_double_initialization_fails() {
    let env = create_test_env();
    let (admin, _, _) = create_test_addresses(&env);
    let contract_id = initialize_contract(&env, &admin);

    let client = interest_rate_strategy::Client::new(&env, &contract_id);

    client.initialize(
        &admin,
        &(1_000_000_000_000_000_000u128),
        &(4_000_000_000_000_000_000u128),
        &(60_000_000_000_000_000_000u128),
        &(800_000_000_000_000_000_000_000_000u128),
    );
}

#[test]
#[should_panic(expected = "Error(Contract, #1)")]
fn test_initialization_invalid_optimal_utilization() {
    let env = create_test_env();
    let (admin, _, _) = create_test_addresses(&env);
    let contract_id = env.register(interest_rate_strategy::WASM, ());
    let client = interest_rate_strategy::Client::new(&env, &contract_id);

    client.initialize(
        &admin,
        &(1_000_000_000_000_000_000u128),
        &(4_000_000_000_000_000_000u128),
        &(60_000_000_000_000_000_000u128),
        &(1_100_000_000_000_000_000_000_000_000u128), // 110% > 100%
    );
}

#[test]
#[should_panic(expected = "Error(Contract, #1)")]
fn test_initialization_invalid_base_rate() {
    let env = create_test_env();
    let (admin, _, _) = create_test_addresses(&env);
    let contract_id = env.register(interest_rate_strategy::WASM, ());
    let client = interest_rate_strategy::Client::new(&env, &contract_id);

    // Base rate > 1000% APY (10 * RAY)
    client.initialize(
        &admin,
        &(11_000_000_000_000_000_000_000_000_000u128), // 1100% > 1000%
        &(4_000_000_000_000_000_000u128),
        &(60_000_000_000_000_000_000u128),
        &(800_000_000_000_000_000_000_000_000u128),
    );
}

#[test]
#[should_panic(expected = "Error(Contract, #1)")]
fn test_initialization_invalid_slope1() {
    let env = create_test_env();
    let (admin, _, _) = create_test_addresses(&env);
    let contract_id = env.register(interest_rate_strategy::WASM, ());
    let client = interest_rate_strategy::Client::new(&env, &contract_id);

    // Slope1 > 1000% APY (10 * RAY)
    client.initialize(
        &admin,
        &(1_000_000_000_000_000_000u128),
        &(11_000_000_000_000_000_000_000_000_000u128), // 1100% > 1000%
        &(60_000_000_000_000_000_000u128),
        &(800_000_000_000_000_000_000_000_000u128),
    );
}

#[test]
#[should_panic(expected = "Error(Contract, #1)")]
fn test_initialization_invalid_slope2() {
    let env = create_test_env();
    let (admin, _, _) = create_test_addresses(&env);
    let contract_id = env.register(interest_rate_strategy::WASM, ());
    let client = interest_rate_strategy::Client::new(&env, &contract_id);

    // Slope2 > 1000% APY (10 * RAY)
    client.initialize(
        &admin,
        &(1_000_000_000_000_000_000u128),
        &(4_000_000_000_000_000_000u128),
        &(11_000_000_000_000_000_000_000_000_000u128), // 1100% > 1000%
        &(800_000_000_000_000_000_000_000_000u128),
    );
}

// ============================================================================
// INTEREST RATE CALCULATION TESTS
// ============================================================================

#[test]
fn test_calculate_rates_zero_utilization() {
    let env = create_test_env();
    let (admin, _, _) = create_test_addresses(&env);
    let contract_id = initialize_contract(&env, &admin);
    let client = interest_rate_strategy::Client::new(&env, &contract_id);

    let asset = Address::generate(&env);

    // Set asset-specific parameters
    client.set_asset_interest_rate_params(
        &admin,
        &asset,
        &(1_000_000_000_000_000_000u128),           // 1% base rate
        &(4_000_000_000_000_000_000u128),           // 4% slope1
        &(60_000_000_000_000_000_000u128),          // 60% slope2
        &(800_000_000_000_000_000_000_000_000u128), // 80% optimal
    );

    // Zero utilization: no debt
    let rates = client.calculate_interest_rates(
        &asset,
        &(1_000_000_000_000_000_000u128), // 1000 tokens available
        &0u128,                           // 0 debt
        &(1_000u128),                     // 10% reserve factor
    );

    // Variable borrow rate should equal base rate (1%)
    assert_eq!(rates.variable_borrow_rate, 1_000_000_000_000_000_000u128);
    // Liquidity rate should be 0 (no utilization)
    assert_eq!(rates.liquidity_rate, 0u128);
}

#[test]
fn test_calculate_rates_below_optimal_utilization() {
    let env = create_test_env();
    let (admin, _, _) = create_test_addresses(&env);
    let contract_id = initialize_contract(&env, &admin);
    let client = interest_rate_strategy::Client::new(&env, &contract_id);

    let asset = Address::generate(&env);

    // Set asset-specific parameters
    client.set_asset_interest_rate_params(
        &admin,
        &asset,
        &(1_000_000_000_000_000_000u128),           // 1% base rate
        &(4_000_000_000_000_000_000u128),           // 4% slope1
        &(60_000_000_000_000_000_000u128),          // 60% slope2
        &(800_000_000_000_000_000_000_000_000u128), // 80% optimal
    );

    // 40% utilization (below 80% optimal)
    let available_liquidity = 6_000_000_000_000_000_000u128; // 600 tokens
    let total_debt = 4_000_000_000_000_000_000u128; // 400 tokens

    let rates = client.calculate_interest_rates(
        &asset,
        &available_liquidity,
        &total_debt,
        &(1_000u128), // 10% reserve factor
    );

    // Variable borrow rate = base + slope1 * (utilization / optimal)
    // = 1% + 4% * (40% / 80%) = 1% + 4% * 0.5 = 1% + 2% = 3%
    let expected_variable_rate =
        1_000_000_000_000_000_000u128 + (4_000_000_000_000_000_000u128 / 2); // 3%
    assert_eq!(rates.variable_borrow_rate, expected_variable_rate);

    // Test liquidity rate calculation using the EXACT same method as the contract
    // liquidity_rate = ray_mul(ray_mul(variable_borrow_rate, utilization_rate), (RAY - reserve_factor_ray))
    let utilization_rate_ray = 400_000_000_000_000_000_000_000_000u128; // 40% in RAY
                                                                        // reserve_factor_ray = ray_div(ray_mul(reserve_factor, RAY), 10000)
    let reserve_factor_ray =
        k2_shared::ray_div(&env, k2_shared::ray_mul(&env, 1_000u128, RAY).unwrap(), 10000).unwrap();

    // Calculate expected using the same ray_mul approach as the contract
    let expected_liquidity_rate = k2_shared::ray_mul(
        &env,
        k2_shared::ray_mul(&env, expected_variable_rate, utilization_rate_ray).unwrap(),
        RAY - reserve_factor_ray,
    ).unwrap();

    // Test that the actual result matches our calculation
    assert_eq!(rates.liquidity_rate, expected_liquidity_rate);
}

#[test]
fn test_calculate_rates_at_optimal_utilization() {
    let env = create_test_env();
    let (admin, _, _) = create_test_addresses(&env);
    let contract_id = initialize_contract(&env, &admin);
    let client = interest_rate_strategy::Client::new(&env, &contract_id);

    let asset = Address::generate(&env);

    // Set asset-specific parameters
    client.set_asset_interest_rate_params(
        &admin,
        &asset,
        &(1_000_000_000_000_000_000u128),           // 1% base rate
        &(4_000_000_000_000_000_000u128),           // 4% slope1
        &(60_000_000_000_000_000_000u128),          // 60% slope2
        &(800_000_000_000_000_000_000_000_000u128), // 80% optimal
    );

    // 80% utilization (at optimal)
    let available_liquidity = 2_000_000_000_000_000_000u128; // 200 tokens
    let total_debt = 8_000_000_000_000_000_000u128; // 800 tokens

    let rates = client.calculate_interest_rates(
        &asset,
        &available_liquidity,
        &total_debt,
        &(1_000u128), // 10% reserve factor
    );

    // Variable borrow rate = base + slope1 = 1% + 4% = 5%
    let expected_variable_rate = 1_000_000_000_000_000_000u128 + 4_000_000_000_000_000_000u128;
    assert_eq!(rates.variable_borrow_rate, expected_variable_rate);

    // Test liquidity rate using the EXACT same calculation as the contract
    let utilization_rate_ray = 800_000_000_000_000_000_000_000_000u128; // 80% in RAY
    let reserve_factor_ray =
        k2_shared::ray_div(&env, k2_shared::ray_mul(&env, 1_000u128, RAY).unwrap(), 10000).unwrap();
    let expected_liquidity_rate = k2_shared::ray_mul(
        &env,
        k2_shared::ray_mul(&env, expected_variable_rate, utilization_rate_ray).unwrap(),
        RAY - reserve_factor_ray,
    ).unwrap();
    assert_eq!(rates.liquidity_rate, expected_liquidity_rate);
}

#[test]
fn test_calculate_rates_above_optimal_utilization() {
    let env = create_test_env();
    let (admin, _, _) = create_test_addresses(&env);
    let contract_id = initialize_contract(&env, &admin);
    let client = interest_rate_strategy::Client::new(&env, &contract_id);

    let asset = Address::generate(&env);

    // Set asset-specific parameters
    client.set_asset_interest_rate_params(
        &admin,
        &asset,
        &(1_000_000_000_000_000_000u128),           // 1% base rate
        &(4_000_000_000_000_000_000u128),           // 4% slope1
        &(60_000_000_000_000_000_000u128),          // 60% slope2
        &(800_000_000_000_000_000_000_000_000u128), // 80% optimal
    );

    // 90% utilization (above 80% optimal)
    let available_liquidity = 1_000_000_000_000_000_000u128; // 100 tokens
    let total_debt = 9_000_000_000_000_000_000u128; // 900 tokens

    let rates = client.calculate_interest_rates(
        &asset,
        &available_liquidity,
        &total_debt,
        &(1_000u128), // 10% reserve factor
    );

    // Variable borrow rate = base + slope1 + slope2 * excess_ratio
    // excess_ratio = (90% - 80%) / (100% - 80%) = 10% / 20% = 0.5
    // = 1% + 4% + 60% * 0.5 = 1% + 4% + 30% = 35%
    let expected_variable_rate = 1_000_000_000_000_000_000u128
        + 4_000_000_000_000_000_000u128
        + (60_000_000_000_000_000_000u128 / 2); // 35%
    assert_eq!(rates.variable_borrow_rate, expected_variable_rate);

    // Test liquidity rate using the EXACT same calculation as the contract
    let utilization_rate_ray = 900_000_000_000_000_000_000_000_000u128; // 90% in RAY
    let reserve_factor_ray =
        k2_shared::ray_div(&env, k2_shared::ray_mul(&env, 1_000u128, RAY).unwrap(), 10000).unwrap();
    let expected_liquidity_rate = k2_shared::ray_mul(
        &env,
        k2_shared::ray_mul(&env, expected_variable_rate, utilization_rate_ray).unwrap(),
        RAY - reserve_factor_ray,
    ).unwrap();
    assert_eq!(rates.liquidity_rate, expected_liquidity_rate);
}

#[test]
fn test_calculate_rates_maximum_utilization() {
    let env = create_test_env();
    let (admin, _, _) = create_test_addresses(&env);
    let contract_id = initialize_contract(&env, &admin);
    let client = interest_rate_strategy::Client::new(&env, &contract_id);

    let asset = Address::generate(&env);

    // Set asset-specific parameters
    client.set_asset_interest_rate_params(
        &admin,
        &asset,
        &(1_000_000_000_000_000_000u128),           // 1% base rate
        &(4_000_000_000_000_000_000u128),           // 4% slope1
        &(60_000_000_000_000_000_000u128),          // 60% slope2
        &(800_000_000_000_000_000_000_000_000u128), // 80% optimal
    );

    // 100% utilization (maximum)
    let available_liquidity = 0u128; // 0 tokens available
    let total_debt = 10_000_000_000_000_000_000u128; // 1000 tokens

    let rates = client.calculate_interest_rates(
        &asset,
        &available_liquidity,
        &total_debt,
        &(1_000u128), // 10% reserve factor
    );

    // Variable borrow rate = base + slope1 + slope2 = 1% + 4% + 60% = 65%
    let expected_variable_rate = 1_000_000_000_000_000_000u128
        + 4_000_000_000_000_000_000u128
        + 60_000_000_000_000_000_000u128; // 65%
    assert_eq!(rates.variable_borrow_rate, expected_variable_rate);

    // Test liquidity rate using the EXACT same calculation as the contract
    let utilization_rate_ray = RAY; // 100% in RAY
    let reserve_factor_ray =
        k2_shared::ray_div(&env, k2_shared::ray_mul(&env, 1_000u128, RAY).unwrap(), 10000).unwrap();
    let expected_liquidity_rate = k2_shared::ray_mul(
        &env,
        k2_shared::ray_mul(&env, expected_variable_rate, utilization_rate_ray).unwrap(),
        RAY - reserve_factor_ray,
    ).unwrap();
    assert_eq!(rates.liquidity_rate, expected_liquidity_rate);
}

// ============================================================================
// EDGE CASE TESTS
// ============================================================================

#[test]
fn test_calculate_rates_zero_available_liquidity() {
    let env = create_test_env();
    let (admin, _, _) = create_test_addresses(&env);
    let contract_id = initialize_contract(&env, &admin);
    let client = interest_rate_strategy::Client::new(&env, &contract_id);

    let asset = Address::generate(&env);

    // Set asset-specific parameters
    client.set_asset_interest_rate_params(
        &admin,
        &asset,
        &(1_000_000_000_000_000_000u128),           // 1% base rate
        &(4_000_000_000_000_000_000u128),           // 4% slope1
        &(60_000_000_000_000_000_000u128),          // 60% slope2
        &(800_000_000_000_000_000_000_000_000u128), // 80% optimal
    );

    // Edge case: zero available liquidity, some debt
    let rates = client.calculate_interest_rates(
        &asset,
        &0u128,                           // 0 available liquidity
        &(1_000_000_000_000_000_000u128), // 1 token debt
        &(1_000u128),                     // 10% reserve factor
    );

    // With zero available liquidity, utilization should be 100% (total_debt / (0 + total_debt))
    // This should trigger the maximum rate calculation: base + slope1 + slope2
    let expected_max_rate = 1_000_000_000_000_000_000u128
        + 4_000_000_000_000_000_000u128
        + 60_000_000_000_000_000_000u128; // 65%
    assert_eq!(rates.variable_borrow_rate, expected_max_rate);

    // Liquidity rate should be calculated with 100% utilization
    let utilization_rate_ray = RAY; // 100% in RAY
    let reserve_factor_ray =
        k2_shared::ray_div(&env, k2_shared::ray_mul(&env, 1_000u128, RAY).unwrap(), 10000).unwrap();
    let expected_liquidity_rate = k2_shared::ray_mul(
        &env,
        k2_shared::ray_mul(&env, expected_max_rate, utilization_rate_ray).unwrap(),
        RAY - reserve_factor_ray,
    ).unwrap();
    assert_eq!(rates.liquidity_rate, expected_liquidity_rate);
}

#[test]
fn test_calculate_rates_zero_total_liquidity() {
    let env = create_test_env();
    let (admin, _, _) = create_test_addresses(&env);
    let contract_id = initialize_contract(&env, &admin);
    let client = interest_rate_strategy::Client::new(&env, &contract_id);

    let asset = Address::generate(&env);

    // Set asset-specific parameters
    client.set_asset_interest_rate_params(
        &admin,
        &asset,
        &(1_000_000_000_000_000_000u128),           // 1% base rate
        &(4_000_000_000_000_000_000u128),           // 4% slope1
        &(60_000_000_000_000_000_000u128),          // 60% slope2
        &(800_000_000_000_000_000_000_000_000u128), // 80% optimal
    );

    // Edge case: zero total liquidity (available + debt = 0)
    let rates = client.calculate_interest_rates(
        &asset,
        &0u128,       // 0 available liquidity
        &0u128,       // 0 debt
        &(1_000u128), // 10% reserve factor
    );

    // Should return base rate and zero liquidity rate
    assert_eq!(rates.variable_borrow_rate, 1_000_000_000_000_000_000u128); // Base rate
    assert_eq!(rates.liquidity_rate, 0u128);
}

#[test]
#[should_panic(expected = "Error(Contract, #1)")]
fn test_calculate_rates_zero_optimal_utilization() {
    let env = create_test_env();
    let (admin, _, _) = create_test_addresses(&env);
    let contract_id = initialize_contract(&env, &admin);
    let client = interest_rate_strategy::Client::new(&env, &contract_id);

    let asset = Address::generate(&env);

    // Setting optimal utilization to 0 should fail validation
    // This prevents degenerate curves where optimal = 0 collapses to single branch
    client.set_asset_interest_rate_params(
        &admin,
        &asset,
        &(1_000_000_000_000_000_000u128),  // 1% base rate
        &(4_000_000_000_000_000_000u128),  // 4% slope1
        &(60_000_000_000_000_000_000u128), // 60% slope2
        &0u128,                            // 0% optimal utilization - INVALID
    );
}

// ============================================================================
// ADMIN FUNCTION TESTS
// ============================================================================

#[test]
fn test_update_interest_rate_params_success() {
    let env = create_test_env();
    let (admin, _, _) = create_test_addresses(&env);
    let contract_id = initialize_contract(&env, &admin);
    let client = interest_rate_strategy::Client::new(&env, &contract_id);

    // Update parameters
    client.update_interest_rate_params(
        &admin,
        &(2_000_000_000_000_000_000u128),           // 2% base rate
        &(5_000_000_000_000_000_000u128),           // 5% slope1
        &(70_000_000_000_000_000_000u128),          // 70% slope2
        &(750_000_000_000_000_000_000_000_000u128), // 75% optimal
    );

    // Verify parameters were updated
    assert_eq!(
        client.get_base_variable_borrow_rate(),
        2_000_000_000_000_000_000u128
    );
    assert_eq!(
        client.get_variable_rate_slope1(),
        5_000_000_000_000_000_000u128
    );
    assert_eq!(
        client.get_variable_rate_slope2(),
        70_000_000_000_000_000_000u128
    );
    assert_eq!(
        client.get_optimal_utilization_rate(),
        750_000_000_000_000_000_000_000_000u128
    );
}

#[test]
#[should_panic(expected = "Error(Contract, #26)")]
fn test_update_interest_rate_params_unauthorized() {
    let env = create_test_env();
    let (admin, user1, _) = create_test_addresses(&env);
    let contract_id = initialize_contract(&env, &admin);
    let client = interest_rate_strategy::Client::new(&env, &contract_id);

    // Try to update parameters as non-admin
    client.update_interest_rate_params(
        &user1, // Not admin
        &(2_000_000_000_000_000_000u128),
        &(5_000_000_000_000_000_000u128),
        &(70_000_000_000_000_000_000u128),
        &(750_000_000_000_000_000_000_000_000u128),
    );
}

// Removed old single-step admin transfer tests
// These are now covered by the two-step admin transfer tests below

#[test]
fn test_two_step_admin_transfer_success() {
    let env = create_test_env();
    let (admin, user1, _) = create_test_addresses(&env);
    let contract_id = initialize_contract(&env, &admin);
    let client = interest_rate_strategy::Client::new(&env, &contract_id);

    // Step 1: Propose new admin
    client.propose_admin(&admin, &user1);
    
    // Verify pending admin
    let pending = client.get_pending_admin();
    assert_eq!(pending, user1);
    
    // Verify current admin unchanged
    assert_eq!(client.admin(), admin);
    
    // Step 2: Accept admin
    client.accept_admin(&user1);
    
    // Verify admin transferred
    assert_eq!(client.admin(), user1);
    
    // Verify new admin can update parameters
    client.update_interest_rate_params(
        &user1,
        &(3_000_000_000_000_000_000u128),
        &(6_000_000_000_000_000_000u128),
        &(80_000_000_000_000_000_000u128),
        &(800_000_000_000_000_000_000_000_000u128),
    );
    
    assert_eq!(
        client.get_base_variable_borrow_rate(),
        3_000_000_000_000_000_000u128
    );
}

#[test]
#[should_panic(expected = "Error(Contract, #26)")]
fn test_propose_admin_unauthorized() {
    let env = create_test_env();
    let (admin, user1, user2) = create_test_addresses(&env);
    let contract_id = initialize_contract(&env, &admin);
    let client = interest_rate_strategy::Client::new(&env, &contract_id);

    // Try to propose admin as non-admin
    client.propose_admin(&user1, &user2);
}

#[test]
#[should_panic(expected = "Error(Contract, #52)")]
fn test_accept_admin_invalid_pending() {
    let env = create_test_env();
    let (admin, user1, user2) = create_test_addresses(&env);
    let contract_id = initialize_contract(&env, &admin);
    let client = interest_rate_strategy::Client::new(&env, &contract_id);

    // Propose user1 as admin
    client.propose_admin(&admin, &user1);
    
    // Try to accept with wrong address
    client.accept_admin(&user2);
}

#[test]
fn test_cancel_admin_proposal() {
    let env = create_test_env();
    let (admin, user1, _) = create_test_addresses(&env);
    let contract_id = initialize_contract(&env, &admin);
    let client = interest_rate_strategy::Client::new(&env, &contract_id);

    // Propose admin
    client.propose_admin(&admin, &user1);
    
    // Cancel proposal
    client.cancel_admin_proposal(&admin);
    
    // Verify admin unchanged
    assert_eq!(client.admin(), admin);
    
    // Verify no pending admin
    let result = client.try_get_pending_admin();
    assert!(result.is_err());
}

#[test]
#[should_panic(expected = "Error(Contract, #51)")]
fn test_accept_admin_without_proposal() {
    let env = create_test_env();
    let (admin, user1, _) = create_test_addresses(&env);
    let contract_id = initialize_contract(&env, &admin);
    let client = interest_rate_strategy::Client::new(&env, &contract_id);

    // Try to accept without proposal
    client.accept_admin(&user1);
}

// ============================================================================
// ASSET-SPECIFIC PARAMETER TESTS
// ============================================================================

#[test]
fn test_set_asset_interest_rate_params_success() {
    let env = create_test_env();
    let (admin, _, _) = create_test_addresses(&env);
    let contract_id = initialize_contract(&env, &admin);
    let client = interest_rate_strategy::Client::new(&env, &contract_id);

    let asset = Address::generate(&env);

    // Set asset-specific parameters
    client.set_asset_interest_rate_params(
        &admin,
        &asset,
        &(3_000_000_000_000_000_000u128),           // 3% base rate
        &(6_000_000_000_000_000_000u128),           // 6% slope1
        &(80_000_000_000_000_000_000u128),          // 80% slope2
        &(850_000_000_000_000_000_000_000_000u128), // 85% optimal
    );

    // Verify asset-specific parameters were set
    let params = client.get_asset_interest_rate_params(&asset).unwrap();
    assert_eq!(
        params.base_variable_borrow_rate,
        3_000_000_000_000_000_000u128
    );
    assert_eq!(params.variable_rate_slope1, 6_000_000_000_000_000_000u128);
    assert_eq!(params.variable_rate_slope2, 80_000_000_000_000_000_000u128);
    assert_eq!(
        params.optimal_utilization_rate,
        850_000_000_000_000_000_000_000_000u128
    );
}

#[test]
#[should_panic(expected = "Error(Contract, #26)")]
fn test_set_asset_interest_rate_params_unauthorized() {
    let env = create_test_env();
    let (admin, user1, _) = create_test_addresses(&env);
    let contract_id = initialize_contract(&env, &admin);
    let client = interest_rate_strategy::Client::new(&env, &contract_id);

    let asset = Address::generate(&env);

    // Try to set asset-specific parameters as non-admin
    client.set_asset_interest_rate_params(
        &user1, // Not admin
        &asset,
        &(3_000_000_000_000_000_000u128),
        &(6_000_000_000_000_000_000u128),
        &(80_000_000_000_000_000_000u128),
        &(850_000_000_000_000_000_000_000_000u128),
    );
}

#[test]
fn test_get_asset_interest_rate_params_none() {
    let env = create_test_env();
    let (admin, _, _) = create_test_addresses(&env);
    let contract_id = initialize_contract(&env, &admin);
    let client = interest_rate_strategy::Client::new(&env, &contract_id);

    let asset = Address::generate(&env);

    // Get parameters for asset that hasn't been set
    let params = client.get_asset_interest_rate_params(&asset);
    assert!(params.is_none());
}

#[test]
fn test_calculate_rates_with_asset_specific_params() {
    let env = create_test_env();
    let (admin, _, _) = create_test_addresses(&env);
    let contract_id = initialize_contract(&env, &admin);
    let client = interest_rate_strategy::Client::new(&env, &contract_id);

    let asset = Address::generate(&env);

    // Set asset-specific parameters different from global
    client.set_asset_interest_rate_params(
        &admin,
        &asset,
        &(5_000_000_000_000_000_000u128), // 5% base rate (vs 1% global)
        &(8_000_000_000_000_000_000u128), // 8% slope1 (vs 4% global)
        &(100_000_000_000_000_000_000u128), // 100% slope2 (vs 60% global)
        &(700_000_000_000_000_000_000_000_000u128), // 70% optimal (vs 80% global)
    );

    // Calculate rates - should use asset-specific parameters
    let rates = client.calculate_interest_rates(
        &asset,
        &(3_000_000_000_000_000_000u128), // 300 tokens available
        &(7_000_000_000_000_000_000u128), // 700 tokens debt (70% utilization)
        &(1_000u128),                     // 10% reserve factor
    );

    // At 70% utilization (optimal), rate should be base + slope1 = 5% + 8% = 13%
    let expected_variable_rate = 5_000_000_000_000_000_000u128 + 8_000_000_000_000_000_000u128;
    assert_eq!(rates.variable_borrow_rate, expected_variable_rate);
}

// ============================================================================
// UTILITY FUNCTION TESTS
// ============================================================================

// ============================================================================
// PRECISION AND OVERFLOW TESTS
// ============================================================================

#[test]
fn test_high_precision_calculations() {
    let env = create_test_env();
    let (admin, _, _) = create_test_addresses(&env);
    let contract_id = initialize_contract(&env, &admin);
    let client = interest_rate_strategy::Client::new(&env, &contract_id);

    let asset = Address::generate(&env);

    // Set asset-specific parameters with high precision
    client.set_asset_interest_rate_params(
        &admin,
        &asset,
        &(1_000_000_000_000_000_000u128),           // 1% base rate
        &(4_000_000_000_000_000_000u128),           // 4% slope1
        &(60_000_000_000_000_000_000u128),          // 60% slope2
        &(800_000_000_000_000_000_000_000_000u128), // 80% optimal
    );

    // Test with very large amounts
    let large_amount = 1_000_000_000_000_000_000_000_000_000u128; // 1M tokens
    let rates = client.calculate_interest_rates(
        &asset,
        &large_amount,
        &(large_amount / 2), // 50% utilization
        &(1_000u128),        // 10% reserve factor
    );

    // Test that large amounts are handled correctly with 50% utilization
    // The contract calculates utilization as: total_debt / (available_liquidity + total_debt)
    // With large_amount available and large_amount/2 debt: (large_amount/2) / (large_amount + large_amount/2) = (large_amount/2) / (3*large_amount/2) = 1/3 = 33.33%
    let total_liquidity = large_amount + (large_amount / 2); // available + debt
    let actual_utilization_rate = k2_shared::ray_div(&env, large_amount / 2, total_liquidity).unwrap();

    // Expected rate should be: base + slope1 * (33.33% / 80%) = 1% + 4% * 0.4167 = 1% + 1.67% = 2.67%
    let optimal_utilization_ray = 800_000_000_000_000_000_000_000_000u128; // 80% in RAY
    let utilization_ratio =
        k2_shared::ray_div(&env, actual_utilization_rate, optimal_utilization_ray).unwrap();
    let expected_variable_rate = 1_000_000_000_000_000_000u128
        + k2_shared::ray_mul(&env, 4_000_000_000_000_000_000u128, utilization_ratio).unwrap();

    assert_eq!(rates.variable_borrow_rate, expected_variable_rate);

    // Test liquidity rate using the EXACT same calculation as the contract
    // reserve_factor_ray = ray_div(ray_mul(reserve_factor, RAY), 10000)
    let reserve_factor_ray =
        k2_shared::ray_div(&env, k2_shared::ray_mul(&env, 1_000u128, RAY).unwrap(), 10000).unwrap();
    let expected_liquidity_rate = k2_shared::ray_mul(
        &env,
        k2_shared::ray_mul(&env, expected_variable_rate, actual_utilization_rate).unwrap(),
        RAY - reserve_factor_ray,
    ).unwrap();
    assert_eq!(rates.liquidity_rate, expected_liquidity_rate);
}

#[test]
fn test_reserve_factor_edge_cases() {
    let env = create_test_env();
    let (admin, _, _) = create_test_addresses(&env);
    let contract_id = initialize_contract(&env, &admin);
    let client = interest_rate_strategy::Client::new(&env, &contract_id);

    let asset = Address::generate(&env);

    // Set asset-specific parameters
    client.set_asset_interest_rate_params(
        &admin,
        &asset,
        &(1_000_000_000_000_000_000u128),           // 1% base rate
        &(4_000_000_000_000_000_000u128),           // 4% slope1
        &(60_000_000_000_000_000_000u128),          // 60% slope2
        &(800_000_000_000_000_000_000_000_000u128), // 80% optimal
    );

    // Test with 0% reserve factor
    let rates_zero_reserve = client.calculate_interest_rates(
        &asset,
        &(5_000_000_000_000_000_000u128), // 500 tokens available
        &(5_000_000_000_000_000_000u128), // 500 tokens debt
        &0u128,                           // 0% reserve factor
    );

    // Test with 100% reserve factor
    let rates_max_reserve = client.calculate_interest_rates(
        &asset,
        &(5_000_000_000_000_000_000u128), // 500 tokens available
        &(5_000_000_000_000_000_000u128), // 500 tokens debt
        &(10_000u128),                    // 100% reserve factor
    );

    // With 0% reserve factor, liquidity rate should be higher
    assert!(rates_zero_reserve.liquidity_rate > rates_max_reserve.liquidity_rate);

    // With 100% reserve factor, liquidity rate should be 0
    assert_eq!(rates_max_reserve.liquidity_rate, 0u128);
}

#[test]
#[should_panic]
fn test_reserve_factor_invalid_above_max() {
    let env = create_test_env();
    let (admin, _, _) = create_test_addresses(&env);
    let contract_id = initialize_contract(&env, &admin);
    let client = interest_rate_strategy::Client::new(&env, &contract_id);

    let asset = Address::generate(&env);

    // Test with reserve factor > 10000 (invalid, should panic)
    let _rates = client.calculate_interest_rates(
        &asset,
        &(5_000_000_000_000_000_000u128), // 500 tokens available
        &(5_000_000_000_000_000_000u128), // 500 tokens debt
        &(10_001u128),                    // 100.01% reserve factor (invalid)
    );
}
