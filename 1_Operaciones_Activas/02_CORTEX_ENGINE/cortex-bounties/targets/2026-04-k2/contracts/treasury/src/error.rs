use soroban_sdk::contracterror;
use k2_shared::KineticRouterError;

/// Error conditions for treasury contract operations.
///
/// Each variant represents a specific validation failure or invalid state that
/// can occur during treasury operations. Error codes are used for efficient
/// error handling and off-chain error reporting.
#[contracterror]
#[derive(Copy, Clone, Debug, Eq, PartialEq, PartialOrd, Ord)]
#[repr(u32)]
pub enum TreasuryError {
    /// Contract has not been initialized yet
    NotInitialized = 1,
    /// Attempt to initialize an already initialized contract
    AlreadyInitialized = 2,
    /// Caller does not have admin privileges
    Unauthorized = 3,
    /// Amount is zero or invalid
    InvalidAmount = 4,
    /// Insufficient balance for withdrawal operation
    InsufficientBalance = 5,
    /// Token transfer operation failed
    TransferFailed = 6,
    /// Recipient address is invalid
    InvalidRecipient = 7,
    /// No pending admin proposal exists
    NoPendingAdmin = 8,
    /// Caller is not the pending admin
    InvalidPendingAdmin = 9,
    /// Asset not found in storage
    AssetNotFound = 10,
}

impl From<KineticRouterError> for TreasuryError {
    fn from(err: KineticRouterError) -> Self {
        match err {
            KineticRouterError::NotInitialized => TreasuryError::NotInitialized,
            KineticRouterError::InvalidAmount => TreasuryError::InvalidAmount,
            KineticRouterError::Unauthorized => TreasuryError::Unauthorized,
            KineticRouterError::MathOverflow => TreasuryError::InvalidAmount,
            _ => TreasuryError::InvalidAmount,
        }
    }
}