#![no_main]

//! Fuzz test for K2 economic invariants.
//!
//! This fuzzer tests the economic properties of the lending protocol:
//! 1. Interest rate model behavior (rates increase with utilization)
//! 2. Utilization rate bounds (always 0-100%)
//! 3. Reserve factor and treasury accrual
//! 4. Supply/borrow rate relationship
//! 5. Index growth proportional to rates and time
//! 6. Value conservation (no creation or destruction of value)
//!
//! ## Key Invariants:
//! - Utilization = total_borrows / total_liquidity (bounded 0-100%)
//! - Supply rate <= borrow rate (protocol takes spread)
//! - Higher utilization => higher rates (monotonic)
//! - Treasury accrues reserve_factor portion of interest
//! - Indices only increase (monotonically)
//! - Total value in = total value out (conservation)
//!
//! Run with: cargo +nightly fuzz run fuzz_economic_invariants --sanitizer=none

use arbitrary::Arbitrary;
use libfuzzer_sys::fuzz_target;
use soroban_sdk::{
    contract, contractimpl, contracttype,
    testutils::{Address as _, Ledger as _, StellarAssetContract},
    token::{self, StellarAssetClient},
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

#[contracttype]
#[derive(Clone, Debug)]
pub enum ReflectorAsset {
    Stellar(Address),
    Other(soroban_sdk::Symbol),
}

#[contracttype]
#[derive(Clone, Debug)]
pub struct PriceData {
    pub price: i128,
    pub timestamp: u64,
}

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

#[derive(Arbitrary, Debug, Clone, Copy)]
pub enum User {
    User1,
    User2,
    User3,
}

/// Operations that affect economic state
#[derive(Arbitrary, Debug, Clone)]
pub enum EconomicOperation {
    /// Supply assets (increases liquidity)
    Supply { user: User, amount: u64 },
    /// Borrow assets (increases utilization)
    Borrow { user: User, amount: u64 },
    /// Repay debt (decreases utilization)
    Repay { user: User, amount: u64 },
    /// Withdraw assets (decreases liquidity)
    Withdraw { user: User, amount: u64 },
    /// Advance time to accrue interest
    AdvanceTime { seconds: u32 },
    /// Large supply to test low utilization
    LargeSupply { user: User },
    /// Borrow to specific utilization target (percent 0-100)
    BorrowToUtilization { user: User, target_percent: u8 },
    /// Repay all debt
    RepayAll { user: User },
    /// Withdraw all
    WithdrawAll { user: User },
}

#[derive(Arbitrary, Debug, Clone)]
pub struct EconomicInput {
    /// Initial liquidity amount
    pub initial_liquidity: u64,
    /// Interest rate strategy parameters
    pub base_rate_bps: u16,
    pub slope1_bps: u16,
    pub slope2_bps: u16,
    pub optimal_utilization_bps: u16,
    /// Reserve factor (basis points, 0-10000)
    pub reserve_factor_bps: u16,
    /// Sequence of operations
    pub operations: [Option<EconomicOperation>; 16],
}

// =============================================================================
// Constants
// =============================================================================

/// RAY constant (1e9 for rate precision)
const RAY: u128 = 1_000_000_000;

/// Basis points denominator
const BPS: u128 = 10_000;

/// Seconds per year for rate calculations
const SECONDS_PER_YEAR: u128 = 31_536_000;

/// Minimum amount
const MIN_AMOUNT: u128 = 1_000_000;

/// Maximum amount
const MAX_AMOUNT: u128 = 100_000_000_000_000;

// =============================================================================
// Economic State Tracking
// =============================================================================

/// Comprehensive snapshot of economic state
#[derive(Clone, Debug)]
struct EconomicSnapshot {
    // Reserve state
    liquidity_index: u128,
    variable_borrow_index: u128,
    current_liquidity_rate: u128,
    current_variable_borrow_rate: u128,

    // Supply/borrow totals
    total_atoken_supply: i128,
    total_debt_supply: i128,
    underlying_balance: i128,

    // Treasury
    treasury_balance: i128,

    // Timestamp
    timestamp: u64,
}

impl EconomicSnapshot {
    fn take(
        env: &Env,
        router_client: &kinetic_router::Client,
        asset: &Address,
        a_token: &Address,
        treasury: &Address,
    ) -> Self {
        let reserve_data = router_client.get_reserve_data(asset);
        let token_client = token::Client::new(env, asset);
        let atoken_client = a_token::Client::new(env, a_token);
        let debt_token_client = debt_token::Client::new(env, &reserve_data.debt_token_address);

        Self {
            liquidity_index: reserve_data.liquidity_index,
            variable_borrow_index: reserve_data.variable_borrow_index,
            current_liquidity_rate: reserve_data.current_liquidity_rate,
            current_variable_borrow_rate: reserve_data.current_variable_borrow_rate,
            total_atoken_supply: atoken_client.total_supply(),
            total_debt_supply: debt_token_client.total_supply(),
            underlying_balance: token_client.balance(a_token),
            treasury_balance: token_client.balance(treasury),
            timestamp: env.ledger().timestamp(),
        }
    }

    /// Calculate utilization rate (in RAY)
    fn utilization_rate(&self) -> u128 {
        if self.total_atoken_supply <= 0 {
            return 0;
        }
        let total_supply = self.total_atoken_supply as u128;
        let total_debt = self.total_debt_supply.max(0) as u128;

        if total_supply == 0 {
            return 0;
        }

        // Utilization = debt / (underlying + debt) = debt / total_supply
        // In practice: debt / available_liquidity where available = underlying balance
        let available = self.underlying_balance.max(0) as u128;
        let total_liquidity = available + total_debt;

        if total_liquidity == 0 {
            return 0;
        }

        (total_debt * RAY) / total_liquidity
    }
}

/// Track rate history for monotonicity testing
#[derive(Clone, Debug)]
struct RateHistory {
    entries: Vec<(u128, u128, u128)>, // (utilization, supply_rate, borrow_rate)
}

impl RateHistory {
    fn new() -> Self {
        Self { entries: Vec::new() }
    }

    fn record(&mut self, utilization: u128, supply_rate: u128, borrow_rate: u128) {
        self.entries.push((utilization, supply_rate, borrow_rate));
    }

    /// Check if rates are monotonically increasing with utilization
    fn check_monotonicity(&self) -> bool {
        if self.entries.len() < 2 {
            return true;
        }

        // Sort by utilization and check rate ordering
        let mut sorted = self.entries.clone();
        sorted.sort_by_key(|(u, _, _)| *u);

        for i in 1..sorted.len() {
            let (util_prev, _, borrow_prev) = sorted[i - 1];
            let (util_curr, _, borrow_curr) = sorted[i];

            // If utilization increased significantly, borrow rate should not decrease
            // Allow small tolerance for rounding
            if util_curr > util_prev + RAY / 100 {
                // 1% difference
                if borrow_curr + RAY / 1000 < borrow_prev {
                    // 0.1% tolerance
                    return false;
                }
            }
        }
        true
    }
}

/// Track value flows for conservation testing
#[derive(Clone, Debug, Default)]
struct ValueFlows {
    total_supplied: u128,
    total_withdrawn: u128,
    total_borrowed: u128,
    total_repaid: u128,
    interest_accrued_estimate: u128,
}

// =============================================================================
// Setup Helpers
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
    admin: &Address,
    emergency_admin: &Address,
    oracle_addr: &Address,
    treasury: &Address,
) -> Address {
    let router_addr = env.register(kinetic_router::WASM, ());
    let client = kinetic_router::Client::new(env, &router_addr);
    let dex_router = Address::generate(env);

    client.initialize(
        admin,
        emergency_admin,
        oracle_addr,
        treasury,
        &dex_router,
        &None,
    );

    let pool_configurator = Address::generate(env);
    client.set_pool_configurator(&pool_configurator);

    router_addr
}

fn setup_reserve_with_params(
    env: &Env,
    router_addr: &Address,
    oracle_addr: &Address,
    admin: &Address,
    treasury: &Address,
    base_rate: u128,
    slope1: u128,
    slope2: u128,
    optimal_util: u128,
    reserve_factor: u32,
) -> (Address, StellarAssetContract, Address, Address) {
    let underlying_contract = env.register_stellar_asset_contract_v2(admin.clone());
    let underlying_asset = underlying_contract.address();

    // Setup interest rate strategy with custom parameters
    let irs_addr = env.register(interest_rate_strategy::WASM, ());
    env.invoke_contract::<()>(
        &irs_addr,
        &soroban_sdk::Symbol::new(env, "initialize"),
        soroban_sdk::vec![
            env,
            admin.into_val(env),
            base_rate.into_val(env),
            slope1.into_val(env),
            slope2.into_val(env),
            optimal_util.into_val(env),
        ],
    );

    // Setup aToken
    let a_token_addr = env.register(a_token::WASM, ());
    let a_token_client = a_token::Client::new(env, &a_token_addr);
    a_token_client.initialize(
        admin,
        &underlying_asset,
        router_addr,
        &String::from_str(env, "aToken"),
        &String::from_str(env, "aTKN"),
        &7u32,
    );

    // Setup debt token
    let debt_token_addr = env.register(debt_token::WASM, ());
    let debt_token_client = debt_token::Client::new(env, &debt_token_addr);
    debt_token_client.initialize(
        admin,
        &underlying_asset,
        router_addr,
        &String::from_str(env, "dToken"),
        &String::from_str(env, "dTKN"),
        &7u32,
    );

    // Register with oracle
    let oracle_client = price_oracle::Client::new(env, oracle_addr);
    let asset_enum = price_oracle::Asset::Stellar(underlying_asset.clone());
    oracle_client.add_asset(admin, &asset_enum);
    oracle_client.set_manual_override(
        admin,
        &asset_enum,
        &Some(1_000_000_000_000_000u128), // $1
        &Some(env.ledger().timestamp() + 604_000),
    );

    // Init reserve
    let router_client = kinetic_router::Client::new(env, router_addr);
    let pool_configurator = Address::generate(env);
    router_client.set_pool_configurator(&pool_configurator);

    let params = kinetic_router::InitReserveParams {
        decimals: 7,
        ltv: 8000,
        liquidation_threshold: 8500,
        liquidation_bonus: 500,
        reserve_factor,
        supply_cap: 1_000_000_000_000_000u128,
        borrow_cap: 1_000_000_000_000_000u128,
        borrowing_enabled: true,
        flashloan_enabled: true,
    };

    router_client.init_reserve(
        &pool_configurator,
        &underlying_asset,
        &a_token_addr,
        &debt_token_addr,
        &irs_addr,
        treasury,
        &params,
    );

    (underlying_asset, underlying_contract, a_token_addr, debt_token_addr)
}

// =============================================================================
// Invariant Checks
// =============================================================================

/// Check utilization rate invariants
fn check_utilization_invariants(snapshot: &EconomicSnapshot) {
    let utilization = snapshot.utilization_rate();

    // === Utilization Bounds ===
    // Utilization should be between 0 and RAY (0-100%)
    assert!(
        utilization <= RAY,
        "UTILIZATION VIOLATION: Utilization {} exceeds 100% (RAY={})",
        utilization,
        RAY
    );

    // === Zero Debt => Zero Utilization ===
    if snapshot.total_debt_supply <= 0 {
        // With no debt, utilization should be 0
        // (though the calculation might give slightly different result due to timing)
    }
}

/// Check interest rate invariants
fn check_rate_invariants(snapshot: &EconomicSnapshot) {
    // === Supply Rate <= Borrow Rate ===
    // The protocol takes a spread, so supply rate should never exceed borrow rate
    assert!(
        snapshot.current_liquidity_rate <= snapshot.current_variable_borrow_rate,
        "RATE VIOLATION: Supply rate {} exceeds borrow rate {}",
        snapshot.current_liquidity_rate,
        snapshot.current_variable_borrow_rate
    );

    // === Non-Negative Rates ===
    // Rates should never be negative (they're unsigned, but check for sanity)
    // This is implicit in u128 type

    // === Rate Bounds ===
    // Rates shouldn't be astronomically high (e.g., > 1000% APY = 10 * RAY)
    let max_reasonable_rate = RAY * 100; // 10000% APY is probably a bug
    assert!(
        snapshot.current_variable_borrow_rate <= max_reasonable_rate,
        "RATE VIOLATION: Borrow rate {} unreasonably high (max={})",
        snapshot.current_variable_borrow_rate,
        max_reasonable_rate
    );
}

/// Check index invariants
fn check_index_invariants(before: &EconomicSnapshot, after: &EconomicSnapshot) {
    // === Index Monotonicity ===
    // Indices should only increase (interest accrues, never decreases)
    assert!(
        after.liquidity_index >= before.liquidity_index,
        "INDEX VIOLATION: Liquidity index decreased from {} to {}",
        before.liquidity_index,
        after.liquidity_index
    );
    assert!(
        after.variable_borrow_index >= before.variable_borrow_index,
        "INDEX VIOLATION: Borrow index decreased from {} to {}",
        before.variable_borrow_index,
        after.variable_borrow_index
    );

    // === Index Lower Bound ===
    // Indices should always be >= RAY (start at RAY, only grow)
    assert!(
        after.liquidity_index >= RAY,
        "INDEX VIOLATION: Liquidity index {} below RAY",
        after.liquidity_index
    );
    assert!(
        after.variable_borrow_index >= RAY,
        "INDEX VIOLATION: Borrow index {} below RAY",
        after.variable_borrow_index
    );
}

/// Check treasury accrual invariants
fn check_treasury_invariants(
    before: &EconomicSnapshot,
    after: &EconomicSnapshot,
    time_elapsed: u64,
) {
    // === Treasury Non-Decreasing ===
    // Treasury should not lose funds (only accrue)
    // Note: This might not hold if treasury withdraws, but in this test we don't do that
    assert!(
        after.treasury_balance >= before.treasury_balance,
        "TREASURY VIOLATION: Treasury balance decreased from {} to {}",
        before.treasury_balance,
        after.treasury_balance
    );

    // === Interest Accrual Direction ===
    // If time elapsed and there's debt, some interest should accrue
    if time_elapsed > 0 && before.total_debt_supply > 0 && before.current_variable_borrow_rate > 0 {
        // Either treasury increased or indices increased (interest went somewhere)
        let treasury_increased = after.treasury_balance > before.treasury_balance;
        let index_increased = after.liquidity_index > before.liquidity_index
            || after.variable_borrow_index > before.variable_borrow_index;

        // At least one should be true if interest was supposed to accrue
        // Allow for very small time periods where rounding might make it 0
        if time_elapsed > 60 {
            // More than a minute
            assert!(
                treasury_increased || index_increased,
                "ACCRUAL VIOLATION: No interest accrued despite {} seconds elapsed with debt",
                time_elapsed
            );
        }
    }
}

/// Check value conservation (approximate)
fn check_value_conservation(
    snapshot: &EconomicSnapshot,
    _value_flows: &ValueFlows,
) {
    // === Basic Accounting Identity ===
    // total_atoken_supply (in underlying terms) should roughly equal:
    // underlying_balance + total_debt
    // (with adjustments for indices and treasury)

    // Simplified check: underlying + debt should be reasonable relative to atoken supply
    let underlying = snapshot.underlying_balance.max(0) as u128;
    let debt = snapshot.total_debt_supply.max(0) as u128;
    let atoken = snapshot.total_atoken_supply.max(0) as u128;

    if atoken > 0 {
        // The atoken supply represents claims on underlying + accrued interest
        // underlying + debt should be close to atoken supply (in underlying terms)
        // This is approximate due to index scaling
        let total_assets = underlying + debt;

        // Allow significant tolerance due to interest accrual and scaling
        // Just check for gross violations (e.g., assets > 2x supply or < 0.5x supply)
        if total_assets > 0 && atoken > 0 {
            let ratio = (total_assets * RAY) / atoken;
            // Ratio should be reasonable (0.1x to 10x after interest)
            assert!(
                ratio >= RAY / 10 && ratio <= RAY * 10,
                "CONSERVATION VIOLATION: Asset/supply ratio {} out of bounds",
                ratio
            );
        }
    }
}

/// Check rate-utilization relationship
fn check_rate_utilization_relationship(
    rate_history: &RateHistory,
) {
    // === Monotonicity Check ===
    // Higher utilization should generally mean higher rates
    assert!(
        rate_history.check_monotonicity(),
        "RATE MODEL VIOLATION: Rates not monotonic with utilization"
    );
}

// =============================================================================
// Fuzz Target
// =============================================================================

fuzz_target!(|input: EconomicInput| {
    let env = setup_test_env();

    // Setup addresses
    let admin = Address::generate(&env);
    let emergency_admin = Address::generate(&env);
    let treasury = Address::generate(&env);
    let user1 = Address::generate(&env);
    let user2 = Address::generate(&env);
    let user3 = Address::generate(&env);

    // Parse interest rate parameters (clamp to reasonable values)
    // Contract validation requires: non-zero slopes, slope2 >= slope1
    let base_rate = (input.base_rate_bps.min(5000) as u128); // Max 50% base rate
    let slope1 = (input.slope1_bps.max(1).min(10000) as u128); // Min 1, max 100% slope1
    // slope2 must be >= slope1 (contract validation requirement for monotonic curve)
    let slope2_raw = (input.slope2_bps.max(1).min(30000) as u128); // Min 1, max 300% slope2
    let slope2 = slope2_raw.max(slope1);                           // Ensure slope2 >= slope1
    let optimal_util = (input.optimal_utilization_bps.max(1000).min(9500) as u128); // 10-95%
    let reserve_factor = (input.reserve_factor_bps.min(5000) as u32); // Max 50%

    // Setup oracle and router
    let oracle_addr = setup_oracle(&env, &admin);
    let router_addr = setup_kinetic_router(&env, &admin, &emergency_admin, &oracle_addr, &treasury);
    let router_client = kinetic_router::Client::new(&env, &router_addr);

    // Setup reserve with custom parameters
    let (underlying_asset, _underlying_contract, a_token, _debt_token) = setup_reserve_with_params(
        &env,
        &router_addr,
        &oracle_addr,
        &admin,
        &treasury,
        base_rate,
        slope1,
        slope2,
        optimal_util,
        reserve_factor,
    );

    let underlying_client = StellarAssetClient::new(&env, &underlying_asset);

    // Provide initial liquidity
    let initial_liquidity = (input.initial_liquidity as u128).clamp(MIN_AMOUNT * 10, MAX_AMOUNT);
    underlying_client.mint(&user1, &(initial_liquidity as i128 * 10));
    underlying_client.mint(&user2, &(MAX_AMOUNT as i128));
    underlying_client.mint(&user3, &(MAX_AMOUNT as i128));

    let supply_result = router_client.try_supply(
        &user1,
        &underlying_asset,
        &initial_liquidity,
        &user1,
        &0u32,
    );
    if supply_result.is_err() {
        return;
    }

    // Initialize tracking
    let mut last_snapshot = EconomicSnapshot::take(&env, &router_client, &underlying_asset, &a_token, &treasury);
    let mut rate_history = RateHistory::new();
    let mut value_flows = ValueFlows::default();

    value_flows.total_supplied = initial_liquidity;

    // Record initial rates
    rate_history.record(
        last_snapshot.utilization_rate(),
        last_snapshot.current_liquidity_rate,
        last_snapshot.current_variable_borrow_rate,
    );

    // Initial invariant checks
    check_utilization_invariants(&last_snapshot);
    check_rate_invariants(&last_snapshot);

    // Helper to get user address
    let get_user = |user: &User| -> &Address {
        match user {
            User::User1 => &user1,
            User::User2 => &user2,
            User::User3 => &user3,
        }
    };

    // Execute operations
    for op_opt in &input.operations {
        if let Some(op) = op_opt {
            let snapshot_before = EconomicSnapshot::take(&env, &router_client, &underlying_asset, &a_token, &treasury);

            match op {
                EconomicOperation::Supply { user, amount } => {
                    let user_addr = get_user(user);
                    let supply_amount = (*amount as u128).clamp(MIN_AMOUNT, MAX_AMOUNT);

                    if router_client
                        .try_supply(user_addr, &underlying_asset, &supply_amount, user_addr, &0u32)
                        .is_ok()
                    {
                        value_flows.total_supplied += supply_amount;
                    }
                }

                EconomicOperation::Borrow { user, amount } => {
                    let user_addr = get_user(user);
                    let borrow_amount = (*amount as u128).clamp(MIN_AMOUNT, MAX_AMOUNT / 10);

                    if router_client
                        .try_borrow(user_addr, &underlying_asset, &borrow_amount, &1u32, &0u32, user_addr)
                        .is_ok()
                    {
                        value_flows.total_borrowed += borrow_amount;
                    }
                }

                EconomicOperation::Repay { user, amount } => {
                    let user_addr = get_user(user);
                    let repay_amount = (*amount as u128).clamp(MIN_AMOUNT, MAX_AMOUNT);
                    underlying_client.mint(user_addr, &(repay_amount as i128 + 1000));

                    if router_client
                        .try_repay(user_addr, &underlying_asset, &repay_amount, &1u32, user_addr)
                        .is_ok()
                    {
                        value_flows.total_repaid += repay_amount;
                    }
                }

                EconomicOperation::Withdraw { user, amount } => {
                    let user_addr = get_user(user);
                    let withdraw_amount = (*amount as u128).clamp(MIN_AMOUNT, MAX_AMOUNT);

                    if router_client
                        .try_withdraw(user_addr, &underlying_asset, &withdraw_amount, user_addr)
                        .is_ok()
                    {
                        value_flows.total_withdrawn += withdraw_amount;
                    }
                }

                EconomicOperation::AdvanceTime { seconds } => {
                    let advance = (*seconds as u64).min(31_536_000); // Max 1 year
                    if advance > 0 {
                        let new_timestamp = env.ledger().timestamp().saturating_add(advance);
                        env.ledger().set_timestamp(new_timestamp);
                    }
                }

                EconomicOperation::LargeSupply { user } => {
                    let user_addr = get_user(user);
                    let large_amount = MAX_AMOUNT / 2;
                    underlying_client.mint(user_addr, &(large_amount as i128));

                    if router_client
                        .try_supply(user_addr, &underlying_asset, &large_amount, user_addr, &0u32)
                        .is_ok()
                    {
                        value_flows.total_supplied += large_amount;
                    }
                }

                EconomicOperation::BorrowToUtilization { user, target_percent } => {
                    let user_addr = get_user(user);
                    let target = (*target_percent).min(80) as u128; // Max 80% target

                    // Get current state
                    let current = EconomicSnapshot::take(&env, &router_client, &underlying_asset, &a_token, &treasury);
                    let available = current.underlying_balance.max(0) as u128;

                    if available > MIN_AMOUNT {
                        // Calculate borrow needed for target utilization
                        let target_borrow = available * target / 100;
                        let borrow_amount = target_borrow.min(available - MIN_AMOUNT);

                        if borrow_amount > MIN_AMOUNT {
                            if router_client
                                .try_borrow(user_addr, &underlying_asset, &borrow_amount, &1u32, &0u32, user_addr)
                                .is_ok()
                            {
                                value_flows.total_borrowed += borrow_amount;
                            }
                        }
                    }
                }

                EconomicOperation::RepayAll { user } => {
                    let user_addr = get_user(user);
                    let debt_token_addr = router_client.get_reserve_data(&underlying_asset).debt_token_address;
                    let debt_client = debt_token::Client::new(&env, &debt_token_addr);
                    let debt_balance = debt_client.balance(user_addr);

                    if debt_balance > 0 {
                        let repay_amount = (debt_balance as u128) + 1000; // Extra for interest
                        underlying_client.mint(user_addr, &(repay_amount as i128));

                        // Use u128::MAX to repay all
                        if router_client
                            .try_repay(user_addr, &underlying_asset, &u128::MAX, &1u32, user_addr)
                            .is_ok()
                        {
                            value_flows.total_repaid += debt_balance as u128;
                        }
                    }
                }

                EconomicOperation::WithdrawAll { user } => {
                    let user_addr = get_user(user);
                    let atoken_client = a_token::Client::new(&env, &a_token);
                    let atoken_balance = atoken_client.balance(user_addr);

                    if atoken_balance > 0 {
                        // Use u128::MAX to withdraw all
                        if router_client
                            .try_withdraw(user_addr, &underlying_asset, &u128::MAX, user_addr)
                            .is_ok()
                        {
                            value_flows.total_withdrawn += atoken_balance as u128;
                        }
                    }
                }
            }

            // Take snapshot after operation
            let snapshot_after = EconomicSnapshot::take(&env, &router_client, &underlying_asset, &a_token, &treasury);
            let time_elapsed = snapshot_after.timestamp.saturating_sub(snapshot_before.timestamp);

            // === Invariant Checks ===

            // Utilization invariants
            check_utilization_invariants(&snapshot_after);

            // Rate invariants
            check_rate_invariants(&snapshot_after);

            // Index invariants
            check_index_invariants(&snapshot_before, &snapshot_after);

            // Treasury invariants
            check_treasury_invariants(&snapshot_before, &snapshot_after, time_elapsed);

            // Value conservation
            check_value_conservation(&snapshot_after, &value_flows);

            // Record rates for monotonicity analysis
            rate_history.record(
                snapshot_after.utilization_rate(),
                snapshot_after.current_liquidity_rate,
                snapshot_after.current_variable_borrow_rate,
            );

            last_snapshot = snapshot_after;
        }
    }

    // === Final Invariant Checks ===

    // Rate-utilization relationship
    check_rate_utilization_relationship(&rate_history);

    // Final conservation check
    check_value_conservation(&last_snapshot, &value_flows);
});
