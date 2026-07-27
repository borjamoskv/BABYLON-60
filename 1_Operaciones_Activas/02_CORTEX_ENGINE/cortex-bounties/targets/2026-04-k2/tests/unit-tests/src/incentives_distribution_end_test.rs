#![cfg(test)]

use crate::incentives;
use k2_shared::RAY;
use soroban_sdk::{
    testutils::{Address as _, Ledger, LedgerInfo},
    Address, Env,
};

fn create_test_env() -> Env {
    let env = Env::default();
    env.mock_all_auths();
    env
}

fn set_timestamp(env: &Env, timestamp: u64) {
    env.ledger().set(LedgerInfo {
        timestamp,
        protocol_version: 23,
        sequence_number: 0,
        network_id: Default::default(),
        base_reserve: 0,
        min_temp_entry_ttl: 0,
        min_persistent_entry_ttl: 0,
        max_entry_ttl: 1_000_000,
    });
}

#[test]
fn test_distribution_end_accrues_final_interval() {
    let env = create_test_env();

    let emission_manager = Address::generate(&env);
    let lending_pool = Address::generate(&env);
    let token = Address::generate(&env);
    let reward_token = Address::generate(&env);

    // Register and initialize contract
    let contract_id = env.register(incentives::WASM, ());
    let client = incentives::Client::new(&env, &contract_id);
    client.initialize(&emission_manager, &lending_pool);

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

#[test]
fn test_distribution_end_partial_interval() {
    let env = create_test_env();

    let emission_manager = Address::generate(&env);
    let lending_pool = Address::generate(&env);
    let token = Address::generate(&env);
    let reward_token = Address::generate(&env);

    // Register and initialize contract
    let contract_id = env.register(incentives::WASM, ());
    let client = incentives::Client::new(&env, &contract_id);
    client.initialize(&emission_manager, &lending_pool);

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

    // First update at t=50
    set_timestamp(&env, 50);
    client.handle_action(
        &token,
        &Address::generate(&env),
        &total_supply,
        &0u128,
        &0u32,
    );

    let mid = client.get_asset_reward_index(&token, &reward_token, &0u32);
    let expected_mid_increment = 500_000 * RAY; // 50 seconds * 1_000_000 / 100
    assert_eq!(mid.index, RAY + expected_mid_increment);
    assert_eq!(mid.last_update_timestamp, 50);

    // Second update past distribution_end at t=150
    // Should accrue for 50..100 only (50 more seconds)
    set_timestamp(&env, 150);
    client.handle_action(
        &token,
        &Address::generate(&env),
        &total_supply,
        &0u128,
        &0u32,
    );

    let after = client.get_asset_reward_index(&token, &reward_token, &0u32);
    let additional_increment = 500_000 * RAY; // 50 more seconds
    let expected_final = RAY + expected_mid_increment + additional_increment;
    
    assert_eq!(
        after.index, expected_final,
        "index should accrue for partial interval up to distribution_end"
    );
    assert_eq!(
        after.last_update_timestamp, 150,
        "timestamp should update to current time"
    );
}
