use k2_shared::{KineticRouterError, LiquidationCallbackParams, ReserveData, UserConfiguration, MAX_RESERVES};
use soroban_sdk::{contracttype, panic_with_error, symbol_short, Address, Env, Map, Symbol, Vec};

// TTL constants: 1 year = 365 days * 17280 ledgers/day ≈ 6,307,200 ledgers
// Extend TTL when remaining time falls below 30 days
pub const TTL_THRESHOLD: u32 = 30 * 17280; // 30 days in ledgers
pub const TTL_EXTENSION: u32 = 365 * 17280; // 1 year in ledgers

pub const MAX_USER_RESERVES: u8 = 15;

const INITIALIZED: Symbol = symbol_short!("INIT");
const POOL_ADMIN: Symbol = symbol_short!("PADMIN");
const PENDING_POOL_ADMIN: Symbol = symbol_short!("PPADMIN");
const EMERGENCY_ADMIN: Symbol = symbol_short!("EADMIN");
const PENDING_EMERGENCY_ADMIN: Symbol = symbol_short!("PEADMIN");
const PRICE_ORACLE: Symbol = symbol_short!("ORACLE");
const TREASURY: Symbol = symbol_short!("TREASURY");
const PAUSED: Symbol = symbol_short!("PAUSED");
const FLASH_LOAN_PREMIUM: Symbol = symbol_short!("FLPREM");
const FLASH_LOAN_PREMIUM_MAX: Symbol = symbol_short!("FLPREMMAX");
const FLASH_LIQ_PREMIUM: Symbol = symbol_short!("FLLIQPR");
const HEALTH_FACTOR_LIQ_THRESHOLD: Symbol = symbol_short!("HFLIQTH");
const MIN_SWAP_OUTPUT_BPS: Symbol = symbol_short!("MINSWAP");
const PARTIAL_LIQ_HF_THRESHOLD: Symbol = symbol_short!("PLIQHF");
const FLASH_LOAN_ACTIVE: Symbol = symbol_short!("FLACTIVE");
const PROTOCOL_LOCKED: Symbol = symbol_short!("REENTRY");
const DEX_ROUTER: Symbol = symbol_short!("DEXROUTE");
const DEX_FACTORY: Symbol = symbol_short!("DEXFACT");
const INCENTIVES: Symbol = symbol_short!("INCENT");
const FLASH_LIQ_HELPER: Symbol = symbol_short!("FLIQHELP");
const POOL_CONFIGURATOR: Symbol = symbol_short!("PCONFIG");
const LIQ_PRICE_TOL_BPS: Symbol = symbol_short!("LPTOLBPS");
/// F-02
const ORACLE_CFG: Symbol = symbol_short!("ORACFG");

const RESERVES_LIST: Symbol = symbol_short!("RLIST");
const RESERVES_COUNT: Symbol = symbol_short!("RCOUNT");
const NEXT_RESERVE_ID: Symbol = symbol_short!("NEXTRID");
const WHITELIST: Symbol = symbol_short!("WLIST");
const RESERVE_ID_TO_ADDRESS: Symbol = symbol_short!("RID2ADDR");

// Storage keys for reserve, user, and list data
const RESERVE_DATA: Symbol = symbol_short!("RDATA");
const RESERVE_DEBT_CEILING: Symbol = symbol_short!("RDEBTCEIL");
const RESERVE_DEFICIT: Symbol = symbol_short!("RDEFICIT");
const USER_CONFIGURATION: Symbol = symbol_short!("UCONFIG");

// Whitelist/blacklist flag keys
const LIQ_WHITELIST_FLAG: Symbol = symbol_short!("LWLF");
const LIQ_BLACKLIST_FLAG: Symbol = symbol_short!("LBLF");
const SWAP_WHITELIST_FLAG: Symbol = symbol_short!("SWLF");
// M-01: Consolidated per-reserve flags into single Maps to reduce instance storage bloat.
// Previous approach used (Symbol, Address) tuples — up to 128 instance entries at max reserves.
// New approach: 2 Map<Address, bool> entries in instance storage.
const RESERVE_WL_MAP: Symbol = symbol_short!("RWLMAP");
const RESERVE_BL_MAP: Symbol = symbol_short!("RBLMAP");

// Blacklist storage keys
const LIQUIDATION_BLACKLIST: Symbol = symbol_short!("LIQBLACK");
const RESERVE_BLACKLIST: Symbol = symbol_short!("RBLACK");

// Authorization keys
const LIQUIDATION_AUTH: Symbol = symbol_short!("LIQAUTH");

// WP-M2: Track liquidation amount in current ledger to enforce close factor
const USER_LIQUIDATION_TRACKER: Symbol = symbol_short!("ULIQTRK");
const USER_LIQ_TIME: Symbol = symbol_short!("ULIQTIME");
const LIQ_TRACKER_EXPIRY: Symbol = symbol_short!("LTEXPIRY");

/// F-04
pub fn extend_instance_ttl(env: &Env) {
    env.storage().instance().extend_ttl(TTL_THRESHOLD, TTL_EXTENSION);
}

pub fn is_initialized(env: &Env) -> bool {
    env.storage().instance().has(&INITIALIZED)
}

pub fn set_initialized(env: &Env) {
    env.storage().instance().set(&INITIALIZED, &true);
    env.storage().instance().extend_ttl(TTL_THRESHOLD, TTL_EXTENSION);
}

pub fn get_pool_admin(env: &Env) -> Result<Address, KineticRouterError> {
    env.storage()
        .instance()
        .get(&POOL_ADMIN)
        .ok_or(KineticRouterError::NotInitialized)
}

pub fn set_pool_admin(env: &Env, admin: &Address) {
    env.storage().instance().set(&POOL_ADMIN, admin);
    env.storage().instance().extend_ttl(TTL_THRESHOLD, TTL_EXTENSION);
}

pub fn get_pending_pool_admin(env: &Env) -> Result<Address, KineticRouterError> {
    env.storage()
        .instance()
        .get(&PENDING_POOL_ADMIN)
        .ok_or(KineticRouterError::NoPendingAdmin)
}

pub fn set_pending_pool_admin(env: &Env, pending_admin: &Address) {
    env.storage().instance().set(&PENDING_POOL_ADMIN, pending_admin);
    env.storage().instance().extend_ttl(TTL_THRESHOLD, TTL_EXTENSION);
}

pub fn clear_pending_pool_admin(env: &Env) {
    if env.storage().instance().has(&PENDING_POOL_ADMIN) {
        env.storage().instance().remove(&PENDING_POOL_ADMIN);
    }
}

pub fn get_emergency_admin(env: &Env) -> Option<Address> {
    env.storage().instance().get(&EMERGENCY_ADMIN)
}

pub fn set_emergency_admin(env: &Env, admin: &Address) {
    env.storage().instance().set(&EMERGENCY_ADMIN, admin);
    env.storage().instance().extend_ttl(TTL_THRESHOLD, TTL_EXTENSION);
}

pub fn get_pending_emergency_admin(env: &Env) -> Result<Address, KineticRouterError> {
    env.storage()
        .instance()
        .get(&PENDING_EMERGENCY_ADMIN)
        .ok_or(KineticRouterError::NoPendingAdmin)
}

pub fn set_pending_emergency_admin(env: &Env, pending_admin: &Address) {
    env.storage().instance().set(&PENDING_EMERGENCY_ADMIN, pending_admin);
    env.storage().instance().extend_ttl(TTL_THRESHOLD, TTL_EXTENSION);
}

pub fn clear_pending_emergency_admin(env: &Env) {
    if env.storage().instance().has(&PENDING_EMERGENCY_ADMIN) {
        env.storage().instance().remove(&PENDING_EMERGENCY_ADMIN);
    }
}

pub fn get_price_oracle_opt(env: &Env) -> Option<Address> {
    env.storage().instance().get(&PRICE_ORACLE)
}

pub fn set_price_oracle(env: &Env, oracle: &Address) {
    env.storage().instance().set(&PRICE_ORACLE, oracle);
    // F-02
    if env.storage().instance().has(&ORACLE_CFG) {
        env.storage().instance().remove(&ORACLE_CFG);
    }
    env.storage().instance().extend_ttl(TTL_THRESHOLD, TTL_EXTENSION);
}

/// F-02
pub fn get_cached_oracle_config(env: &Env) -> Option<k2_shared::OracleConfig> {
    env.storage().instance().get(&ORACLE_CFG)
}

/// F-02
pub fn set_cached_oracle_config(env: &Env, config: &k2_shared::OracleConfig) {
    env.storage().instance().set(&ORACLE_CFG, config);
}

/// F-02
/// Use if oracle precision changes without changing the oracle address.
pub fn flush_oracle_config_cache(env: &Env) {
    if env.storage().instance().has(&ORACLE_CFG) {
        env.storage().instance().remove(&ORACLE_CFG);
    }
}

/// AC-01
/// Must be called by admin after contract upgrade to ensure pre-existing
/// whitelists/blacklists are not silently bypassed.
pub fn sync_access_control_flags(env: &Env) {
    // Sync global lists
    let liq_wl = get_liquidation_whitelist(env);
    env.storage().instance().set(&LIQ_WHITELIST_FLAG, &!liq_wl.is_empty());

    let liq_bl = get_liquidation_blacklist(env);
    env.storage().instance().set(&LIQ_BLACKLIST_FLAG, &!liq_bl.is_empty());

    let swap_wl = get_swap_handler_whitelist(env);
    env.storage().instance().set(&SWAP_WHITELIST_FLAG, &!swap_wl.is_empty());

    // M-01: Sync per-reserve lists into consolidated Maps (2 instance entries, not 2*N)
    let reserves = get_reserves_list(env);
    let mut wl_map: Map<Address, bool> = Map::new(env);
    let mut bl_map: Map<Address, bool> = Map::new(env);
    for i in 0..reserves.len() {
        if let Some(asset) = reserves.get(i) {
            let rwl = get_reserve_whitelist(env, &asset);
            wl_map.set(asset.clone(), !rwl.is_empty());

            let rbl = get_reserve_blacklist(env, &asset);
            bl_map.set(asset.clone(), !rbl.is_empty());
        }
    }
    env.storage().instance().set(&RESERVE_WL_MAP, &wl_map);
    env.storage().instance().set(&RESERVE_BL_MAP, &bl_map);
}

pub fn get_treasury(env: &Env) -> Option<Address> {
    env.storage().instance().get(&TREASURY)
}

pub fn set_treasury(env: &Env, treasury: &Address) {
    env.storage().instance().set(&TREASURY, treasury);
    env.storage().instance().extend_ttl(TTL_THRESHOLD, TTL_EXTENSION);
}

pub fn get_reserve_data(env: &Env, asset: &Address) -> Result<ReserveData, KineticRouterError> {
    let key = (RESERVE_DATA, asset.clone());
    if env.storage().persistent().has(&key) {
        env.storage()
            .persistent()
            .extend_ttl(&key, TTL_THRESHOLD, TTL_EXTENSION);
    }
    env.storage()
        .persistent()
        .get(&key)
        .ok_or(KineticRouterError::ReserveNotFound)
}

pub fn set_reserve_data(env: &Env, asset: &Address, data: &ReserveData) {
    let key = (RESERVE_DATA, asset.clone());
    env.storage().persistent().set(&key, data);
    env.storage()
        .persistent()
        .extend_ttl(&key, TTL_THRESHOLD, TTL_EXTENSION);
}

pub fn get_reserve_debt_ceiling(env: &Env, asset: &Address) -> u128 {
    let key = (RESERVE_DEBT_CEILING, asset.clone());
    if env.storage().persistent().has(&key) {
        env.storage()
            .persistent()
            .extend_ttl(&key, TTL_THRESHOLD, TTL_EXTENSION);
    }
    env.storage().persistent().get(&key).unwrap_or(0)
}

pub fn set_reserve_debt_ceiling(env: &Env, asset: &Address, debt_ceiling: u128) {
    let key = (RESERVE_DEBT_CEILING, asset.clone());
    env.storage().persistent().set(&key, &debt_ceiling);
    env.storage()
        .persistent()
        .extend_ttl(&key, TTL_THRESHOLD, TTL_EXTENSION);
}

pub fn get_reserve_deficit(env: &Env, asset: &Address) -> u128 {
    let key = (RESERVE_DEFICIT, asset.clone());
    if env.storage().persistent().has(&key) {
        env.storage()
            .persistent()
            .extend_ttl(&key, TTL_THRESHOLD, TTL_EXTENSION);
    }
    env.storage().persistent().get(&key).unwrap_or(0)
}

pub fn add_reserve_deficit(env: &Env, asset: &Address, amount: u128) {
    let current = get_reserve_deficit(env, asset);
    let new_deficit = current.checked_add(amount).unwrap_or_else(|| {
        panic_with_error!(env, KineticRouterError::MathOverflow);
    });
    let key = (RESERVE_DEFICIT, asset.clone());
    env.storage().persistent().set(&key, &new_deficit);
    env.storage()
        .persistent()
        .extend_ttl(&key, TTL_THRESHOLD, TTL_EXTENSION);
}

pub fn reduce_reserve_deficit(env: &Env, asset: &Address, amount: u128) {
    let current = get_reserve_deficit(env, asset);
    let new_deficit = current.saturating_sub(amount);
    let key = (RESERVE_DEFICIT, asset.clone());
    if new_deficit == 0 {
        if env.storage().persistent().has(&key) {
            env.storage().persistent().remove(&key);
        }
    } else {
        env.storage().persistent().set(&key, &new_deficit);
        env.storage()
            .persistent()
            .extend_ttl(&key, TTL_THRESHOLD, TTL_EXTENSION);
    }
}

pub fn get_user_configuration(env: &Env, user: &Address) -> UserConfiguration {
    let key = (USER_CONFIGURATION, user.clone());
    if env.storage().persistent().has(&key) {
        env.storage()
            .persistent()
            .extend_ttl(&key, TTL_THRESHOLD, TTL_EXTENSION);
    }
    env.storage()
        .persistent()
        .get(&key)
        .unwrap_or(UserConfiguration { data: 0 })
}

pub fn set_user_configuration(env: &Env, user: &Address, config: &UserConfiguration) {
    let key = (USER_CONFIGURATION, user.clone());
    env.storage().persistent().set(&key, config);
    env.storage()
        .persistent()
        .extend_ttl(&key, TTL_THRESHOLD, TTL_EXTENSION);
}

pub fn get_reserves_list(env: &Env) -> Vec<Address> {
    if env.storage().persistent().has(&RESERVES_LIST) {
        env.storage()
            .persistent()
            .extend_ttl(&RESERVES_LIST, TTL_THRESHOLD, TTL_EXTENSION);
    }
    env.storage()
        .persistent()
        .get(&RESERVES_LIST)
        .unwrap_or(Vec::new(env))
}

pub fn add_reserve_to_list(env: &Env, asset: &Address) {
    let mut reserves = get_reserves_list(env);
    reserves.push_back(asset.clone());
    env.storage().persistent().set(&RESERVES_LIST, &reserves);
    env.storage()
        .persistent()
        .extend_ttl(&RESERVES_LIST, TTL_THRESHOLD, TTL_EXTENSION);
    // N-04: Maintain cached count to avoid deserializing full Vec for .len()
    env.storage().persistent().set(&RESERVES_COUNT, &reserves.len());
    env.storage()
        .persistent()
        .extend_ttl(&RESERVES_COUNT, TTL_THRESHOLD, TTL_EXTENSION);
}

/// N-04: Read cached reserves count (avoids deserializing full reserves Vec)
pub fn get_reserves_count(env: &Env) -> u32 {
    if env.storage().persistent().has(&RESERVES_COUNT) {
        env.storage()
            .persistent()
            .extend_ttl(&RESERVES_COUNT, TTL_THRESHOLD, TTL_EXTENSION);
        env.storage().persistent().get(&RESERVES_COUNT).unwrap_or(0)
    } else {
        // Fallback for existing deployments before RESERVES_COUNT was maintained
        get_reserves_list(env).len()
    }
}

pub fn get_next_reserve_id(env: &Env) -> u32 {
    if env.storage().persistent().has(&NEXT_RESERVE_ID) {
        env.storage()
            .persistent()
            .extend_ttl(&NEXT_RESERVE_ID, TTL_THRESHOLD, TTL_EXTENSION);
    }
    env.storage().persistent().get(&NEXT_RESERVE_ID).unwrap_or(0)
}

/// Increment and get next reserve ID
/// Bounded by MAX_RESERVES (64) - enforced in reserve creation
pub fn increment_and_get_reserve_id(env: &Env) -> u32 {
    let current = get_next_reserve_id(env);
    // I-04
    let next = current.checked_add(1).unwrap_or_else(|| {
        panic_with_error!(env, KineticRouterError::MathOverflow)
    });
    env.storage().persistent().set(&NEXT_RESERVE_ID, &next);
    env.storage()
        .persistent()
        .extend_ttl(&NEXT_RESERVE_ID, TTL_THRESHOLD, TTL_EXTENSION);
    current
}

/// Get reserve address by its ID (O(1) lookup for optimization)
pub fn get_reserve_address_by_id(env: &Env, id: u32) -> Option<Address> {
    let key = (RESERVE_ID_TO_ADDRESS, id);
    if env.storage().persistent().has(&key) {
        env.storage()
            .persistent()
            .extend_ttl(&key, TTL_THRESHOLD, TTL_EXTENSION);
    }
    env.storage().persistent().get(&key)
}

/// Set reserve address for a given ID (stored during init_reserve)
pub fn set_reserve_address_by_id(env: &Env, id: u32, asset: &Address) {
    let key = (RESERVE_ID_TO_ADDRESS, id);
    env.storage().persistent().set(&key, asset);
    env.storage()
        .persistent()
        .extend_ttl(&key, TTL_THRESHOLD, TTL_EXTENSION);
}

/// Remove reserve address mapping (used during drop_reserve)
pub fn remove_reserve_address_by_id(env: &Env, id: u32) {
    let key = (RESERVE_ID_TO_ADDRESS, id);
    if env.storage().persistent().has(&key) {
        env.storage().persistent().remove(&key);
    }
}


pub fn get_dex_router(env: &Env) -> Option<Address> {
    env.storage().instance().get(&DEX_ROUTER)
}

pub fn set_dex_router(env: &Env, router: &Address) {
    env.storage().instance().set(&DEX_ROUTER, router);
    env.storage().instance().extend_ttl(TTL_THRESHOLD, TTL_EXTENSION);
}

/// Get cached DEX factory address (for optimized direct pair swaps)
pub fn get_dex_factory(env: &Env) -> Option<Address> {
    env.storage().instance().get(&DEX_FACTORY)
}

/// Set DEX factory address (cached to avoid router lookup)
pub fn set_dex_factory(env: &Env, factory: &Address) {
    env.storage().instance().set(&DEX_FACTORY, factory);
    env.storage().instance().extend_ttl(TTL_THRESHOLD, TTL_EXTENSION);
}

/// Get incentives contract address
pub fn get_incentives_contract(env: &Env) -> Option<Address> {
    env.storage().instance().get(&INCENTIVES)
}

/// Set incentives contract address
pub fn set_incentives_contract(env: &Env, incentives: &Address) {
    env.storage().instance().set(&INCENTIVES, incentives);
    env.storage().instance().extend_ttl(TTL_THRESHOLD, TTL_EXTENSION);
}

pub fn get_flash_liquidation_helper(env: &Env) -> Option<Address> {
    env.storage().instance().get(&FLASH_LIQ_HELPER)
}

pub fn set_flash_liquidation_helper(env: &Env, helper: &Address) {
    env.storage().instance().set(&FLASH_LIQ_HELPER, helper);
    env.storage().instance().extend_ttl(TTL_THRESHOLD, TTL_EXTENSION);
}


pub fn is_paused(env: &Env) -> bool {
    env.storage().instance().get(&PAUSED).unwrap_or(false)
}

pub fn set_paused(env: &Env, paused: bool) {
    env.storage().instance().set(&PAUSED, &paused);
    env.storage().instance().extend_ttl(TTL_THRESHOLD, TTL_EXTENSION);
}

pub fn validate_admin(env: &Env, caller: &Address) -> Result<(), KineticRouterError> {
    let admin = get_pool_admin(env)?;
    if caller != &admin {
        return Err(KineticRouterError::Unauthorized);
    }
    Ok(())
}

pub fn validate_emergency_admin(env: &Env, caller: &Address) -> Result<(), KineticRouterError> {
    let pool_admin = get_pool_admin(env)?;

    if let Some(emergency_admin) = get_emergency_admin(env) {
        if caller != &emergency_admin && caller != &pool_admin {
            return Err(KineticRouterError::Unauthorized);
        }
    } else {
        if caller != &pool_admin {
            return Err(KineticRouterError::Unauthorized);
        }
    }

    Ok(())
}

pub fn get_pool_configurator(env: &Env) -> Option<Address> {
    env.storage().instance().get(&POOL_CONFIGURATOR)
}

pub fn set_pool_configurator(env: &Env, configurator: &Address) {
    env.storage().instance().set(&POOL_CONFIGURATOR, configurator);
    env.storage().instance().extend_ttl(TTL_THRESHOLD, TTL_EXTENSION);
}

pub fn validate_pool_configurator(env: &Env, caller: &Address) -> Result<(), KineticRouterError> {
    if let Some(pool_configurator) = get_pool_configurator(env) {
        if caller != &pool_configurator {
            return Err(KineticRouterError::Unauthorized);
        }
    } else {
        return Err(KineticRouterError::Unauthorized);
    }
    Ok(())
}

/// Default premium: 30 bps = 0.3%
pub fn get_flash_loan_premium(env: &Env) -> u128 {
    env.storage()
        .instance()
        .get(&FLASH_LOAN_PREMIUM)
        .unwrap_or(30)
}

pub fn set_flash_loan_premium(env: &Env, premium_bps: u128) {
    env.storage()
        .instance()
        .set(&FLASH_LOAN_PREMIUM, &premium_bps);
    env.storage().instance().extend_ttl(TTL_THRESHOLD, TTL_EXTENSION);
}

/// Get maximum flash loan premium allowed (in basis points).
/// This limit prevents accidentally setting excessive fees that could break integrations.
pub fn get_flash_loan_premium_max(env: &Env) -> u128 {
    env.storage()
        .instance()
        .get(&FLASH_LOAN_PREMIUM_MAX)
        .unwrap_or(100) // Default 1% max
}

pub fn set_flash_loan_premium_max(env: &Env, max_bps: u128) {
    env.storage()
        .instance()
        .set(&FLASH_LOAN_PREMIUM_MAX, &max_bps);
    env.storage().instance().extend_ttl(TTL_THRESHOLD, TTL_EXTENSION);
}

/// Flash liquidation premium (extra fee for using protocol-funded flash liquidation).
/// Defaults to 0 (no extra fee beyond the regular protocol fee).
pub fn get_flash_liquidation_premium(env: &Env) -> u128 {
    env.storage()
        .instance()
        .get(&FLASH_LIQ_PREMIUM)
        .unwrap_or(0)
}

pub fn set_flash_liquidation_premium(env: &Env, premium_bps: u128) {
    env.storage()
        .instance()
        .set(&FLASH_LIQ_PREMIUM, &premium_bps);
    env.storage().instance().extend_ttl(TTL_THRESHOLD, TTL_EXTENSION);
}

/// Get health factor threshold below which positions become liquidatable.
/// Health factor = (collateral_value * liquidation_threshold) / debt_value.
/// Positions with HF < threshold can be liquidated.
pub fn get_health_factor_liquidation_threshold(env: &Env) -> u128 {
    env.storage()
        .instance()
        .get(&HEALTH_FACTOR_LIQ_THRESHOLD)
        .unwrap_or(1_000_000_000_000_000_000) // Default 1.0 WAD
}

pub fn set_health_factor_liquidation_threshold(env: &Env, threshold: u128) {
    env.storage()
        .instance()
        .set(&HEALTH_FACTOR_LIQ_THRESHOLD, &threshold);
    env.storage().instance().extend_ttl(TTL_THRESHOLD, TTL_EXTENSION);
}

/// Get minimum swap output threshold for slippage protection during liquidations.
/// Applied as: min_output = (expected_output * threshold_bps) / 10000.
/// Prevents sandwich attacks by ensuring liquidators get fair swap prices.
pub fn get_min_swap_output_bps(env: &Env) -> u128 {
    env.storage()
        .instance()
        .get(&MIN_SWAP_OUTPUT_BPS)
        .unwrap_or(9800) // Default 98% of expected
}

pub fn set_min_swap_output_bps(env: &Env, bps: u128) {
    env.storage()
        .instance()
        .set(&MIN_SWAP_OUTPUT_BPS, &bps);
    env.storage().instance().extend_ttl(TTL_THRESHOLD, TTL_EXTENSION);
}


/// Get health factor threshold for allowing partial liquidations.
/// When HF >= threshold: only partial liquidation (up to close_factor) allowed.
/// When HF < threshold: full liquidation allowed to restore solvency faster.
pub fn get_partial_liquidation_hf_threshold(env: &Env) -> u128 {
    env.storage()
        .instance()
        .get(&PARTIAL_LIQ_HF_THRESHOLD)
        .unwrap_or(500_000_000_000_000_000) // Default 0.5 WAD
}

pub fn set_partial_liquidation_hf_threshold(env: &Env, threshold: u128) {
    env.storage()
        .instance()
        .set(&PARTIAL_LIQ_HF_THRESHOLD, &threshold);
    env.storage().instance().extend_ttl(TTL_THRESHOLD, TTL_EXTENSION);
}


const PRICE_STALENESS_THRESHOLD: Symbol = symbol_short!("PSTALE");

/// Get price staleness threshold in seconds (default: 1 hour = 3600 seconds)
pub fn get_price_staleness_threshold(env: &Env) -> u64 {
    env.storage()
        .instance()
        .get(&PRICE_STALENESS_THRESHOLD)
        .unwrap_or(3600) // Default: 1 hour
}

/// Set price staleness threshold in seconds
pub fn set_price_staleness_threshold(env: &Env, threshold_seconds: u64) {
    env.storage()
        .instance()
        .set(&PRICE_STALENESS_THRESHOLD, &threshold_seconds);
    env.storage().instance().extend_ttl(TTL_THRESHOLD, TTL_EXTENSION);
}

/// M-07
const ASSET_STALENESS_MAP: Symbol = symbol_short!("ASTALMP");

pub fn get_asset_staleness_threshold(env: &Env, asset: &Address) -> Option<u64> {
    let map: Map<Address, u64> = env.storage()
        .instance()
        .get(&ASSET_STALENESS_MAP)
        .unwrap_or_else(|| Map::new(env));
    map.get(asset.clone())
}

/// Set per-asset staleness threshold override.
/// Pass 0 to remove the override and fall back to the global threshold.
pub fn set_asset_staleness_threshold(env: &Env, asset: &Address, threshold_seconds: u64) {
    let mut map: Map<Address, u64> = env.storage()
        .instance()
        .get(&ASSET_STALENESS_MAP)
        .unwrap_or_else(|| Map::new(env));
    if threshold_seconds == 0 {
        map.remove(asset.clone());
    } else {
        map.set(asset.clone(), threshold_seconds);
    }
    env.storage().instance().set(&ASSET_STALENESS_MAP, &map);
}

/// M-03
pub fn get_liquidation_price_tolerance_bps(env: &Env) -> u128 {
    env.storage()
        .instance()
        .get(&LIQ_PRICE_TOL_BPS)
        .unwrap_or(300) // Default: 3% (300 bps)
}

pub fn set_liquidation_price_tolerance_bps(env: &Env, tolerance_bps: u128) {
    env.storage()
        .instance()
        .set(&LIQ_PRICE_TOL_BPS, &tolerance_bps);
    env.storage().instance().extend_ttl(TTL_THRESHOLD, TTL_EXTENSION);
}

/// Protocol-wide reentrancy guard — blocks all entry points when any operation is in flight.
pub fn is_protocol_locked(env: &Env) -> bool {
    env.storage()
        .instance()
        .get(&PROTOCOL_LOCKED)
        .unwrap_or(false)
}

pub fn set_protocol_locked(env: &Env, locked: bool) {
    env.storage().instance().set(&PROTOCOL_LOCKED, &locked);
}

pub fn is_flash_loan_active(env: &Env) -> bool {
    env.storage()
        .instance()
        .get(&FLASH_LOAN_ACTIVE)
        .unwrap_or(false)
}

pub fn set_flash_loan_active(env: &Env, active: bool) {
    env.storage().instance().set(&FLASH_LOAN_ACTIVE, &active);
}

pub fn remove_reserve_data(env: &Env, asset: &Address) {
    let key = (RESERVE_DATA, asset.clone());
    env.storage().persistent().remove(&key);
}

pub fn remove_reserve_from_list(env: &Env, asset: &Address) -> Result<(), KineticRouterError> {
    let reserves = get_reserves_list(env);

    let mut new_reserves = Vec::new(env);
    let len = reserves.len().min(MAX_RESERVES);
    for i in 0..len {
        let reserve = reserves.get(i).ok_or(KineticRouterError::ReserveNotFound)?;
        if reserve != *asset {
            new_reserves.push_back(reserve);
        }
    }

    env.storage()
        .persistent()
        .set(&RESERVES_LIST, &new_reserves);
    env.storage()
        .persistent()
        .extend_ttl(&RESERVES_LIST, TTL_THRESHOLD, TTL_EXTENSION);
    // N-04: Maintain cached count
    env.storage().persistent().set(&RESERVES_COUNT, &new_reserves.len());
    env.storage()
        .persistent()
        .extend_ttl(&RESERVES_COUNT, TTL_THRESHOLD, TTL_EXTENSION);
    Ok(())
}

const LIQUIDATION_CALLBACK: Symbol = symbol_short!("LIQCB");
const LIQUIDATION_WHITELIST: Symbol = symbol_short!("LIQWLIST");

pub fn get_liquidation_callback_params(env: &Env) -> Option<LiquidationCallbackParams> {
    env.storage().temporary().get(&LIQUIDATION_CALLBACK)
}

pub fn set_liquidation_callback_params(env: &Env, params: &LiquidationCallbackParams) {
    env.storage().temporary().set(&LIQUIDATION_CALLBACK, params);
}

pub fn remove_liquidation_callback_params(env: &Env) {
    if env.storage().temporary().has(&LIQUIDATION_CALLBACK) {
        env.storage().temporary().remove(&LIQUIDATION_CALLBACK);
    }
}

// Temporary storage for scaled supply values from liquidation callback.
const LIQ_SCALED_KEY: Symbol = symbol_short!("LIQSCL");

/// Stores callback results: (debt_total_scaled, collateral_total_scaled, user_remaining_collateral_scaled, user_remaining_debt_scaled)
pub fn set_liquidation_scaled_supplies(
    env: &Env, debt_total: i128, collateral_total: i128,
    user_remaining_collateral_scaled: i128, user_remaining_debt_scaled: i128,
) {
    env.storage().temporary().set(&LIQ_SCALED_KEY, &(debt_total, collateral_total, user_remaining_collateral_scaled, user_remaining_debt_scaled));
}

/// Returns (debt_total_scaled, collateral_total_scaled, user_remaining_collateral_scaled, user_remaining_debt_scaled) if set.
pub fn get_liquidation_scaled_supplies(env: &Env) -> Option<(i128, i128, i128, i128)> {
    env.storage().temporary().get(&LIQ_SCALED_KEY)
}

pub fn remove_liquidation_scaled_supplies(env: &Env) {
    if env.storage().temporary().has(&LIQ_SCALED_KEY) {
        env.storage().temporary().remove(&LIQ_SCALED_KEY);
    }
}

pub fn get_liquidation_tracker_expiry(env: &Env) -> u32 {
    env.storage()
        .instance()
        .get(&LIQ_TRACKER_EXPIRY)
        .unwrap_or(17280) // Default: 1 day in ledgers (assuming ~5s per ledger)
}

pub fn set_liquidation_tracker_expiry(env: &Env, expiry_ledgers: u32) {
    env.storage()
        .instance()
        .set(&LIQ_TRACKER_EXPIRY, &expiry_ledgers);
    env.storage().instance().extend_ttl(TTL_THRESHOLD, TTL_EXTENSION);
}

/// WP-M2: Get total amount liquidated for a user.
pub fn get_user_liquidation_amount(env: &Env, user: &Address) -> u128 {
    let key = (USER_LIQUIDATION_TRACKER, user.clone());
    let time_key = (USER_LIQ_TIME, user.clone());

    if env.storage().persistent().has(&key) {
        env.storage().persistent().extend_ttl(&key, TTL_THRESHOLD, TTL_EXTENSION);
    }
    if env.storage().persistent().has(&time_key) {
        env.storage().persistent().extend_ttl(&time_key, TTL_THRESHOLD, TTL_EXTENSION);
    }

    let last_updated: u32 = env.storage().persistent().get(&time_key).unwrap_or(0);
    let current_ledger = env.ledger().sequence();
    let expiry = get_liquidation_tracker_expiry(env);

    // If elapsed ledgers exceed the threshold, consider the tracker reset
    if current_ledger.saturating_sub(last_updated) > expiry {
        return 0;
    }

    env.storage().persistent().get(&key).unwrap_or(0)
}

/// WP-M2: Update total amount liquidated for a user.
pub fn add_user_liquidation_amount(env: &Env, user: &Address, amount: u128) {
    let current = get_user_liquidation_amount(env, user);
    let new_amount = current.checked_add(amount).unwrap_or_else(|| {
        panic_with_error!(env, KineticRouterError::MathOverflow);
    });
    let key = (USER_LIQUIDATION_TRACKER, user.clone());
    env.storage().persistent().set(&key, &new_amount);
    env.storage().persistent().extend_ttl(&key, TTL_THRESHOLD, TTL_EXTENSION);

    let time_key = (USER_LIQ_TIME, user.clone());
    env.storage().persistent().set(&time_key, &env.ledger().sequence());
    env.storage().persistent().extend_ttl(&time_key, TTL_THRESHOLD, TTL_EXTENSION);
}

/// WP-M2: Clear liquidation tracker for a user (e.g. when healthy again).
pub fn clear_user_liquidation_amount(env: &Env, user: &Address) {
    let key = (USER_LIQUIDATION_TRACKER, user.clone());
    if env.storage().persistent().has(&key) {
        env.storage().persistent().remove(&key);
    }

    let time_key = (USER_LIQ_TIME, user.clone());
    if env.storage().persistent().has(&time_key) {
        env.storage().persistent().remove(&time_key);
    }
}

/// Get liquidation whitelist.
/// Returns empty vector if no whitelist is configured.
pub fn get_liquidation_whitelist(env: &Env) -> Vec<Address> {
    if env.storage().persistent().has(&LIQUIDATION_WHITELIST) {
        env.storage()
            .persistent()
            .extend_ttl(&LIQUIDATION_WHITELIST, TTL_THRESHOLD, TTL_EXTENSION);
    }
    env.storage()
        .persistent()
        .get(&LIQUIDATION_WHITELIST)
        .unwrap_or(Vec::new(env))
}

/// Set liquidation whitelist.
/// F-08
pub fn set_liquidation_whitelist(env: &Env, whitelist: &Vec<Address>) {
    env.storage().persistent().set(&LIQUIDATION_WHITELIST, whitelist);
    env.storage()
        .persistent()
        .extend_ttl(&LIQUIDATION_WHITELIST, TTL_THRESHOLD, TTL_EXTENSION);
    env.storage().instance().set(&LIQ_WHITELIST_FLAG, &!whitelist.is_empty());
}

/// Check if address is whitelisted for liquidation.
/// Empty whitelist returns true (open access).
/// F-08
pub fn is_address_whitelisted_for_liquidation(env: &Env, address: &Address) -> bool {
    let has_whitelist: bool = env.storage().instance().get(&LIQ_WHITELIST_FLAG).unwrap_or(false);
    if !has_whitelist {
        return true;
    }

    let whitelist = get_liquidation_whitelist(env);

    if whitelist.is_empty() {
        return true;
    }

    let len = whitelist.len().min(MAX_RESERVES);
    for i in 0..len {
        if let Some(whitelisted_addr) = whitelist.get(i) {
            if whitelisted_addr == *address {
                return true;
            }
        }
    }

    false
}


/// Get whitelist for a reserve
///
/// Returns empty vector if no whitelist is configured
pub fn get_reserve_whitelist(env: &Env, asset: &Address) -> Vec<Address> {
    let key = (WHITELIST, asset.clone());
    if env.storage().persistent().has(&key) {
        env.storage()
            .persistent()
            .extend_ttl(&key, TTL_THRESHOLD, TTL_EXTENSION);
    }
    env.storage()
        .persistent()
        .get(&key)
        .unwrap_or(Vec::new(env))
}

/// Set whitelist for a reserve
/// F-08
pub fn set_reserve_whitelist(env: &Env, asset: &Address, whitelist: &Vec<Address>) {
    let key = (WHITELIST, asset.clone());
    env.storage().persistent().set(&key, whitelist);
    env.storage()
        .persistent()
        .extend_ttl(&key, TTL_THRESHOLD, TTL_EXTENSION);
    // M-01: Update consolidated whitelist Map
    let mut wl_map: Map<Address, bool> = env.storage().instance().get(&RESERVE_WL_MAP).unwrap_or(Map::new(env));
    wl_map.set(asset.clone(), !whitelist.is_empty());
    env.storage().instance().set(&RESERVE_WL_MAP, &wl_map);
}

/// Check if address is whitelisted for a reserve
///
/// Empty whitelist returns true (open access)
/// F-08
pub fn is_address_whitelisted_for_reserve(env: &Env, asset: &Address, address: &Address) -> bool {
    // M-01: Read from consolidated whitelist Map
    let wl_map: Map<Address, bool> = env.storage().instance().get(&RESERVE_WL_MAP).unwrap_or(Map::new(env));
    let has_whitelist = wl_map.get(asset.clone()).unwrap_or(false);
    if !has_whitelist {
        return true;
    }

    let whitelist = get_reserve_whitelist(env, asset);

    if whitelist.is_empty() {
        return true;
    }

    let len = whitelist.len().min(MAX_RESERVES);
    for i in 0..len {
        if let Some(whitelisted_addr) = whitelist.get(i) {
            if whitelisted_addr == *address {
                return true;
            }
        }
    }

    false
}


/// Get blacklist for a reserve.
/// Returns empty vector if no blacklist is configured.
pub fn get_reserve_blacklist(env: &Env, asset: &Address) -> Vec<Address> {
    let key = (RESERVE_BLACKLIST, asset.clone());
    if env.storage().persistent().has(&key) {
        env.storage()
            .persistent()
            .extend_ttl(&key, TTL_THRESHOLD, TTL_EXTENSION);
    }
    env.storage()
        .persistent()
        .get(&key)
        .unwrap_or(Vec::new(env))
}

/// Set blacklist for a reserve.
/// F-08
pub fn set_reserve_blacklist(env: &Env, asset: &Address, blacklist: &Vec<Address>) {
    let key = (RESERVE_BLACKLIST, asset.clone());
    env.storage().persistent().set(&key, blacklist);
    env.storage()
        .persistent()
        .extend_ttl(&key, TTL_THRESHOLD, TTL_EXTENSION);
    // M-01: Update consolidated blacklist Map
    let mut bl_map: Map<Address, bool> = env.storage().instance().get(&RESERVE_BL_MAP).unwrap_or(Map::new(env));
    bl_map.set(asset.clone(), !blacklist.is_empty());
    env.storage().instance().set(&RESERVE_BL_MAP, &bl_map);
}

/// Check if address is blacklisted for a reserve.
/// Empty blacklist returns false (open access).
/// Non-empty blacklist blocks listed addresses.
/// F-08
pub fn is_address_blacklisted_for_reserve(env: &Env, asset: &Address, address: &Address) -> bool {
    // M-01: Read from consolidated blacklist Map
    let bl_map: Map<Address, bool> = env.storage().instance().get(&RESERVE_BL_MAP).unwrap_or(Map::new(env));
    let has_blacklist = bl_map.get(asset.clone()).unwrap_or(false);
    if !has_blacklist {
        return false;
    }

    let blacklist = get_reserve_blacklist(env, asset);

    if blacklist.is_empty() {
        return false;
    }

    let len = blacklist.len().min(MAX_RESERVES);
    for i in 0..len {
        if let Some(blacklisted_addr) = blacklist.get(i) {
            if blacklisted_addr == *address {
                return true;
            }
        }
    }

    false
}


/// Get liquidation blacklist.
/// Returns empty vector if no blacklist is configured.
pub fn get_liquidation_blacklist(env: &Env) -> Vec<Address> {
    let key = LIQUIDATION_BLACKLIST;
    if env.storage().persistent().has(&key) {
        env.storage()
            .persistent()
            .extend_ttl(&key, TTL_THRESHOLD, TTL_EXTENSION);
    }
    env.storage()
        .persistent()
        .get(&key)
        .unwrap_or(Vec::new(env))
}

/// Set liquidation blacklist.
/// F-08
pub fn set_liquidation_blacklist(env: &Env, blacklist: &Vec<Address>) {
    let key = LIQUIDATION_BLACKLIST;
    env.storage().persistent().set(&key, blacklist);
    env.storage()
        .persistent()
        .extend_ttl(&key, TTL_THRESHOLD, TTL_EXTENSION);
    env.storage().instance().set(&LIQ_BLACKLIST_FLAG, &!blacklist.is_empty());
}

/// Check if address is blacklisted for liquidation.
/// Empty blacklist returns false (open access).
/// Non-empty blacklist blocks listed addresses.
/// F-08
pub fn is_address_blacklisted_for_liquidation(env: &Env, address: &Address) -> bool {
    let has_blacklist: bool = env.storage().instance().get(&LIQ_BLACKLIST_FLAG).unwrap_or(false);
    if !has_blacklist {
        return false;
    }

    let blacklist = get_liquidation_blacklist(env);

    if blacklist.is_empty() {
        return false;
    }

    let len = blacklist.len().min(MAX_RESERVES);
    for i in 0..len {
        if let Some(blacklisted_addr) = blacklist.get(i) {
            if blacklisted_addr == *address {
                return true;
            }
        }
    }

    false
}

// M-01
const SWAP_HANDLER_WHITELIST: Symbol = symbol_short!("SWPWLIST");

/// Get the swap handler whitelist.
/// Returns empty vector if no whitelist configured (all handlers allowed for backward compat).
pub fn get_swap_handler_whitelist(env: &Env) -> Vec<Address> {
    if env.storage().persistent().has(&SWAP_HANDLER_WHITELIST) {
        env.storage()
            .persistent()
            .extend_ttl(&SWAP_HANDLER_WHITELIST, TTL_THRESHOLD, TTL_EXTENSION);
    }
    env.storage()
        .persistent()
        .get(&SWAP_HANDLER_WHITELIST)
        .unwrap_or(Vec::new(env))
}

/// Set the swap handler whitelist.
/// F-08
pub fn set_swap_handler_whitelist(env: &Env, whitelist: &Vec<Address>) {
    env.storage().persistent().set(&SWAP_HANDLER_WHITELIST, whitelist);
    env.storage()
        .persistent()
        .extend_ttl(&SWAP_HANDLER_WHITELIST, TTL_THRESHOLD, TTL_EXTENSION);
    env.storage().instance().set(&SWAP_WHITELIST_FLAG, &!whitelist.is_empty());
}

/// Check if a swap handler is whitelisted.
/// Empty whitelist = deny all custom handlers (only built-in DEX allowed).
/// Non-empty whitelist = only listed handlers allowed.
/// F-08
pub fn is_swap_handler_whitelisted(env: &Env, handler: &Address) -> bool {
    let has_whitelist: bool = env.storage().instance().get(&SWAP_WHITELIST_FLAG).unwrap_or(false);
    if !has_whitelist {
        return false; // No whitelist configured = deny custom handlers
    }

    let whitelist = get_swap_handler_whitelist(env);

    if whitelist.is_empty() {
        return false; // No whitelist configured = deny custom handlers
    }

    let len = whitelist.len().min(MAX_RESERVES);
    for i in 0..len {
        if let Some(whitelisted_addr) = whitelist.get(i) {
            if whitelisted_addr == *handler {
                return true;
            }
        }
    }

    false
}

#[derive(Clone)]
pub struct SwapConfig {
    pub dex_router: Option<Address>,
    pub dex_factory: Option<Address>,
    pub flash_loan_premium_bps: u128,
    pub treasury: Option<Address>,
}

/// Get swap-related config.
pub fn get_swap_config(env: &Env) -> SwapConfig {
    SwapConfig {
        dex_router: env.storage().instance().get(&DEX_ROUTER),
        dex_factory: env.storage().instance().get(&DEX_FACTORY),
        flash_loan_premium_bps: env.storage()
            .instance()
            .get(&FLASH_LOAN_PREMIUM)
            .unwrap_or(30),
        treasury: env.storage().instance().get(&TREASURY),
    }
}

// ============================================================================
// Liquidation Authorization (for 2-step flash liquidation)
// ============================================================================

/// Authorization for a prepared liquidation.
/// Stores validation results from prepare_liquidation for use in execute_liquidation.
#[contracttype]
#[derive(Clone)]
pub struct LiquidationAuthorization {
    pub liquidator: Address,
    pub user: Address,
    pub debt_asset: Address,
    pub collateral_asset: Address,
    pub debt_to_cover: u128,
    pub collateral_to_seize: u128,
    pub min_swap_out: u128,
    pub debt_price: u128,
    pub collateral_price: u128,
    pub health_factor_at_prepare: u128,
    pub expires_at: u64,
    pub nonce: u64,
    pub swap_handler: Option<Address>,
}

const LIQUIDATION_AUTH_NONCE: Symbol = symbol_short!("LIQNONCE");

/// Get liquidation authorization for a specific liquidator and user.
pub fn get_liquidation_authorization(
    env: &Env,
    liquidator: &Address,
    user: &Address,
) -> Result<LiquidationAuthorization, KineticRouterError> {
    let key = (LIQUIDATION_AUTH, liquidator.clone(), user.clone());
    env.storage()
        .temporary()
        .get(&key)
        .ok_or(KineticRouterError::InvalidLiquidation)
}

/// Store liquidation authorization with 5-minute TTL.
/// TTL is set to 300 ledgers (~5 minutes at 1 ledger/second).
pub fn set_liquidation_authorization(
    env: &Env,
    liquidator: &Address,
    user: &Address,
    auth: &LiquidationAuthorization,
) {
    let key = (LIQUIDATION_AUTH, liquidator.clone(), user.clone());
    env.storage().temporary().set(&key, auth);
    // L-03: TTL set to 600 ledgers (~10 minutes) to accommodate network congestion.
    // Threshold at 400 triggers early extension.
    env.storage().temporary().extend_ttl(&key, 400, 600);
}

/// Remove liquidation authorization (after execution or expiry).
pub fn remove_liquidation_authorization(env: &Env, liquidator: &Address, user: &Address) {
    let key = (LIQUIDATION_AUTH, liquidator.clone(), user.clone());
    if env.storage().temporary().has(&key) {
        env.storage().temporary().remove(&key);
    }
}

/// Get and increment the liquidation nonce (prevents replay attacks).
pub fn get_and_increment_liquidation_nonce(env: &Env) -> u64 {
    let current_nonce: u64 = env
        .storage()
        .instance()
        .get(&LIQUIDATION_AUTH_NONCE)
        .unwrap_or(0);
    let next_nonce = current_nonce.checked_add(1).unwrap_or_else(|| {
        panic_with_error!(env, KineticRouterError::MathOverflow)
    });
    env.storage()
        .instance()
        .set(&LIQUIDATION_AUTH_NONCE, &next_nonce);
    env.storage().instance().extend_ttl(TTL_THRESHOLD, TTL_EXTENSION);
    current_nonce
}
