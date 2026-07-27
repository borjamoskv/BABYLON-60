#![cfg(test)]

use crate::incentives;
use crate::setup::{create_test_token, deploy_full_protocol, ReflectorStub};
use crate::{
    a_token, debt_token, interest_rate_strategy, kinetic_router, pool_configurator,
};
use k2_shared::KineticRouterError;
use soroban_sdk::{
    testutils::{Address as _, Ledger, LedgerInfo},
    token, Address, Bytes, Env, IntoVal, Symbol, String, Vec,
};

/// Initialize ledger with TTL settings that prevent storage expiration in tests
fn set_ledger_with_realistic_ttl(env: &Env) {
    env.ledger().set(LedgerInfo {
        sequence_number: 100,
        protocol_version: 23,
        timestamp: 1_700_000_000,
        network_id: Default::default(),
        base_reserve: 10,
        min_temp_entry_ttl: 6_307_200,
        min_persistent_entry_ttl: 6_307_200,
        max_entry_ttl: 6_307_200,
    });
}

/// Advance ledger timestamp without causing TTL expiration
fn advance_time_safe(env: &Env, seconds: u64) {
    let current = env.ledger().timestamp();
    let current_seq = env.ledger().sequence();
    env.ledger().set(LedgerInfo {
        timestamp: current + seconds,
        sequence_number: current_seq,
        protocol_version: 23,
        network_id: Default::default(),
        base_reserve: 10,
        min_temp_entry_ttl: 6_307_200,
        min_persistent_entry_ttl: 6_307_200,
        max_entry_ttl: 6_307_200,
    });
}

#[test]
fn test_incentives_pause_state() {
    let env = Env::default();
    env.mock_all_auths();
    
    let admin = Address::generate(&env);
    let emergency_admin = Address::generate(&env);
    let protocol = deploy_full_protocol(&env, &admin, &emergency_admin);
    
    let incentives_client = incentives::Client::new(&env, &protocol.incentives);
    
    let is_paused_initial = incentives_client.is_paused();
    assert_eq!(is_paused_initial, false, "Must not be paused initially. Expected: false, Got: {}", is_paused_initial);
    
    let is_paused_second_call = incentives_client.is_paused();
    assert_eq!(is_paused_initial, is_paused_second_call, "Pause state must be consistent across calls. First: {}, Second: {}", is_paused_initial, is_paused_second_call);
}

#[test]
fn test_incentives_pause_unpause() {
    let env = Env::default();
    env.mock_all_auths();
    
    let admin = Address::generate(&env);
    let emergency_admin = Address::generate(&env);
    let protocol = deploy_full_protocol(&env, &admin, &emergency_admin);
    
    let incentives_client = incentives::Client::new(&env, &protocol.incentives);
    
    let is_paused_initial = incentives_client.is_paused();
    assert_eq!(is_paused_initial, false, "Must not be paused initially. Expected: false, Got: {}", is_paused_initial);
    
    incentives_client.pause(&admin);
    let is_paused_after_pause = incentives_client.is_paused();
    assert_eq!(is_paused_after_pause, true, "Must be paused after pause(). Expected: true, Got: {}", is_paused_after_pause);
    assert_ne!(is_paused_initial, is_paused_after_pause, "Pause state must have changed. Initial: {}, After pause: {}", is_paused_initial, is_paused_after_pause);
    
    incentives_client.unpause(&admin);
    let is_paused_after_unpause = incentives_client.is_paused();
    assert_eq!(is_paused_after_unpause, false, "Must be unpaused after unpause(). Expected: false, Got: {}", is_paused_after_unpause);
    assert_eq!(is_paused_initial, is_paused_after_unpause, "Must return to initial unpaused state. Initial: {}, After unpause: {}", is_paused_initial, is_paused_after_unpause);
    assert_ne!(is_paused_after_pause, is_paused_after_unpause, "Unpause must have changed state from paused. Paused: {}, Unpaused: {}", is_paused_after_pause, is_paused_after_unpause);
}

#[test]
fn test_incentives_get_assets() {
    let env = Env::default();
    env.mock_all_auths();
    
    let admin = Address::generate(&env);
    let emergency_admin = Address::generate(&env);
    let protocol = deploy_full_protocol(&env, &admin, &emergency_admin);
    
    let incentives_client = incentives::Client::new(&env, &protocol.incentives);
    
    let assets = incentives_client.get_assets();
    assert_eq!(assets.len(), 0, "Assets list must be empty initially. Expected: 0, Got: {} assets", assets.len());
    
    let assets_second_call = incentives_client.get_assets();
    assert_eq!(assets.len(), assets_second_call.len(), "Assets list length must be consistent across calls. First: {} assets, Second: {} assets", assets.len(), assets_second_call.len());
    
    for i in 0..assets.len() {
        let asset_first = assets.get(i as u32).unwrap();
        let asset_second = assets_second_call.get(i as u32).unwrap();
        assert_eq!(asset_first, asset_second, "Asset at index {} must be consistent. First: {:?}, Second: {:?}", i, asset_first, asset_second);
    }
}

#[test]
fn test_incentives_get_reward_tokens() {
    let env = Env::default();
    env.mock_all_auths();
    
    let admin = Address::generate(&env);
    let emergency_admin = Address::generate(&env);
    let protocol = deploy_full_protocol(&env, &admin, &emergency_admin);
    
    let incentives_client = incentives::Client::new(&env, &protocol.incentives);
    
    let test_asset = Address::generate(&env);
    let reward_tokens = incentives_client.get_reward_tokens(&test_asset);
    
    assert_eq!(reward_tokens.len(), 0, "Reward tokens list must be empty for unregistered asset. Expected: 0, Got: {} tokens", reward_tokens.len());
    
    let reward_tokens_second_call = incentives_client.get_reward_tokens(&test_asset);
    assert_eq!(reward_tokens.len(), reward_tokens_second_call.len(), "Reward tokens list must be consistent across calls. First: {} tokens, Second: {} tokens", reward_tokens.len(), reward_tokens_second_call.len());
    
    let different_asset = Address::generate(&env);
    let reward_tokens_different = incentives_client.get_reward_tokens(&different_asset);
    assert_eq!(reward_tokens_different.len(), 0, "Reward tokens list must be empty for different unregistered asset. Expected: 0, Got: {} tokens", reward_tokens_different.len());
}

#[test]
fn test_incentives_get_asset_reward_config() {
    let env = Env::default();
    env.mock_all_auths();
    
    let admin = Address::generate(&env);
    let emergency_admin = Address::generate(&env);
    let protocol = deploy_full_protocol(&env, &admin, &emergency_admin);
    
    let incentives_client = incentives::Client::new(&env, &protocol.incentives);
    
    let test_asset = Address::generate(&env);
    let reward_token = Address::generate(&env);
    let reward_type_supply = 0u32;
    let reward_type_borrow = 1u32;
    
    let config_supply = incentives_client.get_asset_reward_config(&test_asset, &reward_token, &reward_type_supply);
    assert_eq!(config_supply, None, "Reward config must be None for unregistered asset/token (supply). Asset: {:?}, Token: {:?}", test_asset, reward_token);
    
    let config_borrow = incentives_client.get_asset_reward_config(&test_asset, &reward_token, &reward_type_borrow);
    assert_eq!(config_borrow, None, "Reward config must be None for unregistered asset/token (borrow). Asset: {:?}, Token: {:?}", test_asset, reward_token);
    
    let config_supply_second = incentives_client.get_asset_reward_config(&test_asset, &reward_token, &reward_type_supply);
    assert_eq!(config_supply, config_supply_second, "Reward config must be consistent across calls. First: {:?}, Second: {:?}", config_supply, config_supply_second);
}

#[test]
fn test_incentives_get_asset_reward_index() {
    let env = Env::default();
    env.mock_all_auths();
    
    let admin = Address::generate(&env);
    let emergency_admin = Address::generate(&env);
    let protocol = deploy_full_protocol(&env, &admin, &emergency_admin);
    
    let incentives_client = incentives::Client::new(&env, &protocol.incentives);
    
    let test_asset = Address::generate(&env);
    let reward_token = Address::generate(&env);
    let reward_type_supply = 0u32;
    let reward_type_borrow = 1u32;
    
    let index_supply = incentives_client.get_asset_reward_index(&test_asset, &reward_token, &reward_type_supply);
    let ray = 1_000_000_000_000_000_000_000_000_000u128;
    assert_eq!(index_supply.index, ray, "Reward index must be RAY (1e27) for unregistered asset/token (supply). Expected: {}, Got: {}", ray, index_supply.index);
    
    let index_borrow = incentives_client.get_asset_reward_index(&test_asset, &reward_token, &reward_type_borrow);
    assert_eq!(index_borrow.index, ray, "Reward index must be RAY (1e27) for unregistered asset/token (borrow). Expected: {}, Got: {}", ray, index_borrow.index);
    
    let index_supply_second = incentives_client.get_asset_reward_index(&test_asset, &reward_token, &reward_type_supply);
    assert_eq!(index_supply.index, index_supply_second.index, "Reward index must be consistent across calls. First: {}, Second: {}", index_supply.index, index_supply_second.index);
}

#[test]
fn test_incentives_get_user_reward_data() {
    let env = Env::default();
    env.mock_all_auths();
    
    let admin = Address::generate(&env);
    let emergency_admin = Address::generate(&env);
    let protocol = deploy_full_protocol(&env, &admin, &emergency_admin);
    
    let incentives_client = incentives::Client::new(&env, &protocol.incentives);
    
    let test_asset = Address::generate(&env);
    let test_user = Address::generate(&env);
    let reward_token = Address::generate(&env);
    let reward_type_supply = 0u32;
    let reward_type_borrow = 1u32;
    
    let reward_data_supply = incentives_client.get_user_reward_data(&test_asset, &reward_token, &test_user, &reward_type_supply);
    let ray = 1_000_000_000_000_000_000_000_000_000u128;
    assert_eq!(reward_data_supply.accrued, 0u128, "User accrued rewards must be zero for unregistered asset/token (supply). Expected: 0, Got: {}", reward_data_supply.accrued);
    assert_eq!(reward_data_supply.balance_snapshot, 0u128, "User balance snapshot must be zero for unregistered asset/token (supply). Expected: 0, Got: {}", reward_data_supply.balance_snapshot);
    assert_eq!(reward_data_supply.index_snapshot, ray, "User index snapshot must be RAY (1e27) for unregistered asset/token (supply). Expected: {}, Got: {}", ray, reward_data_supply.index_snapshot);
    
    let reward_data_borrow = incentives_client.get_user_reward_data(&test_asset, &reward_token, &test_user, &reward_type_borrow);
    assert_eq!(reward_data_borrow.accrued, 0u128, "User accrued rewards must be zero for unregistered asset/token (borrow). Expected: 0, Got: {}", reward_data_borrow.accrued);
    assert_eq!(reward_data_borrow.balance_snapshot, 0u128, "User balance snapshot must be zero for unregistered asset/token (borrow). Expected: 0, Got: {}", reward_data_borrow.balance_snapshot);
    assert_eq!(reward_data_borrow.index_snapshot, ray, "User index snapshot must be RAY (1e27) for unregistered asset/token (borrow). Expected: {}, Got: {}", ray, reward_data_borrow.index_snapshot);
    
    let reward_data_supply_second = incentives_client.get_user_reward_data(&test_asset, &reward_token, &test_user, &reward_type_supply);
    assert_eq!(reward_data_supply.accrued, reward_data_supply_second.accrued, "User reward data must be consistent across calls. First accrued: {}, Second accrued: {}", reward_data_supply.accrued, reward_data_supply_second.accrued);
    assert_eq!(reward_data_supply.balance_snapshot, reward_data_supply_second.balance_snapshot, "User balance snapshot must be consistent across calls. First: {}, Second: {}", reward_data_supply.balance_snapshot, reward_data_supply_second.balance_snapshot);
    assert_eq!(reward_data_supply.index_snapshot, reward_data_supply_second.index_snapshot, "User index snapshot must be consistent across calls. First: {}, Second: {}", reward_data_supply.index_snapshot, reward_data_supply_second.index_snapshot);
}

#[test]
fn test_incentives_get_user_accrued_rewards() {
    let env = Env::default();
    env.mock_all_auths();
    
    let admin = Address::generate(&env);
    let emergency_admin = Address::generate(&env);
    let protocol = deploy_full_protocol(&env, &admin, &emergency_admin);
    
    let incentives_client = incentives::Client::new(&env, &protocol.incentives);
    
    let test_asset = Address::generate(&env);
    let test_user = Address::generate(&env);
    let reward_token = Address::generate(&env);
    let reward_type_supply = 0u32;
    let reward_type_borrow = 1u32;
    
    let rewards_supply = incentives_client.get_user_accrued_rewards(&test_asset, &reward_token, &test_user, &reward_type_supply);
    assert_eq!(rewards_supply, 0u128, "User accrued rewards must be zero for unregistered asset/token (supply). Expected: 0, Got: {}", rewards_supply);
    
    let rewards_borrow = incentives_client.get_user_accrued_rewards(&test_asset, &reward_token, &test_user, &reward_type_borrow);
    assert_eq!(rewards_borrow, 0u128, "User accrued rewards must be zero for unregistered asset/token (borrow). Expected: 0, Got: {}", rewards_borrow);
    
    let rewards_supply_second = incentives_client.get_user_accrued_rewards(&test_asset, &reward_token, &test_user, &reward_type_supply);
    assert_eq!(rewards_supply, rewards_supply_second, "User accrued rewards must be consistent across calls. First: {}, Second: {}", rewards_supply, rewards_supply_second);
    
    let different_user = Address::generate(&env);
    let rewards_different_user = incentives_client.get_user_accrued_rewards(&test_asset, &reward_token, &different_user, &reward_type_supply);
    assert_eq!(rewards_different_user, 0u128, "Different user accrued rewards must also be zero. Expected: 0, Got: {}", rewards_different_user);
}

#[test]
fn test_incentives_reward_token_balance_requires_valid_token() {
    let env = Env::default();
    env.mock_all_auths();
    
    let admin = Address::generate(&env);
    let emergency_admin = Address::generate(&env);
    let protocol = deploy_full_protocol(&env, &admin, &emergency_admin);
    
    let incentives_client = incentives::Client::new(&env, &protocol.incentives);
    
    let invalid_token = Address::generate(&env);
    let balance_result = std::panic::catch_unwind(std::panic::AssertUnwindSafe(|| {
        incentives_client.get_reward_token_balance(&invalid_token)
    }));
    
    assert!(balance_result.is_err(), "get_reward_token_balance must fail for non-existent token contract. Token: {:?}", invalid_token);
    
    let different_invalid_token = Address::generate(&env);
    let balance_result_2 = std::panic::catch_unwind(std::panic::AssertUnwindSafe(|| {
        incentives_client.get_reward_token_balance(&different_invalid_token)
    }));
    
    assert!(balance_result_2.is_err(), "get_reward_token_balance must fail for different non-existent token contract. Token: {:?}", different_invalid_token);
}

// ============================================================================
// REWARD ACCRUAL TESTS
// ============================================================================

#[test]
fn test_reward_accrual_over_time() {
    let env = Env::default();
    env.mock_all_auths();
    set_ledger_with_realistic_ttl(&env);
    
    let admin = Address::generate(&env);
    let emergency_admin = Address::generate(&env);
    let protocol = deploy_full_protocol(&env, &admin, &emergency_admin);
    
    let incentives_client = incentives::Client::new(&env, &protocol.incentives);
    
    // Create test asset (aToken address)
    let asset = Address::generate(&env);
    let reward_token = create_test_token(&env, &admin);
    let reward_token_addr = reward_token.address();
    
    let user = Address::generate(&env);
    let total_supply = 10_000_000_000_000u128; // 10,000 scaled units
    let user_balance = 1_000_000_000_000u128; // 1,000 scaled units (10% of supply)
    let emission_per_second = 100_000_000u128; // 100 tokens/second
    
    // Configure rewards
    incentives_client.configure_asset_rewards(
        &admin,
        &asset,
        &reward_token_addr,
        &0u32,
        &emission_per_second,
        &0u64,
    );
    
    // Initial handle_action sets user snapshot
    incentives_client.handle_action(&asset, &user, &total_supply, &user_balance, &0u32);
    
    let initial_data = incentives_client.get_user_reward_data(&asset, &reward_token_addr, &user, &0u32);
    assert_eq!(initial_data.accrued, 0, "Initial accrued should be 0");
    
    let initial_index = incentives_client.get_asset_reward_index(&asset, &reward_token_addr, &0u32);
    
    // Advance time by 1 hour
    advance_time_safe(&env, 3600);
    
    // Handle action to accrue rewards
    incentives_client.handle_action(&asset, &user, &total_supply, &user_balance, &0u32);
    
    let updated_index = incentives_client.get_asset_reward_index(&asset, &reward_token_addr, &0u32);
    let time_elapsed = updated_index.last_update_timestamp - initial_index.last_update_timestamp;
    
    let after_1h_data = incentives_client.get_user_reward_data(&asset, &reward_token_addr, &user, &0u32);
    
    assert!(time_elapsed > 0, "Time should have elapsed");
    assert!(updated_index.index > initial_index.index, "Index should update");
    assert!(after_1h_data.accrued > 0, "Rewards should accrue after time passes");
    
    // Expected: ~36 billion (emission * time * user_share)
    let expected_min = 30_000_000_000u128;
    assert!(after_1h_data.accrued >= expected_min, "Rewards too low: {}", after_1h_data.accrued);
    
    // Advance another hour and verify rewards double
    advance_time_safe(&env, 3600);
    incentives_client.handle_action(&asset, &user, &total_supply, &user_balance, &0u32);
    
    let after_2h_data = incentives_client.get_user_reward_data(&asset, &reward_token_addr, &user, &0u32);
    assert!(after_2h_data.accrued > after_1h_data.accrued, "Rewards should increase over time");
    
    let ratio = (after_2h_data.accrued as f64) / (after_1h_data.accrued as f64);
    assert!(ratio >= 1.8 && ratio <= 2.2, "Rewards should ~double. Ratio: {}", ratio);
}

#[test]
fn test_reward_accrual_proportional_to_balance() {
    let env = Env::default();
    env.mock_all_auths();
    set_ledger_with_realistic_ttl(&env);
    
    let admin = Address::generate(&env);
    let emergency_admin = Address::generate(&env);
    let protocol = deploy_full_protocol(&env, &admin, &emergency_admin);
    
    let incentives_client = incentives::Client::new(&env, &protocol.incentives);
    
    let asset = Address::generate(&env);
    let reward_token = create_test_token(&env, &admin);
    let reward_token_addr = reward_token.address();
    
    let user1 = Address::generate(&env);
    let user2 = Address::generate(&env);
    let total_supply = 10_000_000_000_000u128;
    let user1_balance = 2_000_000_000_000u128; // 20% of supply
    let user2_balance = 1_000_000_000_000u128; // 10% of supply
    let emission_per_second = 100_000_000u128;
    
    // Configure rewards
    incentives_client.configure_asset_rewards(
        &admin,
        &asset,
        &reward_token_addr,
        &0u32,
        &emission_per_second,
        &0u64,
    );
    
    // Both users start with balances
    incentives_client.handle_action(&asset, &user1, &total_supply, &user1_balance, &0u32);
    incentives_client.handle_action(&asset, &user2, &total_supply, &user2_balance, &0u32);
    
    // Advance time
    advance_time_safe(&env, 3600);
    
    // Update both users
    incentives_client.handle_action(&asset, &user1, &total_supply, &user1_balance, &0u32);
    incentives_client.handle_action(&asset, &user2, &total_supply, &user2_balance, &0u32);
    
    // User1 should have approximately double the rewards of user2 (2x balance)
    let user1_data = incentives_client.get_user_reward_data(&asset, &reward_token_addr, &user1, &0u32);
    let user2_data = incentives_client.get_user_reward_data(&asset, &reward_token_addr, &user2, &0u32);
    
    assert!(user1_data.accrued > user2_data.accrued, "User1 should have more rewards. User1: {}, User2: {}", user1_data.accrued, user2_data.accrued);
    
    let ratio = (user1_data.accrued as f64) / (user2_data.accrued as f64);
    assert!(ratio >= 1.8 && ratio <= 2.2, "User1 should have approximately 2x rewards. Ratio: {}", ratio);
}

// ============================================================================
// MULTIPLE REWARDS PER ASSET TESTS
// ============================================================================

#[test]
fn test_multiple_reward_tokens_per_asset() {
    let env = Env::default();
    env.mock_all_auths();
    set_ledger_with_realistic_ttl(&env);
    
    let admin = Address::generate(&env);
    let emergency_admin = Address::generate(&env);
    let protocol = deploy_full_protocol(&env, &admin, &emergency_admin);
    
    let incentives_client = incentives::Client::new(&env, &protocol.incentives);
    
    let asset = Address::generate(&env);
    let reward_token1 = create_test_token(&env, &admin);
    let reward_token2 = create_test_token(&env, &admin);
    let reward_token1_addr = reward_token1.address();
    let reward_token2_addr = reward_token2.address();
    
    let user = Address::generate(&env);
    let total_supply = 10_000_000_000_000u128;
    let user_balance = 1_000_000_000_000u128;
    
    // Configure two different reward tokens for the same asset
    incentives_client.configure_asset_rewards(
        &admin,
        &asset,
        &reward_token1_addr,
        &0u32,
        &100_000_000u128, // 100 tokens/second
        &0u64,
    );
    
    incentives_client.configure_asset_rewards(
        &admin,
        &asset,
        &reward_token2_addr,
        &0u32,
        &50_000_000u128, // 50 tokens/second
        &0u64,
    );
    
    // Verify both reward tokens are registered
    let reward_tokens = incentives_client.get_reward_tokens(&asset);
    assert_eq!(reward_tokens.len(), 2, "Should have 2 reward tokens");
    
    // User starts accruing
    incentives_client.handle_action(&asset, &user, &total_supply, &user_balance, &0u32);
    
    // Advance time
    advance_time_safe(&env, 3600);
    
    // Update rewards
    incentives_client.handle_action(&asset, &user, &total_supply, &user_balance, &0u32);
    
    // Verify user accrues both reward types
    let token1_data = incentives_client.get_user_reward_data(&asset, &reward_token1_addr, &user, &0u32);
    let token2_data = incentives_client.get_user_reward_data(&asset, &reward_token2_addr, &user, &0u32);
    
    assert!(token1_data.accrued > 0, "Token1 rewards should accrue. Got: {}", token1_data.accrued);
    assert!(token2_data.accrued > 0, "Token2 rewards should accrue. Got: {}", token2_data.accrued);
    
    // Token1 should have approximately 2x rewards (2x emission rate)
    let ratio = (token1_data.accrued as f64) / (token2_data.accrued as f64);
    assert!(ratio >= 1.8 && ratio <= 2.2, "Token1 should have approximately 2x rewards. Ratio: {}", ratio);
}

#[test]
fn test_supply_and_borrow_rewards_separate() {
    let env = Env::default();
    env.mock_all_auths();
    set_ledger_with_realistic_ttl(&env);
    
    let admin = Address::generate(&env);
    let emergency_admin = Address::generate(&env);
    let protocol = deploy_full_protocol(&env, &admin, &emergency_admin);
    
    let incentives_client = incentives::Client::new(&env, &protocol.incentives);
    
    let supply_asset = Address::generate(&env); // aToken
    let borrow_asset = Address::generate(&env); // debtToken
    let reward_token = create_test_token(&env, &admin);
    let reward_token_addr = reward_token.address();
    
    let user = Address::generate(&env);
    let supply_total = 10_000_000_000_000u128;
    let supply_balance = 1_000_000_000_000u128;
    let borrow_total = 5_000_000_000_000u128;
    let borrow_balance = 500_000_000_000u128;
    
    // Configure supply rewards
    incentives_client.configure_asset_rewards(
        &admin,
        &supply_asset,
        &reward_token_addr,
        &0u32, // supply
        &100_000_000u128,
        &0u64,
    );
    
    // Configure borrow rewards
    incentives_client.configure_asset_rewards(
        &admin,
        &borrow_asset,
        &reward_token_addr,
        &1u32, // borrow
        &50_000_000u128,
        &0u64,
    );
    
    // User supplies and borrows
    incentives_client.handle_action(&supply_asset, &user, &supply_total, &supply_balance, &0u32);
    incentives_client.handle_action(&borrow_asset, &user, &borrow_total, &borrow_balance, &1u32);
    
    // Advance time with TTL extension (simulates production)
    let _ = incentives_client.get_user_reward_data(&supply_asset, &reward_token_addr, &user, &0u32);
    let _ = incentives_client.get_user_reward_data(&borrow_asset, &reward_token_addr, &user, &1u32);
    advance_time_safe(&env, 3600);
    
    // Update both positions
    incentives_client.handle_action(&supply_asset, &user, &supply_total, &supply_balance, &0u32);
    incentives_client.handle_action(&borrow_asset, &user, &borrow_total, &borrow_balance, &1u32);
    
    // Verify separate accrual
    let supply_data = incentives_client.get_user_reward_data(&supply_asset, &reward_token_addr, &user, &0u32);
    let borrow_data = incentives_client.get_user_reward_data(&borrow_asset, &reward_token_addr, &user, &1u32);
    
    assert!(supply_data.accrued > 0, "Supply rewards should accrue. Got: {}", supply_data.accrued);
    assert!(borrow_data.accrued > 0, "Borrow rewards should accrue. Got: {}", borrow_data.accrued);
    
    // Supply should have more rewards (higher emission rate and balance)
    assert!(supply_data.accrued > borrow_data.accrued, "Supply rewards should exceed borrow rewards");
}

// ============================================================================
// CLAIMING REWARDS TESTS
// ============================================================================

#[test]
fn test_claim_rewards() {
    let env = Env::default();
    env.mock_all_auths();
    set_ledger_with_realistic_ttl(&env);
    
    let admin = Address::generate(&env);
    let emergency_admin = Address::generate(&env);
    let protocol = deploy_full_protocol(&env, &admin, &emergency_admin);
    
    let incentives_client = incentives::Client::new(&env, &protocol.incentives);
    
    let asset = Address::generate(&env);
    let reward_token = create_test_token(&env, &admin);
    let reward_token_addr = reward_token.address();
    let reward_token_client = token::Client::new(&env, &reward_token_addr);
    
    let user = Address::generate(&env);
    let recipient = Address::generate(&env);
    let total_supply = 10_000_000_000_000u128;
    let user_balance = 1_000_000_000_000u128;
    let emission_per_second = 100_000_000u128;
    
    // Configure rewards
    incentives_client.configure_asset_rewards(
        &admin,
        &asset,
        &reward_token_addr,
        &0u32,
        &emission_per_second,
        &0u64,
    );
    
    // User accrues rewards
    incentives_client.handle_action(&asset, &user, &total_supply, &user_balance, &0u32);
    let _ = incentives_client.get_assets();
    advance_time_safe(&env, 3600);
    incentives_client.handle_action(&asset, &user, &total_supply, &user_balance, &0u32);
    
    // Verify rewards accrued
    let before_claim = incentives_client.get_user_accrued_rewards(&asset, &reward_token_addr, &user, &0u32);
    assert!(before_claim > 0, "Should have accrued rewards. Got: {}", before_claim);
    
    // Fund contract with reward tokens
    let reward_token_sac = token::StellarAssetClient::new(&env, &reward_token_addr);
    reward_token_sac.mint(&admin, &(before_claim as i128 * 2)); // Mint enough
    reward_token_client.transfer(&admin, &protocol.incentives, &(before_claim as i128 * 2));
    
    // Claim rewards
    let mut assets = Vec::new(&env);
    assets.push_back(asset.clone());
    let claimed = incentives_client.claim_rewards(&user, &assets, &reward_token_addr, &0u128, &recipient);
    
    assert_eq!(claimed, before_claim, "Should claim all accrued rewards. Expected: {}, Got: {}", before_claim, claimed);
    
    // Verify rewards reset
    let after_claim = incentives_client.get_user_accrued_rewards(&asset, &reward_token_addr, &user, &0u32);
    assert_eq!(after_claim, 0, "Accrued rewards should be reset after claim. Got: {}", after_claim);
    
    // Verify recipient received tokens
    let recipient_balance = reward_token_client.balance(&recipient);
    assert_eq!(recipient_balance, before_claim as i128, "Recipient should receive rewards. Expected: {}, Got: {}", before_claim, recipient_balance);
}

#[test]
fn test_claim_partial_rewards() {
    let env = Env::default();
    env.mock_all_auths();
    set_ledger_with_realistic_ttl(&env);
    
    let admin = Address::generate(&env);
    let emergency_admin = Address::generate(&env);
    let protocol = deploy_full_protocol(&env, &admin, &emergency_admin);
    
    let incentives_client = incentives::Client::new(&env, &protocol.incentives);
    
    let asset = Address::generate(&env);
    let reward_token = create_test_token(&env, &admin);
    let reward_token_addr = reward_token.address();
    let reward_token_client = token::Client::new(&env, &reward_token_addr);
    
    let user = Address::generate(&env);
    let recipient = Address::generate(&env);
    let total_supply = 10_000_000_000_000u128;
    let user_balance = 1_000_000_000_000u128;
    
    // Configure rewards
    incentives_client.configure_asset_rewards(
        &admin,
        &asset,
        &reward_token_addr,
        &0u32,
        &100_000_000u128,
        &0u64,
    );
    
    // Accrue rewards
    incentives_client.handle_action(&asset, &user, &total_supply, &user_balance, &0u32);
    let _ = incentives_client.get_assets();
    advance_time_safe(&env, 3600);
    incentives_client.handle_action(&asset, &user, &total_supply, &user_balance, &0u32);
    
    let total_accrued = incentives_client.get_user_accrued_rewards(&asset, &reward_token_addr, &user, &0u32);
    assert!(total_accrued > 0);
    
    // Fund contract
    let reward_token_sac = token::StellarAssetClient::new(&env, &reward_token_addr);
    reward_token_sac.mint(&admin, &(total_accrued as i128));
    reward_token_client.transfer(&admin, &protocol.incentives, &(total_accrued as i128));
    
    // Claim partial amount (50%)
    let claim_amount = total_accrued / 2;
    let mut assets = Vec::new(&env);
    assets.push_back(asset.clone());
    let claimed = incentives_client.claim_rewards(&user, &assets, &reward_token_addr, &claim_amount, &recipient);
    
    assert_eq!(claimed, claim_amount, "Should claim requested amount. Expected: {}, Got: {}", claim_amount, claimed);
    
    // Verify remaining rewards
    let remaining = incentives_client.get_user_accrued_rewards(&asset, &reward_token_addr, &user, &0u32);
    assert_eq!(remaining, total_accrued - claim_amount, "Should have remaining rewards. Expected: {}, Got: {}", total_accrued - claim_amount, remaining);
}

#[test]
fn test_claim_all_rewards_multiple_assets() {
    let env = Env::default();
    env.mock_all_auths();
    set_ledger_with_realistic_ttl(&env);
    
    let admin = Address::generate(&env);
    let emergency_admin = Address::generate(&env);
    let protocol = deploy_full_protocol(&env, &admin, &emergency_admin);
    
    let incentives_client = incentives::Client::new(&env, &protocol.incentives);
    
    let asset1 = Address::generate(&env);
    let asset2 = Address::generate(&env);
    let reward_token = create_test_token(&env, &admin);
    let reward_token_addr = reward_token.address();
    let reward_token_client = token::Client::new(&env, &reward_token_addr);
    
    let user = Address::generate(&env);
    let recipient = Address::generate(&env);
    let total_supply = 10_000_000_000_000u128;
    let user_balance = 1_000_000_000_000u128;
    
    // Configure rewards for both assets
    incentives_client.configure_asset_rewards(
        &admin,
        &asset1,
        &reward_token_addr,
        &0u32,
        &100_000_000u128,
        &0u64,
    );
    
    incentives_client.configure_asset_rewards(
        &admin,
        &asset2,
        &reward_token_addr,
        &0u32,
        &100_000_000u128,
        &0u64,
    );
    
    // Accrue rewards on both assets
    incentives_client.handle_action(&asset1, &user, &total_supply, &user_balance, &0u32);
    incentives_client.handle_action(&asset2, &user, &total_supply, &user_balance, &0u32);
    // Advance time with TTL extension (simulates production)
    let _ = incentives_client.get_user_reward_data(&asset1, &reward_token_addr, &user, &0u32);
    let _ = incentives_client.get_user_reward_data(&asset2, &reward_token_addr, &user, &0u32);
    advance_time_safe(&env, 3600);
    incentives_client.handle_action(&asset1, &user, &total_supply, &user_balance, &0u32);
    incentives_client.handle_action(&asset2, &user, &total_supply, &user_balance, &0u32);
    
    let asset1_rewards = incentives_client.get_user_accrued_rewards(&asset1, &reward_token_addr, &user, &0u32);
    let asset2_rewards = incentives_client.get_user_accrued_rewards(&asset2, &reward_token_addr, &user, &0u32);
    let total_rewards = asset1_rewards + asset2_rewards;
    
    // Fund contract
    let reward_token_sac = token::StellarAssetClient::new(&env, &reward_token_addr);
    reward_token_sac.mint(&admin, &(total_rewards as i128));
    reward_token_client.transfer(&admin, &protocol.incentives, &(total_rewards as i128));
    
    // Claim all rewards
    let mut assets = Vec::new(&env);
    assets.push_back(asset1.clone());
    assets.push_back(asset2.clone());
    incentives_client.claim_all_rewards(&user, &assets, &recipient);
    
    // Verify all rewards claimed
    let remaining1 = incentives_client.get_user_accrued_rewards(&asset1, &reward_token_addr, &user, &0u32);
    let remaining2 = incentives_client.get_user_accrued_rewards(&asset2, &reward_token_addr, &user, &0u32);
    
    assert_eq!(remaining1, 0, "Asset1 rewards should be claimed");
    assert_eq!(remaining2, 0, "Asset2 rewards should be claimed");
    
    // Verify recipient received all rewards
    let recipient_balance = reward_token_client.balance(&recipient);
    assert_eq!(recipient_balance, total_rewards as i128, "Recipient should receive all rewards");
}

// ============================================================================
// REWARD DISTRIBUTION TESTS
// ============================================================================

#[test]
fn test_reward_distribution_multiple_users() {
    let env = Env::default();
    env.mock_all_auths();
    set_ledger_with_realistic_ttl(&env);
    
    let admin = Address::generate(&env);
    let emergency_admin = Address::generate(&env);
    let protocol = deploy_full_protocol(&env, &admin, &emergency_admin);
    
    let incentives_client = incentives::Client::new(&env, &protocol.incentives);
    
    let asset = Address::generate(&env);
    let reward_token = create_test_token(&env, &admin);
    let reward_token_addr = reward_token.address();
    
    let user1 = Address::generate(&env);
    let user2 = Address::generate(&env);
    let user3 = Address::generate(&env);
    let total_supply = 10_000_000_000_000u128;
    
    // Configure rewards
    incentives_client.configure_asset_rewards(
        &admin,
        &asset,
        &reward_token_addr,
        &0u32,
        &100_000_000u128,
        &0u64,
    );
    
    // Users have different balances
    let user1_balance = 3_000_000_000_000u128; // 30%
    let user2_balance = 2_000_000_000_000u128; // 20%
    let user3_balance = 1_000_000_000_000u128; // 10%
    
    // All users start accruing
    incentives_client.handle_action(&asset, &user1, &total_supply, &user1_balance, &0u32);
    incentives_client.handle_action(&asset, &user2, &total_supply, &user2_balance, &0u32);
    incentives_client.handle_action(&asset, &user3, &total_supply, &user3_balance, &0u32);
    
    // Advance time
    advance_time_safe(&env, 3600);
    
    // Update all users
    incentives_client.handle_action(&asset, &user1, &total_supply, &user1_balance, &0u32);
    incentives_client.handle_action(&asset, &user2, &total_supply, &user2_balance, &0u32);
    incentives_client.handle_action(&asset, &user3, &total_supply, &user3_balance, &0u32);
    
    // Verify proportional distribution
    let user1_rewards = incentives_client.get_user_accrued_rewards(&asset, &reward_token_addr, &user1, &0u32);
    let user2_rewards = incentives_client.get_user_accrued_rewards(&asset, &reward_token_addr, &user2, &0u32);
    let user3_rewards = incentives_client.get_user_accrued_rewards(&asset, &reward_token_addr, &user3, &0u32);
    
    assert!(user1_rewards > user2_rewards, "User1 should have more rewards than User2");
    assert!(user2_rewards > user3_rewards, "User2 should have more rewards than User3");
    
    // Ratios should match balance ratios
    let ratio_1_2 = (user1_rewards as f64) / (user2_rewards as f64);
    let ratio_2_3 = (user2_rewards as f64) / (user3_rewards as f64);
    
    // User1:User2 should be ~1.5:1 (3:2 balance ratio)
    assert!(ratio_1_2 >= 1.3 && ratio_1_2 <= 1.7, "User1:User2 ratio should be ~1.5. Got: {}", ratio_1_2);
    // User2:User3 should be ~2:1 (2:1 balance ratio)
    assert!(ratio_2_3 >= 1.8 && ratio_2_3 <= 2.2, "User2:User3 ratio should be ~2.0. Got: {}", ratio_2_3);
}

#[test]
fn test_reward_distribution_after_balance_changes() {
    let env = Env::default();
    env.mock_all_auths();
    set_ledger_with_realistic_ttl(&env);
    
    let admin = Address::generate(&env);
    let emergency_admin = Address::generate(&env);
    let protocol = deploy_full_protocol(&env, &admin, &emergency_admin);
    
    let incentives_client = incentives::Client::new(&env, &protocol.incentives);
    
    let asset = Address::generate(&env);
    let reward_token = create_test_token(&env, &admin);
    let reward_token_addr = reward_token.address();
    
    let user = Address::generate(&env);
    let total_supply = 10_000_000_000_000u128;
    let initial_balance = 1_000_000_000_000u128; // 10%
    
    // Configure rewards
    incentives_client.configure_asset_rewards(
        &admin,
        &asset,
        &reward_token_addr,
        &0u32,
        &100_000_000u128,
        &0u64,
    );
    
    // User starts with balance
    incentives_client.handle_action(&asset, &user, &total_supply, &initial_balance, &0u32);
    
    // Period 1: Accrue rewards with initial balance
    advance_time_safe(&env, 1800); // 30 minutes
    incentives_client.handle_action(&asset, &user, &total_supply, &initial_balance, &0u32);
    
    let rewards_period1 = incentives_client.get_user_accrued_rewards(&asset, &reward_token_addr, &user, &0u32);
    
    // User increases balance to 20% - snapshot is now updated
    let increased_balance = 2_000_000_000_000u128;
    incentives_client.handle_action(&asset, &user, &total_supply, &increased_balance, &0u32);
    
    // Period 2: Accrue rewards with new (higher) balance
    advance_time_safe(&env, 1800); // Another 30 minutes  
    incentives_client.handle_action(&asset, &user, &total_supply, &increased_balance, &0u32);
    
    let rewards_total = incentives_client.get_user_accrued_rewards(&asset, &reward_token_addr, &user, &0u32);
    let rewards_period2 = rewards_total - rewards_period1;
    
    // Period 2 should have approximately 2x rewards due to 2x balance
    // (Anti-flash-loan uses min(old, new), but since balance unchanged in period2, it uses full balance)
    let ratio = (rewards_period2 as f64) / (rewards_period1 as f64);
    assert!(ratio >= 1.8 && ratio <= 2.2, 
        "Period 2 should have ~2x rewards (2x balance). Got ratio: {}, P1: {}, P2: {}", 
        ratio, rewards_period1, rewards_period2);
}

#[test]
fn test_tokens_get_incentives_contract_on_deploy_and_init() {
    let env = Env::default();
    env.mock_all_auths_allowing_non_root_auth();
    set_ledger_with_realistic_ttl(&env);
    
    let admin = Address::generate(&env);
    let emergency_admin = Address::generate(&env);
    
    // Setup: Deploy protocol components manually so we can initialize pool WITH incentives
    use crate::{price_oracle, treasury};
    
    // 1. Deploy core contracts
    let price_oracle_id = env.register(price_oracle::WASM, ());
    let price_oracle_client = price_oracle::Client::new(&env, &price_oracle_id);
    let reflector_stub = env.register(ReflectorStub, ());
    price_oracle_client.initialize(&admin, &reflector_stub, &Address::generate(&env), &Address::generate(&env));
    
    let treasury_id = env.register(treasury::WASM, ());
    let treasury_client = treasury::Client::new(&env, &treasury_id);
    treasury_client.initialize(&admin);
    
    let mock_dex_router = Address::generate(&env); // Mock DEX router
    
    // 2. Deploy incentives BEFORE pool initialization
    let incentives_id = env.register(incentives::WASM, ());
    
    // 3. Deploy and initialize pool WITH incentives
    let kinetic_router_id = env.register(kinetic_router::WASM, ());
    let kinetic_router_client = kinetic_router::Client::new(&env, &kinetic_router_id);
    kinetic_router_client.initialize(
        &admin,
        &emergency_admin,
        &price_oracle_id,
        &treasury_id,
        &mock_dex_router,
        &Some(incentives_id.clone()), // Set incentives during initialization
    );
    
    // Initialize incentives contract
    let incentives_client = incentives::Client::new(&env, &incentives_id);
    incentives_client.initialize(&admin, &kinetic_router_id);
    
    // Verify pool has incentives contract set
    let pool_incentives = kinetic_router_client.get_incentives_contract();
    assert!(pool_incentives.is_some(), "Pool should have incentives contract set");
    assert_eq!(pool_incentives.unwrap(), incentives_id, "Incentives address should match");
    
    // 4. Deploy pool configurator
    let pool_configurator_id = env.register(pool_configurator::WASM, ());
    let pool_configurator_client = pool_configurator::Client::new(&env, &pool_configurator_id);
    pool_configurator_client.initialize(&admin, &kinetic_router_id, &price_oracle_id);
    
    let mut set_config_args = Vec::new(&env);
    set_config_args.push_back(pool_configurator_id.clone().into_val(&env));
    let _: Result<(), KineticRouterError> = env.invoke_contract(
        &kinetic_router_id,
        &Symbol::new(&env, "set_pool_configurator"),
        set_config_args,
    );
    
    // 5. Set WASM hashes - upload WASM and get their hashes
    let a_token_wasm_bytes = Bytes::from_slice(&env, a_token::WASM);
    let debt_token_wasm_bytes = Bytes::from_slice(&env, debt_token::WASM);
    let a_token_hash = env.deployer().upload_contract_wasm(a_token_wasm_bytes);
    let debt_token_hash = env.deployer().upload_contract_wasm(debt_token_wasm_bytes);
    pool_configurator_client.set_a_token_wasm_hash(&admin, &a_token_hash);
    pool_configurator_client.set_debt_token_wasm_hash(&admin, &debt_token_hash);
    
    // 6. Create underlying asset
    let underlying_asset_sac = create_test_token(&env, &admin);
    let underlying_asset = underlying_asset_sac.address();
    
    // 7. Deploy interest rate strategy
    let interest_rate_strategy_id = env.register(interest_rate_strategy::WASM, ());
    let interest_rate_strategy_client = interest_rate_strategy::Client::new(&env, &interest_rate_strategy_id);
    interest_rate_strategy_client.initialize(
        &admin,
        &0u128,
        &80000000000000000000000000u128,
        &200000000000000000000000000u128,
        &800000000000000000000000000u128,
    );
    
    // 8. Deploy and initialize reserve - this should set incentives on tokens
    use pool_configurator::InitReserveParams as PoolConfiguratorParams;
    let params = PoolConfiguratorParams {
        decimals: 7,
        ltv: 8000,
        liquidation_threshold: 8500,
        liquidation_bonus: 500,
        reserve_factor: 1000,
        supply_cap: 1_000_000_000_000_000,
        borrow_cap: 500_000_000_000_000,
        borrowing_enabled: true,
        flashloan_enabled: true,
    };
    let (a_token_addr, debt_token_addr) = pool_configurator_client.deploy_and_init_reserve(
        &admin,
        &underlying_asset,
        &interest_rate_strategy_id,
        &treasury_id,
        &String::from_str(&env, "Test aToken"),
        &String::from_str(&env, "aTEST"),
        &String::from_str(&env, "Test Debt Token"),
        &String::from_str(&env, "dTEST"),
        &params,
    );
    
    // 9. Verify tokens were deployed successfully
    let zero_addr = Address::from_string(&String::from_str(&env, "GAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAWHF"));
    assert_ne!(a_token_addr, zero_addr, "a-token should be deployed");
    assert_ne!(debt_token_addr, zero_addr, "debt-token should be deployed");
    
    // 10. STRONG ASSERTION: Directly verify incentives contract is set on a-token
    let a_token_incentives: Option<Address> = env.invoke_contract(
        &a_token_addr,
        &soroban_sdk::Symbol::new(&env, "get_incentives_contract"),
        soroban_sdk::Vec::new(&env),
    );
    assert!(
        a_token_incentives.is_some(),
        "a-token MUST have incentives contract set after deploy_and_init_reserve"
    );
    let a_token_incentives_addr = a_token_incentives.unwrap();
    assert_eq!(
        a_token_incentives_addr,
        incentives_id,
        "a-token incentives contract MUST match pool's incentives contract. Expected: {:?}, Got: {:?}",
        incentives_id,
        a_token_incentives_addr
    );
    
    // 11. STRONG ASSERTION: Directly verify incentives contract is set on debt-token
    let debt_token_incentives: Option<Address> = env.invoke_contract(
        &debt_token_addr,
        &soroban_sdk::Symbol::new(&env, "get_incentives_contract"),
        soroban_sdk::Vec::new(&env),
    );
    assert!(
        debt_token_incentives.is_some(),
        "debt-token MUST have incentives contract set after deploy_and_init_reserve"
    );
    let debt_token_incentives_addr = debt_token_incentives.unwrap();
    assert_eq!(
        debt_token_incentives_addr,
        incentives_id,
        "debt-token incentives contract MUST match pool's incentives contract. Expected: {:?}, Got: {:?}",
        incentives_id,
        debt_token_incentives_addr
    );
    
    // 12. STRONG ASSERTION: Verify both tokens have the SAME incentives contract
    assert_eq!(
        a_token_incentives_addr,
        debt_token_incentives_addr,
        "Both tokens MUST have the same incentives contract address. a-token: {:?}, debt-token: {:?}",
        a_token_incentives_addr,
        debt_token_incentives_addr
    );
    
    // 13. STRONG ASSERTION: Verify incentives contract matches pool's stored value
    let pool_incentives_after = kinetic_router_client.get_incentives_contract();
    assert_eq!(
        pool_incentives_after,
        Some(incentives_id.clone()),
        "Pool MUST still have incentives contract set. Expected: {:?}, Got: {:?}",
        incentives_id,
        pool_incentives_after
    );
    let pool_incentives_addr = pool_incentives_after.unwrap();
    assert_eq!(
        a_token_incentives_addr,
        pool_incentives_addr,
        "a-token incentives MUST match pool's current incentives contract. a-token: {:?}, pool: {:?}",
        a_token_incentives_addr,
        pool_incentives_addr
    );
    assert_eq!(
        debt_token_incentives_addr,
        pool_incentives_addr,
        "debt-token incentives MUST match pool's current incentives contract. debt-token: {:?}, pool: {:?}",
        debt_token_incentives_addr,
        pool_incentives_addr
    );
}
