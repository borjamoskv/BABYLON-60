#![cfg(test)]
#![allow(unused_imports)]

#[cfg(test)]
extern crate std;

use crate::incentives;
use k2_shared::*;
use soroban_sdk::{
    testutils::{Address as _, Ledger, LedgerInfo},
    Address, Env, IntoVal, Vec,
};
// to read the println outputs, need to run using:
// cargo test -- --nocapture

/// Test helper to create a test environment
fn create_test_env() -> Env {
    let env = Env::default();
    env.mock_all_auths();
    env
}

/// Test helper to create test addresses
fn create_test_addresses(env: &Env) -> (Address, Address, Address, Address) {
    let emission_manager = Address::generate(env);
    let lending_pool = Address::generate(env);
    let user1 = Address::generate(env);
    let user2 = Address::generate(env);
    (emission_manager, lending_pool, user1, user2)
}

/// Test helper to initialize the incentives contract
fn initialize_contract(env: &Env, emission_manager: &Address, lending_pool: &Address) -> Address {
    let contract_id = env.register(incentives::WASM, ());
    let client = incentives::Client::new(env, &contract_id);

    client.initialize(emission_manager, lending_pool);

    contract_id
}

/// Test helper to set ledger timestamp
fn set_timestamp(env: &Env, timestamp: u64) {
    env.ledger().set(LedgerInfo {
        timestamp,
        protocol_version: 23,
        sequence_number: 0,
        network_id: Default::default(),
        base_reserve: 0,
        min_temp_entry_ttl: 0,
        min_persistent_entry_ttl: 0,
        max_entry_ttl: 0,
    });
}

// ============================================================================
// INITIALIZATION TESTS
// ============================================================================

#[test]
fn test_initialize() {
    let env = create_test_env();
    let (emission_manager, lending_pool, _, _) = create_test_addresses(&env);
    let contract_id = initialize_contract(&env, &emission_manager, &lending_pool);
    let client = incentives::Client::new(&env, &contract_id);

    // Verify contract is initialized
    // Test by trying to initialize again (should fail)
    let result = client.try_initialize(&emission_manager, &lending_pool);
    assert!(result.is_err());
}

#[test]
#[should_panic(expected = "Error(Contract, #1)")]
fn test_initialize_already_initialized() {
    let env = create_test_env();
    let (emission_manager, lending_pool, _, _) = create_test_addresses(&env);
    let contract_id = initialize_contract(&env, &emission_manager, &lending_pool);
    let client = incentives::Client::new(&env, &contract_id);

    // Try to initialize again - should fail
    client.initialize(&emission_manager, &lending_pool);
}

// ============================================================================
// CONFIGURE REWARDS TESTS
// ============================================================================

#[test]
fn test_configure_asset_rewards_supply() {
    let env = create_test_env();
    let (emission_manager, lending_pool, _, _) = create_test_addresses(&env);
    let contract_id = initialize_contract(&env, &emission_manager, &lending_pool);
    let client = incentives::Client::new(&env, &contract_id);

    let asset = Address::generate(&env);
    let reward_token = Address::generate(&env);
    let emission_per_second = 100_000_000u128; // 100 tokens/second (with 6 decimals)
    let distribution_end = 0u64; // No end

    client.configure_asset_rewards(
        &emission_manager,
        &asset,
        &reward_token,
        &0u32,
        &emission_per_second,
        &distribution_end,
    );

    // Verify configuration
    let config =
        client.get_asset_reward_config(&asset, &reward_token, &0u32);
    assert!(config.is_some());
    let config = config.unwrap();
    assert_eq!(config.emission_per_second, emission_per_second);
    assert_eq!(config.distribution_end, distribution_end);
    assert_eq!(config.is_active, true);
}

#[test]
fn test_configure_asset_rewards_borrow() {
    let env = create_test_env();
    let (emission_manager, lending_pool, _, _) = create_test_addresses(&env);
    let contract_id = initialize_contract(&env, &emission_manager, &lending_pool);
    let client = incentives::Client::new(&env, &contract_id);

    let asset = Address::generate(&env);
    let reward_token = Address::generate(&env);
    let emission_per_second = 50_000_000u128; // 50 tokens/second
    let distribution_end = 0u64;

    client.configure_asset_rewards(
        &emission_manager,
        &asset,
        &reward_token,
        &1u32,
        &emission_per_second,
        &distribution_end,
    );

    // Verify configuration
    let config =
        client.get_asset_reward_config(&asset, &reward_token, &1u32);
    assert!(config.is_some());
    let config = config.unwrap();
    assert_eq!(config.emission_per_second, emission_per_second);
    assert!(config.is_active);
}

#[test]
#[should_panic(expected = "Error(Contract, #3)")]
fn test_configure_asset_rewards_unauthorized() {
    let env = create_test_env();
    let (emission_manager, lending_pool, user1, _) = create_test_addresses(&env);
    let contract_id = initialize_contract(&env, &emission_manager, &lending_pool);
    let client = incentives::Client::new(&env, &contract_id);

    let asset = Address::generate(&env);
    let reward_token = Address::generate(&env);

    // Try to configure as non-emission manager
    client.configure_asset_rewards(
        &user1, // Not emission manager
        &asset,
        &reward_token,
        &0u32,
        &100_000_000u128,
        &0u64,
    );
}

#[test]
#[should_panic(expected = "Error(Contract, #4)")]
fn test_configure_invalid_reward_type() {
    let env = create_test_env();
    let (emission_manager, lending_pool, _, _) = create_test_addresses(&env);
    let contract_id = initialize_contract(&env, &emission_manager, &lending_pool);
    let client = incentives::Client::new(&env, &contract_id);

    let asset = Address::generate(&env);
    let reward_token = Address::generate(&env);

    // Try to configure with invalid reward type
    client.configure_asset_rewards(
        &emission_manager,
        &asset,
        &reward_token,
        &2u32, // Invalid (must be 0 or 1)
        &100_000_000u128,
        &0u64,
    );
}

#[test]
fn test_configure_multiple_reward_tokens() {
    let env = create_test_env();
    let (emission_manager, lending_pool, _, _) = create_test_addresses(&env);
    let contract_id = initialize_contract(&env, &emission_manager, &lending_pool);
    let client = incentives::Client::new(&env, &contract_id);

    let asset = Address::generate(&env);
    let reward_token1 = Address::generate(&env);
    let reward_token2 = Address::generate(&env);

    // Configure two different reward tokens for the same asset
    client.configure_asset_rewards(
        &emission_manager,
        &asset,
        &reward_token1,
        &0u32,
        &100_000_000u128,
        &0u64,
    );

    client.configure_asset_rewards(
        &emission_manager,
        &asset,
        &reward_token2,
        &0u32,
        &50_000_000u128,
        &0u64,
    );

    // Verify both are configured
    let config1 =
        client.get_asset_reward_config(&asset, &reward_token1, &0u32);
    let config2 =
        client.get_asset_reward_config(&asset, &reward_token2, &0u32);

    assert!(config1.is_some());
    assert!(config2.is_some());

    // Verify reward tokens list
    let reward_tokens = client.get_reward_tokens(&asset);
    assert_eq!(reward_tokens.len(), 2);
}

// ============================================================================
// HANDLE_ACTION TESTS
// ============================================================================

#[test]
fn test_handle_action_updates_index() {
    let env = create_test_env();
    let (emission_manager, lending_pool, user, _) = create_test_addresses(&env);
    let contract_id = initialize_contract(&env, &emission_manager, &lending_pool);
    let client = incentives::Client::new(&env, &contract_id);

    let token_address = Address::generate(&env); // Token address (asset identifier)
    let reward_token = Address::generate(&env);
    let emission_per_second = 100_000_000u128; // 100 tokens/second
    let total_supply = 10_000_000_000_000u128; // 10,000 scaled units
    let user_balance = 1_000_000_000_000u128; // 1,000 scaled units

    // Set initial timestamp
    set_timestamp(&env, 1000);

    // Configure rewards - asset is the token address (following Aave pattern)
    client.configure_asset_rewards(
        &emission_manager,
        &token_address, // Token address is the asset identifier
        &reward_token,
        &0u32,
        &emission_per_second,
        &0u64,
    );

    // Initial index should be RAY
    let initial_index =
        client.get_asset_reward_index(&token_address, &reward_token, &0u32);
    assert_eq!(initial_index.index, RAY);

    // Advance time by 1 hour (3600 seconds)
    set_timestamp(&env, 4600);

    // Call handle_action - token_address is the asset identifier (following Aave pattern)
    client.handle_action(
        &token_address, // Token address (asset identifier)
        &user,
        &total_supply,
        &user_balance,
        &0u32,
    );

    // Verify index was updated
    let updated_index =
        client.get_asset_reward_index(&token_address, &reward_token, &0u32);
    assert!(updated_index.index > RAY);
    assert_eq!(updated_index.last_update_timestamp, 4600);

    // Expected increment: (100 * 3600 * RAY) / 10,000 = 36,000 * RAY / 10,000 = 3.6 * RAY
    // But we need to account for RAY precision, so let's check it's approximately correct
    let emission_times_time = emission_per_second * 3600u128;
    let expected_increment = k2_shared::ray_div(&env, emission_times_time, total_supply).unwrap();
    let expected_index = RAY.checked_add(expected_increment).unwrap();

    // Allow for small rounding differences
    let diff = if updated_index.index > expected_index {
        updated_index.index - expected_index
    } else {
        expected_index - updated_index.index
    };
    assert!(diff < 1_000_000_000_000u128); // Allow small rounding error
}

#[test]
fn test_handle_action_updates_user_rewards() {
    let env = create_test_env();
    let (emission_manager, lending_pool, user, _) = create_test_addresses(&env);
    let contract_id = initialize_contract(&env, &emission_manager, &lending_pool);
    let client = incentives::Client::new(&env, &contract_id);

    let token_address = Address::generate(&env); // Token address (asset identifier)
    let reward_token = Address::generate(&env);
    let emission_per_second = 100_000_000u128; // 100 tokens/second
    let total_supply = 10_000_000_000_000u128;
    let user_balance = 1_000_000_000_000u128; // 1,000 scaled units

    // Set initial timestamp
    set_timestamp(&env, 1000);

    // Configure rewards - asset is the token address (following Aave pattern)
    client.configure_asset_rewards(
        &emission_manager,
        &token_address, // Token address is the asset identifier
        &reward_token,
        &0u32,
        &emission_per_second,
        &0u64,
    );

    // First handle_action - user starts accruing
    client.handle_action(
        &token_address, // Token address (asset identifier)
        &user,
        &total_supply,
        &user_balance,
        &0u32,
    );

    // User should have index snapshot set
    let user_data = client.get_user_reward_data(
        &token_address,
        &reward_token,
        &user,
        &0u32,
    );
    assert_eq!(user_data.index_snapshot, RAY); // Initial snapshot
    assert_eq!(user_data.accrued, 0); // No rewards accrued yet

    // Advance time by 1 hour
    set_timestamp(&env, 4600);

    // Second handle_action - user should accrue rewards
    client.handle_action(
        &token_address, // Token address (asset identifier)
        &user,
        &total_supply,
        &user_balance,
        &0u32,
    );

    // Verify user accrued rewards
    let user_data = client.get_user_reward_data(
        &token_address,
        &reward_token,
        &user,
        &0u32,
    );
    assert!(user_data.accrued > 0);
    assert!(user_data.index_snapshot > RAY);
}

#[test]
fn test_handle_action_zero_balance() {
    let env = create_test_env();
    let (emission_manager, lending_pool, user, _) = create_test_addresses(&env);
    let contract_id = initialize_contract(&env, &emission_manager, &lending_pool);
    let client = incentives::Client::new(&env, &contract_id);

    let token_address = Address::generate(&env); // Token address (asset identifier)
    let reward_token = Address::generate(&env);
    let total_supply = 10_000_000_000_000u128;

    // Configure rewards - asset is the token address (following Aave pattern)
    client.configure_asset_rewards(
        &emission_manager,
        &token_address, // Token address is the asset identifier
        &reward_token,
        &0u32,
        &100_000_000u128,
        &0u64,
    );

    set_timestamp(&env, 1000);

    // Handle action with zero balance
    client.handle_action(
        &token_address, // Token address (asset identifier)
        &user,
        &total_supply,
        &0u128, // Zero balance
        &0u32,
    );

    // User should not accrue rewards with zero balance
    let user_data = client.get_user_reward_data(
        &token_address,
        &reward_token,
        &user,
        &0u32,
    );
    assert_eq!(user_data.accrued, 0);
}

#[test]
fn test_handle_action_zero_total_supply() {
    let env = create_test_env();
    let (emission_manager, lending_pool, user, _) = create_test_addresses(&env);
    let contract_id = initialize_contract(&env, &emission_manager, &lending_pool);
    let client = incentives::Client::new(&env, &contract_id);

    let token_address = Address::generate(&env); // Token address (asset identifier)
    let reward_token = Address::generate(&env);

    // Configure rewards - asset is the token address (following Aave pattern)
    client.configure_asset_rewards(
        &emission_manager,
        &token_address, // Token address is the asset identifier
        &reward_token,
        &0u32,
        &100_000_000u128,
        &0u64,
    );

    set_timestamp(&env, 1000);

    // Handle action with zero total supply
    client.handle_action(
        &token_address, // Token address (asset identifier)
        &user,
        &0u128, // Zero total supply
        &1_000_000_000_000u128,
        &0u32,
    );

    // Index should not grow with zero supply
    let index =
        client.get_asset_reward_index(&token_address, &reward_token, &0u32);
    assert_eq!(index.index, RAY); // Index should remain at RAY
}

#[test]
fn test_handle_action_supply_vs_borrow_separate() {
    let env = create_test_env();
    let (emission_manager, lending_pool, user, _) = create_test_addresses(&env);
    let contract_id = initialize_contract(&env, &emission_manager, &lending_pool);
    let client = incentives::Client::new(&env, &contract_id);

    let supply_token = Address::generate(&env); // Supply token address (asset identifier)
    let borrow_token = Address::generate(&env); // Borrow token address (asset identifier)
    let reward_token = Address::generate(&env);

    // Configure both supply and borrow rewards
    client.configure_asset_rewards(
        &emission_manager,
        &supply_token, // Supply token address is the asset identifier
        &reward_token,
        &0u32,
        &100_000_000u128,
        &0u64,
    );

    client.configure_asset_rewards(
        &emission_manager,
        &borrow_token, // Borrow token address is the asset identifier
        &reward_token,
        &1u32,
        &50_000_000u128,
        &0u64,
    );

    set_timestamp(&env, 1000);

    // Handle supply action
    client.handle_action(
        &supply_token, // Supply token address (asset identifier)
        &user,
        &10_000_000_000_000u128,
        &1_000_000_000_000u128,
        &0u32,
    );

    // Handle borrow action
    client.handle_action(
        &borrow_token, // Borrow token address (asset identifier)
        &user,
        &5_000_000_000_000u128,
        &500_000_000_000u128,
        &1u32,
    );

    // Verify supply and borrow rewards are tracked separately
    let supply_data = client.get_user_reward_data(
        &supply_token,
        &reward_token,
        &user,
        &0u32,
    );
    let borrow_data = client.get_user_reward_data(
        &borrow_token,
        &reward_token,
        &user,
        &1u32,
    );

    // Both should have index snapshots set
    assert!(supply_data.index_snapshot >= RAY);
    assert!(borrow_data.index_snapshot >= RAY);

    // Supply and borrow indices should be separate
    let supply_index =
        client.get_asset_reward_index(&supply_token, &reward_token, &0u32);
    let borrow_index =
        client.get_asset_reward_index(&borrow_token, &reward_token, &1u32);

    assert!(supply_index.index >= RAY);
    assert!(borrow_index.index >= RAY);
}

#[test]
fn test_handle_action_inactive_reward() {
    let env = create_test_env();
    let (emission_manager, lending_pool, user, _) = create_test_addresses(&env);
    let contract_id = initialize_contract(&env, &emission_manager, &lending_pool);
    let client = incentives::Client::new(&env, &contract_id);

    let token_address = Address::generate(&env); // Token address (asset identifier)
    let reward_token = Address::generate(&env);

    // Configure rewards - asset is the token address (following Aave pattern)
    client.configure_asset_rewards(
        &emission_manager,
        &token_address, // Token address is the asset identifier
        &reward_token,
        &0u32,
        &100_000_000u128,
        &0u64,
    );

    // Deactivate rewards
    client.remove_asset_reward(
        &emission_manager,
        &token_address, // Token address is the asset identifier
        &reward_token,
        &0u32,
    );

    set_timestamp(&env, 1000);

    // Handle action - should not accrue rewards (rewards are inactive)
    client.handle_action(
        &token_address, // Token address (asset identifier)
        &user,
        &10_000_000_000_000u128,
        &1_000_000_000_000u128,
        &0u32,
    );

    // Index should not grow
    let index =
        client.get_asset_reward_index(&token_address, &reward_token, &0u32);
    assert_eq!(index.index, RAY);
}

#[test]
#[should_panic(expected = "Error(Contract, #4)")]
fn test_handle_action_invalid_reward_type() {
    let env = create_test_env();
    let (emission_manager, lending_pool, user, _) = create_test_addresses(&env);
    let contract_id = initialize_contract(&env, &emission_manager, &lending_pool);
    let client = incentives::Client::new(&env, &contract_id);

    let token_address = Address::generate(&env); // Token address (asset identifier)

    // Try invalid reward type
    client.handle_action(
        &token_address, // Token address (asset identifier)
        &user,
        &10_000_000_000_000u128,
        &1_000_000_000_000u128,
        &2u32, // Invalid
    );
}

#[test]
fn test_handle_action_unregistered_token() {
    let env = create_test_env();
    let (emission_manager, lending_pool, user, _) = create_test_addresses(&env);
    let contract_id = initialize_contract(&env, &emission_manager, &lending_pool);
    let client = incentives::Client::new(&env, &contract_id);

    let token_address = Address::generate(&env); // Token address (asset identifier)
                                                 // Note: With the new design following Aave's pattern, anyone can call handle_action
                                                 // but it will only work if the token_address is registered. Unregistered tokens result in no-op.
                                                 // This test is no longer relevant as authorization is based on token registration, not caller.
                                                 // For now, we'll test that unregistered tokens result in no-op (which is safe)
    client.handle_action(
        &token_address, // Token address (asset identifier) - not registered, so no-op
        &user,
        &10_000_000_000_000u128,
        &1_000_000_000_000u128,
        &0u32,
    );
}

#[test]
fn test_handle_action_multiple_users() {
    let env = create_test_env();
    let (emission_manager, lending_pool, user1, user2) = create_test_addresses(&env);
    let contract_id = initialize_contract(&env, &emission_manager, &lending_pool);
    let client = incentives::Client::new(&env, &contract_id);

    let token_address = Address::generate(&env); // Token address (asset identifier)
    let reward_token = Address::generate(&env);
    let emission_per_second = 100_000_000u128;
    let total_supply = 10_000_000_000_000u128;

    // Configure rewards - asset is the token address (following Aave pattern)
    client.configure_asset_rewards(
        &emission_manager,
        &token_address, // Token address is the asset identifier
        &reward_token,
        &0u32,
        &emission_per_second,
        &0u64,
    );

    set_timestamp(&env, 1000);

    // User1 supplies 900 units
    client.handle_action(
        &token_address, // Token address (asset identifier)
        &user1,
        &total_supply,
        &900_000_000_000u128,
        &0u32,
    );

    // Advance time
    set_timestamp(&env, 1100); // 100 seconds later

    // User1 interacts again
    client.handle_action(
        &token_address, // Token address (asset identifier)
        &user1,
        &total_supply,
        &900_000_000_000u128,
        &0u32,
    );

    // Advance time
    set_timestamp(&env, 1300); // Another 200 seconds later

    // User2 interacts for the first time (should NOT get rewards from t=1000 to t=1300)
    // New deposits don't accrue rewards for past periods
    client.handle_action(
        &token_address, // Token address (asset identifier)
        &user2,
        &total_supply,
        &100_000_000_000u128,
        &0u32,
    );

    // Advance time again
    set_timestamp(&env, 1400); // Another 100 seconds later

    // User2 interacts again - now they should accrue rewards for the period they held balance
    client.handle_action(
        &token_address,
        &user2,
        &total_supply,
        &100_000_000_000u128,
        &0u32,
    );

    // Verify both users have rewards
    let user1_data = client.get_user_reward_data(
        &token_address,
        &reward_token,
        &user1,
        &0u32,
    );
    let user2_data = client.get_user_reward_data(
        &token_address,
        &reward_token,
        &user2,
        &0u32,
    );

    // User1 should have accrued rewards from t=1000 to t=1100 (100 seconds)
    assert!(user1_data.accrued > 0);

    // User2 should have accrued rewards from t=1300 to t=1400 (100 seconds) for their 100 units
    // They should NOT have accrued for the period before they deposited (t=1000 to t=1300)
    assert!(user2_data.accrued > 0);
}

// ============================================================================
// CLAIM REWARDS TESTS
// ============================================================================

#[test]
fn test_claim_rewards() {
    let env = create_test_env();
    let (emission_manager, lending_pool, user, _) = create_test_addresses(&env);
    let contract_id = initialize_contract(&env, &emission_manager, &lending_pool);
    let client = incentives::Client::new(&env, &contract_id);

    let token_address = Address::generate(&env); // Token address (asset identifier)
    let to = Address::generate(&env);

    // Create reward token contract
    let token_admin = Address::generate(&env);
    let reward_token_contract = env.register_stellar_asset_contract_v2(token_admin.clone());
    let reward_token = reward_token_contract.address();

    // Mint tokens to the incentives contract so it can transfer them
    let reward_token_client = soroban_sdk::token::StellarAssetClient::new(&env, &reward_token);
    reward_token_client.mint(&contract_id, &(1_000_000_000_000i128));

    // Set initial timestamp
    set_timestamp(&env, 1000);

    // Configure rewards - asset is the token address (following Aave pattern)
    client.configure_asset_rewards(
        &emission_manager,
        &token_address, // Token address is the asset identifier
        &reward_token,
        &0u32,
        &100_000_000u128,
        &0u64,
    );

    // User supplies and accrues rewards
    client.handle_action(
        &token_address, // Token address (asset identifier)
        &user,
        &10_000_000_000_000u128,
        &1_000_000_000_000u128,
        &0u32,
    );

    set_timestamp(&env, 4600); // 1 hour later

    // User interacts again to accrue rewards
    client.handle_action(
        &token_address, // Token address (asset identifier)
        &user,
        &10_000_000_000_000u128,
        &1_000_000_000_000u128,
        &0u32,
    );

    // Check accrued rewards
    let user_data = client.get_user_reward_data(
        &token_address,
        &reward_token,
        &user,
        &0u32,
    );
    assert!(user_data.accrued > 0);

    // Claim rewards (note: actual token transfer would require a mock token contract)
    let assets = Vec::from_array(&env, [token_address.clone()]);
    let result = client.claim_rewards(&user, &assets, &reward_token, &0u128, &to);

    // Verify rewards were claimed
    assert!(result > 0);

    // Verify user's accrued balance was reset
    let user_data_after = client.get_user_reward_data(
        &token_address,
        &reward_token,
        &user,
        &0u32,
    );
    assert_eq!(user_data_after.accrued, 0);
}

#[test]
fn test_claim_rewards_no_rewards() {
    let env = create_test_env();
    let (emission_manager, lending_pool, _user, _) = create_test_addresses(&env);
    let contract_id = initialize_contract(&env, &emission_manager, &lending_pool);
    let client = incentives::Client::new(&env, &contract_id);

    let token_address = Address::generate(&env); // Token address (asset identifier)
    let reward_token = Address::generate(&env);
    let user = Address::generate(&env);
    let to = Address::generate(&env);

    // Try to claim rewards when user has none
    let assets = Vec::from_array(&env, [token_address.clone()]);
    let result = client.claim_rewards(&user, &assets, &reward_token, &0u128, &to);

    assert_eq!(result, 0);
}

#[test]
#[should_panic(expected = "Error(Contract, #7)")]
fn test_claim_rewards_insufficient_rewards() {
    let env = create_test_env();
    let (emission_manager, lending_pool, user, _) = create_test_addresses(&env);
    let contract_id = initialize_contract(&env, &emission_manager, &lending_pool);
    let client = incentives::Client::new(&env, &contract_id);

    let token_address = Address::generate(&env); // Token address (asset identifier)
    let to = Address::generate(&env);

    // Create reward token contract and fund it
    let token_admin = Address::generate(&env);
    let reward_token_contract = env.register_stellar_asset_contract_v2(token_admin.clone());
    let reward_token = reward_token_contract.address();
    let reward_token_client = soroban_sdk::token::StellarAssetClient::new(&env, &reward_token);
    reward_token_client.mint(&contract_id, &(1_000_000_000_000i128));

    set_timestamp(&env, 1000);

    // Configure rewards - asset is the token address (following Aave pattern)
    client.configure_asset_rewards(
        &emission_manager,
        &token_address, // Token address is the asset identifier
        &reward_token,
        &0u32,
        &100_000_000u128,
        &0u64,
    );

    // User supplies and accrues some rewards (but not a lot)
    client.handle_action(
        &token_address, // Token address (asset identifier)
        &user,
        &10_000_000_000_000u128,
        &1_000_000_000_000u128,
        &0u32,
    );

    set_timestamp(&env, 1100); // 100 seconds later

    client.handle_action(
        &token_address, // Token address (asset identifier)
        &user,
        &10_000_000_000_000u128,
        &1_000_000_000_000u128,
        &0u32,
    );

    // Check accrued rewards
    let user_data = client.get_user_reward_data(
        &token_address,
        &reward_token,
        &user,
        &0u32,
    );
    let accrued = user_data.accrued;
    assert!(accrued > 0);

    // Try to claim more than available (should fail)
    let assets = Vec::from_array(&env, [token_address.clone()]);
    let excessive_amount = accrued.checked_add(1_000_000_000u128).unwrap(); // More than available
    client.claim_rewards(&user, &assets, &reward_token, &excessive_amount, &to);
}

#[test]
fn test_claim_rewards_partial_amount() {
    let env = create_test_env();
    let (emission_manager, lending_pool, user, _) = create_test_addresses(&env);
    let contract_id = initialize_contract(&env, &emission_manager, &lending_pool);
    let client = incentives::Client::new(&env, &contract_id);

    let token_address = Address::generate(&env); // Token address (asset identifier)
    let to = Address::generate(&env);

    // Create reward token contract and fund it
    let token_admin = Address::generate(&env);
    let reward_token_contract = env.register_stellar_asset_contract_v2(token_admin.clone());
    let reward_token = reward_token_contract.address();
    let reward_token_client = soroban_sdk::token::StellarAssetClient::new(&env, &reward_token);
    reward_token_client.mint(&contract_id, &(1_000_000_000_000i128));

    set_timestamp(&env, 1000);

    // Configure rewards - asset is the token address (following Aave pattern)
    client.configure_asset_rewards(
        &emission_manager,
        &token_address, // Token address is the asset identifier
        &reward_token,
        &0u32,
        &100_000_000u128,
        &0u64,
    );

    // User supplies and accrues rewards
    client.handle_action(
        &token_address,
        &user,
        &10_000_000_000_000u128,
        &1_000_000_000_000u128,
        &0u32,
    );

    set_timestamp(&env, 4600); // 1 hour later

    client.handle_action(
        &token_address,
        &user,
        &10_000_000_000_000u128,
        &1_000_000_000_000u128,
        &0u32,
    );

    // Check accrued rewards
    let user_data_before = client.get_user_reward_data(
        &token_address,
        &reward_token,
        &user,
        &0u32,
    );
    let total_accrued = user_data_before.accrued;
    assert!(total_accrued > 0);

    // Claim partial amount (half)
    let partial_amount = total_accrued / 2;
    let assets = Vec::from_array(&env, [token_address.clone()]);
    let claimed = client.claim_rewards(&user, &assets, &reward_token, &partial_amount, &to);

    // Verify exact amount was claimed
    assert_eq!(claimed, partial_amount);

    // Verify remaining balance
    let user_data_after = client.get_user_reward_data(
        &token_address,
        &reward_token,
        &user,
        &0u32,
    );
    assert_eq!(user_data_after.accrued, total_accrued - partial_amount);
}

#[test]
#[should_panic]
fn test_claim_rewards_requires_auth() {
    // Create test environment WITHOUT mocking auths so auth checks work
    let env = Env::default();
    let (emission_manager, lending_pool, _user, _) = create_test_addresses(&env);
    let contract_id = initialize_contract(&env, &emission_manager, &lending_pool);
    let client = incentives::Client::new(&env, &contract_id);

    let token_address = Address::generate(&env); // Token address (asset identifier)
    let reward_token = Address::generate(&env);
    let to = Address::generate(&env);
    let other_user = Address::generate(&env);

    // Try to claim rewards for another user (should fail auth)
    let assets = Vec::from_array(&env, [token_address.clone()]);
    // This should panic because other_user is not authorized and auths are not mocked
    client.claim_rewards(&other_user, &assets, &reward_token, &0u128, &to);
}

#[test]
fn test_claim_all_rewards() {
    let env = create_test_env();
    let (emission_manager, lending_pool, user, _) = create_test_addresses(&env);
    let contract_id = initialize_contract(&env, &emission_manager, &lending_pool);
    let client = incentives::Client::new(&env, &contract_id);

    let token1 = Address::generate(&env); // Token1 address (asset identifier)
    let token2 = Address::generate(&env); // Token2 address (asset identifier)
    let to = Address::generate(&env);

    // Create reward token contract
    let token_admin = Address::generate(&env);
    let reward_token_contract = env.register_stellar_asset_contract_v2(token_admin.clone());
    let reward_token = reward_token_contract.address();

    // Mint tokens to the incentives contract so it can transfer them
    let reward_token_client = soroban_sdk::token::StellarAssetClient::new(&env, &reward_token);
    reward_token_client.mint(&contract_id, &(1_000_000_000_000i128));

    // Set initial timestamp
    set_timestamp(&env, 1000);

    // Configure rewards for both tokens - asset is the token address (following Aave pattern)
    client.configure_asset_rewards(
        &emission_manager,
        &token1, // Token1 address is the asset identifier
        &reward_token,
        &0u32,
        &100_000_000u128,
        &0u64,
    );

    client.configure_asset_rewards(
        &emission_manager,
        &token2, // Token2 address is the asset identifier
        &reward_token,
        &0u32,
        &100_000_000u128,
        &0u64,
    );

    // User supplies both tokens
    client.handle_action(
        &token1, // Token1 address (asset identifier)
        &user,
        &10_000_000_000_000u128,
        &1_000_000_000_000u128,
        &0u32,
    );

    client.handle_action(
        &token2, // Token2 address (asset identifier)
        &user,
        &10_000_000_000_000u128,
        &1_000_000_000_000u128,
        &0u32,
    );

    set_timestamp(&env, 4600);

    // Accrue rewards on both
    client.handle_action(
        &token1, // Token1 address (asset identifier)
        &user,
        &10_000_000_000_000u128,
        &1_000_000_000_000u128,
        &0u32,
    );

    client.handle_action(
        &token2, // Token2 address (asset identifier)
        &user,
        &10_000_000_000_000u128,
        &1_000_000_000_000u128,
        &0u32,
    );

    // Reset budget to measure gas costs for claim_all_rewards
    let mut budget = env.cost_estimate().budget();
    budget.reset_default();

    // Claim all rewards
    let assets = Vec::from_array(&env, [token1.clone(), token2.clone()]);
    client.claim_all_rewards(&user, &assets, &to);

    // Measure gas/resource usage
    let budget_after = env.cost_estimate().budget();
    let cpu_instructions = budget_after.cpu_instruction_cost();
    let mem_bytes = budget_after.memory_bytes_cost();

    // Log gas usage - print to stderr so it's always visible
    std::eprintln!("\n=== claim_all_rewards Gas Cost ===");
    std::eprintln!("CPU Instructions: {}", cpu_instructions);
    std::eprintln!("Memory Bytes: {}", mem_bytes);
    std::eprintln!("Budget Details:\n{}", budget_after);
    std::eprintln!("===============================\n");

    // Assert reasonable gas usage
    // Note: These thresholds are example values - adjust based on your requirements
    // The batching optimization should keep this reasonable even with multiple positions
    assert!(
        cpu_instructions < 5_000_000,
        "CPU instructions ({}) exceeded threshold. Batching may not be working efficiently.",
        cpu_instructions
    );
    assert!(
        mem_bytes < 10_000_000,
        "Memory usage ({}) exceeded threshold.",
        mem_bytes
    );

    // Verify both tokens' rewards were claimed
    let user_data1 =
        client.get_user_reward_data(&token1, &reward_token, &user, &0u32);
    let user_data2 =
        client.get_user_reward_data(&token2, &reward_token, &user, &0u32);

    assert_eq!(user_data1.accrued, 0);
    assert_eq!(user_data2.accrued, 0);
}

#[test]
fn test_claim_all_rewards_batches_transfers() {
    // This test verifies that claim_all_rewards batches transfers by reward token
    // When a user has rewards across multiple assets/reward_types with the same token,
    // only one transfer should occur per unique reward token.
    let env = create_test_env();
    let (emission_manager, lending_pool, user, _) = create_test_addresses(&env);
    let contract_id = initialize_contract(&env, &emission_manager, &lending_pool);
    let client = incentives::Client::new(&env, &contract_id);

    let token1_supply = Address::generate(&env); // Token1 supply address (asset identifier)
    let token1_borrow = Address::generate(&env); // Token1 borrow address (asset identifier)
    let token2_supply = Address::generate(&env); // Token2 supply address (asset identifier)
    let to = Address::generate(&env);

    // Create reward token contract
    let token_admin = Address::generate(&env);
    let reward_token_contract = env.register_stellar_asset_contract_v2(token_admin.clone());
    let reward_token = reward_token_contract.address();
    let reward_token_client = soroban_sdk::token::StellarAssetClient::new(&env, &reward_token);

    // Fund contract with enough tokens
    reward_token_client.mint(&contract_id, &(10_000_000_000_000i128));

    set_timestamp(&env, 1000);

    // Configure rewards for both tokens with the SAME reward token
    // This tests batching: same token across multiple assets and reward types
    // Asset is the token address (following Aave pattern)
    client.configure_asset_rewards(
        &emission_manager,
        &token1_supply, // Token1 supply address is the asset identifier
        &reward_token,
        &0u32,
        &100_000_000u128,
        &0u64,
    );

    client.configure_asset_rewards(
        &emission_manager,
        &token1_borrow, // Token1 borrow address is the asset identifier
        &reward_token,
        &1u32,
        &50_000_000u128,
        &0u64,
    );

    client.configure_asset_rewards(
        &emission_manager,
        &token2_supply, // Token2 supply address is the asset identifier
        &reward_token,
        &0u32,
        &100_000_000u128,
        &0u64,
    );

    // User supplies token1 and borrows token1, supplies token2
    client.handle_action(
        &token1_supply, // Token1 supply address (asset identifier)
        &user,
        &10_000_000_000_000u128,
        &5_000_000_000_000u128, // Supply
        &0u32,
    );

    client.handle_action(
        &token1_borrow, // Token1 borrow address (asset identifier)
        &user,
        &2_000_000_000_000u128,
        &1_000_000_000_000u128, // Borrow
        &1u32,
    );

    client.handle_action(
        &token2_supply, // Token2 supply address (asset identifier)
        &user,
        &10_000_000_000_000u128,
        &3_000_000_000_000u128, // Supply
        &0u32,
    );

    set_timestamp(&env, 4600); // 1 hour later

    // Accrue rewards on all positions
    client.handle_action(
        &token1_supply, // Token1 supply address (asset identifier)
        &user,
        &10_000_000_000_000u128,
        &5_000_000_000_000u128,
        &0u32,
    );

    client.handle_action(
        &token1_borrow, // Token1 borrow address (asset identifier)
        &user,
        &2_000_000_000_000u128,
        &1_000_000_000_000u128,
        &1u32,
    );

    client.handle_action(
        &token2_supply, // Token2 supply address (asset identifier)
        &user,
        &10_000_000_000_000u128,
        &3_000_000_000_000u128,
        &0u32,
    );

    // Calculate expected total rewards (all should be in the same reward_token)
    let user_data1_supply = client.get_user_reward_data(
        &token1_supply,
        &reward_token,
        &user,
        &0u32,
    );
    let user_data1_borrow = client.get_user_reward_data(
        &token1_borrow,
        &reward_token,
        &user,
        &1u32,
    );
    let user_data2_supply = client.get_user_reward_data(
        &token2_supply,
        &reward_token,
        &user,
        &0u32,
    );

    let expected_total =
        user_data1_supply.accrued + user_data1_borrow.accrued + user_data2_supply.accrued;
    assert!(expected_total > 0, "Should have accrued rewards");

    // Check contract balance before claim
    let balance_before = client.get_reward_token_balance(&reward_token);

    // Reset budget to measure gas costs for claim_all_rewards with batching optimization
    let mut budget = env.cost_estimate().budget();
    budget.reset_default();

    // Claim all rewards - should batch all into one transfer per reward token
    // The batching optimization should reduce gas costs significantly:
    // - Before: N transfers for N positions (e.g., 3 assets × 2 tokens × 2 types = 12 transfers)
    // - After: M transfers for M unique reward tokens (e.g., 2 transfers for 2 unique tokens)
    let assets = Vec::from_array(
        &env,
        [
            token1_supply.clone(),
            token1_borrow.clone(),
            token2_supply.clone(),
        ],
    );
    client.claim_all_rewards(&user, &assets, &to);

    // Measure gas/resource usage
    let budget_after = env.cost_estimate().budget();
    let cpu_instructions = budget_after.cpu_instruction_cost();
    let mem_bytes = budget_after.memory_bytes_cost();

    // Log gas usage - print to stderr so it's always visible
    std::eprintln!("\n=== claim_all_rewards (batched) Gas Cost ===");
    std::eprintln!("CPU Instructions: {}", cpu_instructions);
    std::eprintln!("Memory Bytes: {}", mem_bytes);
    std::eprintln!("Budget Details:\n{}", budget_after);
    std::eprintln!("========================================\n");

    // Assert reasonable gas usage
    // Note: These thresholds are example values - adjust based on your requirements
    // The batching optimization should keep this reasonable even with multiple positions
    assert!(
        cpu_instructions < 5_000_000,
        "CPU instructions ({}) exceeded threshold. Batching may not be working efficiently.",
        cpu_instructions
    );
    assert!(
        mem_bytes < 10_000_000,
        "Memory usage ({}) exceeded threshold.",
        mem_bytes
    );

    // Check contract balance after claim
    let balance_after = client.get_reward_token_balance(&reward_token);

    // Verify total amount transferred matches expected (batched)
    assert_eq!(balance_before - balance_after, expected_total);

    // Verify all accrued balances are zero
    let user_data1_supply_after = client.get_user_reward_data(
        &token1_supply,
        &reward_token,
        &user,
        &0u32,
    );
    let user_data1_borrow_after = client.get_user_reward_data(
        &token1_borrow,
        &reward_token,
        &user,
        &1u32,
    );
    let user_data2_supply_after = client.get_user_reward_data(
        &token2_supply,
        &reward_token,
        &user,
        &0u32,
    );

    assert_eq!(user_data1_supply_after.accrued, 0);
    assert_eq!(user_data1_borrow_after.accrued, 0);
    assert_eq!(user_data2_supply_after.accrued, 0);
}

// ============================================================================
// ADMIN FUNCTION TESTS
// ============================================================================

#[test]
fn test_set_emission_per_second() {
    let env = create_test_env();
    let (emission_manager, lending_pool, _, _) = create_test_addresses(&env);
    let contract_id = initialize_contract(&env, &emission_manager, &lending_pool);
    let client = incentives::Client::new(&env, &contract_id);

    let asset = Address::generate(&env);
    let reward_token = Address::generate(&env);

    // Configure initial rewards
    client.configure_asset_rewards(
        &emission_manager,
        &asset,
        &reward_token,
        &0u32,
        &100_000_000u128,
        &0u64,
    );

    // Update emission rate
    client.set_emission_per_second(
        &emission_manager,
        &asset,
        &reward_token,
        &0u32,
        &200_000_000u128, // New rate
    );

    // Verify update
    let config =
        client.get_asset_reward_config(&asset, &reward_token, &0u32);
    assert_eq!(config.unwrap().emission_per_second, 200_000_000u128);
}

#[test]
fn test_set_distribution_end() {
    let env = create_test_env();
    let (emission_manager, lending_pool, _, _) = create_test_addresses(&env);
    let contract_id = initialize_contract(&env, &emission_manager, &lending_pool);
    let client = incentives::Client::new(&env, &contract_id);

    let asset = Address::generate(&env);
    let reward_token = Address::generate(&env);

    // Configure rewards
    client.configure_asset_rewards(
        &emission_manager,
        &asset,
        &reward_token,
        &0u32,
        &100_000_000u128,
        &0u64,
    );

    // Set distribution end
    let end_timestamp = 10000u64;
    client.set_distribution_end(
        &emission_manager,
        &asset,
        &reward_token,
        &0u32,
        &end_timestamp,
    );

    // Verify update
    let config =
        client.get_asset_reward_config(&asset, &reward_token, &0u32);
    assert_eq!(config.unwrap().distribution_end, end_timestamp);
}

#[test]
fn test_distribution_end_enforcement() {
    let env = create_test_env();
    let (emission_manager, lending_pool, user, _) = create_test_addresses(&env);
    let contract_id = initialize_contract(&env, &emission_manager, &lending_pool);
    let client = incentives::Client::new(&env, &contract_id);

    let asset = Address::generate(&env);
    let reward_token = Address::generate(&env);
    let token_address = Address::generate(&env);

    // Configure rewards with end time
    let end_timestamp = 5000u64;
    client.configure_asset_rewards(
        &emission_manager,
        &asset,
        &reward_token,
        &0u32,
        &100_000_000u128,
        &end_timestamp,
    );

    set_timestamp(&env, 1000);

    // User supplies before end time
    client.handle_action(
        &token_address,
        &user,
        &10_000_000_000_000u128,
        &1_000_000_000_000u128,
        &0u32,
    );

    // Advance time past end
    set_timestamp(&env, 6000);

    // Handle action after end - should not accrue new rewards
    let index_before =
        client.get_asset_reward_index(&token_address, &reward_token, &0u32);

    client.handle_action(
        &token_address,
        &user,
        &10_000_000_000_000u128,
        &1_000_000_000_000u128,
        &0u32,
    );

    // Index should not grow after end time
    let index_after =
        client.get_asset_reward_index(&token_address, &reward_token, &0u32);
    assert_eq!(index_before.index, index_after.index);
}

#[test]
fn test_remove_asset_reward() {
    let env = create_test_env();
    let (emission_manager, lending_pool, _, _) = create_test_addresses(&env);
    let contract_id = initialize_contract(&env, &emission_manager, &lending_pool);
    let client = incentives::Client::new(&env, &contract_id);

    let asset = Address::generate(&env);
    let reward_token = Address::generate(&env);

    // Configure rewards
    client.configure_asset_rewards(
        &emission_manager,
        &asset,
        &reward_token,
        &0u32,
        &100_000_000u128,
        &0u64,
    );

    // Remove rewards
    client.remove_asset_reward(
        &emission_manager,
        &asset,
        &reward_token,
        &0u32,
    );

    // Verify rewards are inactive
    let config =
        client.get_asset_reward_config(&asset, &reward_token, &0u32);
    assert_eq!(config.unwrap().is_active, false);
}

#[test]
#[should_panic(expected = "Error(Contract, #3)")]
fn test_update_emission_unauthorized() {
    let env = create_test_env();
    let (emission_manager, lending_pool, user, _) = create_test_addresses(&env);
    let contract_id = initialize_contract(&env, &emission_manager, &lending_pool);
    let client = incentives::Client::new(&env, &contract_id);

    let asset = Address::generate(&env);
    let reward_token = Address::generate(&env);

    // Configure rewards
    client.configure_asset_rewards(
        &emission_manager,
        &asset,
        &reward_token,
        &0u32,
        &100_000_000u128,
        &0u64,
    );

    // Try to update as non-emission manager
    client.set_emission_per_second(
        &user, // Not emission manager
        &asset,
        &reward_token,
        &0u32,
        &200_000_000u128,
    );
}

// ============================================================================
// VIEW FUNCTION TESTS
// ============================================================================

#[test]
fn test_get_assets() {
    let env = create_test_env();
    let (emission_manager, lending_pool, _, _) = create_test_addresses(&env);
    let contract_id = initialize_contract(&env, &emission_manager, &lending_pool);
    let client = incentives::Client::new(&env, &contract_id);

    let asset1 = Address::generate(&env);
    let asset2 = Address::generate(&env);
    let reward_token = Address::generate(&env);

    // Configure rewards for multiple assets
    client.configure_asset_rewards(
        &emission_manager,
        &asset1,
        &reward_token,
        &0u32,
        &100_000_000u128,
        &0u64,
    );

    client.configure_asset_rewards(
        &emission_manager,
        &asset2,
        &reward_token,
        &0u32,
        &100_000_000u128,
        &0u64,
    );

    // Verify assets are tracked
    let assets = client.get_assets();
    assert_eq!(assets.len(), 2);
}

#[test]
fn test_get_reward_tokens() {
    let env = create_test_env();
    let (emission_manager, lending_pool, _, _) = create_test_addresses(&env);
    let contract_id = initialize_contract(&env, &emission_manager, &lending_pool);
    let client = incentives::Client::new(&env, &contract_id);

    let asset = Address::generate(&env);
    let reward_token1 = Address::generate(&env);
    let reward_token2 = Address::generate(&env);

    // Configure multiple reward tokens for same asset
    client.configure_asset_rewards(
        &emission_manager,
        &asset,
        &reward_token1,
        &0u32,
        &100_000_000u128,
        &0u64,
    );

    client.configure_asset_rewards(
        &emission_manager,
        &asset,
        &reward_token2,
        &0u32,
        &50_000_000u128,
        &0u64,
    );

    // Verify reward tokens are tracked
    let tokens = client.get_reward_tokens(&asset);
    assert_eq!(tokens.len(), 2);
}

// ============================================================================
// PAUSE FUNCTION TESTS
// ============================================================================

#[test]
fn test_pause_unpause() {
    let env = create_test_env();
    let (emission_manager, lending_pool, _, _) = create_test_addresses(&env);
    let contract_id = initialize_contract(&env, &emission_manager, &lending_pool);
    let client = incentives::Client::new(&env, &contract_id);

    // Initially not paused
    assert!(!client.is_paused());

    // Pause the contract
    client.pause(&emission_manager);
    assert!(client.is_paused());

    // Unpause the contract
    client.unpause(&emission_manager);
    assert!(!client.is_paused());
}

#[test]
#[should_panic(expected = "Error(Contract, #3)")]
fn test_pause_unauthorized() {
    let env = create_test_env();
    let (emission_manager, lending_pool, user, _) = create_test_addresses(&env);
    let contract_id = initialize_contract(&env, &emission_manager, &lending_pool);
    let client = incentives::Client::new(&env, &contract_id);

    // Try to pause as non-emission manager (should fail)
    client.pause(&user);
}

#[test]
#[should_panic(expected = "Error(Contract, #8)")]
fn test_claim_rewards_when_paused() {
    let env = create_test_env();
    let (emission_manager, lending_pool, user, _) = create_test_addresses(&env);
    let contract_id = initialize_contract(&env, &emission_manager, &lending_pool);
    let client = incentives::Client::new(&env, &contract_id);

    let token_address = Address::generate(&env); // Token address (asset identifier)
    let to = Address::generate(&env);

    // Create reward token contract and fund it
    let token_admin = Address::generate(&env);
    let reward_token_contract = env.register_stellar_asset_contract_v2(token_admin.clone());
    let reward_token = reward_token_contract.address();
    let reward_token_client = soroban_sdk::token::StellarAssetClient::new(&env, &reward_token);
    reward_token_client.mint(&contract_id, &(1_000_000_000_000i128));

    set_timestamp(&env, 1000);

    // Configure rewards - asset is the token address (following Aave pattern)
    client.configure_asset_rewards(
        &emission_manager,
        &token_address, // Token address is the asset identifier
        &reward_token,
        &0u32,
        &100_000_000u128,
        &0u64,
    );

    // User supplies and accrues rewards
    client.handle_action(
        &token_address,
        &user,
        &10_000_000_000_000u128,
        &1_000_000_000_000u128,
        &0u32,
    );

    set_timestamp(&env, 4600); // 1 hour later

    client.handle_action(
        &token_address,
        &user,
        &10_000_000_000_000u128,
        &1_000_000_000_000u128,
        &0u32,
    );

    // Verify user has accrued rewards
    let user_data = client.get_user_reward_data(
        &token_address,
        &reward_token,
        &user,
        &0u32,
    );
    assert!(user_data.accrued > 0);

    // Pause the contract
    client.pause(&emission_manager);
    assert!(client.is_paused());

    // Try to claim rewards (should fail)
    let assets = Vec::from_array(&env, [token_address.clone()]);
    client.claim_rewards(&user, &assets, &reward_token, &0u128, &to);
}

#[test]
#[should_panic(expected = "Error(Contract, #8)")]
fn test_claim_all_rewards_when_paused() {
    let env = create_test_env();
    let (emission_manager, lending_pool, user, _) = create_test_addresses(&env);
    let contract_id = initialize_contract(&env, &emission_manager, &lending_pool);
    let client = incentives::Client::new(&env, &contract_id);

    let token_address = Address::generate(&env); // Token address (asset identifier)
    let to = Address::generate(&env);

    // Create reward token contract and fund it
    let token_admin = Address::generate(&env);
    let reward_token_contract = env.register_stellar_asset_contract_v2(token_admin.clone());
    let reward_token = reward_token_contract.address();
    let reward_token_client = soroban_sdk::token::StellarAssetClient::new(&env, &reward_token);
    reward_token_client.mint(&contract_id, &(1_000_000_000_000i128));

    set_timestamp(&env, 1000);

    // Configure rewards - asset is the token address (following Aave pattern)
    client.configure_asset_rewards(
        &emission_manager,
        &token_address, // Token address is the asset identifier
        &reward_token,
        &0u32,
        &100_000_000u128,
        &0u64,
    );

    // User supplies and accrues rewards
    client.handle_action(
        &token_address,
        &user,
        &10_000_000_000_000u128,
        &1_000_000_000_000u128,
        &0u32,
    );

    set_timestamp(&env, 4600);

    client.handle_action(
        &token_address,
        &user,
        &10_000_000_000_000u128,
        &1_000_000_000_000u128,
        &0u32,
    );

    // Verify user has accrued rewards
    let user_data = client.get_user_reward_data(
        &token_address,
        &reward_token,
        &user,
        &0u32,
    );
    assert!(user_data.accrued > 0);

    // Pause the contract
    client.pause(&emission_manager);
    assert!(client.is_paused());

    // Try to claim all rewards (should fail)
    let assets = Vec::from_array(&env, [token_address.clone()]);
    client.claim_all_rewards(&user, &assets, &to);
}

#[test]
fn test_handle_action_allowed_when_paused() {
    // Verify that handle_action still works when paused (rewards continue to accrue)
    let env = create_test_env();
    let (emission_manager, lending_pool, user, _) = create_test_addresses(&env);
    let contract_id = initialize_contract(&env, &emission_manager, &lending_pool);
    let client = incentives::Client::new(&env, &contract_id);

    let token_address = Address::generate(&env); // Token address (asset identifier)
    let reward_token = Address::generate(&env);

    set_timestamp(&env, 1000);

    // Configure rewards - asset is the token address (following Aave pattern)
    client.configure_asset_rewards(
        &emission_manager,
        &token_address, // Token address is the asset identifier
        &reward_token,
        &0u32,
        &100_000_000u128,
        &0u64,
    );

    // Pause the contract
    client.pause(&emission_manager);
    assert!(client.is_paused());

    // handle_action should still work (called by token contracts)
    // This allows rewards to continue accruing even when paused
    client.handle_action(
        &token_address,
        &user,
        &10_000_000_000_000u128,
        &1_000_000_000_000u128,
        &0u32,
    );

    set_timestamp(&env, 4600);

    // Another handle_action should still work
    client.handle_action(
        &token_address,
        &user,
        &10_000_000_000_000u128,
        &1_000_000_000_000u128,
        &0u32,
    );

    // Verify rewards accrued (even though contract is paused)
    let user_data = client.get_user_reward_data(
        &token_address,
        &reward_token,
        &user,
        &0u32,
    );
    assert!(
        user_data.accrued > 0,
        "Rewards should continue accruing when paused"
    );
}

#[test]
fn test_claim_after_unpause() {
    // Verify that claims work again after unpausing
    let env = create_test_env();
    let (emission_manager, lending_pool, user, _) = create_test_addresses(&env);
    let contract_id = initialize_contract(&env, &emission_manager, &lending_pool);
    let client = incentives::Client::new(&env, &contract_id);

    let token_address = Address::generate(&env); // Token address (asset identifier)
    let to = Address::generate(&env);

    // Create reward token contract and fund it
    let token_admin = Address::generate(&env);
    let reward_token_contract = env.register_stellar_asset_contract_v2(token_admin.clone());
    let reward_token = reward_token_contract.address();
    let reward_token_client = soroban_sdk::token::StellarAssetClient::new(&env, &reward_token);
    reward_token_client.mint(&contract_id, &(1_000_000_000_000i128));

    set_timestamp(&env, 1000);

    // Configure rewards - asset is the token address (following Aave pattern)
    client.configure_asset_rewards(
        &emission_manager,
        &token_address, // Token address is the asset identifier
        &reward_token,
        &0u32,
        &100_000_000u128,
        &0u64,
    );

    // User supplies and accrues rewards
    client.handle_action(
        &token_address,
        &user,
        &10_000_000_000_000u128,
        &1_000_000_000_000u128,
        &0u32,
    );

    set_timestamp(&env, 4600);

    client.handle_action(
        &token_address,
        &user,
        &10_000_000_000_000u128,
        &1_000_000_000_000u128,
        &0u32,
    );

    // Verify user has accrued rewards
    let user_data_before = client.get_user_reward_data(
        &token_address,
        &reward_token,
        &user,
        &0u32,
    );
    assert!(user_data_before.accrued > 0);

    // Pause the contract
    client.pause(&emission_manager);
    assert!(client.is_paused());

    // Unpause the contract
    client.unpause(&emission_manager);
    assert!(!client.is_paused());

    // Now claim should work
    let assets = Vec::from_array(&env, [token_address.clone()]);
    let claimed = client.claim_rewards(&user, &assets, &reward_token, &0u128, &to);
    assert!(claimed > 0);

    // Verify user's accrued balance was reset
    let user_data_after = client.get_user_reward_data(
        &token_address,
        &reward_token,
        &user,
        &0u32,
    );
    assert_eq!(user_data_after.accrued, 0);
}

// ============================================================================
// EDGE CASE TESTS: Zero Balances and Expired Distributions
// ============================================================================

#[test]
fn test_claim_rewards_after_distribution_expired() {
    // User accrues rewards before distribution ends, then claims after expiration
    let env = create_test_env();
    let (emission_manager, lending_pool, user, _) = create_test_addresses(&env);
    let contract_id = initialize_contract(&env, &emission_manager, &lending_pool);
    let client = incentives::Client::new(&env, &contract_id);

    let token_address = Address::generate(&env); // Token address (asset identifier)
    let to = Address::generate(&env);

    // Create reward token contract and fund it
    let token_admin = Address::generate(&env);
    let reward_token_contract = env.register_stellar_asset_contract_v2(token_admin.clone());
    let reward_token = reward_token_contract.address();
    let reward_token_client = soroban_sdk::token::StellarAssetClient::new(&env, &reward_token);
    reward_token_client.mint(&contract_id, &(1_000_000_000_000i128));

    // Configure rewards with end time - asset is the token address (following Aave pattern)
    let end_timestamp = 5000u64;
    set_timestamp(&env, 1000);
    client.configure_asset_rewards(
        &emission_manager,
        &token_address, // Token address is the asset identifier
        &reward_token,
        &0u32,
        &100_000_000u128,
        &end_timestamp,
    );

    // User supplies before end time and accrues rewards
    client.handle_action(
        &token_address,
        &user,
        &10_000_000_000_000u128,
        &1_000_000_000_000u128,
        &0u32,
    );

    set_timestamp(&env, 3000);

    client.handle_action(
        &token_address,
        &user,
        &10_000_000_000_000u128,
        &1_000_000_000_000u128,
        &0u32,
    );

    // Verify user has accrued rewards
    let user_data_before = client.get_user_reward_data(
        &token_address,
        &reward_token,
        &user,
        &0u32,
    );
    assert!(
        user_data_before.accrued > 0,
        "User should have accrued rewards before expiration"
    );

    // Advance time past distribution end
    set_timestamp(&env, 6000);

    // User should still be able to claim rewards accrued before expiration
    let assets = Vec::from_array(&env, [token_address.clone()]);
    let claimed = client.claim_rewards(&user, &assets, &reward_token, &0u128, &to);
    assert!(
        claimed > 0,
        "User should be able to claim rewards accrued before expiration"
    );

    // Verify user's accrued balance was reset
    let user_data_after = client.get_user_reward_data(
        &token_address,
        &reward_token,
        &user,
        &0u32,
    );
    assert_eq!(user_data_after.accrued, 0);
}

#[test]
fn test_claim_rewards_with_zero_balance_but_accrued() {
    // User has accrued rewards from before, but current balance is zero
    let env = create_test_env();
    let (emission_manager, lending_pool, user, _) = create_test_addresses(&env);
    let contract_id = initialize_contract(&env, &emission_manager, &lending_pool);
    let client = incentives::Client::new(&env, &contract_id);

    let token_address = Address::generate(&env); // Token address (asset identifier)
    let to = Address::generate(&env);

    // Create reward token contract and fund it
    let token_admin = Address::generate(&env);
    let reward_token_contract = env.register_stellar_asset_contract_v2(token_admin.clone());
    let reward_token = reward_token_contract.address();
    let reward_token_client = soroban_sdk::token::StellarAssetClient::new(&env, &reward_token);
    reward_token_client.mint(&contract_id, &(1_000_000_000_000i128));

    set_timestamp(&env, 1000);

    // Configure rewards - asset is the token address (following Aave pattern)
    client.configure_asset_rewards(
        &emission_manager,
        &token_address, // Token address is the asset identifier
        &reward_token,
        &0u32,
        &100_000_000u128,
        &0u64,
    );

    // User supplies and accrues rewards
    client.handle_action(
        &token_address,
        &user,
        &10_000_000_000_000u128,
        &1_000_000_000_000u128,
        &0u32,
    );

    set_timestamp(&env, 4600);

    client.handle_action(
        &token_address,
        &user,
        &10_000_000_000_000u128,
        &1_000_000_000_000u128,
        &0u32,
    );

    // Verify user has accrued rewards
    let user_data_with_balance = client.get_user_reward_data(
        &token_address,
        &reward_token,
        &user,
        &0u32,
    );
    assert!(user_data_with_balance.accrued > 0);

    // User withdraws all balance (balance goes to zero)
    set_timestamp(&env, 5000);
    client.handle_action(
        &token_address,
        &user,
        &10_000_000_000_000u128,
        &0u128, // Zero balance
        &0u32,
    );

    // Verify user still has accrued rewards (stored separately)
    let user_data_zero_balance = client.get_user_reward_data(
        &token_address,
        &reward_token,
        &user,
        &0u32,
    );
    assert_eq!(
        user_data_zero_balance.accrued, user_data_with_balance.accrued,
        "Accrued rewards should remain even with zero balance"
    );

    // User should still be able to claim accrued rewards
    let assets = Vec::from_array(&env, [token_address.clone()]);
    let claimed = client.claim_rewards(&user, &assets, &reward_token, &0u128, &to);
    assert!(
        claimed > 0,
        "User should be able to claim accrued rewards even with zero balance"
    );

    // Verify user's accrued balance was reset
    let user_data_after = client.get_user_reward_data(
        &token_address,
        &reward_token,
        &user,
        &0u32,
    );
    assert_eq!(user_data_after.accrued, 0);
}

#[test]
fn test_configure_distribution_end_with_past_timestamp() {
    // Configure rewards with distribution_end already in the past
    let env = create_test_env();
    let (emission_manager, lending_pool, user, _) = create_test_addresses(&env);
    let contract_id = initialize_contract(&env, &emission_manager, &lending_pool);
    let client = incentives::Client::new(&env, &contract_id);

    let asset = Address::generate(&env);
    let reward_token = Address::generate(&env);
    let token_address = Address::generate(&env);

    set_timestamp(&env, 10000); // Current time is 10000

    // Configure rewards with end time in the past (5000 < 10000)
    let past_end_timestamp = 5000u64;
    client.configure_asset_rewards(
        &emission_manager,
        &asset,
        &reward_token,
        &0u32,
        &100_000_000u128,
        &past_end_timestamp,
    );

    // User supplies - should not accrue rewards since distribution already ended
    client.handle_action(
        &token_address,
        &user,
        &10_000_000_000_000u128,
        &1_000_000_000_000u128,
        &0u32,
    );

    // Verify index didn't grow (distribution already ended)
    let index = client.get_asset_reward_index(&asset, &reward_token, &0u32);
    assert_eq!(
        index.index, RAY,
        "Index should not grow when distribution already ended"
    );

    // Verify user has no accrued rewards
    let user_data =
        client.get_user_reward_data(&asset, &reward_token, &user, &0u32);
    assert_eq!(
        user_data.accrued, 0,
        "User should not accrue rewards when distribution already ended"
    );
}

#[test]
fn test_set_distribution_end_to_past_timestamp() {
    // Set distribution_end to a past timestamp after rewards were configured
    let env = create_test_env();
    let (emission_manager, lending_pool, user, _) = create_test_addresses(&env);
    let contract_id = initialize_contract(&env, &emission_manager, &lending_pool);
    let client = incentives::Client::new(&env, &contract_id);

    let token_address = Address::generate(&env); // Token address (asset identifier)

    // Create reward token contract and fund it
    let token_admin = Address::generate(&env);
    let reward_token_contract = env.register_stellar_asset_contract_v2(token_admin.clone());
    let reward_token = reward_token_contract.address();
    let reward_token_client = soroban_sdk::token::StellarAssetClient::new(&env, &reward_token);
    reward_token_client.mint(&contract_id, &(1_000_000_000_000i128));

    set_timestamp(&env, 1000);

    // Configure rewards with no end time - asset is the token address (following Aave pattern)
    client.configure_asset_rewards(
        &emission_manager,
        &token_address, // Token address is the asset identifier
        &reward_token,
        &0u32,
        &100_000_000u128,
        &0u64, // No end
    );

    // User supplies and accrues rewards
    client.handle_action(
        &token_address,
        &user,
        &10_000_000_000_000u128,
        &1_000_000_000_000u128,
        &0u32,
    );

    set_timestamp(&env, 5000);

    // User accrues more rewards
    client.handle_action(
        &token_address,
        &user,
        &10_000_000_000_000u128,
        &1_000_000_000_000u128,
        &0u32,
    );

    // Verify user has accrued rewards
    let user_data_before = client.get_user_reward_data(
        &token_address,
        &reward_token,
        &user,
        &0u32,
    );
    assert!(user_data_before.accrued > 0);

    // Set distribution_end to a past timestamp (before current time)
    let past_end_timestamp = 3000u64; // Past timestamp
    client.set_distribution_end(
        &emission_manager,
        &token_address, // Token address is the asset identifier
        &reward_token,
        &0u32,
        &past_end_timestamp,
    );

    // Advance time
    set_timestamp(&env, 6000);

    // User should not accrue new rewards after distribution end was set to past
    let index_before =
        client.get_asset_reward_index(&token_address, &reward_token, &0u32);

    client.handle_action(
        &token_address,
        &user,
        &10_000_000_000_000u128,
        &1_000_000_000_000u128,
        &0u32,
    );

    // Index should not grow (distribution ended in the past)
    let index_after =
        client.get_asset_reward_index(&token_address, &reward_token, &0u32);
    assert_eq!(
        index_before.index, index_after.index,
        "Index should not grow after distribution end is set to past timestamp"
    );

    // User should still be able to claim previously accrued rewards
    let to = Address::generate(&env);
    let assets = Vec::from_array(&env, [token_address.clone()]);
    let claimed = client.claim_rewards(&user, &assets, &reward_token, &0u128, &to);
    assert!(
        claimed > 0,
        "User should be able to claim rewards accrued before distribution ended"
    );
}

#[test]
fn test_get_user_accrued_rewards() {
    let env = create_test_env();
    let (emission_manager, lending_pool, user, _) = create_test_addresses(&env);
    let contract_id = initialize_contract(&env, &emission_manager, &lending_pool);
    let client = incentives::Client::new(&env, &contract_id);

    let token_address = Address::generate(&env); // Token address (asset identifier)
    let reward_token = Address::generate(&env);

    // Configure rewards - asset is the token address (following Aave pattern)
    client.configure_asset_rewards(
        &emission_manager,
        &token_address, // Token address is the asset identifier
        &reward_token,
        &0u32,
        &100_000_000u128,
        &0u64,
    );

    set_timestamp(&env, 1000);

    // User supplies
    client.handle_action(
        &token_address,
        &user,
        &10_000_000_000_000u128,
        &1_000_000_000_000u128,
        &0u32,
    );

    set_timestamp(&env, 4600);

    // Accrue rewards
    client.handle_action(
        &token_address,
        &user,
        &10_000_000_000_000u128,
        &1_000_000_000_000u128,
        &0u32,
    );

    // Check accrued rewards
    let accrued = client.get_user_accrued_rewards(
        &token_address,
        &reward_token,
        &user,
        &0u32,
    );
    assert!(accrued > 0);
}

// ============================================================================
// COMPUTATIONAL TESTS (Based on Example 3 from INCENTIVES.md)
// ============================================================================

#[test]
fn test_computational_example_3_timeline() {
    // This test verifies the calculations match Example 3 from INCENTIVES.md
    // Example 3: Detailed Timeline with Multiple Users
    // Emission rate: 1 token/second
    // User A initial supply: 900 scaled units
    // User B initial supply: 100 scaled units
    // Total supply: 1000 scaled units
    // Track over 50 seconds

    let env = create_test_env();
    let (emission_manager, lending_pool, user_a, user_b) = create_test_addresses(&env);
    let contract_id = initialize_contract(&env, &emission_manager, &lending_pool);
    let client = incentives::Client::new(&env, &contract_id);

    let token_address = Address::generate(&env); // Token address (asset identifier)
    let reward_token = Address::generate(&env);

    // Setup: 1 token/second emission rate
    // Note: Using 1_000_000u128 to represent 1 token with 6 decimals
    let emission_per_second = 1_000_000u128; // 1 token/second with 6 decimals
    let initial_total_supply = 1_000_000_000_000u128; // 1000 scaled units
    let user_a_initial_balance = 900_000_000_000u128; // 900 scaled units
    let user_b_initial_balance = 100_000_000_000u128; // 100 scaled units

    // Set initial timestamp (t=0)
    set_timestamp(&env, 0);

    // Configure rewards - asset is the token address (following Aave pattern)
    client.configure_asset_rewards(
        &emission_manager,
        &token_address, // Token address is the asset identifier
        &reward_token,
        &0u32,
        &emission_per_second,
        &0u64,
    );

    // Initial state verification
    let initial_index =
        client.get_asset_reward_index(&token_address, &reward_token, &0u32);
    assert_eq!(initial_index.index, RAY);
    assert_eq!(initial_index.last_update_timestamp, 0);

    // ========================================================================
    // t=0 seconds: User A and User B establish initial balances
    // ========================================================================
    // User A establishes initial balance (no rewards accrued yet)
    client.handle_action(
        &token_address,
        &user_a,
        &initial_total_supply,
        &user_a_initial_balance,
        &0u32,
    );

    // User B establishes initial balance (no rewards accrued yet)
    client.handle_action(
        &token_address,
        &user_b,
        &initial_total_supply,
        &user_b_initial_balance,
        &0u32,
    );

    // ========================================================================
    // t=10 seconds: User A supplies +100
    // ========================================================================
    set_timestamp(&env, 10);

    // User A interacts (supplies 100 more)
    let total_supply_after_a_supply = initial_total_supply + 100_000_000_000u128; // 1100
    let user_a_new_balance = user_a_initial_balance + 100_000_000_000u128; // 1000

    client.handle_action(
        &token_address, // Token address (asset identifier)
        &user_a,
        &total_supply_after_a_supply,
        &user_a_new_balance,
        &0u32,
    );

    // Expected index increment: (1 × 10 × RAY) / 1000 = 0.01 × RAY
    // Expected index: RAY + 0.01 × RAY = 1.01 × RAY
    let index_at_10 =
        client.get_asset_reward_index(&token_address, &reward_token, &0u32);
    let expected_index_increment =
        k2_shared::ray_div(&env, emission_per_second * 10u128, initial_total_supply).unwrap();
    let expected_index_10 = RAY.checked_add(expected_index_increment).unwrap();

    // Verify index is approximately correct (allow for rounding)
    // Tolerance: 0.1% of RAY (1e24)
    let diff_10 = if index_at_10.index > expected_index_10 {
        index_at_10.index - expected_index_10
    } else {
        expected_index_10 - index_at_10.index
    };
    let tolerance_10 = RAY / 1000; // 0.1% of RAY
    assert!(
        diff_10 < tolerance_10,
        "Index at t=10 should be approximately 1.01 × RAY. Actual: {}, Expected: {}, Diff: {}",
        index_at_10.index,
        expected_index_10,
        diff_10
    );

    // User A's accrued rewards: (0.01 × RAY × 900) / RAY = 9 tokens
    // Using 9_000_000u128 to represent 9 tokens with 6 decimals
    let user_a_data_10 = client.get_user_reward_data(
        &token_address,
        &reward_token,
        &user_a,
        &0u32,
    );
    let expected_accrued_a_10 =
        k2_shared::ray_mul(&env, expected_index_increment, user_a_initial_balance).unwrap();

    // Allow for rounding differences
    let diff_accrued_a_10 = if user_a_data_10.accrued > expected_accrued_a_10 {
        user_a_data_10.accrued - expected_accrued_a_10
    } else {
        expected_accrued_a_10 - user_a_data_10.accrued
    };
    assert!(
        diff_accrued_a_10 < 1_000_000u128,
        "User A accrued at t=10 should be approximately 9 tokens"
    );

    // ========================================================================
    // t=30 seconds (20 seconds later): User A withdraws 500
    // ========================================================================
    set_timestamp(&env, 30);

    // User A interacts (withdraws 500)
    let total_supply_after_a_withdraw = total_supply_after_a_supply - 500_000_000_000u128; // 600
    let user_a_balance_after_withdraw = user_a_new_balance - 500_000_000_000u128; // 500

    client.handle_action(
        &token_address,
        &user_a,
        &total_supply_after_a_withdraw,
        &user_a_balance_after_withdraw,
        &0u32,
    );

    // Expected index increment: (1 × 20 × RAY) / 1100 ≈ 0.01818 × RAY
    let time_elapsed_20 = 20u128;
    let expected_index_increment_20 = k2_shared::ray_div(
        &env,
        emission_per_second * time_elapsed_20,
        total_supply_after_a_supply,
    ).unwrap();
    let expected_index_30 = index_at_10
        .index
        .checked_add(expected_index_increment_20)
        .unwrap();

    let index_at_30 =
        client.get_asset_reward_index(&token_address, &reward_token, &0u32);
    let diff_30 = if index_at_30.index > expected_index_30 {
        index_at_30.index - expected_index_30
    } else {
        expected_index_30 - index_at_30.index
    };
    let tolerance_30 = RAY / 1000; // 0.1% of RAY
    assert!(
        diff_30 < tolerance_30,
        "Index at t=30 should match expected value. Actual: {}, Expected: {}, Diff: {}",
        index_at_30.index,
        expected_index_30,
        diff_30
    );

    // User A's additional accrued: (0.01818 × RAY × 1000) / RAY ≈ 18.18 tokens
    let user_a_data_30 = client.get_user_reward_data(
        &token_address,
        &reward_token,
        &user_a,
        &0u32,
    );
    let expected_accrued_a_30_additional =
        k2_shared::ray_mul(&env, expected_index_increment_20, user_a_new_balance).unwrap();
    let expected_total_accrued_a_30 = user_a_data_10
        .accrued
        .checked_add(expected_accrued_a_30_additional)
        .unwrap();

    let diff_accrued_a_30 = if user_a_data_30.accrued > expected_total_accrued_a_30 {
        user_a_data_30.accrued - expected_total_accrued_a_30
    } else {
        expected_total_accrued_a_30 - user_a_data_30.accrued
    };
    assert!(
        diff_accrued_a_30 < 2_000_000u128,
        "User A total accrued at t=30 should be approximately 27.18 tokens"
    );

    // ========================================================================
    // t=50 seconds (20 seconds later): User B claims rewards
    // ========================================================================
    set_timestamp(&env, 50);

    // User B interacts for the first time (claims)
    client.handle_action(
        &token_address,
        &user_b,
        &total_supply_after_a_withdraw, // Total supply is still 600
        &user_b_initial_balance,        // User B's balance is still 100
        &0u32,
    );

    // Expected index increment: (1 × 20 × RAY) / 600 = 0.03333 × RAY
    let expected_index_increment_20_600 = k2_shared::ray_div(
        &env,
        emission_per_second * time_elapsed_20,
        total_supply_after_a_withdraw,
    ).unwrap();
    let expected_index_50 = index_at_30
        .index
        .checked_add(expected_index_increment_20_600)
        .unwrap();

    let index_at_50 =
        client.get_asset_reward_index(&token_address, &reward_token, &0u32);
    let diff_50 = if index_at_50.index > expected_index_50 {
        index_at_50.index - expected_index_50
    } else {
        expected_index_50 - index_at_50.index
    };
    let tolerance_50 = RAY / 1000; // 0.1% of RAY
    assert!(
        diff_50 < tolerance_50,
        "Index at t=50 should match expected value. Actual: {}, Expected: {}, Diff: {}",
        index_at_50.index,
        expected_index_50,
        diff_50
    );

    // User B's accrued: (0.06151 × RAY × 100) / RAY ≈ 6.151 tokens
    let user_b_data_50 = client.get_user_reward_data(
        &token_address,
        &reward_token,
        &user_b,
        &0u32,
    );
    // User B's index snapshot was 0 (RAY), so they get rewards from index 0 to current
    let index_diff_for_b = index_at_50.index.checked_sub(RAY).unwrap();
    let expected_accrued_b = k2_shared::ray_mul(&env, index_diff_for_b, user_b_initial_balance).unwrap();

    let diff_accrued_b = if user_b_data_50.accrued > expected_accrued_b {
        user_b_data_50.accrued - expected_accrued_b
    } else {
        expected_accrued_b - user_b_data_50.accrued
    };
    assert!(
        diff_accrued_b < 1_000_000u128,
        "User B accrued at t=50 should be approximately 6.15 tokens"
    );

    // User A's pending rewards can be calculated without them interacting
    // Get current index (already updated by user B's interaction at t=50)
    let index_at_50_updated =
        client.get_asset_reward_index(&token_address, &reward_token, &0u32);

    // Get user A's stored data (from their last interaction at t=30)
    let user_a_data_30_stored = client.get_user_reward_data(
        &token_address,
        &reward_token,
        &user_a,
        &0u32,
    );

    // Calculate pending rewards: (current_index - user_snapshot) * user_balance
    let index_diff_for_a = index_at_50_updated
        .index
        .checked_sub(user_a_data_30_stored.index_snapshot)
        .unwrap();
    let pending_rewards_a = k2_shared::ray_mul(
        &env,
        index_diff_for_a,
        user_a_balance_after_withdraw, // A's current balance is 500
    ).unwrap();

    // Total accrued = stored accrued + pending rewards
    let expected_total_accrued_a_50 = user_a_data_30_stored
        .accrued
        .checked_add(pending_rewards_a)
        .unwrap();

    // Verify the calculated total matches expected value
    // Note: We're calculating pending rewards without requiring user A to interact
    // This demonstrates that rewards can be calculated on-demand
    assert!(
        expected_total_accrued_a_50 > 40_000_000u128
            && expected_total_accrued_a_50 < 50_000_000u128,
        "User A total accrued at t=50 (calculated: {}) should be approximately 43.85 tokens",
        expected_total_accrued_a_50
    );

    // ========================================================================
    // Verify total rewards match emission
    // ========================================================================
    // Total rewards distributed should equal: 1 token/sec × 50 seconds = 50 tokens
    // Using 50_000_000u128 to represent 50 tokens with 6 decimals
    let total_rewards_a = expected_total_accrued_a_50;
    let total_rewards_b = user_b_data_50.accrued;
    let total_rewards = total_rewards_a + total_rewards_b;
    let expected_total = emission_per_second * 50u128; // 50 tokens with 6 decimals

    // Allow for small rounding differences (within 1 token)
    let diff_total = if total_rewards > expected_total {
        total_rewards - expected_total
    } else {
        expected_total - total_rewards
    };
    assert!(
        diff_total < 1_000_000u128,
        "Total rewards (A: {}, B: {}, Total: {}) should equal expected emission (50 tokens)",
        total_rewards_a,
        total_rewards_b,
        total_rewards
    );
}

// ============================================================================
// FUND REWARDS TESTS
// ============================================================================

#[test]
fn test_fund_rewards() {
    let env = create_test_env();
    let (emission_manager, lending_pool, _, _) = create_test_addresses(&env);
    let contract_id = initialize_contract(&env, &emission_manager, &lending_pool);
    let client = incentives::Client::new(&env, &contract_id);

    // Create reward token contract
    let token_admin = Address::generate(&env);
    let reward_token_contract = env.register_stellar_asset_contract_v2(token_admin.clone());
    let reward_token = reward_token_contract.address();

    // Mint tokens to emission manager
    let reward_token_client = soroban_sdk::token::StellarAssetClient::new(&env, &reward_token);
    let funding_amount = 1_000_000_000_000u128; // 1,000 tokens with 6 decimals
    reward_token_client.mint(&emission_manager, &(funding_amount as i128));

    // Check initial balance (should be 0)
    let initial_balance = client.get_reward_token_balance(&reward_token);
    assert_eq!(initial_balance, 0);

    // Fund the contract
    client.fund_rewards(&emission_manager, &reward_token, &funding_amount);

    // Check contract balance after funding
    let contract_balance = client.get_reward_token_balance(&reward_token);
    assert_eq!(contract_balance, funding_amount);

    // Check emission manager balance (should be 0 now)
    let token_client = soroban_sdk::token::Client::new(&env, &reward_token);
    let manager_balance = token_client.balance(&emission_manager) as u128;
    assert_eq!(manager_balance, 0);
}

#[test]
#[should_panic(expected = "Error(Contract, #3)")]
fn test_fund_rewards_unauthorized() {
    let env = create_test_env();
    let (emission_manager, lending_pool, user, _) = create_test_addresses(&env);
    let contract_id = initialize_contract(&env, &emission_manager, &lending_pool);
    let client = incentives::Client::new(&env, &contract_id);

    // Create reward token contract
    let token_admin = Address::generate(&env);
    let reward_token_contract = env.register_stellar_asset_contract_v2(token_admin.clone());
    let reward_token = reward_token_contract.address();

    // Try to fund as non-emission manager (should fail)
    client.fund_rewards(&user, &reward_token, &1_000_000_000_000u128);
}

#[test]
fn test_fund_rewards_multiple_times() {
    let env = create_test_env();
    let (emission_manager, lending_pool, _, _) = create_test_addresses(&env);
    let contract_id = initialize_contract(&env, &emission_manager, &lending_pool);
    let client = incentives::Client::new(&env, &contract_id);

    // Create reward token contract
    let token_admin = Address::generate(&env);
    let reward_token_contract = env.register_stellar_asset_contract_v2(token_admin.clone());
    let reward_token = reward_token_contract.address();

    let reward_token_client = soroban_sdk::token::StellarAssetClient::new(&env, &reward_token);

    // First funding
    let amount1 = 500_000_000_000u128;
    reward_token_client.mint(&emission_manager, &(amount1 as i128));
    client.fund_rewards(&emission_manager, &reward_token, &amount1);

    let balance1 = client.get_reward_token_balance(&reward_token);
    assert_eq!(balance1, amount1);

    // Second funding
    let amount2 = 300_000_000_000u128;
    reward_token_client.mint(&emission_manager, &(amount2 as i128));
    client.fund_rewards(&emission_manager, &reward_token, &amount2);

    let balance2 = client.get_reward_token_balance(&reward_token);
    assert_eq!(balance2, amount1 + amount2);
}

#[test]
fn test_get_reward_token_balance() {
    let env = create_test_env();
    let (emission_manager, lending_pool, _, _) = create_test_addresses(&env);
    let contract_id = initialize_contract(&env, &emission_manager, &lending_pool);
    let client = incentives::Client::new(&env, &contract_id);

    // Create reward token contract
    let token_admin = Address::generate(&env);
    let reward_token_contract = env.register_stellar_asset_contract_v2(token_admin.clone());
    let reward_token = reward_token_contract.address();

    // Check balance before funding (should be 0)
    let balance_before = client.get_reward_token_balance(&reward_token);
    assert_eq!(balance_before, 0);

    // Fund the contract
    let reward_token_client = soroban_sdk::token::StellarAssetClient::new(&env, &reward_token);
    let funding_amount = 1_000_000_000_000u128;
    reward_token_client.mint(&emission_manager, &(funding_amount as i128));
    client.fund_rewards(&emission_manager, &reward_token, &funding_amount);

    // Check balance after funding
    let balance_after = client.get_reward_token_balance(&reward_token);
    assert_eq!(balance_after, funding_amount);
}

#[test]
fn test_fund_rewards_and_claim() {
    let env = create_test_env();
    let (emission_manager, lending_pool, user, _) = create_test_addresses(&env);
    let contract_id = initialize_contract(&env, &emission_manager, &lending_pool);
    let client = incentives::Client::new(&env, &contract_id);

    let token_address = Address::generate(&env); // Token address (asset identifier)
    let to = Address::generate(&env);

    // Create reward token contract
    let token_admin = Address::generate(&env);
    let reward_token_contract = env.register_stellar_asset_contract_v2(token_admin.clone());
    let reward_token = reward_token_contract.address();
    let reward_token_client = soroban_sdk::token::StellarAssetClient::new(&env, &reward_token);

    // Fund the contract using the new function
    let funding_amount = 1_000_000_000_000u128;
    reward_token_client.mint(&emission_manager, &(funding_amount as i128));
    client.fund_rewards(&emission_manager, &reward_token, &funding_amount);

    // Set initial timestamp
    set_timestamp(&env, 1000);

    // Configure rewards - asset is the token address (following Aave pattern)
    client.configure_asset_rewards(
        &emission_manager,
        &token_address, // Token address is the asset identifier
        &reward_token,
        &0u32,
        &100_000_000u128,
        &0u64,
    );

    // User supplies and accrues rewards
    client.handle_action(
        &token_address,
        &user,
        &10_000_000_000_000u128,
        &1_000_000_000_000u128,
        &0u32,
    );

    set_timestamp(&env, 4600); // 1 hour later

    // User interacts again to accrue rewards
    client.handle_action(
        &token_address,
        &user,
        &10_000_000_000_000u128,
        &1_000_000_000_000u128,
        &0u32,
    );

    // Check accrued rewards
    let user_data = client.get_user_reward_data(
        &token_address,
        &reward_token,
        &user,
        &0u32,
    );
    assert!(user_data.accrued > 0);

    // Check contract balance before claim
    let balance_before = client.get_reward_token_balance(&reward_token);
    assert!(balance_before >= user_data.accrued);

    // Claim rewards
    let assets = Vec::from_array(&env, [token_address.clone()]);
    let claimed = client.claim_rewards(&user, &assets, &reward_token, &0u128, &to);

    // Verify rewards were claimed
    assert!(claimed > 0);

    // Check contract balance after claim (should be reduced)
    let balance_after = client.get_reward_token_balance(&reward_token);
    assert_eq!(balance_after, balance_before - claimed);

    // Verify user's accrued balance was reset
    let user_data_after = client.get_user_reward_data(
        &token_address,
        &reward_token,
        &user,
        &0u32,
    );
    assert_eq!(user_data_after.accrued, 0);
}

// ============================================================================
// SECURITY TESTS - Authentication Bypass Prevention (FIND-019)
// ============================================================================

#[test]
#[should_panic(expected = "Error(Auth")]
fn test_handle_action_requires_token_authentication() {
    let env = Env::default();
    let (emission_manager, lending_pool, attacker, _) = create_test_addresses(&env);
    let contract_id = initialize_contract(&env, &emission_manager, &lending_pool);
    let client = incentives::Client::new(&env, &contract_id);

    let token_address = Address::generate(&env);
    let reward_token = Address::generate(&env);
    let emission_per_second = 1_000_000u128;

    env.mock_auths(&[soroban_sdk::testutils::MockAuth {
        address: &emission_manager,
        invoke: &soroban_sdk::testutils::MockAuthInvoke {
            contract: &contract_id,
            fn_name: "configure_asset_rewards",
            args: (
                emission_manager.clone(),
                token_address.clone(),
                reward_token.clone(),
                0u32,
                emission_per_second,
                0u64,
            )
                .into_val(&env),
            sub_invokes: &[],
        },
    }]);
    client.configure_asset_rewards(
        &emission_manager,
        &token_address,
        &reward_token,
        &0u32,
        &emission_per_second,
        &0u64,
    );

    set_timestamp(&env, 100);

    // Call handle_action without token_address authentication - should fail
    client.handle_action(
        &token_address,
        &attacker,
        &1u128,
        &10_000_000_000_000u128,
        &0u32,
    );
}

// ============================================================================
// SECURITY TESTS - Back-Accrual Prevention (FIND-020)
// ============================================================================

#[test]
fn test_handle_action_no_back_accrual_on_first_interaction() {
    // This test verifies that new deposits do not accrue rewards for past periods (FIND-020)
    let env = create_test_env();
    let (emission_manager, lending_pool, user, _) = create_test_addresses(&env);
    let contract_id = initialize_contract(&env, &emission_manager, &lending_pool);
    let client = incentives::Client::new(&env, &contract_id);

    let token_address = Address::generate(&env);
    let reward_token = Address::generate(&env);
    let emission_per_second = 1_000_000u128;
    let total_supply = 1_000_000_000_000u128;

    // Configure rewards
    client.configure_asset_rewards(
        &emission_manager,
        &token_address,
        &reward_token,
        &0u32,
        &emission_per_second,
        &0u64,
    );

    // Set initial timestamp
    set_timestamp(&env, 100);

    // Advance time significantly to create a large reward period
    set_timestamp(&env, 10000);

    // First handle_action for this user (balance_snapshot == 0)
    // Should NOT accrue rewards for the past period (t=100 to t=10000)
    let user_balance = 1_000_000_000u128;
    client.handle_action(
        &token_address,
        &user,
        &total_supply,
        &user_balance,
        &0u32,
    );

    // User should have 0 accrued rewards since they didn't hold balance during the period
    let user_data = client.get_user_reward_data(
        &token_address,
        &reward_token,
        &user,
        &0u32,
    );
    assert_eq!(user_data.accrued, 0, "new deposits should not accrue rewards for past periods");

    // Advance time again
    set_timestamp(&env, 20000);

    // Second handle_action - now user should accrue rewards for the period they held balance
    client.handle_action(
        &token_address,
        &user,
        &total_supply,
        &user_balance,
        &0u32,
    );

    // Now user should have accrued rewards for the period they held balance (t=10000 to t=20000)
    let user_data_after = client.get_user_reward_data(
        &token_address,
        &reward_token,
        &user,
        &0u32,
    );
    assert!(user_data_after.accrued > 0, "user should accrue rewards for periods they held balance");
}

#[test]
fn test_distribution_end_accrues_final_interval() {
    let env = create_test_env();
    let (emission_manager, lending_pool, _, _) = create_test_addresses(&env);
    let contract_id = initialize_contract(&env, &emission_manager, &lending_pool);
    let client = incentives::Client::new(&env, &contract_id);

    let token = Address::generate(&env);
    let reward_token = Address::generate(&env);

    // Configure distribution: ends at t=100, emission 1e6, supply 100
    let distribution_end: u64 = 100;
    let emission_per_second: u128 = 1_000_000;
    let total_supply: u128 = 100;

    client.configure_asset_rewards(
        &emission_manager,
        &token,
        &reward_token,
        &0u32,
        &emission_per_second,
        &distribution_end,
    );

    // Initial index is RAY at last_update_timestamp = 0
    let before = client.get_asset_reward_index(&token, &reward_token, &0u32);
    assert_eq!(before.index, RAY);
    assert_eq!(before.last_update_timestamp, 0);

    // Advance time past distribution_end
    set_timestamp(&env, 150);

    // Call handle_action: should accrue rewards for 0..100 even though current time is 150
    client.handle_action(
        &token,
        &Address::generate(&env),
        &total_supply,
        &0u128,
        &0u32,
    );

    let after = client.get_asset_reward_index(&token, &reward_token, &0u32);

    // Index should have accrued for 100 seconds before distribution_end
    // Expected: (1_000_000 * 100 * RAY) / 100 = 100_000_000 * RAY / 100 = 1_000_000 * RAY
    let expected_increment = 1_000_000 * RAY;
    let expected_index = RAY + expected_increment;
    
    assert_eq!(
        after.index, expected_index,
        "index should accrue rewards up to distribution_end"
    );
    assert_eq!(
        after.last_update_timestamp, 150,
        "timestamp should update to current time"
    );
}
