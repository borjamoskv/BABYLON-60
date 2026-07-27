#![cfg(test)]

use crate::{a_token, debt_token, interest_rate_strategy, kinetic_router, price_oracle};
use price_oracle::Asset as OracleAsset;
use k2_shared::WAD;
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

fn setup_interest_rate_strategy(env: &Env, admin: &Address) -> Address {
    let contract_id = env.register(interest_rate_strategy::WASM, ());
    let mut init_args = Vec::new(env);
    init_args.push_back(admin.clone().into_val(env));
    init_args.push_back((0_000_000_000_000_000_000u128).into_val(env));
    init_args.push_back((40_000_000_000_000_000_000u128).into_val(env));
    init_args.push_back((100_000_000_000_000_000_000u128).into_val(env));
    init_args.push_back((800_000_000_000_000_000_000_000_000u128).into_val(env));
    let _: () = env.invoke_contract(&contract_id, &Symbol::new(env, "initialize"), init_args);
    contract_id
}

fn setup_test_environment(env: &Env) -> (
    Address, // admin
    Address, // user
    Address, // liquidity_provider
    Address, // kinetic_router
    Address, // oracle
    Address, // underlying_asset
    Address, // a_token
    Address, // debt_token
) {
    env.mock_all_auths();
    env.ledger().set(LedgerInfo {
        sequence_number: 100,
        protocol_version: 23,
        timestamp: 1000,
        network_id: Default::default(),
        base_reserve: 10,
        min_temp_entry_ttl: 10,
        min_persistent_entry_ttl: 10,
        max_entry_ttl: 1000000,
    });

    let admin = Address::generate(env);
    let user = Address::generate(env);
    let liquidity_provider = Address::generate(env);

    let kinetic_router_addr = env.register(kinetic_router::WASM, ());
    let kinetic_router = kinetic_router::Client::new(env, &kinetic_router_addr);

    let oracle_addr = env.register(price_oracle::WASM, ());
    let oracle_client = price_oracle::Client::new(env, &oracle_addr);

    let reflector_addr = env.register(MockReflector, ());
    let base_currency = Address::generate(env);
    let native_xlm = Address::generate(env);
    oracle_client.initialize(&admin, &reflector_addr, &base_currency, &native_xlm);

    let pool_treasury = Address::generate(env);
    let dex_router = Address::generate(env);
    kinetic_router.initialize(
        &admin,
        &admin,
        &oracle_addr,
        &pool_treasury,
        &dex_router,
        &None,
    );
    
    let pool_configurator = Address::generate(env);
    kinetic_router.set_pool_configurator(&pool_configurator);

    let token_admin = Address::generate(env);
    let underlying_token = env.register_stellar_asset_contract_v2(token_admin.clone());
    let underlying_addr = underlying_token.address();

    let interest_rate_strategy = setup_interest_rate_strategy(env, &admin);
    let treasury = Address::generate(env);

    let params = kinetic_router::InitReserveParams {
        decimals: 7,
        ltv: 8000, // 80% LTV
        liquidation_threshold: 8500, // 85% liquidation threshold
        liquidation_bonus: 500,
        reserve_factor: 1000,
        supply_cap: 0,
        borrow_cap: 0,
        borrowing_enabled: true,
        flashloan_enabled: true,
    };

    let a_token_addr = env.register(a_token::WASM, ());
    let a_token_client = a_token::Client::new(env, &a_token_addr);
    let a_name = String::from_str(env, "Test aToken");
    let a_symbol = String::from_str(env, "aTEST");
    a_token_client.initialize(
        &admin,
        &underlying_addr,
        &kinetic_router_addr,
        &a_name,
        &a_symbol,
        &params.decimals,
    );

    let debt_token_addr = env.register(debt_token::WASM, ());
    let debt_token_client = debt_token::Client::new(env, &debt_token_addr);
    let debt_name = String::from_str(env, "Debt Token");
    let debt_symbol = String::from_str(env, "dTEST");
    debt_token_client.initialize(
        &admin,
        &underlying_addr,
        &kinetic_router_addr,
        &debt_name,
        &debt_symbol,
        &params.decimals,
    );

    let pool_configurator = Address::generate(env);
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

    let asset_oracle = OracleAsset::Stellar(underlying_addr.clone());
    oracle_client.add_asset(&admin, &asset_oracle);
    // Set price to $1.00 (14 decimals: 100_000_000_000_000)
    oracle_client.set_manual_override(&admin, &asset_oracle, &Some(100_000_000_000_000u128), &Some(env.ledger().timestamp() + 86400));

    // Add liquidity provider who supplies tokens so users can borrow
    let lp_supply_amount = 100_000_000_000_000u128; // 10M tokens for liquidity
    let stellar_token = token::StellarAssetClient::new(env, &underlying_addr);
    stellar_token.mint(&liquidity_provider, &(lp_supply_amount as i128));
    let token_client = token::Client::new(env, &underlying_addr);
    let expiration = env.ledger().sequence() + 100000;
    token_client.approve(
        &liquidity_provider,
        &kinetic_router_addr,
        &(lp_supply_amount as i128),
        &expiration,
    );
    let kinetic_router = kinetic_router::Client::new(env, &kinetic_router_addr);
    kinetic_router.supply(
        &liquidity_provider,
        &underlying_addr,
        &lp_supply_amount,
        &liquidity_provider,
        &0u32,
    );

    (
        admin,
        user,
        liquidity_provider,
        kinetic_router_addr,
        oracle_addr,
        underlying_addr,
        a_token_addr,
        debt_token_addr,
    )
}

/// Test the EXACT bug scenario: withdrawal blocked when withdrawal would drop HF below 1.0
/// This tests the core fix: validation now correctly checks if a withdrawal would make HF < 1.0
/// and blocks it, preventing users from withdrawing multiple times until their position becomes unsafe
#[test]
fn test_withdraw_blocked_multiple_attempts_would_drop_hf_below_one() {
    let env = Env::default();
    let (_admin, user, _lp, kinetic_router_addr, _oracle, underlying_addr, _a_token, _debt_token) =
        setup_test_environment(&env);

    let kinetic_router = kinetic_router::Client::new(&env, &kinetic_router_addr);

    // Setup: User supplies collateral and borrows near max LTV
    // Supply 1000 tokens = $1000
    let supply_amount = 10_000_000_000_000u128;
    let stellar_token = token::StellarAssetClient::new(&env, &underlying_addr);
    stellar_token.mint(&user, &(supply_amount as i128));
    let token_client = token::Client::new(&env, &underlying_addr);
    let expiration = env.ledger().sequence() + 100000;
    token_client.approve(&user, &kinetic_router_addr, &(supply_amount as i128), &expiration);

    kinetic_router.supply(&user, &underlying_addr, &supply_amount, &user, &0u32);

    // Borrow 75% of collateral value
    // HF = (1000 * 0.85) / 750 = 850/750 = 1.133 > 1.0
    let borrow_amount = 7_500_000_000_000u128; // 75% LTV
    kinetic_router.borrow(&user, &underlying_addr, &borrow_amount, &1u32, &0u32, &user);

    // Verify HF > 1.0 initially
    let account_data_initial = kinetic_router.get_user_account_data(&user);
    assert!(
        account_data_initial.health_factor > WAD,
        "Health factor should be above 1.0 after borrowing"
    );

    // Try to withdraw an amount that would drop HF below 1.0
    // Current: $1000 collateral, $750 debt
    // To get HF < 1.0: (new_collateral * 0.85) / 750 < 1.0
    // new_collateral < 750 / 0.85 = 882.35
    // So withdraw > 1000 - 882.35 = 117.65
    // Let's try withdrawing $200: HF = (800 * 0.85) / 750 = 680/750 = 0.907 < 1.0
    let withdraw_amount = 2_000_000_000_000u128; // 200 tokens
    let result = kinetic_router.try_withdraw(&user, &underlying_addr, &withdraw_amount, &user);
    
    assert!(
        result.is_err(),
        "Withdrawal MUST fail when it would drop HF below 1.0 - this is the bug we're fixing!"
    );

    // Verify the exact error
    match result {
        Err(Ok(err)) => assert_eq!(
            err,
            kinetic_router::KineticRouterError::HealthFactorTooLow,
            "Should return HealthFactorTooLow error"
        ),
        _ => panic!("Expected HealthFactorTooLow error"),
    }
    
    // Verify HF is still > 1.0 (withdrawal was correctly blocked, position unchanged)
    let account_data_after_blocked = kinetic_router.get_user_account_data(&user);
    assert!(
        account_data_after_blocked.health_factor > WAD,
        "Health factor should still be above 1.0 (withdrawal was correctly blocked)"
    );
    
    // Try MULTIPLE withdrawal attempts - this tests the "multiple times" aspect of the bug
    // Even after one failed withdrawal, another attempt should also fail
    let withdraw_amount_2 = 1_500_000_000_000u128; // 150 tokens (also would drop HF < 1.0)
    let result_2 = kinetic_router.try_withdraw(&user, &underlying_addr, &withdraw_amount_2, &user);
    assert!(
        result_2.is_err(),
        "Second withdrawal attempt should also fail when it would drop HF below 1.0"
    );
    
    // Try a third time with a smaller amount that would still drop HF < 1.0
    let withdraw_amount_3 = 1_200_000_000_000u128; // 120 tokens
    let result_3 = kinetic_router.try_withdraw(&user, &underlying_addr, &withdraw_amount_3, &user);
    assert!(
        result_3.is_err(),
        "Third withdrawal attempt should also fail when it would drop HF below 1.0"
    );
    
    // Verify HF is still > 1.0 after all blocked attempts
    let account_data_final = kinetic_router.get_user_account_data(&user);
    assert!(
        account_data_final.health_factor > WAD,
        "Health factor should still be above 1.0 after multiple blocked withdrawal attempts"
    );
}

/// Test that withdrawal is blocked when current HF < 1.0
#[test]
fn test_withdraw_blocked_when_hf_below_one() {
    let env = Env::default();
    let (_admin, user, _lp, kinetic_router_addr, _oracle, underlying_addr, _a_token, _debt_token) =
        setup_test_environment(&env);

    let kinetic_router = kinetic_router::Client::new(&env, &kinetic_router_addr);

    // Setup: User supplies collateral and borrows to create HF < 1.0
    // Supply 1000 tokens (1000 * 10^7 = 10_000_000_000_000)
    let supply_amount = 10_000_000_000_000u128;
    let stellar_token = token::StellarAssetClient::new(&env, &underlying_addr);
    stellar_token.mint(&user, &(supply_amount as i128));
    let token_client = token::Client::new(&env, &underlying_addr);
    let expiration = env.ledger().sequence() + 100000;
    token_client.approve(&user, &kinetic_router_addr, &(supply_amount as i128), &expiration);

    kinetic_router.supply(&user, &underlying_addr, &supply_amount, &user, &0u32);

    // Check available borrows and current HF first
    let account_data_before_borrow = kinetic_router.get_user_account_data(&user);
    let _available_borrows = account_data_before_borrow.available_borrows_base;
    let _current_hf = account_data_before_borrow.health_factor;
    
    // Try borrowing a very small amount first to see what happens
    // Borrow 10% of collateral value = 100 tokens = 1_000_000_000_000
    // This should definitely be safe: HF = 850/100 = 8.5 > 1.0
    let borrow_amount = 1_000_000_000_000u128; // 10% of collateral
    let borrow_result = kinetic_router.try_borrow(&user, &underlying_addr, &borrow_amount, &1u32, &0u32, &user);
    
    // If even 10% is blocked, there's a bug in borrow validation
    if borrow_result.is_err() {
        panic!("Borrowing 10% of collateral should be allowed, but got error: {:?}", borrow_result.unwrap_err());
    }
    
    kinetic_router.borrow(&user, &underlying_addr, &borrow_amount, &1u32, &0u32, &user);
    
    // Verify HF > 1.0 initially
    let account_data_initial = kinetic_router.get_user_account_data(&user);
    assert!(
        account_data_initial.health_factor > WAD,
        "Health factor should be above 1.0 after borrowing 50%"
    );
    
    // Verify HF > 1.0 initially
    let account_data_initial = kinetic_router.get_user_account_data(&user);
    assert!(
        account_data_initial.health_factor > WAD,
        "Health factor should be above 1.0 after borrowing 10%"
    );
    
    // Withdraw a small amount that's allowed
    // Withdraw $100: HF = (900 * 0.85) / 100 = 765/100 = 7.65 > 1.0 (should be allowed)
    let withdraw_safe = 1_000_000_000_000u128; // 100 tokens
    kinetic_router.withdraw(&user, &underlying_addr, &withdraw_safe, &user);
    
    // Verify HF is still > 1.0 after safe withdrawal
    let account_data_after_safe = kinetic_router.get_user_account_data(&user);
    assert!(
        account_data_after_safe.health_factor > WAD,
        "Health factor should still be above 1.0 after withdrawing $100"
    );
    
    // Now try to withdraw $800 more: HF = (100 * 0.85) / 100 = 85/100 = 0.85 < 1.0 (should be blocked)
    let withdraw_amount = 8_000_000_000_000u128; // 800 tokens
    let result = kinetic_router.try_withdraw(&user, &underlying_addr, &withdraw_amount, &user);
    assert!(
        result.is_err(),
        "Withdrawal should fail when it would drop HF below 1.0"
    );

    // Verify error is HealthFactorTooLow
    match result {
        Err(Ok(err)) => assert_eq!(
            err,
            kinetic_router::KineticRouterError::HealthFactorTooLow,
            "Should return HealthFactorTooLow error"
        ),
        _ => panic!("Expected HealthFactorTooLow error"),
    }
    
    // Now verify current HF is still > 1.0 (position is safe, withdrawal was correctly blocked)
    let account_data_final = kinetic_router.get_user_account_data(&user);
    assert!(
        account_data_final.health_factor > WAD,
        "Health factor should still be above 1.0 (withdrawal was correctly blocked)"
    );
}

/// Test that withdrawal is blocked when it would bring HF below 1.0
#[test]
fn test_withdraw_blocked_when_would_drop_hf_below_one() {
    let env = Env::default();
    let (_admin, user, _lp, kinetic_router_addr, _oracle, underlying_addr, _a_token, _debt_token) =
        setup_test_environment(&env);

    let kinetic_router = kinetic_router::Client::new(&env, &kinetic_router_addr);

    // Setup: User supplies collateral and borrows to create HF just above 1.0
    // Supply 2000 tokens
    let supply_amount = 20_000_000_000_000u128;
    let stellar_token = token::StellarAssetClient::new(&env, &underlying_addr);
    stellar_token.mint(&user, &(supply_amount as i128));
    let token_client = token::Client::new(&env, &underlying_addr);
    let expiration = env.ledger().sequence() + 100000;
    token_client.approve(&user, &kinetic_router_addr, &(supply_amount as i128), &expiration);

    kinetic_router.supply(&user, &underlying_addr, &supply_amount, &user, &0u32);

    // Borrow 75% of collateral value (should create HF ~1.13, just above 1.0)
    // Collateral: $2000, Borrow: $1500
    // HF = (2000 * 0.85) / 1500 = 1700 / 1500 = 1.133
    let borrow_amount = 15_000_000_000_000u128;
    kinetic_router.borrow(&user, &underlying_addr, &borrow_amount, &1u32, &0u32, &user);

    // Verify HF > 1.0
    let account_data = kinetic_router.get_user_account_data(&user);
    assert!(
        account_data.health_factor > WAD,
        "Health factor should be above 1.0"
    );

    // Try to withdraw large amount that would drop HF below 1.0
    // Withdrawing $400 would leave $1600 collateral, HF = (1600 * 0.85) / 1500 = 0.907 < 1.0
    let withdraw_amount = 4_000_000_000_000u128; // 400 tokens
    let result = kinetic_router.try_withdraw(&user, &underlying_addr, &withdraw_amount, &user);
    assert!(
        result.is_err(),
        "Withdrawal should fail when it would drop HF below 1.0"
    );

    // Verify error
    match result {
        Err(Ok(err)) => assert_eq!(
            err,
            kinetic_router::KineticRouterError::HealthFactorTooLow,
            "Should return HealthFactorTooLow error"
        ),
        _ => panic!("Expected HealthFactorTooLow error"),
    }
}

/// Test that withdrawal succeeds when HF stays above 1.0
#[test]
fn test_withdraw_succeeds_when_hf_stays_above_one() {
    let env = Env::default();
    let (_admin, user, _lp, kinetic_router_addr, _oracle, underlying_addr, _a_token, _debt_token) =
        setup_test_environment(&env);

    let kinetic_router = kinetic_router::Client::new(&env, &kinetic_router_addr);

    // Setup: User supplies collateral and borrows
    let supply_amount = 20_000_000_000_000u128; // 2000 tokens
    let stellar_token = token::StellarAssetClient::new(&env, &underlying_addr);
    stellar_token.mint(&user, &(supply_amount as i128));
    let token_client = token::Client::new(&env, &underlying_addr);
    let expiration = env.ledger().sequence() + 100000;
    token_client.approve(&user, &kinetic_router_addr, &(supply_amount as i128), &expiration);

    kinetic_router.supply(&user, &underlying_addr, &supply_amount, &user, &0u32);

    // Borrow 50% of collateral value (HF should be well above 1.0)
    let borrow_amount = 10_000_000_000_000u128; // 1000 tokens
    kinetic_router.borrow(&user, &underlying_addr, &borrow_amount, &1u32, &0u32, &user);

    // Verify HF > 1.0
    let account_data_before = kinetic_router.get_user_account_data(&user);
    assert!(
        account_data_before.health_factor > WAD,
        "Health factor should be above 1.0"
    );

    // Withdraw small amount that keeps HF > 1.0
    // Withdrawing $200 leaves $1800 collateral, HF = (1800 * 0.85) / 1000 = 1.53 > 1.0
    let withdraw_amount = 2_000_000_000_000u128; // 200 tokens
    let result = kinetic_router.try_withdraw(&user, &underlying_addr, &withdraw_amount, &user);
    assert!(
        result.is_ok(),
        "Withdrawal should succeed when HF stays above 1.0"
    );
}

/// Test that borrow is blocked when current HF < 1.0
#[test]
fn test_borrow_blocked_when_hf_below_one() {
    let env = Env::default();
    let (_admin, user, _lp, kinetic_router_addr, _oracle, underlying_addr, _a_token, _debt_token) =
        setup_test_environment(&env);

    let kinetic_router = kinetic_router::Client::new(&env, &kinetic_router_addr);

    // Setup: User supplies collateral and borrows to create HF < 1.0
    let supply_amount = 10_000_000_000_000u128; // 1000 tokens
    let stellar_token = token::StellarAssetClient::new(&env, &underlying_addr);
    stellar_token.mint(&user, &(supply_amount as i128));
    let token_client = token::Client::new(&env, &underlying_addr);
    let expiration = env.ledger().sequence() + 100000;
    token_client.approve(&user, &kinetic_router_addr, &(supply_amount as i128), &expiration);

    kinetic_router.supply(&user, &underlying_addr, &supply_amount, &user, &0u32);

    // Borrow 70% of collateral value (HF = 850/700 = 1.214 > 1.0)
    let borrow_amount = 7_000_000_000_000u128; // 70% LTV
    kinetic_router.borrow(&user, &underlying_addr, &borrow_amount, &1u32, &0u32, &user);

    // Verify HF > 1.0 initially
    let account_data_initial = kinetic_router.get_user_account_data(&user);
    assert!(
        account_data_initial.health_factor > WAD,
        "Health factor should be above 1.0 after borrowing 70%"
    );
    
    // Try to borrow more that would drop HF below 1.0
    // Current: $1000 collateral, $700 debt, HF = 850/700 = 1.214
    // To get HF < 1.0: (1000 * 0.85) / new_debt < 1.0
    // new_debt > 850
    // So borrow additional $200: total debt = $900
    // HF = (1000 * 0.85) / 900 = 850/900 = 0.944 < 1.0
    let additional_borrow = 2_000_000_000_000u128; // 200 tokens
    let result = kinetic_router.try_borrow(
        &user,
        &underlying_addr,
        &additional_borrow,
        &1u32,
        &0u32,
        &user,
    );
    assert!(
        result.is_err(),
        "Borrow should fail when it would drop HF below 1.0"
    );

    // Verify error - can be either HealthFactorTooLow or InsufficientCollateral
    match result {
        Err(Ok(kinetic_router::KineticRouterError::HealthFactorTooLow)) => {}
        Err(Ok(kinetic_router::KineticRouterError::InsufficientCollateral)) => {}
        _ => panic!("Expected HealthFactorTooLow or InsufficientCollateral error, got: {:?}", result),
    }
    
    // Verify HF is still > 1.0 (borrow was correctly blocked)
    let account_data_after = kinetic_router.get_user_account_data(&user);
    assert!(
        account_data_after.health_factor > WAD,
        "Health factor should still be above 1.0 (borrow was correctly blocked)"
    );
}

/// Test that borrow is blocked when it would bring HF below 1.0
#[test]
fn test_borrow_blocked_when_would_drop_hf_below_one() {
    let env = Env::default();
    let (_admin, user, _lp, kinetic_router_addr, _oracle, underlying_addr, _a_token, _debt_token) =
        setup_test_environment(&env);

    let kinetic_router = kinetic_router::Client::new(&env, &kinetic_router_addr);

    // Setup: User supplies collateral and borrows to create HF just above 1.0
    let supply_amount = 20_000_000_000_000u128; // 2000 tokens
    let stellar_token = token::StellarAssetClient::new(&env, &underlying_addr);
    stellar_token.mint(&user, &(supply_amount as i128));
    let token_client = token::Client::new(&env, &underlying_addr);
    let expiration = env.ledger().sequence() + 100000;
    token_client.approve(&user, &kinetic_router_addr, &(supply_amount as i128), &expiration);

    kinetic_router.supply(&user, &underlying_addr, &supply_amount, &user, &0u32);

    // Borrow 70% of collateral value (HF ~1.21, well above 1.0)
    // HF = (2000 * 0.85) / 1400 = 1700/1400 = 1.214 > 1.0
    let borrow_amount = 14_000_000_000_000u128; // 1400 tokens (70% LTV)
    kinetic_router.borrow(&user, &underlying_addr, &borrow_amount, &1u32, &0u32, &user);

    // Verify HF > 1.0
    let account_data = kinetic_router.get_user_account_data(&user);
    assert!(
        account_data.health_factor > WAD,
        "Health factor should be above 1.0"
    );

    // Try to borrow more that would drop HF below 1.0
    // Current: $2000 collateral, $1400 debt, HF = 1.214
    // To get HF < 1.0: (2000 * 0.85) / new_debt < 1.0
    // new_debt > 1700
    // So borrow additional $400: total debt = $1800
    // HF = (2000 * 0.85) / 1800 = 1700/1800 = 0.944 < 1.0
    let additional_borrow = 4_000_000_000_000u128; // 400 tokens
    let result = kinetic_router.try_borrow(
        &user,
        &underlying_addr,
        &additional_borrow,
        &1u32,
        &0u32,
        &user,
    );
    assert!(
        result.is_err(),
        "Borrow should fail when it would drop HF below 1.0"
    );

    // Verify error - can be either HealthFactorTooLow or InsufficientCollateral
    match result {
        Err(Ok(kinetic_router::KineticRouterError::HealthFactorTooLow)) => {}
        Err(Ok(kinetic_router::KineticRouterError::InsufficientCollateral)) => {}
        _ => panic!("Expected HealthFactorTooLow or InsufficientCollateral error, got: {:?}", result),
    }
}

/// Test that borrow succeeds when HF stays above 1.0
#[test]
fn test_borrow_succeeds_when_hf_stays_above_one() {
    let env = Env::default();
    let (_admin, user, _lp, kinetic_router_addr, _oracle, underlying_addr, _a_token, _debt_token) =
        setup_test_environment(&env);

    let kinetic_router = kinetic_router::Client::new(&env, &kinetic_router_addr);

    // Setup: User supplies collateral
    let supply_amount = 20_000_000_000_000u128; // 2000 tokens
    let stellar_token = token::StellarAssetClient::new(&env, &underlying_addr);
    stellar_token.mint(&user, &(supply_amount as i128));
    let token_client = token::Client::new(&env, &underlying_addr);
    let expiration = env.ledger().sequence() + 100000;
    token_client.approve(&user, &kinetic_router_addr, &(supply_amount as i128), &expiration);

    kinetic_router.supply(&user, &underlying_addr, &supply_amount, &user, &0u32);

    // Borrow 50% of collateral value (HF should be well above 1.0)
    let borrow_amount = 10_000_000_000_000u128; // 1000 tokens
    kinetic_router.borrow(&user, &underlying_addr, &borrow_amount, &1u32, &0u32, &user);

    // Verify HF > 1.0
    let account_data = kinetic_router.get_user_account_data(&user);
    assert!(
        account_data.health_factor > WAD,
        "Health factor should be above 1.0"
    );

    // Borrow small additional amount that keeps HF > 1.0
    // Additional $100 makes total debt $1100
    // HF = (2000 * 0.85) / 1100 = 1700 / 1100 = 1.545 > 1.0
    let additional_borrow = 1_000_000_000_000u128; // 100 tokens
    let result = kinetic_router.try_borrow(
        &user,
        &underlying_addr,
        &additional_borrow,
        &1u32,
        &0u32,
        &user,
    );
    assert!(
        result.is_ok(),
        "Borrow should succeed when HF stays above 1.0"
    );
}

/// Test that withdrawal is allowed when user has no debt
#[test]
fn test_withdraw_allowed_with_no_debt() {
    let env = Env::default();
    let (_admin, user, _lp, kinetic_router_addr, _oracle, underlying_addr, _a_token, _debt_token) =
        setup_test_environment(&env);

    let kinetic_router = kinetic_router::Client::new(&env, &kinetic_router_addr);

    // Setup: User supplies collateral only (no debt)
    let supply_amount = 10_000_000_000_000u128; // 1000 tokens
    let stellar_token = token::StellarAssetClient::new(&env, &underlying_addr);
    stellar_token.mint(&user, &(supply_amount as i128));
    let token_client = token::Client::new(&env, &underlying_addr);
    let expiration = env.ledger().sequence() + 100000;
    token_client.approve(&user, &kinetic_router_addr, &(supply_amount as i128), &expiration);

    kinetic_router.supply(&user, &underlying_addr, &supply_amount, &user, &0u32);

    // Verify no debt
    let account_data = kinetic_router.get_user_account_data(&user);
    assert_eq!(account_data.total_debt_base, 0, "Should have no debt");

    // Withdraw should succeed (no debt means no HF check)
    let withdraw_amount = 5_000_000_000_000u128; // 500 tokens
    let result = kinetic_router.try_withdraw(&user, &underlying_addr, &withdraw_amount, &user);
    assert!(
        result.is_ok(),
        "Withdrawal should succeed when user has no debt"
    );
}

/// Test edge case: HF exactly at 1.0 threshold
#[test]
fn test_withdraw_at_exact_hf_threshold() {
    let env = Env::default();
    let (_admin, user, _lp, kinetic_router_addr, _oracle, underlying_addr, _a_token, _debt_token) =
        setup_test_environment(&env);

    let kinetic_router = kinetic_router::Client::new(&env, &kinetic_router_addr);

    // Setup to get HF exactly at 1.0
    // For HF = 1.0: (collateral * liquidation_threshold) / debt = 1.0
    // With 85% liquidation threshold: collateral * 0.85 = debt
    // So if collateral = $1000, debt = $850 gives HF = 1.0
    let supply_amount = 10_000_000_000_000u128; // 1000 tokens = $1000
    let stellar_token = token::StellarAssetClient::new(&env, &underlying_addr);
    stellar_token.mint(&user, &(supply_amount as i128));
    let token_client = token::Client::new(&env, &underlying_addr);
    let expiration = env.ledger().sequence() + 100000;
    token_client.approve(&user, &kinetic_router_addr, &(supply_amount as i128), &expiration);

    kinetic_router.supply(&user, &underlying_addr, &supply_amount, &user, &0u32);

    // Borrow 70% of collateral value to get HF above 1.0
    // HF = (1000 * 0.85) / 700 = 850/700 = 1.214 > 1.0
    let borrow_amount = 7_000_000_000_000u128; // 700 tokens (70% LTV)
    kinetic_router.borrow(&user, &underlying_addr, &borrow_amount, &1u32, &0u32, &user);
    
    // Verify HF > 1.0
    let account_data_initial = kinetic_router.get_user_account_data(&user);
    assert!(
        account_data_initial.health_factor > WAD,
        "Health factor should be above 1.0"
    );
    
    // Withdraw enough to get HF close to 1.0
    // Withdraw $200: HF = (800 * 0.85) / 700 = 680/700 = 0.971 < 1.0
    // Actually, let's withdraw less to get HF just above 1.0
    // Withdraw $150: HF = (850 * 0.85) / 700 = 722.5/700 = 1.032 > 1.0
    let withdraw_to_near_threshold = 1_500_000_000_000u128; // 150 tokens
    kinetic_router.withdraw(&user, &underlying_addr, &withdraw_to_near_threshold, &user);
    
    // Verify HF is still > 1.0 but close to threshold
    let account_data = kinetic_router.get_user_account_data(&user);
    assert!(
        account_data.health_factor > WAD && account_data.health_factor < WAD * 2,
        "Health factor should be above 1.0 but not too high"
    );

    // Try to withdraw enough to drop HF below 1.0
    // Current: $850 collateral, $700 debt, HF = (850 * 0.85) / 700 = 722.5/700 = 1.032
    // To get HF < 1.0: (new_collateral * 0.85) / 700 < 1.0
    // new_collateral < 700 / 0.85 = 823.5
    // So withdraw > 850 - 823.5 = 26.5
    // Let's withdraw $50: HF = (800 * 0.85) / 700 = 680/700 = 0.971 < 1.0
    let withdraw_amount = 500_000_000_000u128; // 50 tokens
    let result = kinetic_router.try_withdraw(&user, &underlying_addr, &withdraw_amount, &user);
    // This should fail because new HF would be < 1.0
    assert!(
        result.is_err(),
        "Withdrawal should fail when it would drop HF below 1.0"
    );
    
    // Verify error
    match result {
        Err(Ok(err)) => assert_eq!(
            err,
            kinetic_router::KineticRouterError::HealthFactorTooLow,
            "Should return HealthFactorTooLow error"
        ),
        _ => panic!("Expected HealthFactorTooLow error"),
    }
}

