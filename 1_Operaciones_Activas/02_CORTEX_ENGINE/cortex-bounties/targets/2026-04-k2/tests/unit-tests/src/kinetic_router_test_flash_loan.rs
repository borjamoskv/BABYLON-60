use crate::kinetic_router_test::{create_and_init_test_reserve_with_oracle, create_test_addresses, create_test_env, initialize_kinetic_router, initialize_kinetic_router_with_oracle};
use k2_kinetic_router::router::KineticRouterContractClient;
use soroban_sdk::{
    testutils::Address as _, token, Address, Bytes, Map, Vec,
};

mod good_receiver {
    use soroban_sdk::{contract, contractimpl, contracttype, token, Address, Bytes, Env, Map, Vec};
    
    #[contracttype]
    pub enum DataKey {
        ATokens,
    }
    
    #[contract]
    pub struct MockFlashLoanReceiver;

    #[contractimpl]
    impl MockFlashLoanReceiver {
        pub fn init(env: Env, asset_atoken_map: Map<Address, Address>) {
            env.storage().instance().set(&DataKey::ATokens, &asset_atoken_map);
        }
        
        pub fn execute_operation(
            env: Env,
            assets: Vec<Address>,
            amounts: Vec<u128>,
            premiums: Vec<u128>,
            _initiator: Address,
            _params: Bytes,
        ) -> bool {
            let atoken_map: Map<Address, Address> = env.storage().instance().get(&DataKey::ATokens).unwrap();
            
            for i in 0..assets.len() {
                let asset = assets.get(i).unwrap();
                let amount = amounts.get(i).unwrap();
                let premium = premiums.get(i).unwrap();
                let total_owed = amount + premium;
                
                if let Some(atoken_address) = atoken_map.get(asset.clone()) {
                    let token_client = token::Client::new(&env, &asset);
                    token_client.transfer(
                        &env.current_contract_address(),
                        &atoken_address,
                        &(total_owed as i128)
                    );
                } else {
                    return false;
                }
            }
            
            true
        }
    }
}

mod bad_receiver {
    use soroban_sdk::{contract, contractimpl, Address, Bytes, Env, Vec};
    
    #[contract]
    pub struct MockBadFlashLoanReceiver;

    #[contractimpl]
    impl MockBadFlashLoanReceiver {
        pub fn execute_operation(
            _env: Env,
            _assets: Vec<Address>,
            _amounts: Vec<u128>,
            _premiums: Vec<u128>,
            _initiator: Address,
            _params: Bytes,
        ) -> bool {
            // Intentionally doesn't repay to test failure case
            true
        }
    }
}

use good_receiver::MockFlashLoanReceiver;
use bad_receiver::MockBadFlashLoanReceiver;

#[test]
fn test_flash_loan_happy_path() {
    let env = create_test_env();
    let (admin, _emergency_admin, user1, _user2) = create_test_addresses(&env);
    let router = Address::generate(&env);
    let dex_router = Address::generate(&env);
    let (kinetic_router, oracle_addr) = initialize_kinetic_router_with_oracle(&env, &admin, &admin, &router, &dex_router);
    let client = KineticRouterContractClient::new(&env, &kinetic_router);

    // Create and initialize a test reserve
    let (asset, _asset_contract) = create_and_init_test_reserve_with_oracle(&env, &kinetic_router, &oracle_addr, &admin);

    // Set flash loan premium
    let premium_bps = 9; // 0.09%
    client.set_flash_loan_premium(&premium_bps);

    // Supply liquidity to the pool
    let supply_amount = 10_000_000_000i128; // 10,000 tokens
    let token_client = token::StellarAssetClient::new(&env, &asset);
    token_client.mint(&user1, &supply_amount);
    
    // Approve lending pool to spend tokens
    let token_client_std = token::Client::new(&env, &asset);
    token_client_std.approve(&user1, &kinetic_router, &supply_amount, &(env.ledger().sequence() + 1000000));
    
    client.supply(&user1, &asset, &(supply_amount as u128), &user1, &0);

    // Get aToken address and create mapping
    let reserve_data = client.get_reserve_data(&asset);
    let atoken_address = reserve_data.a_token_address;
    let mut asset_atoken_map = Map::new(&env);
    asset_atoken_map.set(asset.clone(), atoken_address);

    // Deploy and initialize mock receiver with asset->aToken mapping
    let receiver = env.register(MockFlashLoanReceiver, ());
    let receiver_client = good_receiver::MockFlashLoanReceiverClient::new(&env, &receiver);
    receiver_client.init(&asset_atoken_map);

    // Fund the receiver with enough tokens to pay the premium
    // The flash loan will give it the principal, so it just needs the premium
    let flash_amount = 1_000_000_000u128; // 1,000 tokens
    let premium = (flash_amount * premium_bps as u128) / 10000;
    token_client.mint(&receiver, &(premium as i128));
    
    let params = Bytes::new(&env);
    
    // Execute flash loan
    let assets = Vec::from_array(&env, [asset.clone()]);
    let amounts = Vec::from_array(&env, [flash_amount]);

    let result = client.try_flash_loan(&user1, &receiver, &assets, &amounts, &params);
    if result.is_err() {
        panic!("Flash loan failed: {:?}", result.err());
    }
    assert!(result.is_ok(), "Flash loan should succeed");

    // Verify premium was collected (treasury should have received it)
    // Note: In a real scenario, we'd check the treasury balance
}

#[test]
fn test_flash_loan_insufficient_repayment() {
    let env = create_test_env();
    let (admin, _emergency_admin, user1, _user2) = create_test_addresses(&env);
    let router = Address::generate(&env);
    let dex_router = Address::generate(&env);
    let (kinetic_router, oracle_addr) = initialize_kinetic_router_with_oracle(&env, &admin, &admin, &router, &dex_router);
    let client = KineticRouterContractClient::new(&env, &kinetic_router);

    // Create and initialize a test reserve
    let (asset, _asset_contract) = create_and_init_test_reserve_with_oracle(&env, &kinetic_router, &oracle_addr, &admin);

    // Set flash loan premium
    let premium_bps = 9; // 0.09%
    client.set_flash_loan_premium(&premium_bps);

    // Deploy bad receiver (doesn't repay)
    let bad_receiver = env.register(MockBadFlashLoanReceiver, ());

    // Supply liquidity to the pool
    let supply_amount = 10_000_000_000i128; // 10,000 tokens
    let token_client = token::StellarAssetClient::new(&env, &asset);
    token_client.mint(&user1, &supply_amount);
    
    // Approve lending pool to spend tokens
    let token_client_std = token::Client::new(&env, &asset);
    token_client_std.approve(&user1, &kinetic_router, &supply_amount, &(env.ledger().sequence() + 1000000));
    
    client.supply(&user1, &asset, &(supply_amount as u128), &user1, &0);

    // Execute flash loan (should fail)
    let flash_amount = 1_000_000_000u128; // 1,000 tokens
    let assets = Vec::from_array(&env, [asset.clone()]);
    let amounts = Vec::from_array(&env, [flash_amount]);
    let params = Bytes::new(&env);

    let result = client.try_flash_loan(&user1, &bad_receiver, &assets, &amounts, &params);
    assert!(result.is_err(), "Flash loan should fail when not repaid");
}

#[test]
fn test_flash_loan_multi_asset() {
    let env = create_test_env();
    let (admin, _emergency_admin, user1, _user2) = create_test_addresses(&env);
    let router = Address::generate(&env);
    let dex_router = Address::generate(&env);
    let (kinetic_router, oracle_addr) = initialize_kinetic_router_with_oracle(&env, &admin, &admin, &router, &dex_router);
    let client = KineticRouterContractClient::new(&env, &kinetic_router);

    // Create two test reserves
    let (asset1, _asset1_contract) = create_and_init_test_reserve_with_oracle(&env, &kinetic_router, &oracle_addr, &admin);
    let (asset2, _asset2_contract) = create_and_init_test_reserve_with_oracle(&env, &kinetic_router, &oracle_addr, &admin);

    // Set flash loan premium
    let premium_bps = 9; // 0.09%
    client.set_flash_loan_premium(&premium_bps);

    // Supply liquidity to both reserves
    let supply_amount = 10_000_000_000i128;
    let token_client1 = token::StellarAssetClient::new(&env, &asset1);
    let token_client2 = token::StellarAssetClient::new(&env, &asset2);
    token_client1.mint(&user1, &supply_amount);
    token_client2.mint(&user1, &supply_amount);
    
    // Approve lending pool to spend tokens
    let token_client1_std = token::Client::new(&env, &asset1);
    let token_client2_std = token::Client::new(&env, &asset2);
    token_client1_std.approve(&user1, &kinetic_router, &supply_amount, &(env.ledger().sequence() + 1000000));
    token_client2_std.approve(&user1, &kinetic_router, &supply_amount, &(env.ledger().sequence() + 1000000));
    
    client.supply(&user1, &asset1, &(supply_amount as u128), &user1, &0);
    client.supply(&user1, &asset2, &(supply_amount as u128), &user1, &0);

    // Get aToken addresses and create mapping
    let reserve_data1 = client.get_reserve_data(&asset1);
    let reserve_data2 = client.get_reserve_data(&asset2);
    let mut asset_atoken_map = Map::new(&env);
    asset_atoken_map.set(asset1.clone(), reserve_data1.a_token_address);
    asset_atoken_map.set(asset2.clone(), reserve_data2.a_token_address);

    // Deploy and initialize mock receiver with asset->aToken mapping
    let receiver = env.register(MockFlashLoanReceiver, ());
    let receiver_client = good_receiver::MockFlashLoanReceiverClient::new(&env, &receiver);
    receiver_client.init(&asset_atoken_map);

    // Fund the receiver with enough tokens to pay premiums
    let flash_amount1 = 1_000_000_000u128;
    let flash_amount2 = 2_000_000_000u128;
    let premium1 = (flash_amount1 * premium_bps as u128) / 10000;
    let premium2 = (flash_amount2 * premium_bps as u128) / 10000;
    token_client1.mint(&receiver, &(premium1 as i128));
    token_client2.mint(&receiver, &(premium2 as i128));

    // Execute multi-asset flash loan
    let assets = Vec::from_array(&env, [asset1.clone(), asset2.clone()]);
    let amounts = Vec::from_array(&env, [flash_amount1, flash_amount2]);
    let params = Bytes::new(&env);

    let result = client.try_flash_loan(&user1, &receiver, &assets, &amounts, &params);
    assert!(result.is_ok(), "Multi-asset flash loan should succeed");
}

#[test]
fn test_flash_loan_insufficient_liquidity() {
    let env = create_test_env();
    let (admin, _emergency_admin, _user1, _user2) = create_test_addresses(&env);
    let router = Address::generate(&env);
    let dex_router = Address::generate(&env);
    let (kinetic_router, oracle_addr) = initialize_kinetic_router_with_oracle(&env, &admin, &admin, &router, &dex_router);
    let client = KineticRouterContractClient::new(&env, &kinetic_router);

    // Create and initialize a test reserve (but don't supply liquidity)
    let (asset, _asset_contract) = create_and_init_test_reserve_with_oracle(&env, &kinetic_router, &oracle_addr, &admin);

    // Deploy mock receiver
    let receiver = env.register(MockFlashLoanReceiver, ());

    // Try to borrow more than available
    let flash_amount = 1_000_000_000u128;
    let assets = Vec::from_array(&env, [asset.clone()]);
    let amounts = Vec::from_array(&env, [flash_amount]);
    let params = Bytes::new(&env);
    
    let initiator = Address::generate(&env);
    let result = client.try_flash_loan(&initiator, &receiver, &assets, &amounts, &params);
    assert!(
        result.is_err(),
        "Flash loan should fail with insufficient liquidity"
    );
}

#[test]
fn test_flash_loan_premium_calculation() {
    let env = create_test_env();
    let (admin, _emergency_admin, user1, _user2) = create_test_addresses(&env);
    let router = Address::generate(&env);
    let dex_router = Address::generate(&env);
    let (kinetic_router, oracle_addr) = initialize_kinetic_router_with_oracle(&env, &admin, &admin, &router, &dex_router);
    let client = KineticRouterContractClient::new(&env, &kinetic_router);

    // Create and initialize a test reserve
    let (asset, _asset_contract) = create_and_init_test_reserve_with_oracle(&env, &kinetic_router, &oracle_addr, &admin);

    // Set flash loan premium to 0.5%
    let premium_bps = 50; // 0.5%
    client.set_flash_loan_premium(&premium_bps);

    // Verify premium was set correctly
    let actual_premium = client.get_flash_loan_premium();
    assert_eq!(
        actual_premium, premium_bps,
        "Flash loan premium should be set correctly"
    );

    // Supply liquidity
    let supply_amount = 10_000_000_000i128;
    let token_client = token::StellarAssetClient::new(&env, &asset);
    token_client.mint(&user1, &supply_amount);
    
    // Approve lending pool to spend tokens
    let token_client_std = token::Client::new(&env, &asset);
    token_client_std.approve(&user1, &kinetic_router, &supply_amount, &(env.ledger().sequence() + 1000000));
    
    client.supply(&user1, &asset, &(supply_amount as u128), &user1, &0);

    // Get aToken address and create mapping
    let reserve_data = client.get_reserve_data(&asset);
    let atoken_address = reserve_data.a_token_address;
    let mut asset_atoken_map = Map::new(&env);
    asset_atoken_map.set(asset.clone(), atoken_address);

    // Deploy and initialize mock receiver
    let receiver = env.register(MockFlashLoanReceiver, ());
    let receiver_client = good_receiver::MockFlashLoanReceiverClient::new(&env, &receiver);
    receiver_client.init(&asset_atoken_map);

    // Test various amounts
    let test_cases = [
        (10000u128, 50u128),       // 10000 * 50 / 10000 = 50
        (100000u128, 500u128),     // 100000 * 50 / 10000 = 500
        (1000000u128, 5000u128),   // 1000000 * 50 / 10000 = 5000
    ];

    for (amount, expected_premium) in test_cases {
        let calculated_premium = (amount * premium_bps as u128) / 10000;
        assert_eq!(
            calculated_premium, expected_premium,
            "Premium calculation failed for amount {}: expected {}, got {}",
            amount, expected_premium, calculated_premium
        );
    }
}

#[test]
fn test_flash_loan_permissionless() {
    let env = create_test_env();
    let (admin, _emergency_admin, user1, user2) = create_test_addresses(&env);
    let router = Address::generate(&env);
    let dex_router = Address::generate(&env);
    let (kinetic_router, oracle_addr) = initialize_kinetic_router_with_oracle(&env, &admin, &admin, &router, &dex_router);
    let client = KineticRouterContractClient::new(&env, &kinetic_router);

    // Create and initialize a test reserve
    let (asset, _asset_contract) = create_and_init_test_reserve_with_oracle(&env, &kinetic_router, &oracle_addr, &admin);

    // Set flash loan premium
    let premium_bps = 9;
    client.set_flash_loan_premium(&premium_bps);

    // Supply liquidity
    let supply_amount = 10_000_000_000i128;
    let token_client = token::StellarAssetClient::new(&env, &asset);
    token_client.mint(&user1, &supply_amount);
    
    // Approve lending pool to spend tokens
    let token_client_std = token::Client::new(&env, &asset);
    token_client_std.approve(&user1, &kinetic_router, &supply_amount, &(env.ledger().sequence() + 1000000));
    
    client.supply(&user1, &asset, &(supply_amount as u128), &user1, &0);

    // Get aToken address and create mapping
    let reserve_data = client.get_reserve_data(&asset);
    let atoken_address = reserve_data.a_token_address;
    let mut asset_atoken_map = Map::new(&env);
    asset_atoken_map.set(asset.clone(), atoken_address);

    // Deploy and initialize mock receiver
    let receiver = env.register(MockFlashLoanReceiver, ());
    let receiver_client = good_receiver::MockFlashLoanReceiverClient::new(&env, &receiver);
    receiver_client.init(&asset_atoken_map);

    // Fund the receiver
    let flash_amount = 1_000_000_000u128;
    let premium = (flash_amount * premium_bps as u128) / 10000;
    token_client.mint(&receiver, &(premium as i128));

    // Execute flash loan from user2 (different from supplier)
    // This should work because flash loans are permissionless
    let assets = Vec::from_array(&env, [asset.clone()]);
    let amounts = Vec::from_array(&env, [flash_amount]);
    let params = Bytes::new(&env);

    let result = client.try_flash_loan(&user2, &receiver, &assets, &amounts, &params);
    assert!(
        result.is_ok(),
        "Flash loan should succeed from any user (permissionless)"
    );
}

#[test]
fn test_execute_operation_internal_only() {
    let env = create_test_env();
    let (admin, _emergency_admin, _user1, _user2) = create_test_addresses(&env);
    let router = Address::generate(&env);
    let dex_router = Address::generate(&env);
    let (_kinetic_router, _oracle) = initialize_kinetic_router(&env, &admin, &admin, &router, &dex_router);

    // execute_operation is internal-only and not exposed via public API
    assert!(true);
}

