#![no_main]

mod common;

use libfuzzer_sys::fuzz_target;
use soroban_sdk::Env;
use std::sync::atomic::{AtomicU64, Ordering};

use common::{
    Input, TestEnv, ProtocolSnapshot,
    execute_operation,
    verify_operation_invariants, verify_protocol_invariants, verify_protocol_solvency,
    verify_treasury_accrual, verify_interest_invariants, verify_interest_math,
    verify_utilization_invariants, verify_liquidation_invariants,
    verify_final_invariants, verify_cumulative_rounding,
    verify_index_monotonicity, verify_debt_ceiling_invariants,
    verify_liquidation_bonus_invariants, verify_reserve_factor_invariants,
    verify_pause_state_invariant, verify_access_control_invariants,
    verify_flash_loan_premium, verify_flash_loan_repayment,
    verify_accrued_to_treasury_monotonicity,
    verify_fee_calculation_invariants, verify_no_value_extraction,
    verify_liquidation_fairness, verify_no_rate_manipulation,
    verify_admin_cannot_steal, verify_parameter_bounds, verify_oracle_sanity,
    verify_failed_operation_unchanged, verify_no_dust_accumulation,
    MAX_ROUNDING_PER_OP, ROUNDING_TRACK_MULTIPLIER,
    operations::{Operation, FlashLoanReceiverType},
    stats::{STATS, INVARIANT_STATS, InvariantType, stats_enabled},
};

/// Counter for periodic stats printing
static RUN_COUNT: AtomicU64 = AtomicU64::new(0);

fuzz_target!(|input: Input| {
    let env = Env::default();
    let track_stats = stats_enabled();
    
    let mut test_env = match TestEnv::new(&env, &input) {
        Some(e) => e,
        None => return,
    };
    
    let mut last_snapshot = ProtocolSnapshot::capture(&test_env);
    let mut last_timestamp = env.ledger().timestamp();
    
    for op in &input.operations {
        let before = ProtocolSnapshot::capture(&test_env);
        let success = execute_operation(&mut test_env, op);
        let after = ProtocolSnapshot::capture(&test_env);
        
        // Track operation statistics if enabled
        if track_stats {
            STATS.record_operation(op, success);
        }
        
        test_env.increment_operation_count();
        
        // Track rounding errors per asset
        // We track errors up to ROUNDING_TRACK_MULTIPLIER * MAX_ROUNDING_PER_OP
        // to catch legitimate rounding while flagging potential exploits
        for i in 0..test_env.assets.len() {
            let before_total = before.total_supply[i] + before.total_debt[i];
            let after_total = after.total_supply[i] + after.total_debt[i];
            let diff = (after_total - before_total).abs();
            if diff > 0 && diff < MAX_ROUNDING_PER_OP * ROUNDING_TRACK_MULTIPLIER {
                test_env.track_rounding_error(i, diff);
            }
        }
        
        // Core invariants - checked after every operation
        verify_operation_invariants(&test_env, op, &before, &after, success);
        if track_stats { INVARIANT_STATS.record(InvariantType::OperationInvariants); }
        
        // Verify failed operations don't modify state
        if !success {
            verify_failed_operation_unchanged(&test_env, &before, &after);
            if track_stats { INVARIANT_STATS.record(InvariantType::FailedOperationUnchanged); }
        }
        verify_protocol_invariants(&test_env, &after);
        if track_stats { INVARIANT_STATS.record(InvariantType::ProtocolInvariants); }
        verify_protocol_solvency(&test_env, &after);
        if track_stats { INVARIANT_STATS.record(InvariantType::ProtocolSolvency); }
        verify_treasury_accrual(&test_env, &before, &after);
        if track_stats { INVARIANT_STATS.record(InvariantType::TreasuryAccrual); }
        verify_utilization_invariants(&test_env, &after);
        if track_stats { INVARIANT_STATS.record(InvariantType::UtilizationInvariants); }
        verify_liquidation_invariants(&test_env, &after);
        if track_stats { INVARIANT_STATS.record(InvariantType::LiquidationInvariants); }
        
        // Flash loan specific invariants
        match op {
            Operation::FlashLoan { asset_idx, amount_percent, receiver_type, .. } => {
                if matches!(receiver_type, FlashLoanReceiverType::Standard) {
                    let available = before.available_liquidity[(*asset_idx as usize) % test_env.assets.len()];
                    let amount = ((available as u128) * (*amount_percent as u128) / 100).max(1);
                    verify_flash_loan_premium(&test_env, &before, &after, *asset_idx as usize, amount, success);
                    if track_stats { INVARIANT_STATS.record(InvariantType::FlashLoanPremium); }
                }
                verify_flash_loan_repayment(&test_env, &before, &after, *asset_idx as usize, success);
                if track_stats { INVARIANT_STATS.record(InvariantType::FlashLoanRepayment); }
            }
            Operation::MultiAssetFlashLoan { asset_indices, receiver_type, .. } => {
                if matches!(receiver_type, FlashLoanReceiverType::Standard) {
                    for &asset_idx in asset_indices.iter() {
                        verify_flash_loan_repayment(&test_env, &before, &after, asset_idx as usize, success);
                        if track_stats { INVARIANT_STATS.record(InvariantType::FlashLoanRepayment); }
                    }
                }
            }
            _ => {}
        }
        
        // Index monotonicity - indices should only increase
        verify_index_monotonicity(&test_env, &before, &after);
        if track_stats { INVARIANT_STATS.record(InvariantType::IndexMonotonicity); }
        
        // Accrued to treasury monotonicity - should never decrease (except to 0 on collection)
        verify_accrued_to_treasury_monotonicity(&test_env, &before, &after);
        if track_stats { INVARIANT_STATS.record(InvariantType::AccruedTreasuryMonotonicity); }
        
        // Debt ceiling enforcement
        verify_debt_ceiling_invariants(&test_env, &after);
        if track_stats { INVARIANT_STATS.record(InvariantType::DebtCeilingInvariants); }
        
        // Reserve factor validation
        verify_reserve_factor_invariants(&test_env, &before, &after);
        if track_stats { INVARIANT_STATS.record(InvariantType::ReserveFactorInvariants); }
        
        // Time-dependent invariants
        let current_timestamp = env.ledger().timestamp();
        if current_timestamp > last_timestamp {
            verify_interest_invariants(&test_env);
            if track_stats { INVARIANT_STATS.record(InvariantType::InterestInvariants); }
            verify_interest_math(&test_env, &before, &after);
            if track_stats { INVARIANT_STATS.record(InvariantType::InterestMath); }
            // Fee calculation checks when time passes (interest accrues)
            verify_fee_calculation_invariants(&test_env, &before, &after);
            if track_stats { INVARIANT_STATS.record(InvariantType::FeeCalculationInvariants); }
            last_timestamp = current_timestamp;
        }
        
        // Liquidation-specific fairness check
        match op {
            Operation::Liquidate { liquidator_idx, user_idx, collateral_idx, debt_idx, .. } 
            | Operation::LiquidateReceiveAToken { liquidator_idx, user_idx, collateral_idx, debt_idx, .. } => {
                verify_liquidation_fairness(
                    &test_env, &before, &after,
                    *liquidator_idx as usize, *user_idx as usize,
                    *collateral_idx as usize, *debt_idx as usize,
                    success
                );
                if track_stats { INVARIANT_STATS.record(InvariantType::LiquidationFairness); }
            }
            Operation::MultiAssetLiquidation { liquidator_idx, user_idx, collateral_idx, debt_idx, .. } 
            | Operation::CreateAndLiquidate { liquidator_idx, user_idx, collateral_idx, debt_idx } => {
                verify_liquidation_fairness(
                    &test_env, &before, &after,
                    *liquidator_idx as usize, *user_idx as usize,
                    *collateral_idx as usize, *debt_idx as usize,
                    success
                );
                if track_stats { INVARIANT_STATS.record(InvariantType::LiquidationFairness); }
            }
            _ => {}
        }
        
        // Rate manipulation detection
        verify_no_rate_manipulation(&test_env, &before, &after);
        if track_stats { INVARIANT_STATS.record(InvariantType::NoRateManipulation); }
        
        // Oracle sanity checks
        verify_oracle_sanity(&test_env, &before, &after);
        if track_stats { INVARIANT_STATS.record(InvariantType::OracleSanity); }
        
        // Economic exploit detection - check every 5 operations to reduce overhead
        if test_env.operation_count % 5 == 0 {
            verify_no_value_extraction(&test_env, &before, &after);
            if track_stats { INVARIANT_STATS.record(InvariantType::NoValueExtraction); }
            verify_admin_cannot_steal(&test_env, &before, &after);
            if track_stats { INVARIANT_STATS.record(InvariantType::AdminCannotSteal); }
        }
        
        last_snapshot = after;
    }
    
    // Final comprehensive checks
    verify_final_invariants(&test_env, &last_snapshot);
    if track_stats { INVARIANT_STATS.record(InvariantType::FinalInvariants); }
    verify_cumulative_rounding(&test_env);
    if track_stats { INVARIANT_STATS.record(InvariantType::CumulativeRounding); }
    verify_no_dust_accumulation(&test_env, &last_snapshot);
    if track_stats { INVARIANT_STATS.record(InvariantType::DustAccumulation); }
    
    // Configuration invariants - checked at end
    verify_liquidation_bonus_invariants(&test_env);
    if track_stats { INVARIANT_STATS.record(InvariantType::LiquidationBonusInvariants); }
    verify_pause_state_invariant(&test_env);
    if track_stats { INVARIANT_STATS.record(InvariantType::PauseStateInvariant); }
    verify_access_control_invariants(&test_env);
    if track_stats { INVARIANT_STATS.record(InvariantType::AccessControlInvariants); }
    verify_parameter_bounds(&test_env);
    if track_stats { INVARIANT_STATS.record(InvariantType::ParameterBounds); }
    
    // Print stats periodically
    let count = RUN_COUNT.fetch_add(1, Ordering::Relaxed) + 1;
    if count == 1 {
        eprintln!("\n[FUZZ] Stats tracking enabled - will print every 100 successful runs");
    }
    if count % 100 == 0 {
        eprintln!("\n[FUZZ] === {} successful fuzz runs completed ===", count);
        STATS.print_summary();
        INVARIANT_STATS.print_summary();
    }
});
