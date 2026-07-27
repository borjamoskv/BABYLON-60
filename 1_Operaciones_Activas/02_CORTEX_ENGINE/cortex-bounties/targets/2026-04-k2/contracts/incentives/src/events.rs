use soroban_sdk::{contracttype, Address};

/// Event emitted when rewards are claimed
#[contracttype]
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct RewardsClaimedEvent {
    pub user: Address,
    pub reward_token: Address,
    pub amount: u128,
    pub to: Address,
}

/// Event emitted when asset rewards are configured
#[contracttype]
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct AssetRewardConfiguredEvent {
    pub asset: Address,
    pub reward_token: Address,
    pub reward_type: u32,
    pub emission_per_second: u128,
    pub distribution_end: u64,
}

/// Event emitted when emission rate is updated
#[contracttype]
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct EmissionRateUpdatedEvent {
    pub asset: Address,
    pub reward_token: Address,
    pub reward_type: u32,
    pub new_emission_per_second: u128,
}

/// Event emitted when distribution end is updated
#[contracttype]
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct DistributionEndUpdatedEvent {
    pub asset: Address,
    pub reward_token: Address,
    pub reward_type: u32,
    pub new_distribution_end: u64,
}

/// Event emitted when asset reward is removed/deactivated
#[contracttype]
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct AssetRewardRemovedEvent {
    pub asset: Address,
    pub reward_token: Address,
    pub reward_type: u32,
}

/// Event emitted when rewards are updated for a user
#[contracttype]
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct RewardUpdatedEvent {
    pub asset: Address,
    pub user: Address,
    pub reward_token: Address,
    pub reward_type: u32,
    pub new_accrued: u128,
    pub total_accrued: u128,
    pub updated_index: u128,
}

/// Event emitted when rewards are funded to the contract
#[contracttype]
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct RewardsFundedEvent {
    pub reward_token: Address,
    pub amount: u128,
    pub funder: Address,
}

/// Event emitted when contract is paused
#[contracttype]
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct ContractPausedEvent {
    pub paused_by: Address,
}

/// Event emitted when contract is unpaused
#[contracttype]
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct ContractUnpausedEvent {
    pub unpaused_by: Address,
}
