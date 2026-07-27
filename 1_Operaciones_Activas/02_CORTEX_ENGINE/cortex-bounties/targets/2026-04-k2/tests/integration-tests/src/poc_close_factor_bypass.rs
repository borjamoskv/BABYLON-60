#![cfg(test)]

use crate::setup::{deploy_test_protocol_two_assets, set_default_ledger};
use crate::price_oracle;
use k2_shared::WAD;
use soroban_sdk::Env;

#[test]
fn test_poc_close_factor_bypass_multi_liquidation() {
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
    
    // 4. Perform 2nd Liquidation in the same block/tx (another 50% of remainder)
    // Now that we have stateful tracking, this MUST revert with LiquidationAmountTooHigh
    let debt_to_cover_2 = debt_after_1 / 2;
    let res = protocol.kinetic_router.try_liquidation_call(
        &protocol.liquidator,
        &protocol.usdc_asset,
        &protocol.usdt_asset,
        &protocol.user,
        &debt_to_cover_2,
        &false,
    );
    
    // Verify that the bypass is blocked
    match res {
        Err(Ok(err)) => assert_eq!(err, crate::kinetic_router::KineticRouterError::LiquidationAmountTooHigh, "Should fail with LiquidationAmountTooHigh"),
        _ => panic!("Expected second liquidation to fail with LiquidationAmountTooHigh, but got {:?}", res),
    }
    
    let debt_after_2 = protocol.usdt_debt_token.balance(&protocol.user) as u128;
    assert_eq!(debt_after_2, debt_after_1, "Debt should not have changed after failed liquidation");
    
    println!("SUCCESS: Close factor bypass blocked by stateful tracker.");
    
    // 5. Verify tracker persists across calls in same ledger
    let res_3 = protocol.kinetic_router.try_liquidation_call(
        &protocol.liquidator,
        &protocol.usdc_asset,
        &protocol.usdt_asset,
        &protocol.user,
        &1u128, // Even 1 unit should fail
        &false,
    );
    
    match res_3 {
        Err(Ok(err)) => assert_eq!(err, crate::kinetic_router::KineticRouterError::LiquidationAmountTooHigh, "Should still fail with LiquidationAmountTooHigh"),
        _ => panic!("Expected third liquidation to fail"),
    }
}
