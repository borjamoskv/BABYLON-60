use soroban_sdk::Env;
use crate::storage::{AssetRewardConfig, AssetRewardIndex};
use crate::error::IncentivesError;

/// Update the asset reward index based on time elapsed
/// 
/// Formula:
/// - time_elapsed = current_timestamp - last_update_timestamp
/// - effective_time = min(time_elapsed, time_until_distribution_end)
/// - reward_increment = (emission_per_second × effective_time × RAY) / total_supply
/// - new_index = old_index + reward_increment
pub fn update_asset_reward_index(
    env: &Env,
    config: &AssetRewardConfig,
    current_index: &AssetRewardIndex,
    total_supply: u128,
) -> Result<AssetRewardIndex, IncentivesError> {
    let current_timestamp = env.ledger().timestamp();
    
    // If rewards are inactive, only update timestamp
    if !config.is_active {
        return Ok(AssetRewardIndex {
            index: current_index.index,
            last_update_timestamp: current_timestamp,
        });
    }
    
    // Calculate time elapsed
    let time_elapsed = if current_timestamp > current_index.last_update_timestamp {
        current_timestamp.checked_sub(current_index.last_update_timestamp)
            .ok_or(crate::error::IncentivesError::MathOverflow)?
    } else {
        0
    };
    
    // Check if distribution has ended
    let distribution_ended = config.distribution_end > 0 
        && current_timestamp >= config.distribution_end;
    
    // Cap effective time at distribution_end
    let effective_time = if distribution_ended {
        if config.distribution_end > current_index.last_update_timestamp {
            config.distribution_end.checked_sub(current_index.last_update_timestamp)
                .ok_or(crate::error::IncentivesError::MathOverflow)?
        } else {
            0
        }
    } else if config.distribution_end > 0 && config.distribution_end > current_index.last_update_timestamp {
        let time_until_end = config.distribution_end.checked_sub(current_index.last_update_timestamp)
            .ok_or(crate::error::IncentivesError::MathOverflow)?;
        if time_until_end < time_elapsed {
            time_until_end
        } else {
            time_elapsed
        }
    } else {
        time_elapsed
    };
    
    // If no effective time or zero supply, only update timestamp
    if effective_time == 0 || total_supply == 0 {
        return Ok(AssetRewardIndex {
            index: current_index.index,
            last_update_timestamp: current_timestamp,
        });
    }
    
    // Calculate reward increment: (emission_per_second × effective_time × RAY) / total_supply
    // First multiply emission_per_second by effective_time
    let emission_times_time = config.emission_per_second
        .checked_mul(effective_time as u128)
        .ok_or(IncentivesError::MathOverflow)?;
    
    // Then multiply by RAY and divide by total_supply
    // Using ray_div: (emission_times_time * RAY) / total_supply
    let reward_increment = k2_shared::ray_div(
        env,
        emission_times_time,
        total_supply,
    ).map_err(|_| IncentivesError::MathOverflow)?;
    
    // Calculate new index
    let new_index = current_index.index
        .checked_add(reward_increment)
        .ok_or(IncentivesError::MathOverflow)?;
    
    Ok(AssetRewardIndex {
        index: new_index,
        last_update_timestamp: current_timestamp,
    })
}

/// Calculate user's accrued rewards
/// 
/// Formula:
/// - index_diff = current_index - user_snapshot
/// - accrued = (index_diff × user_balance) / RAY
pub fn calculate_user_accrued_rewards(
    env: &Env,
    current_index: u128,
    user_snapshot: u128,
    user_balance: u128,
) -> Result<u128, crate::error::IncentivesError> {
    // If user has no balance, no rewards accrued
    if user_balance == 0 {
        return Ok(0);
    }
    
    // Calculate index difference (current_index >= user_snapshot by design)
    let index_diff = current_index.checked_sub(user_snapshot)
        .ok_or(crate::error::IncentivesError::MathOverflow)?;
    
    // Calculate accrued: (index_diff × user_balance) / RAY
    k2_shared::ray_mul(env, index_diff, user_balance)
        .map_err(|_| crate::error::IncentivesError::MathOverflow)
}

