#![cfg(test)]

// Tests the upgrade flow for the price oracle contract.
// These tests show how admin-controlled upgrades work and confirm
// the oracle keeps its asset whitelist after code changes.
//
// The price oracle is upgradeable because price feed logic may need updates.
// Upgrades let us fix bugs without losing configured assets or prices.

use crate::price_oracle;
use crate::price_oracle_test::{create_test_addresses, create_test_env, initialize_oracle};
use soroban_sdk::{testutils::Address as _, Address};

const PRICE_ORACLE_WASM: &[u8] = include_bytes!("../../../target/wasm32v1-none/release/k2_price_oracle.optimized.wasm");

// Verifies that the admin can upgrade the contract with new WASM.
// This is the core upgrade operation for the oracle.
#[test]
fn test_upgrade_success() {
    let env = create_test_env();
    let (admin, _user1, _user2) = create_test_addresses(&env);

    let oracle = initialize_oracle(&env, &admin);
    let client = price_oracle::Client::new(&env, &oracle);

    let version_before = client.version();
    assert_eq!(version_before, 2);

    let new_wasm_hash = env.deployer().upload_contract_wasm(PRICE_ORACLE_WASM);

    env.mock_all_auths();
    let result = client.try_upgrade(&new_wasm_hash);
    assert!(result.is_ok(), "Upgrade should succeed: {:?}", result);

    let version_after = client.version();
    assert_eq!(version_after, 2);
}

// Confirms that only the admin can upgrade the contract.
// This protects the oracle from unauthorized code changes.
#[test]
#[should_panic(expected = "Unauthorized")]
fn test_upgrade_unauthorized() {
    let env = create_test_env();
    let (admin, _user1, _user2) = create_test_addresses(&env);

    let oracle = initialize_oracle(&env, &admin);
    let client = price_oracle::Client::new(&env, &oracle);

    let new_wasm_hash = env.deployer().upload_contract_wasm(PRICE_ORACLE_WASM);

    env.set_auths(&[]);
    client.upgrade(&new_wasm_hash);
}

// Checks that contract state survives an upgrade.
// Whitelisted assets must remain after code changes.
#[test]
fn test_upgrade_preserves_state() {
    let env = create_test_env();
    let (admin, _user1, _user2) = create_test_addresses(&env);

    let oracle = initialize_oracle(&env, &admin);
    let client = price_oracle::Client::new(&env, &oracle);

    let asset = price_oracle::Asset::Stellar(Address::generate(&env));
    client.add_asset(&admin, &asset);
    
    let assets_before = client.get_whitelisted_assets();
    assert_eq!(assets_before.len(), 1);

    env.mock_all_auths();
    let new_wasm_hash = env.deployer().upload_contract_wasm(PRICE_ORACLE_WASM);
    client.upgrade(&new_wasm_hash);

    let assets_after = client.get_whitelisted_assets();
    assert_eq!(assets_after, assets_before);
    assert_eq!(assets_after.len(), 1);
}

// Verifies the version function returns the correct value.
// Version tracking helps confirm upgrades worked.
#[test]
fn test_version() {
    let env = create_test_env();
    let (admin, _user1, _user2) = create_test_addresses(&env);

    let oracle = initialize_oracle(&env, &admin);
    let client = price_oracle::Client::new(&env, &oracle);

    let version = client.version();
    assert_eq!(version, 2);
}

// Confirms the admin address is stored and retrievable.
// The admin controls upgrades, so this must work correctly.
#[test]
fn test_get_admin() {
    let env = create_test_env();
    let (admin, _user1, _user2) = create_test_addresses(&env);

    let oracle = initialize_oracle(&env, &admin);
    let client = price_oracle::Client::new(&env, &oracle);

    let returned_admin = client.admin();
    assert_eq!(returned_admin, admin);
}

// =============================================================================
// TWO-STEP ADMIN TRANSFER TESTS
// =============================================================================

// Verifies successful two-step admin transfer (propose + accept).
// This prevents irreversible admin transfer mistakes by requiring
// the new admin to prove control before the transfer finalizes.
#[test]
fn test_two_step_admin_transfer_success() {
    let env = create_test_env();
    let (admin, user1, _user2) = create_test_addresses(&env);

    let oracle = initialize_oracle(&env, &admin);
    let client = price_oracle::Client::new(&env, &oracle);

    // Step 1: Current admin proposes new admin
    env.mock_all_auths();
    client.propose_admin(&admin, &user1);

    // Verify pending admin is set
    let pending = client.get_pending_admin();
    assert_eq!(pending, user1, "Pending admin should be user1");

    // Verify current admin is unchanged
    assert_eq!(client.admin(), admin, "Current admin should remain unchanged");

    // Step 2: Pending admin accepts the role
    client.accept_admin(&user1);

    // Verify admin transferred
    assert_eq!(client.admin(), user1, "Admin should be transferred");

    // Verify no pending admin remains
    let result = client.try_get_pending_admin();
    assert!(result.is_err(), "Pending admin should be cleared");

    // Verify new admin can perform admin operations
    let new_wasm_hash = env.deployer().upload_contract_wasm(PRICE_ORACLE_WASM);
    client.upgrade(&new_wasm_hash);
}

// Confirms that only the current admin can propose a new admin.
// This prevents unauthorized attempts to take over the contract.
#[test]
#[should_panic(expected = "Error(Contract, #14)")]
fn test_propose_admin_unauthorized() {
    let env = create_test_env();
    let (admin, user1, user2) = create_test_addresses(&env);

    let oracle = initialize_oracle(&env, &admin);
    let client = price_oracle::Client::new(&env, &oracle);

    // Unauthorized user attempts to propose admin
    env.set_auths(&[]);
    client.propose_admin(&user1, &user2);
}

// Verifies that only the pending admin can accept the role.
// Wrong address should not be able to steal admin privileges.
#[test]
#[should_panic(expected = "Error(Contract, #10)")]
fn test_accept_admin_invalid_pending() {
    let env = create_test_env();
    let (admin, user1, user2) = create_test_addresses(&env);

    let oracle = initialize_oracle(&env, &admin);
    let client = price_oracle::Client::new(&env, &oracle);

    // Admin proposes user1
    env.mock_all_auths();
    client.propose_admin(&admin, &user1);

    // user2 (wrong address) tries to accept
    client.accept_admin(&user2);
}

// Confirms that accept fails when no proposal exists.
// This prevents creating an admin out of thin air.
#[test]
#[should_panic(expected = "Error(Contract, #10)")]
fn test_accept_admin_without_proposal() {
    let env = create_test_env();
    let (admin, user1, _user2) = create_test_addresses(&env);

    let oracle = initialize_oracle(&env, &admin);
    let client = price_oracle::Client::new(&env, &oracle);

    // Try to accept without any proposal
    env.mock_all_auths();
    client.accept_admin(&user1);
}

// Verifies the admin can cancel a pending proposal.
// This provides a recovery mechanism if wrong address was proposed.
#[test]
fn test_cancel_admin_proposal() {
    let env = create_test_env();
    let (admin, user1, _user2) = create_test_addresses(&env);

    let oracle = initialize_oracle(&env, &admin);
    let client = price_oracle::Client::new(&env, &oracle);

    // Propose new admin
    env.mock_all_auths();
    client.propose_admin(&admin, &user1);

    // Verify pending admin exists
    assert_eq!(client.get_pending_admin(), user1);

    // Cancel the proposal
    client.cancel_admin_proposal(&admin);

    // Verify no pending admin
    let result = client.try_get_pending_admin();
    assert!(result.is_err(), "Pending admin should be cleared");

    // Verify current admin unchanged
    assert_eq!(client.admin(), admin);
}

// Confirms that proposing a new admin overrides any existing proposal.
// The most recent proposal is what matters.
#[test]
fn test_override_existing_proposal() {
    let env = create_test_env();
    let (admin, user1, user2) = create_test_addresses(&env);

    let oracle = initialize_oracle(&env, &admin);
    let client = price_oracle::Client::new(&env, &oracle);

    env.mock_all_auths();

    // First proposal
    client.propose_admin(&admin, &user1);
    assert_eq!(client.get_pending_admin(), user1);

    // Second proposal overrides first
    client.propose_admin(&admin, &user2);
    assert_eq!(client.get_pending_admin(), user2);

    // user2 can accept, user1 cannot
    client.accept_admin(&user2);
    assert_eq!(client.admin(), user2);
}
