use soroban_sdk::{contracttype, Address};

#[contracttype]
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct SupplyEvent {
    pub reserve: Address,
    pub user: Address,
    pub on_behalf_of: Address,
    pub amount: u128,
    pub referral_code: u32,
}

#[contracttype]
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct WithdrawEvent {
    pub reserve: Address,
    pub user: Address,
    pub to: Address,
    pub amount: u128,
}

#[contracttype]
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct BorrowEvent {
    pub reserve: Address,
    pub user: Address,
    pub on_behalf_of: Address,
    pub amount: u128,
    pub borrow_rate_mode: u32,
    pub borrow_rate: u128,
    pub referral_code: u32,
}

#[contracttype]
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct RepayEvent {
    pub reserve: Address,
    pub user: Address,
    pub repayer: Address,
    pub amount: u128,
    pub use_a_tokens: bool,
}

#[contracttype]
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct LiquidationCallEvent {
    pub collateral_asset: Address,
    pub debt_asset: Address,
    pub user: Address,
    pub debt_to_cover: u128,
    pub liquidated_collateral_amount: u128,
    pub liquidator: Address,
    pub receive_a_token: bool,
    pub protocol_fee: u128,
    pub liquidator_collateral: u128,
}

#[contracttype]
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct LiquidationFeeTransferFailedEvent {
    pub collateral_asset: Address,
    pub debt_asset: Address,
    pub user: Address,
    pub protocol_fee_amount: u128,
    pub treasury: Address,
}

#[contracttype]
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct FlashLoanEvent {
    pub target: Address,
    pub initiator: Address,
    pub asset: Address,
    pub amount: u128,
    pub premium: u128,
    pub referral_code: u32,
}

#[contracttype]
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct ReserveUsedAsCollateralEvent {
    pub reserve: Address,
    pub user: Address,
    pub enabled: bool,
}

#[contracttype]
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct ReserveDataUpdatedEvent {
    pub reserve: Address,
    pub liquidity_rate: u128,
    pub stable_borrow_rate: u128,
    pub variable_borrow_rate: u128,
    pub liquidity_index: u128,
    pub variable_borrow_index: u128,
}

#[contracttype]
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct AMMRouterUpdated {
    pub router: Address,
    pub added: bool,
}

#[contracttype]
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct AdminProposedEvent {
    pub current_admin: Address,
    pub pending_admin: Address,
}

#[contracttype]
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct AdminAcceptedEvent {
    pub previous_admin: Address,
    pub new_admin: Address,
}

#[contracttype]
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct AdminProposalCancelledEvent {
    pub admin: Address,
    pub cancelled_pending_admin: Address,
}
