use crate::storage;
use k2_shared::*;
use soroban_sdk::{symbol_short, Address, Env, Symbol};

pub fn set_flash_loan_premium(env: Env, premium_bps: u128) -> Result<(), KineticRouterError> {
    let admin = storage::get_pool_admin(&env)?;
    admin.require_auth();

    // Validate that base + existing surcharge doesn't exceed the max
    let max_premium = storage::get_flash_loan_premium_max(&env);
    let liq_surcharge = storage::get_flash_liquidation_premium(&env);
    let combined = premium_bps.checked_add(liq_surcharge)
        .ok_or(KineticRouterError::MathOverflow)?;
    if combined > max_premium {
        return Err(KineticRouterError::InvalidAmount);
    }

    storage::set_flash_loan_premium(&env, premium_bps);

    env.events()
        .publish((symbol_short!("fl_prem"),), premium_bps);

    Ok(())
}

pub fn set_flash_loan_premium_max(env: Env, max_premium_bps: u128) -> Result<(), KineticRouterError> {
    let admin = storage::get_pool_admin(&env)?;
    admin.require_auth();

    // N-10
    if max_premium_bps > 10000 {
        return Err(KineticRouterError::InvalidAmount);
    }

    storage::set_flash_loan_premium_max(&env, max_premium_bps);

    env.events().publish(
        (symbol_short!("fl_prem"), symbol_short!("max")),
        max_premium_bps,
    );

    Ok(())
}

pub fn get_flash_loan_premium_max(env: Env) -> u128 {
    storage::get_flash_loan_premium_max(&env)
}

pub fn set_hf_liquidation_threshold(env: Env, threshold: u128) -> Result<(), KineticRouterError> {
    let admin = storage::get_pool_admin(&env)?;
    admin.require_auth();

    // N-10
    // HF threshold determines when positions become liquidatable
    let min_threshold = 500_000_000_000_000_000u128; // 0.5 WAD
    let max_threshold = 1_200_000_000_000_000_000u128; // M-09: 1.2 WAD
    if threshold < min_threshold || threshold > max_threshold {
        return Err(KineticRouterError::InvalidAmount);
    }

    storage::set_health_factor_liquidation_threshold(&env, threshold);

    env.events().publish(
        (
            symbol_short!("hf"),
            symbol_short!("liq"),
            symbol_short!("th"),
        ),
        threshold,
    );

    Ok(())
}

pub fn get_hf_liquidation_threshold(env: Env) -> u128 {
    storage::get_health_factor_liquidation_threshold(&env)
}

pub fn set_min_swap_output_bps(env: Env, min_output_bps: u128) -> Result<(), KineticRouterError> {
    let admin = storage::get_pool_admin(&env)?;
    admin.require_auth();

    // M-05: Enforce slippage floor to prevent sandwich attacks
    if min_output_bps < MIN_SWAP_OUTPUT_FLOOR_BPS || min_output_bps > BASIS_POINTS_MULTIPLIER {
        return Err(KineticRouterError::InvalidAmount);
    }

    storage::set_min_swap_output_bps(&env, min_output_bps);

    env.events().publish(
        (
            symbol_short!("min"),
            symbol_short!("swap"),
            symbol_short!("bps"),
        ),
        min_output_bps,
    );

    Ok(())
}

pub fn get_min_swap_output_bps(env: Env) -> u128 {
    storage::get_min_swap_output_bps(&env)
}

pub fn set_partial_liq_hf_threshold(env: Env, threshold: u128) -> Result<(), KineticRouterError> {
    let admin = storage::get_pool_admin(&env)?;
    admin.require_auth();

    // N-10
    // Partial liquidation threshold must be below the main liquidation threshold (1.0 WAD)
    if threshold == 0 || threshold >= k2_shared::WAD {
        return Err(KineticRouterError::InvalidAmount);
    }

    storage::set_partial_liquidation_hf_threshold(&env, threshold);

    env.events().publish(
        (
            symbol_short!("part"),
            symbol_short!("liq"),
            symbol_short!("hf"),
        ),
        threshold,
    );

    Ok(())
}

pub fn get_partial_liq_hf_threshold(env: Env) -> u128 {
    storage::get_partial_liquidation_hf_threshold(&env)
}

pub fn set_price_staleness_threshold(env: Env, threshold_seconds: u64) -> Result<(), KineticRouterError> {
    let admin = storage::get_pool_admin(&env)?;
    admin.require_auth();

    // M-07
    if threshold_seconds < MIN_PRICE_STALENESS_THRESHOLD
        || threshold_seconds > MAX_PRICE_STALENESS_THRESHOLD
    {
        return Err(KineticRouterError::InvalidAmount);
    }

    storage::set_price_staleness_threshold(&env, threshold_seconds);

    env.events().publish(
        (
            symbol_short!("price"),
            symbol_short!("stale"),
            symbol_short!("th"),
        ),
        threshold_seconds,
    );

    Ok(())
}

pub fn get_price_staleness_threshold(env: Env) -> u64 {
    storage::get_price_staleness_threshold(&env)
}

/// M-07
/// Different assets may have different oracle heartbeats (e.g., BTC every 60s, stablecoins every 24h).
/// Pass threshold_seconds = 0 to remove the override and fall back to global.
pub fn set_asset_staleness_threshold(env: Env, asset: Address, threshold_seconds: u64) -> Result<(), KineticRouterError> {
    let admin = storage::get_pool_admin(&env)?;
    admin.require_auth();

    // Validate bounds (0 means remove override)
    if threshold_seconds != 0
        && (threshold_seconds < MIN_PRICE_STALENESS_THRESHOLD
            || threshold_seconds > MAX_PRICE_STALENESS_THRESHOLD)
    {
        return Err(KineticRouterError::InvalidAmount);
    }

    storage::set_asset_staleness_threshold(&env, &asset, threshold_seconds);

    env.events().publish(
        (symbol_short!("asset"), symbol_short!("stale"), symbol_short!("th")),
        (asset, threshold_seconds),
    );

    Ok(())
}

/// M-07
pub fn get_asset_staleness_threshold(env: Env, asset: Address) -> Option<u64> {
    storage::get_asset_staleness_threshold(&env, &asset)
}

/// M-03 / N-02
pub fn set_liquidation_price_tolerance(env: Env, tolerance_bps: u128) -> Result<(), KineticRouterError> {
    let admin = storage::get_pool_admin(&env)?;
    admin.require_auth();

    // N-02
    // Cap at 5000 bps (50%) as a reasonable maximum tolerance
    if tolerance_bps > 5000 {
        return Err(KineticRouterError::InvalidAmount);
    }

    storage::set_liquidation_price_tolerance_bps(&env, tolerance_bps);

    env.events().publish(
        (symbol_short!("liq"), symbol_short!("tol_bps")),
        tolerance_bps,
    );

    Ok(())
}

pub fn get_flash_loan_premium(env: Env) -> u128 {
    storage::get_flash_loan_premium(&env)
}

pub fn set_flash_liquidation_premium(env: Env, premium_bps: u128) -> Result<(), KineticRouterError> {
    let admin = storage::get_pool_admin(&env)?;
    admin.require_auth();

    // Validate that existing base + new surcharge doesn't exceed the max
    let max_premium = storage::get_flash_loan_premium_max(&env);
    let base_premium = storage::get_flash_loan_premium(&env);
    let combined = base_premium.checked_add(premium_bps)
        .ok_or(KineticRouterError::MathOverflow)?;
    if combined > max_premium {
        return Err(KineticRouterError::InvalidAmount);
    }

    storage::set_flash_liquidation_premium(&env, premium_bps);

    env.events()
        .publish((symbol_short!("fl_liq"), symbol_short!("prem")), premium_bps);

    Ok(())
}

pub fn get_flash_liquidation_premium(env: Env) -> u128 {
    storage::get_flash_liquidation_premium(&env)
}

pub fn set_treasury(env: Env, treasury: Address) -> Result<(), KineticRouterError> {
    let admin = storage::get_pool_admin(&env)?;
    admin.require_auth();

    storage::set_treasury(&env, &treasury);

    const EVENT_SET: Symbol = symbol_short!("set");
    env.events()
        .publish((symbol_short!("treasury"), EVENT_SET), treasury);

    Ok(())
}

pub fn get_treasury(env: Env) -> Option<Address> {
    storage::get_treasury(&env)
}

pub fn set_flash_liquidation_helper(env: Env, helper: Address) -> Result<(), KineticRouterError> {
    let admin = storage::get_pool_admin(&env)?;
    admin.require_auth();

    storage::set_flash_liquidation_helper(&env, &helper);

    const EVENT_SET: Symbol = symbol_short!("set");
    env.events()
        .publish((symbol_short!("fliqhelp"), EVENT_SET), helper);

    Ok(())
}

pub fn get_flash_liquidation_helper(env: Env) -> Option<Address> {
    storage::get_flash_liquidation_helper(&env)
}

pub fn set_pool_configurator(env: Env, configurator: Address) -> Result<(), KineticRouterError> {
    let admin = storage::get_pool_admin(&env)?;
    admin.require_auth();

    storage::set_pool_configurator(&env, &configurator);

    const EVENT_SET: Symbol = symbol_short!("set");
    env.events()
        .publish((symbol_short!("pconfig"), EVENT_SET), configurator);

    Ok(())
}

pub fn get_pool_configurator(env: Env) -> Option<Address> {
    storage::get_pool_configurator(&env)
}

pub fn get_incentives_contract(env: Env) -> Option<Address> {
    storage::get_incentives_contract(&env)
}

pub fn set_incentives_contract(env: Env, incentives: Address) -> Result<u32, KineticRouterError> {
    let admin = storage::get_pool_admin(&env)?;
    admin.require_auth();
    
    storage::set_incentives_contract(&env, &incentives);
    
    let mut updated_count = 0u32;
    let reserves_list = storage::get_reserves_list(&env);

    for i in 0..reserves_list.len().min(MAX_RESERVES) {
        if let Some(asset) = reserves_list.get(i) {
            let reserve_data = storage::get_reserve_data(&env, &asset)?;
            crate::reserve::propagate_incentives_to_tokens(
                &env, &reserve_data.a_token_address, &reserve_data.debt_token_address, &incentives,
            )?;
            updated_count += 1;
        }
    }
    
    env.events().publish(
        (symbol_short!("incentive"), symbol_short!("updated")),
        updated_count,
    );
    
    Ok(updated_count)
}
