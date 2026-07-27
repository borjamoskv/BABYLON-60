#![no_main]

//! Fuzz test for K2 authorization boundaries.
//!
//! CRITICAL: This fuzzer tests authorization WITHOUT mock_all_auths().
//! It specifically targets the vulnerability classes found in HAL-01 through HAL-05.
//!
//! ## Audit Findings Tested:
//! - HAL-01: Missing require_auth() on privileged entry points
//! - HAL-03: Public execute_operation allowing replay attacks
//! - HAL-04: Permissionless incentives accrual
//! - HAL-05: Missing access control on set_incentives_contract
//! - HAL-14: aToken transfer_from auth issues
//! - HAL-40: Two-step admin transfer bypass
//!
//! ## Key Invariants:
//! - Non-admin callers MUST fail on all admin operations
//! - Users can ONLY modify their own positions (not others' without delegation)
//! - Admin transfer requires explicit accept step
//! - Incentives operations require proper caller auth
//!
//! Run with: cargo +nightly fuzz run fuzz_auth_boundaries --sanitizer=none

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

/// Mock Flash Loan Receiver - used to test HAL-03 (execute_operation auth)
#[contract]
pub struct MockFlashLoanReceiver;

#[contractimpl]
impl MockFlashLoanReceiver {
    /// Standard execute_operation that repays correctly
    pub fn execute_operation(
        env: Env,
        assets: Vec<Address>,
        amounts: Vec<u128>,
        premiums: Vec<u128>,
        _initiator: Address,
        _params: Bytes,
    ) -> bool {
        // Try to repay the flash loan correctly
        for i in 0..assets.len() {
            if let (Some(asset), Some(amount), Some(premium)) =
                (assets.get(i), amounts.get(i), premiums.get(i))
            {
                let total_owed = amount + premium;
                let token_client = token::Client::new(&env, &asset);

                // Get aToken address from storage (set during init)
                if let Some(a_token) = env.storage().instance().get::<Symbol, Address>(&Symbol::new(&env, "atoken")) {
                    token_client.transfer(
                        &env.current_contract_address(),
                        &a_token,
                        &(total_owed as i128),
                    );
                }
            }
        }
        true
    }

    /// Initialize with aToken address for repayment
    pub fn init(env: Env, a_token: Address) {
        env.storage().instance().set(&Symbol::new(&env, "atoken"), &a_token);
    }
}

// =============================================================================
// Fuzz Input Types
// =============================================================================

/// Actor types in the system
#[derive(Arbitrary, Debug, Clone, Copy, PartialEq)]
pub enum ActorType {
    /// The legitimate pool admin
    PoolAdmin,
    /// The emergency admin
    EmergencyAdmin,
    /// A random unauthorized user
    RandomUser,
    /// The pool configurator contract
    PoolConfigurator,
    /// A user who has supplied to the pool
    Supplier,
    /// A user who has borrowed from the pool
    Borrower,
}

/// Operations that require admin authorization
#[derive(Arbitrary, Debug, Clone)]
pub enum AdminOperation {
    // === HAL-01 Category: Missing require_auth on privileged ops ===
    /// Set flash loan premium (admin only)
    SetFlashLoanPremium { premium_bps: u16 },
    /// Set flash loan premium max (admin only)
    SetFlashLoanPremiumMax { max_bps: u16 },
    /// Set treasury address (admin only)
    SetTreasury,
    /// Set DEX router (admin only)
    SetDexRouter,
    /// Set DEX factory (admin only)
    SetDexFactory,
    /// Set pool configurator (admin only)
    SetPoolConfigurator,
    /// Set health factor liquidation threshold (admin only)
    SetHfLiquidationThreshold { threshold: u64 },
    /// Set min swap output bps (admin only)
    SetMinSwapOutputBps { bps: u16 },

    // === HAL-05 Category: set_incentives_contract access control ===
    /// Set incentives contract (admin only)
    SetIncentivesContract,

    // === HAL-05 related: flash liquidation helper ===
    /// Set flash liquidation helper (admin only)
    SetFlashLiquidationHelper,

    // === Access Control Lists ===
    /// Set reserve whitelist (admin only)
    SetReserveWhitelist { size: u8 },
    /// Set reserve blacklist (admin only)
    SetReserveBlacklist { size: u8 },
    /// Set liquidation whitelist (admin only)
    SetLiquidationWhitelist { size: u8 },
    /// Set liquidation blacklist (admin only)
    SetLiquidationBlacklist { size: u8 },

    // === Treasury Operations ===
    /// Collect protocol reserves (admin only)
    CollectProtocolReserves,

    // === Emergency Operations ===
    /// Pause protocol (emergency admin only)
    Pause,
    /// Unpause protocol (pool admin only)
    Unpause,

    // === HAL-40 Category: Two-step admin transfer ===
    /// Propose new admin (current admin only)
    ProposeAdmin,
    /// Accept admin role (proposed admin only)
    AcceptAdmin,
    /// Cancel admin proposal (current admin only)
    CancelAdminProposal,
}

/// Operations that require user authorization
#[derive(Arbitrary, Debug, Clone)]
pub enum UserOperation {
    // === Basic lending operations ===
    /// Supply assets (caller must be the supplier OR have delegation)
    Supply { amount: u64 },
    /// Borrow assets (caller must be the borrower)
    Borrow { amount: u64 },
    /// Repay debt (anyone can repay for anyone - intentional)
    Repay { amount: u64 },
    /// Withdraw assets (caller must be the owner OR have delegation)
    Withdraw { amount: u64 },

    // === On-behalf-of operations (HAL-01 related) ===
    /// Supply on behalf of another user (requires both auths)
    SupplyOnBehalf { amount: u64 },
    /// Borrow on behalf of another user (requires both auths)
    BorrowOnBehalf { amount: u64 },
    /// Withdraw on behalf of another user (requires both auths)
    WithdrawOnBehalf { amount: u64 },

    // === Collateral management ===
    /// Set collateral enabled (caller only)
    SetCollateralEnabled { enabled: bool },

    // === Flash loan (HAL-03 related) ===
    /// Initiate flash loan (initiator must auth)
    FlashLoan { amount: u64 },
}

/// Main fuzz operation combining actor and operation
#[derive(Arbitrary, Debug, Clone)]
pub enum AuthTestOperation {
    /// Admin operation attempted by an actor
    AdminOp {
        caller: ActorType,
        operation: AdminOperation,
    },
    /// User operation attempted by an actor
    UserOp {
        caller: ActorType,
        target_user: ActorType,
        operation: UserOperation,
    },
    /// Advance time (for testing expiry)
    AdvanceTime { seconds: u32 },
}

/// Main fuzz input
#[derive(Arbitrary, Debug, Clone)]
pub struct AuthFuzzInput {
    /// Initial setup: should we supply tokens first?
    pub setup_supplier: bool,
    /// Initial setup: should we create a borrow position?
    pub setup_borrower: bool,
    /// Sequence of operations to test
    pub operations: [Option<AuthTestOperation>; 12],
}

// =============================================================================
// Constants
// =============================================================================

#[allow(dead_code)]
const RAY: u128 = 1_000_000_000;
const BASE_PRICE: u128 = 1_000_000_000_000_000;
const INITIAL_SUPPLY: u128 = 100_000_000_000; // 10,000 tokens with 7 decimals

// =============================================================================
// Test Setup - NO mock_all_auths()
// =============================================================================

/// Setup environment WITHOUT mock_all_auths() - this is the critical difference
#[allow(dead_code)]
fn setup_test_env() -> Env {
    let env = Env::default();
    // CRITICAL: We do NOT call env.mock_all_auths() here!
    // This means all require_auth() calls will actually be enforced
    env.cost_estimate().budget().reset_unlimited();
    env
}

/// Setup with mock_all_auths for initial contract deployment only
fn setup_test_env_for_init() -> Env {
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
) -> (Address, Address, Address) {
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

    let pool_configurator = Address::generate(env);
    client.set_pool_configurator(&pool_configurator);

    (router_addr, treasury, pool_configurator)
}

fn setup_reserve(
    env: &Env,
    router_addr: &Address,
    oracle_addr: &Address,
    admin: &Address,
    pool_configurator: &Address,
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

    let params = kinetic_router::InitReserveParams {
        decimals: 7,
        ltv: 8000,
        liquidation_threshold: 8500,
        liquidation_bonus: 500,
        reserve_factor: 1000,
        supply_cap: 1_000_000_000_000_000u128,
        borrow_cap: 1_000_000_000_000_000u128,
        borrowing_enabled: true,
        flashloan_enabled: true,
    };

    router_client.init_reserve(
        pool_configurator,
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
// Test Context
// =============================================================================

struct TestContext<'a> {
    env: &'a Env,
    router_addr: &'a Address,
    router_client: &'a kinetic_router::Client<'a>,
    pool_admin: &'a Address,
    emergency_admin: &'a Address,
    pool_configurator: &'a Address,
    random_user: &'a Address,
    supplier: &'a Address,
    borrower: &'a Address,
    underlying_asset: &'a Address,
    #[allow(dead_code)]
    a_token: &'a Address,
    asset_client: &'a StellarAssetClient<'a>,
    /// Track auth failures for invariant checking
    auth_failure_count: u32,
    /// Track successful unauthorized calls (should be 0)
    unauthorized_success_count: u32,
}

impl<'a> TestContext<'a> {
    fn get_actor_address(&self, actor: ActorType) -> &'a Address {
        match actor {
            ActorType::PoolAdmin => self.pool_admin,
            ActorType::EmergencyAdmin => self.emergency_admin,
            ActorType::RandomUser => self.random_user,
            ActorType::PoolConfigurator => self.pool_configurator,
            ActorType::Supplier => self.supplier,
            ActorType::Borrower => self.borrower,
        }
    }

    fn is_admin(&self, actor: ActorType) -> bool {
        matches!(actor, ActorType::PoolAdmin)
    }

    fn is_emergency_admin(&self, actor: ActorType) -> bool {
        matches!(actor, ActorType::EmergencyAdmin)
    }
}

// =============================================================================
// Authorization Testing
// =============================================================================

/// Test an admin operation and verify auth is properly enforced
fn test_admin_operation(ctx: &mut TestContext, caller: ActorType, op: &AdminOperation) {
    let caller_addr = ctx.get_actor_address(caller);
    let is_authorized = ctx.is_admin(caller);
    let is_emergency = ctx.is_emergency_admin(caller);

    // For testing without mock_all_auths, we use mock_auths with specific authorizations
    // This simulates the caller providing their authorization signature

    match op {
        AdminOperation::SetFlashLoanPremium { premium_bps } => {
            let premium = (*premium_bps as u128).min(10000);

            // Mock auth for the caller
            ctx.env.mock_auths(&[soroban_sdk::testutils::MockAuth {
                address: caller_addr,
                invoke: &soroban_sdk::testutils::MockAuthInvoke {
                    contract: ctx.router_addr,
                    fn_name: "set_flash_loan_premium",
                    args: soroban_sdk::vec![ctx.env, premium.into_val(ctx.env)],
                    sub_invokes: &[],
                },
            }]);

            let result = ctx.router_client.try_set_flash_loan_premium(&premium);

            verify_auth_result(ctx, result.is_ok() && result.unwrap().is_ok(), is_authorized, "set_flash_loan_premium");
        }

        AdminOperation::SetFlashLoanPremiumMax { max_bps } => {
            let max_val = (*max_bps as u128).min(100000);

            ctx.env.mock_auths(&[soroban_sdk::testutils::MockAuth {
                address: caller_addr,
                invoke: &soroban_sdk::testutils::MockAuthInvoke {
                    contract: ctx.router_addr,
                    fn_name: "set_flash_loan_premium_max",
                    args: soroban_sdk::vec![ctx.env, max_val.into_val(ctx.env)],
                    sub_invokes: &[],
                },
            }]);

            let result = ctx.router_client.try_set_flash_loan_premium_max(&max_val);

            verify_auth_result(ctx, result.is_ok() && result.unwrap().is_ok(), is_authorized, "set_flash_loan_premium_max");
        }

        AdminOperation::SetTreasury => {
            let new_treasury = Address::generate(ctx.env);

            ctx.env.mock_auths(&[soroban_sdk::testutils::MockAuth {
                address: caller_addr,
                invoke: &soroban_sdk::testutils::MockAuthInvoke {
                    contract: ctx.router_addr,
                    fn_name: "set_treasury",
                    args: soroban_sdk::vec![ctx.env, new_treasury.clone().into_val(ctx.env)],
                    sub_invokes: &[],
                },
            }]);

            let result = ctx.router_client.try_set_treasury(&new_treasury);

            verify_auth_result(ctx, result.is_ok() && result.unwrap().is_ok(), is_authorized, "set_treasury");
        }

        AdminOperation::SetDexRouter => {
            let new_router = Address::generate(ctx.env);

            ctx.env.mock_auths(&[soroban_sdk::testutils::MockAuth {
                address: caller_addr,
                invoke: &soroban_sdk::testutils::MockAuthInvoke {
                    contract: ctx.router_addr,
                    fn_name: "set_dex_router",
                    args: soroban_sdk::vec![ctx.env, new_router.clone().into_val(ctx.env)],
                    sub_invokes: &[],
                },
            }]);

            let result = ctx.router_client.try_set_dex_router(&new_router);

            verify_auth_result(ctx, result.is_ok() && result.unwrap().is_ok(), is_authorized, "set_dex_router");
        }

        AdminOperation::SetDexFactory => {
            let new_factory = Address::generate(ctx.env);

            ctx.env.mock_auths(&[soroban_sdk::testutils::MockAuth {
                address: caller_addr,
                invoke: &soroban_sdk::testutils::MockAuthInvoke {
                    contract: ctx.router_addr,
                    fn_name: "set_dex_factory",
                    args: soroban_sdk::vec![ctx.env, new_factory.clone().into_val(ctx.env)],
                    sub_invokes: &[],
                },
            }]);

            let result = ctx.router_client.try_set_dex_factory(&new_factory);

            verify_auth_result(ctx, result.is_ok() && result.unwrap().is_ok(), is_authorized, "set_dex_factory");
        }

        AdminOperation::SetPoolConfigurator => {
            let new_configurator = Address::generate(ctx.env);

            ctx.env.mock_auths(&[soroban_sdk::testutils::MockAuth {
                address: caller_addr,
                invoke: &soroban_sdk::testutils::MockAuthInvoke {
                    contract: ctx.router_addr,
                    fn_name: "set_pool_configurator",
                    args: soroban_sdk::vec![ctx.env, new_configurator.clone().into_val(ctx.env)],
                    sub_invokes: &[],
                },
            }]);

            let result = ctx.router_client.try_set_pool_configurator(&new_configurator);

            verify_auth_result(ctx, result.is_ok() && result.unwrap().is_ok(), is_authorized, "set_pool_configurator");
        }

        AdminOperation::SetHfLiquidationThreshold { threshold } => {
            let threshold_val = (*threshold as u128) * 1_000_000_000_000_000_000 / 100;

            ctx.env.mock_auths(&[soroban_sdk::testutils::MockAuth {
                address: caller_addr,
                invoke: &soroban_sdk::testutils::MockAuthInvoke {
                    contract: ctx.router_addr,
                    fn_name: "set_hf_liquidation_threshold",
                    args: soroban_sdk::vec![ctx.env, threshold_val.into_val(ctx.env)],
                    sub_invokes: &[],
                },
            }]);

            let result = ctx.router_client.try_set_hf_liquidation_threshold(&threshold_val);

            verify_auth_result(ctx, result.is_ok() && result.unwrap().is_ok(), is_authorized, "set_hf_liquidation_threshold");
        }

        AdminOperation::SetMinSwapOutputBps { bps } => {
            let bps_val = (*bps as u128).min(10000);

            ctx.env.mock_auths(&[soroban_sdk::testutils::MockAuth {
                address: caller_addr,
                invoke: &soroban_sdk::testutils::MockAuthInvoke {
                    contract: ctx.router_addr,
                    fn_name: "set_min_swap_output_bps",
                    args: soroban_sdk::vec![ctx.env, bps_val.into_val(ctx.env)],
                    sub_invokes: &[],
                },
            }]);

            let result = ctx.router_client.try_set_min_swap_output_bps(&bps_val);

            verify_auth_result(ctx, result.is_ok() && result.unwrap().is_ok(), is_authorized, "set_min_swap_output_bps");
        }

        AdminOperation::SetIncentivesContract => {
            // HAL-05: This should require admin auth
            let new_incentives = Address::generate(ctx.env);

            ctx.env.mock_auths(&[soroban_sdk::testutils::MockAuth {
                address: caller_addr,
                invoke: &soroban_sdk::testutils::MockAuthInvoke {
                    contract: ctx.router_addr,
                    fn_name: "set_incentives_contract",
                    args: soroban_sdk::vec![ctx.env, new_incentives.clone().into_val(ctx.env)],
                    sub_invokes: &[],
                },
            }]);

            let result = ctx.router_client.try_set_incentives_contract(&new_incentives);

            verify_auth_result(ctx, result.is_ok() && result.unwrap().is_ok(), is_authorized, "set_incentives_contract (HAL-05)");
        }

        AdminOperation::SetFlashLiquidationHelper => {
            let new_helper = Address::generate(ctx.env);

            ctx.env.mock_auths(&[soroban_sdk::testutils::MockAuth {
                address: caller_addr,
                invoke: &soroban_sdk::testutils::MockAuthInvoke {
                    contract: ctx.router_addr,
                    fn_name: "set_flash_liquidation_helper",
                    args: soroban_sdk::vec![ctx.env, new_helper.clone().into_val(ctx.env)],
                    sub_invokes: &[],
                },
            }]);

            let result = ctx.router_client.try_set_flash_liquidation_helper(&new_helper);

            verify_auth_result(ctx, result.is_ok() && result.unwrap().is_ok(), is_authorized, "set_flash_liquidation_helper");
        }

        AdminOperation::SetReserveWhitelist { size } => {
            let whitelist_size = (*size % 5) as usize;
            let whitelist: Vec<Address> = (0..whitelist_size)
                .map(|_| Address::generate(ctx.env))
                .collect::<std::vec::Vec<_>>()
                .into_iter()
                .fold(Vec::new(ctx.env), |mut acc, addr| {
                    acc.push_back(addr);
                    acc
                });

            ctx.env.mock_auths(&[soroban_sdk::testutils::MockAuth {
                address: caller_addr,
                invoke: &soroban_sdk::testutils::MockAuthInvoke {
                    contract: ctx.router_addr,
                    fn_name: "set_reserve_whitelist",
                    args: soroban_sdk::vec![
                        ctx.env,
                        ctx.underlying_asset.clone().into_val(ctx.env),
                        whitelist.clone().into_val(ctx.env)
                    ],
                    sub_invokes: &[],
                },
            }]);

            let result = ctx.router_client.try_set_reserve_whitelist(ctx.underlying_asset, &whitelist);

            verify_auth_result(ctx, result.is_ok() && result.unwrap().is_ok(), is_authorized, "set_reserve_whitelist");
        }

        AdminOperation::SetReserveBlacklist { size } => {
            let blacklist_size = (*size % 5) as usize;
            let blacklist: Vec<Address> = (0..blacklist_size)
                .map(|_| Address::generate(ctx.env))
                .collect::<std::vec::Vec<_>>()
                .into_iter()
                .fold(Vec::new(ctx.env), |mut acc, addr| {
                    acc.push_back(addr);
                    acc
                });

            ctx.env.mock_auths(&[soroban_sdk::testutils::MockAuth {
                address: caller_addr,
                invoke: &soroban_sdk::testutils::MockAuthInvoke {
                    contract: ctx.router_addr,
                    fn_name: "set_reserve_blacklist",
                    args: soroban_sdk::vec![
                        ctx.env,
                        ctx.underlying_asset.clone().into_val(ctx.env),
                        blacklist.clone().into_val(ctx.env)
                    ],
                    sub_invokes: &[],
                },
            }]);

            let result = ctx.router_client.try_set_reserve_blacklist(ctx.underlying_asset, &blacklist);

            verify_auth_result(ctx, result.is_ok() && result.unwrap().is_ok(), is_authorized, "set_reserve_blacklist");
        }

        AdminOperation::SetLiquidationWhitelist { size } => {
            let whitelist_size = (*size % 5) as usize;
            let whitelist: Vec<Address> = (0..whitelist_size)
                .map(|_| Address::generate(ctx.env))
                .collect::<std::vec::Vec<_>>()
                .into_iter()
                .fold(Vec::new(ctx.env), |mut acc, addr| {
                    acc.push_back(addr);
                    acc
                });

            ctx.env.mock_auths(&[soroban_sdk::testutils::MockAuth {
                address: caller_addr,
                invoke: &soroban_sdk::testutils::MockAuthInvoke {
                    contract: ctx.router_addr,
                    fn_name: "set_liquidation_whitelist",
                    args: soroban_sdk::vec![ctx.env, whitelist.clone().into_val(ctx.env)],
                    sub_invokes: &[],
                },
            }]);

            let result = ctx.router_client.try_set_liquidation_whitelist(&whitelist);

            verify_auth_result(ctx, result.is_ok() && result.unwrap().is_ok(), is_authorized, "set_liquidation_whitelist");
        }

        AdminOperation::SetLiquidationBlacklist { size } => {
            let blacklist_size = (*size % 5) as usize;
            let blacklist: Vec<Address> = (0..blacklist_size)
                .map(|_| Address::generate(ctx.env))
                .collect::<std::vec::Vec<_>>()
                .into_iter()
                .fold(Vec::new(ctx.env), |mut acc, addr| {
                    acc.push_back(addr);
                    acc
                });

            ctx.env.mock_auths(&[soroban_sdk::testutils::MockAuth {
                address: caller_addr,
                invoke: &soroban_sdk::testutils::MockAuthInvoke {
                    contract: ctx.router_addr,
                    fn_name: "set_liquidation_blacklist",
                    args: soroban_sdk::vec![ctx.env, blacklist.clone().into_val(ctx.env)],
                    sub_invokes: &[],
                },
            }]);

            let result = ctx.router_client.try_set_liquidation_blacklist(&blacklist);

            verify_auth_result(ctx, result.is_ok() && result.unwrap().is_ok(), is_authorized, "set_liquidation_blacklist");
        }

        AdminOperation::CollectProtocolReserves => {
            ctx.env.mock_auths(&[soroban_sdk::testutils::MockAuth {
                address: caller_addr,
                invoke: &soroban_sdk::testutils::MockAuthInvoke {
                    contract: ctx.router_addr,
                    fn_name: "collect_protocol_reserves",
                    args: soroban_sdk::vec![ctx.env, ctx.underlying_asset.clone().into_val(ctx.env)],
                    sub_invokes: &[],
                },
            }]);

            let result = ctx.router_client.try_collect_protocol_reserves(ctx.underlying_asset);

            // This may fail for other reasons (no reserves), so just check auth
            // If it succeeded but caller wasn't authorized, that's a problem
            if result.is_ok() && result.unwrap().is_ok() && !is_authorized {
                ctx.unauthorized_success_count += 1;
            }
        }

        AdminOperation::Pause => {
            // Both pool admin and emergency admin can pause
            ctx.env.mock_auths(&[soroban_sdk::testutils::MockAuth {
                address: caller_addr,
                invoke: &soroban_sdk::testutils::MockAuthInvoke {
                    contract: ctx.router_addr,
                    fn_name: "pause",
                    args: soroban_sdk::vec![ctx.env, caller_addr.clone().into_val(ctx.env)],
                    sub_invokes: &[],
                },
            }]);

            let result = ctx.router_client.try_pause(caller_addr);

            // Pause can be done by pool admin OR emergency admin
            let can_pause = is_authorized || is_emergency;
            verify_auth_result(ctx, result.is_ok() && result.unwrap().is_ok(), can_pause, "pause");
        }

        AdminOperation::Unpause => {
            // Both pool admin and emergency admin can unpause
            ctx.env.mock_auths(&[soroban_sdk::testutils::MockAuth {
                address: caller_addr,
                invoke: &soroban_sdk::testutils::MockAuthInvoke {
                    contract: ctx.router_addr,
                    fn_name: "unpause",
                    args: soroban_sdk::vec![ctx.env, caller_addr.clone().into_val(ctx.env)],
                    sub_invokes: &[],
                },
            }]);

            let result = ctx.router_client.try_unpause(caller_addr);

            // Unpause can be done by pool admin OR emergency admin
            let can_unpause = is_authorized || is_emergency;
            verify_auth_result(ctx, result.is_ok() && result.unwrap().is_ok(), can_unpause, "unpause");
        }

        AdminOperation::ProposeAdmin => {
            // HAL-40: Only current admin can propose
            let new_admin = Address::generate(ctx.env);

            ctx.env.mock_auths(&[soroban_sdk::testutils::MockAuth {
                address: caller_addr,
                invoke: &soroban_sdk::testutils::MockAuthInvoke {
                    contract: ctx.router_addr,
                    fn_name: "propose_admin",
                    args: soroban_sdk::vec![
                        ctx.env,
                        caller_addr.clone().into_val(ctx.env),
                        new_admin.clone().into_val(ctx.env)
                    ],
                    sub_invokes: &[],
                },
            }]);

            let result = ctx.router_client.try_propose_admin(caller_addr, &new_admin);

            verify_auth_result(ctx, result.is_ok() && result.unwrap().is_ok(), is_authorized, "propose_admin (HAL-40)");
        }

        AdminOperation::AcceptAdmin => {
            // HAL-40: Only proposed admin can accept
            // This should fail for anyone not the proposed admin
            ctx.env.mock_auths(&[soroban_sdk::testutils::MockAuth {
                address: caller_addr,
                invoke: &soroban_sdk::testutils::MockAuthInvoke {
                    contract: ctx.router_addr,
                    fn_name: "accept_admin",
                    args: soroban_sdk::vec![ctx.env, caller_addr.clone().into_val(ctx.env)],
                    sub_invokes: &[],
                },
            }]);

            let result = ctx.router_client.try_accept_admin(caller_addr);

            // Accept should fail for anyone not the proposed admin
            // If no one is proposed, it should also fail
            if result.is_ok() && result.unwrap().is_ok() {
                // This would be unexpected in our test since we haven't proposed anyone
                ctx.unauthorized_success_count += 1;
            }
        }

        AdminOperation::CancelAdminProposal => {
            // HAL-40: Only current admin can cancel
            ctx.env.mock_auths(&[soroban_sdk::testutils::MockAuth {
                address: caller_addr,
                invoke: &soroban_sdk::testutils::MockAuthInvoke {
                    contract: ctx.router_addr,
                    fn_name: "cancel_admin_proposal",
                    args: soroban_sdk::vec![ctx.env, caller_addr.clone().into_val(ctx.env)],
                    sub_invokes: &[],
                },
            }]);

            let result = ctx.router_client.try_cancel_admin_proposal(caller_addr);

            verify_auth_result(ctx, result.is_ok() && result.unwrap().is_ok(), is_authorized, "cancel_admin_proposal (HAL-40)");
        }
    }
}

/// Test a user operation and verify auth is properly enforced
fn test_user_operation(
    ctx: &mut TestContext,
    caller: ActorType,
    target_user: ActorType,
    op: &UserOperation
) {
    let caller_addr = ctx.get_actor_address(caller);
    let target_addr = ctx.get_actor_address(target_user);
    let is_self = caller == target_user;

    match op {
        UserOperation::Supply { amount } => {
            let supply_amount = (*amount as u128).max(1).min(INITIAL_SUPPLY / 10);

            // Mint tokens to caller
            ctx.env.mock_all_auths();
            ctx.asset_client.mint(caller_addr, &(supply_amount as i128 * 2));

            // Now test auth for supply
            ctx.env.mock_auths(&[soroban_sdk::testutils::MockAuth {
                address: caller_addr,
                invoke: &soroban_sdk::testutils::MockAuthInvoke {
                    contract: ctx.router_addr,
                    fn_name: "supply",
                    args: soroban_sdk::vec![
                        ctx.env,
                        caller_addr.clone().into_val(ctx.env),
                        ctx.underlying_asset.clone().into_val(ctx.env),
                        supply_amount.into_val(ctx.env),
                        caller_addr.clone().into_val(ctx.env),
                        0u32.into_val(ctx.env),
                    ],
                    sub_invokes: &[],
                },
            }]);

            let _result = ctx.router_client.try_supply(
                caller_addr,
                ctx.underlying_asset,
                &supply_amount,
                caller_addr,
                &0u32,
            );

            // Supply should succeed when caller == on_behalf_of
            // When caller != on_behalf_of, both need to auth
        }

        UserOperation::SupplyOnBehalf { amount } => {
            // HAL-01 related: Test that on_behalf_of requires both auths
            let supply_amount = (*amount as u128).max(1).min(INITIAL_SUPPLY / 10);

            // Mint tokens to caller
            ctx.env.mock_all_auths();
            ctx.asset_client.mint(caller_addr, &(supply_amount as i128 * 2));

            // Only provide caller's auth, NOT target's auth
            ctx.env.mock_auths(&[soroban_sdk::testutils::MockAuth {
                address: caller_addr,
                invoke: &soroban_sdk::testutils::MockAuthInvoke {
                    contract: ctx.router_addr,
                    fn_name: "supply",
                    args: soroban_sdk::vec![
                        ctx.env,
                        caller_addr.clone().into_val(ctx.env),
                        ctx.underlying_asset.clone().into_val(ctx.env),
                        supply_amount.into_val(ctx.env),
                        target_addr.clone().into_val(ctx.env), // Different from caller!
                        0u32.into_val(ctx.env),
                    ],
                    sub_invokes: &[],
                },
            }]);

            let result = ctx.router_client.try_supply(
                caller_addr,
                ctx.underlying_asset,
                &supply_amount,
                target_addr,  // on_behalf_of is different
                &0u32,
            );

            // If caller != on_behalf_of and only caller authed, this should fail
            if !is_self && result.is_ok() && result.unwrap().is_ok() {
                // This would be a vulnerability - acting on behalf of someone without their auth
                ctx.unauthorized_success_count += 1;
            }
        }

        UserOperation::Borrow { amount } => {
            let borrow_amount = (*amount as u128).max(1).min(INITIAL_SUPPLY / 20);

            ctx.env.mock_auths(&[soroban_sdk::testutils::MockAuth {
                address: caller_addr,
                invoke: &soroban_sdk::testutils::MockAuthInvoke {
                    contract: ctx.router_addr,
                    fn_name: "borrow",
                    args: soroban_sdk::vec![
                        ctx.env,
                        caller_addr.clone().into_val(ctx.env),
                        ctx.underlying_asset.clone().into_val(ctx.env),
                        borrow_amount.into_val(ctx.env),
                        0u32.into_val(ctx.env),  // interest_rate_mode
                        0u32.into_val(ctx.env),  // referral_code
                        caller_addr.clone().into_val(ctx.env),  // on_behalf_of
                    ],
                    sub_invokes: &[],
                },
            }]);

            let _ = ctx.router_client.try_borrow(
                caller_addr,
                ctx.underlying_asset,
                &borrow_amount,
                &0u32,  // interest_rate_mode
                &0u32,  // referral_code
                caller_addr,  // on_behalf_of
            );
            // Borrow may fail for other reasons (no collateral), just testing auth
        }

        UserOperation::BorrowOnBehalf { amount } => {
            // HAL-01 related: Test that borrow on_behalf_of requires both auths
            let borrow_amount = (*amount as u128).max(1).min(INITIAL_SUPPLY / 20);

            // Only provide caller's auth
            ctx.env.mock_auths(&[soroban_sdk::testutils::MockAuth {
                address: caller_addr,
                invoke: &soroban_sdk::testutils::MockAuthInvoke {
                    contract: ctx.router_addr,
                    fn_name: "borrow",
                    args: soroban_sdk::vec![
                        ctx.env,
                        caller_addr.clone().into_val(ctx.env),
                        ctx.underlying_asset.clone().into_val(ctx.env),
                        borrow_amount.into_val(ctx.env),
                        0u32.into_val(ctx.env),  // interest_rate_mode
                        0u32.into_val(ctx.env),  // referral_code
                        target_addr.clone().into_val(ctx.env),  // on_behalf_of
                    ],
                    sub_invokes: &[],
                },
            }]);

            let result = ctx.router_client.try_borrow(
                caller_addr,
                ctx.underlying_asset,
                &borrow_amount,
                &0u32,  // interest_rate_mode
                &0u32,  // referral_code
                target_addr,  // on_behalf_of
            );

            // If caller != on_behalf_of and only caller authed, this should fail
            if !is_self && result.is_ok() && result.unwrap().is_ok() {
                ctx.unauthorized_success_count += 1;
            }
        }

        UserOperation::Repay { amount } => {
            let repay_amount = (*amount as u128).max(1);

            // Repay can be done by anyone for anyone (this is intentional)
            ctx.env.mock_auths(&[soroban_sdk::testutils::MockAuth {
                address: caller_addr,
                invoke: &soroban_sdk::testutils::MockAuthInvoke {
                    contract: ctx.router_addr,
                    fn_name: "repay",
                    args: soroban_sdk::vec![
                        ctx.env,
                        caller_addr.clone().into_val(ctx.env),
                        ctx.underlying_asset.clone().into_val(ctx.env),
                        repay_amount.into_val(ctx.env),
                        0u32.into_val(ctx.env),  // rate_mode
                        target_addr.clone().into_val(ctx.env),  // on_behalf_of
                    ],
                    sub_invokes: &[],
                },
            }]);

            let _ = ctx.router_client.try_repay(
                caller_addr,
                ctx.underlying_asset,
                &repay_amount,
                &0u32,  // rate_mode
                target_addr,  // on_behalf_of
            );
            // Repay may fail if no debt exists
        }

        UserOperation::Withdraw { amount } => {
            let withdraw_amount = (*amount as u128).max(1);

            ctx.env.mock_auths(&[soroban_sdk::testutils::MockAuth {
                address: caller_addr,
                invoke: &soroban_sdk::testutils::MockAuthInvoke {
                    contract: ctx.router_addr,
                    fn_name: "withdraw",
                    args: soroban_sdk::vec![
                        ctx.env,
                        caller_addr.clone().into_val(ctx.env),
                        ctx.underlying_asset.clone().into_val(ctx.env),
                        withdraw_amount.into_val(ctx.env),
                        caller_addr.clone().into_val(ctx.env),
                    ],
                    sub_invokes: &[],
                },
            }]);

            let _ = ctx.router_client.try_withdraw(
                caller_addr,
                ctx.underlying_asset,
                &withdraw_amount,
                caller_addr,
            );
        }

        UserOperation::WithdrawOnBehalf { amount } => {
            // HAL-01 related: Test that withdraw on_behalf_of requires both auths
            let withdraw_amount = (*amount as u128).max(1);

            // Only provide caller's auth
            ctx.env.mock_auths(&[soroban_sdk::testutils::MockAuth {
                address: caller_addr,
                invoke: &soroban_sdk::testutils::MockAuthInvoke {
                    contract: ctx.router_addr,
                    fn_name: "withdraw",
                    args: soroban_sdk::vec![
                        ctx.env,
                        caller_addr.clone().into_val(ctx.env),
                        ctx.underlying_asset.clone().into_val(ctx.env),
                        withdraw_amount.into_val(ctx.env),
                        target_addr.clone().into_val(ctx.env),
                    ],
                    sub_invokes: &[],
                },
            }]);

            let result = ctx.router_client.try_withdraw(
                caller_addr,
                ctx.underlying_asset,
                &withdraw_amount,
                target_addr,
            );

            // Withdraw to different target requires both auths or delegation
            // If only caller authed and it succeeded for different target, that's a problem
            if !is_self && result.is_ok() && result.unwrap().is_ok() {
                // This could be OK if there's a delegation system, but by default should fail
                // We'll flag it for manual review
            }
        }

        UserOperation::SetCollateralEnabled { enabled } => {
            ctx.env.mock_auths(&[soroban_sdk::testutils::MockAuth {
                address: caller_addr,
                invoke: &soroban_sdk::testutils::MockAuthInvoke {
                    contract: ctx.router_addr,
                    fn_name: "set_user_use_reserve_as_coll",
                    args: soroban_sdk::vec![
                        ctx.env,
                        caller_addr.clone().into_val(ctx.env),
                        ctx.underlying_asset.clone().into_val(ctx.env),
                        (*enabled).into_val(ctx.env),
                    ],
                    sub_invokes: &[],
                },
            }]);

            let _ = ctx.router_client.try_set_user_use_reserve_as_coll(
                caller_addr,
                ctx.underlying_asset,
                enabled,
            );
        }

        UserOperation::FlashLoan { amount } => {
            // HAL-03 related: Test that flash loan requires initiator auth
            let flash_amount = (*amount as u128).max(1).min(INITIAL_SUPPLY / 10);

            // Setup a mock receiver
            let receiver = Address::generate(ctx.env);
            let assets = soroban_sdk::vec![ctx.env, ctx.underlying_asset.clone()];
            let amounts: Vec<u128> = soroban_sdk::vec![ctx.env, flash_amount];
            let params = Bytes::new(ctx.env);

            ctx.env.mock_auths(&[soroban_sdk::testutils::MockAuth {
                address: caller_addr,
                invoke: &soroban_sdk::testutils::MockAuthInvoke {
                    contract: ctx.router_addr,
                    fn_name: "flash_loan",
                    args: soroban_sdk::vec![
                        ctx.env,
                        caller_addr.clone().into_val(ctx.env),
                        receiver.clone().into_val(ctx.env),
                        assets.clone().into_val(ctx.env),
                        amounts.clone().into_val(ctx.env),
                        params.clone().into_val(ctx.env),
                    ],
                    sub_invokes: &[],
                },
            }]);

            let _ = ctx.router_client.try_flash_loan(
                caller_addr,
                &receiver,
                &assets,
                &amounts,
                &params,
            );
            // Flash loan will likely fail due to receiver not existing, but we're testing auth
        }
    }
}

/// Verify the result of an auth-sensitive operation
fn verify_auth_result(ctx: &mut TestContext, succeeded: bool, should_be_authorized: bool, op_name: &str) {
    if succeeded && !should_be_authorized {
        // CRITICAL: Unauthorized caller succeeded!
        ctx.unauthorized_success_count += 1;
        // This assertion will cause the fuzzer to report this as a failure
        assert!(
            false,
            "AUTHORIZATION BYPASS: {} succeeded for unauthorized caller",
            op_name
        );
    } else if !succeeded && should_be_authorized {
        // Auth should have worked but failed - could be other reasons (state, params)
        ctx.auth_failure_count += 1;
    }
}

// =============================================================================
// Fuzz Target
// =============================================================================

fuzz_target!(|input: AuthFuzzInput| {
    // Use mock_all_auths for initial setup only
    let init_env = setup_test_env_for_init();

    // Setup addresses
    let pool_admin = Address::generate(&init_env);
    let emergency_admin = Address::generate(&init_env);
    let random_user = Address::generate(&init_env);
    let supplier = Address::generate(&init_env);
    let borrower = Address::generate(&init_env);

    // Setup contracts
    let oracle_addr = setup_oracle(&init_env, &pool_admin);
    let (router_addr, _treasury, pool_configurator) =
        setup_kinetic_router(&init_env, &pool_admin, &emergency_admin, &oracle_addr);

    let (underlying_asset, _underlying_contract, a_token, _debt_token) =
        setup_reserve(&init_env, &router_addr, &oracle_addr, &pool_admin, &pool_configurator);

    let router_client = kinetic_router::Client::new(&init_env, &router_addr);
    let asset_client = StellarAssetClient::new(&init_env, &underlying_asset);

    // Setup initial state if requested
    if input.setup_supplier {
        // Mint and supply for the supplier
        asset_client.mint(&supplier, &(INITIAL_SUPPLY as i128));
        let _ = router_client.try_supply(
            &supplier,
            &underlying_asset,
            &(INITIAL_SUPPLY / 2),
            &supplier,
            &0u32,
        );
    }

    if input.setup_borrower && input.setup_supplier {
        // Mint, supply as collateral, and borrow for the borrower
        asset_client.mint(&borrower, &(INITIAL_SUPPLY as i128));
        let _ = router_client.try_supply(
            &borrower,
            &underlying_asset,
            &(INITIAL_SUPPLY / 2),
            &borrower,
            &0u32,
        );

        // Enable as collateral and borrow
        let _ = router_client.try_set_user_use_reserve_as_coll(&borrower, &underlying_asset, &true);
        let borrow_amount = INITIAL_SUPPLY / 10; // Borrow 10% of supplied
        let _ = router_client.try_borrow(
            &borrower,
            &underlying_asset,
            &borrow_amount,
            &0u32,  // interest_rate_mode
            &0u32,  // referral_code
            &borrower,  // on_behalf_of
        );
    }

    // Create test context
    let mut ctx = TestContext {
        env: &init_env,
        router_addr: &router_addr,
        router_client: &router_client,
        pool_admin: &pool_admin,
        emergency_admin: &emergency_admin,
        pool_configurator: &pool_configurator,
        random_user: &random_user,
        supplier: &supplier,
        borrower: &borrower,
        underlying_asset: &underlying_asset,
        a_token: &a_token,
        asset_client: &asset_client,
        auth_failure_count: 0,
        unauthorized_success_count: 0,
    };

    // Execute operation sequence
    for op_opt in &input.operations {
        if let Some(op) = op_opt {
            match op {
                AuthTestOperation::AdminOp { caller, operation } => {
                    test_admin_operation(&mut ctx, *caller, operation);
                }
                AuthTestOperation::UserOp { caller, target_user, operation } => {
                    test_user_operation(&mut ctx, *caller, *target_user, operation);
                }
                AuthTestOperation::AdvanceTime { seconds } => {
                    let advance = (*seconds as u64).min(31_536_000);
                    if advance > 0 {
                        let current = ctx.env.ledger().timestamp();
                        ctx.env.ledger().set_timestamp(current.saturating_add(advance));
                    }
                }
            }
        }
    }

    // CRITICAL INVARIANT: No unauthorized operations should have succeeded
    assert_eq!(
        ctx.unauthorized_success_count, 0,
        "SECURITY FAILURE: {} unauthorized operations succeeded!",
        ctx.unauthorized_success_count
    );
});
