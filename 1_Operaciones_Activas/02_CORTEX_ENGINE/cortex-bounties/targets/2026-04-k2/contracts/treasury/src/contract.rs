use crate::events;
use crate::storage;
use crate::error::TreasuryError;
use k2_shared::{safe_i128_to_u128, safe_u128_to_i128, upgradeable};
use soroban_sdk::{
    contract, contractimpl, panic_with_error, token, Address, Env, IntoVal, Map, Symbol, Vec,
};

#[contract]
pub struct TreasuryContract;

#[contractimpl]
impl TreasuryContract {
    pub fn __constructor(env: Env, admin: Address) {
        upgradeable::admin::set_admin(&env, &admin);
        storage::set_initialized(&env);

        events::publish_init(&env, admin);
    }

    /// Initialize the treasury contract with an admin address.
    ///
    /// The admin address is a single account.
    /// Once initialized, the contract cannot be reinitialized. This ensures the admin
    /// address remains consistent and prevents accidental reconfiguration.
    ///
    /// # Arguments
    /// * `env` - The execution environment
    /// * `admin` - Address of the admin (can be multisig contract for enhanced security)
    ///
    /// # Returns
    /// * `Ok(())` - Treasury initialized successfully
    /// * `Err(TreasuryError)` - Initialization failed (e.g., already initialized)
    pub fn initialize(_env: Env, _admin: Address) -> Result<(), TreasuryError> {
        panic!("TREASURY_ALREADY_INITIALIZED_AT_CONSTRUCTOR");
    }

    /// Record a deposit of tokens to the treasury.
    ///
    /// This function verifies that tokens have been transferred to the treasury contract
    /// address and updates internal balance tracking. Only the admin can call this function.
    /// The function verifies that the actual
    /// token balance is sufficient to support the claimed deposit amount to prevent fabricated balances.
    ///
    /// # Arguments
    /// * `env` - The execution environment
    /// * `caller` - Address of the caller (must be admin)
    /// * `asset` - Address of the token contract
    /// * `amount` - Amount of tokens being deposited (must be > 0)
    /// * `from` - Address that sent the tokens (for event tracking and audit trail)
    ///
    /// # Returns
    /// * `Ok(())` - Deposit recorded successfully
    /// * `Err(TreasuryError)` - Deposit failed (unauthorized, not initialized, invalid amount, transfer not verified, or overflow)
    pub fn deposit(
        env: Env,
        caller: Address,
        asset: Address,
        amount: u128,
        from: Address,
    ) -> Result<(), TreasuryError> {
        if !storage::is_initialized(&env) {
            return Err(TreasuryError::NotInitialized);
        }

        // Require admin authorization to prevent unauthorized balance fabrication
        storage::require_admin(&env, &caller)?;
        caller.require_auth();

        if amount == 0 {
            return Err(TreasuryError::InvalidAmount);
        }

        // Verify that the actual token balance is sufficient to support the deposit
        // This prevents fabricated balances beyond what actually exists in the treasury
        let token_client = token::Client::new(&env, &asset);
        let actual_balance = token_client.balance(&env.current_contract_address());
        if actual_balance < 0 {
            panic_with_error!(&env, TreasuryError::InvalidAmount);
        }
        // S-04
        let actual_balance_u128 = safe_i128_to_u128(&env, actual_balance);

        // Get current internal balance
        let internal_balance = storage::get_balance(&env, &asset);

        // Verify that actual balance >= internal balance + amount
        // This ensures we're not recording more than what actually exists
        let required_balance = internal_balance
            .checked_add(amount)
            .ok_or(TreasuryError::InvalidAmount)?;
        
        if actual_balance_u128 < required_balance {
            return Err(TreasuryError::TransferFailed);
        }

        // Only update internal accounting after verifying the transfer
        storage::add_balance(&env, &asset, amount)?;
        events::publish_deposit(&env, asset, amount, from);

        Ok(())
    }

    /// Sync balance from token contract and update internal tracking.
    ///
    /// This function queries the token contract's balance function to reconcile the
    /// actual balance held by the treasury with internal tracking. Use this when tokens
    /// are transferred directly to the treasury address without calling deposit(), such
    /// as when protocol fees are collected automatically.
    ///
    /// # Arguments
    /// * `env` - The execution environment
    /// * `asset` - Address of the token contract
    ///
    /// # Returns
    /// * `Ok(u128)` - Current balance synced from token contract
    /// * `Err(TreasuryError)` - Sync failed (not initialized or token contract query failed)
    pub fn sync_balance(env: Env, asset: Address) -> Result<u128, TreasuryError> {
        if !storage::is_initialized(&env) {
            return Err(TreasuryError::NotInitialized);
        }
        
        // Require admin authorization to sync balance
        let admin = upgradeable::admin::get_admin(&env).map_err(|_| TreasuryError::NotInitialized)?;
        admin.require_auth();
        let token_client = token::Client::new(&env, &asset);
        let balance = token_client.balance(&env.current_contract_address());

        if balance < 0 {
            panic_with_error!(&env, TreasuryError::InvalidAmount);
        }
        // S-04
        let balance_u128 = safe_i128_to_u128(&env, balance);
        storage::set_balance(&env, &asset, balance_u128)?;
        Ok(balance_u128)
    }

    /// Withdraw tokens from the treasury (admin only).
    ///
    /// This function performs two critical operations atomically: it updates internal
    /// balance tracking and transfers tokens to the recipient. If the token transfer
    /// fails, the balance update is reverted, ensuring consistency. Only authorized
    /// admins (or multisig contract if configured) can perform withdrawals.
    ///
    /// # Arguments
    /// * `env` - The execution environment
    /// * `caller` - Admin address (must be authorized - regular admin or multisig contract)
    /// * `asset` - Address of the token contract to withdraw
    /// * `amount` - Amount of tokens to withdraw (must be > 0 and <= available balance)
    /// * `to` - Address to receive the tokens
    ///
    /// # Returns
    /// * `Ok(())` - Withdrawal successful (balance updated and tokens transferred)
    /// * `Err(TreasuryError)` - Withdrawal failed (unauthorized, insufficient balance, or transfer failed)
    pub fn withdraw(
        env: Env,
        caller: Address,
        asset: Address,
        amount: u128,
        to: Address,
    ) -> Result<(), TreasuryError> {
        if !storage::is_initialized(&env) {
            return Err(TreasuryError::NotInitialized);
        }

        storage::require_admin(&env, &caller)?;
        caller.require_auth();

        if amount == 0 {
            return Err(TreasuryError::InvalidAmount);
        }

        storage::subtract_balance(&env, &asset, amount)?;

        // Use token::Client for standard Stellar token interface
        let token_client = token::Client::new(&env, &asset);
        token_client.transfer(
            &env.current_contract_address(),
            &to,
            &safe_u128_to_i128(&env, amount),
        );

        events::publish_withdraw(&env, asset, amount, to, caller);
        Ok(())
    }

    /// Get the balance of a specific asset in the treasury.
    ///
    /// Returns the internally tracked balance for the given asset. This may differ
    /// from the actual token contract balance if sync_balance() hasn't been called
    /// after direct transfers to the treasury address.
    ///
    /// # Arguments
    /// * `env` - The execution environment
    /// * `asset` - Address of the token contract
    ///
    /// # Returns
    /// * `u128` - Balance of the asset (0 if asset has never been deposited)
    pub fn get_balance(env: Env, asset: Address) -> u128 {
        storage::get_balance(&env, &asset)
    }

    /// Get all balances in the treasury.
    ///
    /// Returns a map of all assets that have been deposited to the treasury along
    /// with their tracked balances. Assets with zero balance are not included in
    /// the map.
    ///
    /// # Arguments
    /// * `env` - The execution environment
    ///
    /// # Returns
    /// * `Map<Address, u128>` - Map of asset addresses to their balances
    pub fn get_all_balances(env: Env) -> Result<Map<Address, u128>, TreasuryError> {
        storage::get_all_balances(&env)
    }

    /// Get the admin address.
    ///
    /// # Arguments
    /// * `env` - The execution environment
    ///
    /// # Returns
    /// * `Result<Address, TreasuryError>` - Admin address or error
    pub fn get_admin(env: Env) -> Result<Address, TreasuryError> {
        upgradeable::admin::get_admin(&env).map_err(|_| TreasuryError::NotInitialized)
    }

    /// Propose a new admin address (two-step transfer, step 1).
    /// Only the current admin can propose a new admin.
    /// The proposed admin must call `accept_admin` to complete the transfer.
    ///
    /// # Arguments
    /// * `env` - The execution environment
    /// * `caller` - Current admin address (must be authorized)
    /// * `pending_admin` - Proposed new admin address
    ///
    /// # Returns
    /// * `Ok(())` - Admin proposal created successfully
    /// * `Err(TreasuryError)` - Proposal failed (unauthorized or not initialized)
    pub fn propose_admin(
        env: Env,
        caller: Address,
        pending_admin: Address,
    ) -> Result<(), TreasuryError> {
        if !storage::is_initialized(&env) {
            return Err(TreasuryError::NotInitialized);
        }

        upgradeable::admin::propose_admin(&env, &caller, &pending_admin)
            .map_err(|e| match e {
                upgradeable::UpgradeError::Unauthorized => TreasuryError::Unauthorized,
                upgradeable::UpgradeError::NoPendingAdmin => TreasuryError::NoPendingAdmin,
                upgradeable::UpgradeError::InvalidPendingAdmin => TreasuryError::InvalidPendingAdmin,
                _ => TreasuryError::Unauthorized,
            })
    }

    /// Accept admin role (two-step transfer, step 2).
    /// Only the pending admin can call this to finalize the transfer.
    ///
    /// # Arguments
    /// * `env` - The execution environment
    /// * `caller` - Pending admin address (must be authorized)
    ///
    /// # Returns
    /// * `Ok(())` - Admin transfer completed successfully
    /// * `Err(TreasuryError)` - Transfer failed (not initialized, no pending admin, or invalid caller)
    pub fn accept_admin(env: Env, caller: Address) -> Result<(), TreasuryError> {
        if !storage::is_initialized(&env) {
            return Err(TreasuryError::NotInitialized);
        }

        upgradeable::admin::accept_admin(&env, &caller)
            .map_err(|e| match e {
                upgradeable::UpgradeError::Unauthorized => TreasuryError::Unauthorized,
                upgradeable::UpgradeError::NoPendingAdmin => TreasuryError::NoPendingAdmin,
                upgradeable::UpgradeError::InvalidPendingAdmin => TreasuryError::InvalidPendingAdmin,
                _ => TreasuryError::Unauthorized,
            })
    }

    /// Cancel a pending admin proposal.
    /// Only the current admin can cancel a pending proposal.
    ///
    /// # Arguments
    /// * `env` - The execution environment
    /// * `caller` - Current admin address (must be authorized)
    ///
    /// # Returns
    /// * `Ok(())` - Proposal cancelled successfully
    /// * `Err(TreasuryError)` - Cancellation failed (unauthorized, not initialized, or no pending admin)
    pub fn cancel_admin_proposal(env: Env, caller: Address) -> Result<(), TreasuryError> {
        if !storage::is_initialized(&env) {
            return Err(TreasuryError::NotInitialized);
        }

        upgradeable::admin::cancel_admin_proposal(&env, &caller)
            .map_err(|e| match e {
                upgradeable::UpgradeError::Unauthorized => TreasuryError::Unauthorized,
                upgradeable::UpgradeError::NoPendingAdmin => TreasuryError::NoPendingAdmin,
                upgradeable::UpgradeError::InvalidPendingAdmin => TreasuryError::InvalidPendingAdmin,
                _ => TreasuryError::Unauthorized,
            })
    }

    /// Get the pending admin address, if any.
    ///
    /// # Arguments
    /// * `env` - The execution environment
    ///
    /// # Returns
    /// * `Ok(Address)` - Pending admin address
    /// * `Err(TreasuryError)` - No pending admin proposal exists
    pub fn get_pending_admin(env: Env) -> Result<Address, TreasuryError> {
        upgradeable::admin::get_pending_admin(&env)
            .map_err(|e| match e {
                upgradeable::UpgradeError::NoPendingAdmin => TreasuryError::NoPendingAdmin,
                upgradeable::UpgradeError::InvalidPendingAdmin => TreasuryError::InvalidPendingAdmin,
                _ => TreasuryError::NoPendingAdmin,
            })
    }

}

