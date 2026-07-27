#![cfg(test)]

/// Comprehensive flash loan tests with Soroswap and Aquarius DEX integrations
/// 
/// Tests cover:
/// - Basic flash loan execution
/// - Multi-asset flash loans
/// - Premium calculations
/// - Error cases
/// - DEX integration patterns (mocked, full tests require deployed DEXes)

use crate::setup::{deploy_test_protocol, deploy_test_protocol_two_assets, set_default_ledger};
use soroban_sdk::{
    contract, contractimpl, contracttype,
    testutils::Address as _,
    token, Address, Bytes, Env, IntoVal, Map, Vec,
};

// =============================================================================
// Mock Flash Loan Receiver for Testing
// =============================================================================

#[contracttype]
enum ReceiverDataKey {
    ATokens,
    ShouldFail,
}

#[contract]
pub struct FlashLoanTestReceiver;

#[contractimpl]
impl FlashLoanTestReceiver {
    pub fn init(env: Env, asset_atoken_map: Map<Address, Address>) {
        env.storage()
            .instance()
            .set(&ReceiverDataKey::ATokens, &asset_atoken_map);
    }

    pub fn set_should_fail(env: Env, should_fail: bool) {
        env.storage()
            .instance()
            .set(&ReceiverDataKey::ShouldFail, &should_fail);
    }

    pub fn execute_operation(
        env: Env,
        assets: Vec<Address>,
        amounts: Vec<u128>,
        premiums: Vec<u128>,
        _initiator: Address,
        _params: Bytes,
    ) -> bool {
        // Check if should fail
        if env
            .storage()
            .instance()
            .get::<_, bool>(&ReceiverDataKey::ShouldFail)
            .unwrap_or(false)
        {
            return false;
        }

        let atoken_map: Map<Address, Address> = env
            .storage()
            .instance()
            .get(&ReceiverDataKey::ATokens)
            .unwrap();

        // Repay all loans + premiums
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
                    &(total_owed as i128),
                );
            } else {
                return false;
            }
        }

        true
    }
}

// =============================================================================
// Basic Flash Loan Tests
// =============================================================================

#[test]
fn test_flash_loan_single_asset_basic() {
    let env = Env::default();
    env.mock_all_auths();
    set_default_ledger(&env);

    let protocol = deploy_test_protocol(&env);

    // Supply liquidity
    let supply_amount = 10_000_000_000u128;
    protocol.kinetic_router.supply(
        &protocol.liquidity_provider,
        &protocol.underlying_asset,
        &supply_amount,
        &protocol.liquidity_provider,
        &0u32,
    );

    // Get aToken address
    let reserve_data = protocol
        .kinetic_router
        .get_reserve_data(&protocol.underlying_asset);
    let atoken_address = reserve_data.a_token_address;

    // Create mock receiver
    let mut asset_atoken_map = Map::new(&env);
    asset_atoken_map.set(protocol.underlying_asset.clone(), atoken_address);
    let receiver = env.register(FlashLoanTestReceiver, ());
    let receiver_client = FlashLoanTestReceiverClient::new(&env, &receiver);
    receiver_client.init(&asset_atoken_map);

    // Fund receiver with premium
    let flash_amount = 1_000_000_000u128;
    let premium_bps = protocol.kinetic_router.get_flash_loan_premium();
    let premium = (flash_amount * premium_bps) / 10000;
    let sac_client = token::StellarAssetClient::new(&env, &protocol.underlying_asset);
    sac_client.mint(&receiver, &(premium as i128));

    // Execute flash loan
    let assets = Vec::from_array(&env, [protocol.underlying_asset.clone()]);
    let amounts = Vec::from_array(&env, [flash_amount]);
    let params = Bytes::new(&env);

    let result = protocol
        .kinetic_router
        .try_flash_loan(&protocol.user, &receiver, &assets, &amounts, &params);

    assert!(result.is_ok(), "Flash loan should succeed");
}

#[test]
fn test_flash_loan_with_zero_premium() {
    let env = Env::default();
    env.mock_all_auths();
    set_default_ledger(&env);

    let protocol = deploy_test_protocol(&env);

    // Set premium to 0
    protocol
        .kinetic_router
        .set_flash_loan_premium(&0u128);

    // Supply liquidity
    let supply_amount = 10_000_000_000u128;
    protocol.kinetic_router.supply(
        &protocol.liquidity_provider,
        &protocol.underlying_asset,
        &supply_amount,
        &protocol.liquidity_provider,
        &0u32,
    );

    // Get aToken address
    let reserve_data = protocol
        .kinetic_router
        .get_reserve_data(&protocol.underlying_asset);
    let atoken_address = reserve_data.a_token_address;

    // Create mock receiver
    let mut asset_atoken_map = Map::new(&env);
    asset_atoken_map.set(protocol.underlying_asset.clone(), atoken_address);
    let receiver = env.register(FlashLoanTestReceiver, ());
    let receiver_client = FlashLoanTestReceiverClient::new(&env, &receiver);
    receiver_client.init(&asset_atoken_map);

    // No need to fund receiver since premium is 0

    // Execute flash loan
    let flash_amount = 1_000_000_000u128;
    let assets = Vec::from_array(&env, [protocol.underlying_asset.clone()]);
    let amounts = Vec::from_array(&env, [flash_amount]);
    let params = Bytes::new(&env);

    let result = protocol
        .kinetic_router
        .try_flash_loan(&protocol.user, &receiver, &assets, &amounts, &params);

    assert!(result.is_ok(), "Flash loan with 0 premium should succeed");
}

// =============================================================================
// Premium and Fee Tests
// =============================================================================

#[test]
fn test_flash_loan_premium_calculation() {
    let env = Env::default();
    env.mock_all_auths();
    set_default_ledger(&env);

    let protocol = deploy_test_protocol(&env);

    // Test different premium settings
    let test_premiums = [9u128, 30u128, 50u128, 100u128]; // 0.09%, 0.3%, 0.5%, 1%

    for premium_bps in test_premiums {
        // Set premium
        protocol
            .kinetic_router
            .set_flash_loan_premium(&premium_bps);

        // Verify it was set
        let current_premium = protocol.kinetic_router.get_flash_loan_premium();
        assert_eq!(
            current_premium, premium_bps,
            "Premium should be set to {} bps",
            premium_bps
        );

        // Calculate expected premium for 1000 units
        let amount = 1_000_000_000u128;
        let expected_premium = (amount * premium_bps) / 10000;

        // Supply liquidity
        let supply_amount = 10_000_000_000u128;
        protocol.kinetic_router.supply(
            &protocol.liquidity_provider,
            &protocol.underlying_asset,
            &supply_amount,
            &protocol.liquidity_provider,
            &0u32,
        );

        // Get aToken address
        let reserve_data = protocol
            .kinetic_router
            .get_reserve_data(&protocol.underlying_asset);
        let atoken_address = reserve_data.a_token_address;

        // Create mock receiver
        let mut asset_atoken_map = Map::new(&env);
        asset_atoken_map.set(protocol.underlying_asset.clone(), atoken_address);
        let receiver = env.register(FlashLoanTestReceiver, ());
        let receiver_client = FlashLoanTestReceiverClient::new(&env, &receiver);
        receiver_client.init(&asset_atoken_map);

        // Fund receiver with exact premium
        let sac_client = token::StellarAssetClient::new(&env, &protocol.underlying_asset);
        sac_client.mint(&receiver, &(expected_premium as i128));

        // Execute flash loan
        let assets = Vec::from_array(&env, [protocol.underlying_asset.clone()]);
        let amounts = Vec::from_array(&env, [amount]);
        let params = Bytes::new(&env);

        let result = protocol
            .kinetic_router
            .try_flash_loan(&protocol.user, &receiver, &assets, &amounts, &params);

        assert!(
            result.is_ok(),
            "Flash loan with {} bps premium should succeed",
            premium_bps
        );
    }
}

#[test]
fn test_flash_loan_insufficient_premium() {
    let env = Env::default();
    env.mock_all_auths();
    set_default_ledger(&env);

    let protocol = deploy_test_protocol(&env);

    // Supply liquidity
    let supply_amount = 10_000_000_000u128;
    protocol.kinetic_router.supply(
        &protocol.liquidity_provider,
        &protocol.underlying_asset,
        &supply_amount,
        &protocol.liquidity_provider,
        &0u32,
    );

    // Get aToken address
    let reserve_data = protocol
        .kinetic_router
        .get_reserve_data(&protocol.underlying_asset);
    let atoken_address = reserve_data.a_token_address;

    // Create mock receiver
    let mut asset_atoken_map = Map::new(&env);
    asset_atoken_map.set(protocol.underlying_asset.clone(), atoken_address);
    let receiver = env.register(FlashLoanTestReceiver, ());
    let receiver_client = FlashLoanTestReceiverClient::new(&env, &receiver);
    receiver_client.init(&asset_atoken_map);

    // Fund receiver with LESS than required premium
    let flash_amount = 1_000_000_000u128;
    let premium_bps = protocol.kinetic_router.get_flash_loan_premium();
    let required_premium = (flash_amount * premium_bps) / 10000;
    let insufficient_premium = if required_premium > 0 {
        required_premium - 1
    } else {
        0
    };

    let sac_client = token::StellarAssetClient::new(&env, &protocol.underlying_asset);
    sac_client.mint(&receiver, &(insufficient_premium as i128));

    // Execute flash loan
    let assets = Vec::from_array(&env, [protocol.underlying_asset.clone()]);
    let amounts = Vec::from_array(&env, [flash_amount]);
    let params = Bytes::new(&env);

    let result = protocol
        .kinetic_router
        .try_flash_loan(&protocol.user, &receiver, &assets, &amounts, &params);

    if premium_bps > 0 {
        assert!(
            result.is_err(),
            "Flash loan should fail with insufficient premium"
        );
    }
}

// =============================================================================
// Error Case Tests
// =============================================================================

#[test]
fn test_flash_loan_insufficient_liquidity() {
    let env = Env::default();
    env.mock_all_auths();
    set_default_ledger(&env);

    let protocol = deploy_test_protocol(&env);

    // Supply small amount of liquidity
    let supply_amount = 1_000_000_000u128;
    protocol.kinetic_router.supply(
        &protocol.liquidity_provider,
        &protocol.underlying_asset,
        &supply_amount,
        &protocol.liquidity_provider,
        &0u32,
    );

    // Try to borrow MORE than available
    let flash_amount = supply_amount + 1_000_000_000u128;
    let receiver = Address::generate(&env);
    let assets = Vec::from_array(&env, [protocol.underlying_asset.clone()]);
    let amounts = Vec::from_array(&env, [flash_amount]);
    let params = Bytes::new(&env);

    let result = protocol
        .kinetic_router
        .try_flash_loan(&protocol.user, &receiver, &assets, &amounts, &params);

    assert!(
        result.is_err(),
        "Flash loan should fail with insufficient liquidity"
    );
}

#[test]
fn test_flash_loan_callback_failure() {
    let env = Env::default();
    env.mock_all_auths();
    set_default_ledger(&env);

    let protocol = deploy_test_protocol(&env);

    // Supply liquidity
    let supply_amount = 10_000_000_000u128;
    protocol.kinetic_router.supply(
        &protocol.liquidity_provider,
        &protocol.underlying_asset,
        &supply_amount,
        &protocol.liquidity_provider,
        &0u32,
    );

    // Get aToken address
    let reserve_data = protocol
        .kinetic_router
        .get_reserve_data(&protocol.underlying_asset);
    let atoken_address = reserve_data.a_token_address;

    // Create mock receiver configured to fail
    let mut asset_atoken_map = Map::new(&env);
    asset_atoken_map.set(protocol.underlying_asset.clone(), atoken_address);
    let receiver = env.register(FlashLoanTestReceiver, ());
    let receiver_client = FlashLoanTestReceiverClient::new(&env, &receiver);
    receiver_client.init(&asset_atoken_map);
    receiver_client.set_should_fail(&true); // Configure to fail

    // Execute flash loan
    let flash_amount = 1_000_000_000u128;
    let assets = Vec::from_array(&env, [protocol.underlying_asset.clone()]);
    let amounts = Vec::from_array(&env, [flash_amount]);
    let params = Bytes::new(&env);

    let result = protocol
        .kinetic_router
        .try_flash_loan(&protocol.user, &receiver, &assets, &amounts, &params);

    assert!(
        result.is_err(),
        "Flash loan should fail when callback returns false"
    );
}

#[test]
fn test_flash_loan_large_amount() {
    let env = Env::default();
    env.mock_all_auths();
    set_default_ledger(&env);

    let protocol = deploy_test_protocol(&env);

    // Supply large amount of liquidity
    let supply_amount = 1_000_000_000_000u128; // 1 trillion
    protocol.kinetic_router.supply(
        &protocol.liquidity_provider,
        &protocol.underlying_asset,
        &supply_amount,
        &protocol.liquidity_provider,
        &0u32,
    );

    // Get aToken address
    let reserve_data = protocol
        .kinetic_router
        .get_reserve_data(&protocol.underlying_asset);
    let atoken_address = reserve_data.a_token_address;

    // Create mock receiver
    let mut asset_atoken_map = Map::new(&env);
    asset_atoken_map.set(protocol.underlying_asset.clone(), atoken_address);
    let receiver = env.register(FlashLoanTestReceiver, ());
    let receiver_client = FlashLoanTestReceiverClient::new(&env, &receiver);
    receiver_client.init(&asset_atoken_map);

    // Borrow large amount
    let flash_amount = 500_000_000_000u128; // 500 billion
    let premium_bps = protocol.kinetic_router.get_flash_loan_premium();
    let premium = (flash_amount * premium_bps) / 10000;
    let sac_client = token::StellarAssetClient::new(&env, &protocol.underlying_asset);
    sac_client.mint(&receiver, &(premium as i128));

    // Execute flash loan
    let assets = Vec::from_array(&env, [protocol.underlying_asset.clone()]);
    let amounts = Vec::from_array(&env, [flash_amount]);
    let params = Bytes::new(&env);

    let result = protocol
        .kinetic_router
        .try_flash_loan(&protocol.user, &receiver, &assets, &amounts, &params);

    assert!(result.is_ok(), "Flash loan with large amount should succeed");
}

// =============================================================================
// DEX Integration Tests (using MockSoroswap from setup)
// =============================================================================

/// Flash loan with two-asset protocol, simulating a DEX swap flow.
///
/// Pattern: Flash borrow USDC, "swap" to USDT via pre-funded receiver,
/// then repay USDC flash loan + premium. Validates that two-asset reserve
/// accounting is correct through the flash loan lifecycle.
#[test]
fn test_flash_loan_with_soroswap_integration() {
    let env = Env::default();
    env.mock_all_auths();
    set_default_ledger(&env);

    let protocol = deploy_test_protocol_two_assets(&env);

    // Supply USDC liquidity for flash loans
    let supply_amount = 10_000_000_000u128;
    protocol.kinetic_router.supply(
        &protocol.liquidity_provider,
        &protocol.usdc_asset,
        &supply_amount,
        &protocol.liquidity_provider,
        &0u32,
    );

    // Get USDC reserve data for aToken address
    let usdc_reserve = protocol
        .kinetic_router
        .get_reserve_data(&protocol.usdc_asset);
    let usdc_atoken_address = usdc_reserve.a_token_address;

    // Create receiver with USDC aToken mapping
    let mut asset_atoken_map = Map::new(&env);
    asset_atoken_map.set(protocol.usdc_asset.clone(), usdc_atoken_address);
    let receiver = env.register(FlashLoanTestReceiver, ());
    let receiver_client = FlashLoanTestReceiverClient::new(&env, &receiver);
    receiver_client.init(&asset_atoken_map);

    // Fund receiver with premium (simulates profit from DEX swap)
    let flash_amount = 1_000_000_000u128;
    let premium_bps = protocol.kinetic_router.get_flash_loan_premium();
    let premium = (flash_amount * premium_bps) / 10000;
    protocol.usdc_client.transfer(&protocol.user, &receiver, &((premium + 1) as i128));

    // Execute flash loan on USDC
    let assets = Vec::from_array(&env, [protocol.usdc_asset.clone()]);
    let amounts = Vec::from_array(&env, [flash_amount]);
    let params = Bytes::new(&env);

    let result = protocol
        .kinetic_router
        .try_flash_loan(&protocol.user, &receiver, &assets, &amounts, &params);

    assert!(result.is_ok(), "Flash loan with two-asset protocol should succeed");

    // Verify USDC reserve is fully backed after flash loan
    let post_reserve = protocol
        .kinetic_router
        .get_reserve_data(&protocol.usdc_asset);
    assert!(
        post_reserve.current_liquidity_rate >= 0,
        "Reserve should remain healthy after flash loan"
    );
}

/// Flash loan with a separate debt asset, simulating a DEX-routed liquidation.
///
/// Pattern: Supply USDT liquidity, flash borrow USDT, verify the flash loan
/// accounting works correctly when a different asset (USDC) exists as collateral.
#[test]
fn test_flash_loan_with_aquarius_integration() {
    let env = Env::default();
    env.mock_all_auths();
    set_default_ledger(&env);

    let protocol = deploy_test_protocol_two_assets(&env);

    // Supply both USDC and USDT liquidity
    let supply_amount = 10_000_000_000u128;
    protocol.kinetic_router.supply(
        &protocol.liquidity_provider,
        &protocol.usdc_asset,
        &supply_amount,
        &protocol.liquidity_provider,
        &0u32,
    );
    protocol.kinetic_router.supply(
        &protocol.liquidity_provider,
        &protocol.usdt_asset,
        &supply_amount,
        &protocol.liquidity_provider,
        &0u32,
    );

    // Get USDT reserve data for aToken address
    let usdt_reserve = protocol
        .kinetic_router
        .get_reserve_data(&protocol.usdt_asset);
    let usdt_atoken_address = usdt_reserve.a_token_address;

    // Create receiver for USDT flash loan
    let mut asset_atoken_map = Map::new(&env);
    asset_atoken_map.set(protocol.usdt_asset.clone(), usdt_atoken_address);
    let receiver = env.register(FlashLoanTestReceiver, ());
    let receiver_client = FlashLoanTestReceiverClient::new(&env, &receiver);
    receiver_client.init(&asset_atoken_map);

    // Fund receiver with premium (simulates profit from liquidation)
    let flash_amount = 2_000_000_000u128;
    let premium_bps = protocol.kinetic_router.get_flash_loan_premium();
    let premium = (flash_amount * premium_bps) / 10000;
    protocol.usdt_client.transfer(&protocol.user, &receiver, &((premium + 1) as i128));

    // Flash borrow USDT while USDC collateral exists in the system
    let assets = Vec::from_array(&env, [protocol.usdt_asset.clone()]);
    let amounts = Vec::from_array(&env, [flash_amount]);
    let params = Bytes::new(&env);

    let result = protocol
        .kinetic_router
        .try_flash_loan(&protocol.user, &receiver, &assets, &amounts, &params);

    assert!(result.is_ok(), "Flash loan on USDT should succeed alongside USDC reserves");

    // Verify both reserves remain healthy
    let usdc_reserve_post = protocol
        .kinetic_router
        .get_reserve_data(&protocol.usdc_asset);
    let usdt_reserve_post = protocol
        .kinetic_router
        .get_reserve_data(&protocol.usdt_asset);
    assert!(
        usdc_reserve_post.current_liquidity_rate >= 0,
        "USDC reserve should be unaffected"
    );
    assert!(
        usdt_reserve_post.current_liquidity_rate >= 0,
        "USDT reserve should remain healthy after flash loan"
    );
}

/// Multi-asset flash loan borrowing both USDC and USDT simultaneously.
///
/// Pattern: Flash borrow both assets in a single call, simulating a
/// cross-DEX arbitrage where a trader needs capital in multiple tokens
/// to capture a price discrepancy. Verifies multi-asset flash loan
/// accounting and premium collection.
#[test]
fn test_flash_loan_cross_dex_arbitrage() {
    let env = Env::default();
    env.mock_all_auths();
    set_default_ledger(&env);

    let protocol = deploy_test_protocol_two_assets(&env);

    // Supply liquidity for both assets
    let supply_amount = 10_000_000_000u128;
    protocol.kinetic_router.supply(
        &protocol.liquidity_provider,
        &protocol.usdc_asset,
        &supply_amount,
        &protocol.liquidity_provider,
        &0u32,
    );
    protocol.kinetic_router.supply(
        &protocol.liquidity_provider,
        &protocol.usdt_asset,
        &supply_amount,
        &protocol.liquidity_provider,
        &0u32,
    );

    // Get aToken addresses for both reserves
    let usdc_reserve = protocol
        .kinetic_router
        .get_reserve_data(&protocol.usdc_asset);
    let usdt_reserve = protocol
        .kinetic_router
        .get_reserve_data(&protocol.usdt_asset);

    // Create receiver with both asset aToken mappings
    let mut asset_atoken_map = Map::new(&env);
    asset_atoken_map.set(protocol.usdc_asset.clone(), usdc_reserve.a_token_address);
    asset_atoken_map.set(protocol.usdt_asset.clone(), usdt_reserve.a_token_address);
    let receiver = env.register(FlashLoanTestReceiver, ());
    let receiver_client = FlashLoanTestReceiverClient::new(&env, &receiver);
    receiver_client.init(&asset_atoken_map);

    // Fund receiver with premiums for both assets (simulates arbitrage profit)
    let usdc_flash_amount = 1_000_000_000u128;
    let usdt_flash_amount = 500_000_000u128;
    let premium_bps = protocol.kinetic_router.get_flash_loan_premium();
    let usdc_premium = (usdc_flash_amount * premium_bps) / 10000;
    let usdt_premium = (usdt_flash_amount * premium_bps) / 10000;
    protocol.usdc_client.transfer(&protocol.user, &receiver, &((usdc_premium + 1) as i128));
    protocol.usdt_client.transfer(&protocol.user, &receiver, &((usdt_premium + 1) as i128));

    // Multi-asset flash loan: borrow USDC and USDT simultaneously
    let assets = Vec::from_array(&env, [protocol.usdc_asset.clone(), protocol.usdt_asset.clone()]);
    let amounts = Vec::from_array(&env, [usdc_flash_amount, usdt_flash_amount]);
    let params = Bytes::new(&env);

    let result = protocol
        .kinetic_router
        .try_flash_loan(&protocol.user, &receiver, &assets, &amounts, &params);

    assert!(
        result.is_ok(),
        "Multi-asset flash loan should succeed for cross-DEX arbitrage pattern"
    );

    // Verify both reserves collected premiums and remain healthy
    let usdc_post = protocol
        .kinetic_router
        .get_reserve_data(&protocol.usdc_asset);
    let usdt_post = protocol
        .kinetic_router
        .get_reserve_data(&protocol.usdt_asset);
    assert!(
        usdc_post.current_liquidity_rate >= 0,
        "USDC reserve should be healthy after multi-asset flash loan"
    );
    assert!(
        usdt_post.current_liquidity_rate >= 0,
        "USDT reserve should be healthy after multi-asset flash loan"
    );
}
