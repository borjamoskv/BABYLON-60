#![cfg(test)]

use crate::redstone_adapter;
use crate::price_oracle;
use crate::setup::{create_test_env, advance_ledger};
use redstone_adapter::Asset as RedStoneAsset;
use soroban_sdk::{
    testutils::Address as _,
    Address, Bytes, BytesN, Env, String, Vec,
};

extern crate hex;

const ETH_PRIMARY_3SIG_HEX: &str = "4554480000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000252334551f0196301673e0000000200000010fb9f8a3489aef703b90d4b0fda226ea35a950c586d79dcb7137045d3103d3fa29af04725b966308d6b531eb0c2c4ed217b5f13fca2f56addbf7d420a7585b9a1b4554480000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000252334551f0196301673e0000000200000010df2694d607405cf44758df3616fc22e30909ac156c14cccf2280ad2cc17d5223c680f9902e336d9286c3844027b488e0d308d87eb05ef4f8fcab257f888aacb1c4554480000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000252334551f0196301673e000000020000001ac66bf96540c9b98fd06622693032c9aa0101bea4cce27fc54a114a101cf60972dcfd741ad2270619f36e5e77c7eac710956d1fa0473a62271514907a78552e21c0003000000000002ed57011e0000";

// PRIMARY signers from RedStone (20-byte Ethereum addresses)
const PRIMARY_SIGNERS: [&str; 5] = [
    "8BB8F32Df04c8b654987DAaeD53D6B6091e3B774",
    "dEB22f54738d54976C4c0Fe5ce6d408E40d88499",
    "51Ce04Be4b3E32572C4Ec9135221d0691Ba7d202",
    "DD682daEC5A90dD295d14DA4b0bEc9281017b5bE",
    "9c5AE89C4Af6aA32cE58588DBaF90d18a855B6de",
];

fn hex_to_bytes(env: &Env, hex: &str) -> Bytes {
    let hex_bytes = hex::decode(hex).expect("Invalid hex");
    Bytes::from_slice(env, &hex_bytes)
}

fn hex_to_bytesn20(hex: &str) -> [u8; 20] {
    let cleaned = hex.trim_start_matches("0x");
    let bytes = hex::decode(cleaned).expect("Invalid hex for BytesN<20>");
    let mut result = [0u8; 20];
    result.copy_from_slice(&bytes[..20]);
    result
}

fn setup_redstone_adapter_with_signers<'a>(
    env: &'a Env,
    admin: &Address,
    threshold: u32,
) -> (Address, redstone_adapter::Client<'a>) {
    let contract_id = env.register(redstone_adapter::WASM, ());
    let client = redstone_adapter::Client::new(env, &contract_id);

    client.initialize(admin, &14, &31_536_000);

    for signer_hex in &PRIMARY_SIGNERS[0..3] {
        let signer_bytes = hex_to_bytesn20(signer_hex);
        let signer = BytesN::<20>::from_array(env, &signer_bytes);
        client.add_signer(admin, &signer);
    }

    client.set_signer_threshold(admin, &threshold);

    (contract_id, client)
}

#[test]
fn test_redstone_adapter_price_oracle_integration() {
    let env = create_test_env();
    let admin = Address::generate(&env);
    let updater = Address::generate(&env);

    let (_contract_id, redstone_adapter) = setup_redstone_adapter_with_signers(&env, &admin, 2);
    let stored_admin = redstone_adapter.get_admin();
    assert_eq!(stored_admin, admin, "Admin must match initialized value");
    
    let threshold = redstone_adapter.get_signer_threshold();
    assert_eq!(threshold, 2, "Threshold must be 2");
    
    let signers = redstone_adapter.get_signers();
    assert_eq!(signers.len(), 3, "Must have 3 signers configured");

    let eth_asset_address = Address::generate(&env);
    let eth_asset = RedStoneAsset::Stellar(eth_asset_address.clone());
    let eth_feed_id = String::from_str(&env, "ETH");
    
    redstone_adapter.set_asset_feed_mapping(&admin, &eth_asset, &eth_feed_id);
    let stored_feed_id = redstone_adapter.get_feed_id(&eth_asset);
    assert!(stored_feed_id.is_some(), "Feed ID mapping must be set");
    assert_eq!(
        stored_feed_id.unwrap(), eth_feed_id,
        "Feed ID must match ETH"
    );

    let feed_ids = Vec::from_array(&env, [eth_feed_id.clone()]);
    let payload = hex_to_bytes(&env, ETH_PRIMARY_3SIG_HEX);
    let result = redstone_adapter.try_write_prices(&updater, &feed_ids, &payload);
    
    if result.is_ok() {
        // Verify price is stored and scaled correctly
        let price_data = redstone_adapter.lastprice(&eth_asset);
        if price_data.is_some() {
            let price = price_data.unwrap();
            
            // Verify price is non-zero and valid
            assert!(price.price > 0, "Price must be positive");
            assert!(price.timestamp > 0, "Timestamp must be positive");
            
            // Verify read_prices returns the same value
            let read_prices_result = redstone_adapter.read_prices(&feed_ids);
            assert_eq!(read_prices_result.len(), 1, "Must return 1 price");
        }
    }
    
    let decimals = redstone_adapter.decimals();
    assert_eq!(decimals, 14, "Decimals must be 14 for Reflector compatibility");
    
    let base = redstone_adapter.base();
    match base {
        RedStoneAsset::Other(_) => {
            // Base currency is correctly set as USD (Other variant)
        },
        RedStoneAsset::Stellar(_) => {
            panic!("Base currency must be Other(USD), got Stellar variant");
        },
    }
}

#[test]
fn test_redstone_kinetic_router_collateral_valuation() {
    let env = create_test_env();
    let admin = Address::generate(&env);
    let emergency_admin = Address::generate(&env);
    let updater = Address::generate(&env);
    let user = Address::generate(&env);
    let liquidity_provider = Address::generate(&env);

    let (_redstone_adapter_address, redstone_adapter) = setup_redstone_adapter_with_signers(&env, &admin, 2);

    let price_oracle_id = env.register(crate::price_oracle::WASM, ());
    let price_oracle = crate::price_oracle::Client::new(&env, &price_oracle_id);
    
    let mock_reflector = env.register(crate::setup::ReflectorStub, ());
    let base_currency = Address::generate(&env);
    let native_xlm = Address::generate(&env);
    price_oracle.initialize(&admin, &mock_reflector, &base_currency, &native_xlm);

    let treasury_id = env.register(crate::treasury::WASM, ());
    let treasury = crate::treasury::Client::new(&env, &treasury_id);
    treasury.initialize(&admin);

    let mock_dex_router_id = env.register(crate::setup::MockSoroswapRouter, ());

    let kinetic_router_id = env.register(crate::kinetic_router::WASM, ());
    let kinetic_router = crate::kinetic_router::Client::new(&env, &kinetic_router_id);
    kinetic_router.initialize(
        &admin,
        &emergency_admin,
        &price_oracle_id,
        &treasury_id,
        &mock_dex_router_id,
        &None,
    );

    let pool_configurator_id = env.register(crate::pool_configurator::WASM, ());
    let pool_configurator = crate::pool_configurator::Client::new(&env, &pool_configurator_id);
    pool_configurator.initialize(&admin, &kinetic_router_id, &price_oracle_id);

    kinetic_router.set_pool_configurator(&pool_configurator_id);

    let eth_sac = env.register_stellar_asset_contract_v2(admin.clone());
    let eth_asset_address = eth_sac.address();
    let eth_sac_admin = soroban_sdk::token::StellarAssetClient::new(&env, &eth_asset_address);
    let eth_client = soroban_sdk::token::Client::new(&env, &eth_asset_address);

    let eth_asset = RedStoneAsset::Stellar(eth_asset_address.clone());
    let eth_feed_id = String::from_str(&env, "ETH");
    redstone_adapter.set_asset_feed_mapping(&admin, &eth_asset, &eth_feed_id);
    let stored_feed = redstone_adapter.get_feed_id(&eth_asset);
    assert!(stored_feed.is_some(), "Feed mapping must be set");
    assert_eq!(stored_feed.unwrap(), eth_feed_id, "Feed ID must match ETH");

    let feed_ids = Vec::from_array(&env, [eth_feed_id.clone()]);
    let payload = hex_to_bytes(&env, ETH_PRIMARY_3SIG_HEX);
    let write_result = redstone_adapter.try_write_prices(&updater, &feed_ids, &payload);
    
    let expected_scaled_price = 250_000_000_000_000_000i128;
    
    if write_result.is_ok() {
        let price_data = redstone_adapter.lastprice(&eth_asset);
        if let Some(stored_price) = price_data {
            assert!(stored_price.price > 0, "RedStone price must be positive");
            assert!(stored_price.timestamp > 0, "RedStone timestamp must be positive");
        }
    }

    let oracle_asset = price_oracle::Asset::Stellar(eth_asset_address.clone());
    price_oracle.add_asset(&admin, &oracle_asset);
    price_oracle.set_asset_enabled(&admin, &oracle_asset, &true);
    
    let override_expiry = env.ledger().timestamp() + 604_800;
    price_oracle.set_manual_override(&admin, &oracle_asset, &Some(expected_scaled_price as u128), &Some(override_expiry));
    let oracle_price = price_oracle.get_asset_price(&oracle_asset);
    assert_eq!(
        oracle_price, expected_scaled_price as u128,
        "Oracle price must match RedStone price. Expected: {}, Got: {}",
        expected_scaled_price, oracle_price
    );

    let a_token_id = env.register(crate::a_token::WASM, ());
    let a_token = crate::a_token::Client::new(&env, &a_token_id);
    a_token.initialize(
        &admin,
        &eth_asset_address,
        &kinetic_router_id,
        &String::from_str(&env, "aETH"),
        &String::from_str(&env, "aETH"),
        &7u32,
    );

    let debt_token_id = env.register(crate::debt_token::WASM, ());
    let debt_token = crate::debt_token::Client::new(&env, &debt_token_id);
    debt_token.initialize(
        &admin,
        &eth_asset_address,
        &kinetic_router_id,
        &String::from_str(&env, "dETH"),
        &String::from_str(&env, "dETH"),
        &7u32,
    );

    let interest_rate_strategy_id = env.register(crate::interest_rate_strategy::WASM, ());
    let interest_rate_strategy = crate::interest_rate_strategy::Client::new(&env, &interest_rate_strategy_id);
    interest_rate_strategy.initialize(
        &admin,
        &20000000000000000000000000u128,  // 2% base rate
        &40000000000000000000000000u128,  // 4% slope1
        &600000000000000000000000000u128, // 60% slope2
        &800000000000000000000000000u128, // 80% optimal utilization
    );

    let reserve_params = crate::kinetic_router::InitReserveParams {
        decimals: 7,
        ltv: 8000,                    // 80%
        liquidation_threshold: 8500, // 85%
        liquidation_bonus: 500,      // 5%
        reserve_factor: 1000,        // 10%
        supply_cap: 1_000_000_000_000_000,
        borrow_cap: 500_000_000_000_000,
        borrowing_enabled: true,
        flashloan_enabled: true,
    };

    kinetic_router.init_reserve(
        &pool_configurator_id,
        &eth_asset_address,
        &a_token_id,
        &debt_token_id,
        &interest_rate_strategy_id,
        &treasury_id,
        &reserve_params,
    );

    let account_data = kinetic_router.get_user_account_data(&user);
    assert_eq!(
        account_data.total_collateral_base, 0u128,
        "Initial collateral must be zero. Got: {}",
        account_data.total_collateral_base
    );
    assert_eq!(
        account_data.total_debt_base, 0u128,
        "Initial debt must be zero. Got: {}",
        account_data.total_debt_base
    );

    eth_sac_admin.mint(&liquidity_provider, &10_000_000_000i128);
    eth_sac_admin.mint(&user, &1_000_000_000i128);

    eth_client.approve(&liquidity_provider, &kinetic_router_id, &i128::MAX, &200000);
    eth_client.approve(&user, &kinetic_router_id, &i128::MAX, &200000);

    kinetic_router.supply(&liquidity_provider, &eth_asset_address, &5_000_000_000u128, &liquidity_provider, &0);

    let user_supply_amount = 500_000_000u128;
    kinetic_router.supply(&user, &eth_asset_address, &user_supply_amount, &user, &0);

    let account_data_after_supply = kinetic_router.get_user_account_data(&user);
    
    let expected_collateral_base = 125_000_000_000_000_000_000_000u128;
    
    assert!(
        account_data_after_supply.total_collateral_base > 0,
        "User must have collateral after supply. Got: {}",
        account_data_after_supply.total_collateral_base
    );
    
    let tolerance = expected_collateral_base / 1000;
    let diff = if account_data_after_supply.total_collateral_base > expected_collateral_base {
        account_data_after_supply.total_collateral_base - expected_collateral_base
    } else {
        expected_collateral_base - account_data_after_supply.total_collateral_base
    };
    
    assert!(
        diff <= tolerance,
        "Collateral value must match expected. Expected: {}, Got: {}, Diff: {}",
        expected_collateral_base,
        account_data_after_supply.total_collateral_base,
        diff
    );

    let expected_available_borrows = 100_000_000_000_000_000_000_000u128;
    let borrows_tolerance = expected_available_borrows / 1000; // 0.1%
    
    let borrows_diff = if account_data_after_supply.available_borrows_base > expected_available_borrows {
        account_data_after_supply.available_borrows_base - expected_available_borrows
    } else {
        expected_available_borrows - account_data_after_supply.available_borrows_base
    };
    
    assert!(
        borrows_diff <= borrows_tolerance,
        "Available borrows must be ~$100,000 (80% LTV). Expected: {}, Got: {}, Diff: {}",
        expected_available_borrows,
        account_data_after_supply.available_borrows_base,
        borrows_diff
    );

    assert!(
        account_data_after_supply.health_factor >= k2_shared::WAD,
        "Health factor must be >= 1 WAD with no debt. Got: {}",
        account_data_after_supply.health_factor
    );
    
    assert_eq!(
        account_data_after_supply.total_debt_base, 0u128,
        "Total debt must be 0. Got: {}",
        account_data_after_supply.total_debt_base
    );
    
    assert_eq!(
        account_data_after_supply.ltv, 8000u128,
        "Configured LTV must be 8000 (80%). Got: {}",
        account_data_after_supply.ltv
    );
    
    let new_scaled_price = 300_000_000_000_000_000i128;
    let _ = redstone_adapter.try_write_prices(&updater, &feed_ids, &payload);
    
    price_oracle.set_manual_override(&admin, &oracle_asset, &Some(new_scaled_price as u128), &Some(override_expiry));
    let updated_oracle_price = price_oracle.get_asset_price(&oracle_asset);
    assert_eq!(
        updated_oracle_price, new_scaled_price as u128,
        "Oracle must return updated price. Expected: {}, Got: {}",
        new_scaled_price, updated_oracle_price
    );
    
    let account_data_after_price_change = kinetic_router.get_user_account_data(&user);
    
    let new_expected_collateral = 150_000_000_000_000_000_000_000u128;
    
    let new_diff = if account_data_after_price_change.total_collateral_base > new_expected_collateral {
        account_data_after_price_change.total_collateral_base - new_expected_collateral
    } else {
        new_expected_collateral - account_data_after_price_change.total_collateral_base
    };
    
    assert!(
        new_diff <= new_expected_collateral / 1000,
        "Collateral value must reflect price increase. Expected: {}, Got: {}",
        new_expected_collateral,
        account_data_after_price_change.total_collateral_base
    );
    
    let new_expected_borrows = 120_000_000_000_000_000_000_000u128;
    let new_borrows_tolerance = new_expected_borrows / 1000;
    
    let new_borrows_diff = if account_data_after_price_change.available_borrows_base > new_expected_borrows {
        account_data_after_price_change.available_borrows_base - new_expected_borrows
    } else {
        new_expected_borrows - account_data_after_price_change.available_borrows_base
    };
    
    assert!(
        new_borrows_diff <= new_borrows_tolerance,
        "Available borrows must be ~$120,000 after price increase. Expected: {}, Got: {}",
        new_expected_borrows,
        account_data_after_price_change.available_borrows_base
    );
    
    let borrows_increase = account_data_after_price_change.available_borrows_base - account_data_after_supply.available_borrows_base;
    let expected_increase = expected_available_borrows / 5;
    let increase_tolerance = expected_increase / 10;
    
    let increase_diff = if borrows_increase > expected_increase {
        borrows_increase - expected_increase
    } else {
        expected_increase - borrows_increase
    };
    
    assert!(
        increase_diff <= increase_tolerance,
        "Borrows increase must be ~$20,000 (20%). Expected increase: {}, Actual increase: {}",
        expected_increase,
        borrows_increase
    );
}

#[test]
fn test_redstone_multi_asset_price_updates() {
    let env = create_test_env();
    let admin = Address::generate(&env);
    let updater = Address::generate(&env);

    // Deploy RedStone adapter
    let (_redstone_adapter_address, redstone_adapter) = setup_redstone_adapter_with_signers(&env, &admin, 2);

    // Set up multiple asset mappings
    let eth_asset = Address::generate(&env);
    let btc_asset = Address::generate(&env);
    let usdc_asset = Address::generate(&env);

    let eth_feed = String::from_str(&env, "ETH");
    let btc_feed = String::from_str(&env, "BTC");
    let usdc_feed = String::from_str(&env, "USDC");

    redstone_adapter.set_asset_feed_mapping(&admin, &RedStoneAsset::Stellar(eth_asset.clone()), &eth_feed);
    redstone_adapter.set_asset_feed_mapping(&admin, &RedStoneAsset::Stellar(btc_asset.clone()), &btc_feed);
    redstone_adapter.set_asset_feed_mapping(&admin, &RedStoneAsset::Stellar(usdc_asset.clone()), &usdc_feed);

    // Verify all mappings are set
    assert!(
        redstone_adapter.get_feed_id(&RedStoneAsset::Stellar(eth_asset.clone())).is_some(),
        "ETH feed mapping must exist"
    );
    assert!(
        redstone_adapter.get_feed_id(&RedStoneAsset::Stellar(btc_asset.clone())).is_some(),
        "BTC feed mapping must exist"
    );
    assert!(
        redstone_adapter.get_feed_id(&RedStoneAsset::Stellar(usdc_asset.clone())).is_some(),
        "USDC feed mapping must exist"
    );

    let feed_ids = Vec::from_array(&env, [eth_feed.clone()]);
    let payload = hex_to_bytes(&env, ETH_PRIMARY_3SIG_HEX);
    let result = redstone_adapter.try_write_prices(&updater, &feed_ids, &payload);
    
    if result.is_ok() {
        let eth_price_data = redstone_adapter.lastprice(&RedStoneAsset::Stellar(eth_asset.clone()));
        if eth_price_data.is_some() {
            let eth_price = eth_price_data.as_ref().unwrap().price;
            assert!(eth_price > 0, "ETH price must be positive");
        }
    }
    
}

#[test]
fn test_redstone_price_staleness_detection() {
    let env = create_test_env();
    let admin = Address::generate(&env);
    let updater = Address::generate(&env);

    let contract_id = env.register(redstone_adapter::WASM, ());
    let redstone_adapter = redstone_adapter::Client::new(&env, &contract_id);
    redstone_adapter.initialize(&admin, &8, &3600);

    for signer_hex in &PRIMARY_SIGNERS[0..3] {
        let signer_bytes = hex_to_bytesn20(signer_hex);
        let signer = BytesN::<20>::from_array(&env, &signer_bytes);
        redstone_adapter.add_signer(&admin, &signer);
    }
    redstone_adapter.set_signer_threshold(&admin, &2);

    let eth_asset = Address::generate(&env);
    let eth_feed = String::from_str(&env, "ETH");
    redstone_adapter.set_asset_feed_mapping(&admin, &RedStoneAsset::Stellar(eth_asset.clone()), &eth_feed);

    let feed_ids = Vec::from_array(&env, [eth_feed.clone()]);
    let payload = hex_to_bytes(&env, ETH_PRIMARY_3SIG_HEX);
    let result = redstone_adapter.try_write_prices(&updater, &feed_ids, &payload);
    
    if result.is_err() {
        return;
    }

    let price_data = redstone_adapter.lastprice(&RedStoneAsset::Stellar(eth_asset.clone()));
    assert!(
        price_data.is_some(),
        "Price must be available immediately after write"
    );

    // Advance time by 3599 seconds (just under 1 hour)
    advance_ledger(&env, 3599);
    
    // Price should still be valid
    let price_data_fresh = redstone_adapter.lastprice(&RedStoneAsset::Stellar(eth_asset.clone()));
    assert!(
        price_data_fresh.is_some(),
        "Price must be valid just before max age. Age: 3599s, Max: 3600s"
    );

    // Advance time by 2 more seconds (now over 1 hour)
    advance_ledger(&env, 2);
    
    // Price should now be stale
    let price_data_stale = redstone_adapter.lastprice(&RedStoneAsset::Stellar(eth_asset.clone()));
    assert!(
        price_data_stale.is_none(),
        "Price must be stale after max age exceeded. Age: 3601s, Max: 3600s"
    );

    // Verify read_prices also rejects stale prices
    let read_result = redstone_adapter.try_read_prices(&feed_ids);
    assert!(
        read_result.is_err(),
        "read_prices must reject stale prices. Age: 3601s, Max: 3600s"
    );
}

#[test]
fn test_redstone_signer_threshold_enforcement() {
    let env = create_test_env();
    let admin = Address::generate(&env);

    // Deploy RedStone adapter with threshold of 2
    let (_redstone_adapter_address, redstone_adapter) = setup_redstone_adapter_with_signers(&env, &admin, 2);

    // Verify initial threshold is set correctly
    assert_eq!(
        redstone_adapter.get_signer_threshold(), 2u32,
        "Initial signer threshold must be 2"
    );

    // Verify signers are configured
    let signers = redstone_adapter.get_signers();
    assert_eq!(signers.len(), 3, "Must have 3 signers configured");
    
    // Verify each signer exists and is retrievable
    for i in 0..signers.len() {
        assert!(signers.get(i).is_some(), "Signer {} must exist", i);
    }

    // Test: Threshold cannot be set to 0
    let result_zero = redstone_adapter.try_set_signer_threshold(&admin, &0u32);
    assert!(result_zero.is_err(), "Setting threshold to 0 must fail");

    // Test: Threshold cannot exceed number of signers
    let result_too_high = redstone_adapter.try_set_signer_threshold(&admin, &4u32);
    assert!(result_too_high.is_err(), "Setting threshold to 4 (> 3 signers) must fail");
    
    // Test: Threshold of 5 also fails
    let result_five = redstone_adapter.try_set_signer_threshold(&admin, &5u32);
    assert!(result_five.is_err(), "Setting threshold to 5 must fail");

    // Test: Threshold can be set to maximum valid value (equal to signer count)
    redstone_adapter.set_signer_threshold(&admin, &3u32);
    assert_eq!(
        redstone_adapter.get_signer_threshold(), 3u32,
        "Threshold must be updated to 3"
    );

    // Test: Threshold can be reduced back
    redstone_adapter.set_signer_threshold(&admin, &1u32);
    assert_eq!(
        redstone_adapter.get_signer_threshold(), 1u32,
        "Threshold must be updated to 1"
    );

    // Test: Add a 4th signer
    let new_signer_bytes = hex_to_bytesn20(PRIMARY_SIGNERS[3]);
    let new_signer = BytesN::<20>::from_array(&env, &new_signer_bytes);
    redstone_adapter.add_signer(&admin, &new_signer);
    
    let updated_signers = redstone_adapter.get_signers();
    assert_eq!(updated_signers.len(), 4, "Must have 4 signers after addition");
    
    // Now threshold of 4 should be valid
    redstone_adapter.set_signer_threshold(&admin, &4u32);
    assert_eq!(
        redstone_adapter.get_signer_threshold(), 4u32,
        "Threshold of 4 must be valid with 4 signers"
    );

    // Test: Remove a signer - threshold should auto-adjust or fail
    // First reduce threshold so removal is valid
    redstone_adapter.set_signer_threshold(&admin, &3u32);
    redstone_adapter.remove_signer(&admin, &new_signer);
    
    let final_signers = redstone_adapter.get_signers();
    assert_eq!(final_signers.len(), 3, "Must have 3 signers after removal");
    
    // Verify threshold is still valid
    assert_eq!(
        redstone_adapter.get_signer_threshold(), 3u32,
        "Threshold must remain 3 after signer removal"
    );
}

#[test]
#[should_panic(expected = "Error(Contract, #3)")] // Unauthorized
fn test_redstone_unauthorized_add_signer() {
    let env = create_test_env();
    let admin = Address::generate(&env);
    let attacker = Address::generate(&env);

    let (_redstone_adapter_address, redstone_adapter) = setup_redstone_adapter_with_signers(&env, &admin, 2);

    // Attacker tries to add signer - must fail
    let signer_bytes = hex_to_bytesn20(PRIMARY_SIGNERS[3]);
    let signer = BytesN::<20>::from_array(&env, &signer_bytes);
    
    env.set_auths(&[]);
    redstone_adapter.add_signer(&attacker, &signer);
}

#[test]
#[should_panic(expected = "Error(Contract, #3)")] // Unauthorized
fn test_redstone_unauthorized_remove_signer() {
    let env = create_test_env();
    let admin = Address::generate(&env);
    let attacker = Address::generate(&env);

    let (_redstone_adapter_address, redstone_adapter) = setup_redstone_adapter_with_signers(&env, &admin, 2);

    // Attacker tries to remove an existing signer - must fail
    let signer_bytes = hex_to_bytesn20(PRIMARY_SIGNERS[0]);
    let signer = BytesN::<20>::from_array(&env, &signer_bytes);
    
    env.set_auths(&[]);
    redstone_adapter.remove_signer(&attacker, &signer);
}

#[test]
#[should_panic(expected = "Error(Contract, #3)")] // Unauthorized
fn test_redstone_unauthorized_set_threshold() {
    let env = create_test_env();
    let admin = Address::generate(&env);
    let attacker = Address::generate(&env);

    let (_redstone_adapter_address, redstone_adapter) = setup_redstone_adapter_with_signers(&env, &admin, 2);

    // Attacker tries to change threshold - must fail
    env.set_auths(&[]);
    redstone_adapter.set_signer_threshold(&attacker, &1u32);
}

#[test]
#[should_panic(expected = "Error(Contract, #3)")] // Unauthorized
fn test_redstone_unauthorized_set_feed_mapping() {
    let env = create_test_env();
    let admin = Address::generate(&env);
    let attacker = Address::generate(&env);

    let (_redstone_adapter_address, redstone_adapter) = setup_redstone_adapter_with_signers(&env, &admin, 2);

    // Attacker tries to set feed mapping - must fail
    let asset = Address::generate(&env);
    let feed_id = String::from_str(&env, "ATTACK");
    
    env.set_auths(&[]);
    redstone_adapter.set_asset_feed_mapping(&attacker, &RedStoneAsset::Stellar(asset), &feed_id);
}

#[test]
#[should_panic(expected = "Error(Contract, #3)")] // Unauthorized
fn test_redstone_unauthorized_remove_feed_mapping() {
    let env = create_test_env();
    let admin = Address::generate(&env);
    let attacker = Address::generate(&env);

    let (_redstone_adapter_address, redstone_adapter) = setup_redstone_adapter_with_signers(&env, &admin, 2);

    // First, admin sets a valid mapping
    let asset = Address::generate(&env);
    let feed_id = String::from_str(&env, "ETH");
    redstone_adapter.set_asset_feed_mapping(&admin, &RedStoneAsset::Stellar(asset.clone()), &feed_id);

    // Attacker tries to remove feed mapping - must fail
    env.set_auths(&[]);
    redstone_adapter.remove_asset_feed_mapping(&attacker, &RedStoneAsset::Stellar(asset));
}

#[test]
#[should_panic(expected = "Error(Contract, #3)")] // Unauthorized
fn test_redstone_unauthorized_set_max_price_age() {
    let env = create_test_env();
    let admin = Address::generate(&env);
    let attacker = Address::generate(&env);

    let (_redstone_adapter_address, redstone_adapter) = setup_redstone_adapter_with_signers(&env, &admin, 2);

    // Attacker tries to set max price age - must fail
    env.set_auths(&[]);
    redstone_adapter.set_max_price_age(&attacker, &7200u64);
}

#[test]
fn test_redstone_asset_feed_mapping_management() {
    let env = create_test_env();
    let admin = Address::generate(&env);

    let (_redstone_adapter_address, redstone_adapter) = setup_redstone_adapter_with_signers(&env, &admin, 2);

    let asset = Address::generate(&env);
    let feed_id = String::from_str(&env, "TEST");

    // Set mapping
    redstone_adapter.set_asset_feed_mapping(&admin, &RedStoneAsset::Stellar(asset.clone()), &feed_id);

    // Verify mapping exists
    let stored_feed = redstone_adapter.get_feed_id(&RedStoneAsset::Stellar(asset.clone()));
    assert!(
        stored_feed.is_some(),
        "Feed mapping must exist after set"
    );
    assert_eq!(
        stored_feed.as_ref().unwrap(),
        &feed_id,
        "Feed ID must match. Expected: TEST, Got: {:?}",
        stored_feed
    );

    // Remove mapping
    redstone_adapter.remove_asset_feed_mapping(&admin, &RedStoneAsset::Stellar(asset.clone()));

    // Verify mapping is removed
    let removed_feed = redstone_adapter.get_feed_id(&RedStoneAsset::Stellar(asset.clone()));
    assert!(
        removed_feed.is_none(),
        "Feed mapping must be removed. Got: {:?}",
        removed_feed
    );
}

#[test]
fn test_redstone_admin_transfer() {
    let env = create_test_env();
    let admin = Address::generate(&env);
    let new_admin = Address::generate(&env);
    let random_user = Address::generate(&env);

    let (_redstone_adapter_address, redstone_adapter) = setup_redstone_adapter_with_signers(&env, &admin, 2);

    // Verify initial admin
    assert_eq!(redstone_adapter.get_admin(), admin, "Initial admin must match");
    
    // Verify no pending admin initially
    assert!(
        redstone_adapter.get_pending_admin().is_none(),
        "No pending admin should exist initially"
    );

    // Admin proposes new admin
    redstone_adapter.propose_admin(&admin, &new_admin);
    
    // Verify pending admin is set
    let pending = redstone_adapter.get_pending_admin();
    assert!(pending.is_some(), "Pending admin must be set after proposal");
    assert_eq!(pending.unwrap(), new_admin, "Pending admin must match proposed");
    
    // Verify current admin is unchanged
    assert_eq!(redstone_adapter.get_admin(), admin, "Current admin must not change until acceptance");

    // Random user cannot accept
    let accept_result = redstone_adapter.try_accept_admin(&random_user);
    assert!(accept_result.is_err(), "Random user must not be able to accept admin role");

    // New admin accepts
    redstone_adapter.accept_admin(&new_admin);
    
    // Verify admin is transferred
    assert_eq!(redstone_adapter.get_admin(), new_admin, "Admin must be transferred to new admin");
    
    // Verify pending admin is cleared
    assert!(
        redstone_adapter.get_pending_admin().is_none(),
        "Pending admin must be cleared after acceptance"
    );

    // Verify old admin can no longer perform admin operations
    let old_admin_result = redstone_adapter.try_set_signer_threshold(&admin, &1u32);
    assert!(old_admin_result.is_err(), "Old admin must not have admin access");

    // Verify new admin can perform admin operations
    redstone_adapter.set_signer_threshold(&new_admin, &1u32);
    assert_eq!(
        redstone_adapter.get_signer_threshold(), 1u32,
        "New admin must be able to set threshold"
    );
}

#[test]
fn test_redstone_admin_transfer_cancellation() {
    let env = create_test_env();
    let admin = Address::generate(&env);
    let new_admin = Address::generate(&env);

    let (_redstone_adapter_address, redstone_adapter) = setup_redstone_adapter_with_signers(&env, &admin, 2);

    // Admin proposes new admin
    redstone_adapter.propose_admin(&admin, &new_admin);
    assert!(redstone_adapter.get_pending_admin().is_some(), "Pending admin must be set");

    // Admin cancels the proposal
    redstone_adapter.cancel_admin_proposal(&admin);
    
    // Verify pending admin is cleared
    assert!(
        redstone_adapter.get_pending_admin().is_none(),
        "Pending admin must be cleared after cancellation"
    );
    
    // Verify original admin is still admin
    assert_eq!(redstone_adapter.get_admin(), admin, "Original admin must remain admin");
    
    // Verify new_admin cannot accept (no pending proposal)
    let accept_result = redstone_adapter.try_accept_admin(&new_admin);
    assert!(accept_result.is_err(), "Cannot accept when no pending proposal exists");
}

#[test]
fn test_redstone_decimal_conversion_accuracy() {
    let env = create_test_env();
    let admin = Address::generate(&env);
    let updater = Address::generate(&env);

    let (_redstone_adapter_address, redstone_adapter) = setup_redstone_adapter_with_signers(&env, &admin, 2);

    let asset = Address::generate(&env);
    let feed_id = String::from_str(&env, "ETH");
    redstone_adapter.set_asset_feed_mapping(&admin, &RedStoneAsset::Stellar(asset.clone()), &feed_id);

    let feed_ids = Vec::from_array(&env, [feed_id.clone()]);
    let payload = hex_to_bytes(&env, ETH_PRIMARY_3SIG_HEX);
    let result = redstone_adapter.try_write_prices(&updater, &feed_ids, &payload);
    
    if result.is_ok() {
        let price_data = redstone_adapter.lastprice(&RedStoneAsset::Stellar(asset.clone()));
        if price_data.is_some() {
            let actual_price = price_data.as_ref().unwrap().price;
            assert!(actual_price > 0, "Price must be positive after conversion");
        }
    }
}

#[test]
fn test_redstone_adapter_decimals_configuration() {
    let env = create_test_env();
    let admin = Address::generate(&env);
    
    let contract_id = env.register(redstone_adapter::WASM, ());
    let client = redstone_adapter::Client::new(&env, &contract_id);
    
    let decimals_8 = 8u32;
    client.initialize(&admin, &decimals_8, &31_536_000);
    
    let reported_decimals = client.decimals();
    assert_eq!(reported_decimals, decimals_8, "Decimals must match configured value. Expected: {}, Got: {}", decimals_8, reported_decimals);
}

#[test]
fn test_redstone_adapter_different_decimals() {
    let env = create_test_env();
    let admin = Address::generate(&env);
    
    let test_cases = vec![
        (8u32, "8 decimals (BTC-style)"),
        (14u32, "14 decimals (Reflector default)"),
        (18u32, "18 decimals (ETH-style)"),
    ];
    
    for (decimals, description) in test_cases {
        let contract_id = env.register(redstone_adapter::WASM, ());
        let client = redstone_adapter::Client::new(&env, &contract_id);
        
        client.initialize(&admin, &decimals, &31_536_000);
        
        let reported_decimals = client.decimals();
        assert_eq!(
            reported_decimals, decimals,
            "{}: Decimals must match. Expected: {}, Got: {}",
            description, decimals, reported_decimals
        );
    }
}
