#![cfg(test)]

use crate::contract::TokenContractClient;

use super::*;
use soroban_sdk::{testutils::{Address as _, MockAuth, MockAuthInvoke}, Address, Env, IntoVal, String};

#[test]
fn test_initialize() {
    let env = Env::default();
    let admin = Address::generate(&env);
    let name = String::from_str(&env, "USD Coin");
    let symbol = String::from_str(&env, "USDC");
    let decimals = 6u32;

    let contract_id = env.register(TokenContract, (admin.clone(), name.clone(), symbol.clone(), decimals.clone()));
    let client = TokenContractClient::new(&env, &contract_id);



    assert_eq!(client.name(), name);
    assert_eq!(client.symbol(), symbol);
    assert_eq!(client.decimals(), decimals);
    assert_eq!(client.admin(), admin);
}

#[test]
fn test_mint() {
    let env = Env::default();
    
    let admin = Address::generate(&env);
    let user = Address::generate(&env);
    let name = String::from_str(&env, "USD Coin");
    let symbol = String::from_str(&env, "USDC");
    let decimals = 6u32;

    let contract_id = env.register(TokenContract, (admin.clone(), name.clone(), symbol.clone(), decimals.clone()));
    let client = TokenContractClient::new(&env, &contract_id);



    // Mock only admin's auth for the mint call
    env.mock_auths(&[MockAuth {
        address: &admin,
        invoke: &MockAuthInvoke {
            contract: &contract_id,
            fn_name: "mint",
            args: (&user, 1000000_i128).into_val(&env),
            sub_invokes: &[],
        },
    }]);

    // Mint tokens to user (admin must authorize)
    client.mint(&user, &1000000);

    assert_eq!(client.balance(&user), 1000000);
}

#[test]
fn test_transfer() {
    let env = Env::default();
    env.mock_all_auths();
    
    let admin = Address::generate(&env);
    let user1 = Address::generate(&env);
    let user2 = Address::generate(&env);
    let name = String::from_str(&env, "USD Coin");
    let symbol = String::from_str(&env, "USDC");
    let decimals = 6u32;

    let contract_id = env.register(TokenContract, (admin.clone(), name.clone(), symbol.clone(), decimals.clone()));
    let client = TokenContractClient::new(&env, &contract_id);



    // Mint tokens to user1
    client.mint(&user1, &1000000);

    // Transfer from user1 to user2 (user1 must authorize)
    client.transfer(&user1, &user2, &500000);

    assert_eq!(client.balance(&user1), 500000);
    assert_eq!(client.balance(&user2), 500000);
}

#[test]
fn test_approve_and_transfer_from() {
    let env = Env::default();
    env.mock_all_auths();
    
    let admin = Address::generate(&env);
    let user1 = Address::generate(&env);
    let user2 = Address::generate(&env);
    let spender = Address::generate(&env);
    let name = String::from_str(&env, "USD Coin");
    let symbol = String::from_str(&env, "USDC");
    let decimals = 6u32;

    let contract_id = env.register(TokenContract, (admin.clone(), name.clone(), symbol.clone(), decimals.clone()));
    let client = TokenContractClient::new(&env, &contract_id);



    // Mint tokens to user1
    client.mint(&user1, &1000000);

    // Approve spender to spend user1's tokens (user1 must authorize)
    client.approve(&user1, &spender, &500000, &1000);

    assert_eq!(client.allowance(&user1, &spender), 500000);

    // Transfer from user1 to user2 using spender (spender must authorize)
    client.transfer_from(&spender, &user1, &user2, &300000);

    assert_eq!(client.balance(&user1), 700000);
    assert_eq!(client.balance(&user2), 300000);
    assert_eq!(client.allowance(&user1, &spender), 200000);
}
