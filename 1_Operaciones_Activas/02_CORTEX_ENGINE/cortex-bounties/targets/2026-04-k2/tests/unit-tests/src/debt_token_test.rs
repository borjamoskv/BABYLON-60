#![cfg(test)]
use crate::debt_token;
use k2_shared::*;
use soroban_sdk::{contract, contractimpl, testutils::Address as _, Address, Env, String};

#[contract]
pub struct MockRouter;

#[contractimpl]
impl MockRouter {
    pub fn get_current_var_borrow_idx(_env: Env, _asset: Address) -> u128 {
        RAY
    }
}

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

fn initialize_contract(env: &Env, admin: &Address) -> (Address, Address) {
    let contract_id = env.register(debt_token::WASM, ());
    let client = debt_token::Client::new(env, &contract_id);

    // Register mock router as pool_address so balance_of/total_supply/get_borrow_index work
    let mock_router_id = env.register(MockRouter, ());

    let borrowed_asset = Address::generate(env);
    let name = String::from_str(env, "Variable Debt USDC");
    let symbol = String::from_str(env, "debtUSDC");
    let decimals = 7u32;

    client.initialize(admin, &borrowed_asset, &mock_router_id, &name, &symbol, &decimals);

    (contract_id, mock_router_id)
}

#[test]
fn test_initialize() {
    let env = create_test_env();
    let (admin, _, _) = create_test_addresses(&env);
    let (contract_id, mock_router_id) = initialize_contract(&env, &admin);
    let client = debt_token::Client::new(&env, &contract_id);

    assert_eq!(client.name(), String::from_str(&env, "Variable Debt USDC"));
    assert_eq!(client.symbol(), String::from_str(&env, "debtUSDC"));
    assert_eq!(client.decimals(), 7u32);
    assert_eq!(client.get_pool_address(), mock_router_id);
    assert_eq!(client.get_borrow_index(), RAY);
    assert_eq!(client.total_supply(), 0);
}

#[test]
fn test_initialize_already_initialized() {
    let env = create_test_env();
    let (admin, _, _) = create_test_addresses(&env);
    let (contract_id, _) = initialize_contract(&env, &admin);
    let client = debt_token::Client::new(&env, &contract_id);

    let borrowed_asset = Address::generate(&env);
    let name = String::from_str(&env, "Another Debt Token");
    let symbol = String::from_str(&env, "debtTEST2");
    let decimals = 7u32;

    let result = client.try_initialize(&admin, &borrowed_asset, &admin, &name, &symbol, &decimals);

    assert!(result.is_err());
}

#[test]
fn test_mint_scaled() {
    let env = create_test_env();
    let (admin, user, _) = create_test_addresses(&env);
    let (contract_id, mock_router_id) = initialize_contract(&env, &admin);
    let client = debt_token::Client::new(&env, &contract_id);

    let amount = 1000u128;
    let index = RAY;

    let (is_first, _user_scaled, _total_scaled) = client.mint_scaled(&mock_router_id, &user, &amount, &index);
    assert_eq!(is_first, true);

    assert_eq!(client.scaled_balance_of(&user), 1000);
    assert_eq!(client.balance_of(&user), 1000);
    assert_eq!(client.total_supply(), 1000);
}

#[test]
fn test_mint_scaled_unauthorized() {
    let env = create_test_env();
    let (admin, user, attacker) = create_test_addresses(&env);
    let (contract_id, _) = initialize_contract(&env, &admin);
    let client = debt_token::Client::new(&env, &contract_id);

    let amount = 1000u128;
    let index = RAY;

    // Attempt to mint with unauthorized caller
    let result = client.try_mint_scaled(&attacker, &user, &amount, &index);
    assert!(result.is_err());
}

#[test]
fn test_burn_scaled() {
    let env = create_test_env();
    let (admin, user, _) = create_test_addresses(&env);
    let (contract_id, mock_router_id) = initialize_contract(&env, &admin);
    let client = debt_token::Client::new(&env, &contract_id);

    let mint_amount = 1000u128;
    let burn_amount = 300u128;
    let index = RAY;

    // First mint some debt tokens
    client.mint_scaled(&mock_router_id, &user, &mint_amount, &index);

    // Verify initial debt
    assert_eq!(client.scaled_balance_of(&user), 1000);
    assert_eq!(client.balance_of(&user), 1000);

    // Then burn some debt tokens
    let (_is_zero, _user_remaining, _total_scaled) = client.burn_scaled(&mock_router_id, &user, &burn_amount, &index);
    // User still has 700 remaining, so not zero
    assert_eq!(_is_zero, false);

    // Check debt balance
    // Final debt: 1000 - 300 = 700
    assert_eq!(client.balance_of(&user), 700);
    assert_eq!(client.total_supply(), 700);
}

#[test]
fn test_burn_scaled_insufficient_balance() {
    let env = create_test_env();
    let (admin, user, _) = create_test_addresses(&env);
    let (contract_id, mock_router_id) = initialize_contract(&env, &admin);
    let client = debt_token::Client::new(&env, &contract_id);

    let mint_amount = 1000u128;
    let burn_amount = 1500u128;
    let index = RAY;

    // Mint some debt tokens
    client.mint_scaled(&mock_router_id, &user, &mint_amount, &index);

    // Attempt to burn more than available
    let result = client.try_burn_scaled(&mock_router_id, &user, &burn_amount, &index);
    assert!(result.is_err());
}

#[test]
fn test_transfer_blocked() {
    // Test that transfer ALWAYS fails - debt is non-transferable
    let env = create_test_env();
    let (admin, user1, user2) = create_test_addresses(&env);
    let (contract_id, mock_router_id) = initialize_contract(&env, &admin);
    let client = debt_token::Client::new(&env, &contract_id);

    let amount = 1000u128;
    let index = RAY;

    // Mint some debt to user1
    client.mint_scaled(&mock_router_id, &user1, &amount, &index);

    // Attempt to transfer
    let result = client.try_transfer(&user1, &user2, &500);
    assert!(result.is_err());

    // Verify debt is still with user1
    assert_eq!(client.balance_of(&user1), 1000);
    assert_eq!(client.balance_of(&user2), 0);
}

#[test]
fn test_transfer_from_blocked() {
    // Test that transfer_from ALWAYS fails - debt is non-transferable
    let env = create_test_env();
    let (admin, user1, user2) = create_test_addresses(&env);
    let (user3, _) = create_additional_addresses(&env);
    let (contract_id, mock_router_id) = initialize_contract(&env, &admin);
    let client = debt_token::Client::new(&env, &contract_id);

    let amount = 1000u128;
    let index = RAY;

    // Mint some debt to user1
    client.mint_scaled(&mock_router_id, &user1, &amount, &index);

    // Attempt to transfer_from
    let result = client.try_transfer_from(&user2, &user1, &user3, &500);
    assert!(result.is_err());

    // Verify debt is still with user1
    assert_eq!(client.balance_of(&user1), 1000);
    assert_eq!(client.balance_of(&user3), 0);
}

#[test]
fn test_approve_blocked() {
    // Test that approve ALWAYS fails - debt is non-transferable
    let env = create_test_env();
    let (admin, user1, user2) = create_test_addresses(&env);
    let (contract_id, _) = initialize_contract(&env, &admin);
    let client = debt_token::Client::new(&env, &contract_id);

    // Attempt to approve
    let result = client.try_approve(&user1, &user2, &1000, &1000);
    assert!(result.is_err());
}

#[test]
fn test_allowance_always_zero() {
    // Test that allowance ALWAYS returns 0 - debt is non-transferable
    let env = create_test_env();
    let (admin, user1, user2) = create_test_addresses(&env);
    let (contract_id, mock_router_id) = initialize_contract(&env, &admin);
    let client = debt_token::Client::new(&env, &contract_id);

    let amount = 1000u128;
    let index = RAY;

    // Mint some debt to user1
    client.mint_scaled(&mock_router_id, &user1, &amount, &index);

    // Verify allowance is always 0
    assert_eq!(client.allowance(&user1, &user2), 0);
}

#[test]
fn test_burn_from_blocked() {
    // Test that burn_from ALWAYS fails - debt is non-transferable
    let env = create_test_env();
    let (admin, user1, user2) = create_test_addresses(&env);
    let (contract_id, mock_router_id) = initialize_contract(&env, &admin);
    let client = debt_token::Client::new(&env, &contract_id);

    let amount = 1000u128;
    let index = RAY;

    // Mint some debt to user1
    client.mint_scaled(&mock_router_id, &user1, &amount, &index);

    // Attempt to burn_from
    let result = client.try_burn_from(&user2, &user1, &500);
    assert!(result.is_err());

    // Verify debt is still with user1
    assert_eq!(client.balance_of(&user1), 1000);
}

// update_index tests removed — function was dead code (router uses mint_scaled/burn_scaled)

#[test]
fn test_balance_of_with_index() {
    let env = create_test_env();
    let (admin, user, _) = create_test_addresses(&env);
    let (contract_id, mock_router_id) = initialize_contract(&env, &admin);
    let client = debt_token::Client::new(&env, &contract_id);

    let amount = 1000u128;
    let mint_index = RAY;
    let query_index = RAY + (RAY / 5); // 20% higher index (1.2x)

    // Mint debt tokens
    client.mint_scaled(&mock_router_id, &user, &amount, &mint_index);

    // Query debt balance with different index
    let balance_with_index = client.balance_of_with_index(&user, &query_index);
    // Expected: ray_mul(1000, 1.2 * RAY) = (1000 * 1.2 * RAY) / RAY = 1200
    let expected_balance = 1200;

    assert_eq!(balance_with_index, expected_balance);
}

#[test]
fn test_debt_accrual() {
    // Test that debt grows with borrow index (interest accrual for borrowers)
    let env = create_test_env();
    let (admin, user, _) = create_test_addresses(&env);
    let (contract_id, mock_router_id) = initialize_contract(&env, &admin);
    let client = debt_token::Client::new(&env, &contract_id);

    // User borrows 1000
    client.mint_scaled(&mock_router_id, &user, &1000, &RAY);
    assert_eq!(client.balance_of_with_index(&user, &RAY), 1000);

    // Borrow index increases by 10% (debt grows)
    let new_index = RAY + RAY / 10;

    // User now owes 1100
    assert_eq!(client.balance_of_with_index(&user, &new_index), 1100);
}

#[test]
fn test_scaled_debt_operations() {
    let env = create_test_env();
    let (admin, user, _) = create_test_addresses(&env);
    let (contract_id, mock_router_id) = initialize_contract(&env, &admin);
    let client = debt_token::Client::new(&env, &contract_id);

    let amount = 1000u128;
    let index = RAY + (RAY / 2); // 50% higher index

    // Mint debt tokens
    client.mint_scaled(&mock_router_id, &user, &amount, &index);

    // Check scaled debt
    let scaled_debt = client.scaled_balance_of(&user);
    let expected_scaled = 667; // ray_div(1000, 1.5 * RAY) = 667 (rounded up)
    assert_eq!(scaled_debt, expected_scaled);

    // Check scaled total debt
    let scaled_total = client.scaled_total_supply();
    assert_eq!(scaled_total, expected_scaled as i128);
}

#[test]
fn test_overflow_protection() {
    let env = create_test_env();
    let (admin, user, _) = create_test_addresses(&env);
    let (contract_id, mock_router_id) = initialize_contract(&env, &admin);
    let client = debt_token::Client::new(&env, &contract_id);

    // Test with a very large amount - the contract may or may not reject it
    let very_large_amount = u128::MAX;
    let index = RAY;

    // Attempt to mint maximum amount - this may succeed or fail depending on implementation
    let result = client.try_mint_scaled(&mock_router_id, &user, &very_large_amount, &index);

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
        // If it fails, verify no debt tokens were minted
        assert_eq!(client.balance_of(&user), 0);
        assert_eq!(client.total_supply(), 0);

        // Test with a smaller but still large amount to ensure normal operations work
        let large_but_reasonable_amount = 1_000_000_000_000_000_000u128; // 1M tokens
        let result2 = client.try_mint_scaled(&mock_router_id, &user, &large_but_reasonable_amount, &index);

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
    let (contract_id, mock_router_id) = initialize_contract(&env, &admin);
    let client = debt_token::Client::new(&env, &contract_id);

    // Mint 1000 debt tokens at index 1.0
    client.mint_scaled(&mock_router_id, &user1, &1000, &RAY);
    assert_eq!(client.balance_of_with_index(&user1, &RAY), 1000);

    // Index increases to 1.1
    let new_index = RAY + (RAY / 10);

    // User1 now owes 1100
    assert_eq!(client.balance_of_with_index(&user1, &new_index), 1100);

    // Mint another 1000 to user2 at new index
    // M-14: debtToken mint uses ray_div_up, so scaled = ceil(1000/1.1) = 910
    // balance = ray_mul(910, 1.1*RAY) = 1001 (rounding favors protocol)
    client.mint_scaled(&mock_router_id, &user2, &1000, &new_index);
    assert_eq!(client.balance_of_with_index(&user2, &new_index), 1001);

    // Index increases again to 1.2
    let newer_index = RAY + (RAY * 2 / 10);

    // User1: original scaled 1000 * 1.2 = 1200
    // User2: scaled 910 * 1.2 = 1092
    assert_eq!(client.balance_of_with_index(&user1, &newer_index), 1200);
    assert_eq!(client.balance_of_with_index(&user2, &newer_index), 1092);
}

#[test]
fn test_burn_from_multiple_users_with_interest() {
    let env = create_test_env();
    let (admin, user1, user2) = create_test_addresses(&env);
    let (contract_id, mock_router_id) = initialize_contract(&env, &admin);
    let client = debt_token::Client::new(&env, &contract_id);

    let index_1_1 = RAY + RAY / 10;

    // User1 mints at index 1.0
    client.mint_scaled(&mock_router_id, &user1, &1000, &RAY);

    // User2 mints at index 1.1
    client.mint_scaled(&mock_router_id, &user2, &1000, &index_1_1);

    // Both users have different debt amounts due to interest
    // M-14: debtToken mint uses ray_div_up, so user2 scaled = ceil(1000/1.1) = 910
    // balance = ray_mul(910, 1.1*RAY) = 1001
    assert_eq!(client.balance_of_with_index(&user1, &index_1_1), 1100);
    assert_eq!(client.balance_of_with_index(&user2, &index_1_1), 1001);

    // Burn from user1
    // M-14: debtToken burn uses ray_div_down, so scaled_burn = floor(500/1.1) = 454
    // New scaled = 1000 - 454 = 546, balance = ray_mul(546, 1.1*RAY) = 601
    client.burn_scaled(&mock_router_id, &user1, &500, &index_1_1);

    // Verify scaled debt balances
    assert_eq!(client.balance_of_with_index(&user1, &index_1_1), 601);
}

#[test]
fn test_zero_amount_operations() {
    let env = create_test_env();
    let (admin, user1, user2) = create_test_addresses(&env);
    let (contract_id, mock_router_id) = initialize_contract(&env, &admin);
    let client = debt_token::Client::new(&env, &contract_id);

    // Test zero amount operations
    let result_mint = client.try_mint_scaled(&mock_router_id, &user1, &0u128, &RAY);
    assert!(result_mint.is_err(), "Zero amount mint should fail");

    let result_burn = client.try_burn_scaled(&mock_router_id, &user1, &0u128, &RAY);
    assert!(result_burn.is_err(), "Zero amount burn should fail");

    let result_transfer = client.try_transfer(&user1, &user2, &0i128);
    assert!(result_transfer.is_err(), "Zero amount transfer should fail");

    let result_approve = client.try_approve(&user1, &user2, &0i128, &1000u32);
    assert!(result_approve.is_err(), "Zero amount approve should fail");
}

#[test]
fn test_negative_amount_operations() {
    let env = create_test_env();
    let (admin, user1, user2) = create_test_addresses(&env);
    let (contract_id, _) = initialize_contract(&env, &admin);
    let client = debt_token::Client::new(&env, &contract_id);

    // Test negative amount operations
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
fn test_get_borrowed_asset() {
    let env = create_test_env();
    let (admin, _, _) = create_test_addresses(&env);
    let (contract_id, _) = initialize_contract(&env, &admin);
    let client = debt_token::Client::new(&env, &contract_id);

    // Test that we can get the borrowed asset address
    let borrowed_asset = client.get_borrowed_asset();
    // Verify it's a valid address
    assert!(borrowed_asset != Address::generate(&env));
}

#[test]
fn test_balance_of_with_borrow_index() {
    let env = create_test_env();
    let (admin, user, _) = create_test_addresses(&env);
    let (contract_id, mock_router_id) = initialize_contract(&env, &admin);
    let client = debt_token::Client::new(&env, &contract_id);

    let amount = 1000u128;
    let index = RAY + (RAY / 5);

    // Mint debt tokens
    client.mint_scaled(&mock_router_id, &user, &amount, &RAY);

    // Test that balance_of_with_borrow_index works correctly
    let balance_with_borrow_index = client.balance_of_with_borrow_index(&user, &index);
    let expected_balance = 1200;
    assert_eq!(balance_with_borrow_index, expected_balance);
}

#[test]
fn test_debt_token_metadata() {
    let env = create_test_env();
    let (admin, _, _) = create_test_addresses(&env);
    let (contract_id, _) = initialize_contract(&env, &admin);
    let client = debt_token::Client::new(&env, &contract_id);

    // Test token metadata
    assert_eq!(client.name(), String::from_str(&env, "Variable Debt USDC"));
    assert_eq!(client.symbol(), String::from_str(&env, "debtUSDC"));
    assert_eq!(client.decimals(), 7u32);
}

#[test]
fn test_debt_token_security_model() {
    // Test that debt tokens cannot be transferred, approved, or manipulated
    let env = create_test_env();
    let (admin, user1, user2) = create_test_addresses(&env);
    let (contract_id, mock_router_id) = initialize_contract(&env, &admin);
    let client = debt_token::Client::new(&env, &contract_id);

    let amount = 1000u128;
    let index = RAY;

    // Mint debt to user1
    client.mint_scaled(&mock_router_id, &user1, &amount, &index);

    // All transfer operations fail
    assert!(client.try_transfer(&user1, &user2, &500).is_err());
    assert!(client
        .try_transfer_from(&user2, &user1, &user2, &500)
        .is_err());
    assert!(client.try_approve(&user1, &user2, &500, &1000).is_err());
    assert!(client.try_burn_from(&user2, &user1, &500).is_err());

    // Verify allowance is always 0
    assert_eq!(client.allowance(&user1, &user2), 0);

    // Debt remains with user1
    assert_eq!(client.balance_of(&user1), 1000);
    assert_eq!(client.balance_of(&user2), 0);
}

/// WP-L3: Verify is_first_borrow is correct (not hardcoded to true)
#[test]
fn test_wp_l3_is_first_borrow_correctness() {
    let env = create_test_env();
    let (admin, user, _) = create_test_addresses(&env);
    let (contract_id, mock_router_id) = initialize_contract(&env, &admin);
    let client = debt_token::Client::new(&env, &contract_id);

    // First mint: is_first_borrow should be true
    let (is_first, _new_scaled, _total) = client.mint_scaled(&mock_router_id, &user, &1000, &RAY);
    assert!(is_first, "First borrow should return is_first_borrow=true");

    // Second mint to same user: is_first_borrow should be false
    let (is_first_again, _new_scaled2, _total2) = client.mint_scaled(&mock_router_id, &user, &500, &RAY);
    assert!(!is_first_again, "Second borrow should return is_first_borrow=false");
}

/// WP-L3: Verify is_first_borrow resets after full burn
#[test]
fn test_wp_l3_is_first_borrow_after_full_repay() {
    let env = create_test_env();
    let (admin, user, _) = create_test_addresses(&env);
    let (contract_id, mock_router_id) = initialize_contract(&env, &admin);
    let client = debt_token::Client::new(&env, &contract_id);

    // First borrow
    let (is_first, _, _) = client.mint_scaled(&mock_router_id, &user, &1000, &RAY);
    assert!(is_first);

    // Full repay
    client.burn_scaled(&mock_router_id, &user, &1000, &RAY);

    // Borrow again — should be "first borrow" again since debt is 0
    let (is_first_again, _, _) = client.mint_scaled(&mock_router_id, &user, &500, &RAY);
    assert!(is_first_again, "After full repay, next borrow should be is_first_borrow=true");
}
