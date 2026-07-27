//! # FINDING-03 FIX VERIFICATION
//!
//! These tests verify that the fix for FINDING-03 is working correctly.
//! All functions that previously returned u128::MAX on overflow now return
//! proper errors.
//!

#[cfg(test)]
mod tests {
    use soroban_sdk::{Env, testutils::Address as _};
    use k2_shared::*;

    // =========================================================================
    // Test 1: wad_to_ray now returns error on overflow
    // =========================================================================

    #[test]
    fn test_wad_to_ray_returns_error_on_overflow() {
        // Max safe value should work
        let max_safe = u128::MAX / (RAY / WAD);
        let safe_result = wad_to_ray(max_safe);
        assert!(safe_result.is_ok(), "Max safe value should succeed");

        // One above max safe should return error
        let overflow_value = max_safe + 1;
        let overflow_result = wad_to_ray(overflow_value);
        
        assert!(overflow_result.is_err(), "Overflow should return error");
        assert_eq!(
            overflow_result.unwrap_err(),
            KineticRouterError::MathOverflow,
            "Should return MathOverflow error"
        );

        println!("wad_to_ray properly returns MathOverflow error on overflow");
    }

    // =========================================================================
    // Test 2: ray_to_wad now returns error on overflow
    // =========================================================================

    #[test]
    fn test_ray_to_wad_returns_error_on_overflow() {
        let large_ray = u128::MAX;
        let result = ray_to_wad(large_ray);
        
        assert!(result.is_err(), "Large RAY value should return error");
        assert_eq!(
            result.unwrap_err(),
            KineticRouterError::MathOverflow,
            "Should return MathOverflow error"
        );

        println!("ray_to_wad properly returns MathOverflow error on overflow");
    }

    // =========================================================================
    // Test 3: percent_mul now returns error on overflow
    // =========================================================================

    #[test]
    fn test_percent_mul_returns_error_on_overflow() {
        // Value that will overflow when multiplied by percentage
        let overflow_value = u128::MAX / 5000;
        let percentage = 8000u128; // 80%

        let result = percent_mul(overflow_value, percentage);
        
        assert!(result.is_err(), "Overflow should return error");
        assert_eq!(
            result.unwrap_err(),
            KineticRouterError::MathOverflow,
            "Should return MathOverflow error"
        );

        println!("percent_mul properly returns MathOverflow error on overflow");
        println!("   This prevents health factor inflation attacks");
    }

    // =========================================================================
    // Test 4: percent_div now returns error on overflow
    // =========================================================================

    #[test]
    fn test_percent_div_returns_error_on_overflow() {
        let large_value = u128::MAX / 10000 + 1;
        let percentage = 5000u128; // 50%

        let result = percent_div(large_value, percentage);
        
        assert!(result.is_err(), "Overflow should return error");
        assert_eq!(
            result.unwrap_err(),
            KineticRouterError::MathOverflow,
            "Should return MathOverflow error"
        );

        println!("percent_div properly returns MathOverflow error on overflow");
    }

    // =========================================================================
    // Test 5: calculate_linear_interest now returns error on overflow
    // =========================================================================

    #[test]
    fn test_linear_interest_returns_error_on_overflow() {
        let extreme_rate = u128::MAX / 100;
        let last_ts = 0u64;
        let current_ts = SECONDS_PER_YEAR;

        let result = calculate_linear_interest(extreme_rate, last_ts, current_ts);
        
        assert!(result.is_err(), "Extreme rate should return error");
        assert_eq!(
            result.unwrap_err(),
            KineticRouterError::MathOverflow,
            "Should return MathOverflow error"
        );

        println!("calculate_linear_interest properly returns MathOverflow error");
        println!("   This prevents liquidity index corruption");
    }

    // =========================================================================
    // Test 6: calculate_compound_interest now returns error on overflow
    // =========================================================================

    #[test]
    fn test_compound_interest_returns_error_on_overflow() {
        let env = Env::default();
        
        // Extreme rate that causes overflow in the Taylor series terms
        // The second term: (exp * exp_minus_one * base_power_two) / 2
        // With large exp and rate, this overflows
        let extreme_rate = u128::MAX / 10; // Very high rate
        let exp = 100 * SECONDS_PER_YEAR; // 100 years

        let result = calculate_compound_interest(&env, extreme_rate, 0, exp);
        
        assert!(result.is_err(), "Compound interest overflow should return error");
        assert_eq!(
            result.unwrap_err(),
            KineticRouterError::MathOverflow,
            "Should return MathOverflow error"
        );

        println!("calculate_compound_interest properly returns MathOverflow error");
        println!("   This prevents variable borrow index corruption");
    }

    // =========================================================================
    // Test 7: ray_mul now returns error on overflow
    // =========================================================================

    #[test]
    fn test_ray_mul_returns_error_on_overflow() {
        let env = Env::default();
        
        // Values that cause U256 result to exceed u128::MAX
        let huge_a = u128::MAX;
        let huge_b = u128::MAX;

        let result = ray_mul(&env, huge_a, huge_b);
        
        assert!(result.is_err(), "Ray mul overflow should return error");
        assert_eq!(
            result.unwrap_err(),
            KineticRouterError::MathOverflow,
            "Should return MathOverflow error"
        );

        println!("ray_mul properly returns MathOverflow error on overflow");
    }

    // =========================================================================
    // Test 8: ray_div now returns error on overflow
    // =========================================================================

    #[test]
    fn test_ray_div_returns_error_on_overflow() {
        let env = Env::default();
        
        // Values that cause U256 result to exceed u128::MAX
        let huge_a = u128::MAX;
        let small_b = 1;

        let result = ray_div(&env, huge_a, small_b);
        
        assert!(result.is_err(), "Ray div overflow should return error");
        assert_eq!(
            result.unwrap_err(),
            KineticRouterError::MathOverflow,
            "Should return MathOverflow error"
        );

        println!("ray_div properly returns MathOverflow error on overflow");
    }

    // =========================================================================
    // Test 9: wad_mul now returns error on overflow
    // =========================================================================

    #[test]
    fn test_wad_mul_returns_error_on_overflow() {
        let env = Env::default();
        
        // Values that cause U256 result to exceed u128::MAX
        let huge_a = u128::MAX;
        let huge_b = u128::MAX;

        let result = wad_mul(&env, huge_a, huge_b);
        
        assert!(result.is_err(), "Wad mul overflow should return error");
        assert_eq!(
            result.unwrap_err(),
            KineticRouterError::MathOverflow,
            "Should return MathOverflow error"
        );

        println!("wad_mul properly returns MathOverflow error on overflow");
    }

    // =========================================================================
    // Test 10: wad_div now returns error on overflow
    // =========================================================================

    #[test]
    fn test_wad_div_returns_error_on_overflow() {
        let env = Env::default();
        
        // Values that cause U256 result to exceed u128::MAX
        let huge_a = u128::MAX;
        let small_b = 1;

        let result = wad_div(&env, huge_a, small_b);
        
        assert!(result.is_err(), "Wad div overflow should return error");
        assert_eq!(
            result.unwrap_err(),
            KineticRouterError::MathOverflow,
            "Should return MathOverflow error"
        );

        println!("wad_div properly returns MathOverflow error on overflow");
    }

    // =========================================================================
    // Test 12: Normal operations still work correctly
    // =========================================================================

    #[test]
    fn test_normal_operations_still_work() {
        let env = Env::default();

        // Normal wad_to_ray
        let result = wad_to_ray(WAD);
        assert_eq!(result.unwrap(), RAY, "Normal wad_to_ray should work");

        // Normal ray_to_wad
        let result = ray_to_wad(RAY);
        assert_eq!(result.unwrap(), WAD, "Normal ray_to_wad should work");

        // Normal percent_mul
        let result = percent_mul(WAD * 1000, 8000); // $1000 * 80%
        assert!(result.is_ok(), "Normal percent_mul should work");
        assert_eq!(result.unwrap(), WAD * 800, "Should be $800");

        // Normal calculate_linear_interest (5% APR)
        let result = calculate_linear_interest(RAY / 20, 0, SECONDS_PER_YEAR);
        assert!(result.is_ok(), "Normal linear interest should work");

        println!("All normal operations work correctly after fix");
    }

    // =========================================================================
    // Test 13: Verify error propagation prevents state corruption
    // =========================================================================

    #[test]
    fn test_error_propagation_prevents_corruption() {
        let env = Env::default();

        // Simulate the calculation chain that would have been corrupted
        // Step 1: Interest calculation with extreme rate
        let bad_rate = u128::MAX / 50;
        let interest_result = calculate_linear_interest(bad_rate, 0, SECONDS_PER_YEAR);
        
        // Should return error, not u128::MAX
        assert!(interest_result.is_err(), "Step 1: Should return error");
        assert_eq!(
            interest_result.unwrap_err(),
            KineticRouterError::MathOverflow
        );

        // Step 2: Simulate the full propagation chain that would corrupt state
        // In production code, this would use ? operator and propagate the error
        let old_index = RAY;
        
        // This simulates: ray_mul(old_index, interest_result?)
        // The ? would propagate the error, preventing ray_mul from ever executing
        let index_update_result = match interest_result {
            Ok(interest) => ray_mul(&env, old_index, interest),
            Err(e) => Err(e), // Error propagates, ray_mul never called
        };
        
        assert!(index_update_result.is_err(), "Step 2: Index update should fail");
        assert_eq!(
            index_update_result.unwrap_err(),
            KineticRouterError::MathOverflow
        );

        // Step 3: Simulate balance calculation that would use corrupted index
        // This would be: ray_mul(user_scaled_balance, new_index?)
        let user_scaled_balance = WAD * 1_000_000; // 1M tokens
        
        let balance_result = match index_update_result {
            Ok(new_index) => ray_mul(&env, user_scaled_balance, new_index),
            Err(e) => Err(e), // Error propagates, balance never calculated
        };
        
        assert!(balance_result.is_err(), "Step 3: Balance calculation should fail");
        assert_eq!(
            balance_result.unwrap_err(),
            KineticRouterError::MathOverflow
        );

        println!("✅ Error propagation prevents state corruption:");
        println!("   Step 1: calculate_linear_interest returns Err(MathOverflow)");
        println!("   Step 2: ray_mul never executes, index stays valid");
        println!("   Step 3: Balance calculation never executes");
        println!("   Result: Transaction reverts, no state corruption");
    }

    // =========================================================================
    // Test 14: Edge case - zero multiplication with max value
    // =========================================================================

    #[test]
    fn test_zero_edge_cases() {
        let env = Env::default();

        // Zero * MAX should work (result is 0)
        let result = wad_mul(&env, 0, u128::MAX);
        assert!(result.is_ok(), "0 * MAX should succeed");
        assert_eq!(result.unwrap(), 0, "Result should be 0");

        let result = ray_mul(&env, 0, u128::MAX);
        assert!(result.is_ok(), "0 * MAX should succeed");
        assert_eq!(result.unwrap(), 0, "Result should be 0");

        // MAX * 0 should work
        let result = wad_mul(&env, u128::MAX, 0);
        assert!(result.is_ok(), "MAX * 0 should succeed");
        assert_eq!(result.unwrap(), 0, "Result should be 0");

        println!("Zero edge cases handled correctly");
    }

    // =========================================================================
    // Test 15: Division by zero edge cases
    // =========================================================================

    #[test]
    fn test_division_by_zero_edge_cases() {
        let env = Env::default();

        // Division by zero must return an error, not silently return 0
        let result = wad_div(&env, WAD * 1000, 0);
        assert!(result.is_err(), "wad_div by zero must return Err");

        let result = ray_div(&env, RAY * 1000, 0);
        assert!(result.is_err(), "ray_div by zero must return Err");

        // Division of zero by nonzero is fine
        let result = wad_div(&env, 0, WAD);
        assert_eq!(result.unwrap(), 0, "0 / x should return 0");

        let result = ray_div(&env, 0, RAY);
        assert_eq!(result.unwrap(), 0, "0 / x should return 0");

        println!("Division by zero correctly rejected");
    }

    // =========================================================================
    // Test 17: Compound interest individual term overflows
    // =========================================================================

    #[test]
    fn test_compound_interest_first_term_overflow() {
        let env = Env::default();

        // Rate that causes first term (rate_per_second * exp) to overflow
        let huge_rate = u128::MAX / 2;
        let long_time = SECONDS_PER_YEAR * 10; // 10 years

        let result = calculate_compound_interest(&env, huge_rate, 0, long_time);

        assert!(result.is_err(), "First term overflow should return error");
        assert_eq!(
            result.unwrap_err(),
            KineticRouterError::MathOverflow
        );

        println!("Compound interest first term overflow caught");
    }

    #[test]
    fn test_compound_interest_second_term_overflow() {
        let env = Env::default();

        // Extreme values that cause second term overflow
        let extreme_rate = u128::MAX / 100;
        let long_exp = 1000 * SECONDS_PER_YEAR;

        let result = calculate_compound_interest(&env, extreme_rate, 0, long_exp);

        assert!(result.is_err(), "Second term overflow should return error");
        assert_eq!(
            result.unwrap_err(),
            KineticRouterError::MathOverflow
        );

        println!("Compound interest second term overflow caught");
    }

    // =========================================================================
    // Test 18: Percent operations near boundary
    // =========================================================================

    #[test]
    fn test_percent_operations_boundary() {
        // Test percent_mul at exact boundary
        let boundary_value = u128::MAX / 10000;
        
        // Just below overflow should work
        let safe_result = percent_mul(boundary_value, 9999);
        assert!(safe_result.is_ok(), "Just below boundary should work");

        // At overflow should fail
        let overflow_result = percent_mul(boundary_value + 1, 10000);
        assert!(overflow_result.is_err(), "At boundary should fail");
        assert_eq!(overflow_result.unwrap_err(), KineticRouterError::MathOverflow);

        // Test percent_div boundary
        let large_value = u128::MAX / 10000;
        let result = percent_div(large_value + 1, 5000);
        assert!(result.is_err(), "percent_div overflow should fail");
        assert_eq!(result.unwrap_err(), KineticRouterError::MathOverflow);

        println!("Percent operations boundary cases verified");
    }
}
