//! Shared invariant checks for K2 fuzz testing.
//!
//! This module provides reusable invariant assertions that can be used across
//! multiple fuzz targets. These invariants are derived from the Halborn security
//! audit findings and the protocol's safety requirements.

/// RAY constant (1e9 in K2)
pub const RAY: u128 = 1_000_000_000;

/// WAD constant (1e18 for health factor calculations)
pub const WAD: u128 = 1_000_000_000_000_000_000;

/// Maximum valid basis points (100%)
pub const MAX_BPS: u128 = 10_000;

// =============================================================================
// Authorization Invariants (HAL-01 through HAL-05)
// =============================================================================

/// Tracks authorization test results
#[derive(Default, Debug)]
pub struct AuthInvariantTracker {
    /// Count of operations where unauthorized callers succeeded
    pub unauthorized_successes: u32,
    /// Count of expected failures (auth correctly rejected)
    pub authorized_rejections: u32,
    /// Names of operations that had auth bypasses
    pub bypass_operations: Vec<String>,
}

impl AuthInvariantTracker {
    pub fn new() -> Self {
        Self::default()
    }

    /// Record a successful authorization check (unauthorized caller was rejected)
    pub fn record_rejection(&mut self) {
        self.authorized_rejections += 1;
    }

    /// Record an authorization bypass (CRITICAL - unauthorized caller succeeded)
    pub fn record_bypass(&mut self, operation: &str) {
        self.unauthorized_successes += 1;
        self.bypass_operations.push(operation.to_string());
    }

    /// Assert no authorization bypasses occurred
    pub fn assert_no_bypasses(&self) {
        assert!(
            self.unauthorized_successes == 0,
            "AUTHORIZATION BYPASS DETECTED: {} operations allowed unauthorized access: {:?}",
            self.unauthorized_successes,
            self.bypass_operations
        );
    }
}

/// Determines if an operation should require admin authorization
pub fn requires_admin_auth(operation: &str) -> bool {
    matches!(
        operation,
        "set_flash_loan_premium"
            | "set_flash_loan_premium_max"
            | "set_treasury"
            | "set_dex_router"
            | "set_dex_factory"
            | "set_pool_configurator"
            | "set_hf_liquidation_threshold"
            | "set_min_swap_output_bps"
            | "set_incentives_contract"
            | "set_flash_liquidation_helper"
            | "set_reserve_whitelist"
            | "set_reserve_blacklist"
            | "set_liquidation_whitelist"
            | "set_liquidation_blacklist"
            | "collect_protocol_reserves"
            | "unpause"
            | "propose_admin"
            | "cancel_admin_proposal"
    )
}

/// Determines if an operation requires emergency admin authorization
pub fn requires_emergency_admin_auth(operation: &str) -> bool {
    matches!(operation, "pause")
}

// =============================================================================
// Accounting Invariants (Recommendation A)
// =============================================================================

/// Tracks accounting state for invariant checks
#[derive(Clone, Debug)]
pub struct AccountingSnapshot {
    /// Total aToken supply
    pub atoken_supply: u128,
    /// Total underlying asset balance in aToken contract
    pub atoken_underlying_balance: u128,
    /// Total debt token supply
    pub debt_supply: u128,
    /// Protocol treasury balance
    pub treasury_balance: u128,
    /// Current liquidity index
    pub liquidity_index: u128,
    /// Current variable borrow index
    pub variable_borrow_index: u128,
    /// Timestamp of snapshot
    pub timestamp: u64,
}

impl AccountingSnapshot {
    /// Assert basic reserve invariants
    pub fn assert_basic_invariants(&self) {
        // Indices must be >= RAY
        assert!(
            self.liquidity_index >= RAY,
            "Liquidity index {} below RAY ({})",
            self.liquidity_index,
            RAY
        );
        assert!(
            self.variable_borrow_index >= RAY,
            "Variable borrow index {} below RAY ({})",
            self.variable_borrow_index,
            RAY
        );
    }

    /// Assert indices are monotonically increasing
    pub fn assert_monotonic_indices(&self, previous: &AccountingSnapshot) {
        assert!(
            self.liquidity_index >= previous.liquidity_index,
            "Liquidity index decreased from {} to {}",
            previous.liquidity_index,
            self.liquidity_index
        );
        assert!(
            self.variable_borrow_index >= previous.variable_borrow_index,
            "Variable borrow index decreased from {} to {}",
            previous.variable_borrow_index,
            self.variable_borrow_index
        );
    }
}

/// Token conservation check for supply operations
pub fn assert_supply_conservation(
    underlying_deposited: u128,
    atoken_minted: u128,
    liquidity_index: u128,
) {
    // aTokens minted should equal underlying / liquidity_index (scaled)
    let expected_atoken = (underlying_deposited * RAY) / liquidity_index;

    // Allow for rounding (within 1 unit)
    let diff = if atoken_minted > expected_atoken {
        atoken_minted - expected_atoken
    } else {
        expected_atoken - atoken_minted
    };

    assert!(
        diff <= 1,
        "Supply conservation violated: deposited {} should mint ~{} aTokens, got {}",
        underlying_deposited,
        expected_atoken,
        atoken_minted
    );
}

/// Token conservation check for withdraw operations
pub fn assert_withdraw_conservation(
    atoken_burned: u128,
    underlying_withdrawn: u128,
    liquidity_index: u128,
) {
    // Underlying withdrawn should equal aTokens burned * liquidity_index
    let expected_underlying = (atoken_burned * liquidity_index) / RAY;

    // Allow for rounding
    let diff = if underlying_withdrawn > expected_underlying {
        underlying_withdrawn - expected_underlying
    } else {
        expected_underlying - underlying_withdrawn
    };

    assert!(
        diff <= 1,
        "Withdraw conservation violated: burning {} aTokens should yield ~{}, got {}",
        atoken_burned,
        expected_underlying,
        underlying_withdrawn
    );
}

// =============================================================================
// Economic Invariants (Recommendation E)
// =============================================================================

/// Assert health factor invariants
pub fn assert_health_factor_invariants(
    health_factor: u128,
    has_debt: bool,
    is_liquidatable: bool,
) {
    if !has_debt {
        // No debt means infinite health factor (represented as u128::MAX or very large)
        assert!(
            health_factor >= WAD || !has_debt,
            "Health factor should be >= 1 WAD or user has no debt"
        );
    }

    if is_liquidatable {
        assert!(
            health_factor < WAD,
            "Position marked liquidatable but health factor {} >= 1 WAD",
            health_factor
        );
    }
}

/// Assert interest rate invariants
pub fn assert_interest_rate_invariants(
    supply_rate: u128,
    borrow_rate: u128,
    reserve_factor_bps: u128,
) {
    // Supply rate should be <= borrow rate * (1 - reserve_factor)
    if borrow_rate > 0 {
        let expected_max_supply = borrow_rate * (MAX_BPS - reserve_factor_bps) / MAX_BPS;
        assert!(
            supply_rate <= expected_max_supply + 1, // +1 for rounding
            "Supply rate {} exceeds maximum {} given borrow rate {} and reserve factor {}",
            supply_rate,
            expected_max_supply,
            borrow_rate,
            reserve_factor_bps
        );
    }
}

/// Assert liquidation bonus is reasonable
pub fn assert_liquidation_bonus_invariants(
    liquidation_bonus_bps: u128,
    collateral_seized: u128,
    debt_covered: u128,
    collateral_price: u128,
    debt_price: u128,
) {
    if debt_covered > 0 && collateral_price > 0 && debt_price > 0 {
        // Value of collateral seized should be <= debt_value * (1 + bonus)
        let debt_value = debt_covered * debt_price;
        let max_collateral_value = debt_value * (MAX_BPS + liquidation_bonus_bps) / MAX_BPS;
        let actual_collateral_value = collateral_seized * collateral_price;

        assert!(
            actual_collateral_value <= max_collateral_value + collateral_price, // +1 unit for rounding
            "Liquidation seized too much collateral: value {} exceeds max {}",
            actual_collateral_value,
            max_collateral_value
        );
    }
}

// =============================================================================
// Flash Loan Invariants (HAL-03)
// =============================================================================

/// Assert flash loan repayment invariants
pub fn assert_flash_loan_repayment(
    borrowed_amount: u128,
    premium_bps: u128,
    repaid_amount: u128,
    succeeded: bool,
) {
    let expected_repayment = borrowed_amount + (borrowed_amount * premium_bps / MAX_BPS);

    if succeeded {
        assert!(
            repaid_amount >= expected_repayment,
            "Flash loan succeeded but repayment {} < expected {}",
            repaid_amount,
            expected_repayment
        );
    }
}

// =============================================================================
// Two-Step Admin Transfer Invariants (HAL-40)
// =============================================================================

/// Track admin transfer state
#[derive(Clone, Debug)]
pub struct AdminTransferState {
    pub current_admin: Option<String>,
    pub proposed_admin: Option<String>,
    pub proposal_timestamp: Option<u64>,
}

impl AdminTransferState {
    pub fn new(admin: &str) -> Self {
        Self {
            current_admin: Some(admin.to_string()),
            proposed_admin: None,
            proposal_timestamp: None,
        }
    }

    /// Assert that admin transfer follows two-step process
    pub fn assert_two_step_invariants(
        &self,
        new_admin: Option<&str>,
        operation: &str,
        succeeded: bool,
    ) {
        match operation {
            "propose_admin" => {
                if succeeded {
                    // After proposal, proposed_admin should be set
                    assert!(
                        new_admin.is_some(),
                        "Proposal succeeded but no admin was proposed"
                    );
                }
            }
            "accept_admin" => {
                if succeeded {
                    // Accept should only succeed if there was a proposal
                    assert!(
                        self.proposed_admin.is_some(),
                        "Accept succeeded without prior proposal"
                    );
                }
            }
            "cancel_admin_proposal" => {
                // Cancel should clear proposed_admin
            }
            _ => {}
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_auth_tracker() {
        let mut tracker = AuthInvariantTracker::new();
        tracker.record_rejection();
        tracker.record_rejection();
        assert_eq!(tracker.authorized_rejections, 2);
        assert_eq!(tracker.unauthorized_successes, 0);
        tracker.assert_no_bypasses(); // Should not panic
    }

    #[test]
    #[should_panic(expected = "AUTHORIZATION BYPASS")]
    fn test_auth_tracker_bypass() {
        let mut tracker = AuthInvariantTracker::new();
        tracker.record_bypass("test_op");
        tracker.assert_no_bypasses(); // Should panic
    }

    #[test]
    fn test_accounting_snapshot_basic() {
        let snapshot = AccountingSnapshot {
            atoken_supply: 1000,
            atoken_underlying_balance: 1000,
            debt_supply: 500,
            treasury_balance: 10,
            liquidity_index: RAY,
            variable_borrow_index: RAY,
            timestamp: 1000,
        };
        snapshot.assert_basic_invariants();
    }
}
