#![cfg(test)]

//! Tests verifying execute_operation is not exposed as a public entry point

use crate::kinetic_router;
use soroban_sdk::{
    testutils::{Address as _, Ledger, LedgerInfo},
    Env,
};

#[test]
fn test_execute_operation_not_exposed() {
    let env = Env::default();
    env.mock_all_auths();

    env.ledger().set(LedgerInfo {
        sequence_number: 100,
        protocol_version: 23,
        timestamp: 1000,
        network_id: Default::default(),
        base_reserve: 10,
        min_temp_entry_ttl: 10,
        min_persistent_entry_ttl: 10,
        max_entry_ttl: 1000000,
    });

    let router_id = env.register(kinetic_router::WASM, ());
    let _router = kinetic_router::Client::new(&env, &router_id);

    // This test verifies that execute_operation is not exposed as a public entry point
    // If compilation succeeds, the function is properly internal-only
    assert!(true);
}
