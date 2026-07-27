use k2_shared::upgradeable::{admin, UpgradeError};
use soroban_sdk::{Address, BytesN, Env};

pub const VERSION: u32 = 2;

pub fn initialize_admin(env: &Env, admin: &Address) {
    admin::set_admin(env, admin);
}

pub fn get_admin(env: &Env) -> Result<Address, UpgradeError> {
    admin::get_admin(env)
}

pub fn upgrade(env: Env, new_wasm_hash: BytesN<32>) -> Result<(), UpgradeError> {
    let admin = admin::get_admin(&env)?;
    admin.require_auth();
    env.deployer().update_current_contract_wasm(new_wasm_hash);
    Ok(())
}

pub fn version() -> u32 {
    VERSION
}




