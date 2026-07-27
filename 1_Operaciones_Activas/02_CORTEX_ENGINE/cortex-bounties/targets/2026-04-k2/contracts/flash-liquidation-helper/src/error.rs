use k2_shared::KineticRouterError;
use soroban_sdk::contracterror;

#[contracterror]
#[derive(Copy, Clone, Debug, Eq, PartialEq, PartialOrd, Ord)]
#[repr(u32)]
pub enum Error {
    Unknown = 0,
    MathOverflow = 1,
    InvalidLiquidation = 2,
    LiquidationAmountTooHigh = 3,
    InvalidAmount = 4,
    InsufficientSwapOut = 5,
    PriceOracleNotFound = 6,
    NoDebtOfRequestedType = 7,
}

impl From<KineticRouterError> for Error {
    fn from(err: KineticRouterError) -> Self {
        match err {
            KineticRouterError::MathOverflow => Error::MathOverflow,
            KineticRouterError::InvalidLiquidation => Error::InvalidLiquidation,
            KineticRouterError::LiquidationAmountTooHigh => Error::LiquidationAmountTooHigh,
            KineticRouterError::InvalidAmount => Error::InvalidAmount,
            KineticRouterError::InsufficientSwapOut => Error::InsufficientSwapOut,
            KineticRouterError::PriceOracleNotFound => Error::PriceOracleNotFound,
            KineticRouterError::NoDebtOfRequestedType => Error::NoDebtOfRequestedType,
            _ => Error::Unknown,
        }
    }
}

