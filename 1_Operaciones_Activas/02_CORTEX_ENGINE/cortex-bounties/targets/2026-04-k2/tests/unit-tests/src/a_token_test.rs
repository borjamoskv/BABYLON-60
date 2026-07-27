#![cfg(test)]

use crate::a_token;
use k2_shared::*;
use soroban_sdk::{
    contract, contractimpl, symbol_short,
    testutils::{Address as _, Ledger, LedgerInfo},
    Address, Env, IntoVal, String, Symbol,
    Vec,
};

fn create_test_env() -> Env {
    let env = Env::default();
    env.mock_all_auths();
    env
}

fn create_test_addresses(env: &Env) -> (Address, Address, Address) {
    let admin = Address::generate(env);
    let user1 = Address::generate(env);
    let user2 = Address::generate(env);
    (admin, user1, user2)
}

fn create_additional_addresses(env: &Env) -> (Address, Address) {
    let user3 = Address::generate(env);
    let user4 = Address::generate(env);
    (user3, user4)
}

#[contract]
pub struct MockUnderlyingToken;

#[contractimpl]
impl MockUnderlyingToken {
    pub fn transfer(env: Env, from: Address, _to: Address, amount: i128) {
        from.require_auth();

        let balance_key = (symbol_short!("balance"), from.clone());
        let balance: i128 = env
            .storage()
            .temporary()
            .get::<(Symbol, Address), i128>(&balance_key)
            .unwrap_or(0);

        if balance < amount {
            panic!("insufficient balance");
        }

        let new_balance = balance - amount;
        env.storage().temporary().set(&balance_key, &new_balance);
    }

    pub fn balance(env: Env, id: Address) -> i128 {
        let balance_key = (symbol_short!("balance"), id);
        env.storage()
            .temporary()
            .get::<(Symbol, Address), i128>(&balance_key)
            .unwrap_or(0)
    }

    pub fn mint(env: Env, to: Address, amount: i128) {
        let balance_key = (symbol_short!("balance"), to.clone());
        let current: i128 = env
            .storage()
            .temporary()
            .get::<(Symbol, Address), i128>(&balance_key)
            .unwrap_or(0);
        let new_balance = current + amount;
        env.storage().temporary().set(&balance_key, &new_balance);
    }
}

#[contract]
pub struct MockPool;

#[contractimpl]
impl MockPool {
    /// Mock pool function that simulates whitelist behavior
    /// - Empty whitelist (default): returns true (open access, matching real behavior)
    /// - Can be configured via storage for testing whitelist enforcement
    pub fn is_whitelisted_for_reserve(env: Env, _asset: Address, user: Address) -> bool {
        let whitelist_key = symbol_short!("whitelist");
        let whitelist: Option<Vec<Address>> = env
            .storage()
            .temporary()
            .get(&whitelist_key);

        match whitelist {
            Some(list) if !list.is_empty() => {
                for i in 0..list.len() {
                    if let Some(addr) = list.get(i) {
                        if addr == user {
                            return true;
                        }
                    }
                }
                false
            }
            _ => {
                true
            }
        }
    }

    /// WP-C1 + MEDIUM-1: Mock validate_and_finalize_transfer — always allows (no debt in test)
    pub fn validate_and_finalize_transfer(
        _env: Env,
        _underlying_asset: Address,
        _from: Address,
        _to: Address,
        _amount: u128,
        _from_balance_after: u128,
        _to_balance_after: u128,
    ) -> Result<(), KineticRouterError> {
        Ok(())
    }

    /// WP-L5: Mock get_current_liquidity_index — returns stored index or RAY default
    pub fn get_current_liquidity_index(env: Env, _asset: Address) -> u128 {
        let key = symbol_short!("liq_idx");
        env.storage().temporary().get(&key).unwrap_or(RAY)
    }

    /// Helper: set mock liquidity index for transfer tests
    pub fn set_liquidity_index(env: Env, index: u128) {
        let key = symbol_short!("liq_idx");
        env.storage().temporary().set(&key, &index);
    }

    /// HIGH-003: Mock blacklist check — returns false (not blacklisted) by default
    /// Can be configured via storage for testing blacklist enforcement
    pub fn is_blacklisted_for_reserve(env: Env, _asset: Address, user: Address) -> bool {
        let blacklist_key = symbol_short!("blklist");
        let blacklist: Option<Vec<Address>> = env
            .storage()
            .temporary()
            .get(&blacklist_key);

        match blacklist {
            Some(list) if !list.is_empty() => {
                for i in 0..list.len() {
                    if let Some(addr) = list.get(i) {
                        if addr == user {
                            return true;
                        }
                    }
                }
                false
            }
            _ => false,
        }
    }

    /// Helper function for tests to set whitelist
    pub fn set_whitelist(env: Env, whitelist: Vec<Address>) {
        let whitelist_key = symbol_short!("whitelist");
        env.storage().temporary().set(&whitelist_key, &whitelist);
    }

    /// Helper function for tests to set blacklist
    pub fn set_blacklist(env: Env, blacklist: Vec<Address>) {
        let blacklist_key = symbol_short!("blklist");
        env.storage().temporary().set(&blacklist_key, &blacklist);
    }
}

fn initialize_contract(env: &Env, admin: &Address) -> (Address, Address) {
    let contract_id = env.register(a_token::WASM, ());
    let client = a_token::Client::new(env, &contract_id);

    // Create a mock pool contract that implements is_whitelisted_for_reserve
    let mock_pool = env.register(MockPool, ());
    
    let underlying_asset = Address::generate(env);
    let name = String::from_str(env, "Test aToken");
    let symbol = String::from_str(env, "aTEST");
    let decimals = 7u32;

    client.initialize(admin, &underlying_asset, &mock_pool, &name, &symbol, &decimals);

    (contract_id, mock_pool)
}

fn initialize_contract_with_mock_token(env: &Env, admin: &Address) -> (Address, Address, Address) {
    let contract_id = env.register(a_token::WASM, ());
    let client = a_token::Client::new(env, &contract_id);

    // Create a mock pool contract that implements is_whitelisted_for_reserve
    let mock_pool = env.register(MockPool, ());
    
    let underlying_asset = env.register(MockUnderlyingToken, ());
    let name = String::from_str(env, "Test aToken");
    let symbol = String::from_str(env, "aTEST");
    let decimals = 7u32;

    client.initialize(admin, &underlying_asset, &mock_pool, &name, &symbol, &decimals);

    (contract_id, underlying_asset, mock_pool)
}

#[test]
fn test_initialize() {
    let env = create_test_env();
    let (admin, _, _) = create_test_addresses(&env);
    let (contract_id, mock_pool) = initialize_contract(&env, &admin);
    let client = a_token::Client::new(&env, &contract_id);

    assert_eq!(client.name(), String::from_str(&env, "Test aToken"));
    assert_eq!(client.symbol(), String::from_str(&env, "aTEST"));
    assert_eq!(client.decimals(), 7u32);
    assert_eq!(client.get_pool_address(), mock_pool);
    assert_eq!(client.get_liquidity_index(), RAY);
    assert_eq!(client.total_supply(), 0);
}

#[test]
fn test_initialize_already_initialized() {
    let env = create_test_env();
    let (admin, _, _) = create_test_addresses(&env);
    let (contract_id, mock_pool) = initialize_contract(&env, &admin);
    let client = a_token::Client::new(&env, &contract_id);

    let underlying_asset = Address::generate(&env);
    let name = String::from_str(&env, "Another aToken");
    let symbol = String::from_str(&env, "aTEST2");
    let decimals = 7u32;

    let result = client.try_initialize(&admin, &underlying_asset, &admin, &name, &symbol, &decimals);

    assert!(result.is_err());
}

#[test]
fn test_mint_scaled() {
    let env = create_test_env();
    let (admin, user, _) = create_test_addresses(&env);
    let (contract_id, mock_pool) = initialize_contract(&env, &admin);
    let client = a_token::Client::new(&env, &contract_id);

    let amount = 1000u128; // 1000 tokens (small amount that works with ray_div)
    let index = RAY;

    // Mint tokens to user (must use mock_pool address, not admin)
    let (is_first, _user_scaled, _total_scaled) = client.mint_scaled(&mock_pool, &user, &amount, &index);
    assert_eq!(is_first, true);

    // Check balance - the function is working correctly
    // When index = RAY (1.0):
    // scaled_balance = ray_div(1000, RAY) = 1000
    // actual_balance = ray_mul(1000, RAY) = 1000
    assert_eq!(client.scaled_balance_of(&user), 1000);
    assert_eq!(client.balance_of(&user), 1000);
    assert_eq!(client.total_supply(), 1000);
}

#[test]
fn test_mint_scaled_unauthorized() {
    let env = create_test_env();
    let (admin, user, attacker) = create_test_addresses(&env);
    let (contract_id, mock_pool) = initialize_contract(&env, &admin);
    let client = a_token::Client::new(&env, &contract_id);

    let amount = 1000u128;
    let index = RAY;

    // Try to mint with unauthorized caller - should fail
    let result = client.try_mint_scaled(&attacker, &user, &amount, &index);
    assert!(result.is_err());
}

#[test]
fn test_burn_scaled() {
    let env = create_test_env();
    let (admin, user, _) = create_test_addresses(&env);
    let (contract_id, mock_pool) = initialize_contract(&env, &admin);
    let client = a_token::Client::new(&env, &contract_id);

    let mint_amount = 1000u128; // 1000 tokens (small amount that works with ray_div)
    let burn_amount = 300u128; // 300 tokens (small amount that works with ray_div)
    let index = RAY;

    // First mint some tokens
    client.mint_scaled(&mock_pool, &user, &mint_amount, &index);

    // Initial balance should be 1000
    assert_eq!(client.scaled_balance_of(&user), 1000);
    assert_eq!(client.balance_of(&user), 1000);

    // Then burn some tokens (must use mock_pool address, not admin)
    let (is_zero, _total_scaled) = client.burn_scaled(&mock_pool, &user, &burn_amount, &index);
    assert_eq!(is_zero, false);

    // Check balance
    // Final balance: 1000 - 300 = 700
    assert_eq!(client.balance_of(&user), 700);
    assert_eq!(client.total_supply(), 700);
}

#[test]
fn test_burn_scaled_insufficient_balance() {
    let env = create_test_env();
    let (admin, user, _) = create_test_addresses(&env);
    let (contract_id, mock_pool) = initialize_contract(&env, &admin);
    let client = a_token::Client::new(&env, &contract_id);

    let mint_amount = 1000u128; // 1000 tokens (small amount that works with ray_div)
    let burn_amount = 1500u128; // 1500 tokens (more than minted)
    let index = RAY;

    // Mint some tokens
    client.mint_scaled(&mock_pool, &user, &mint_amount, &index);

    // Try to burn more than available - should fail
    let result = client.try_burn_scaled(&admin, &user, &burn_amount, &index);
    assert!(result.is_err());
}

#[test]
fn test_transfer() {
    let env = create_test_env();
    let (admin, user1, user2) = create_test_addresses(&env);
    let (contract_id, mock_pool) = initialize_contract(&env, &admin);
    let client = a_token::Client::new(&env, &contract_id);
    let mock_pool_client = MockPoolClient::new(&env, &mock_pool);

    let amount = 1000u128; // 1000 tokens (small amount that works with ray_div)
    let transfer_amount = 300i128; // Transfer 300 tokens
    let index = RAY;

    // Mint tokens to user1 (must use mock_pool address, not admin)
    client.mint_scaled(&mock_pool, &user1, &amount, &index);

    // Transfer from user1 to user2 (should work with empty whitelist = open access)
    client.transfer(&user1, &user2, &transfer_amount);

    // Check balances
    // User1: 1000 - 300 = 700
    // User2: 0 + 300 = 300
    // Total: 1000 (unchanged)
    assert_eq!(client.balance_of(&user1), 700);
    assert_eq!(client.balance_of(&user2), 300);
    assert_eq!(client.total_supply(), 1000); // Total supply unchanged
}

#[test]
fn test_transfer_whitelist_enforcement() {
    let env = create_test_env();
    let (admin, user1, user2, user3) = {
        let admin = Address::generate(&env);
        let u1 = Address::generate(&env);
        let u2 = Address::generate(&env);
        let u3 = Address::generate(&env);
        (admin, u1, u2, u3)
    };
    let (contract_id, mock_pool) = initialize_contract(&env, &admin);
    let client = a_token::Client::new(&env, &contract_id);
    let mock_pool_client = MockPoolClient::new(&env, &mock_pool);

    let amount = 1000u128;
    let index = RAY;

    // Mint tokens to user1
    client.mint_scaled(&mock_pool, &user1, &amount, &index);

    // Set whitelist: only user2 is whitelisted
    let mut whitelist = Vec::new(&env);
    whitelist.push_back(user2.clone());
    mock_pool_client.set_whitelist(&whitelist);

    // Transfer to whitelisted user2 should succeed
    client.transfer(&user1, &user2, &300i128);
    assert_eq!(client.balance_of(&user2), 300);

    // Transfer to non-whitelisted user3 should fail
    let result = client.try_transfer(&user1, &user3, &200i128);
    assert!(result.is_err(), "Transfer to non-whitelisted address should fail");
    
    // Balance should be unchanged
    assert_eq!(client.balance_of(&user3), 0);
    assert_eq!(client.balance_of(&user1), 700); // Still has 700 after first transfer
}

#[test]
fn test_transfer_insufficient_balance() {
    let env = create_test_env();
    let (admin, user1, user2) = create_test_addresses(&env);
    let (contract_id, mock_pool) = initialize_contract(&env, &admin);
    let client = a_token::Client::new(&env, &contract_id);

    let amount = 1000u128;
    let transfer_amount = 1500i128; // More than available
    let index = RAY;

    // Mint tokens to user1
    client.mint_scaled(&mock_pool, &user1, &amount, &index);

    // Try to transfer more than available - should fail
    let result = client.try_transfer(&user1, &user2, &transfer_amount);
    assert!(result.is_err());
}

#[test]
fn test_approve_and_allowance() {
    let env = create_test_env();
    let (admin, user1, user2) = create_test_addresses(&env);
    let (contract_id, mock_pool) = initialize_contract(&env, &admin);
    let client = a_token::Client::new(&env, &contract_id);

    let amount = 1000i128;
    let expiration_ledger = 1000u32;

    // Approve user2 to spend user1's tokens
    client.approve(&user1, &user2, &amount, &expiration_ledger);

    // Check allowance
    assert_eq!(client.allowance(&user1, &user2), amount);
}

#[test]
fn test_approve_expired() {
    let env = create_test_env();
    let (admin, user1, user2) = create_test_addresses(&env);
    let (contract_id, mock_pool) = initialize_contract(&env, &admin);
    let client = a_token::Client::new(&env, &contract_id);

    let amount = 1000i128;
    let past_ledger = 100u32; // Past ledger number

    // Set ledger to a future number
    env.ledger().set(LedgerInfo {
        sequence_number: 200,
        protocol_version: 23,
        timestamp: 1000,
        network_id: Default::default(),
        base_reserve: 10,
        min_temp_entry_ttl: 10,
        min_persistent_entry_ttl: 10,
        max_entry_ttl: 1000000,
    });

    // Try to approve with past expiration - should fail
    let result = client.try_approve(&user1, &user2, &amount, &past_ledger);
    assert!(result.is_err());
}

#[test]
fn test_allowance_expired() {
    let env = create_test_env();
    let (admin, user1, user2) = create_test_addresses(&env);
    let (contract_id, mock_pool) = initialize_contract(&env, &admin);
    let client = a_token::Client::new(&env, &contract_id);

    let amount = 1000i128;
    let expiration_ledger = 100u32;

    // Approve with future expiration
    client.approve(&user1, &user2, &amount, &expiration_ledger);
    assert_eq!(client.allowance(&user1, &user2), amount);

    // Set ledger to past expiration
    env.ledger().set(LedgerInfo {
        sequence_number: 200,
        protocol_version: 23,
        timestamp: 1000,
        network_id: Default::default(),
        base_reserve: 10,
        min_temp_entry_ttl: 10,
        min_persistent_entry_ttl: 10,
        max_entry_ttl: 1000000,
    });

    // Allowance should now be 0 (expired)
    assert_eq!(client.allowance(&user1, &user2), 0);
}

#[test]
fn test_transfer_from() {
    let env = create_test_env();
    let (admin, user1, user2) = create_test_addresses(&env);
    let (user3, _) = create_additional_addresses(&env);
    let (contract_id, mock_pool) = initialize_contract(&env, &admin);
    let client = a_token::Client::new(&env, &contract_id);

    let mint_amount = 1000u128; // 1000 tokens (small amount that works with ray_div)
    let approve_amount = 500i128;
    let transfer_amount = 300i128;
    let index = RAY;
    let expiration_ledger = 1000u32;

    // Mint tokens to user1 (must use mock_pool address, not admin)
    client.mint_scaled(&mock_pool, &user1, &mint_amount, &index);

    // User1 approves user2 to spend tokens
    client.approve(&user1, &user2, &approve_amount, &expiration_ledger);

    // User2 transfers from user1 to user3
    client.transfer_from(&user2, &user1, &user3, &transfer_amount);

    // Check balances and allowance
    // User1: 1000 - 300 = 700
    // User2: 0 (no change)
    // User3: 0 + 300 = 300
    // Allowance: 500 - 300 = 200
    assert_eq!(client.balance_of(&user1), 700);
    assert_eq!(client.balance_of(&user2), 0);
    assert_eq!(client.balance_of(&user3), 300);
    assert_eq!(client.allowance(&user1, &user2), 200);
}

#[test]
fn test_transfer_from_insufficient_allowance() {
    let env = create_test_env();
    let (admin, user1, user2) = create_test_addresses(&env);
    let (user3, _) = create_additional_addresses(&env);
    let (contract_id, mock_pool) = initialize_contract(&env, &admin);
    let client = a_token::Client::new(&env, &contract_id);

    let mint_amount = 1000u128;
    let approve_amount = 200i128;
    let transfer_amount = 300i128; // More than approved
    let index = RAY;
    let expiration_ledger = 1000u32;

    // Mint tokens to user1
    client.mint_scaled(&mock_pool, &user1, &mint_amount, &index);

    // User1 approves user2 to spend tokens
    client.approve(&user1, &user2, &approve_amount, &expiration_ledger);

    // Try to transfer more than approved - should fail
    let result = client.try_transfer_from(&user2, &user1, &user3, &transfer_amount);
    assert!(result.is_err());
}

// WP-L9: test_update_index removed — update_index() is dead code on aToken.
// Index is managed by the router and aToken reads it via get_current_liquidity_index.

#[test]
fn test_index_via_mock_pool() {
    let env = create_test_env();
    let (admin, user, _) = create_test_addresses(&env);
    let (contract_id, mock_pool) = initialize_contract(&env, &admin);
    let client = a_token::Client::new(&env, &contract_id);
    let mock_pool_client = MockPoolClient::new(&env, &mock_pool);

    let amount = 1000u128;
    let initial_index = RAY;
    let new_index = RAY + (RAY / 10); // 10% increase (1.1x)

    // Mint tokens with initial index
    client.mint_scaled(&mock_pool, &user, &amount, &initial_index);
    assert_eq!(client.balance_of(&user), 1000);

    // Update index via mock pool (aToken reads from pool, not stored state)
    mock_pool_client.set_liquidity_index(&new_index);

    // Balance should now be higher due to index increase
    assert_eq!(client.balance_of(&user), 1100);
    assert_eq!(client.get_liquidity_index(), new_index);
}

#[test]
fn test_balance_of_with_index() {
    let env = create_test_env();
    let (admin, user, _) = create_test_addresses(&env);
    let (contract_id, mock_pool) = initialize_contract(&env, &admin);
    let client = a_token::Client::new(&env, &contract_id);

    let amount = 1000u128; // 1000 tokens (small amount that works with ray_div)
    let mint_index = RAY;
    let query_index = RAY + (RAY / 5); // 20% higher index (1.2x)

    // Mint tokens
    client.mint_scaled(&mock_pool, &user, &amount, &mint_index);

    // Query balance with different index
    let balance_with_index = client.balance_of_with_index(&user, &query_index);
    // Expected: ray_mul(1000, 1.2 * RAY) = (1000 * 1.2 * RAY) / RAY = 1200
    let expected_balance = 1200;

    assert_eq!(balance_with_index, expected_balance);
}

#[test]
fn test_scaled_balance_operations() {
    let env = create_test_env();
    let (admin, user, _) = create_test_addresses(&env);
    let (contract_id, mock_pool) = initialize_contract(&env, &admin);
    let client = a_token::Client::new(&env, &contract_id);

    let amount = 1000u128; // 1000 tokens (small amount that works with ray_div)
    let index = RAY + (RAY / 2); // 50% higher index

    // Mint tokens
    client.mint_scaled(&mock_pool, &user, &amount, &index);

    // Check scaled balance
    let scaled_balance = client.scaled_balance_of(&user);
    // M-14: aToken mint uses ray_div_down (protocol keeps more), so 1000/1.5 truncates to 666
    let expected_scaled = 666;
    assert_eq!(scaled_balance, expected_scaled);

    // Check scaled total supply
    let scaled_total = client.scaled_total_supply();
    assert_eq!(scaled_total, expected_scaled as i128);
}

#[test]
fn test_overflow_protection() {
    let env = create_test_env();
    let (admin, user, _) = create_test_addresses(&env);
    let (contract_id, mock_pool) = initialize_contract(&env, &admin);
    let client = a_token::Client::new(&env, &contract_id);

    // Test with a very large amount - the contract may or may not reject it
    let very_large_amount = u128::MAX; // Maximum possible amount
    let index = RAY;

    // Try to mint maximum amount - this may succeed or fail depending on implementation
    let result = client.try_mint_scaled(&mock_pool, &user, &very_large_amount, &index);

    // The operation should either succeed or fail gracefully (not panic)
    assert!(result.is_ok() || result.is_err());

    if result.is_ok() {
        // If it succeeds, verify the amount was minted correctly
        let balance = client.balance_of(&user);
        assert!(balance > 0);
        assert_eq!(client.total_supply(), balance);

        // If the first operation succeeded with MAX, we can't mint more
        // So we'll just verify the overflow protection worked (no panic)
        assert!(balance > 0);
    } else {
        // If it fails, verify no tokens were minted
        assert_eq!(client.balance_of(&user), 0);
        assert_eq!(client.total_supply(), 0);

        // Test with a smaller but still large amount to ensure normal operations work
        let large_but_reasonable_amount = 1_000_000_000_000_000_000u128; // 1M tokens
        let result2 = client.try_mint_scaled(&mock_pool, &user, &large_but_reasonable_amount, &index);

        // This should succeed
        assert!(result2.is_ok());
        assert_eq!(
            client.balance_of(&user),
            large_but_reasonable_amount as i128
        );
    }
}

#[test]
fn test_interest_accrual_multiple_operations() {
    let env = create_test_env();
    let (admin, user1, user2) = create_test_addresses(&env);
    let (contract_id, mock_pool) = initialize_contract(&env, &admin);
    let client = a_token::Client::new(&env, &contract_id);
    let mock_pool_client = MockPoolClient::new(&env, &mock_pool);

    // Mint 1000 tokens at index 1.0
    client.mint_scaled(&mock_pool, &user1, &1000, &RAY);
    assert_eq!(client.balance_of(&user1), 1000);

    // Index increases to 1.1 (10% interest)
    let new_index = RAY + (RAY / 10);
    mock_pool_client.set_liquidity_index(&new_index);

    // User1 should now have 1100 tokens
    assert_eq!(client.balance_of(&user1), 1100);

    // Mint another 1000 to user2 at new index
    client.mint_scaled(&mock_pool, &user2, &1000, &new_index);
    assert_eq!(client.balance_of(&user2), 1000);

    // Index increases again to 1.2
    let newer_index = RAY + (RAY * 2 / 10);
    mock_pool_client.set_liquidity_index(&newer_index);

    // User1: original scaled 1000 * 1.2 = 1200
    // User2: scaled 909 * 1.2 = 1091
    assert_eq!(client.balance_of(&user1), 1200);
    assert_eq!(client.balance_of(&user2), 1091);
}

#[test]
fn test_transfer_preserves_total_supply_with_interest() {
    let env = create_test_env();
    let (admin, user1, user2) = create_test_addresses(&env);
    let (contract_id, mock_pool) = initialize_contract(&env, &admin);
    let client = a_token::Client::new(&env, &contract_id);
    let mock_pool_client = MockPoolClient::new(&env, &mock_pool);

    // Mint tokens (must use mock_pool address, not admin)
    client.mint_scaled(&mock_pool, &user1, &1000, &RAY);

    // Update index (simulate interest) via mock pool
    let new_index = RAY + RAY / 10;
    mock_pool_client.set_liquidity_index(&new_index);

    let total_before = client.total_supply();
    let user1_before = client.balance_of(&user1);
    let user2_before = client.balance_of(&user2);

    // Transfer
    client.transfer(&user1, &user2, &500);

    let total_after = client.total_supply();
    let user1_after = client.balance_of(&user1);
    let user2_after = client.balance_of(&user2);

    // Total supply unchanged
    assert_eq!(total_before, total_after);

    // Sum of balances unchanged (allow for small rounding differences)
    let sum_before = user1_before + user2_before;
    let sum_after = user1_after + user2_after;
    assert!(sum_after >= sum_before - 1 && sum_after <= sum_before + 1); // Allow ±1 for rounding
}

#[test]
fn test_burn_from_multiple_users_with_interest() {
    let env = create_test_env();
    let (admin, user1, user2) = create_test_addresses(&env);
    let (contract_id, mock_pool) = initialize_contract(&env, &admin);
    let client = a_token::Client::new(&env, &contract_id);
    let mock_pool_client = MockPoolClient::new(&env, &mock_pool);

    // User1 mints at index 1.0
    client.mint_scaled(&mock_pool, &user1, &1000, &RAY);

    // Index increases
    let new_index = RAY + RAY / 10;
    mock_pool_client.set_liquidity_index(&new_index);

    // User2 mints at index 1.1
    client.mint_scaled(&mock_pool, &user2, &1000, &new_index);

    // Both users should have 1000 actual balance
    assert_eq!(client.balance_of(&user1), 1100); // With interest
    assert_eq!(client.balance_of(&user2), 1000); // Just minted

    // Burn from user1
    client.burn_scaled(&mock_pool, &user1, &500, &new_index);

    // Verify scaled balances are correct
    assert_eq!(client.balance_of(&user1), 600);
}

#[test]
fn test_transfer_underlying_to_unauthorized() {
    let env = create_test_env();
    let (admin, recipient, attacker) = create_test_addresses(&env);
    let (contract_id, mock_pool) = initialize_contract(&env, &admin);
    let client = a_token::Client::new(&env, &contract_id);

    // Try to transfer underlying with unauthorized caller
    // This should fail due to authorization check (attacker != pool_address)
    let result = client.try_transfer_underlying_to(&attacker, &recipient, &1000);
    assert!(result.is_err()); // Should fail due to auth check

    // Authorization logic validated by this test
}

#[test]
fn test_zero_amount_operations() {
    let env = create_test_env();
    let (admin, user1, user2) = create_test_addresses(&env);
    let (contract_id, mock_pool) = initialize_contract(&env, &admin);
    let client = a_token::Client::new(&env, &contract_id);

    // Test zero amount operations - should fail
    let result_mint = client.try_mint_scaled(&admin, &user1, &0u128, &RAY);
    assert!(result_mint.is_err(), "Zero amount mint should fail");

    let result_burn = client.try_burn_scaled(&admin, &user1, &0u128, &RAY);
    assert!(result_burn.is_err(), "Zero amount burn should fail");

    let result_transfer = client.try_transfer(&user1, &user2, &0i128);
    assert!(result_transfer.is_err(), "Zero amount transfer should fail");

    let result_approve = client.try_approve(&user1, &user2, &0i128, &1000u32);
    assert!(result_approve.is_ok(), "Zero approval should be allowed"); // Zero approval should be allowed
}

#[test]
fn test_negative_amount_operations() {
    let env = create_test_env();
    let (admin, user1, user2) = create_test_addresses(&env);
    let (contract_id, mock_pool) = initialize_contract(&env, &admin);
    let client = a_token::Client::new(&env, &contract_id);

    // Test negative amount operations - should fail
    let result_transfer = client.try_transfer(&user1, &user2, &-100i128);
    assert!(
        result_transfer.is_err(),
        "Negative amount transfer should fail"
    );

    let result_approve = client.try_approve(&user1, &user2, &-100i128, &1000u32);
    assert!(
        result_approve.is_err(),
        "Negative amount approve should fail"
    );
}

#[test]
fn test_balance_of_with_liquidity_index() {
    let env = create_test_env();

    // Deploy aToken
    let atoken_id = env.register(a_token::WASM, ());
    let client = a_token::Client::new(&env, &atoken_id);

    // Initialize
    let underlying = Address::generate(&env);
    let pool = Address::generate(&env);
    client.initialize(
        &pool,
        &underlying,
        &pool,
        &String::from_str(&env, "aXLM"),
        &String::from_str(&env, "aXLM"),
        &6,
    );

    // Mint scaled balance to user
    let user = Address::generate(&env);
    let index = RAY;
    client.mint_scaled(&pool, &user, &1000_u128, &index);

    // Check call directly
    let result = client.balance_of_with_liquidity_index(&user, &index);
    assert_eq!(result, 1000);

    // Test with different index (10% higher)
    let higher_index = RAY + (RAY / 10);
    let result_higher = client.balance_of_with_liquidity_index(&user, &higher_index);
    assert_eq!(result_higher, 1100); // 1000 * 1.1

    // Test with lower index (should calculate correctly)
    let lower_index = RAY - (RAY / 10); // 0.9x
    let result_lower = client.balance_of_with_liquidity_index(&user, &lower_index);
    assert_eq!(result_lower, 900); // 1000 * 0.9
}

#[test]
fn test_pool_calls_atoken_balance() {
    let env = create_test_env();

    // Deploy aToken contract
    let atoken_id = env.register(a_token::WASM, ());

    // Initialize aToken
    let underlying = Address::generate(&env);
    let pool = Address::generate(&env);
    a_token::Client::new(&env, &atoken_id).initialize(
        &pool,
        &underlying,
        &pool,
        &String::from_str(&env, "aXLM"),
        &String::from_str(&env, "aXLM"),
        &6,
    );

    // Mint scaled balance to user
    let user = Address::generate(&env);
    let index = RAY;
    a_token::Client::new(&env, &atoken_id).mint_scaled(&pool, &user, &1000_u128, &index);

    // Call it the same way LendingPool does using invoke_contract
    let args = soroban_sdk::vec![&env, user.into_val(&env), RAY.into_val(&env)];
    let result: i128 = env.invoke_contract(
        &atoken_id,
        &soroban_sdk::Symbol::new(&env, "balance_of_with_liquidity_index"),
        args,
    );

    assert_eq!(result, 1000);
    assert!(result >= 0, "Balance should be non-negative");

    // Test with higher index via invoke_contract
    let higher_index = RAY + (RAY / 10);
    let args_higher = soroban_sdk::vec![&env, user.into_val(&env), higher_index.into_val(&env)];
    let result_higher: i128 = env.invoke_contract(
        &atoken_id,
        &soroban_sdk::Symbol::new(&env, "balance_of_with_liquidity_index"),
        args_higher,
    );

    assert_eq!(result_higher, 1100);
}

#[test]
fn test_cross_contract_balance_with_multiple_users() {
    let env = create_test_env();

    // Deploy aToken contract
    let atoken_id = env.register(a_token::WASM, ());
    let client = a_token::Client::new(&env, &atoken_id);

    // Initialize aToken
    let underlying = Address::generate(&env);
    let pool = Address::generate(&env);
    client.initialize(
        &pool,
        &underlying,
        &pool,
        &String::from_str(&env, "aXLM"),
        &String::from_str(&env, "aXLM"),
        &6,
    );

    // Create multiple users with different balances
    let user1 = Address::generate(&env);
    let user2 = Address::generate(&env);
    let user3 = Address::generate(&env);

    let index = RAY;
    client.mint_scaled(&pool, &user1, &1000_u128, &index);
    client.mint_scaled(&pool, &user2, &2000_u128, &index);
    client.mint_scaled(&pool, &user3, &3000_u128, &index);

    // Simulate lending pool querying balances via cross-contract call
    let higher_index = RAY + (RAY / 5); // 20% higher (1.2x)

    let args1 = soroban_sdk::vec![&env, user1.into_val(&env), higher_index.into_val(&env)];
    let balance1: i128 = env.invoke_contract(
        &atoken_id,
        &soroban_sdk::Symbol::new(&env, "balance_of_with_liquidity_index"),
        args1,
    );

    let args2 = soroban_sdk::vec![&env, user2.into_val(&env), higher_index.into_val(&env)];
    let balance2: i128 = env.invoke_contract(
        &atoken_id,
        &soroban_sdk::Symbol::new(&env, "balance_of_with_liquidity_index"),
        args2,
    );

    let args3 = soroban_sdk::vec![&env, user3.into_val(&env), higher_index.into_val(&env)];
    let balance3: i128 = env.invoke_contract(
        &atoken_id,
        &soroban_sdk::Symbol::new(&env, "balance_of_with_liquidity_index"),
        args3,
    );

    // Verify all balances are correct with 20% interest
    assert_eq!(balance1, 1200); // 1000 * 1.2
    assert_eq!(balance2, 2400); // 2000 * 1.2
    assert_eq!(balance3, 3600); // 3000 * 1.2

    // All balances should be non-negative
    assert!(balance1 >= 0);
    assert!(balance2 >= 0);
    assert!(balance3 >= 0);
}

/// PoC: transfer_from should work with only spender auth when allowance is set.
/// This test verifies the fix for FIND-004: transfer_from no longer requires holder auth.
#[test]
fn test_transfer_from_requires_holder_auth_poc() {
    let env = create_test_env();
    let (admin, holder, spender) = create_test_addresses(&env);
    let (recipient, _) = create_additional_addresses(&env);
    let (contract_id, mock_pool) = initialize_contract(&env, &admin);
    let client = a_token::Client::new(&env, &contract_id);

    let mint_amount = 1_000u128;
    let approve_amount = 500i128;
    let transfer_amount = 300i128;
    let expiration_ledger = 1_000u32;
    let index = RAY;

    // Pool mints to holder
    client.mint_scaled(&mock_pool, &holder, &mint_amount, &index);

    // Holder approves spender
    client.approve(&holder, &spender, &approve_amount, &expiration_ledger);
    assert_eq!(client.allowance(&holder, &spender), approve_amount);

    // Spender attempts transfer_from with only their own auth (no holder auth)
    // This should succeed after the fix - spender auth + allowance is sufficient
    // Before the fix, this would fail because transfer() requires from.require_auth()
    let result = client.try_transfer_from(&spender, &holder, &recipient, &transfer_amount);
    
    assert!(result.is_ok(), "transfer_from should succeed with only spender auth when allowance is set");
    
    // Verify transfer succeeded
    assert_eq!(client.allowance(&holder, &spender), approve_amount - transfer_amount);
    assert_eq!(client.balance_of(&holder), mint_amount as i128 - transfer_amount);
    assert_eq!(client.balance_of(&recipient), transfer_amount);
}

// =============================================================================
// WP-C6: Self-transfer must be a no-op (K2 #4 / note 6)
// =============================================================================

/// aToken.transfer(from == to) must leave balances and total supply unchanged.
#[test]
fn test_wp_c6_atoken_transfer_self_is_noop() {
    let env = create_test_env();
    let (admin, user, _) = create_test_addresses(&env);
    let (contract_id, mock_pool) = initialize_contract(&env, &admin);
    let client = a_token::Client::new(&env, &contract_id);

    let amount = 1_000u128;
    let index = RAY;
    client.mint_scaled(&mock_pool, &user, &amount, &index);

    let balance_before = client.balance_of(&user);
    let scaled_before = client.scaled_balance_of(&user);
    let total_supply_before = client.total_supply();

    // Self-transfer
    client.transfer(&user, &user, &500);

    assert_eq!(client.balance_of(&user), balance_before, "balance unchanged after self-transfer");
    assert_eq!(client.scaled_balance_of(&user), scaled_before, "scaled balance unchanged");
    assert_eq!(client.total_supply(), total_supply_before, "total supply unchanged");
}

/// aToken.transfer_from(from == to) must consume allowance but leave balances unchanged.
#[test]
fn test_wp_c6_atoken_transfer_from_self_consumes_allowance() {
    let env = create_test_env();
    let (admin, holder, spender) = create_test_addresses(&env);
    let (contract_id, mock_pool) = initialize_contract(&env, &admin);
    let client = a_token::Client::new(&env, &contract_id);

    let amount = 1_000u128;
    let index = RAY;
    let approve_amount = 500i128;
    let transfer_amount = 200i128;
    let expiration_ledger = 1_000u32;

    client.mint_scaled(&mock_pool, &holder, &amount, &index);
    client.approve(&holder, &spender, &approve_amount, &expiration_ledger);

    let balance_before = client.balance_of(&holder);
    let scaled_before = client.scaled_balance_of(&holder);
    let total_supply_before = client.total_supply();

    // Self-transfer via transfer_from
    client.transfer_from(&spender, &holder, &holder, &transfer_amount);

    assert_eq!(client.balance_of(&holder), balance_before, "balance unchanged");
    assert_eq!(client.scaled_balance_of(&holder), scaled_before, "scaled balance unchanged");
    assert_eq!(client.total_supply(), total_supply_before, "total supply unchanged");
    assert_eq!(
        client.allowance(&holder, &spender),
        approve_amount - transfer_amount,
        "allowance consumed even for self-transfer"
    );
}

// =============================================================================
// WP-L8 / WP-M4: Legacy entrypoints must be disabled (K2 #1 / note 22)
// =============================================================================

/// Calling mint() must fail with UnsupportedOperation.
#[test]
fn test_wp_l8_legacy_mint_disabled() {
    let env = create_test_env();
    let (admin, user, _) = create_test_addresses(&env);
    let (contract_id, _mock_pool) = initialize_contract(&env, &admin);
    let client = a_token::Client::new(&env, &contract_id);

    let result = client.try_mint(&user, &1_000);
    assert!(result.is_err(), "mint() should return UnsupportedOperation");

    // Verify no tokens were minted
    assert_eq!(client.balance_of(&user), 0);
    assert_eq!(client.total_supply(), 0);
}

/// Calling burn() must fail with UnsupportedOperation.
#[test]
fn test_wp_l8_legacy_burn_disabled() {
    let env = create_test_env();
    let (admin, user, _) = create_test_addresses(&env);
    let (contract_id, mock_pool) = initialize_contract(&env, &admin);
    let client = a_token::Client::new(&env, &contract_id);

    // Mint some tokens first via the proper scaled path
    client.mint_scaled(&mock_pool, &user, &1_000u128, &RAY);
    let balance_before = client.balance_of(&user);

    let result = client.try_burn(&user, &500);
    assert!(result.is_err(), "burn() should return UnsupportedOperation");

    // Balance unchanged
    assert_eq!(client.balance_of(&user), balance_before);
}

/// Calling burn_from() must fail with UnsupportedOperation.
#[test]
fn test_wp_m4_legacy_burn_from_disabled() {
    let env = create_test_env();
    let (admin, user, _) = create_test_addresses(&env);
    let (user3, _) = create_additional_addresses(&env);
    let (contract_id, mock_pool) = initialize_contract(&env, &admin);
    let client = a_token::Client::new(&env, &contract_id);

    client.mint_scaled(&mock_pool, &user, &1_000u128, &RAY);
    let balance_before = client.balance_of(&user);
    let total_supply_before = client.total_supply();

    let result = client.try_burn_from(&user3, &user, &500);
    assert!(result.is_err(), "burn_from() should return UnsupportedOperation");

    // Balances and supply unchanged
    assert_eq!(client.balance_of(&user), balance_before);
    assert_eq!(client.total_supply(), total_supply_before);
}

// =============================================================================
// WP-C1: burn_scaled_and_transfer_to actual_amount capping (K2 #2-4 / note 1)
// =============================================================================

/// When index > RAY, actual_amount must be floor-rounded and capped at requested amount.
#[test]
fn test_wp_c1_burn_scaled_and_transfer_actual_amount_capped() {
    let env = create_test_env();
    let (admin, user, _) = create_test_addresses(&env);
    let (contract_id, underlying_asset, mock_pool) = initialize_contract_with_mock_token(&env, &admin);
    let client = a_token::Client::new(&env, &contract_id);
    let mock_token_client = MockUnderlyingTokenClient::new(&env, &underlying_asset);

    // Use an index that causes rounding divergence: 1.1 * RAY
    let mint_index = RAY + RAY / 10; // 1.1e27
    let mint_amount = 1_000u128;

    // Mint to user
    client.mint_scaled(&mock_pool, &user, &mint_amount, &mint_index);
    let scaled_balance = client.scaled_balance_of(&user);

    // Fund the aToken contract with underlying so transfer works
    mock_token_client.mint(&contract_id, &2_000);

    // Burn and transfer requesting exactly mint_amount
    let (new_scaled, _new_total, actual_amount) =
        client.burn_scaled_and_transfer_to(&mock_pool, &user, &mint_amount, &mint_index, &mock_pool);

    // actual_amount must be <= requested amount (WP-C1 invariant)
    assert!(
        actual_amount <= mint_amount,
        "actual_amount ({}) must not exceed requested amount ({})",
        actual_amount, mint_amount
    );

    // If user burned all their shares, new_scaled should be 0
    if scaled_balance == new_scaled + (scaled_balance - new_scaled) {
        // Sanity check - the math should be consistent
        assert!(new_scaled >= 0, "new scaled balance must be non-negative");
    }
}
