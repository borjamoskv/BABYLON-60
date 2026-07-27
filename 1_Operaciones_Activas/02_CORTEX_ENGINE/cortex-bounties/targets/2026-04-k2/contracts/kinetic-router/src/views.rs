use crate::{calculation, storage, validation};
use k2_shared::{dex, safe_i128_to_u128, safe_u128_to_i128, KineticRouterError, ReserveData, UserAccountData, UserConfiguration, WAD};
use soroban_sdk::{Address, Env, IntoVal, Vec};

pub fn get_user_account_data(
    env: Env,
    user: Address,
) -> Result<UserAccountData, KineticRouterError> {
    calculation::calculate_user_account_data(&env, &user)
}

pub fn get_reserve_data(env: Env, asset: Address) -> Result<ReserveData, KineticRouterError> {
    storage::get_reserve_data(&env, &asset)
}

pub fn get_current_reserve_data(
    env: Env,
    asset: Address,
) -> Result<ReserveData, KineticRouterError> {
    calculation::get_current_reserve_data(&env, &asset)
}

pub fn get_current_liquidity_index(env: Env, asset: Address) -> Result<u128, KineticRouterError> {
    calculation::get_current_liquidity_index(&env, &asset)
}

pub fn get_current_var_borrow_idx(env: Env, asset: Address) -> Result<u128, KineticRouterError> {
    calculation::get_current_variable_borrow_index(&env, &asset)
}

pub fn get_user_configuration(env: Env, user: Address) -> UserConfiguration {
    storage::get_user_configuration(&env, &user)
}

pub fn get_reserves_list(env: Env) -> Vec<Address> {
    storage::get_reserves_list(&env)
}

pub fn update_reserve_state(
    env: Env,
    asset: Address,
) -> Result<ReserveData, KineticRouterError> {
    calculation::update_reserve_state(&env, &asset)
}

pub fn is_paused(env: Env) -> bool {
    storage::is_paused(&env)
}

pub fn get_protocol_reserves(env: Env, asset: Address) -> Result<u128, KineticRouterError> {
    calculation::get_protocol_reserves(&env, &asset)
}
