use k2_shared::upgradeable::{admin, UpgradeError};
use crate::storage;
use soroban_sdk::{Address, BytesN, Env};

/// Contract version for tracking upgrades
/// Increment this with each upgrade
pub const VERSION: u32 = 3;

/// Initialize admin during contract deployment
pub fn initialize_admin(env: &Env, admin: &Address) {
    admin::set_admin(env, admin);
}

/// Get current admin address
pub fn get_admin(env: &Env) -> Result<Address, UpgradeError> {
    admin::get_admin(env)
}

/// Upgrade contract WASM
///
/// # Security
/// - Only admin can upgrade
/// - Requires admin authentication
/// - Uses Soroban deployer to update WASM
///
/// # Arguments
/// * `env` - Soroban environment
/// * `new_wasm_hash` - Hash of new WASM to deploy
///
/// # Returns
/// * `Ok(())` if upgrade successful
/// * `Err(UpgradeError::Unauthorized)` if caller is not admin
pub fn upgrade(env: Env, new_wasm_hash: BytesN<32>) -> Result<(), UpgradeError> {
    // Get admin and require authentication
    let admin = admin::get_admin(&env)?;
    admin.require_auth();

    // M-02
    if let Ok(pool_admin) = storage::get_pool_admin(&env) {
        pool_admin.require_auth();
    }

    // M-02: Sync access control flags before upgrade so new WASM has correct state
    storage::sync_access_control_flags(&env);

    // Perform upgrade using Soroban deployer
    env.deployer().update_current_contract_wasm(new_wasm_hash);

    Ok(())
}

/// Get contract version
pub fn version() -> u32 {
    VERSION
}
