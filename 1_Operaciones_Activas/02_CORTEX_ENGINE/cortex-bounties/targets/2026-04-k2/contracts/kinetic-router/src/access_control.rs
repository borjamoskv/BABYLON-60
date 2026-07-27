use crate::storage;
use k2_shared::*;
use soroban_sdk::{symbol_short, Address, Env, Vec};

/// Set reserve whitelist (admin only).
///
/// # Arguments
/// * `asset` - Underlying asset address
/// * `whitelist` - Addresses allowed to interact with this reserve
///
/// # Behavior
/// * Empty whitelist: open access (no restrictions)
/// * Non-empty whitelist: restricted to listed addresses only
///
/// # Note
/// This replaces the entire whitelist. To modify the whitelist,
/// first get the current list, modify it, then set the complete new list.
///
/// # Errors
/// * `Unauthorized` - Caller is not admin
pub fn set_reserve_whitelist(
    env: Env,
    asset: Address,
    whitelist: Vec<Address>,
) -> Result<(), KineticRouterError> {
    let admin = storage::get_pool_admin(&env)?;
    admin.require_auth();

    storage::set_reserve_whitelist(&env, &asset, &whitelist);

    env.events()
        .publish((symbol_short!("wlist"), asset.clone()), whitelist.len());

    Ok(())
}

/// Get reserve whitelist
///
/// Returns empty vector if no restrictions configured
pub fn get_reserve_whitelist(env: Env, asset: Address) -> Vec<Address> {
    storage::get_reserve_whitelist(&env, &asset)
}

/// Check if address is whitelisted for reserve
///
/// Returns true if address is whitelisted or whitelist is empty (open access)
pub fn is_whitelisted_for_reserve(env: Env, asset: Address, address: Address) -> bool {
    storage::is_address_whitelisted_for_reserve(&env, &asset, &address)
}

/// Set liquidation whitelist (admin only).
///
/// # Arguments
/// * `whitelist` - Addresses allowed to perform liquidations
///
/// # Behavior
/// * Empty whitelist: open access to liquidation
/// * Non-empty whitelist: restricted to listed addresses only
///
/// # Errors
/// * `Unauthorized` - Caller is not admin
pub fn set_liquidation_whitelist(
    env: Env,
    whitelist: Vec<Address>,
) -> Result<(), KineticRouterError> {
    let admin = storage::get_pool_admin(&env)?;
    admin.require_auth();

    storage::set_liquidation_whitelist(&env, &whitelist);

    env.events()
        .publish((symbol_short!("liqwlist"), 0), whitelist.len());

    Ok(())
}

/// Get liquidation whitelist.
/// Returns empty vector if no restrictions configured (open access).
pub fn get_liquidation_whitelist(env: Env) -> Vec<Address> {
    storage::get_liquidation_whitelist(&env)
}

/// Check if address is whitelisted for liquidation.
/// Returns true if address is whitelisted or whitelist is empty (open access).
pub fn is_whitelisted_for_liquidation(env: Env, address: Address) -> bool {
    storage::is_address_whitelisted_for_liquidation(&env, &address)
}

/// Set reserve blacklist (admin only).
/// # Arguments
/// * `asset` - Underlying asset address
/// * `blacklist` - Addresses blocked from interacting with this reserve
///
/// # Behavior
/// * Empty blacklist: open access
/// * Non-empty blacklist: blocks listed addresses
///
/// # Errors
/// * `Unauthorized` - Caller is not admin
pub fn set_reserve_blacklist(
    env: Env,
    asset: Address,
    blacklist: Vec<Address>,
) -> Result<(), KineticRouterError> {
    let admin = storage::get_pool_admin(&env)?;
    admin.require_auth();

    storage::set_reserve_blacklist(&env, &asset, &blacklist);

    env.events()
        .publish((symbol_short!("rblack"), asset.clone()), blacklist.len());

    Ok(())
}

/// Get reserve blacklist.
/// Returns empty vector if no blacklist is configured (open access).
pub fn get_reserve_blacklist(env: Env, asset: Address) -> Vec<Address> {
    storage::get_reserve_blacklist(&env, &asset)
}

/// Check if address is blacklisted for reserve.
/// Returns true if address is blacklisted.
/// Empty blacklist returns false (open access).
pub fn is_blacklisted_for_reserve(env: Env, asset: Address, address: Address) -> bool {
    storage::is_address_blacklisted_for_reserve(&env, &asset, &address)
}

/// Set liquidation blacklist (admin only).
/// # Arguments
/// * `blacklist` - Addresses blocked from performing liquidations
///
/// # Behavior
/// * Empty blacklist: open access to liquidation
/// * Non-empty blacklist: blocks listed addresses from liquidation
///
/// # Errors
/// * `Unauthorized` - Caller is not admin
pub fn set_liquidation_blacklist(
    env: Env,
    blacklist: Vec<Address>,
) -> Result<(), KineticRouterError> {
    let admin = storage::get_pool_admin(&env)?;
    admin.require_auth();

    storage::set_liquidation_blacklist(&env, &blacklist);

    env.events()
        .publish((symbol_short!("liqblack"), 0), blacklist.len());

    Ok(())
}

/// Get liquidation blacklist.
/// Returns empty vector if no blacklist is configured (open access).
pub fn get_liquidation_blacklist(env: Env) -> Vec<Address> {
    storage::get_liquidation_blacklist(&env)
}

/// Check if address is blacklisted for liquidation.
/// Returns true if address is blacklisted.
/// Empty blacklist returns false (open access).
pub fn is_blacklisted_for_liquidation(env: Env, address: Address) -> bool {
    storage::is_address_blacklisted_for_liquidation(&env, &address)
}

// M-01

/// Set swap handler whitelist (admin only).
///
/// # Arguments
/// * `whitelist` - Addresses of approved swap handler contracts
///
/// # Behavior
/// * Empty whitelist: deny all custom handlers (only built-in DEX allowed)
/// * Non-empty whitelist: only listed handlers allowed
///
/// # Errors
/// * `Unauthorized` - Caller is not admin
pub fn set_swap_handler_whitelist(
    env: Env,
    whitelist: Vec<Address>,
) -> Result<(), KineticRouterError> {
    let admin = storage::get_pool_admin(&env)?;
    admin.require_auth();

    storage::set_swap_handler_whitelist(&env, &whitelist);

    env.events()
        .publish((symbol_short!("swpwlist"), 0u32), whitelist.len());

    Ok(())
}

/// Get swap handler whitelist.
/// Returns empty vector if no whitelist configured.
pub fn get_swap_handler_whitelist(env: Env) -> Vec<Address> {
    storage::get_swap_handler_whitelist(&env)
}

/// Check if a swap handler is whitelisted.
/// Empty whitelist = deny all custom handlers.
pub fn is_swap_handler_whitelisted(env: Env, handler: Address) -> bool {
    storage::is_swap_handler_whitelisted(&env, &handler)
}
