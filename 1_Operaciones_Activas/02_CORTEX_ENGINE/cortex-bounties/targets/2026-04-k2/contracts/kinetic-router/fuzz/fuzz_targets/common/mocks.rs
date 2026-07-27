use soroban_sdk::{contract, contractimpl, Env, Address, Bytes, xdr::FromXdr};
use k2_kinetic_router::KineticRouterContractClient;

#[contract]
pub struct MockReflector;

#[contractimpl]
impl MockReflector {
    pub fn decimals(_env: Env) -> u32 {
        14
    }
}

fn extract_router_address(env: &Env, params: &Bytes) -> Option<Address> {
    if params.is_empty() {
        return None;
    }
    Address::from_xdr(env, params).ok()
}

#[contract]
pub struct MockFlashLoanReceiver;

#[contractimpl]
impl MockFlashLoanReceiver {
    pub fn execute_operation(
        _env: Env,
        _assets: soroban_sdk::Vec<Address>,
        _amounts: soroban_sdk::Vec<u128>,
        _premiums: soroban_sdk::Vec<u128>,
        _initiator: Address,
        _params: Bytes,
    ) -> bool {
        true
    }
}

#[contract]
pub struct ReentrantFlashLoanReceiver;

#[contractimpl]
impl ReentrantFlashLoanReceiver {
    pub fn execute_operation(
        env: Env,
        assets: soroban_sdk::Vec<Address>,
        amounts: soroban_sdk::Vec<u128>,
        _premiums: soroban_sdk::Vec<u128>,
        initiator: Address,
        params: Bytes,
    ) -> bool {
        if let Some(router_addr) = extract_router_address(&env, &params) {
            let router = KineticRouterContractClient::new(&env, &router_addr);
            
            if let Some(asset) = assets.first() {
                if let Some(amount) = amounts.first() {
                    let borrow_result = router.try_borrow(&initiator, &asset, &(amount / 2), &1u32, &0u32, &initiator);
                    if borrow_result.is_ok() {
                        panic!("CRITICAL: Reentrancy via borrow during flash loan callback succeeded!");
                    }
                    
                    let mut nested_assets = soroban_sdk::Vec::new(&env);
                    nested_assets.push_back(asset.clone());
                    let mut nested_amounts = soroban_sdk::Vec::new(&env);
                    nested_amounts.push_back(amount / 4);
                    let nested_params = Bytes::new(&env);
                    
                    let flash_result = router.try_flash_loan(
                        &initiator,
                        &env.current_contract_address(),
                        &nested_assets,
                        &nested_amounts,
                        &nested_params,
                    );
                    if flash_result.is_ok() {
                        panic!("CRITICAL: Nested flash loan reentrancy succeeded!");
                    }
                    
                    let _withdraw_result = router.try_withdraw(&initiator, &asset, &(amount / 4), &initiator);
                }
            }
        }
        true
    }
}

#[contract]
pub struct ReentrantRepayLiquidationReceiver;

#[contractimpl]
impl ReentrantRepayLiquidationReceiver {
    pub fn execute_operation(
        env: Env,
        assets: soroban_sdk::Vec<Address>,
        amounts: soroban_sdk::Vec<u128>,
        premiums: soroban_sdk::Vec<u128>,
        initiator: Address,
        params: Bytes,
    ) -> bool {
        if let Some(router_addr) = extract_router_address(&env, &params) {
            let router = KineticRouterContractClient::new(&env, &router_addr);
            
            if let (Some(asset), Some(amount), Some(premium)) = (assets.first(), amounts.first(), premiums.first()) {
                let _repay_result = router.try_repay(&initiator, &asset, &(amount / 2), &1u32, &initiator);
                
                let potential_victim = soroban_sdk::Address::from_string(
                    &soroban_sdk::String::from_str(&env, "GAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAWHF")
                );
                
                let _liquidation_result = router.try_liquidation_call(
                    &initiator, &asset, &asset, &potential_victim, &(amount / 4), &false,
                );
                
                let self_liq_result = router.try_liquidation_call(
                    &initiator, &asset, &asset, &initiator, &(amount / 4), &false,
                );
                if self_liq_result.is_ok() {
                    panic!("CRITICAL: Self-liquidation during flash loan callback succeeded!");
                }
                
                let _prepare_result = router.try_prepare_liquidation(
                    &initiator, &potential_victim, &asset, &asset, &(amount / 4), &0u128, &None,
                );
                
                let deadline = env.ledger().timestamp() + 300;
                let _execute_result = router.try_execute_liquidation(
                    &initiator, &potential_victim, &asset, &asset, &deadline,
                );
                
                use soroban_sdk::token::TokenClient;
                let token = TokenClient::new(&env, &asset);
                let repay_amount = amount + premium;
                token.approve(&env.current_contract_address(), &router_addr, &(repay_amount as i128), &(env.ledger().sequence() + 100));
            }
        }
        true
    }
}

#[contract]
pub struct NonRepayingFlashLoanReceiver;

#[contractimpl]
impl NonRepayingFlashLoanReceiver {
    pub fn execute_operation(
        env: Env,
        assets: soroban_sdk::Vec<Address>,
        amounts: soroban_sdk::Vec<u128>,
        _premiums: soroban_sdk::Vec<u128>,
        initiator: Address,
        _params: Bytes,
    ) -> bool {
        if let (Some(asset), Some(_amount)) = (assets.first(), amounts.first()) {
            use soroban_sdk::token::TokenClient;
            let token = TokenClient::new(&env, &asset);
            let balance = token.balance(&env.current_contract_address());
            if balance > 0 {
                let _transfer_result = token.try_transfer(&env.current_contract_address(), &initiator, &balance);
            }
        }
        true
    }
}

#[contract]
pub struct StateManipulatingReceiver;

#[contractimpl]
impl StateManipulatingReceiver {
    pub fn execute_operation(
        env: Env,
        assets: soroban_sdk::Vec<Address>,
        amounts: soroban_sdk::Vec<u128>,
        premiums: soroban_sdk::Vec<u128>,
        initiator: Address,
        params: Bytes,
    ) -> bool {
        if let Some(router_addr) = extract_router_address(&env, &params) {
            let router = KineticRouterContractClient::new(&env, &router_addr);
            
            if let (Some(asset), Some(amount), Some(premium)) = (assets.first(), amounts.first(), premiums.first()) {
                let _user_data_before = router.try_get_user_account_data(&initiator);
                let supply_result = router.try_supply(&initiator, &asset, &amount, &initiator, &0u32);
                
                if supply_result.is_ok() {
                    let _borrow_result = router.try_borrow(&initiator, &asset, &(amount / 2), &1u32, &0u32, &initiator);
                    let _ = router.try_withdraw(&initiator, &asset, &amount, &initiator);
                }
                
                let _collateral_result = router.try_set_user_use_reserve_as_coll(&initiator, &asset, &true);
                
                let pause_result = router.try_pause(&initiator);
                if pause_result.is_ok() {
                    panic!("CRITICAL: Non-admin was able to pause protocol during flash loan!");
                }
                
                use soroban_sdk::token::TokenClient;
                let token = TokenClient::new(&env, &asset);
                let repay_amount = amount + premium;
                token.approve(&env.current_contract_address(), &router_addr, &(repay_amount as i128), &(env.ledger().sequence() + 100));
            }
        }
        true
    }
}

#[contract]
pub struct OracleManipulatingReceiver;

#[contractimpl]
impl OracleManipulatingReceiver {
    pub fn execute_operation(
        env: Env,
        assets: soroban_sdk::Vec<Address>,
        amounts: soroban_sdk::Vec<u128>,
        premiums: soroban_sdk::Vec<u128>,
        initiator: Address,
        params: Bytes,
    ) -> bool {
        if let Some(router_addr) = extract_router_address(&env, &params) {
            let router = KineticRouterContractClient::new(&env, &router_addr);
            
            if let (Some(asset), Some(amount), Some(premium)) = (assets.first(), amounts.first(), premiums.first()) {
                let _health_before = if let Ok(Ok(data)) = router.try_get_user_account_data(&initiator) {
                    data.health_factor
                } else {
                    u128::MAX
                };
                
                let excessive_borrow = router.try_borrow(&initiator, &asset, &(amount * 10), &1u32, &0u32, &initiator);
                if excessive_borrow.is_ok() {
                    if let Ok(Ok(data)) = router.try_get_user_account_data(&initiator) {
                        assert!(data.health_factor >= 1_000_000_000_000_000_000 || data.total_debt_base == 0,
                            "CRITICAL: Excessive borrow during flash loan resulted in unhealthy position! HF: {}",
                            data.health_factor);
                    }
                }
                
                let self_liq = router.try_liquidation_call(&initiator, &asset, &asset, &initiator, &(amount / 2), &false);
                if self_liq.is_ok() {
                    panic!("CRITICAL: Self-liquidation succeeded during flash loan callback!");
                }
                
                let supply_result = router.try_supply(&initiator, &asset, &amount, &initiator, &0u32);
                if supply_result.is_ok() {
                    let withdraw_result = router.try_withdraw(&initiator, &asset, &(amount * 2), &initiator);
                    if withdraw_result.is_ok() {
                        panic!("CRITICAL: Withdrew more than supplied during flash loan!");
                    }
                    let _ = router.try_withdraw(&initiator, &asset, &amount, &initiator);
                }
                
                use soroban_sdk::token::TokenClient;
                let token = TokenClient::new(&env, &asset);
                let repay_amount = amount + premium;
                token.approve(&env.current_contract_address(), &router_addr, &(repay_amount as i128), &(env.ledger().sequence() + 100));
            }
        }
        true
    }
}
