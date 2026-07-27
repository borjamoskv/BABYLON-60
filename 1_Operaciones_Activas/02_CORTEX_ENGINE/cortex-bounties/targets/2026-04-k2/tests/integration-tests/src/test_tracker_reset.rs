#![cfg(test)]

use crate::setup::{deploy_test_protocol_two_assets, set_default_ledger};
use crate::price_oracle;
use k2_shared::WAD;
use soroban_sdk::{Env, testutils::Address as _};

#[test]
fn test_liquidation_tracker_reset_after_repay() {
    let env = Env::default();
    env.mock_all_auths();
    set_default_ledger(&env);
    
    let protocol = deploy_test_protocol_two_assets(&env);
    
    let usdc_supply = 10_000_000_000u128; // 10 USDC (7 decimals)
    let usdt_liquidity = 20_000_000_000u128; // 20 USDT (7 decimals)
    let borrow_amount = 6_000_000_000u128; // 6 USDT (7 decimals)
    
    // 1. Setup position
    protocol.kinetic_router.supply(
        &protocol.liquidity_provider,
        &protocol.usdt_asset,
        &usdt_liquidity,
        &protocol.liquidity_provider,
        &0u32,
    );
    
    protocol.kinetic_router.supply(
        &protocol.user,
        &protocol.usdc_asset,
        &usdc_supply,
        &protocol.user,
        &0u32,
    );
    
    protocol.kinetic_router.set_user_use_reserve_as_coll(
        &protocol.user,
        &protocol.usdc_asset,
        &true,
    );
    
    protocol.kinetic_router.borrow(
        &protocol.user,
        &protocol.usdt_asset,
        &borrow_amount,
        &1u32,
        &0u32,
        &protocol.user,
    );
    
    // 2. Make position unhealthy (crash USDC price to $0.60)
    let crashed_price = 600_000_000_000_000u128; // 0.60 (40% crash)
    let usdc_asset_enum = price_oracle::Asset::Stellar(protocol.usdc_asset.clone());
    protocol.price_oracle.reset_circuit_breaker(&protocol.admin, &usdc_asset_enum);
    
    let expiry = env.ledger().timestamp() + 86400;
    protocol.price_oracle.set_manual_override(
        &protocol.admin,
        &usdc_asset_enum,
        &Some(crashed_price),
        &Some(expiry),
    );
    
    // 3. Perform 1st Liquidation (50%)
    let debt_to_cover_1 = borrow_amount / 2;
    protocol.kinetic_router.liquidation_call(
        &protocol.liquidator,
        &protocol.usdc_asset,
        &protocol.usdt_asset,
        &protocol.user,
        &debt_to_cover_1,
        &false,
    );
    
    let debt_after_1 = protocol.usdt_debt_token.balance(&protocol.user) as u128;
    
    // 4. Verify that another liquidation fails (tracker is active)
    let res = protocol.kinetic_router.try_liquidation_call(
        &protocol.liquidator,
        &protocol.usdc_asset,
        &protocol.usdt_asset,
        &protocol.user,
        &1u128,
        &false,
    );
    match res {
        Err(Ok(err)) => assert_eq!(err, crate::kinetic_router::KineticRouterError::LiquidationAmountTooHigh, "Should fail with LiquidationAmountTooHigh (12)"), // 12 is LiquidationAmountTooHigh
        _ => panic!("Expected failure with LiquidationAmountTooHigh, got {:?}", res),
    }

    // 5. User repays debt to restore health
    // We need enough USDC to repay. The user already has some or we can give them more.
    // Actually, we can just supply more USDC to increase health factor.
    let usdc_supply_2 = 10_000_000_000u128;
    protocol.kinetic_router.supply(
        &protocol.user,
        &protocol.usdc_asset,
        &usdc_supply_2,
        &protocol.user,
        &0u32,
    );
    
    // Position should be healthy now. The supply operation should have cleared the tracker.
    
    // 6. Make position unhealthy again (crash USDC price even further to $0.10)
    let crashed_price_2 = 100_000_000_000_000u128; // 0.10
    protocol.price_oracle.reset_circuit_breaker(&protocol.admin, &usdc_asset_enum);
    protocol.price_oracle.set_manual_override(
        &protocol.admin,
        &usdc_asset_enum,
        &Some(crashed_price_2),
        &Some(expiry),
    );
    
    // 7. Perform liquidation. If tracker was reset, this should SUCCEED.
    // If bug exists, this will FAIL because tracker still contains previous liquidation amount.
    let current_debt = protocol.usdt_debt_token.balance(&protocol.user) as u128;
    let debt_to_cover_2 = current_debt / 2;
    
    protocol.kinetic_router.liquidation_call(
        &protocol.liquidator,
        &protocol.usdc_asset,
        &protocol.usdt_asset,
        &protocol.user,
        &debt_to_cover_2,
        &false,
    );
    
    let final_debt = protocol.usdt_debt_token.balance(&protocol.user) as u128;
    assert!(final_debt < current_debt, "Debt should have been reduced by liquidation");
    
    println!("SUCCESS: Liquidation tracker reset verified.");
}

#[test]
fn test_liquidation_tracker_reset_after_full_repay() {
    let env = Env::default();
    env.mock_all_auths();
    set_default_ledger(&env);
    
    let protocol = deploy_test_protocol_two_assets(&env);
    
    let usdc_supply = 10_000_000_000u128;
    let usdt_liquidity = 20_000_000_000u128;
    let borrow_amount = 6_000_000_000u128;
    
    protocol.kinetic_router.supply(&protocol.liquidity_provider, &protocol.usdt_asset, &usdt_liquidity, &protocol.liquidity_provider, &0u32);
    protocol.kinetic_router.supply(&protocol.user, &protocol.usdc_asset, &usdc_supply, &protocol.user, &0u32);
    protocol.kinetic_router.set_user_use_reserve_as_coll(&protocol.user, &protocol.usdc_asset, &true);
    protocol.kinetic_router.borrow(&protocol.user, &protocol.usdt_asset, &borrow_amount, &1u32, &0u32, &protocol.user);
    
    // 1. Liquidate partially
    let usdc_asset_enum = price_oracle::Asset::Stellar(protocol.usdc_asset.clone());
    protocol.price_oracle.reset_circuit_breaker(&protocol.admin, &usdc_asset_enum);
    protocol.price_oracle.set_manual_override(&protocol.admin, &usdc_asset_enum, &Some(600_000_000_000_000), &Some(env.ledger().timestamp() + 86400));
    
    protocol.kinetic_router.liquidation_call(&protocol.liquidator, &protocol.usdc_asset, &protocol.usdt_asset, &protocol.user, &(borrow_amount / 2), &false);
    
    // 2. Full repay
    protocol.kinetic_router.repay(&protocol.user, &protocol.usdt_asset, &u128::MAX, &1u32, &protocol.user);
    
    // Tracker should be cleared.
    // 3. Borrow again and liquidate again
    protocol.kinetic_router.borrow(&protocol.user, &protocol.usdt_asset, &2_000_000_000u128, &1u32, &0u32, &protocol.user);
    
    // Make unhealthy again
    protocol.price_oracle.reset_circuit_breaker(&protocol.admin, &usdc_asset_enum);
    protocol.price_oracle.set_manual_override(&protocol.admin, &usdc_asset_enum, &Some(100_000_000_000_000), &Some(env.ledger().timestamp() + 86400));
    
    // Liquidation should work
    protocol.kinetic_router.liquidation_call(&protocol.liquidator, &protocol.usdc_asset, &protocol.usdt_asset, &protocol.user, &1_000_000_000u128, &false);
    
    let final_debt = protocol.usdt_debt_token.balance(&protocol.user) as u128;
    assert_eq!(final_debt, 1_000_000_000u128);
}
