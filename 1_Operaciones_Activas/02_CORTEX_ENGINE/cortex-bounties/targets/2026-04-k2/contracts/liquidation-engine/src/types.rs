use soroban_sdk::{contracttype, Address};

#[contracttype]
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct LiquidationCall {
    pub liquidator: Address,
    pub user: Address,
    pub collateral_asset: Address,
    pub debt_asset: Address,
    pub debt_to_cover: u128,
    pub collateral_to_liquidate: u128,
    pub liquidation_bonus: u128,
    pub timestamp: u64,
}

#[contracttype]
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct LiquidationCalculation {
    pub collateral_amount: u128,
    pub bonus_amount: u128,
    pub liquidation_bonus_percentage: u128,
    pub health_factor_after: u128,
}
