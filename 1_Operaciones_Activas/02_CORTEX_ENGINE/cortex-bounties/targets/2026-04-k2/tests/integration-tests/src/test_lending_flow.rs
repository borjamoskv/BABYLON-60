#![cfg(test)]

use crate::setup::deploy_test_protocol;
use soroban_sdk::{
    testutils::{MockAuth, MockAuthInvoke},
    Env, IntoVal,
};

#[test]
fn test_supply_and_withdraw() {
    let env = Env::default();
    env.mock_all_auths(); // Mock auths for setup only
    
    let protocol = deploy_test_protocol(&env);
    
    let supply_amount = 1_000_000_000u128;
    let initial_balance = protocol.underlying_asset_client.balance(&protocol.liquidity_provider);
    
    // Supply tokens with specific auth
    env.mock_auths(&[MockAuth {
        address: &protocol.liquidity_provider,
        invoke: &MockAuthInvoke {
            contract: &protocol.kinetic_router_address,
            fn_name: "supply",
            args: (
                &protocol.liquidity_provider,
                &protocol.underlying_asset,
                &supply_amount,
                &protocol.liquidity_provider,
                &0u32,
            )
                .into_val(&env),
            sub_invokes: &[],
        },
    }]);
    
    protocol.kinetic_router.supply(
        &protocol.liquidity_provider,
        &protocol.underlying_asset,
        &supply_amount,
        &protocol.liquidity_provider,
        &0u32,
    );
    
    // Verify auth was checked
    let auths = env.auths();
    assert_eq!(auths.len(), 1);
    assert_eq!(auths[0].0, protocol.liquidity_provider);
    
    // Verify a-token balance matches supply amount (1:1 initially)
    let a_token_balance = protocol.a_token.balance(&protocol.liquidity_provider);
    assert_eq!(a_token_balance, supply_amount as i128, "Should receive exact a-token amount");
    
    // Verify underlying tokens were transferred
    let balance_after_supply = protocol.underlying_asset_client.balance(&protocol.liquidity_provider);
    assert_eq!(
        balance_after_supply, 
        initial_balance - supply_amount as i128,
        "Underlying tokens should be transferred"
    );
    
    // Verify reserve data updated
    let reserve_data_after_supply = protocol.kinetic_router.get_reserve_data(&protocol.underlying_asset);
    assert!(reserve_data_after_supply.liquidity_index > 0, "Liquidity index should be initialized");
    // No borrows yet — liquidity rate should be 0 (no interest earned at 0% utilization)
    assert_eq!(reserve_data_after_supply.current_liquidity_rate, 0, "Liquidity rate should be 0 with no borrows");

    // Withdraw half with specific auth
    let withdraw_amount = supply_amount / 2;
    env.mock_auths(&[MockAuth {
        address: &protocol.liquidity_provider,
        invoke: &MockAuthInvoke {
            contract: &protocol.kinetic_router_address,
            fn_name: "withdraw",
            args: (
                &protocol.liquidity_provider,
                &protocol.underlying_asset,
                &withdraw_amount,
                &protocol.liquidity_provider,
            )
                .into_val(&env),
            sub_invokes: &[],
        },
    }]);
    
    let withdrawn_amount = protocol.kinetic_router.withdraw(
        &protocol.liquidity_provider,
        &protocol.underlying_asset,
        &withdraw_amount,
        &protocol.liquidity_provider,
    );
    
    // Verify auth was checked
    let auths = env.auths();
    assert_eq!(auths.len(), 1);
    assert_eq!(auths[0].0, protocol.liquidity_provider);
    
    // Verify exact amount withdrawn
    assert_eq!(withdrawn_amount, withdraw_amount, "Should withdraw exact requested amount");
    
    // Verify a-tokens were burned proportionally
    let a_token_balance_after = protocol.a_token.balance(&protocol.liquidity_provider);
    assert_eq!(
        a_token_balance_after,
        (supply_amount - withdraw_amount) as i128,
        "A-tokens should be burned exactly by withdraw amount"
    );
    
    // Verify underlying tokens were received
    let final_balance = protocol.underlying_asset_client.balance(&protocol.liquidity_provider);
    assert_eq!(
        final_balance,
        balance_after_supply + withdraw_amount as i128,
        "Should receive exact withdrawn tokens"
    );
    
    // Verify reserve liquidity decreased
    let reserve_data_after_withdraw = protocol.kinetic_router.get_reserve_data(&protocol.underlying_asset);
    assert_eq!(
        reserve_data_after_withdraw.liquidity_index,
        reserve_data_after_supply.liquidity_index,
        "Liquidity index should remain unchanged (no interest accrued yet)"
    );
}

#[test]
fn test_borrow_and_repay() {
    let env = Env::default();
    env.mock_all_auths(); // Mock auths for setup only
    
    let protocol = deploy_test_protocol(&env);
    
    let liquidity_amount = 20_000_000_000u128; // Liquidity provider supplies to pool
    let collateral_amount = 10_000_000_000u128; // User supplies as collateral
    let borrow_amount = 1_000_000_000u128;
    
    let initial_balance = protocol.underlying_asset_client.balance(&protocol.user);
    
    // Liquidity provider supplies to pool (creates pool liquidity for borrowing)
    env.mock_auths(&[MockAuth {
        address: &protocol.liquidity_provider,
        invoke: &MockAuthInvoke {
            contract: &protocol.kinetic_router_address,
            fn_name: "supply",
            args: (
                &protocol.liquidity_provider,
                &protocol.underlying_asset,
                &liquidity_amount,
                &protocol.liquidity_provider,
                &0u32,
            )
                .into_val(&env),
            sub_invokes: &[],
        },
    }]);
    protocol.kinetic_router.supply(
        &protocol.liquidity_provider,
        &protocol.underlying_asset,
        &liquidity_amount,
        &protocol.liquidity_provider,
        &0u32,
    );
    
    // User supplies collateral (separate from pool liquidity)
    env.mock_auths(&[MockAuth {
        address: &protocol.user,
        invoke: &MockAuthInvoke {
            contract: &protocol.kinetic_router_address,
            fn_name: "supply",
            args: (
                &protocol.user,
                &protocol.underlying_asset,
                &collateral_amount,
                &protocol.user,
                &0u32,
            )
                .into_val(&env),
            sub_invokes: &[],
        },
    }]);
    protocol.kinetic_router.supply(
        &protocol.user,
        &protocol.underlying_asset,
        &collateral_amount,
        &protocol.user,
        &0u32,
    );
    
    // Enable reserve as collateral
    env.mock_auths(&[MockAuth {
        address: &protocol.user,
        invoke: &MockAuthInvoke {
            contract: &protocol.kinetic_router_address,
            fn_name: "set_user_use_reserve_as_coll",
            args: (
                &protocol.user,
                &protocol.underlying_asset,
                &true,
            )
                .into_val(&env),
            sub_invokes: &[],
        },
    }]);
    protocol.kinetic_router.set_user_use_reserve_as_coll(
        &protocol.user,
        &protocol.underlying_asset,
        &true,
    );
    
    // Verify user configuration
    let user_config = protocol.kinetic_router.get_user_configuration(&protocol.user);
    assert!(user_config.data != 0, "Should be using collateral");
    
    // Get initial account data
    let account_data_before = protocol.kinetic_router.get_user_account_data(&protocol.user);
    assert_eq!(account_data_before.total_debt_base, 0, "Should have no debt initially");
    assert!(account_data_before.total_collateral_base > 0, "Should have collateral");
    assert!(account_data_before.health_factor > 1_000_000_000_000_000_000u128, "Health factor should be very high with no debt");
    assert!(account_data_before.available_borrows_base > 0, "Should have available borrows");
    
    // Store health factor before borrowing
    let health_factor_before = account_data_before.health_factor;
    
    // Borrow with specific auth
    env.mock_auths(&[MockAuth {
        address: &protocol.user,
        invoke: &MockAuthInvoke {
            contract: &protocol.kinetic_router_address,
            fn_name: "borrow",
            args: (
                &protocol.user,
                &protocol.underlying_asset,
                &borrow_amount,
                &1u32,
                &0u32,
                &protocol.user,
            )
                .into_val(&env),
            sub_invokes: &[],
        },
    }]);
    protocol.kinetic_router.borrow(
        &protocol.user,
        &protocol.underlying_asset,
        &borrow_amount,
        &1u32, // Variable rate (mode 1)
        &0u32,
        &protocol.user,
    );
    
    // Verify auth was checked
    let auths = env.auths();
    assert_eq!(auths.len(), 1);
    assert_eq!(auths[0].0, protocol.user);
    
    // Verify borrowed tokens received exactly
    let balance_after_borrow = protocol.underlying_asset_client.balance(&protocol.user);
    assert_eq!(
        balance_after_borrow,
        initial_balance - collateral_amount as i128 + borrow_amount as i128,
        "Should receive exact borrowed amount"
    );
    
    // Verify debt tokens minted exactly
    let debt_balance = protocol.debt_token.balance(&protocol.user);
    assert_eq!(debt_balance, borrow_amount as i128, "Debt tokens should be minted exactly");
    
    // Verify account data shows debt
    let account_data_after_borrow = protocol.kinetic_router.get_user_account_data(&protocol.user);
    assert!(account_data_after_borrow.total_debt_base > 0, "Total debt should be positive");
    assert!(account_data_after_borrow.total_debt_base >= borrow_amount, "Total debt should be at least borrow amount (may include scaling)");
    assert!(account_data_after_borrow.total_collateral_base > 0, "Should still have collateral");
    assert!(account_data_after_borrow.health_factor > 0, "Health factor should be positive");
    assert!(account_data_after_borrow.health_factor < health_factor_before, "Health factor should decrease after borrowing");
    assert!(account_data_after_borrow.available_borrows_base < account_data_before.available_borrows_base, "Available borrows should decrease");
    
    // Store health factor before repaying
    let health_factor_before_repay = account_data_after_borrow.health_factor;
    
    // Repay with specific auth
    env.mock_auths(&[MockAuth {
        address: &protocol.user,
        invoke: &MockAuthInvoke {
            contract: &protocol.kinetic_router_address,
            fn_name: "repay",
            args: (
                &protocol.user,
                &protocol.underlying_asset,
                &borrow_amount,
                &1u32,
                &protocol.user,
            )
                .into_val(&env),
            sub_invokes: &[],
        },
    }]);
    let repaid_amount = protocol.kinetic_router.repay(
        &protocol.user,
        &protocol.underlying_asset,
        &borrow_amount,
        &1u32,
        &protocol.user,
    );
    
    // Verify auth was checked
    let auths = env.auths();
    assert_eq!(auths.len(), 1);
    assert_eq!(auths[0].0, protocol.user);
    
    // Verify exact amount repaid
    assert_eq!(repaid_amount, borrow_amount, "Should repay exact requested amount");
    
    // Verify debt tokens burned completely
    let debt_balance_after = protocol.debt_token.balance(&protocol.user);
    assert_eq!(debt_balance_after, 0, "Debt tokens should be completely burned");
    
    // Verify account data shows no debt
    let account_data_after_repay = protocol.kinetic_router.get_user_account_data(&protocol.user);
    assert_eq!(account_data_after_repay.total_debt_base, 0, "Should have no debt after repay");
    assert!(account_data_after_repay.total_collateral_base > 0, "Should still have collateral");
    assert!(account_data_after_repay.health_factor > health_factor_before_repay, "Health factor should increase after repaying");
    assert!(account_data_after_repay.available_borrows_base > account_data_after_borrow.available_borrows_base, "Available borrows should increase after repay");
    
    // Verify balance decreased by repay amount
    let balance_after_repay = protocol.underlying_asset_client.balance(&protocol.user);
    assert_eq!(
        balance_after_repay,
        balance_after_borrow - borrow_amount as i128,
        "Balance should decrease by exact repay amount"
    );
}

#[test]
fn test_full_lending_cycle() {
    let env = Env::default();
    env.mock_all_auths();
    
    let protocol = deploy_test_protocol(&env);
    
    let supply_amount = 10_000_000_000u128;
    
    // Get initial reserve data
    let reserve_data_before = protocol.kinetic_router.get_reserve_data(&protocol.underlying_asset);
    let initial_liquidity_index = reserve_data_before.liquidity_index;
    
    // User supplies
    protocol.kinetic_router.supply(
        &protocol.user,
        &protocol.underlying_asset,
        &supply_amount,
        &protocol.user,
        &0u32,
    );
    
    // Verify reserve data updated
    let reserve_data = protocol.kinetic_router.get_reserve_data(&protocol.underlying_asset);
    assert_eq!(reserve_data.liquidity_index, initial_liquidity_index, "Liquidity index should not change on first supply");
    assert!((reserve_data.configuration.data_low >> 50) & 1 == 1, "Reserve should be active");
    assert!((reserve_data.configuration.data_low >> 52) & 1 == 1, "Borrowing should be enabled");
    assert_eq!(reserve_data.a_token_address, protocol.a_token.address, "A-token address should match");
    assert_eq!(reserve_data.debt_token_address, protocol.debt_token.address, "Debt token address should match");
    
    // Verify user account data
    let account_data = protocol.kinetic_router.get_user_account_data(&protocol.user);
    assert!(account_data.total_collateral_base > 0, "Should have collateral");
    assert_eq!(account_data.total_debt_base, 0, "Should have no debt");
    assert!(account_data.health_factor > 1_000_000_000_000_000_000u128, "Health factor should be very high with no debt");
    assert!(account_data.available_borrows_base > 0, "Should have available borrows");
    assert!(account_data.current_liquidation_threshold > 0, "Liquidation threshold should be set based on reserve config");
    
    // Verify reserves list
    let reserves_list = protocol.kinetic_router.get_reserves_list();
    assert_eq!(reserves_list.len(), 1, "Should have exactly one reserve");
    assert_eq!(reserves_list.get(0).unwrap(), protocol.underlying_asset, "Reserve should be in list");
    
    // Verify utilization rate is 0 (no borrows) via liquidity rate
    let reserve_data = protocol.kinetic_router.get_reserve_data(&protocol.underlying_asset);
    assert_eq!(reserve_data.current_liquidity_rate, 0, "Liquidity rate should be 0 with no borrows (0% utilization)");

    // Verify collateral value matches supply (via get_user_account_data)
    assert!(account_data.total_collateral_base > 0, "Collateral value should be positive");
    // Collateral value is scaled by 1e12 (WAD/1e6) to convert to base units
    let expected_collateral_value = supply_amount.checked_mul(1_000_000_000_000u128).unwrap();
    assert_eq!(account_data.total_collateral_base, expected_collateral_value, "Collateral value should equal supply amount scaled by 1e12. Expected: {}, Got: {}", expected_collateral_value, account_data.total_collateral_base);
}

#[test]
fn test_supply_increases_liquidity() {
    let env = Env::default();
    env.mock_all_auths();
    
    let protocol = deploy_test_protocol(&env);
    
    let first_supply = 5_000_000_000u128;
    let second_supply = 3_000_000_000u128;
    
    // First supply
    protocol.kinetic_router.supply(
        &protocol.liquidity_provider,
        &protocol.underlying_asset,
        &first_supply,
        &protocol.liquidity_provider,
        &0u32,
    );
    
    let balance_after_first = protocol.a_token.balance(&protocol.liquidity_provider);
    assert_eq!(balance_after_first, first_supply as i128);
    
    // Second supply
    protocol.kinetic_router.supply(
        &protocol.liquidity_provider,
        &protocol.underlying_asset,
        &second_supply,
        &protocol.liquidity_provider,
        &0u32,
    );
    
    let balance_after_second = protocol.a_token.balance(&protocol.liquidity_provider);
    assert_eq!(
        balance_after_second,
        (first_supply + second_supply) as i128,
        "A-token balance should accumulate"
    );
}

#[test]
fn test_cannot_borrow_without_collateral() {
    let env = Env::default();
    env.mock_all_auths();
    
    let protocol = deploy_test_protocol(&env);
    
    let borrow_amount = 1_000_000_000u128;
    
    // Try to borrow without any collateral
    let result = protocol.kinetic_router.try_borrow(
        &protocol.user,
        &protocol.underlying_asset,
        &borrow_amount,
        &1u32,
        &0u32,
        &protocol.user,
    );
    
    assert!(result.is_err(), "Should not be able to borrow without collateral");
}

#[test]
fn test_cannot_withdraw_more_than_supplied() {
    let env = Env::default();
    env.mock_all_auths();
    
    let protocol = deploy_test_protocol(&env);
    
    let supply_amount = 1_000_000_000u128;
    
    // Supply
    protocol.kinetic_router.supply(
        &protocol.user,
        &protocol.underlying_asset,
        &supply_amount,
        &protocol.user,
        &0u32,
    );
    
    // Try to withdraw more than supplied
    let result = protocol.kinetic_router.try_withdraw(
        &protocol.user,
        &protocol.underlying_asset,
        &(supply_amount * 2),
        &protocol.user,
    );
    
    assert!(result.is_err(), "Should not be able to withdraw more than supplied");
}
