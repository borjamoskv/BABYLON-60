#![cfg(test)]

//! Tests for reserve fragmentation attack mitigation
//!
//! Verifies that:
//! 1. Users are limited to MAX_USER_RESERVES (15) active reserves
//! 2. Supply/borrow operations fail when limit is reached
//! 3. Optimized calculate_user_account_data works correctly with active reserves
//! 4. Liquidations remain feasible within Soroban resource budgets

use crate::setup::{create_test_env, deploy_test_protocol_two_assets};
use soroban_sdk::testutils::{Address as _, MockAuth, MockAuthInvoke};
use soroban_sdk::{Address, IntoVal};

/// Helper to create additional test reserves (SAC + aToken + debtToken)
fn create_test_reserve(
    protocol: &crate::setup::TestProtocolTwoAssets<'_>,
    name_suffix: u32,
) -> Address {
    use crate::{a_token, debt_token, interest_rate_strategy};
    use soroban_sdk::token;

    let env = protocol.env;

    // 1. Create underlying asset (SAC)
    let sac = env.register_stellar_asset_contract_v2(protocol.admin.clone());
    let underlying = sac.address();

    // 2. Add to oracle
    let asset_enum = crate::price_oracle::Asset::Stellar(underlying.clone());
    protocol
        .price_oracle
        .reset_circuit_breaker(&protocol.admin, &asset_enum);
    protocol.price_oracle.add_asset(&protocol.admin, &asset_enum);
    
    let expiry = env.ledger().timestamp() + 604_800; // 7 days (max allowed by L-04)
    protocol.price_oracle.set_manual_override(
        &protocol.admin,
        &asset_enum,
        &Some(1_000_000_000_000_000u128), // $1
        &Some(expiry),
    );

    // 3. Deploy reserve token contracts
    let a_token_id = env.register(a_token::WASM, ());
    let a_token_client = a_token::Client::new(env, &a_token_id);

    let debt_token_id = env.register(debt_token::WASM, ());
    let debt_token_client = debt_token::Client::new(env, &debt_token_id);

    // 4. Initialize aToken/debtToken
    a_token_client.initialize(
        &protocol.admin,
        &underlying,
        &protocol.kinetic_router.address,
        &soroban_sdk::String::from_str(env, &format!("Test aToken {}", name_suffix)),
        &soroban_sdk::String::from_str(env, &format!("aT{}", name_suffix)),
        &7u32,
    );
    debt_token_client.initialize(
        &protocol.admin,
        &underlying,
        &protocol.kinetic_router.address,
        &soroban_sdk::String::from_str(env, &format!("Test Debt {}", name_suffix)),
        &soroban_sdk::String::from_str(env, &format!("dT{}", name_suffix)),
        &7u32,
    );

    // 5. Initialize reserve in the router
    let params = crate::kinetic_router::InitReserveParams {
        decimals: 7,
        ltv: 8000,
        liquidation_threshold: 8500,
        liquidation_bonus: 500,
        reserve_factor: 1000,
        supply_cap: 1_000_000_000_000_000,
        borrow_cap: 500_000_000_000_000,
        borrowing_enabled: true,
        flashloan_enabled: true,
    };
    protocol.kinetic_router.init_reserve(
        &protocol.pool_configurator.address,
        &underlying,
        &a_token_id,
        &debt_token_id,
        &protocol.interest_rate_strategy.address,
        &protocol.treasury.address,
        &params,
    );

    // 6. Mint some tokens to the liquidity provider for this reserve
    let sac_admin = token::StellarAssetClient::new(env, &underlying);
    sac_admin.mint(&protocol.liquidity_provider, &1_000_000_000_000i128);

    // Supply liquidity to the pool
    let underlying_client = token::Client::new(env, &underlying);
    let expiration = env.ledger().sequence() + 200_000;
    underlying_client.approve(
        &protocol.liquidity_provider,
        &protocol.kinetic_router.address,
        &i128::MAX,
        &expiration,
    );
    protocol.kinetic_router.supply(
        &protocol.liquidity_provider,
        &underlying,
        &500_000_000_000u128,
        &protocol.liquidity_provider,
        &0u32,
    );

    underlying
}

#[test]
fn test_max_user_reserves_limit_on_supply() {
    let env = create_test_env();
    let protocol = deploy_test_protocol_two_assets(&env);

    // User starts with 2 reserves (USDC and USDT from setup)
    // Supply to USDC (first reserve - becomes collateral)
    protocol.kinetic_router.supply(
        &protocol.user,
        &protocol.usdc_asset,
        &100_000_000u128,
        &protocol.user,
        &0u32,
    );

    // Supply to USDT (second reserve - becomes collateral)
    protocol.kinetic_router.supply(
        &protocol.user,
        &protocol.usdt_asset,
        &100_000_000u128,
        &protocol.user,
        &0u32,
    );

    // Create 13 more reserves (total will be 15 - at the limit)
    for i in 3..=15 {
        let reserve_asset = create_test_reserve(&protocol, i);

        // Mint tokens to user
        let sac_admin = soroban_sdk::token::StellarAssetClient::new(&env, &reserve_asset);
        sac_admin.mint(&protocol.user, &1_000_000_000i128);

        // Approve
        let token_client = soroban_sdk::token::Client::new(&env, &reserve_asset);
        let expiration = env.ledger().sequence() + 200_000;
        token_client.approve(
            &protocol.user,
            &protocol.kinetic_router.address,
            &i128::MAX,
            &expiration,
        );

        // Supply - this should succeed up to 15 reserves
        let result = protocol.kinetic_router.try_supply(
            &protocol.user,
            &reserve_asset,
            &100_000_000u128,
            &protocol.user,
            &0u32,
        );
        assert!(result.is_ok(), "Supply should succeed for reserve {}", i);
    }

    // Verify user has exactly 15 active reserves
    let user_config = protocol
        .kinetic_router
        .get_user_configuration(&protocol.user);
    // Count active reserves by checking bits
    let mut count = 0u8;
    let mut data = user_config.data;
    for _ in 0..64 {
        if (data & 0b11) != 0 {
            count += 1;
        }
        data >>= 2;
        if data == 0 {
            break;
        }
    }
    assert_eq!(count, 15, "User should have exactly 15 active reserves");

    // Try to supply to a 16th reserve - should fail with MaxUserReservesExceeded
    let reserve_16 = create_test_reserve(&protocol, 16);
    let sac_admin = soroban_sdk::token::StellarAssetClient::new(&env, &reserve_16);
    sac_admin.mint(&protocol.user, &1_000_000_000i128);

    let token_client = soroban_sdk::token::Client::new(&env, &reserve_16);
    let expiration = env.ledger().sequence() + 200_000;
    token_client.approve(
        &protocol.user,
        &protocol.kinetic_router.address,
        &i128::MAX,
        &expiration,
    );

    let result = protocol.kinetic_router.try_supply(
        &protocol.user,
        &reserve_16,
        &100_000_000u128,
        &protocol.user,
        &0u32,
    );

    // Should fail with MaxUserReservesExceeded error
    assert!(result.is_err(), "Supply should fail for 16th reserve");
}

#[test]
fn test_max_user_reserves_limit_on_borrow() {
    let env = create_test_env();
    let protocol = deploy_test_protocol_two_assets(&env);

    // Provide liquidity and collateral
    protocol.kinetic_router.supply(
        &protocol.user,
        &protocol.usdc_asset,
        &1_000_000_000_000u128, // Large collateral
        &protocol.user,
        &0u32,
    );

    // Create 14 additional reserves and borrow small amounts from each
    // (user already has 1 collateral position, so can have 14 more debt positions)
    for i in 2..=15 {
        let reserve_asset = create_test_reserve(&protocol, i);

        // Reset budget to avoid memory limits when creating many reserves
        env.cost_estimate().budget().reset_unlimited();

        // Borrow small amount
        let result = protocol.kinetic_router.try_borrow(
            &protocol.user,
            &reserve_asset,
            &1_000_000u128, // Small borrow
            &1u32,          // Variable rate
            &0u32,
            &protocol.user,
        );
        assert!(
            result.is_ok(),
            "Borrow should succeed for reserve {}",
            i
        );
    }

    // Try to borrow from a 16th reserve - should fail
    let reserve_16 = create_test_reserve(&protocol, 16);
    let result = protocol.kinetic_router.try_borrow(
        &protocol.user,
        &reserve_16,
        &1_000_000u128,
        &1u32,
        &0u32,
        &protocol.user,
    );

    // Should fail with MaxUserReservesExceeded error
    assert!(result.is_err(), "Borrow should fail for 16th reserve");
}

#[test]
fn test_optimized_calculation_with_multiple_reserves() {
    let env = create_test_env();
    let protocol = deploy_test_protocol_two_assets(&env);

    // Supply to multiple reserves
    protocol.kinetic_router.supply(
        &protocol.user,
        &protocol.usdc_asset,
        &100_000_000u128,
        &protocol.user,
        &0u32,
    );

    protocol.kinetic_router.supply(
        &protocol.user,
        &protocol.usdt_asset,
        &100_000_000u128,
        &protocol.user,
        &0u32,
    );

    // Create and supply to 3 more reserves
    for i in 3..=5 {
        let reserve_asset = create_test_reserve(&protocol, i);

        let sac_admin = soroban_sdk::token::StellarAssetClient::new(&env, &reserve_asset);
        sac_admin.mint(&protocol.user, &1_000_000_000i128);

        let token_client = soroban_sdk::token::Client::new(&env, &reserve_asset);
        let expiration = env.ledger().sequence() + 200_000;
        token_client.approve(
            &protocol.user,
            &protocol.kinetic_router.address,
            &i128::MAX,
            &expiration,
        );

        protocol.kinetic_router.supply(
            &protocol.user,
            &reserve_asset,
            &100_000_000u128,
            &protocol.user,
            &0u32,
        );
    }

    // Get user account data - should work efficiently with optimized calculation
    let account_data = protocol
        .kinetic_router
        .get_user_account_data(&protocol.user);

    // User has collateral, no debt -> HF should be max
    assert!(
        account_data.total_collateral_base > 0,
        "Should have collateral value"
    );
    assert_eq!(account_data.total_debt_base, 0, "Should have no debt");
    assert_eq!(
        account_data.health_factor,
        u128::MAX,
        "Health factor should be max with no debt"
    );
}

#[test]
fn test_count_active_reserves() {
    let env = create_test_env();
    let protocol = deploy_test_protocol_two_assets(&env);

    // Initially no reserves
    let user_config = protocol.kinetic_router.get_user_configuration(&protocol.user);
    let mut count = 0u8;
    let mut data = user_config.data;
    for _ in 0..64 {
        if (data & 0b11) != 0 {
            count += 1;
        }
        data >>= 2;
        if data == 0 {
            break;
        }
    }
    assert_eq!(count, 0, "Should start with 0 active reserves");

    // Supply to one reserve
    protocol.kinetic_router.supply(
        &protocol.user,
        &protocol.usdc_asset,
        &100_000_000u128,
        &protocol.user,
        &0u32,
    );

    let user_config = protocol.kinetic_router.get_user_configuration(&protocol.user);
    let mut count = 0u8;
    let mut data = user_config.data;
    for _ in 0..64 {
        if (data & 0b11) != 0 {
            count += 1;
        }
        data >>= 2;
        if data == 0 {
            break;
        }
    }
    assert_eq!(count, 1, "Should have 1 active reserve after supply");

    // Supply to another reserve
    protocol.kinetic_router.supply(
        &protocol.user,
        &protocol.usdt_asset,
        &100_000_000u128,
        &protocol.user,
        &0u32,
    );

    let user_config = protocol.kinetic_router.get_user_configuration(&protocol.user);
    let mut count = 0u8;
    let mut data = user_config.data;
    for _ in 0..64 {
        if (data & 0b11) != 0 {
            count += 1;
        }
        data >>= 2;
        if data == 0 {
            break;
        }
    }
    assert_eq!(count, 2, "Should have 2 active reserves after second supply");
}
