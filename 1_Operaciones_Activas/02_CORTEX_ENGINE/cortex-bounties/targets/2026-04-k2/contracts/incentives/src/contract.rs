use crate::calculation;
use crate::error::IncentivesError;
use crate::events;
use crate::storage;
use k2_shared::*;
use soroban_sdk::token;
use soroban_sdk::{contract, contractimpl, panic_with_error, symbol_short, Address, Env, Map, Symbol, Vec};

use k2_shared::safe_u128_to_i128;

/// Incentives Contract
///
/// Manages reward distribution for supply and borrow positions in the K2 Lending Protocol.
/// Uses an index-based reward system similar to Aave's RewardsController for gas efficiency.
///
/// Key Features:
/// - Lazy reward accrual (rewards calculated only when users interact)
/// - Dual incentivization (separate rewards for supply and borrow)
/// - Multiple reward tokens per asset
/// - Time-based distribution with configurable emission rates and end dates
///
/// # Funding Requirements
///
/// **IMPORTANT**: The contract must be funded with reward tokens before users can claim rewards.
/// The emission manager must deposit reward tokens into the contract using `fund_rewards()`.
/// The contract transfers reward tokens from its own balance when users claim rewards.
/// Use `get_reward_token_balance()` to check the contract's balance for each reward token.
#[contract]
pub struct IncentivesContract;

#[contractimpl]
impl IncentivesContract {
    /// Initialize the incentives contract
    ///
    /// # Arguments
    /// - `emission_manager`: Address authorized to configure rewards
    /// - `lending_pool`: Address authorized to call `handle_action`
    pub fn __constructor(
        env: Env,
        emission_manager: Address,
        lending_pool: Address,
    ) {
        if storage::is_initialized(&env) {
            panic!("Already initialized");
        }

        storage::set_emission_manager(&env, &emission_manager);
        storage::set_lending_pool(&env, &lending_pool);
        storage::set_initialized(&env);
    }

    pub fn initialize(
        _env: Env,
        _emission_manager: Address,
        _lending_pool: Address,
    ) -> Result<(), IncentivesError> {
        panic!("Initialization is atomic at deployment. Use __constructor.");
    }

    /// Handle action called by token contracts (aToken/debtToken) when balances change
    ///
    /// This is the core function that updates reward indices and calculates user rewards.
    /// Called after balance updates (mint/burn) to update rewards.
    ///
    /// # Arguments
    /// - `token_address`: The aToken or debtToken address (the asset identifier)
    /// - `user`: The user address whose balance changed
    /// - `total_supply`: Total scaled supply/borrow for the asset
    /// - `user_balance`: User's scaled balance
    /// - `reward_type`: 0 for supply, 1 for borrow
    ///
    /// # Security
    /// - Only the token contract itself can call this function (enforced via require_auth)
    /// - Asset is determined by `token_address` parameter
    /// - If token_address is not a registered asset, function returns early (no-op)
    /// - Parameters cannot affect rewards unless token_address is a whitelisted token contract
    pub fn handle_action(
        env: Env,
        token_address: Address,
        user: Address,
        total_supply: u128,
        user_balance: u128,
        reward_type: u32,
    ) -> Result<(), IncentivesError> {
        token_address.require_auth();

        if !storage::is_initialized(&env) {
            return Err(IncentivesError::NotInitialized);
        }

        if reward_type != storage::REWARD_TYPE_SUPPLY && reward_type != storage::REWARD_TYPE_BORROW
        {
            return Err(IncentivesError::InvalidRewardType);
        }

        let asset = token_address;
        let reward_tokens = storage::get_reward_tokens(&env, &asset);
        if reward_tokens.len() == 0 {
            return Ok(());
        }

        // Process each reward token
        for i in 0..reward_tokens.len() {
            let reward_token = reward_tokens.get(i).ok_or(IncentivesError::MathOverflow)?;

            // Accrue rewards for this user/asset/token/type combination
            let mut user_data = _accrue_user_rewards(
                &env,
                &asset,
                &reward_token,
                &user,
                reward_type,
                total_supply,
            )?;

            // Update balance snapshot to the NEW balance after accrual
            user_data.balance_snapshot = user_balance;

            // Save updated user data
            storage::set_user_reward_data(
                &env,
                &asset,
                &reward_token,
                &user,
                reward_type,
                &user_data,
            );

            // Emit event for reward update
            env.events().publish(
                (symbol_short!("reward"), symbol_short!("updated")),
                events::RewardUpdatedEvent {
                    asset: asset.clone(),
                    user: user.clone(),
                    reward_token: reward_token.clone(),
                    reward_type,
                    new_accrued: 0, // Injected via internal call, event field left for compatibility
                    total_accrued: user_data.accrued,
                    updated_index: user_data.index_snapshot,
                },
            );
        }

        Ok(())
    }

    /// Claim rewards for specific assets and reward token
    ///
    /// # Arguments
    /// - `caller`: Address calling the function (must be authorized)
    /// - `assets`: List of assets to claim rewards for
    /// - `reward_token`: The reward token to claim
    /// - `amount`: Amount to claim (0 = claim all available)
    /// - `to`: Address to receive the rewards
    ///
    /// # Returns
    /// The amount of rewards actually claimed
    ///
    /// # Errors
    /// Returns `InsufficientRewards` if `amount > 0` and the requested amount exceeds
    /// the total claimable rewards across all assets and reward types.
    pub fn claim_rewards(
        env: Env,
        caller: Address,
        assets: Vec<Address>,
        reward_token: Address,
        amount: u128,
        to: Address,
    ) -> Result<u128, IncentivesError> {
        // Validate caller authorization
        caller.require_auth();

        // Check if contract is paused
        if storage::is_paused(&env) {
            return Err(IncentivesError::ContractPaused);
        }

        let user = caller.clone();

        // ========================================================================
        // PHASE 1: Update and accrue all pending rewards (lazy-sync)
        // ========================================================================
        let mut total_claimable = 0u128;

        for i in 0..assets.len() {
            let asset = assets.get(i).ok_or(IncentivesError::MathOverflow)?;

            // Fetch total supply for this asset (required for index update)
            let total_supply = _get_scaled_total_supply(&env, &asset);

            for reward_type in [storage::REWARD_TYPE_SUPPLY, storage::REWARD_TYPE_BORROW] {
                // Accrue pending rewards since last interaction
                let user_data = _accrue_user_rewards(
                    &env,
                    &asset,
                    &reward_token,
                    &user,
                    reward_type,
                    total_supply,
                )?;

                // Save accrued state
                storage::set_user_reward_data(
                    &env,
                    &asset,
                    &reward_token,
                    &user,
                    reward_type,
                    &user_data,
                );

                total_claimable = total_claimable
                    .checked_add(user_data.accrued)
                    .ok_or(IncentivesError::MathOverflow)?;
            }
        }

        // ========================================================================
        // PHASE 2: Validate requested amount
        // ========================================================================
        let amount_to_claim = if amount == 0 {
            total_claimable
        } else {
            if amount > total_claimable {
                return Err(IncentivesError::InsufficientRewards);
            }
            amount
        };

        if amount_to_claim == 0 {
            return Ok(0);
        }

        // ========================================================================
        // PHASE 3: Deduct rewards from state
        // ========================================================================
        let mut total_claimed = 0u128;

        for i in 0..assets.len() {
            let asset = assets.get(i).ok_or(IncentivesError::MathOverflow)?;

            for reward_type in [storage::REWARD_TYPE_SUPPLY, storage::REWARD_TYPE_BORROW] {
                if total_claimed >= amount_to_claim {
                    break;
                }

                let mut user_data = storage::get_user_reward_data(
                    &env,
                    &asset,
                    &reward_token,
                    &user,
                    reward_type,
                );

                let remaining_to_claim = amount_to_claim
                    .checked_sub(total_claimed)
                    .ok_or(IncentivesError::MathOverflow)?;

                let claimable = if remaining_to_claim < user_data.accrued {
                    remaining_to_claim
                } else {
                    user_data.accrued
                };

                if claimable > 0 {
                    user_data.accrued = user_data
                        .accrued
                        .checked_sub(claimable)
                        .ok_or(IncentivesError::MathOverflow)?;

                    storage::set_user_reward_data(
                        &env,
                        &asset,
                        &reward_token,
                        &user,
                        reward_type,
                        &user_data,
                    );

                    total_claimed = total_claimed
                        .checked_add(claimable)
                        .ok_or(IncentivesError::MathOverflow)?;
                }
            }
            if total_claimed >= amount_to_claim {
                break;
            }
        }

        // ========================================================================
        // PHASE 4: Transfer rewards and emit event
        // ========================================================================
        if total_claimed > 0 {
            let client = token::Client::new(&env, &reward_token);
            client.transfer(
                &env.current_contract_address(),
                &to,
                &safe_u128_to_i128(&env, total_claimed),
            );

            env.events().publish(
                (symbol_short!("claim"), symbol_short!("rewards")),
                events::RewardsClaimedEvent {
                    user: user.clone(),
                    reward_token,
                    amount: total_claimed,
                    to,
                },
            );
        }

        Ok(total_claimed)
    }

    /// Claim all rewards for all configured reward tokens
    ///
    /// This function batches transfers by reward token to reduce gas costs.
    /// Instead of one transfer per (asset, reward_token, reward_type) combination,
    /// it accumulates all rewards per reward token and does a single transfer per token.
    ///
    /// # Gas Optimization
    /// - **Before**: N transfers for N reward positions (e.g., 3 assets × 2 tokens × 2 types = 12 transfers)
    /// - **After**: M transfers for M unique reward tokens (e.g., 2 transfers for 2 unique tokens)
    /// - **Savings**: Reduces transfers from O(assets × tokens × types) to O(unique_tokens)
    ///
    /// # Arguments
    /// - `caller`: Address calling the function (must be authorized)
    /// - `assets`: List of assets to claim rewards for
    /// - `to`: Address to receive the rewards
    pub fn claim_all_rewards(
        env: Env,
        caller: Address,
        assets: Vec<Address>,
        to: Address,
    ) -> Result<(), IncentivesError> {
        // Clone caller before require_auth (which moves it)
        let user = caller.clone();

        // Validate caller authorization
        caller.require_auth();

        // Check if contract is paused
        if storage::is_paused(&env) {
            return Err(IncentivesError::ContractPaused);
        }

        use crate::constants::MAX_CLAIMABLE_ASSETS;

        // Get all configured assets if none provided
        let assets_to_process = if assets.len() == 0 {
            storage::get_assets(&env)
        } else {
            assets
        };

        if assets_to_process.len() > MAX_CLAIMABLE_ASSETS {
            return Err(IncentivesError::MaxAssetsExceeded);
        }

        // ========================================================================
        // PHASE 1: Collect all unique reward tokens and accumulate amounts
        // ========================================================================
        // We'll use a Vec to store (reward_token, total_amount) pairs
        // Since we can't use HashMap in Soroban easily, we'll accumulate as we go
        let mut reward_token_amounts: Map<Address, u128> = Map::new(&env);

        // First pass: Update state and accumulate rewards per token
        for i in 0..assets_to_process.len().min(MAX_CLAIMABLE_ASSETS) {
            let asset = assets_to_process.get(i).ok_or(IncentivesError::MathOverflow)?;

            // Get all reward tokens for this asset
            let reward_tokens = storage::get_reward_tokens(&env, &asset);
            let total_supply = _get_scaled_total_supply(&env, &asset);

            // Process each reward token
            for j in 0..reward_tokens.len() {
                let reward_token = reward_tokens.get(j).ok_or(IncentivesError::MathOverflow)?;

                // Process both reward types
                for reward_type in [storage::REWARD_TYPE_SUPPLY, storage::REWARD_TYPE_BORROW] {
                    // Accrue and update user data
                    let mut user_data = _accrue_user_rewards(
                        &env,
                        &asset,
                        &reward_token,
                        &user,
                        reward_type,
                        total_supply,
                    )?;

                    if user_data.accrued > 0 {
                        let claimable = user_data.accrued;
                        user_data.accrued = 0;
                        storage::set_user_reward_data(
                            &env,
                            &asset,
                            &reward_token,
                            &user,
                            reward_type,
                            &user_data,
                        );

                        let existing = reward_token_amounts.get(reward_token.clone()).unwrap_or(0u128);
                        let new_amount = existing
                            .checked_add(claimable)
                            .ok_or(IncentivesError::MathOverflow)?;
                        reward_token_amounts.set(reward_token.clone(), new_amount);
                    } else {
                        // Still save to update index_snapshot even if 0 rewards
                        storage::set_user_reward_data(
                            &env,
                            &asset,
                            &reward_token,
                            &user,
                            reward_type,
                            &user_data,
                        );
                    }
                }
            }
        }

        // ========================================================================
        // PHASE 2: Execute batched transfers (one per reward token)
        // ========================================================================
        let reward_keys = reward_token_amounts.keys();
        for i in 0..reward_keys.len() {
            let reward_token = reward_keys.get(i).ok_or(KineticRouterError::InvalidAmount)?;
            let total_amount = reward_token_amounts.get(reward_token.clone()).unwrap_or(0);

            if total_amount > 0 {
                // Single transfer for all accumulated rewards of this token
                let client = token::Client::new(&env, &reward_token);
                client.transfer(
                    &env.current_contract_address(),
                    &to,
                    &safe_u128_to_i128(&env, total_amount),
                );

                // Emit event for the batched transfer
                env.events().publish(
                    (symbol_short!("claim"), symbol_short!("rewards")),
                    events::RewardsClaimedEvent {
                        user: user.clone(),
                        reward_token: reward_token.clone(),
                        amount: total_amount,
                        to: to.clone(),
                    },
                );
            }
        }

        Ok(())
    }

    /// Configure asset rewards (admin function)
    ///
    /// Following Aave's pattern: rewards are configured per token contract (aToken/debtToken),
    /// not per underlying asset. The `asset` parameter is the token address that will call handle_action.
    ///
    /// # Arguments
    /// - `caller`: Must be emission_manager
    /// - `asset`: The token address (aToken or debtToken) - this is the asset identifier
    /// - `reward_token`: The reward token to distribute
    /// - `reward_type`: 0 for supply, 1 for borrow
    /// - `emission_per_second`: Emission rate in reward tokens per second
    /// - `distribution_end`: Distribution end timestamp (0 = no end)
    pub fn configure_asset_rewards(
        env: Env,
        caller: Address,
        asset: Address,
        reward_token: Address,
        reward_type: u32,
        emission_per_second: u128,
        distribution_end: u64,
    ) -> Result<(), IncentivesError> {
        // Validate caller
        storage::validate_emission_manager(&env, &caller)?;
        caller.require_auth();

        // Validate reward type
        if reward_type != storage::REWARD_TYPE_SUPPLY && reward_type != storage::REWARD_TYPE_BORROW
        {
            return Err(IncentivesError::InvalidRewardType);
        }

        // Create or update configuration
        let config = storage::AssetRewardConfig {
            emission_per_second,
            distribution_end,
            is_active: true,
        };

        storage::set_asset_reward_config(&env, &asset, &reward_token, reward_type, &config)?;

        // Initialize index if it doesn't exist
        if !storage::has_asset_reward_index(&env, &asset, &reward_token, reward_type) {
            let current_timestamp = env.ledger().timestamp();
            let new_index = storage::AssetRewardIndex {
                index: RAY,
                last_update_timestamp: current_timestamp,
            };
            storage::set_asset_reward_index(&env, &asset, &reward_token, reward_type, &new_index);
        }

        // Emit event
        env.events().publish(
            (
                symbol_short!("asset"),
                symbol_short!("reward"),
                symbol_short!("config"),
            ),
            events::AssetRewardConfiguredEvent {
                asset,
                reward_token,
                reward_type,
                emission_per_second,
                distribution_end,
            },
        );

        Ok(())
    }

    /// Set emission per second for an asset reward (admin function)
    ///
    /// # Arguments
    /// - `caller`: Must be emission_manager
    /// - `asset`: The underlying asset address
    /// - `reward_token`: The reward token address
    /// - `reward_type`: 0 for supply, 1 for borrow
    /// - `new_emission_per_second`: New emission rate
    pub fn set_emission_per_second(
        env: Env,
        caller: Address,
        asset: Address,
        reward_token: Address,
        reward_type: u32,
        new_emission_per_second: u128,
    ) -> Result<(), IncentivesError> {
        // Validate caller
        storage::validate_emission_manager(&env, &caller)?;
        caller.require_auth();

        // Validate reward type
        if reward_type != storage::REWARD_TYPE_SUPPLY && reward_type != storage::REWARD_TYPE_BORROW
        {
            return Err(IncentivesError::InvalidRewardType);
        }

        // Get existing configuration
        let mut config = storage::get_asset_reward_config(&env, &asset, &reward_token, reward_type)
            .ok_or(IncentivesError::AssetRewardConfigNotFound)?;

        // N-12
        if config.is_active {
            // Get total supply for this asset
            let total_supply = _get_scaled_total_supply(&env, &asset);

            if total_supply > 0 {
                let current_index = storage::get_asset_reward_index(&env, &asset, &reward_token, reward_type);
                let updated_index = calculation::update_asset_reward_index(
                    &env,
                    &config,
                    &current_index,
                    total_supply,
                )?;
                storage::set_asset_reward_index(&env, &asset, &reward_token, reward_type, &updated_index);
            }
        }

        // Update emission rate
        config.emission_per_second = new_emission_per_second;

        // Save updated configuration
        storage::set_asset_reward_config(&env, &asset, &reward_token, reward_type, &config)?;

        // Emit event
        env.events().publish(
            (
                symbol_short!("emission"),
                symbol_short!("rate"),
                symbol_short!("updated"),
            ),
            events::EmissionRateUpdatedEvent {
                asset,
                reward_token,
                reward_type,
                new_emission_per_second,
            },
        );

        Ok(())
    }

    /// Set distribution end timestamp (admin function)
    ///
    /// # Arguments
    /// - `caller`: Must be emission_manager
    /// - `asset`: The underlying asset address
    /// - `reward_token`: The reward token address
    /// - `reward_type`: 0 for supply, 1 for borrow
    /// - `new_distribution_end`: New distribution end timestamp (0 = no end)
    pub fn set_distribution_end(
        env: Env,
        caller: Address,
        asset: Address,
        reward_token: Address,
        reward_type: u32,
        new_distribution_end: u64,
    ) -> Result<(), IncentivesError> {
        // Validate caller
        storage::validate_emission_manager(&env, &caller)?;
        caller.require_auth();

        // Validate reward type
        if reward_type != storage::REWARD_TYPE_SUPPLY && reward_type != storage::REWARD_TYPE_BORROW
        {
            return Err(IncentivesError::InvalidRewardType);
        }

        // Get existing configuration
        let mut config = storage::get_asset_reward_config(&env, &asset, &reward_token, reward_type)
            .ok_or(IncentivesError::AssetRewardConfigNotFound)?;

        // Update distribution end
        config.distribution_end = new_distribution_end;

        // Save updated configuration
        storage::set_asset_reward_config(&env, &asset, &reward_token, reward_type, &config)?;

        // Emit event
        env.events().publish(
            (symbol_short!("dist_end"), symbol_short!("updated")),
            events::DistributionEndUpdatedEvent {
                asset,
                reward_token,
                reward_type,
                new_distribution_end,
            },
        );

        Ok(())
    }

    /// Remove/deactivate asset reward (admin function)
    ///
    /// # Arguments
    /// - `caller`: Must be emission_manager
    /// - `asset`: The underlying asset address
    /// - `reward_token`: The reward token address
    /// - `reward_type`: 0 for supply, 1 for borrow
    pub fn remove_asset_reward(
        env: Env,
        caller: Address,
        asset: Address,
        reward_token: Address,
        reward_type: u32,
    ) -> Result<(), IncentivesError> {
        // Validate caller
        storage::validate_emission_manager(&env, &caller)?;
        caller.require_auth();

        // Validate reward type
        if reward_type != storage::REWARD_TYPE_SUPPLY && reward_type != storage::REWARD_TYPE_BORROW
        {
            return Err(IncentivesError::InvalidRewardType);
        }

        // Get existing configuration
        let mut config = storage::get_asset_reward_config(&env, &asset, &reward_token, reward_type)
            .ok_or(IncentivesError::AssetRewardConfigNotFound)?;

        // Deactivate
        config.is_active = false;

        // Save updated configuration
        storage::set_asset_reward_config(&env, &asset, &reward_token, reward_type, &config)?;

        // Emit event
        env.events().publish(
            (
                symbol_short!("asset"),
                symbol_short!("reward"),
                symbol_short!("removed"),
            ),
            events::AssetRewardRemovedEvent {
                asset,
                reward_token,
                reward_type,
            },
        );

        Ok(())
    }

    /// Permanently delete a reward token from an asset's registered list.
    ///
    /// Unlike `remove_asset_reward` which only deactivates, this removes the token
    /// from the enumeration list entirely. Both supply and borrow configs for this
    /// reward token must be inactive before deletion.
    ///
    /// # Arguments
    /// - `caller`: Must be emission_manager
    /// - `asset`: The aToken or debtToken address
    /// - `reward_token`: The reward token to unregister
    pub fn delete_reward_token(
        env: Env,
        caller: Address,
        asset: Address,
        reward_token: Address,
    ) -> Result<(), IncentivesError> {
        storage::validate_emission_manager(&env, &caller)?;
        caller.require_auth();

        // Ensure both supply and borrow configs are inactive
        for reward_type in [storage::REWARD_TYPE_SUPPLY, storage::REWARD_TYPE_BORROW] {
            if let Some(config) =
                storage::get_asset_reward_config(&env, &asset, &reward_token, reward_type)
            {
                if config.is_active {
                    return Err(IncentivesError::RewardTokenStillActive);
                }
            }
        }

        // Remove from registered list
        storage::remove_reward_token(&env, &asset, &reward_token);

        // Check if asset has any remaining reward tokens — if not, remove asset too
        let remaining = storage::get_reward_tokens(&env, &asset);
        if remaining.len() == 0 {
            storage::remove_asset(&env, &asset);
        }

        env.events().publish(
            (symbol_short!("reward"), symbol_short!("deleted")),
            (asset, reward_token),
        );

        Ok(())
    }

    /// Pause the incentives contract (emergency admin function)
    ///
    /// When paused, users cannot claim rewards. Admin functions remain available.
    /// Rewards continue to accrue via `handle_action`, but claims are blocked.
    ///
    /// # Arguments
    /// - `caller`: Must be emission_manager
    pub fn pause(env: Env, caller: Address) -> Result<(), IncentivesError> {
        // Validate caller
        storage::validate_emission_manager(&env, &caller)?;
        caller.require_auth();

        storage::set_paused(&env, true);

        // Emit event
        env.events().publish(
            (symbol_short!("pause"),),
            events::ContractPausedEvent { paused_by: caller },
        );

        Ok(())
    }

    /// Unpause the incentives contract (emergency admin function)
    ///
    /// # Arguments
    /// - `caller`: Must be emission_manager
    pub fn unpause(env: Env, caller: Address) -> Result<(), IncentivesError> {
        // Validate caller
        storage::validate_emission_manager(&env, &caller)?;
        caller.require_auth();

        storage::set_paused(&env, false);

        // Emit event
        env.events().publish(
            (symbol_short!("unpause"),),
            events::ContractUnpausedEvent {
                unpaused_by: caller,
            },
        );

        Ok(())
    }

    /// Check if the contract is paused
    ///
    /// # Returns
    /// `true` if paused, `false` otherwise
    pub fn is_paused(env: Env) -> bool {
        storage::is_paused(&env)
    }

    /// Fund the contract with reward tokens (admin function)
    ///
    /// Transfers reward tokens from the emission manager to the contract.
    /// The contract must be funded before users can claim rewards.
    ///
    /// # Arguments
    /// - `caller`: Must be emission_manager
    /// - `reward_token`: The reward token address to fund
    /// - `amount`: Amount of reward tokens to transfer to the contract
    pub fn fund_rewards(
        env: Env,
        caller: Address,
        reward_token: Address,
        amount: u128,
    ) -> Result<(), IncentivesError> {
        // Validate caller authorization
        caller.require_auth();

        // Validate caller is emission manager
        storage::validate_emission_manager(&env, &caller)?;

        if amount == 0 {
            return Err(IncentivesError::MathOverflow); // Reuse error for invalid amount
        }

        // Transfer tokens from caller to contract
        let client = token::Client::new(&env, &reward_token);
        client.transfer(&caller, &env.current_contract_address(), &safe_u128_to_i128(&env, amount));

        // Emit event
        env.events().publish(
            (symbol_short!("rewards"), symbol_short!("funded")),
            events::RewardsFundedEvent {
                reward_token,
                amount,
                funder: caller,
            },
        );

        Ok(())
    }

    // ============================================================================
    // View Functions
    // ============================================================================

    /// Get asset reward configuration
    pub fn get_asset_reward_config(
        env: Env,
        asset: Address,
        reward_token: Address,
        reward_type: u32,
    ) -> Option<storage::AssetRewardConfig> {
        storage::get_asset_reward_config(&env, &asset, &reward_token, reward_type)
    }

    /// Get asset reward index
    pub fn get_asset_reward_index(
        env: Env,
        asset: Address,
        reward_token: Address,
        reward_type: u32,
    ) -> storage::AssetRewardIndex {
        storage::get_asset_reward_index(&env, &asset, &reward_token, reward_type)
    }

    /// Get user reward data
    pub fn get_user_reward_data(
        env: Env,
        asset: Address,
        reward_token: Address,
        user: Address,
        reward_type: u32,
    ) -> storage::UserRewardData {
        storage::get_user_reward_data(&env, &asset, &reward_token, &user, reward_type)
    }

    /// Get user's accrued rewards
    pub fn get_user_accrued_rewards(
        env: Env,
        asset: Address,
        reward_token: Address,
        user: Address,
        reward_type: u32,
    ) -> u128 {
        let user_data =
            storage::get_user_reward_data(&env, &asset, &reward_token, &user, reward_type);
        user_data.accrued
    }

    /// Get all configured assets
    pub fn get_assets(env: Env) -> Vec<Address> {
        storage::get_assets(&env)
    }

    /// Get reward tokens for an asset
    pub fn get_reward_tokens(env: Env, asset: Address) -> Vec<Address> {
        storage::get_reward_tokens(&env, &asset)
    }

    /// Get the contract's balance for a reward token
    ///
    /// Returns the amount of reward tokens held by the contract.
    /// This can be used to check if the contract has sufficient funds
    /// to cover pending reward claims.
    ///
    /// # Arguments
    /// - `reward_token`: The reward token address to check
    ///
    /// # Returns
    /// The contract's balance of the reward token
    pub fn get_reward_token_balance(env: Env, reward_token: Address) -> u128 {
        let client = token::Client::new(&env, &reward_token);
        let balance = client.balance(&env.current_contract_address());
        
        k2_shared::safe_i128_to_u128(&env, balance)
    }
}

fn _get_scaled_total_supply(env: &Env, asset: &Address) -> u128 {
    let args = Vec::new(env);
    match env.try_invoke_contract::<u128, IncentivesError>(
        asset,
        &Symbol::new(env, "scaled_total_supply"),
        args,
    ) {
        Ok(Ok(supply)) => supply,
        _ => 0,
    }
}

fn _accrue_user_rewards(
    env: &Env,
    asset: &Address,
    reward_token: &Address,
    user: &Address,
    reward_type: u32,
    total_supply: u128,
) -> Result<storage::UserRewardData, IncentivesError> {
    let mut user_data = storage::get_user_reward_data(env, asset, reward_token, user, reward_type);

    // Get asset reward configuration
    let config = match storage::get_asset_reward_config(env, asset, reward_token, reward_type) {
        Some(config) => config,
        None => return Ok(user_data), // Skip if not configured
    };

    // Skip update if no supply or inactive, but still return current user_data
    if !config.is_active || total_supply == 0 {
        return Ok(user_data);
    }

    // Get current asset reward index
    let current_index = storage::get_asset_reward_index(env, asset, reward_token, reward_type);

    // Update the global reward index
    let updated_index = calculation::update_asset_reward_index(
        env,
        &config,
        &current_index,
        total_supply,
    )?;

    // Save updated global index
    storage::set_asset_reward_index(
        env,
        asset,
        reward_token,
        reward_type,
        &updated_index,
    );

    // Calculate new accrued rewards based on balance HELD (snapshot)
    let new_accrued = calculation::calculate_user_accrued_rewards(
        env,
        updated_index.index,
        user_data.index_snapshot,
        user_data.balance_snapshot,
    )?;

    user_data.accrued = user_data
        .accrued
        .checked_add(new_accrued)
        .ok_or(IncentivesError::MathOverflow)?;

    // Update index snapshot
    user_data.index_snapshot = updated_index.index;

    Ok(user_data)
}
