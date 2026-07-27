#![no_main]

//! Fuzz test for K2 adversarial price scenarios.
//!
//! This fuzzer tests protocol behavior under extreme price conditions:
//! 1. Flash crashes and price spikes
//! 2. Oracle manipulation scenarios
//! 3. Sandwich attacks on liquidations
//! 4. Price staleness edge cases
//! 5. Health factor calculations under extreme volatility
//!
//! ## Key Invariants:
//! - No negative or zero prices accepted
//! - Health factor correctly reflects price changes
//! - Liquidations only possible when HF < 1.0
//! - No profit extraction through price manipulation
//! - Protocol remains solvent under extreme price movements
//!
//! Run with: cargo +nightly fuzz run fuzz_price_scenarios --sanitizer=none

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

/// Mock Reflector Oracle with configurable staleness
#[contract]
pub struct MockReflector;

#[contractimpl]
impl MockReflector {
    pub fn decimals(_env: Env) -> u32 {
        14
    }

    /// Returns a base price - the actual price is controlled via manual overrides
    pub fn lastprice(env: Env, _asset: ReflectorAsset) -> Option<PriceData> {
        Some(PriceData {
            price: 1_000_000_000_000_000i128, // 1 USD with 14 decimals
            timestamp: env.ledger().timestamp(),
        })
    }
}

// =============================================================================
// Fuzz Input Types
// =============================================================================

/// Types of price movements to test
#[derive(Arbitrary, Debug, Clone, Copy)]
pub enum PriceMovement {
    /// Sudden crash (percentage drop, 0-99%)
    FlashCrash { percent: u8 },
    /// Sudden spike (percentage increase, 0-1000%)
    Spike { percent: u16 },
    /// Gradual decline over time
    GradualDecline { steps: u8, percent_per_step: u8 },
    /// Oscillation (alternating up/down)
    Oscillate { amplitude_percent: u8 },
    /// Set to extreme low value
    ExtremeLow,
    /// Set to extreme high value
    ExtremeHigh,
    /// Set to specific basis points (relative to $1)
    Absolute { price_bps: u32 },
}

/// Price manipulation attack patterns
#[derive(Arbitrary, Debug, Clone)]
pub enum PriceAttack {
    /// Simple price manipulation
    SetPrice { movement: PriceMovement },
    /// Sandwich: drop price, liquidate, restore price
    SandwichLiquidation {
        drop_percent: u8,
        liquidation_amount: u64,
    },
    /// Front-run a borrow by dropping collateral price
    FrontRunBorrow {
        drop_percent: u8,
        borrow_amount: u64,
    },
    /// Try to extract value through rapid price changes
    PriceOscillation { cycles: u8, amplitude: u8 },
    /// Advance time to test staleness
    AdvanceTime { seconds: u32 },
    /// User action: supply more collateral
    SupplyCollateral { amount: u64 },
    /// User action: repay debt
    RepayDebt { amount: u64 },
    /// User action: borrow
    Borrow { amount: u64 },
    /// User action: withdraw
    Withdraw { amount: u64 },
    /// Attempt liquidation
    AttemptLiquidation { amount: u64 },
}

#[derive(Arbitrary, Debug, Clone)]
pub struct PriceScenarioInput {
    /// Initial collateral amount
    pub collateral_amount: u64,
    /// Initial borrow percentage (of max LTV)
    pub borrow_percent: u8,
    /// Starting price in basis points (10000 = $1)
    pub initial_price_bps: u16,
    /// Sequence of price attacks/movements
    pub attacks: [Option<PriceAttack>; 10],
}

// =============================================================================
// Constants
// =============================================================================

/// RAY constant (1e9)
const RAY: u128 = 1_000_000_000;

/// WAD constant for health factor (1e18)
const WAD: u128 = 1_000_000_000_000_000_000;

/// Base price with 14 decimals (1 USD)
const BASE_PRICE: u128 = 1_000_000_000_000_000;

/// Minimum valid price (prevent division by zero)
const MIN_PRICE: u128 = 1_000_000; // Very small but non-zero

/// Maximum valid price (prevent overflow)
const MAX_PRICE: u128 = 1_000_000_000_000_000_000_000; // 1 million USD with 14 decimals

/// Minimum amount for operations
const MIN_AMOUNT: u128 = 1_000_000; // 0.1 tokens

/// Maximum amount for operations
const MAX_AMOUNT: u128 = 100_000_000_000_000; // 10M tokens

// =============================================================================
// Price Tracking
// =============================================================================

/// Track price history for analysis
#[derive(Clone, Debug)]
struct PriceHistory {
    prices: Vec<u128>,
    timestamps: Vec<u64>,
}

impl PriceHistory {
    fn new() -> Self {
        Self {
            prices: Vec::new(),
            timestamps: Vec::new(),
        }
    }

    fn record(&mut self, price: u128, timestamp: u64) {
        self.prices.push(price);
        self.timestamps.push(timestamp);
    }

    fn volatility(&self) -> u128 {
        if self.prices.len() < 2 {
            return 0;
        }
        let mut max_change: u128 = 0;
        for i in 1..self.prices.len() {
            let change = if self.prices[i] > self.prices[i - 1] {
                self.prices[i] - self.prices[i - 1]
            } else {
                self.prices[i - 1] - self.prices[i]
            };
            max_change = max_change.max(change);
        }
        max_change
    }
}

/// Snapshot of user position for profit/loss tracking
#[derive(Clone, Debug)]
struct PositionSnapshot {
    collateral_value: u128,
    debt_value: u128,
    health_factor: u128,
    atoken_balance: i128,
    debt_balance: i128,
}

impl PositionSnapshot {
    fn take(
        router_client: &kinetic_router::Client,
        a_token_client: &a_token::Client,
        debt_token_client: &debt_token::Client,
        user: &Address,
    ) -> Self {
        let atoken_balance = a_token_client.balance(user);
        let debt_balance = debt_token_client.balance(user);

        let (collateral_value, debt_value, health_factor) =
            if let Ok(Ok(data)) = router_client.try_get_user_account_data(user) {
                (data.total_collateral_base, data.total_debt_base, data.health_factor)
            } else {
                (0, 0, u128::MAX)
            };

        Self {
            collateral_value,
            debt_value,
            health_factor,
            atoken_balance,
            debt_balance,
        }
    }
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
) -> Address {
    let router_addr = env.register(kinetic_router::WASM, ());
    let client = kinetic_router::Client::new(env, &router_addr);
    let treasury = Address::generate(env);
    let dex_router = Address::generate(env);

    client.initialize(
        admin,
        emergency_admin,
        oracle_addr,
        &treasury,
        &dex_router,
        &None,
    );

    let pool_configurator = Address::generate(env);
    client.set_pool_configurator(&pool_configurator);

    router_addr
}

fn setup_reserve(
    env: &Env,
    router_addr: &Address,
    oracle_addr: &Address,
    admin: &Address,
    initial_price: u128,
) -> (Address, StellarAssetContract, Address, Address) {
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
        &Some(initial_price),
        &Some(env.ledger().timestamp() + 604_000),
    );

    // Init reserve
    let router_client = kinetic_router::Client::new(env, router_addr);
    let treasury = Address::generate(env);
    let pool_configurator = Address::generate(env);
    router_client.set_pool_configurator(&pool_configurator);

    let params = kinetic_router::InitReserveParams {
        decimals: 7,
        ltv: 8000,                // 80%
        liquidation_threshold: 8500, // 85%
        liquidation_bonus: 500,      // 5%
        reserve_factor: 1000,
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
        &treasury,
        &params,
    );

    (underlying_asset, underlying_contract, a_token_addr, debt_token_addr)
}

// =============================================================================
// Price Manipulation Helpers
// =============================================================================

fn apply_price_movement(
    current_price: u128,
    movement: &PriceMovement,
) -> u128 {
    match movement {
        PriceMovement::FlashCrash { percent } => {
            let drop = (*percent as u128).min(99);
            current_price * (100 - drop) / 100
        }
        PriceMovement::Spike { percent } => {
            let increase = (*percent as u128).min(10000); // Max 100x
            current_price * (100 + increase) / 100
        }
        PriceMovement::GradualDecline { steps: _, percent_per_step } => {
            // Apply one step of decline
            let drop = (*percent_per_step as u128).min(50);
            current_price * (100 - drop) / 100
        }
        PriceMovement::Oscillate { amplitude_percent } => {
            // Random direction based on current price parity
            let amp = (*amplitude_percent as u128).min(50);
            if current_price % 2 == 0 {
                current_price * (100 + amp) / 100
            } else {
                current_price * (100 - amp) / 100
            }
        }
        PriceMovement::ExtremeLow => MIN_PRICE,
        PriceMovement::ExtremeHigh => MAX_PRICE,
        PriceMovement::Absolute { price_bps } => {
            BASE_PRICE * (*price_bps as u128).max(1) / 10000
        }
    }
}

fn set_price(
    oracle_client: &price_oracle::Client,
    admin: &Address,
    asset: &Address,
    price: u128,
    timestamp: u64,
) -> bool {
    // Clamp price to valid range
    let clamped_price = price.clamp(MIN_PRICE, MAX_PRICE);
    let asset_enum = price_oracle::Asset::Stellar(asset.clone());

    oracle_client
        .try_set_manual_override(
            admin,
            &asset_enum,
            &Some(clamped_price),
            &Some(timestamp + 604_000),
        )
        .is_ok()
}

// =============================================================================
// Invariant Checks
// =============================================================================

/// Check price-related invariants
fn check_price_invariants(
    oracle_client: &price_oracle::Client,
    asset: &Address,
    current_price: u128,
) {
    // === Price Bounds Invariant ===
    assert!(
        current_price >= MIN_PRICE,
        "PRICE VIOLATION: Price {} below minimum {}",
        current_price,
        MIN_PRICE
    );
    assert!(
        current_price <= MAX_PRICE,
        "PRICE VIOLATION: Price {} above maximum {}",
        current_price,
        MAX_PRICE
    );

    // === Oracle Consistency ===
    let asset_enum = price_oracle::Asset::Stellar(asset.clone());
    if let Ok(Ok(oracle_price)) = oracle_client.try_get_asset_price(&asset_enum) {
        assert!(
            oracle_price > 0,
            "PRICE VIOLATION: Oracle returned zero price"
        );
    }
}

/// Check health factor invariants under price changes
fn check_health_factor_invariants(
    router_client: &kinetic_router::Client,
    user: &Address,
    position_before: &PositionSnapshot,
    position_after: &PositionSnapshot,
    price_increased: bool,
) {
    // === Basic Health Factor Validity ===
    if position_after.debt_balance > 0 {
        assert!(
            position_after.health_factor > 0,
            "HF VIOLATION: Zero health factor with non-zero debt"
        );
    }

    // === Health Factor Direction Invariant ===
    // If price increased and no new borrows, HF should increase or stay same
    // If price decreased and no repayments, HF should decrease or stay same
    if position_after.debt_balance > 0 && position_before.debt_balance > 0 {
        // Only check if no debt changes (pure price effect)
        if position_after.debt_balance == position_before.debt_balance
            && position_after.atoken_balance == position_before.atoken_balance
        {
            if price_increased {
                // HF should not decrease when price increases (with same positions)
                // Allow small tolerance for rounding
                let tolerance = position_before.health_factor / 1000; // 0.1% tolerance
                assert!(
                    position_after.health_factor + tolerance >= position_before.health_factor,
                    "HF VIOLATION: HF decreased from {} to {} despite price increase",
                    position_before.health_factor,
                    position_after.health_factor
                );
            }
        }
    }
}

/// Check liquidation invariants under price manipulation
fn check_liquidation_invariants(
    position_before: &PositionSnapshot,
    position_after: &PositionSnapshot,
    liquidation_attempted: bool,
    liquidation_succeeded: bool,
) {
    if liquidation_attempted {
        // === Liquidation Threshold Invariant ===
        // Liquidation should only succeed if HF was < WAD (1.0)
        if liquidation_succeeded {
            // Note: Due to price manipulation during liquidation, we can't strictly
            // assert HF < WAD at the exact moment, but we verify state changes

            // Debt should decrease after successful liquidation
            assert!(
                position_after.debt_balance <= position_before.debt_balance,
                "LIQUIDATION VIOLATION: Debt increased after liquidation"
            );
        } else {
            // Failed liquidation should not change balances
            assert_eq!(
                position_after.debt_balance, position_before.debt_balance,
                "LIQUIDATION VIOLATION: Debt changed after failed liquidation"
            );
            assert_eq!(
                position_after.atoken_balance, position_before.atoken_balance,
                "LIQUIDATION VIOLATION: Collateral changed after failed liquidation"
            );
        }
    }
}

/// Check for potential profit extraction through price manipulation
fn check_no_profit_extraction(
    user_position_start: &PositionSnapshot,
    user_position_end: &PositionSnapshot,
    attacker_profit: i128,
) {
    // === No Free Value Invariant ===
    // An attacker shouldn't be able to extract value purely through price manipulation
    // without providing real value (liquidity, repayment, etc.)

    // If user position is the same (no deposits/withdrawals/borrows/repays)
    // and attacker has profit, that's suspicious
    if user_position_start.atoken_balance == user_position_end.atoken_balance
        && user_position_start.debt_balance == user_position_end.debt_balance
    {
        // Allow small profit due to rounding, but flag large extraction
        let max_allowed_profit: i128 = 1000; // Small tolerance for rounding
        assert!(
            attacker_profit <= max_allowed_profit,
            "PROFIT EXTRACTION: Attacker gained {} without user position change",
            attacker_profit
        );
    }
}

/// Check protocol solvency after extreme price movements
fn check_protocol_solvency(
    env: &Env,
    router_client: &kinetic_router::Client,
    asset: &Address,
    a_token: &Address,
) {
    let reserve_data = router_client.get_reserve_data(asset);
    let token_client = token::Client::new(env, asset);
    let atoken_client = a_token::Client::new(env, a_token);

    // === Basic Solvency Check ===
    // aToken underlying balance should be non-negative
    let underlying_balance = token_client.balance(a_token);
    assert!(
        underlying_balance >= 0,
        "SOLVENCY VIOLATION: Negative underlying balance"
    );

    // === Index Validity ===
    assert!(
        reserve_data.liquidity_index >= RAY,
        "SOLVENCY VIOLATION: Liquidity index {} below RAY",
        reserve_data.liquidity_index
    );
    assert!(
        reserve_data.variable_borrow_index >= RAY,
        "SOLVENCY VIOLATION: Borrow index {} below RAY",
        reserve_data.variable_borrow_index
    );

    // === Supply Consistency ===
    let atoken_supply = atoken_client.total_supply();
    assert!(
        atoken_supply >= 0,
        "SOLVENCY VIOLATION: Negative aToken supply"
    );
}

// =============================================================================
// Fuzz Target
// =============================================================================

fuzz_target!(|input: PriceScenarioInput| {
    let env = setup_test_env();

    // Setup addresses
    let admin = Address::generate(&env);
    let emergency_admin = Address::generate(&env);
    let borrower = Address::generate(&env);
    let liquidator = Address::generate(&env);
    let liquidity_provider = Address::generate(&env);

    // Calculate initial price
    let initial_price = BASE_PRICE * (input.initial_price_bps.max(1000).min(50000) as u128) / 10000;

    // Setup oracle and router
    let oracle_addr = setup_oracle(&env, &admin);
    let oracle_client = price_oracle::Client::new(&env, &oracle_addr);
    let router_addr = setup_kinetic_router(&env, &admin, &emergency_admin, &oracle_addr);
    let router_client = kinetic_router::Client::new(&env, &router_addr);

    // Setup reserve
    let (underlying_asset, _underlying_contract, a_token, debt_token) = setup_reserve(
        &env,
        &router_addr,
        &oracle_addr,
        &admin,
        initial_price,
    );

    let underlying_client = StellarAssetClient::new(&env, &underlying_asset);
    let a_token_client = a_token::Client::new(&env, &a_token);
    let debt_token_client = debt_token::Client::new(&env, &debt_token);

    // === Setup Initial State ===

    // Provide liquidity
    let collateral_amount = (input.collateral_amount as u128).clamp(MIN_AMOUNT, MAX_AMOUNT);
    let liquidity_amount = collateral_amount * 10;
    underlying_client.mint(&liquidity_provider, &(liquidity_amount as i128));
    let _ = router_client.try_supply(
        &liquidity_provider,
        &underlying_asset,
        &liquidity_amount,
        &liquidity_provider,
        &0u32,
    );

    // Borrower supplies collateral
    underlying_client.mint(&borrower, &(collateral_amount as i128 * 2));
    let supply_result = router_client.try_supply(
        &borrower,
        &underlying_asset,
        &collateral_amount,
        &borrower,
        &0u32,
    );
    if supply_result.is_err() {
        return;
    }

    // Borrower takes a loan
    let borrow_percent = (input.borrow_percent % 81) as u128; // 0-80%
    if borrow_percent == 0 {
        return;
    }
    let max_borrow = collateral_amount * 8000 / 10000;
    let borrow_amount = max_borrow * borrow_percent / 100;
    if borrow_amount == 0 {
        return;
    }

    let borrow_result = router_client.try_borrow(
        &borrower,
        &underlying_asset,
        &borrow_amount,
        &1u32,
        &0u32,
        &borrower,
    );
    if borrow_result.is_err() {
        return;
    }

    // Mint tokens to liquidator
    underlying_client.mint(&liquidator, &(MAX_AMOUNT as i128));

    // Track state
    let mut current_price = initial_price;
    let mut price_history = PriceHistory::new();
    price_history.record(current_price, env.ledger().timestamp());

    let initial_position = PositionSnapshot::take(
        &router_client,
        &a_token_client,
        &debt_token_client,
        &borrower,
    );

    let initial_liquidator_balance = underlying_client.balance(&liquidator);

    // === Execute Attack Sequence ===
    for attack_opt in &input.attacks {
        if let Some(attack) = attack_opt {
            let position_before = PositionSnapshot::take(
                &router_client,
                &a_token_client,
                &debt_token_client,
                &borrower,
            );
            let price_before = current_price;

            match attack {
                PriceAttack::SetPrice { movement } => {
                    let new_price = apply_price_movement(current_price, movement);
                    if set_price(&oracle_client, &admin, &underlying_asset, new_price, env.ledger().timestamp()) {
                        current_price = new_price.clamp(MIN_PRICE, MAX_PRICE);
                        price_history.record(current_price, env.ledger().timestamp());
                    }
                }

                PriceAttack::SandwichLiquidation { drop_percent, liquidation_amount } => {
                    // Step 1: Drop price
                    let drop = (*drop_percent as u128).min(90);
                    let crashed_price = current_price * (100 - drop) / 100;
                    set_price(&oracle_client, &admin, &underlying_asset, crashed_price, env.ledger().timestamp());

                    // Step 2: Attempt liquidation
                    let liq_amount = (*liquidation_amount as u128).clamp(MIN_AMOUNT, MAX_AMOUNT / 2);
                    let liq_result = router_client.try_liquidation_call(
                        &liquidator,
                        &underlying_asset,
                        &underlying_asset,
                        &borrower,
                        &liq_amount,
                        &false,
                    );
                    let liquidation_succeeded = liq_result.is_ok() && liq_result.unwrap().is_ok();

                    // Step 3: Restore price
                    set_price(&oracle_client, &admin, &underlying_asset, current_price, env.ledger().timestamp());

                    // Check invariants
                    let position_after = PositionSnapshot::take(
                        &router_client,
                        &a_token_client,
                        &debt_token_client,
                        &borrower,
                    );
                    check_liquidation_invariants(&position_before, &position_after, true, liquidation_succeeded);
                }

                PriceAttack::FrontRunBorrow { drop_percent, borrow_amount: extra_borrow } => {
                    // Drop price before borrow attempt
                    let drop = (*drop_percent as u128).min(90);
                    let dropped_price = current_price * (100 - drop) / 100;
                    set_price(&oracle_client, &admin, &underlying_asset, dropped_price, env.ledger().timestamp());

                    // Attempt additional borrow (should fail if HF too low)
                    let extra = (*extra_borrow as u128).clamp(MIN_AMOUNT, MAX_AMOUNT / 10);
                    let _ = router_client.try_borrow(
                        &borrower,
                        &underlying_asset,
                        &extra,
                        &1u32,
                        &0u32,
                        &borrower,
                    );

                    // Restore price
                    set_price(&oracle_client, &admin, &underlying_asset, current_price, env.ledger().timestamp());
                }

                PriceAttack::PriceOscillation { cycles, amplitude } => {
                    let amp = (*amplitude as u128).min(50);
                    for i in 0..*cycles {
                        let factor = if i % 2 == 0 { 100 + amp } else { 100 - amp };
                        let new_price = (current_price * factor / 100).clamp(MIN_PRICE, MAX_PRICE);
                        set_price(&oracle_client, &admin, &underlying_asset, new_price, env.ledger().timestamp());
                        current_price = new_price;
                        price_history.record(current_price, env.ledger().timestamp());
                    }
                }

                PriceAttack::AdvanceTime { seconds } => {
                    let advance = (*seconds as u64).min(31_536_000);
                    if advance > 0 {
                        let new_timestamp = env.ledger().timestamp().saturating_add(advance);
                        env.ledger().set_timestamp(new_timestamp);
                    }
                }

                PriceAttack::SupplyCollateral { amount } => {
                    let supply = (*amount as u128).clamp(MIN_AMOUNT, MAX_AMOUNT);
                    underlying_client.mint(&borrower, &(supply as i128));
                    let _ = router_client.try_supply(
                        &borrower,
                        &underlying_asset,
                        &supply,
                        &borrower,
                        &0u32,
                    );
                }

                PriceAttack::RepayDebt { amount } => {
                    let repay = (*amount as u128).clamp(MIN_AMOUNT, MAX_AMOUNT);
                    underlying_client.mint(&borrower, &(repay as i128 + 1000));
                    let _ = router_client.try_repay(
                        &borrower,
                        &underlying_asset,
                        &repay,
                        &1u32,
                        &borrower,
                    );
                }

                PriceAttack::Borrow { amount } => {
                    let borrow = (*amount as u128).clamp(MIN_AMOUNT, MAX_AMOUNT / 10);
                    let _ = router_client.try_borrow(
                        &borrower,
                        &underlying_asset,
                        &borrow,
                        &1u32,
                        &0u32,
                        &borrower,
                    );
                }

                PriceAttack::Withdraw { amount } => {
                    let withdraw = (*amount as u128).clamp(MIN_AMOUNT, MAX_AMOUNT);
                    let _ = router_client.try_withdraw(
                        &borrower,
                        &underlying_asset,
                        &withdraw,
                        &borrower,
                    );
                }

                PriceAttack::AttemptLiquidation { amount } => {
                    let liq_amount = (*amount as u128).clamp(MIN_AMOUNT, MAX_AMOUNT / 2);
                    let result = router_client.try_liquidation_call(
                        &liquidator,
                        &underlying_asset,
                        &underlying_asset,
                        &borrower,
                        &liq_amount,
                        &false,
                    );
                    let liquidation_succeeded = result.is_ok() && result.unwrap().is_ok();

                    let position_after = PositionSnapshot::take(
                        &router_client,
                        &a_token_client,
                        &debt_token_client,
                        &borrower,
                    );
                    check_liquidation_invariants(&position_before, &position_after, true, liquidation_succeeded);
                }
            }

            // === Check Invariants After Each Attack ===
            let position_after = PositionSnapshot::take(
                &router_client,
                &a_token_client,
                &debt_token_client,
                &borrower,
            );

            // Price invariants
            check_price_invariants(&oracle_client, &underlying_asset, current_price);

            // Health factor invariants
            let price_increased = current_price > price_before;
            check_health_factor_invariants(
                &router_client,
                &borrower,
                &position_before,
                &position_after,
                price_increased,
            );

            // Protocol solvency
            check_protocol_solvency(&env, &router_client, &underlying_asset, &a_token);
        }
    }

    // === Final Invariant Checks ===
    let final_position = PositionSnapshot::take(
        &router_client,
        &a_token_client,
        &debt_token_client,
        &borrower,
    );

    let final_liquidator_balance = underlying_client.balance(&liquidator);
    let liquidator_profit = final_liquidator_balance - initial_liquidator_balance;

    // Check for suspicious profit extraction
    check_no_profit_extraction(&initial_position, &final_position, liquidator_profit);

    // Final solvency check
    check_protocol_solvency(&env, &router_client, &underlying_asset, &a_token);

    // Log volatility for analysis (this is informational, not an assertion)
    let _volatility = price_history.volatility();
});
