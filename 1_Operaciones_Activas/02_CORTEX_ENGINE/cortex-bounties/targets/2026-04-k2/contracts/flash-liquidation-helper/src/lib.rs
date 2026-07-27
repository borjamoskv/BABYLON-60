#![no_std]
use soroban_sdk::{contract, contractimpl, Env};
use k2_shared::{
    FlashLiquidationValidationParams, FlashLiquidationValidationResult,
};

mod error;
mod validation;

pub use error::Error;
pub use validation::*;

#[contract]
pub struct FlashLiquidationHelper;

#[contractimpl]
impl FlashLiquidationHelper {
    /// Validate flash liquidation parameters
    pub fn validate(
        env: Env,
        params: FlashLiquidationValidationParams,
    ) -> Result<FlashLiquidationValidationResult, Error> {
        validation::validate_flash_liquidation(
            &env,
            &params,
        )
        .map_err(|e| Error::from(e))
    }
}
