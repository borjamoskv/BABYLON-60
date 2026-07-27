#![cfg(test)]

//! # K2 Protocol Integration Tests
//!
//! This crate contains integration tests that test the interaction between
//! multiple K2 protocol contracts using compiled WASM binaries.
//!
//! ## Building
//!
//! Before running tests, build all contracts with optimization:
//! ```bash
//! stellar contract build
//! ```
//!
//! This creates optimized WASM files (< 128KB) in `target/wasm32v1-none/release/*.optimized.wasm`
//! which are used by the integration tests to match production deployments.
//!
//! ## Running Tests
//!
//! ```bash
//! cargo test -p k2-integration-tests
//! ```

// =============================================================================
// Contract WASM Imports
// =============================================================================

/// Kinetic Router - Main lending pool contract
/// Uses optimized WASM (< 128KB requirement)
pub mod kinetic_router {
    soroban_sdk::contractimport!(
        file = "../../target/wasm32v1-none/release/k2_kinetic_router.optimized.wasm"
    );
}

/// A-Token - Interest-bearing supply token
/// Uses optimized WASM
pub mod a_token {
    soroban_sdk::contractimport!(file = "../../target/wasm32v1-none/release/k2_a_token.optimized.wasm");
}

/// Debt Token - Variable debt token
/// Uses optimized WASM
pub mod debt_token {
    soroban_sdk::contractimport!(file = "../../target/wasm32v1-none/release/k2_debt_token.optimized.wasm");
}

/// Price Oracle - Asset price feeds
/// Uses optimized WASM
pub mod price_oracle {
    soroban_sdk::contractimport!(file = "../../target/wasm32v1-none/release/k2_price_oracle.optimized.wasm");
}

/// Interest Rate Strategy - Utilization-based rate model
/// Uses optimized WASM
pub mod interest_rate_strategy {
    soroban_sdk::contractimport!(
        file = "../../target/wasm32v1-none/release/k2_interest_rate_strategy.optimized.wasm"
    );
}

/// Incentives - Reward distribution
/// Uses optimized WASM
pub mod incentives {
    soroban_sdk::contractimport!(file = "../../target/wasm32v1-none/release/k2_incentives.optimized.wasm");
}

/// Treasury - Protocol fee collection
/// Uses optimized WASM
pub mod treasury {
    soroban_sdk::contractimport!(file = "../../target/wasm32v1-none/release/k2_treasury.optimized.wasm");
}

/// Pool Configurator - Reserve configuration
/// Uses optimized WASM
pub mod pool_configurator {
    soroban_sdk::contractimport!(
        file = "../../target/wasm32v1-none/release/k2_pool_configurator.optimized.wasm"
    );
}

/// Flash Liquidation Helper - Minimal contract for heavy validation logic
/// Uses optimized WASM
pub mod flash_liquidation_helper {
    soroban_sdk::contractimport!(
        file = "../../target/wasm32v1-none/release/k2_flash_liquidation_helper.optimized.wasm"
    );
}

/// Aquarius Swap Adapter - DEX adapter for Aquarius AMM
/// Uses optimized WASM
/// Disabled: Aquarius AMM WASM not available in standard build
// pub mod aquarius_swap_adapter {
//     soroban_sdk::contractimport!(
//         file = "../../target/wasm32v1-none/release/aquarius_swap_adapter.optimized.wasm"
//     );
// }

/// Soroswap Swap Adapter - DEX adapter for Soroswap
/// Uses optimized WASM
pub mod soroswap_swap_adapter {
    soroban_sdk::contractimport!(
        file = "../../target/wasm32v1-none/release/soroswap_swap_adapter.optimized.wasm"
    );
}


pub mod gas_tracking;
pub mod resource_analyzer;
pub mod setup;

// External Aquarius integration tests - requires external WASM binaries
// Disabled: external/aquarius contracts not available
// To enable: build Aquarius and place WASM files in external/aquarius/
// mod test_aquarius_integration;
// mod test_aquarius_k2_integration;
// mod test_k2_aquarius_full_integration;

mod test_auth;
mod test_flash_liquidation;
mod test_flash_liquidation_edge_cases;
mod test_flash_loan;
// mod test_flash_loan_dex_integration; // Requires Aquarius - disabled for standard builds
mod test_incentives;
mod test_interest_accrual;
mod test_lending_flow;
mod test_liquidation_flow;
mod test_liquidator;
mod test_oracle_integration;
mod test_prepare_execute_liquidation; // 2-step liquidation tests
// Deprecated: RedStone adapter removed in favor of direct custom oracle integration
// mod test_redstone_integration; // RedStone adapter integration tests
// mod test_redstone_feed_direct; // Requires external RedStone WASM - disabled for standard builds
mod test_reserve_fragmentation; // Reserve fragmentation attack mitigation tests
mod test_resource_analysis;
mod test_swap_collateral;
mod test_treasury;
mod test_upgrades;
mod poc_borrow_ltv_mismatch; // PoC test for borrow-limit inconsistency (FIND-043)
mod test_critical_flows; // Phase 4: Integration regression tests
mod poc_close_factor_bypass;
mod test_tracker_reset;

mod poc_liquidation_dos;
mod poc_execute_liquidation_bypass;
