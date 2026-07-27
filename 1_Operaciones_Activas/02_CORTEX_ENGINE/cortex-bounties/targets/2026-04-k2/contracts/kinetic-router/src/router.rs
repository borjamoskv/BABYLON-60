use crate::{storage, validation};
use k2_shared::*;
use soroban_sdk::{contract, contractimpl, panic_with_error, symbol_short, Address, BytesN, Env, IntoVal, Symbol, U256, Vec};

#[contract]
pub struct KineticRouterContract;

/// RAII reentrancy guard — automatically unlocks on drop (any return path).
/// Fixes lock-leak bugs where early `return Err` paths skipped unlock.
struct ReentrancyGuard<'a> {
    env: &'a Env,
}

impl<'a> Drop for ReentrancyGuard<'a> {
    fn drop(&mut self) {
        storage::set_protocol_locked(self.env, false);
    }
}

/// Acquire reentrancy guard: extends TTL, checks/sets lock, returns RAII guard.
#[inline(never)]
fn acquire_reentrancy_guard(env: &Env) -> ReentrancyGuard {
    storage::extend_instance_ttl(env);
    if storage::is_protocol_locked(env) {
        panic_with_error!(env, SecurityError::ReentrancyDetected);
    }
    storage::set_protocol_locked(env, true);
    ReentrancyGuard { env }
}

/// Generic two-step admin propose helper.
fn propose_role_admin(
    env: &Env,
    caller: &Address,
    pending_admin: &Address,
    get_pending: fn(&Env) -> Result<Address, KineticRouterError>,
    set_pending: fn(&Env, &Address),
    cancel_topic: Symbol,
    propose_topic: Symbol,
) -> Result<(), KineticRouterError> {
    storage::validate_admin(env, caller)?;
    caller.require_auth();

    if let Ok(existing_pending) = get_pending(env) {
        use k2_shared::events::AdminProposalCancelledEvent;
        env.events().publish(
            (cancel_topic,),
            AdminProposalCancelledEvent {
                admin: caller.clone(),
                cancelled_pending_admin: existing_pending,
            },
        );
    }

    set_pending(env, pending_admin);

    use k2_shared::events::AdminProposedEvent;
    env.events().publish(
        (propose_topic,),
        AdminProposedEvent {
            current_admin: caller.clone(),
            pending_admin: pending_admin.clone(),
        },
    );

    Ok(())
}

/// Generic two-step admin accept helper.
fn accept_role_admin(
    env: &Env,
    caller: &Address,
    pending: &Address,
    previous: &Address,
    set_admin: fn(&Env, &Address),
    clear_pending: fn(&Env),
    accept_topic: Symbol,
) -> Result<(), KineticRouterError> {
    if caller != pending {
        return Err(KineticRouterError::InvalidPendingAdmin);
    }
    caller.require_auth();

    set_admin(env, caller);
    clear_pending(env);

    use k2_shared::events::AdminAcceptedEvent;
    env.events().publish(
        (accept_topic,),
        AdminAcceptedEvent {
            previous_admin: previous.clone(),
            new_admin: caller.clone(),
        },
    );

    Ok(())
}

/// Generic two-step admin cancel helper.
fn cancel_role_admin(
    env: &Env,
    caller: &Address,
    get_pending: fn(&Env) -> Result<Address, KineticRouterError>,
    clear_pending: fn(&Env),
    cancel_topic: Symbol,
) -> Result<(), KineticRouterError> {
    storage::validate_admin(env, caller)?;
    caller.require_auth();

    let cancelled_pending = get_pending(env)?;
    clear_pending(env);

    use k2_shared::events::AdminProposalCancelledEvent;
    env.events().publish(
        (cancel_topic,),
        AdminProposalCancelledEvent {
            admin: caller.clone(),
            cancelled_pending_admin: cancelled_pending,
        },
    );

    Ok(())
}

#[contractimpl]
impl KineticRouterContract {

    /// Initialize the lending pool contract
    ///
    /// # Arguments
    /// * `env` - The Soroban environment
    /// * `pool_admin` - Address with pool admin privileges
    /// * `emergency_admin` - Address with emergency admin privileges
    /// * `price_oracle` - Address of the price oracle contract
    /// * `treasury` - Address of the treasury (receives protocol fees)
    /// * `dex_router` - Address of DEX router (Soroswap router)
    pub fn initialize(
        env: Env,
        pool_admin: Address,
        emergency_admin: Address,
        price_oracle: Address,
        treasury: Address,
        dex_router: Address,
        incentives_contract: Option<Address>,
    ) -> Result<(), KineticRouterError> {
        if storage::is_initialized(&env) {
            return Err(KineticRouterError::AlreadyInitialized);
        }

        crate::upgrade::initialize_admin(&env, &pool_admin);

        storage::set_pool_admin(&env, &pool_admin);
        storage::set_emergency_admin(&env, &emergency_admin);
        storage::set_price_oracle(&env, &price_oracle);
        storage::set_treasury(&env, &treasury);

        // Initialize protocol parameters with safe defaults.
        storage::set_flash_loan_premium_max(&env, 100);
        storage::set_health_factor_liquidation_threshold(&env, 1_000_000_000_000_000_000);
        storage::set_min_swap_output_bps(&env, 9800);
        storage::set_partial_liquidation_hf_threshold(&env, 500_000_000_000_000_000);
        storage::set_dex_router(&env, &dex_router);
        if let Some(incentives) = incentives_contract {
            storage::set_incentives_contract(&env, &incentives);
        }
        storage::set_initialized(&env);

        Ok(())
    }

    /// Supply assets to the protocol
    ///
    /// # Arguments
    /// * `env` - The Soroban environment
    /// * `caller` - The address calling this function
    /// * `asset` - The address of the underlying asset to supply
    /// * `amount` - The amount to be supplied
    /// * `on_behalf_of` - The address that will receive the aTokens
    /// * `_referral_code` - Code used to register the integrator (unused for now)
    ///
    /// # Returns
    /// * `Ok(())` - Supply successful
    /// * `Err(KineticRouterError)` - Supply failed due to validation or cap limits
    ///
    /// # Cap Enforcement
    /// This function enforces supply caps if configured. Caps are stored as whole tokens
    /// and converted to smallest units during enforcement to maximize the effective range.
    pub fn supply(
        env: Env,
        caller: Address,
        asset: Address,
        amount: u128,
        on_behalf_of: Address,
        _referral_code: u32,
    ) -> Result<(), KineticRouterError> {
        let _guard = acquire_reentrancy_guard(&env);
        crate::operations::supply(env.clone(), caller, asset, amount, on_behalf_of, _referral_code)
    }

    pub fn withdraw(
        env: Env,
        caller: Address,
        asset: Address,
        amount: u128,
        to: Address,
    ) -> Result<u128, KineticRouterError> {
        let _guard = acquire_reentrancy_guard(&env);
        crate::operations::withdraw(env.clone(), caller, asset, amount, to)
    }

    pub fn swap_collateral(
        env: Env,
        caller: Address,
        from_asset: Address,
        to_asset: Address,
        amount: u128,
        min_amount_out: u128,
        swap_handler: Option<Address>,
    ) -> Result<u128, KineticRouterError> {
        let _guard = acquire_reentrancy_guard(&env);
        crate::swap::swap_collateral(env.clone(), caller, from_asset, to_asset, amount, min_amount_out, swap_handler)
    }

    /// Set DEX router address (admin only)
    pub fn set_dex_router(env: Env, router: Address) -> Result<(), KineticRouterError> {
        let admin = storage::get_pool_admin(&env)?;
        admin.require_auth();
        storage::set_dex_router(&env, &router);
        // M-06
        env.events().publish(
            (symbol_short!("dex"), symbol_short!("router")),
            router,
        );
        Ok(())
    }

    /// Get DEX router address
    pub fn get_dex_router(env: Env) -> Option<Address> {
        storage::get_dex_router(&env)
    }

    /// Set DEX factory address (admin only)
    pub fn set_dex_factory(env: Env, factory: Address) -> Result<(), KineticRouterError> {
        let admin = storage::get_pool_admin(&env)?;
        admin.require_auth();
        storage::set_dex_factory(&env, &factory);
        // M-06: Emit event for off-chain indexers
        env.events().publish(
            (symbol_short!("dex"), symbol_short!("factory")),
            factory,
        );
        Ok(())
    }

    /// Get DEX factory address
    pub fn get_dex_factory(env: Env) -> Option<Address> {
        storage::get_dex_factory(&env)
    }

    pub fn borrow(
        env: Env,
        caller: Address,
        asset: Address,
        amount: u128,
        interest_rate_mode: u32,
        _referral_code: u32,
        on_behalf_of: Address,
    ) -> Result<(), KineticRouterError> {
        let _guard = acquire_reentrancy_guard(&env);
        crate::operations::borrow(env.clone(), caller, asset, amount, interest_rate_mode, _referral_code, on_behalf_of)
    }

    pub fn repay(
        env: Env,
        caller: Address,
        asset: Address,
        amount: u128,
        rate_mode: u32,
        on_behalf_of: Address,
    ) -> Result<u128, KineticRouterError> {
        let _guard = acquire_reentrancy_guard(&env);
        crate::operations::repay(env.clone(), caller, asset, amount, rate_mode, on_behalf_of)
    }

    /// Liquidate a position
    ///
    /// # Arguments
    /// * `collateral_asset` - The address of the underlying asset used as collateral
    /// * `debt_asset` - The address of the underlying borrowed asset to be repaid
    /// * `user` - The address of the borrower getting liquidated
    /// * `debt_to_cover` - The debt amount of borrowed asset to liquidate
    /// * `receive_a_token` - True if liquidator receives aTokens, false for underlying asset
    pub fn liquidation_call(
        env: Env,
        liquidator: Address,
        collateral_asset: Address,
        debt_asset: Address,
        user: Address,
        debt_to_cover: u128,
        _receive_a_token: bool,
    ) -> Result<(), KineticRouterError> {
        let _guard = acquire_reentrancy_guard(&env);
        crate::liquidation::liquidation_call(
            env.clone(),
            liquidator,
            collateral_asset,
            debt_asset,
            user,
            debt_to_cover,
            _receive_a_token,
        )
    }

    pub fn set_flash_loan_premium(env: Env, premium_bps: u128) -> Result<(), KineticRouterError> {
        crate::params::set_flash_loan_premium(env, premium_bps)
    }

    /// Set maximum flash loan premium allowed (admin only)
    ///
    /// # Arguments
    /// * `max_premium_bps` - Maximum premium in basis points (e.g., 100 = 1%)
    ///
    /// # Returns
    /// * `Ok(())` if max premium updated successfully
    /// * `Err(Unauthorized)` if caller is not admin
    pub fn set_flash_loan_premium_max(env: Env, max_premium_bps: u128) -> Result<(), KineticRouterError> {
        crate::params::set_flash_loan_premium_max(env, max_premium_bps)
    }

    pub fn get_flash_loan_premium_max(env: Env) -> u128 {
        crate::params::get_flash_loan_premium_max(env)
    }

    pub fn set_hf_liquidation_threshold(env: Env, threshold: u128) -> Result<(), KineticRouterError> {
        crate::params::set_hf_liquidation_threshold(env, threshold)
    }

    pub fn get_hf_liquidation_threshold(env: Env) -> u128 {
        crate::params::get_hf_liquidation_threshold(env)
    }

    pub fn set_min_swap_output_bps(env: Env, min_output_bps: u128) -> Result<(), KineticRouterError> {
        crate::params::set_min_swap_output_bps(env, min_output_bps)
    }

    pub fn get_min_swap_output_bps(env: Env) -> u128 {
        crate::params::get_min_swap_output_bps(env)
    }

    pub fn set_partial_liq_hf_threshold(env: Env, threshold: u128) -> Result<(), KineticRouterError> {
        crate::params::set_partial_liq_hf_threshold(env, threshold)
    }

    pub fn get_partial_liq_hf_threshold(env: Env) -> u128 {
        crate::params::get_partial_liq_hf_threshold(env)
    }

    pub fn set_liquidation_tracker_expiry(env: Env, expiry_ledgers: u32) -> Result<(), KineticRouterError> {
        crate::admin::set_liquidation_tracker_expiry(env, expiry_ledgers)
    }

    pub fn get_liquidation_tracker_expiry(env: Env) -> u32 {
        crate::admin::get_liquidation_tracker_expiry(env)
    }

    pub fn get_flash_loan_premium(env: Env) -> u128 {
        crate::params::get_flash_loan_premium(env)
    }

    /// Set extra premium charged for flash liquidations (admin only).
    /// This is on top of the regular protocol fee collected during liquidation.
    /// Set to 0 to disable the extra fee (default).
    pub fn set_flash_liquidation_premium(env: Env, premium_bps: u128) -> Result<(), KineticRouterError> {
        crate::params::set_flash_liquidation_premium(env, premium_bps)
    }

    pub fn get_flash_liquidation_premium(env: Env) -> u128 {
        crate::params::get_flash_liquidation_premium(env)
    }

    /// Sets the price tolerance for two-step liquidation execution (in basis points).
    /// Default is 300 (3%). Admin has full flexibility to set any value.
    pub fn set_liquidation_price_tolerance(env: Env, tolerance_bps: u128) -> Result<(), KineticRouterError> {
        crate::params::set_liquidation_price_tolerance(env, tolerance_bps)
    }

    /// M-07
    pub fn set_asset_staleness_threshold(env: Env, asset: Address, threshold_seconds: u64) -> Result<(), KineticRouterError> {
        crate::params::set_asset_staleness_threshold(env, asset, threshold_seconds)
    }

    /// M-07
    pub fn get_asset_staleness_threshold(env: Env, asset: Address) -> Option<u64> {
        crate::params::get_asset_staleness_threshold(env, asset)
    }

    pub fn get_user_liquidation_amount(env: Env, user: Address) -> u128 {
        storage::get_user_liquidation_amount(&env, &user)
    }

    /// Execute a flash loan
    ///
    /// Flash loans are permissionless - anyone can initiate them.
    /// The receiver contract must implement `execute_operation` callback.
    ///
    /// # Parameters
    /// - `initiator`: Address initiating the flash loan (must authorize)
    /// - `receiver`: Contract that will receive the loan and execute callback
    /// - `assets`: Assets to borrow
    /// - `amounts`: Amounts to borrow for each asset
    /// - `params`: Arbitrary data passed to receiver
    ///
    /// # Receiver Callback
    /// The receiver must implement `execute_operation` with the standard flash loan interface.
    ///
    /// # Authorization
    /// Initiator must authorize the call, but anyone can be an initiator.
    /// The receiver handles its own authorization logic.
    ///
    /// # Errors
    /// - `InvalidFlashLoanParams`: Invalid parameters
    /// - `InsufficientFlashLoanLiquidity`: Not enough liquidity
    /// - `FlashLoanExecutionFailed`: Receiver callback failed
    /// - `FlashLoanNotRepaid`: Loan not fully repaid
    pub fn flash_loan(
        env: Env,
        initiator: Address,
        receiver: Address,
        assets: Vec<Address>,
        amounts: Vec<u128>,
        params: soroban_sdk::Bytes,
    ) -> Result<(), KineticRouterError> {
        let _guard = acquire_reentrancy_guard(&env);
        initiator.require_auth();

        // Validate input vector lengths
        if assets.len() > MAX_RESERVES || amounts.len() > MAX_RESERVES {
            panic_with_error!(&env, KineticRouterError::InvalidFlashLoanParams);
        }
        if assets.len() != amounts.len() {
            panic_with_error!(&env, KineticRouterError::InvalidFlashLoanParams);
        }

        for i in 0..assets.len() {
            if let Some(asset) = assets.get(i) {
                validation::validate_reserve_whitelist_access(&env, &asset, &initiator)?;
                // N-13
                validation::validate_reserve_whitelist_access(&env, &asset, &receiver)?;
                // AC-03
                validation::validate_reserve_blacklist_access(&env, &asset, &initiator)?;
                validation::validate_reserve_blacklist_access(&env, &asset, &receiver)?;
            }
        }
        crate::flash_loan::internal_flash_loan(
            &env, initiator, receiver, assets, amounts, params, true, // charge premium
        )
    }

    /// Prepare a liquidation - validates and stores authorization (TX1 of 2-step liquidation)
    /// This is the expensive validation step (~40M CPU) but can fail/retry safely.
    ///
    /// # Arguments
    /// * `liquidator` - Address executing the liquidation
    /// * `user` - Address being liquidated
    /// * `debt_asset` - Asset to repay
    /// * `collateral_asset` - Asset to seize
    /// * `debt_to_cover` - Amount of debt to repay
    /// * `min_swap_out` - Minimum acceptable swap output (slippage protection)
    /// * `swap_handler` - Optional custom swap handler address
    ///
    /// # Returns
    /// * `LiquidationAuthorization` - Authorization token for execute_liquidation
    pub fn prepare_liquidation(
        env: Env,
        liquidator: Address,
        user: Address,
        debt_asset: Address,
        collateral_asset: Address,
        debt_to_cover: u128,
        min_swap_out: u128,
        swap_handler: Option<Address>,
    ) -> Result<storage::LiquidationAuthorization, KineticRouterError> {
        let _guard = acquire_reentrancy_guard(&env);
        liquidator.require_auth();

        if storage::is_paused(&env) {
            return Err(KineticRouterError::AssetPaused);
        }

        // Step 1: Validate liquidator whitelist/blacklist (~1M CPU)
        validation::validate_liquidation_whitelist_access(&env, &liquidator)?;
        validation::validate_liquidation_blacklist_access(&env, &liquidator)?;

        // Step 2: Get asset prices from oracle (~10M CPU)
        let (debt_price_data, collateral_price_data) =
            crate::liquidation::get_asset_prices_batch(&env, &debt_asset, &collateral_asset)?;

        // Step 3: Calculate health factor (expensive - loops all reserves, ~25M CPU)
        // CRIT-02: Pass known prices from step 2 to avoid redundant oracle calls
        let mut known_prices = soroban_sdk::Map::new(&env);
        known_prices.set(debt_asset.clone(), debt_price_data.price);
        known_prices.set(collateral_asset.clone(), collateral_price_data.price);

        let user_config = storage::get_user_configuration(&env, &user);
        let params = crate::calculation::AccountDataParams {
            known_prices: Some(&known_prices),
            known_reserves: None,
            user_config: Some(&user_config),
            extra_assets: None,
            return_prices: false,
            known_balances: None,
        };
        let result = crate::calculation::calculate_user_account_data_unified(
            &env,
            &user,
            params,
        )?;
        let user_account_data = result.account_data;

        // Step 4: Verify position is liquidatable (HF < 1.0)
        if user_account_data.total_debt_base == 0 {
            return Err(KineticRouterError::NoDebtOfRequestedType);
        }

        if user_account_data.health_factor >= WAD {
            return Err(KineticRouterError::InvalidLiquidation);
        }

        // Step 5: Fetch and validate reserve data (~2M CPU)
        let raw_collateral_reserve = storage::get_reserve_data(&env, &collateral_asset)?;
        let raw_debt_reserve = storage::get_reserve_data(&env, &debt_asset)?;

        let collateral_reserve_data = crate::calculation::update_state(&env, &collateral_asset, &raw_collateral_reserve)?;
        let debt_reserve_data = crate::calculation::update_state(&env, &debt_asset, &raw_debt_reserve)?;

        if !collateral_reserve_data.configuration.is_active() {
            return Err(KineticRouterError::AssetNotActive);
        }
        if !debt_reserve_data.configuration.is_active() {
            return Err(KineticRouterError::AssetNotActive);
        }
        if collateral_reserve_data.configuration.is_paused() {
            return Err(KineticRouterError::AssetPaused);
        }
        if debt_reserve_data.configuration.is_paused() {
            return Err(KineticRouterError::AssetPaused);
        }

        if collateral_price_data.price == 0 || debt_price_data.price == 0 {
            return Err(KineticRouterError::PriceOracleNotFound);
        }

        // Get oracle config for dynamic price precision conversion
        let oracle_to_wad = crate::calculation::get_oracle_precision_factor(&env)?;

        // Step 5b: Enforce close factor — prevent liquidating more than allowed share of debt.
        let effective_debt_to_cover;
        {
            // N-01
            let mut debt_balance_args = Vec::new(&env);
            debt_balance_args.push_back(user.to_val());
            debt_balance_args.push_back(IntoVal::into_val(
                &debt_reserve_data.variable_borrow_index,
                &env,
            ));

            let debt_balance_result = env.try_invoke_contract::<i128, KineticRouterError>(
                &debt_reserve_data.debt_token_address,
                &Symbol::new(&env, "balance_of_with_index"),
                debt_balance_args,
            );

            let debt_balance = match debt_balance_result {
                Ok(Ok(bal)) => bal,
                Ok(Err(_)) | Err(_) => return Err(KineticRouterError::NoDebtOfRequestedType),
            };

            let debt_decimals = debt_reserve_data.configuration.get_decimals() as u32;
            let debt_decimals_pow = 10_u128
                .checked_pow(debt_decimals)
                .ok_or(KineticRouterError::MathOverflow)?;

            // N-01 / WP-M2: Close factor validation
            let individual_debt_base = crate::calculation::value_in_base(
                &env, k2_shared::safe_i128_to_u128(&env, debt_balance),
                debt_price_data.price, oracle_to_wad, debt_decimals_pow,
            )?;

            // Fetch collateral balance for small position check
            let collateral_decimals = collateral_reserve_data.configuration.get_decimals() as u32;
            let collateral_decimals_pow = 10_u128
                .checked_pow(collateral_decimals)
                .ok_or(KineticRouterError::MathOverflow)?;

            let mut coll_bal_args = Vec::new(&env);
            coll_bal_args.push_back(user.to_val());
            coll_bal_args.push_back(IntoVal::into_val(
                &collateral_reserve_data.liquidity_index, &env,
            ));
            let user_collateral_balance = match env.try_invoke_contract::<i128, KineticRouterError>(
                &collateral_reserve_data.a_token_address,
                &Symbol::new(&env, "balance_of_with_index"),
                coll_bal_args,
            ) {
                Ok(Ok(bal)) => k2_shared::safe_i128_to_u128(&env, bal),
                Ok(Err(_)) | Err(_) => 0u128,
            };

            let individual_collateral_base = crate::calculation::value_in_base(
                &env, user_collateral_balance,
                collateral_price_data.price, oracle_to_wad, collateral_decimals_pow,
            )?;
            let debt_to_cover_base = crate::calculation::value_in_base(
                &env, debt_to_cover,
                debt_price_data.price, oracle_to_wad, debt_decimals_pow,
            )?;
            crate::liquidation::validate_close_factor(
                &env, &user, user_account_data.health_factor,
                individual_debt_base, individual_collateral_base, debt_to_cover_base,
            )?;

            // H-08: Check min_remaining_debt early in prepare_liquidation
            // Clamp debt_to_cover to actual debt balance when it would leave dust
            // below min_remaining_debt. This handles the race condition where interest
            // accrues between the caller's balance query and tx execution.
            let debt_to_cover_i128 = k2_shared::safe_u128_to_i128(&env, debt_to_cover);
            let remaining_debt = debt_balance
                .checked_sub(debt_to_cover_i128)
                .ok_or(KineticRouterError::MathOverflow)?;
            effective_debt_to_cover = if remaining_debt > 0 {
                let remaining_debt_u128 = k2_shared::safe_i128_to_u128(&env, remaining_debt);
                let min_remaining_whole = debt_reserve_data.configuration.get_min_remaining_debt();
                if min_remaining_whole > 0 {
                    let min_remaining_debt = (min_remaining_whole as u128)
                        .checked_mul(debt_decimals_pow)
                        .ok_or(KineticRouterError::MathOverflow)?;
                    if remaining_debt_u128 < min_remaining_debt {
                        // Dust remainder: clamp to full debt for clean liquidation
                        k2_shared::safe_i128_to_u128(&env, debt_balance)
                    } else {
                        debt_to_cover
                    }
                } else {
                    debt_to_cover
                }
            } else {
                debt_to_cover
            };
        }

        // Step 6: Calculate liquidation amounts
        let (_collateral_amount, computed_collateral_to_seize) =
            crate::calculation::calculate_liquidation_amounts_with_reserves(
                &env,
                &collateral_reserve_data,
                &debt_reserve_data,
                effective_debt_to_cover,
                collateral_price_data.price,
                debt_price_data.price,
                oracle_to_wad,
            )?;

        if effective_debt_to_cover == 0 || computed_collateral_to_seize == 0 {
            return Err(KineticRouterError::InvalidAmount);
        }

        // Step 7: Store authorization with 5-minute expiry
        let nonce = storage::get_and_increment_liquidation_nonce(&env);
        // I-05, L-03: Increased from 300 to 600 ledgers (~10 min) for congestion tolerance
        let expires_at = env.ledger().timestamp()
            .checked_add(600)
            .ok_or(KineticRouterError::MathOverflow)?;

        let auth = storage::LiquidationAuthorization {
            liquidator: liquidator.clone(),
            user: user.clone(),
            debt_asset: debt_asset.clone(),
            collateral_asset: collateral_asset.clone(),
            debt_to_cover: effective_debt_to_cover,
            collateral_to_seize: computed_collateral_to_seize,
            min_swap_out,
            debt_price: debt_price_data.price,
            collateral_price: collateral_price_data.price,
            health_factor_at_prepare: user_account_data.health_factor,
            expires_at,
            nonce,
            swap_handler,
        };

        storage::set_liquidation_authorization(&env, &liquidator, &user, &auth);

        env.events().publish(
            (symbol_short!("prep_ok"),),
            (nonce, expires_at),
        );

        Ok(auth)
    }

    /// Execute a prepared liquidation - atomic swap + debt repayment (TX2 of 2-step liquidation)
    /// Uses pre-validated data from prepare_liquidation (~60M CPU).
    ///
    /// # Arguments
    /// * `liquidator` - Address executing the liquidation (must match authorization)
    /// * `user` - Address being liquidated (must match authorization)
    /// * `debt_asset` - Asset to repay (must match authorization)
    /// * `collateral_asset` - Asset to seize (must match authorization)
    /// * `deadline` - Transaction deadline timestamp
    pub fn execute_liquidation(
        env: Env,
        liquidator: Address,
        user: Address,
        debt_asset: Address,
        collateral_asset: Address,
        deadline: u64,
    ) -> Result<(), KineticRouterError> {
        let _guard = acquire_reentrancy_guard(&env);
        liquidator.require_auth();

        if storage::is_paused(&env) {
            return Err(KineticRouterError::AssetPaused);
        }

        validation::validate_liquidation_whitelist_access(&env, &liquidator)?;
        validation::validate_liquidation_blacklist_access(&env, &liquidator)?;

        // Step 1: Load and validate authorization
        let auth = storage::get_liquidation_authorization(&env, &liquidator, &user)?;

        // Verify not expired
        // WP-L5: Do not call remove_liquidation_authorization before return Err —
        // Soroban rolls back all state changes on error, making the removal ineffective.
        // The auth will expire naturally based on expires_at.
        if env.ledger().timestamp() > auth.expires_at {
            return Err(KineticRouterError::Expired);
        }

        // Verify deadline
        if env.ledger().timestamp() > deadline {
            return Err(KineticRouterError::Expired);
        }

        // Verify parameters match authorization
        if auth.debt_asset != debt_asset || auth.collateral_asset != collateral_asset {
            return Err(KineticRouterError::InvalidLiquidation);
        }

        // Step 2: Quick price sanity check (5% tolerance to detect manipulation)
        let (current_debt_price, current_collateral_price) =
            crate::liquidation::get_asset_prices_batch(&env, &debt_asset, &collateral_asset)?;

        // M-03
        let tolerance_bps = storage::get_liquidation_price_tolerance_bps(&env);
        let lower_factor = 10000u128.checked_sub(tolerance_bps).ok_or(KineticRouterError::MathOverflow)?;
        let upper_factor = 10000u128.checked_add(tolerance_bps).ok_or(KineticRouterError::MathOverflow)?;

        // Validate debt price within tolerance
        let debt_price_min = auth.debt_price.checked_mul(lower_factor).ok_or(KineticRouterError::MathOverflow)?.checked_div(10000).ok_or(KineticRouterError::MathOverflow)?;
        let debt_price_max = auth.debt_price.checked_mul(upper_factor).ok_or(KineticRouterError::MathOverflow)?.checked_div(10000).ok_or(KineticRouterError::MathOverflow)?;
        if current_debt_price.price < debt_price_min || current_debt_price.price > debt_price_max {
            return Err(KineticRouterError::InvalidLiquidation);
        }

        // Validate collateral price within tolerance
        let collateral_price_min = auth.collateral_price.checked_mul(lower_factor).ok_or(KineticRouterError::MathOverflow)?.checked_div(10000).ok_or(KineticRouterError::MathOverflow)?;
        let collateral_price_max = auth.collateral_price.checked_mul(upper_factor).ok_or(KineticRouterError::MathOverflow)?.checked_div(10000).ok_or(KineticRouterError::MathOverflow)?;
        if current_collateral_price.price < collateral_price_min || current_collateral_price.price > collateral_price_max {
            return Err(KineticRouterError::InvalidLiquidation);
        }

        // Step 3: Update state + HF calc + close-factor (shared queries)
        // update_state before HF calc enables known_reserves passthrough (saves 2 storage reads).
        // HF calc's balance_cache is reused in close-factor block (saves 2 cross-contract calls).
        let raw_debt_reserve = storage::get_reserve_data(&env, &debt_asset)?;
        let debt_reserve_data = crate::calculation::update_state(&env, &debt_asset, &raw_debt_reserve)?;

        let raw_collateral_reserve = storage::get_reserve_data(&env, &collateral_asset)?;
        let collateral_reserve_data = crate::calculation::update_state(&env, &collateral_asset, &raw_collateral_reserve)?;

        // F-07
        let oracle_to_wad = crate::calculation::get_oracle_precision_factor(&env)?;

        // CRIT-01: Pass known prices + reserves to HF calc
        let mut exec_known_prices = soroban_sdk::Map::new(&env);
        exec_known_prices.set(debt_asset.clone(), current_debt_price.price);
        exec_known_prices.set(collateral_asset.clone(), current_collateral_price.price);

        let mut known_reserves = soroban_sdk::Map::new(&env);
        known_reserves.set(debt_asset.clone(), debt_reserve_data.clone());
        known_reserves.set(collateral_asset.clone(), collateral_reserve_data.clone());

        let user_config = storage::get_user_configuration(&env, &user);
        let params = crate::calculation::AccountDataParams {
            known_prices: Some(&exec_known_prices),
            known_reserves: Some(&known_reserves),
            user_config: Some(&user_config),
            extra_assets: None,
            return_prices: false,
            known_balances: None,
        };
        let result = crate::calculation::calculate_user_account_data_unified(
            &env,
            &user,
            params,
        )?;
        let user_account_data = result.account_data;

        // Verify position is still liquidatable at execution time
        // WP-L5: No remove_liquidation_authorization here — rolled back on Err anyway
        if user_account_data.health_factor >= WAD {
            return Err(KineticRouterError::InvalidLiquidation);
        }

        // Reuse cached balances from HF calc (saves 2 cross-contract calls vs re-querying)
        let exec_user_collateral_balance = result.balance_cache
            .try_get(collateral_asset.clone())
            .ok()
            .flatten()
            .map(|(coll, _)| coll)
            .ok_or(KineticRouterError::InsufficientCollateral)?;

        let debt_balance = {
            let (_, debt_u128) = result.balance_cache
                .try_get(debt_asset.clone())
                .ok()
                .flatten()
                .ok_or(KineticRouterError::NoDebtOfRequestedType)?;
            k2_shared::safe_u128_to_i128(&env, debt_u128)
        };

        // N-07: Close-factor validation using cached balances
        let effective_debt_to_cover;
        {
            let debt_decimals = debt_reserve_data.configuration.get_decimals() as u32;
            let debt_decimals_pow = 10_u128
                .checked_pow(debt_decimals)
                .ok_or(KineticRouterError::MathOverflow)?;

            let individual_debt_base = crate::calculation::value_in_base(
                &env, k2_shared::safe_i128_to_u128(&env, debt_balance),
                current_debt_price.price, oracle_to_wad, debt_decimals_pow,
            )?;

            let collateral_decimals = collateral_reserve_data.configuration.get_decimals() as u32;
            let collateral_decimals_pow = 10_u128
                .checked_pow(collateral_decimals)
                .ok_or(KineticRouterError::MathOverflow)?;

            let individual_collateral_base = crate::calculation::value_in_base(
                &env, exec_user_collateral_balance,
                current_collateral_price.price, oracle_to_wad, collateral_decimals_pow,
            )?;
            let auth_debt_to_cover_base = crate::calculation::value_in_base(
                &env, auth.debt_to_cover,
                current_debt_price.price, oracle_to_wad, debt_decimals_pow,
            )?;
            // WP-L5: No remove_liquidation_authorization here — rolled back on Err anyway
            if let Err(_) = crate::liquidation::validate_close_factor(
                &env, &user, user_account_data.health_factor,
                individual_debt_base, individual_collateral_base, auth_debt_to_cover_base,
            ) {
                return Err(KineticRouterError::LiquidationAmountTooHigh);
            }

            // M-13: min_remaining_debt check — clamp to full debt if dust remainder
            let debt_to_cover_i128 = k2_shared::safe_u128_to_i128(&env, auth.debt_to_cover);
            let remaining_debt = debt_balance
                .checked_sub(debt_to_cover_i128)
                .ok_or(KineticRouterError::MathOverflow)?;

            effective_debt_to_cover = if remaining_debt > 0 {
                let remaining_debt_u128 = k2_shared::safe_i128_to_u128(&env, remaining_debt);
                let min_remaining_whole = debt_reserve_data.configuration.get_min_remaining_debt();
                if min_remaining_whole > 0 {
                    let min_remaining_debt = (min_remaining_whole as u128)
                        .checked_mul(debt_decimals_pow)
                        .ok_or(KineticRouterError::MathOverflow)?;
                    if remaining_debt_u128 < min_remaining_debt {
                        // Dust remainder: clamp to full debt for clean liquidation
                        k2_shared::safe_i128_to_u128(&env, debt_balance)
                    } else {
                        auth.debt_to_cover
                    }
                } else {
                    auth.debt_to_cover
                }
            } else {
                auth.debt_to_cover
            };
        }

        let pool_address = env.current_contract_address();

        // Step 4: Recompute collateral with current prices and enforce borrower-safe bound
        let (_collateral_amount, computed_collateral_to_seize) =
            crate::calculation::calculate_liquidation_amounts_with_reserves(
                &env,
                &collateral_reserve_data,
                &debt_reserve_data,
                effective_debt_to_cover,
                current_collateral_price.price,
                current_debt_price.price,
                oracle_to_wad,
            )?;

        // Use minimum to protect borrower from over-seizure
        let safe_collateral_to_seize = if computed_collateral_to_seize < auth.collateral_to_seize {
            env.events().publish(
                (symbol_short!("coll_adj"),),
                (auth.collateral_to_seize, computed_collateral_to_seize),
            );
            computed_collateral_to_seize
        } else {
            auth.collateral_to_seize
        };

        // M-16 — P2 optimization: reuse collateral balance from close-factor block.
        // Within the same transaction, the balance hasn't changed (no burns happened yet).
        let user_collateral_balance = exec_user_collateral_balance;

        let collateral_cap_triggered;
        let (actual_debt_to_cover, actual_collateral_to_seize) = if safe_collateral_to_seize > user_collateral_balance {
            collateral_cap_triggered = true;
            // Ceiling division: adjusted_debt = ceil(debt * user_balance / seizure)
            let adjusted_debt = {
                let dtc = U256::from_u128(&env, effective_debt_to_cover);
                let ucb = U256::from_u128(&env, user_collateral_balance);
                let cts = U256::from_u128(&env, safe_collateral_to_seize);
                let one = U256::from_u128(&env, 1u128);
                dtc.mul(&ucb).add(&cts).sub(&one).div(&cts)
                    .to_u128()
                    .ok_or(KineticRouterError::MathOverflow)?
            };
            env.events().publish(
                (symbol_short!("col_cap"),),
                (safe_collateral_to_seize, user_collateral_balance, effective_debt_to_cover, adjusted_debt),
            );
            (adjusted_debt, user_collateral_balance)
        } else {
            collateral_cap_triggered = false;
            (effective_debt_to_cover, safe_collateral_to_seize)
        };

        // Step 6: Set up callback params for flash loan
        // S-01: Scale min_swap_out proportionally when collateral cap reduces amounts
        let adjusted_min_swap_out = if collateral_cap_triggered {
            let mso = U256::from_u128(&env, auth.min_swap_out);
            let acs = U256::from_u128(&env, actual_collateral_to_seize);
            let scs = U256::from_u128(&env, safe_collateral_to_seize);
            mso.mul(&acs).div(&scs)
                .to_u128()
                .ok_or(KineticRouterError::MathOverflow)?
        } else {
            auth.min_swap_out
        };

        let callback_params = LiquidationCallbackParams {
            liquidator: liquidator.clone(),
            user: user.clone(),
            debt_asset: debt_asset.clone(),
            collateral_asset: collateral_asset.clone(),
            debt_to_cover: actual_debt_to_cover,
            collateral_to_seize: actual_collateral_to_seize,
            min_swap_out: adjusted_min_swap_out,
            deadline_ts: deadline,
            debt_price: current_debt_price.price,
            collateral_price: current_collateral_price.price,
            collateral_reserve_data: collateral_reserve_data.clone(),
            debt_reserve_data: debt_reserve_data.clone(),
            swap_handler: auth.swap_handler,
        };
        storage::set_liquidation_callback_params(&env, &callback_params);

        // Step 7: Execute flash loan (atomic swap + debt repayment)
        let mut assets = Vec::new(&env);
        assets.push_back(debt_asset.clone());
        let mut amounts = Vec::new(&env);
        amounts.push_back(actual_debt_to_cover);
        let params_bytes = soroban_sdk::Bytes::new(&env);

        crate::flash_loan::internal_flash_loan_with_reserve_data(
            &env,
            pool_address.clone(),
            pool_address.clone(),
            assets,
            amounts,
            params_bytes,
            false, // No premium for internal liquidation
            Some(&debt_reserve_data),
        )?;

        let fresh_debt_reserve_data = &debt_reserve_data;
        let fresh_collateral_reserve_data = &collateral_reserve_data;

        let (debt_total_scaled_cb, collateral_total_scaled_cb,
             user_remaining_coll_scaled, user_remaining_debt_scaled) =
            storage::get_liquidation_scaled_supplies(&env)
                .ok_or(KineticRouterError::InvalidLiquidation)?;
        storage::remove_liquidation_scaled_supplies(&env);

        // Track callback scaled totals for interest rate update (saves 2 scaled_total_supply calls)
        let mut final_debt_scaled_total: Option<u128> = Some(k2_shared::safe_i128_to_u128(&env, debt_total_scaled_cb));
        let final_collateral_scaled_total: Option<u128> = Some(k2_shared::safe_i128_to_u128(&env, collateral_total_scaled_cb));

        let mut remaining_debt = if user_remaining_debt_scaled <= 0 {
            0i128
        } else {
            let scaled_u128 = k2_shared::safe_i128_to_u128(&env, user_remaining_debt_scaled);
            let actual = k2_shared::ray_mul(&env, scaled_u128, fresh_debt_reserve_data.variable_borrow_index)?;
            k2_shared::safe_u128_to_i128(&env, actual)
        };

        let remaining_collateral = if user_remaining_coll_scaled <= 0 {
            0i128
        } else {
            let scaled_u128 = k2_shared::safe_i128_to_u128(&env, user_remaining_coll_scaled);
            let actual = k2_shared::ray_mul(&env, scaled_u128, fresh_collateral_reserve_data.liquidity_index)?;
            k2_shared::safe_u128_to_i128(&env, actual)
        };

        // M-16 / H-05: All collateral seized — remaining debt is unrecoverable bad debt.
        // Socialize unconditionally (no threshold). There is no collateral for another
        // liquidation to seize, so the debt must be burned and tracked as deficit.
        if collateral_cap_triggered && remaining_debt > 0 {
            let remaining_debt_u128 = k2_shared::safe_i128_to_u128(&env, remaining_debt);

            let mut bad_debt_burn_args = Vec::new(&env);
            bad_debt_burn_args.push_back(pool_address.to_val());
            bad_debt_burn_args.push_back(user.to_val());
            bad_debt_burn_args.push_back(IntoVal::into_val(&remaining_debt_u128, &env));
            bad_debt_burn_args.push_back(IntoVal::into_val(
                &fresh_debt_reserve_data.variable_borrow_index, &env,
            ));

            let bad_debt_burn_result = env.try_invoke_contract::<(bool, i128, i128), KineticRouterError>(
                &fresh_debt_reserve_data.debt_token_address,
                &Symbol::new(&env, "burn_scaled"),
                bad_debt_burn_args,
            );

            match bad_debt_burn_result {
                Ok(Ok((_is_zero, updated_total_scaled, _user_remaining))) => {
                    final_debt_scaled_total = Some(k2_shared::safe_i128_to_u128(&env, updated_total_scaled));
                }
                Ok(Err(_)) | Err(_) => {
                    return Err(KineticRouterError::InsufficientCollateral);
                }
            }

            // Track bad debt as deficit instead of socializing to depositors (Aave V3.3 pattern)
            storage::add_reserve_deficit(&env, &debt_asset, remaining_debt_u128);

            remaining_debt = 0;

            // I-03: Structured deficit event with collateral context
            env.events().publish(
                (symbol_short!("deficit"), symbol_short!("bad_debt")),
                (user.clone(), collateral_asset.clone(), debt_asset.clone(), remaining_debt_u128, storage::get_reserve_deficit(&env, &debt_asset)),
            );
        } else if remaining_debt > 0 {
            // F-1: Match liquidation.rs — when collateral_cap not triggered but partial
            // liquidation leaves dust below min_remaining_debt, revert.
            let min_remaining_whole = fresh_debt_reserve_data.configuration.get_min_remaining_debt();
            if min_remaining_whole > 0 {
                let remaining_debt_u128 = k2_shared::safe_i128_to_u128(&env, remaining_debt);
                let debt_decimals = fresh_debt_reserve_data.configuration.get_decimals() as u32;
                let debt_decimals_pow = 10_u128
                    .checked_pow(debt_decimals)
                    .ok_or(KineticRouterError::MathOverflow)?;
                let min_remaining_debt_val = (min_remaining_whole as u128)
                    .checked_mul(debt_decimals_pow)
                    .ok_or(KineticRouterError::MathOverflow)?;
                if remaining_debt_u128 < min_remaining_debt_val {
                    return Err(KineticRouterError::InvalidLiquidation);
                }
            }
        }

        // H-2
        {
            let mut post_user_config = storage::get_user_configuration(&env, &user);
            let mut config_changed = false;
            if remaining_collateral <= 0 {
                post_user_config.set_using_as_collateral(
                    k2_shared::safe_reserve_id(&env, fresh_collateral_reserve_data.id), false,
                );
                config_changed = true;
            }
            if remaining_debt <= 0 {
                post_user_config.set_borrowing(
                    k2_shared::safe_reserve_id(&env, fresh_debt_reserve_data.id), false,
                );
                config_changed = true;
            }
            if config_changed {
                storage::set_user_configuration(&env, &user, &post_user_config);
            }
        }

        // WP-L7: Check min leftover value for both debt and collateral (mirrors liquidation.rs)
        // When partial liquidation leaves tiny remaining positions, they become
        // uneconomical to liquidate further. Revert to force full liquidation.
        if remaining_debt > 0 && remaining_collateral > 0 {
            let remaining_debt_u128 = k2_shared::safe_i128_to_u128(&env, remaining_debt);
            let debt_decimals = fresh_debt_reserve_data.configuration.get_decimals() as u32;
            let debt_decimals_pow = 10_u128
                .checked_pow(debt_decimals)
                .ok_or(KineticRouterError::MathOverflow)?;
            let remaining_debt_value = {
                let rd = U256::from_u128(&env, remaining_debt_u128);
                let dp = U256::from_u128(&env, current_debt_price.price);
                let otw = U256::from_u128(&env, oracle_to_wad);
                let ddp = U256::from_u128(&env, debt_decimals_pow);
                rd.mul(&dp).mul(&otw).div(&ddp)
                    .to_u128()
                    .ok_or(KineticRouterError::MathOverflow)?
            };
            let remaining_collateral_u128 = k2_shared::safe_i128_to_u128(&env, remaining_collateral);
            let collateral_decimals = fresh_collateral_reserve_data.configuration.get_decimals() as u32;
            let collateral_decimals_pow = 10_u128
                .checked_pow(collateral_decimals)
                .ok_or(KineticRouterError::MathOverflow)?;
            let remaining_collateral_value = {
                let rc = U256::from_u128(&env, remaining_collateral_u128);
                let cp = U256::from_u128(&env, current_collateral_price.price);
                let otw = U256::from_u128(&env, oracle_to_wad);
                let cdp = U256::from_u128(&env, collateral_decimals_pow);
                rc.mul(&cp).mul(&otw).div(&cdp)
                    .to_u128()
                    .ok_or(KineticRouterError::MathOverflow)?
            };
            if remaining_debt_value < MIN_LEFTOVER_BASE || remaining_collateral_value < MIN_LEFTOVER_BASE {
                return Err(KineticRouterError::InvalidLiquidation);
            }
        }

        // Interest rate update: pass known scaled totals from callback (saves 2 scaled_total_supply calls)
        if collateral_asset == debt_asset {
            // Same asset: both a-token and debt-token totals known
            crate::calculation::update_interest_rates_and_store(
                &env, &debt_asset, fresh_debt_reserve_data,
                final_collateral_scaled_total, final_debt_scaled_total,
            )?;
        } else {
            // Debt reserve: debt_token total known, a_token unknown
            crate::calculation::update_interest_rates_and_store(
                &env, &debt_asset, fresh_debt_reserve_data,
                None, final_debt_scaled_total,
            )?;
            // Collateral reserve: a_token total known, debt_token unknown
            crate::calculation::update_interest_rates_and_store(
                &env, &collateral_asset, fresh_collateral_reserve_data,
                final_collateral_scaled_total, None,
            )?;
        }

        // WP-M2: Track liquidation amount to prevent bypass
        let debt_decimals = debt_reserve_data.configuration.get_decimals() as u32;
        let debt_decimals_pow = 10_u128
            .checked_pow(debt_decimals)
            .ok_or(KineticRouterError::MathOverflow)?;

        let actual_debt_to_cover_base = crate::calculation::value_in_base(
            &env, actual_debt_to_cover,
            current_debt_price.price, oracle_to_wad, debt_decimals_pow,
        )?;
        
        // DEBUG
        // println!("DEBUG: execute_liquidation tracking amount: {}", actual_debt_to_cover_base);
        // let before = storage::get_user_liquidation_amount(&env, &user);
        // println!("DEBUG: amount before: {}", before);
        
        storage::add_user_liquidation_amount(&env, &user, actual_debt_to_cover_base);
        
        // let after = storage::get_user_liquidation_amount(&env, &user);
        // println!("DEBUG: amount after: {}", after);

        // Step 8: Clear authorization (prevents replay)
        storage::remove_liquidation_authorization(&env, &liquidator, &user);

        env.events().publish(
            (symbol_short!("exec_ok"),),
            auth.nonce,
        );

        Ok(())
    }

    /// Set treasury address for protocol fees (admin only)
    ///
    /// # Arguments
    /// * `treasury` - New treasury address for protocol fee collection
    ///
    /// # Returns
    /// * `Ok(())` if treasury updated successfully
    /// * `Err(Unauthorized)` if caller is not admin
    pub fn set_treasury(env: Env, treasury: Address) -> Result<(), KineticRouterError> {
        crate::params::set_treasury(env, treasury)
    }

    pub fn get_treasury(env: Env) -> Option<Address> {
        crate::params::get_treasury(env)
    }

    /// F-02
    /// Safety net for when oracle precision changes without changing the oracle address.
    pub fn flush_oracle_config_cache(env: Env) -> Result<(), KineticRouterError> {
        let admin = storage::get_pool_admin(&env)?;
        admin.require_auth();
        storage::flush_oracle_config_cache(&env);
        Ok(())
    }

    /// AC-01
    /// Must be called once after contract upgrade to prevent whitelist/blacklist bypass.
    pub fn sync_access_control_flags(env: Env) -> Result<(), KineticRouterError> {
        let admin = storage::get_pool_admin(&env)?;
        admin.require_auth();
        storage::sync_access_control_flags(&env);
        Ok(())
    }

    pub fn set_flash_liquidation_helper(env: Env, helper: Address) -> Result<(), KineticRouterError> {
        crate::params::set_flash_liquidation_helper(env, helper)
    }

    pub fn get_flash_liquidation_helper(env: Env) -> Option<Address> {
        crate::params::get_flash_liquidation_helper(env)
    }

    /// Set pool configurator contract address (admin only)
    ///
    /// # Arguments
    /// * `configurator` - Pool configurator contract address
    ///
    /// # Returns
    /// * `Ok(())` if configurator address updated successfully
    /// * `Err(Unauthorized)` if caller is not admin
    pub fn set_pool_configurator(env: Env, configurator: Address) -> Result<(), KineticRouterError> {
        crate::params::set_pool_configurator(env, configurator)
    }

    pub fn get_pool_configurator(env: Env) -> Option<Address> {
        crate::params::get_pool_configurator(env)
    }

    /// Get available protocol reserves for an asset
    ///
    /// Protocol reserves accumulate due to the reserve factor, which reduces supplier APY.
    /// Reserves = underlying_balance_in_atoken - total_withdrawable_supply
    ///
    /// # Arguments
    /// * `asset` - The address of the underlying asset
    ///
    /// # Returns
    /// * `Ok(u128)` - Available reserves in smallest units
    /// * `Err` - If reserve not found or calculation fails
    pub fn get_protocol_reserves(env: Env, asset: Address) -> Result<u128, KineticRouterError> {
        crate::views::get_protocol_reserves(env, asset)
    }

    pub fn collect_protocol_reserves(env: Env, asset: Address) -> Result<u128, KineticRouterError> {
        let _guard = acquire_reentrancy_guard(&env);
        crate::treasury::collect_protocol_reserves(env.clone(), asset)
    }

    /// Cover accumulated bad debt deficit for a reserve.
    /// Permissionless: anyone can inject tokens to replenish pool liquidity.
    /// Returns the actual amount covered (capped at current deficit).
    pub fn cover_deficit(
        env: Env,
        caller: Address,
        asset: Address,
        amount: u128,
    ) -> Result<u128, KineticRouterError> {
        let _guard = acquire_reentrancy_guard(&env);
        crate::treasury::cover_deficit(env.clone(), caller, asset, amount)
    }

    /// Get accumulated bad debt deficit for a reserve (0 if none).
    pub fn get_reserve_deficit(env: Env, asset: Address) -> u128 {
        storage::get_reserve_deficit(&env, &asset)
    }

    pub fn set_user_use_reserve_as_coll(
        env: Env,
        caller: Address,
        asset: Address,
        use_as_collateral: bool,
    ) -> Result<(), KineticRouterError> {
        // F-04
        storage::extend_instance_ttl(&env);
        // Require caller authentication to prevent unauthorized collateral changes
        caller.require_auth();
        // LOW-001: Whitelist + blacklist must both be checked, matching all other user-facing ops
        validation::validate_reserve_whitelist_access(&env, &asset, &caller)?;
        validation::validate_reserve_blacklist_access(&env, &asset, &caller)?;

        // Validate reserve exists and is active
        let reserve_data = storage::get_reserve_data(&env, &asset)?;
        if !reserve_data.configuration.is_active() {
            return Err(KineticRouterError::AssetNotActive);
        }

        if use_as_collateral {
            crate::price::verify_oracle_price_exists_and_nonzero(&env, &asset)?;

            let mut user_config = storage::get_user_configuration(&env, &caller);
            user_config.set_using_as_collateral(k2_shared::safe_reserve_id(&env, reserve_data.id), true);
            storage::set_user_configuration(&env, &caller, &user_config);
        } else {
            // C-02
            // factor calculation reflects the post-toggle state (asset no longer
            // counted as collateral).  If HF is too low, revert the toggle.
            let mut user_config = storage::get_user_configuration(&env, &caller);
            user_config.set_using_as_collateral(k2_shared::safe_reserve_id(&env, reserve_data.id), false);
            storage::set_user_configuration(&env, &caller, &user_config);

            let user_account_data = crate::calculation::calculate_user_account_data(&env, &caller)?;
            if user_account_data.health_factor < 1_000_000_000_000_000_000 {
                // Revert the toggle -- position would become under-collateralized
                user_config.set_using_as_collateral(k2_shared::safe_reserve_id(&env, reserve_data.id), true);
                storage::set_user_configuration(&env, &caller, &user_config);
                return Err(KineticRouterError::InvalidLiquidation);
            }
        }

        env.events().publish(
            (symbol_short!("coll"), caller.clone(), asset.clone()),
            use_as_collateral,
        );

        Ok(())
    }

    /// Get user account data
    ///
    /// # Arguments
    /// * `user` - The address of the user
    pub fn get_user_account_data(
        env: Env,
        user: Address,
    ) -> Result<UserAccountData, KineticRouterError> {
        crate::views::get_user_account_data(env, user)
    }

    pub fn get_reserve_data(env: Env, asset: Address) -> Result<ReserveData, KineticRouterError> {
        crate::views::get_reserve_data(env, asset)
    }

    pub fn get_current_reserve_data(
        env: Env,
        asset: Address,
    ) -> Result<ReserveData, KineticRouterError> {
        crate::views::get_current_reserve_data(env, asset)
    }

    pub fn get_current_liquidity_index(
        env: Env,
        asset: Address,
    ) -> Result<u128, KineticRouterError> {
        crate::views::get_current_liquidity_index(env, asset)
    }

    pub fn get_current_var_borrow_idx(
        env: Env,
        asset: Address,
    ) -> Result<u128, KineticRouterError> {
        crate::views::get_current_var_borrow_idx(env, asset)
    }

    /// Get incentives contract address
    ///
    /// # Arguments
    /// * `env` - The Soroban environment
    ///
    /// # Returns
    /// * `Option<Address>` - The incentives contract address if set, None otherwise
    pub fn get_incentives_contract(env: Env) -> Option<Address> {
        crate::params::get_incentives_contract(env)
    }

    pub fn set_incentives_contract(env: Env, incentives: Address) -> Result<u32, KineticRouterError> {
        crate::params::set_incentives_contract(env, incentives)
    }

    /// Get user configuration
    ///
    /// # Arguments
    /// * `user` - The address of the user
    pub fn get_user_configuration(env: Env, user: Address) -> UserConfiguration {
        crate::views::get_user_configuration(env, user)
    }

    pub fn get_reserves_list(env: Env) -> Vec<Address> {
        crate::views::get_reserves_list(env)
    }

    /// L-02
    pub fn update_reserve_state(
        env: Env,
        asset: Address,
    ) -> Result<ReserveData, KineticRouterError> {
        crate::views::update_reserve_state(env, asset)
    }


    pub fn is_paused(env: Env) -> bool {
        crate::views::is_paused(env)
    }

    pub fn pause(env: Env, caller: Address) -> Result<(), KineticRouterError> {
        crate::emergency::pause(env, caller)
    }

    pub fn unpause(env: Env, caller: Address) -> Result<(), KineticRouterError> {
        crate::emergency::unpause(env, caller)
    }

    /// Initialize a new reserve
    ///
    /// # Note
    /// This function should be called by the pool configurator contract.
    /// The pool configurator should validate authorization before calling this function.
    ///
    /// # Arguments
    /// * `underlying_asset` - The address of the underlying asset
    /// * `a_token_impl` - The address of the aToken implementation
    /// * `variable_debt_impl` - The address of the variable debt token implementation
    /// * `interest_rate_strategy` - The address of the interest rate strategy
    /// * `treasury` - The address of the treasury
    /// * `params` - Reserve initialization parameters
    pub fn init_reserve(
        env: Env,
        caller: Address,
        underlying_asset: Address,
        a_token_impl: Address,
        variable_debt_impl: Address,
        interest_rate_strategy: Address,
        _treasury: Address,
        params: InitReserveParams,
    ) -> Result<(), KineticRouterError> {
        crate::reserve::init_reserve(
            env,
            caller,
            underlying_asset,
            a_token_impl,
            variable_debt_impl,
            interest_rate_strategy,
            _treasury,
            params,
        )
    }


    /// Updates the supply cap for a reserve.
    ///
    /// The supply cap limits the total amount that can be supplied to a reserve.
    /// Caps are stored as whole tokens (not smallest units) to maximize the
    /// effective range within the 32-bit storage limit.
    ///
    /// # Arguments
    /// - `env`: The Soroban environment
    /// - `asset`: The underlying asset address
    /// - `supply_cap`: New supply cap in whole tokens (0 = no cap, virtually unlimited)
    ///
    /// # Returns
    /// - `Ok(())`: Supply cap updated successfully
    /// - `Err(KineticRouterError::InvalidAmount)`: Invalid cap value
    /// - `Err(KineticRouterError::Unauthorized)`: Caller is not admin
    ///
    /// # Events
    /// Emits `(sup_cap, asset)` event with the new supply cap value.
    pub fn set_reserve_supply_cap(
        env: Env,
        asset: Address,
        supply_cap: u128,
    ) -> Result<(), KineticRouterError> {
        crate::reserve::set_reserve_supply_cap(env, asset, supply_cap)
    }

    /// Updates the borrow cap for a reserve.
    ///
    /// The borrow cap limits the total amount that can be borrowed from a reserve.
    /// Caps are stored as whole tokens (not smallest units) to maximize the
    /// effective range within the 32-bit storage limit.
    ///
    /// # Arguments
    /// - `env`: The Soroban environment
    /// - `asset`: The underlying asset address
    /// - `borrow_cap`: New borrow cap in whole tokens (0 = no cap, virtually unlimited)
    ///
    /// # Returns
    /// - `Ok(())`: Borrow cap updated successfully
    /// - `Err(KineticRouterError::InvalidAmount)`: Invalid cap value
    /// - `Err(KineticRouterError::Unauthorized)`: Caller is not admin
    ///
    /// # Events
    /// Emits `(bor_cap, asset)` event with the new borrow cap value.
    pub fn set_reserve_borrow_cap(
        env: Env,
        asset: Address,
        borrow_cap: u128,
    ) -> Result<(), KineticRouterError> {
        crate::reserve::set_reserve_borrow_cap(env, asset, borrow_cap)
    }

    /// Sets the minimum remaining debt after partial liquidation for a reserve.
    /// Value is in whole tokens (same convention as borrow/supply caps).
    /// Prevents dust debt positions that are uneconomical to liquidate.
    pub fn set_reserve_min_remaining_debt(
        env: Env,
        asset: Address,
        min_remaining_debt: u32,
    ) -> Result<(), KineticRouterError> {
        crate::reserve::set_reserve_min_remaining_debt(env, asset, min_remaining_debt)
    }

    /// Updates the debt ceiling for a reserve.
    ///
    /// The debt ceiling limits the total amount of debt that can be borrowed across
    /// all users for a specific reserve. This is different from borrow cap which limits
    /// per-reserve borrowing. Debt ceiling is stored as whole tokens (not smallest units).
    ///
    /// # Arguments
    /// - `env`: The Soroban environment
    /// - `asset`: The underlying asset address
    /// - `debt_ceiling`: New debt ceiling in whole tokens (0 = no ceiling)
    ///
    /// # Returns
    /// - `Ok(())`: Debt ceiling updated successfully
    /// - `Err(KineticRouterError::ReserveNotFound)`: Reserve does not exist
    /// - `Err(KineticRouterError::Unauthorized)`: Caller is not admin
    ///
    /// # Events
    /// Emits `(set_cap, asset)` event with `(debt_ceil, debt_ceiling)` value.
    pub fn set_reserve_debt_ceiling(
        env: Env,
        asset: Address,
        debt_ceiling: u128,
    ) -> Result<(), KineticRouterError> {
        crate::reserve::set_reserve_debt_ceiling(env, asset, debt_ceiling)
    }

    /// Gets the debt ceiling for a reserve.
    ///
    /// # Arguments
    /// - `asset`: The underlying asset address
    ///
    /// # Returns
    /// - `Ok(u128)`: Debt ceiling in whole tokens (0 = no ceiling)
    /// - `Err(KineticRouterError::ReserveNotFound)`: Reserve does not exist
    pub fn get_reserve_debt_ceiling(
        env: Env,
        asset: Address,
    ) -> Result<u128, KineticRouterError> {
        crate::reserve::get_reserve_debt_ceiling(env, asset)
    }

    /// Update reserve configuration (called by pool configurator)
    ///
    /// # Arguments
    /// - `caller`: The address calling this function (must be pool configurator)
    /// - `asset`: The underlying asset address
    /// - `configuration`: New reserve configuration
    pub fn update_reserve_configuration(
        env: Env,
        caller: Address,
        asset: Address,
        configuration: ReserveConfiguration,
    ) -> Result<(), KineticRouterError> {
        crate::reserve::update_reserve_configuration(env, caller, asset, configuration)
    }

    pub fn update_reserve_rate_strategy(
        env: Env,
        caller: Address,
        asset: Address,
        interest_rate_strategy: Address,
    ) -> Result<(), KineticRouterError> {
        crate::reserve::update_reserve_rate_strategy(env, caller, asset, interest_rate_strategy)
    }

    pub fn update_atoken_implementation(
        env: Env,
        caller: Address,
        asset: Address,
        a_token_impl: BytesN<32>,
    ) -> Result<(), KineticRouterError> {
        crate::reserve::update_atoken_implementation(env, caller, asset, a_token_impl)
    }

    pub fn update_debt_token_implementation(
        env: Env,
        caller: Address,
        asset: Address,
        debt_token_impl: BytesN<32>,
    ) -> Result<(), KineticRouterError> {
        crate::reserve::update_debt_token_implementation(env, caller, asset, debt_token_impl)
    }

    pub fn drop_reserve(
        env: Env,
        caller: Address,
        asset: Address,
    ) -> Result<(), KineticRouterError> {
        crate::reserve::drop_reserve(env, caller, asset)
    }

    /// Upgrade contract WASM (admin only)
    ///
    /// # Arguments
    /// * `new_wasm_hash` - Hash of new WASM binary
    ///
    /// # Errors
    /// * `Unauthorized` - Caller is not admin
    pub fn upgrade(env: Env, new_wasm_hash: BytesN<32>) -> Result<(), KineticRouterError> {
        crate::upgrade::upgrade(env, new_wasm_hash).map_err(|_| KineticRouterError::Unauthorized)
    }

    pub fn version(_env: Env) -> u32 {
        crate::upgrade::version()
    }

    pub fn get_admin(env: Env) -> Result<Address, KineticRouterError> {
        crate::upgrade::get_admin(&env).map_err(|_| KineticRouterError::Unauthorized)
    }

    /// Propose a new upgrade admin address (two-step transfer, step 1).
    /// Only the current admin can propose a new admin.
    /// The proposed admin must call `accept_admin` to complete the transfer.
    pub fn propose_admin(
        env: Env,
        caller: Address,
        pending_admin: Address,
    ) -> Result<(), KineticRouterError> {
        use k2_shared::upgradeable::admin;
        admin::propose_admin(&env, &caller, &pending_admin)
            .map_err(|e| match e {
                k2_shared::upgradeable::UpgradeError::Unauthorized => KineticRouterError::Unauthorized,
                k2_shared::upgradeable::UpgradeError::NoPendingAdmin => KineticRouterError::NoPendingAdmin,
                k2_shared::upgradeable::UpgradeError::InvalidPendingAdmin => KineticRouterError::InvalidPendingAdmin,
                _ => KineticRouterError::Unauthorized,
            })
    }

    /// Accept upgrade admin role (two-step transfer, step 2).
    /// Only the pending admin can call this to finalize the transfer.
    pub fn accept_admin(env: Env, caller: Address) -> Result<(), KineticRouterError> {
        use k2_shared::upgradeable::admin;
        admin::accept_admin(&env, &caller)
            .map_err(|e| match e {
                k2_shared::upgradeable::UpgradeError::NoPendingAdmin => KineticRouterError::NoPendingAdmin,
                k2_shared::upgradeable::UpgradeError::InvalidPendingAdmin => KineticRouterError::InvalidPendingAdmin,
                _ => KineticRouterError::Unauthorized,
            })
    }

    /// Cancel a pending upgrade admin proposal.
    /// Only the current admin can cancel a pending proposal.
    pub fn cancel_admin_proposal(env: Env, caller: Address) -> Result<(), KineticRouterError> {
        use k2_shared::upgradeable::admin;
        admin::cancel_admin_proposal(&env, &caller)
            .map_err(|e| match e {
                k2_shared::upgradeable::UpgradeError::Unauthorized => KineticRouterError::Unauthorized,
                k2_shared::upgradeable::UpgradeError::NoPendingAdmin => KineticRouterError::NoPendingAdmin,
                _ => KineticRouterError::Unauthorized,
            })
    }

    /// Get the pending upgrade admin address, if any.
    pub fn get_pending_admin(env: Env) -> Result<Address, KineticRouterError> {
        use k2_shared::upgradeable::admin;
        admin::get_pending_admin(&env)
            .map_err(|_| KineticRouterError::NoPendingAdmin)
    }

    /// Propose a new pool admin address (two-step transfer, step 1).
    pub fn propose_pool_admin(
        env: Env,
        caller: Address,
        pending_admin: Address,
    ) -> Result<(), KineticRouterError> {
        propose_role_admin(
            &env, &caller, &pending_admin,
            storage::get_pending_pool_admin,
            storage::set_pending_pool_admin,
            soroban_sdk::symbol_short!("pool_admc"),
            soroban_sdk::symbol_short!("pool_admp"),
        )
    }

    /// Accept pool admin role (two-step transfer, step 2).
    pub fn accept_pool_admin(env: Env, caller: Address) -> Result<(), KineticRouterError> {
        let pending = storage::get_pending_pool_admin(&env)?;
        let previous = storage::get_pool_admin(&env)?;
        accept_role_admin(
            &env, &caller, &pending, &previous,
            storage::set_pool_admin,
            storage::clear_pending_pool_admin,
            soroban_sdk::symbol_short!("pool_adma"),
        )
    }

    /// Cancel a pending pool admin proposal.
    pub fn cancel_pool_admin_proposal(env: Env, caller: Address) -> Result<(), KineticRouterError> {
        cancel_role_admin(
            &env, &caller,
            storage::get_pending_pool_admin,
            storage::clear_pending_pool_admin,
            soroban_sdk::symbol_short!("pool_admc"),
        )
    }

    /// Get the pending pool admin address, if any.
    pub fn get_pending_pool_admin(env: Env) -> Result<Address, KineticRouterError> {
        storage::get_pending_pool_admin(&env)
    }

    /// Propose a new emergency admin address (two-step transfer, step 1).
    pub fn propose_emergency_admin(
        env: Env,
        caller: Address,
        pending_admin: Address,
    ) -> Result<(), KineticRouterError> {
        propose_role_admin(
            &env, &caller, &pending_admin,
            storage::get_pending_emergency_admin,
            storage::set_pending_emergency_admin,
            soroban_sdk::symbol_short!("emrg_admc"),
            soroban_sdk::symbol_short!("emrg_admp"),
        )
    }

    /// Accept emergency admin role (two-step transfer, step 2).
    pub fn accept_emergency_admin(env: Env, caller: Address) -> Result<(), KineticRouterError> {
        let pending = storage::get_pending_emergency_admin(&env)?;
        let previous_admin = storage::get_emergency_admin(&env);
        let prev = previous_admin.unwrap_or_else(|| {
            storage::get_pool_admin(&env).unwrap_or_else(|_| {
                panic_with_error!(&env, KineticRouterError::NotInitialized)
            })
        });
        accept_role_admin(
            &env, &caller, &pending, &prev,
            storage::set_emergency_admin,
            storage::clear_pending_emergency_admin,
            soroban_sdk::symbol_short!("emrg_adma"),
        )
    }

    /// Cancel a pending emergency admin proposal.
    pub fn cancel_emergency_admin_proposal(env: Env, caller: Address) -> Result<(), KineticRouterError> {
        cancel_role_admin(
            &env, &caller,
            storage::get_pending_emergency_admin,
            storage::clear_pending_emergency_admin,
            soroban_sdk::symbol_short!("emrg_admc"),
        )
    }

    /// Get the pending emergency admin address, if any.
    pub fn get_pending_emergency_admin(env: Env) -> Result<Address, KineticRouterError> {
        storage::get_pending_emergency_admin(&env)
    }

    /// Set reserve whitelist (admin only)
    ///
    /// # Arguments
    /// * `caller` - Pool admin address
    /// * `asset` - Underlying asset address
    /// * `whitelist` - Addresses allowed to interact with this reserve
    ///
    /// # Behavior
    /// * Empty whitelist: open access
    /// * Non-empty whitelist: restricted to listed addresses
    ///
    /// ** Note **: This function replaces the entire whitelist. To add/remove addresses,
    /// first get the current list, modify it, then set the complete new list.
    ///
    /// # Errors
    /// * `Unauthorized` - Caller is not admin
    pub fn set_reserve_whitelist(
        env: Env,
        asset: Address,
        whitelist: Vec<Address>,
    ) -> Result<(), KineticRouterError> {
        crate::access_control::set_reserve_whitelist(env, asset, whitelist)
    }

    pub fn get_reserve_whitelist(env: Env, asset: Address) -> Vec<Address> {
        crate::access_control::get_reserve_whitelist(env, asset)
    }

    pub fn is_whitelisted_for_reserve(env: Env, asset: Address, address: Address) -> bool {
        crate::access_control::is_whitelisted_for_reserve(env, asset, address)
    }

    pub fn set_liquidation_whitelist(
        env: Env,
        whitelist: Vec<Address>,
    ) -> Result<(), KineticRouterError> {
        crate::access_control::set_liquidation_whitelist(env, whitelist)
    }

    pub fn get_liquidation_whitelist(env: Env) -> Vec<Address> {
        crate::access_control::get_liquidation_whitelist(env)
    }

    pub fn is_whitelisted_for_liquidation(env: Env, address: Address) -> bool {
        crate::access_control::is_whitelisted_for_liquidation(env, address)
    }

    pub fn set_reserve_blacklist(
        env: Env,
        asset: Address,
        blacklist: Vec<Address>,
    ) -> Result<(), KineticRouterError> {
        crate::access_control::set_reserve_blacklist(env, asset, blacklist)
    }

    pub fn get_reserve_blacklist(env: Env, asset: Address) -> Vec<Address> {
        crate::access_control::get_reserve_blacklist(env, asset)
    }

    pub fn is_blacklisted_for_reserve(env: Env, asset: Address, address: Address) -> bool {
        crate::access_control::is_blacklisted_for_reserve(env, asset, address)
    }

    pub fn set_liquidation_blacklist(
        env: Env,
        blacklist: Vec<Address>,
    ) -> Result<(), KineticRouterError> {
        crate::access_control::set_liquidation_blacklist(env, blacklist)
    }

    pub fn get_liquidation_blacklist(env: Env) -> Vec<Address> {
        crate::access_control::get_liquidation_blacklist(env)
    }

    pub fn is_blacklisted_for_liquidation(env: Env, address: Address) -> bool {
        crate::access_control::is_blacklisted_for_liquidation(env, address)
    }

    /// M-01
    /// Only whitelisted handlers can be used for custom swaps.
    /// Empty whitelist = deny all custom handlers (only built-in DEX).
    pub fn set_swap_handler_whitelist(
        env: Env,
        whitelist: Vec<Address>,
    ) -> Result<(), KineticRouterError> {
        crate::access_control::set_swap_handler_whitelist(env, whitelist)
    }

    pub fn get_swap_handler_whitelist(env: Env) -> Vec<Address> {
        crate::access_control::get_swap_handler_whitelist(env)
    }

    pub fn is_swap_handler_whitelisted(env: Env, handler: Address) -> bool {
        crate::access_control::is_swap_handler_whitelisted(env, handler)
    }

    /// WP-C1 + MEDIUM-1 fix: Validate sender HF and update bitmaps for aToken transfers.
    /// Called by aToken.transfer_internal() after computing balances but before writing them.
    /// Single cross-contract call replaces separate validate + finalize to save router size.
    ///
    /// 1. HF check: if sender has debt, validate the transfer won't make them liquidatable
    /// 2. Bitmap sync: clear sender's collateral bit if balance → 0, set receiver's if new position
    pub fn validate_and_finalize_transfer(
        env: Env,
        underlying_asset: Address,
        from: Address,
        to: Address,
        amount: u128,
        from_balance_after: u128,
        to_balance_after: u128,
    ) -> Result<(), KineticRouterError> {
        let reserve_data = storage::get_reserve_data(&env, &underlying_asset)?;
        let reserve_id = k2_shared::safe_reserve_id(&env, reserve_data.id);

        // Caller must be the aToken contract for this reserve.
        // In the legitimate flow, the aToken invokes this function via
        // env.try_invoke_contract, so require_auth() succeeds. Any other
        // caller (EOA or unrelated contract) will fail this check.
        reserve_data.a_token_address.require_auth();

        // --- HF validation (WP-C1) ---
        let mut from_config = storage::get_user_configuration(&env, &from);
        if from_config.has_any_borrowing() {
            let reserve_data = crate::calculation::update_state_without_store(&env, &reserve_data)?;
            let oracle_to_wad = crate::calculation::get_oracle_precision_factor(&env)?;
            validation::validate_user_can_withdraw(&env, &from, &underlying_asset, amount, &reserve_data, oracle_to_wad)?;
        }

        // --- Bitmap sync (MEDIUM-1 fix) ---
        // Sender: clear collateral bit if balance is now zero
        if from_balance_after == 0 {
            from_config.set_using_as_collateral(reserve_id, false);
            storage::set_user_configuration(&env, &from, &from_config);
        }

        // Receiver: set collateral bit if they now have a position
        if to_balance_after > 0 {
            let mut to_config = storage::get_user_configuration(&env, &to);
            if !to_config.is_using_as_collateral(reserve_id) {
                let active_count = to_config.count_active_reserves();
                if active_count >= storage::MAX_USER_RESERVES {
                    panic_with_error!(&env, k2_shared::UserReserveError::MaxUserReservesExceeded);
                }
                to_config.set_using_as_collateral(reserve_id, true);
                storage::set_user_configuration(&env, &to, &to_config);
            }
        }

        Ok(())
    }
}

