#![cfg(test)]

use crate::{a_token, debt_token, interest_rate_strategy, kinetic_router, price_oracle};
use k2_shared::{RAY, SECONDS_PER_YEAR};
use soroban_sdk::{
    contract, contractimpl,
    testutils::{Address as _, Ledger, LedgerInfo},
    token, Address, Env, IntoVal, String, Symbol, Vec,
};

// Mock Reflector Oracle that implements decimals()
#[contract]
pub struct MockReflector;

#[contractimpl]
impl MockReflector {
    pub fn decimals(_env: Env) -> u32 {
        14
    }
}

// Helper function to deploy and initialize interest rate strategy contract
fn setup_interest_rate_strategy(env: &Env, admin: &Address) -> Address {
    let contract_id = env.register(interest_rate_strategy::WASM, ());

    // Initialize using invoke_contract since the client type might not be easily accessible
    let mut init_args = Vec::new(env);
    init_args.push_back(admin.clone().into_val(env));
    init_args.push_back((0_000_000_000_000_000_000u128).into_val(env)); // base_variable_borrow_rate: 1% (in RAY)
    init_args.push_back((40_000_000_000_000_000_000u128).into_val(env)); // variable_rate_slope1: 40% (in RAY)
    init_args.push_back((100_000_000_000_000_000_000u128).into_val(env)); // variable_rate_slope2: 100% (in RAY)
    init_args.push_back((800_000_000_000_000_000_000_000_000u128).into_val(env)); // optimal_utilization_rate: 80% (in RAY)

    let _: () = env.invoke_contract(&contract_id, &Symbol::new(env, "initialize"), init_args);

    contract_id
}

#[test]
fn test_supply_and_get_account_data() {
    let env = Env::default();
    env.mock_all_auths();

    let admin = Address::generate(&env);
    let user = Address::generate(&env);

    let kinetic_router_addr = env.register(kinetic_router::WASM, ());
    let kinetic_router = kinetic_router::Client::new(&env, &kinetic_router_addr);

    let oracle_addr = env.register(price_oracle::WASM, ());
    let oracle_client = price_oracle::Client::new(&env, &oracle_addr);

    let reflector_addr = env.register(MockReflector, ());
    let base_currency = Address::generate(&env);
    let native_xlm = Address::generate(&env);
    oracle_client.initialize(&admin, &reflector_addr, &base_currency, &native_xlm);

    let pool_treasury = Address::generate(&env);
    let dex_router = Address::generate(&env);
    kinetic_router.initialize(
        &admin,
        &admin,
        &oracle_addr,
        &pool_treasury,
        &dex_router,
        &None,
    );

    let pool_configurator = Address::generate(&env);
    kinetic_router.set_pool_configurator(&pool_configurator);

    let token_admin = Address::generate(&env);
    let underlying_token = env.register_stellar_asset_contract_v2(token_admin.clone());
    let underlying_addr = underlying_token.address();

    // Setup interest rate strategy (placeholder for now - would need actual deployment for full testing)
    let interest_rate_strategy = setup_interest_rate_strategy(&env, &admin);
    let treasury = Address::generate(&env);

    let params = kinetic_router::InitReserveParams {
        decimals: 7,
        ltv: 7500,
        liquidation_threshold: 8000,
        liquidation_bonus: 500,
        reserve_factor: 1000,
        supply_cap: 0,
        borrow_cap: 0,
        borrowing_enabled: true,
        flashloan_enabled: true,
    };

    let a_token_addr = env.register(a_token::WASM, ());
    let a_token_client = a_token::Client::new(&env, &a_token_addr);
    let a_name = String::from_str(&env, "Test aToken");
    let a_symbol = String::from_str(&env, "aTEST");
    a_token_client.initialize(
        &admin,
        &underlying_addr,
        &kinetic_router_addr,
        &a_name,
        &a_symbol,
        &params.decimals,
    );

    let debt_token_addr = env.register(debt_token::WASM, ());
    let debt_token_client = debt_token::Client::new(&env, &debt_token_addr);
    let debt_name = String::from_str(&env, "Debt Token");
    let debt_symbol = String::from_str(&env, "dTEST");
    debt_token_client.initialize(
        &admin,
        &underlying_addr,
        &kinetic_router_addr,
        &debt_name,
        &debt_symbol,
        &params.decimals,
    );

    let pool_configurator = Address::generate(&env);
    kinetic_router.set_pool_configurator(&pool_configurator);
    kinetic_router.init_reserve(
        &pool_configurator,
        &underlying_addr,
        &a_token_addr,
        &debt_token_addr,
        &interest_rate_strategy,
        &treasury,
        &params,
    );

    let asset_oracle = price_oracle::Asset::Stellar(underlying_addr.clone());
    oracle_client.add_asset(&admin, &asset_oracle);

    // Oracle price format: 14 decimals, so $1.00 = 100_000_000_000_000
    oracle_client.set_manual_override(&admin, &asset_oracle, &Some(100_000_000_000_000u128), &Some(env.ledger().timestamp() + 86400));

    // Verify price is set
    let price_data = oracle_client.get_asset_price_data(&asset_oracle);
    assert_eq!(price_data.price, 100_000_000_000_000u128);

    // Mint tokens to user
    let mint_amount = 10_000_000_000_000i128; // 1M tokens with 7 decimals
    let stellar_token = token::StellarAssetClient::new(&env, &underlying_addr);
    stellar_token.mint(&user, &mint_amount);

    // Approve lending pool to spend tokens
    let token_client = token::Client::new(&env, &underlying_addr);
    let expiration = env.ledger().sequence() + 1000000; // Valid expiration
    token_client.approve(&user, &kinetic_router_addr, &mint_amount, &expiration);

    // Supply tokens
    let supply_amount = 10_000_000_000_000u128;
    kinetic_router.supply(&user, &underlying_addr, &supply_amount, &user, &0u32);

    // Get user account data - THIS IS WHERE IT WAS PANICKING
    let account_data = kinetic_router.get_user_account_data(&user);

    // Verify account data
    assert!(
        account_data.total_collateral_base > 0,
        "Should have collateral"
    );
    assert_eq!(account_data.total_debt_base, 0, "Should have no debt");
    assert!(
        account_data.available_borrows_base > 0,
        "Should be able to borrow"
    );

    // Expected: 1M USDC at $1.00 = $1M = 1e24 in WAD
    let expected_collateral = 1_000_000_000_000_000_000_000_000u128;
    assert_eq!(
        account_data.total_collateral_base, expected_collateral,
        "Collateral value should be $1M in WAD"
    );
}

#[test]
fn test_borrow_validation() {
    let env = Env::default();
    env.mock_all_auths();

    // Setup addresses
    let admin = Address::generate(&env);
    let user = Address::generate(&env);

    // Deploy and initialize lending pool
    let kinetic_router_addr = env.register(kinetic_router::WASM, ());
    let kinetic_router = kinetic_router::Client::new(&env, &kinetic_router_addr);

    // Deploy mock oracle
    let oracle_addr = env.register(price_oracle::WASM, ());
    let oracle_client = price_oracle::Client::new(&env, &oracle_addr);

    let reflector_addr = env.register(MockReflector, ());
    let base_currency = Address::generate(&env);
    let native_xlm = Address::generate(&env);
    oracle_client.initialize(&admin, &reflector_addr, &base_currency, &native_xlm);

    let pool_treasury = Address::generate(&env);
    let dex_router = Address::generate(&env);
    kinetic_router.initialize(
        &admin,
        &admin,
        &oracle_addr,
        &pool_treasury,
        &dex_router,
        &None,
    );

    let pool_configurator = Address::generate(&env);
    kinetic_router.set_pool_configurator(&pool_configurator);

    // Create underlying token
    let token_admin = Address::generate(&env);
    let underlying_token = env.register_stellar_asset_contract_v2(token_admin.clone());
    let underlying_addr = underlying_token.address();

    // Interest rate strategy placeholder
    // Setup interest rate strategy (placeholder for now - would need actual deployment for full testing)
    let interest_rate_strategy = setup_interest_rate_strategy(&env, &admin);
    let treasury = Address::generate(&env);

    // Initialize reserve with 75% LTV
    let params = kinetic_router::InitReserveParams {
        decimals: 7,
        ltv: 7500, // 75%
        liquidation_threshold: 8000,
        liquidation_bonus: 500,
        reserve_factor: 1000,
        supply_cap: 0,
        borrow_cap: 0,
        borrowing_enabled: true,
        flashloan_enabled: true,
    };

    // Deploy and initialize aToken contract
    let a_token_addr = env.register(a_token::WASM, ());
    let a_token_client = a_token::Client::new(&env, &a_token_addr);
    let a_name = String::from_str(&env, "Test aToken");
    let a_symbol = String::from_str(&env, "aTEST");
    a_token_client.initialize(
        &admin,
        &underlying_addr,
        &kinetic_router_addr,
        &a_name,
        &a_symbol,
        &params.decimals,
    );

    // Deploy and initialize debt token contract
    let debt_token_addr = env.register(debt_token::WASM, ());
    let debt_token_client = debt_token::Client::new(&env, &debt_token_addr);
    let debt_name = String::from_str(&env, "Debt Token");
    let debt_symbol = String::from_str(&env, "dTEST");
    debt_token_client.initialize(
        &admin,
        &underlying_addr,
        &kinetic_router_addr,
        &debt_name,
        &debt_symbol,
        &params.decimals,
    );

    let pool_configurator = Address::generate(&env);
    kinetic_router.set_pool_configurator(&pool_configurator);
    kinetic_router.init_reserve(
        &pool_configurator,
        &underlying_addr,
        &a_token_addr,
        &debt_token_addr,
        &interest_rate_strategy,
        &treasury,
        &params,
    );

    // Whitelist and set price: $1.00 = 100_000_000_000_000 (14 decimals as per oracle spec)
    let asset_oracle = price_oracle::Asset::Stellar(underlying_addr.clone());
    oracle_client.add_asset(&admin, &asset_oracle);
    oracle_client.set_manual_override(&admin, &asset_oracle, &Some(100_000_000_000_000u128), &Some(env.ledger().timestamp() + 86400));

    // Mint and supply 1M tokens
    let mint_amount = 10_000_000_000_000i128;
    let stellar_token = token::StellarAssetClient::new(&env, &underlying_addr);
    stellar_token.mint(&user, &mint_amount);

    // Approve lending pool to spend tokens
    let token_client = token::Client::new(&env, &underlying_addr);
    let expiration = env.ledger().sequence() + 1000000; // Valid expiration
    token_client.approve(&user, &kinetic_router_addr, &mint_amount, &expiration);

    kinetic_router.supply(
        &user,
        &underlying_addr,
        &10_000_000_000_000u128,
        &user,
        &0u32,
    );

    // Get account data
    let account_data = kinetic_router.get_user_account_data(&user);

    // With $1M collateral and 75% LTV, user should be able to borrow up to $750k
    let expected_available = 750_000_000_000_000_000_000_000u128; // $750k in WAD
    assert!(
        account_data.available_borrows_base >= expected_available * 99 / 100, // Allow 1% margin
        "Should be able to borrow at least 75% of collateral"
    );
}

#[test]
fn test_get_protocol_reserves() {
    let env = Env::default();
    env.mock_all_auths();

    // Setup addresses
    let admin = Address::generate(&env);
    let user = Address::generate(&env);

    // Deploy and initialize lending pool
    let kinetic_router_addr = env.register(kinetic_router::WASM, ());
    let kinetic_router = kinetic_router::Client::new(&env, &kinetic_router_addr);

    // Deploy mock oracle
    let oracle_addr = env.register(price_oracle::WASM, ());
    let oracle_client = price_oracle::Client::new(&env, &oracle_addr);

    // Initialize oracle with Reflector address (mock)
    let reflector_addr = env.register(MockReflector, ());
    let base_currency = Address::generate(&env);
    let native_xlm = Address::generate(&env);
    oracle_client.initialize(&admin, &reflector_addr, &base_currency, &native_xlm);

    // Initialize lending pool
    let pool_treasury = Address::generate(&env);
    let dex_router = Address::generate(&env);
    kinetic_router.initialize(
        &admin,
        &admin,
        &oracle_addr,
        &pool_treasury,
        &dex_router,
        &None,
    );

    let pool_configurator = Address::generate(&env);
    kinetic_router.set_pool_configurator(&pool_configurator);

    // Create underlying token
    let token_admin = Address::generate(&env);
    let underlying_token = env.register_stellar_asset_contract_v2(token_admin.clone());
    let underlying_addr = underlying_token.address();

    // Interest rate strategy and treasury placeholders
    // Setup interest rate strategy (placeholder for now - would need actual deployment for full testing)
    let interest_rate_strategy = setup_interest_rate_strategy(&env, &admin);
    let treasury = Address::generate(&env);

    let params = kinetic_router::InitReserveParams {
        decimals: 7,
        ltv: 7500,                   // 75%
        liquidation_threshold: 8000, // 80%
        liquidation_bonus: 500,      // 5%
        reserve_factor: 1000,        // 10%
        supply_cap: 0,               // No cap
        borrow_cap: 0,               // No cap
        borrowing_enabled: true,
        flashloan_enabled: true,
    };

    // Deploy and initialize aToken contract
    let a_token_addr = env.register(a_token::WASM, ());
    let a_token_client = a_token::Client::new(&env, &a_token_addr);
    let a_name = String::from_str(&env, "Test aToken");
    let a_symbol = String::from_str(&env, "aTEST");
    a_token_client.initialize(
        &admin,
        &underlying_addr,
        &kinetic_router_addr,
        &a_name,
        &a_symbol,
        &params.decimals,
    );

    // Deploy and initialize debt token contract
    let debt_token_addr = env.register(debt_token::WASM, ());
    let debt_token_client = debt_token::Client::new(&env, &debt_token_addr);
    let debt_name = String::from_str(&env, "Debt Token");
    let debt_symbol = String::from_str(&env, "dTEST");
    debt_token_client.initialize(
        &admin,
        &underlying_addr,
        &kinetic_router_addr,
        &debt_name,
        &debt_symbol,
        &params.decimals,
    );

    let pool_configurator = Address::generate(&env);
    kinetic_router.set_pool_configurator(&pool_configurator);
    kinetic_router.init_reserve(
        &pool_configurator,
        &underlying_addr,
        &a_token_addr,
        &debt_token_addr,
        &interest_rate_strategy,
        &treasury,
        &params,
    );

    // Whitelist asset in oracle and set price
    let asset_oracle = price_oracle::Asset::Stellar(underlying_addr.clone());
    oracle_client.add_asset(&admin, &asset_oracle);
    oracle_client.set_manual_override(&admin, &asset_oracle, &Some(100_000_000_000_000u128), &Some(env.ledger().timestamp() + 86400));

    // Initially, reserves should be 0
    let initial_reserves = kinetic_router.get_protocol_reserves(&underlying_addr);
    assert_eq!(initial_reserves, 0, "Initial reserves should be 0");

    // Mint tokens to user
    let mint_amount = 10_000_000_000_000i128; // 1M tokens with 7 decimals
    let stellar_token = token::StellarAssetClient::new(&env, &underlying_addr);
    stellar_token.mint(&user, &mint_amount);

    // Approve lending pool to spend tokens
    let token_client = token::Client::new(&env, &underlying_addr);
    let expiration = env.ledger().sequence() + 1000000;
    token_client.approve(&user, &kinetic_router_addr, &mint_amount, &expiration);

    // Supply tokens
    let supply_amount = 10_000_000_000_000u128;
    kinetic_router.supply(&user, &underlying_addr, &supply_amount, &user, &0u32);

    // After supply, reserves should still be 0 (no borrowing yet, no interest accrued)
    let reserves_after_supply = kinetic_router.get_protocol_reserves(&underlying_addr);
    assert_eq!(
        reserves_after_supply, 0,
        "Reserves should be 0 after supply only"
    );

    // Borrow some tokens to generate interest
    let borrow_amount = 5_000_000_000_000u128; // 500k tokens
    kinetic_router.borrow(
        &user,
        &underlying_addr,
        &borrow_amount,
        &1u32, // variable rate (1 = variable, 2 = stable)
        &0u32, // referral code
        &user,
    );

    // After borrowing, reserves may still be 0 if no time has passed for interest to accrue
    // But the function should still work correctly - just verify it doesn't panic
    let _reserves_after_borrow = kinetic_router.get_protocol_reserves(&underlying_addr);
}

#[test]
fn test_collect_protocol_reserves() {
    let env = Env::default();

    // Setup addresses
    let admin = Address::generate(&env);
    let user = Address::generate(&env);
    let non_admin = Address::generate(&env);
    
    // Mock admin auth for initialization
    env.mock_all_auths();

    // Deploy and initialize lending pool
    let kinetic_router_addr = env.register(kinetic_router::WASM, ());
    let kinetic_router = kinetic_router::Client::new(&env, &kinetic_router_addr);

    // Deploy mock oracle
    let oracle_addr = env.register(price_oracle::WASM, ());
    let oracle_client = price_oracle::Client::new(&env, &oracle_addr);

    // Initialize oracle with Reflector address (mock)
    let reflector_addr = env.register(MockReflector, ());
    let base_currency = Address::generate(&env);
    let native_xlm = Address::generate(&env);
    oracle_client.initialize(&admin, &reflector_addr, &base_currency, &native_xlm);

    // Initialize lending pool with treasury
    let pool_treasury = Address::generate(&env);
    let dex_router = Address::generate(&env);
    kinetic_router.initialize(
        &admin,
        &admin,
        &oracle_addr,
        &pool_treasury,
        &dex_router,
        &None,
    );

    let pool_configurator = Address::generate(&env);
    kinetic_router.set_pool_configurator(&pool_configurator);

    // Create underlying token
    let token_admin = Address::generate(&env);
    let underlying_token = env.register_stellar_asset_contract_v2(token_admin.clone());
    let underlying_addr = underlying_token.address();

    // Interest rate strategy and treasury placeholders
    // Setup interest rate strategy (placeholder for now - would need actual deployment for full testing)
    let interest_rate_strategy = setup_interest_rate_strategy(&env, &admin);
    let treasury = Address::generate(&env);

    let params = kinetic_router::InitReserveParams {
        decimals: 7,
        ltv: 7500,                   // 75%
        liquidation_threshold: 8000, // 80%
        liquidation_bonus: 500,      // 5%
        reserve_factor: 1000,        // 10%
        supply_cap: 0,               // No cap
        borrow_cap: 0,               // No cap
        borrowing_enabled: true,
        flashloan_enabled: true,
    };

    // Deploy and initialize aToken contract
    let a_token_addr = env.register(a_token::WASM, ());
    let a_token_client = a_token::Client::new(&env, &a_token_addr);
    let a_name = String::from_str(&env, "Test aToken");
    let a_symbol = String::from_str(&env, "aTEST");
    a_token_client.initialize(
        &admin,
        &underlying_addr,
        &kinetic_router_addr,
        &a_name,
        &a_symbol,
        &params.decimals,
    );

    // Deploy and initialize debt token contract
    let debt_token_addr = env.register(debt_token::WASM, ());
    let debt_token_client = debt_token::Client::new(&env, &debt_token_addr);
    let debt_name = String::from_str(&env, "Debt Token");
    let debt_symbol = String::from_str(&env, "dTEST");
    debt_token_client.initialize(
        &admin,
        &underlying_addr,
        &kinetic_router_addr,
        &debt_name,
        &debt_symbol,
        &params.decimals,
    );

    let pool_configurator = Address::generate(&env);
    kinetic_router.set_pool_configurator(&pool_configurator);
    kinetic_router.init_reserve(
        &pool_configurator,
        &underlying_addr,
        &a_token_addr,
        &debt_token_addr,
        &interest_rate_strategy,
        &treasury,
        &params,
    );

    // Whitelist asset in oracle and set price
    let asset_oracle = price_oracle::Asset::Stellar(underlying_addr.clone());
    oracle_client.add_asset(&admin, &asset_oracle);
    oracle_client.set_manual_override(&admin, &asset_oracle, &Some(100_000_000_000_000u128), &Some(env.ledger().timestamp() + 86400));

    // Mint tokens to user
    let mint_amount = 10_000_000_000_000i128; // 1M tokens with 7 decimals
    let stellar_token = token::StellarAssetClient::new(&env, &underlying_addr);
    stellar_token.mint(&user, &mint_amount);

    // Approve lending pool to spend tokens
    let token_client = token::Client::new(&env, &underlying_addr);
    let expiration = env.ledger().sequence() + 1000000;
    token_client.approve(&user, &kinetic_router_addr, &mint_amount, &expiration);

    // Supply tokens
    let supply_amount = 10_000_000_000_000u128;
    kinetic_router.supply(&user, &underlying_addr, &supply_amount, &user, &0u32);

    // Get treasury address
    let treasury_addr = kinetic_router.get_treasury().unwrap();
    assert_eq!(treasury_addr, pool_treasury, "Treasury should match");

    // Check initial treasury balance
    let initial_treasury_balance = token_client.balance(&treasury_addr);
    assert_eq!(
        initial_treasury_balance, 0,
        "Treasury should start with 0 balance"
    );

    // Try to collect reserves as non-admin - should fail
    env.mock_auths(&[]);
    let result = kinetic_router.try_collect_protocol_reserves(&underlying_addr);
    assert!(
        result.is_err(),
        "Non-admin should not be able to collect reserves"
    );

    // Collect reserves as admin (should succeed even if reserves are 0)
    env.mock_all_auths();
    let collected_amount = kinetic_router.collect_protocol_reserves(&underlying_addr);

    // Initially, reserves should be 0 (no interest accrued yet)
    assert_eq!(collected_amount, 0, "Reserves should be 0 initially");

    // Verify treasury balance didn't change (no reserves to collect)
    let treasury_balance_after = token_client.balance(&treasury_addr);
    assert_eq!(
        treasury_balance_after, initial_treasury_balance,
        "Treasury balance should not change when no reserves exist"
    );

    // Query reserves again - should still be 0
    let reserves_after_collect = kinetic_router.get_protocol_reserves(&underlying_addr);
    assert_eq!(
        reserves_after_collect, 0,
        "Reserves should still be 0 after collection"
    );
}

#[test]
fn test_variable_borrow_index_increases_over_time() {
    let env = Env::default();
    env.mock_all_auths();

    let admin = Address::generate(&env);
    let user = Address::generate(&env);

    let kinetic_router_addr = env.register(kinetic_router::WASM, ());
    let kinetic_router = kinetic_router::Client::new(&env, &kinetic_router_addr);

    let oracle_addr = env.register(price_oracle::WASM, ());
    let oracle_client = price_oracle::Client::new(&env, &oracle_addr);

    let reflector_addr = env.register(MockReflector, ());
    let base_currency = Address::generate(&env);
    let native_xlm = Address::generate(&env);
    oracle_client.initialize(&admin, &reflector_addr, &base_currency, &native_xlm);

    let pool_treasury = Address::generate(&env);
    let dex_router = Address::generate(&env);
    kinetic_router.initialize(
        &admin,
        &admin,
        &oracle_addr,
        &pool_treasury,
        &dex_router,
        &None,
    );

    let pool_configurator = Address::generate(&env);
    kinetic_router.set_pool_configurator(&pool_configurator);

    let token_admin = Address::generate(&env);
    let underlying_token = env.register_stellar_asset_contract_v2(token_admin.clone());
    let underlying_addr = underlying_token.address();

    // Setup interest rate strategy (placeholder for now - would need actual deployment for full testing)
    let interest_rate_strategy = setup_interest_rate_strategy(&env, &admin);
    let treasury = Address::generate(&env);

    let params = kinetic_router::InitReserveParams {
        decimals: 7,
        ltv: 7500,
        liquidation_threshold: 8000,
        liquidation_bonus: 500,
        reserve_factor: 1000,
        supply_cap: 0,
        borrow_cap: 0,
        borrowing_enabled: true,
        flashloan_enabled: true,
    };

    let a_token_addr = env.register(a_token::WASM, ());
    let a_token_client = a_token::Client::new(&env, &a_token_addr);
    let a_name = String::from_str(&env, "Test aToken");
    let a_symbol = String::from_str(&env, "aTEST");
    a_token_client.initialize(
        &admin,
        &underlying_addr,
        &kinetic_router_addr,
        &a_name,
        &a_symbol,
        &params.decimals,
    );

    let debt_token_addr = env.register(debt_token::WASM, ());
    let debt_token_client = debt_token::Client::new(&env, &debt_token_addr);
    let debt_name = String::from_str(&env, "Debt Token");
    let debt_symbol = String::from_str(&env, "dTEST");
    debt_token_client.initialize(
        &admin,
        &underlying_addr,
        &kinetic_router_addr,
        &debt_name,
        &debt_symbol,
        &params.decimals,
    );

    let pool_configurator = Address::generate(&env);
    kinetic_router.set_pool_configurator(&pool_configurator);
    kinetic_router.init_reserve(
        &pool_configurator,
        &underlying_addr,
        &a_token_addr,
        &debt_token_addr,
        &interest_rate_strategy,
        &treasury,
        &params,
    );

    let asset_oracle = price_oracle::Asset::Stellar(underlying_addr.clone());
    oracle_client.add_asset(&admin, &asset_oracle);
    oracle_client.set_manual_override(&admin, &asset_oracle, &Some(100_000_000_000_000u128), &Some(env.ledger().timestamp() + 86400));

    // Mint and supply tokens
    let mint_amount = 10_000_000_000_000i128;
    let stellar_token = token::StellarAssetClient::new(&env, &underlying_addr);
    stellar_token.mint(&user, &mint_amount);
    let token_client = token::Client::new(&env, &underlying_addr);
    let expiration = env.ledger().sequence() + 1000000;
    token_client.approve(&user, &kinetic_router_addr, &mint_amount, &expiration);

    let supply_amount = 10_000_000_000_000u128;
    kinetic_router.supply(&user, &underlying_addr, &supply_amount, &user, &0u32);

    // Borrow tokens
    let borrow_amount = 5_000_000_000_000u128;
    kinetic_router.borrow(&user, &underlying_addr, &borrow_amount, &1u32, &0u32, &user);

    // Get initial variable borrow index
    let reserve_data_before = kinetic_router.get_reserve_data(&underlying_addr);
    let initial_index = reserve_data_before.variable_borrow_index;
    assert_eq!(
        initial_index, RAY,
        "Initial variable borrow index should be RAY (1.0)"
    );

    // Trigger a state update by doing a small supply operation
    // This will calculate interest rates based on current utilization (50% = 5M borrowed / 10M supplied)
    // The rates will be non-zero and stored for the next interest accrual period
    let small_supply = 1u128;
    stellar_token.mint(&user, &(small_supply as i128));
    let expiration_supply = env.ledger().sequence() + 1000000;
    token_client.approve(
        &user,
        &kinetic_router_addr,
        &(small_supply as i128),
        &expiration_supply,
    );
    kinetic_router.supply(&user, &underlying_addr, &small_supply, &user, &0u32);

    // Advance time to accrue interest (1 year for testing to ensure noticeable interest accrual)
    let new_timestamp = env.ledger().timestamp() + SECONDS_PER_YEAR;
    let current_sequence = env.ledger().sequence();
    let max_entry_ttl = 1000000u32;
    env.ledger().set(LedgerInfo {
        timestamp: new_timestamp,
        protocol_version: 23,
        sequence_number: current_sequence + 1,
        network_id: Default::default(),
        base_reserve: 0,
        min_temp_entry_ttl: 0,
        min_persistent_entry_ttl: 0,
        max_entry_ttl: max_entry_ttl,
    });

    // Trigger state update by repaying a small amount to accrue interest
    // This will call update_state() which calculates and applies interest using the rates
    // that were set after the borrow operation
    let repay_amount = 1_000_000u128;
    stellar_token.mint(&user, &(repay_amount as i128));
    let new_expiration = (env.ledger().sequence() as u32) + max_entry_ttl - 1;
    token_client.approve(
        &user,
        &kinetic_router_addr,
        &(repay_amount as i128),
        &new_expiration,
    );
    kinetic_router.repay(&user, &underlying_addr, &repay_amount, &1u32, &user);

    // Check that variable borrow index has increased after interest accrual
    let reserve_data_after = kinetic_router.get_reserve_data(&underlying_addr);
    let updated_index = reserve_data_after.variable_borrow_index;
    assert!(
        updated_index > initial_index,
        "Variable borrow index should increase after interest accrual. Initial: {}, Updated: {}",
        initial_index,
        updated_index
    );
}

#[test]
fn test_index_synchronization_to_token_contracts() {
    let env = Env::default();
    env.mock_all_auths();

    let admin = Address::generate(&env);
    let user = Address::generate(&env);

    let kinetic_router_addr = env.register(kinetic_router::WASM, ());
    let kinetic_router = kinetic_router::Client::new(&env, &kinetic_router_addr);

    let oracle_addr = env.register(price_oracle::WASM, ());
    let oracle_client = price_oracle::Client::new(&env, &oracle_addr);

    let reflector_addr = env.register(MockReflector, ());
    let base_currency = Address::generate(&env);
    let native_xlm = Address::generate(&env);
    oracle_client.initialize(&admin, &reflector_addr, &base_currency, &native_xlm);

    let pool_treasury = Address::generate(&env);
    let dex_router = Address::generate(&env);
    kinetic_router.initialize(
        &admin,
        &admin,
        &oracle_addr,
        &pool_treasury,
        &dex_router,
        &None,
    );

    let pool_configurator = Address::generate(&env);
    kinetic_router.set_pool_configurator(&pool_configurator);

    let token_admin = Address::generate(&env);
    let underlying_token = env.register_stellar_asset_contract_v2(token_admin.clone());
    let underlying_addr = underlying_token.address();

    // Setup interest rate strategy contract
    let interest_rate_strategy = setup_interest_rate_strategy(&env, &admin);
    let treasury = Address::generate(&env);

    let params = kinetic_router::InitReserveParams {
        decimals: 7,
        ltv: 7500,
        liquidation_threshold: 8000,
        liquidation_bonus: 500,
        reserve_factor: 1000,
        supply_cap: 0,
        borrow_cap: 0,
        borrowing_enabled: true,
        flashloan_enabled: true,
    };

    let a_token_addr = env.register(a_token::WASM, ());
    let a_token_client = a_token::Client::new(&env, &a_token_addr);
    let a_name = String::from_str(&env, "Test aToken");
    let a_symbol = String::from_str(&env, "aTEST");
    a_token_client.initialize(
        &admin,
        &underlying_addr,
        &kinetic_router_addr,
        &a_name,
        &a_symbol,
        &params.decimals,
    );

    let debt_token_addr = env.register(debt_token::WASM, ());
    let debt_token_client = debt_token::Client::new(&env, &debt_token_addr);
    let debt_name = String::from_str(&env, "Debt Token");
    let debt_symbol = String::from_str(&env, "dTEST");
    debt_token_client.initialize(
        &admin,
        &underlying_addr,
        &kinetic_router_addr,
        &debt_name,
        &debt_symbol,
        &params.decimals,
    );

    let pool_configurator = Address::generate(&env);
    kinetic_router.set_pool_configurator(&pool_configurator);
    kinetic_router.init_reserve(
        &pool_configurator,
        &underlying_addr,
        &a_token_addr,
        &debt_token_addr,
        &interest_rate_strategy,
        &treasury,
        &params,
    );

    let asset_oracle = price_oracle::Asset::Stellar(underlying_addr.clone());
    oracle_client.add_asset(&admin, &asset_oracle);
    oracle_client.set_manual_override(&admin, &asset_oracle, &Some(100_000_000_000_000u128), &Some(env.ledger().timestamp() + 86400));

    // Mint and supply tokens
    let mint_amount = 10_000_000_000_000i128;
    let stellar_token = token::StellarAssetClient::new(&env, &underlying_addr);
    stellar_token.mint(&user, &mint_amount);
    let token_client = token::Client::new(&env, &underlying_addr);
    let expiration = env.ledger().sequence() + 1000000;
    token_client.approve(&user, &kinetic_router_addr, &mint_amount, &expiration);

    let supply_amount = 10_000_000_000_000u128;
    kinetic_router.supply(&user, &underlying_addr, &supply_amount, &user, &0u32);

    // Borrow tokens
    let borrow_amount = 5_000_000_000_000u128;
    kinetic_router.borrow(&user, &underlying_addr, &borrow_amount, &1u32, &0u32, &user);

    // Get initial indices from router and token contracts
    let reserve_data_before = kinetic_router.get_reserve_data(&underlying_addr);
    let a_token_index_before = a_token_client.get_liquidity_index();
    let debt_token_index_before = debt_token_client.get_borrow_index();

    // Initially, indices should match (both start at RAY)
    assert_eq!(
        reserve_data_before.liquidity_index, a_token_index_before,
        "Initial liquidity indices should match"
    );
    assert_eq!(
        reserve_data_before.variable_borrow_index, debt_token_index_before,
        "Initial variable borrow indices should match"
    );

    // Trigger a state update by doing a small supply operation
    // This will calculate interest rates based on current utilization (50% = 5M borrowed / 10M supplied)
    // The rates will be non-zero and stored for the next interest accrual period
    let small_supply = 1u128;
    stellar_token.mint(&user, &(small_supply as i128));
    let expiration_supply = env.ledger().sequence() + 1000000;
    token_client.approve(
        &user,
        &kinetic_router_addr,
        &(small_supply as i128),
        &expiration_supply,
    );
    kinetic_router.supply(&user, &underlying_addr, &small_supply, &user, &0u32);

    // Advance time to accrue interest (1 year for testing to ensure noticeable interest accrual)
    let new_timestamp = env.ledger().timestamp() + SECONDS_PER_YEAR;
    let current_sequence = env.ledger().sequence();
    let max_entry_ttl = 1000000u32;
    env.ledger().set(LedgerInfo {
        timestamp: new_timestamp,
        protocol_version: 23,
        sequence_number: current_sequence + 1,
        network_id: Default::default(),
        base_reserve: 0,
        min_temp_entry_ttl: 0,
        min_persistent_entry_ttl: 0,
        max_entry_ttl: max_entry_ttl,
    });

    // Trigger state update by repaying a small amount to accrue interest
    // This will call update_state() which calculates and applies interest using the rates
    // that were set after the borrow operation, and then sync_indices_to_tokens() will be called
    let repay_amount = 1_000_000u128;
    stellar_token.mint(&user, &(repay_amount as i128));
    let new_expiration = (env.ledger().sequence() as u32) + max_entry_ttl - 1;
    token_client.approve(
        &user,
        &kinetic_router_addr,
        &(repay_amount as i128),
        &new_expiration,
    );
    kinetic_router.repay(&user, &underlying_addr, &repay_amount, &1u32, &user);

    // After state update, indices should have increased and be synchronized
    let reserve_data_after = kinetic_router.get_reserve_data(&underlying_addr);
    let a_token_index_after = a_token_client.get_liquidity_index();
    let debt_token_index_after = debt_token_client.get_borrow_index();

    // Verify indices have increased after interest accrual
    assert!(
        reserve_data_after.liquidity_index > reserve_data_before.liquidity_index,
        "Liquidity index should increase after interest accrual. Before: {}, After: {}",
        reserve_data_before.liquidity_index,
        reserve_data_after.liquidity_index
    );
    assert!(
        reserve_data_after.variable_borrow_index > reserve_data_before.variable_borrow_index,
        "Variable borrow index should increase after interest accrual. Before: {}, After: {}",
        reserve_data_before.variable_borrow_index,
        reserve_data_after.variable_borrow_index
    );

    // Verify indices are synchronized between router and token contracts
    assert_eq!(
        reserve_data_after.liquidity_index, a_token_index_after,
        "Liquidity indices should be synchronized after state update. Router: {}, aToken: {}",
        reserve_data_after.liquidity_index, a_token_index_after
    );
    assert_eq!(
        reserve_data_after.variable_borrow_index, debt_token_index_after,
        "Variable borrow indices should be synchronized after state update. Router: {}, debtToken: {}",
        reserve_data_after.variable_borrow_index,
        debt_token_index_after
    );
}

#[test]
fn test_borrower_debt_increases_with_interest() {
    let env = Env::default();
    env.mock_all_auths();

    let admin = Address::generate(&env);
    let user = Address::generate(&env);

    let kinetic_router_addr = env.register(kinetic_router::WASM, ());
    let kinetic_router = kinetic_router::Client::new(&env, &kinetic_router_addr);

    let oracle_addr = env.register(price_oracle::WASM, ());
    let oracle_client = price_oracle::Client::new(&env, &oracle_addr);

    let reflector_addr = env.register(MockReflector, ());
    let base_currency = Address::generate(&env);
    let native_xlm = Address::generate(&env);
    oracle_client.initialize(&admin, &reflector_addr, &base_currency, &native_xlm);

    let pool_treasury = Address::generate(&env);
    let dex_router = Address::generate(&env);
    kinetic_router.initialize(
        &admin,
        &admin,
        &oracle_addr,
        &pool_treasury,
        &dex_router,
        &None,
    );

    let pool_configurator = Address::generate(&env);
    kinetic_router.set_pool_configurator(&pool_configurator);

    let token_admin = Address::generate(&env);
    let underlying_token = env.register_stellar_asset_contract_v2(token_admin.clone());
    let underlying_addr = underlying_token.address();

    // Setup interest rate strategy (placeholder for now - would need actual deployment for full testing)
    let interest_rate_strategy = setup_interest_rate_strategy(&env, &admin);
    let treasury = Address::generate(&env);

    let params = kinetic_router::InitReserveParams {
        decimals: 7,
        ltv: 7500,
        liquidation_threshold: 8000,
        liquidation_bonus: 500,
        reserve_factor: 1000,
        supply_cap: 0,
        borrow_cap: 0,
        borrowing_enabled: true,
        flashloan_enabled: true,
    };

    let a_token_addr = env.register(a_token::WASM, ());
    let a_token_client = a_token::Client::new(&env, &a_token_addr);
    let a_name = String::from_str(&env, "Test aToken");
    let a_symbol = String::from_str(&env, "aTEST");
    a_token_client.initialize(
        &admin,
        &underlying_addr,
        &kinetic_router_addr,
        &a_name,
        &a_symbol,
        &params.decimals,
    );

    let debt_token_addr = env.register(debt_token::WASM, ());
    let debt_token_client = debt_token::Client::new(&env, &debt_token_addr);
    let debt_name = String::from_str(&env, "Debt Token");
    let debt_symbol = String::from_str(&env, "dTEST");
    debt_token_client.initialize(
        &admin,
        &underlying_addr,
        &kinetic_router_addr,
        &debt_name,
        &debt_symbol,
        &params.decimals,
    );

    let pool_configurator = Address::generate(&env);
    kinetic_router.set_pool_configurator(&pool_configurator);
    kinetic_router.init_reserve(
        &pool_configurator,
        &underlying_addr,
        &a_token_addr,
        &debt_token_addr,
        &interest_rate_strategy,
        &treasury,
        &params,
    );

    let asset_oracle = price_oracle::Asset::Stellar(underlying_addr.clone());
    oracle_client.add_asset(&admin, &asset_oracle);
    oracle_client.set_manual_override(&admin, &asset_oracle, &Some(100_000_000_000_000u128), &Some(env.ledger().timestamp() + 86400));

    // Mint and supply tokens
    let mint_amount = 10_000_000_000_000i128;
    let stellar_token = token::StellarAssetClient::new(&env, &underlying_addr);
    stellar_token.mint(&user, &mint_amount);
    let token_client = token::Client::new(&env, &underlying_addr);
    let expiration = env.ledger().sequence() + 1000000;
    token_client.approve(&user, &kinetic_router_addr, &mint_amount, &expiration);

    let supply_amount = 10_000_000_000_000u128;
    kinetic_router.supply(&user, &underlying_addr, &supply_amount, &user, &0u32);

    // Borrow tokens
    let borrow_amount = 5_000_000_000_000u128;
    kinetic_router.borrow(&user, &underlying_addr, &borrow_amount, &1u32, &0u32, &user);

    // Get initial debt balance
    let initial_debt = debt_token_client.balance_of(&user);
    assert_eq!(
        initial_debt, borrow_amount as i128,
        "Initial debt should equal borrow amount"
    );

    // First, trigger a state update to calculate interest rates based on current utilization
    // This will set non-zero rates for future interest accrual
    let _reserve_data_after_borrow = kinetic_router.get_reserve_data(&underlying_addr);

    // Advance time to accrue interest (1 year for testing to ensure noticeable interest accrual)
    let new_timestamp = env.ledger().timestamp() + SECONDS_PER_YEAR;
    let current_sequence = env.ledger().sequence();
    let max_entry_ttl = 1000000u32;
    env.ledger().set(LedgerInfo {
        timestamp: new_timestamp,
        protocol_version: 23,
        sequence_number: current_sequence + 1,
        network_id: Default::default(),
        base_reserve: 0,
        min_temp_entry_ttl: 0,
        min_persistent_entry_ttl: 0,
        max_entry_ttl: max_entry_ttl,
    });

    // Trigger state update by repaying a small amount to accrue interest
    // This will call update_state() which calculates and applies interest using the rates
    // that were set after the borrow operation
    let repay_amount = 1_000_000u128;
    stellar_token.mint(&user, &(repay_amount as i128));
    let new_expiration = (env.ledger().sequence() as u32) + max_entry_ttl - 1;
    token_client.approve(
        &user,
        &kinetic_router_addr,
        &(repay_amount as i128),
        &new_expiration,
    );
    kinetic_router.repay(&user, &underlying_addr, &repay_amount, &1u32, &user);

    // The balance calculation uses the updated index, so debt should increase
    let updated_debt = debt_token_client.balance_of(&user);

    // After repaying, debt should decrease, but by less than the repayment amount
    // because interest accrued. This means: (initial_debt - updated_debt) < repay_amount
    let debt_decrease = initial_debt - updated_debt;
    assert!(
        debt_decrease < repay_amount as i128,
        "Debt decrease should be less than repayment amount due to interest accrual. Initial: {}, Updated: {}, Decrease: {}, Repaid: {}",
        initial_debt,
        updated_debt,
        debt_decrease,
        repay_amount
    );
}
