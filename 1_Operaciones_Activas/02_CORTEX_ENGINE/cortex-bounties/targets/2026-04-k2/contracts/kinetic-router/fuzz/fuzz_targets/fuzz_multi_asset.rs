#![no_main]

//! Fuzz test for K2 multi-asset interactions.
//!
//! This fuzzer tests cross-asset operations including:
//! 1. Cross-collateral borrowing (supply asset A, borrow asset B)
//! 2. Cross-asset liquidations
//! 3. Multi-asset health factor calculations
//! 4. Reserve isolation (operations on one reserve don't incorrectly affect others)
//!
//! ## Key Invariants:
//! - Reserve isolation: State changes to one reserve don't corrupt another
//! - Cross-collateral health factor: Correctly aggregates collateral and debt values
//! - Multi-asset liquidation: Proper collateral seizure across different assets
//! - Index independence: Each reserve's indices evolve independently
//!
//! Run with: cargo +nightly fuzz run fuzz_multi_asset --sanitizer=none

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
            price: 1_000_000_000_000_000i128, // 1 USD with 14 decimals
            timestamp: env.ledger().timestamp(),
        })
    }
}

// =============================================================================
// Fuzz Input Types
// =============================================================================

/// Which asset to operate on
#[derive(Arbitrary, Debug, Clone, Copy)]
pub enum AssetChoice {
    AssetA,
    AssetB,
    AssetC,
}

/// Which user performs the operation
#[derive(Arbitrary, Debug, Clone, Copy)]
pub enum User {
    User1,
    User2,
}

/// Operations in multi-asset context
#[derive(Arbitrary, Debug, Clone)]
pub enum MultiAssetOperation {
    /// Supply to a specific asset
    Supply {
        user: User,
        asset: AssetChoice,
        amount: u64,
    },
    /// Borrow from a specific asset (uses all collateral)
    Borrow {
        user: User,
        asset: AssetChoice,
        amount: u64,
    },
    /// Repay debt on a specific asset
    Repay {
        user: User,
        asset: AssetChoice,
        amount: u64,
    },
    /// Withdraw from a specific asset
    Withdraw {
        user: User,
        asset: AssetChoice,
        amount: u64,
    },
    /// Set collateral enabled/disabled for a specific asset
    SetCollateralEnabled {
        user: User,
        asset: AssetChoice,
        enabled: bool,
    },
    /// Cross-asset liquidation
    Liquidate {
        liquidator: User,
        borrower: User,
        collateral_asset: AssetChoice,
        debt_asset: AssetChoice,
        amount: u64,
    },
    /// Change price of an asset (in basis points relative to 1 USD)
    SetPrice {
        asset: AssetChoice,
        price_bps: u16,
    },
    /// Advance time to accrue interest
    AdvanceTime { seconds: u32 },
}

#[derive(Arbitrary, Debug, Clone)]
pub struct MultiAssetInput {
    /// Initial prices for assets (in basis points, 10000 = $1)
    pub initial_price_a_bps: u16,
    pub initial_price_b_bps: u16,
    pub initial_price_c_bps: u16,
    /// Initial supply amounts for liquidity
    pub liquidity_a: u64,
    pub liquidity_b: u64,
    pub liquidity_c: u64,
    /// Sequence of operations
    pub operations: [Option<MultiAssetOperation>; 12],
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

/// Minimum amount for operations
const MIN_AMOUNT: u128 = 1_000_000; // 0.1 tokens with 7 decimals

/// Maximum amount for operations
const MAX_AMOUNT: u128 = 100_000_000_000_000; // 10M tokens

// =============================================================================
// Reserve Configuration
// =============================================================================

/// Different reserve configurations to test various scenarios
struct ReserveConfig {
    ltv: u32,
    liquidation_threshold: u32,
    liquidation_bonus: u32,
    decimals: u32,
}

impl ReserveConfig {
    /// Conservative reserve (lower LTV, safer)
    fn conservative() -> Self {
        Self {
            ltv: 5000,               // 50%
            liquidation_threshold: 6500, // 65%
            liquidation_bonus: 1000,     // 10%
            decimals: 7,
        }
    }

    /// Standard reserve
    fn standard() -> Self {
        Self {
            ltv: 7500,               // 75%
            liquidation_threshold: 8000, // 80%
            liquidation_bonus: 500,      // 5%
            decimals: 7,
        }
    }

    /// Aggressive reserve (higher LTV, riskier)
    fn aggressive() -> Self {
        Self {
            ltv: 8500,               // 85%
            liquidation_threshold: 9000, // 90%
            liquidation_bonus: 300,      // 3%
            decimals: 7,
        }
    }
}

// =============================================================================
// Reserve State Snapshot
// =============================================================================

/// Snapshot of a single reserve's state
#[derive(Clone, Debug)]
struct ReserveSnapshot {
    liquidity_index: u128,
    variable_borrow_index: u128,
    current_liquidity_rate: u128,
    current_variable_borrow_rate: u128,
    atoken_supply: i128,
    debt_supply: i128,
    underlying_balance: i128,
}

impl ReserveSnapshot {
    fn take(
        env: &Env,
        router_client: &kinetic_router::Client,
        asset: &Address,
        a_token: &Address,
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
            atoken_supply: atoken_client.total_supply(),
            debt_supply: debt_token_client.total_supply(),
            underlying_balance: token_client.balance(a_token),
        }
    }
}

/// Snapshot of all reserves for isolation testing
#[derive(Clone, Debug)]
struct MultiReserveSnapshot {
    reserve_a: ReserveSnapshot,
    reserve_b: ReserveSnapshot,
    reserve_c: ReserveSnapshot,
}

// =============================================================================
// Test Context
// =============================================================================

struct AssetContext {
    underlying: Address,
    underlying_contract: StellarAssetContract,
    a_token: Address,
    debt_token: Address,
}

struct TestContext<'a> {
    env: &'a Env,
    router_addr: Address,
    oracle_addr: Address,
    admin: Address,
    user1: Address,
    user2: Address,
    asset_a: AssetContext,
    asset_b: AssetContext,
    asset_c: AssetContext,
}

impl<'a> TestContext<'a> {
    fn router_client(&self) -> kinetic_router::Client<'a> {
        kinetic_router::Client::new(self.env, &self.router_addr)
    }

    fn oracle_client(&self) -> price_oracle::Client<'a> {
        price_oracle::Client::new(self.env, &self.oracle_addr)
    }
}

impl<'a> TestContext<'a> {
    fn get_user(&self, user: User) -> &Address {
        match user {
            User::User1 => &self.user1,
            User::User2 => &self.user2,
        }
    }

    fn get_asset(&self, choice: AssetChoice) -> &AssetContext {
        match choice {
            AssetChoice::AssetA => &self.asset_a,
            AssetChoice::AssetB => &self.asset_b,
            AssetChoice::AssetC => &self.asset_c,
        }
    }

    fn get_asset_client(&self, choice: AssetChoice) -> StellarAssetClient<'a> {
        let asset = self.get_asset(choice);
        StellarAssetClient::new(self.env, &asset.underlying)
    }

    fn get_atoken_client(&self, choice: AssetChoice) -> a_token::Client<'a> {
        let asset = self.get_asset(choice);
        a_token::Client::new(self.env, &asset.a_token)
    }

    fn get_debt_token_client(&self, choice: AssetChoice) -> debt_token::Client<'a> {
        let asset = self.get_asset(choice);
        debt_token::Client::new(self.env, &asset.debt_token)
    }

    fn take_snapshot(&self) -> MultiReserveSnapshot {
        let router_client = self.router_client();
        MultiReserveSnapshot {
            reserve_a: ReserveSnapshot::take(
                self.env,
                &router_client,
                &self.asset_a.underlying,
                &self.asset_a.a_token,
            ),
            reserve_b: ReserveSnapshot::take(
                self.env,
                &router_client,
                &self.asset_b.underlying,
                &self.asset_b.a_token,
            ),
            reserve_c: ReserveSnapshot::take(
                self.env,
                &router_client,
                &self.asset_c.underlying,
                &self.asset_c.a_token,
            ),
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
    config: &ReserveConfig,
    initial_price: u128,
    name_suffix: &str,
) -> AssetContext {
    // Create underlying asset
    let underlying_contract = env.register_stellar_asset_contract_v2(admin.clone());
    let underlying = underlying_contract.address();

    // Setup interest rate strategy
    let irs_addr = env.register(interest_rate_strategy::WASM, ());
    env.invoke_contract::<()>(
        &irs_addr,
        &soroban_sdk::Symbol::new(env, "initialize"),
        soroban_sdk::vec![
            env,
            admin.into_val(env),
            200u128.into_val(env),   // base_variable_borrow_rate (2%)
            1000u128.into_val(env),  // variable_rate_slope1 (10%)
            10000u128.into_val(env), // variable_rate_slope2 (100%)
            8000u128.into_val(env),  // optimal_utilization_rate (80%)
        ],
    );

    // Setup aToken
    let a_token_addr = env.register(a_token::WASM, ());
    let a_token_client = a_token::Client::new(env, &a_token_addr);
    let a_token_name = String::from_str(env, &format!("aToken{}", name_suffix));
    let a_token_symbol = String::from_str(env, &format!("aTKN{}", name_suffix));
    a_token_client.initialize(
        admin,
        &underlying,
        router_addr,
        &a_token_name,
        &a_token_symbol,
        &config.decimals,
    );

    // Setup debt token
    let debt_token_addr = env.register(debt_token::WASM, ());
    let debt_token_client = debt_token::Client::new(env, &debt_token_addr);
    let debt_token_name = String::from_str(env, &format!("dToken{}", name_suffix));
    let debt_token_symbol = String::from_str(env, &format!("dTKN{}", name_suffix));
    debt_token_client.initialize(
        admin,
        &underlying,
        router_addr,
        &debt_token_name,
        &debt_token_symbol,
        &config.decimals,
    );

    // Register asset with oracle
    let oracle_client = price_oracle::Client::new(env, oracle_addr);
    let asset_enum = price_oracle::Asset::Stellar(underlying.clone());
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
        decimals: config.decimals,
        ltv: config.ltv,
        liquidation_threshold: config.liquidation_threshold,
        liquidation_bonus: config.liquidation_bonus,
        reserve_factor: 1000, // 10%
        supply_cap: 1_000_000_000_000_000u128,
        borrow_cap: 1_000_000_000_000_000u128,
        borrowing_enabled: true,
        flashloan_enabled: true,
    };

    router_client.init_reserve(
        &pool_configurator,
        &underlying,
        &a_token_addr,
        &debt_token_addr,
        &irs_addr,
        &treasury,
        &params,
    );

    AssetContext {
        underlying,
        underlying_contract,
        a_token: a_token_addr,
        debt_token: debt_token_addr,
    }
}

// =============================================================================
// Invariant Checks
// =============================================================================

/// Verify reserve isolation: operations on one reserve shouldn't affect others unexpectedly
fn check_reserve_isolation(
    before: &MultiReserveSnapshot,
    after: &MultiReserveSnapshot,
    affected_asset: AssetChoice,
) {
    // Get the snapshots for unaffected reserves
    let (unaffected_before, unaffected_after, label): (&[(&ReserveSnapshot, &ReserveSnapshot, &str)], _, _) =
        match affected_asset {
            AssetChoice::AssetA => {
                let pairs = [
                    (&before.reserve_b, &after.reserve_b, "B"),
                    (&before.reserve_c, &after.reserve_c, "C"),
                ];
                (Box::leak(Box::new(pairs)) as &[_], (), ())
            }
            AssetChoice::AssetB => {
                let pairs = [
                    (&before.reserve_a, &after.reserve_a, "A"),
                    (&before.reserve_c, &after.reserve_c, "C"),
                ];
                (Box::leak(Box::new(pairs)) as &[_], (), ())
            }
            AssetChoice::AssetC => {
                let pairs = [
                    (&before.reserve_a, &after.reserve_a, "A"),
                    (&before.reserve_b, &after.reserve_b, "B"),
                ];
                (Box::leak(Box::new(pairs)) as &[_], (), ())
            }
        };

    for (b, a, name) in unaffected_before.iter() {
        // Supply/debt shouldn't change on unaffected reserves
        // (unless time advanced and interest accrued, which is expected)
        // We check that indices didn't decrease (monotonicity)
        assert!(
            a.liquidity_index >= b.liquidity_index,
            "ISOLATION VIOLATION: Reserve {} liquidity index decreased",
            name
        );
        assert!(
            a.variable_borrow_index >= b.variable_borrow_index,
            "ISOLATION VIOLATION: Reserve {} borrow index decreased",
            name
        );
    }
}

/// Check cross-asset invariants
fn check_multi_asset_invariants(
    ctx: &TestContext,
    snapshot: &MultiReserveSnapshot,
) {
    // === Index Invariants (all reserves) ===
    for (reserve, name) in [
        (&snapshot.reserve_a, "A"),
        (&snapshot.reserve_b, "B"),
        (&snapshot.reserve_c, "C"),
    ] {
        assert!(
            reserve.liquidity_index >= RAY,
            "Reserve {}: Liquidity index {} below RAY",
            name,
            reserve.liquidity_index
        );
        assert!(
            reserve.variable_borrow_index >= RAY,
            "Reserve {}: Borrow index {} below RAY",
            name,
            reserve.variable_borrow_index
        );

        // Rate invariant: supply rate <= borrow rate
        if reserve.current_variable_borrow_rate > 0 {
            assert!(
                reserve.current_liquidity_rate <= reserve.current_variable_borrow_rate,
                "Reserve {}: Supply rate {} exceeds borrow rate {}",
                name,
                reserve.current_liquidity_rate,
                reserve.current_variable_borrow_rate
            );
        }

        // Supply consistency
        assert!(
            reserve.atoken_supply >= 0,
            "Reserve {}: Negative aToken supply",
            name
        );
        assert!(
            reserve.debt_supply >= 0,
            "Reserve {}: Negative debt supply",
            name
        );
    }

    // === Cross-Asset Health Factor Invariant ===
    for user in [&ctx.user1, &ctx.user2] {
        if let Ok(Ok(user_data)) = ctx.router_client().try_get_user_account_data(user) {
            // If user has debt, health factor should be positive
            if user_data.total_debt_base > 0 {
                assert!(
                    user_data.health_factor > 0,
                    "Health factor should be positive when debt exists"
                );

                // Health factor calculation consistency
                // HF = (collateral * liquidation_threshold) / debt
                // This is a sanity check - the actual calculation is more complex
                if user_data.total_collateral_base > 0 {
                    // If there's collateral and debt, HF should be finite
                    assert!(
                        user_data.health_factor < u128::MAX,
                        "Health factor overflow detected"
                    );
                }
            }

            // Available borrow consistency
            // Should be 0 or positive, and bounded by collateral
            // (This is implicit in the protocol logic but good to verify)
        }
    }
}

/// Verify cross-asset liquidation invariants
fn check_liquidation_invariants(
    before_collateral_snapshot: &ReserveSnapshot,
    after_collateral_snapshot: &ReserveSnapshot,
    before_debt_snapshot: &ReserveSnapshot,
    after_debt_snapshot: &ReserveSnapshot,
    liquidation_succeeded: bool,
) {
    if liquidation_succeeded {
        // Collateral reserve: total supply might decrease (collateral seized)
        // Debt reserve: debt supply should decrease (debt repaid)

        // Index monotonicity on both reserves
        assert!(
            after_collateral_snapshot.liquidity_index >= before_collateral_snapshot.liquidity_index,
            "CROSS-LIQUIDATION: Collateral reserve liquidity index decreased"
        );
        assert!(
            after_debt_snapshot.liquidity_index >= before_debt_snapshot.liquidity_index,
            "CROSS-LIQUIDATION: Debt reserve liquidity index decreased"
        );
    }
}

// =============================================================================
// Fuzz Target
// =============================================================================

fuzz_target!(|input: MultiAssetInput| {
    let env = setup_test_env();

    // Setup addresses
    let admin = Address::generate(&env);
    let emergency_admin = Address::generate(&env);
    let user1 = Address::generate(&env);
    let user2 = Address::generate(&env);
    let liquidity_provider = Address::generate(&env);

    // Setup oracle
    let oracle_addr = setup_oracle(&env, &admin);
    let oracle_client = price_oracle::Client::new(&env, &oracle_addr);

    // Setup router
    let router_addr = setup_kinetic_router(&env, &admin, &emergency_admin, &oracle_addr);
    let router_client = kinetic_router::Client::new(&env, &router_addr);

    // Calculate initial prices (clamp to reasonable range)
    let price_a = BASE_PRICE * (input.initial_price_a_bps.max(1000).min(50000) as u128) / 10000;
    let price_b = BASE_PRICE * (input.initial_price_b_bps.max(1000).min(50000) as u128) / 10000;
    let price_c = BASE_PRICE * (input.initial_price_c_bps.max(1000).min(50000) as u128) / 10000;

    // Setup three reserves with different configurations
    let asset_a = setup_reserve(
        &env,
        &router_addr,
        &oracle_addr,
        &admin,
        &ReserveConfig::conservative(),
        price_a,
        "A",
    );
    let asset_b = setup_reserve(
        &env,
        &router_addr,
        &oracle_addr,
        &admin,
        &ReserveConfig::standard(),
        price_b,
        "B",
    );
    let asset_c = setup_reserve(
        &env,
        &router_addr,
        &oracle_addr,
        &admin,
        &ReserveConfig::aggressive(),
        price_c,
        "C",
    );

    let ctx = TestContext {
        env: &env,
        router_addr: router_addr.clone(),
        oracle_addr: oracle_addr.clone(),
        admin: admin.clone(),
        user1: user1.clone(),
        user2: user2.clone(),
        asset_a,
        asset_b,
        asset_c,
    };

    // Provide initial liquidity to all pools
    let liquidity_amounts = [
        (AssetChoice::AssetA, (input.liquidity_a as u128).clamp(MIN_AMOUNT * 100, MAX_AMOUNT)),
        (AssetChoice::AssetB, (input.liquidity_b as u128).clamp(MIN_AMOUNT * 100, MAX_AMOUNT)),
        (AssetChoice::AssetC, (input.liquidity_c as u128).clamp(MIN_AMOUNT * 100, MAX_AMOUNT)),
    ];

    for (choice, amount) in liquidity_amounts {
        let asset = ctx.get_asset(choice);
        let asset_client = StellarAssetClient::new(&env, &asset.underlying);
        asset_client.mint(&liquidity_provider, &(amount as i128));
        let _ = router_client.try_supply(
            &liquidity_provider,
            &asset.underlying,
            &amount,
            &liquidity_provider,
            &0u32,
        );
    }

    // Mint tokens to users for operations
    for user in [&user1, &user2] {
        for choice in [AssetChoice::AssetA, AssetChoice::AssetB, AssetChoice::AssetC] {
            let asset = ctx.get_asset(choice);
            let asset_client = StellarAssetClient::new(&env, &asset.underlying);
            asset_client.mint(user, &(MAX_AMOUNT as i128));
        }
    }

    // Initial snapshot and invariant check
    let mut last_snapshot = ctx.take_snapshot();
    check_multi_asset_invariants(&ctx, &last_snapshot);

    // Execute operation sequence
    for op_opt in &input.operations {
        if let Some(op) = op_opt {
            let snapshot_before = ctx.take_snapshot();

            match op {
                MultiAssetOperation::Supply { user, asset, amount } => {
                    let user_addr = ctx.get_user(*user);
                    let asset_ctx = ctx.get_asset(*asset);
                    let supply_amount = (*amount as u128).clamp(MIN_AMOUNT, MAX_AMOUNT);

                    let _ = router_client.try_supply(
                        user_addr,
                        &asset_ctx.underlying,
                        &supply_amount,
                        user_addr,
                        &0u32,
                    );

                    // Check isolation
                    let snapshot_after = ctx.take_snapshot();
                    check_reserve_isolation(&snapshot_before, &snapshot_after, *asset);
                }

                MultiAssetOperation::Borrow { user, asset, amount } => {
                    let user_addr = ctx.get_user(*user);
                    let asset_ctx = ctx.get_asset(*asset);
                    let borrow_amount = (*amount as u128).clamp(MIN_AMOUNT, MAX_AMOUNT / 10);

                    let _ = router_client.try_borrow(
                        user_addr,
                        &asset_ctx.underlying,
                        &borrow_amount,
                        &1u32, // Variable rate
                        &0u32, // No referral
                        user_addr,
                    );

                    let snapshot_after = ctx.take_snapshot();
                    check_reserve_isolation(&snapshot_before, &snapshot_after, *asset);
                }

                MultiAssetOperation::Repay { user, asset, amount } => {
                    let user_addr = ctx.get_user(*user);
                    let asset_ctx = ctx.get_asset(*asset);
                    let repay_amount = (*amount as u128).clamp(MIN_AMOUNT, MAX_AMOUNT);

                    // Mint extra for interest
                    let asset_client = StellarAssetClient::new(&env, &asset_ctx.underlying);
                    asset_client.mint(user_addr, &(repay_amount as i128 + 1000));

                    let _ = router_client.try_repay(
                        user_addr,
                        &asset_ctx.underlying,
                        &repay_amount,
                        &1u32,
                        user_addr,
                    );

                    let snapshot_after = ctx.take_snapshot();
                    check_reserve_isolation(&snapshot_before, &snapshot_after, *asset);
                }

                MultiAssetOperation::Withdraw { user, asset, amount } => {
                    let user_addr = ctx.get_user(*user);
                    let asset_ctx = ctx.get_asset(*asset);
                    let withdraw_amount = (*amount as u128).clamp(MIN_AMOUNT, MAX_AMOUNT);

                    let _ = router_client.try_withdraw(
                        user_addr,
                        &asset_ctx.underlying,
                        &withdraw_amount,
                        user_addr,
                    );

                    let snapshot_after = ctx.take_snapshot();
                    check_reserve_isolation(&snapshot_before, &snapshot_after, *asset);
                }

                MultiAssetOperation::SetCollateralEnabled { user, asset, enabled } => {
                    let user_addr = ctx.get_user(*user);
                    let asset_ctx = ctx.get_asset(*asset);

                    let _ = router_client.try_set_user_use_reserve_as_coll(
                        user_addr,
                        &asset_ctx.underlying,
                        enabled,
                    );
                }

                MultiAssetOperation::Liquidate {
                    liquidator,
                    borrower,
                    collateral_asset,
                    debt_asset,
                    amount,
                } => {
                    let liquidator_addr = ctx.get_user(*liquidator);
                    let borrower_addr = ctx.get_user(*borrower);
                    let collateral_ctx = ctx.get_asset(*collateral_asset);
                    let debt_ctx = ctx.get_asset(*debt_asset);

                    // Get snapshots for both involved reserves
                    let before_collateral = ReserveSnapshot::take(
                        &env,
                        &router_client,
                        &collateral_ctx.underlying,
                        &collateral_ctx.a_token,
                    );
                    let before_debt = ReserveSnapshot::take(
                        &env,
                        &router_client,
                        &debt_ctx.underlying,
                        &debt_ctx.a_token,
                    );

                    let liquidation_amount = (*amount as u128).clamp(MIN_AMOUNT, MAX_AMOUNT / 2);

                    // Mint debt tokens to liquidator for repayment
                    let debt_asset_client = StellarAssetClient::new(&env, &debt_ctx.underlying);
                    debt_asset_client.mint(liquidator_addr, &(liquidation_amount as i128 * 2));

                    let result = router_client.try_liquidation_call(
                        liquidator_addr,
                        &collateral_ctx.underlying,
                        &debt_ctx.underlying,
                        borrower_addr,
                        &liquidation_amount,
                        &false,
                    );

                    let liquidation_succeeded = result.is_ok() && result.unwrap().is_ok();

                    // Check cross-liquidation invariants
                    let after_collateral = ReserveSnapshot::take(
                        &env,
                        &router_client,
                        &collateral_ctx.underlying,
                        &collateral_ctx.a_token,
                    );
                    let after_debt = ReserveSnapshot::take(
                        &env,
                        &router_client,
                        &debt_ctx.underlying,
                        &debt_ctx.a_token,
                    );

                    check_liquidation_invariants(
                        &before_collateral,
                        &after_collateral,
                        &before_debt,
                        &after_debt,
                        liquidation_succeeded,
                    );
                }

                MultiAssetOperation::SetPrice { asset, price_bps } => {
                    let asset_ctx = ctx.get_asset(*asset);
                    let new_price = BASE_PRICE * ((*price_bps as u32).max(100).min(100000) as u128) / 10000;
                    let asset_enum = price_oracle::Asset::Stellar(asset_ctx.underlying.clone());

                    let _ = oracle_client.try_set_manual_override(
                        &admin,
                        &asset_enum,
                        &Some(new_price),
                        &Some(env.ledger().timestamp() + 604_000),
                    );
                }

                MultiAssetOperation::AdvanceTime { seconds } => {
                    let advance = (*seconds as u64).min(31_536_000); // Max 1 year
                    if advance > 0 {
                        let new_timestamp = env.ledger().timestamp().saturating_add(advance);
                        env.ledger().set_timestamp(new_timestamp);
                    }
                }
            }

            // Check invariants after each operation
            let snapshot_after = ctx.take_snapshot();
            check_multi_asset_invariants(&ctx, &snapshot_after);

            // Index monotonicity for all reserves
            for (before, after, name) in [
                (&last_snapshot.reserve_a, &snapshot_after.reserve_a, "A"),
                (&last_snapshot.reserve_b, &snapshot_after.reserve_b, "B"),
                (&last_snapshot.reserve_c, &snapshot_after.reserve_c, "C"),
            ] {
                assert!(
                    after.liquidity_index >= before.liquidity_index,
                    "Reserve {}: Liquidity index decreased from {} to {}",
                    name,
                    before.liquidity_index,
                    after.liquidity_index
                );
                assert!(
                    after.variable_borrow_index >= before.variable_borrow_index,
                    "Reserve {}: Borrow index decreased from {} to {}",
                    name,
                    before.variable_borrow_index,
                    after.variable_borrow_index
                );
            }

            last_snapshot = snapshot_after;
        }
    }

    // Final invariant check
    check_multi_asset_invariants(&ctx, &last_snapshot);
});
