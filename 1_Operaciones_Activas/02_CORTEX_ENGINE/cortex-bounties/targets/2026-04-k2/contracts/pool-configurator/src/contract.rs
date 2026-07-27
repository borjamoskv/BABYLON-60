use crate::oracle;
use crate::reserve;
use crate::storage;
use k2_shared::{InitReserveParams, *};
use soroban_sdk::{
    contract, contractimpl, panic_with_error, symbol_short, Address, BytesN, Env, IntoVal, String, Vec,
};

#[contract]
pub struct PoolConfiguratorContract;

#[contractimpl]
impl PoolConfiguratorContract {
    pub fn __constructor(
        env: Env,
        pool_admin: Address,
        kinetic_router: Address,
        price_oracle: Address,
    ) {
        if storage::is_initialized(&env) {
            panic!("Already initialized");
        }

        crate::upgrade::initialize_admin(&env, &pool_admin);
        storage::set_pool_admin(&env, &pool_admin);
        storage::set_emergency_admin(&env, &pool_admin);
        storage::set_kinetic_router(&env, &kinetic_router);
        storage::set_price_oracle(&env, &price_oracle);
        storage::set_initialized(&env);
    }

    pub fn initialize(
        _env: Env,
        _pool_admin: Address,
        _kinetic_router: Address,
        _price_oracle: Address,
    ) -> Result<(), KineticRouterError> {
        panic!("Initialization is atomic at deployment. Use __constructor.");
    }

    pub fn init_reserve(
        env: Env,
        caller: Address,
        underlying_asset: Address,
        a_token_impl: Address,
        variable_debt_impl: Address,
        interest_rate_strategy: Address,
        treasury: Address,
        params: InitReserveParams,
    ) -> Result<(), KineticRouterError> {
        reserve::init_reserve(
            &env,
            &caller,
            &underlying_asset,
            &a_token_impl,
            &variable_debt_impl,
            &interest_rate_strategy,
            &treasury,
            params,
        )
    }

    /// Store the aToken WASM hash for factory deployments.
    /// Must be called by admin before deploying reserves via factory.
    pub fn set_a_token_wasm_hash(
        env: Env,
        caller: Address,
        hash: BytesN<32>,
    ) -> Result<(), KineticRouterError> {
        caller.require_auth();
        storage::validate_admin(&env, &caller)?;
        storage::set_a_token_wasm_hash(&env, &hash);

        // Emit event to enable off-chain monitoring of critical contract code changes
        env.events().publish(
            (
                symbol_short!("atoken"),
                symbol_short!("wasm"),
                symbol_short!("hash"),
            ),
            hash,
        );

        Ok(())
    }

    /// Store the debt token WASM hash for factory deployments.
    /// Must be called by admin before deploying reserves via factory.
    pub fn set_debt_token_wasm_hash(
        env: Env,
        caller: Address,
        hash: BytesN<32>,
    ) -> Result<(), KineticRouterError> {
        caller.require_auth();
        storage::validate_admin(&env, &caller)?;
        storage::set_debt_token_wasm_hash(&env, &hash);

        // Emit event to enable off-chain monitoring of critical contract code changes
        env.events().publish(
            (
                symbol_short!("debt"),
                symbol_short!("token"),
                symbol_short!("wasm"),
                symbol_short!("hash"),
            ),
            hash,
        );

        Ok(())
    }

    /// Deploy and initialize aToken and debt token contracts, then register the reserve.
    /// Returns (aToken_address, debt_token_address).
    pub fn deploy_and_init_reserve(
        env: Env,
        caller: Address,
        underlying_asset: Address,
        interest_rate_strategy: Address,
        treasury: Address,
        a_token_name: String,
        a_token_symbol: String,
        debt_token_name: String,
        debt_token_symbol: String,
        params: InitReserveParams,
    ) -> Result<(Address, Address), KineticRouterError> {
        reserve::deploy_and_init_reserve(
            &env,
            &caller,
            &underlying_asset,
            &interest_rate_strategy,
            &treasury,
            a_token_name,
            a_token_symbol,
            debt_token_name,
            debt_token_symbol,
            params,
        )
    }

    pub fn configure_reserve_as_collateral(
        env: Env,
        caller: Address,
        asset: Address,
        ltv: u32,
        liquidation_threshold: u32,
        liquidation_bonus: u32,
    ) -> Result<(), KineticRouterError> {
        reserve::configure_reserve_as_collateral(
            &env,
            &caller,
            &asset,
            ltv,
            liquidation_threshold,
            liquidation_bonus,
        )
    }

    pub fn enable_borrowing_on_reserve(
        env: Env,
        caller: Address,
        asset: Address,
        stable_rate_enabled: bool,
    ) -> Result<(), KineticRouterError> {
        reserve::enable_borrowing_on_reserve(&env, &caller, &asset, stable_rate_enabled)
    }

    pub fn set_reserve_active(
        env: Env,
        caller: Address,
        asset: Address,
        active: bool,
    ) -> Result<(), KineticRouterError> {
        reserve::set_reserve_active(&env, &caller, &asset, active)
    }

    pub fn set_reserve_freeze(
        env: Env,
        caller: Address,
        asset: Address,
        freeze: bool,
    ) -> Result<(), KineticRouterError> {
        reserve::set_reserve_freeze(&env, &caller, &asset, freeze)
    }

    pub fn set_reserve_pause(
        env: Env,
        caller: Address,
        asset: Address,
        paused: bool,
    ) -> Result<(), KineticRouterError> {
        reserve::set_reserve_pause(&env, &caller, &asset, paused)
    }

    pub fn set_reserve_factor(
        env: Env,
        caller: Address,
        asset: Address,
        reserve_factor: u32,
    ) -> Result<(), KineticRouterError> {
        reserve::set_reserve_factor(&env, &caller, &asset, reserve_factor)
    }

    pub fn set_reserve_interest_rate(
        env: Env,
        caller: Address,
        asset: Address,
        rate_strategy: Address,
    ) -> Result<(), KineticRouterError> {
        reserve::set_reserve_interest_rate(&env, &caller, &asset, &rate_strategy)
    }

    pub fn set_supply_cap(
        env: Env,
        caller: Address,
        asset: Address,
        supply_cap: u128,
    ) -> Result<(), KineticRouterError> {
        reserve::set_supply_cap(&env, &caller, &asset, supply_cap)
    }

    pub fn set_borrow_cap(
        env: Env,
        caller: Address,
        asset: Address,
        borrow_cap: u128,
    ) -> Result<(), KineticRouterError> {
        reserve::set_borrow_cap(&env, &caller, &asset, borrow_cap)
    }

    pub fn set_debt_ceiling(
        env: Env,
        caller: Address,
        asset: Address,
        debt_ceiling: u128,
    ) -> Result<(), KineticRouterError> {
        reserve::set_debt_ceiling(&env, &caller, &asset, debt_ceiling)
    }

    pub fn set_reserve_flashloaning(
        env: Env,
        caller: Address,
        asset: Address,
        enabled: bool,
    ) -> Result<(), KineticRouterError> {
        reserve::set_reserve_flashloaning(&env, &caller, &asset, enabled)
    }

    pub fn update_atoken(
        env: Env,
        caller: Address,
        asset: Address,
        implementation: soroban_sdk::BytesN<32>,
    ) -> Result<(), KineticRouterError> {
        reserve::update_atoken(&env, &caller, &asset, &implementation)
    }

    pub fn update_variable_debt_token(
        env: Env,
        caller: Address,
        asset: Address,
        implementation: soroban_sdk::BytesN<32>,
    ) -> Result<(), KineticRouterError> {
        reserve::update_variable_debt_token(&env, &caller, &asset, &implementation)
    }

    pub fn drop_reserve(
        env: Env,
        caller: Address,
        asset: Address,
    ) -> Result<(), KineticRouterError> {
        reserve::drop_reserve(&env, &caller, &asset)
    }

    /// Pause reserve deployment (emergency admin only)
    ///
    /// # Arguments
    /// - `caller`: Emergency admin address (must be authorized)
    ///
    /// # Returns
    /// - `Ok(())`: Reserve deployment paused successfully
    /// - `Err(KineticRouterError::Unauthorized)`: Caller is not emergency admin
    pub fn pause_reserve_deployment(env: Env, caller: Address) -> Result<(), KineticRouterError> {
        caller.require_auth();
        storage::validate_emergency_admin(&env, &caller)?;

        storage::set_reserve_deployment_paused(&env, true);

        // Emit event to alert monitoring systems of emergency pause activation
        env.events().publish(
            (
                symbol_short!("reserve"),
                symbol_short!("deploy"),
                symbol_short!("paused"),
            ),
            true,
        );

        Ok(())
    }

    /// Unpause reserve deployment (emergency admin only)
    ///
    /// # Arguments
    /// - `caller`: Emergency admin address (must be authorized)
    ///
    /// # Returns
    /// - `Ok(())`: Reserve deployment unpaused successfully
    /// - `Err(KineticRouterError::Unauthorized)`: Caller is not emergency admin
    pub fn unpause_reserve_deployment(env: Env, caller: Address) -> Result<(), KineticRouterError> {
        caller.require_auth();
        storage::validate_emergency_admin(&env, &caller)?;

        storage::set_reserve_deployment_paused(&env, false);

        // Emit event to alert monitoring systems that normal operations have resumed
        env.events().publish(
            (
                symbol_short!("reserve"),
                symbol_short!("deploy"),
                symbol_short!("unpaused"),
            ),
            false,
        );

        Ok(())
    }

    /// Check if reserve deployment is paused
    ///
    /// # Returns
    /// - `bool`: True if reserve deployment is paused, false otherwise
    pub fn is_reserve_deployment_paused(env: Env) -> bool {
        storage::is_reserve_deployment_paused(&env)
    }

    pub fn get_pool_admin(env: Env) -> Address {
        storage::get_pool_admin(&env).unwrap_or_else(|e| panic_with_error!(&env, e))
    }

    pub fn get_kinetic_router(env: Env) -> Address {
        storage::get_kinetic_router(&env).unwrap_or_else(|e| panic_with_error!(&env, e))
    }

    pub fn get_price_oracle(env: Env) -> Address {
        storage::get_price_oracle(&env).unwrap_or_else(|e| panic_with_error!(&env, e))
    }

    pub fn add_oracle_asset(
        env: Env,
        caller: Address,
        asset: Asset,
    ) -> Result<(), KineticRouterError> {
        oracle::add_oracle_asset(&env, &caller, &asset)
    }

    pub fn remove_oracle_asset(
        env: Env,
        caller: Address,
        asset: Asset,
    ) -> Result<(), KineticRouterError> {
        oracle::remove_oracle_asset(&env, &caller, &asset)
    }

    pub fn set_oracle_asset_enabled(
        env: Env,
        caller: Address,
        asset: Asset,
        enabled: bool,
    ) -> Result<(), KineticRouterError> {
        oracle::set_oracle_asset_enabled(&env, &caller, &asset, enabled)
    }

    pub fn set_oracle_manual_override(
        env: Env,
        caller: Address,
        asset: Asset,
        price: Option<i128>,
        expiry_timestamp: Option<u64>,
    ) -> Result<(), KineticRouterError> {
        oracle::set_oracle_manual_override(&env, &caller, &asset, price, expiry_timestamp)
    }

    pub fn get_oracle_whitelisted_assets(env: Env) -> Result<Vec<Asset>, KineticRouterError> {
        let price_oracle_address = storage::get_price_oracle(&env)?;

        Ok(env.invoke_contract(
            &price_oracle_address,
            &soroban_sdk::Symbol::new(&env, "get_whitelisted_assets"),
            soroban_sdk::vec![&env],
        ))
    }

    pub fn get_oracle_asset_config(env: Env, asset: Asset) -> Result<Option<AssetConfig>, KineticRouterError> {
        let price_oracle_address = storage::get_price_oracle(&env)?;

        Ok(env.invoke_contract(
            &price_oracle_address,
            &soroban_sdk::Symbol::new(&env, "get_asset_config"),
            soroban_sdk::vec![&env, asset.into_val(&env)],
        ))
    }

    pub fn get_oracle_asset_price(env: Env, asset: Asset) -> Result<u128, KineticRouterError> {
        let price_oracle_address = storage::get_price_oracle(&env)?;

        Ok(env.invoke_contract(
            &price_oracle_address,
            &soroban_sdk::Symbol::new(&env, "get_asset_price"),
            soroban_sdk::vec![&env, asset.into_val(&env)],
        ))
    }

    pub fn get_oracle_asset_price_data(env: Env, asset: Asset) -> Result<PriceData, KineticRouterError> {
        let price_oracle_address = storage::get_price_oracle(&env)?;

        Ok(env.invoke_contract(
            &price_oracle_address,
            &soroban_sdk::Symbol::new(&env, "get_asset_price_data"),
            soroban_sdk::vec![&env, asset.into_val(&env)],
        ))
    }

    /// Set incentives contract on pool and update all existing tokens
    pub fn set_incentives_contract(
        env: Env,
        caller: Address,
        incentives: Address,
    ) -> Result<u32, KineticRouterError> {
        caller.require_auth();
        storage::validate_admin(&env, &caller)?;

        let kinetic_router = storage::get_kinetic_router(&env)?;
        let updated_count: u32 = env.invoke_contract(
            &kinetic_router,
            &soroban_sdk::Symbol::new(&env, "set_incentives_contract"),
            soroban_sdk::vec![&env, caller.into_val(&env), incentives.into_val(&env)],
        );

        Ok(updated_count)
    }

    pub fn upgrade(env: Env, new_wasm_hash: BytesN<32>) -> Result<(), KineticRouterError> {
        let admin = storage::get_pool_admin(&env)?;
        admin.require_auth();
        crate::upgrade::upgrade(env, new_wasm_hash).map_err(|_| KineticRouterError::Unauthorized)
    }

    pub fn version(_env: Env) -> u32 {
        crate::upgrade::version()
    }

    /// Get current admin address
    pub fn get_admin(env: Env) -> Result<Address, KineticRouterError> {
        storage::get_pool_admin(&env)
    }

    /// Propose a new admin address (two-step transfer, step 1).
    /// Only the current admin can propose a new admin.
    /// The proposed admin must call `accept_admin` to complete the transfer.
    ///
    /// # Arguments
    /// * `caller` - Current admin address (must be authorized)
    /// * `pending_admin` - Proposed new admin address
    ///
    /// # Errors
    /// * `Unauthorized` - Caller is not current admin
    pub fn propose_admin(
        env: Env,
        caller: Address,
        pending_admin: Address,
    ) -> Result<(), KineticRouterError> {
        storage::validate_admin(&env, &caller)?;
        caller.require_auth();
        
        // Check if there's an existing pending admin and emit cancellation event if so
        if let Ok(existing_pending) = storage::get_pending_pool_admin(&env) {
            use k2_shared::events::AdminProposalCancelledEvent;
            env.events().publish(
                (soroban_sdk::symbol_short!("adm_canc"),),
                AdminProposalCancelledEvent {
                    admin: caller.clone(),
                    cancelled_pending_admin: existing_pending,
                },
            );
        }
        
        storage::set_pending_pool_admin(&env, &pending_admin);
        
        // Emit event
        use k2_shared::events::AdminProposedEvent;
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
    ///
    /// # Arguments
    /// * `caller` - Pending admin address (must be authorized)
    ///
    /// # Errors
    /// * `NoPendingAdmin` - No pending admin proposal exists
    /// * `InvalidPendingAdmin` - Caller is not the pending admin
    pub fn accept_admin(env: Env, caller: Address) -> Result<(), KineticRouterError> {
        let pending_admin = storage::get_pending_pool_admin(&env)?;
        if caller != pending_admin {
            return Err(KineticRouterError::InvalidPendingAdmin);
        }
        caller.require_auth();
        
        let previous_admin = storage::get_pool_admin(&env)?;
        storage::set_pool_admin(&env, &caller);
        crate::upgrade::initialize_admin(&env, &caller);
        storage::clear_pending_pool_admin(&env);
        
        // Emit event
        use k2_shared::events::AdminAcceptedEvent;
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
    ///
    /// # Arguments
    /// * `caller` - Current admin address (must be authorized)
    ///
    /// # Errors
    /// * `Unauthorized` - Caller is not current admin
    /// * `NoPendingAdmin` - No pending admin proposal exists
    pub fn cancel_admin_proposal(env: Env, caller: Address) -> Result<(), KineticRouterError> {
        storage::validate_admin(&env, &caller)?;
        caller.require_auth();
        
        let cancelled_pending = storage::get_pending_pool_admin(&env)?;
        storage::clear_pending_pool_admin(&env);
        
        // Emit event
        use k2_shared::events::AdminProposalCancelledEvent;
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
    pub fn get_pending_admin(env: Env) -> Result<Address, KineticRouterError> {
        storage::get_pending_pool_admin(&env)
    }
}
