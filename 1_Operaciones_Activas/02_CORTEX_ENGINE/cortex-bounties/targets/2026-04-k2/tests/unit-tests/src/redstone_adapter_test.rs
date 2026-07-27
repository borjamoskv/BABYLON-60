#![cfg(test)]

use crate::redstone_adapter;
use redstone_adapter::Asset;
use soroban_sdk::{testutils::Address as _, Address, Env, String, Symbol, Vec};

pub fn create_test_env() -> Env {
    let env = Env::default();
    env.mock_all_auths();
    
    // Set a realistic timestamp (not 0) to match production conditions
    use soroban_sdk::testutils::Ledger;
    env.ledger().with_mut(|li| {
        li.timestamp = 1704067200; // Jan 1, 2024 00:00:00 UTC
    });
    
    env
}

pub fn create_test_addresses(env: &Env) -> (Address, Address, Address) {
    let admin = Address::generate(env);
    let updater = Address::generate(env);
    let user = Address::generate(env);
    (admin, updater, user)
}

pub fn initialize_adapter(env: &Env, admin: &Address) -> Address {
    let contract_id = env.register(redstone_adapter::WASM, ());
    let client = redstone_adapter::Client::new(env, &contract_id);

    client.initialize(admin, &14, &3600); // 14 decimals for Reflector compatibility, 1 hour max age

    contract_id
}

// =============================================================================
// Initialization Tests
// =============================================================================

#[test]
fn test_adapter_initialization() {
    let env = create_test_env();
    let (admin, _updater, _user) = create_test_addresses(&env);

    let adapter = initialize_adapter(&env, &admin);
    let client = redstone_adapter::Client::new(&env, &adapter);

    // Verify admin
    let stored_admin = client.get_admin();
    assert_eq!(stored_admin, admin);

    // Verify decimals (returns 14 for Reflector compatibility)
    let decimals = client.decimals();
    assert_eq!(decimals, 14);
}

#[test]
#[should_panic]
fn test_adapter_double_initialization() {
    let env = create_test_env();
    let (admin, _updater, _user) = create_test_addresses(&env);

    let adapter = initialize_adapter(&env, &admin);
    let client = redstone_adapter::Client::new(&env, &adapter);

    // Should panic on second initialization
    client.initialize(&admin, &8, &3600);
}

// =============================================================================
// Asset Mapping Tests
// =============================================================================

#[test]
fn test_set_asset_feed_mapping_stellar() {
    let env = create_test_env();
    let (admin, _updater, _user) = create_test_addresses(&env);

    let adapter = initialize_adapter(&env, &admin);
    let client = redstone_adapter::Client::new(&env, &adapter);

    let usdc_address = Address::generate(&env);
    let asset = Asset::Stellar(usdc_address.clone());
    let feed_id = String::from_str(&env, "USDC");

    client.set_asset_feed_mapping(&admin, &asset, &feed_id);

    // Verify mapping
    let stored_feed_id = client.get_feed_id(&asset);
    assert!(stored_feed_id.is_some());
    assert_eq!(stored_feed_id.unwrap(), feed_id);
}

#[test]
fn test_set_asset_feed_mapping_other() {
    let env = create_test_env();
    let (admin, _updater, _user) = create_test_addresses(&env);

    let adapter = initialize_adapter(&env, &admin);
    let client = redstone_adapter::Client::new(&env, &adapter);

    let btc_symbol = Symbol::new(&env, "BTC");
    let asset = Asset::Other(btc_symbol);
    let feed_id = String::from_str(&env, "BTC");

    client.set_asset_feed_mapping(&admin, &asset, &feed_id);

    // Verify mapping
    let stored_feed_id = client.get_feed_id(&asset);
    assert!(stored_feed_id.is_some());
    assert_eq!(stored_feed_id.unwrap(), feed_id);
}

#[test]
#[should_panic]
fn test_set_asset_feed_mapping_unauthorized() {
    let env = create_test_env();
    let (admin, _updater, user) = create_test_addresses(&env);

    let adapter = initialize_adapter(&env, &admin);
    let client = redstone_adapter::Client::new(&env, &adapter);

    let asset = Asset::Stellar(Address::generate(&env));
    let feed_id = String::from_str(&env, "USDC");

    // Should panic - user is not admin
    client.set_asset_feed_mapping(&user, &asset, &feed_id);
}

#[test]
fn test_remove_asset_feed_mapping() {
    let env = create_test_env();
    let (admin, _updater, _user) = create_test_addresses(&env);

    let adapter = initialize_adapter(&env, &admin);
    let client = redstone_adapter::Client::new(&env, &adapter);

    let asset = Asset::Stellar(Address::generate(&env));
    let feed_id = String::from_str(&env, "USDC");

    // Set mapping
    client.set_asset_feed_mapping(&admin, &asset, &feed_id);
    assert!(client.get_feed_id(&asset).is_some());

    // Remove mapping
    client.remove_asset_feed_mapping(&admin, &asset);
    assert!(client.get_feed_id(&asset).is_none());
}

// =============================================================================
// Price Reading Tests
// =============================================================================

#[test]
#[should_panic]
fn test_read_prices_not_found() {
    let env = create_test_env();
    let (admin, _updater, _user) = create_test_addresses(&env);

    let adapter = initialize_adapter(&env, &admin);
    let client = redstone_adapter::Client::new(&env, &adapter);

    let feed_id = String::from_str(&env, "NONEXISTENT");
    let feed_ids = Vec::from_array(&env, [feed_id]);

    // Should panic - feed not found
    client.read_prices(&feed_ids);
}

// =============================================================================
// Reflector Interface Tests
// =============================================================================

#[test]
fn test_lastprice_no_mapping() {
    let env = create_test_env();
    let (admin, _updater, _user) = create_test_addresses(&env);

    let adapter = initialize_adapter(&env, &admin);
    let client = redstone_adapter::Client::new(&env, &adapter);

    let asset = Asset::Stellar(Address::generate(&env));

    // Should return None - no mapping exists
    let price_data = client.lastprice(&asset);
    assert!(price_data.is_none());
}

#[test]
fn test_lastprice_no_price_data() {
    let env = create_test_env();
    let (admin, _updater, _user) = create_test_addresses(&env);

    let adapter = initialize_adapter(&env, &admin);
    let client = redstone_adapter::Client::new(&env, &adapter);

    let asset = Asset::Stellar(Address::generate(&env));
    let feed_id = String::from_str(&env, "USDC");
    client.set_asset_feed_mapping(&admin, &asset, &feed_id);

    // Without writing any price, should return None
    let price_data = client.lastprice(&asset);
    assert!(price_data.is_none());
}

#[test]
fn test_decimals_interface() {
    let env = create_test_env();
    let (admin, _updater, _user) = create_test_addresses(&env);

    let adapter = initialize_adapter(&env, &admin);
    let client = redstone_adapter::Client::new(&env, &adapter);

    // Should always return 14 for Reflector compatibility
    let decimals = client.decimals();
    assert_eq!(decimals, 14);
}

// =============================================================================
// Admin Configuration Tests
// =============================================================================

#[test]
fn test_set_max_price_age() {
    let env = create_test_env();
    let (admin, _updater, _user) = create_test_addresses(&env);

    let adapter = initialize_adapter(&env, &admin);
    let client = redstone_adapter::Client::new(&env, &adapter);

    // Set max age to 120 seconds (above 60s minimum) - just verify it doesn't panic
    client.set_max_price_age(&admin, &120);
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
    let (admin, _updater, user) = create_test_addresses(&env);

    let adapter = initialize_adapter(&env, &admin);
    let client = redstone_adapter::Client::new(&env, &adapter);

    // Step 1: Current admin proposes new admin
    client.propose_admin(&admin, &user);

    // Verify pending admin is set
    let pending = client.get_pending_admin();
    assert!(pending.is_some(), "Pending admin should be set");
    assert_eq!(pending.unwrap(), user);

    // Verify current admin is unchanged
    assert_eq!(client.get_admin(), admin);

    // Step 2: Pending admin accepts the role
    client.accept_admin(&user);

    // Verify admin transferred
    assert_eq!(client.get_admin(), user);

    // Verify no pending admin remains
    let pending_after = client.get_pending_admin();
    assert!(pending_after.is_none(), "Pending admin should be cleared");

    // Verify new admin can perform admin operations
    let new_max_age = 7200u64;
    client.set_max_price_age(&user, &new_max_age);
}

// Confirms that only the current admin can propose a new admin.
// This prevents unauthorized attempts to take over the contract.
#[test]
#[should_panic(expected = "Error(Contract, #3)")]
fn test_propose_admin_unauthorized() {
    let env = create_test_env();
    let (admin, updater, user) = create_test_addresses(&env);

    let adapter = initialize_adapter(&env, &admin);
    let client = redstone_adapter::Client::new(&env, &adapter);

    // Unauthorized user attempts to propose admin
    env.set_auths(&[]);
    client.propose_admin(&updater, &user);
}

// Verifies that only the pending admin can accept the role.
// Wrong address should not be able to steal admin privileges.
#[test]
#[should_panic(expected = "Error(Contract, #13)")]
fn test_accept_admin_invalid_pending() {
    let env = create_test_env();
    let (admin, updater, user) = create_test_addresses(&env);

    let adapter = initialize_adapter(&env, &admin);
    let client = redstone_adapter::Client::new(&env, &adapter);

    // Admin proposes user
    client.propose_admin(&admin, &user);

    // updater (wrong address) tries to accept
    client.accept_admin(&updater);
}

// Confirms that accept fails when no proposal exists.
// This prevents creating an admin out of thin air.
#[test]
#[should_panic(expected = "Error(Contract, #12)")]
fn test_accept_admin_without_proposal() {
    let env = create_test_env();
    let (admin, _updater, user) = create_test_addresses(&env);

    let adapter = initialize_adapter(&env, &admin);
    let client = redstone_adapter::Client::new(&env, &adapter);

    // Try to accept without any proposal
    client.accept_admin(&user);
}

// Verifies the admin can cancel a pending proposal.
// This provides a recovery mechanism if wrong address was proposed.
#[test]
fn test_cancel_admin_proposal() {
    let env = create_test_env();
    let (admin, _updater, user) = create_test_addresses(&env);

    let adapter = initialize_adapter(&env, &admin);
    let client = redstone_adapter::Client::new(&env, &adapter);

    // Propose new admin
    client.propose_admin(&admin, &user);

    // Verify pending admin exists
    assert!(client.get_pending_admin().is_some());

    // Cancel the proposal
    client.cancel_admin_proposal(&admin);

    // Verify no pending admin
    assert!(client.get_pending_admin().is_none());

    // Verify current admin unchanged
    assert_eq!(client.get_admin(), admin);
}

// Confirms that proposing a new admin overrides any existing proposal.
// The most recent proposal is what matters.
#[test]
fn test_override_existing_proposal() {
    let env = create_test_env();
    let (admin, updater, user) = create_test_addresses(&env);

    let adapter = initialize_adapter(&env, &admin);
    let client = redstone_adapter::Client::new(&env, &adapter);

    // First proposal
    client.propose_admin(&admin, &user);
    assert_eq!(client.get_pending_admin().unwrap(), user);

    // Second proposal overrides first
    client.propose_admin(&admin, &updater);
    assert_eq!(client.get_pending_admin().unwrap(), updater);

    // updater can accept, user cannot
    client.accept_admin(&updater);
    assert_eq!(client.get_admin(), updater);
}

// Verifies that only the admin can cancel proposals.
#[test]
#[should_panic(expected = "Error(Contract, #3)")]
fn test_cancel_admin_proposal_unauthorized() {
    let env = create_test_env();
    let (admin, updater, user) = create_test_addresses(&env);

    let adapter = initialize_adapter(&env, &admin);
    let client = redstone_adapter::Client::new(&env, &adapter);

    // Admin proposes user
    client.propose_admin(&admin, &user);

    // updater (not admin) tries to cancel
    env.set_auths(&[]);
    client.cancel_admin_proposal(&updater);
}
