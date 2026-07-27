#![cfg(test)]

//! # K2 Protocol Unit Tests
//!
//! Unit tests using WASM-backed contract registration for accurate resource measurement.
//! 
//! ## Building
//! 
//! Before running tests, build all contracts:
//! ```bash
//! stellar contract build
//! ```
//! 
//! ## Running Tests
//! 
//! ```bash
//! cargo test -p k2-unit-tests
//! ```

// =============================================================================
// Contract WASM Imports
// =============================================================================

/// Kinetic Router - Main lending pool contract
pub mod kinetic_router {
    soroban_sdk::contractimport!(
        file = "../../target/wasm32v1-none/release/k2_kinetic_router.optimized.wasm"
    );
}

/// A-Token - Interest-bearing supply token
pub mod a_token {
    soroban_sdk::contractimport!(file = "../../target/wasm32v1-none/release/k2_a_token.optimized.wasm");
}

/// Debt Token - Variable debt token
pub mod debt_token {
    soroban_sdk::contractimport!(file = "../../target/wasm32v1-none/release/k2_debt_token.optimized.wasm");
}

/// Price Oracle - Asset price feeds
pub mod price_oracle {
    soroban_sdk::contractimport!(file = "../../target/wasm32v1-none/release/k2_price_oracle.optimized.wasm");
}

/// Interest Rate Strategy - Utilization-based rate model
pub mod interest_rate_strategy {
    soroban_sdk::contractimport!(
        file = "../../target/wasm32v1-none/release/k2_interest_rate_strategy.optimized.wasm"
    );
}

/// Incentives - Reward distribution
pub mod incentives {
    soroban_sdk::contractimport!(file = "../../target/wasm32v1-none/release/k2_incentives.optimized.wasm");
}

/// Treasury - Protocol fee collection
pub mod treasury {
    soroban_sdk::contractimport!(file = "../../target/wasm32v1-none/release/k2_treasury.optimized.wasm");
}

/// Pool Configurator - Reserve configuration
pub mod pool_configurator {
    soroban_sdk::contractimport!(
        file = "../../target/wasm32v1-none/release/k2_pool_configurator.optimized.wasm"
    );
}

/// Flash Liquidation Helper - Validation logic
pub mod flash_liquidation_helper {
    soroban_sdk::contractimport!(
        file = "../../target/wasm32v1-none/release/k2_flash_liquidation_helper.optimized.wasm"
    );
}

/// Liquidation Engine - Liquidation logic
pub mod liquidation_engine {
    soroban_sdk::contractimport!(
        file = "../../target/wasm32v1-none/release/k2_liquidation_engine.optimized.wasm"
    );
}

/// Base Token - Standard SEP-41 token
pub mod base_token {
    soroban_sdk::contractimport!(file = "../../target/wasm32v1-none/release/k2_token.optimized.wasm");
}


// =============================================================================
// Test Modules
// =============================================================================

mod a_token_test;
mod debt_token_test;
mod flash_liquidation_helper_test;
mod incentives_auth_bypass_poc;
mod incentives_distribution_end_test;
mod incentives_test;
mod interest_rate_strategy_test;
mod kinetic_router_functional_tests;
mod kinetic_router_reserve_id_collision_poc;
mod kinetic_router_test;
mod kinetic_router_test_blacklist;
mod kinetic_router_test_blacklist_bypass;
mod kinetic_router_test_flash_loan;
mod kinetic_router_test_gated_pool;
mod kinetic_router_test_health_factor_validation;
mod kinetic_router_test_large_numbers;
mod kinetic_router_test_liquidation;
mod kinetic_router_test_liquidation_whitelist;
mod kinetic_router_test_price_calc;
mod kinetic_router_test_recipient_validation;
mod kinetic_router_test_reserve_id_fix;
mod kinetic_router_test_supply_borrow;
mod kinetic_router_test_upgrade;
mod kinetic_router_test_execute_operation_security;
mod kinetic_router_test_dynamic_precision;
mod liquidation_engine_test;
mod pool_configurator_test;
mod price_oracle_test;
mod price_oracle_test_precision;
mod price_oracle_test_stub;
mod price_oracle_test_stub_internal;
mod price_oracle_test_upgrade;
// Deprecated: RedStone adapter removed in favor of direct custom oracle integration
// mod redstone_adapter_test;
// mod redstone_adapter_test_process_payload;
mod treasury_test;

mod audit_finding_03_fix_verification;
mod audit_remediation_coverage;
mod kinetic_router_test_auth_edge;
mod kinetic_router_test_invariants;
mod kinetic_router_test_coverage;
mod kinetic_router_test_safety;

mod atoken_transfer_bitmap_desync;
mod audit_poc_pr78;
mod kinetic_router_test_optimizations;
mod poc_stale_threshold_withdraw;
mod token_test;
