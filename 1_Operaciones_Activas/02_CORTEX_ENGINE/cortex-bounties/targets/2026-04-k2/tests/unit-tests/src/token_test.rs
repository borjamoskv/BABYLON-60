#![cfg(test)]

use crate::base_token;
use soroban_sdk::{testutils::Address as _, Address, Env, String};

fn setup_token(env: &Env) -> (base_token::Client, Address) {
    let admin = Address::generate(env);
    let contract_id = env.register(base_token::WASM, ());
    let client = base_token::Client::new(env, &contract_id);

    client.initialize(
        &admin,
        &String::from_str(env, "USD Coin"),
        &String::from_str(env, "USDC"),
        &6,
    );

    (client, admin)
}

#[test]
fn test_initialize() {
    let env = Env::default();
    let (client, admin) = setup_token(&env);

    assert_eq!(client.name(), String::from_str(&env, "USD Coin"));
    assert_eq!(client.symbol(), String::from_str(&env, "USDC"));
    assert_eq!(client.decimals(), 6u32);
    assert_eq!(client.admin(), admin);
}

#[test]
fn test_mint() {
    let env = Env::default();
    env.mock_all_auths();
    let (client, _admin) = setup_token(&env);
    let user = Address::generate(&env);

    client.mint(&user, &1_000_000);
    assert_eq!(client.balance(&user), 1_000_000);
}

#[test]
fn test_transfer() {
    let env = Env::default();
    env.mock_all_auths();
    let (client, _admin) = setup_token(&env);
    let user1 = Address::generate(&env);
    let user2 = Address::generate(&env);

    client.mint(&user1, &1_000_000);
    client.transfer(&user1, &user2, &500_000);

    assert_eq!(client.balance(&user1), 500_000);
    assert_eq!(client.balance(&user2), 500_000);
}

#[test]
fn test_approve_and_transfer_from() {
    let env = Env::default();
    env.mock_all_auths();
    let (client, _admin) = setup_token(&env);
    let user1 = Address::generate(&env);
    let user2 = Address::generate(&env);
    let spender = Address::generate(&env);

    client.mint(&user1, &1_000_000);
    client.approve(&user1, &spender, &500_000, &1000);

    assert_eq!(client.allowance(&user1, &spender), 500_000);

    client.transfer_from(&spender, &user1, &user2, &300_000);

    assert_eq!(client.balance(&user1), 700_000);
    assert_eq!(client.balance(&user2), 300_000);
    assert_eq!(client.allowance(&user1, &spender), 200_000);
}

// =============================================================================
// WP-C6: Self-transfer must be a no-op (K2 #4 / note 6)
// =============================================================================

/// token.transfer(from == to) must leave balance unchanged.
#[test]
fn test_wp_c6_base_token_transfer_self_is_noop() {
    let env = Env::default();
    env.mock_all_auths();
    let (client, _admin) = setup_token(&env);
    let user = Address::generate(&env);

    client.mint(&user, &1_000_000);
    let balance_before = client.balance(&user);

    // Self-transfer
    client.transfer(&user, &user, &500_000);

    assert_eq!(client.balance(&user), balance_before, "balance unchanged after self-transfer");
}

/// token.transfer_from(from == to) must consume allowance but leave balance unchanged.
#[test]
fn test_wp_c6_base_token_transfer_from_self_consumes_allowance() {
    let env = Env::default();
    env.mock_all_auths();
    let (client, _admin) = setup_token(&env);
    let user = Address::generate(&env);
    let spender = Address::generate(&env);

    client.mint(&user, &1_000_000);
    client.approve(&user, &spender, &500_000, &1000);
    let balance_before = client.balance(&user);

    // Self-transfer via transfer_from
    client.transfer_from(&spender, &user, &user, &300_000);

    assert_eq!(client.balance(&user), balance_before, "balance unchanged after self-transfer");
    assert_eq!(
        client.allowance(&user, &spender), 200_000,
        "allowance consumed even for self-transfer"
    );
}
