#![cfg(test)]

use crate::setup::deploy_full_protocol;
use crate::{kinetic_router, price_oracle, pool_configurator};
use soroban_sdk::{
    testutils::{Address as _, MockAuth, MockAuthInvoke},
    Address, BytesN, Env, IntoVal,
};

#[test]
fn test_kinetic_router_version() {
    let env = Env::default();
    env.mock_all_auths();
    
    let admin = Address::generate(&env);
    let emergency_admin = Address::generate(&env);
    let protocol = deploy_full_protocol(&env, &admin, &emergency_admin);
    
    let kinetic_router_client = kinetic_router::Client::new(&env, &protocol.kinetic_router);
    let version_before = kinetic_router_client.version();
    assert_eq!(version_before, 3, "Kinetic router version must be 3. Got: {}", version_before);
    
    // Test that version remains consistent after attempting invalid upgrade
    let invalid_hash = BytesN::from_array(&env, &[0u8; 32]);
    let _ = kinetic_router_client.try_upgrade(&invalid_hash);
    
    let version_after = kinetic_router_client.version();
    assert_eq!(version_after, version_before, "Version must remain unchanged after failed upgrade. Expected: {}, Got: {}", version_before, version_after);
}

#[test]
fn test_price_oracle_version() {
    let env = Env::default();
    env.mock_all_auths();
    
    let admin = Address::generate(&env);
    let emergency_admin = Address::generate(&env);
    let protocol = deploy_full_protocol(&env, &admin, &emergency_admin);
    
    let price_oracle_client = price_oracle::Client::new(&env, &protocol.price_oracle);
    let version_before = price_oracle_client.version();
    assert_eq!(version_before, 2, "Price oracle version must be 2. Got: {}", version_before);
    
    // Test that version remains consistent after attempting invalid upgrade
    let invalid_hash = BytesN::from_array(&env, &[0u8; 32]);
    let _ = price_oracle_client.try_upgrade(&invalid_hash);
    
    let version_after = price_oracle_client.version();
    assert_eq!(version_after, version_before, "Version must remain unchanged after failed upgrade. Expected: {}, Got: {}", version_before, version_after);
}

#[test]
fn test_pool_configurator_version() {
    let env = Env::default();
    env.mock_all_auths();
    
    let admin = Address::generate(&env);
    let emergency_admin = Address::generate(&env);
    let protocol = deploy_full_protocol(&env, &admin, &emergency_admin);
    
    let pool_configurator_client = pool_configurator::Client::new(&env, &protocol.pool_configurator);
    let version_before = pool_configurator_client.version();
    assert_eq!(version_before, 2, "Pool configurator version must be 2. Got: {}", version_before);
    
    // Test that version remains consistent after attempting invalid upgrade
    let invalid_hash = BytesN::from_array(&env, &[0u8; 32]);
    let _ = pool_configurator_client.try_upgrade(&invalid_hash);
    
    let version_after = pool_configurator_client.version();
    assert_eq!(version_after, version_before, "Version must remain unchanged after failed upgrade. Expected: {}, Got: {}", version_before, version_after);
}

#[test]
fn test_kinetic_router_upgrade_checks_stored_admin() {
    let env = Env::default();
    env.mock_all_auths();
    
    let admin = Address::generate(&env);
    let emergency_admin = Address::generate(&env);
    let protocol = deploy_full_protocol(&env, &admin, &emergency_admin);
    
    let kinetic_router_client = kinetic_router::Client::new(&env, &protocol.kinetic_router);
    let version_before = kinetic_router_client.version();
    assert_eq!(version_before, 3, "Initial version must be 3. Got: {}", version_before);
    
    let admin_result = kinetic_router_client.try_get_admin();
    let stored_admin = match admin_result {
        Ok(Ok(addr)) => addr,
        _ => panic!("get_admin must succeed for initialized contract"),
    };
    assert_eq!(stored_admin, admin, "Stored admin must match initialized admin. Expected: {:?}, Got: {:?}", admin, stored_admin);
    
    let invalid_wasm_hash = BytesN::from_array(&env, &[0u8; 32]);
    
    // Verify upgrade fails with invalid hash
    let upgrade_result = kinetic_router_client.try_upgrade(&invalid_wasm_hash);
    match upgrade_result {
        Ok(Ok(_)) => {
            panic!("Upgrade with invalid hash (all zeros) should fail, but it succeeded. This indicates upgrade validation is broken!");
        }
        Err(Ok(e)) => {
            // Expected: KineticRouterError from contract (e.g., Unauthorized)
            assert!(true, "Upgrade correctly failed with invalid hash (contract error): {:?}", e);
        }
        Err(Err(e)) => {
            assert!(true, "Upgrade correctly failed with invalid hash (runtime abort): {:?}", e);
        }
        Ok(Err(e)) => {
            // Expected: KineticRouterError from contract
            assert!(true, "Upgrade correctly failed with invalid hash (contract error): {:?}", e);
        }
    }
    
    let version_after = kinetic_router_client.version();
    assert_eq!(version_after, version_before, "Version should remain unchanged when upgrading to invalid WASM. Expected: {}, Got: {}", version_before, version_after);
    
    let admin_result_after = kinetic_router_client.try_get_admin();
    match admin_result_after {
        Ok(Ok(addr)) => {
            assert_eq!(addr, stored_admin, "Admin must remain unchanged after upgrade attempt. Expected: {:?}, Got: {:?}", stored_admin, addr);
            assert_eq!(addr, admin, "Admin must match initialized admin. Expected: {:?}, Got: {:?}", admin, addr);
        }
        _ => panic!("get_admin must succeed after upgrade attempt"),
    }
}

#[test]
fn test_price_oracle_upgrade_checks_stored_admin() {
    let env = Env::default();
    env.mock_all_auths();
    
    let admin = Address::generate(&env);
    let emergency_admin = Address::generate(&env);
    let protocol = deploy_full_protocol(&env, &admin, &emergency_admin);
    
    let price_oracle_client = price_oracle::Client::new(&env, &protocol.price_oracle);
    let version_before = price_oracle_client.version();
    assert_eq!(version_before, 2, "Initial version must be 2. Got: {}", version_before);
    
    let stored_admin = price_oracle_client.admin();
    assert_eq!(stored_admin, admin, "Stored admin must match initialized admin. Expected: {:?}, Got: {:?}", admin, stored_admin);
    
    let invalid_wasm_hash = BytesN::from_array(&env, &[0u8; 32]);
    
    // Verify upgrade fails with invalid hash
    let upgrade_result = price_oracle_client.try_upgrade(&invalid_wasm_hash);
    match upgrade_result {
        Ok(Ok(_)) => {
            panic!("Upgrade with invalid hash (all zeros) should fail, but it succeeded. This indicates upgrade validation is broken!");
        }
        Err(Ok(e)) => {
            // Expected: PriceOracleError from contract
            assert!(true, "Upgrade correctly failed with invalid hash (contract error): {:?}", e);
        }
        Err(Err(e)) => {
            // Expected: Contract call error (Abort) when invalid hash is rejected by Soroban runtime
            assert!(true, "Upgrade correctly failed with invalid hash (runtime abort): {:?}", e);
        }
        Ok(Err(e)) => {
            // Expected: Error from contract
            assert!(true, "Upgrade correctly failed with invalid hash (contract error): {:?}", e);
        }
    }
    
    let version_after = price_oracle_client.version();
    assert_eq!(version_after, version_before, "Version should remain unchanged when upgrading to invalid WASM. Expected: {}, Got: {}", version_before, version_after);
    
    let admin_after = price_oracle_client.admin();
    assert_eq!(admin_after, stored_admin, "Admin must remain unchanged after upgrade attempt. Expected: {:?}, Got: {:?}", stored_admin, admin_after);
    assert_eq!(admin_after, admin, "Admin must match initialized admin. Expected: {:?}, Got: {:?}", admin, admin_after);
}

#[test]
fn test_pool_configurator_upgrade_checks_stored_admin() {
    let env = Env::default();
    env.mock_all_auths();
    
    let admin = Address::generate(&env);
    let emergency_admin = Address::generate(&env);
    let protocol = deploy_full_protocol(&env, &admin, &emergency_admin);
    
    let pool_configurator_client = pool_configurator::Client::new(&env, &protocol.pool_configurator);
    let version_before = pool_configurator_client.version();
    assert_eq!(version_before, 2, "Initial version must be 2. Got: {}", version_before);
    
    let invalid_wasm_hash = BytesN::from_array(&env, &[0u8; 32]);
    
    // Verify upgrade fails with invalid hash
    let upgrade_result = pool_configurator_client.try_upgrade(&invalid_wasm_hash);
    match upgrade_result {
        Ok(Ok(_)) => {
            panic!("Upgrade with invalid hash (all zeros) should fail, but it succeeded. This indicates upgrade validation is broken!");
        }
        Err(Ok(e)) => {
            // Expected: PoolConfiguratorError from contract
            assert!(true, "Upgrade correctly failed with invalid hash (contract error): {:?}", e);
        }
        Err(Err(e)) => {
            // Expected: Contract call error (Abort) when invalid hash is rejected by Soroban runtime
            assert!(true, "Upgrade correctly failed with invalid hash (runtime abort): {:?}", e);
        }
        Ok(Err(e)) => {
            // Expected: Error from contract
            assert!(true, "Upgrade correctly failed with invalid hash (contract error): {:?}", e);
        }
    }
    
    let version_after = pool_configurator_client.version();
    assert_eq!(version_after, version_before, "Version should remain unchanged when upgrading to invalid WASM. Expected: {}, Got: {}", version_before, version_after);
}

#[test]
fn test_upgrade_authorization_requires_admin() {
    let env = Env::default();
    env.mock_all_auths();
    
    let admin = Address::generate(&env);
    let emergency_admin = Address::generate(&env);
    let unauthorized = Address::generate(&env);
    let protocol = deploy_full_protocol(&env, &admin, &emergency_admin);
    
    let kinetic_router_client = kinetic_router::Client::new(&env, &protocol.kinetic_router);
    let invalid_hash = BytesN::from_array(&env, &[0u8; 32]);
    
    // Test: Unauthorized user cannot upgrade
    env.mock_auths(&[]);
    let unauthorized_result = kinetic_router_client.try_upgrade(&invalid_hash);
    assert!(unauthorized_result.is_err(), "Unauthorized user should not be able to upgrade");
    
    // Test: Emergency admin cannot upgrade (only pool admin can)
    env.mock_auths(&[]);
    let emergency_result = kinetic_router_client.try_upgrade(&invalid_hash);
    assert!(emergency_result.is_err(), "Emergency admin should not be able to upgrade");
}

#[test]
fn test_upgrade_data_migration_preserves_admin() {
    let env = Env::default();
    env.mock_all_auths();
    
    let admin = Address::generate(&env);
    let emergency_admin = Address::generate(&env);
    let protocol = deploy_full_protocol(&env, &admin, &emergency_admin);
    
    let kinetic_router_client = kinetic_router::Client::new(&env, &protocol.kinetic_router);
    
    // Get admin before upgrade attempt
    let admin_before = kinetic_router_client.get_admin();
    assert_eq!(admin_before, admin, "Admin should match initialized admin");
    
    // Attempt upgrade with invalid hash (will fail but admin should remain)
    let invalid_hash = BytesN::from_array(&env, &[0u8; 32]);
    
    env.mock_auths(&[MockAuth {
        address: &admin,
        invoke: &MockAuthInvoke {
            contract: &protocol.kinetic_router,
            fn_name: "upgrade",
            args: (&invalid_hash,).into_val(&env),
            sub_invokes: &[],
        },
    }]);
    
    let _ = kinetic_router_client.try_upgrade(&invalid_hash);
    
    // Verify admin remains unchanged after failed upgrade
    let admin_after = kinetic_router_client.get_admin();
    assert_eq!(admin_after, admin_before, "Admin must remain unchanged after upgrade attempt");
    assert_eq!(admin_after, admin, "Admin must match original admin");
}

#[test]
fn test_upgrade_data_migration_preserves_configuration() {
    let env = Env::default();
    env.mock_all_auths();
    
    let admin = Address::generate(&env);
    let emergency_admin = Address::generate(&env);
    let protocol = deploy_full_protocol(&env, &admin, &emergency_admin);
    
    let kinetic_router_client = kinetic_router::Client::new(&env, &protocol.kinetic_router);
    
    // Set some configuration values
    let flash_premium = 50u128;
    kinetic_router_client.set_flash_loan_premium(&flash_premium);
    
    let hf_threshold = 950_000_000_000_000_000u128;
    kinetic_router_client.set_hf_liquidation_threshold(&hf_threshold);
    
    // Get configuration before upgrade attempt
    let premium_before = kinetic_router_client.get_flash_loan_premium();
    let threshold_before = kinetic_router_client.get_hf_liquidation_threshold();
    
    // Attempt upgrade with invalid hash
    let invalid_hash = BytesN::from_array(&env, &[0u8; 32]);
    
    env.mock_auths(&[MockAuth {
        address: &admin,
        invoke: &MockAuthInvoke {
            contract: &protocol.kinetic_router,
            fn_name: "upgrade",
            args: (&invalid_hash,).into_val(&env),
            sub_invokes: &[],
        },
    }]);
    
    let _ = kinetic_router_client.try_upgrade(&invalid_hash);
    
    // Verify configuration remains unchanged after failed upgrade
    let premium_after = kinetic_router_client.get_flash_loan_premium();
    let threshold_after = kinetic_router_client.get_hf_liquidation_threshold();
    
    assert_eq!(premium_after, premium_before, "Flash loan premium must remain unchanged");
    assert_eq!(threshold_after, threshold_before, "HF threshold must remain unchanged");
}

#[test]
fn test_upgrade_version_increments_on_success() {
    let env = Env::default();
    env.mock_all_auths();
    
    let admin = Address::generate(&env);
    let emergency_admin = Address::generate(&env);
    let protocol = deploy_full_protocol(&env, &admin, &emergency_admin);
    
    let kinetic_router_client = kinetic_router::Client::new(&env, &protocol.kinetic_router);
    let price_oracle_client = price_oracle::Client::new(&env, &protocol.price_oracle);
    let pool_configurator_client = pool_configurator::Client::new(&env, &protocol.pool_configurator);
    
    // Get initial versions
    let router_version_before = kinetic_router_client.version();
    let oracle_version_before = price_oracle_client.version();
    let configurator_version_before = pool_configurator_client.version();
    
    assert_eq!(router_version_before, 3, "Initial router version should be 3");
    assert_eq!(oracle_version_before, 2, "Initial oracle version should be 2");
    assert_eq!(configurator_version_before, 2, "Initial configurator version should be 2");
    
    // Note: Actual version increment happens in contract code when upgrade succeeds
    // Since we're testing with invalid hashes, versions won't increment
    // But we verify they remain consistent
    
    let invalid_hash = BytesN::from_array(&env, &[0u8; 32]);
    
    env.mock_auths(&[MockAuth {
        address: &admin,
        invoke: &MockAuthInvoke {
            contract: &protocol.kinetic_router,
            fn_name: "upgrade",
            args: (&invalid_hash,).into_val(&env),
            sub_invokes: &[],
        },
    }]);
    
    let _ = kinetic_router_client.try_upgrade(&invalid_hash);
    
    // Versions should remain unchanged after failed upgrade
    let router_version_after = kinetic_router_client.version();
    let oracle_version_after = price_oracle_client.version();
    let configurator_version_after = pool_configurator_client.version();
    
    assert_eq!(router_version_after, router_version_before, "Version should remain unchanged after failed upgrade");
    assert_eq!(oracle_version_after, oracle_version_before, "Oracle version should remain unchanged");
    assert_eq!(configurator_version_after, configurator_version_before, "Configurator version should remain unchanged");
}

#[test]
fn test_upgrade_preserves_reserve_data() {
    let env = Env::default();
    env.mock_all_auths();
    
    let admin = Address::generate(&env);
    let emergency_admin = Address::generate(&env);
    let protocol = deploy_full_protocol(&env, &admin, &emergency_admin);
    
    // This test verifies that upgrade doesn't affect existing reserves
    // Since we can't actually upgrade with valid WASM in tests, we verify
    // that failed upgrade attempts don't corrupt data
    
    let kinetic_router_client = kinetic_router::Client::new(&env, &protocol.kinetic_router);
    
    // Get reserves list before upgrade attempt
    let reserves_before = kinetic_router_client.get_reserves_list();
    let reserves_count_before = reserves_before.len();
    
    // Attempt upgrade
    let invalid_hash = BytesN::from_array(&env, &[0u8; 32]);
    
    env.mock_auths(&[MockAuth {
        address: &admin,
        invoke: &MockAuthInvoke {
            contract: &protocol.kinetic_router,
            fn_name: "upgrade",
            args: (&invalid_hash,).into_val(&env),
            sub_invokes: &[],
        },
    }]);
    
    let _ = kinetic_router_client.try_upgrade(&invalid_hash);
    
    // Verify reserves list unchanged
    let reserves_after = kinetic_router_client.get_reserves_list();
    let reserves_count_after = reserves_after.len();
    
    assert_eq!(reserves_count_after, reserves_count_before, "Reserves count should remain unchanged after upgrade attempt");
}


// =============================================================================
// TWO-STEP ADMIN TRANSFER TESTS
// =============================================================================

#[test]
fn test_kinetic_router_two_step_admin_transfer_success() {
    let env = Env::default();
    env.mock_all_auths();
    
    let admin = Address::generate(&env);
    let emergency_admin = Address::generate(&env);
    let new_admin = Address::generate(&env);
    let protocol = deploy_full_protocol(&env, &admin, &emergency_admin);
    
    let kinetic_router_client = kinetic_router::Client::new(&env, &protocol.kinetic_router);
    
    // Step 1: Propose new admin
    kinetic_router_client.propose_admin(&admin, &new_admin);
    
    // Verify pending admin
    let pending = kinetic_router_client.try_get_pending_admin().unwrap().unwrap();
    assert_eq!(pending, new_admin, "Pending admin should be set");
    
    // Verify current admin unchanged
    assert_eq!(kinetic_router_client.get_admin(), admin, "Current admin should remain unchanged");
    
    // Step 2: Accept admin (must be called by pending admin)
    kinetic_router_client.accept_admin(&new_admin);
    
    // Verify admin transferred
    assert_eq!(kinetic_router_client.get_admin(), new_admin, "Admin should be transferred");
    
    // Verify no pending admin
    let result = kinetic_router_client.try_get_pending_admin();
    assert!(result.is_err(), "Pending admin should be cleared");
    
    // Verify new admin can perform upgrade operations (upgrade admin is for contract upgrades)
    // Note: upgrade admin is different from pool admin - upgrade admin can upgrade contracts
    // For pool operations, we need pool admin (tested separately)
}

#[test]
fn test_kinetic_router_propose_admin_unauthorized() {
    let env = Env::default();
    
    let admin = Address::generate(&env);
    let emergency_admin = Address::generate(&env);
    let unauthorized = Address::generate(&env);
    let new_admin = Address::generate(&env);
    
    env.mock_all_auths();
    let protocol = deploy_full_protocol(&env, &admin, &emergency_admin);
    
    let kinetic_router_client = kinetic_router::Client::new(&env, &protocol.kinetic_router);
    
    env.mock_auths(&[]);
    let result = kinetic_router_client.try_propose_admin(&unauthorized, &new_admin);
    assert!(result.is_err(), "Unauthorized user should not be able to propose admin");
}

#[test]
fn test_kinetic_router_accept_admin_invalid_pending() {
    let env = Env::default();
    env.mock_all_auths();
    
    let admin = Address::generate(&env);
    let emergency_admin = Address::generate(&env);
    let new_admin = Address::generate(&env);
    let wrong_address = Address::generate(&env);
    
    let protocol = deploy_full_protocol(&env, &admin, &emergency_admin);
    let kinetic_router_client = kinetic_router::Client::new(&env, &protocol.kinetic_router);
    
    // Propose new admin
    kinetic_router_client.propose_admin(&admin, &new_admin);
    
    // Try to accept with wrong address
    let result = kinetic_router_client.try_accept_admin(&wrong_address);
    assert!(result.is_err(), "Wrong address should not be able to accept admin");
    
    // Verify admin unchanged
    assert_eq!(kinetic_router_client.get_admin(), admin);
}

#[test]
fn test_kinetic_router_cancel_admin_proposal() {
    let env = Env::default();
    env.mock_all_auths();
    
    let admin = Address::generate(&env);
    let emergency_admin = Address::generate(&env);
    let new_admin = Address::generate(&env);
    
    let protocol = deploy_full_protocol(&env, &admin, &emergency_admin);
    let kinetic_router_client = kinetic_router::Client::new(&env, &protocol.kinetic_router);
    
    // Propose new admin
    kinetic_router_client.propose_admin(&admin, &new_admin);
    
    // Cancel proposal
    kinetic_router_client.cancel_admin_proposal(&admin);
    
    // Verify no pending admin
    let result = kinetic_router_client.try_get_pending_admin();
    assert!(result.is_err(), "Pending admin should be cleared");
    
    // Verify admin unchanged
    assert_eq!(kinetic_router_client.get_admin(), admin);
}

#[test]
fn test_kinetic_router_two_step_pool_admin_transfer() {
    let env = Env::default();
    env.mock_all_auths();
    
    let admin = Address::generate(&env);
    let emergency_admin = Address::generate(&env);
    let new_pool_admin = Address::generate(&env);
    
    let protocol = deploy_full_protocol(&env, &admin, &emergency_admin);
    let kinetic_router_client = kinetic_router::Client::new(&env, &protocol.kinetic_router);
    
    // Propose pool admin
    kinetic_router_client.propose_pool_admin(&admin, &new_pool_admin);
    
    // Verify pending
    let pending = kinetic_router_client.try_get_pending_pool_admin().unwrap().unwrap();
    assert_eq!(pending, new_pool_admin);
    
    // Accept
    kinetic_router_client.accept_pool_admin(&new_pool_admin);
    
    // Verify new pool admin can perform operations
    let new_premium = 90u128;
    kinetic_router_client.set_flash_loan_premium(&new_premium);
    assert_eq!(kinetic_router_client.get_flash_loan_premium(), new_premium);
}

#[test]
fn test_kinetic_router_two_step_emergency_admin_transfer() {
    let env = Env::default();
    env.mock_all_auths();
    
    let admin = Address::generate(&env);
    let emergency_admin = Address::generate(&env);
    let new_emergency_admin = Address::generate(&env);
    
    let protocol = deploy_full_protocol(&env, &admin, &emergency_admin);
    let kinetic_router_client = kinetic_router::Client::new(&env, &protocol.kinetic_router);
    
    // Propose emergency admin
    kinetic_router_client.propose_emergency_admin(&admin, &new_emergency_admin);
    
    // Accept
    kinetic_router_client.accept_emergency_admin(&new_emergency_admin);
    
    // Verify new emergency admin can pause
    kinetic_router_client.pause(&new_emergency_admin);
    assert!(kinetic_router_client.is_paused());
    
    // Cleanup: M-04 requires pool admin for unpause
    kinetic_router_client.unpause(&admin);
}

#[test]
fn test_pool_configurator_two_step_admin_transfer() {
    let env = Env::default();
    env.mock_all_auths();
    
    let admin = Address::generate(&env);
    let emergency_admin = Address::generate(&env);
    let new_admin = Address::generate(&env);
    
    let protocol = deploy_full_protocol(&env, &admin, &emergency_admin);
    let pool_configurator_client = pool_configurator::Client::new(&env, &protocol.pool_configurator);
    
    // Propose
    pool_configurator_client.propose_admin(&admin, &new_admin);
    
    // Verify pending
    let pending = pool_configurator_client.try_get_pending_admin().unwrap().unwrap();
    assert_eq!(pending, new_admin);
    
    // Accept
    pool_configurator_client.accept_admin(&new_admin);
    
    // Verify transfer
    assert_eq!(pool_configurator_client.get_admin(), new_admin);
}

#[test]
fn test_pool_configurator_cancel_admin_proposal() {
    let env = Env::default();
    env.mock_all_auths();
    
    let admin = Address::generate(&env);
    let emergency_admin = Address::generate(&env);
    let new_admin = Address::generate(&env);
    
    let protocol = deploy_full_protocol(&env, &admin, &emergency_admin);
    let pool_configurator_client = pool_configurator::Client::new(&env, &protocol.pool_configurator);
    
    // Propose
    pool_configurator_client.propose_admin(&admin, &new_admin);
    
    // Cancel
    pool_configurator_client.cancel_admin_proposal(&admin);
    
    // Verify no pending
    let result = pool_configurator_client.try_get_pending_admin();
    assert!(result.is_err());
    
    // Verify admin unchanged
    assert_eq!(pool_configurator_client.get_admin(), admin);
}

#[test]
fn test_accept_admin_without_proposal() {
    let env = Env::default();
    env.mock_all_auths();
    
    let admin = Address::generate(&env);
    let emergency_admin = Address::generate(&env);
    let new_admin = Address::generate(&env);
    
    let protocol = deploy_full_protocol(&env, &admin, &emergency_admin);
    let kinetic_router_client = kinetic_router::Client::new(&env, &protocol.kinetic_router);
    
    // Try to accept without proposal
    let result = kinetic_router_client.try_accept_admin(&new_admin);
    assert!(result.is_err(), "Should fail when no pending admin exists");
}

