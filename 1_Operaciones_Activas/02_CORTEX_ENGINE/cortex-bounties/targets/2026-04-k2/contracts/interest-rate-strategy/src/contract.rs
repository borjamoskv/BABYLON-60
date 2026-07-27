use crate::storage;
use crate::storage::InterestRateParams;
use crate::validation::validate_interest_rate_params;
use k2_shared::*;
use soroban_sdk::{contract, contractimpl, panic_with_error, Address, BytesN, Env};

/// Interest rate strategy contract implementing variable rate calculation model
/// Supports linear, exponential, and custom interest rate curves for variable rates only
#[contract]
pub struct InterestRateStrategyContract;

#[contractimpl]
impl InterestRateStrategyContract {
    pub fn __constructor(
        env: Env,
        admin: Address,
        base_variable_borrow_rate: u128,
        variable_rate_slope1: u128,
        variable_rate_slope2: u128,
        optimal_utilization_rate: u128,
    ) {
        if storage::is_initialized(&env) {
            panic!("Already initialized");
        }

        // Validate parameters
        let params = InterestRateParams {
            base_variable_borrow_rate,
            variable_rate_slope1,
            variable_rate_slope2,
            optimal_utilization_rate,
        };
        validate_interest_rate_params(&params).unwrap();

        crate::upgrade::initialize_admin(&env, &admin);
        storage::set_interest_rate_params(&env, &params);
        storage::set_initialized(&env);
    }

    pub fn initialize(
        _env: Env,
        _admin: Address,
        _base_variable_borrow_rate: u128,
        _variable_rate_slope1: u128,
        _variable_rate_slope2: u128,
        _optimal_utilization_rate: u128,
    ) -> Result<(), KineticRouterError> {
        panic!("Initialization is atomic at deployment. Use __constructor.");
    }

    /// Calculate interest rates based on supply and demand
    pub fn calculate_interest_rates(
        env: Env,
        asset: Address,
        available_liquidity: u128,
        total_variable_debt: u128,
        reserve_factor: u128,
    ) -> Result<CalculatedRates, KineticRouterError> {
        // Validate reserve_factor is in valid basis points range (0-10000)
        // Prevents underflow in RAY - reserve_factor_ray calculation
        if reserve_factor > BASIS_POINTS {
            return Err(KineticRouterError::InvalidAmount);
        }

        let params = storage::get_asset_interest_rate_params(&env, &asset)
            .unwrap_or_else(|| storage::get_interest_rate_params(&env));

        let total_liquidity = available_liquidity.checked_add(total_variable_debt)
            .ok_or(KineticRouterError::MathOverflow)?;
        let utilization_rate = if total_liquidity == 0 {
            0
        } else {
            ray_div(
                &env,
                total_variable_debt,
                total_liquidity,
            )?
        };

        let variable_borrow_rate = if utilization_rate > params.optimal_utilization_rate {
            let excess_utilization_rate = utilization_rate.checked_sub(params.optimal_utilization_rate)
                .ok_or(KineticRouterError::MathOverflow)?;
            let excess_utilization_rate_ratio = if RAY == params.optimal_utilization_rate {
                0
            } else {
                ray_div(
                    &env,
                    excess_utilization_rate,
                    RAY.checked_sub(params.optimal_utilization_rate)
                        .ok_or(KineticRouterError::MathOverflow)?,
                )?
            };

            let slope2_component = ray_mul(
                &env,
                params.variable_rate_slope2,
                excess_utilization_rate_ratio,
            )?;
            
            params.base_variable_borrow_rate
                .checked_add(params.variable_rate_slope1)
                .and_then(|v| v.checked_add(slope2_component))
                .ok_or(KineticRouterError::MathOverflow)?
        } else {
            let utilization_rate_ratio = if params.optimal_utilization_rate == 0 {
                0
            } else {
                ray_div(&env, utilization_rate, params.optimal_utilization_rate)?
            };

            let slope1_component = ray_mul(&env, params.variable_rate_slope1, utilization_rate_ratio)?;
            
            params.base_variable_borrow_rate
                .checked_add(slope1_component)
                .ok_or(KineticRouterError::MathOverflow)?
        };

        // Convert reserve_factor from basis points to RAY
        // Since we've validated reserve_factor <= BASIS_POINTS, overflow is impossible
        // (reserve_factor * RAY) / BASIS_POINTS <= (BASIS_POINTS * RAY) / BASIS_POINTS = RAY
        let reserve_factor_ray = reserve_factor
            .checked_mul(RAY)
            .and_then(|v| v.checked_div(BASIS_POINTS))
            .ok_or(KineticRouterError::MathOverflow)?;
        
        // Validate reserve_factor_ray <= RAY to prevent underflow
        // This should never happen given the validation above, but defensive check
        if reserve_factor_ray > RAY {
            return Err(KineticRouterError::InvalidAmount);
        }

        let borrow_rate_times_utilization = ray_mul(&env, variable_borrow_rate, utilization_rate)?;
        let liquidity_rate = ray_mul(
            &env,
            borrow_rate_times_utilization,
            RAY.checked_sub(reserve_factor_ray)
                .ok_or(KineticRouterError::MathOverflow)?,
        )?;

        Ok(CalculatedRates {
            liquidity_rate,
            variable_borrow_rate,
        })
    }

    pub fn get_base_variable_borrow_rate(env: Env) -> u128 {
        let params = storage::get_interest_rate_params(&env);
        params.base_variable_borrow_rate
    }

    pub fn get_variable_rate_slope1(env: Env) -> u128 {
        let params = storage::get_interest_rate_params(&env);
        params.variable_rate_slope1
    }

    pub fn get_variable_rate_slope2(env: Env) -> u128 {
        let params = storage::get_interest_rate_params(&env);
        params.variable_rate_slope2
    }

    pub fn get_optimal_utilization_rate(env: Env) -> u128 {
        let params = storage::get_interest_rate_params(&env);
        params.optimal_utilization_rate
    }

    /// Update interest rate parameters (admin only)
    pub fn update_interest_rate_params(
        env: Env,
        caller: Address,
        base_variable_borrow_rate: u128,
        variable_rate_slope1: u128,
        variable_rate_slope2: u128,
        optimal_utilization_rate: u128,
    ) -> Result<(), KineticRouterError> {
        storage::validate_admin(&env, &caller)?;
        caller.require_auth();

        // Validate parameters
        let new_params = InterestRateParams {
            base_variable_borrow_rate,
            variable_rate_slope1,
            variable_rate_slope2,
            optimal_utilization_rate,
        };
        validate_interest_rate_params(&new_params)?;

        storage::set_interest_rate_params(&env, &new_params);
        
        env.events().publish(
            (soroban_sdk::symbol_short!("rate"), soroban_sdk::symbol_short!("params"), soroban_sdk::symbol_short!("updated")),
            new_params,
        );
        
        Ok(())
    }

    pub fn admin(env: Env) -> Address {
        storage::get_admin(&env).unwrap_or_else(|e| panic_with_error!(&env, e))
    }

    /// Propose a new admin address (two-step transfer, step 1).
    /// Only the current admin can propose a new admin.
    /// The proposed admin must call `accept_admin` to complete the transfer.
    pub fn propose_admin(
        env: Env,
        caller: Address,
        pending_admin: Address,
    ) -> Result<(), KineticRouterError> {
        storage::validate_admin(&env, &caller)?;
        caller.require_auth();
        
        // Check if there's an existing pending admin and emit cancellation event if so
        if let Ok(existing_pending) = storage::get_pending_admin(&env) {
            use k2_shared::events::AdminProposalCancelledEvent;
            env.events().publish(
                (soroban_sdk::symbol_short!("adm_canc"),),
                AdminProposalCancelledEvent {
                    admin: caller.clone(),
                    cancelled_pending_admin: existing_pending,
                },
            );
        }
        
        storage::set_pending_admin(&env, &pending_admin);
        
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
    pub fn accept_admin(env: Env, caller: Address) -> Result<(), KineticRouterError> {
        let pending_admin = storage::get_pending_admin(&env)?;
        if caller != pending_admin {
            return Err(KineticRouterError::InvalidPendingAdmin);
        }
        caller.require_auth();
        
        let previous_admin = storage::get_admin(&env)?;
        storage::set_admin(&env, &caller);
        storage::clear_pending_admin(&env);
        
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
    pub fn cancel_admin_proposal(env: Env, caller: Address) -> Result<(), KineticRouterError> {
        storage::validate_admin(&env, &caller)?;
        caller.require_auth();
        
        let cancelled_pending = storage::get_pending_admin(&env)?;
        storage::clear_pending_admin(&env);
        
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
        storage::get_pending_admin(&env)
    }

    /// Set interest rate parameters for a specific asset
    pub fn set_asset_interest_rate_params(
        env: Env,
        caller: Address,
        asset: Address,
        base_variable_borrow_rate: u128,
        variable_rate_slope1: u128,
        variable_rate_slope2: u128,
        optimal_utilization_rate: u128,
    ) -> Result<(), KineticRouterError> {
        storage::validate_admin(&env, &caller)?;
        caller.require_auth();

        // Validate parameters
        let params = InterestRateParams {
            base_variable_borrow_rate,
            variable_rate_slope1,
            variable_rate_slope2,
            optimal_utilization_rate,
        };
        validate_interest_rate_params(&params)?;

        storage::set_asset_interest_rate_params(&env, &asset, &params);
        
        env.events().publish(
            (soroban_sdk::symbol_short!("asset"), soroban_sdk::symbol_short!("rate"), soroban_sdk::symbol_short!("params"), soroban_sdk::symbol_short!("updated")),
            (asset.clone(), params),
        );
        
        Ok(())
    }

    pub fn get_asset_interest_rate_params(env: Env, asset: Address) -> Option<InterestRateParams> {
        storage::get_asset_interest_rate_params(&env, &asset)
    }

    /// Upgrade contract WASM (admin only)
    pub fn upgrade(env: Env, new_wasm_hash: BytesN<32>) -> Result<(), KineticRouterError> {
        crate::upgrade::upgrade(env, new_wasm_hash).map_err(|_| KineticRouterError::Unauthorized)
    }

    pub fn version(_env: Env) -> u32 {
        crate::upgrade::version()
    }
}
