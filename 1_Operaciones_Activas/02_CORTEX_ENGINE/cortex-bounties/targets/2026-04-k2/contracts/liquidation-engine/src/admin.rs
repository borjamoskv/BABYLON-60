use k2_shared::KineticRouterError;
use soroban_sdk::Env;

use crate::storage;

pub fn set_close_factor(env: &Env, close_factor: u128) -> Result<(), KineticRouterError> {
    let admin = storage::get_admin(env).ok_or(KineticRouterError::NotInitialized)?;
    admin.require_auth();

    if close_factor > k2_shared::MAX_LIQUIDATION_CLOSE_FACTOR {
        return Err(KineticRouterError::InvalidAmount);
    }

    storage::set_close_factor(env, close_factor);
    
    env.events().publish(
        (soroban_sdk::symbol_short!("close"), soroban_sdk::symbol_short!("factor"), soroban_sdk::symbol_short!("set")),
        close_factor,
    );
    
    Ok(())
}

pub fn pause(env: &Env) -> Result<(), KineticRouterError> {
    let admin = storage::get_admin(env).ok_or(KineticRouterError::NotInitialized)?;
    admin.require_auth();

    storage::set_paused(env, true);
    
    env.events().publish(
        (soroban_sdk::symbol_short!("pause"),),
        true,
    );
    
    Ok(())
}

pub fn unpause(env: &Env) -> Result<(), KineticRouterError> {
    let admin = storage::get_admin(env).ok_or(KineticRouterError::NotInitialized)?;
    admin.require_auth();

    storage::set_paused(env, false);
    
    env.events().publish(
        (soroban_sdk::symbol_short!("unpause"),),
        false,
    );
    
    Ok(())
}
