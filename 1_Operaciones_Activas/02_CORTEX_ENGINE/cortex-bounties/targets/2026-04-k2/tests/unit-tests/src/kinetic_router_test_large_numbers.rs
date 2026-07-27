#![cfg(test)]

use crate::{a_token, debt_token, interest_rate_strategy, kinetic_router, price_oracle};
use price_oracle::Asset as OracleAsset;
use soroban_sdk::{contract, contractimpl, testutils::Address as _, token, Address, Env, IntoVal, String, Symbol, Vec};

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

    // Initialize using invoke_contract
    let mut init_args = Vec::new(env);
    init_args.push_back(admin.clone().into_val(env));
    init_args.push_back((0_000_000_000_000_000_000u128).into_val(env)); // base_variable_borrow_rate: 0% (in RAY)
    init_args.push_back((40_000_000_000_000_000_000u128).into_val(env)); // variable_rate_slope1: 40% (in RAY)
    init_args.push_back((100_000_000_000_000_000_000u128).into_val(env)); // variable_rate_slope2: 100% (in RAY)
    init_args.push_back((800_000_000_000_000_000_000_000_000u128).into_val(env)); // optimal_utilization_rate: 80% (in RAY)

    let _: () = env.invoke_contract(&contract_id, &Symbol::new(env, "initialize"), init_args);

    contract_id
}

fn setup_test_environment(env: &Env) -> (Address, Address, Address, Address, Address) {
    let admin = Address::generate(env);
    let user = Address::generate(env);

    let kinetic_router_addr = env.register(kinetic_router::WASM, ());
    let kinetic_router = kinetic_router::Client::new(env, &kinetic_router_addr);

    let oracle_addr = env.register(price_oracle::WASM, ());
    let oracle_client = price_oracle::Client::new(env, &oracle_addr);

    // Use mock reflector that implements decimals()
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

    (admin, user, kinetic_router_addr, oracle_addr, pool_treasury)
}

fn create_reserve_with_cap(
    env: &Env,
    kinetic_router: &kinetic_router::Client,
    kinetic_router_addr: &Address,
    admin: &Address,
    oracle: &price_oracle::Client,
    supply_cap: u128,
    borrow_cap: u128,
    decimals: u8,
) -> (Address, Address, Address) {
    let token_admin = Address::generate(env);
    let underlying_token = env.register_stellar_asset_contract_v2(token_admin.clone());
    let underlying_addr = underlying_token.address();
    
    // IMPORTANT: Mint tokens BEFORE initializing aToken/debtToken
    // This initializes the Stellar Asset Contract storage (decimals, etc.)
    let stellar_client = token::StellarAssetClient::new(env, &underlying_addr);
    stellar_client.mint(&token_admin, &1_000_000_000_000i128);

    let interest_rate_strategy = setup_interest_rate_strategy(env, admin);
    let treasury = Address::generate(env);

    let params = kinetic_router::InitReserveParams {
        decimals: decimals as u32,
        ltv: 7500,
        liquidation_threshold: 8000,
        liquidation_bonus: 500,
        reserve_factor: 1000,
        supply_cap,
        borrow_cap,
        borrowing_enabled: true,
        flashloan_enabled: true,
    };

    let a_token_addr = env.register(a_token::WASM, ());
    let a_token_client = a_token::Client::new(env, &a_token_addr);
    let a_name = String::from_str(env, "Test aToken");
    let a_symbol = String::from_str(env, "aTEST");
    a_token_client.initialize(
        admin,
        &underlying_addr,
        kinetic_router_addr,
        &a_name,
        &a_symbol,
        &params.decimals,
    );

    let debt_token_addr = env.register(debt_token::WASM, ());
    let debt_token_client = debt_token::Client::new(env, &debt_token_addr);
    let debt_name = String::from_str(env, "Debt Token");
    let debt_symbol = String::from_str(env, "dTEST");
    debt_token_client.initialize(
        admin,
        &underlying_addr,
        kinetic_router_addr,
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
    oracle.add_asset(admin, &asset_oracle);
    // Oracle price format: 14 decimals, so $1.00 = 100_000_000_000_000
    let expiry = env.ledger().timestamp() + 86400; // 24 hours
    oracle.set_manual_override(admin, &asset_oracle, &Some(100_000_000_000_000u128), &Some(expiry));

    (underlying_addr, a_token_addr, debt_token_addr)
}

#[test]
fn test_supply_large_amounts_usdc() {
    let env = Env::default();
    env.mock_all_auths();

    let (admin, user, kinetic_router_addr, oracle_addr, _) = setup_test_environment(&env);
    let kinetic_router = kinetic_router::Client::new(&env, &kinetic_router_addr);
    let oracle_client = price_oracle::Client::new(&env, &oracle_addr);

    // Create reserve with very large supply cap (10 million tokens)
    // USDC has 9 decimals
    let supply_cap = 10_000_000u128; // 10 million tokens
    let (underlying_addr, _, _) = create_reserve_with_cap(
        &env,
        &kinetic_router,
        &kinetic_router_addr,
        &admin,
        &oracle_client,
        supply_cap,
        0,
        9, // USDC decimals
    );

    // Mint 5 million USDC to user (5,000,000 * 10^9 = 5_000_000_000_000_000)
    let mint_amount = 5_000_000_000_000_000i128; // 5M USDC
    let stellar_token = token::StellarAssetClient::new(&env, &underlying_addr);
    stellar_token.mint(&user, &mint_amount);

    // Approve
    let token_client = token::Client::new(&env, &underlying_addr);
    let expiration = env.ledger().sequence() + 1000000;
    token_client.approve(&user, &kinetic_router_addr, &mint_amount, &expiration);

    // Supply 5 million USDC
    let supply_amount = 5_000_000_000_000_000u128;
    kinetic_router.supply(&user, &underlying_addr, &supply_amount, &user, &0u32);

    // Verify account data
    let account_data = kinetic_router.get_user_account_data(&user);
    assert!(account_data.total_collateral_base > 0, "Should have collateral");
}

#[test]
fn test_supply_exceeds_cap_large_numbers() {
    let env = Env::default();
    env.mock_all_auths();

    let (admin, user, kinetic_router_addr, oracle_addr, _) = setup_test_environment(&env);
    let kinetic_router = kinetic_router::Client::new(&env, &kinetic_router_addr);
    let oracle_client = price_oracle::Client::new(&env, &oracle_addr);

    // Create reserve with supply cap of 1 million tokens
    let supply_cap = 1_000_000u128; // 1 million tokens
    let (underlying_addr, _, _) = create_reserve_with_cap(
        &env,
        &kinetic_router,
        &kinetic_router_addr,
        &admin,
        &oracle_client,
        supply_cap,
        0,
        9, // USDC decimals
    );

    // Mint 2 million USDC to user
    let mint_amount = 2_000_000_000_000_000i128; // 2M USDC
    let stellar_token = token::StellarAssetClient::new(&env, &underlying_addr);
    stellar_token.mint(&user, &mint_amount);

    // Approve
    let token_client = token::Client::new(&env, &underlying_addr);
    let expiration = env.ledger().sequence() + 1000000;
    token_client.approve(&user, &kinetic_router_addr, &mint_amount, &expiration);

    // First supply 1 million USDC (should succeed)
    let supply_amount_1 = 1_000_000_000_000_000u128; // 1M USDC
    kinetic_router.supply(&user, &underlying_addr, &supply_amount_1, &user, &0u32);

    // Try to supply another 1 million USDC (should fail - exceeds cap)
    let supply_amount_2 = 1_000_000_000_000_000u128; // 1M USDC
    let result = kinetic_router.try_supply(&user, &underlying_addr, &supply_amount_2, &user, &0u32);
    assert!(result.is_err(), "Should fail when exceeding supply cap");
}

#[test]
fn test_supply_multiple_users_large_amounts() {
    let env = Env::default();
    env.mock_all_auths();

    let (admin, user1, kinetic_router_addr, oracle_addr, _) = setup_test_environment(&env);
    let user2 = Address::generate(&env);
    let kinetic_router = kinetic_router::Client::new(&env, &kinetic_router_addr);
    let oracle_client = price_oracle::Client::new(&env, &oracle_addr);

    // Create reserve with very large supply cap (100 million tokens)
    let supply_cap = 100_000_000u128; // 100 million tokens
    let (underlying_addr, _, _) = create_reserve_with_cap(
        &env,
        &kinetic_router,
        &kinetic_router_addr,
        &admin,
        &oracle_client,
        supply_cap,
        0,
        9, // USDC decimals
    );

    // Mint 10 million USDC to each user
    let mint_amount = 10_000_000_000_000_000i128; // 10M USDC
    let stellar_token = token::StellarAssetClient::new(&env, &underlying_addr);
    stellar_token.mint(&user1, &mint_amount);
    stellar_token.mint(&user2, &mint_amount);

    // Approve for both users
    let token_client = token::Client::new(&env, &underlying_addr);
    let expiration = env.ledger().sequence() + 1000000;
    token_client.approve(&user1, &kinetic_router_addr, &mint_amount, &expiration);
    token_client.approve(&user2, &kinetic_router_addr, &mint_amount, &expiration);

    // User1 supplies 10 million USDC
    let supply_amount = 10_000_000_000_000_000u128;
    kinetic_router.supply(&user1, &underlying_addr, &supply_amount, &user1, &0u32);

    // User2 supplies 10 million USDC
    kinetic_router.supply(&user2, &underlying_addr, &supply_amount, &user2, &0u32);

    // Verify both users have collateral
    let account_data_1 = kinetic_router.get_user_account_data(&user1);
    let account_data_2 = kinetic_router.get_user_account_data(&user2);
    assert!(account_data_1.total_collateral_base > 0, "User1 should have collateral");
    assert!(account_data_2.total_collateral_base > 0, "User2 should have collateral");
}

#[test]
fn test_borrow_large_amounts() {
    let env = Env::default();
    env.mock_all_auths();

    let (admin, user, kinetic_router_addr, oracle_addr, _) = setup_test_environment(&env);
    let kinetic_router = kinetic_router::Client::new(&env, &kinetic_router_addr);
    let oracle_client = price_oracle::Client::new(&env, &oracle_addr);

    // Create reserve with large borrow cap (5 million tokens)
    let borrow_cap = 5_000_000u128; // 5 million tokens
    let (underlying_addr, _, _) = create_reserve_with_cap(
        &env,
        &kinetic_router,
        &kinetic_router_addr,
        &admin,
        &oracle_client,
        0,
        borrow_cap,
        9, // USDC decimals
    );

    // Mint 10 million USDC to user for collateral
    let mint_amount = 10_000_000_000_000_000i128; // 10M USDC
    let stellar_token = token::StellarAssetClient::new(&env, &underlying_addr);
    stellar_token.mint(&user, &mint_amount);

    // Approve and supply
    let token_client = token::Client::new(&env, &underlying_addr);
    let expiration = env.ledger().sequence() + 1000000;
    token_client.approve(&user, &kinetic_router_addr, &mint_amount, &expiration);

    let supply_amount = 10_000_000_000_000_000u128;
    kinetic_router.supply(&user, &underlying_addr, &supply_amount, &user, &0u32);

    // Borrow 2 million USDC
    let borrow_amount = 2_000_000_000_000_000u128; // 2M USDC
    kinetic_router.borrow(&user, &underlying_addr, &borrow_amount, &1u32, &0u32, &user);

    // Verify account data
    let account_data = kinetic_router.get_user_account_data(&user);
    assert!(account_data.total_debt_base > 0, "Should have debt");
    assert!(account_data.total_collateral_base > account_data.total_debt_base, "Collateral should exceed debt");
}

#[test]
fn test_borrow_exceeds_cap_large_numbers() {
    let env = Env::default();
    env.mock_all_auths();

    let (admin, user, kinetic_router_addr, oracle_addr, _) = setup_test_environment(&env);
    let kinetic_router = kinetic_router::Client::new(&env, &kinetic_router_addr);
    let oracle_client = price_oracle::Client::new(&env, &oracle_addr);

    // Create reserve with borrow cap of 1 million tokens
    let borrow_cap = 1_000_000u128; // 1 million tokens
    let (underlying_addr, _, _) = create_reserve_with_cap(
        &env,
        &kinetic_router,
        &kinetic_router_addr,
        &admin,
        &oracle_client,
        0,
        borrow_cap,
        9, // USDC decimals
    );

    // Mint 10 million USDC to user for collateral
    let mint_amount = 10_000_000_000_000_000i128; // 10M USDC
    let stellar_token = token::StellarAssetClient::new(&env, &underlying_addr);
    stellar_token.mint(&user, &mint_amount);

    // Approve and supply
    let token_client = token::Client::new(&env, &underlying_addr);
    let expiration = env.ledger().sequence() + 1000000;
    token_client.approve(&user, &kinetic_router_addr, &mint_amount, &expiration);

    let supply_amount = 10_000_000_000_000_000u128;
    kinetic_router.supply(&user, &underlying_addr, &supply_amount, &user, &0u32);

    // Borrow 1 million USDC (should succeed)
    let borrow_amount_1 = 1_000_000_000_000_000u128; // 1M USDC
    kinetic_router.borrow(&user, &underlying_addr, &borrow_amount_1, &1u32, &0u32, &user);

    // Try to borrow another 1 million USDC (should fail - exceeds cap)
    let borrow_amount_2 = 1_000_000_000_000_000u128; // 1M USDC
    let result = kinetic_router.try_borrow(&user, &underlying_addr, &borrow_amount_2, &1u32, &0u32, &user);
    assert!(result.is_err(), "Should fail when exceeding borrow cap");
}

#[test]
fn test_xlm_large_amounts() {
    let env = Env::default();
    env.mock_all_auths();

    let (admin, user, kinetic_router_addr, oracle_addr, _) = setup_test_environment(&env);
    let kinetic_router = kinetic_router::Client::new(&env, &kinetic_router_addr);
    let oracle_client = price_oracle::Client::new(&env, &oracle_addr);

    // Create reserve with large supply cap (50 million XLM)
    // XLM has 7 decimals
    let supply_cap = 50_000_000u128; // 50 million XLM
    let (underlying_addr, _, _) = create_reserve_with_cap(
        &env,
        &kinetic_router,
        &kinetic_router_addr,
        &admin,
        &oracle_client,
        supply_cap,
        0,
        7, // XLM decimals
    );

    // Mint 20 million XLM to user (20,000,000 * 10^7 = 200_000_000_000_000)
    let mint_amount = 200_000_000_000_000i128; // 20M XLM
    let stellar_token = token::StellarAssetClient::new(&env, &underlying_addr);
    stellar_token.mint(&user, &mint_amount);

    // Approve
    let token_client = token::Client::new(&env, &underlying_addr);
    let expiration = env.ledger().sequence() + 1000000;
    token_client.approve(&user, &kinetic_router_addr, &mint_amount, &expiration);

    // Supply 20 million XLM
    let supply_amount = 200_000_000_000_000u128;
    kinetic_router.supply(&user, &underlying_addr, &supply_amount, &user, &0u32);

    // Verify account data
    let account_data = kinetic_router.get_user_account_data(&user);
    assert!(account_data.total_collateral_base > 0, "Should have collateral");
}

#[test]
fn test_repay_large_amounts() {
    let env = Env::default();
    env.mock_all_auths();

    let (admin, user, kinetic_router_addr, oracle_addr, _) = setup_test_environment(&env);
    let kinetic_router = kinetic_router::Client::new(&env, &kinetic_router_addr);
    let oracle_client = price_oracle::Client::new(&env, &oracle_addr);

    // Create reserve
    let (underlying_addr, _, _) = create_reserve_with_cap(
        &env,
        &kinetic_router,
        &kinetic_router_addr,
        &admin,
        &oracle_client,
        0,
        0,
        9, // USDC decimals
    );

    // Mint 10 million USDC to user
    let mint_amount = 10_000_000_000_000_000i128; // 10M USDC
    let stellar_token = token::StellarAssetClient::new(&env, &underlying_addr);
    stellar_token.mint(&user, &mint_amount);

    // Approve and supply
    let token_client = token::Client::new(&env, &underlying_addr);
    let expiration = env.ledger().sequence() + 1000000;
    token_client.approve(&user, &kinetic_router_addr, &mint_amount, &expiration);

    let supply_amount = 10_000_000_000_000_000u128;
    kinetic_router.supply(&user, &underlying_addr, &supply_amount, &user, &0u32);

    // Borrow 3 million USDC
    let borrow_amount = 3_000_000_000_000_000u128; // 3M USDC
    kinetic_router.borrow(&user, &underlying_addr, &borrow_amount, &1u32, &0u32, &user);

    // Mint more tokens for repayment
    let borrow_amount_i128 = borrow_amount as i128;
    stellar_token.mint(&user, &borrow_amount_i128);
    token_client.approve(&user, &kinetic_router_addr, &borrow_amount_i128, &expiration);

    // Repay the full amount
    kinetic_router.repay(&user, &underlying_addr, &u128::MAX, &1u32, &user);

    // Verify debt is cleared
    let account_data = kinetic_router.get_user_account_data(&user);
    assert_eq!(account_data.total_debt_base, 0, "Debt should be cleared");
}

#[test]
fn test_withdraw_large_amounts() {
    let env = Env::default();
    env.mock_all_auths();

    let (admin, user, kinetic_router_addr, oracle_addr, _) = setup_test_environment(&env);
    let kinetic_router = kinetic_router::Client::new(&env, &kinetic_router_addr);
    let oracle_client = price_oracle::Client::new(&env, &oracle_addr);

    // Create reserve
    let (underlying_addr, _, _) = create_reserve_with_cap(
        &env,
        &kinetic_router,
        &kinetic_router_addr,
        &admin,
        &oracle_client,
        0,
        0,
        9, // USDC decimals
    );

    // Mint 10 million USDC to user
    let mint_amount = 10_000_000_000_000_000i128; // 10M USDC
    let stellar_token = token::StellarAssetClient::new(&env, &underlying_addr);
    stellar_token.mint(&user, &mint_amount);

    // Approve and supply
    let token_client = token::Client::new(&env, &underlying_addr);
    let expiration = env.ledger().sequence() + 1000000;
    token_client.approve(&user, &kinetic_router_addr, &mint_amount, &expiration);

    let supply_amount = 10_000_000_000_000_000u128;
    kinetic_router.supply(&user, &underlying_addr, &supply_amount, &user, &0u32);

    // Withdraw 5 million USDC
    let withdraw_amount = 5_000_000_000_000_000u128; // 5M USDC
    let withdrawn = kinetic_router.withdraw(&user, &underlying_addr, &withdraw_amount, &user);

    assert_eq!(withdrawn, withdraw_amount, "Should withdraw the requested amount");

    // Verify account data
    let account_data = kinetic_router.get_user_account_data(&user);
    assert!(account_data.total_collateral_base > 0, "Should still have some collateral");
}

#[test]
fn test_supply_billion_usdc() {
    let env = Env::default();
    env.mock_all_auths();

    let (admin, user, kinetic_router_addr, oracle_addr, _) = setup_test_environment(&env);
    let kinetic_router = kinetic_router::Client::new(&env, &kinetic_router_addr);
    let oracle_client = price_oracle::Client::new(&env, &oracle_addr);

    // Create reserve with very large supply cap (10 billion tokens)
    let supply_cap = 10_000_000_000u128; // 10 billion tokens
    let (underlying_addr, _, _) = create_reserve_with_cap(
        &env,
        &kinetic_router,
        &kinetic_router_addr,
        &admin,
        &oracle_client,
        supply_cap,
        0,
        9, // USDC decimals
    );

    // Mint 1 billion USDC to user (1,000,000,000 * 10^9 = 1_000_000_000_000_000_000)
    let mint_amount = 1_000_000_000_000_000_000i128; // 1B USDC
    let stellar_token = token::StellarAssetClient::new(&env, &underlying_addr);
    stellar_token.mint(&user, &mint_amount);

    // Approve
    let token_client = token::Client::new(&env, &underlying_addr);
    let expiration = env.ledger().sequence() + 1000000;
    token_client.approve(&user, &kinetic_router_addr, &mint_amount, &expiration);

    // Supply 1 billion USDC
    let supply_amount = 1_000_000_000_000_000_000u128;
    kinetic_router.supply(&user, &underlying_addr, &supply_amount, &user, &0u32);

    // Verify account data
    let account_data = kinetic_router.get_user_account_data(&user);
    assert!(account_data.total_collateral_base > 0, "Should have collateral");
    assert!(account_data.total_collateral_base > 1_000_000_000_000_000_000_000_000u128, "Collateral should be > $1B in WAD");
}

#[test]
fn test_supply_trillion_usdc() {
    let env = Env::default();
    env.mock_all_auths();

    let (admin, user, kinetic_router_addr, oracle_addr, _) = setup_test_environment(&env);
    let kinetic_router = kinetic_router::Client::new(&env, &kinetic_router_addr);
    let oracle_client = price_oracle::Client::new(&env, &oracle_addr);

    // Create reserve with very large supply cap (1 trillion tokens)
    let supply_cap = 1_000_000_000_000u128; // 1 trillion tokens
    let (underlying_addr, _, _) = create_reserve_with_cap(
        &env,
        &kinetic_router,
        &kinetic_router_addr,
        &admin,
        &oracle_client,
        supply_cap,
        0,
        9, // USDC decimals
    );

    // Mint 100 billion USDC to user (100,000,000,000 * 10^9 = 100_000_000_000_000_000_000)
    let mint_amount = 100_000_000_000_000_000_000i128; // 100B USDC
    let stellar_token = token::StellarAssetClient::new(&env, &underlying_addr);
    stellar_token.mint(&user, &mint_amount);

    // Approve
    let token_client = token::Client::new(&env, &underlying_addr);
    let expiration = env.ledger().sequence() + 1000000;
    token_client.approve(&user, &kinetic_router_addr, &mint_amount, &expiration);

    // Supply 100 billion USDC
    let supply_amount = 100_000_000_000_000_000_000u128;
    kinetic_router.supply(&user, &underlying_addr, &supply_amount, &user, &0u32);

    // Verify account data
    let account_data = kinetic_router.get_user_account_data(&user);
    assert!(account_data.total_collateral_base > 0, "Should have collateral");
    assert!(account_data.total_collateral_base > 100_000_000_000_000_000_000_000_000u128, "Collateral should be > $100B in WAD");
}

#[test]
fn test_borrow_billion_usdc() {
    let env = Env::default();
    env.mock_all_auths();

    let (admin, user, kinetic_router_addr, oracle_addr, _) = setup_test_environment(&env);
    let kinetic_router = kinetic_router::Client::new(&env, &kinetic_router_addr);
    let oracle_client = price_oracle::Client::new(&env, &oracle_addr);

    // Create reserve with large borrow cap (5 billion tokens)
    let borrow_cap = 5_000_000_000u128; // 5 billion tokens
    let (underlying_addr, _, _) = create_reserve_with_cap(
        &env,
        &kinetic_router,
        &kinetic_router_addr,
        &admin,
        &oracle_client,
        0,
        borrow_cap,
        9, // USDC decimals
    );

    // Mint 10 billion USDC to user for collateral
    let mint_amount = 10_000_000_000_000_000_000i128; // 10B USDC
    let stellar_token = token::StellarAssetClient::new(&env, &underlying_addr);
    stellar_token.mint(&user, &mint_amount);

    // Approve and supply
    let token_client = token::Client::new(&env, &underlying_addr);
    let expiration = env.ledger().sequence() + 1000000;
    token_client.approve(&user, &kinetic_router_addr, &mint_amount, &expiration);

    let supply_amount = 10_000_000_000_000_000_000u128;
    kinetic_router.supply(&user, &underlying_addr, &supply_amount, &user, &0u32);

    // Borrow 1 billion USDC
    let borrow_amount = 1_000_000_000_000_000_000u128; // 1B USDC
    kinetic_router.borrow(&user, &underlying_addr, &borrow_amount, &1u32, &0u32, &user);

    // Verify account data
    let account_data = kinetic_router.get_user_account_data(&user);
    assert!(account_data.total_debt_base > 0, "Should have debt");
    assert!(account_data.total_debt_base > 1_000_000_000_000_000_000_000_000u128, "Debt should be > $1B in WAD");
    assert!(account_data.total_collateral_base > account_data.total_debt_base, "Collateral should exceed debt");
}

#[test]
fn test_cap_validation_billion() {
    let env = Env::default();
    env.mock_all_auths();

    let (admin, user, kinetic_router_addr, oracle_addr, _) = setup_test_environment(&env);
    let kinetic_router = kinetic_router::Client::new(&env, &kinetic_router_addr);
    let oracle_client = price_oracle::Client::new(&env, &oracle_addr);

    // Create reserve with supply cap of 1 billion tokens
    let supply_cap = 1_000_000_000u128; // 1 billion tokens
    let (underlying_addr, _, _) = create_reserve_with_cap(
        &env,
        &kinetic_router,
        &kinetic_router_addr,
        &admin,
        &oracle_client,
        supply_cap,
        0,
        9, // USDC decimals
    );

    // Mint 2 billion USDC to user
    let mint_amount = 2_000_000_000_000_000_000i128; // 2B USDC
    let stellar_token = token::StellarAssetClient::new(&env, &underlying_addr);
    stellar_token.mint(&user, &mint_amount);

    // Approve
    let token_client = token::Client::new(&env, &underlying_addr);
    let expiration = env.ledger().sequence() + 1000000;
    token_client.approve(&user, &kinetic_router_addr, &mint_amount, &expiration);

    // First supply 1 billion USDC (should succeed)
    let supply_amount_1 = 1_000_000_000_000_000_000u128; // 1B USDC
    kinetic_router.supply(&user, &underlying_addr, &supply_amount_1, &user, &0u32);

    // Try to supply another 1 billion USDC (should fail - exceeds cap)
    let supply_amount_2 = 1_000_000_000_000_000_000u128; // 1B USDC
    let result = kinetic_router.try_supply(&user, &underlying_addr, &supply_amount_2, &user, &0u32);
    assert!(result.is_err(), "Should fail when exceeding supply cap");
}

#[test]
fn test_multiple_users_billion_amounts() {
    let env = Env::default();
    env.mock_all_auths();

    let (admin, user1, kinetic_router_addr, oracle_addr, _) = setup_test_environment(&env);
    let user2 = Address::generate(&env);
    let user3 = Address::generate(&env);
    let kinetic_router = kinetic_router::Client::new(&env, &kinetic_router_addr);
    let oracle_client = price_oracle::Client::new(&env, &oracle_addr);

    // Create reserve with very large supply cap (100 billion tokens)
    let supply_cap = 100_000_000_000u128; // 100 billion tokens
    let (underlying_addr, _, _) = create_reserve_with_cap(
        &env,
        &kinetic_router,
        &kinetic_router_addr,
        &admin,
        &oracle_client,
        supply_cap,
        0,
        9, // USDC decimals
    );

    // Mint 10 billion USDC to each user
    let mint_amount = 10_000_000_000_000_000_000i128; // 10B USDC
    let stellar_token = token::StellarAssetClient::new(&env, &underlying_addr);
    stellar_token.mint(&user1, &mint_amount);
    stellar_token.mint(&user2, &mint_amount);
    stellar_token.mint(&user3, &mint_amount);

    // Approve for all users
    let token_client = token::Client::new(&env, &underlying_addr);
    let expiration = env.ledger().sequence() + 1000000;
    token_client.approve(&user1, &kinetic_router_addr, &mint_amount, &expiration);
    token_client.approve(&user2, &kinetic_router_addr, &mint_amount, &expiration);
    token_client.approve(&user3, &kinetic_router_addr, &mint_amount, &expiration);

    // Each user supplies 10 billion USDC
    let supply_amount = 10_000_000_000_000_000_000u128;
    kinetic_router.supply(&user1, &underlying_addr, &supply_amount, &user1, &0u32);
    kinetic_router.supply(&user2, &underlying_addr, &supply_amount, &user2, &0u32);
    kinetic_router.supply(&user3, &underlying_addr, &supply_amount, &user3, &0u32);

    // Verify all users have collateral
    let account_data_1 = kinetic_router.get_user_account_data(&user1);
    let account_data_2 = kinetic_router.get_user_account_data(&user2);
    let account_data_3 = kinetic_router.get_user_account_data(&user3);
    assert!(account_data_1.total_collateral_base > 0, "User1 should have collateral");
    assert!(account_data_2.total_collateral_base > 0, "User2 should have collateral");
    assert!(account_data_3.total_collateral_base > 0, "User3 should have collateral");
    
    // Total supply should be 30 billion USDC
    // Verify aggregate calculations work correctly
    assert!(account_data_1.total_collateral_base > 10_000_000_000_000_000_000_000_000u128, "User1 collateral should be > $10B");
}

