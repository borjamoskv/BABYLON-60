#![allow(dead_code)]
//! This module contains administrative functions for the Kinetic Router contract.
//! These functions are intended to be called by the contract admin to configure protocol parameters
//! and manage the contract's lifecycle. All functions are part of the contract's public interface.

use crate::events;
use crate::storage;
use crate::upgrade;
use k2_shared::*;
use soroban_sdk::{symbol_short, Address, BytesN, Env};

/// Set the flash loan premium (fee charged on flash loans)
pub fn set_flash_loan_premium(env: Env, premium_bps: u128) -> Result<(), KineticRouterError> {
    let admin = storage::get_pool_admin(&env)?;
    admin.require_auth();

    if premium_bps > storage::get_flash_loan_premium_max(&env) {
        return Err(KineticRouterError::InvalidAmount);
    }

    let old_premium = storage::get_flash_loan_premium(&env);
    storage::set_flash_loan_premium(&env, premium_bps);
    
    env.events().publish(
        (symbol_short!("fl_prem"), symbol_short!("updated")),
        events::FlashLoanPremiumUpdatedEvent {
            old_premium_bps: old_premium,
            new_premium_bps: premium_bps,
        },
    );
    
    Ok(())
}

/// Set the maximum allowed flash loan premium
pub fn set_flash_loan_premium_max(env: Env, premium_max_bps: u128) -> Result<(), KineticRouterError> {
    let admin = storage::get_pool_admin(&env)?;
    admin.require_auth();

    storage::set_flash_loan_premium_max(&env, premium_max_bps);
    Ok(())
}

/// Get the maximum allowed flash loan premium
pub fn get_flash_loan_premium_max(env: Env) -> u128 {
    storage::get_flash_loan_premium_max(&env)
}

/// Set the health factor threshold for liquidation
pub fn set_hf_liquidation_threshold(env: Env, threshold: u128) -> Result<(), KineticRouterError> {
    let admin = storage::get_pool_admin(&env)?;
    admin.require_auth();

    storage::set_health_factor_liquidation_threshold(&env, threshold);
    Ok(())
}

/// Get the health factor liquidation threshold
pub fn get_hf_liquidation_threshold(env: Env) -> u128 {
    storage::get_health_factor_liquidation_threshold(&env)
}

/// Set minimum swap output in basis points for flash liquidations
pub fn set_min_swap_output_bps(env: Env, min_output_bps: u128) -> Result<(), KineticRouterError> {
    let admin = storage::get_pool_admin(&env)?;
    admin.require_auth();

    // M-05: Enforce slippage floor to prevent sandwich attacks
    if min_output_bps < MIN_SWAP_OUTPUT_FLOOR_BPS || min_output_bps > BASIS_POINTS_MULTIPLIER {
        return Err(KineticRouterError::InvalidAmount);
    }

    storage::set_min_swap_output_bps(&env, min_output_bps);
    Ok(())
}

/// Get minimum swap output in basis points
pub fn get_min_swap_output_bps(env: Env) -> u128 {
    storage::get_min_swap_output_bps(&env)
}


/// Set partial liquidation health factor threshold
pub fn set_partial_liq_hf_threshold(env: Env, threshold: u128) -> Result<(), KineticRouterError> {
    let admin = storage::get_pool_admin(&env)?;
    admin.require_auth();

    storage::set_partial_liquidation_hf_threshold(&env, threshold);
    Ok(())
}

/// Get partial liquidation health factor threshold
pub fn get_partial_liq_hf_threshold(env: Env) -> u128 {
    storage::get_partial_liquidation_hf_threshold(&env)
}

/// Set liquidation tracker expiry in ledgers
pub fn set_liquidation_tracker_expiry(env: Env, expiry_ledgers: u32) -> Result<(), KineticRouterError> {
    let admin = storage::get_pool_admin(&env)?;
    admin.require_auth();

    storage::set_liquidation_tracker_expiry(&env, expiry_ledgers);
    Ok(())
}

/// Get liquidation tracker expiry in ledgers
pub fn get_liquidation_tracker_expiry(env: Env) -> u32 {
    storage::get_liquidation_tracker_expiry(&env)
}

/// Get the current flash loan premium
pub fn get_flash_loan_premium(env: Env) -> u128 {
    storage::get_flash_loan_premium(&env)
}

/// Set the treasury address
pub fn set_treasury(env: Env, treasury: Address) -> Result<(), KineticRouterError> {
    let admin = storage::get_pool_admin(&env)?;
    admin.require_auth();

    let old_treasury = storage::get_treasury(&env);
    storage::set_treasury(&env, &treasury);
    
    env.events().publish(
        (symbol_short!("treasury"), symbol_short!("updated")),
        events::TreasuryUpdatedEvent {
            old_treasury,
            new_treasury: treasury,
        },
    );
    
    Ok(())
}

/// Get the treasury address
pub fn get_treasury(env: Env) -> Option<Address> {
    storage::get_treasury(&env)
}

/// Set the flash liquidation helper contract address
pub fn set_flash_liquidation_helper(env: Env, helper: Address) -> Result<(), KineticRouterError> {
    let admin = storage::get_pool_admin(&env)?;
    admin.require_auth();

    storage::set_flash_liquidation_helper(&env, &helper);
    Ok(())
}

/// Get the flash liquidation helper contract address
pub fn get_flash_liquidation_helper(env: Env) -> Option<Address> {
    storage::get_flash_liquidation_helper(&env)
}

/// Set the pool configurator contract address
pub fn set_pool_configurator(env: Env, configurator: Address) -> Result<(), KineticRouterError> {
    let admin = storage::get_pool_admin(&env)?;
    admin.require_auth();

    storage::set_pool_configurator(&env, &configurator);
    Ok(())
}

/// Get the pool configurator contract address
pub fn get_pool_configurator(env: Env) -> Option<Address> {
    storage::get_pool_configurator(&env)
}

/// Set the incentives contract address
pub fn set_incentives_contract(env: Env, incentives_contract: Address) -> Result<(), KineticRouterError> {
    let admin = storage::get_pool_admin(&env)?;
    admin.require_auth();

    storage::set_incentives_contract(&env, &incentives_contract);
    Ok(())
}

/// Get the incentives contract address
pub fn get_incentives_contract(env: Env) -> Option<Address> {
    storage::get_incentives_contract(&env)
}

/// Pause the protocol (emergency admin only)
pub fn pause(env: Env) -> Result<(), KineticRouterError> {
    let emergency_admin = storage::get_emergency_admin(&env).ok_or(KineticRouterError::Unauthorized)?;
    emergency_admin.require_auth();

    storage::set_paused(&env, true);
    
    env.events().publish(
        (symbol_short!("paused"),),
        events::ProtocolPausedEvent {
            paused_by: emergency_admin,
        },
    );
    
    Ok(())
}

/// Unpause the protocol (admin only)
pub fn unpause(env: Env) -> Result<(), KineticRouterError> {
    let admin = storage::get_pool_admin(&env)?;
    admin.require_auth();

    storage::set_paused(&env, false);
    
    let admin_addr = admin.clone();
    env.events().publish(
        (symbol_short!("unpaused"),),
        events::ProtocolUnpausedEvent {
            unpaused_by: admin_addr,
        },
    );
    
    Ok(())
}

/// Check if the protocol is paused
pub fn is_paused(env: Env) -> bool {
    storage::is_paused(&env)
}

/// Upgrade the contract
pub fn upgrade(env: Env, new_wasm_hash: BytesN<32>) -> Result<(), KineticRouterError> {
    upgrade::upgrade(env, new_wasm_hash).map_err(|_| KineticRouterError::Unauthorized)
}

/// Get contract version
pub fn version(_env: Env) -> u32 {
    upgrade::version()
}

/// Get admin address
pub fn get_admin(env: Env) -> Result<Address, KineticRouterError> {
    upgrade::get_admin(&env).map_err(|_| KineticRouterError::Unauthorized)
}
