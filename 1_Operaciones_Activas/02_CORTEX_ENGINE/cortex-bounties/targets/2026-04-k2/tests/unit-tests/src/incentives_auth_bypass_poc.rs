#![cfg(test)]
#![allow(unused_imports)]

#[cfg(test)]
extern crate std;

use crate::incentives;
use k2_shared::RAY;
use soroban_sdk::{
    contract, contractimpl, symbol_short,
    testutils::{Address as _, Ledger, LedgerInfo, MockAuth, MockAuthInvoke},
    Address, Env, IntoVal,
};

#[contract]
pub struct MockRewardToken;

#[contractimpl]
impl MockRewardToken {
    pub fn mint(env: Env, to: Address, amount: i128) {
        let key = (symbol_short!("bal"), to.clone());
        let cur: i128 = env
            .storage()
            .temporary()
            .get(&key)
            .unwrap_or(0);
        env.storage().temporary().set(&key, &(cur + amount));
    }

    pub fn transfer(env: Env, from: Address, to: Address, amount: i128) {
        from.require_auth();
        let from_key = (symbol_short!("bal"), from.clone());
        let to_key = (symbol_short!("bal"), to.clone());

        let from_bal: i128 = env
            .storage()
            .temporary()
            .get(&from_key)
            .unwrap_or(0);
        if from_bal < amount {
            panic!("insufficient");
        }
        env.storage().temporary().set(&from_key, &(from_bal - amount));

        let to_bal: i128 = env
            .storage()
            .temporary()
            .get(&to_key)
            .unwrap_or(0);
        env.storage().temporary().set(&to_key, &(to_bal + amount));
    }

    pub fn balance_of(env: Env, owner: Address) -> i128 {
        let key = (symbol_short!("bal"), owner);
        env.storage().temporary().get(&key).unwrap_or(0)
    }
}

fn set_timestamp(env: &Env, timestamp: u64) {
    env.ledger().set(LedgerInfo {
        protocol_version: 23,
        sequence_number: 1,
        timestamp,
        network_id: Default::default(),
        base_reserve: 0,
        min_temp_entry_ttl: 0,
        min_persistent_entry_ttl: 0,
        max_entry_ttl: 1_000_000,
    });
}

/// Test helper to create a test environment WITHOUT mock_all_auths
/// This is important for testing authentication requirements
fn create_test_env_no_mock_auths() -> Env {
    let env = Env::default();
    env
}

/// Test helper to initialize the incentives contract
fn initialize_contract(env: &Env, emission_manager: &Address, lending_pool: &Address) -> Address {
    let contract_id = env.register(incentives::WASM, ());
    let client = incentives::Client::new(env, &contract_id);

    // Mock auth for initialization
    env.mock_auths(&[MockAuth {
        address: emission_manager,
        invoke: &MockAuthInvoke {
            contract: &contract_id,
            fn_name: "initialize",
            args: (emission_manager.clone(), lending_pool.clone()).into_val(env),
            sub_invokes: &[],
        },
    }]);

    client.initialize(emission_manager, lending_pool);

    contract_id
}

/// PoC Test: Verifies that FIND-019 vulnerability is fixed
/// 
/// This test demonstrates that the authentication fix prevents unauthorized
/// reward accrual. An attacker cannot call handle_action with forged balances
/// because token_address.require_auth() enforces that only the token contract
/// itself can authenticate the call.
#[test]
#[should_panic(expected = "Error(Auth")]
fn incentives_handle_action_prevents_unauthenticated_spoof() {
    let env = create_test_env_no_mock_auths();

    // Addresses
    let emission_manager = Address::generate(&env);
    let lending_pool = Address::generate(&env);
    let attacker = Address::generate(&env);
    let token = Address::generate(&env); // supposed aToken/debtToken
    // Deploy a mock reward token and fund the incentives contract so claims succeed
    let reward_token_id = env.register(MockRewardToken, ());
    let reward_token = reward_token_id.clone();

    // Deploy incentives
    let incentives_id = initialize_contract(&env, &emission_manager, &lending_pool);
    let incentives = incentives::Client::new(&env, &incentives_id);

    // Configure rewards (requires emission_manager auth)
    env.mock_auths(&[MockAuth {
        address: &emission_manager,
        invoke: &MockAuthInvoke {
            contract: &incentives_id,
            fn_name: "configure_asset_rewards",
            args: (
                emission_manager.clone(),
                token.clone(),
                reward_token.clone(),
                0u32,            // supply reward type
                1_000_000u128,   // emission_per_second
                0u64,            // distribution_end
            )
                .into_val(&env),
            sub_invokes: &[],
        },
    }]);
    incentives.configure_asset_rewards(
        &emission_manager,
        &token,
        &reward_token,
        &0u32,
        &1_000_000u128,
        &0u64,
    );

    // Advance time so index accrues
    set_timestamp(&env, 100);

    // Fund incentives contract with reward tokens so claim_rewards can transfer out
    // Fund with plenty of reward tokens so the forged accrual could be claimed if attack succeeded
    let incentives_reward_balance: i128 = 1_000_000_000_000_000_000_000; // 1e21
    let reward_client = MockRewardTokenClient::new(&env, &reward_token_id);
    reward_client.mint(&incentives_id, &incentives_reward_balance);

    // === Attack Attempt ===
    // Attacker tries to call handle_action with forged supply/balance
    // This should FAIL because token_address.require_auth() enforces authentication
    // The token contract must authenticate itself - attacker cannot forge this
    
    // Choose balances that would drain full incentives_reward_balance if attack succeeded:
    // accrued = emission_per_second * time_elapsed * user_balance / total_supply
    // Solve user_balance = incentives_reward_balance / (emission_per_second * time_elapsed)
    // With emission_per_second=1_000_000, time_elapsed=100, total_supply=1:
    // user_balance = 1e21 / 1e8 = 1e13
    let forged_total_supply = 1u128; // smallest to maximize accrual
    let forged_user_balance = 10_000_000_000_000u128; // 1e13
    
    // Attempt to call handle_action WITHOUT token authentication
    // This should panic with Auth error because token_address.require_auth() fails
    // The attacker cannot authenticate as the token contract
    incentives.handle_action(
        &token,
        &attacker,
        &forged_total_supply,
        &forged_user_balance,
        &0u32,
    );
    
    // If we reach here, the attack succeeded (which should not happen)
    // The test should panic before reaching this point
    panic!("Authentication bypass succeeded - vulnerability not fixed!");
}

/// Test: Verifies that legitimate token contract CAN call handle_action
/// 
/// This test ensures that the fix doesn't break legitimate functionality.
/// When a token contract authenticates itself, handle_action should succeed.
#[test]
fn incentives_handle_action_allows_authenticated_token() {
    let env = create_test_env_no_mock_auths();

    // Addresses
    let emission_manager = Address::generate(&env);
    let lending_pool = Address::generate(&env);
    let user = Address::generate(&env);
    let token = Address::generate(&env); // aToken/debtToken contract
    
    // Deploy incentives
    let incentives_id = initialize_contract(&env, &emission_manager, &lending_pool);
    let incentives = incentives::Client::new(&env, &incentives_id);

    let reward_token = Address::generate(&env);

    // Configure rewards
    env.mock_auths(&[MockAuth {
        address: &emission_manager,
        invoke: &MockAuthInvoke {
            contract: &incentives_id,
            fn_name: "configure_asset_rewards",
            args: (
                emission_manager.clone(),
                token.clone(),
                reward_token.clone(),
                0u32,
                1_000_000u128,
                0u64,
            )
                .into_val(&env),
            sub_invokes: &[],
        },
    }]);
    incentives.configure_asset_rewards(
        &emission_manager,
        &token,
        &reward_token,
        &0u32,
        &1_000_000u128,
        &0u64,
    );

    set_timestamp(&env, 100);

    // First call: Set initial balance snapshot (no rewards accrued yet due to flash-loan protection)
    env.mock_auths(&[MockAuth {
        address: &token,
        invoke: &MockAuthInvoke {
            contract: &incentives_id,
            fn_name: "handle_action",
            args: (
                token.clone(),
                user.clone(),
                10_000_000_000_000u128, // total_supply
                1_000_000_000_000u128,  // user_balance
                0u32,
            )
                .into_val(&env),
            sub_invokes: &[],
        },
    }]);

    incentives.handle_action(
        &token,
        &user,
        &10_000_000_000_000u128,
        &1_000_000_000_000u128,
        &0u32,
    );

    // Advance time to accrue rewards
    set_timestamp(&env, 200);

    // Second call: Now rewards will accrue because balance_snapshot is set
    env.mock_auths(&[MockAuth {
        address: &token,
        invoke: &MockAuthInvoke {
            contract: &incentives_id,
            fn_name: "handle_action",
            args: (
                token.clone(),
                user.clone(),
                10_000_000_000_000u128, // total_supply
                1_000_000_000_000u128,  // user_balance
                0u32,
            )
                .into_val(&env),
            sub_invokes: &[],
        },
    }]);

    // This should succeed because token authenticates itself
    incentives.handle_action(
        &token,
        &user,
        &10_000_000_000_000u128,
        &1_000_000_000_000u128,
        &0u32,
    );

    // Verify rewards were accrued correctly
    let user_data = incentives.get_user_reward_data(&token, &reward_token, &user, &0u32);
    assert!(user_data.accrued > 0, "User should have accrued rewards");
    
    // Verify index was updated
    let index = incentives.get_asset_reward_index(&token, &reward_token, &0u32);
    assert!(index.index > RAY, "Reward index should have increased");
}
