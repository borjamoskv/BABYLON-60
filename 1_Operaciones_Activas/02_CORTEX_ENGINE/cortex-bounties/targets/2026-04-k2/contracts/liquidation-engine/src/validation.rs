use k2_shared::{validate_amount, KineticRouterError};
use soroban_sdk::{Address, Env};

use crate::storage;

pub fn validate_liquidation_params(
    env: &Env,
    collateral_asset: &Address,
    debt_asset: &Address,
    _user: &Address,
    debt_to_cover: u128,
) -> Result<(), KineticRouterError> {
    if storage::is_paused(env) {
        return Err(KineticRouterError::AssetPaused);
    }

    validate_amount(debt_to_cover)?;

    Ok(())
}
