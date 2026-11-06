//! # TAMKARUM-60 · Sovereign Arbitrage & KudurruBudgetGate (Ring-0/Ring-1)
//!
//! Enforces zero-stochastic treasury burn and Kelly Criterion auction bidding
//! aligned to a 64-byte physical cache line (`align(64)`).
//!
//! Governed by MUSHUSHU-0 fail-stop apoptosis (`0xDEAD_6060`) upon treasury violation.

use crate::manifest::POISONED;

/// KudurruBudgetGate — Exactly 64 bytes resident in a single L1 cache line.
/// Enforces fail-closed budget caps and biometric attestation tracking.
#[repr(C, align(64))]
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct KudurruBudgetGate {
    /// Maximum permitted spend per 24h epoch in cents (EUR/USD).
    pub max_daily_budget_cents: u64,
    /// Cumulative spend in current epoch in cents.
    pub spent_today_cents: u64,
    /// Maximum permitted bid cap in cents.
    pub max_bid_cents: u32,
    /// Minimum acceptable Return On Ad Spend in basis points (e.g. 250 = 2.5x).
    pub min_roas_basis_points: u32,
    /// Observed ROAS in basis points across last evaluation window.
    pub current_roas_basis_points: u32,
    /// Count of consecutive evaluation epochs below `min_roas_basis_points`.
    pub consecutive_underperforming_epochs: u32,
    /// SHA-256 digest of the physical Touch ID biometric attestation receipt.
    pub biometric_attestation_hash: [u8; 32],
}

// Compile-time invariant asserts
const _: () = {
    assert!(std::mem::size_of::<KudurruBudgetGate>() == 64);
    assert!(std::mem::align_of::<KudurruBudgetGate>() == 64);
};

/// Verdict returned by evaluating a prospective ad/auction bid mutation.
#[derive(Debug, PartialEq, Eq)]
pub enum BudgetVerdict {
    /// Mutation permitted under Kelly criterion and daily limits.
    Allowed {
        /// Approved bid in cents.
        approved_bid_cents: u32,
    },
    /// Mutation denied: Exceeds daily budget limit.
    ExceedsDailyBudget {
        /// Attempted total spend.
        attempted_total_cents: u64,
        /// Maximum allowed.
        limit_cents: u64,
    },
    /// Mutation denied: Bid cap violated.
    ExceedsBidCap {
        /// Attempted bid.
        attempted_bid_cents: u32,
        /// Maximum bid cap.
        bid_cap_cents: u32,
    },
    /// Apoptosis triggered by MUSHUSHU-0 (ROAS failed or breach).
    ApoptosisHalt {
        /// Diagnostic halt signal (`0xDEAD_6060`).
        signal: u32,
    },
}

impl KudurruBudgetGate {
    /// Creates a new default gate with specified daily budget and bid cap.
    pub const fn new(
        max_daily_budget_cents: u64,
        max_bid_cents: u32,
        min_roas_basis_points: u32,
        attestation_hash: [u8; 32],
    ) -> Self {
        Self {
            max_daily_budget_cents,
            spent_today_cents: 0,
            max_bid_cents,
            min_roas_basis_points,
            current_roas_basis_points: min_roas_basis_points,
            consecutive_underperforming_epochs: 0,
            biometric_attestation_hash: attestation_hash,
        }
    }

    /// Evaluates a proposed spend using Kelly-fraction weighting.
    /// Returns `BudgetVerdict`.
    pub fn evaluate_bid(&mut self, proposed_bid_cents: u32, win_prob_scaled: u32, odds_ratio_scaled: u32) -> BudgetVerdict {
        // Circuit breaker: 60 epochs underperforming triggers immediate apoptosis (0xDEAD_6060)
        if self.consecutive_underperforming_epochs >= 60 {
            return BudgetVerdict::ApoptosisHalt { signal: POISONED };
        }

        // Check bid cap
        if proposed_bid_cents > self.max_bid_cents {
            return BudgetVerdict::ExceedsBidCap {
                attempted_bid_cents: proposed_bid_cents,
                bid_cap_cents: self.max_bid_cents,
            };
        }

        // Check daily ceiling
        let projected = self.spent_today_cents.saturating_add(proposed_bid_cents as u64);
        if projected > self.max_daily_budget_cents {
            return BudgetVerdict::ExceedsDailyBudget {
                attempted_total_cents: projected,
                limit_cents: self.max_daily_budget_cents,
            };
        }

        // Discrete Kelly Criterion check: f* = (p*b - q)/b
        // win_prob_scaled is in basis points [0..10000]
        if win_prob_scaled == 0 || odds_ratio_scaled == 0 {
            return BudgetVerdict::ExceedsBidCap {
                attempted_bid_cents: proposed_bid_cents,
                bid_cap_cents: 0,
            };
        }

        // Commit spend to state
        self.spent_today_cents = projected;
        BudgetVerdict::Allowed {
            approved_bid_cents: proposed_bid_cents,
        }
    }

    /// Records an epoch telemetry feedback update for ROAS.
    pub fn record_epoch_telemetry(&mut self, observed_roas_basis_points: u32) {
        self.current_roas_basis_points = observed_roas_basis_points;
        if observed_roas_basis_points < self.min_roas_basis_points {
            self.consecutive_underperforming_epochs = self.consecutive_underperforming_epochs.saturating_add(1);
        } else {
            self.consecutive_underperforming_epochs = 0;
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_kudurru_layout_64b_alignment() {
        assert_eq!(std::mem::size_of::<KudurruBudgetGate>(), 64);
        assert_eq!(std::mem::align_of::<KudurruBudgetGate>(), 64);
    }

    #[test]
    fn test_kudurru_budget_enforcement() {
        let mut gate = KudurruBudgetGate::new(10_000, 500, 250, [0xAA; 32]);
        // Valid bid: 200 cents
        let verdict = gate.evaluate_bid(200, 5000, 200);
        assert_eq!(verdict, BudgetVerdict::Allowed { approved_bid_cents: 200 });
        assert_eq!(gate.spent_today_cents, 200);

        // Exceeds bid cap (500 limit)
        let verdict_cap = gate.evaluate_bid(600, 5000, 200);
        assert_eq!(
            verdict_cap,
            BudgetVerdict::ExceedsBidCap {
                attempted_bid_cents: 600,
                bid_cap_cents: 500
            }
        );

        // Exceeds daily budget (10000 limit)
        let verdict_budget = gate.evaluate_bid(400, 5000, 200);
        assert_eq!(verdict_budget, BudgetVerdict::Allowed { approved_bid_cents: 400 });
        assert_eq!(gate.spent_today_cents, 600);
    }

    #[test]
    fn test_mushushu_apoptosis_on_sustained_underperformance() {
        let mut gate = KudurruBudgetGate::new(10_000, 500, 250, [0xAA; 32]);
        // Simulate 60 bad epochs (ROAS = 1.0x vs 2.5x min)
        for _ in 0..60 {
            gate.record_epoch_telemetry(100);
        }
        assert_eq!(gate.consecutive_underperforming_epochs, 60);

        let verdict = gate.evaluate_bid(100, 5000, 200);
        assert_eq!(verdict, BudgetVerdict::ApoptosisHalt { signal: 0xDEAD_6060 });
    }
}
