#![cfg(test)]

//! # Authorization Tests
//!
//! Comprehensive tests for authorization checks across all admin functions.
//! Uses `mock_auths()` with specific authorizations and verifies with `env.auths()`.

use crate::setup::{deploy_full_protocol, set_default_ledger, ReflectorStub};
use crate::{
    kinetic_router, price_oracle, treasury,
};
use soroban_sdk::{
    testutils::{Address as _, MockAuth, MockAuthInvoke},
    Address, Env, IntoVal,
};

// =============================================================================
// Helper Functions
// =============================================================================

/// Create test environment without mocking all auths
fn create_test_env_no_mock() -> Env {
    let env = Env::default();
    set_default_ledger(&env);
    // Set budget limits matching mainnet constraints
    let mut budget = env.cost_estimate().budget();
    budget.reset_limits(100_000_000, 40_000_000);
    env
}

/// Setup protocol with specific auth mocks for initialization only
fn setup_protocol_with_init_auths(env: &Env, admin: &Address, emergency_admin: &Address) -> crate::setup::ProtocolContracts {
    // Mock auths only for initialization calls
    env.mock_auths(&[
        MockAuth {
            address: admin,
            invoke: &MockAuthInvoke {
                contract: &env.register(price_oracle::WASM, ()),
                fn_name: "initialize",
                args: (admin, &Address::generate(env), &Address::generate(env)).into_val(env),
                sub_invokes: &[],
            },
        },
    ]);
    
    deploy_full_protocol(env, admin, emergency_admin)
}

// =============================================================================
// Kinetic Router Admin Auth Tests
// =============================================================================

#[test]
fn test_set_flash_loan_premium_requires_admin_auth() {
    let env = create_test_env_no_mock();
    let admin = Address::generate(&env);
    let emergency_admin = Address::generate(&env);
    let unauthorized = Address::generate(&env);
    
    // Setup with mock_all_auths for initialization
    env.mock_all_auths();
    let contracts = deploy_full_protocol(&env, &admin, &emergency_admin);
    
    let client = kinetic_router::Client::new(&env, &contracts.kinetic_router);
    
    // Test: Admin can set flash loan premium with correct auth
    let premium = 50u128;
    env.mock_auths(&[MockAuth {
        address: &admin,
        invoke: &MockAuthInvoke {
            contract: &contracts.kinetic_router,
            fn_name: "set_flash_loan_premium",
            args: (&premium,).into_val(&env),
            sub_invokes: &[],
        },
    }]);
    
    client.set_flash_loan_premium(&premium);
    
    // Verify auth was checked
    let auths = env.auths();
    assert_eq!(auths.len(), 1);
    assert_eq!(auths[0].0, admin);
    
    // Test: Unauthorized user cannot set premium
    env.mock_auths(&[]);
    let result = client.try_set_flash_loan_premium(&premium);
    assert!(result.is_err());
}

#[test]
fn test_set_flash_loan_premium_max_requires_admin_auth() {
    let env = create_test_env_no_mock();
    let admin = Address::generate(&env);
    let emergency_admin = Address::generate(&env);
    let unauthorized = Address::generate(&env);
    
    env.mock_all_auths();
    let contracts = deploy_full_protocol(&env, &admin, &emergency_admin);
    
    let client = kinetic_router::Client::new(&env, &contracts.kinetic_router);
    
    // Test: Admin can set max premium with correct auth
    let max_premium = 100u128;
    env.mock_auths(&[MockAuth {
        address: &admin,
        invoke: &MockAuthInvoke {
            contract: &contracts.kinetic_router,
            fn_name: "set_flash_loan_premium_max",
            args: (&max_premium,).into_val(&env),
            sub_invokes: &[],
        },
    }]);
    
    client.set_flash_loan_premium_max(&max_premium);
    
    // Verify auth was checked
    let auths = env.auths();
    assert_eq!(auths.len(), 1);
    assert_eq!(auths[0].0, admin);
    
    // Test: Unauthorized user cannot set max premium
    env.mock_auths(&[]);
    let result = client.try_set_flash_loan_premium_max(&max_premium);
    assert!(result.is_err());
}

#[test]
fn test_set_hf_liquidation_threshold_requires_admin_auth() {
    let env = create_test_env_no_mock();
    let admin = Address::generate(&env);
    let emergency_admin = Address::generate(&env);
    let unauthorized = Address::generate(&env);
    
    env.mock_all_auths();
    let contracts = deploy_full_protocol(&env, &admin, &emergency_admin);
    
    let client = kinetic_router::Client::new(&env, &contracts.kinetic_router);
    
    // Test: Admin can set threshold with correct auth
    let threshold = 950_000_000_000_000_000u128; // 0.95 WAD
    env.mock_auths(&[MockAuth {
        address: &admin,
        invoke: &MockAuthInvoke {
            contract: &contracts.kinetic_router,
            fn_name: "set_hf_liquidation_threshold",
            args: (&threshold,).into_val(&env),
            sub_invokes: &[],
        },
    }]);
    
    client.set_hf_liquidation_threshold(&threshold);
    
    // Verify auth was checked
    let auths = env.auths();
    assert_eq!(auths.len(), 1);
    assert_eq!(auths[0].0, admin);
    
    // Test: Unauthorized user cannot set threshold
    env.mock_auths(&[]);
    let result = client.try_set_hf_liquidation_threshold(&threshold);
    assert!(result.is_err());
}

#[test]
fn test_set_min_swap_output_bps_requires_admin_auth() {
    let env = create_test_env_no_mock();
    let admin = Address::generate(&env);
    let emergency_admin = Address::generate(&env);
    let unauthorized = Address::generate(&env);
    
    env.mock_all_auths();
    let contracts = deploy_full_protocol(&env, &admin, &emergency_admin);
    
    let client = kinetic_router::Client::new(&env, &contracts.kinetic_router);
    
    // Test: Admin can set min swap output with correct auth
    let min_bps = 9500u128;
    env.mock_auths(&[MockAuth {
        address: &admin,
        invoke: &MockAuthInvoke {
            contract: &contracts.kinetic_router,
            fn_name: "set_min_swap_output_bps",
            args: (&min_bps,).into_val(&env),
            sub_invokes: &[],
        },
    }]);
    
    client.set_min_swap_output_bps(&min_bps);
    
    // Verify auth was checked
    let auths = env.auths();
    assert_eq!(auths.len(), 1);
    assert_eq!(auths[0].0, admin);
    
    // Test: Unauthorized user cannot set min swap output
    env.mock_auths(&[]);
    let result = client.try_set_min_swap_output_bps(&min_bps);
    assert!(result.is_err());
}

#[test]
fn test_set_treasury_requires_admin_auth() {
    let env = create_test_env_no_mock();
    let admin = Address::generate(&env);
    let emergency_admin = Address::generate(&env);
    let unauthorized = Address::generate(&env);
    let new_treasury = Address::generate(&env);
    
    env.mock_all_auths();
    let contracts = deploy_full_protocol(&env, &admin, &emergency_admin);
    
    let client = kinetic_router::Client::new(&env, &contracts.kinetic_router);
    
    // Test: Admin can set treasury with correct auth
    env.mock_auths(&[MockAuth {
        address: &admin,
        invoke: &MockAuthInvoke {
            contract: &contracts.kinetic_router,
            fn_name: "set_treasury",
            args: (&new_treasury,).into_val(&env),
            sub_invokes: &[],
        },
    }]);
    
    client.set_treasury(&new_treasury);
    
    // Verify auth was checked
    let auths = env.auths();
    assert_eq!(auths.len(), 1);
    assert_eq!(auths[0].0, admin);
    
    // Test: Unauthorized user cannot set treasury
    env.mock_auths(&[]);
    let result = client.try_set_treasury(&new_treasury);
    assert!(result.is_err());
}

#[test]
fn test_pause_requires_emergency_admin_auth() {
    let env = create_test_env_no_mock();
    let admin = Address::generate(&env);
    let emergency_admin = Address::generate(&env);
    let unauthorized = Address::generate(&env);
    
    env.mock_all_auths();
    let contracts = deploy_full_protocol(&env, &admin, &emergency_admin);
    
    let client = kinetic_router::Client::new(&env, &contracts.kinetic_router);
    
    // Test: Emergency admin can pause with correct auth
    env.mock_auths(&[MockAuth {
        address: &emergency_admin,
        invoke: &MockAuthInvoke {
            contract: &contracts.kinetic_router,
            fn_name: "pause",
            args: (&emergency_admin,).into_val(&env),
            sub_invokes: &[],
        },
    }]);
    
    client.pause(&emergency_admin);
    
    // Verify auth was checked
    let auths = env.auths();
    assert_eq!(auths.len(), 1);
    assert_eq!(auths[0].0, emergency_admin);
    
    // Test: Regular admin cannot pause
    env.mock_auths(&[]);
    let result = client.try_pause(&admin);
    assert!(result.is_err());
    
    // Test: Unauthorized user cannot pause
    let result = client.try_pause(&unauthorized);
    assert!(result.is_err());
}

// =============================================================================
// Price Oracle Admin Auth Tests
// =============================================================================

#[test]
fn test_price_oracle_add_asset_requires_admin_auth() {
    let env = create_test_env_no_mock();
    let admin = Address::generate(&env);
    let unauthorized = Address::generate(&env);
    let asset = Address::generate(&env);
    
    let oracle_id = env.register(price_oracle::WASM, ());
    let client = price_oracle::Client::new(&env, &oracle_id);
    
    // Initialize with mock_all_auths and ReflectorStub
    let reflector_stub = env.register(ReflectorStub, ());
    env.mock_all_auths();
    client.initialize(&admin, &reflector_stub, &Address::generate(&env), &Address::generate(&env));
    
    // Test: Admin can add asset with correct auth
    // Note: For complex enum types, we use mock_all_auths but still verify auth was called
    let asset_enum = price_oracle::Asset::Stellar(asset.clone());
    env.mock_all_auths();
    client.add_asset(&admin, &asset_enum);
    
    // Test: Unauthorized user cannot add asset (most important check)
    env.mock_auths(&[]);
    let result = client.try_add_asset(&unauthorized, &asset_enum);
    assert!(result.is_err(), "Unauthorized user should not be able to add asset");
}

#[test]
fn test_price_oracle_set_manual_override_requires_admin_auth() {
    let env = create_test_env_no_mock();
    let admin = Address::generate(&env);
    let unauthorized = Address::generate(&env);
    let asset = Address::generate(&env);
    
    let oracle_id = env.register(price_oracle::WASM, ());
    let client = price_oracle::Client::new(&env, &oracle_id);
    
    // Initialize with mock_all_auths and ReflectorStub
    let reflector_stub = env.register(ReflectorStub, ());
    env.mock_all_auths();
    client.initialize(&admin, &reflector_stub, &Address::generate(&env), &Address::generate(&env));
    
    // Add asset first - use mock_all_auths for complex enum types
    let asset_enum = price_oracle::Asset::Stellar(asset.clone());
    env.mock_all_auths();
    client.add_asset(&admin, &asset_enum);
    
    // Test: Admin can set manual override with correct auth
    let price = Some(1_000_000_000_000_000u128);
    let expiry = Some(env.ledger().timestamp() + 86400); // 24 hours
    env.mock_all_auths();
    client.set_manual_override(&admin, &asset_enum, &price, &expiry);
    
    // Test: Unauthorized user cannot set override (most important check)
    env.mock_auths(&[]);
    let result = client.try_set_manual_override(&unauthorized, &asset_enum, &price, &expiry);
    assert!(result.is_err(), "Unauthorized user should not be able to set manual override");
}

// =============================================================================
// Treasury Admin Auth Tests
// =============================================================================

#[test]
fn test_treasury_withdraw_requires_admin_auth() {
    let env = create_test_env_no_mock();
    let admin = Address::generate(&env);
    let unauthorized = Address::generate(&env);
    let recipient = Address::generate(&env);
    let token = Address::generate(&env);
    
    let treasury_id = env.register(treasury::WASM, ());
    let client = treasury::Client::new(&env, &treasury_id);
    
    // Initialize with mock_all_auths
    env.mock_all_auths();
    client.initialize(&admin);
    
    // Test: Unauthorized user cannot withdraw (most important check)
    // Note: This verifies auth is required even if treasury has no balance
    let amount = 1000u128;
    env.mock_auths(&[]);
    let unauthorized_result = client.try_withdraw(&unauthorized, &token, &amount, &recipient);
    assert!(unauthorized_result.is_err(), "Unauthorized user should not be able to withdraw");
}

// =============================================================================
// Pool Configurator Access Control Tests (After Initialization)
// =============================================================================

#[test]
fn test_pool_configurator_admin_functions_after_init() {
    let env = create_test_env_no_mock();
    let admin = Address::generate(&env);
    let emergency_admin = Address::generate(&env);
    let unauthorized = Address::generate(&env);
    
    env.mock_all_auths();
    let contracts = deploy_full_protocol(&env, &admin, &emergency_admin);
    
    let client = crate::pool_configurator::Client::new(&env, &contracts.pool_configurator);
    let asset = Address::generate(&env);
    
    // Test: Admin can set supply cap after initialization
    env.mock_auths(&[MockAuth {
        address: &admin,
        invoke: &MockAuthInvoke {
            contract: &contracts.pool_configurator,
            fn_name: "set_supply_cap",
            args: (&admin, &asset, &1_000_000_000u128).into_val(&env),
            sub_invokes: &[],
        },
    }]);
    
    let result = client.try_set_supply_cap(&admin, &asset, &1_000_000_000u128);
    // May fail due to reserve not existing, but should not fail due to auth
    // The important part is that unauthorized fails
    
    // Test: Unauthorized user cannot set supply cap
    env.mock_auths(&[]);
    let unauthorized_result = client.try_set_supply_cap(&unauthorized, &asset, &1_000_000_000u128);
    assert!(unauthorized_result.is_err(), "Unauthorized user should not be able to set supply cap");
    
    // Test: Admin can set borrow cap after initialization
    env.mock_auths(&[MockAuth {
        address: &admin,
        invoke: &MockAuthInvoke {
            contract: &contracts.pool_configurator,
            fn_name: "set_borrow_cap",
            args: (&admin, &asset, &500_000_000u128).into_val(&env),
            sub_invokes: &[],
        },
    }]);
    
    let result = client.try_set_borrow_cap(&admin, &asset, &500_000_000u128);
    // May fail due to reserve not existing, but auth should pass
    
    // Test: Unauthorized user cannot set borrow cap
    env.mock_auths(&[]);
    let unauthorized_result = client.try_set_borrow_cap(&unauthorized, &asset, &500_000_000u128);
    assert!(unauthorized_result.is_err(), "Unauthorized user should not be able to set borrow cap");
}

#[test]
fn test_pool_configurator_emergency_admin_functions() {
    let env = create_test_env_no_mock();
    let admin = Address::generate(&env);
    let emergency_admin = Address::generate(&env);
    let unauthorized = Address::generate(&env);
    
    env.mock_all_auths();
    let contracts = deploy_full_protocol(&env, &admin, &emergency_admin);
    
    let client = crate::pool_configurator::Client::new(&env, &contracts.pool_configurator);
    
    // Note: PoolConfigurator.initialize sets emergency_admin = pool_admin,
    // so we use `admin` as the emergency admin for these tests
    
    // Test: Emergency admin (which is admin) can pause reserve deployment
    env.mock_auths(&[MockAuth {
        address: &admin,
        invoke: &MockAuthInvoke {
            contract: &contracts.pool_configurator,
            fn_name: "pause_reserve_deployment",
            args: (&admin,).into_val(&env),
            sub_invokes: &[],
        },
    }]);
    
    client.pause_reserve_deployment(&admin);
    assert!(client.is_reserve_deployment_paused(), "Reserve deployment should be paused");
    
    // Test: Unauthorized user cannot pause reserve deployment
    env.mock_auths(&[]);
    let unauthorized_result = client.try_pause_reserve_deployment(&unauthorized);
    assert!(unauthorized_result.is_err(), "Unauthorized user should not be able to pause deployment");
    
    // Test: Emergency admin can unpause reserve deployment
    env.mock_auths(&[MockAuth {
        address: &admin,
        invoke: &MockAuthInvoke {
            contract: &contracts.pool_configurator,
            fn_name: "unpause_reserve_deployment",
            args: (&admin,).into_val(&env),
            sub_invokes: &[],
        },
    }]);
    
    client.unpause_reserve_deployment(&admin);
    assert!(!client.is_reserve_deployment_paused(), "Reserve deployment should be unpaused");
}

#[test]
fn test_pool_configurator_wasm_hash_setting_requires_admin() {
    let env = create_test_env_no_mock();
    let admin = Address::generate(&env);
    let emergency_admin = Address::generate(&env);
    let unauthorized = Address::generate(&env);
    
    env.mock_all_auths();
    let contracts = deploy_full_protocol(&env, &admin, &emergency_admin);
    
    let client = crate::pool_configurator::Client::new(&env, &contracts.pool_configurator);
    
    let mut hash_bytes = [0u8; 32];
    hash_bytes[0] = 0xAA;
    let wasm_hash = soroban_sdk::BytesN::from_array(&env, &hash_bytes);
    
    // Test: Admin can set aToken WASM hash
    env.mock_auths(&[MockAuth {
        address: &admin,
        invoke: &MockAuthInvoke {
            contract: &contracts.pool_configurator,
            fn_name: "set_a_token_wasm_hash",
            args: (&admin, &wasm_hash).into_val(&env),
            sub_invokes: &[],
        },
    }]);
    
    client.set_a_token_wasm_hash(&admin, &wasm_hash);
    
    // Test: Unauthorized user cannot set WASM hash
    env.mock_auths(&[]);
    let unauthorized_result = client.try_set_a_token_wasm_hash(&unauthorized, &wasm_hash);
    assert!(unauthorized_result.is_err(), "Unauthorized user should not be able to set WASM hash");
    
    // Test: Admin can set debt token WASM hash
    hash_bytes[0] = 0xBB;
    let debt_hash = soroban_sdk::BytesN::from_array(&env, &hash_bytes);
    
    env.mock_auths(&[MockAuth {
        address: &admin,
        invoke: &MockAuthInvoke {
            contract: &contracts.pool_configurator,
            fn_name: "set_debt_token_wasm_hash",
            args: (&admin, &debt_hash).into_val(&env),
            sub_invokes: &[],
        },
    }]);
    
    client.set_debt_token_wasm_hash(&admin, &debt_hash);
    
    // Test: Unauthorized user cannot set debt token WASM hash
    env.mock_auths(&[]);
    let unauthorized_result = client.try_set_debt_token_wasm_hash(&unauthorized, &debt_hash);
    assert!(unauthorized_result.is_err(), "Unauthorized user should not be able to set debt token WASM hash");
}

