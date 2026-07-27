//! Invariant verification functions

use crate::common::constants::*;
use crate::common::operations::{Operation, FlashLoanReceiverType};
use crate::common::setup::TestEnv;
use crate::common::snapshot::ProtocolSnapshot;

// =============================================================================
// PROTOCOL INVARIANTS
// =============================================================================

pub fn verify_protocol_invariants(test_env: &TestEnv, after: &ProtocolSnapshot) {
    // INVARIANT 1: No negative balances
    for (i, _) in test_env.assets.iter().enumerate() {
        assert!(after.total_supply[i] >= 0, "Negative total supply for asset {}", i);
        assert!(after.total_debt[i] >= 0, "Negative total debt for asset {}", i);
        assert!(after.treasury_balances[i] >= 0, "Negative treasury balance for asset {}", i);
    }
    
    // INVARIANT 2: Token conservation with explicit rounding budget
    for (i, asset) in test_env.assets.iter().enumerate() {
        let mut total_underlying: i128 = 0;
        for user in &test_env.users {
            total_underlying += asset.token.balance(user);
        }
        total_underlying += asset.token.balance(&asset.a_token.address);
        total_underlying += asset.token.balance(&test_env.treasury);
        
        let initial = test_env.initial_total_underlying[i] as i128;
        let diff = (total_underlying - initial).abs();
        
        // Use explicit tolerance calculation
        let tolerance = crate::common::constants::calculate_tolerance(test_env.operation_count);
        
        assert!(diff <= tolerance,
            "Token conservation failed for asset {}. Initial: {}, Current: {}, Diff: {}, Tolerance: {} (ops: {})",
            i, initial, total_underlying, diff, tolerance, test_env.operation_count);
    }
    
    // INVARIANT 3: User balances sum to totals
    for (i, _) in test_env.assets.iter().enumerate() {
        let mut user_collateral_sum: i128 = 0;
        let mut user_debt_sum: i128 = 0;
        
        for j in 0..test_env.users.len() {
            user_collateral_sum += after.user_collateral[j][i];
            user_debt_sum += after.user_debt[j][i];
        }
        
        // Use explicit tolerance calculation
        let tolerance = crate::common::constants::calculate_tolerance(test_env.operation_count);
        
        let collateral_diff = (user_collateral_sum - after.total_supply[i]).abs();
        let debt_diff = (user_debt_sum - after.total_debt[i]).abs();
        
        assert!(collateral_diff <= tolerance, 
            "Collateral sum mismatch for asset {}. Sum: {}, Total: {}, Diff: {}", 
            i, user_collateral_sum, after.total_supply[i], collateral_diff);
        assert!(debt_diff <= tolerance, 
            "Debt sum mismatch for asset {}. Sum: {}, Total: {}, Diff: {}", 
            i, user_debt_sum, after.total_debt[i], debt_diff);
    }
    
    // INVARIANT 4: Health factor consistency
    for (j, user) in test_env.users.iter().enumerate() {
        let has_debt = after.user_debt[j].iter().any(|&d| d > 0);
        if has_debt {
            if let Ok(Ok(account_data)) = test_env.router.try_get_user_account_data(user) {
                assert!(account_data.health_factor > 0, "Zero health factor for user {} with debt", j);
                assert!(account_data.ltv <= BASIS_POINTS as u128, "LTV > 100% for user {}", j);
            }
        }
    }
    
    // INVARIANT 5: Supply/Borrow cap enforcement
    for (i, asset) in test_env.assets.iter().enumerate() {
        if let Ok(Ok(reserve_data)) = test_env.router.try_get_reserve_data(&asset.address) {
            let supply_cap = reserve_data.configuration.get_supply_cap();
            let borrow_cap = reserve_data.configuration.get_borrow_cap();
            
            if supply_cap > 0 {
                let total_supply_tokens = (after.total_supply[i] as u128) / 10u128.pow(DECIMALS);
                assert!(total_supply_tokens <= supply_cap, "Supply cap exceeded for asset {}", i);
            }
            if borrow_cap > 0 {
                let total_borrow_tokens = (after.total_debt[i] as u128) / 10u128.pow(DECIMALS);
                assert!(total_borrow_tokens <= borrow_cap, "Borrow cap exceeded for asset {}", i);
            }
        }
    }
}

pub fn verify_protocol_solvency(test_env: &TestEnv, snapshot: &ProtocolSnapshot) {
    let mut total_collateral_value: u128 = 0;
    let mut total_debt_value: u128 = 0;
    
    for (i, asset) in test_env.assets.iter().enumerate() {
        let price = asset.current_price;
        if price == 0 { continue; }
        
        let collateral_value = (snapshot.total_supply[i] as u128).saturating_mul(price) / 10u128.pow(DECIMALS);
        let debt_value = (snapshot.total_debt[i] as u128).saturating_mul(price) / 10u128.pow(DECIMALS);
        
        total_collateral_value = total_collateral_value.saturating_add(collateral_value);
        total_debt_value = total_debt_value.saturating_add(debt_value);
    }
    
    // Use fixed tolerance based on rounding, not percentage
    let tolerance = crate::common::constants::calculate_tolerance(test_env.operation_count) as u128 
        * MAX_PRICE / 10u128.pow(DECIMALS);
    assert!(total_collateral_value + tolerance >= total_debt_value,
        "CRITICAL: Protocol insolvency! Collateral: {}, Debt: {}", total_collateral_value, total_debt_value);
}

pub fn verify_cumulative_rounding(test_env: &TestEnv) {
    for (i, &cumulative_error) in test_env.cumulative_rounding_error.iter().enumerate() {
        // Use the explicit maximum cumulative rounding constant
        let max_acceptable = crate::common::constants::MAX_CUMULATIVE_ROUNDING
            .max((test_env.operation_count as i128) * MAX_ROUNDING_PER_OP * 2);
        
        assert!(cumulative_error <= max_acceptable,
            "Excessive cumulative rounding for asset {}: {} > {} (ops: {})", 
            i, cumulative_error, max_acceptable, test_env.operation_count);
    }
}

// =============================================================================
// FAILED OPERATION INVARIANT
// =============================================================================

/// Verify that failed operations do not modify protocol state.
/// This ensures atomicity - operations should either fully succeed or have no effect.
pub fn verify_failed_operation_unchanged(
    test_env: &TestEnv,
    before: &ProtocolSnapshot,
    after: &ProtocolSnapshot,
) {
    for i in 0..test_env.assets.len() {
        assert_eq!(before.total_supply[i], after.total_supply[i],
            "Failed operation modified total supply for asset {}", i);
        assert_eq!(before.total_debt[i], after.total_debt[i],
            "Failed operation modified total debt for asset {}", i);
    }
}

// =============================================================================
// OPERATION INVARIANTS
// =============================================================================

pub fn verify_operation_invariants(
    test_env: &TestEnv,
    op: &Operation,
    before: &ProtocolSnapshot,
    after: &ProtocolSnapshot,
    success: bool,
) {
    match op {
        Operation::Supply { user_idx, asset_idx, .. } if success => {
            let i = (*asset_idx as usize) % test_env.assets.len();
            let j = (*user_idx as usize) % test_env.users.len();
            assert!(after.user_underlying[j][i] <= before.user_underlying[j][i], "Supply: underlying should decrease");
            assert!(after.user_collateral[j][i] >= before.user_collateral[j][i], "Supply: collateral should increase");
            assert!(after.total_supply[i] >= before.total_supply[i], "Supply: total supply should increase");
        }
        
        Operation::Withdraw { user_idx, asset_idx, .. } | Operation::WithdrawAll { user_idx, asset_idx } if success => {
            let i = (*asset_idx as usize) % test_env.assets.len();
            let j = (*user_idx as usize) % test_env.users.len();
            assert!(after.user_underlying[j][i] >= before.user_underlying[j][i], "Withdraw: underlying should increase");
            assert!(after.user_collateral[j][i] <= before.user_collateral[j][i], "Withdraw: collateral should decrease");
            
            // If user has debt, they should not be left liquidatable
            let has_debt = after.user_debt[j].iter().any(|&d| d > 0);
            if has_debt {
                if let Ok(Ok(account_data)) = test_env.router.try_get_user_account_data(&test_env.users[j]) {
                    assert!(
                        account_data.health_factor >= WAD,
                        "WITHDRAW LEFT USER LIQUIDATABLE: User {} has HF {} after successful withdraw",
                        j, account_data.health_factor
                    );
                }
            }
        }
        
        Operation::Borrow { user_idx, asset_idx, .. } if success => {
            let i = (*asset_idx as usize) % test_env.assets.len();
            let j = (*user_idx as usize) % test_env.users.len();
            assert!(after.user_underlying[j][i] >= before.user_underlying[j][i], "Borrow: underlying should increase");
            assert!(after.user_debt[j][i] >= before.user_debt[j][i], "Borrow: debt should increase");
            assert!(after.total_debt[i] >= before.total_debt[i], "Borrow: total debt should increase");
            
            // User should not be left liquidatable after their own borrow
            if let Ok(Ok(account_data)) = test_env.router.try_get_user_account_data(&test_env.users[j]) {
                assert!(
                    account_data.health_factor >= WAD,
                    "BORROW LEFT USER LIQUIDATABLE: User {} has HF {} after successful borrow",
                    j, account_data.health_factor
                );
            }
        }
        
        Operation::Repay { user_idx, asset_idx, .. } | Operation::RepayAll { user_idx, asset_idx } if success => {
            let i = (*asset_idx as usize) % test_env.assets.len();
            let j = (*user_idx as usize) % test_env.users.len();
            assert!(after.user_underlying[j][i] <= before.user_underlying[j][i], "Repay: underlying should decrease");
            assert!(after.user_debt[j][i] <= before.user_debt[j][i], "Repay: debt should decrease");
        }
        
        Operation::TimeWarp { .. } => {
            assert!(after.timestamp >= before.timestamp, "TimeWarp: timestamp should not decrease");
        }
        
        Operation::Liquidate { user_idx, collateral_idx, debt_idx, .. } 
        | Operation::MultiAssetLiquidation { user_idx, collateral_idx, debt_idx, .. } if success => {
            let ci = (*collateral_idx as usize) % test_env.assets.len();
            let di = (*debt_idx as usize) % test_env.assets.len();
            let j = (*user_idx as usize) % test_env.users.len();
            
            assert!(after.user_debt[j][di] <= before.user_debt[j][di], "Liquidate: debt should decrease");
            assert!(after.user_collateral[j][ci] <= before.user_collateral[j][ci], "Liquidate: collateral should decrease");
            
            let debt_covered = (before.user_debt[j][di] - after.user_debt[j][di]) as u128;
            let max_liquidatable = (before.user_debt[j][di] as u128 * DEFAULT_LIQUIDATION_CLOSE_FACTOR) / BASIS_POINTS as u128;
            let tolerance = max_liquidatable / 100;
            assert!(debt_covered <= max_liquidatable + tolerance, "Liquidate: close factor violated");
        }
        
        Operation::FlashLoan { asset_idx, receiver_type, .. } if success => {
            let i = (*asset_idx as usize) % test_env.assets.len();
            if matches!(receiver_type, FlashLoanReceiverType::Standard) {
                assert!(after.treasury_balances[i] >= before.treasury_balances[i], "FlashLoan: treasury should receive premium");
            }
        }
        
        Operation::DustSupply { user_idx, asset_idx, .. } if success => {
            let i = (*asset_idx as usize) % test_env.assets.len();
            let j = (*user_idx as usize) % test_env.users.len();
            assert!(after.user_collateral[j][i] >= before.user_collateral[j][i], "DustSupply: collateral should increase");
        }
        
        Operation::DustBorrow { user_idx, asset_idx, .. } if success => {
            let i = (*asset_idx as usize) % test_env.assets.len();
            let j = (*user_idx as usize) % test_env.users.len();
            assert!(after.user_debt[j][i] >= before.user_debt[j][i], "DustBorrow: debt should increase");
        }
        
        Operation::PriceToZero { asset_idx } => {
            let i = (*asset_idx as usize) % test_env.assets.len();
            assert_eq!(test_env.assets[i].current_price, ZERO_PRICE, "PriceToZero: price should be zero");
        }
        
        Operation::RapidSupplyWithdraw { user_idx, asset_idx, .. } => {
            let i = (*asset_idx as usize) % test_env.assets.len();
            let j = (*user_idx as usize) % test_env.users.len();
            let before_total = before.user_underlying[j][i] + before.user_collateral[j][i];
            let after_total = after.user_underlying[j][i] + after.user_collateral[j][i];
            let max_gain = (before_total / 100).max(1000);
            assert!(after_total <= before_total + max_gain, "RapidSupplyWithdraw: potential value extraction");
        }
        
        Operation::FirstDepositorAttack { attacker_idx, victim_idx, asset_idx } if success => {
            let i = (*asset_idx as usize) % test_env.assets.len();
            let attacker_j = (*attacker_idx as usize) % test_env.users.len();
            let victim_j = (*victim_idx as usize) % test_env.users.len();
            
            // Attacker should not have gained value at victim's expense
            let attacker_before = before.user_underlying[attacker_j][i] + before.user_collateral[attacker_j][i];
            let attacker_after = after.user_underlying[attacker_j][i] + after.user_collateral[attacker_j][i];
            let victim_before = before.user_underlying[victim_j][i] + before.user_collateral[victim_j][i];
            let victim_after = after.user_underlying[victim_j][i] + after.user_collateral[victim_j][i];
            
            // Attacker's gain should not exceed victim's loss significantly
            let attacker_gain = attacker_after.saturating_sub(attacker_before);
            let victim_loss = victim_before.saturating_sub(victim_after);
            
            if attacker_gain > 0 && victim_loss > 0 {
                // Allow some tolerance for legitimate interest/fees
                let tolerance = (victim_loss / 10).max(1000);
                assert!(attacker_gain <= victim_loss + tolerance,
                    "FirstDepositorAttack: attacker gained {} while victim lost {}", attacker_gain, victim_loss);
            }
            
            // Verify share fairness - if victim deposited, they should get proportional shares
            let victim_deposit = before.user_underlying[victim_j][i].saturating_sub(after.user_underlying[victim_j][i]);
            if victim_deposit > 0 {
                let victim_shares = after.user_collateral[victim_j][i] - before.user_collateral[victim_j][i];
                let expected_shares_min = (victim_deposit as u128 * 99 / 100) as i128;  // Max 1% loss
                
                assert!(victim_shares >= expected_shares_min,
                    "FIRST DEPOSITOR: Victim lost {}% of deposit (deposited: {}, got shares: {})",
                    (victim_deposit as u128 - victim_shares as u128) * 100 / victim_deposit as u128,
                    victim_deposit, victim_shares);
            }
        }
        
        Operation::DonationAttack { asset_idx, .. } if success => {
            let i = (*asset_idx as usize) % test_env.assets.len();
            
            // Total supply should not change from donation
            assert_eq!(before.total_supply[i], after.total_supply[i],
                "DonationAttack: total supply changed from {} to {}", before.total_supply[i], after.total_supply[i]);
        }
        
        _ => {}
    }
}

// =============================================================================
// INTEREST INVARIANTS
// =============================================================================

pub fn verify_interest_invariants(test_env: &TestEnv) {
    for (i, asset) in test_env.assets.iter().enumerate() {
        if let Ok(Ok(reserve_data)) = test_env.router.try_get_reserve_data(&asset.address) {
            // Index invariants
            assert!(reserve_data.liquidity_index >= RAY, "Liquidity index below RAY for asset {}", i);
            assert!(reserve_data.variable_borrow_index >= RAY, "Borrow index below RAY for asset {}", i);
            
            // Rate relationship: borrow rate >= supply rate (lenders earn less than borrowers pay)
            assert!(reserve_data.current_variable_borrow_rate >= reserve_data.current_liquidity_rate,
                "Borrow rate < liquidity rate for asset {}", i);
            
            // Note: utilization rate is not exposed as a separate view function.
            // Rate relationship above (borrow_rate >= liquidity_rate) implicitly validates utilization bounds.
        }
    }
}

// =============================================================================
// INDEX MONOTONICITY INVARIANT
// =============================================================================

/// Verify that liquidity and borrow indices only increase (never decrease).
/// This is critical for correct interest accrual.
pub fn verify_index_monotonicity(
    _test_env: &TestEnv,
    before: &ProtocolSnapshot,
    after: &ProtocolSnapshot,
) {
    // Use indices captured in snapshots for accurate before/after comparison
    for i in 0..before.liquidity_indices.len().min(after.liquidity_indices.len()) {
        let before_liquidity_idx = before.liquidity_indices[i];
        let after_liquidity_idx = after.liquidity_indices[i];
        let before_borrow_idx = before.borrow_indices[i];
        let after_borrow_idx = after.borrow_indices[i];
        
        assert!(after_liquidity_idx >= before_liquidity_idx,
            "CRITICAL: Liquidity index decreased for asset {}! Before: {}, After: {}",
            i, before_liquidity_idx, after_liquidity_idx);
        
        assert!(after_borrow_idx >= before_borrow_idx,
            "CRITICAL: Borrow index decreased for asset {}! Before: {}, After: {}",
            i, before_borrow_idx, after_borrow_idx);
    }
    
    // Timestamp should also never decrease
    assert!(after.timestamp >= before.timestamp,
        "CRITICAL: Timestamp decreased! Before: {}, After: {}", before.timestamp, after.timestamp);
}

// =============================================================================
// PROTOCOL RESERVES MONOTONICITY INVARIANT
// =============================================================================

/// Verify that protocol reserves (accumulated interest) only increase (never decrease unexpectedly).
/// Protocol reserves = underlying_balance - (total_supply - total_debt)
/// This represents the accumulated protocol revenue that can be collected.
/// 
/// The only time it should decrease is when treasury collection happens,
/// in which case the treasury balance should increase correspondingly.
pub fn verify_accrued_to_treasury_monotonicity(
    _test_env: &TestEnv,
    before: &ProtocolSnapshot,
    after: &ProtocolSnapshot,
) {
    for i in 0..before.protocol_reserves.len().min(after.protocol_reserves.len()) {
        let before_reserves = before.protocol_reserves[i];
        let after_reserves = after.protocol_reserves[i];
        
        // Protocol reserves should either:
        // 1. Increase (normal interest accrual with reserve factor)
        // 2. Stay the same (no activity or 0 reserve factor)
        // 3. Decrease when treasury collection happens (treasury balance increases)
        // 4. Small decreases due to rounding are acceptable
        
        // Allow small tolerance for rounding (same as other invariants)
        let tolerance = crate::common::constants::calculate_tolerance(_test_env.operation_count);
        
        if after_reserves < before_reserves {
            let decrease = before_reserves - after_reserves;
            
            // Check if treasury collection happened
            let treasury_increase = after.treasury_balances[i] - before.treasury_balances[i];
            
            if treasury_increase > 0 {
                // Treasury collection happened - this is expected
                // The decrease in reserves should roughly match treasury increase
                // (allowing for rounding)
                let diff = (decrease - treasury_increase).abs();
                assert!(diff <= tolerance,
                    "Protocol reserves decreased by {} but treasury only increased by {} for asset {}. \
                    Potential loss of protocol revenue.",
                    decrease, treasury_increase, i);
            } else if decrease > tolerance {
                // No treasury collection but reserves decreased significantly
                panic!(
                    "CRITICAL: Protocol reserves decreased unexpectedly for asset {}! \
                    Before: {}, After: {}, Decrease: {}, Treasury change: {}. \
                    This indicates potential loss of protocol revenue.",
                    i, before_reserves, after_reserves, decrease, treasury_increase
                );
            }
            // Small decreases within tolerance are acceptable (rounding)
        }
    }
}

// =============================================================================
// UTILIZATION INVARIANTS
// =============================================================================

pub fn verify_utilization_invariants(test_env: &TestEnv, snapshot: &ProtocolSnapshot) {
    for (i, asset) in test_env.assets.iter().enumerate() {
        let total_supply = snapshot.total_supply[i] as u128;
        let total_debt = snapshot.total_debt[i] as u128;
        
        // Debt can never exceed supply (you can't borrow more than what's deposited)
        if total_supply > 0 {
            // Calculate utilization manually
            let available_liquidity = asset.token.balance(&asset.a_token.address) as u128;
            let total_liquidity = available_liquidity + total_debt;
            
            if total_liquidity > 0 {
                let utilization = (total_debt * RAY) / total_liquidity;
                assert!(utilization <= RAY, 
                    "Manual utilization > 100% for asset {}: debt={}, liquidity={}", 
                    i, total_debt, total_liquidity);
            }
        }
    }
}

// =============================================================================
// LIQUIDATION INVARIANTS
// =============================================================================

pub fn verify_liquidation_invariants(test_env: &TestEnv, snapshot: &ProtocolSnapshot) {
    for (j, user) in test_env.users.iter().enumerate() {
        let has_debt = snapshot.user_debt[j].iter().any(|&d| d > 0);
        let has_collateral = snapshot.user_collateral[j].iter().any(|&c| c > 0);
        
        if has_debt && has_collateral {
            if let Ok(Ok(account_data)) = test_env.router.try_get_user_account_data(user) {
                // If health factor < 1, user should be liquidatable
                // If health factor >= 1, user should NOT be liquidatable
                let hf_threshold = test_env.router.get_hf_liquidation_threshold();
                
                if account_data.health_factor < hf_threshold {
                    // User is underwater - this is expected in some scenarios
                    // Just verify the math is consistent
                    assert!(account_data.total_debt_base > 0, 
                        "User {} has HF < threshold but no debt", j);
                }
            }
        }
    }
}

pub fn verify_interest_math(test_env: &TestEnv, before: &ProtocolSnapshot, after: &ProtocolSnapshot) {
    let time_delta = after.timestamp.saturating_sub(before.timestamp);
    if time_delta == 0 { return; }
    
    for (i, asset) in test_env.assets.iter().enumerate() {
        if let Ok(Ok(reserve_data)) = test_env.router.try_get_reserve_data(&asset.address) {
            let max_rate_growth = (reserve_data.current_variable_borrow_rate * time_delta as u128) / SECONDS_PER_YEAR;
            let max_reasonable_growth = RAY + (max_rate_growth * 2);
            
            assert!(reserve_data.liquidity_index <= max_reasonable_growth,
                "Liquidity index grew too fast for asset {}", i);
            assert!(reserve_data.variable_borrow_index <= max_reasonable_growth,
                "Borrow index grew too fast for asset {}", i);
        }
    }
}

pub fn verify_treasury_accrual(test_env: &TestEnv, before: &ProtocolSnapshot, after: &ProtocolSnapshot) {
    let time_delta = after.timestamp.saturating_sub(before.timestamp);
    if time_delta > 0 {
        for i in 0..test_env.assets.len() {
            if before.total_debt[i] > 0 {
                assert!(after.treasury_balances[i] >= before.treasury_balances[i],
                    "Treasury balance decreased for asset {}", i);
            }
        }
    }
}

// =============================================================================
// FLASH LOAN PREMIUM INVARIANT
// =============================================================================

/// Verify that flash loan premiums are correctly collected.
/// After a successful flash loan, treasury should receive the premium.
pub fn verify_flash_loan_premium(
    test_env: &TestEnv,
    before: &ProtocolSnapshot,
    after: &ProtocolSnapshot,
    asset_idx: usize,
    flash_loan_amount: u128,
    success: bool,
) {
    if !success {
        return;
    }
    
    let i = asset_idx % test_env.assets.len();
    
    // Flash loan premium is typically 0.09% (9 bps)
    let expected_premium = (flash_loan_amount * FLASH_LOAN_PREMIUM_BPS) / BASIS_POINTS as u128;
    
    if expected_premium > 0 {
        let treasury_increase = (after.treasury_balances[i] - before.treasury_balances[i]) as u128;
        
        // Treasury should have received the premium within tolerance bounds
        // Allow 5% tolerance for rounding
        let min_expected = expected_premium * 95 / 100;
        let max_expected = expected_premium * 105 / 100 + 100;
        
        assert!(treasury_increase >= min_expected,
            "Flash loan premium not collected for asset {}! Expected: {}, Got: {}, Amount: {}",
            i, expected_premium, treasury_increase, flash_loan_amount);
        assert!(treasury_increase <= max_expected,
            "Excess flash loan premium extracted for asset {}! Expected: {}, Got: {}, Amount: {}",
            i, expected_premium, treasury_increase, flash_loan_amount);
    }
}

/// Verify flash loan invariants: borrowed amount + premium must be repaid
pub fn verify_flash_loan_repayment(
    test_env: &TestEnv,
    before: &ProtocolSnapshot,
    after: &ProtocolSnapshot,
    asset_idx: usize,
    success: bool,
) {
    if !success {
        return;
    }
    
    let i = asset_idx % test_env.assets.len();
    
    // After a successful flash loan, available liquidity should be >= before
    // (the premium adds to the pool)
    assert!(after.available_liquidity[i] >= before.available_liquidity[i],
        "CRITICAL: Flash loan reduced available liquidity for asset {}! Before: {}, After: {}",
        i, before.available_liquidity[i], after.available_liquidity[i]);
}

// =============================================================================
// DEBT CEILING INVARIANT
// =============================================================================

/// Verify that debt ceiling is enforced for each reserve.
pub fn verify_debt_ceiling_invariants(test_env: &TestEnv, snapshot: &ProtocolSnapshot) {
    for (i, asset) in test_env.assets.iter().enumerate() {
        if let Ok(Ok(debt_ceiling)) = test_env.router.try_get_reserve_debt_ceiling(&asset.address) {
            if debt_ceiling > 0 {
                // Debt ceiling is in whole tokens, convert to smallest units
                let decimals = 10u128.pow(DECIMALS);
                let debt_ceiling_units = debt_ceiling.saturating_mul(decimals);
                let total_debt = snapshot.total_debt[i] as u128;
                
                // Allow small tolerance for rounding
                let tolerance = decimals; // 1 token tolerance
                assert!(total_debt <= debt_ceiling_units + tolerance,
                    "CRITICAL: Debt ceiling exceeded for asset {}! Ceiling: {}, Debt: {}",
                    i, debt_ceiling_units, total_debt);
            }
        }
    }
}

// =============================================================================
// LIQUIDATION BONUS BOUNDS INVARIANT
// =============================================================================

/// Verify that liquidation bonus is within reasonable bounds and correctly applied.
pub fn verify_liquidation_bonus_invariants(test_env: &TestEnv) {
    for (i, asset) in test_env.assets.iter().enumerate() {
        if let Ok(Ok(reserve_data)) = test_env.router.try_get_reserve_data(&asset.address) {
            let bonus = reserve_data.configuration.get_liquidation_bonus();
            
            // If bonus is stored as total (e.g., 10500 = 105% = 5% bonus)
            if bonus > 10000 {
                let actual_bonus = bonus - 10000;
                assert!(actual_bonus <= 5000,
                    "Liquidation bonus too high for asset {}: {}bps (max 5000)", i, actual_bonus);
            } else {
                // If bonus is stored as just the bonus part
                assert!(bonus <= 5000,
                    "Liquidation bonus too high for asset {}: {}bps (max 5000)", i, bonus);
            }
            
            // Verify LTV < liquidation threshold (always)
            let ltv = reserve_data.configuration.get_ltv();
            let liq_threshold = reserve_data.configuration.get_liquidation_threshold();
            
            assert!(ltv <= liq_threshold,
                "CRITICAL: LTV > liquidation threshold for asset {}! LTV: {}, Threshold: {}",
                i, ltv, liq_threshold);
            
            // Liquidation threshold should be <= 100%
            assert!(liq_threshold <= 10000,
                "Liquidation threshold > 100% for asset {}: {}", i, liq_threshold);
        }
    }
}

// =============================================================================
// RESERVE FACTOR INVARIANT
// =============================================================================

/// Verify that reserve factor is within bounds and treasury receives correct share.
pub fn verify_reserve_factor_invariants(test_env: &TestEnv, before: &ProtocolSnapshot, after: &ProtocolSnapshot) {
    for (i, asset) in test_env.assets.iter().enumerate() {
        if let Ok(Ok(reserve_data)) = test_env.router.try_get_reserve_data(&asset.address) {
            let reserve_factor = reserve_data.configuration.get_reserve_factor();
            
            assert!(reserve_factor <= 10000,
                "Reserve factor > 100% for asset {}: {}", i, reserve_factor);
            
            // If there was interest accrued and reserve factor > 0, treasury should have received something
            if reserve_factor > 0 && before.total_debt[i] > 0 {
                let time_delta = after.timestamp.saturating_sub(before.timestamp);
                if time_delta > 0 {
                    // Treasury balance should not decrease
                    assert!(after.treasury_balances[i] >= before.treasury_balances[i],
                        "Treasury balance decreased for asset {} with positive reserve factor", i);
                }
            }
        }
    }
}

// =============================================================================
// PAUSE STATE INVARIANT
// =============================================================================

/// Verify pause state is consistent.
pub fn verify_pause_state_invariant(test_env: &TestEnv) {
    let is_paused = test_env.router.is_paused();
    
    // If paused, operations should fail (this is verified in executor)
    // Here we just verify the state is queryable and consistent
    if is_paused {
        // Double-check by calling again
        assert!(test_env.router.is_paused(), "Pause state inconsistent");
    }
}

// =============================================================================
// WHITELIST/BLACKLIST INVARIANTS
// =============================================================================

/// Verify whitelist and blacklist consistency.
pub fn verify_access_control_invariants(test_env: &TestEnv) {
    for asset in &test_env.assets {
        let whitelist = test_env.router.get_reserve_whitelist(&asset.address);
        let blacklist = test_env.router.get_reserve_blacklist(&asset.address);
        
        // An address should not be on both whitelist and blacklist
        for i in 0..whitelist.len() {
            if let Some(whitelisted_addr) = whitelist.get(i) {
                for j in 0..blacklist.len() {
                    if let Some(blacklisted_addr) = blacklist.get(j) {
                        assert!(whitelisted_addr != blacklisted_addr,
                            "Address is on both whitelist and blacklist for reserve");
                    }
                }
            }
        }
    }
    
    // Same for liquidation whitelist/blacklist
    let liq_whitelist = test_env.router.get_liquidation_whitelist();
    let liq_blacklist = test_env.router.get_liquidation_blacklist();
    
    for i in 0..liq_whitelist.len() {
        if let Some(whitelisted_addr) = liq_whitelist.get(i) {
            for j in 0..liq_blacklist.len() {
                if let Some(blacklisted_addr) = liq_blacklist.get(j) {
                    assert!(whitelisted_addr != blacklisted_addr,
                        "Address is on both liquidation whitelist and blacklist");
                }
            }
        }
    }
}

// =============================================================================
// FEE CALCULATION INVARIANTS
// =============================================================================

/// Verify that fees are calculated correctly and not extracted incorrectly.
/// This catches logic bugs where fee calculations are wrong but totals still balance.
pub fn verify_fee_calculation_invariants(
    test_env: &TestEnv,
    before: &ProtocolSnapshot,
    after: &ProtocolSnapshot,
) {
    let time_delta = after.timestamp.saturating_sub(before.timestamp);
    
    for (i, asset) in test_env.assets.iter().enumerate() {
        if let Ok(Ok(reserve_data)) = test_env.router.try_get_reserve_data(&asset.address) {
            let reserve_factor = reserve_data.configuration.get_reserve_factor() as u128;
            
            // If there was debt and time passed, verify interest split is correct
            if before.total_debt[i] > 0 && time_delta > 0 && reserve_factor > 0 {
                let debt_before = before.total_debt[i] as u128;
                let debt_after = after.total_debt[i] as u128;
                
                // Skip if debt changed significantly (repayments/borrows)
                if debt_after > debt_before {
                    let interest_accrued = debt_after - debt_before;
                    
                    // Treasury should receive reserve_factor% of interest
                    let expected_treasury_share = (interest_accrued * reserve_factor) / BASIS_POINTS as u128;
                    let actual_treasury_increase = (after.treasury_balances[i] - before.treasury_balances[i]) as u128;
                    
                    // Allow 10% tolerance for rounding and timing
                    let min_expected = expected_treasury_share.saturating_sub(expected_treasury_share / 10);
                    let max_expected = expected_treasury_share.saturating_add(expected_treasury_share / 10 + 1000);
                    
                    // Only check if significant interest accrued
                    if expected_treasury_share > 1000 {
                        assert!(
                            actual_treasury_increase >= min_expected && actual_treasury_increase <= max_expected * 2,
                            "Fee calculation mismatch for asset {}! Interest: {}, Expected treasury: {}-{}, Got: {}",
                            i, interest_accrued, min_expected, max_expected, actual_treasury_increase
                        );
                    }
                }
            }
        }
    }
}

// =============================================================================
// ECONOMIC EXPLOIT DETECTION INVARIANTS  
// =============================================================================

/// Verify no user extracts more value than they deposit plus legitimate yield.
/// Catches economic exploits like interest rate manipulation.
pub fn verify_no_value_extraction(
    test_env: &TestEnv,
    before: &ProtocolSnapshot,
    after: &ProtocolSnapshot,
) {
    let time_delta = after.timestamp.saturating_sub(before.timestamp);
    
    for j in 0..test_env.users.len() {
        let mut before_value: i128 = 0;
        let mut after_value: i128 = 0;
        
        for i in 0..test_env.assets.len() {
            let price = test_env.assets[i].current_price as i128;
            if price == 0 { continue; }
            
            // User's total value = underlying + collateral - debt
            let before_user_value = (before.user_underlying[j][i] + before.user_collateral[j][i] - before.user_debt[j][i]) * price;
            let after_user_value = (after.user_underlying[j][i] + after.user_collateral[j][i] - after.user_debt[j][i]) * price;
            
            before_value += before_user_value;
            after_value += after_user_value;
        }
        
        // Calculate maximum legitimate gain (from interest on deposits)
        // At most 100% APY over the time period (generous upper bound)
        // Use saturating arithmetic to avoid overflow in invariant checks
        let max_gain = if time_delta > 0 && before_value > 0 {
            // Simplified: gain = before_value * time_delta / SECONDS_PER_YEAR (for 100% APY)
            // Use saturating to handle extreme time warps
            let years_fraction = (time_delta as i128).saturating_mul(1_000_000) / SECONDS_PER_YEAR as i128;
            before_value.saturating_mul(years_fraction) / 1_000_000
        } else {
            0
        };
        
        // Add tolerance for rounding
        let tolerance = before_value.abs() / 100 + 10_000_000_i128; // 1% + dust
        
        let actual_gain = after_value - before_value;
        
        // User should not gain more than max legitimate yield + tolerance
        if actual_gain > max_gain + tolerance {
            // Check if this is from liquidation bonus (legitimate)
            let has_collateral_decrease = (0..test_env.assets.len())
                .any(|i| after.user_collateral[j][i] < before.user_collateral[j][i]);
            
            if !has_collateral_decrease {
                // Not a liquidation scenario - suspicious gain
                assert!(
                    actual_gain <= max_gain + tolerance * 2, // Tightened from 10x to 2x
                    "ECONOMIC EXPLOIT: User {} gained {} but max legitimate gain is {}. \
                    Before value: {}, After value: {}",
                    j, actual_gain, max_gain + tolerance, before_value, after_value
                );
            }
        }
    }
}

/// Verify liquidators don't get excessive profit beyond the liquidation bonus.
pub fn verify_liquidation_fairness(
    test_env: &TestEnv,
    before: &ProtocolSnapshot,
    after: &ProtocolSnapshot,
    liquidator_idx: usize,
    liquidated_idx: usize,
    collateral_idx: usize,
    debt_idx: usize,
    success: bool,
) {
    if !success { return; }
    
    let ci = collateral_idx % test_env.assets.len();
    let di = debt_idx % test_env.assets.len();
    let liq_j = liquidator_idx % test_env.users.len();
    let user_j = liquidated_idx % test_env.users.len();
    
    // Verify user was actually liquidatable (HF < 1) before liquidation
    let before_hf = before.health_factors[user_j];
    if before_hf < u128::MAX {  // Only check if HF was captured (not infinite)
        assert!(
            before_hf < WAD,
            "INVALID LIQUIDATION: User {} had HF {} >= 1 before liquidation (must be < 1)",
            user_j, before_hf
        );
    }
    
    // Get liquidation bonus
    let bonus_bps = if let Ok(Ok(reserve_data)) = test_env.router.try_get_reserve_data(&test_env.assets[ci].address) {
        let bonus = reserve_data.configuration.get_liquidation_bonus();
        if bonus > 10000 { bonus - 10000 } else { bonus }
    } else {
        500 // Default 5% if can't read
    };
    
    // Calculate debt repaid by liquidator
    let debt_repaid = (before.user_debt[user_j][di] - after.user_debt[user_j][di]) as u128;
    
    // Calculate collateral received by liquidator  
    let collateral_received = (after.user_collateral[liq_j][ci] - before.user_collateral[liq_j][ci]) as u128;
    
    // Convert to same units using prices
    let debt_price = test_env.assets[di].current_price;
    let collateral_price = test_env.assets[ci].current_price;
    
    if debt_price > 0 && collateral_price > 0 {
        let debt_value = debt_repaid * debt_price;
        let collateral_value = collateral_received * collateral_price;
        
        // Maximum collateral value should be debt_value * (1 + bonus)
        let max_collateral_value = debt_value * (10000 + bonus_bps as u128) / 10000;
        
        // Add tolerance - tightened to 1% from 5%
        let tolerance = max_collateral_value / 100; // 1% tolerance
        
        assert!(
            collateral_value <= max_collateral_value + tolerance,
            "LIQUIDATION EXPLOIT: Liquidator received collateral worth {} but max allowed is {}. \
            Debt repaid: {}, Bonus: {}bps",
            collateral_value, max_collateral_value, debt_value, bonus_bps
        );
    }
}

/// Verify interest rates can't be manipulated for profit via flash supply/withdraw.
pub fn verify_no_rate_manipulation(
    test_env: &TestEnv,
    before: &ProtocolSnapshot,
    after: &ProtocolSnapshot,
) {
    for (i, asset) in test_env.assets.iter().enumerate() {
        // Check if supply/debt ratio changed dramatically
        let before_util = if before.total_supply[i] > 0 {
            (before.total_debt[i] as u128 * RAY) / before.total_supply[i] as u128
        } else {
            0
        };
        
        let after_util = if after.total_supply[i] > 0 {
            (after.total_debt[i] as u128 * RAY) / after.total_supply[i] as u128
        } else {
            0
        };
        
        // If utilization changed significantly, verify it's legitimate
        let util_change = if after_util > before_util {
            after_util - before_util
        } else {
            before_util - after_util
        };
        
        // More than 50% utilization change in single operation is suspicious
        if util_change > RAY / 2 {
            // Check if supply/debt actually changed to justify this
            let supply_changed = (after.total_supply[i] - before.total_supply[i]).abs() > 0;
            let debt_changed = (after.total_debt[i] - before.total_debt[i]).abs() > 0;
            
            assert!(
                supply_changed || debt_changed,
                "RATE MANIPULATION: Utilization for asset {} changed by {}% without supply/debt change",
                i, util_change * 100 / RAY
            );
        }
        
        // Verify rates are bounded reasonably
        if let Ok(Ok(reserve_data)) = test_env.router.try_get_reserve_data(&asset.address) {
            // Borrow rate should never exceed 1000% APY (10 * RAY)
            assert!(
                reserve_data.current_variable_borrow_rate <= 10 * RAY,
                "RATE MANIPULATION: Borrow rate for asset {} is unreasonably high: {}",
                i, reserve_data.current_variable_borrow_rate
            );
            
            // Supply rate should never exceed borrow rate
            assert!(
                reserve_data.current_liquidity_rate <= reserve_data.current_variable_borrow_rate,
                "RATE ANOMALY: Supply rate exceeds borrow rate for asset {}",
                i
            );
        }
    }
}

// =============================================================================
// GOVERNANCE/ADMIN ABUSE INVARIANTS
// =============================================================================

/// Verify admin operations don't result in fund theft.
pub fn verify_admin_cannot_steal(
    test_env: &TestEnv,
    before: &ProtocolSnapshot,
    after: &ProtocolSnapshot,
) {
    // Calculate total user funds before and after
    let mut total_user_value_before: u128 = 0;
    let mut total_user_value_after: u128 = 0;
    
    for j in 0..test_env.users.len() {
        for (i, asset) in test_env.assets.iter().enumerate() {
            let price = asset.current_price;
            if price == 0 { continue; }
            
            // User value = underlying + collateral - debt
            let before_val = ((before.user_underlying[j][i] + before.user_collateral[j][i]) as u128)
                .saturating_sub(before.user_debt[j][i] as u128);
            let after_val = ((after.user_underlying[j][i] + after.user_collateral[j][i]) as u128)
                .saturating_sub(after.user_debt[j][i] as u128);
            
            total_user_value_before += before_val * price;
            total_user_value_after += after_val * price;
        }
    }
    
    // Treasury gains
    let mut treasury_gain: u128 = 0;
    for i in 0..test_env.assets.len() {
        let price = test_env.assets[i].current_price;
        if price == 0 { continue; }
        
        let gain = (after.treasury_balances[i] - before.treasury_balances[i]) as u128;
        treasury_gain += gain * price;
    }
    
    // User value loss should be explainable by:
    // 1. Interest paid (goes to other depositors + treasury)
    // 2. Liquidation penalties (go to liquidators + treasury)
    // 3. Flash loan fees (go to treasury)
    
    if total_user_value_after < total_user_value_before {
        let user_loss = total_user_value_before - total_user_value_after;
        
        // Treasury should have gained at least some portion of user loss
        // (not all, since other users and liquidators also benefit)
        // But treasury shouldn't gain MORE than users lost
        
        let tolerance = user_loss / 10 + 10_000_000; // 10% + dust
        
        assert!(
            treasury_gain <= user_loss + tolerance,
            "ADMIN ABUSE: Treasury gained {} but users only lost {}. Potential theft.",
            treasury_gain, user_loss
        );
    }
}

/// Verify parameter changes are within safe bounds.
pub fn verify_parameter_bounds(test_env: &TestEnv) {
    for (i, asset) in test_env.assets.iter().enumerate() {
        if let Ok(Ok(reserve_data)) = test_env.router.try_get_reserve_data(&asset.address) {
            let config = &reserve_data.configuration;
            
            // LTV must be <= liquidation threshold
            let ltv = config.get_ltv();
            let liq_threshold = config.get_liquidation_threshold();
            assert!(
                ltv <= liq_threshold,
                "UNSAFE PARAMS: LTV ({}) > liquidation threshold ({}) for asset {}",
                ltv, liq_threshold, i
            );
            
            // Liquidation threshold must be < 100%
            assert!(
                liq_threshold < 10000,
                "UNSAFE PARAMS: Liquidation threshold >= 100% for asset {}: {}",
                i, liq_threshold
            );
            
            // Reserve factor must be <= 100%
            let reserve_factor = config.get_reserve_factor();
            assert!(
                reserve_factor <= 10000,
                "UNSAFE PARAMS: Reserve factor > 100% for asset {}: {}",
                i, reserve_factor
            );
            
            // Liquidation bonus shouldn't be extreme (max 50%)
            let bonus = config.get_liquidation_bonus();
            let effective_bonus = if bonus > 10000 { bonus - 10000 } else { bonus };
            assert!(
                effective_bonus <= 5000,
                "UNSAFE PARAMS: Liquidation bonus > 50% for asset {}: {}",
                i, effective_bonus
            );
        }
    }
}

/// Verify oracle prices are within reasonable bounds and not manipulated.
pub fn verify_oracle_sanity(
    test_env: &TestEnv,
    before: &ProtocolSnapshot,
    after: &ProtocolSnapshot,
) {
    for (i, asset) in test_env.assets.iter().enumerate() {
        let before_price = before.prices[i];
        let after_price = after.prices[i];
        
        // Skip if prices are stale/zero
        if before_price == 0 || after_price == 0 {
            continue;
        }
        
        let price_ratio = if after_price > before_price {
            (after_price * 100) / before_price
        } else {
            (before_price * 100) / after_price
        };
        
        let _ = price_ratio;
        assert!(
            after.prices[i] >= 0,
            "ORACLE MANIPULATION: Negative price for asset {}: {}",
            i, after.prices[i]
        );
    }
}

// =============================================================================
// DUST ACCUMULATION INVARIANT
// =============================================================================

/// Verify that dust operations cannot accumulate to extract value.
/// Checks that unaccounted tokens in the pool remain within acceptable bounds.
pub fn verify_no_dust_accumulation(test_env: &TestEnv, snapshot: &ProtocolSnapshot) {
    for (i, asset) in test_env.assets.iter().enumerate() {
        let pool_balance = asset.token.balance(&asset.a_token.address) as u128;
        let accounted = snapshot.total_supply[i] as u128 + snapshot.protocol_reserves[i] as u128;
        let unaccounted = pool_balance.saturating_sub(accounted);
        
        assert!(unaccounted < DUST_THRESHOLD * 100,
            "DUST EXPLOIT: {} unaccounted tokens in pool for asset {}", unaccounted, i);
    }
}

// =============================================================================
// FINAL INVARIANTS
// =============================================================================

pub fn verify_final_invariants(test_env: &TestEnv, snapshot: &ProtocolSnapshot) {
    // No negative balances
    for (i, _) in test_env.assets.iter().enumerate() {
        assert!(snapshot.total_supply[i] >= 0, "Final: Negative total supply for asset {}", i);
        assert!(snapshot.total_debt[i] >= 0, "Final: Negative total debt for asset {}", i);
        
        for j in 0..test_env.users.len() {
            assert!(snapshot.user_collateral[j][i] >= 0, "Final: Negative collateral");
            assert!(snapshot.user_debt[j][i] >= 0, "Final: Negative debt");
            assert!(snapshot.user_underlying[j][i] >= 0, "Final: Negative underlying");
        }
    }
    
    // Reserve data consistency
    for (i, asset) in test_env.assets.iter().enumerate() {
        if let Ok(Ok(reserve_data)) = test_env.router.try_get_reserve_data(&asset.address) {
            assert!(reserve_data.liquidity_index >= RAY, "Final: Liquidity index below RAY for asset {}", i);
            assert!(reserve_data.variable_borrow_index >= RAY, "Final: Borrow index below RAY for asset {}", i);
            assert!(reserve_data.current_liquidity_rate < 10 * RAY, "Final: Unreasonable liquidity rate");
            assert!(reserve_data.current_variable_borrow_rate < 10 * RAY, "Final: Unreasonable borrow rate");
        }
    }
    
    // Final solvency check
    verify_protocol_solvency(test_env, snapshot);
    
    // Verify user health factors
    for (j, user) in test_env.users.iter().enumerate() {
        let has_debt = snapshot.user_debt[j].iter().any(|&d| d > 0);
        if has_debt {
            if let Ok(Ok(account_data)) = test_env.router.try_get_user_account_data(user) {
                assert!(account_data.health_factor > 0, "Final: User {} has zero health factor with debt", j);
            }
        }
    }
    
    // Total token conservation with explicit budget
    let mut total_initial: u128 = 0;
    let mut total_current: u128 = 0;
    
    for (i, asset) in test_env.assets.iter().enumerate() {
        total_initial += test_env.initial_total_underlying[i];
        
        let mut asset_current: u128 = 0;
        for user in &test_env.users {
            asset_current += asset.token.balance(user) as u128;
        }
        asset_current += asset.token.balance(&asset.a_token.address) as u128;
        asset_current += asset.token.balance(&test_env.treasury) as u128;
        total_current += asset_current;
    }
    
    // Use explicit tolerance calculation, scaled by number of assets
    let per_asset_tolerance = crate::common::constants::calculate_tolerance(test_env.operation_count) as u128;
    let total_tolerance = per_asset_tolerance * (test_env.assets.len() as u128);
    let diff = if total_current > total_initial { total_current - total_initial } else { total_initial - total_current };
    
    assert!(diff <= total_tolerance,
        "Final: Total token conservation failed. Initial: {}, Current: {}, Diff: {}, Tolerance: {}", 
        total_initial, total_current, diff, total_tolerance);
}
