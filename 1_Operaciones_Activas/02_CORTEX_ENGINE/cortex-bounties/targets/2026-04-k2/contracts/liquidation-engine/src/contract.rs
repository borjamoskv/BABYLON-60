use crate::admin;
use crate::calculation;
use crate::storage;
use crate::types::{LiquidationCall, LiquidationCalculation};
use crate::validation;
use k2_shared::*;
use soroban_sdk::{contract, contractimpl, Address, BytesN, Env, IntoVal, Symbol, U256, Vec};

#[contract]
pub struct LiquidationEngineContract;

#[contractimpl]
impl LiquidationEngineContract {
    pub fn __constructor(
        env: Env,
        admin: Address,
        kinetic_router: Address,
        price_oracle: Address,
    ) {
        if storage::is_initialized(&env) {
             panic!("Already initialized");
        }

        crate::upgrade::initialize_admin(&env, &admin);
        storage::set_admin(&env, &admin);
        storage::set_kinetic_router(&env, &kinetic_router);
        storage::set_price_oracle(&env, &price_oracle);
        storage::set_initialized(&env);
    }

    pub fn initialize(
        _env: Env,
        _admin: Address,
        _kinetic_router: Address,
        _price_oracle: Address,
    ) -> Result<(), KineticRouterError> {
        panic!("Initialization is atomic at deployment. Use __constructor.");
    }

    pub fn calculate_liquidation(
        env: Env,
        collateral_asset: Address,
        debt_asset: Address,
        user: Address,
        debt_to_cover: u128,
    ) -> Result<LiquidationCalculation, KineticRouterError> {
        calculation::calculate_liquidation(
            &env,
            collateral_asset,
            debt_asset,
            user,
            debt_to_cover,
        )
    }

    pub fn execute_liquidation(
        env: Env,
        liquidator: Address,
        collateral_asset: Address,
        debt_asset: Address,
        user: Address,
        debt_to_cover: u128,
        _receive_a_token: bool,
    ) -> Result<LiquidationCall, KineticRouterError> {
        let current_timestamp = get_current_timestamp(&env);

        validation::validate_liquidation_params(
            &env,
            &collateral_asset,
            &debt_asset,
            &user,
            debt_to_cover,
        )?;

        let liquidation_result =
            calculation::calculate_liquidation(&env, collateral_asset.clone(), debt_asset.clone(), user.clone(), debt_to_cover)?;

        let kinetic_router = storage::get_kinetic_router(&env)?;
        let mut args = Vec::new(&env);
        args.push_back(liquidator.clone().into_val(&env));
        args.push_back(collateral_asset.clone().into_val(&env));
        args.push_back(debt_asset.clone().into_val(&env));
        args.push_back(user.clone().into_val(&env));
        args.push_back(debt_to_cover.into_val(&env));
        args.push_back(_receive_a_token.into_val(&env)); 

        let _: () =
            env.invoke_contract(&kinetic_router, &Symbol::new(&env, "liquidation_call"), args);

        let liquidation_call = LiquidationCall {
            liquidator,
            user,
            collateral_asset,
            debt_asset,
            debt_to_cover,
            collateral_to_liquidate: liquidation_result.collateral_amount,
            liquidation_bonus: liquidation_result.bonus_amount,
            timestamp: current_timestamp,
        };

        storage::add_liquidation_record(&env, &liquidation_call);

        Ok(liquidation_call)
    }

    pub fn get_max_liquidatable_debt(
        env: Env,
        _collateral_asset: Address,
        _debt_asset: Address,
        user: Address,
    ) -> Result<u128, KineticRouterError> {
        let kinetic_router = storage::get_kinetic_router(&env)?;
        let mut args = Vec::new(&env);
        args.push_back(user.clone().into_val(&env));

        let user_account_data: UserAccountData = env.invoke_contract(
            &kinetic_router,
            &Symbol::new(&env, "get_user_account_data"),
            args,
        );

        let close_factor = storage::get_close_factor(&env);
        let max_liquidatable_debt = user_account_data.total_debt_base
            .checked_mul(close_factor)
            .ok_or(KineticRouterError::MathOverflow)?
            .checked_div(BASIS_POINTS_MULTIPLIER)
            .ok_or(KineticRouterError::MathOverflow)?;

        Ok(max_liquidatable_debt)
    }

    pub fn get_liquidation_bonus(env: Env, asset: Address) -> Result<u128, KineticRouterError> {
        calculation::get_liquidation_bonus(env, asset)
    }

    pub fn is_position_liquidatable(env: Env, user: Address) -> Result<bool, KineticRouterError> {
        let kinetic_router = storage::get_kinetic_router(&env)?;
        let mut args = Vec::new(&env);
        args.push_back(user.clone().into_val(&env));

        let user_account_data: UserAccountData = env.invoke_contract(
            &kinetic_router,
            &Symbol::new(&env, "get_user_account_data"),
            args,
        );

        Ok(user_account_data.health_factor < WAD)
    }

    pub fn get_user_health_factor(env: Env, user: Address) -> Result<u128, KineticRouterError> {
        let kinetic_router = storage::get_kinetic_router(&env)?;
        let mut args = Vec::new(&env);
        args.push_back(user.clone().into_val(&env));

        let user_account_data: UserAccountData = env.invoke_contract(
            &kinetic_router,
            &Symbol::new(&env, "get_user_account_data"),
            args,
        );
        Ok(user_account_data.health_factor)
    }

    pub fn calculate_collateral_needed(
        env: Env,
        collateral_asset: Address,
        debt_asset: Address,
        debt_amount: u128,
    ) -> Result<u128, KineticRouterError> {
        let price_oracle = storage::get_price_oracle(&env)?;

        let collateral_asset_type = Asset::Stellar(collateral_asset.clone());
        let debt_asset_type = Asset::Stellar(debt_asset.clone());

        let mut collateral_args = Vec::new(&env);
        collateral_args.push_back(collateral_asset_type.into_val(&env));
        let collateral_price: u128 = env.invoke_contract(
            &price_oracle,
            &Symbol::new(&env, "get_asset_price"),
            collateral_args,
        );

        let mut debt_args = Vec::new(&env);
        debt_args.push_back(debt_asset_type.into_val(&env));
        let debt_price: u128 = env.invoke_contract(
            &price_oracle,
            &Symbol::new(&env, "get_asset_price"),
            debt_args,
        );

        let liquidation_bonus = Self::get_liquidation_bonus(env.clone(), collateral_asset)?;

        let debt_amount_base = wad_mul(&env, debt_amount, debt_price)?;

        // Safe calculation using U256 to prevent overflow
        let debt_u256 = U256::from_u128(&env, debt_amount_base);
        let bonus_u256 = U256::from_u128(&env, liquidation_bonus);
        let wad_u256 = U256::from_u128(&env, WAD);
        let bonus_amount_u256 = debt_u256.mul(&bonus_u256).div(&wad_u256);
        let collateral_amount_base = debt_u256
            .add(&bonus_amount_u256)
            .to_u128()
            .ok_or(KineticRouterError::MathOverflow)?;
        let collateral_amount = wad_div(&env, collateral_amount_base, collateral_price)?;

        Ok(collateral_amount)
    }

    pub fn get_close_factor(env: Env) -> u128 {
        storage::get_close_factor(&env)
    }

    pub fn set_close_factor(env: Env, close_factor: u128) -> Result<(), KineticRouterError> {
        admin::set_close_factor(&env, close_factor)
    }

    pub fn get_user_liquidation_ids(env: Env, user: Address) -> Vec<u32> {
        storage::get_user_liquidation_ids(&env, &user)
    }

    pub fn get_liquidation_record(env: Env, liquidation_id: u32) -> Option<LiquidationCall> {
        storage::get_liquidation_record(&env, liquidation_id)
    }

    pub fn get_total_liquidations(env: Env) -> u32 {
        storage::get_total_liquidations_count(&env)
    }

    pub fn pause(env: Env) -> Result<(), KineticRouterError> {
        admin::pause(&env)
    }

    pub fn unpause(env: Env) -> Result<(), KineticRouterError> {
        admin::unpause(&env)
    }

    pub fn is_paused(env: Env) -> bool {
        storage::is_paused(&env)
    }

    pub fn upgrade(env: Env, new_wasm_hash: BytesN<32>) -> Result<(), KineticRouterError> {
        let admin = crate::upgrade::get_admin(&env).map_err(|_| KineticRouterError::Unauthorized)?;
        admin.require_auth();
        crate::upgrade::upgrade(env, new_wasm_hash).map_err(|_| KineticRouterError::Unauthorized)
    }

    pub fn version(_env: Env) -> u32 {
        crate::upgrade::version()
    }
}
