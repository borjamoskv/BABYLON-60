use crate::storage;
use k2_shared::*;
use soroban_sdk::{Address, Env};

/// Pause the protocol (emergency admin or pool admin)
pub fn pause(env: Env, caller: Address) -> Result<(), KineticRouterError> {
    storage::validate_emergency_admin(&env, &caller)?;
    caller.require_auth();
    storage::set_paused(&env, true);
    Ok(())
}

/// M-04
/// Emergency admin can pause but cannot unpause, preventing a compromised
/// emergency key from undoing a deliberate pause set by the pool admin.
pub fn unpause(env: Env, caller: Address) -> Result<(), KineticRouterError> {
    storage::validate_admin(&env, &caller)?;
    caller.require_auth();
    storage::set_paused(&env, false);
    Ok(())
}
