use soroban_sdk::{Env, Address, String, testutils::Address as _, testutils::Ledger, token::StellarAssetClient};
use k2_kinetic_router::{KineticRouterContract, KineticRouterContractClient};
use k2_a_token::{ATokenContract, ATokenContractClient};
use k2_debt_token::{DebtTokenContract, DebtTokenContractClient};
use k2_interest_rate_strategy::{InterestRateStrategyContract, InterestRateStrategyContractClient};
use k2_price_oracle::{PriceOracleContract, PriceOracleContractClient};
use k2_shared::{Asset, InitReserveParams};

use crate::common::constants::*;
use crate::common::mocks::{MockReflector, MockFlashLoanReceiver, ReentrantFlashLoanReceiver, ReentrantRepayLiquidationReceiver, NonRepayingFlashLoanReceiver, StateManipulatingReceiver, OracleManipulatingReceiver};
use crate::common::operations::{AssetConfig, FlashLoanReceiverType, Input};

pub struct AssetData<'a> {
    pub address: Address,
    pub token: StellarAssetClient<'a>,
    pub a_token: ATokenContractClient<'a>,
    pub debt_token: DebtTokenContractClient<'a>,
    #[allow(dead_code)]
    pub strategy: Address,
    #[allow(dead_code)]
    pub config: AssetConfig,
    pub current_price: u128,
}

pub struct TestEnv<'a> {
    pub env: &'a Env,
    pub router: KineticRouterContractClient<'a>,
    pub router_address: Address,
    pub oracle: PriceOracleContractClient<'a>,
    pub assets: Vec<AssetData<'a>>,
    pub users: Vec<Address>,
    pub admin: Address,
    pub treasury: Address,
    #[allow(dead_code)]
    pub pool_configurator: Address,
    pub flash_loan_receiver_standard: Address,
    pub flash_loan_receiver_reentrant: Address,
    pub flash_loan_receiver_reentrant_repay_liq: Address,
    pub flash_loan_receiver_non_repaying: Address,
    pub flash_loan_receiver_state_manipulating: Address,
    pub flash_loan_receiver_oracle_manipulating: Address,
    pub initial_total_underlying: Vec<u128>,
    pub cumulative_rounding_error: Vec<i128>,
    pub operation_count: u64,
}

impl<'a> TestEnv<'a> {
    pub fn new(env: &'a Env, input: &Input) -> Option<Self> {
        env.mock_all_auths();
        env.cost_estimate().budget().reset_unlimited();
        
        let admin = Address::generate(env);
        let treasury = Address::generate(env);
        let dex_router = Address::generate(env);
        let base_currency = Address::generate(env);
        
        // 8 users for more complex multi-user interaction scenarios
        let users: Vec<Address> = (0..8).map(|_| Address::generate(env)).collect();
        
        // Deploy mocks
        let reflector_id = env.register(MockReflector, ());
        let flash_loan_receiver_standard = env.register(MockFlashLoanReceiver, ());
        let flash_loan_receiver_reentrant = env.register(ReentrantFlashLoanReceiver, ());
        let flash_loan_receiver_reentrant_repay_liq = env.register(ReentrantRepayLiquidationReceiver, ());
        let flash_loan_receiver_non_repaying = env.register(NonRepayingFlashLoanReceiver, ());
        let flash_loan_receiver_state_manipulating = env.register(StateManipulatingReceiver, ());
        let flash_loan_receiver_oracle_manipulating = env.register(OracleManipulatingReceiver, ());
        
        // Deploy oracle
        let oracle_id = env.register(PriceOracleContract, ());
        let oracle = PriceOracleContractClient::new(env, &oracle_id);
        if oracle.try_initialize(&admin, &reflector_id, &base_currency, &base_currency).is_err() {
            return None;
        }
        
        // Deploy router
        let router_id = env.register(KineticRouterContract, ());
        let router = KineticRouterContractClient::new(env, &router_id);
        
        if router.try_initialize(&admin, &admin, &oracle_id, &treasury, &dex_router, &None).is_err() {
            return None;
        }
        
        let pool_configurator = Address::generate(env);
        if router.try_set_pool_configurator(&pool_configurator).is_err() {
            return None;
        }
        
        let mut assets = Vec::new();
        let mut initial_total_underlying = Vec::new();
        let mut cumulative_rounding_error = Vec::new();
        
        for (i, config) in input.asset_configs.iter().enumerate() {
            let asset = deploy_asset(
                env, &admin, &pool_configurator, &treasury, &router_id,
                &router, &oracle, config, input.initial_prices[i], &users,
            )?;
            
            let total: u128 = users.iter().map(|u| asset.token.balance(u) as u128).sum();
            initial_total_underlying.push(total);
            cumulative_rounding_error.push(0i128);
            assets.push(asset);
        }
        
        Some(TestEnv {
            env, router, router_address: router_id, oracle, assets, users, admin, treasury,
            pool_configurator, flash_loan_receiver_standard, flash_loan_receiver_reentrant,
            flash_loan_receiver_reentrant_repay_liq, flash_loan_receiver_non_repaying, 
            flash_loan_receiver_state_manipulating, flash_loan_receiver_oracle_manipulating,
            initial_total_underlying, cumulative_rounding_error, operation_count: 0,
        })
    }
    
    pub fn get_user(&self, idx: u8) -> &Address {
        &self.users[(idx as usize) % self.users.len()]
    }
    
    pub fn get_asset(&self, idx: u8) -> &AssetData<'a> {
        &self.assets[(idx as usize) % self.assets.len()]
    }
    
    pub fn advance_time(&self, seconds: u32) {
        let current = self.env.ledger().timestamp();
        self.env.ledger().with_mut(|li| {
            li.timestamp = current.saturating_add(seconds as u64);
        });
    }
    
    pub fn set_price(&mut self, asset_idx: u8, new_price: u128) {
        let idx = (asset_idx as usize) % self.assets.len();
        let asset = &self.assets[idx];
        let asset_enum = Asset::Stellar(asset.address.clone());
        let expiry = self.env.ledger().timestamp() + 604_000;
        let _ = self.oracle.try_set_manual_override(&self.admin, &asset_enum, &Some(new_price), &Some(expiry));
        self.assets[idx].current_price = new_price;
    }
    
    pub fn set_price_stale(&mut self, asset_idx: u8) {
        let idx = (asset_idx as usize) % self.assets.len();
        let asset = &self.assets[idx];
        let asset_enum = Asset::Stellar(asset.address.clone());
        let expiry = self.env.ledger().timestamp().saturating_sub(1);
        let _ = self.oracle.try_set_manual_override(&self.admin, &asset_enum, &Some(asset.current_price), &Some(expiry));
    }
    
    pub fn get_price(&self, asset_idx: u8) -> u128 {
        self.assets[(asset_idx as usize) % self.assets.len()].current_price
    }
    
    pub fn get_flash_loan_receiver(&self, receiver_type: FlashLoanReceiverType) -> &Address {
        match receiver_type {
            FlashLoanReceiverType::Standard => &self.flash_loan_receiver_standard,
            FlashLoanReceiverType::Reentrant => &self.flash_loan_receiver_reentrant,
            FlashLoanReceiverType::ReentrantRepayLiquidation => &self.flash_loan_receiver_reentrant_repay_liq,
            FlashLoanReceiverType::NonRepaying => &self.flash_loan_receiver_non_repaying,
            FlashLoanReceiverType::StateManipulating => &self.flash_loan_receiver_state_manipulating,
            FlashLoanReceiverType::OracleManipulating => &self.flash_loan_receiver_oracle_manipulating,
        }
    }
    
    /// Get the router address for passing to flash loan receivers.
    pub fn get_router_address(&self) -> &Address {
        &self.router_address
    }
    
    /// Get router address serialized as bytes for flash loan params
    pub fn get_router_contract_id_bytes(&self) -> soroban_sdk::Bytes {
        // For adversarial receivers, we pass the router address via XDR serialization
        use soroban_sdk::xdr::ToXdr;
        (&self.router_address).to_xdr(self.env)
    }
    
    /// Check if protocol is currently paused
    pub fn is_paused(&self) -> bool {
        self.router.is_paused()
    }
    
    pub fn track_rounding_error(&mut self, asset_idx: usize, error: i128) {
        if asset_idx < self.cumulative_rounding_error.len() {
            self.cumulative_rounding_error[asset_idx] = 
                self.cumulative_rounding_error[asset_idx].saturating_add(error.abs());
        }
    }
    
    pub fn increment_operation_count(&mut self) {
        self.operation_count += 1;
    }
}

fn deploy_asset<'a>(
    env: &'a Env,
    admin: &Address,
    pool_configurator: &Address,
    treasury: &Address,
    router_id: &Address,
    router: &KineticRouterContractClient<'a>,
    oracle: &PriceOracleContractClient<'a>,
    config: &AssetConfig,
    initial_price: u128,
    users: &[Address],
) -> Option<AssetData<'a>> {
    let token_contract = env.register_stellar_asset_contract_v2(admin.clone());
    let token_id = token_contract.address();
    let token = StellarAssetClient::new(env, &token_id);
    
    for user in users {
        token.mint(user, &INITIAL_BALANCE);
    }
    
    let asset_enum = Asset::Stellar(token_id.clone());
    if oracle.try_add_asset(admin, &asset_enum).is_err() { return None; }
    
    let expiry = env.ledger().timestamp() + 604_000;
    if oracle.try_set_manual_override(admin, &asset_enum, &Some(initial_price), &Some(expiry)).is_err() {
        return None;
    }
    
    let a_token_id = env.register(ATokenContract, ());
    let a_token = ATokenContractClient::new(env, &a_token_id);
    if a_token.try_initialize(admin, &token_id, router_id, &String::from_str(env, "aToken"), &String::from_str(env, "aTKN"), &DECIMALS).is_err() {
        return None;
    }
    
    let debt_token_id = env.register(DebtTokenContract, ());
    let debt_token = DebtTokenContractClient::new(env, &debt_token_id);
    if debt_token.try_initialize(admin, &token_id, router_id, &String::from_str(env, "dToken"), &String::from_str(env, "dTKN"), &DECIMALS).is_err() {
        return None;
    }
    
    let strategy_id = env.register(InterestRateStrategyContract, ());
    let strategy = InterestRateStrategyContractClient::new(env, &strategy_id);
    // Parameter order: admin, base_rate, slope1, slope2, optimal_utilization
    if strategy.try_initialize(admin, &config.base_rate, &config.slope1, &config.slope2, &config.optimal_utilization).is_err() {
        return None;
    }
    
    let params = InitReserveParams {
        decimals: DECIMALS,
        ltv: config.ltv,
        liquidation_threshold: config.liquidation_threshold,
        liquidation_bonus: config.liquidation_bonus,
        reserve_factor: config.reserve_factor,
        supply_cap: config.supply_cap,
        borrow_cap: config.borrow_cap,
        borrowing_enabled: true,
        flashloan_enabled: config.flashloan_enabled,
    };
    
    if router.try_init_reserve(pool_configurator, &token_id, &a_token_id, &debt_token_id, &strategy_id, treasury, &params).is_err() {
        return None;
    }
    
    Some(AssetData {
        address: token_id, token, a_token, debt_token, strategy: strategy_id,
        config: config.clone(), current_price: initial_price,
    })
}
