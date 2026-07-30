// C5-REAL EXERGY CERTIFIED
use anchor_lang::prelude::error_code;

#[error_code]
pub enum PriceFeedError {
    TooManyUpdaters,
    InvalidUpdater,
    NotFound,
    InvalidSize,
}
