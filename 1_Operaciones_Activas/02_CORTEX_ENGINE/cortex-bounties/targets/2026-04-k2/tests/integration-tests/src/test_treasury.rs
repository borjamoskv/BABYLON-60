#![cfg(test)]

use crate::interest_rate_strategy;
use crate::price_oracle;
use crate::setup::{create_test_token, deploy_full_protocol, set_default_ledger};
use crate::treasury;
use soroban_sdk::{testutils::Address as _, testutils::Ledger, token, Address, Env};

#[test]
fn test_treasury_get_admin() {
    let env = Env::default();
    env.mock_all_auths();

    let admin = Address::generate(&env);
    let emergency_admin = Address::generate(&env);
    let protocol = deploy_full_protocol(&env, &admin, &emergency_admin);

    let treasury_client = treasury::Client::new(&env, &protocol.treasury);
    let treasury_admin_before = treasury_client.get_admin();

    assert_eq!(
        treasury_admin_before, admin,
        "Treasury admin must match deployment admin exactly. Expected: {:?}, Got: {:?}",
        admin, treasury_admin_before
    );

    // Test that admin remains consistent after balance query operation
    let test_asset = Address::generate(&env);
    let _ = treasury_client.get_balance(&test_asset);

    let treasury_admin_after = treasury_client.get_admin();
    assert_eq!(
        treasury_admin_after, treasury_admin_before,
        "Treasury admin must remain unchanged after balance query. Expected: {:?}, Got: {:?}",
        treasury_admin_before, treasury_admin_after
    );
}

#[test]
fn test_treasury_get_balance() {
    let env = Env::default();
    env.mock_all_auths();

    let admin = Address::generate(&env);
    let emergency_admin = Address::generate(&env);
    let protocol = deploy_full_protocol(&env, &admin, &emergency_admin);

    let treasury_client = treasury::Client::new(&env, &protocol.treasury);
    let test_asset = Address::generate(&env);

    let balance_before = treasury_client.get_balance(&test_asset);
    assert_eq!(
        balance_before, 0u128,
        "Treasury balance must be exactly zero for unregistered asset. Expected: 0, Got: {}",
        balance_before
    );

    // Test that balance remains consistent after querying all balances
    let _ = treasury_client.get_all_balances();

    let balance_after = treasury_client.get_balance(&test_asset);
    assert_eq!(
        balance_after, balance_before,
        "Treasury balance must remain unchanged after querying all balances. Expected: {}, Got: {}",
        balance_before, balance_after
    );

    let different_asset = Address::generate(&env);
    let balance_different = treasury_client.get_balance(&different_asset);
    assert_eq!(balance_different, 0u128, "Treasury balance must be exactly zero for different unregistered asset. Expected: 0, Got: {}", balance_different);
}

#[test]
fn test_treasury_get_all_balances() {
    let env = Env::default();
    env.mock_all_auths();

    let admin = Address::generate(&env);
    let emergency_admin = Address::generate(&env);
    let protocol = deploy_full_protocol(&env, &admin, &emergency_admin);

    let treasury_client = treasury::Client::new(&env, &protocol.treasury);

    let balances = treasury_client.get_all_balances();
    assert_eq!(
        balances.len(),
        0u32,
        "Treasury balances map must be empty initially. Expected: 0, Got: {} assets",
        balances.len()
    );

    let balances_second = treasury_client.get_all_balances();
    assert_eq!(balances.len(), balances_second.len(), "Treasury balances map length must be consistent across calls. First: {} assets, Second: {} assets", balances.len(), balances_second.len());

    let test_asset = Address::generate(&env);
    let balance_from_map = balances.get(test_asset.clone());
    assert_eq!(
        balance_from_map, None,
        "Balance for unregistered asset must be None. Got: {:?}",
        balance_from_map
    );

    let balance_from_map_second = balances_second.get(test_asset);
    assert_eq!(
        balance_from_map, balance_from_map_second,
        "Balance consistency check for unregistered asset. First: {:?}, Second: {:?}",
        balance_from_map, balance_from_map_second
    );
}

#[test]
fn test_treasury_deposit() {
    let env = Env::default();
    env.mock_all_auths();

    let admin = Address::generate(&env);
    let emergency_admin = Address::generate(&env);
    let protocol = deploy_full_protocol(&env, &admin, &emergency_admin);

    let treasury_client = treasury::Client::new(&env, &protocol.treasury);
    let token = create_test_token(&env, &protocol.treasury);
    let token_address = token.address();
    let depositor = Address::generate(&env);
    let deposit_amount = 1_000_000_000u128;

    let balance_before = treasury_client.get_balance(&token_address);
    assert_eq!(
        balance_before, 0u128,
        "Balance must be zero before deposit. Expected: 0, Got: {}",
        balance_before
    );

    let token_sac_client = token::StellarAssetClient::new(&env, &token_address);
    token_sac_client.mint(&depositor, &(deposit_amount as i128));
    let token_client = token::Client::new(&env, &token_address);
    token_client.transfer(&depositor, &protocol.treasury, &(deposit_amount as i128));

    treasury_client.deposit(&admin, &token_address, &deposit_amount, &depositor);

    let balance_after = treasury_client.get_balance(&token_address);
    assert_eq!(
        balance_after, deposit_amount,
        "Balance must equal deposit amount after deposit. Expected: {}, Got: {}",
        deposit_amount, balance_after
    );

    // Verify internal accounting matches actual token balance
    let actual_token_balance = token_client.balance(&protocol.treasury) as u128;
    assert_eq!(
        balance_after, actual_token_balance,
        "Internal accounting must match actual token balance. Internal: {}, Actual: {}",
        balance_after, actual_token_balance
    );

    let balances_map = treasury_client.get_all_balances();
    assert_eq!(
        balances_map.len(),
        1u32,
        "Balances map must contain exactly one asset after deposit. Expected: 1, Got: {}",
        balances_map.len()
    );
    let balance_from_map = balances_map.get(token_address.clone()).unwrap();
    assert_eq!(
        balance_from_map, deposit_amount,
        "Balance from map must match deposit amount. Expected: {}, Got: {}",
        deposit_amount, balance_from_map
    );

    let second_deposit_amount = 500_000_000u128;
    token_sac_client.mint(&depositor, &(second_deposit_amount as i128));
    token_client.transfer(
        &depositor,
        &protocol.treasury,
        &(second_deposit_amount as i128),
    );

    treasury_client.deposit(&admin, &token_address, &second_deposit_amount, &depositor);

    let balance_after_second = treasury_client.get_balance(&token_address);
    let expected_total = deposit_amount + second_deposit_amount;
    assert_eq!(
        balance_after_second, expected_total,
        "Balance must equal sum of all deposits. Expected: {}, Got: {}",
        expected_total, balance_after_second
    );

    // Verify internal accounting matches actual token balance after second deposit
    let actual_token_balance_after_second = token_client.balance(&protocol.treasury) as u128;
    assert_eq!(balance_after_second, actual_token_balance_after_second, "Internal accounting must match actual token balance after second deposit. Internal: {}, Actual: {}", balance_after_second, actual_token_balance_after_second);
}

#[test]
fn test_treasury_deposit_zero_amount_fails() {
    let env = Env::default();
    env.mock_all_auths();

    let admin = Address::generate(&env);
    let emergency_admin = Address::generate(&env);
    let protocol = deploy_full_protocol(&env, &admin, &emergency_admin);

    let treasury_client = treasury::Client::new(&env, &protocol.treasury);
    let token = create_test_token(&env, &protocol.treasury);
    let token_address = token.address();
    let depositor = Address::generate(&env);

    let result = treasury_client.try_deposit(&admin, &token_address, &0u128, &depositor);
    assert!(
        result.is_err(),
        "Deposit with zero amount must fail. Result: {:?}",
        result
    );
}

#[test]
fn test_treasury_withdraw() {
    let env = Env::default();
    env.mock_all_auths();

    let admin = Address::generate(&env);
    let emergency_admin = Address::generate(&env);
    let protocol = deploy_full_protocol(&env, &admin, &emergency_admin);

    let treasury_client = treasury::Client::new(&env, &protocol.treasury);
    let token = create_test_token(&env, &protocol.treasury);
    let token_address = token.address();
    let depositor = Address::generate(&env);
    let recipient = Address::generate(&env);
    let deposit_amount = 1_000_000_000u128;
    let withdraw_amount = 600_000_000u128;

    let token_sac_client = token::StellarAssetClient::new(&env, &token_address);
    token_sac_client.mint(&depositor, &(deposit_amount as i128));
    let token_client = token::Client::new(&env, &token_address);
    token_client.transfer(&depositor, &protocol.treasury, &(deposit_amount as i128));

    treasury_client.deposit(&admin, &token_address, &deposit_amount, &depositor);

    let balance_before_withdraw = treasury_client.get_balance(&token_address);
    assert_eq!(
        balance_before_withdraw, deposit_amount,
        "Balance before withdraw must equal deposit. Expected: {}, Got: {}",
        deposit_amount, balance_before_withdraw
    );

    treasury_client.withdraw(&admin, &token_address, &withdraw_amount, &recipient);

    let balance_after_withdraw = treasury_client.get_balance(&token_address);
    let expected_balance = deposit_amount - withdraw_amount;
    assert_eq!(
        balance_after_withdraw, expected_balance,
        "Balance after withdraw must equal deposit minus withdrawal. Expected: {}, Got: {}",
        expected_balance, balance_after_withdraw
    );

    let recipient_balance = token_client.balance(&recipient);
    assert_eq!(
        recipient_balance, withdraw_amount as i128,
        "Recipient balance must equal withdrawal amount. Expected: {}, Got: {}",
        withdraw_amount, recipient_balance
    );

    let treasury_balance = token_client.balance(&protocol.treasury);
    assert_eq!(
        treasury_balance, expected_balance as i128,
        "Treasury token balance must match internal balance. Expected: {}, Got: {}",
        expected_balance, treasury_balance
    );
}

#[test]
fn test_treasury_withdraw_unauthorized_fails() {
    let env = Env::default();
    env.mock_all_auths();

    let admin = Address::generate(&env);
    let emergency_admin = Address::generate(&env);
    let protocol = deploy_full_protocol(&env, &admin, &emergency_admin);

    let treasury_client = treasury::Client::new(&env, &protocol.treasury);
    let token = create_test_token(&env, &protocol.treasury);
    let token_address = token.address();
    let depositor = Address::generate(&env);
    let unauthorized = Address::generate(&env);
    let recipient = Address::generate(&env);
    let deposit_amount = 1_000_000_000u128;
    let withdraw_amount = 500_000_000u128;

    let token_sac_client = token::StellarAssetClient::new(&env, &token_address);
    token_sac_client.mint(&depositor, &(deposit_amount as i128));
    let token_client = token::Client::new(&env, &token_address);
    token_client.transfer(&depositor, &protocol.treasury, &(deposit_amount as i128));

    treasury_client.deposit(&admin, &token_address, &deposit_amount, &depositor);

    let result =
        treasury_client.try_withdraw(&unauthorized, &token_address, &withdraw_amount, &recipient);
    assert!(
        result.is_err(),
        "Withdraw by unauthorized address must fail. Result: {:?}",
        result
    );

    let balance_after_failed_withdraw = treasury_client.get_balance(&token_address);
    assert_eq!(
        balance_after_failed_withdraw, deposit_amount,
        "Balance must remain unchanged after failed withdraw. Expected: {}, Got: {}",
        deposit_amount, balance_after_failed_withdraw
    );
}

#[test]
fn test_treasury_withdraw_insufficient_balance_fails() {
    let env = Env::default();
    env.mock_all_auths();

    let admin = Address::generate(&env);
    let emergency_admin = Address::generate(&env);
    let protocol = deploy_full_protocol(&env, &admin, &emergency_admin);

    let treasury_client = treasury::Client::new(&env, &protocol.treasury);
    let token = create_test_token(&env, &protocol.treasury);
    let token_address = token.address();
    let depositor = Address::generate(&env);
    let recipient = Address::generate(&env);
    let deposit_amount = 1_000_000_000u128;
    let excessive_withdraw_amount = 2_000_000_000u128;

    let token_sac_client = token::StellarAssetClient::new(&env, &token_address);
    token_sac_client.mint(&depositor, &(deposit_amount as i128));
    let token_client = token::Client::new(&env, &token_address);
    token_client.transfer(&depositor, &protocol.treasury, &(deposit_amount as i128));

    treasury_client.deposit(&admin, &token_address, &deposit_amount, &depositor);

    let result = treasury_client.try_withdraw(
        &admin,
        &token_address,
        &excessive_withdraw_amount,
        &recipient,
    );
    assert!(
        result.is_err(),
        "Withdraw exceeding balance must fail. Result: {:?}",
        result
    );

    let balance_after_failed_withdraw = treasury_client.get_balance(&token_address);
    assert_eq!(
        balance_after_failed_withdraw, deposit_amount,
        "Balance must remain unchanged after failed withdraw. Expected: {}, Got: {}",
        deposit_amount, balance_after_failed_withdraw
    );
}

#[test]
fn test_treasury_withdraw_zero_amount_fails() {
    let env = Env::default();
    env.mock_all_auths();

    let admin = Address::generate(&env);
    let emergency_admin = Address::generate(&env);
    let protocol = deploy_full_protocol(&env, &admin, &emergency_admin);

    let treasury_client = treasury::Client::new(&env, &protocol.treasury);
    let token = create_test_token(&env, &protocol.treasury);
    let token_address = token.address();
    let depositor = Address::generate(&env);
    let recipient = Address::generate(&env);
    let deposit_amount = 1_000_000_000u128;

    let token_sac_client = token::StellarAssetClient::new(&env, &token_address);
    token_sac_client.mint(&depositor, &(deposit_amount as i128));
    let token_client = token::Client::new(&env, &token_address);
    token_client.transfer(&depositor, &protocol.treasury, &(deposit_amount as i128));

    treasury_client.deposit(&admin, &token_address, &deposit_amount, &depositor);

    let result = treasury_client.try_withdraw(&admin, &token_address, &0u128, &recipient);
    assert!(
        result.is_err(),
        "Withdraw with zero amount must fail. Result: {:?}",
        result
    );

    let balance_after_failed_withdraw = treasury_client.get_balance(&token_address);
    assert_eq!(
        balance_after_failed_withdraw, deposit_amount,
        "Balance must remain unchanged after failed withdraw. Expected: {}, Got: {}",
        deposit_amount, balance_after_failed_withdraw
    );
}

#[test]
fn test_treasury_sync_balance() {
    let env = Env::default();
    env.mock_all_auths();

    let admin = Address::generate(&env);
    let emergency_admin = Address::generate(&env);
    let protocol = deploy_full_protocol(&env, &admin, &emergency_admin);

    let treasury_client = treasury::Client::new(&env, &protocol.treasury);
    let token = create_test_token(&env, &protocol.treasury);
    let token_address = token.address();
    let depositor = Address::generate(&env);
    let direct_transfer_amount = 1_500_000_000u128;

    let token_sac_client = token::StellarAssetClient::new(&env, &token_address);
    token_sac_client.mint(&depositor, &(direct_transfer_amount as i128));

    let balance_before_sync = treasury_client.get_balance(&token_address);
    assert_eq!(
        balance_before_sync, 0u128,
        "Balance before sync must be zero. Expected: 0, Got: {}",
        balance_before_sync
    );

    let token_client = token::Client::new(&env, &token_address);
    token_client.transfer(
        &depositor,
        &protocol.treasury,
        &(direct_transfer_amount as i128),
    );

    let synced_balance = treasury_client.sync_balance(&token_address);
    assert_eq!(
        synced_balance, direct_transfer_amount,
        "Synced balance must equal transferred amount. Expected: {}, Got: {}",
        direct_transfer_amount, synced_balance
    );

    let balance_after_sync = treasury_client.get_balance(&token_address);
    assert_eq!(
        balance_after_sync, direct_transfer_amount,
        "Balance after sync must equal transferred amount. Expected: {}, Got: {}",
        direct_transfer_amount, balance_after_sync
    );
    assert_eq!(
        balance_after_sync, synced_balance,
        "Balance after sync must equal synced balance. Expected: {}, Got: {}",
        synced_balance, balance_after_sync
    );

    // Verify internal accounting matches actual token balance after sync
    let actual_token_balance = token_client.balance(&protocol.treasury) as u128;
    assert_eq!(
        balance_after_sync, actual_token_balance,
        "Internal accounting must match actual token balance after sync. Internal: {}, Actual: {}",
        balance_after_sync, actual_token_balance
    );

    let balances_map = treasury_client.get_all_balances();
    let balance_from_map = balances_map.get(token_address.clone()).unwrap();
    assert_eq!(
        balance_from_map, direct_transfer_amount,
        "Balance from map must equal synced amount. Expected: {}, Got: {}",
        direct_transfer_amount, balance_from_map
    );
}

#[test]
fn test_treasury_multiple_assets() {
    let env = Env::default();
    env.mock_all_auths();

    let admin = Address::generate(&env);
    let emergency_admin = Address::generate(&env);
    let protocol = deploy_full_protocol(&env, &admin, &emergency_admin);

    let treasury_client = treasury::Client::new(&env, &protocol.treasury);
    let token1 = create_test_token(&env, &admin);
    let token1_address = token1.address();
    let token2 = create_test_token(&env, &admin);
    let token2_address = token2.address();
    let depositor = Address::generate(&env);
    let deposit1_amount = 1_000_000_000u128;
    let deposit2_amount = 2_000_000_000u128;

    let token1_sac_client = token::StellarAssetClient::new(&env, &token1_address);
    let token2_sac_client = token::StellarAssetClient::new(&env, &token2_address);
    token1_sac_client.mint(&depositor, &(deposit1_amount as i128));
    token2_sac_client.mint(&depositor, &(deposit2_amount as i128));

    let token1_client = token::Client::new(&env, &token1_address);
    let token2_client = token::Client::new(&env, &token2_address);
    token1_client.transfer(&depositor, &protocol.treasury, &(deposit1_amount as i128));
    token2_client.transfer(&depositor, &protocol.treasury, &(deposit2_amount as i128));

    treasury_client.deposit(&admin, &token1_address, &deposit1_amount, &depositor);
    treasury_client.deposit(&admin, &token2_address, &deposit2_amount, &depositor);

    let balance1 = treasury_client.get_balance(&token1_address);
    let balance2 = treasury_client.get_balance(&token2_address);

    assert_eq!(
        balance1, deposit1_amount,
        "Token1 balance must equal deposit. Expected: {}, Got: {}",
        deposit1_amount, balance1
    );
    assert_eq!(
        balance2, deposit2_amount,
        "Token2 balance must equal deposit. Expected: {}, Got: {}",
        deposit2_amount, balance2
    );

    // Verify internal accounting matches actual token balances
    let actual_token1_balance = token1_client.balance(&protocol.treasury) as u128;
    let actual_token2_balance = token2_client.balance(&protocol.treasury) as u128;
    assert_eq!(
        balance1, actual_token1_balance,
        "Token1 internal accounting must match actual token balance. Internal: {}, Actual: {}",
        balance1, actual_token1_balance
    );
    assert_eq!(
        balance2, actual_token2_balance,
        "Token2 internal accounting must match actual token balance. Internal: {}, Actual: {}",
        balance2, actual_token2_balance
    );

    let balances_map = treasury_client.get_all_balances();
    assert_eq!(
        balances_map.len(),
        2u32,
        "Balances map must contain exactly two assets. Expected: 2, Got: {}",
        balances_map.len()
    );

    let balance1_from_map = balances_map.get(token1_address.clone()).unwrap();
    let balance2_from_map = balances_map.get(token2_address.clone()).unwrap();

    assert_eq!(
        balance1_from_map, deposit1_amount,
        "Token1 balance from map must equal deposit. Expected: {}, Got: {}",
        deposit1_amount, balance1_from_map
    );
    assert_eq!(
        balance2_from_map, deposit2_amount,
        "Token2 balance from map must equal deposit. Expected: {}, Got: {}",
        deposit2_amount, balance2_from_map
    );
}

#[test]
fn test_treasury_withdraw_limit_enforcement() {
    let env = Env::default();
    env.mock_all_auths();

    let admin = Address::generate(&env);
    let emergency_admin = Address::generate(&env);
    let protocol = deploy_full_protocol(&env, &admin, &emergency_admin);

    let treasury_client = treasury::Client::new(&env, &protocol.treasury);
    let token = create_test_token(&env, &protocol.treasury);
    let token_address = token.address();
    let depositor = Address::generate(&env);
    let recipient = Address::generate(&env);
    let deposit_amount = 1_000_000_000u128;

    // Deposit tokens
    let token_sac_client = token::StellarAssetClient::new(&env, &token_address);
    token_sac_client.mint(&depositor, &(deposit_amount as i128));
    let token_client = token::Client::new(&env, &token_address);
    token_client.transfer(&depositor, &protocol.treasury, &(deposit_amount as i128));
    treasury_client.deposit(&admin, &token_address, &deposit_amount, &depositor);

    // Test: Cannot withdraw more than balance
    let excessive_amount = deposit_amount + 1u128;
    let result =
        treasury_client.try_withdraw(&admin, &token_address, &excessive_amount, &recipient);
    assert!(result.is_err(), "Withdraw exceeding balance must fail");

    // Verify balance unchanged
    let balance_after_failed = treasury_client.get_balance(&token_address);
    assert_eq!(
        balance_after_failed, deposit_amount,
        "Balance must remain unchanged after failed withdraw"
    );
}

#[test]
fn test_treasury_withdraw_permissions_multiple_admins() {
    let env = Env::default();
    env.mock_all_auths();

    let admin = Address::generate(&env);
    let emergency_admin = Address::generate(&env);
    let protocol = deploy_full_protocol(&env, &admin, &emergency_admin);

    let treasury_client = treasury::Client::new(&env, &protocol.treasury);
    let token = create_test_token(&env, &protocol.treasury);
    let token_address = token.address();
    let depositor = Address::generate(&env);
    let recipient = Address::generate(&env);
    let deposit_amount = 1_000_000_000u128;

    // Deposit tokens
    let token_sac_client = token::StellarAssetClient::new(&env, &token_address);
    token_sac_client.mint(&depositor, &(deposit_amount as i128));
    let token_client = token::Client::new(&env, &token_address);
    token_client.transfer(&depositor, &protocol.treasury, &(deposit_amount as i128));
    treasury_client.deposit(&admin, &token_address, &deposit_amount, &depositor);

    // Test: Only admin can withdraw (not emergency_admin)
    let withdraw_amount = 500_000_000u128;

    // Admin can withdraw
    treasury_client.withdraw(&admin, &token_address, &withdraw_amount, &recipient);
    let balance_after_admin = treasury_client.get_balance(&token_address);
    assert_eq!(
        balance_after_admin,
        deposit_amount - withdraw_amount,
        "Balance should decrease after admin withdraw"
    );

    // Emergency admin cannot withdraw (different from pool admin)
    let result = treasury_client.try_withdraw(
        &emergency_admin,
        &token_address,
        &withdraw_amount,
        &recipient,
    );
    assert!(
        result.is_err(),
        "Emergency admin should not be able to withdraw from treasury"
    );
}

#[test]
fn test_treasury_withdraw_zero_amount_fails_after_init() {
    let env = Env::default();
    env.mock_all_auths();

    let admin = Address::generate(&env);
    let emergency_admin = Address::generate(&env);
    let protocol = deploy_full_protocol(&env, &admin, &emergency_admin);

    let treasury_client = treasury::Client::new(&env, &protocol.treasury);
    let token = create_test_token(&env, &protocol.treasury);
    let token_address = token.address();
    let recipient = Address::generate(&env);

    // Test: Withdraw zero amount fails
    let result = treasury_client.try_withdraw(&admin, &token_address, &0u128, &recipient);
    assert!(result.is_err(), "Withdraw with zero amount must fail");
}

#[test]
fn test_treasury_withdraw_requires_auth() {
    let env = Env::default();
    let admin = Address::generate(&env);
    let emergency_admin = Address::generate(&env);

    // Don't mock all auths - we want to test auth requirement
    env.mock_all_auths();
    let protocol = deploy_full_protocol(&env, &admin, &emergency_admin);

    let treasury_client = treasury::Client::new(&env, &protocol.treasury);
    let token = create_test_token(&env, &protocol.treasury);
    let token_address = token.address();
    let depositor = Address::generate(&env);
    let recipient = Address::generate(&env);
    let deposit_amount = 1_000_000_000u128;

    // Deposit tokens
    let token_sac_client = token::StellarAssetClient::new(&env, &token_address);
    token_sac_client.mint(&depositor, &(deposit_amount as i128));
    let token_client = token::Client::new(&env, &token_address);
    token_client.transfer(&depositor, &protocol.treasury, &(deposit_amount as i128));
    treasury_client.deposit(&admin, &token_address, &deposit_amount, &depositor);

    // Test: Withdraw without auth fails
    env.mock_auths(&[]);
    let result = treasury_client.try_withdraw(&admin, &token_address, &500_000_000u128, &recipient);
    assert!(result.is_err(), "Withdraw without auth must fail");
}

#[test]
fn test_collect_protocol_reserves_and_withdraw() {
    let env = Env::default();
    env.mock_all_auths();
    set_default_ledger(&env);

    // Deploy full protocol with a reserve
    let protocol = crate::setup::deploy_test_protocol(&env);

    // Deploy a new interest rate strategy with much higher rates for faster reserve accrual
    // This will generate significantly more interest and thus more reserves
    let high_rate_strategy_id = env.register(interest_rate_strategy::WASM, ());
    let high_rate_strategy = interest_rate_strategy::Client::new(&env, &high_rate_strategy_id);

    // Initialize with high interest rates:
    // - 10% base rate (vs 2% default)
    // - 100% slope1 (vs 4% default)
    // - 100% slope2 (vs 60% default)
    // - 80% optimal utilization (same)
    let ray = 1_000_000_000_000_000_000_000_000_000u128; // RAY constant
    high_rate_strategy.initialize(
        &protocol.admin,
        &(10 * ray / 100),  // base_variable_borrow_rate: 10%
        &(100 * ray / 100), // variable_rate_slope1: 100%
        &(100 * ray / 100), // variable_rate_slope2: 100%
        &(80 * ray / 100),  // optimal_utilization_rate: 80%
    );

    // Update the reserve to use the high-rate strategy
    protocol.pool_configurator.set_reserve_interest_rate(
        &protocol.admin,
        &protocol.underlying_asset,
        &high_rate_strategy_id,
    );

    // Supply assets to create liquidity
    // First, liquidity provider supplies to create pool liquidity
    let lp_supply = 20_000_000_000u128; // 20M tokens (7 decimals)
    protocol.kinetic_router.supply(
        &protocol.liquidity_provider,
        &protocol.underlying_asset,
        &lp_supply,
        &protocol.liquidity_provider,
        &0u32,
    );

    // User supplies more to have enough collateral for high utilization borrowing
    // Need 40M collateral to borrow 30M (75% of 40M total supply) at 80% LTV
    let user_supply = 40_000_000_000u128; // 40M tokens
    protocol.kinetic_router.supply(
        &protocol.user,
        &protocol.underlying_asset,
        &user_supply,
        &protocol.user,
        &0u32,
    );

    // Enable asset as collateral
    protocol.kinetic_router.set_user_use_reserve_as_coll(
        &protocol.user,
        &protocol.underlying_asset,
        &true,
    );

    // Borrow to create utilization and interest accrual
    // Borrow 30M from total supply of 60M = 50% utilization
    // Higher utilization = higher interest rates = more reserves accumulate
    // At 50% utilization: borrow_rate ≈ 2% + (50%/80%) * 4% = 4.5%
    // Liquidity rate ≈ 4.5% * 50% = 2.25%
    // Reserve accrual ≈ 2.25% * 10% = 0.225% per year
    let borrow_amount = 30_000_000_000u128; // 30M tokens (within 80% LTV of 40M collateral)
    protocol.kinetic_router.borrow(
        &protocol.user,
        &protocol.underlying_asset,
        &borrow_amount,
        &1u32,
        &0u32,
        &protocol.user,
    );

    // Check initial treasury balance (should be 0)
    let treasury_balance_before = protocol.treasury.get_balance(&protocol.underlying_asset);
    assert_eq!(
        treasury_balance_before, 0u128,
        "Treasury should start with 0 balance"
    );

    // Advance time to allow interest to accrue (365 days = 1 year)
    // Longer time period ensures measurable reserves accumulate
    // With high rates (10% base, 100% slope1) at 50% utilization:
    // borrow_rate ≈ 10% + (50%/80%) * 100% = 72.5%
    // Liquidity rate ≈ 72.5% * 50% = 36.25%
    // Reserve accrual ≈ 36.25% * 10% = 3.625% per year
    // Over 1 year: 3.625% of borrowed amount
    // On 30M borrowed: ~1,087,500 tokens should accumulate
    env.ledger().with_mut(|li| {
        li.timestamp += 31_536_000; // 365 days in seconds (1 year)
    });

    // Refresh oracle price after time advance (L-04: overrides expire after 7 days)
    let asset_enum = price_oracle::Asset::Stellar(protocol.underlying_asset.clone());
    protocol.price_oracle.set_manual_override(
        &protocol.admin,
        &asset_enum,
        &Some(1_000_000_000_000_000u128),
        &Some(env.ledger().timestamp() + 604_800),
    );

    // Update reserve state to accrue interest (this calculates and stores the new indices)
    protocol
        .kinetic_router
        .update_reserve_state(&protocol.underlying_asset);

    // Repay a portion of the debt to ensure interest has actually accrued
    // This also triggers state updates and ensures reserves are properly calculated
    // Get current debt amount (principal + accrued interest)
    let user_account_data = protocol
        .kinetic_router
        .get_user_account_data(&protocol.user);
    let current_debt = user_account_data.total_debt_base;

    // Repay a small amount to trigger interest accrual and state update
    // This ensures the interest that has accrued is properly reflected
    if current_debt > borrow_amount {
        // Interest has accrued, repay a small portion to ensure state is updated
        let repay_amount = (current_debt - borrow_amount) / 10; // Repay 10% of accrued interest
        if repay_amount > 0 {
            protocol.kinetic_router.repay(
                &protocol.user,
                &protocol.underlying_asset,
                &repay_amount,
                &1u32,
                &protocol.user,
            );
        }
    }

    // Check protocol reserves before collection
    let reserves_before = protocol
        .kinetic_router
        .get_protocol_reserves(&protocol.underlying_asset);
    assert!(
        reserves_before > 0,
        "Protocol reserves should be positive after interest accrual. Got: {}",
        reserves_before
    );

    // Collect protocol reserves (transfers from aToken to Treasury)
    let collected_amount = protocol
        .kinetic_router
        .collect_protocol_reserves(&protocol.underlying_asset);

    assert!(
        collected_amount > 0,
        "Collected amount should be positive. Got: {}",
        collected_amount
    );
    assert_eq!(
        collected_amount, reserves_before,
        "Collected amount should equal protocol reserves. Expected: {}, Got: {}",
        reserves_before, collected_amount
    );

    // Sync treasury balance to update internal tracking after direct transfer
    let synced_balance = protocol.treasury.sync_balance(&protocol.underlying_asset);
    assert_eq!(
        synced_balance, collected_amount,
        "Synced balance should equal collected amount. Expected: {}, Got: {}",
        collected_amount, synced_balance
    );

    // Verify Treasury balance increased
    let treasury_balance_after_collect = protocol.treasury.get_balance(&protocol.underlying_asset);
    assert_eq!(
        treasury_balance_after_collect, collected_amount,
        "Treasury balance should equal collected amount. Expected: {}, Got: {}",
        collected_amount, treasury_balance_after_collect
    );

    // Verify protocol reserves are now 0 (or very small due to rounding)
    let reserves_after = protocol
        .kinetic_router
        .get_protocol_reserves(&protocol.underlying_asset);
    assert_eq!(
        reserves_after, 0u128,
        "Protocol reserves should be 0 after collection. Got: {}",
        reserves_after
    );

    // Now withdraw from Treasury to a recipient
    let recipient = Address::generate(&env);
    let withdraw_amount = collected_amount / 2; // Withdraw half

    protocol.treasury.withdraw(
        &protocol.admin,
        &protocol.underlying_asset,
        &withdraw_amount,
        &recipient,
    );

    // Verify Treasury balance decreased
    let treasury_balance_after_withdraw = protocol.treasury.get_balance(&protocol.underlying_asset);
    let expected_treasury_balance = collected_amount - withdraw_amount;
    assert_eq!(
        treasury_balance_after_withdraw, expected_treasury_balance,
        "Treasury balance should decrease after withdraw. Expected: {}, Got: {}",
        expected_treasury_balance, treasury_balance_after_withdraw
    );

    // Verify recipient received tokens
    let token_client = soroban_sdk::token::Client::new(&env, &protocol.underlying_asset);
    let recipient_balance = token_client.balance(&recipient);
    assert_eq!(
        recipient_balance, withdraw_amount as i128,
        "Recipient should receive withdrawn amount. Expected: {}, Got: {}",
        withdraw_amount, recipient_balance
    );

    // Verify Treasury token balance matches internal balance
    let treasury_address = protocol.kinetic_router.get_treasury().unwrap();
    let treasury_token_balance = token_client.balance(&treasury_address);
    assert_eq!(
        treasury_token_balance, expected_treasury_balance as i128,
        "Treasury token balance should match internal balance. Expected: {}, Got: {}",
        expected_treasury_balance, treasury_token_balance
    );
}
