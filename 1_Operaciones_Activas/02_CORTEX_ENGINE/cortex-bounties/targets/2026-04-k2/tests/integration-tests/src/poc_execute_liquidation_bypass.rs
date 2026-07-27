#![cfg(test)]

use crate::setup::{deploy_test_protocol_two_assets, set_default_ledger};
use crate::price_oracle;
use k2_shared::WAD;
use soroban_sdk::{Env, Address};

#[test]
fn test_poc_execute_liquidation_bypass_blocked() {
    let env = Env::default();
    env.mock_all_auths();
    set_default_ledger(&env);
    
    let protocol = deploy_test_protocol_two_assets(&env);
    
    let usdc_supply = 1_000_000_000_000u128; // 100,000 USDC (7 decimals) -> $100,000
    let usdt_liquidity = 2_000_000_000_000u128; // 200,000 USDT (7 decimals)
    let borrow_amount = 600_000_000_000u128; // 60,000 USDT (7 decimals) -> $60,000
    
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
    let crashed_price = 600_000_000_000_000u128; // 0.60
    let usdc_asset_enum = price_oracle::Asset::Stellar(protocol.usdc_asset.clone());
    protocol.price_oracle.reset_circuit_breaker(&protocol.admin, &usdc_asset_enum);
    
    let expiry = env.ledger().timestamp() + 86400;
    protocol.price_oracle.set_manual_override(
        &protocol.admin,
        &usdc_asset_enum,
        &Some(crashed_price),
        &Some(expiry),
    );
    
    // 3. Perform 1st Liquidation via Flash Loan (50%)
    let debt_to_cover_1 = borrow_amount / 2;
    let min_swap_out = 0u128; // Simplified for test
    
    protocol.kinetic_router.prepare_liquidation(
        &protocol.liquidator,
        &protocol.user,
        &protocol.usdt_asset,
        &protocol.usdc_asset,
        &debt_to_cover_1,
        &min_swap_out,
        &None::<Address>,
    );
    
    let deadline = env.ledger().timestamp() + 300;
    protocol.kinetic_router.execute_liquidation(
        &protocol.liquidator,
        &protocol.user,
        &protocol.usdt_asset,
        &protocol.usdc_asset,
        &deadline,
    );
    
    let debt_after_1 = protocol.usdt_debt_token.balance(&protocol.user) as u128;
    
    let tracker_val = protocol.kinetic_router.get_user_liquidation_amount(&protocol.user);
    println!("DEBUG: tracker value after 1st liquidation: {}", tracker_val);
    
    // 4. Attempt 2nd Liquidation (synchronous)
    // This should fail because the tracker was updated by execute_liquidation
    let debt_to_cover_2 = debt_after_1 / 2;
    let res = protocol.kinetic_router.try_liquidation_call(
        &protocol.liquidator,
        &protocol.usdc_asset,
        &protocol.usdt_asset,
        &protocol.user,
        &debt_to_cover_2,
        &false,
    );
    
    match res {
        Err(Ok(err)) => assert_eq!(err, crate::kinetic_router::KineticRouterError::LiquidationAmountTooHigh, "Should fail with LiquidationAmountTooHigh after flash liquidation"),
        _ => panic!("Expected second liquidation to fail, but got {:?}", res),
    }
    
    println!("SUCCESS: Flash liquidation correctly updated tracker and blocked bypass.");
}
