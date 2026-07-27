#![cfg(test)]

//! Full integration tests for K2 + Aquarius DEX
//!
//! These tests deploy both K2 protocol and Aquarius AMM, then test:
//! - swap_collateral with Aquarius adapter
//! - prepare_liquidation + execute_liquidation with Aquarius adapter
//!
//! This verifies the complete flow of using Aquarius as the DEX backend for K2.

use crate::setup::{create_test_env_with_budget_limits, deploy_test_protocol_two_assets};
use k2_shared::WAD;
use soroban_sdk::{
    testutils::{Address as _, MockAuth, MockAuthInvoke},
    Address, BytesN, Env, IntoVal, Vec,
    token::{StellarAssetClient as TokenAdminClient},
};

// Import Aquarius contracts with unique module names
mod aquarius_pool {
    soroban_sdk::contractimport!(
        file = "../../aquarius-amm/contracts/soroban_liquidity_pool_contract.wasm"
    );
}

mod aquarius_router {
    soroban_sdk::contractimport!(
        file = "../../aquarius-amm/contracts/soroban_liquidity_pool_router_contract.wasm"
    );
}

mod aquarius_plane {
    soroban_sdk::contractimport!(
        file = "../../aquarius-amm/contracts/soroban_liquidity_pool_plane_contract.wasm"
    );
}

mod aquarius_config_storage {
    soroban_sdk::contractimport!(
        file = "../../aquarius-amm/contracts/soroban_config_storage_contract.wasm"
    );
}

mod aquarius_lp_token {
    soroban_sdk::contractimport!(
        file = "../../aquarius-amm/contracts/soroban_token_contract.wasm"
    );
}

mod aquarius_boost_feed {
    soroban_sdk::contractimport!(
        file = "../../aquarius-amm/contracts/soroban_locker_feed_contract.wasm"
    );
}

mod aquarius_rewards_gauge {
    soroban_sdk::contractimport!(
        file = "../../aquarius-amm/contracts/soroban_rewards_gauge_contract.wasm"
    );
}

/// Helper struct to manage Aquarius deployment
struct AquariusDeployment<'a> {
    pub router: aquarius_router::Client<'a>,
    pub plane: aquarius_plane::Client<'a>,
    pub config_storage: aquarius_config_storage::Client<'a>,
    pub reward_token: Address,
    pub admin: Address,
}

impl<'a> AquariusDeployment<'a> {
    /// Deploy Aquarius infrastructure
    fn deploy(env: &'a Env, admin: &Address) -> Self {
        let emergency_admin = Address::generate(env);

        // Create reward token (needed for pool creation fees)
        let reward_token = env
            .register_stellar_asset_contract_v2(admin.clone())
            .address();

        // Create locked token for boost feed
        let locked_token = env
            .register_stellar_asset_contract_v2(admin.clone())
            .address();
        let locked_token_admin = TokenAdminClient::new(env, &locked_token);

        // Deploy boost feed
        let boost_feed = aquarius_boost_feed::Client::new(
            env,
            &env.register(
                aquarius_boost_feed::WASM,
                aquarius_boost_feed::Args::__constructor(admin, admin, &emergency_admin),
            ),
        );
        locked_token_admin.mint(admin, &53_000_000_000_0000000);
        boost_feed.set_total_supply(admin, &53_000_000_000_0000000);

        // Upload contract WASMs
        let pool_hash = env
            .deployer()
            .upload_contract_wasm(aquarius_pool::WASM);
        let token_hash = env
            .deployer()
            .upload_contract_wasm(aquarius_lp_token::WASM);
        let rewards_gauge_hash = env
            .deployer()
            .upload_contract_wasm(aquarius_rewards_gauge::WASM);

        // Deploy plane
        let plane = aquarius_plane::Client::new(
            env,
            &env.register(aquarius_plane::WASM, ()),
        );

        // Deploy config storage
        let config_storage = aquarius_config_storage::Client::new(
            env,
            &env.register(
                aquarius_config_storage::WASM,
                aquarius_config_storage::Args::__constructor(admin, &emergency_admin),
            ),
        );

        // Deploy router
        let router = aquarius_router::Client::new(
            env,
            &env.register(aquarius_router::WASM, ()),
        );

        // Initialize router
        router.init_admin(admin);
        router.init_config_storage(admin, &config_storage.address);
        router.set_rewards_gauge_hash(admin, &rewards_gauge_hash);
        router.set_pool_hash(admin, &pool_hash);
        router.set_token_hash(admin, &token_hash);
        router.set_reward_token(admin, &reward_token);
        router.set_pools_plane(admin, &plane.address);
        router.configure_init_pool_payment(
            admin,
            &reward_token,
            &10_0000000,
            &1_0000000,
            &router.address,
        );
        router.set_reward_boost_config(admin, &locked_token, &boost_feed.address);
        router.set_protocol_fee_fraction(admin, &5000); // 50% protocol fee

        Self {
            router,
            plane,
            config_storage,
            reward_token,
            admin: admin.clone(),
        }
    }

    /// Create a liquidity pool for a token pair
    fn create_pool(
        &self,
        env: &'a Env,
        token0: &Address,
        token1: &Address,
        fee_fraction: u32,
    ) -> (aquarius_pool::Client<'a>, Address, BytesN<32>) {
        // Tokens must be sorted
        assert!(token0 < token1, "Tokens must be sorted");

        // Mint reward tokens for pool creation fee
        let reward_admin = TokenAdminClient::new(env, &self.reward_token);
        reward_admin.mint(&self.admin, &10_0000000);

        let tokens = Vec::from_array(env, [token0.clone(), token1.clone()]);
        let (pool_hash, pool_address) = self.router.init_standard_pool(
            &self.admin,
            &tokens,
            &fee_fraction,
        );

        (
            aquarius_pool::Client::new(env, &pool_address),
            pool_address,
            pool_hash,
        )
    }
}

#[test]
fn test_swap_collateral_with_aquarius() {
    let env = create_test_env_with_budget_limits();
    let protocol = deploy_test_protocol_two_assets(&env);

    // Deploy Aquarius
    let aquarius = AquariusDeployment::deploy(&env, &protocol.admin);

    // Deploy Aquarius adapter
    let adapter_id = env.register(crate::aquarius_swap_adapter::WASM, ());
    let adapter = crate::aquarius_swap_adapter::Client::new(&env, &adapter_id);
    adapter.initialize(&protocol.admin, &aquarius.router.address);

    // Sort tokens for Aquarius (required)
    let (token0, token1) = if protocol.usdc_asset < protocol.usdt_asset {
        (protocol.usdc_asset.clone(), protocol.usdt_asset.clone())
    } else {
        (protocol.usdt_asset.clone(), protocol.usdc_asset.clone())
    };

    // Create Aquarius pool with 0.3% fee
    let (pool, pool_address, _pool_hash) = aquarius.create_pool(&env, &token0, &token1, 30);

    // Register pool with adapter (required for swaps)
    env.mock_auths(&[MockAuth {
        address: &protocol.admin,
        invoke: &MockAuthInvoke {
            contract: &adapter_id,
            fn_name: "register_pool",
            args: (
                &protocol.admin,
                &token0,
                &token1,
                &pool_address,
            )
                .into_val(&env),
            sub_invokes: &[],
        },
    }]);
    adapter.register_pool(&protocol.admin, &token0, &token1, &pool_address);

    // Add liquidity to Aquarius pool
    // Ensure auth is mocked for mint operations
    env.mock_all_auths();

    // M-01: Whitelist the Aquarius adapter as a swap handler
    let mut whitelist = Vec::new(&env);
    whitelist.push_back(adapter_id.clone());
    protocol.kinetic_router.set_swap_handler_whitelist(&whitelist);

    let token0_admin = TokenAdminClient::new(&env, &token0);
    let token1_admin = TokenAdminClient::new(&env, &token1);

    token0_admin.mint(&protocol.admin, &10_000_000_0000000);
    token1_admin.mint(&protocol.admin, &10_000_000_0000000);

    pool.deposit(
        &protocol.admin,
        &Vec::from_array(&env, [10_000_000_0000000u128, 10_000_000_0000000u128]),
        &0u128,
    );

    // Setup K2 position: User supplies USDC, borrows USDT
    let usdc_supply = 100_000_000_000u128; // 100 USDC
    let usdt_borrow = 30_000_000_000u128;  // 30 USDT

    // LP provides USDT liquidity
    protocol.kinetic_router.supply(
        &protocol.liquidity_provider,
        &protocol.usdt_asset,
        &200_000_000_000u128,
        &protocol.liquidity_provider,
        &0u32,
    );

    // User supplies USDC
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

    // User borrows USDT
    protocol.kinetic_router.borrow(
        &protocol.user,
        &protocol.usdt_asset,
        &usdt_borrow,
        &1u32,
        &0u32,
        &protocol.user,
    );

    // Get initial balances
    let user_usdc_collateral_before = protocol.usdc_a_token.balance(&protocol.user);
    let user_usdt_collateral_before = protocol.usdt_a_token.balance(&protocol.user);

    println!("\n=== Testing swap_collateral with Aquarius ===");
    println!("USDC collateral before: {}", user_usdc_collateral_before);
    println!("USDT collateral before: {}", user_usdt_collateral_before);

    // Swap 20 USDC collateral to USDT via Aquarius
    let swap_amount = 20_000_000_000u128;
    let min_amount_out = 18_000_000_000u128; // Allow some slippage

    env.mock_auths(&[MockAuth {
        address: &protocol.user,
        invoke: &MockAuthInvoke {
            contract: &protocol.kinetic_router.address,
            fn_name: "swap_collateral",
            args: (
                &protocol.user,
                &protocol.usdc_asset,
                &protocol.usdt_asset,
                &swap_amount,
                &min_amount_out,
                &Some(adapter_id.clone()), // Use Aquarius adapter
            )
                .into_val(&env),
            sub_invokes: &[],
        },
    }]);

    protocol.kinetic_router.swap_collateral(
        &protocol.user,
        &protocol.usdc_asset,
        &protocol.usdt_asset,
        &swap_amount,
        &min_amount_out,
        &Some(adapter_id.clone()), // Use Aquarius adapter
    );

    // Verify swap occurred
    let user_usdc_collateral_after = protocol.usdc_a_token.balance(&protocol.user);
    let user_usdt_collateral_after = protocol.usdt_a_token.balance(&protocol.user);

    println!("USDC collateral after: {}", user_usdc_collateral_after);
    println!("USDT collateral after: {}", user_usdt_collateral_after);

    assert!(
        user_usdc_collateral_after < user_usdc_collateral_before,
        "USDC collateral should decrease"
    );
    assert!(
        user_usdt_collateral_after > user_usdt_collateral_before,
        "USDT collateral should increase"
    );

    let usdc_decrease = (user_usdc_collateral_before - user_usdc_collateral_after) as u128;
    let usdt_increase = (user_usdt_collateral_after - user_usdt_collateral_before) as u128;

    println!("USDC decrease: {}", usdc_decrease);
    println!("USDT increase: {}", usdt_increase);

    assert_eq!(usdc_decrease, swap_amount, "USDC should decrease by swap amount");
    assert!(usdt_increase >= min_amount_out, "USDT increase should meet minimum");

    println!("✅ swap_collateral with Aquarius successful!");
}

#[test]
fn test_flash_liquidation_with_aquarius() {
    let env = create_test_env_with_budget_limits();
    let protocol = deploy_test_protocol_two_assets(&env);

    // Deploy Aquarius
    let aquarius = AquariusDeployment::deploy(&env, &protocol.admin);

    // Deploy Aquarius adapter
    let adapter_id = env.register(crate::aquarius_swap_adapter::WASM, ());
    let adapter = crate::aquarius_swap_adapter::Client::new(&env, &adapter_id);
    adapter.initialize(&protocol.admin, &aquarius.router.address);

    // Sort tokens for Aquarius
    let (token0, token1) = if protocol.usdc_asset < protocol.usdt_asset {
        (protocol.usdc_asset.clone(), protocol.usdt_asset.clone())
    } else {
        (protocol.usdt_asset.clone(), protocol.usdc_asset.clone())
    };

    // Create Aquarius pool with 0.3% fee
    let (pool, pool_address, _pool_hash) = aquarius.create_pool(&env, &token0, &token1, 30);

    // Register pool with adapter (required for swaps)
    env.mock_auths(&[MockAuth {
        address: &protocol.admin,
        invoke: &MockAuthInvoke {
            contract: &adapter_id,
            fn_name: "register_pool",
            args: (
                &protocol.admin,
                &token0,
                &token1,
                &pool_address,
            )
                .into_val(&env),
            sub_invokes: &[],
        },
    }]);
    adapter.register_pool(&protocol.admin, &token0, &token1, &pool_address);

    // Add liquidity to Aquarius pool
    env.mock_all_auths();

    // M-01: Whitelist the Aquarius adapter as a swap handler
    let mut whitelist = Vec::new(&env);
    whitelist.push_back(adapter_id.clone());
    protocol.kinetic_router.set_swap_handler_whitelist(&whitelist);

    let token0_admin = TokenAdminClient::new(&env, &token0);
    let token1_admin = TokenAdminClient::new(&env, &token1);

    token0_admin.mint(&protocol.admin, &10_000_000_0000000);
    token1_admin.mint(&protocol.admin, &10_000_000_0000000);

    pool.deposit(
        &protocol.admin,
        &Vec::from_array(&env, [10_000_000_0000000u128, 10_000_000_0000000u128]),
        &0u128,
    );

    // Setup liquidatable position (H-04: 70% LTV + $0.80 crash)
    let usdc_supply = 100_000_000_000u128;
    let usdt_borrow = 70_000_000_000u128;

    // LP provides liquidity
    protocol.kinetic_router.supply(
        &protocol.liquidity_provider,
        &protocol.usdt_asset,
        &200_000_000_000u128,
        &protocol.liquidity_provider,
        &0u32,
    );

    // User supplies USDC
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

    // User borrows USDT
    protocol.kinetic_router.borrow(
        &protocol.user,
        &protocol.usdt_asset,
        &usdt_borrow,
        &1u32,
        &0u32,
        &protocol.user,
    );

    // Verify position is healthy
    let account_data_before = protocol.kinetic_router.get_user_account_data(&protocol.user);
    assert!(
        account_data_before.health_factor >= WAD,
        "Position should be healthy before price crash"
    );

    // Crash USDC price to make position liquidatable
    let usdc_asset_enum = crate::price_oracle::Asset::Stellar(protocol.usdc_asset.clone());
    protocol.price_oracle.reset_circuit_breaker(&protocol.admin, &usdc_asset_enum);
    let expiry = env.ledger().timestamp() + 86400;
    protocol.price_oracle.set_manual_override(
        &protocol.admin,
        &usdc_asset_enum,
        &Some(800_000_000_000_000u128), // $0.80
        &Some(expiry),
    );

    // Verify position is now liquidatable
    let account_data_after_crash = protocol.kinetic_router.get_user_account_data(&protocol.user);
    assert!(
        account_data_after_crash.health_factor < WAD,
        "Position should be liquidatable after crash. HF: {}",
        account_data_after_crash.health_factor
    );

    println!("\n=== Testing flash liquidation with Aquarius ===");
    println!("Health factor: {}", account_data_after_crash.health_factor);
    println!("Total debt: {}", account_data_after_crash.total_debt_base);
    println!("Total collateral: {}", account_data_after_crash.total_collateral_base);

    // Get initial balances
    let liquidator_usdt_before = protocol.usdt_client.balance(&protocol.liquidator);
    let user_debt_before = protocol.usdt_debt_token.balance(&protocol.user);

    let debt_to_cover = 35_000_000_000u128;
    let min_swap_out = 30_000_000_000u128;
    let deadline = env.ledger().timestamp() + 300;

    // Step 1: Prepare liquidation with Aquarius adapter
    env.mock_auths(&[MockAuth {
        address: &protocol.liquidator,
        invoke: &MockAuthInvoke {
            contract: &protocol.kinetic_router.address,
            fn_name: "prepare_liquidation",
            args: (
                &protocol.liquidator,
                &protocol.user,
                &protocol.usdt_asset,
                &protocol.usdc_asset,
                &debt_to_cover,
                &min_swap_out,
                &Some(adapter_id.clone()), // Use Aquarius adapter
            )
                .into_val(&env),
            sub_invokes: &[],
        },
    }]);

    let auth = protocol.kinetic_router.prepare_liquidation(
        &protocol.liquidator,
        &protocol.user,
        &protocol.usdt_asset,
        &protocol.usdc_asset,
        &debt_to_cover,
        &min_swap_out,
        &Some(adapter_id.clone()), // Use Aquarius adapter
    );

    println!("✅ Prepare liquidation successful");
    println!("   Nonce: {}", auth.nonce);
    println!("   Collateral to seize: {}", auth.collateral_to_seize);

    // Step 2: Execute liquidation
    env.mock_auths(&[MockAuth {
        address: &protocol.liquidator,
        invoke: &MockAuthInvoke {
            contract: &protocol.kinetic_router.address,
            fn_name: "execute_liquidation",
            args: (
                &protocol.liquidator,
                &protocol.user,
                &protocol.usdt_asset,
                &protocol.usdc_asset,
                &deadline,
            )
                .into_val(&env),
            sub_invokes: &[],
        },
    }]);

    protocol.kinetic_router.execute_liquidation(
        &protocol.liquidator,
        &protocol.user,
        &protocol.usdt_asset,
        &protocol.usdc_asset,
        &deadline,
    );

    println!("✅ Execute liquidation successful");

    // Verify liquidation occurred
    let liquidator_usdt_after = protocol.usdt_client.balance(&protocol.liquidator);
    let user_debt_after = protocol.usdt_debt_token.balance(&protocol.user);

    println!("Liquidator USDT before: {}", liquidator_usdt_before);
    println!("Liquidator USDT after: {}", liquidator_usdt_after);
    println!("User debt before: {}", user_debt_before);
    println!("User debt after: {}", user_debt_after);

    assert!(
        user_debt_after < user_debt_before,
        "User debt should decrease"
    );
    assert!(
        liquidator_usdt_after > liquidator_usdt_before,
        "Liquidator should profit"
    );

    let account_data_after = protocol.kinetic_router.get_user_account_data(&protocol.user);
    println!("Health factor after liquidation: {}", account_data_after.health_factor);

    println!("✅ Flash liquidation with Aquarius successful!");
}

#[test]
fn test_multiple_swaps_with_aquarius() {
    let env = create_test_env_with_budget_limits();
    let protocol = deploy_test_protocol_two_assets(&env);

    // Deploy Aquarius
    let aquarius = AquariusDeployment::deploy(&env, &protocol.admin);

    // Deploy Aquarius adapter
    let adapter_id = env.register(crate::aquarius_swap_adapter::WASM, ());
    let adapter = crate::aquarius_swap_adapter::Client::new(&env, &adapter_id);
    adapter.initialize(&protocol.admin, &aquarius.router.address);

    // Sort tokens for Aquarius
    let (token0, token1) = if protocol.usdc_asset < protocol.usdt_asset {
        (protocol.usdc_asset.clone(), protocol.usdt_asset.clone())
    } else {
        (protocol.usdt_asset.clone(), protocol.usdc_asset.clone())
    };

    // Create Aquarius pool
    let (pool, pool_address, _pool_hash) = aquarius.create_pool(&env, &token0, &token1, 30);

    // Register pool with adapter (required for swaps)
    env.mock_auths(&[MockAuth {
        address: &protocol.admin,
        invoke: &MockAuthInvoke {
            contract: &adapter_id,
            fn_name: "register_pool",
            args: (
                &protocol.admin,
                &token0,
                &token1,
                &pool_address,
            )
                .into_val(&env),
            sub_invokes: &[],
        },
    }]);
    adapter.register_pool(&protocol.admin, &token0, &token1, &pool_address);

    // Add liquidity
    env.mock_all_auths();

    // M-01: Whitelist the Aquarius adapter as a swap handler
    let mut whitelist = Vec::new(&env);
    whitelist.push_back(adapter_id.clone());
    protocol.kinetic_router.set_swap_handler_whitelist(&whitelist);

    let token0_admin = TokenAdminClient::new(&env, &token0);
    let token1_admin = TokenAdminClient::new(&env, &token1);

    token0_admin.mint(&protocol.admin, &10_000_000_0000000);
    token1_admin.mint(&protocol.admin, &10_000_000_0000000);

    pool.deposit(
        &protocol.admin,
        &Vec::from_array(&env, [10_000_000_0000000u128, 10_000_000_0000000u128]),
        &0u128,
    );

    // Setup position
    let usdc_supply = 200_000_000_000u128; // 200 USDC
    let usdt_borrow = 50_000_000_000u128;  // 50 USDT

    protocol.kinetic_router.supply(
        &protocol.liquidity_provider,
        &protocol.usdt_asset,
        &300_000_000_000u128,
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
        &usdt_borrow,
        &1u32,
        &0u32,
        &protocol.user,
    );

    println!("\n=== Testing multiple swaps with Aquarius ===");

    // Perform multiple swaps
    for i in 1..=3 {
        let swap_amount = 10_000_000_000u128;
        let min_amount_out = 9_000_000_000u128;

        let user_usdc_before = protocol.usdc_a_token.balance(&protocol.user);
        let user_usdt_before = protocol.usdt_a_token.balance(&protocol.user);

        env.mock_auths(&[MockAuth {
            address: &protocol.user,
            invoke: &MockAuthInvoke {
                contract: &protocol.kinetic_router.address,
                fn_name: "swap_collateral",
                args: (
                    &protocol.user,
                    &protocol.usdc_asset,
                    &protocol.usdt_asset,
                    &swap_amount,
                    &min_amount_out,
                    &Some(adapter_id.clone()),
                )
                    .into_val(&env),
                sub_invokes: &[],
            },
        }]);

        protocol.kinetic_router.swap_collateral(
            &protocol.user,
            &protocol.usdc_asset,
            &protocol.usdt_asset,
            &swap_amount,
            &min_amount_out,
            &Some(adapter_id.clone()),
        );

        let user_usdc_after = protocol.usdc_a_token.balance(&protocol.user);
        let user_usdt_after = protocol.usdt_a_token.balance(&protocol.user);

        println!("Swap {}: USDC {} -> {}, USDT {} -> {}", 
            i, user_usdc_before, user_usdc_after, user_usdt_before, user_usdt_after);

        assert!(user_usdc_after < user_usdc_before, "USDC should decrease");
        assert!(user_usdt_after > user_usdt_before, "USDT should increase");
    }

    println!("✅ Multiple swaps with Aquarius successful!");
}
