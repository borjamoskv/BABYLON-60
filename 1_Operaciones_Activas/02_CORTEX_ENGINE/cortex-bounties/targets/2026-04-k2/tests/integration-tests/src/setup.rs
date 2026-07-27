//! # Integration Test Setup Utilities
//!
//! Common setup functions for deploying and configuring the K2 protocol
//! in integration tests.

use crate::{
    a_token, debt_token, flash_liquidation_helper, incentives,
    interest_rate_strategy, kinetic_router, pool_configurator, price_oracle,
    treasury,
};
use k2_shared::{Asset, InitReserveParams, KineticRouterError, PriceData, TEST_PRICE_DEFAULT, WAD};
use soroban_sdk::{
    contract, contractimpl, contracttype,
    testutils::{Address as _, Ledger, LedgerInfo, StellarAssetContract},
    token, Address, Env, IntoVal, Symbol, Vec,
};

// =============================================================================
// Protocol Deployment Result
// =============================================================================

/// Contains all deployed protocol contract addresses
pub struct ProtocolContracts {
    pub kinetic_router: Address,
    pub price_oracle: Address,
    pub incentives: Address,
    pub treasury: Address,
    pub pool_configurator: Address,
    pub mock_dex_router: Address,
}

/// Contains addresses for a single reserve
pub struct ReserveContracts {
    pub underlying: Address,
    pub a_token: Address,
    pub debt_token: Address,
    pub interest_rate_strategy: Address,
    pub stellar_asset: StellarAssetContract,
}

/// Full test environment with all protocol contracts
pub struct TestEnv {
    pub env: Env,
    pub admin: Address,
    pub emergency_admin: Address,
    pub protocol: ProtocolContracts,
}

/// Test protocol with clients and test users for easy testing
pub struct TestProtocol<'a> {
    pub env: &'a Env,
    pub admin: Address,
    pub emergency_admin: Address,
    pub oracle_admin: Address,
    pub liquidity_provider: Address,
    pub user: Address,
    pub liquidator: Address,
    pub kinetic_router: kinetic_router::Client<'a>,
    pub kinetic_router_address: Address,
    pub price_oracle: price_oracle::Client<'a>,
    pub incentives: incentives::Client<'a>,
    pub treasury: treasury::Client<'a>,
    pub pool_configurator: pool_configurator::Client<'a>,
    pub mock_dex_router: Address,
    pub a_token: a_token::Client<'a>,
    pub debt_token: debt_token::Client<'a>,
    pub interest_rate_strategy: interest_rate_strategy::Client<'a>,
    pub underlying_asset: Address,
    pub underlying_asset_client: token::Client<'a>,
}

/// Test protocol with two assets for flash liquidation testing
pub struct TestProtocolTwoAssets<'a> {
    pub env: &'a Env,
    pub admin: Address,
    pub emergency_admin: Address,
    pub oracle_admin: Address,
    pub liquidity_provider: Address,
    pub user: Address,
    pub liquidator: Address,
    pub kinetic_router: kinetic_router::Client<'a>,
    pub price_oracle: price_oracle::Client<'a>,
    pub incentives: incentives::Client<'a>,
    pub treasury: treasury::Client<'a>,
    pub pool_configurator: pool_configurator::Client<'a>,
    pub mock_dex_router: Address,
    // USDC (collateral asset)
    pub usdc_asset: Address,
    pub usdc_client: token::Client<'a>,
    pub usdc_a_token: a_token::Client<'a>,
    pub usdc_debt_token: debt_token::Client<'a>,
    // USDT (debt asset)
    pub usdt_asset: Address,
    pub usdt_client: token::Client<'a>,
    pub usdt_a_token: a_token::Client<'a>,
    pub usdt_debt_token: debt_token::Client<'a>,
    pub interest_rate_strategy: interest_rate_strategy::Client<'a>,
}

// =============================================================================
// Environment Setup
// =============================================================================

/// Create a default test environment with mocked auths
pub fn create_test_env() -> Env {
    let env = Env::default();
    env.mock_all_auths_allowing_non_root_auth();
    set_default_ledger(&env);
    env
}

/// Create a test environment with realistic budget limits matching testnet/mainnet
///
/// Testnet typically has stricter limits than default test environment.
/// Actual Stellar Soroban network limits (with 20% safety buffer):
/// - CPU: 80M instructions (100M limit - 20% buffer)
/// - Memory: 40MB (actual Stellar network limit)
pub fn create_test_env_with_budget_limits() -> Env {
    let env = Env::default();
    env.mock_all_auths();
    set_default_ledger(&env);

    // Set realistic budget limits matching testnet/mainnet constraints
    // Testnet/mainnet has 100M CPU instructions and 40MB memory limits
    let mut budget = env.cost_estimate().budget();

    // Set high limits for full test (protocol deployment + operation)
    // The gas_tracking module checks individual operations against realistic limits
    budget.reset_limits(100_000_000, 40_000_000); // 100M CPU, 40MB memory for full test

    env
}

/// Set default ledger info for tests
pub fn set_default_ledger(env: &Env) {
    env.ledger().set(LedgerInfo {
        sequence_number: 100,
        protocol_version: 23,
        timestamp: 1_700_000_000,
        network_id: Default::default(),
        base_reserve: 10,
        min_temp_entry_ttl: 10,
        min_persistent_entry_ttl: 10,
        max_entry_ttl: 3_110_400, // ~6 months
    });
}

/// Advance ledger by specified number of seconds
pub fn advance_ledger(env: &Env, seconds: u64) {
    let current = env.ledger().timestamp();
    let current_seq = env.ledger().sequence();
    env.ledger().set(LedgerInfo {
        sequence_number: current_seq + (seconds / 5) as u32, // ~5 seconds per ledger
        protocol_version: 23,
        timestamp: current + seconds,
        network_id: Default::default(),
        base_reserve: 10,
        min_temp_entry_ttl: 10,
        min_persistent_entry_ttl: 10,
        max_entry_ttl: 3_110_400,
    });
}

// =============================================================================
// Protocol Deployment
// =============================================================================

/// Deploy the full K2 protocol with all core contracts
pub fn deploy_full_protocol(
    env: &Env,
    admin: &Address,
    emergency_admin: &Address,
) -> ProtocolContracts {
    // 1. Deploy Price Oracle
    let price_oracle_id = env.register(price_oracle::WASM, ());
    let price_oracle_client = price_oracle::Client::new(env, &price_oracle_id);

    // Initialize with a mock reflector stub (implements decimals())
    let mock_reflector = env.register(ReflectorStub, ());
    let base_currency = Address::generate(env);
    let native_xlm = Address::generate(env);
    price_oracle_client.initialize(admin, &mock_reflector, &base_currency, &native_xlm);

    // 2. Deploy Treasury
    let treasury_id = env.register(treasury::WASM, ());
    let treasury_client = treasury::Client::new(env, &treasury_id);
    treasury_client.initialize(admin);

    // 3. Deploy mock DEX router
    let mock_dex_router_id = env.register(MockSoroswapRouter, ());

    // 4. Deploy Kinetic Router (main lending pool)
    let kinetic_router_id = env.register(kinetic_router::WASM, ());
    let kinetic_router_client = kinetic_router::Client::new(env, &kinetic_router_id);

    kinetic_router_client.initialize(
        admin,
        emergency_admin,
        &price_oracle_id,
        &treasury_id,
        &mock_dex_router_id,
        &None, // No incentives controller initially
    );

    // 5. Liquidation Engine - commented out due to type conflicts
    let _liquidation_engine_id = Address::generate(env);

    // 6. Deploy Incentives Controller
    let incentives_id = env.register(incentives::WASM, ());
    let incentives_client = incentives::Client::new(env, &incentives_id);
    incentives_client.initialize(admin, &kinetic_router_id);

    // 7. Deploy Pool Configurator
    let pool_configurator_id = env.register(pool_configurator::WASM, ());
    let pool_configurator_client = pool_configurator::Client::new(env, &pool_configurator_id);
    pool_configurator_client.initialize(admin, &kinetic_router_id, &price_oracle_id);

    let mut set_config_args = Vec::new(env);
    set_config_args.push_back(pool_configurator_id.clone().into_val(env));
    let _: Result<(), KineticRouterError> = env.invoke_contract(
        &kinetic_router_id,
        &Symbol::new(env, "set_pool_configurator"),
        set_config_args,
    );

    ProtocolContracts {
        kinetic_router: kinetic_router_id,
        price_oracle: price_oracle_id,
        incentives: incentives_id,
        treasury: treasury_id,
        pool_configurator: pool_configurator_id,
        mock_dex_router: mock_dex_router_id,
    }
}

/// Deploy a complete test environment
pub fn deploy_test_env() -> TestEnv {
    let env = create_test_env();
    let admin = Address::generate(&env);
    let emergency_admin = Address::generate(&env);

    let protocol = deploy_full_protocol(&env, &admin, &emergency_admin);

    TestEnv {
        env,
        admin,
        emergency_admin,
        protocol,
    }
}

// =============================================================================
// Reserve Setup
// =============================================================================

/// Create a new test token using Stellar Asset Contract
pub fn create_test_token(env: &Env, admin: &Address) -> StellarAssetContract {
    env.register_stellar_asset_contract_v2(admin.clone())
}

/*
pub fn setup_reserve(
    env: &Env,
    kinetic_router: &Address,
    admin: &Address,
    name: &str,
    symbol: &str,
    decimals: u32,
    params: InitReserveParams,
) -> ReserveContracts {
    // Create underlying token
    let underlying_token = create_test_token(env, admin);
    let underlying_addr = underlying_token.address();

    // Deploy Interest Rate Strategy
    let interest_rate_strategy_id = env.register(interest_rate_strategy::WASM, ());
    let interest_rate_strategy_client = interest_rate_strategy::Client::new(env, &interest_rate_strategy_id);

    // Initialize with standard parameters:
    // - 2% base rate
    // - 10% slope1 (below optimal)
    // - 100% slope2 (above optimal)
    // - 80% optimal utilization
    interest_rate_strategy_client.initialize(
        admin,
        &(2 * RAY / 100),   // base_variable_borrow_rate: 2%
        &(10 * RAY / 100),  // variable_rate_slope1: 10%
        &(100 * RAY / 100), // variable_rate_slope2: 100%
        &(80 * RAY / 100),  // optimal_utilization_rate: 80%
    );

    // Deploy A-Token
    let a_token_id = env.register(a_token::WASM, ());
    let a_token_client = a_token::Client::new(env, &a_token_id);
    let a_name = String::from_str(env, name);
    let a_symbol = String::from_str(env, symbol);
    a_token_client.initialize(
        admin,
        &underlying_addr,
        kinetic_router,
        &a_name,
        &a_symbol,
        &decimals,
    );

    // Deploy Debt Token
    let debt_token_id = env.register(debt_token::WASM, ());
    let debt_token_client = debt_token::Client::new(env, &debt_token_id);
    let debt_name = String::from_str(env, name);
    let debt_symbol = String::from_str(env, symbol);
    debt_token_client.initialize(
        admin,
        &underlying_addr,
        kinetic_router,
        &debt_name,
        &debt_symbol,
        &decimals,
    );

    // Initialize reserve in Kinetic Router
    let kinetic_router_client = kinetic_router::Client::new(env, kinetic_router);
    let treasury = Address::generate(env);

    kinetic_router_client.init_reserve(
        &contracts.pool_configurator,
        &underlying_addr,
        &a_token_id,
        &debt_token_id,
        &interest_rate_strategy_id,
        &treasury,
        &params,
    );

    ReserveContracts {
        underlying: underlying_addr,
        a_token: a_token_id,
        debt_token: debt_token_id,
        interest_rate_strategy: interest_rate_strategy_id,
        stellar_asset: underlying_token,
    }
}
*/

/// Create default reserve parameters
pub fn default_reserve_params() -> InitReserveParams {
    InitReserveParams {
        decimals: 7,
        ltv: 8000,                   // 80%
        liquidation_threshold: 8500, // 85%
        liquidation_bonus: 500,      // 5%
        reserve_factor: 1000,        // 10%
        supply_cap: 1_000_000_000,   // 1B tokens
        borrow_cap: 500_000_000,     // 500M tokens
        borrowing_enabled: true,
        flashloan_enabled: true,
    }
}

/// Create conservative reserve parameters (lower LTV)
pub fn conservative_reserve_params() -> InitReserveParams {
    InitReserveParams {
        decimals: 7,
        ltv: 5000,                   // 50%
        liquidation_threshold: 6500, // 65%
        liquidation_bonus: 1000,     // 10%
        reserve_factor: 2000,        // 20%
        supply_cap: 100_000_000,     // 100M tokens
        borrow_cap: 50_000_000,      // 50M tokens
        borrowing_enabled: true,
        flashloan_enabled: true,
    }
}

// =============================================================================
// Oracle Setup
// =============================================================================

/*
pub fn set_oracle_price(env: &Env, oracle: &Address, asset: &Address, price: u128) {
    let oracle_client = price_oracle::Client::new(env, oracle);
    let asset_enum = Asset::Stellar(asset.clone());

    // Add asset to oracle whitelist
    oracle_client.add_asset(&Address::generate(env), &asset_enum);

    // Set manual override price
    oracle_client.set_manual_override(&Address::generate(env), &asset_enum, &Some(price), &Some(env.ledger().timestamp() + 86400));
}
*/

// =============================================================================
// Token Operations
// =============================================================================

/// Mint tokens to a user
pub fn mint_tokens(env: &Env, token: &StellarAssetContract, to: &Address, amount: i128) {
    let stellar_client = token::StellarAssetClient::new(env, &token.address());
    stellar_client.mint(to, &amount);
}

/// Approve tokens for spending
pub fn approve_tokens(
    env: &Env,
    token_addr: &Address,
    owner: &Address,
    spender: &Address,
    amount: i128,
) {
    let token_client = token::Client::new(env, token_addr);
    let expiration = env.ledger().sequence() + 100_000;
    token_client.approve(owner, spender, &amount, &expiration);
}

/// Get token balance
pub fn get_token_balance(env: &Env, token_addr: &Address, account: &Address) -> i128 {
    let token_client = token::Client::new(env, token_addr);
    token_client.balance(account)
}

// =============================================================================
// Lending Operations (Convenience Wrappers)
// =============================================================================

/// Supply tokens to the lending pool
pub fn supply(env: &Env, kinetic_router: &Address, user: &Address, asset: &Address, amount: u128) {
    let client = kinetic_router::Client::new(env, kinetic_router);
    client.supply(user, asset, &amount, user, &0);
}

/// Borrow tokens from the lending pool
pub fn borrow(env: &Env, kinetic_router: &Address, user: &Address, asset: &Address, amount: u128) {
    let client = kinetic_router::Client::new(env, kinetic_router);
    client.borrow(user, asset, &amount, &1, &0, user);
}

/// Repay borrowed tokens
pub fn repay(env: &Env, kinetic_router: &Address, user: &Address, asset: &Address, amount: u128) {
    let client = kinetic_router::Client::new(env, kinetic_router);
    client.repay(user, asset, &amount, &1, user);
}

/// Withdraw supplied tokens
pub fn withdraw(
    env: &Env,
    kinetic_router: &Address,
    user: &Address,
    asset: &Address,
    amount: u128,
) {
    let client = kinetic_router::Client::new(env, kinetic_router);
    client.withdraw(user, asset, &amount, user);
}

// =============================================================================
// Quick Test Setup
// =============================================================================

/// Quick setup for integration tests - deploys full protocol with a test reserve
pub fn deploy_test_protocol(env: &Env) -> TestProtocol {
    let admin = Address::generate(env);
    let emergency_admin = Address::generate(env);
    let oracle_admin = admin.clone();
    let liquidity_provider = Address::generate(env);
    let user = Address::generate(env);
    let liquidator = Address::generate(env);

    // Deploy core protocol
    let contracts = deploy_full_protocol(env, &admin, &emergency_admin);

    // Create clients
    let kinetic_router = kinetic_router::Client::new(env, &contracts.kinetic_router);
    let price_oracle = price_oracle::Client::new(env, &contracts.price_oracle);
    let incentives = incentives::Client::new(env, &contracts.incentives);
    let treasury = treasury::Client::new(env, &contracts.treasury);
    let pool_configurator = pool_configurator::Client::new(env, &contracts.pool_configurator);
    let mock_dex_router = contracts.mock_dex_router.clone();

    // Create a test token using Stellar Asset Contract
    let underlying_asset_sac = env.register_stellar_asset_contract_v2(admin.clone());
    let underlying_asset_address = underlying_asset_sac.address();

    // Create token client using the imported token module
    let underlying_asset_client = token::Client::new(env, &underlying_asset_address);

    // Mint tokens to test users using the SAC client
    let sac_admin_client = token::StellarAssetClient::new(env, &underlying_asset_address);
    sac_admin_client.mint(&liquidity_provider, &100_000_000_000_000i128);
    sac_admin_client.mint(&user, &100_000_000_000_000i128);
    sac_admin_client.mint(&liquidator, &100_000_000_000_000i128);

    // Approve kinetic router to spend tokens for all users
    underlying_asset_client.approve(
        &liquidity_provider,
        &contracts.kinetic_router,
        &i128::MAX,
        &200000,
    );
    underlying_asset_client.approve(&user, &contracts.kinetic_router, &i128::MAX, &200000);
    underlying_asset_client.approve(&liquidator, &contracts.kinetic_router, &i128::MAX, &200000);

    // Deploy reserve tokens (a-token, debt token, interest rate strategy)
    let a_token_id = env.register(a_token::WASM, ());
    let a_token = a_token::Client::new(env, &a_token_id);

    let debt_token_id = env.register(debt_token::WASM, ());
    let debt_token = debt_token::Client::new(env, &debt_token_id);

    let interest_rate_strategy_id = env.register(interest_rate_strategy::WASM, ());
    let interest_rate_strategy =
        interest_rate_strategy::Client::new(env, &interest_rate_strategy_id);

    // Initialize interest rate strategy
    interest_rate_strategy.initialize(
        &admin,
        &20000000000000000000000000u128, // base_variable_borrow_rate: 2%
        &40000000000000000000000000u128, // variable_rate_slope1: 4%
        &600000000000000000000000000u128, // variable_rate_slope2: 60%
        &800000000000000000000000000u128, // optimal_utilization_rate: 80%
    );

    // Initialize a-token
    a_token.initialize(
        &admin,
        &underlying_asset_address,
        &contracts.kinetic_router,
        &soroban_sdk::String::from_str(env, "Test aToken"),
        &soroban_sdk::String::from_str(env, "aTST"),
        &7u32,
    );

    // Initialize debt token
    debt_token.initialize(
        &admin,
        &underlying_asset_address,
        &contracts.kinetic_router,
        &soroban_sdk::String::from_str(env, "Test Debt"),
        &soroban_sdk::String::from_str(env, "dTST"),
        &7u32,
    );

    // Set oracle price for the asset
    let asset_enum = price_oracle::Asset::Stellar(underlying_asset_address.clone());
    price_oracle.add_asset(&admin, &asset_enum);
    // Set price to 1 USD (oracle uses 14 decimals, not 18!)
    price_oracle.set_manual_override(&admin, &asset_enum, &Some(1_000_000_000_000_000u128), &Some(env.ledger().timestamp() + 604_800));

    // Initialize reserve in kinetic router
    let reserve_params = kinetic_router::InitReserveParams {
        decimals: 7,
        ltv: 8000,
        liquidation_threshold: 8500,
        liquidation_bonus: 500,
        reserve_factor: 1000,
        supply_cap: 1_000_000_000_000_000,
        borrow_cap: 500_000_000_000_000,
        borrowing_enabled: true,
        flashloan_enabled: true,
    };

    kinetic_router.init_reserve(
        &contracts.pool_configurator,
        &underlying_asset_address,
        &a_token_id,
        &debt_token_id,
        &interest_rate_strategy_id,
        &contracts.treasury,
        &reserve_params,
    );

    TestProtocol {
        env,
        admin,
        emergency_admin,
        oracle_admin,
        liquidity_provider,
        user,
        liquidator,
        kinetic_router,
        kinetic_router_address: contracts.kinetic_router,
        price_oracle,
        incentives,
        treasury,
        pool_configurator,
        mock_dex_router,
        a_token,
        debt_token,
        interest_rate_strategy,
        underlying_asset: underlying_asset_address,
        underlying_asset_client,
    }
}

/// Setup protocol with two assets (USDC and USDT) for flash liquidation testing
pub fn deploy_test_protocol_two_assets(env: &Env) -> TestProtocolTwoAssets {
    let admin = Address::generate(env);
    let emergency_admin = Address::generate(env);
    let oracle_admin = admin.clone();
    let liquidity_provider = Address::generate(env);
    let user = Address::generate(env);
    let liquidator = Address::generate(env);

    // Deploy core protocol
    let contracts = deploy_full_protocol(env, &admin, &emergency_admin);

    // Create clients
    let kinetic_router = kinetic_router::Client::new(env, &contracts.kinetic_router);
    let price_oracle = price_oracle::Client::new(env, &contracts.price_oracle);
    let incentives = incentives::Client::new(env, &contracts.incentives);
    let treasury = treasury::Client::new(env, &contracts.treasury);
    let pool_configurator = pool_configurator::Client::new(env, &contracts.pool_configurator);

    // Create USDC asset (collateral) first - needed for Soroswap setup
    let usdc_sac = env.register_stellar_asset_contract_v2(admin.clone());
    let usdc_address = usdc_sac.address();
    let usdc_client = token::Client::new(env, &usdc_address);
    let usdc_sac_admin = token::StellarAssetClient::new(env, &usdc_address);

    // Create USDT asset (debt)
    let usdt_sac = env.register_stellar_asset_contract_v2(admin.clone());
    let usdt_address = usdt_sac.address();
    let usdt_client = token::Client::new(env, &usdt_address);
    let usdt_sac_admin = token::StellarAssetClient::new(env, &usdt_address);

    // Setup mock Soroswap infrastructure with seeded liquidity
    // Seed with 10M USDC and 10M USDT for swaps (enough for liquidation)
    let usdc_liquidity = 10_000_000_000_000i128; // 10M USDC (7 decimals)
    let usdt_liquidity = 10_000_000_000_000i128; // 10M USDT (7 decimals)

    // Mint liquidity to admin for seeding pool
    usdc_sac_admin.mint(&admin, &usdc_liquidity);
    usdt_sac_admin.mint(&admin, &usdt_liquidity);

    // Setup mock Soroswap router/factory/pair with liquidity
    let mock_dex_router = setup_mock_soroswap_with_liquidity(
        env,
        &admin,
        &usdc_address,
        &usdt_address,
        usdc_liquidity,
        usdt_liquidity,
    );

    // Set DEX router on kinetic router
    kinetic_router.set_dex_router(&mock_dex_router);

    // Mint tokens to test users
    usdc_sac_admin.mint(&liquidity_provider, &100_000_000_000_000i128);
    usdc_sac_admin.mint(&user, &100_000_000_000_000i128);
    usdc_sac_admin.mint(&liquidator, &100_000_000_000_000i128);

    usdt_sac_admin.mint(&liquidity_provider, &100_000_000_000_000i128);
    usdt_sac_admin.mint(&user, &100_000_000_000_000i128);
    usdt_sac_admin.mint(&liquidator, &100_000_000_000_000i128);

    // Approve kinetic router for all users
    usdc_client.approve(
        &liquidity_provider,
        &contracts.kinetic_router,
        &i128::MAX,
        &200000,
    );
    usdc_client.approve(&user, &contracts.kinetic_router, &i128::MAX, &200000);
    usdc_client.approve(&liquidator, &contracts.kinetic_router, &i128::MAX, &200000);

    usdt_client.approve(
        &liquidity_provider,
        &contracts.kinetic_router,
        &i128::MAX,
        &200000,
    );
    usdt_client.approve(&user, &contracts.kinetic_router, &i128::MAX, &200000);
    usdt_client.approve(&liquidator, &contracts.kinetic_router, &i128::MAX, &200000);

    // Approve DEX router to spend tokens for swaps
    usdc_client.approve(&admin, &mock_dex_router, &i128::MAX, &200000);
    usdt_client.approve(&admin, &mock_dex_router, &i128::MAX, &200000);

    // Deploy reserve tokens for USDC
    let usdc_a_token_id = env.register(a_token::WASM, ());
    let usdc_a_token = a_token::Client::new(env, &usdc_a_token_id);
    let usdc_debt_token_id = env.register(debt_token::WASM, ());
    let usdc_debt_token = debt_token::Client::new(env, &usdc_debt_token_id);

    // Deploy reserve tokens for USDT
    let usdt_a_token_id = env.register(a_token::WASM, ());
    let usdt_a_token = a_token::Client::new(env, &usdt_a_token_id);
    let usdt_debt_token_id = env.register(debt_token::WASM, ());
    let usdt_debt_token = debt_token::Client::new(env, &usdt_debt_token_id);

    // Deploy interest rate strategy (shared)
    let interest_rate_strategy_id = env.register(interest_rate_strategy::WASM, ());
    let interest_rate_strategy =
        interest_rate_strategy::Client::new(env, &interest_rate_strategy_id);

    // Initialize interest rate strategy
    interest_rate_strategy.initialize(
        &admin,
        &20000000000000000000000000u128, // base_variable_borrow_rate: 2%
        &40000000000000000000000000u128, // variable_rate_slope1: 4%
        &600000000000000000000000000u128, // variable_rate_slope2: 60%
        &800000000000000000000000000u128, // optimal_utilization_rate: 80%
    );

    // Initialize USDC a-token and debt token
    usdc_a_token.initialize(
        &admin,
        &usdc_address,
        &contracts.kinetic_router,
        &soroban_sdk::String::from_str(env, "aUSDC"),
        &soroban_sdk::String::from_str(env, "aUSDC"),
        &7u32,
    );

    usdc_debt_token.initialize(
        &admin,
        &usdc_address,
        &contracts.kinetic_router,
        &soroban_sdk::String::from_str(env, "dUSDC"),
        &soroban_sdk::String::from_str(env, "dUSDC"),
        &7u32,
    );

    // Initialize USDT a-token and debt token
    usdt_a_token.initialize(
        &admin,
        &usdt_address,
        &contracts.kinetic_router,
        &soroban_sdk::String::from_str(env, "aUSDT"),
        &soroban_sdk::String::from_str(env, "aUSDT"),
        &7u32,
    );

    usdt_debt_token.initialize(
        &admin,
        &usdt_address,
        &contracts.kinetic_router,
        &soroban_sdk::String::from_str(env, "dUSDT"),
        &soroban_sdk::String::from_str(env, "dUSDT"),
        &7u32,
    );

    // Set oracle prices for both assets (oracle uses 14 decimals, not 18!)
    let usdc_asset_enum = price_oracle::Asset::Stellar(usdc_address.clone());
    price_oracle.add_asset(&admin, &usdc_asset_enum);
    price_oracle.set_manual_override(&admin, &usdc_asset_enum, &Some(1_000_000_000_000_000u128), &Some(env.ledger().timestamp() + 604_800)); // $1.00 with 14 decimals, 2 year expiry

    let usdt_asset_enum = price_oracle::Asset::Stellar(usdt_address.clone());
    price_oracle.add_asset(&admin, &usdt_asset_enum);
    price_oracle.set_manual_override(&admin, &usdt_asset_enum, &Some(1_000_000_000_000_000u128), &Some(env.ledger().timestamp() + 604_800)); // $1.00 with 14 decimals, 2 year expiry

    // Initialize USDC reserve
    let usdc_reserve_params = kinetic_router::InitReserveParams {
        decimals: 7,
        ltv: 8000,
        liquidation_threshold: 8500,
        liquidation_bonus: 500,
        reserve_factor: 1000,
        supply_cap: 1_000_000_000_000_000,
        borrow_cap: 500_000_000_000_000,
        borrowing_enabled: true,
        flashloan_enabled: true,
    };

    kinetic_router.init_reserve(
        &contracts.pool_configurator,
        &usdc_address,
        &usdc_a_token_id,
        &usdc_debt_token_id,
        &interest_rate_strategy_id,
        &contracts.treasury,
        &usdc_reserve_params,
    );

    // Initialize USDT reserve
    let usdt_reserve_params = kinetic_router::InitReserveParams {
        decimals: 7,
        ltv: 8000,
        liquidation_threshold: 8500,
        liquidation_bonus: 500,
        reserve_factor: 1000,
        supply_cap: 1_000_000_000_000_000,
        borrow_cap: 500_000_000_000_000,
        borrowing_enabled: true,
        flashloan_enabled: true,
    };

    kinetic_router.init_reserve(
        &contracts.pool_configurator,
        &usdt_address,
        &usdt_a_token_id,
        &usdt_debt_token_id,
        &interest_rate_strategy_id,
        &contracts.treasury,
        &usdt_reserve_params,
    );

    // Deploy and configure flash liquidation helper contract
    // This reduces VM budget overhead by moving heavy validation to a minimal contract
    let flash_helper_id = env.register(flash_liquidation_helper::WASM, ());
    kinetic_router.set_flash_liquidation_helper(&flash_helper_id);

    TestProtocolTwoAssets {
        env,
        admin,
        emergency_admin,
        oracle_admin,
        liquidity_provider,
        user,
        liquidator,
        kinetic_router,
        price_oracle,
        incentives,
        treasury,
        pool_configurator,
        mock_dex_router,
        usdc_asset: usdc_address,
        usdc_client,
        usdc_a_token,
        usdc_debt_token,
        usdt_asset: usdt_address,
        usdt_client,
        usdt_a_token,
        usdt_debt_token,
        interest_rate_strategy,
    }
}

// =============================================================================
// Assertions & Helpers
// =============================================================================

/*
pub fn get_user_account_data(
    env: &Env,
    kinetic_router: &Address,
    user: &Address,
) -> k2_shared::UserAccountData {
    let client = kinetic_router::Client::new(env, kinetic_router);
    client.get_user_account_data(user)
}
*/

/// Check if user health factor is below liquidation threshold
pub fn is_liquidatable(env: &Env, kinetic_router: &Address, user: &Address) -> bool {
    let client = kinetic_router::Client::new(env, kinetic_router);
    let account_data = client.get_user_account_data(user);
    account_data.health_factor < WAD
}

/// Generate multiple test addresses
pub fn generate_users(env: &Env, count: usize) -> soroban_sdk::Vec<Address> {
    let mut users = soroban_sdk::Vec::new(env);
    for _ in 0..count {
        users.push_back(Address::generate(env));
    }
    users
}

// =============================================================================
// Mock Reflector Oracle Stub
// =============================================================================

#[contract]
pub struct ReflectorStub;

#[contractimpl]
impl ReflectorStub {
    pub fn lastprice(env: Env, _asset: Asset) -> Option<PriceData> {
        Some(PriceData {
            price: TEST_PRICE_DEFAULT,
            timestamp: env.ledger().timestamp(),
        })
    }

    pub fn twap(_env: Env, _asset: Asset, _periods: u32) -> Option<i128> {
        Some(TEST_PRICE_DEFAULT as i128)
    }

    pub fn decimals(_env: Env) -> u32 {
        14
    }

    pub fn base(env: Env) -> Asset {
        Asset::Other(Symbol::new(&env, "USD"))
    }
}

// =============================================================================
// Mock Soroswap Infrastructure
// =============================================================================

#[contracttype]
#[derive(Clone)]
enum MockSoroswapDataKey {
    Factory,
    Pair(Address, Address),
}

#[contract]
pub struct MockSoroswapRouter;

#[contractimpl]
impl MockSoroswapRouter {
    pub fn router_initialize(env: Env, factory: Address) {
        env.storage()
            .persistent()
            .set(&MockSoroswapDataKey::Factory, &factory);
    }

    pub fn get_factory(env: Env) -> Address {
        env.storage()
            .persistent()
            .get(&MockSoroswapDataKey::Factory)
            .expect("Factory not initialized")
    }

    pub fn router_get_amounts_out(env: Env, amount_in: i128, _path: Vec<Address>) -> Vec<i128> {
        // Simple 1:1 swap for stablecoins (minus 0.05% fee)
        let mut amounts = Vec::new(&env);
        amounts.push_back(amount_in);
        let amount_out = (amount_in * 9995) / 10000; // 0.05% fee
        amounts.push_back(amount_out);
        amounts
    }

    pub fn swap_exact_tokens_for_tokens(
        env: Env,
        amount_in: i128,
        amount_out_min: i128,
        path: Vec<Address>,
        to: Address,
        _deadline: u64,
    ) -> Vec<i128> {
        let token0 = path.get(0).unwrap();
        let token1 = path.get(1).unwrap();

        let factory = Self::get_factory(env.clone());
        let factory_client = MockSoroswapFactoryClient::new(&env, &factory);
        let pair_address = factory_client.get_pair(&token0, &token1);

        let amount_out = (amount_in * 9995) / 10000;

        if amount_out < amount_out_min {
            panic!("Insufficient output amount");
        }

        let router_address = env.current_contract_address();
        let token1_client = token::Client::new(&env, &token1);
        
        let router_balance = token1_client.balance(&router_address);
        if router_balance < amount_out {
            panic!("Insufficient router liquidity: need {}, have {}", amount_out, router_balance);
        }

        // Authorize the transfer (required in Soroban for contract-to-contract transfers)
        env.authorize_as_current_contract(soroban_sdk::vec![
            &env,
            soroban_sdk::auth::InvokerContractAuthEntry::Contract(
                soroban_sdk::auth::SubContractInvocation {
                    context: soroban_sdk::auth::ContractContext {
                        contract: token1.clone(),
                        fn_name: soroban_sdk::Symbol::new(&env, "transfer"),
                        args: soroban_sdk::vec![
                            &env,
                            router_address.to_val(),
                            to.to_val(),
                            amount_out.into_val(&env),
                        ],
                    },
                    sub_invocations: soroban_sdk::vec![&env],
                },
            ),
        ]);

        let transfer_symbol = soroban_sdk::Symbol::new(&env, "transfer");
        let mut transfer_args = soroban_sdk::Vec::new(&env);
        transfer_args.push_back(router_address.to_val());
        transfer_args.push_back(to.to_val());
        transfer_args.push_back(amount_out.into_val(&env));
        
        let _: () = env.invoke_contract(
            &token1,
            &transfer_symbol,
            transfer_args,
        );

        let mut amounts = Vec::new(&env);
        amounts.push_back(amount_in);
        amounts.push_back(amount_out);
        amounts
    }
}

#[contract]
pub struct MockSoroswapFactory;

#[contractimpl]
impl MockSoroswapFactory {
    pub fn pair_exists(_env: Env, token_a: Address, token_b: Address) -> bool {
        token_a != token_b
    }

    pub fn get_pair(env: Env, token_a: Address, token_b: Address) -> Address {
        // Return same pair address for same token pair
        let (token0, token1) = if token_a < token_b {
            (token_a, token_b)
        } else {
            (token_b, token_a)
        };

        env.storage()
            .persistent()
            .get(&MockSoroswapDataKey::Pair(token0.clone(), token1.clone()))
            .unwrap_or_else(|| {
                // Create new pair address (just return a generated address)
                let pair = Address::generate(&env);
                env.storage()
                    .persistent()
                    .set(&MockSoroswapDataKey::Pair(token0, token1), &pair);
                pair
            })
    }
}

/// Setup mock Soroswap infrastructure with seeded liquidity
/// Returns router address that can handle swaps
pub fn setup_mock_soroswap_with_liquidity(
    env: &Env,
    admin: &Address,
    token0: &Address,
    token1: &Address,
    token0_amount: i128,
    token1_amount: i128,
) -> Address {
    // Deploy factory
    let factory_id = env.register(MockSoroswapFactory, ());

    // Deploy router
    let router_id = env.register(MockSoroswapRouter, ());

    // Initialize router with factory
    let router_client = MockSoroswapRouterClient::new(env, &router_id);
    router_client.router_initialize(&factory_id);

    // Create/get pair
    let factory_client = MockSoroswapFactoryClient::new(env, &factory_id);
    let _pair_id = factory_client.get_pair(token0, token1);

    // Seed liquidity by transferring tokens to router
    // Router will hold the liquidity and can swap from it
    let token0_client = token::Client::new(env, token0);
    let token1_client = token::Client::new(env, token1);

    // Approve router to spend tokens
    token0_client.approve(admin, &router_id, &i128::MAX, &200000);
    token1_client.approve(admin, &router_id, &i128::MAX, &200000);

    // Transfer liquidity to router
    token0_client.transfer(admin, &router_id, &token0_amount);
    token1_client.transfer(admin, &router_id, &token1_amount);

    router_id
}
