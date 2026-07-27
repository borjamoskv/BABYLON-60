use soroban_sdk::{contracterror, Address, Env, Symbol};

// TTL constants: 1 year = 365 days * 17280 ledgers/day ≈ 6,307,200 ledgers
// Extend TTL when remaining time falls below 30 days
const TTL_THRESHOLD: u32 = 30 * 17280; // 30 days in ledgers
const TTL_EXTENSION: u32 = 365 * 17280; // 1 year in ledgers

/// Error conditions for upgradeable contract operations.
#[contracterror]
#[derive(Copy, Clone, Debug, Eq, PartialEq, PartialOrd, Ord)]
#[repr(u32)]
pub enum UpgradeError {
    Unauthorized = 1,
    InvalidWasmHash = 2,
    NoPendingAdmin = 3,
    InvalidPendingAdmin = 4,
}

/// Storage key for the primary admin address used by upgradeable contracts.
pub const ADMIN_KEY: Symbol = soroban_sdk::symbol_short!("ADMIN");
/// Storage key for the pending admin address (two-step transfer).
pub const PENDING_ADMIN_KEY: Symbol = soroban_sdk::symbol_short!("PUPGADM");

/// Module providing administrative access control functions for upgradeable contracts.
/// These functions support single-admin configurations.
pub mod admin {
    use super::*;

    /// Store the primary admin address in contract instance storage.
    pub fn set_admin(env: &Env, admin: &Address) {
        env.storage().instance().set(&ADMIN_KEY, admin);
        env.storage().instance().extend_ttl(TTL_THRESHOLD, TTL_EXTENSION);
    }

    /// Retrieve the primary admin address from contract instance storage.
    pub fn get_admin(env: &Env) -> Result<Address, UpgradeError> {
        let admin = env.storage()
            .instance()
            .get(&ADMIN_KEY)
            .ok_or(UpgradeError::Unauthorized)?;
        env.storage().instance().extend_ttl(TTL_THRESHOLD, TTL_EXTENSION);
        Ok(admin)
    }

    /// Validate that the caller has administrative privileges.
    /// Performs standard single-admin validation.
    pub fn require_admin(env: &Env, caller: &Address) -> Result<(), UpgradeError> {
        let admin = get_admin(env)?;
        if caller != &admin {
            return Err(UpgradeError::Unauthorized);
        }
        Ok(())
    }

    /// Propose a new admin address (two-step transfer, step 1).
    /// Only the current admin can propose a new admin.
    /// The proposed admin must call `accept_admin` to complete the transfer.
    /// 
    /// If a pending admin already exists, it will be replaced by the new proposal.
    pub fn propose_admin(env: &Env, caller: &Address, pending_admin: &Address) -> Result<(), UpgradeError> {
        require_admin(env, caller)?;
        caller.require_auth();
        
        // Check if there's an existing pending admin and emit cancellation event if so
        if let Ok(existing_pending) = get_pending_admin(env) {
            use crate::events::AdminProposalCancelledEvent;
            env.events().publish(
                (soroban_sdk::symbol_short!("adm_canc"),),
                AdminProposalCancelledEvent {
                    admin: caller.clone(),
                    cancelled_pending_admin: existing_pending,
                },
            );
        }
        
        env.storage().instance().set(&PENDING_ADMIN_KEY, pending_admin);
        env.storage().instance().extend_ttl(TTL_THRESHOLD, TTL_EXTENSION);
        
        // Emit event
        use crate::events::AdminProposedEvent;
        env.events().publish(
            (soroban_sdk::symbol_short!("adm_prop"),),
            AdminProposedEvent {
                current_admin: caller.clone(),
                pending_admin: pending_admin.clone(),
            },
        );
        
        Ok(())
    }

    /// Accept admin role (two-step transfer, step 2).
    /// Only the pending admin can call this to finalize the transfer.
    pub fn accept_admin(env: &Env, caller: &Address) -> Result<(), UpgradeError> {
        let pending_admin = get_pending_admin(env)?;
        if caller != &pending_admin {
            return Err(UpgradeError::InvalidPendingAdmin);
        }
        caller.require_auth();
        
        let previous_admin = get_admin(env)?;
        set_admin(env, caller);
        clear_pending_admin(env);
        
        // Emit event
        use crate::events::AdminAcceptedEvent;
        env.events().publish(
            (soroban_sdk::symbol_short!("adm_acc"),),
            AdminAcceptedEvent {
                previous_admin,
                new_admin: caller.clone(),
            },
        );
        
        Ok(())
    }

    /// Cancel a pending admin proposal.
    /// Only the current admin can cancel a pending proposal.
    pub fn cancel_admin_proposal(env: &Env, caller: &Address) -> Result<(), UpgradeError> {
        require_admin(env, caller)?;
        caller.require_auth();
        
        let cancelled_pending = get_pending_admin(env)?;
        clear_pending_admin(env);
        
        // Emit event
        use crate::events::AdminProposalCancelledEvent;
        env.events().publish(
            (soroban_sdk::symbol_short!("adm_canc"),),
            AdminProposalCancelledEvent {
                admin: caller.clone(),
                cancelled_pending_admin: cancelled_pending,
            },
        );
        
        Ok(())
    }

    /// Get the pending admin address, if any.
    pub fn get_pending_admin(env: &Env) -> Result<Address, UpgradeError> {
        let result = env.storage()
            .instance()
            .get(&PENDING_ADMIN_KEY)
            .ok_or(UpgradeError::NoPendingAdmin);
        if result.is_ok() {
            env.storage().instance().extend_ttl(TTL_THRESHOLD, TTL_EXTENSION);
        }
        result
    }

    /// Clear the pending admin (internal helper).
    fn clear_pending_admin(env: &Env) {
        if env.storage().instance().has(&PENDING_ADMIN_KEY) {
            env.storage().instance().remove(&PENDING_ADMIN_KEY);
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use soroban_sdk::{contract, contractimpl, testutils::Address as _, Env};

    #[contract]
    pub struct TestContract;

    #[contractimpl]
    impl TestContract {}

    #[test]
    fn test_admin_storage() {
        let env = Env::default();
        let contract_id = env.register_contract(None, TestContract);
        env.as_contract(&contract_id, || {
            let admin_addr = Address::generate(&env);

            admin::set_admin(&env, &admin_addr);
            let retrieved = admin::get_admin(&env).unwrap();

            assert_eq!(admin_addr, retrieved);
        });
    }

    #[test]
    fn test_require_admin_success() {
        let env = Env::default();
        let contract_id = env.register_contract(None, TestContract);
        env.as_contract(&contract_id, || {
            let admin_addr = Address::generate(&env);

            admin::set_admin(&env, &admin_addr);
            let result = admin::require_admin(&env, &admin_addr);

            assert!(result.is_ok());
        });
    }

    #[test]
    fn test_get_admin_not_initialized() {
        let env = Env::default();
        let contract_id = env.register_contract(None, TestContract);
        env.as_contract(&contract_id, || {
            let result = admin::get_admin(&env);
            assert_eq!(result, Err(UpgradeError::Unauthorized));
        });
    }

    #[test]
    fn test_require_admin_unauthorized() {
        let env = Env::default();
        let contract_id = env.register_contract(None, TestContract);
        env.as_contract(&contract_id, || {
            let admin_addr = Address::generate(&env);
            let other_addr = Address::generate(&env);

            admin::set_admin(&env, &admin_addr);
            let result = admin::require_admin(&env, &other_addr);

            assert_eq!(result, Err(UpgradeError::Unauthorized));
        });
    }

}
