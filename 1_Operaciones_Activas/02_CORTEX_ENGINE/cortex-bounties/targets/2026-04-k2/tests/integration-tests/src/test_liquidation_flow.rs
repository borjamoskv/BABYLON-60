#![cfg(test)]

use crate::setup::{deploy_test_protocol, deploy_test_protocol_two_assets, set_default_ledger};
use crate::price_oracle;
use k2_shared::WAD;
use soroban_sdk::Env;

#[test]
fn test_liquidation_call() {
    let env = Env::default();
    env.mock_all_auths();
    set_default_ledger(&env);
    
    let protocol = deploy_test_protocol_two_assets(&env);
    
    let usdc_supply = 10_000_000_000u128; // 10 USDC (7 decimals)
    let usdt_liquidity = 20_000_000_000u128; // 20 USDT (7 decimals)
    let borrow_amount = 6_000_000_000u128; // 6 USDT (7 decimals)
    
    // Liquidity provider supplies USDT
    protocol.kinetic_router.supply(
        &protocol.liquidity_provider,
        &protocol.usdt_asset,
        &usdt_liquidity,
        &protocol.liquidity_provider,
        &0u32,
    );
    
    // User supplies USDC as collateral
    protocol.kinetic_router.supply(
        &protocol.user,
        &protocol.usdc_asset,
        &usdc_supply,
        &protocol.user,
        &0u32,
    );
    
    // Enable USDC as collateral
    protocol.kinetic_router.set_user_use_reserve_as_coll(
        &protocol.user,
        &protocol.usdc_asset,
        &true,
    );
    
    // User borrows USDT
    protocol.kinetic_router.borrow(
        &protocol.user,
        &protocol.usdt_asset,
        &borrow_amount,
        &1u32, // Variable rate mode
        &0u32,
        &protocol.user,
    );
    
    // Verify position details before liquidation
    let account_data_before = protocol.kinetic_router.get_user_account_data(&protocol.user);
    assert!(account_data_before.health_factor >= WAD, "Position should be healthy before price crash. HF: {}", account_data_before.health_factor);
    assert!(account_data_before.total_debt_base > 0, "Debt should be positive");
    assert!(account_data_before.total_collateral_base > 0, "Should have collateral");
    
    // Verify debt tokens minted
    let debt_balance_before = protocol.usdt_debt_token.balance(&protocol.user);
    assert_eq!(debt_balance_before, borrow_amount as i128, "Debt tokens should match borrow amount");
    
    // Crash USDC price to make position unhealthy
    let crashed_price = 700_000_000_000_000u128; // 0.70 with 14 decimals (30% crash)
    let usdc_asset_enum = price_oracle::Asset::Stellar(protocol.usdc_asset.clone());
    
    // Reset circuit breaker first to allow large price change
    protocol.price_oracle.reset_circuit_breaker(&protocol.admin, &usdc_asset_enum);
    
    // Set crashed price
    let expiry = env.ledger().timestamp() + 86400; // 24 hours
    protocol.price_oracle.set_manual_override(
        &protocol.admin,
        &usdc_asset_enum,
        &Some(crashed_price),
        &Some(expiry),
    );
    
    // Verify position is now unhealthy
    let account_data_after_crash = protocol.kinetic_router.get_user_account_data(&protocol.user);
    assert!(
        account_data_after_crash.health_factor < WAD,
        "Health factor should be unhealthy after price crash (< 1.0 WAD). HF: {}",
        account_data_after_crash.health_factor
    );
    assert!(
        account_data_after_crash.health_factor > WAD / 100,
        "Health factor should not be near zero (> 0.01 WAD). HF: {}",
        account_data_after_crash.health_factor
    );
    
    // Perform liquidation — liquidate half the debt
    let debt_to_cover = borrow_amount / 2;
    protocol.kinetic_router.liquidation_call(
        &protocol.liquidator,
        &protocol.usdc_asset, // collateral
        &protocol.usdt_asset, // debt
        &protocol.user,
        &debt_to_cover,
        &false, // receive_a_token
    );
    
    // Verify liquidation worked
    let account_data_after_liquidation = protocol.kinetic_router.get_user_account_data(&protocol.user);
    assert!(
        account_data_after_liquidation.total_debt_base < account_data_after_crash.total_debt_base,
        "Debt should decrease after liquidation. Before: {}, After: {}",
        account_data_after_crash.total_debt_base,
        account_data_after_liquidation.total_debt_base
    );
    
    let debt_balance_after = protocol.usdt_debt_token.balance(&protocol.user);
    assert!(
        debt_balance_after < debt_balance_before,
        "Debt token balance should decrease after liquidation. Before: {}, After: {}",
        debt_balance_before,
        debt_balance_after
    );
    
    // Health factor should improve but may still be unhealthy
    assert!(
        account_data_after_liquidation.health_factor > 0,
        "Health factor should remain positive after liquidation. HF: {}",
        account_data_after_liquidation.health_factor
    );
}

#[test]
fn test_health_factor_calculation() {
    let env = Env::default();
    env.mock_all_auths();
    
    let protocol = deploy_test_protocol(&env);
    
    let supply_amount = 10_000_000_000u128;
    
    // Supply collateral
    protocol.kinetic_router.supply(
        &protocol.user,
        &protocol.underlying_asset,
        &supply_amount,
        &protocol.user,
        &0u32,
    );
    
    // Enable as collateral
    protocol.kinetic_router.set_user_use_reserve_as_coll(
        &protocol.user,
        &protocol.underlying_asset,
        &true,
    );
    
    // Get account data
    let account_data = protocol.kinetic_router.get_user_account_data(&protocol.user);
    
    // With no debt, health factor should be very high
    assert!(account_data.total_collateral_base > 0, "Should have collateral");
    assert_eq!(account_data.total_debt_base, 0, "Should have no debt");
    assert!(account_data.health_factor > 1_000_000_000_000_000_000u128, "Health factor should be very high (near max) with no debt");
    assert!(account_data.available_borrows_base > 0, "Should have available borrows");
    assert!(account_data.current_liquidation_threshold > 0, "Liquidation threshold should be set based on reserve config");
    
    // Verify collateral value (via get_user_account_data().total_collateral_base)
    // Collateral value is scaled by 1e12 (WAD/1e6) to convert to base units
    let expected_collateral_value = supply_amount.checked_mul(1_000_000_000_000u128).unwrap();
    assert_eq!(account_data.total_collateral_base, expected_collateral_value, "Collateral value should equal supply amount scaled by 1e12. Expected: {}, Got: {}", expected_collateral_value, account_data.total_collateral_base);
}

#[test]
fn test_collateral_value() {
    let env = Env::default();
    env.mock_all_auths();
    
    let protocol = deploy_test_protocol(&env);
    
    let supply_amount = 5_000_000_000u128;
    
    // Supply
    protocol.kinetic_router.supply(
        &protocol.user,
        &protocol.underlying_asset,
        &supply_amount,
        &protocol.user,
        &0u32,
    );
    
    // Enable as collateral
    protocol.kinetic_router.set_user_use_reserve_as_coll(
        &protocol.user,
        &protocol.underlying_asset,
        &true,
    );
    
    // Get account data (includes collateral value)
    let account_data = protocol.kinetic_router.get_user_account_data(&protocol.user);

    // Verify collateral value
    assert!(account_data.total_collateral_base > 0, "Collateral value should be positive");
    // Collateral value is scaled by 1e12 (WAD/1e6) to convert to base units
    let expected_collateral_value = supply_amount.checked_mul(1_000_000_000_000u128).unwrap();
    assert_eq!(account_data.total_collateral_base, expected_collateral_value, "Total collateral should equal supply amount scaled by 1e12. Expected: {}, Got: {}", expected_collateral_value, account_data.total_collateral_base);
    
    // Verify collateral is properly configured
    let user_config = protocol.kinetic_router.get_user_configuration(&protocol.user);
    assert!(user_config.data != 0, "User should be using asset as collateral");
}
