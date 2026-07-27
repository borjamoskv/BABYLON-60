use std::sync::atomic::{AtomicU64, Ordering};
use crate::common::operations::Operation;

pub struct OperationStats {
    pub supply: AtomicU64,
    pub supply_on_behalf: AtomicU64,
    pub withdraw: AtomicU64,
    pub withdraw_all: AtomicU64,
    pub withdraw_to_recipient: AtomicU64,
    pub borrow: AtomicU64,
    pub borrow_to_recipient: AtomicU64,
    pub repay: AtomicU64,
    pub repay_all: AtomicU64,
    pub repay_on_behalf: AtomicU64,
    pub set_collateral: AtomicU64,
    pub time_warp: AtomicU64,
    pub extreme_time_warp: AtomicU64,
    pub price_change: AtomicU64,
    pub liquidate: AtomicU64,
    pub liquidate_receive_a_token: AtomicU64,
    pub prepare_liquidation: AtomicU64,
    pub execute_liquidation: AtomicU64,
    pub full_multi_asset_liquidation: AtomicU64,
    pub create_and_liquidate: AtomicU64,
    pub flash_loan: AtomicU64,
    pub multi_asset_flash_loan: AtomicU64,
    pub zero_amount_ops: AtomicU64,
    pub dust_ops: AtomicU64,
    pub max_amount_ops: AtomicU64,
    pub price_to_zero: AtomicU64,
    pub price_to_max: AtomicU64,
    pub oracle_stale: AtomicU64,
    pub price_volatility: AtomicU64,
    pub pause_protocol: AtomicU64,
    pub unpause_protocol: AtomicU64,
    pub collect_reserves: AtomicU64,
    pub self_liquidation_attempt: AtomicU64,
    pub multi_asset_liquidation: AtomicU64,
    pub rapid_supply_withdraw: AtomicU64,
    pub rapid_borrow_repay: AtomicU64,
    pub sandwich_price_change: AtomicU64,
    pub interest_accrual_exploit: AtomicU64,
    pub first_depositor_attack: AtomicU64,
    pub donation_attack: AtomicU64,
    pub update_reserve_config: AtomicU64,
    pub update_rate_strategy: AtomicU64,
    pub drop_reserve: AtomicU64,
    pub set_caps: AtomicU64,
    pub whitelist_blacklist: AtomicU64,
    pub admin_transfer: AtomicU64,
    pub swap_collateral: AtomicU64,
    pub transfer_a_token: AtomicU64,
    pub drain_liquidity: AtomicU64,
    pub max_utilization: AtomicU64,
    pub bad_debt_scenario: AtomicU64,
    pub reserve_state_ops: AtomicU64,
    pub flash_loan_while_paused: AtomicU64,
    pub dangerous_sequences: AtomicU64,
    pub total_ops: AtomicU64,
    pub successful_ops: AtomicU64,
}

impl OperationStats {
    pub const fn new() -> Self {
        Self {
            supply: AtomicU64::new(0),
            supply_on_behalf: AtomicU64::new(0),
            withdraw: AtomicU64::new(0),
            withdraw_all: AtomicU64::new(0),
            withdraw_to_recipient: AtomicU64::new(0),
            borrow: AtomicU64::new(0),
            borrow_to_recipient: AtomicU64::new(0),
            repay: AtomicU64::new(0),
            repay_all: AtomicU64::new(0),
            repay_on_behalf: AtomicU64::new(0),
            set_collateral: AtomicU64::new(0),
            time_warp: AtomicU64::new(0),
            extreme_time_warp: AtomicU64::new(0),
            price_change: AtomicU64::new(0),
            liquidate: AtomicU64::new(0),
            liquidate_receive_a_token: AtomicU64::new(0),
            prepare_liquidation: AtomicU64::new(0),
            execute_liquidation: AtomicU64::new(0),
            full_multi_asset_liquidation: AtomicU64::new(0),
            create_and_liquidate: AtomicU64::new(0),
            flash_loan: AtomicU64::new(0),
            multi_asset_flash_loan: AtomicU64::new(0),
            zero_amount_ops: AtomicU64::new(0),
            dust_ops: AtomicU64::new(0),
            max_amount_ops: AtomicU64::new(0),
            price_to_zero: AtomicU64::new(0),
            price_to_max: AtomicU64::new(0),
            oracle_stale: AtomicU64::new(0),
            price_volatility: AtomicU64::new(0),
            pause_protocol: AtomicU64::new(0),
            unpause_protocol: AtomicU64::new(0),
            collect_reserves: AtomicU64::new(0),
            self_liquidation_attempt: AtomicU64::new(0),
            multi_asset_liquidation: AtomicU64::new(0),
            rapid_supply_withdraw: AtomicU64::new(0),
            rapid_borrow_repay: AtomicU64::new(0),
            sandwich_price_change: AtomicU64::new(0),
            interest_accrual_exploit: AtomicU64::new(0),
            first_depositor_attack: AtomicU64::new(0),
            donation_attack: AtomicU64::new(0),
            update_reserve_config: AtomicU64::new(0),
            update_rate_strategy: AtomicU64::new(0),
            drop_reserve: AtomicU64::new(0),
            set_caps: AtomicU64::new(0),
            whitelist_blacklist: AtomicU64::new(0),
            admin_transfer: AtomicU64::new(0),
            swap_collateral: AtomicU64::new(0),
            transfer_a_token: AtomicU64::new(0),
            drain_liquidity: AtomicU64::new(0),
            max_utilization: AtomicU64::new(0),
            bad_debt_scenario: AtomicU64::new(0),
            reserve_state_ops: AtomicU64::new(0),
            flash_loan_while_paused: AtomicU64::new(0),
            dangerous_sequences: AtomicU64::new(0),
            total_ops: AtomicU64::new(0),
            successful_ops: AtomicU64::new(0),
        }
    }
    
    pub fn record_operation(&self, op: &Operation, success: bool) {
        self.total_ops.fetch_add(1, Ordering::Relaxed);
        if success {
            self.successful_ops.fetch_add(1, Ordering::Relaxed);
        }
        
        match op {
            Operation::Supply { .. } => self.supply.fetch_add(1, Ordering::Relaxed),
            Operation::SupplyOnBehalf { .. } => self.supply_on_behalf.fetch_add(1, Ordering::Relaxed),
            Operation::Withdraw { .. } => self.withdraw.fetch_add(1, Ordering::Relaxed),
            Operation::WithdrawAll { .. } => self.withdraw_all.fetch_add(1, Ordering::Relaxed),
            Operation::WithdrawToRecipient { .. } => self.withdraw_to_recipient.fetch_add(1, Ordering::Relaxed),
            Operation::Borrow { .. } => self.borrow.fetch_add(1, Ordering::Relaxed),
            Operation::BorrowToRecipient { .. } => self.borrow_to_recipient.fetch_add(1, Ordering::Relaxed),
            Operation::Repay { .. } => self.repay.fetch_add(1, Ordering::Relaxed),
            Operation::RepayAll { .. } => self.repay_all.fetch_add(1, Ordering::Relaxed),
            Operation::RepayOnBehalf { .. } => self.repay_on_behalf.fetch_add(1, Ordering::Relaxed),
            Operation::SetCollateral { .. } => self.set_collateral.fetch_add(1, Ordering::Relaxed),
            Operation::TimeWarp { .. } => self.time_warp.fetch_add(1, Ordering::Relaxed),
            Operation::ExtremeTimeWarp { .. } => self.extreme_time_warp.fetch_add(1, Ordering::Relaxed),
            Operation::PriceChange { .. } => self.price_change.fetch_add(1, Ordering::Relaxed),
            Operation::Liquidate { .. } => self.liquidate.fetch_add(1, Ordering::Relaxed),
            Operation::LiquidateReceiveAToken { .. } => self.liquidate_receive_a_token.fetch_add(1, Ordering::Relaxed),
            Operation::PrepareLiquidation { .. } => self.prepare_liquidation.fetch_add(1, Ordering::Relaxed),
            Operation::ExecuteLiquidation { .. } => self.execute_liquidation.fetch_add(1, Ordering::Relaxed),
            Operation::FullMultiAssetLiquidation { .. } => self.full_multi_asset_liquidation.fetch_add(1, Ordering::Relaxed),
            Operation::CreateAndLiquidate { .. } => self.create_and_liquidate.fetch_add(1, Ordering::Relaxed),
            Operation::FlashLoan { .. } => self.flash_loan.fetch_add(1, Ordering::Relaxed),
            Operation::MultiAssetFlashLoan { .. } => self.multi_asset_flash_loan.fetch_add(1, Ordering::Relaxed),
            Operation::ZeroAmountSupply { .. } | Operation::ZeroAmountBorrow { .. } | 
            Operation::ZeroAmountWithdraw { .. } | Operation::ZeroAmountRepay { .. } => {
                self.zero_amount_ops.fetch_add(1, Ordering::Relaxed)
            },
            Operation::DustSupply { .. } | Operation::DustBorrow { .. } |
            Operation::DustWithdraw { .. } | Operation::DustRepay { .. } => {
                self.dust_ops.fetch_add(1, Ordering::Relaxed)
            },
            Operation::MaxAmountSupply { .. } | Operation::MaxAmountBorrow { .. } => {
                self.max_amount_ops.fetch_add(1, Ordering::Relaxed)
            },
            Operation::PriceToZero { .. } => self.price_to_zero.fetch_add(1, Ordering::Relaxed),
            Operation::PriceToMax { .. } => self.price_to_max.fetch_add(1, Ordering::Relaxed),
            Operation::OracleStale { .. } => self.oracle_stale.fetch_add(1, Ordering::Relaxed),
            Operation::PriceVolatility { .. } => self.price_volatility.fetch_add(1, Ordering::Relaxed),
            Operation::PauseProtocol => self.pause_protocol.fetch_add(1, Ordering::Relaxed),
            Operation::UnpauseProtocol => self.unpause_protocol.fetch_add(1, Ordering::Relaxed),
            Operation::CollectProtocolReserves { .. } => self.collect_reserves.fetch_add(1, Ordering::Relaxed),
            Operation::SelfLiquidationAttempt { .. } => self.self_liquidation_attempt.fetch_add(1, Ordering::Relaxed),
            Operation::MultiAssetLiquidation { .. } => self.multi_asset_liquidation.fetch_add(1, Ordering::Relaxed),
            Operation::RapidSupplyWithdraw { .. } => self.rapid_supply_withdraw.fetch_add(1, Ordering::Relaxed),
            Operation::RapidBorrowRepay { .. } => self.rapid_borrow_repay.fetch_add(1, Ordering::Relaxed),
            Operation::SandwichPriceChange { .. } => self.sandwich_price_change.fetch_add(1, Ordering::Relaxed),
            Operation::InterestAccrualExploit { .. } => self.interest_accrual_exploit.fetch_add(1, Ordering::Relaxed),
            Operation::FirstDepositorAttack { .. } => self.first_depositor_attack.fetch_add(1, Ordering::Relaxed),
            Operation::DonationAttack { .. } => self.donation_attack.fetch_add(1, Ordering::Relaxed),
            Operation::UpdateReserveConfiguration { .. } => self.update_reserve_config.fetch_add(1, Ordering::Relaxed),
            Operation::UpdateReserveRateStrategy { .. } => self.update_rate_strategy.fetch_add(1, Ordering::Relaxed),
            Operation::DropReserve { .. } => self.drop_reserve.fetch_add(1, Ordering::Relaxed),
            Operation::SetReserveSupplyCap { .. } | Operation::SetReserveBorrowCap { .. } |
            Operation::SetReserveDebtCeiling { .. } => self.set_caps.fetch_add(1, Ordering::Relaxed),
            Operation::SetReserveWhitelist { .. } | Operation::SetReserveBlacklist { .. } |
            Operation::SetLiquidationWhitelist { .. } | Operation::SetLiquidationBlacklist { .. } => {
                self.whitelist_blacklist.fetch_add(1, Ordering::Relaxed)
            },
            Operation::ProposePoolAdmin { .. } | Operation::AcceptPoolAdmin { .. } => {
                self.admin_transfer.fetch_add(1, Ordering::Relaxed)
            },
            Operation::SwapCollateral { .. } => self.swap_collateral.fetch_add(1, Ordering::Relaxed),
            Operation::TransferAToken { .. } => self.transfer_a_token.fetch_add(1, Ordering::Relaxed),
            Operation::DrainLiquidity { .. } => self.drain_liquidity.fetch_add(1, Ordering::Relaxed),
            Operation::MaxUtilization { .. } => self.max_utilization.fetch_add(1, Ordering::Relaxed),
            Operation::BadDebtScenario { .. } => self.bad_debt_scenario.fetch_add(1, Ordering::Relaxed),
            Operation::SetReserveActive { .. } | Operation::SetReserveFrozen { .. } => {
                self.reserve_state_ops.fetch_add(1, Ordering::Relaxed)
            },
            Operation::FlashLoanWhilePaused { .. } => self.flash_loan_while_paused.fetch_add(1, Ordering::Relaxed),
            Operation::BorrowMaxWithdrawAttempt { .. } | Operation::PriceCrashLiquidation { .. } => {
                self.dangerous_sequences.fetch_add(1, Ordering::Relaxed)
            },
        };
    }
    
    /// Print statistics summary (call at end of fuzzing or periodically)
    pub fn print_summary(&self) {
        let total = self.total_ops.load(Ordering::Relaxed);
        let successful = self.successful_ops.load(Ordering::Relaxed);
        
        if total == 0 {
            return;
        }
        
        eprintln!("\n========== FUZZER OPERATION STATISTICS ==========");
        eprintln!("Total operations: {} ({}% success rate)", total, successful * 100 / total);
        eprintln!();
        
        eprintln!("--- Core Operations ---");
        self.print_stat("Supply", self.supply.load(Ordering::Relaxed), total);
        self.print_stat("SupplyOnBehalf", self.supply_on_behalf.load(Ordering::Relaxed), total);
        self.print_stat("Withdraw", self.withdraw.load(Ordering::Relaxed), total);
        self.print_stat("WithdrawAll", self.withdraw_all.load(Ordering::Relaxed), total);
        self.print_stat("Borrow", self.borrow.load(Ordering::Relaxed), total);
        self.print_stat("Repay", self.repay.load(Ordering::Relaxed), total);
        self.print_stat("RepayAll", self.repay_all.load(Ordering::Relaxed), total);
        
        eprintln!("\n--- Liquidation Operations ---");
        self.print_stat("Liquidate", self.liquidate.load(Ordering::Relaxed), total);
        self.print_stat("LiquidateReceiveAToken", self.liquidate_receive_a_token.load(Ordering::Relaxed), total);
        self.print_stat("PrepareLiquidation", self.prepare_liquidation.load(Ordering::Relaxed), total);
        self.print_stat("ExecuteLiquidation", self.execute_liquidation.load(Ordering::Relaxed), total);
        self.print_stat("FullMultiAssetLiquidation", self.full_multi_asset_liquidation.load(Ordering::Relaxed), total);
        self.print_stat("CreateAndLiquidate", self.create_and_liquidate.load(Ordering::Relaxed), total);
        self.print_stat("MultiAssetLiquidation", self.multi_asset_liquidation.load(Ordering::Relaxed), total);
        self.print_stat("SelfLiquidationAttempt", self.self_liquidation_attempt.load(Ordering::Relaxed), total);
        
        eprintln!("\n--- Flash Loan Operations ---");
        self.print_stat("FlashLoan", self.flash_loan.load(Ordering::Relaxed), total);
        self.print_stat("MultiAssetFlashLoan", self.multi_asset_flash_loan.load(Ordering::Relaxed), total);
        self.print_stat("FlashLoanWhilePaused", self.flash_loan_while_paused.load(Ordering::Relaxed), total);
        
        eprintln!("\n--- Edge Cases ---");
        self.print_stat("ZeroAmountOps", self.zero_amount_ops.load(Ordering::Relaxed), total);
        self.print_stat("DustOps", self.dust_ops.load(Ordering::Relaxed), total);
        self.print_stat("MaxAmountOps", self.max_amount_ops.load(Ordering::Relaxed), total);
        
        eprintln!("\n--- Oracle Operations ---");
        self.print_stat("PriceChange", self.price_change.load(Ordering::Relaxed), total);
        self.print_stat("PriceToZero", self.price_to_zero.load(Ordering::Relaxed), total);
        self.print_stat("PriceToMax", self.price_to_max.load(Ordering::Relaxed), total);
        self.print_stat("OracleStale", self.oracle_stale.load(Ordering::Relaxed), total);
        self.print_stat("PriceVolatility", self.price_volatility.load(Ordering::Relaxed), total);
        
        eprintln!("\n--- Adversarial Patterns ---");
        self.print_stat("RapidSupplyWithdraw", self.rapid_supply_withdraw.load(Ordering::Relaxed), total);
        self.print_stat("RapidBorrowRepay", self.rapid_borrow_repay.load(Ordering::Relaxed), total);
        self.print_stat("SandwichPriceChange", self.sandwich_price_change.load(Ordering::Relaxed), total);
        self.print_stat("InterestAccrualExploit", self.interest_accrual_exploit.load(Ordering::Relaxed), total);
        self.print_stat("FirstDepositorAttack", self.first_depositor_attack.load(Ordering::Relaxed), total);
        self.print_stat("DonationAttack", self.donation_attack.load(Ordering::Relaxed), total);
        self.print_stat("BadDebtScenario", self.bad_debt_scenario.load(Ordering::Relaxed), total);
        self.print_stat("DangerousSequences", self.dangerous_sequences.load(Ordering::Relaxed), total);
        
        eprintln!("\n--- Admin Operations ---");
        self.print_stat("UpdateReserveConfig", self.update_reserve_config.load(Ordering::Relaxed), total);
        self.print_stat("UpdateRateStrategy", self.update_rate_strategy.load(Ordering::Relaxed), total);
        self.print_stat("DropReserve", self.drop_reserve.load(Ordering::Relaxed), total);
        self.print_stat("SetCaps", self.set_caps.load(Ordering::Relaxed), total);
        self.print_stat("WhitelistBlacklist", self.whitelist_blacklist.load(Ordering::Relaxed), total);
        self.print_stat("AdminTransfer", self.admin_transfer.load(Ordering::Relaxed), total);
        
        eprintln!("\n--- Environmental ---");
        self.print_stat("TimeWarp", self.time_warp.load(Ordering::Relaxed), total);
        self.print_stat("ExtremeTimeWarp", self.extreme_time_warp.load(Ordering::Relaxed), total);
        self.print_stat("PauseProtocol", self.pause_protocol.load(Ordering::Relaxed), total);
        self.print_stat("UnpauseProtocol", self.unpause_protocol.load(Ordering::Relaxed), total);
        
        eprintln!("\n--- Other ---");
        self.print_stat("SwapCollateral", self.swap_collateral.load(Ordering::Relaxed), total);
        self.print_stat("TransferAToken", self.transfer_a_token.load(Ordering::Relaxed), total);
        self.print_stat("DrainLiquidity", self.drain_liquidity.load(Ordering::Relaxed), total);
        self.print_stat("MaxUtilization", self.max_utilization.load(Ordering::Relaxed), total);
        
        eprintln!("==================================================\n");
    }
    
    fn print_stat(&self, name: &str, count: u64, total: u64) {
        if count > 0 {
            let pct = count * 100 / total;
            eprintln!("  {:30} {:>8} ({:>2}%)", name, count, pct);
        }
    }
}

pub static STATS: OperationStats = OperationStats::new();

pub fn stats_enabled() -> bool {
    true
}

pub struct InvariantStats {
    pub operation_invariants: AtomicU64,
    pub protocol_invariants: AtomicU64,
    pub protocol_solvency: AtomicU64,
    pub treasury_accrual: AtomicU64,
    pub utilization_invariants: AtomicU64,
    pub liquidation_invariants: AtomicU64,
    pub index_monotonicity: AtomicU64,
    pub accrued_treasury_monotonicity: AtomicU64,
    pub debt_ceiling_invariants: AtomicU64,
    pub reserve_factor_invariants: AtomicU64,
    pub interest_invariants: AtomicU64,
    pub interest_math: AtomicU64,
    pub fee_calculation_invariants: AtomicU64,
    pub flash_loan_premium: AtomicU64,
    pub flash_loan_repayment: AtomicU64,
    pub liquidation_fairness: AtomicU64,
    pub no_rate_manipulation: AtomicU64,
    pub oracle_sanity: AtomicU64,
    pub no_value_extraction: AtomicU64,
    pub admin_cannot_steal: AtomicU64,
    pub final_invariants: AtomicU64,
    pub cumulative_rounding: AtomicU64,
    pub liquidation_bonus_invariants: AtomicU64,
    pub pause_state_invariant: AtomicU64,
    pub access_control_invariants: AtomicU64,
    pub parameter_bounds: AtomicU64,
    pub failed_operation_unchanged: AtomicU64,
    pub dust_accumulation: AtomicU64,
}

impl InvariantStats {
    pub const fn new() -> Self {
        Self {
            operation_invariants: AtomicU64::new(0),
            protocol_invariants: AtomicU64::new(0),
            protocol_solvency: AtomicU64::new(0),
            treasury_accrual: AtomicU64::new(0),
            utilization_invariants: AtomicU64::new(0),
            liquidation_invariants: AtomicU64::new(0),
            index_monotonicity: AtomicU64::new(0),
            accrued_treasury_monotonicity: AtomicU64::new(0),
            debt_ceiling_invariants: AtomicU64::new(0),
            reserve_factor_invariants: AtomicU64::new(0),
            interest_invariants: AtomicU64::new(0),
            interest_math: AtomicU64::new(0),
            fee_calculation_invariants: AtomicU64::new(0),
            flash_loan_premium: AtomicU64::new(0),
            flash_loan_repayment: AtomicU64::new(0),
            liquidation_fairness: AtomicU64::new(0),
            no_rate_manipulation: AtomicU64::new(0),
            oracle_sanity: AtomicU64::new(0),
            no_value_extraction: AtomicU64::new(0),
            admin_cannot_steal: AtomicU64::new(0),
            final_invariants: AtomicU64::new(0),
            cumulative_rounding: AtomicU64::new(0),
            liquidation_bonus_invariants: AtomicU64::new(0),
            pause_state_invariant: AtomicU64::new(0),
            access_control_invariants: AtomicU64::new(0),
            parameter_bounds: AtomicU64::new(0),
            failed_operation_unchanged: AtomicU64::new(0),
            dust_accumulation: AtomicU64::new(0),
        }
    }
    
    pub fn record(&self, invariant: InvariantType) {
        match invariant {
            InvariantType::OperationInvariants => self.operation_invariants.fetch_add(1, Ordering::Relaxed),
            InvariantType::ProtocolInvariants => self.protocol_invariants.fetch_add(1, Ordering::Relaxed),
            InvariantType::ProtocolSolvency => self.protocol_solvency.fetch_add(1, Ordering::Relaxed),
            InvariantType::TreasuryAccrual => self.treasury_accrual.fetch_add(1, Ordering::Relaxed),
            InvariantType::UtilizationInvariants => self.utilization_invariants.fetch_add(1, Ordering::Relaxed),
            InvariantType::LiquidationInvariants => self.liquidation_invariants.fetch_add(1, Ordering::Relaxed),
            InvariantType::IndexMonotonicity => self.index_monotonicity.fetch_add(1, Ordering::Relaxed),
            InvariantType::AccruedTreasuryMonotonicity => self.accrued_treasury_monotonicity.fetch_add(1, Ordering::Relaxed),
            InvariantType::DebtCeilingInvariants => self.debt_ceiling_invariants.fetch_add(1, Ordering::Relaxed),
            InvariantType::ReserveFactorInvariants => self.reserve_factor_invariants.fetch_add(1, Ordering::Relaxed),
            InvariantType::InterestInvariants => self.interest_invariants.fetch_add(1, Ordering::Relaxed),
            InvariantType::InterestMath => self.interest_math.fetch_add(1, Ordering::Relaxed),
            InvariantType::FeeCalculationInvariants => self.fee_calculation_invariants.fetch_add(1, Ordering::Relaxed),
            InvariantType::FlashLoanPremium => self.flash_loan_premium.fetch_add(1, Ordering::Relaxed),
            InvariantType::FlashLoanRepayment => self.flash_loan_repayment.fetch_add(1, Ordering::Relaxed),
            InvariantType::LiquidationFairness => self.liquidation_fairness.fetch_add(1, Ordering::Relaxed),
            InvariantType::NoRateManipulation => self.no_rate_manipulation.fetch_add(1, Ordering::Relaxed),
            InvariantType::OracleSanity => self.oracle_sanity.fetch_add(1, Ordering::Relaxed),
            InvariantType::NoValueExtraction => self.no_value_extraction.fetch_add(1, Ordering::Relaxed),
            InvariantType::AdminCannotSteal => self.admin_cannot_steal.fetch_add(1, Ordering::Relaxed),
            InvariantType::FinalInvariants => self.final_invariants.fetch_add(1, Ordering::Relaxed),
            InvariantType::CumulativeRounding => self.cumulative_rounding.fetch_add(1, Ordering::Relaxed),
            InvariantType::LiquidationBonusInvariants => self.liquidation_bonus_invariants.fetch_add(1, Ordering::Relaxed),
            InvariantType::PauseStateInvariant => self.pause_state_invariant.fetch_add(1, Ordering::Relaxed),
            InvariantType::AccessControlInvariants => self.access_control_invariants.fetch_add(1, Ordering::Relaxed),
            InvariantType::ParameterBounds => self.parameter_bounds.fetch_add(1, Ordering::Relaxed),
            InvariantType::FailedOperationUnchanged => self.failed_operation_unchanged.fetch_add(1, Ordering::Relaxed),
            InvariantType::DustAccumulation => self.dust_accumulation.fetch_add(1, Ordering::Relaxed),
        };
    }
    
    pub fn print_summary(&self) {
        eprintln!("\n========== INVARIANT EXECUTION STATISTICS ==========");
        
        eprintln!("\n--- Core Invariants (every operation) ---");
        self.print_invariant("OperationInvariants", self.operation_invariants.load(Ordering::Relaxed));
        self.print_invariant("ProtocolInvariants", self.protocol_invariants.load(Ordering::Relaxed));
        self.print_invariant("ProtocolSolvency", self.protocol_solvency.load(Ordering::Relaxed));
        self.print_invariant("TreasuryAccrual", self.treasury_accrual.load(Ordering::Relaxed));
        self.print_invariant("UtilizationInvariants", self.utilization_invariants.load(Ordering::Relaxed));
        self.print_invariant("LiquidationInvariants", self.liquidation_invariants.load(Ordering::Relaxed));
        self.print_invariant("IndexMonotonicity", self.index_monotonicity.load(Ordering::Relaxed));
        self.print_invariant("AccruedTreasuryMonotonicity", self.accrued_treasury_monotonicity.load(Ordering::Relaxed));
        self.print_invariant("DebtCeilingInvariants", self.debt_ceiling_invariants.load(Ordering::Relaxed));
        self.print_invariant("ReserveFactorInvariants", self.reserve_factor_invariants.load(Ordering::Relaxed));
        
        eprintln!("\n--- Time-Dependent Invariants ---");
        self.print_invariant("InterestInvariants", self.interest_invariants.load(Ordering::Relaxed));
        self.print_invariant("InterestMath", self.interest_math.load(Ordering::Relaxed));
        self.print_invariant("FeeCalculationInvariants", self.fee_calculation_invariants.load(Ordering::Relaxed));
        
        eprintln!("\n--- Flash Loan Invariants ---");
        self.print_invariant("FlashLoanPremium", self.flash_loan_premium.load(Ordering::Relaxed));
        self.print_invariant("FlashLoanRepayment", self.flash_loan_repayment.load(Ordering::Relaxed));
        
        eprintln!("\n--- Liquidation Invariants ---");
        self.print_invariant("LiquidationFairness", self.liquidation_fairness.load(Ordering::Relaxed));
        
        eprintln!("\n--- Economic Exploit Detection ---");
        self.print_invariant("NoRateManipulation", self.no_rate_manipulation.load(Ordering::Relaxed));
        self.print_invariant("OracleSanity", self.oracle_sanity.load(Ordering::Relaxed));
        self.print_invariant("NoValueExtraction", self.no_value_extraction.load(Ordering::Relaxed));
        self.print_invariant("AdminCannotSteal", self.admin_cannot_steal.load(Ordering::Relaxed));
        
        eprintln!("\n--- Final/Configuration Invariants ---");
        self.print_invariant("FinalInvariants", self.final_invariants.load(Ordering::Relaxed));
        self.print_invariant("CumulativeRounding", self.cumulative_rounding.load(Ordering::Relaxed));
        self.print_invariant("LiquidationBonusInvariants", self.liquidation_bonus_invariants.load(Ordering::Relaxed));
        self.print_invariant("PauseStateInvariant", self.pause_state_invariant.load(Ordering::Relaxed));
        self.print_invariant("AccessControlInvariants", self.access_control_invariants.load(Ordering::Relaxed));
        self.print_invariant("ParameterBounds", self.parameter_bounds.load(Ordering::Relaxed));
        self.print_invariant("FailedOperationUnchanged", self.failed_operation_unchanged.load(Ordering::Relaxed));
        self.print_invariant("DustAccumulation", self.dust_accumulation.load(Ordering::Relaxed));
        
        // Flag any invariants that weren't executed
        eprintln!("\n--- COVERAGE WARNINGS ---");
        let mut all_covered = true;
        if self.liquidation_fairness.load(Ordering::Relaxed) == 0 {
            eprintln!("  WARNING: LiquidationFairness never executed (no liquidations?)");
            all_covered = false;
        }
        if self.flash_loan_premium.load(Ordering::Relaxed) == 0 {
            eprintln!("  WARNING: FlashLoanPremium never executed (no flash loans?)");
            all_covered = false;
        }
        if self.interest_invariants.load(Ordering::Relaxed) == 0 {
            eprintln!("  WARNING: InterestInvariants never executed (no time warps?)");
            all_covered = false;
        }
        if all_covered {
            eprintln!("  All invariants were executed at least once!");
        }
        
        eprintln!("=====================================================\n");
    }
    
    fn print_invariant(&self, name: &str, count: u64) {
        let status = if count == 0 { "NEVER RUN" } else { "" };
        eprintln!("  {:35} {:>10} {}", name, count, status);
    }
}

#[derive(Clone, Copy)]
pub enum InvariantType {
    OperationInvariants,
    ProtocolInvariants,
    ProtocolSolvency,
    TreasuryAccrual,
    UtilizationInvariants,
    LiquidationInvariants,
    IndexMonotonicity,
    AccruedTreasuryMonotonicity,
    DebtCeilingInvariants,
    ReserveFactorInvariants,
    InterestInvariants,
    InterestMath,
    FeeCalculationInvariants,
    FlashLoanPremium,
    FlashLoanRepayment,
    LiquidationFairness,
    NoRateManipulation,
    OracleSanity,
    NoValueExtraction,
    AdminCannotSteal,
    FinalInvariants,
    CumulativeRounding,
    LiquidationBonusInvariants,
    PauseStateInvariant,
    AccessControlInvariants,
    ParameterBounds,
    FailedOperationUnchanged,
    DustAccumulation,
}

pub static INVARIANT_STATS: InvariantStats = InvariantStats::new();
