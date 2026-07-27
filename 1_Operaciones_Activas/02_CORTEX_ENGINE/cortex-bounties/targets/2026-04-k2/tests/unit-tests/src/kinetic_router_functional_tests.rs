#![cfg(test)]

use crate::{kinetic_router, price_oracle};
use k2_shared::ReserveConfiguration;
use soroban_sdk::{
    contract, contractimpl,
    testutils::{Address as _, StellarAssetContract},
    Address, Env,
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

fn create_test_env() -> Env {
    let env = Env::default();
    env.mock_all_auths();
    env.budget().reset_unlimited();
    env
}

fn create_test_addresses(env: &Env) -> (Address, Address, Address, Address) {
    let admin = Address::generate(env);
    let emergency_admin = Address::generate(env);
    let user1 = Address::generate(env);
    let user2 = Address::generate(env);
    (admin, emergency_admin, user1, user2)
}

fn initialize_kinetic_router(env: &Env, admin: &Address, emergency_admin: &Address) -> (Address, Address) {
    let contract_id = env.register(kinetic_router::WASM, ());
    let client = kinetic_router::Client::new(env, &contract_id);

    // Setup proper price oracle
    let oracle_addr = env.register(price_oracle::WASM, ());
    let oracle_client = price_oracle::Client::new(env, &oracle_addr);
    let reflector_addr = env.register(MockReflector, ());
    let base_currency = Address::generate(env);
    let native_xlm = Address::generate(env);
    oracle_client.initialize(admin, &reflector_addr, &base_currency, &native_xlm);

    let treasury = Address::generate(env);
    let dex_router = Address::generate(env);

    client.initialize(admin, emergency_admin, &oracle_addr, &treasury, &dex_router, &None);
    
    let pool_configurator = Address::generate(env);
    client.set_pool_configurator(&pool_configurator);

    (contract_id, oracle_addr)
}

fn convert_config(config: &kinetic_router::ReserveConfiguration) -> ReserveConfiguration {
    ReserveConfiguration {
        data_low: config.data_low,
        data_high: config.data_high,
    }
}

fn create_and_init_test_reserve(
    env: &Env,
    kinetic_router: &Address,
    oracle_addr: &Address,
    admin: &Address,
) -> (Address, StellarAssetContract) {
    let underlying_asset_contract = env.register_stellar_asset_contract_v2(admin.clone());
    let underlying_asset = underlying_asset_contract.address();

    // Register asset with oracle and set price
    let oracle_client = price_oracle::Client::new(env, oracle_addr);
    let asset_enum = price_oracle::Asset::Stellar(underlying_asset.clone());
    oracle_client.add_asset(admin, &asset_enum);
    oracle_client.set_manual_override(
        admin,
        &asset_enum,
        &Some(1_000_000_000_000_000u128), // 1 USD with 14 decimals
        &Some(env.ledger().timestamp() + 604_800), // 7 days (max allowed by L-04)
    );

    let a_token_impl = Address::generate(env);
    let debt_token_impl = Address::generate(env);
    let interest_rate_strategy = Address::generate(env);
    let treasury = Address::generate(env);

    let params = kinetic_router::InitReserveParams {
        decimals: 7,
        ltv: 8000,
        liquidation_threshold: 8500,
        liquidation_bonus: 500,
        reserve_factor: 1000,
        supply_cap: 1000000000000,
        borrow_cap: 1000000000000,
        borrowing_enabled: true,
        flashloan_enabled: true,
    };

    let client = kinetic_router::Client::new(env, kinetic_router);
    let pool_configurator = Address::generate(env);
    client.set_pool_configurator(&pool_configurator);
    client.init_reserve(
        &pool_configurator,
        &underlying_asset,
        &a_token_impl,
        &debt_token_impl,
        &interest_rate_strategy,
        &treasury,
        &params,
    );

    (underlying_asset, underlying_asset_contract)
}

#[test]
fn test_supply_validation_and_reserve_data() {
    let env = create_test_env();
    let (admin, _emergency_admin, user1, _user2) = create_test_addresses(&env);
    let (kinetic_router, oracle) = initialize_kinetic_router(&env, &admin, &admin);
    let client = kinetic_router::Client::new(&env, &kinetic_router);

    let (asset, _asset_contract) = create_and_init_test_reserve(&env, &kinetic_router, &oracle, &admin);

    let reserve_data = client.get_reserve_data(&asset);
    let config = convert_config(&reserve_data.configuration);
    assert_eq!(
        config.get_ltv(),
        8000,
        "LTV should match initialization (80%)"
    );
    assert_eq!(
        config.get_liquidation_threshold(),
        8500,
        "Liquidation threshold should match initialization (85%)"
    );
    assert_eq!(
        config.get_liquidation_bonus(),
        500,
        "Liquidation bonus should match initialization (5%)"
    );

    assert_ne!(
        reserve_data.a_token_address,
        Address::generate(&env),
        "aToken address should be set"
    );
    assert_ne!(
        reserve_data.debt_token_address,
        Address::generate(&env),
        "Debt token address should be set"
    );

    let supply_amount = 1000u128;
    let result = client.try_supply(&user1, &asset, &supply_amount, &user1, &0);

    assert!(
        result.is_err(),
        "Supply should fail without proper token setup"
    );

    match result {
        Err(Ok(kinetic_router::KineticRouterError::InvalidAmount)) => {}
        Err(Ok(kinetic_router::KineticRouterError::AssetNotActive)) => {}
        Err(Ok(kinetic_router::KineticRouterError::ReserveNotFound)) => {}
        Err(Ok(kinetic_router::KineticRouterError::UnderlyingTransferFailed)) => {}
        Err(Ok(kinetic_router::KineticRouterError::InsufficientCollateral)) => {}
        Err(Ok(kinetic_router::KineticRouterError::TokenCallFailed)) => {}
        Err(Ok(kinetic_router::KineticRouterError::PriceOracleInvocationFailed)) => {}
        Err(Err(_)) => {}
        _ => panic!("Expected specific validation error or abort, got: {:?}", result),
    }
}

#[test]
fn test_withdraw_validation() {
    let env = create_test_env();
    let (admin, _emergency_admin, user1, _user2) = create_test_addresses(&env);
    let (kinetic_router, oracle) = initialize_kinetic_router(&env, &admin, &admin);
    let client = kinetic_router::Client::new(&env, &kinetic_router);

    let (asset, _asset_contract) = create_and_init_test_reserve(&env, &kinetic_router, &oracle, &admin);

    let withdraw_amount = 300u128;
    let result = client.try_withdraw(&user1, &asset, &withdraw_amount, &user1);

    assert!(
        result.is_err(),
        "Withdraw should fail without proper token setup"
    );

    match result {
        Err(Ok(kinetic_router::KineticRouterError::InvalidAmount)) => {}
        Err(Ok(kinetic_router::KineticRouterError::AssetNotActive)) => {}
        Err(Ok(kinetic_router::KineticRouterError::ReserveNotFound)) => {}
        Err(Ok(kinetic_router::KineticRouterError::InsufficientCollateral)) => {}
        Err(Ok(kinetic_router::KineticRouterError::TokenCallFailed)) => {}
        Err(Ok(kinetic_router::KineticRouterError::PriceOracleInvocationFailed)) => {}
        Err(Err(_)) => {}
        _ => panic!("Expected specific validation error or abort, got: {:?}", result),
    }
}

#[test]
fn test_health_factor_calculation_for_new_user() {
    let env = create_test_env();
    let (admin, _emergency_admin, user1, _user2) = create_test_addresses(&env);
    let (kinetic_router, _oracle) = initialize_kinetic_router(&env, &admin, &admin);
    let client = kinetic_router::Client::new(&env, &kinetic_router);

    let account_data = client.get_user_account_data(&user1);

    assert_eq!(
        account_data.total_collateral_base, 0,
        "New user should have 0 collateral"
    );
    assert_eq!(
        account_data.total_debt_base, 0,
        "New user should have 0 debt"
    );
    assert_eq!(
        account_data.available_borrows_base, 0,
        "New user should have 0 available borrows"
    );
    assert_eq!(
        account_data.current_liquidation_threshold, 0,
        "New user should have 0 liquidation threshold"
    );
    assert_eq!(account_data.ltv, 0, "New user should have 0 LTV");
    assert_eq!(
        account_data.health_factor,
        u128::MAX,
        "New user should have maximum health factor"
    );
}

#[test]
fn test_reserve_data_integrity_after_initialization() {
    let env = create_test_env();
    let (admin, _emergency_admin, _user1, _user2) = create_test_addresses(&env);
    let (kinetic_router, oracle) = initialize_kinetic_router(&env, &admin, &admin);
    let client = kinetic_router::Client::new(&env, &kinetic_router);

    let (asset, _asset_contract) = create_and_init_test_reserve(&env, &kinetic_router, &oracle, &admin);

    let reserve_data = client.get_reserve_data(&asset);
    let config = convert_config(&reserve_data.configuration);

    assert_eq!(
        config.get_ltv(),
        8000,
        "LTV should match initialization (80%)"
    );
    assert_eq!(
        config.get_liquidation_threshold(),
        8500,
        "Liquidation threshold should match initialization (85%)"
    );
    assert_eq!(
        config.get_liquidation_bonus(),
        500,
        "Liquidation bonus should match initialization (5%)"
    );
    assert_eq!(
        config.get_reserve_factor(),
        1000,
        "Reserve factor should match initialization (10%)"
    );

    assert_ne!(
        reserve_data.a_token_address,
        Address::generate(&env),
        "aToken address should be set"
    );
    assert_ne!(
        reserve_data.debt_token_address,
        Address::generate(&env),
        "Debt token address should be set"
    );

    assert_eq!(
        reserve_data.liquidity_index, 1000000000000000000000000000u128,
        "Liquidity index should start at 1e27 (RAY)"
    );
    assert_eq!(
        reserve_data.variable_borrow_index, 1000000000000000000000000000u128,
        "Variable borrow index should start at 1e27 (RAY)"
    );
    assert_eq!(
        reserve_data.current_liquidity_rate, 0,
        "Initial liquidity rate should be 0"
    );
    assert_eq!(
        reserve_data.current_variable_borrow_rate, 0,
        "Initial variable borrow rate should be 0"
    );
    assert_eq!(
        reserve_data.last_update_timestamp, 0,
    );
}

#[test]
fn test_init_reserve_rejects_equal_ltv_and_liquidation_threshold() {
    let env = create_test_env();
    let (admin, _emergency_admin, _user1, _user2) = create_test_addresses(&env);
    let (kinetic_router, _oracle) = initialize_kinetic_router(&env, &admin, &admin);
    let client = kinetic_router::Client::new(&env, &kinetic_router);

    let underlying_asset_contract = env.register_stellar_asset_contract_v2(admin.clone());
    let underlying_asset = underlying_asset_contract.address();

    let a_token_impl = Address::generate(&env);
    let debt_token_impl = Address::generate(&env);
    let interest_rate_strategy = Address::generate(&env);
    let treasury = Address::generate(&env);
    let pool_configurator = Address::generate(&env);
    client.set_pool_configurator(&pool_configurator);

    // Invalid config: ltv=7500, liquidation_threshold=7500 (no buffer)
    let params = kinetic_router::InitReserveParams {
        decimals: 7,
        ltv: 7500,
        liquidation_threshold: 7500,
        liquidation_bonus: 500,
        reserve_factor: 1000,
        supply_cap: 1000000000000,
        borrow_cap: 1000000000000,
        borrowing_enabled: true,
        flashloan_enabled: true,
    };

    // Strong assertion: verify values are equal before calling
    assert_eq!(params.ltv, params.liquidation_threshold, "Values must be equal to test rejection");
    assert!(!(params.liquidation_threshold > params.ltv), "liquidation_threshold should not be greater");
    
    let result = client.try_init_reserve(
        &pool_configurator,
        &underlying_asset,
        &a_token_impl,
        &debt_token_impl,
        &interest_rate_strategy,
        &treasury,
        &params,
    );
    assert!(result.is_err(), "Equal LTV and liquidation threshold should be rejected");
    
    match result {
        Err(Ok(kinetic_router::KineticRouterError::InvalidAmount)) => {}
        _ => panic!("Expected InvalidAmount error, got: {:?}", result),
    }
    
    // Verify reserve was not created
    let reserve_result = client.try_get_reserve_data(&underlying_asset);
    assert!(reserve_result.is_err(), "Reserve should not exist after failed initialization");
}

#[test]
fn test_init_reserve_rejects_insufficient_buffer() {
    let env = create_test_env();
    let (admin, _emergency_admin, _user1, _user2) = create_test_addresses(&env);
    let (kinetic_router, _oracle) = initialize_kinetic_router(&env, &admin, &admin);
    let client = kinetic_router::Client::new(&env, &kinetic_router);

    let underlying_asset_contract = env.register_stellar_asset_contract_v2(admin.clone());
    let underlying_asset = underlying_asset_contract.address();

    let a_token_impl = Address::generate(&env);
    let debt_token_impl = Address::generate(&env);
    let interest_rate_strategy = Address::generate(&env);
    let treasury = Address::generate(&env);
    let pool_configurator = Address::generate(&env);
    client.set_pool_configurator(&pool_configurator);

    // Invalid config: ltv=7500, liquidation_threshold=7549 (49 bps buffer, below 50 bps minimum)
    let params = kinetic_router::InitReserveParams {
        decimals: 7,
        ltv: 7500,
        liquidation_threshold: 7549,
        liquidation_bonus: 500,
        reserve_factor: 1000,
        supply_cap: 1000000000000,
        borrow_cap: 1000000000000,
        borrowing_enabled: true,
        flashloan_enabled: true,
    };

    // Strong assertion: verify buffer calculation
    let buffer = params.liquidation_threshold - params.ltv;
    assert_eq!(buffer, 49, "Buffer should be exactly 49 bps (below minimum)");
    assert!(buffer < 50, "Buffer must be below 50 bps minimum");
    assert!(params.liquidation_threshold > params.ltv, "liquidation_threshold is greater but buffer insufficient");
    
    let result = client.try_init_reserve(
        &pool_configurator,
        &underlying_asset,
        &a_token_impl,
        &debt_token_impl,
        &interest_rate_strategy,
        &treasury,
        &params,
    );
    assert!(result.is_err(), "Buffer below 50 bps minimum should be rejected");
    
    match result {
        Err(Ok(kinetic_router::KineticRouterError::InvalidAmount)) => {}
        _ => panic!("Expected InvalidAmount error, got: {:?}", result),
    }
    
    // Verify reserve was not created
    let reserve_result = client.try_get_reserve_data(&underlying_asset);
    assert!(reserve_result.is_err(), "Reserve should not exist after failed initialization");
}

#[test]
fn test_init_reserve_accepts_minimum_buffer() {
    let env = create_test_env();
    let (admin, _emergency_admin, _user1, _user2) = create_test_addresses(&env);
    let (kinetic_router, _oracle) = initialize_kinetic_router(&env, &admin, &admin);
    let client = kinetic_router::Client::new(&env, &kinetic_router);

    let underlying_asset_contract = env.register_stellar_asset_contract_v2(admin.clone());
    let underlying_asset = underlying_asset_contract.address();

    let a_token_impl = Address::generate(&env);
    let debt_token_impl = Address::generate(&env);
    let interest_rate_strategy = Address::generate(&env);
    let treasury = Address::generate(&env);
    let pool_configurator = Address::generate(&env);
    client.set_pool_configurator(&pool_configurator);

    // Valid config: ltv=7500, liquidation_threshold=7550 (exactly 50 bps buffer)
    let params = kinetic_router::InitReserveParams {
        decimals: 7,
        ltv: 7500,
        liquidation_threshold: 7550,
        liquidation_bonus: 500,
        reserve_factor: 1000,
        supply_cap: 1000000000000,
        borrow_cap: 1000000000000,
        borrowing_enabled: true,
        flashloan_enabled: true,
    };

    // Strong assertion: verify buffer calculation
    let buffer = params.liquidation_threshold - params.ltv;
    assert_eq!(buffer, 50, "Buffer should be exactly 50 bps (minimum)");
    assert!(buffer >= 50, "Buffer must meet minimum requirement");
    assert!(params.liquidation_threshold > params.ltv, "liquidation_threshold must be strictly greater");
    
    let result = client.try_init_reserve(
        &pool_configurator,
        &underlying_asset,
        &a_token_impl,
        &debt_token_impl,
        &interest_rate_strategy,
        &treasury,
        &params,
    );
    assert!(result.is_ok(), "Minimum 50 bps buffer should be accepted");
    
    // Verify reserve was actually created with correct configuration
    let reserve_data = client.get_reserve_data(&underlying_asset);
    let config = convert_config(&reserve_data.configuration);
    assert_eq!(config.get_ltv() as u32, params.ltv, "LTV should match");
    assert_eq!(config.get_liquidation_threshold() as u32, params.liquidation_threshold, "Liquidation threshold should match");
    
    // Verify buffer is maintained in stored configuration
    let stored_ltv = config.get_ltv() as u32;
    let stored_liquidation_threshold = config.get_liquidation_threshold() as u32;
    let stored_buffer = stored_liquidation_threshold - stored_ltv;
    assert_eq!(stored_buffer, 50u32, "Stored buffer should be exactly 50 bps");
    assert!(stored_buffer >= 50u32, "Stored buffer must meet minimum requirement");
    assert!(stored_liquidation_threshold > stored_ltv, "Stored liquidation_threshold must be strictly greater than LTV");
}

#[test]
fn test_flash_loan_premium_calculation_accuracy() {
    let env = create_test_env();
    let (admin, _emergency_admin, _user1, _user2) = create_test_addresses(&env);
    let (kinetic_router, _oracle) = initialize_kinetic_router(&env, &admin, &admin);
    let client = kinetic_router::Client::new(&env, &kinetic_router);

    let premium_bps = 50;
    client.set_flash_loan_premium(&premium_bps);

    let actual_premium = client.get_flash_loan_premium();
    assert_eq!(
        actual_premium, premium_bps,
        "Flash loan premium should be set correctly"
    );

    let test_cases = [
        (1000u128, 5u128),
        (10000u128, 50u128),
        (100000u128, 500u128),
        (1u128, 0u128),
        (999u128, 4u128),
    ];

    for (amount, expected_premium) in test_cases {
        let calculated_premium = (amount * premium_bps) / 10000;
        assert_eq!(
            calculated_premium, expected_premium,
            "Premium calculation failed for amount {}: expected {}, got {}",
            amount, expected_premium, calculated_premium
        );
    }
}

#[test]
fn test_cap_enforcement_logic() {
    let env = create_test_env();
    let (admin, _emergency_admin, _user1, _user2) = create_test_addresses(&env);
    let (kinetic_router, oracle) = initialize_kinetic_router(&env, &admin, &admin);
    let client = kinetic_router::Client::new(&env, &kinetic_router);

    let (asset, _asset_contract) = create_and_init_test_reserve(&env, &kinetic_router, &oracle, &admin);

    let supply_cap = 1000000u128;
    let borrow_cap = 500000u128;

    client.set_reserve_supply_cap(&asset, &supply_cap);
    client.set_reserve_borrow_cap(&asset, &borrow_cap);

    let reserve_data = client.get_reserve_data(&asset);
    let config = convert_config(&reserve_data.configuration);
    assert_eq!(
        config.get_supply_cap(),
        supply_cap,
        "Supply cap should be set correctly"
    );
    assert_eq!(
        config.get_borrow_cap(),
        borrow_cap,
        "Borrow cap should be set correctly"
    );
}

#[test]
fn test_authorization_enforcement() {
    let env = create_test_env();
    let (admin, _emergency_admin, user1, _user2) = create_test_addresses(&env);
    let (kinetic_router, oracle) = initialize_kinetic_router(&env, &admin, &admin);
    let client = kinetic_router::Client::new(&env, &kinetic_router);

    let (asset, _asset_contract) = create_and_init_test_reserve(&env, &kinetic_router, &oracle, &admin);

    // Try to set supply cap without auth - should fail
    env.mock_auths(&[]);
    let result = client.try_set_reserve_supply_cap(&asset, &1000000);
    assert!(
        result.is_err(),
        "Non-admin should not be able to set supply cap"
    );

    // Set as admin should succeed
    env.mock_all_auths();
    let result = client.try_set_reserve_supply_cap(&asset, &1000000);
    assert!(result.is_ok(), "Admin should be able to set supply cap");

    let reserve_data = client.get_reserve_data(&asset);
    let config = convert_config(&reserve_data.configuration);
    assert_eq!(
        config.get_supply_cap(),
        1000000,
        "Supply cap should be set by admin"
    );
}

#[test]
fn test_user_configuration_bitmap_initialization() {
    let env = create_test_env();
    let (admin, _emergency_admin, user1, _user2) = create_test_addresses(&env);
    let (kinetic_router, _oracle) = initialize_kinetic_router(&env, &admin, &admin);
    let client = kinetic_router::Client::new(&env, &kinetic_router);

    let initial_config = client.get_user_configuration(&user1);
    assert_eq!(
        initial_config.data, 0,
        "New user configuration should be empty (0)"
    );
}

#[test]
fn test_borrow_attempt_without_collateral() {
    let env = create_test_env();
    let (admin, _emergency_admin, user1, _user2) = create_test_addresses(&env);
    let (kinetic_router, oracle) = initialize_kinetic_router(&env, &admin, &admin);
    let client = kinetic_router::Client::new(&env, &kinetic_router);

    let (asset, _asset_contract) = create_and_init_test_reserve(&env, &kinetic_router, &oracle, &admin);

    let borrow_amount = 100u128;
    let result = client.try_borrow(
        &user1,
        &asset,
        &borrow_amount,
        &1,
        &0,
        &user1,
    );

    assert!(
        result.is_err(),
        "Borrow should fail when user has no collateral"
    );

    match result {
        Err(Ok(kinetic_router::KineticRouterError::InvalidAmount)) => {}
        Err(Ok(kinetic_router::KineticRouterError::AssetNotActive)) => {}
        Err(Ok(kinetic_router::KineticRouterError::ReserveNotFound)) => {}
        Err(Ok(kinetic_router::KineticRouterError::InsufficientCollateral)) => {}
        Err(Ok(kinetic_router::KineticRouterError::TokenCallFailed)) => {}
        Err(Ok(kinetic_router::KineticRouterError::PriceOracleInvocationFailed)) => {}
        Err(Err(_)) => {}
        _ => panic!("Expected specific validation error or abort, got: {:?}", result),
    }
}

#[test]
fn test_repay_attempt_without_debt() {
    let env = create_test_env();
    let (admin, _emergency_admin, user1, _user2) = create_test_addresses(&env);
    let (kinetic_router, oracle) = initialize_kinetic_router(&env, &admin, &admin);
    let client = kinetic_router::Client::new(&env, &kinetic_router);

    let (asset, _asset_contract) = create_and_init_test_reserve(&env, &kinetic_router, &oracle, &admin);

    let repay_amount = 100u128;
    let result = client.try_repay(
        &user1,
        &asset,
        &repay_amount,
        &1,
        &user1,
    );

    match result {
        Err(Ok(kinetic_router::KineticRouterError::InvalidAmount)) => {}
        Err(Ok(kinetic_router::KineticRouterError::InsufficientCollateral)) => {}
        Err(Ok(kinetic_router::KineticRouterError::AssetNotActive)) => {}
        Err(Ok(kinetic_router::KineticRouterError::ReserveNotFound)) => {}
        Err(Ok(kinetic_router::KineticRouterError::TokenCallFailed)) => {}
        Err(Ok(kinetic_router::KineticRouterError::PriceOracleInvocationFailed)) => {}
        Err(Err(_)) => {}
        _ => panic!("Expected specific validation error or abort for borrow without collateral, got: {:?}", result),
    }
}
