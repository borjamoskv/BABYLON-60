use soroban_sdk::contracterror;
use k2_shared::KineticRouterError;

/// Incentives contract errors
#[contracterror]
#[derive(Copy, Clone, Debug, Eq, PartialEq, PartialOrd, Ord)]
#[repr(u32)]
pub enum IncentivesError {
    /// Contract already initialized
    AlreadyInitialized = 1,
    /// Contract not initialized
    NotInitialized = 2,
    /// Unauthorized access
    Unauthorized = 3,
    /// Invalid reward type (must be 0 for supply or 1 for borrow)
    InvalidRewardType = 4,
    /// Asset reward configuration not found
    AssetRewardConfigNotFound = 5,
    /// Math overflow occurred during calculation
    MathOverflow = 6,
    /// Insufficient rewards available to claim
    InsufficientRewards = 7,
    /// Contract is paused
    ContractPaused = 8,
    /// Maximum number of reward tokens per asset exceeded
    MaxRewardTokensExceeded = 9,
    /// Maximum number of assets exceeded
    MaxAssetsExceeded = 10,
    /// Token returned a negative balance (broken invariant)
    InvalidBalance = 11,
    /// Cannot delete reward token that is still active
    RewardTokenStillActive = 12,
}

impl From<KineticRouterError> for IncentivesError {
    fn from(err: KineticRouterError) -> Self {
        match err {
            KineticRouterError::NotInitialized => IncentivesError::NotInitialized,
            KineticRouterError::InvalidAmount => IncentivesError::MathOverflow,
            KineticRouterError::Unauthorized => IncentivesError::Unauthorized,
            KineticRouterError::MathOverflow => IncentivesError::MathOverflow,
            _ => IncentivesError::MathOverflow,
        }
    }
}
