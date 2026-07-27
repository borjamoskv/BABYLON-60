use crate::storage;
use k2_shared::{Asset, KineticRouterError, ReserveConfiguration, UserAccountData, BASIS_POINTS_MULTIPLIER, WAD};
use soroban_sdk::{Address, Env, IntoVal, Symbol, U256, Vec};

use crate::types::LiquidationCalculation;

pub fn calculate_liquidation(
    env: &Env,
    collateral_asset: Address,
    debt_asset: Address,
    user: Address,
    debt_to_cover: u128,
) -> Result<LiquidationCalculation, KineticRouterError> {
    let kinetic_router = storage::get_kinetic_router(env)?;
    let mut args = Vec::new(env);
    args.push_back(user.clone().into_val(env));

    let user_account_data: UserAccountData = env.invoke_contract(
        &kinetic_router,
        &Symbol::new(env, "get_user_account_data"),
        args,
    );

    if user_account_data.health_factor >= WAD {
        return Err(KineticRouterError::InvalidLiquidation);
    }

    let price_oracle = storage::get_price_oracle(env)?;

    let collateral_asset_type = Asset::Stellar(collateral_asset.clone());
    let debt_asset_type = Asset::Stellar(debt_asset.clone());

    let mut collateral_args = Vec::new(env);
    collateral_args.push_back(collateral_asset_type.into_val(env));
    let collateral_price: u128 = env.invoke_contract(
        &price_oracle,
        &Symbol::new(env, "get_asset_price"),
        collateral_args,
    );

    let mut debt_args = Vec::new(env);
    debt_args.push_back(debt_asset_type.into_val(env));
    let debt_price: u128 = env.invoke_contract(
        &price_oracle,
        &Symbol::new(env, "get_asset_price"),
        debt_args,
    );

    let close_factor = storage::get_close_factor(env);
    // Safe multiplication using U256 to prevent overflow
    let debt_u256 = U256::from_u128(env, user_account_data.total_debt_base);
    let factor_u256 = U256::from_u128(env, close_factor);
    let bps_u256 = U256::from_u128(env, BASIS_POINTS_MULTIPLIER);
    let max_liquidatable_debt_total = (debt_u256.mul(&factor_u256).div(&bps_u256))
        .to_u128()
        .ok_or(KineticRouterError::MathOverflow)?;

    // Get cumulative liquidations for this user in current transaction
    let already_liquidated_this_tx = storage::get_user_liquidated_this_tx(env, &user);
    
    // Calculate remaining liquidatable amount
    let remaining_liquidatable = if already_liquidated_this_tx >= max_liquidatable_debt_total {
        0
    } else {
        max_liquidatable_debt_total - already_liquidated_this_tx
    };

    let debt_to_cover_base = k2_shared::wad_mul(env, debt_to_cover, debt_price)?;

    // Enforce cumulative close factor limit
    let actual_debt_to_cover = if debt_to_cover_base > remaining_liquidatable {
        remaining_liquidatable
    } else {
        debt_to_cover_base
    };

    // Track cumulative liquidation for this transaction
    if actual_debt_to_cover > 0 {
        storage::add_user_liquidated_this_tx(env, &user, actual_debt_to_cover);
    }

    let liquidation_bonus_bps = get_liquidation_bonus(env.clone(), collateral_asset.clone())?;
    
    // Safe calculation of liquidation_bonus_percentage using U256
    let bonus_bps_u256 = U256::from_u128(env, liquidation_bonus_bps);
    let bps_mult_u256 = U256::from_u128(env, BASIS_POINTS_MULTIPLIER);
    let wad_u256 = U256::from_u128(env, WAD);
    let liquidation_bonus_percentage = (bonus_bps_u256.mul(&bps_mult_u256).div(&wad_u256))
        .to_u128()
        .ok_or(KineticRouterError::MathOverflow)?;

    // Safe calculation of collateral_amount_base using U256 to prevent overflow
    let debt_u256 = U256::from_u128(env, actual_debt_to_cover);
    let bonus_u256 = U256::from_u128(env, liquidation_bonus_bps);
    let bonus_amount_u256 = debt_u256.mul(&bonus_u256).div(&wad_u256);
    let collateral_amount_base = debt_u256
        .add(&bonus_amount_u256)
        .to_u128()
        .ok_or(KineticRouterError::MathOverflow)?;
    let collateral_amount = k2_shared::wad_div(env, collateral_amount_base, collateral_price)?;
    let bonus_amount = collateral_amount_base - actual_debt_to_cover;

    let remaining_debt = user_account_data.total_debt_base - actual_debt_to_cover;
    let remaining_collateral = user_account_data.total_collateral_base - collateral_amount_base;

    let health_factor_after = if remaining_debt == 0 {
        u128::MAX
    } else {
        // Safe multiplication using U256 to prevent overflow
        let collateral_u256 = U256::from_u128(env, remaining_collateral);
        let threshold_u256 = U256::from_u128(env, user_account_data.current_liquidation_threshold);
        let debt_u256 = U256::from_u128(env, remaining_debt);
        (collateral_u256.mul(&threshold_u256).div(&debt_u256))
            .to_u128()
            .ok_or(KineticRouterError::MathOverflow)?
    };

    let result = LiquidationCalculation {
        collateral_amount,
        bonus_amount,
        liquidation_bonus_percentage,
        health_factor_after,
    };

    Ok(result)
}

pub fn get_liquidation_bonus(env: Env, asset: Address) -> Result<u128, KineticRouterError> {
    let kinetic_router = storage::get_kinetic_router(&env)?;
    let mut args = Vec::new(&env);
    args.push_back(asset.clone().into_val(&env));

    let reserve_data: k2_shared::ReserveData =
        env.invoke_contract(&kinetic_router, &Symbol::new(&env, "get_reserve_data"), args);

    // Convert kinetic router ReserveConfiguration to shared ReserveConfiguration
    let shared_config = ReserveConfiguration {
        data_low: reserve_data.configuration.data_low,
        data_high: reserve_data.configuration.data_high,
    };

    // Get liquidation bonus from reserve configuration
    let liquidation_bonus_bps = shared_config.get_liquidation_bonus() as u128;
    
    // Safe multiplication using U256 to prevent overflow
    let bonus_bps_u256 = U256::from_u128(&env, liquidation_bonus_bps);
    let wad_u256 = U256::from_u128(&env, WAD);
    let bps_mult_u256 = U256::from_u128(&env, BASIS_POINTS_MULTIPLIER);
    let liquidation_bonus_wad = (bonus_bps_u256.mul(&wad_u256).div(&bps_mult_u256))
        .to_u128()
        .ok_or(KineticRouterError::MathOverflow)?;

    Ok(liquidation_bonus_wad)
}
