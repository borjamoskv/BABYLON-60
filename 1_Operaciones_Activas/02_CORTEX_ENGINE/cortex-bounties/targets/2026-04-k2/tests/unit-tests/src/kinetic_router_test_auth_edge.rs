#![cfg(test)]

//! Phase 3: Authorization & Edge Case Tests
//!
//! Tests for auth enforcement and error paths:
//! G-17: Flash loan premium delivery to treasury
//! G-18: Zero/expired price blocks liquidation
//! G-20: Borrow rejects when insufficient liquidity
//! G-28: Debt ceiling blocks excess borrow
//! M-15: claim_all_rewards capped at 10 assets
//! Paused protocol blocks all operations

use crate::{a_token, debt_token, incentives, interest_rate_strategy, kinetic_router, price_oracle};
use k2_shared::{RAY, WAD};
use soroban_sdk::{
    contract, contractimpl,
    testutils::{Address as _, Ledger, LedgerInfo},
    token, Address, Bytes, Env, IntoVal, Map, String, Symbol, Vec,
};

// =============================================================================
// Mock Contracts
// =============================================================================

#[contract]
pub struct MockReflector;

#[contractimpl]
impl MockReflector {
    pub fn decimals(_env: Env) -> u32 {
        14
    }
}

/// Mock flash loan receiver that correctly repays amount + premium
#[contract]
pub struct MockFlashLoanReceiver;

#[contractimpl]
impl MockFlashLoanReceiver {
    pub fn set_atoken(env: Env, asset: Address, atoken: Address) {
        env.storage().instance().set(&asset, &atoken);
    }

    pub fn execute_operation(
        env: Env,
        assets: Vec<Address>,
        amounts: Vec<u128>,
        premiums: Vec<u128>,
        _initiator: Address,
        _params: Bytes,
    ) -> bool {
        for i in 0..assets.len() {
            let asset = assets.get(i).unwrap();
            let amount = amounts.get(i).unwrap();
            let premium = premiums.get(i).unwrap();
            let total_owed = amount + premium;

            // Get aToken address from storage
            let atoken: Address = env.storage().instance().get(&asset).unwrap();

            // Return total_owed to the aToken contract
            let token_client = token::Client::new(&env, &asset);
            token_client.transfer(
                &env.current_contract_address(),
                &atoken,
                &(total_owed as i128),
            );
        }
        true
    }
}

// =============================================================================
// Setup Helpers (same pattern as Phase 1/2)
// =============================================================================

fn setup_ledger(env: &Env) {
    env.ledger().set(LedgerInfo {
        sequence_number: 100,
        protocol_version: 23,
        timestamp: 1_000_000,
        network_id: Default::default(),
        base_reserve: 10,
        min_temp_entry_ttl: 10,
        min_persistent_entry_ttl: 10,
        max_entry_ttl: 3_000_000,
    });
}

fn setup_interest_rate_strategy(env: &Env, admin: &Address) -> Address {
    let contract_id = env.register(interest_rate_strategy::WASM, ());
    let mut init_args = Vec::new(env);
    init_args.push_back(admin.clone().into_val(env));
    init_args.push_back((0u128).into_val(env));
    init_args.push_back((40_000_000_000_000_000_000u128).into_val(env));
    init_args.push_back((100_000_000_000_000_000_000u128).into_val(env));
    init_args.push_back((800_000_000_000_000_000_000_000_000u128).into_val(env));
    let _: () = env.invoke_contract(&contract_id, &Symbol::new(env, "initialize"), init_args);
    contract_id
}

fn deploy_reserve(
    env: &Env,
    kinetic_router_addr: &Address,
    oracle_addr: &Address,
    admin: &Address,
    ltv: u32,
    liquidation_threshold: u32,
    liquidation_bonus: u32,
) -> (Address, Address, Address) {
    let token_admin = Address::generate(env);
    let underlying_token = env.register_stellar_asset_contract_v2(token_admin.clone());
    let underlying_addr = underlying_token.address();

    let irs_addr = setup_interest_rate_strategy(env, admin);
    let treasury = Address::generate(env);

    let params = kinetic_router::InitReserveParams {
        decimals: 7,
        ltv,
        liquidation_threshold,
        liquidation_bonus,
        reserve_factor: 1000,
        supply_cap: 0,
        borrow_cap: 0,
        borrowing_enabled: true,
        flashloan_enabled: true,
    };

    let a_token_addr = env.register(a_token::WASM, ());
    let a_token_client = a_token::Client::new(env, &a_token_addr);
    a_token_client.initialize(
        admin,
        &underlying_addr,
        kinetic_router_addr,
        &String::from_str(env, "aToken"),
        &String::from_str(env, "aTKN"),
        &params.decimals,
    );

    let debt_token_addr = env.register(debt_token::WASM, ());
    let debt_token_client = debt_token::Client::new(env, &debt_token_addr);
    debt_token_client.initialize(
        admin,
        &underlying_addr,
        kinetic_router_addr,
        &String::from_str(env, "debtToken"),
        &String::from_str(env, "dTKN"),
        &params.decimals,
    );

    let pool_configurator = Address::generate(env);
    let router_client = kinetic_router::Client::new(env, kinetic_router_addr);
    router_client.set_pool_configurator(&pool_configurator);
    router_client.init_reserve(
        &pool_configurator,
        &underlying_addr,
        &a_token_addr,
        &debt_token_addr,
        &irs_addr,
        &treasury,
        &params,
    );

    let oracle_client = price_oracle::Client::new(env, oracle_addr);
    let asset_oracle = price_oracle::Asset::Stellar(underlying_addr.clone());
    oracle_client.add_asset(admin, &asset_oracle);
    oracle_client.set_manual_override(
        admin,
        &asset_oracle,
        &Some(100_000_000_000_000u128), // $1.00 at 14 decimals
        &Some(env.ledger().timestamp() + 604_800),
    );

    (underlying_addr, a_token_addr, debt_token_addr)
}

fn deploy_protocol(env: &Env) -> (Address, Address, Address, Address) {
    let admin = Address::generate(env);
    let emergency_admin = Address::generate(env);

    let kinetic_router_addr = env.register(kinetic_router::WASM, ());
    let kinetic_router = kinetic_router::Client::new(env, &kinetic_router_addr);

    let oracle_addr = env.register(price_oracle::WASM, ());
    let oracle_client = price_oracle::Client::new(env, &oracle_addr);
    let reflector_addr = env.register(MockReflector, ());
    let base_currency = Address::generate(env);
    let native_xlm = Address::generate(env);
    oracle_client.initialize(&admin, &reflector_addr, &base_currency, &native_xlm);

    let pool_treasury = Address::generate(env);
    let dex_router = Address::generate(env);
    kinetic_router.initialize(
        &admin,
        &emergency_admin,
        &oracle_addr,
        &pool_treasury,
        &dex_router,
        &None,
    );

    (kinetic_router_addr, oracle_addr, admin, emergency_admin)
}

fn mint_and_approve(env: &Env, underlying: &Address, router: &Address, user: &Address, amount: u128) {
    let stellar_token = token::StellarAssetClient::new(env, underlying);
    stellar_token.mint(user, &(amount as i128));
    let token_client = token::Client::new(env, underlying);
    let expiration = env.ledger().sequence() + 1_000_000;
    token_client.approve(user, router, &(amount as i128), &expiration);
}

fn advance_time(env: &Env, seconds: u64) {
    let info = env.ledger().get();
    env.ledger().set(LedgerInfo {
        sequence_number: info.sequence_number + 10,
        timestamp: info.timestamp + seconds,
        ..info
    });
}

// =============================================================================
// G-17: Flash loan premium delivery to treasury
// =============================================================================

#[test]
fn test_flash_loan_premium_to_treasury() {
    let env = Env::default();
    env.mock_all_auths();
    env.budget().reset_unlimited();
    setup_ledger(&env);

    let (router_addr, oracle_addr, admin, _) = deploy_protocol(&env);
    let (underlying, a_token_addr, _) = deploy_reserve(&env, &router_addr, &oracle_addr, &admin, 8000, 8500, 500);
    let router = kinetic_router::Client::new(&env, &router_addr);

    // Set flash loan premium to 9 bps (0.09%)
    router.set_flash_loan_premium(&9u128);

    // Supply liquidity
    let lp = Address::generate(&env);
    let supply_amount = 10_000_0000000u128;
    mint_and_approve(&env, &underlying, &router_addr, &lp, supply_amount);
    router.supply(&lp, &underlying, &supply_amount, &lp, &0u32);

    // Deploy mock receiver and set up aToken mapping
    let receiver_addr = env.register(MockFlashLoanReceiver, ());
    let receiver_client = MockFlashLoanReceiverClient::new(&env, &receiver_addr);
    receiver_client.set_atoken(&underlying, &a_token_addr);

    // Fund receiver with enough to pay premium
    let flash_amount = 1_000_0000000u128; // 1000 tokens
    // Premium = 1000 * 9 / 10000 = 0.9 tokens, rounded up = 1 (percent_mul_up)
    let max_premium = 1_0000000u128; // 1 token (more than enough for rounding)
    let stellar_token = token::StellarAssetClient::new(&env, &underlying);
    stellar_token.mint(&receiver_addr, &(max_premium as i128));

    // Get treasury address and initial balance
    let treasury = router.get_treasury().unwrap();
    let token_client = token::Client::new(&env, &underlying);
    let treasury_before = token_client.balance(&treasury);

    // Execute flash loan
    let initiator = Address::generate(&env);
    let assets = Vec::from_array(&env, [underlying.clone()]);
    let amounts = Vec::from_array(&env, [flash_amount]);
    let params = Bytes::new(&env);

    let result = router.try_flash_loan(&initiator, &receiver_addr, &assets, &amounts, &params);
    assert!(result.is_ok(), "Flash loan should succeed: {:?}", result.err());

    // Verify treasury received the premium
    let treasury_after = token_client.balance(&treasury);
    let premium_received = treasury_after - treasury_before;

    assert!(
        premium_received > 0,
        "Treasury should have received premium. Before: {}, After: {}",
        treasury_before, treasury_after
    );

    // Premium should be approximately flash_amount * 9 / 10000 = 0.09%
    // For 1000_0000000 * 9 / 10000 = 900000 (0.09 tokens)
    // With percent_mul_up rounding: ceil(1000_0000000 * 9 / 10000) = 900000
    let expected_premium = 900000i128; // 0.09 tokens at 7 decimals
    assert!(
        premium_received >= expected_premium,
        "Premium should be >= expected. Received: {}, Expected: {}",
        premium_received, expected_premium
    );
}

// =============================================================================
// G-20: Borrow rejects when insufficient liquidity
// =============================================================================

#[test]
fn test_borrow_insufficient_liquidity_rejected() {
    let env = Env::default();
    env.mock_all_auths();
    env.budget().reset_unlimited();
    setup_ledger(&env);

    let (router_addr, oracle_addr, admin, _) = deploy_protocol(&env);
    let (asset_a, _, _) = deploy_reserve(&env, &router_addr, &oracle_addr, &admin, 8000, 8500, 500);
    let (asset_b, _, _) = deploy_reserve(&env, &router_addr, &oracle_addr, &admin, 8000, 8500, 500);
    let router = kinetic_router::Client::new(&env, &router_addr);

    let lp = Address::generate(&env);
    let borrower = Address::generate(&env);

    // LP provides only 100 tokens of asset B as liquidity
    let lp_amount = 100_0000000u128;
    mint_and_approve(&env, &asset_b, &router_addr, &lp, lp_amount);
    router.supply(&lp, &asset_b, &lp_amount, &lp, &0u32);

    // Borrower supplies 500 tokens of asset A as collateral (plenty of collateral)
    let collateral = 500_0000000u128;
    mint_and_approve(&env, &asset_a, &router_addr, &borrower, collateral);
    router.supply(&borrower, &asset_a, &collateral, &borrower, &0u32);

    // Attempt to borrow 200 tokens of B (only 100 available) → should fail
    let result = router.try_borrow(&borrower, &asset_b, &200_0000000u128, &1u32, &0u32, &borrower);
    assert!(result.is_err(), "Borrow exceeding available liquidity should be rejected");

    // Borrow 50 tokens → should succeed (within available liquidity)
    router.borrow(&borrower, &asset_b, &50_0000000u128, &1u32, &0u32, &borrower);

    let data = router.get_user_account_data(&borrower);
    assert!(data.health_factor >= WAD, "Should be healthy after valid borrow");
}

// =============================================================================
// G-28: Debt ceiling blocks excess borrow
// =============================================================================

#[test]
fn test_debt_ceiling_blocks_excess_borrow() {
    let env = Env::default();
    env.mock_all_auths();
    env.budget().reset_unlimited();
    setup_ledger(&env);

    let (router_addr, oracle_addr, admin, _) = deploy_protocol(&env);
    let (asset_a, _, _) = deploy_reserve(&env, &router_addr, &oracle_addr, &admin, 8000, 8500, 500);
    let (asset_b, _, _) = deploy_reserve(&env, &router_addr, &oracle_addr, &admin, 8000, 8500, 500);
    let router = kinetic_router::Client::new(&env, &router_addr);

    // Set debt ceiling of 50 whole tokens on asset B
    router.set_reserve_debt_ceiling(&asset_b, &50u128);

    let lp = Address::generate(&env);
    let borrower = Address::generate(&env);

    // LP provides liquidity
    let lp_amount = 10_000_0000000u128;
    mint_and_approve(&env, &asset_b, &router_addr, &lp, lp_amount);
    router.supply(&lp, &asset_b, &lp_amount, &lp, &0u32);

    // Borrower supplies plenty of collateral
    let collateral = 1_000_0000000u128;
    mint_and_approve(&env, &asset_a, &router_addr, &borrower, collateral);
    router.supply(&borrower, &asset_a, &collateral, &borrower, &0u32);

    // Attempt to borrow 60 tokens (exceeds 50 token ceiling) → should fail
    let result = router.try_borrow(&borrower, &asset_b, &60_0000000u128, &1u32, &0u32, &borrower);
    assert!(result.is_err(), "Borrow exceeding debt ceiling should be rejected");

    // Borrow 40 tokens → should succeed (within ceiling)
    router.borrow(&borrower, &asset_b, &40_0000000u128, &1u32, &0u32, &borrower);

    let data = router.get_user_account_data(&borrower);
    assert!(data.total_debt_base > 0, "Should have debt after valid borrow");

    // Try to borrow 15 more (total 55 > 50 ceiling) → should fail
    let result2 = router.try_borrow(&borrower, &asset_b, &15_0000000u128, &1u32, &0u32, &borrower);
    assert!(result2.is_err(), "Second borrow pushing over debt ceiling should be rejected");
}

// =============================================================================
// M-15: claim_all_rewards capped at 10 assets
// =============================================================================

#[test]
fn test_claim_all_rewards_capped_at_10() {
    let env = Env::default();
    env.mock_all_auths();
    env.budget().reset_unlimited();
    setup_ledger(&env);

    // Deploy incentives contract
    let admin = Address::generate(&env);
    let lending_pool = Address::generate(&env);
    let incentives_addr = env.register(incentives::WASM, ());
    let incentives_client = incentives::Client::new(&env, &incentives_addr);
    incentives_client.initialize(&admin, &lending_pool);

    let user = Address::generate(&env);

    // Create a Vec with 11 fake asset addresses (exceeds the 10-asset cap)
    let mut assets = Vec::new(&env);
    for _ in 0..11 {
        assets.push_back(Address::generate(&env));
    }

    // claim_all_rewards with 11 assets should fail with MaxAssetsExceeded
    let result = incentives_client.try_claim_all_rewards(&user, &assets, &user);
    assert!(result.is_err(), "claim_all_rewards with 11 assets should be rejected (M-15 cap)");

    // Verify the specific error
    match result {
        Err(Ok(incentives::IncentivesError::MaxAssetsExceeded)) => {
            // Expected
        }
        other => panic!("Expected MaxAssetsExceeded error, got: {:?}", other),
    }

    // With 10 assets should not hit the cap (may fail for other reasons like
    // assets not being configured, but NOT MaxAssetsExceeded)
    let mut assets_10 = Vec::new(&env);
    for _ in 0..10 {
        assets_10.push_back(Address::generate(&env));
    }

    let result_10 = incentives_client.try_claim_all_rewards(&user, &assets_10, &user);
    // This may succeed or fail for other reasons, but should NOT be MaxAssetsExceeded
    if let Err(Ok(incentives::IncentivesError::MaxAssetsExceeded)) = result_10 {
        panic!("10 assets should NOT trigger MaxAssetsExceeded cap");
    }
}

// =============================================================================
// Paused protocol blocks all operations
// =============================================================================

#[test]
fn test_paused_pool_blocks_operations() {
    let env = Env::default();
    env.mock_all_auths();
    env.budget().reset_unlimited();
    setup_ledger(&env);

    let (router_addr, oracle_addr, admin, emergency_admin) = deploy_protocol(&env);
    let (underlying, _, _) = deploy_reserve(&env, &router_addr, &oracle_addr, &admin, 8000, 8500, 500);
    let router = kinetic_router::Client::new(&env, &router_addr);

    let user = Address::generate(&env);
    let supply_amount = 100_0000000u128;
    mint_and_approve(&env, &underlying, &router_addr, &user, supply_amount);

    // Verify supply works before pause
    router.supply(&user, &underlying, &50_0000000u128, &user, &0u32);

    // Emergency admin pauses the pool
    router.pause(&emergency_admin);
    assert!(router.is_paused(), "Pool should be paused");

    // Supply should fail while paused
    let supply_result = router.try_supply(&user, &underlying, &10_0000000u128, &user, &0u32);
    assert!(supply_result.is_err(), "Supply should be blocked while paused");

    // Withdraw should fail while paused
    let withdraw_result = router.try_withdraw(&user, &underlying, &10_0000000u128, &user);
    assert!(withdraw_result.is_err(), "Withdraw should be blocked while paused");

    // Borrow should fail while paused
    let borrow_result = router.try_borrow(&user, &underlying, &10_0000000u128, &1u32, &0u32, &user);
    assert!(borrow_result.is_err(), "Borrow should be blocked while paused");

    // Pool admin unpauses
    router.unpause(&admin);
    assert!(!router.is_paused(), "Pool should be unpaused");

    // Supply should work again after unpause
    let result_after = router.try_supply(&user, &underlying, &10_0000000u128, &user, &0u32);
    assert!(result_after.is_ok(), "Supply should succeed after unpause");
}

// =============================================================================
// G-18: Expired price blocks liquidation
// =============================================================================

#[test]
fn test_expired_price_blocks_liquidation() {
    let env = Env::default();
    env.mock_all_auths();
    env.budget().reset_unlimited();
    setup_ledger(&env);

    let (router_addr, oracle_addr, admin, _) = deploy_protocol(&env);
    let router = kinetic_router::Client::new(&env, &router_addr);
    let oracle_client = price_oracle::Client::new(&env, &oracle_addr);

    // Deploy two reserves with short-lived price overrides
    let (asset_a, _, _) = deploy_reserve(&env, &router_addr, &oracle_addr, &admin, 8000, 8500, 500);
    let (asset_b, _, _) = deploy_reserve(&env, &router_addr, &oracle_addr, &admin, 8000, 8500, 500);

    let lp = Address::generate(&env);
    let user = Address::generate(&env);
    let liquidator = Address::generate(&env);

    // LP supplies liquidity for asset B
    let lp_amount = 10_000_0000000u128;
    mint_and_approve(&env, &asset_b, &router_addr, &lp, lp_amount);
    router.supply(&lp, &asset_b, &lp_amount, &lp, &0u32);

    // User supplies asset A and borrows asset B
    let supply_a = 200_0000000u128;
    let borrow_b = 100_0000000u128;
    mint_and_approve(&env, &asset_a, &router_addr, &user, supply_a);
    router.supply(&user, &asset_a, &supply_a, &user, &0u32);
    router.borrow(&user, &asset_b, &borrow_b, &1u32, &0u32, &user);

    // Now set a short-lived price for asset A that makes user unhealthy
    // First reset circuit breaker, then set a low price with short expiry
    let asset_a_oracle = price_oracle::Asset::Stellar(asset_a.clone());
    oracle_client.reset_circuit_breaker(&admin, &asset_a_oracle);
    oracle_client.set_manual_override(
        &admin,
        &asset_a_oracle,
        &Some(40_000_000_000_000u128), // $0.40 → HF = (200*0.40*0.85)/100 = 0.68
        &Some(env.ledger().timestamp() + 100), // Expires in 100 seconds
    );

    // Fund liquidator
    mint_and_approve(&env, &asset_b, &router_addr, &liquidator, borrow_b);

    // Verify user is liquidatable now (price is valid)
    let data = router.get_user_account_data(&user);
    assert!(data.health_factor < WAD, "Should be liquidatable with valid price");

    // Advance time past the price expiry
    advance_time(&env, 200);

    // Now try to liquidate — should fail because the price is stale/expired
    let result = router.try_liquidation_call(
        &liquidator,
        &asset_a,
        &asset_b,
        &user,
        &(borrow_b / 2),
        &false,
    );
    assert!(result.is_err(), "Liquidation should fail when price has expired");
}

// =============================================================================
// Flash loan on insufficient liquidity
// =============================================================================

#[test]
fn test_flash_loan_insufficient_liquidity_rejected() {
    let env = Env::default();
    env.mock_all_auths();
    env.budget().reset_unlimited();
    setup_ledger(&env);

    let (router_addr, oracle_addr, admin, _) = deploy_protocol(&env);
    let (underlying, _, _) = deploy_reserve(&env, &router_addr, &oracle_addr, &admin, 8000, 8500, 500);
    let router = kinetic_router::Client::new(&env, &router_addr);

    // Supply only 100 tokens
    let lp = Address::generate(&env);
    let lp_amount = 100_0000000u128;
    mint_and_approve(&env, &underlying, &router_addr, &lp, lp_amount);
    router.supply(&lp, &underlying, &lp_amount, &lp, &0u32);

    // Try to flash loan 200 tokens (more than available)
    let receiver = Address::generate(&env);
    let initiator = Address::generate(&env);
    let assets = Vec::from_array(&env, [underlying.clone()]);
    let amounts = Vec::from_array(&env, [200_0000000u128]);
    let params = Bytes::new(&env);

    let result = router.try_flash_loan(&initiator, &receiver, &assets, &amounts, &params);
    assert!(result.is_err(), "Flash loan exceeding pool liquidity should be rejected");
}
