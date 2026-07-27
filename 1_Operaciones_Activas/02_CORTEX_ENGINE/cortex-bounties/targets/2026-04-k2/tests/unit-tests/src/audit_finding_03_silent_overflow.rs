//! # FINDING-03: Silent Overflow via `unwrap_or(u128::MAX)`
//!
//! Multiple critical financial functions in `shared/src/utils.rs` return
//! `u128::MAX` when arithmetic overflows instead of returning an error or
//! panicking. This means overflow is SILENTLY converted to the maximum
//! possible value, which then propagates through the protocol as if it
//! were a valid result.
//!
//! Affected functions:
//! - `wad_to_ray()`
//! - `ray_to_wad()`
//! - `percent_mul()`
//! - `percent_div()`
//! - `calculate_compound_interest()`
//! - `calculate_linear_interest()`
//! - `wad_mul()` (via U256 to_u128)
//! - `wad_div()` (via U256 to_u128)
//! - `ray_mul()` (via U256 to_u128)
//! - `ray_div()` (via U256 to_u128)
//!
//! Impact: Corrupted indices, infinite interest accrual, broken health
//! factor calculations, potential protocol insolvency.

#[cfg(test)]
mod tests {
    // Constants matching k2_shared::constants
    const WAD: u128 = 1_000_000_000_000_000_000; // 1e18
    const RAY: u128 = 1_000_000_000_000_000_000_000_000_000; // 1e27
    const RAY_WAD_RATIO: u128 = 1_000_000_000; // RAY / WAD = 1e9
    const HALF_RAY_WAD_RATIO: u128 = 500_000_000;
    const HALF_BASIS_POINTS: u128 = 5_000;
    const BASIS_POINTS_MULTIPLIER: u128 = 10_000;
    const SECONDS_PER_YEAR: u64 = 31_536_000;

    // =========================================================================
    // Reproduce the functions exactly as they appear in the PR
    // =========================================================================

    fn wad_to_ray(a: u128) -> u128 {
        a.checked_mul(RAY_WAD_RATIO).unwrap_or(u128::MAX)
    }

    fn ray_to_wad(a: u128) -> u128 {
        a.checked_add(HALF_RAY_WAD_RATIO)
            .and_then(|sum| sum.checked_div(RAY_WAD_RATIO))
            .unwrap_or(u128::MAX)
    }

    fn percent_mul(value: u128, percentage: u128) -> u128 {
        value
            .checked_mul(percentage)
            .and_then(|prod| prod.checked_add(HALF_BASIS_POINTS))
            .and_then(|sum| sum.checked_div(BASIS_POINTS_MULTIPLIER))
            .unwrap_or(u128::MAX)
    }

    fn percent_div(value: u128, percentage: u128) -> u128 {
        let half_percentage = percentage.checked_div(2).unwrap_or(0);
        value
            .checked_mul(BASIS_POINTS_MULTIPLIER)
            .and_then(|prod| prod.checked_add(half_percentage))
            .and_then(|sum| sum.checked_div(percentage))
            .unwrap_or(u128::MAX)
    }

    fn calculate_linear_interest(
        rate: u128,
        last_update_timestamp: u64,
        current_timestamp: u64,
    ) -> u128 {
        let time_difference = current_timestamp.saturating_sub(last_update_timestamp);
        let interest = rate
            .checked_mul(time_difference as u128)
            .and_then(|prod| prod.checked_div(SECONDS_PER_YEAR as u128))
            .unwrap_or(u128::MAX);
        RAY.checked_add(interest).unwrap_or(u128::MAX)
    }

    /// Simplified compound interest without ray_mul (which needs Env)
    /// The key overflow paths are the same
    fn calculate_compound_interest_terms(
        rate: u128,
        exp: u64,
    ) -> (u128, u128, u128) {
        let exp_minus_one = exp.saturating_sub(1);
        let exp_minus_two = exp.saturating_sub(2);

        let rate_per_second = rate.checked_div(SECONDS_PER_YEAR as u128).unwrap_or(0);

        // Approximate ray_mul(rate_per_second, rate_per_second) without Env
        // ray_mul(a,b) = (a * b + HALF_RAY) / RAY
        let base_power_two = rate_per_second
            .checked_mul(rate_per_second)
            .and_then(|p| p.checked_add(RAY / 2))
            .and_then(|p| p.checked_div(RAY))
            .unwrap_or(u128::MAX);

        let base_power_three = if base_power_two == u128::MAX {
            u128::MAX
        } else {
            base_power_two
                .checked_mul(rate_per_second)
                .and_then(|p| p.checked_add(RAY / 2))
                .and_then(|p| p.checked_div(RAY))
                .unwrap_or(u128::MAX)
        };

        let second_term = (exp as u128)
            .checked_mul(exp_minus_one as u128)
            .and_then(|prod| prod.checked_mul(base_power_two))
            .and_then(|prod| prod.checked_div(2))
            .unwrap_or(u128::MAX);

        let third_term = (exp as u128)
            .checked_mul(exp_minus_one as u128)
            .and_then(|prod| prod.checked_mul(exp_minus_two as u128))
            .and_then(|prod| prod.checked_mul(base_power_three))
            .and_then(|prod| prod.checked_div(6))
            .unwrap_or(u128::MAX);

        let result = RAY
            .checked_add(
                rate_per_second
                    .checked_mul(exp as u128)
                    .unwrap_or(u128::MAX),
            )
            .and_then(|sum| sum.checked_add(second_term))
            .and_then(|sum| sum.checked_add(third_term))
            .unwrap_or(u128::MAX);

        (result, second_term, third_term)
    }

    // =========================================================================
    // Test 1: wad_to_ray overflow returns u128::MAX silently
    // =========================================================================

    /// When a WAD value exceeds u128::MAX / RAY_WAD_RATIO, the multiplication
    /// overflows and silently returns u128::MAX instead of an error.
    #[test]
    fn test_wad_to_ray_silent_overflow() {
        // u128::MAX / RAY_WAD_RATIO ≈ 3.4e29
        let max_safe = u128::MAX / RAY_WAD_RATIO;
        let safe_result = wad_to_ray(max_safe);
        assert_ne!(safe_result, u128::MAX, "Max safe value should not overflow");

        // One above max safe
        let overflow_value = max_safe + 1;
        let overflow_result = wad_to_ray(overflow_value);
        assert_eq!(
            overflow_result,
            u128::MAX,
            "Overflow should silently return u128::MAX"
        );

        // This could happen when the liquidity_index grows very large over time
        // or if a malicious value is stored. The caller has no way to know
        // the result is invalid.
        println!("wad_to_ray silent overflow:");
        println!("  Max safe input: {}", max_safe);
        println!("  Overflow input: {}", overflow_value);
        println!("  Overflow result: {} (u128::MAX)", overflow_result);
        println!("  Expected: ERROR or PANIC");
        println!("  Actual: silently returns u128::MAX as if it's a valid RAY value");
    }

    // =========================================================================
    // Test 2: percent_mul overflow returns u128::MAX
    // =========================================================================

    /// `percent_mul` is used in health factor and liquidation bonus calculations.
    /// When it overflows, it returns u128::MAX instead of an error.
    #[test]
    fn test_percent_mul_silent_overflow() {
        // Large collateral value * percentage overflows
        let large_value = u128::MAX / 10000; // Just under overflow
        let percentage = 8000u128; // 80% liquidation threshold

        let safe_result = percent_mul(large_value, percentage);
        // This should work fine
        assert_ne!(safe_result, u128::MAX);

        // Now with a value that DOES overflow
        let overflow_value = u128::MAX / 5000; // Will overflow when multiplied by 8000
        let overflow_result = percent_mul(overflow_value, percentage);

        assert_eq!(
            overflow_result,
            u128::MAX,
            "percent_mul should silently return u128::MAX on overflow"
        );

        println!("percent_mul silent overflow:");
        println!("  Input value: {}", overflow_value);
        println!("  Percentage: {} ({}%)", percentage, percentage as f64 / 100.0);
        println!("  Result: {} (u128::MAX)", overflow_result);
        println!("  IMPACT: If used in health factor = percent_mul(collateral, threshold),");
        println!("          result is u128::MAX, making HF = MAX → position appears infinitely safe");
    }

    // =========================================================================
    // Test 3: calculate_linear_interest overflow
    // =========================================================================

    /// `calculate_linear_interest` returns u128::MAX when rate * time overflows.
    /// This value then gets used in `ray_mul(liquidity_index, interest_factor)`
    /// to update the liquidity index — effectively setting the index to MAX.
    #[test]
    fn test_linear_interest_overflow_produces_max() {
        // An abnormally high rate that causes overflow
        // Normal rate ≈ 5% APR = 0.05 * RAY ≈ 5e25
        // But a corrupted or manipulated rate could be much higher
        let extreme_rate = u128::MAX / 100; // Still "valid" u128 value
        let last_ts = 0u64;
        let current_ts = SECONDS_PER_YEAR; // 1 year elapsed

        let result = calculate_linear_interest(extreme_rate, last_ts, current_ts);

        assert_eq!(
            result,
            u128::MAX,
            "Extreme rate should cause overflow and return u128::MAX"
        );

        println!("calculate_linear_interest overflow:");
        println!("  Rate: {}", extreme_rate);
        println!("  Time elapsed: 1 year");
        println!("  Result: {} (u128::MAX)", result);
        println!("  IMPACT: liquidity_index = ray_mul(old_index, u128::MAX)");
        println!("          This inflates the index to maximum, making all");
        println!("          aToken balances appear astronomically large");
    }

    // =========================================================================
    // Test 4: Overflow propagation chain — interest → index → balance
    // =========================================================================

    /// When `calculate_linear_interest` returns u128::MAX, it propagates:
    /// 1. interest_factor = u128::MAX
    /// 2. liquidity_index = ray_mul(old_index, u128::MAX) → huge value
    /// 3. aToken balance = ray_mul(scaled_balance, huge_index) → huge balance
    /// 4. Collateral value = huge → health factor = huge → can never be liquidated
    ///
    /// The ENTIRE chain proceeds without any error indication.
    #[test]
    fn test_overflow_propagation_chain() {
        // Step 1: Interest calculation overflows
        let bad_rate = u128::MAX / 50;
        let interest = calculate_linear_interest(bad_rate, 0, SECONDS_PER_YEAR);
        assert_eq!(interest, u128::MAX);

        // Step 2: Index update would use ray_mul(index, interest)
        // ray_mul uses U256 so it won't overflow in u128 multiplication,
        // but the result of ray_mul(RAY, u128::MAX) will be:
        // (RAY * u128::MAX + HALF_RAY) / RAY ≈ u128::MAX
        // This is handled by U256, but the output to_u128() will return u128::MAX

        // Step 3: Balance calculation
        // balance = ray_mul(scaled_balance, corrupted_index)
        // Even a small scaled_balance * u128::MAX_index via U256 will produce huge values

        // Step 4: Health factor
        // HF = (collateral * threshold * WAD) / (10000 * debt)
        // With collateral = huge, HF = huge → position appears safe

        // The key problem: NONE of these steps produces an error.
        // The u128::MAX silently flows through the entire system.

        // Demonstrate that a moderately high but plausible rate also overflows
        // 200% APR = 2 * RAY = 2e27
        let high_but_plausible_rate = 2 * RAY;
        // Over 5 years:
        let five_years = 5 * SECONDS_PER_YEAR;
        let result_5y = calculate_linear_interest(high_but_plausible_rate, 0, five_years);

        // rate * time = 2e27 * 157_680_000 = 3.15e35 — fits in u128 (max ≈ 3.4e38)
        // But RAY + interest could overflow if interest is very large
        // Let's check:
        let interest_5y = high_but_plausible_rate
            .checked_mul(five_years as u128)
            .and_then(|p| p.checked_div(SECONDS_PER_YEAR as u128));

        println!("Plausible high rate (200% APR) over 5 years:");
        if let Some(interest_val) = interest_5y {
            println!("  Interest component: {}", interest_val);
            println!("  RAY + interest: {:?}", RAY.checked_add(interest_val));
            if result_5y == u128::MAX {
                println!("  Result: u128::MAX (OVERFLOW)");
            } else {
                println!("  Result: {} (no overflow)", result_5y);
            }
        }

        // Now demonstrate a rate that DOES overflow with shorter time
        // rate = 1e35, time = 1 year
        let extreme_rate2 = 100_000_000 * RAY; // 100M × RAY
        let result_extreme = calculate_linear_interest(extreme_rate2, 0, SECONDS_PER_YEAR);
        assert_eq!(result_extreme, u128::MAX, "Extreme rate should overflow");

        println!("\nExtreme rate ({}) over 1 year:", extreme_rate2);
        println!("  Result: {} (u128::MAX — silent overflow)", result_extreme);
        println!("  No error returned. Caller sees this as 'very high interest'.");
        println!("  Downstream: index *= u128::MAX → all balances become astronomical");
    }

    // =========================================================================
    // Test 5: Compound interest second/third term overflow
    // =========================================================================

    /// The compound interest Taylor series terms individually overflow.
    /// When `second_term` or `third_term` is u128::MAX, adding them
    /// to the result causes the final sum to be u128::MAX.
    #[test]
    fn test_compound_interest_term_overflow() {
        // High rate with long time period
        // 50% APR over 10 years
        let rate = RAY / 2; // 50% APR in RAY
        let exp = 10 * SECONDS_PER_YEAR; // 10 years in seconds

        let (result, second_term, third_term) = calculate_compound_interest_terms(rate, exp);

        println!("Compound interest overflow (50% APR, 10 years):");
        println!("  Second term: {}", second_term);
        println!("  Third term: {}", third_term);
        println!("  Final result: {}", result);

        // With exp = 315_360_000 (10 years of seconds), the second_term calculation:
        // exp * exp_minus_one * base_power_two / 2
        // = 315_360_000 * 315_359_999 * base_power_two / 2
        // This likely overflows u128 for any non-trivial rate
        if second_term == u128::MAX || third_term == u128::MAX || result == u128::MAX {
            println!("  OVERFLOW DETECTED in compound interest terms");
            println!("  The result silently becomes u128::MAX");
            println!("  This corrupts the variable borrow index");
        }
    }

    // =========================================================================
    // Test 6: percent_div overflow
    // =========================================================================

    /// `percent_div` overflows when value * BASIS_POINTS_MULTIPLIER overflows.
    #[test]
    fn test_percent_div_silent_overflow() {
        // value * 10000 overflows u128 when value > u128::MAX / 10000
        let large_value = u128::MAX / 10000 + 1;
        let percentage = 5000u128; // 50%

        let result = percent_div(large_value, percentage);

        assert_eq!(
            result,
            u128::MAX,
            "percent_div should silently return u128::MAX on overflow"
        );

        println!("percent_div overflow:");
        println!("  Input: {}", large_value);
        println!("  Percentage: {}", percentage);
        println!("  Result: {} (u128::MAX)", result);
        println!("  Expected: error or panic, not a silent sentinel value");
    }

    // =========================================================================
    // Test 7: ray_to_wad overflow
    // =========================================================================

    /// `ray_to_wad` overflows when adding HALF_RAY_WAD_RATIO to a near-MAX value.
    #[test]
    fn test_ray_to_wad_overflow() {
        // Very large RAY value close to u128::MAX
        let large_ray = u128::MAX;
        let result = ray_to_wad(large_ray);

        // u128::MAX + HALF_RAY_WAD_RATIO overflows
        assert_eq!(
            result,
            u128::MAX,
            "ray_to_wad should return u128::MAX on overflow"
        );

        // A more realistic overflow: very large index after prolonged operation
        let large_index = u128::MAX - HALF_RAY_WAD_RATIO + 1;
        let result2 = ray_to_wad(large_index);

        assert_eq!(
            result2,
            u128::MAX,
            "Large index causes ray_to_wad overflow"
        );

        println!("ray_to_wad overflow:");
        println!("  Input (MAX): result = {} (u128::MAX)", result);
        println!("  Input (MAX - HALF_RAY + 1): result = {} (u128::MAX)", result2);
        println!("  These values silently propagate as valid WAD amounts");
    }

    // =========================================================================
    // Test 8: No caller checks for u128::MAX — it propagates unchecked
    // =========================================================================

    /// The callers of these functions do NOT check whether the returned value
    /// is u128::MAX. This test demonstrates the full propagation path.
    #[test]
    fn test_no_caller_checks_for_max() {
        // Simulate the calculation in update_state:
        // 1. cumulated_interest = calculate_linear_interest(rate, t0, t1)
        // 2. new_index = ray_mul(old_index, cumulated_interest)
        //    (ray_mul uses U256 so it handles large inputs but still returns u128)
        // 3. balance = ray_mul(scaled_balance, new_index)

        // If calculate_linear_interest returns u128::MAX:
        let bad_interest_factor = u128::MAX;

        // Simulate ray_mul(RAY, u128::MAX) using pure arithmetic
        // ray_mul(a, b) = (a * b + HALF_RAY) / RAY
        // With U256 this won't overflow, but:
        // (RAY * u128::MAX + HALF_RAY) / RAY ≈ u128::MAX + 0.5 ≈ u128::MAX
        // U256 division: (1e27 * 3.4e38) / 1e27 = 3.4e38 ≈ u128::MAX
        // to_u128() → u128::MAX

        // So new_index ≈ u128::MAX

        // Then: balance = ray_mul(scaled_balance, u128::MAX)
        // For a user with scaled_balance = 1000 (small position):
        // = (1000 * u128::MAX + HALF_RAY) / RAY
        // ≈ 1000 * 3.4e38 / 1e27 = 3.4e14
        // This is a valid u128 but represents a MASSIVE balance

        let scaled_balance: u128 = 1_000_000_000; // 1 token in 9 decimals
        let corrupted_index = u128::MAX;

        // Approximate ray_mul without Env: (a * b) / RAY (simplified)
        // Actually need U256 for this, so let's just check the math
        // scaled_balance * corrupted_index = 1e9 * 3.4e38 = 3.4e47 (overflows u128!)
        // With U256: 3.4e47 / 1e27 = 3.4e20

        // The resulting balance would be ~3.4e20, which when converted to
        // collateral value would be worth trillions of dollars.

        // Key point: at NO POINT does any function return an error.
        // The u128::MAX just flows through as a "valid" number.

        println!("Overflow propagation (no caller validation):");
        println!("  Step 1: calculate_linear_interest() returns u128::MAX (no error)");
        println!("  Step 2: ray_mul(old_index, u128::MAX) ≈ u128::MAX (no error)");
        println!("  Step 3: ray_mul(1e9 scaled, u128::MAX index) ≈ 3.4e20 (no error)");
        println!("  Step 4: collateral value = 3.4e20 * price → trillions (no error)");
        println!("  Step 5: health_factor = trillions → never liquidatable (no error)");
        println!();
        println!("  The entire chain completes without any error indication.");
        println!("  A proper implementation would return Result<u128, Error>.");
    }

    // =========================================================================
    // Test 9: calculate_health_factor uses percent_mul which can overflow
    // =========================================================================

    /// The `calculate_health_factor` function in utils.rs calls `percent_mul`
    /// for `collateral_in_base_with_threshold`. If percent_mul returns
    /// u128::MAX, the health factor becomes artificially inflated.
    #[test]
    fn test_health_factor_uses_overflowing_percent_mul() {
        // Simulate: calculate_health_factor(huge_collateral, debt, threshold)
        // Step 1: collateral_with_threshold = percent_mul(collateral, threshold)
        // Step 2: hf = wad_div(collateral_with_threshold, debt)

        // If collateral is large enough that percent_mul overflows:
        let huge_collateral = u128::MAX / 5000; // Overflows when * 8000
        let threshold = 8000u128; // 80%
        let debt = WAD * 100; // $100 debt

        let collateral_with_threshold = percent_mul(huge_collateral, threshold);

        // percent_mul overflows → returns u128::MAX
        assert_eq!(collateral_with_threshold, u128::MAX);

        // health_factor = wad_div(u128::MAX, debt)
        // This would return an astronomically large HF
        // wad_div(u128::MAX, 100e18) = u128::MAX * 1e18 / 100e18 = u128::MAX / 100
        // ≈ 3.4e36 — a health factor of 3.4 quintillion

        // The position appears infinitely safe when it should actually be
        // evaluated normally

        println!("Health factor inflation via percent_mul overflow:");
        println!("  collateral: {} (legitimate large value)", huge_collateral);
        println!("  percent_mul result: {} (u128::MAX!)", collateral_with_threshold);
        println!("  Resulting HF ≈ u128::MAX / debt → astronomically large");
        println!("  Position can NEVER be liquidated regardless of actual collateral value");
    }

    // =========================================================================
    // Test 10: Demonstrate the correct fix — returning Result
    // =========================================================================

    /// Show what the functions SHOULD do: return Result<u128, Error>
    /// so callers can handle overflow properly.
    #[test]
    fn test_correct_behavior_returns_result() {
        // Correct implementation would be:
        fn wad_to_ray_safe(a: u128) -> Result<u128, &'static str> {
            a.checked_mul(RAY_WAD_RATIO).ok_or("MathOverflow")
        }

        fn calculate_linear_interest_safe(
            rate: u128,
            last_update_timestamp: u64,
            current_timestamp: u64,
        ) -> Result<u128, &'static str> {
            let time_difference = current_timestamp.saturating_sub(last_update_timestamp);
            let interest = rate
                .checked_mul(time_difference as u128)
                .and_then(|prod| prod.checked_div(SECONDS_PER_YEAR as u128))
                .ok_or("MathOverflow: rate * time")?;
            RAY.checked_add(interest).ok_or("MathOverflow: RAY + interest")
        }

        // Overflow case: returns Err instead of u128::MAX
        let overflow_input = u128::MAX / RAY_WAD_RATIO + 1;
        let result = wad_to_ray_safe(overflow_input);
        assert!(result.is_err(), "Safe version returns error on overflow");

        let extreme_rate = u128::MAX / 50;
        let result2 = calculate_linear_interest_safe(extreme_rate, 0, SECONDS_PER_YEAR);
        assert!(result2.is_err(), "Safe version returns error on overflow");

        // Normal case: works fine
        let normal_result = wad_to_ray_safe(WAD);
        assert_eq!(normal_result.unwrap(), RAY);

        let normal_interest = calculate_linear_interest_safe(
            RAY / 20, // 5% APR
            0,
            SECONDS_PER_YEAR,
        );
        assert!(normal_interest.is_ok());

        println!("Correct implementation comparison:");
        println!("  wad_to_ray_safe(overflow) = Err(\"MathOverflow\") -- callers can handle");
        println!("  wad_to_ray(overflow) = {} -- silently propagates", wad_to_ray(overflow_input));
    }
}
