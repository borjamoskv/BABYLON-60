#![cfg(test)]
use super::*;
use soroban_sdk::{testutils::Address as _, Address, Env};

#[test]
fn test_initialize() {
    let env = Env::default();
    let admin = Address::generate(&env);
    let router = Address::generate(&env);
    let factory = Address::generate(&env);
    
    let contract_id = env.register(SoroswapSwapAdapter, (admin.clone(), router.clone(), Some(factory.clone())));
    let client = SoroswapSwapAdapterClient::new(&env, &contract_id);
    
    assert_eq!(client.get_router(), router);
}

#[test]
fn test_initialize_without_factory() {
    let env = Env::default();
    let admin = Address::generate(&env);
    let router = Address::generate(&env);
    
    let contract_id = env.register(SoroswapSwapAdapter, (admin.clone(), router.clone(), Option::<Address>::None));
    let client = SoroswapSwapAdapterClient::new(&env, &contract_id);
    
    assert_eq!(client.get_router(), router);
}

#[test]
#[should_panic(expected = "SOROSWAP_ADAPTER_ALREADY_INITIALIZED_AT_CONSTRUCTOR")]
fn test_initialize_fails() {
    let env = Env::default();
    let admin = Address::generate(&env);
    let router = Address::generate(&env);
    
    let contract_id = env.register(SoroswapSwapAdapter, (admin.clone(), router.clone(), Option::<Address>::None));
    let client = SoroswapSwapAdapterClient::new(&env, &contract_id);
    
    client.initialize(&admin, &router, &None);
}

#[test]
fn test_set_router() {
    let env = Env::default();
    let admin = Address::generate(&env);
    let router = Address::generate(&env);
    let new_router = Address::generate(&env);
    
    let contract_id = env.register(SoroswapSwapAdapter, (admin.clone(), router.clone(), Option::<Address>::None));
    let client = SoroswapSwapAdapterClient::new(&env, &contract_id);
    
    env.mock_all_auths();
    
    client.set_router(&admin, &new_router);
    
    assert_eq!(client.get_router(), new_router);
}
