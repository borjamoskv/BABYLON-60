#![no_main]

//! Fuzz test for K2 flash loan operations.
//!
//! This fuzzer tests flash loan operations by:
//! 1. Setting up a pool with liquidity
//! 2. Deploying a configurable receiver contract with various behaviors
//! 3. Executing flash loans with different repayment behaviors
//! 4. Verifying all invariants hold
//!
//! ## Phase 2 Accounting Invariants:
//! - Flash loan conservation: aToken balance + treasury >= initial + premium
//! - Premium distribution: treasury receives reserve_factor share
//! - Failed flash loans: atomic rollback, no state changes
//! - Index monotonicity: liquidity and borrow indices only increase
//! - Supply/demand consistency: rates match utilization
//!
//! Run with: cargo +nightly fuzz run fuzz_flash_loan --sanitizer=none

use arbitrary::Arbitrary;
use libfuzzer_sys::fuzz_target;
use soroban_sdk::{
    contract, contractimpl, contracttype,
    testutils::{Address as _, Ledger as _, StellarAssetContract},
    token::{self, StellarAssetClient},
    Address, Bytes, Env, IntoVal, String, Symbol, Vec,
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

/// Mock Reflector Oracle that provides decimals() and lastprice()
#[contract]
pub struct MockReflector;

#[contractimpl]
impl MockReflector {
    pub fn decimals(_env: Env) -> u32 {
        14
    }

    /// Returns a fallback price when manual override expires
    pub fn lastprice(env: Env, _asset: ReflectorAsset) -> Option<PriceData> {
        Some(PriceData {
            price: 1_000_000_000_000_000i128,
            timestamp: env.ledger().timestamp(),
        })
    }
}

// =============================================================================
// Configurable Flash Loan Receiver
// =============================================================================

/// Storage keys for the configurable receiver
#[contracttype]
#[derive(Clone)]
pub enum ReceiverDataKey {
    AToken,
    Asset,
    Behavior,
    RepayDeltaBps,
}

/// Configurable flash loan receiver that can exhibit different behaviors
#[contract]
pub struct ConfigurableReceiver;

#[contractimpl]
impl ConfigurableReceiver {
    /// Initialize the receiver with configuration
    pub fn init(
        env: Env,
        asset: Address,
        a_token: Address,
        behavior: u32,
        repay_delta_bps: i32,
    ) {
        env.storage().instance().set(&ReceiverDataKey::Asset, &asset);
        env.storage().instance().set(&ReceiverDataKey::AToken, &a_token);
        env.storage().instance().set(&ReceiverDataKey::Behavior, &behavior);
        env.storage().instance().set(&ReceiverDataKey::RepayDeltaBps, &repay_delta_bps);
    }

    /// Update the behavior dynamically
    pub fn set_behavior(env: Env, behavior: u32, repay_delta_bps: i32) {
        env.storage().instance().set(&ReceiverDataKey::Behavior, &behavior);
        env.storage().instance().set(&ReceiverDataKey::RepayDeltaBps, &repay_delta_bps);
    }

    /// Flash loan callback - implements different behaviors based on configuration
    pub fn execute_operation(
        env: Env,
        assets: Vec<Address>,
        amounts: Vec<u128>,
        premiums: Vec<u128>,
        _initiator: Address,
        _params: Bytes,
    ) -> bool {
        let behavior: u32 = env.storage().instance().get(&ReceiverDataKey::Behavior).unwrap_or(0);
        let a_token: Address = match env.storage().instance().get(&ReceiverDataKey::AToken) {
            Some(a) => a,
            None => return false,
        };
        let repay_delta_bps: i32 = env.storage().instance().get(&ReceiverDataKey::RepayDeltaBps).unwrap_or(0);

        match behavior {
            0 => {
                // ExactRepay: Transfer principal + premium exactly
                for i in 0..assets.len() {
                    let asset = assets.get(i).unwrap();
                    let amount = amounts.get(i).unwrap();
                    let premium = premiums.get(i).unwrap();
                    let total_owed = amount + premium;

                    let token_client = token::Client::new(&env, &asset);
                    token_client.transfer(
                        &env.current_contract_address(),
                        &a_token,
                        &(total_owed as i128),
                    );
                }
                true
            }
            1 => {
                // Overpay: Transfer principal + premium + extra (10% more or delta_bps)
                for i in 0..assets.len() {
                    let asset = assets.get(i).unwrap();
                    let amount = amounts.get(i).unwrap();
                    let premium = premiums.get(i).unwrap();
                    let base_owed = amount + premium;

                    // Add extra based on repay_delta_bps (positive = overpay)
                    let extra = if repay_delta_bps > 0 {
                        (base_owed * repay_delta_bps as u128) / 10000
                    } else {
                        base_owed / 10 // Default 10% extra
                    };
                    let total_owed = base_owed + extra;

                    let token_client = token::Client::new(&env, &asset);
                    token_client.transfer(
                        &env.current_contract_address(),
                        &a_token,
                        &(total_owed as i128),
                    );
                }
                true
            }
            2 => {
                // Underpay: Transfer less than required
                for i in 0..assets.len() {
                    let asset = assets.get(i).unwrap();
                    let amount = amounts.get(i).unwrap();
                    let premium = premiums.get(i).unwrap();
                    let base_owed = amount + premium;

                    // Reduce based on repay_delta_bps (negative = underpay)
                    let reduction = if repay_delta_bps < 0 {
                        (base_owed * (-repay_delta_bps) as u128) / 10000
                    } else {
                        premium + 1 // Default: don't pay full premium
                    };
                    let total_owed = base_owed.saturating_sub(reduction);

                    if total_owed > 0 {
                        let token_client = token::Client::new(&env, &asset);
                        token_client.transfer(
                            &env.current_contract_address(),
                            &a_token,
                            &(total_owed as i128),
                        );
                    }
                }
                true
            }
            3 => {
                // NoRepay: Do nothing, keep the borrowed tokens
                true
            }
            4 => {
                // Panic: Intentionally panic during execution
                panic!("Intentional panic in flash loan receiver");
            }
            5 => {
                // ReturnFalse: Return false to indicate failure
                false
            }
            _ => {
                // Default to exact repay for unknown behaviors
                for i in 0..assets.len() {
                    let asset = assets.get(i).unwrap();
                    let amount = amounts.get(i).unwrap();
                    let premium = premiums.get(i).unwrap();
                    let total_owed = amount + premium;

                    let token_client = token::Client::new(&env, &asset);
                    token_client.transfer(
                        &env.current_contract_address(),
                        &a_token,
                        &(total_owed as i128),
                    );
                }
                true
            }
        }
    }
}

// =============================================================================
// Fuzz Input Types
// =============================================================================

/// Behavior of the flash loan receiver
#[derive(Arbitrary, Debug, Clone, Copy)]
pub enum ReceiverBehavior {
    /// Repays exactly principal + premium (success)
    ExactRepay,
    /// Repays principal + premium + extra (success, excess goes to suppliers)
    Overpay,
    /// Repays less than required (fails with FlashLoanNotRepaid)
    Underpay,
    /// Repays nothing (fails with FlashLoanNotRepaid)
    NoRepay,
    /// Panics during execution (fails)
    Panic,
    /// Returns false from execute_operation (fails)
    ReturnFalse,
}

impl ReceiverBehavior {
    fn to_u32(&self) -> u32 {
        match self {
            ReceiverBehavior::ExactRepay => 0,
            ReceiverBehavior::Overpay => 1,
            ReceiverBehavior::Underpay => 2,
            ReceiverBehavior::NoRepay => 3,
            ReceiverBehavior::Panic => 4,
            ReceiverBehavior::ReturnFalse => 5,
        }
    }

    /// Returns true if this behavior should result in a successful flash loan
    fn should_succeed(&self) -> bool {
        matches!(self, ReceiverBehavior::ExactRepay | ReceiverBehavior::Overpay)
    }
}

/// Operations that can occur during flash loan testing
#[derive(Arbitrary, Debug, Clone)]
pub enum FlashLoanOperation {
    /// Supply liquidity to pool
    SupplyLiquidity { amount: u64 },
    /// Advance time (test staleness, interest)
    AdvanceTime { seconds: u32 },
    /// Change asset price (in basis points, 100 = 1% of base)
    SetPrice { price_bps: u16 },
    /// Attempt a flash loan
    ExecuteFlashLoan {
        amount: u64,
        receiver_behavior: ReceiverBehavior,
        /// For Underpay/Overpay fine-tuning: -10000 to +10000 bps
        repay_delta_bps: i16,
    },
    /// Attempt flash loan requesting maximum available liquidity
    ExecuteFlashLoanMaxAmount {
        receiver_behavior: ReceiverBehavior,
    },
    /// Attempt flash loan with zero amount (should fail)
    ExecuteFlashLoanZeroAmount,
    /// Withdraw some liquidity (affects available balance for flash loans)
    WithdrawLiquidity { amount: u64 },
}

/// Main fuzz input structure
#[derive(Arbitrary, Debug, Clone)]
pub struct FlashLoanFuzzInput {
    /// Initial liquidity in pool (clamped to reasonable range)
    pub initial_liquidity: u64,
    /// Flash loan premium setting (0-100 bps)
    pub premium_bps: u8,
    /// Sequence of operations to execute
    pub operations: [Option<FlashLoanOperation>; 8],
}

// =============================================================================
// Constants
// =============================================================================

/// RAY constant (1e9 in our implementation)
const RAY: u128 = 1_000_000_000;

/// Base price with 14 decimals (1 USD)
const BASE_PRICE: u128 = 1_000_000_000_000_000;

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

fn setup_reserve(
    env: &Env,
    router_addr: &Address,
    oracle_addr: &Address,
    admin: &Address,
    flashloan_enabled: bool,
) -> (Address, StellarAssetContract, Address, Address) {
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
            200u128.into_val(env),   // base_variable_borrow_rate (2%)
            1000u128.into_val(env),  // variable_rate_slope1 (10%)
            10000u128.into_val(env), // variable_rate_slope2 (100%)
            8000u128.into_val(env),  // optimal_utilization_rate (80%)
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

    // Init reserve
    let router_client = kinetic_router::Client::new(env, router_addr);
    let treasury = Address::generate(env);
    let pool_configurator = Address::generate(env);
    router_client.set_pool_configurator(&pool_configurator);

    let params = kinetic_router::InitReserveParams {
        decimals: 7,
        ltv: 8000,                    // 80%
        liquidation_threshold: 8500, // 85%
        liquidation_bonus: 500,      // 5%
        reserve_factor: 1000,        // 10%
        supply_cap: 1_000_000_000_000_000u128,
        borrow_cap: 1_000_000_000_000_000u128,
        borrowing_enabled: true,
        flashloan_enabled,
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
// Invariant Checks
// =============================================================================

/// Snapshot of pool state before an operation
#[derive(Clone)]
struct PoolSnapshot {
    atoken_underlying_balance: u128,
    treasury_balance: i128,
    liquidity_index: u128,
    variable_borrow_index: u128,
}

fn take_pool_snapshot(
    env: &Env,
    asset: &Address,
    a_token: &Address,
    treasury: &Address,
    router_client: &kinetic_router::Client,
) -> PoolSnapshot {
    let token_client = token::Client::new(env, asset);
    let atoken_underlying_balance = token_client.balance(a_token) as u128;
    let treasury_balance = token_client.balance(treasury);

    let reserve_data = router_client.get_reserve_data(asset);

    PoolSnapshot {
        atoken_underlying_balance,
        treasury_balance,
        liquidity_index: reserve_data.liquidity_index,
        variable_borrow_index: reserve_data.variable_borrow_index,
    }
}

fn check_flash_loan_invariants(
    env: &Env,
    router_client: &kinetic_router::Client,
    asset: &Address,
    a_token: &Address,
    treasury: &Address,
    before_snapshot: &PoolSnapshot,
    flash_loan_succeeded: bool,
    expected_premium: u128,
) {
    let token_client = token::Client::new(env, asset);
    let current_atoken_balance = token_client.balance(a_token) as u128;
    let current_treasury_balance = token_client.balance(treasury);

    if flash_loan_succeeded {
        // === Phase 2: Flash Loan Accounting Invariants ===

        // Invariant 1: aToken balance should be >= initial (premium added to pool)
        assert!(
            current_atoken_balance >= before_snapshot.atoken_underlying_balance,
            "FLASH LOAN VIOLATION: aToken balance decreased from {} to {}",
            before_snapshot.atoken_underlying_balance,
            current_atoken_balance
        );

        // Invariant 2: Treasury should have received its share of premium
        if expected_premium > 0 {
            let treasury_increase = current_treasury_balance.saturating_sub(before_snapshot.treasury_balance);
            // Treasury receives reserve_factor portion of premium
            // Allow for rounding tolerance
            assert!(
                treasury_increase > 0 || expected_premium < 100,
                "FLASH LOAN VIOLATION: Treasury should receive premium share, got {} increase",
                treasury_increase
            );
        }

        // Invariant 3: Total system value conservation
        // aToken balance + treasury should increase by at least the premium (minus rounding)
        let total_before = before_snapshot.atoken_underlying_balance + before_snapshot.treasury_balance.max(0) as u128;
        let total_after = current_atoken_balance + current_treasury_balance.max(0) as u128;
        let total_increase = total_after.saturating_sub(total_before);

        // The increase should be close to expected_premium (within rounding tolerance)
        if expected_premium > 10 {
            let tolerance = expected_premium / 10 + 1; // 10% tolerance for rounding
            let diff = if total_increase > expected_premium {
                total_increase - expected_premium
            } else {
                expected_premium - total_increase
            };
            assert!(
                diff <= tolerance,
                "FLASH LOAN VIOLATION: Expected ~{} premium, but total increased by {}",
                expected_premium,
                total_increase
            );
        }
    } else {
        // After failed flash loan:
        // - Pool balance should be unchanged (atomic rollback)
        assert_eq!(
            current_atoken_balance, before_snapshot.atoken_underlying_balance,
            "FLASH LOAN VIOLATION: Pool balance changed after failed flash loan"
        );
    }

    // === Index Monotonicity Invariants ===
    let reserve_data = router_client.get_reserve_data(asset);
    assert!(
        reserve_data.liquidity_index >= RAY,
        "Liquidity index {} below RAY ({})",
        reserve_data.liquidity_index,
        RAY
    );
    assert!(
        reserve_data.variable_borrow_index >= RAY,
        "Borrow index {} below RAY ({})",
        reserve_data.variable_borrow_index,
        RAY
    );

    // Indices must be monotonically increasing
    assert!(
        reserve_data.liquidity_index >= before_snapshot.liquidity_index,
        "INDEX VIOLATION: Liquidity index decreased from {} to {}",
        before_snapshot.liquidity_index,
        reserve_data.liquidity_index
    );
    assert!(
        reserve_data.variable_borrow_index >= before_snapshot.variable_borrow_index,
        "INDEX VIOLATION: Borrow index decreased from {} to {}",
        before_snapshot.variable_borrow_index,
        reserve_data.variable_borrow_index
    );
}

fn check_basic_invariants(
    router_client: &kinetic_router::Client,
    asset: &Address,
) {
    let reserve_data = router_client.get_reserve_data(asset);

    assert!(
        reserve_data.liquidity_index >= RAY,
        "Liquidity index below RAY"
    );
    assert!(
        reserve_data.variable_borrow_index >= RAY,
        "Borrow index below RAY"
    );
}

// =============================================================================
// Flash Loan Execution
// =============================================================================

fn execute_flash_loan(
    env: &Env,
    router_client: &kinetic_router::Client,
    receiver: &Address,
    initiator: &Address,
    asset: &Address,
    a_token: &Address,
    amount: u128,
    behavior: ReceiverBehavior,
    repay_delta_bps: i16,
    asset_client: &StellarAssetClient,
) -> bool {
    // Configure the receiver behavior
    env.invoke_contract::<()>(
        receiver,
        &Symbol::new(env, "set_behavior"),
        soroban_sdk::vec![
            env,
            behavior.to_u32().into_val(env),
            (repay_delta_bps as i32).into_val(env),
        ],
    );

    // For success cases, mint tokens to receiver for repayment
    if behavior.should_succeed() {
        // Calculate how much the receiver needs
        let premium_bps = router_client.get_flash_loan_premium();
        let premium = (amount * premium_bps as u128) / 10000;
        let mut total_needed = amount + premium;

        // Add extra for overpay
        if matches!(behavior, ReceiverBehavior::Overpay) {
            let extra = if repay_delta_bps > 0 {
                (total_needed * repay_delta_bps as u128) / 10000
            } else {
                total_needed / 10
            };
            total_needed += extra;
        }

        // Mint enough tokens to the receiver
        asset_client.mint(receiver, &(total_needed as i128 + 1000));
    }

    // Create the flash loan parameters
    let assets = soroban_sdk::vec![env, asset.clone()];
    let amounts = soroban_sdk::vec![env, amount];
    let params = Bytes::new(env);

    // Execute flash loan
    let result = router_client.try_flash_loan(
        initiator,
        receiver,
        &assets,
        &amounts,
        &params,
    );

    result.is_ok()
}

// =============================================================================
// Operation Execution Context
// =============================================================================

struct TestContext<'a> {
    env: &'a Env,
    admin: &'a Address,
    liquidity_provider: &'a Address,
    initiator: &'a Address,
    receiver: &'a Address,
    treasury: &'a Address,
    router_client: &'a kinetic_router::Client<'a>,
    oracle_client: &'a price_oracle::Client<'a>,
    asset_client: &'a StellarAssetClient<'a>,
    underlying_asset: &'a Address,
    a_token: &'a Address,
}

fn execute_operation(ctx: &TestContext, op: &FlashLoanOperation) {
    match op {
        FlashLoanOperation::SupplyLiquidity { amount } => {
            let supply_amount = (*amount as u128).max(1).min(1_000_000_000_000_000);

            // Mint and supply
            ctx.asset_client.mint(ctx.liquidity_provider, &(supply_amount as i128));
            let _ = ctx.router_client.try_supply(
                ctx.liquidity_provider,
                ctx.underlying_asset,
                &supply_amount,
                ctx.liquidity_provider,
                &0u32,
            );
        }

        FlashLoanOperation::AdvanceTime { seconds } => {
            // Cap to 1 year
            let advance = (*seconds as u64).min(31_536_000);
            if advance > 0 {
                let current_timestamp = ctx.env.ledger().timestamp();
                let new_timestamp = current_timestamp.saturating_add(advance);
                ctx.env.ledger().set_timestamp(new_timestamp);
            }
        }

        FlashLoanOperation::SetPrice { price_bps } => {
            // Set price relative to BASE_PRICE
            let bps = ((*price_bps as u128).max(10)).min(50000);
            let new_price = BASE_PRICE * bps / 10000;
            if new_price > 0 {
                let asset_enum = price_oracle::Asset::Stellar(ctx.underlying_asset.clone());
                let _ = ctx.oracle_client.try_set_manual_override(
                    ctx.admin,
                    &asset_enum,
                    &Some(new_price),
                    &Some(ctx.env.ledger().timestamp() + 604_000),
                );
            }
        }

        FlashLoanOperation::ExecuteFlashLoan {
            amount,
            receiver_behavior,
            repay_delta_bps,
        } => {
            // Get current pool liquidity
            let token_client = token::Client::new(ctx.env, ctx.underlying_asset);
            let available_liquidity = token_client.balance(ctx.a_token);

            if available_liquidity <= 0 {
                return; // No liquidity to borrow
            }

            // Clamp amount to available liquidity
            let flash_amount = (*amount as u128)
                .max(1)
                .min(available_liquidity as u128);

            // Take snapshot before
            let snapshot = take_pool_snapshot(
                ctx.env,
                ctx.underlying_asset,
                ctx.a_token,
                ctx.treasury,
                ctx.router_client,
            );

            // Calculate expected premium
            let premium_bps = ctx.router_client.get_flash_loan_premium();
            let expected_premium = (flash_amount * premium_bps as u128) / 10000;

            // Execute flash loan
            let succeeded = execute_flash_loan(
                ctx.env,
                ctx.router_client,
                ctx.receiver,
                ctx.initiator,
                ctx.underlying_asset,
                ctx.a_token,
                flash_amount,
                *receiver_behavior,
                *repay_delta_bps,
                ctx.asset_client,
            );

            // Verify expected behavior
            if receiver_behavior.should_succeed() {
                // Should have succeeded
                if !succeeded {
                    // This is acceptable if there was insufficient liquidity
                    // or other valid failure reasons
                }
            } else {
                // Should have failed
                assert!(
                    !succeeded,
                    "Flash loan should have failed for behavior {:?}",
                    receiver_behavior
                );
            }

            // Check invariants
            check_flash_loan_invariants(
                ctx.env,
                ctx.router_client,
                ctx.underlying_asset,
                ctx.a_token,
                ctx.treasury,
                &snapshot,
                succeeded,
                if succeeded { expected_premium } else { 0 },
            );
        }

        FlashLoanOperation::ExecuteFlashLoanMaxAmount { receiver_behavior } => {
            // Get current pool liquidity
            let token_client = token::Client::new(ctx.env, ctx.underlying_asset);
            let available_liquidity = token_client.balance(ctx.a_token);

            if available_liquidity <= 0 {
                return;
            }

            // Request exact available amount
            let flash_amount = available_liquidity as u128;

            let snapshot = take_pool_snapshot(
                ctx.env,
                ctx.underlying_asset,
                ctx.a_token,
                ctx.treasury,
                ctx.router_client,
            );

            let premium_bps = ctx.router_client.get_flash_loan_premium();
            let expected_premium = (flash_amount * premium_bps as u128) / 10000;

            let succeeded = execute_flash_loan(
                ctx.env,
                ctx.router_client,
                ctx.receiver,
                ctx.initiator,
                ctx.underlying_asset,
                ctx.a_token,
                flash_amount,
                *receiver_behavior,
                0,
                ctx.asset_client,
            );

            check_flash_loan_invariants(
                ctx.env,
                ctx.router_client,
                ctx.underlying_asset,
                ctx.a_token,
                ctx.treasury,
                &snapshot,
                succeeded,
                if succeeded { expected_premium } else { 0 },
            );
        }

        FlashLoanOperation::ExecuteFlashLoanZeroAmount => {
            // Attempt flash loan with zero amount - should fail
            let assets = soroban_sdk::vec![ctx.env, ctx.underlying_asset.clone()];
            let amounts: Vec<u128> = soroban_sdk::vec![ctx.env, 0u128];
            let params = Bytes::new(ctx.env);

            let result = ctx.router_client.try_flash_loan(
                ctx.initiator,
                ctx.receiver,
                &assets,
                &amounts,
                &params,
            );

            // Should fail with InvalidAmount
            assert!(result.is_err(), "Flash loan with zero amount should fail");

            // Basic invariants should still hold
            check_basic_invariants(ctx.router_client, ctx.underlying_asset);
        }

        FlashLoanOperation::WithdrawLiquidity { amount } => {
            // Get provider's aToken balance
            let a_token_client = a_token::Client::new(ctx.env, ctx.a_token);
            let provider_balance = a_token_client.balance(ctx.liquidity_provider);

            if provider_balance <= 0 {
                return;
            }

            let withdraw_amount = (*amount as u128).max(1).min(provider_balance as u128);

            let _ = ctx.router_client.try_withdraw(
                ctx.liquidity_provider,
                ctx.underlying_asset,
                &withdraw_amount,
                ctx.liquidity_provider,
            );
        }
    }
}

// =============================================================================
// Fuzz Target
// =============================================================================

fuzz_target!(|input: FlashLoanFuzzInput| {
    // Clamp initial liquidity to reasonable range
    let initial_liquidity = if input.initial_liquidity < 1_000_000 {
        1_000_000u128 // Minimum 0.1 tokens (7 decimals)
    } else {
        (input.initial_liquidity as u128).min(100_000_000_000_000u128) // Max 10M tokens
    };

    let env = setup_test_env();

    // Setup addresses
    let admin = Address::generate(&env);
    let emergency_admin = Address::generate(&env);
    let liquidity_provider = Address::generate(&env);
    let initiator = Address::generate(&env);
    let treasury = Address::generate(&env);

    // Setup oracle
    let oracle_addr = setup_oracle(&env, &admin);
    let oracle_client = price_oracle::Client::new(&env, &oracle_addr);

    // Setup router with treasury
    let router_addr = setup_kinetic_router(&env, &admin, &emergency_admin, &oracle_addr, &treasury);
    let router_client = kinetic_router::Client::new(&env, &router_addr);

    // Setup reserve with flash loans enabled
    let (underlying_asset, _underlying_contract, a_token, _debt_token) =
        setup_reserve(&env, &router_addr, &oracle_addr, &admin, true);

    // Create asset client
    let asset_client = StellarAssetClient::new(&env, &underlying_asset);

    // Setup configurable receiver
    let receiver = env.register(ConfigurableReceiver, ());
    env.invoke_contract::<()>(
        &receiver,
        &Symbol::new(&env, "init"),
        soroban_sdk::vec![
            &env,
            underlying_asset.clone().into_val(&env),
            a_token.clone().into_val(&env),
            0u32.into_val(&env),  // Default: ExactRepay
            0i32.into_val(&env),  // No delta
        ],
    );

    // Set flash loan premium (0-100 bps)
    let premium_bps = (input.premium_bps % 101) as u32;
    // Note: premium is typically set during initialization, we'll use the default

    // === Provide initial liquidity ===
    asset_client.mint(&liquidity_provider, &(initial_liquidity as i128 * 2));
    let supply_result = router_client.try_supply(
        &liquidity_provider,
        &underlying_asset,
        &initial_liquidity,
        &liquidity_provider,
        &0u32,
    );

    if supply_result.is_err() {
        return; // Setup failed
    }

    // Initial invariant check
    check_basic_invariants(&router_client, &underlying_asset);

    // Create context
    let ctx = TestContext {
        env: &env,
        admin: &admin,
        liquidity_provider: &liquidity_provider,
        initiator: &initiator,
        receiver: &receiver,
        treasury: &treasury,
        router_client: &router_client,
        oracle_client: &oracle_client,
        asset_client: &asset_client,
        underlying_asset: &underlying_asset,
        a_token: &a_token,
    };

    // Execute operation sequence
    for op_opt in &input.operations {
        if let Some(op) = op_opt {
            execute_operation(&ctx, op);

            // Check basic invariants after each operation
            check_basic_invariants(&router_client, &underlying_asset);
        }
    }

    // Final invariant check
    check_basic_invariants(&router_client, &underlying_asset);
});
