use crate::common::setup::TestEnv;

#[derive(Debug, Clone)]
pub struct ProtocolSnapshot {
    pub total_supply: Vec<i128>,
    pub total_debt: Vec<i128>,
    pub user_collateral: Vec<Vec<i128>>,
    pub user_debt: Vec<Vec<i128>>,
    pub user_underlying: Vec<Vec<i128>>,
    pub treasury_balances: Vec<i128>,
    pub timestamp: u64,
    pub liquidity_indices: Vec<u128>,
    pub borrow_indices: Vec<u128>,
    pub available_liquidity: Vec<i128>,
    pub protocol_reserves: Vec<i128>,
    pub prices: Vec<u128>,
    pub health_factors: Vec<u128>,
}

impl ProtocolSnapshot {
    pub fn capture(test_env: &TestEnv) -> Self {
        let mut total_supply = Vec::new();
        let mut total_debt = Vec::new();
        let mut treasury_balances = Vec::new();
        let mut liquidity_indices = Vec::new();
        let mut borrow_indices = Vec::new();
        let mut available_liquidity = Vec::new();
        let mut protocol_reserves = Vec::new();
        let mut prices = Vec::new();
        
        for asset in &test_env.assets {
            let supply = asset.a_token.total_supply();
            let debt = asset.debt_token.total_supply();
            let underlying_balance = asset.token.balance(&asset.a_token.address);
            
            total_supply.push(supply);
            total_debt.push(debt);
            treasury_balances.push(asset.token.balance(&test_env.treasury));
            available_liquidity.push(underlying_balance);
            prices.push(asset.current_price);
            
            let expected_balance = supply - debt;
            let reserves = underlying_balance - expected_balance;
            protocol_reserves.push(reserves);
            
            if let Ok(Ok(reserve_data)) = test_env.router.try_get_reserve_data(&asset.address) {
                liquidity_indices.push(reserve_data.liquidity_index);
                borrow_indices.push(reserve_data.variable_borrow_index);
            } else {
                liquidity_indices.push(crate::common::constants::RAY);
                borrow_indices.push(crate::common::constants::RAY);
            }
        }
        
        let mut user_collateral = Vec::new();
        let mut user_debt = Vec::new();
        let mut user_underlying = Vec::new();
        let mut health_factors = Vec::new();
        
        for user in &test_env.users {
            let mut collateral = Vec::new();
            let mut debt = Vec::new();
            let mut underlying = Vec::new();
            
            for asset in &test_env.assets {
                collateral.push(asset.a_token.balance(user));
                debt.push(asset.debt_token.balance(user));
                underlying.push(asset.token.balance(user));
            }
            
            user_collateral.push(collateral);
            user_debt.push(debt);
            user_underlying.push(underlying);
            
            // Capture health factor for each user
            let hf = if let Ok(Ok(account_data)) = test_env.router.try_get_user_account_data(user) {
                account_data.health_factor
            } else {
                u128::MAX  // No debt or query failed = infinite health factor
            };
            health_factors.push(hf);
        }
        
        ProtocolSnapshot {
            total_supply,
            total_debt,
            user_collateral,
            user_debt,
            user_underlying,
            treasury_balances,
            timestamp: test_env.env.ledger().timestamp(),
            liquidity_indices,
            borrow_indices,
            available_liquidity,
            protocol_reserves,
            prices,
            health_factors,
        }
    }
}
