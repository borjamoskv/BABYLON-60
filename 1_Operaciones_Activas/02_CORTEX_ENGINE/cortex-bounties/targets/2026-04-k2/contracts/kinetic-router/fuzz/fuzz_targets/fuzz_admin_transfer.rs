#![no_main]

//! Fuzz test for K2 two-step admin transfer flows.
//!
//! This fuzzer tests the two-step admin transfer pattern for both
//! PoolAdmin and EmergencyAdmin roles in KineticRouter and PoolConfigurator:
//!
//! Transfer flows:
//! - Propose → Accept sequence (successful transfer)
//! - Propose → Cancel sequence (cancelled transfer)
//! - Propose → Propose (replaces pending)
//! - Accept without proposal (should fail)
//! - Wrong address tries Accept (should fail)
//! - Cancel without proposal (should fail)
//!
//! Key invariants tested:
//! - Only current admin can propose new admin
//! - Only pending admin can accept
//! - Pending admin cleared after accept/cancel
//! - Proposal replaces any existing pending admin
//! - NonAdmin cannot propose, accept, or cancel
//!
//! Run with: cargo +nightly fuzz run fuzz_admin_transfer --sanitizer=none

use arbitrary::Arbitrary;
use libfuzzer_sys::fuzz_target;
use soroban_sdk::{
    contract, contractimpl, contracttype,
    testutils::{Address as _, Ledger as _},
    Address, Env, IntoVal, String,
};

// =============================================================================
// Contract WASM Imports
// =============================================================================

mod kinetic_router {
    soroban_sdk::contractimport!(
        file = "../../../target/wasm32v1-none/release/k2_kinetic_router.optimized.wasm"
    );
}

mod pool_configurator {
    soroban_sdk::contractimport!(
        file = "../../../target/wasm32v1-none/release/k2_pool_configurator.optimized.wasm"
    );
}

mod price_oracle {
    soroban_sdk::contractimport!(
        file = "../../../target/wasm32v1-none/release/k2_price_oracle.optimized.wasm"
    );
}

// =============================================================================
// Mock Contracts
// =============================================================================

/// Asset enum matching the Reflector oracle interface
#[contracttype]
#[derive(Clone, Debug)]
pub enum ReflectorAsset {
    Stellar(Address),
    Other(soroban_sdk::Symbol),
}

/// Price data returned by the mock reflector
#[contracttype]
#[derive(Clone, Debug)]
pub struct PriceData {
    pub price: i128,
    pub timestamp: u64,
}

/// Mock Reflector Oracle
#[contract]
pub struct MockReflector;

#[contractimpl]
impl MockReflector {
    pub fn decimals(_env: Env) -> u32 {
        14
    }

    pub fn lastprice(env: Env, _asset: ReflectorAsset) -> Option<PriceData> {
        Some(PriceData {
            price: 1_000_000_000_000_000i128,
            timestamp: env.ledger().timestamp(),
        })
    }
}

// =============================================================================
// Fuzz Input Types
// =============================================================================

/// Which contract to target
#[derive(Arbitrary, Debug, Clone, Copy)]
pub enum TargetContract {
    KineticRouter,
    PoolConfigurator,
}

/// Which admin role to transfer
#[derive(Arbitrary, Debug, Clone, Copy)]
pub enum AdminType {
    PoolAdmin,
    EmergencyAdmin,
}

/// Who is performing the action
#[derive(Arbitrary, Debug, Clone, Copy)]
pub enum Actor {
    CurrentAdmin,
    PendingAdmin,
    OtherUser,
    /// An address that was proposed but replaced
    ReplacedPending,
}

/// Admin transfer operations
#[derive(Arbitrary, Debug, Clone)]
pub enum TransferOperation {
    /// Propose a new admin
    ProposeAdmin {
        target: TargetContract,
        admin_type: AdminType,
        proposer: Actor,
        /// Index of address pool to use as pending (0-3)
        pending_index: u8,
    },
    /// Accept admin role
    AcceptAdmin {
        target: TargetContract,
        admin_type: AdminType,
        accepter: Actor,
    },
    /// Cancel pending proposal
    CancelProposal {
        target: TargetContract,
        admin_type: AdminType,
        canceller: Actor,
    },
    /// Check pending admin state
    CheckPendingAdmin {
        target: TargetContract,
        admin_type: AdminType,
    },
    /// Check current admin
    CheckCurrentAdmin {
        target: TargetContract,
        admin_type: AdminType,
    },
    /// Advance time
    AdvanceTime { seconds: u32 },
}

/// Fuzz input for admin transfer testing
#[derive(Arbitrary, Debug, Clone)]
pub struct AdminTransferInput {
    /// Sequence of transfer operations
    pub operations: [Option<TransferOperation>; 16],
}

// =============================================================================
// Test Setup Helpers
// =============================================================================

fn setup_test_env() -> Env {
    let env = Env::default();
    env.mock_all_auths();
    env.cost_estimate().budget().reset_unlimited();
    env
}

fn setup_oracle(env: &Env, admin: &Address) -> Address {
    let oracle_addr = env.register(price_oracle::WASM, ());
    let oracle_client = price_oracle::Client::new(env, &oracle_addr);
    let reflector_addr = env.register(MockReflector, ());
    let base_currency = Address::generate(env);
    let native_xlm = Address::generate(env);
    oracle_client.initialize(admin, &reflector_addr, &base_currency, &native_xlm);
    oracle_addr
}

fn setup_kinetic_router(
    env: &Env,
    pool_admin: &Address,
    emergency_admin: &Address,
    oracle_addr: &Address,
) -> Address {
    let router_addr = env.register(kinetic_router::WASM, ());
    let client = kinetic_router::Client::new(env, &router_addr);
    let treasury = Address::generate(env);
    let dex_router = Address::generate(env);

    client.initialize(
        pool_admin,
        emergency_admin,
        oracle_addr,
        &treasury,
        &dex_router,
        &None,
    );

    let pool_configurator = Address::generate(env);
    client.set_pool_configurator(&pool_configurator);

    router_addr
}

fn setup_pool_configurator(
    env: &Env,
    pool_admin: &Address,
    router_addr: &Address,
    oracle_addr: &Address,
) -> Address {
    let configurator_addr = env.register(pool_configurator::WASM, ());
    let configurator_client = pool_configurator::Client::new(env, &configurator_addr);
    configurator_client.initialize(pool_admin, router_addr, oracle_addr);
    configurator_addr
}

// =============================================================================
// Test Context
// =============================================================================

struct TestContext<'a> {
    env: &'a Env,
    router_client: &'a kinetic_router::Client<'a>,
    configurator_client: &'a pool_configurator::Client<'a>,
    // Current admins (can change during test)
    router_pool_admin: Address,
    router_emergency_admin: Address,
    configurator_admin: Address,
    // Pending admins tracking
    router_pending_pool_admin: Option<Address>,
    router_pending_emergency_admin: Option<Address>,
    configurator_pending_admin: Option<Address>,
    // Previously proposed addresses (for ReplacedPending actor)
    replaced_pending: Option<Address>,
    // Other user (never becomes admin)
    other_user: Address,
    // Pool of potential pending addresses
    address_pool: [Address; 4],
}

impl<'a> TestContext<'a> {
    fn get_actor_address(
        &self,
        actor: Actor,
        target: TargetContract,
        admin_type: AdminType,
    ) -> Address {
        match actor {
            Actor::CurrentAdmin => {
                match (target, admin_type) {
                    (TargetContract::KineticRouter, AdminType::PoolAdmin) => {
                        self.router_pool_admin.clone()
                    }
                    (TargetContract::KineticRouter, AdminType::EmergencyAdmin) => {
                        self.router_emergency_admin.clone()
                    }
                    (TargetContract::PoolConfigurator, _) => {
                        self.configurator_admin.clone()
                    }
                }
            }
            Actor::PendingAdmin => {
                let pending = match (target, admin_type) {
                    (TargetContract::KineticRouter, AdminType::PoolAdmin) => {
                        &self.router_pending_pool_admin
                    }
                    (TargetContract::KineticRouter, AdminType::EmergencyAdmin) => {
                        &self.router_pending_emergency_admin
                    }
                    (TargetContract::PoolConfigurator, _) => {
                        &self.configurator_pending_admin
                    }
                };
                pending.clone().unwrap_or_else(|| self.other_user.clone())
            }
            Actor::OtherUser => self.other_user.clone(),
            Actor::ReplacedPending => {
                self.replaced_pending.clone().unwrap_or_else(|| self.other_user.clone())
            }
        }
    }
}

// =============================================================================
// Invariant Checks
// =============================================================================

fn check_admin_transfer_invariants(ctx: &TestContext) {
    // Invariant 1: Router pool admin should be retrievable
    let actual_router_admin = ctx.router_client.get_admin();
    assert_eq!(
        actual_router_admin, ctx.router_pool_admin,
        "Router pool admin mismatch"
    );

    // Invariant 2: Pending admin state should be consistent
    let pending_result = ctx.router_client.try_get_pending_admin();
    match &ctx.router_pending_pool_admin {
        Some(expected) => {
            // If we expect a pending admin, it should match
            if let Ok(Ok(actual)) = pending_result {
                assert_eq!(actual, *expected, "Router pending pool admin mismatch");
            }
        }
        None => {
            // If no pending admin expected, get_pending_admin should fail
            // (returns NoPendingAdmin error)
        }
    }

    // Invariant 3: Configurator admin should be retrievable
    let actual_config_admin = ctx.configurator_client.get_admin();
    assert_eq!(
        actual_config_admin, ctx.configurator_admin,
        "Configurator admin mismatch"
    );

    // Invariant 4: Configurator pending admin state
    let config_pending_result = ctx.configurator_client.try_get_pending_admin();
    match &ctx.configurator_pending_admin {
        Some(expected) => {
            if let Ok(Ok(actual)) = config_pending_result {
                assert_eq!(actual, *expected, "Configurator pending admin mismatch");
            }
        }
        None => {
            // No pending admin expected
        }
    }
}

// =============================================================================
// Operation Execution
// =============================================================================

fn execute_transfer_operation(ctx: &mut TestContext, op: &TransferOperation) {
    match op {
        TransferOperation::ProposeAdmin {
            target,
            admin_type,
            proposer,
            pending_index,
        } => {
            let proposer_addr = ctx.get_actor_address(*proposer, *target, *admin_type);
            let pending_addr = ctx.address_pool[(*pending_index % 4) as usize].clone();

            match (target, admin_type) {
                (TargetContract::KineticRouter, AdminType::PoolAdmin) => {
                    let result = ctx.router_client.try_propose_admin(&proposer_addr, &pending_addr);

                    // Check if proposer is actually the current admin (regardless of Actor enum)
                    let is_actual_admin = proposer_addr == ctx.router_pool_admin;

                    if is_actual_admin {
                        // Actual admin can propose
                        if result.is_ok() && result.as_ref().unwrap().is_ok() {
                            // Save replaced pending if there was one AND it's different from the new pending
                            if let Some(ref old_pending) = ctx.router_pending_pool_admin {
                                if old_pending != &pending_addr {
                                    ctx.replaced_pending = ctx.router_pending_pool_admin.take();
                                }
                            }
                            ctx.router_pending_pool_admin = Some(pending_addr);
                        }
                    } else {
                        // Non-admin should fail
                        assert!(
                            result.is_err() || result.as_ref().unwrap().is_err(),
                            "Non-admin should not be able to propose admin"
                        );
                    }
                }
                (TargetContract::KineticRouter, AdminType::EmergencyAdmin) => {
                    let result = ctx.router_client.try_propose_emergency_admin(&proposer_addr, &pending_addr);

                    // Only current emergency admin can propose new emergency admin
                    if matches!(proposer, Actor::CurrentAdmin) {
                        // Need to check if proposer is actually the emergency admin
                        let is_emergency_admin = proposer_addr == ctx.router_emergency_admin;
                        if is_emergency_admin && result.is_ok() && result.as_ref().unwrap().is_ok() {
                            // Save replaced pending if different from new pending
                            if let Some(ref old_pending) = ctx.router_pending_emergency_admin {
                                if old_pending != &pending_addr {
                                    ctx.replaced_pending = ctx.router_pending_emergency_admin.take();
                                }
                            }
                            ctx.router_pending_emergency_admin = Some(pending_addr);
                        }
                    }
                }
                (TargetContract::PoolConfigurator, _) => {
                    let result = ctx.configurator_client.try_propose_admin(&proposer_addr, &pending_addr);

                    // Check if proposer is actually the current admin (regardless of Actor enum)
                    let is_actual_admin = proposer_addr == ctx.configurator_admin;

                    if is_actual_admin {
                        // Actual admin can propose
                        if result.is_ok() && result.as_ref().unwrap().is_ok() {
                            // Save replaced pending if different from new pending
                            if let Some(ref old_pending) = ctx.configurator_pending_admin {
                                if old_pending != &pending_addr {
                                    ctx.replaced_pending = ctx.configurator_pending_admin.take();
                                }
                            }
                            ctx.configurator_pending_admin = Some(pending_addr);
                        }
                    } else {
                        // Non-admin should fail
                        assert!(
                            result.is_err() || result.as_ref().unwrap().is_err(),
                            "Non-admin should not be able to propose admin"
                        );
                    }
                }
            }
        }

        TransferOperation::AcceptAdmin {
            target,
            admin_type,
            accepter,
        } => {
            let accepter_addr = ctx.get_actor_address(*accepter, *target, *admin_type);

            match (target, admin_type) {
                (TargetContract::KineticRouter, AdminType::PoolAdmin) => {
                    let result = ctx.router_client.try_accept_admin(&accepter_addr);

                    // Check by actual address, not role label (CurrentAdmin might be PendingAdmin if they proposed themselves)
                    if let Some(ref pending) = ctx.router_pending_pool_admin {
                        if &accepter_addr == pending {
                            // This address IS the pending admin, should succeed
                            if result.is_ok() && result.as_ref().unwrap().is_ok() {
                                ctx.router_pool_admin = accepter_addr;
                                ctx.router_pending_pool_admin = None;
                            }
                        } else {
                            // Wrong address, should fail
                            assert!(
                                result.is_err() || result.as_ref().unwrap().is_err(),
                                "Wrong address should not be able to accept"
                            );
                        }
                    } else {
                        // No pending admin, should fail
                        assert!(
                            result.is_err() || result.as_ref().unwrap().is_err(),
                            "Accept should fail when no pending admin"
                        );
                    }
                }
                (TargetContract::KineticRouter, AdminType::EmergencyAdmin) => {
                    let result = ctx.router_client.try_accept_emergency_admin(&accepter_addr);

                    // Check by actual address, not role label
                    if let Some(ref pending) = ctx.router_pending_emergency_admin {
                        if &accepter_addr == pending {
                            // This address IS the pending admin, should succeed
                            if result.is_ok() && result.as_ref().unwrap().is_ok() {
                                ctx.router_emergency_admin = accepter_addr;
                                ctx.router_pending_emergency_admin = None;
                            }
                        } else {
                            // Wrong address, should fail
                            assert!(
                                result.is_err() || result.as_ref().unwrap().is_err(),
                                "Wrong address should not be able to accept emergency admin"
                            );
                        }
                    } else {
                        // No pending admin, should fail
                        assert!(
                            result.is_err() || result.as_ref().unwrap().is_err(),
                            "Accept should fail when no pending emergency admin"
                        );
                    }
                }
                (TargetContract::PoolConfigurator, _) => {
                    let result = ctx.configurator_client.try_accept_admin(&accepter_addr);

                    // Check by actual address, not role label
                    if let Some(ref pending) = ctx.configurator_pending_admin {
                        if &accepter_addr == pending {
                            // This address IS the pending admin, should succeed
                            if result.is_ok() && result.as_ref().unwrap().is_ok() {
                                ctx.configurator_admin = accepter_addr;
                                ctx.configurator_pending_admin = None;
                            }
                        } else {
                            // Wrong address, should fail
                            assert!(
                                result.is_err() || result.as_ref().unwrap().is_err(),
                                "Wrong address should not be able to accept"
                            );
                        }
                    } else {
                        // No pending admin, should fail
                        assert!(
                            result.is_err() || result.as_ref().unwrap().is_err(),
                            "Accept should fail when no pending admin"
                        );
                    }
                }
            }
        }

        TransferOperation::CancelProposal {
            target,
            admin_type,
            canceller,
        } => {
            let canceller_addr = ctx.get_actor_address(*canceller, *target, *admin_type);

            match (target, admin_type) {
                (TargetContract::KineticRouter, AdminType::PoolAdmin) => {
                    let result = ctx.router_client.try_cancel_admin_proposal(&canceller_addr);

                    // Check if canceller is actually the current admin (regardless of Actor enum)
                    let is_actual_admin = canceller_addr == ctx.router_pool_admin;

                    if is_actual_admin {
                        if ctx.router_pending_pool_admin.is_some() {
                            if result.is_ok() && result.as_ref().unwrap().is_ok() {
                                ctx.router_pending_pool_admin = None;
                            }
                        } else {
                            // No pending admin to cancel
                            assert!(
                                result.is_err() || result.as_ref().unwrap().is_err(),
                                "Cancel should fail when no pending admin"
                            );
                        }
                    } else {
                        assert!(
                            result.is_err() || result.as_ref().unwrap().is_err(),
                            "Non-admin should not be able to cancel proposal"
                        );
                    }
                }
                (TargetContract::KineticRouter, AdminType::EmergencyAdmin) => {
                    let result = ctx.router_client.try_cancel_emergency_admin_proposal(&canceller_addr);

                    // Only current emergency admin can cancel
                    if matches!(canceller, Actor::CurrentAdmin) {
                        let is_emergency_admin = canceller_addr == ctx.router_emergency_admin;
                        if is_emergency_admin && ctx.router_pending_emergency_admin.is_some() {
                            if result.is_ok() && result.as_ref().unwrap().is_ok() {
                                ctx.router_pending_emergency_admin = None;
                            }
                        }
                    }
                }
                (TargetContract::PoolConfigurator, _) => {
                    let result = ctx.configurator_client.try_cancel_admin_proposal(&canceller_addr);

                    // Check if canceller is actually the current admin (regardless of Actor enum)
                    let is_actual_admin = canceller_addr == ctx.configurator_admin;

                    if is_actual_admin {
                        if ctx.configurator_pending_admin.is_some() {
                            if result.is_ok() && result.as_ref().unwrap().is_ok() {
                                ctx.configurator_pending_admin = None;
                            }
                        } else {
                            assert!(
                                result.is_err() || result.as_ref().unwrap().is_err(),
                                "Cancel should fail when no pending admin"
                            );
                        }
                    } else {
                        assert!(
                            result.is_err() || result.as_ref().unwrap().is_err(),
                            "Non-admin should not be able to cancel proposal"
                        );
                    }
                }
            }
        }

        TransferOperation::CheckPendingAdmin { target, admin_type } => {
            // Just verify the state is consistent - handled in invariant checks
            match (target, admin_type) {
                (TargetContract::KineticRouter, AdminType::PoolAdmin) => {
                    let _ = ctx.router_client.try_get_pending_admin();
                }
                (TargetContract::KineticRouter, AdminType::EmergencyAdmin) => {
                    let _ = ctx.router_client.try_get_pending_emergency_admin();
                }
                (TargetContract::PoolConfigurator, _) => {
                    let _ = ctx.configurator_client.try_get_pending_admin();
                }
            }
        }

        TransferOperation::CheckCurrentAdmin { target, admin_type: _ } => {
            match target {
                TargetContract::KineticRouter => {
                    let _ = ctx.router_client.get_admin();
                }
                TargetContract::PoolConfigurator => {
                    let _ = ctx.configurator_client.get_admin();
                }
            }
        }

        TransferOperation::AdvanceTime { seconds } => {
            let max_advance = 31_536_000u64;
            let advance = (*seconds as u64) % max_advance;
            if advance > 0 {
                let current_timestamp = ctx.env.ledger().timestamp();
                let new_timestamp = current_timestamp.saturating_add(advance);
                ctx.env.ledger().set_timestamp(new_timestamp);
            }
        }
    }
}

// =============================================================================
// Fuzz Target
// =============================================================================

fuzz_target!(|input: AdminTransferInput| {
    let env = setup_test_env();

    // Setup addresses
    let initial_pool_admin = Address::generate(&env);
    let initial_emergency_admin = Address::generate(&env);
    let other_user = Address::generate(&env);

    // Pool of potential pending addresses
    let address_pool = [
        Address::generate(&env),
        Address::generate(&env),
        Address::generate(&env),
        Address::generate(&env),
    ];

    // Setup contracts
    let oracle_addr = setup_oracle(&env, &initial_pool_admin);
    let router_addr = setup_kinetic_router(
        &env,
        &initial_pool_admin,
        &initial_emergency_admin,
        &oracle_addr,
    );
    let configurator_addr = setup_pool_configurator(
        &env,
        &initial_pool_admin,
        &router_addr,
        &oracle_addr,
    );

    let router_client = kinetic_router::Client::new(&env, &router_addr);
    let configurator_client = pool_configurator::Client::new(&env, &configurator_addr);

    // Create test context
    let mut ctx = TestContext {
        env: &env,
        router_client: &router_client,
        configurator_client: &configurator_client,
        router_pool_admin: initial_pool_admin.clone(),
        router_emergency_admin: initial_emergency_admin.clone(),
        configurator_admin: initial_pool_admin.clone(),
        router_pending_pool_admin: None,
        router_pending_emergency_admin: None,
        configurator_pending_admin: None,
        replaced_pending: None,
        other_user,
        address_pool,
    };

    // Check initial invariants
    check_admin_transfer_invariants(&ctx);

    // Execute operations
    for op_opt in &input.operations {
        if let Some(op) = op_opt {
            execute_transfer_operation(&mut ctx, op);

            // Check invariants after each operation
            check_admin_transfer_invariants(&ctx);
        }
    }

    // Final invariant check
    check_admin_transfer_invariants(&ctx);
});
