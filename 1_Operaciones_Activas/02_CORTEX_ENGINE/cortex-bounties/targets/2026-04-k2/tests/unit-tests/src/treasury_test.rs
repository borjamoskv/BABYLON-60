#![cfg(test)]

use crate::treasury;
use soroban_sdk::{
    contract, contractimpl, symbol_short, token,
    testutils::Address as _,
    Address, Env, Symbol,
};

fn create_test_env() -> Env {
    let env = Env::default();
    env.mock_all_auths();
    env
}

fn create_treasury(env: &Env) -> Address {
    env.register(treasury::WASM, ())
}

#[contract]
pub struct MockToken;

#[contractimpl]
impl MockToken {
    pub fn balance(env: Env, id: Address) -> i128 {
        let balance_key = (symbol_short!("balance"), id);
        env.storage()
            .temporary()
            .get::<(Symbol, Address), i128>(&balance_key)
            .unwrap_or(0)
    }

    pub fn transfer(env: Env, from: Address, to: Address, amount: i128) -> bool {
        from.require_auth();

        if amount < 0 {
            return false;
        }

        let from_key = (symbol_short!("balance"), from.clone());
        let to_key = (symbol_short!("balance"), to.clone());

        let from_balance = env
            .storage()
            .temporary()
            .get::<(Symbol, Address), i128>(&from_key)
            .unwrap_or(0);

        if from_balance < amount {
            return false;
        }

        let to_balance = env
            .storage()
            .temporary()
            .get::<(Symbol, Address), i128>(&to_key)
            .unwrap_or(0);

        env.storage()
            .temporary()
            .set(&from_key, &(from_balance - amount));
        env.storage()
            .temporary()
            .set(&to_key, &(to_balance + amount));

        true
    }

    pub fn mint(env: Env, to: Address, amount: i128) {
        let to_key = (symbol_short!("balance"), to.clone());
        let balance = env
            .storage()
            .temporary()
            .get::<(Symbol, Address), i128>(&to_key)
            .unwrap_or(0);
        env.storage()
            .temporary()
            .set(&to_key, &(balance + amount));
    }
}

fn create_token(env: &Env) -> Address {
    env.register(MockToken, ())
}

// Create a Stellar Asset Contract for withdraw tests (uses standard token interface)
fn create_stellar_token(env: &Env, admin: &Address) -> Address {
    let token_contract = env.register_stellar_asset_contract_v2(admin.clone());
    token_contract.address()
}

#[test]
fn test_initialize() {
    let env = create_test_env();
    let treasury_id = create_treasury(&env);
    let client = treasury::Client::new(&env, &treasury_id);
    let admin = Address::generate(&env);
    let different_admin = Address::generate(&env);

    client.initialize(&admin);
    
    // Verify admin persists across calls
    assert_eq!(client.get_admin(), admin);
}

#[test]
fn test_initialize_twice() {
    let env = create_test_env();
    let treasury_id = create_treasury(&env);
    let client = treasury::Client::new(&env, &treasury_id);
    let admin = Address::generate(&env);

    client.initialize(&admin);
    let result = client.try_initialize(&admin);
    assert_eq!(result, Err(Ok(treasury::TreasuryError::AlreadyInitialized)));
}

#[test]
fn test_deposit() {
    let env = create_test_env();
    let treasury_id = create_treasury(&env);
    let client = treasury::Client::new(&env, &treasury_id);
    let admin = Address::generate(&env);
    let token = create_token(&env);
    let other_token = create_token(&env);

    client.initialize(&admin);

    // Verify balance is 0 before deposit
    assert_eq!(client.get_balance(&token), 0u128);

    let amount = 1000u128;
    let from = Address::generate(&env);

    // Mint tokens to treasury first
    env.as_contract(&token, || {
        MockToken::mint(env.clone(), treasury_id.clone(), amount as i128);
    });

    client.deposit(&admin, &token, &amount, &from);

    // Verify balance increased correctly
    assert_eq!(client.get_balance(&token), amount);
    // Verify other token balance is still 0
    assert_eq!(client.get_balance(&other_token), 0u128);
}

#[test]
fn test_deposit_multiple_assets() {
    let env = create_test_env();
    let treasury_id = create_treasury(&env);
    let client = treasury::Client::new(&env, &treasury_id);
    let admin = Address::generate(&env);
    let token1 = create_token(&env);
    let token2 = create_token(&env);

    client.initialize(&admin);

    // Mint tokens to treasury first
    env.as_contract(&token1, || {
        MockToken::mint(env.clone(), treasury_id.clone(), 1000);
    });
    env.as_contract(&token2, || {
        MockToken::mint(env.clone(), treasury_id.clone(), 2000);
    });

    client.deposit(&admin, &token1, &1000u128, &admin);
    client.deposit(&admin, &token2, &2000u128, &admin);

    assert_eq!(client.get_balance(&token1), 1000u128);
    assert_eq!(client.get_balance(&token2), 2000u128);
}

#[test]
fn test_deposit_accumulates() {
    let env = create_test_env();
    let treasury_id = create_treasury(&env);
    let client = treasury::Client::new(&env, &treasury_id);
    let admin = Address::generate(&env);
    let token = create_token(&env);

    client.initialize(&admin);

    // Verify initial balance
    assert_eq!(client.get_balance(&token), 0u128);

    // Mint tokens to treasury first
    env.as_contract(&token, || {
        MockToken::mint(env.clone(), treasury_id.clone(), 1000);
    });

    // First deposit
    client.deposit(&admin, &token, &500u128, &admin);
    assert_eq!(client.get_balance(&token), 500u128);

    // Second deposit should accumulate
    client.deposit(&admin, &token, &300u128, &admin);
    assert_eq!(client.get_balance(&token), 800u128);

    // Third deposit
    client.deposit(&admin, &token, &200u128, &admin);
    assert_eq!(client.get_balance(&token), 1000u128);
}

#[test]
fn test_deposit_zero_amount() {
    let env = create_test_env();
    let treasury_id = create_treasury(&env);
    let client = treasury::Client::new(&env, &treasury_id);
    let admin = Address::generate(&env);
    let token = create_token(&env);

    client.initialize(&admin);

    let result = client.try_deposit(&admin, &token, &0u128, &admin);
    assert_eq!(result, Err(Ok(treasury::TreasuryError::InvalidAmount)));
}

#[test]
fn test_deposit_before_init() {
    let env = create_test_env();
    let treasury_id = create_treasury(&env);
    let client = treasury::Client::new(&env, &treasury_id);
    let token = create_token(&env);
    let from = Address::generate(&env);

    let result = client.try_deposit(&from, &token, &1000u128, &from);
    assert_eq!(result, Err(Ok(treasury::TreasuryError::NotInitialized)));
}

#[test]
fn test_withdraw() {
    let env = create_test_env();
    let treasury_id = create_treasury(&env);
    let client = treasury::Client::new(&env, &treasury_id);
    let admin = Address::generate(&env);
    let token = create_stellar_token(&env, &admin);
    let recipient = Address::generate(&env);

    client.initialize(&admin);

    // Mint tokens to treasury using Stellar Asset Client
    let sac = token::StellarAssetClient::new(&env, &token);
    sac.mint(&treasury_id, &1000);

    // Record the deposit in treasury's internal accounting
    client.deposit(&admin, &token, &1000u128, &admin);
    assert_eq!(client.get_balance(&token), 1000u128);

    // Withdraw should succeed and decrease balance
    client.withdraw(&admin, &token, &500u128, &recipient);
    
    // Verify balance decreased correctly
    assert_eq!(client.get_balance(&token), 500u128);
    
    // Verify recipient received tokens
    let token_client = token::Client::new(&env, &token);
    assert_eq!(token_client.balance(&recipient), 500);
}

#[test]
fn test_withdraw_insufficient_balance() {
    let env = create_test_env();
    let treasury_id = create_treasury(&env);
    let client = treasury::Client::new(&env, &treasury_id);
    let admin = Address::generate(&env);
    let token = create_token(&env);
    let recipient = Address::generate(&env);

    client.initialize(&admin);

    // Mint tokens to treasury first
    env.as_contract(&token, || {
        MockToken::mint(env.clone(), treasury_id.clone(), 100);
    });

    client.deposit(&admin, &token, &100u128, &admin);
    assert_eq!(client.get_balance(&token), 100u128);

    // Try to withdraw more than available
    let result = client.try_withdraw(&admin, &token, &200u128, &recipient);
    assert_eq!(result, Err(Ok(treasury::TreasuryError::InsufficientBalance)));
    
    // Verify balance unchanged after failed withdrawal
    assert_eq!(client.get_balance(&token), 100u128);
}

#[test]
fn test_withdraw_unauthorized() {
    let env = create_test_env();
    let treasury_id = create_treasury(&env);
    let client = treasury::Client::new(&env, &treasury_id);
    let admin = Address::generate(&env);
    let unauthorized = Address::generate(&env);
    let token = create_stellar_token(&env, &admin);
    let recipient = Address::generate(&env);

    client.initialize(&admin);

    // Mint tokens to treasury
    let sac = token::StellarAssetClient::new(&env, &token);
    sac.mint(&treasury_id, &1000);

    client.deposit(&admin, &token, &1000u128, &admin);
    assert_eq!(client.get_balance(&token), 1000u128);

    // Verify unauthorized address cannot withdraw
    let result = client.try_withdraw(&unauthorized, &token, &500u128, &recipient);
    assert_eq!(result, Err(Ok(treasury::TreasuryError::Unauthorized)));
    
    // Verify balance unchanged after unauthorized attempt
    assert_eq!(client.get_balance(&token), 1000u128);
    
    // Verify admin can still withdraw
    client.withdraw(&admin, &token, &500u128, &recipient);
    assert_eq!(client.get_balance(&token), 500u128);
}

#[test]
fn test_withdraw_zero_amount() {
    let env = create_test_env();
    let treasury_id = create_treasury(&env);
    let client = treasury::Client::new(&env, &treasury_id);
    let admin = Address::generate(&env);
    let token = create_token(&env);
    let recipient = Address::generate(&env);

    client.initialize(&admin);

    let result = client.try_withdraw(&admin, &token, &0u128, &recipient);
    assert_eq!(result, Err(Ok(treasury::TreasuryError::InvalidAmount)));
}

#[test]
fn test_get_all_balances() {
    let env = create_test_env();
    let treasury_id = create_treasury(&env);
    let client = treasury::Client::new(&env, &treasury_id);
    let admin = Address::generate(&env);
    let token1 = create_token(&env);
    let token2 = create_token(&env);
    let token3 = create_token(&env);

    client.initialize(&admin);

    // Initially should be empty or have zero balances
    let initial_balances = client.get_all_balances();
    assert_eq!(initial_balances.len(), 0);

    // Mint tokens to treasury first
    env.as_contract(&token1, || {
        MockToken::mint(env.clone(), treasury_id.clone(), 1000);
    });
    env.as_contract(&token2, || {
        MockToken::mint(env.clone(), treasury_id.clone(), 2000);
    });

    client.deposit(&admin, &token1, &1000u128, &admin);
    client.deposit(&admin, &token2, &2000u128, &admin);

    let balances = client.get_all_balances();
    
    // Verify correct balances
    assert_eq!(balances.get(token1.clone()).unwrap(), 1000u128);
    assert_eq!(balances.get(token2.clone()).unwrap(), 2000u128);
    
    // Verify token3 is not in the map (or has zero balance)
    assert_eq!(balances.get(token3.clone()).unwrap_or(0), 0u128);
    
    // Verify map size
    assert_eq!(balances.len(), 2);
}

#[test]
fn test_sync_balance() {
    let env = create_test_env();
    let treasury_id = create_treasury(&env);
    let client = treasury::Client::new(&env, &treasury_id);
    let admin = Address::generate(&env);
    let token = create_token(&env);

    client.initialize(&admin);

    // Mint tokens directly to treasury (simulating external transfer)
    env.as_contract(&token, || {
        MockToken::mint(env.clone(), treasury_id.clone(), 5000);
    });

    // Sync should update internal balance tracking
    let synced_balance = client.try_sync_balance(&token).unwrap();
    assert_eq!(synced_balance, Ok(5000u128));
    assert_eq!(client.get_balance(&token), 5000u128);

    // Mint more tokens
    env.as_contract(&token, || {
        MockToken::mint(env.clone(), treasury_id.clone(), 2000);
    });

    // Sync again should update to new total
    let synced_balance = client.try_sync_balance(&token).unwrap();
    assert_eq!(synced_balance, Ok(7000u128));
    assert_eq!(client.get_balance(&token), 7000u128);
}

#[test]
fn test_withdraw_decreases_balance() {
    let env = create_test_env();
    let treasury_id = create_treasury(&env);
    let client = treasury::Client::new(&env, &treasury_id);
    let admin = Address::generate(&env);
    let token = create_stellar_token(&env, &admin);
    let recipient = Address::generate(&env);

    client.initialize(&admin);

    // Mint tokens to treasury
    let sac = token::StellarAssetClient::new(&env, &token);
    sac.mint(&treasury_id, &1000);

    // Mint tokens to treasury first
    env.as_contract(&token, || {
        MockToken::mint(env.clone(), treasury_id.clone(), 1000);
    });

    // Deposit and verify balance
    client.deposit(&admin, &token, &1000u128, &admin);
    assert_eq!(client.get_balance(&token), 1000u128);

    // Withdraw partial amount
    client.withdraw(&admin, &token, &300u128, &recipient);
    assert_eq!(client.get_balance(&token), 700u128);

    // Withdraw more
    client.withdraw(&admin, &token, &200u128, &recipient);
    assert_eq!(client.get_balance(&token), 500u128);

    // Verify final balance
    assert_eq!(client.get_balance(&token), 500u128);
}

#[test]
fn test_multiple_withdrawals() {
    let env = create_test_env();
    let treasury_id = create_treasury(&env);
    let client = treasury::Client::new(&env, &treasury_id);
    let admin = Address::generate(&env);
    let token = create_stellar_token(&env, &admin);
    let recipient1 = Address::generate(&env);
    let recipient2 = Address::generate(&env);

    client.initialize(&admin);

    // Mint tokens to treasury
    let sac = token::StellarAssetClient::new(&env, &token);
    sac.mint(&treasury_id, &10000);

    // Mint tokens to treasury first
    env.as_contract(&token, || {
        MockToken::mint(env.clone(), treasury_id.clone(), 10000);
    });

    client.deposit(&admin, &token, &10000u128, &admin);
    assert_eq!(client.get_balance(&token), 10000u128);

    // Multiple withdrawals to different recipients
    client.withdraw(&admin, &token, &2000u128, &recipient1);
    assert_eq!(client.get_balance(&token), 8000u128);

    client.withdraw(&admin, &token, &3000u128, &recipient2);
    assert_eq!(client.get_balance(&token), 5000u128);

    client.withdraw(&admin, &token, &1000u128, &recipient1);
    assert_eq!(client.get_balance(&token), 4000u128);

    // Verify recipients received tokens
    let token_client = token::Client::new(&env, &token);
    assert_eq!(token_client.balance(&recipient1), 3000);
    assert_eq!(token_client.balance(&recipient2), 3000);
}
