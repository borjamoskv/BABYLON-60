use soroban_sdk::contracterror;

#[contracterror]
#[derive(Copy, Clone, Debug, Eq, PartialEq, PartialOrd, Ord)]
#[repr(u32)]
pub enum KineticRouterError {
    InvalidAmount = 1,
    AssetNotActive = 2,
    AssetFrozen = 3,
    AssetPaused = 4,
    BorrowingNotEnabled = 5,
    InsufficientCollateral = 7,
    HealthFactorTooLow = 8,
    PriceOracleNotFound = 10,
    InvalidLiquidation = 11,
    LiquidationAmountTooHigh = 12,
    NoDebtOfRequestedType = 13,
    InvalidFlashLoanParams = 14,
    FlashLoanNotAuthorized = 15,
    IsolationModeViolation = 16,
    PriceOracleInvocationFailed = 17,
    PriceOracleError = 18,
    SupplyCapExceeded = 19,
    BorrowCapExceeded = 20,
    DebtCeilingExceeded = 21,
    UserInIsolationMode = 22,
    ReserveNotFound = 24,
    UserNotFound = 25,
    Unauthorized = 26,
    AlreadyInitialized = 27,
    NotInitialized = 28,
    ReserveAlreadyInitialized = 29,
    FlashLoanExecutionFailed = 30,
    FlashLoanNotRepaid = 31,
    InsufficientFlashLoanLiquidity = 32,
    ATokenMintFailed = 33,
    DebtTokenMintFailed = 34,
    UnderlyingTransferFailed = 35,
    FlashLoanTransferFailed = 36,
    MathOverflow = 37,
    Expired = 38,
    InsufficientSwapOut = 39,
    MinProfitNotMet = 40,
    TreasuryNotSet = 41,
    InsufficientLiquidity = 42,
    AMMRequired = 43,
    UnauthorizedAMM = 44,
    AdapterNotInitialized = 45,
    ATokenBurnFailed = 46,
    WASMHashNotSet = 47,
    TokenDeploymentFailed = 48,
    TokenInitializationFailed = 49,
    AddressNotWhitelisted = 50,
    NoPendingAdmin = 51,
    InvalidPendingAdmin = 52,
    TokenCallFailed = 53,
}

#[contracterror]
#[derive(Copy, Clone, Debug, Eq, PartialEq, PartialOrd, Ord)]
#[repr(u32)]
pub enum OracleError {
    AssetPriceNotFound = 1,
    PriceSourceNotSet = 2,
    InvalidPriceSource = 3,
    PriceTooOld = 4,
    PriceHeartbeatExceeded = 5,
    NotInitialized = 6,
    AssetNotWhitelisted = 7,
    AssetDisabled = 8,
    OracleQueryFailed = 9,
    InvalidCalculation = 10,
    FallbackNotImplemented = 11,
    AlreadyInitialized = 12,
    AssetAlreadyWhitelisted = 13,
    Unauthorized = 14,
    PriceManipulationDetected = 15,
    PriceChangeTooLarge = 16,
    OverrideExpired = 17,
    MathOverflow = 18,
    InvalidPrice = 19,
    /// M-05
    InvalidConfig = 20,
    /// L-04
    OverrideDurationTooLong = 21,
}

#[contracterror]
#[derive(Copy, Clone, Debug, Eq, PartialEq, PartialOrd, Ord)]
#[repr(u32)]
pub enum TokenError {
    InsufficientBalance = 1,
    TransferFailed = 2,
    MintFailed = 3,
    BurnFailed = 4,
    InvalidRecipient = 5,
    TokenNotFound = 6,
    Unauthorized = 7,
    InvalidAmount = 8,
    InsufficientAllowance = 9,
    InvalidIndex = 10,
    UnsupportedOperation = 11,
    AlreadyInitialized = 12,
}

#[contracterror]
#[derive(Copy, Clone, Debug, Eq, PartialEq, PartialOrd, Ord)]
#[repr(u32)]
pub enum ReserveManagementError {
    MaxReservesReached = 1,
    CannotDropActiveReserve = 2,
}

#[contracterror]
#[derive(Copy, Clone, Debug, Eq, PartialEq, PartialOrd, Ord)]
#[repr(u32)]
pub enum UserReserveError {
    MaxUserReservesExceeded = 1,
}

#[contracterror]
#[derive(Copy, Clone, Debug, Eq, PartialEq, PartialOrd, Ord)]
#[repr(u32)]
pub enum OperationError {
    InvalidRecipient = 1,
    RecipientIsAToken = 2,
    RecipientIsDebtToken = 3,
    DebtTokenBurnFailed = 4,
    InvalidRepayAmount = 5,
    /// LOW-3: Partial repay would leave dust debt below min_remaining_debt
    RepayWouldLeaveDust = 6,
}

#[contracterror]
#[derive(Copy, Clone, Debug, Eq, PartialEq, PartialOrd, Ord)]
#[repr(u32)]
pub enum SecurityError {
    ReentrancyDetected = 1,
    InvalidFundingAmount = 2,
    TTLExtensionFailed = 3,
}

/// L-13
/// Replaces raw panic!() calls for on-chain debuggability.
#[contracterror]
#[derive(Copy, Clone, Debug, Eq, PartialEq, PartialOrd, Ord)]
#[repr(u32)]
pub enum ConfigurationError {
    /// LTV exceeds 10000 bps (100%)
    InvalidLTV = 1,
    /// Liquidation threshold exceeds 10000 bps (100%)
    InvalidLiquidationThreshold = 2,
    /// Liquidation bonus exceeds 10000 bps (100%)
    InvalidLiquidationBonus = 3,
}
