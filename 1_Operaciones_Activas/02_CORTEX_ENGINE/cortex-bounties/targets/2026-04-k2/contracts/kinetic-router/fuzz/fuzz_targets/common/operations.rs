use libfuzzer_sys::arbitrary::{Arbitrary, Unstructured};
use crate::common::constants::*;

#[derive(Debug, Clone, Copy)]
pub enum FlashLoanReceiverType {
    Standard,
    Reentrant,
    ReentrantRepayLiquidation,
    NonRepaying,
    StateManipulating,
    OracleManipulating,
}

#[derive(Debug, Clone, Copy)]
pub enum Operation {
    Supply { user_idx: u8, asset_idx: u8, amount_percent: u8 },
    SupplyOnBehalf { user_idx: u8, recipient_idx: u8, asset_idx: u8, amount_percent: u8 },
    Withdraw { user_idx: u8, asset_idx: u8, amount_percent: u8 },
    WithdrawAll { user_idx: u8, asset_idx: u8 },
    WithdrawToRecipient { user_idx: u8, recipient_idx: u8, asset_idx: u8, amount_percent: u8 },
    Borrow { user_idx: u8, asset_idx: u8, amount_percent: u8 },
    BorrowToRecipient { user_idx: u8, recipient_idx: u8, asset_idx: u8, amount_percent: u8 },
    Repay { user_idx: u8, asset_idx: u8, amount_percent: u8 },
    RepayAll { user_idx: u8, asset_idx: u8 },
    RepayOnBehalf { payer_idx: u8, borrower_idx: u8, asset_idx: u8, amount_percent: u8 },
    SetCollateral { user_idx: u8, asset_idx: u8, use_as_collateral: bool },
    TimeWarp { seconds: u32 },
    ExtremeTimeWarp { years: u8 },
    PriceChange { asset_idx: u8, price_change_bps: i16 },
    Liquidate { liquidator_idx: u8, user_idx: u8, collateral_idx: u8, debt_idx: u8, amount_percent: u8 },
    LiquidateReceiveAToken { liquidator_idx: u8, user_idx: u8, collateral_idx: u8, debt_idx: u8, amount_percent: u8 },
    PrepareLiquidation { liquidator_idx: u8, user_idx: u8, collateral_idx: u8, debt_idx: u8 },
    CreateAndLiquidate { liquidator_idx: u8, user_idx: u8, collateral_idx: u8, debt_idx: u8 },
    FlashLoan { user_idx: u8, asset_idx: u8, amount_percent: u8, receiver_type: FlashLoanReceiverType },
    MultiAssetFlashLoan { user_idx: u8, asset_indices: [u8; 2], amount_percents: [u8; 2], receiver_type: FlashLoanReceiverType },
    SwapCollateral { user_idx: u8, from_idx: u8, to_idx: u8, amount_percent: u8 },
    ZeroAmountSupply { user_idx: u8, asset_idx: u8 },
    ZeroAmountBorrow { user_idx: u8, asset_idx: u8 },
    ZeroAmountWithdraw { user_idx: u8, asset_idx: u8 },
    ZeroAmountRepay { user_idx: u8, asset_idx: u8 },
    DustSupply { user_idx: u8, asset_idx: u8, dust_amount: u8 },
    DustBorrow { user_idx: u8, asset_idx: u8, dust_amount: u8 },
    DustWithdraw { user_idx: u8, asset_idx: u8, dust_amount: u8 },
    DustRepay { user_idx: u8, asset_idx: u8, dust_amount: u8 },
    MaxAmountSupply { user_idx: u8, asset_idx: u8 },
    MaxAmountBorrow { user_idx: u8, asset_idx: u8 },
    PriceToZero { asset_idx: u8 },
    PriceToMax { asset_idx: u8 },
    OracleStale { asset_idx: u8 },
    PriceVolatility { asset_idx: u8, swings: u8 },
    PauseProtocol,
    UnpauseProtocol,
    CollectProtocolReserves { asset_idx: u8 },
    SelfLiquidationAttempt { user_idx: u8, collateral_idx: u8, debt_idx: u8 },
    MultiAssetLiquidation { liquidator_idx: u8, user_idx: u8, collateral_idx: u8, debt_idx: u8 },
    RapidSupplyWithdraw { user_idx: u8, asset_idx: u8, iterations: u8 },
    RapidBorrowRepay { user_idx: u8, asset_idx: u8, iterations: u8 },
    SandwichPriceChange { attacker_idx: u8, victim_idx: u8, asset_idx: u8 },
    InterestAccrualExploit { user_idx: u8, asset_idx: u8 },
    TransferAToken { from_idx: u8, to_idx: u8, asset_idx: u8, amount_percent: u8 },
    DrainLiquidity { user_idx: u8, asset_idx: u8 },
    MaxUtilization { user_idx: u8, asset_idx: u8 },
    ExecuteLiquidation { liquidator_idx: u8, user_idx: u8, collateral_idx: u8, debt_idx: u8, amount_percent: u8 },
    UpdateReserveConfiguration { asset_idx: u8, ltv: u32, liquidation_threshold: u32, liquidation_bonus: u32 },
    UpdateReserveRateStrategy { asset_idx: u8 },
    DropReserve { asset_idx: u8 },
    SetReserveSupplyCap { asset_idx: u8, cap: u32 },
    SetReserveBorrowCap { asset_idx: u8, cap: u32 },
    SetReserveDebtCeiling { asset_idx: u8, ceiling: u32 },
    SetReserveWhitelist { asset_idx: u8, user_idx: u8, add: bool },
    SetReserveBlacklist { asset_idx: u8, user_idx: u8, add: bool },
    SetLiquidationWhitelist { user_idx: u8, add: bool },
    SetLiquidationBlacklist { user_idx: u8, add: bool },
    ProposePoolAdmin { new_admin_idx: u8 },
    AcceptPoolAdmin { pending_admin_idx: u8 },
    BorrowMaxWithdrawAttempt { user_idx: u8, supply_asset_idx: u8, borrow_asset_idx: u8 },
    PriceCrashLiquidation { user_idx: u8, liquidator_idx: u8, asset_idx: u8 },
    FirstDepositorAttack { attacker_idx: u8, victim_idx: u8, asset_idx: u8 },
    DonationAttack { attacker_idx: u8, asset_idx: u8, donation_amount: u8 },
    SetReserveActive { asset_idx: u8, active: bool },
    SetReserveFrozen { asset_idx: u8, frozen: bool },
    FlashLoanWhilePaused { user_idx: u8, asset_idx: u8, amount_percent: u8 },
    BadDebtScenario { user_idx: u8, asset_idx: u8 },
    FullMultiAssetLiquidation { liquidator_idx: u8, user_idx: u8 },
}

#[derive(Debug, Clone)]
pub struct AssetConfig {
    pub ltv: u32,
    pub liquidation_threshold: u32,
    pub liquidation_bonus: u32,
    pub reserve_factor: u32,
    pub base_rate: u128,
    pub slope1: u128,
    pub slope2: u128,
    pub optimal_utilization: u128,
    pub supply_cap: u128,
    pub borrow_cap: u128,
    pub flashloan_enabled: bool,
}

#[derive(Clone)]
struct SimulatedState {
    underlying: [[u128; 4]; 8],
    collateral: [[u128; 4]; 8],
    debt: [[u128; 4]; 8],
    pool_liquidity: [u128; 4],
    paused: bool,
}

impl Default for SimulatedState {
    fn default() -> Self {
        Self {
            underlying: [[INITIAL_BALANCE as u128; 4]; 8],
            collateral: [[0; 4]; 8],
            debt: [[0; 4]; 8],
            pool_liquidity: [0; 4],
            paused: false,
        }
    }
}

impl SimulatedState {
    fn update(&mut self, op: &Operation) {
        match op {
            Operation::Supply { user_idx, asset_idx, amount_percent } => {
                let u = (*user_idx as usize) % 8;
                let a = (*asset_idx as usize) % 4;
                let amount = (self.underlying[u][a] * (*amount_percent as u128) / 100).max(1);
                if amount <= self.underlying[u][a] {
                    self.underlying[u][a] = self.underlying[u][a].saturating_sub(amount);
                    self.collateral[u][a] = self.collateral[u][a].saturating_add(amount);
                    self.pool_liquidity[a] = self.pool_liquidity[a].saturating_add(amount);
                }
            }
            Operation::SupplyOnBehalf { user_idx, recipient_idx, asset_idx, amount_percent } => {
                let u = (*user_idx as usize) % 8;
                let r = (*recipient_idx as usize) % 8;
                let a = (*asset_idx as usize) % 4;
                let amount = (self.underlying[u][a] * (*amount_percent as u128) / 100).max(1);
                if amount <= self.underlying[u][a] {
                    self.underlying[u][a] = self.underlying[u][a].saturating_sub(amount);
                    self.collateral[r][a] = self.collateral[r][a].saturating_add(amount);
                    self.pool_liquidity[a] = self.pool_liquidity[a].saturating_add(amount);
                }
            }
            Operation::Withdraw { user_idx, asset_idx, amount_percent } => {
                let u = (*user_idx as usize) % 8;
                let a = (*asset_idx as usize) % 4;
                let amount = (self.collateral[u][a] * (*amount_percent as u128) / 100).max(1);
                if amount <= self.collateral[u][a] && amount <= self.pool_liquidity[a] {
                    self.collateral[u][a] = self.collateral[u][a].saturating_sub(amount);
                    self.underlying[u][a] = self.underlying[u][a].saturating_add(amount);
                    self.pool_liquidity[a] = self.pool_liquidity[a].saturating_sub(amount);
                }
            }
            Operation::WithdrawAll { user_idx, asset_idx } => {
                let u = (*user_idx as usize) % 8;
                let a = (*asset_idx as usize) % 4;
                let amount = self.collateral[u][a].min(self.pool_liquidity[a]);
                self.collateral[u][a] = self.collateral[u][a].saturating_sub(amount);
                self.underlying[u][a] = self.underlying[u][a].saturating_add(amount);
                self.pool_liquidity[a] = self.pool_liquidity[a].saturating_sub(amount);
            }
            Operation::Borrow { user_idx, asset_idx, amount_percent } => {
                let u = (*user_idx as usize) % 8;
                let a = (*asset_idx as usize) % 4;
                let max_borrow = self.pool_liquidity[a].min(self.total_collateral_value(u) / 4);
                let amount = (max_borrow * (*amount_percent as u128) / 100).max(1);
                if amount <= self.pool_liquidity[a] {
                    self.debt[u][a] = self.debt[u][a].saturating_add(amount);
                    self.underlying[u][a] = self.underlying[u][a].saturating_add(amount);
                    self.pool_liquidity[a] = self.pool_liquidity[a].saturating_sub(amount);
                }
            }
            Operation::BorrowToRecipient { user_idx, recipient_idx, asset_idx, amount_percent } => {
                let u = (*user_idx as usize) % 8;
                let r = (*recipient_idx as usize) % 8;
                let a = (*asset_idx as usize) % 4;
                let max_borrow = self.pool_liquidity[a].min(self.total_collateral_value(u) / 4);
                let amount = (max_borrow * (*amount_percent as u128) / 100).max(1);
                if amount <= self.pool_liquidity[a] {
                    self.debt[u][a] = self.debt[u][a].saturating_add(amount);
                    self.underlying[r][a] = self.underlying[r][a].saturating_add(amount);
                    self.pool_liquidity[a] = self.pool_liquidity[a].saturating_sub(amount);
                }
            }
            Operation::Repay { user_idx, asset_idx, amount_percent } => {
                let u = (*user_idx as usize) % 8;
                let a = (*asset_idx as usize) % 4;
                let max_repay = self.debt[u][a].min(self.underlying[u][a]);
                let amount = (max_repay * (*amount_percent as u128) / 100).max(1);
                if amount <= self.underlying[u][a] && amount <= self.debt[u][a] {
                    self.debt[u][a] = self.debt[u][a].saturating_sub(amount);
                    self.underlying[u][a] = self.underlying[u][a].saturating_sub(amount);
                    self.pool_liquidity[a] = self.pool_liquidity[a].saturating_add(amount);
                }
            }
            Operation::RepayAll { user_idx, asset_idx } => {
                let u = (*user_idx as usize) % 8;
                let a = (*asset_idx as usize) % 4;
                let amount = self.debt[u][a].min(self.underlying[u][a]);
                self.debt[u][a] = self.debt[u][a].saturating_sub(amount);
                self.underlying[u][a] = self.underlying[u][a].saturating_sub(amount);
                self.pool_liquidity[a] = self.pool_liquidity[a].saturating_add(amount);
            }
            Operation::PauseProtocol => self.paused = true,
            Operation::UnpauseProtocol => self.paused = false,
            Operation::DustSupply { user_idx, asset_idx, dust_amount } => {
                let u = (*user_idx as usize) % 8;
                let a = (*asset_idx as usize) % 4;
                let amount = *dust_amount as u128;
                if amount <= self.underlying[u][a] {
                    self.underlying[u][a] = self.underlying[u][a].saturating_sub(amount);
                    self.collateral[u][a] = self.collateral[u][a].saturating_add(amount);
                    self.pool_liquidity[a] = self.pool_liquidity[a].saturating_add(amount);
                }
            }
            Operation::MaxAmountSupply { user_idx, asset_idx } => {
                let u = (*user_idx as usize) % 8;
                let a = (*asset_idx as usize) % 4;
                let amount = self.underlying[u][a];
                self.underlying[u][a] = 0;
                self.collateral[u][a] = self.collateral[u][a].saturating_add(amount);
                self.pool_liquidity[a] = self.pool_liquidity[a].saturating_add(amount);
            }
            _ => {}
        }
    }
    
    /// Total collateral value for a user (simplified: sum across assets)
    fn total_collateral_value(&self, user: usize) -> u128 {
        self.collateral[user].iter().sum()
    }
    
    /// Total debt for a user
    fn total_debt(&self, user: usize) -> u128 {
        self.debt[user].iter().sum()
    }
    
    /// Approximate health factor (collateral / debt ratio)
    /// Returns 1000 (representing HF=1.0) as baseline, >1000 = healthy
    fn health_factor(&self, user: usize) -> u128 {
        let debt = self.total_debt(user);
        if debt == 0 {
            return u128::MAX; // No debt = infinite health
        }
        // Simplified: collateral value * 0.75 (avg liquidation threshold) / debt
        // Return in basis points (10000 = HF 1.0)
        let collateral = self.total_collateral_value(user);
        (collateral * 7500 / debt).min(100_000)
    }
    
    /// Check if user can safely withdraw amount without becoming unhealthy
    #[allow(dead_code)]
    fn can_safely_withdraw(&self, user: usize, asset: usize, amount: u128) -> bool {
        let debt = self.total_debt(user);
        if debt == 0 {
            return true; // No debt, any withdrawal is safe
        }
        let remaining_collateral = self.total_collateral_value(user).saturating_sub(amount);
        // Need remaining collateral * 0.75 > debt (HF > 1.0)
        remaining_collateral * 7500 > debt * 10000
    }
    
    /// Check if user has meaningful collateral
    fn has_collateral(&self, user: usize) -> bool {
        self.collateral[user].iter().any(|&c| c > DUST_THRESHOLD)
    }
    
    /// Check if user has debt
    fn has_debt(&self, user: usize) -> bool {
        self.debt[user].iter().any(|&d| d > 0)
    }
    
    /// Check if any user has collateral
    fn any_collateral(&self) -> bool {
        (0..8).any(|u| self.has_collateral(u))
    }
    
    /// Check if any user has debt
    fn any_debt(&self) -> bool {
        (0..8).any(|u| self.has_debt(u))
    }
    
    /// Get user with most collateral for an asset
    fn best_user_for_withdraw(&self, asset: usize) -> u8 {
        (0..8).max_by_key(|&u| self.collateral[u][asset]).unwrap_or(0) as u8
    }
    
    /// Get user with most debt for an asset
    fn best_user_for_repay(&self, asset: usize) -> u8 {
        (0..8).max_by_key(|&u| self.debt[u][asset]).unwrap_or(0) as u8
    }
    
    /// Get user with most collateral overall (best for borrowing)
    fn best_user_for_borrow(&self) -> u8 {
        (0..8).max_by_key(|&u| self.total_collateral_value(u)).unwrap_or(0) as u8
    }
    
    /// Get asset with most liquidity (best for flash loans)
    fn best_asset_for_flashloan(&self) -> u8 {
        (0..4).max_by_key(|&a| self.pool_liquidity[a]).unwrap_or(0) as u8
    }
    
    /// Check if pool has liquidity for an asset
    fn has_liquidity(&self, asset: usize) -> bool {
        self.pool_liquidity[asset] > DUST_THRESHOLD
    }
    
    /// Get user with lowest health factor (best liquidation target)
    /// Returns user with HF closest to 1.0 (most likely to be liquidatable after price change)
    fn best_user_for_liquidation(&self) -> Option<u8> {
        (0..8)
            .filter(|&u| self.has_debt(u) && self.has_collateral(u))
            .min_by_key(|&u| self.health_factor(u))
            .map(|u| u as u8)
    }
    
    /// Check if any user has low health factor (close to liquidatable)
    fn has_low_health_user(&self) -> bool {
        (0..8).any(|u| {
            let hf = self.health_factor(u);
            hf < 15000 && hf > 0 // HF between 0 and 1.5
        })
    }
}

#[derive(Debug)]
pub struct Input {
    pub operations: Vec<Operation>,
    pub asset_configs: [AssetConfig; 4],
    pub initial_prices: [u128; 4],
}

impl<'a> Arbitrary<'a> for Input {
    fn arbitrary(u: &mut Unstructured<'a>) -> libfuzzer_sys::arbitrary::Result<Self> {
        let num_ops = u.int_in_range(5..=25)?;
        let mut operations = Vec::with_capacity(num_ops);
        let mut state = SimulatedState::default();
        
        for i in 0..num_ops {
            let op = generate_stateful_operation(u, &state, i, num_ops)?;
            state.update(&op);
            operations.push(op);
        }
        
        let asset_configs = [
            generate_asset_config(u)?,
            generate_asset_config(u)?,
            generate_asset_config(u)?,
            generate_asset_config(u)?,
        ];
        
        let initial_prices = [
            u.int_in_range(MIN_PRICE..=MAX_PRICE)?,
            u.int_in_range(MIN_PRICE..=MAX_PRICE)?,
            u.int_in_range(MIN_PRICE..=MAX_PRICE)?,
            u.int_in_range(MIN_PRICE..=MAX_PRICE)?,
        ];
        
        Ok(Input { operations, asset_configs, initial_prices })
    }
}

/// State-aware operation generation - builds valid category list based on state
fn generate_stateful_operation(
    u: &mut Unstructured,
    state: &SimulatedState,
    op_index: usize,
    total_ops: usize,
) -> libfuzzer_sys::arbitrary::Result<Operation> {
    // First 3 operations: guarantee Supply to build state
    if op_index < 3 {
        return generate_supply_operation(u, state);
    }
    
    let phase = (op_index * 100) / total_ops;
    let has_collateral = state.any_collateral();
    let has_debt = state.any_debt();
    let has_liquidity = (0..4).any(|a| state.has_liquidity(a));
    
    // Build weighted category list based on phase and state
    let mut categories: Vec<(OperationCategory, u8)> = Vec::new();
    let has_low_health = state.has_low_health_user();
    
    match phase {
        0..=30 => {
            // Early phase: aggressively build state
            categories.push((OperationCategory::Supply, 5));
            if has_collateral {
                categories.push((OperationCategory::Borrow, 4)); // Build debt early
            }
            categories.push((OperationCategory::Environmental, 1));
            categories.push((OperationCategory::Oracle, 1));
        }
        31..=60 => {
            // Mid phase: balanced with state-aware weights
            categories.push((OperationCategory::Supply, 2));
            if has_collateral {
                categories.push((OperationCategory::Borrow, 3));
                // Only withdraw if no debt or healthy
                if !has_debt || state.health_factor(state.best_user_for_borrow() as usize) > 15000 {
                    categories.push((OperationCategory::Withdraw, 2));
                }
            }
            if has_debt {
                categories.push((OperationCategory::Repay, 2));
                // Only attempt liquidation if someone is close to liquidatable
                if has_low_health {
                    categories.push((OperationCategory::Liquidation, 4));
                } else {
                    categories.push((OperationCategory::Liquidation, 1)); // CreateAndLiquidate to setup
                }
            }
            if has_liquidity {
                categories.push((OperationCategory::FlashLoan, 2));
            }
            categories.push((OperationCategory::Oracle, 2)); // Price changes can make users liquidatable
            categories.push((OperationCategory::Environmental, 2));
            categories.push((OperationCategory::Admin, 1));
            categories.push((OperationCategory::Adversarial, 1));
        }
        _ => {
            // Late phase: stress testing
            if has_debt {
                categories.push((OperationCategory::Repay, 2));
                categories.push((OperationCategory::Liquidation, has_low_health.then_some(5).unwrap_or(2)));
            }
            if has_collateral && (!has_debt || state.health_factor(state.best_user_for_borrow() as usize) > 12000) {
                categories.push((OperationCategory::Withdraw, 2));
            }
            categories.push((OperationCategory::EdgeCase, 2));
            categories.push((OperationCategory::Adversarial, 3));
            categories.push((OperationCategory::Oracle, 3)); // Heavy oracle testing late
            categories.push((OperationCategory::Environmental, 2));
            if has_liquidity {
                categories.push((OperationCategory::FlashLoan, 2));
            }
            categories.push((OperationCategory::Admin, 1));
        }
    }
    
    // Fallback if no categories (shouldn't happen, but safety)
    if categories.is_empty() {
        categories.push((OperationCategory::Supply, 1));
    }
    
    // Calculate total weight
    let total_weight: u8 = categories.iter().map(|(_, w)| w).sum();
    
    // Pick randomly based on weights
    let roll = u.int_in_range(0..=(total_weight.saturating_sub(1) as u32))? as u8;
    let mut cumulative = 0u8;
    let mut selected = OperationCategory::Supply;
    
    for (cat, weight) in &categories {
        cumulative = cumulative.saturating_add(*weight);
        if roll < cumulative {
            selected = *cat;
            break;
        }
    }
    
    generate_operation_for_category(u, selected, state)
}

#[derive(Clone, Copy)]
enum OperationCategory {
    Supply,
    Withdraw,
    Borrow,
    Repay,
    Liquidation,
    FlashLoan,
    Oracle,
    Environmental,
    EdgeCase,
    Adversarial,
    Admin,
}

fn generate_supply_operation(u: &mut Unstructured, state: &SimulatedState) -> libfuzzer_sys::arbitrary::Result<Operation> {
    // Pick user with most underlying balance for higher success rate
    let asset_idx = u.int_in_range(0..=3)?;
    let user_idx = (0..8u8)
        .max_by_key(|&uid| state.underlying[uid as usize][asset_idx as usize])
        .unwrap_or_else(|| u.int_in_range(0..=7).unwrap_or(0));
    
    match u.int_in_range(0..=4)? {
        0..=3 => Ok(Operation::Supply {
            user_idx,
            asset_idx,
            amount_percent: u.int_in_range(40..=80)?, // Higher amounts to build liquidity
        }),
        _ => Ok(Operation::SupplyOnBehalf {
            user_idx,
            recipient_idx: u.int_in_range(0..=7)?,
            asset_idx,
            amount_percent: u.int_in_range(40..=80)?,
        }),
    }
}

fn generate_operation_for_category(
    u: &mut Unstructured,
    category: OperationCategory,
    state: &SimulatedState,
) -> libfuzzer_sys::arbitrary::Result<Operation> {
    match category {
        OperationCategory::Supply => generate_supply_operation(u, state),
        
        OperationCategory::Withdraw => {
            let asset_idx = u.int_in_range(0..=3)?;
            // Pick user with most collateral for this asset
            let user_idx = state.best_user_for_withdraw(asset_idx as usize);
            let user = user_idx as usize;
            let asset = asset_idx as usize;
            
            // Calculate safe withdrawal percentage based on health factor
            let has_debt = state.has_debt(user);
            let collateral = state.collateral[user][asset];
            
            // If user has debt, limit withdrawal to maintain health factor
            let max_percent = if has_debt && collateral > 0 {
                // Calculate max safe withdrawal: keep HF > 1.2 after withdrawal
                let total_coll = state.total_collateral_value(user);
                let total_debt = state.total_debt(user);
                let min_coll_needed = total_debt * 10000 / 7500 * 12 / 10; // HF = 1.2
                let withdrawable = total_coll.saturating_sub(min_coll_needed);
                let max_withdraw_this_asset = withdrawable.min(collateral);
                ((max_withdraw_this_asset * 100 / collateral.max(1)) as u8).min(50).max(10)
            } else {
                90 // No debt, can withdraw most
            };
            
            match u.int_in_range(0..=2)? {
                0 => Ok(Operation::Withdraw {
                    user_idx,
                    asset_idx,
                    amount_percent: u.int_in_range(10..=max_percent)?,
                }),
                1 if !has_debt => Ok(Operation::WithdrawAll { user_idx, asset_idx }),
                1 => Ok(Operation::Withdraw {
                    user_idx,
                    asset_idx,
                    amount_percent: u.int_in_range(10..=max_percent)?,
                }),
                _ => Ok(Operation::WithdrawToRecipient {
                    user_idx,
                    recipient_idx: u.int_in_range(0..=7)?,
                    asset_idx,
                    amount_percent: u.int_in_range(10..=max_percent)?,
                }),
            }
        }
        
        OperationCategory::Borrow => {
            // Pick user with most collateral (best for borrowing)
            let user_idx = state.best_user_for_borrow();
            // Pick asset with most liquidity
            let asset_idx = state.best_asset_for_flashloan();
            // Check user's health to decide how aggressive to borrow
            let user_hf = state.health_factor(user_idx as usize);
            let max_borrow_pct = if user_hf > 20000 { 40 } else { 25 }; // More conservative if HF is lower
            
            match u.int_in_range(0..=2)? {
                0..=1 => Ok(Operation::Borrow {
                    user_idx,
                    asset_idx,
                    amount_percent: u.int_in_range(15..=max_borrow_pct)?,
                }),
                _ => Ok(Operation::BorrowToRecipient {
                    user_idx,
                    recipient_idx: u.int_in_range(0..=7)?,
                    asset_idx,
                    amount_percent: u.int_in_range(15..=max_borrow_pct)?,
                }),
            }
        }
        
        OperationCategory::Repay => {
            // Find an asset where someone actually has debt
            let asset_idx = (0..4u8)
                .filter(|&a| (0..8).any(|u| state.debt[u][a as usize] > 0))
                .next()
                .unwrap_or_else(|| u.int_in_range(0..=3).unwrap_or(0));
            // Pick user with most debt for this asset
            let user_idx = state.best_user_for_repay(asset_idx as usize);
            // Check if user has underlying tokens to repay with
            let user = user_idx as usize;
            let has_funds = state.underlying[user][asset_idx as usize] > DUST_THRESHOLD;
            
            match u.int_in_range(0..=2)? {
                0..=1 if has_funds => Ok(Operation::Repay {
                    user_idx,
                    asset_idx,
                    amount_percent: u.int_in_range(30..=100)?,
                }),
                _ if has_funds => Ok(Operation::RepayAll { user_idx, asset_idx }),
                _ => Ok(Operation::RepayOnBehalf {
                    payer_idx: (0..8u8)
                        .filter(|&p| state.underlying[p as usize][asset_idx as usize] > DUST_THRESHOLD)
                        .next()
                        .unwrap_or(0),
                    borrower_idx: user_idx,
                    asset_idx,
                    amount_percent: u.int_in_range(30..=100)?,
                }),
            }
        }
        
        OperationCategory::Liquidation => {
            // Liquidator needs underlying tokens, pick one with balance
            let liquidator_idx = u.int_in_range(0..=7)?;
            // Target user with lowest health factor (most likely liquidatable)
            let user_idx = state.best_user_for_liquidation()
                .unwrap_or_else(|| u.int_in_range(0..=7).unwrap_or(0));
            
            // Pick collateral and debt assets that the target user actually has
            let user = user_idx as usize;
            let collateral_idx = (0..4u8)
                .filter(|&a| state.collateral[user][a as usize] > DUST_THRESHOLD)
                .next()
                .unwrap_or_else(|| u.int_in_range(0..=3).unwrap_or(0));
            let debt_idx = (0..4u8)
                .filter(|&a| state.debt[user][a as usize] > 0)
                .next()
                .unwrap_or_else(|| u.int_in_range(0..=3).unwrap_or(0));
            
            // Favor CreateAndLiquidate (which sets up unhealthy position) if user isn't already unhealthy
            let hf = state.health_factor(user);
            let favor_create = hf > 10000; // HF > 1.0, user is healthy
            
            match u.int_in_range(0..=5)? {
                0 if !favor_create => Ok(Operation::Liquidate {
                    liquidator_idx,
                    user_idx,
                    collateral_idx,
                    debt_idx,
                    amount_percent: u.int_in_range(30..=100)?,
                }),
                1 if !favor_create => Ok(Operation::LiquidateReceiveAToken {
                    liquidator_idx,
                    user_idx,
                    collateral_idx,
                    debt_idx,
                    amount_percent: u.int_in_range(30..=100)?,
                }),
                0..=3 => Ok(Operation::CreateAndLiquidate {
                    liquidator_idx,
                    user_idx,
                    collateral_idx,
                    debt_idx,
                }),
                4 => Ok(Operation::MultiAssetLiquidation {
                    liquidator_idx,
                    user_idx,
                    collateral_idx,
                    debt_idx,
                }),
                _ => Ok(Operation::SelfLiquidationAttempt {
                    user_idx,
                    collateral_idx,
                    debt_idx,
                }),
            }
        }
        
        OperationCategory::FlashLoan => {
            let receiver_type = generate_receiver_type(u)?;
            // Pick asset with most liquidity
            let asset_idx = state.best_asset_for_flashloan();
            match u.int_in_range(0..=2)? {
                0..=1 => Ok(Operation::FlashLoan {
                    user_idx: u.int_in_range(0..=7)?,
                    asset_idx,
                    amount_percent: u.int_in_range(20..=80)?,
                    receiver_type,
                }),
                _ => Ok(Operation::MultiAssetFlashLoan {
                    user_idx: u.int_in_range(0..=7)?,
                    asset_indices: [asset_idx, u.int_in_range(0..=3)?],
                    amount_percents: [u.int_in_range(10..=90)?, u.int_in_range(10..=90)?],
                    receiver_type,
                }),
            }
        }
        
        OperationCategory::Oracle => {
            match u.int_in_range(0..=4)? {
                0..=1 => Ok(Operation::PriceChange {
                    asset_idx: u.int_in_range(0..=3)?,
                    price_change_bps: u.int_in_range(-3000..=3000)?,
                }),
                2 => Ok(Operation::PriceToZero { asset_idx: u.int_in_range(0..=3)? }),
                3 => Ok(Operation::PriceVolatility {
                    asset_idx: u.int_in_range(0..=3)?,
                    swings: u.int_in_range(2..=5)?,
                }),
                _ => Ok(Operation::OracleStale { asset_idx: u.int_in_range(0..=3)? }),
            }
        }
        
        OperationCategory::Environmental => {
            match u.int_in_range(0..=5)? {
                0..=2 => Ok(Operation::TimeWarp {
                    seconds: match u.int_in_range(0..=3)? {
                        0 => u.int_in_range(1..=3600)?,
                        1 => u.int_in_range(3600..=86400)?,
                        2 => u.int_in_range(86400..=604800)?,
                        _ => u.int_in_range(604800..=2592000)?,
                    },
                }),
                3 => Ok(Operation::ExtremeTimeWarp { years: u.int_in_range(1..=5)? }),
                4 => if state.paused {
                    Ok(Operation::UnpauseProtocol)
                } else {
                    Ok(Operation::PauseProtocol)
                },
                _ => Ok(Operation::CollectProtocolReserves { asset_idx: u.int_in_range(0..=3)? }),
            }
        }
        
        OperationCategory::EdgeCase => {
            match u.int_in_range(0..=7)? {
                0 => Ok(Operation::ZeroAmountSupply {
                    user_idx: u.int_in_range(0..=7)?,
                    asset_idx: u.int_in_range(0..=3)?,
                }),
                1 => Ok(Operation::ZeroAmountBorrow {
                    user_idx: u.int_in_range(0..=7)?,
                    asset_idx: u.int_in_range(0..=3)?,
                }),
                2 => Ok(Operation::DustSupply {
                    user_idx: u.int_in_range(0..=7)?,
                    asset_idx: u.int_in_range(0..=3)?,
                    dust_amount: u.int_in_range(1..=100)?,
                }),
                3 => Ok(Operation::DustBorrow {
                    user_idx: u.int_in_range(0..=7)?,
                    asset_idx: u.int_in_range(0..=3)?,
                    dust_amount: u.int_in_range(1..=100)?,
                }),
                4 => Ok(Operation::MaxAmountSupply {
                    user_idx: u.int_in_range(0..=7)?,
                    asset_idx: u.int_in_range(0..=3)?,
                }),
                5 => Ok(Operation::MaxAmountBorrow {
                    user_idx: u.int_in_range(0..=7)?,
                    asset_idx: u.int_in_range(0..=3)?,
                }),
                6 => Ok(Operation::BadDebtScenario {
                    user_idx: u.int_in_range(0..=7)?,
                    asset_idx: u.int_in_range(0..=3)?,
                }),
                _ => Ok(Operation::FlashLoanWhilePaused {
                    user_idx: u.int_in_range(0..=7)?,
                    asset_idx: u.int_in_range(0..=3)?,
                    amount_percent: u.int_in_range(10..=90)?,
                }),
            }
        }
        
        OperationCategory::Adversarial => {
            match u.int_in_range(0..=6)? {
                0 => Ok(Operation::RapidSupplyWithdraw {
                    user_idx: u.int_in_range(0..=7)?,
                    asset_idx: u.int_in_range(0..=3)?,
                    iterations: u.int_in_range(2..=5)?,
                }),
                1 => Ok(Operation::RapidBorrowRepay {
                    user_idx: state.best_user_for_borrow(),
                    asset_idx: u.int_in_range(0..=3)?,
                    iterations: u.int_in_range(2..=5)?,
                }),
                2 => Ok(Operation::SandwichPriceChange {
                    attacker_idx: u.int_in_range(0..=7)?,
                    victim_idx: u.int_in_range(0..=7)?,
                    asset_idx: u.int_in_range(0..=3)?,
                }),
                3 => Ok(Operation::InterestAccrualExploit {
                    user_idx: u.int_in_range(0..=7)?,
                    asset_idx: u.int_in_range(0..=3)?,
                }),
                4 => Ok(Operation::FirstDepositorAttack {
                    attacker_idx: u.int_in_range(0..=7)?,
                    victim_idx: u.int_in_range(0..=7)?,
                    asset_idx: u.int_in_range(0..=3)?,
                }),
                5 => Ok(Operation::DonationAttack {
                    attacker_idx: u.int_in_range(0..=7)?,
                    asset_idx: u.int_in_range(0..=3)?,
                    donation_amount: u.int_in_range(1..=50)?,
                }),
                _ => Ok(Operation::BorrowMaxWithdrawAttempt {
                    user_idx: u.int_in_range(0..=7)?,
                    supply_asset_idx: u.int_in_range(0..=3)?,
                    borrow_asset_idx: u.int_in_range(0..=3)?,
                }),
            }
        }
        
        OperationCategory::Admin => {
            match u.int_in_range(0..=5)? {
                0 => {
                    let ltv = u.int_in_range(1000..=7500)?;
                    let liquidation_threshold = u.int_in_range(ltv + 500..=9000)?;
                    Ok(Operation::UpdateReserveConfiguration {
                        asset_idx: u.int_in_range(0..=3)?,
                        ltv,
                        liquidation_threshold,
                        liquidation_bonus: u.int_in_range(100..=1500)?,
                    })
                }
                1 => Ok(Operation::SetReserveSupplyCap {
                    asset_idx: u.int_in_range(0..=3)?,
                    cap: u.int_in_range(0..=1_000_000)?,
                }),
                2 => Ok(Operation::SetReserveBorrowCap {
                    asset_idx: u.int_in_range(0..=3)?,
                    cap: u.int_in_range(0..=500_000)?,
                }),
                3 => Ok(Operation::SetReserveWhitelist {
                    asset_idx: u.int_in_range(0..=3)?,
                    user_idx: u.int_in_range(0..=7)?,
                    add: u.arbitrary()?,
                }),
                4 => Ok(Operation::SetReserveActive {
                    asset_idx: u.int_in_range(0..=3)?,
                    active: u.arbitrary()?,
                }),
                _ => Ok(Operation::SetReserveFrozen {
                    asset_idx: u.int_in_range(0..=3)?,
                    frozen: u.arbitrary()?,
                }),
            }
        }
    }
}

fn generate_receiver_type(u: &mut Unstructured) -> libfuzzer_sys::arbitrary::Result<FlashLoanReceiverType> {
    match u.int_in_range(0..=5)? {
        0 => Ok(FlashLoanReceiverType::Standard),
        1 => Ok(FlashLoanReceiverType::Reentrant),
        2 => Ok(FlashLoanReceiverType::ReentrantRepayLiquidation),
        3 => Ok(FlashLoanReceiverType::NonRepaying),
        4 => Ok(FlashLoanReceiverType::StateManipulating),
        _ => Ok(FlashLoanReceiverType::OracleManipulating),
    }
}

fn generate_asset_config(u: &mut Unstructured) -> libfuzzer_sys::arbitrary::Result<AssetConfig> {
    let ltv = u.int_in_range(1000..=7500)?;
    let liquidation_threshold = u.int_in_range(ltv + 500..=9000)?;
    let liquidation_bonus = u.int_in_range(100..=1500)?;
    let reserve_factor = u.int_in_range(0..=3000)?;
    
    let base_rate = u.int_in_range(0..=RAY / 100)?;
    let slope1 = u.int_in_range(RAY / 100..=RAY / 10)?;
    let slope2 = u.int_in_range(RAY / 10..=RAY)?;
    let optimal_utilization = u.int_in_range(RAY / 2..=RAY * 9 / 10)?;
    
    let supply_cap = if u.arbitrary()? { u.int_in_range(1000..=1_000_000)? } else { 0 };
    let borrow_cap = if u.arbitrary()? { u.int_in_range(500..=500_000)? } else { 0 };
    let flashloan_enabled = u.arbitrary()?;
    
    Ok(AssetConfig {
        ltv,
        liquidation_threshold,
        liquidation_bonus,
        reserve_factor,
        base_rate,
        slope1,
        slope2,
        optimal_utilization,
        supply_cap,
        borrow_cap,
        flashloan_enabled,
    })
}
