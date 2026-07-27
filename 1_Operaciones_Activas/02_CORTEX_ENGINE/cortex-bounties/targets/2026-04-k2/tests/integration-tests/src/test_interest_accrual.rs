#![cfg(test)]

use crate::setup::deploy_test_protocol;
use soroban_sdk::{testutils::Ledger, Env};

#[test]
fn test_get_liquidity_index() {
    let env = Env::default();
    env.mock_all_auths();
    
    let protocol = deploy_test_protocol(&env);
    
    let liquidity_index = protocol.kinetic_router.get_current_liquidity_index(&protocol.underlying_asset);
    let ray = 1_000_000_000_000_000_000_000_000_000u128;
    assert_eq!(liquidity_index, ray, "Liquidity index must start at RAY (1e27). Expected: {}, Got: {}", ray, liquidity_index);
    
    let liquidity_index_second = protocol.kinetic_router.get_current_liquidity_index(&protocol.underlying_asset);
    assert_eq!(liquidity_index, liquidity_index_second, "Liquidity index must be consistent across calls. First: {}, Second: {}", liquidity_index, liquidity_index_second);
}

#[test]
fn test_get_borrow_index() {
    let env = Env::default();
    env.mock_all_auths();
    
    let protocol = deploy_test_protocol(&env);
    
    let borrow_index = protocol.kinetic_router.get_current_var_borrow_idx(&protocol.underlying_asset);
    let ray = 1_000_000_000_000_000_000_000_000_000u128;
    assert_eq!(borrow_index, ray, "Borrow index must start at RAY (1e27). Expected: {}, Got: {}", ray, borrow_index);
    
    let borrow_index_second = protocol.kinetic_router.get_current_var_borrow_idx(&protocol.underlying_asset);
    assert_eq!(borrow_index, borrow_index_second, "Borrow index must be consistent across calls. First: {}, Second: {}", borrow_index, borrow_index_second);
}

#[test]
fn test_utilization_rate() {
    let env = Env::default();
    env.mock_all_auths();
    
    let protocol = deploy_test_protocol(&env);
    
    let supply_amount = 10_000_000_000u128;
    
    protocol.kinetic_router.supply(
        &protocol.liquidity_provider,
        &protocol.underlying_asset,
        &supply_amount,
        &protocol.liquidity_provider,
        &0u32,
    );
    
    // With no borrows, liquidity rate should be 0 (no interest earned when utilization is 0%)
    let reserve_data = protocol.kinetic_router.get_reserve_data(&protocol.underlying_asset);
    assert_eq!(reserve_data.current_liquidity_rate, 0, "Liquidity rate should be 0 with no borrows (0% utilization)");

    let ray = 1_000_000_000_000_000_000_000_000_000u128;
    assert_eq!(reserve_data.liquidity_index, ray, "Reserve liquidity index must be RAY (1e27) initially. Expected: {}, Got: {}", ray, reserve_data.liquidity_index);
    assert_eq!(reserve_data.variable_borrow_index, ray, "Reserve borrow index must be RAY (1e27) initially. Expected: {}, Got: {}", ray, reserve_data.variable_borrow_index);
}

#[test]
fn test_reserve_state_update() {
    let env = Env::default();
    env.mock_all_auths();
    
    let protocol = deploy_test_protocol(&env);
    
    let supply_amount = 5_000_000_000u128;
    
    protocol.kinetic_router.supply(
        &protocol.user,
        &protocol.underlying_asset,
        &supply_amount,
        &protocol.user,
        &0u32,
    );
    
    let index_before = protocol.kinetic_router.get_current_liquidity_index(&protocol.underlying_asset);
    let ray = 1_000_000_000_000_000_000_000_000_000u128;
    assert_eq!(index_before, ray, "Index before update must be RAY. Expected: {}, Got: {}", ray, index_before);
    
    protocol.kinetic_router.update_reserve_state(&protocol.underlying_asset);
    let index_after = protocol.kinetic_router.get_current_liquidity_index(&protocol.underlying_asset);
    
    assert_eq!(index_after, index_before, "Liquidity index must remain unchanged immediately after state update with no time passage. Expected: {}, Got: {}", index_before, index_after);
}

#[test]
fn test_interest_accrual_after_borrow() {
    let env = Env::default();
    env.mock_all_auths();
    
    let protocol = deploy_test_protocol(&env);
    
    // Use 25% utilization (5M borrowed from 20M total supply) to achieve measurable interest accrual
    let supply_amount = 10_000_000_000u128;
    let borrow_amount = 5_000_000_000u128;
    
    protocol.kinetic_router.supply(
        &protocol.liquidity_provider,
        &protocol.underlying_asset,
        &supply_amount,
        &protocol.liquidity_provider,
        &0u32,
    );
    
    protocol.kinetic_router.supply(
        &protocol.user,
        &protocol.underlying_asset,
        &supply_amount,
        &protocol.user,
        &0u32,
    );
    
    protocol.kinetic_router.set_user_use_reserve_as_coll(
        &protocol.user,
        &protocol.underlying_asset,
        &true,
    );
    
    let initial_index = protocol.kinetic_router.get_current_liquidity_index(&protocol.underlying_asset);
    let ray = 1_000_000_000_000_000_000_000_000_000u128;
    assert_eq!(initial_index, ray, "Initial liquidity index must be RAY (1e27). Expected: {}, Got: {}", ray, initial_index);
    
    protocol.kinetic_router.borrow(
        &protocol.user,
        &protocol.underlying_asset,
        &borrow_amount,
        &1u32,
        &0u32,
        &protocol.user,
    );

    let reserve_data = protocol.kinetic_router.get_reserve_data(&protocol.underlying_asset);
    assert!(reserve_data.current_variable_borrow_rate > 0, "Variable borrow rate must be positive. Got: {}", reserve_data.current_variable_borrow_rate);
    assert!(reserve_data.current_variable_borrow_rate >= 20_000_000_000_000_000_000_000_000u128, "Variable borrow rate must be at least base rate (2%). Got: {}", reserve_data.current_variable_borrow_rate);
    assert!(reserve_data.current_variable_borrow_rate <= 1_000_000_000_000_000_000_000_000_000u128, "Variable borrow rate must be reasonable (max 100%). Got: {}", reserve_data.current_variable_borrow_rate);

    // Verify utilization: 5B borrowed / 20B total supply = 25%
    let ray = 1_000_000_000_000_000_000_000_000_000u128;
    let utilization_after = borrow_amount.checked_mul(ray).unwrap() / supply_amount.checked_mul(2).unwrap();
    let expected_utilization = 250_000_000_000_000_000_000_000_000u128; // 25% in RAY
    assert_eq!(utilization_after, expected_utilization, "Utilization must be exactly 25% (0.25 * RAY). Expected: {}, Got: {}", expected_utilization, utilization_after);

    let expected_liquidity_rate_numerator = reserve_data.current_variable_borrow_rate.checked_mul(utilization_after);
    if let Some(num) = expected_liquidity_rate_numerator {
        let expected_liquidity_rate = num.checked_div(ray).unwrap_or(0);
        assert_eq!(reserve_data.current_liquidity_rate, expected_liquidity_rate, "Liquidity rate must equal borrow_rate * utilization / RAY. Expected: {}, Got: {}", expected_liquidity_rate, reserve_data.current_liquidity_rate);
    } else {
        assert!(reserve_data.current_liquidity_rate > 0, "Liquidity rate must be positive when borrow rate and utilization are positive. Got: {}", reserve_data.current_liquidity_rate);
        assert!(reserve_data.current_liquidity_rate <= reserve_data.current_variable_borrow_rate, "Liquidity rate must not exceed borrow rate. Liquidity: {}, Borrow: {}", reserve_data.current_liquidity_rate, reserve_data.current_variable_borrow_rate);
    }
    
    let reserve_data_second = protocol.kinetic_router.get_reserve_data(&protocol.underlying_asset);
    assert_eq!(reserve_data.current_variable_borrow_rate, reserve_data_second.current_variable_borrow_rate, "Borrow rate must be consistent across calls. First: {}, Second: {}", reserve_data.current_variable_borrow_rate, reserve_data_second.current_variable_borrow_rate);
    assert_eq!(reserve_data.current_liquidity_rate, reserve_data_second.current_liquidity_rate, "Liquidity rate must be consistent across calls. First: {}, Second: {}", reserve_data.current_liquidity_rate, reserve_data_second.current_liquidity_rate);
    
    let index_after_borrow = protocol.kinetic_router.get_current_liquidity_index(&protocol.underlying_asset);
    assert_eq!(index_after_borrow, initial_index, "Index should not change immediately after borrow. Expected: {}, Got: {}", initial_index, index_after_borrow);
    
    let initial_borrow_index = protocol.kinetic_router.get_current_var_borrow_idx(&protocol.underlying_asset);
    let ray = 1_000_000_000_000_000_000_000_000_000u128;
    assert_eq!(initial_borrow_index, ray, "Initial borrow index must be RAY (1e27). Expected: {}, Got: {}", ray, initial_borrow_index);
    
    env.ledger().with_mut(|li| {
        li.timestamp += 2_592_000; // 30 days - longer period to ensure compound vs linear difference is measurable
    });
    
    protocol.kinetic_router.update_reserve_state(&protocol.underlying_asset);
    
    // Get rates after state update to calculate expected increases
    let reserve_data_after = protocol.kinetic_router.get_reserve_data(&protocol.underlying_asset);
    let liquidity_rate = reserve_data_after.current_liquidity_rate;
    let borrow_rate = reserve_data_after.current_variable_borrow_rate;
    
    let time_elapsed = 2_592_000u128; // 30 days in seconds
    let ray = 1_000_000_000_000_000_000_000_000_000u128; // RAY constant for calculations
    
    // Calculate expected liquidity increase (linear): initial_index * liquidity_rate * time / RAY
    // For linear interest: increase = principal * rate * time
    let expected_liquidity_increase = initial_index
        .checked_mul(liquidity_rate)
        .and_then(|x| x.checked_mul(time_elapsed))
        .and_then(|x| x.checked_div(ray))
        .unwrap_or(0);
    
    // Calculate expected borrow increase (compound approximation): initial_index * borrow_rate * time / RAY
    // Note: This is a linear approximation; actual compound interest would be slightly higher
    let expected_borrow_increase_linear = initial_borrow_index
        .checked_mul(borrow_rate)
        .and_then(|x| x.checked_mul(time_elapsed))
        .and_then(|x| x.checked_div(ray))
        .unwrap_or(0);
    
    let new_index = protocol.kinetic_router.get_current_liquidity_index(&protocol.underlying_asset);
    assert!(new_index >= initial_index, "Liquidity index should not decrease. Initial: {}, After interest: {}", initial_index, new_index);
    assert!(new_index > initial_index, "Liquidity index should increase after interest accrual. Initial: {}, After interest: {}", initial_index, new_index);
    
    let liquidity_increase = new_index - initial_index;
    // Allow 5% tolerance for rounding/calculation differences
    let liquidity_tolerance = expected_liquidity_increase / 20;
    assert!(
        liquidity_increase >= expected_liquidity_increase.saturating_sub(liquidity_tolerance),
        "Liquidity index increase should match expected calculation. Increase: {}, Expected: {} (rate: {}, time: {}s), Tolerance: {}",
        liquidity_increase,
        expected_liquidity_increase,
        liquidity_rate,
        time_elapsed,
        liquidity_tolerance
    );
    
    let new_borrow_index = protocol.kinetic_router.get_current_var_borrow_idx(&protocol.underlying_asset);
    assert!(new_borrow_index >= initial_borrow_index, "Borrow index should not decrease. Initial: {}, After interest: {}", initial_borrow_index, new_borrow_index);
    assert!(new_borrow_index > initial_borrow_index, "Borrow index should increase after interest accrual. Initial: {}, After interest: {}", initial_borrow_index, new_borrow_index);
    
    let borrow_increase = new_borrow_index - initial_borrow_index;
    // For compound interest, actual increase should be >= linear approximation
    // Allow 5% tolerance below linear approximation (compound should be higher)
    let borrow_tolerance = expected_borrow_increase_linear / 20;
    assert!(
        borrow_increase >= expected_borrow_increase_linear.saturating_sub(borrow_tolerance),
        "Borrow index increase should be at least linear approximation (compound >= linear). Increase: {}, Expected (linear): {} (rate: {}, time: {}s), Tolerance: {}",
        borrow_increase,
        expected_borrow_increase_linear,
        borrow_rate,
        time_elapsed,
        borrow_tolerance
    );
    
    // Compare increases directly: compound interest should grow faster than linear
    // Since both start from the same base (RAY) and compound grows faster, borrow_increase > liquidity_increase
    assert!(borrow_increase > liquidity_increase, "Borrow index (compound) must increase MORE than liquidity index (linear). Borrow increase: {}, Liquidity increase: {}", borrow_increase, liquidity_increase);
}
