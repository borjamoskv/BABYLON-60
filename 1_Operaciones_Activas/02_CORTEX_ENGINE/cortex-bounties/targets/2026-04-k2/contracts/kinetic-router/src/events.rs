// Re-export events from shared module for convenience
pub use k2_shared::{
    AdminAcceptedEvent, AdminProposalCancelledEvent, AdminProposedEvent, AMMRouterUpdated,
    BorrowEvent, FlashLoanEvent, LiquidationCallEvent, LiquidationFeeTransferFailedEvent,
    RepayEvent, ReserveDataUpdatedEvent, ReserveUsedAsCollateralEvent, SupplyEvent,
    WithdrawEvent,
};

use soroban_sdk::{contracttype, Address};

// Additional kinetic-router specific events

#[contracttype]
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct ProtocolPausedEvent {
    pub paused_by: Address,
}

#[contracttype]
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct ProtocolUnpausedEvent {
    pub unpaused_by: Address,
}

#[contracttype]
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct ReserveInitializedEvent {
    pub asset: Address,
    pub a_token: Address,
    pub debt_token: Address,
    pub interest_rate_strategy: Address,
}

#[contracttype]
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct ReserveDroppedEvent {
    pub asset: Address,
}

#[contracttype]
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct FlashLoanPremiumUpdatedEvent {
    pub old_premium_bps: u128,
    pub new_premium_bps: u128,
}

#[contracttype]
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct TreasuryUpdatedEvent {
    pub old_treasury: Option<Address>,
    pub new_treasury: Address,
}

#[contracttype]
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct PriceOracleUpdatedEvent {
    pub old_oracle: Option<Address>,
    pub new_oracle: Address,
}
