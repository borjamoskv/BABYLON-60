#![cfg(test)]

use crate::{a_token, debt_token, interest_rate_strategy, kinetic_router, price_oracle};
use soroban_sdk::{
    contract, contractimpl,
    testutils::{Address as _},
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
    let mut init_args = Vec::new(env);
    init_args.push_back(admin.clone().into_val(env));
    init_args.push_back((0_000_000_000_000_000_000u128).into_val(env));
    init_args.push_back((40_000_000_000_000_000_000u128).into_val(env));
    init_args.push_back((100_000_000_000_000_000_000u128).into_val(env));
    init_args.push_back((800_000_000_000_000_000_000_000_000u128).into_val(env));
    let _: () = env.invoke_contract(&contract_id, &Symbol::new(env, "initialize"), init_args);
    contract_id
}

// Helper to setup a basic pool with a reserve
fn setup_pool_with_reserve(env: &Env) -> (kinetic_router::Client, Address, Address, Address, Address) {
    let admin = Address::generate(env);
    let user = Address::generate(env);

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
    let a_token_client = a_token::Client::new(env, &a_token_addr);
    let a_name = String::from_str(env, "Test aToken");
    let a_symbol = String::from_str(env, "aTEST");
    a_token_client.initialize(
        &admin,
        &underlying_addr,
        &kinetic_router_addr,
        &a_name,
        &a_symbol,
        &7u32,
    );

    let debt_token_addr = env.register(debt_token::WASM, ());
    let debt_token_client = debt_token::Client::new(env, &debt_token_addr);
    let d_name = String::from_str(env, "Test DebtToken");
    let d_symbol = String::from_str(env, "dTEST");
    debt_token_client.initialize(
        &admin,
        &underlying_addr,
        &kinetic_router_addr,
        &d_name,
        &d_symbol,
        &7u32,
    );

    // Register asset with oracle and set price (1 USD with 14 decimals)
    let asset_enum = price_oracle::Asset::Stellar(underlying_addr.clone());
    oracle_client.add_asset(&admin, &asset_enum);
    oracle_client.set_manual_override(
        &admin,
        &asset_enum,
        &Some(1_000_000_000_000_000u128), // 1 USD with 14 decimals
        &Some(env.ledger().timestamp() + 604_800), // 7 days (max allowed by L-04)
    );

    kinetic_router.init_reserve(
        &pool_configurator,
        &underlying_addr,
        &a_token_addr,
        &debt_token_addr,
        &interest_rate_strategy,
        &treasury,
        &params,
    );

    (kinetic_router, kinetic_router_addr, underlying_addr, a_token_addr, debt_token_addr)
}

/// TEST-44: Verify supply function rejects on_behalf_of == aToken address
#[test]
#[should_panic(expected = "Error(Contract, #2)")]
fn test_supply_to_atoken_rejected() {
    let env = Env::default();
    env.mock_all_auths();

    let (kinetic_router, kinetic_router_addr, underlying_addr, a_token_addr, _debt_token_addr) = 
        setup_pool_with_reserve(&env);

    let user = Address::generate(&env);
    let supply_amount = 1_000_000u128;

    // Mint tokens to user
    let token_admin = Address::generate(&env);
    let stellar_token = token::StellarAssetClient::new(&env, &underlying_addr);
    stellar_token.mint(&user, &(supply_amount as i128));

    // Approve router to spend tokens
    let token_client = token::Client::new(&env, &underlying_addr);
    let max_entry_ttl = 1000000u32;
    let new_expiration = (env.ledger().sequence() as u32) + max_entry_ttl - 1;
    token_client.approve(
        &user,
        &kinetic_router_addr,
        &(supply_amount as i128),
        &new_expiration,
    );

    // This should panic with OperationError::RecipientIsAToken (error code #2)
    kinetic_router.supply(&user, &underlying_addr, &supply_amount, &a_token_addr, &0u32);
}

/// TEST-44: Verify supply function rejects on_behalf_of == debtToken address
#[test]
#[should_panic(expected = "Error(Contract, #3)")]
fn test_supply_to_debttoken_rejected() {
    let env = Env::default();
    env.mock_all_auths();

    let (kinetic_router, kinetic_router_addr, underlying_addr, _a_token_addr, debt_token_addr) = 
        setup_pool_with_reserve(&env);

    let user = Address::generate(&env);
    let supply_amount = 1_000_000u128;

    // Mint tokens to user
    let token_admin = Address::generate(&env);
    let stellar_token = token::StellarAssetClient::new(&env, &underlying_addr);
    stellar_token.mint(&user, &(supply_amount as i128));

    // Approve router to spend tokens
    let token_client = token::Client::new(&env, &underlying_addr);
    let max_entry_ttl = 1000000u32;
    let new_expiration = (env.ledger().sequence() as u32) + max_entry_ttl - 1;
    token_client.approve(
        &user,
        &kinetic_router_addr,
        &(supply_amount as i128),
        &new_expiration,
    );

    // This should panic with OperationError::RecipientIsDebtToken (error code #3)
    kinetic_router.supply(&user, &underlying_addr, &supply_amount, &debt_token_addr, &0u32);
}

/// TEST-44: Verify supply function accepts normal user addresses
#[test]
fn test_supply_to_normal_user_accepted() {
    let env = Env::default();
    env.mock_all_auths();

    let (kinetic_router, kinetic_router_addr, underlying_addr, _a_token_addr, _debt_token_addr) = 
        setup_pool_with_reserve(&env);

    let user = Address::generate(&env);
    let supply_amount = 1_000_000u128;

    // Mint tokens to user
    let token_admin = Address::generate(&env);
    let stellar_token = token::StellarAssetClient::new(&env, &underlying_addr);
    stellar_token.mint(&user, &(supply_amount as i128));

    // Approve router to spend tokens
    let token_client = token::Client::new(&env, &underlying_addr);
    let max_entry_ttl = 1000000u32;
    let new_expiration = (env.ledger().sequence() as u32) + max_entry_ttl - 1;
    token_client.approve(
        &user,
        &kinetic_router_addr,
        &(supply_amount as i128),
        &new_expiration,
    );

    // This should succeed
    kinetic_router.supply(&user, &underlying_addr, &supply_amount, &user, &0u32);
}

/// TEST-44: Verify withdraw function rejects to == aToken address
#[test]
#[should_panic(expected = "Error(Contract, #2)")]
fn test_withdraw_to_atoken_rejected() {
    let env = Env::default();
    env.mock_all_auths();

    let (kinetic_router, kinetic_router_addr, underlying_addr, a_token_addr, _debt_token_addr) = 
        setup_pool_with_reserve(&env);

    let user = Address::generate(&env);
    let supply_amount = 1_000_000u128;

    // First supply some tokens
    let token_admin = Address::generate(&env);
    let stellar_token = token::StellarAssetClient::new(&env, &underlying_addr);
    stellar_token.mint(&user, &(supply_amount as i128));

    let token_client = token::Client::new(&env, &underlying_addr);
    let max_entry_ttl = 1000000u32;
    let new_expiration = (env.ledger().sequence() as u32) + max_entry_ttl - 1;
    token_client.approve(
        &user,
        &kinetic_router_addr,
        &(supply_amount as i128),
        &new_expiration,
    );

    kinetic_router.supply(&user, &underlying_addr, &supply_amount, &user, &0u32);

    // Now try to withdraw to aToken address - should panic with error #2
    kinetic_router.withdraw(&user, &underlying_addr, &supply_amount, &a_token_addr);
}

/// TEST-44: Verify withdraw function rejects to == debtToken address
#[test]
#[should_panic(expected = "Error(Contract, #3)")]
fn test_withdraw_to_debttoken_rejected() {
    let env = Env::default();
    env.mock_all_auths();

    let (kinetic_router, kinetic_router_addr, underlying_addr, _a_token_addr, debt_token_addr) = 
        setup_pool_with_reserve(&env);

    let user = Address::generate(&env);
    let supply_amount = 1_000_000u128;

    // First supply some tokens
    let token_admin = Address::generate(&env);
    let stellar_token = token::StellarAssetClient::new(&env, &underlying_addr);
    stellar_token.mint(&user, &(supply_amount as i128));

    let token_client = token::Client::new(&env, &underlying_addr);
    let max_entry_ttl = 1000000u32;
    let new_expiration = (env.ledger().sequence() as u32) + max_entry_ttl - 1;
    token_client.approve(
        &user,
        &kinetic_router_addr,
        &(supply_amount as i128),
        &new_expiration,
    );

    kinetic_router.supply(&user, &underlying_addr, &supply_amount, &user, &0u32);

    // Now try to withdraw to debtToken address - should panic with error #3
    kinetic_router.withdraw(&user, &underlying_addr, &supply_amount, &debt_token_addr);
}

/// TEST-44: Verify borrow function rejects on_behalf_of == aToken address
#[test]
#[should_panic(expected = "Error(Contract, #2)")]
fn test_borrow_to_atoken_rejected() {
    let env = Env::default();
    env.mock_all_auths();

    let (kinetic_router, kinetic_router_addr, underlying_addr, a_token_addr, _debt_token_addr) = 
        setup_pool_with_reserve(&env);

    let liquidity_provider = Address::generate(&env);
    let supply_amount = 10_000_000u128;

    // First, have a liquidity provider supply tokens
    let token_admin = Address::generate(&env);
    let stellar_token = token::StellarAssetClient::new(&env, &underlying_addr);
    stellar_token.mint(&liquidity_provider, &(supply_amount as i128));

    let token_client = token::Client::new(&env, &underlying_addr);
    let max_entry_ttl = 1000000u32;
    let new_expiration = (env.ledger().sequence() as u32) + max_entry_ttl - 1;
    token_client.approve(
        &liquidity_provider,
        &kinetic_router_addr,
        &(supply_amount as i128),
        &new_expiration,
    );

    kinetic_router.supply(&liquidity_provider, &underlying_addr, &supply_amount, &liquidity_provider, &0u32);

    let borrower = Address::generate(&env);
    let borrow_amount = 1_000_000u128;

    // Borrower needs collateral first
    stellar_token.mint(&borrower, &(supply_amount as i128));
    token_client.approve(
        &borrower,
        &kinetic_router_addr,
        &(supply_amount as i128),
        &new_expiration,
    );
    kinetic_router.supply(&borrower, &underlying_addr, &supply_amount, &borrower, &0u32);
    kinetic_router.set_user_use_reserve_as_coll(&borrower, &underlying_addr, &true);

    // This should panic with OperationError::RecipientIsAToken (error code #2)
    kinetic_router.borrow(&borrower, &underlying_addr, &borrow_amount, &1u32, &0u32, &a_token_addr);
}

/// TEST-44: Verify borrow function rejects on_behalf_of == debtToken address
#[test]
#[should_panic(expected = "Error(Contract, #3)")]
fn test_borrow_to_debttoken_rejected() {
    let env = Env::default();
    env.mock_all_auths();

    let (kinetic_router, kinetic_router_addr, underlying_addr, _a_token_addr, debt_token_addr) = 
        setup_pool_with_reserve(&env);

    let liquidity_provider = Address::generate(&env);
    let supply_amount = 10_000_000u128;

    // First, have a liquidity provider supply tokens
    let token_admin = Address::generate(&env);
    let stellar_token = token::StellarAssetClient::new(&env, &underlying_addr);
    stellar_token.mint(&liquidity_provider, &(supply_amount as i128));

    let token_client = token::Client::new(&env, &underlying_addr);
    let max_entry_ttl = 1000000u32;
    let new_expiration = (env.ledger().sequence() as u32) + max_entry_ttl - 1;
    token_client.approve(
        &liquidity_provider,
        &kinetic_router_addr,
        &(supply_amount as i128),
        &new_expiration,
    );

    kinetic_router.supply(&liquidity_provider, &underlying_addr, &supply_amount, &liquidity_provider, &0u32);

    let borrower = Address::generate(&env);
    let borrow_amount = 1_000_000u128;

    // Borrower needs collateral first
    stellar_token.mint(&borrower, &(supply_amount as i128));
    token_client.approve(
        &borrower,
        &kinetic_router_addr,
        &(supply_amount as i128),
        &new_expiration,
    );
    kinetic_router.supply(&borrower, &underlying_addr, &supply_amount, &borrower, &0u32);
    kinetic_router.set_user_use_reserve_as_coll(&borrower, &underlying_addr, &true);

    // This should panic with OperationError::RecipientIsDebtToken (error code #3)
    kinetic_router.borrow(&borrower, &underlying_addr, &borrow_amount, &1u32, &0u32, &debt_token_addr);
}
