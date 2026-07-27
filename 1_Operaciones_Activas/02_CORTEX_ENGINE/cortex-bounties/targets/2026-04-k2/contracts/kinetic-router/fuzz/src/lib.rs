//! Shared types for K2 fuzz testing
//!
//! This module contains types used by both the fuzz targets and the seed generator.
//! It also provides shared invariant checks derived from the Halborn security audit.

use arbitrary::Arbitrary;

pub mod invariants;

/// Which user to perform the operation as
#[derive(Arbitrary, Debug, Clone, Copy)]
pub enum User {
    User1,
    User2,
}

/// Individual operations that can be performed on the lending pool
#[derive(Arbitrary, Debug, Clone)]
pub enum Operation {
    /// Supply assets to the pool
    Supply { user: User, amount: u64 },
    /// Borrow assets from the pool (requires collateral)
    Borrow { user: User, amount: u64 },
    /// Repay borrowed assets
    Repay { user: User, amount: u64 },
    /// Withdraw supplied assets
    Withdraw { user: User, amount: u64 },
    /// Advance time to test interest accrual
    AdvanceTime { seconds: u32 },
    /// Supply additional collateral without withdrawing
    SupplyMore { user: User, amount: u64 },
    /// Partial withdraw (percentage-based, 0-100)
    PartialWithdraw { user: User, percent: u8 },
    /// Repay full debt
    RepayAll { user: User },
    /// Withdraw all available
    WithdrawAll { user: User },
    /// Set price (in basis points relative to base price, 100 = 1%)
    SetPrice { price_bps: u16 },
    /// Attempt liquidation
    Liquidate { liquidator: User, borrower: User, amount: u64 },
    /// Set collateral enabled/disabled for a user
    SetCollateralEnabled { user: User, enabled: bool },
}

/// Amount hints for edge case testing
#[derive(Arbitrary, Debug, Clone, Copy)]
pub enum AmountHint {
    /// Use the raw amount value
    Raw,
    /// Use u64::MAX
    Max,
    /// Use amount = 1 (minimum)
    Min,
    /// Use a power of 2 near the amount
    PowerOfTwo,
    /// Use 80% of max (LTV boundary)
    LtvBoundary,
}

/// Enhanced fuzz input with operation sequencing
#[derive(Arbitrary, Debug, Clone)]
pub struct LendingInput {
    /// Initial supply for user1 to bootstrap (required for most operations)
    pub initial_supply_user1: u64,
    /// Initial supply for user2
    pub initial_supply_user2: u64,
    /// Hint for how to interpret initial_supply
    pub initial_supply_hint: AmountHint,
    /// Sequence of operations to execute (up to 16)
    pub operations: [Option<Operation>; 16],
}

impl User {
    /// Discriminant value for User1 variant
    pub const USER1: u8 = 0;
    /// Discriminant value for User2 variant
    pub const USER2: u8 = 1;
}

impl Operation {
    /// Discriminant value for Supply variant
    pub const SUPPLY: u8 = 0;
    /// Discriminant value for Borrow variant
    pub const BORROW: u8 = 1;
    /// Discriminant value for Repay variant
    pub const REPAY: u8 = 2;
    /// Discriminant value for Withdraw variant
    pub const WITHDRAW: u8 = 3;
    /// Discriminant value for AdvanceTime variant
    pub const ADVANCE_TIME: u8 = 4;
    /// Discriminant value for SupplyMore variant
    pub const SUPPLY_MORE: u8 = 5;
    /// Discriminant value for PartialWithdraw variant
    pub const PARTIAL_WITHDRAW: u8 = 6;
    /// Discriminant value for RepayAll variant
    pub const REPAY_ALL: u8 = 7;
    /// Discriminant value for WithdrawAll variant
    pub const WITHDRAW_ALL: u8 = 8;
    /// Discriminant value for SetPrice variant
    pub const SET_PRICE: u8 = 9;
    /// Discriminant value for Liquidate variant
    pub const LIQUIDATE: u8 = 10;
    /// Discriminant value for SetCollateralEnabled variant
    pub const SET_COLLATERAL_ENABLED: u8 = 11;
}

impl AmountHint {
    /// Discriminant value for Raw variant
    pub const RAW: u8 = 0;
    /// Discriminant value for Max variant
    pub const MAX: u8 = 1;
    /// Discriminant value for Min variant
    pub const MIN: u8 = 2;
    /// Discriminant value for PowerOfTwo variant
    pub const POWER_OF_TWO: u8 = 3;
    /// Discriminant value for LtvBoundary variant
    pub const LTV_BOUNDARY: u8 = 4;
}
