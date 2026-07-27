#![cfg(test)]

// Tests the upgrade flow for the lending pool contract.
use k2_kinetic_router::KineticRouterContract;
// These tests show how admin-controlled upgrades work and confirm
// the pool keeps its state after code changes.
//
// The lending pool is upgradeable because it manages core protocol logic
// that may need fixes or improvements. Upgrades let us fix bugs and add
// features without losing user funds or positions.

use k2_kinetic_router::router::KineticRouterContractClient;
use crate::kinetic_router_test::{create_test_addresses, create_test_env, initialize_kinetic_router};
use soroban_sdk::{testutils::Address as _, Address};

const KINETIC_ROUTER_WASM: &[u8] =
    include_bytes!("../../../target/wasm32v1-none/release/k2_kinetic_router.optimized.wasm");

// Verifies that the admin can upgrade the contract with new WASM.
// This is the core upgrade operation that lets us deploy bug fixes.
#[test]
fn test_upgrade_success() {
    let env = create_test_env();

    // Increase budget to handle the contract initialization costs
    env.cost_estimate().budget().reset_unlimited();

    let (admin, emergency_admin, _user1, _user2) = create_test_addresses(&env);
    let router = Address::generate(&env);
    let dex_router = Address::generate(&env);

    let (kinetic_router, _oracle) =
        initialize_kinetic_router(&env, &admin, &emergency_admin, &router, &dex_router);
    let client = KineticRouterContractClient::new(&env, &kinetic_router);

    let version_before = client.version();
    assert_eq!(version_before, 3);

    let new_wasm_hash = env.deployer().upload_contract_wasm(KINETIC_ROUTER_WASM);

    env.mock_all_auths();
    let result = client.try_upgrade(&new_wasm_hash);
    assert!(result.is_ok(), "Upgrade should succeed");

    let version_after = client.version();
    assert_eq!(version_after, 3);
}

// Confirms that only the admin can upgrade the contract.
// This protects the protocol from unauthorized code changes.
#[test]
fn test_upgrade_unauthorized() {
    let env = create_test_env();

    // Increase budget to handle the contract initialization costs
    env.cost_estimate().budget().reset_unlimited();

    let (admin, emergency_admin, _user1, _user2) = create_test_addresses(&env);
    let router = Address::generate(&env);
    let dex_router = Address::generate(&env);

    let (kinetic_router, _oracle) =
        initialize_kinetic_router(&env, &admin, &emergency_admin, &router, &dex_router);
    let client = KineticRouterContractClient::new(&env, &kinetic_router);

    let new_wasm_hash = env.deployer().upload_contract_wasm(KINETIC_ROUTER_WASM);

    env.set_auths(&[]);
    let result = client.try_upgrade(&new_wasm_hash);
    assert!(
        result.is_err(),
        "Upgrade should fail for unauthorized caller"
    );
}

// Checks that contract state survives an upgrade.
// User funds and positions must remain intact after code changes.
#[test]
fn test_upgrade_preserves_state() {
    let env = create_test_env();

    // Increase budget to handle the contract initialization and state preservation costs
    env.cost_estimate().budget().reset_unlimited();

    let (admin, emergency_admin, _user1, _user2) = create_test_addresses(&env);
    let router = Address::generate(&env);
    let dex_router = Address::generate(&env);

    let (kinetic_router, _oracle) =
        initialize_kinetic_router(&env, &admin, &emergency_admin, &router, &dex_router);
    let client = KineticRouterContractClient::new(&env, &kinetic_router);

    let reserves_before = client.get_reserves_list();

    env.mock_all_auths();
    let new_wasm_hash = env.deployer().upload_contract_wasm(KINETIC_ROUTER_WASM);
    client.upgrade(&new_wasm_hash);

    let reserves_after = client.get_reserves_list();
    assert_eq!(reserves_before, reserves_after);
}

// Confirms the admin address is stored and retrievable.
// The admin controls upgrades, so this must work correctly.
#[test]
fn test_get_admin() {
    let env = create_test_env();
    let (admin, emergency_admin, _user1, _user2) = create_test_addresses(&env);
    let router = Address::generate(&env);
    let dex_router = Address::generate(&env);

    let (kinetic_router, _oracle) =
        initialize_kinetic_router(&env, &admin, &emergency_admin, &router, &dex_router);
    let client = KineticRouterContractClient::new(&env, &kinetic_router);

    let returned_admin = client.get_admin();
    assert_eq!(returned_admin, admin);
}

// Verifies the version function returns the correct value.
// Version tracking helps us confirm upgrades worked.
#[test]
fn test_version() {
    let env = create_test_env();
    let (admin, emergency_admin, _user1, _user2) = create_test_addresses(&env);
    let router = Address::generate(&env);
    let dex_router = Address::generate(&env);

    let (kinetic_router, _oracle) =
        initialize_kinetic_router(&env, &admin, &emergency_admin, &router, &dex_router);
    let client = KineticRouterContractClient::new(&env, &kinetic_router);

    let version = client.version();
    assert_eq!(version, 3);
}
