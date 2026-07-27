#![no_main]

//! Fuzz test for K2 reserve configuration operations.
//!
//! This fuzzer tests reserve configuration through PoolConfigurator:
//! - LTV and liquidation threshold relationships (50 bps buffer requirement)
//! - Reserve factor bounds (max 10,000 bps)
//! - Liquidation bonus bounds (max 10,000 bps)
//! - Supply/borrow caps (u64 overflow protection)
//! - Reserve flags (active, frozen, paused, borrowing_enabled, flashloan_enabled)
//!
//! Key invariants tested:
//! - liquidation_threshold > ltv + 50 bps (anti-hair-trigger)
//! - ltv <= 10,000 bps
//! - liquidation_threshold <= 10,000 bps
//! - liquidation_bonus <= 10,000 bps
//! - reserve_factor <= 10,000 bps
//! - supply_cap <= u64::MAX
//! - borrow_cap <= u64::MAX
//!
//! Note: Authorization testing is not performed because mock_all_auths() bypasses
//! all authorization checks. This fuzzer focuses on parameter validation only.
//!
//! Run with: cargo +nightly fuzz run fuzz_reserve_config --sanitizer=none

use arbitrary::Arbitrary;
use libfuzzer_sys::fuzz_target;
use k2_shared::ReserveConfiguration as SharedReserveConfig;
use soroban_sdk::{
    contract, contractimpl, contracttype,
    testutils::{Address as _, Ledger as _},
    Address, Env, IntoVal, String,
};

// =============================================================================
// Contract WASM Imports
// =============================================================================

mod kinetic_router {
    soroban_sdk::contractimport!(
        file = "../../../target/wasm32v1-none/release/k2_kinetic_router.optimized.wasm"
    );
}

mod pool_configurator {
    soroban_sdk::contractimport!(
        file = "../../../target/wasm32v1-none/release/k2_pool_configurator.optimized.wasm"
    );
}

mod a_token {
    soroban_sdk::contractimport!(
        file = "../../../target/wasm32v1-none/release/k2_a_token.optimized.wasm"
    );
}

mod debt_token {
    soroban_sdk::contractimport!(
        file = "../../../target/wasm32v1-none/release/k2_debt_token.optimized.wasm"
    );
}

mod price_oracle {
    soroban_sdk::contractimport!(
        file = "../../../target/wasm32v1-none/release/k2_price_oracle.optimized.wasm"
    );
}

mod interest_rate_strategy {
    soroban_sdk::contractimport!(
        file = "../../../target/wasm32v1-none/release/k2_interest_rate_strategy.optimized.wasm"
    );
}

// =============================================================================
// Mock Contracts
// =============================================================================

/// Asset enum matching the Reflector oracle interface
#[contracttype]
#[derive(Clone, Debug)]
pub enum ReflectorAsset {
    Stellar(Address),
    Other(soroban_sdk::Symbol),
}

/// Price data returned by the mock reflector
#[contracttype]
#[derive(Clone, Debug)]
pub struct PriceData {
    pub price: i128,
    pub timestamp: u64,
}

/// Mock Reflector Oracle
#[contract]
pub struct MockReflector;

#[contractimpl]
impl MockReflector {
    pub fn decimals(_env: Env) -> u32 {
        14
    }

    pub fn lastprice(env: Env, _asset: ReflectorAsset) -> Option<PriceData> {
        Some(PriceData {
            price: 1_000_000_000_000_000i128,
            timestamp: env.ledger().timestamp(),
        })
    }
}

// =============================================================================
// Fuzz Input Types
// =============================================================================

/// Hint for generating boundary values
#[derive(Arbitrary, Debug, Clone, Copy)]
pub enum BoundaryHint {
    Raw,
    MaxValid,
    JustAboveMax,
    Zero,
    Max,
}

/// Reserve configuration operations
#[derive(Arbitrary, Debug, Clone)]
pub enum ConfigOperation {
    /// Configure collateral parameters (LTV, liquidation threshold, bonus)
    ConfigureAsCollateral {
        ltv_bps: u16,
        liquidation_threshold_bps: u16,
        liquidation_bonus_bps: u16,
        ltv_hint: BoundaryHint,
        threshold_hint: BoundaryHint,
        bonus_hint: BoundaryHint,
    },
    /// Set reserve active state
    SetReserveActive { active: bool },
    /// Set reserve frozen state
    SetReserveFreeze { freeze: bool },
    /// Set reserve paused state (emergency admin only)
    SetReservePause { paused: bool },
    /// Set reserve factor
    SetReserveFactor {
        factor_bps: u16,
        hint: BoundaryHint,
    },
    /// Enable/disable borrowing
    EnableBorrowing { enabled: bool },
    /// Enable/disable flashloaning
    SetFlashloaning { enabled: bool },
    /// Set supply cap
    SetSupplyCap {
        cap_low: u64,
        cap_high: u64,
        hint: BoundaryHint,
    },
    /// Set borrow cap
    SetBorrowCap {
        cap_low: u64,
        cap_high: u64,
        hint: BoundaryHint,
    },
    /// Set debt ceiling
    SetDebtCeiling {
        ceiling_low: u64,
        ceiling_high: u64,
        hint: BoundaryHint,
    },
    /// Advance time
    AdvanceTime { seconds: u32 },
}

/// Fuzz input for reserve configuration
#[derive(Arbitrary, Debug, Clone)]
pub struct ReserveConfigInput {
    /// Sequence of configuration operations
    pub operations: [Option<ConfigOperation>; 12],
    /// Initial LTV (used to test threshold relationship)
    pub initial_ltv_bps: u16,
    /// Initial liquidation threshold
    pub initial_threshold_bps: u16,
}

// =============================================================================
// Constants
// =============================================================================

/// Maximum valid basis points (100%)
const MAX_BPS: u32 = 10_000;

/// Minimum buffer between LTV and liquidation threshold (50 bps)
const MIN_BUFFER_BPS: u32 = 50;

/// Base price with 14 decimals
const BASE_PRICE: u128 = 1_000_000_000_000_000;

/// u64 max for cap validation
const U64_MAX: u128 = u64::MAX as u128;

// =============================================================================
// Test Setup Helpers
// =============================================================================

fn setup_test_env() -> Env {
    let env = Env::default();
    env.mock_all_auths();
    env.cost_estimate().budget().reset_unlimited();
    env
}

fn setup_oracle(env: &Env, admin: &Address) -> Address {
    let oracle_addr = env.register(price_oracle::WASM, ());
    let oracle_client = price_oracle::Client::new(env, &oracle_addr);
    let reflector_addr = env.register(MockReflector, ());
    let base_currency = Address::generate(env);
    let native_xlm = Address::generate(env);
    oracle_client.initialize(admin, &reflector_addr, &base_currency, &native_xlm);
    oracle_addr
}

fn setup_kinetic_router(
    env: &Env,
    pool_admin: &Address,
    emergency_admin: &Address,
    oracle_addr: &Address,
    configurator_addr: &Address,
) -> Address {
    let router_addr = env.register(kinetic_router::WASM, ());
    let client = kinetic_router::Client::new(env, &router_addr);
    let treasury = Address::generate(env);
    let dex_router = Address::generate(env);

    client.initialize(
        pool_admin,
        emergency_admin,
        oracle_addr,
        &treasury,
        &dex_router,
        &None,
    );

    client.set_pool_configurator(configurator_addr);

    router_addr
}

fn setup_pool_configurator(
    env: &Env,
    pool_admin: &Address,
    router_addr: &Address,
    oracle_addr: &Address,
) -> Address {
    let configurator_addr = env.register(pool_configurator::WASM, ());
    let configurator_client = pool_configurator::Client::new(env, &configurator_addr);

    configurator_client.initialize(pool_admin, router_addr, oracle_addr);

    configurator_addr
}

fn setup_reserve(
    env: &Env,
    router_addr: &Address,
    configurator_addr: &Address,
    oracle_addr: &Address,
    admin: &Address,
    initial_ltv: u32,
    initial_threshold: u32,
) -> Address {
    // Create underlying asset
    let underlying_contract = env.register_stellar_asset_contract_v2(admin.clone());
    let underlying_asset = underlying_contract.address();

    // Setup interest rate strategy
    let irs_addr = env.register(interest_rate_strategy::WASM, ());
    env.invoke_contract::<()>(
        &irs_addr,
        &soroban_sdk::Symbol::new(env, "initialize"),
        soroban_sdk::vec![
            env,
            admin.into_val(env),
            200u128.into_val(env),
            1000u128.into_val(env),
            10000u128.into_val(env),
            8000u128.into_val(env),
        ],
    );

    // Setup aToken
    let a_token_addr = env.register(a_token::WASM, ());
    let a_token_client = a_token::Client::new(env, &a_token_addr);
    a_token_client.initialize(
        admin,
        &underlying_asset,
        router_addr,
        &String::from_str(env, "Test aToken"),
        &String::from_str(env, "aTEST"),
        &7u32,
    );

    // Setup debt token
    let debt_token_addr = env.register(debt_token::WASM, ());
    let debt_token_client = debt_token::Client::new(env, &debt_token_addr);
    debt_token_client.initialize(
        admin,
        &underlying_asset,
        router_addr,
        &String::from_str(env, "Test Debt"),
        &String::from_str(env, "dTEST"),
        &7u32,
    );

    // Register asset with oracle
    let oracle_client = price_oracle::Client::new(env, oracle_addr);
    let asset_enum = price_oracle::Asset::Stellar(underlying_asset.clone());
    oracle_client.add_asset(admin, &asset_enum);
    oracle_client.set_manual_override(
        admin,
        &asset_enum,
        &Some(BASE_PRICE),
        &Some(env.ledger().timestamp() + 604_000),
    );

    // Init reserve via configurator
    let configurator_client = pool_configurator::Client::new(env, configurator_addr);
    let treasury = Address::generate(env);

    // Ensure valid initial values
    let ltv = initial_ltv.min(MAX_BPS - MIN_BUFFER_BPS - 1);
    let threshold = (ltv + MIN_BUFFER_BPS + 1).min(MAX_BPS);

    let params = pool_configurator::InitReserveParams {
        decimals: 7,
        ltv,
        liquidation_threshold: threshold,
        liquidation_bonus: 500,
        reserve_factor: 1000,
        supply_cap: 1_000_000_000_000_000u128,
        borrow_cap: 1_000_000_000_000_000u128,
        borrowing_enabled: true,
        flashloan_enabled: true,
    };

    let _ = configurator_client.try_init_reserve(
        admin,
        &underlying_asset,
        &a_token_addr,
        &debt_token_addr,
        &irs_addr,
        &treasury,
        &params,
    );

    underlying_asset
}

// =============================================================================
// Boundary Value Processing
// =============================================================================

fn process_bps_value(raw: u16, hint: BoundaryHint) -> u32 {
    match hint {
        BoundaryHint::Raw => raw as u32,
        BoundaryHint::MaxValid => MAX_BPS,
        BoundaryHint::JustAboveMax => MAX_BPS + 1,
        BoundaryHint::Zero => 0,
        BoundaryHint::Max => u32::MAX,
    }
}

fn process_cap_value(low: u64, high: u64, hint: BoundaryHint) -> u128 {
    let raw = ((high as u128) << 64) | (low as u128);
    match hint {
        BoundaryHint::Raw => raw.min(U64_MAX * 2),
        BoundaryHint::MaxValid => U64_MAX,
        BoundaryHint::JustAboveMax => U64_MAX + 1,
        BoundaryHint::Zero => 0,
        BoundaryHint::Max => u128::MAX,
    }
}

// =============================================================================
// Invariant Checks
// =============================================================================

fn check_reserve_config_invariants(
    router_client: &kinetic_router::Client,
    asset: &Address,
) {
    let reserve_data = router_client.get_reserve_data(asset);

    // Convert to shared type to use getter methods
    let config = SharedReserveConfig {
        data_low: reserve_data.configuration.data_low,
        data_high: reserve_data.configuration.data_high,
    };

    // Extract configuration values using shared type methods
    let ltv = config.get_ltv() as u32;
    let threshold = config.get_liquidation_threshold() as u32;
    let bonus = config.get_liquidation_bonus() as u32;
    let reserve_factor = config.get_reserve_factor() as u32;

    // Invariant 1: LTV should be <= 10,000 bps
    assert!(
        ltv <= MAX_BPS,
        "LTV {} exceeds max {}",
        ltv,
        MAX_BPS
    );

    // Invariant 2: Liquidation threshold should be <= 10,000 bps
    assert!(
        threshold <= MAX_BPS,
        "Liquidation threshold {} exceeds max {}",
        threshold,
        MAX_BPS
    );

    // Invariant 3: Liquidation threshold should be > LTV + 50 bps (if both non-zero)
    if ltv > 0 && threshold > 0 {
        assert!(
            threshold >= ltv + MIN_BUFFER_BPS,
            "Liquidation threshold {} must be >= LTV {} + {} bps buffer",
            threshold,
            ltv,
            MIN_BUFFER_BPS
        );
    }

    // Invariant 4: Liquidation bonus should be <= 10,000 bps
    assert!(
        bonus <= MAX_BPS,
        "Liquidation bonus {} exceeds max {}",
        bonus,
        MAX_BPS
    );

    // Invariant 5: Reserve factor should be <= 10,000 bps
    assert!(
        reserve_factor <= MAX_BPS,
        "Reserve factor {} exceeds max {}",
        reserve_factor,
        MAX_BPS
    );
}

// =============================================================================
// Test Context
// =============================================================================

struct TestContext<'a> {
    env: &'a Env,
    configurator_client: &'a pool_configurator::Client<'a>,
    #[allow(dead_code)]
    router_client: &'a kinetic_router::Client<'a>,
    pool_admin: &'a Address,
    emergency_admin: &'a Address,
    underlying_asset: &'a Address,
}

// =============================================================================
// Operation Execution
// =============================================================================

/// Execute a configuration operation.
/// Note: Authorization is not tested because mock_all_auths() bypasses all checks.
/// This function focuses on parameter validation only.
fn execute_config_operation(ctx: &TestContext, op: &ConfigOperation) {
    match op {
        ConfigOperation::ConfigureAsCollateral {
            ltv_bps,
            liquidation_threshold_bps,
            liquidation_bonus_bps,
            ltv_hint,
            threshold_hint,
            bonus_hint,
        } => {
            let ltv = process_bps_value(*ltv_bps, *ltv_hint);
            let threshold = process_bps_value(*liquidation_threshold_bps, *threshold_hint);
            let bonus = process_bps_value(*liquidation_bonus_bps, *bonus_hint);

            let result = ctx.configurator_client.try_configure_reserve_as_collateral(
                ctx.pool_admin,
                ctx.underlying_asset,
                &ltv,
                &threshold,
                &bonus,
            );

            // Invalid configurations should fail
            let should_fail = ltv > MAX_BPS
                || threshold > MAX_BPS
                || bonus > MAX_BPS
                || (threshold > 0 && ltv > 0 && threshold < ltv + MIN_BUFFER_BPS)
                || (threshold > 0 && threshold <= ltv);

            if should_fail {
                assert!(result.is_err() || result.as_ref().unwrap().is_err(),
                    "Invalid config (ltv={}, threshold={}, bonus={}) should fail",
                    ltv, threshold, bonus);
            }
        }

        ConfigOperation::SetReserveActive { active } => {
            let _ = ctx.configurator_client.try_set_reserve_active(
                ctx.pool_admin,
                ctx.underlying_asset,
                active,
            );
        }

        ConfigOperation::SetReserveFreeze { freeze } => {
            let _ = ctx.configurator_client.try_set_reserve_freeze(
                ctx.pool_admin,
                ctx.underlying_asset,
                freeze,
            );
        }

        ConfigOperation::SetReservePause { paused } => {
            // Use emergency admin for pause operations
            let _ = ctx.configurator_client.try_set_reserve_pause(
                ctx.emergency_admin,
                ctx.underlying_asset,
                paused,
            );
        }

        ConfigOperation::SetReserveFactor { factor_bps, hint } => {
            let factor = process_bps_value(*factor_bps, *hint);

            let result = ctx.configurator_client.try_set_reserve_factor(
                ctx.pool_admin,
                ctx.underlying_asset,
                &factor,
            );

            // Factor > 10,000 should fail
            if factor > MAX_BPS {
                assert!(result.is_err() || result.as_ref().unwrap().is_err(),
                    "Reserve factor {} > 10,000 should fail", factor);
            }
        }

        ConfigOperation::EnableBorrowing { enabled } => {
            let _ = ctx.configurator_client.try_enable_borrowing_on_reserve(
                ctx.pool_admin,
                ctx.underlying_asset,
                enabled,
            );
        }

        ConfigOperation::SetFlashloaning { enabled } => {
            let _ = ctx.configurator_client.try_set_reserve_flashloaning(
                ctx.pool_admin,
                ctx.underlying_asset,
                enabled,
            );
        }

        ConfigOperation::SetSupplyCap { cap_low, cap_high, hint } => {
            let cap = process_cap_value(*cap_low, *cap_high, *hint);

            let result = ctx.configurator_client.try_set_supply_cap(
                ctx.pool_admin,
                ctx.underlying_asset,
                &cap,
            );

            // Cap > u64::MAX should fail
            if cap > U64_MAX {
                assert!(result.is_err() || result.as_ref().unwrap().is_err(),
                    "Supply cap {} > u64::MAX should fail", cap);
            }
        }

        ConfigOperation::SetBorrowCap { cap_low, cap_high, hint } => {
            let cap = process_cap_value(*cap_low, *cap_high, *hint);

            let result = ctx.configurator_client.try_set_borrow_cap(
                ctx.pool_admin,
                ctx.underlying_asset,
                &cap,
            );

            // Cap > u64::MAX should fail
            if cap > U64_MAX {
                assert!(result.is_err() || result.as_ref().unwrap().is_err(),
                    "Borrow cap {} > u64::MAX should fail", cap);
            }
        }

        ConfigOperation::SetDebtCeiling { ceiling_low, ceiling_high, hint } => {
            let ceiling = process_cap_value(*ceiling_low, *ceiling_high, *hint);

            let result = ctx.configurator_client.try_set_debt_ceiling(
                ctx.pool_admin,
                ctx.underlying_asset,
                &ceiling,
            );

            // Ceiling > u64::MAX should fail
            if ceiling > U64_MAX {
                assert!(result.is_err() || result.as_ref().unwrap().is_err(),
                    "Debt ceiling {} > u64::MAX should fail", ceiling);
            }
        }

        ConfigOperation::AdvanceTime { seconds } => {
            let max_advance = 31_536_000u64;
            let advance = (*seconds as u64) % max_advance;
            if advance > 0 {
                let current_timestamp = ctx.env.ledger().timestamp();
                let new_timestamp = current_timestamp.saturating_add(advance);
                ctx.env.ledger().set_timestamp(new_timestamp);
            }
        }
    }
}

// =============================================================================
// Fuzz Target
// =============================================================================

fuzz_target!(|input: ReserveConfigInput| {
    let env = setup_test_env();

    // Setup distinct addresses
    let pool_admin = Address::generate(&env);
    let emergency_admin = Address::generate(&env);

    // Setup contracts
    let oracle_addr = setup_oracle(&env, &pool_admin);

    // First register the pool configurator
    let configurator_addr = env.register(pool_configurator::WASM, ());

    // Setup router with configurator address
    let router_addr = setup_kinetic_router(
        &env,
        &pool_admin,
        &emergency_admin,
        &oracle_addr,
        &configurator_addr,
    );

    // Initialize configurator
    let configurator_client = pool_configurator::Client::new(&env, &configurator_addr);
    configurator_client.initialize(&pool_admin, &router_addr, &oracle_addr);

    // Setup reserve with initial configuration
    let initial_ltv = (input.initial_ltv_bps as u32).min(MAX_BPS - MIN_BUFFER_BPS - 100);
    let initial_threshold = (input.initial_threshold_bps as u32)
        .max(initial_ltv + MIN_BUFFER_BPS + 1)
        .min(MAX_BPS);

    let underlying_asset = setup_reserve(
        &env,
        &router_addr,
        &configurator_addr,
        &oracle_addr,
        &pool_admin,
        initial_ltv,
        initial_threshold,
    );

    let router_client = kinetic_router::Client::new(&env, &router_addr);

    // Create test context
    let ctx = TestContext {
        env: &env,
        configurator_client: &configurator_client,
        router_client: &router_client,
        pool_admin: &pool_admin,
        emergency_admin: &emergency_admin,
        underlying_asset: &underlying_asset,
    };

    // Check initial invariants
    check_reserve_config_invariants(&router_client, &underlying_asset);

    // Execute operations
    for op_opt in input.operations.iter() {
        if let Some(op) = op_opt {
            execute_config_operation(&ctx, op);

            // Check invariants after each operation
            check_reserve_config_invariants(&router_client, &underlying_asset);
        }
    }

    // Final invariant check
    check_reserve_config_invariants(&router_client, &underlying_asset);
});
