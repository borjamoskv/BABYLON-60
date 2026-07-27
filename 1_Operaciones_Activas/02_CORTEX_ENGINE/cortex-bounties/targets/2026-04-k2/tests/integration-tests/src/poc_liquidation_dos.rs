#![cfg(test)]

use crate::setup::{deploy_test_protocol_two_assets, set_default_ledger};
use crate::price_oracle;
use k2_shared::WAD;
use soroban_sdk::{Env, testutils::Ledger};

#[test]
fn test_poc_liquidation_dos() {
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
    
    // 4. Restore health factor above 1.0 (Price recovers to $1.0)
    protocol.price_oracle.reset_circuit_breaker(&protocol.admin, &usdc_asset_enum);
    let recovered_price = 1_000_000_000_000_000u128; // 1.00
    protocol.price_oracle.set_manual_override(
        &protocol.admin,
        &usdc_asset_enum,
        &Some(recovered_price),
        &Some(expiry),
    );

    // Verify HF > 1.0
    let account_data = protocol.kinetic_router.get_user_account_data(&protocol.user);
    assert!(account_data.health_factor > WAD, "Health factor should be recovered");

    // 5. Advance time and ledger (Stay within tracker window)
    let next_ledger = env.ledger().sequence() + 100;
    let next_timestamp = env.ledger().timestamp() + 3600; // 1 hour
    env.ledger().set(soroban_sdk::testutils::LedgerInfo {
        timestamp: next_timestamp,
        protocol_version: 23,
        sequence_number: next_ledger,
        network_id: Default::default(),
        base_reserve: 10,
        min_temp_entry_ttl: 10,
        min_persistent_entry_ttl: 10,
        max_entry_ttl: 3_110_400,
    });

    // 6. Make position unhealthy again (crash USDC price to $0.50)
    protocol.price_oracle.reset_circuit_breaker(&protocol.admin, &usdc_asset_enum);
    let crashed_price_2 = 500_000_000_000_000u128; // 0.50
    let expiry_2 = env.ledger().timestamp() + 86400;
    protocol.price_oracle.set_manual_override(
        &protocol.admin,
        &usdc_asset_enum,
        &Some(crashed_price_2),
        &Some(expiry_2),
    );
    
    // Also update USDT price expiry so oracle doesn't trap
    let usdt_asset_enum = price_oracle::Asset::Stellar(protocol.usdt_asset.clone());
    protocol.price_oracle.set_manual_override(
        &protocol.admin,
        &usdt_asset_enum,
        &Some(1_000_000_000_000_000u128), // 1.00
        &Some(expiry_2),
    );

    let account_data_2 = protocol.kinetic_router.get_user_account_data(&protocol.user);
    assert!(account_data_2.health_factor < WAD, "Health factor should be unhealthy again");

    // 7. Try to liquidate again (e.g. 50% of the new debt)
    let current_debt = account_data_2.total_debt_base; // This is base, we need token amount
    let debt_token_balance = protocol.usdt_debt_token.balance(&protocol.user) as u128;
    
    // We try to liquidate even a tiny amount, say 10%
    let debt_to_cover_2 = debt_token_balance / 10;
    
    let res = protocol.kinetic_router.try_liquidation_call(
        &protocol.liquidator,
        &protocol.usdc_asset,
        &protocol.usdt_asset,
        &protocol.user,
        &debt_to_cover_2,
        &false,
    );
    
    // Verify that liquidation fails due to the accumulated tracker
    match res {
        Err(Ok(err)) => assert_eq!(err, crate::kinetic_router::KineticRouterError::LiquidationAmountTooHigh, "Should fail with LiquidationAmountTooHigh due to DoS"),
        _ => panic!("Expected second liquidation to fail with LiquidationAmountTooHigh, but got {:?}", res),
    }
    
    println!("SUCCESS: Liquidation DoS demonstrated. Tracker persisted across ledgers.");
}
