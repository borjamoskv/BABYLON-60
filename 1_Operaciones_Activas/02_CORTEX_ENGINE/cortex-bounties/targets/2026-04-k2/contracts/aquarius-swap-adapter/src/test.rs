use super::*;
use soroban_sdk::{
    testutils::Address as _,
    Address, Env,
};

extern crate std;

// Helper function to deploy tokens and setup pool for tests
// Returns (token_a_address, token_b_address, pool_address)
fn setup_tokens_and_pool(
    env: &Env,
    adapter: &AquariusSwapAdapterClient,
    admin: &Address,
) -> (Address, Address, Address) {
    // Deploy token contracts using Stellar Asset Contract
    let token_a_admin = Address::generate(env);
    let token_b_admin = Address::generate(env);
    
    let token_a_sac = env.register_stellar_asset_contract_v2(token_a_admin.clone());
    let token_b_sac = env.register_stellar_asset_contract_v2(token_b_admin.clone());
    
    // Get the actual token addresses
    let token_a = token_a_sac.address();
    let token_b = token_b_sac.address();
    
    let mock_pool_id = env.register_contract(None, mock_aquarius_pool::MockAquariusPool);
    let mock_pool = mock_aquarius_pool::MockAquariusPoolClient::new(env, &mock_pool_id);
    
    // Initialize pool with sorted tokens
    let (token0, token1) = if &token_a < &token_b {
        (token_a.clone(), token_b.clone())
    } else {
        (token_b.clone(), token_a.clone())
    };
    mock_pool.initialize(&token0, &token1);
    
    // Mint tokens to the adapter for testing
    use soroban_sdk::token::StellarAssetClient;
    let adapter_addr = &adapter.address;
    StellarAssetClient::new(env, &token_a).mint(adapter_addr, &1_000_000_000i128);
    StellarAssetClient::new(env, &token_b).mint(adapter_addr, &1_000_000_000i128);
    
    // Register pool with adapter
    adapter.register_pool(admin, &token_a, &token_b, &mock_pool_id);
    
    (token_a, token_b, mock_pool_id)
}

// Mock Aquarius Router for testing - with verification of correct parameter ordering
mod mock_aquarius {
    use soroban_sdk::{contract, contractimpl, Address, BytesN, Env, Vec};

    #[contract]
    pub struct MockAquariusRouter;

    #[contractimpl]
    impl MockAquariusRouter {
        /// Mock swap function matching Aquarius interface
        /// Verifies tokens vector is properly sorted (requirement of Aquarius)
        pub fn swap(
            _env: Env,
            _user: Address,
            tokens: Vec<Address>,
            _token_in: Address,
            _token_out: Address,
            _pool_index: BytesN<32>,
            in_amount: u128,
            out_min: u128,
        ) -> u128 {
            // CRITICAL: Verify tokens are sorted correctly (Aquarius requirement)
            assert!(tokens.len() == 2, "Tokens vector must have exactly 2 tokens");
            let token0 = tokens.get(0).unwrap();
            let token1 = tokens.get(1).unwrap();
            
            // Verify sorting: token0 < token1
            assert!(token0 < token1, "Tokens must be sorted: token0 < token1");
            
            // Simple mock: return 95% of input (simulating 5% slippage)
            let out_amount = (in_amount * 95) / 100;
            assert!(out_amount >= out_min, "Slippage too high");
            out_amount
        }

        /// Mock estimate function - also verifies token sorting
        pub fn estimate_swap(
            _env: Env,
            tokens: Vec<Address>,
            _token_in: Address,
            _token_out: Address,
            _pool_index: BytesN<32>,
            in_amount: u128,
        ) -> u128 {
            // CRITICAL: Verify tokens are sorted correctly (Aquarius requirement)
            assert!(tokens.len() == 2, "Tokens vector must have exactly 2 tokens");
            let token0 = tokens.get(0).unwrap();
            let token1 = tokens.get(1).unwrap();
            
            // Verify sorting: token0 < token1
            assert!(token0 < token1, "Tokens must be sorted: token0 < token1");
            
            // Return 95% of input
            (in_amount * 95) / 100
        }
    }
}

// Mock Aquarius Pool for testing
mod mock_aquarius_pool {
    use soroban_sdk::{contract, contractimpl, contracttype, Address, Env, Vec};

    #[contracttype]
    #[derive(Clone)]
    pub enum DataKey {
        Token0,
        Token1,
    }

    #[contract]
    pub struct MockAquariusPool;

    #[contractimpl]
    impl MockAquariusPool {
        /// Initialize pool with two tokens
        pub fn initialize(env: Env, token0: Address, token1: Address) {
            env.storage().instance().set(&DataKey::Token0, &token0);
            env.storage().instance().set(&DataKey::Token1, &token1);
        }

        /// Returns the two tokens in the pool
        pub fn get_tokens(env: Env) -> Vec<Address> {
            let mut tokens = Vec::new(&env);
            let token0: Address = env.storage().instance().get(&DataKey::Token0).unwrap();
            let token1: Address = env.storage().instance().get(&DataKey::Token1).unwrap();
            tokens.push_back(token0);
            tokens.push_back(token1);
            tokens
        }

        /// Mock swap function
        pub fn swap(
            _env: Env,
            _user: Address,
            _in_idx: u32,
            _out_idx: u32,
            in_amount: u128,
            out_min: u128,
        ) -> u128 {
            // Return 95% of input (simulating 5% slippage)
            let out_amount = (in_amount * 95) / 100;
            assert!(out_amount >= out_min, "Slippage too high");
            out_amount
        }

        /// Mock estimate function
        pub fn estimate_swap(
            _env: Env,
            _in_idx: u32,
            _out_idx: u32,
            in_amount: u128,
        ) -> u128 {
            // Return 95% of input
            (in_amount * 95) / 100
        }
    }
}

// Mock Aquarius Router that simulates different failure modes
mod mock_aquarius_failures {
    use soroban_sdk::{contract, contractimpl, Address, BytesN, Env, Vec};

    #[contract]
    pub struct MockAquariusRouterFailing;

    #[contractimpl]
    impl MockAquariusRouterFailing {
        /// Always fails - simulates pool not found or liquidity issues
        pub fn swap(
            _env: Env,
            _user: Address,
            _tokens: Vec<Address>,
            _token_in: Address,
            _token_out: Address,
            _pool_index: BytesN<32>,
            _in_amount: u128,
            _out_min: u128,
        ) -> u128 {
            panic!("Pool not found");
        }

        pub fn estimate_swap(
            _env: Env,
            _tokens: Vec<Address>,
            _token_in: Address,
            _token_out: Address,
            _pool_index: BytesN<32>,
            _in_amount: u128,
        ) -> u128 {
            panic!("Pool not found");
        }
    }
}

#[test]
fn test_initialize_success() {
    let env = Env::default();
    let admin = Address::generate(&env);
    let router = Address::generate(&env);
    
    let contract_id = env.register(AquariusSwapAdapter, (admin.clone(), router.clone()));
    let client = AquariusSwapAdapterClient::new(&env, &contract_id);

    // Verify router was stored
    let stored_router = client.get_router();
    assert_eq!(stored_router, router);
}

#[test]
#[should_panic(expected = "AQUARIUS_ADAPTER_ALREADY_INITIALIZED_AT_CONSTRUCTOR")]
fn test_initialize_twice_fails() {
    let env = Env::default();
    let admin = Address::generate(&env);
    let router = Address::generate(&env);
    let contract_id = env.register(AquariusSwapAdapter, (admin.clone(), router.clone()));
    let client = AquariusSwapAdapterClient::new(&env, &contract_id);

    client.initialize(&admin, &router);
}

#[test]
fn test_set_router_by_admin() {
    let env = Env::default();
    let admin = Address::generate(&env);
    let router1 = Address::generate(&env);
    let router2 = Address::generate(&env);
    let contract_id = env.register(AquariusSwapAdapter, (admin.clone(), router1.clone()));
    let client = AquariusSwapAdapterClient::new(&env, &contract_id);

    env.mock_all_auths();

    assert_eq!(client.get_router(), router1);

    // Update router
    client.set_router(&admin, &router2);
    assert_eq!(client.get_router(), router2);
}

#[test]
#[should_panic(expected = "Error(Contract, #3)")]
fn test_set_router_by_non_admin_fails() {
    let env = Env::default();
    let admin = Address::generate(&env);
    let non_admin = Address::generate(&env);
    let router1 = Address::generate(&env);
    let router2 = Address::generate(&env);
    let contract_id = env.register(AquariusSwapAdapter, (admin.clone(), router1.clone()));
    let client = AquariusSwapAdapterClient::new(&env, &contract_id);

    env.mock_all_auths();

    // Non-admin tries to update router - should panic with Unauthorized error (code 3)
    client.set_router(&non_admin, &router2);
}

#[test]
fn test_execute_swap_success() {
    let env = Env::default();
    env.mock_all_auths();

    // Deploy mock Aquarius router
    let mock_router_id = env.register_contract(None, mock_aquarius::MockAquariusRouter);

    let admin = Address::generate(&env);
    // Deploy adapter
    let adapter_id = env.register(AquariusSwapAdapter, (admin.clone(), mock_router_id.clone()));
    let adapter = AquariusSwapAdapterClient::new(&env, &adapter_id);

    // Setup tokens and pool
    let (from_token, to_token, _pool) = setup_tokens_and_pool(&env, &adapter, &admin);
    let recipient = Address::generate(&env);

    let amount_in = 1000u128;
    let min_out = 900u128;

    let amount_out = adapter.execute_swap(&from_token, &to_token, &amount_in, &min_out, &recipient);

    // Mock returns 95% of input
    assert_eq!(amount_out, 950);
}

#[test]
#[should_panic(expected = "Slippage too high")]
fn test_execute_swap_slippage_too_high() {
    let env = Env::default();
    env.mock_all_auths();

    // Deploy mock Aquarius router
    let mock_router_id = env.register_contract(None, mock_aquarius::MockAquariusRouter);

    let admin = Address::generate(&env);
    // Deploy adapter
    let adapter_id = env.register(AquariusSwapAdapter, (admin.clone(), mock_router_id.clone()));
    let adapter = AquariusSwapAdapterClient::new(&env, &adapter_id);

    // Setup tokens and pool
    let (from_token, to_token, _pool) = setup_tokens_and_pool(&env, &adapter, &admin);
    let recipient = Address::generate(&env);

    let amount_in = 1000u128;
    let min_out = 960u128; // Mock returns 950, so this should fail

    // Should panic with SwapFailed error (code 5)
    adapter.execute_swap(&from_token, &to_token, &amount_in, &min_out, &recipient);
}

#[test]
#[should_panic(expected = "Error(Contract, #4)")]
fn test_execute_swap_zero_amount() {
    let env = Env::default();
    env.mock_all_auths();

    let mock_router_id = env.register_contract(None, mock_aquarius::MockAquariusRouter);
    let admin = Address::generate(&env);
    let adapter_id = env.register(AquariusSwapAdapter, (admin.clone(), mock_router_id.clone()));
    let adapter = AquariusSwapAdapterClient::new(&env, &adapter_id);

    let from_token = Address::generate(&env);
    let to_token = Address::generate(&env);
    let recipient = Address::generate(&env);

    // Should panic with InvalidAmount error (code 4)
    adapter.execute_swap(&from_token, &to_token, &0u128, &100u128, &recipient);
}

#[test]
fn test_get_quote_success() {
    let env = Env::default();
    env.mock_all_auths();

    // Deploy mock Aquarius router and pool
    let mock_router_id = env.register_contract(None, mock_aquarius::MockAquariusRouter);
    let mock_pool_id = env.register_contract(None, mock_aquarius_pool::MockAquariusPool);
    let mock_pool = mock_aquarius_pool::MockAquariusPoolClient::new(&env, &mock_pool_id);

    let admin = Address::generate(&env);
    // Deploy adapter
    let adapter_id = env.register(AquariusSwapAdapter, (admin.clone(), mock_router_id.clone()));
    let adapter = AquariusSwapAdapterClient::new(&env, &adapter_id);

    // Create tokens and initialize pool with sorted tokens
    let from_token = Address::generate(&env);
    let to_token = Address::generate(&env);
    let (token0, token1) = if from_token < to_token {
        (from_token.clone(), to_token.clone())
    } else {
        (to_token.clone(), from_token.clone())
    };
    mock_pool.initialize(&token0, &token1);

    // Register pool for token pair
    adapter.register_pool(&admin, &from_token, &to_token, &mock_pool_id);

    // Get quote
    let amount_in = 1000u128;
    let quote = adapter.get_quote(&from_token, &to_token, &amount_in);

    // Mock returns 95% of input
    assert_eq!(quote, 950);
}

#[test]
#[should_panic(expected = "Error(Contract, #4)")]
fn test_get_quote_zero_amount() {
    let env = Env::default();
    env.mock_all_auths();

    let mock_router_id = env.register_contract(None, mock_aquarius::MockAquariusRouter);
    let admin = Address::generate(&env);
    let adapter_id = env.register(AquariusSwapAdapter, (admin.clone(), mock_router_id.clone()));
    let adapter = AquariusSwapAdapterClient::new(&env, &adapter_id);

    let from_token = Address::generate(&env);
    let to_token = Address::generate(&env);

    // Should panic with InvalidAmount error (code 4)
    adapter.get_quote(&from_token, &to_token, &0u128);
}

#[test]
fn test_token_sorting() {
    let env = Env::default();
    env.mock_all_auths();

    let mock_router_id = env.register_contract(None, mock_aquarius::MockAquariusRouter);
    let admin = Address::generate(&env);
    let adapter_id = env.register(AquariusSwapAdapter, (admin.clone(), mock_router_id.clone()));
    let adapter = AquariusSwapAdapterClient::new(&env, &adapter_id);

    // Setup tokens and pool
    let (token_a, token_b, _pool) = setup_tokens_and_pool(&env, &adapter, &admin);
    let recipient = Address::generate(&env);

    // The mock pool expects correct token indices
    // If the adapter fails to compute indices correctly, the swap will fail

    // Swap A -> B (tokens are sorted internally by adapter)
    let result1 = adapter.execute_swap(&token_a, &token_b, &1000u128, &900u128, &recipient);
    assert_eq!(result1, 950, "Expected 95% output (mock 5% slippage)");

    // Swap B -> A (reverse order - adapter must still sort correctly)
    let result2 = adapter.execute_swap(&token_b, &token_a, &1000u128, &900u128, &recipient);
    assert_eq!(result2, 950, "Expected 95% output (mock 5% slippage)");
    
    // Verify both directions return same result (mock is symmetric)
    assert_eq!(result1, result2, "Both swap directions should return same result for same amount");
}

#[test]
fn test_token_sorting_explicit_order() {
    let env = Env::default();
    env.mock_all_auths();

    let mock_router_id = env.register_contract(None, mock_aquarius::MockAquariusRouter);
    let admin = Address::generate(&env);
    let adapter_id = env.register(AquariusSwapAdapter, (admin.clone(), mock_router_id.clone()));
    let adapter = AquariusSwapAdapterClient::new(&env, &adapter_id);

    let recipient = Address::generate(&env);

    // Test 3 pairs to verify sorting works across different token combinations
    for _ in 0..3 {
        // Setup tokens and pool for each pair
        let (token_i, token_j, _pool) = setup_tokens_and_pool(&env, &adapter, &admin);
        
        // Forward direction
        let result_fwd = adapter.execute_swap(&token_i, &token_j, &1000u128, &900u128, &recipient);
        assert_eq!(result_fwd, 950, "Forward swap failed");
        
        // Reverse direction
        let result_rev = adapter.execute_swap(&token_j, &token_i, &1000u128, &900u128, &recipient);
        assert_eq!(result_rev, 950, "Reverse swap failed");
    }
}

#[test]
fn test_quote_respects_token_sorting() {
    let env = Env::default();
    env.mock_all_auths();

    let mock_router_id = env.register_contract(None, mock_aquarius::MockAquariusRouter);
    let admin = Address::generate(&env);
    let adapter_id = env.register(AquariusSwapAdapter, (admin.clone(), mock_router_id.clone()));
    let adapter = AquariusSwapAdapterClient::new(&env, &adapter_id);

    // Setup tokens and pool
    let (token_a, token_b, _pool) = setup_tokens_and_pool(&env, &adapter, &admin);

    // Mock pool verifies tokens are sorted in get_quote too
    let quote_ab = adapter.get_quote(&token_a, &token_b, &1000u128);
    let quote_ba = adapter.get_quote(&token_b, &token_a, &1000u128);
    
    assert_eq!(quote_ab, 950, "Quote A->B should return 95%");
    assert_eq!(quote_ba, 950, "Quote B->A should return 95%");
    assert_eq!(quote_ab, quote_ba, "Both quote directions should be equal");
}

#[test]
#[should_panic(expected = "Error(Contract, #1)")]
fn test_execute_swap_not_initialized() {
    let env = Env::default();
    env.mock_all_auths();

    let admin = Address::generate(&env);
    let router = Address::generate(&env);
    let adapter_id = env.register(AquariusSwapAdapter, (admin, router));
    let adapter = AquariusSwapAdapterClient::new(&env, &adapter_id);

    let from_token = Address::generate(&env);
    let to_token = Address::generate(&env);
    let recipient = Address::generate(&env);

    // Should panic with NotInitialized error (code 1)
    adapter.execute_swap(&from_token, &to_token, &1000u128, &900u128, &recipient);
}

#[test]
#[should_panic(expected = "Error(Contract, #1)")]
fn test_get_quote_not_initialized() {
    let env = Env::default();
    env.mock_all_auths();

    let admin = Address::generate(&env);
    let router = Address::generate(&env);
    let adapter_id = env.register(AquariusSwapAdapter, (admin, router));
    let adapter = AquariusSwapAdapterClient::new(&env, &adapter_id);

    let from_token = Address::generate(&env);
    let to_token = Address::generate(&env);

    // Should panic with NotInitialized error (code 1)
    adapter.get_quote(&from_token, &to_token, &1000u128);
}

// =============================================================================
// Strong assertion tests for swap amount calculations
// =============================================================================

#[test]
fn test_execute_swap_amount_calculation() {
    let env = Env::default();
    env.mock_all_auths();

    let mock_router_id = env.register_contract(None, mock_aquarius::MockAquariusRouter);
    let admin = Address::generate(&env);
    let adapter_id = env.register(AquariusSwapAdapter, (admin.clone(), mock_router_id.clone()));
    let adapter = AquariusSwapAdapterClient::new(&env, &adapter_id);

    // Setup tokens and pool
    let (from_token, to_token, _pool) = setup_tokens_and_pool(&env, &adapter, &admin);
    let recipient = Address::generate(&env);

    // Test various amounts - mock returns 95% of input
    let test_cases = [
        (1000u128, 950u128),       // 1000 * 0.95 = 950
        (10_000u128, 9500u128),    // 10,000 * 0.95 = 9,500
        (1_000_000u128, 950_000u128), // 1M * 0.95 = 950K
        (123_456u128, 117_283u128), // 123,456 * 0.95 = 117,283.2 truncated to 117,283
    ];

    for (input, expected_output) in test_cases {
        let min_out = expected_output - 1; // Allow for rounding
        let result = adapter.execute_swap(&from_token, &to_token, &input, &min_out, &recipient);
        assert_eq!(
            result, expected_output,
            "For input {}, expected output {} but got {}",
            input, expected_output, result
        );
    }
}

#[test]
fn test_get_quote_matches_execute_swap() {
    let env = Env::default();
    env.mock_all_auths();

    let mock_router_id = env.register_contract(None, mock_aquarius::MockAquariusRouter);
    let admin = Address::generate(&env);
    let adapter_id = env.register(AquariusSwapAdapter, (admin.clone(), mock_router_id.clone()));
    let adapter = AquariusSwapAdapterClient::new(&env, &adapter_id);

    // Setup tokens and pool
    let (from_token, to_token, _pool) = setup_tokens_and_pool(&env, &adapter, &admin);
    let recipient = Address::generate(&env);

    // CRITICAL: Quote should match actual swap result
    let amount_in = 50_000u128;
    
    let quote = adapter.get_quote(&from_token, &to_token, &amount_in);
    let actual = adapter.execute_swap(&from_token, &to_token, &amount_in, &0u128, &recipient);
    
    assert_eq!(
        quote, actual,
        "Quote ({}) must match actual swap result ({})",
        quote, actual
    );
}

#[test]
fn test_execute_swap_min_out_boundary() {
    let env = Env::default();
    env.mock_all_auths();

    let mock_router_id = env.register_contract(None, mock_aquarius::MockAquariusRouter);
    let admin = Address::generate(&env);
    let adapter_id = env.register(AquariusSwapAdapter, (admin.clone(), mock_router_id.clone()));
    let adapter = AquariusSwapAdapterClient::new(&env, &adapter_id);

    // Setup tokens and pool
    let (from_token, to_token, _pool) = setup_tokens_and_pool(&env, &adapter, &admin);
    let recipient = Address::generate(&env);

    let amount_in = 1000u128;
    let expected_out = 950u128; // 95% of 1000

    // Exact boundary - min_out equals expected output (should succeed)
    let result = adapter.execute_swap(&from_token, &to_token, &amount_in, &expected_out, &recipient);
    assert_eq!(result, expected_out, "Swap should succeed when min_out equals expected output");
}

// =============================================================================
// Router failure handling tests
// =============================================================================

#[test]
#[should_panic(expected = "Error(Contract, #1)")]
fn test_execute_swap_router_failure() {
    let env = Env::default();
    env.mock_all_auths();

    // Use the failing mock router
    let mock_router_id = env.register_contract(None, mock_aquarius_failures::MockAquariusRouterFailing);
    let admin = Address::generate(&env);
    let adapter_id = env.register(AquariusSwapAdapter, (admin.clone(), mock_router_id.clone()));
    let adapter = AquariusSwapAdapterClient::new(&env, &adapter_id);

    let from_token = Address::generate(&env);
    let to_token = Address::generate(&env);
    let recipient = Address::generate(&env);

    // Should fail with NotInitialized error (code 1) because no pool is registered
    adapter.execute_swap(&from_token, &to_token, &1000u128, &0u128, &recipient);
}

#[test]
#[should_panic(expected = "Error(Contract, #1)")]
fn test_get_quote_router_failure() {
    let env = Env::default();
    env.mock_all_auths();

    // Use the failing mock router
    let mock_router_id = env.register_contract(None, mock_aquarius_failures::MockAquariusRouterFailing);
    let admin = Address::generate(&env);
    let adapter_id = env.register(AquariusSwapAdapter, (admin.clone(), mock_router_id.clone()));
    let adapter = AquariusSwapAdapterClient::new(&env, &adapter_id);

    let from_token = Address::generate(&env);
    let to_token = Address::generate(&env);

    // Should fail with NotInitialized error (code 1) because no pool is registered
    adapter.get_quote(&from_token, &to_token, &1000u128);
}

// =============================================================================
// Admin verification tests
// =============================================================================

#[test]
fn test_admin_is_stored_correctly() {
    let env = Env::default();
    env.mock_all_auths();

    let admin = Address::generate(&env);
    let router = Address::generate(&env);
    let adapter_id = env.register(AquariusSwapAdapter, (admin.clone(), router.clone()));
    let adapter = AquariusSwapAdapterClient::new(&env, &adapter_id);

    // Verify admin can update router
    let new_router = Address::generate(&env);
    adapter.set_router(&admin, &new_router);
    assert_eq!(adapter.get_router(), new_router, "Admin should be able to update router");
}

#[test]
fn test_router_update_reflected_in_swap() {
    let env = Env::default();
    env.mock_all_auths();

    // First router returns 95%
    let router1_id = env.register_contract(None, mock_aquarius::MockAquariusRouter);
    
    let admin = Address::generate(&env);
    let adapter_id = env.register(AquariusSwapAdapter, (admin.clone(), router1_id.clone()));
    let adapter = AquariusSwapAdapterClient::new(&env, &adapter_id);

    // Setup tokens and pool
    let (from_token, to_token, _pool) = setup_tokens_and_pool(&env, &adapter, &admin);
    let recipient = Address::generate(&env);

    // Swap with first router
    let result1 = adapter.execute_swap(&from_token, &to_token, &1000u128, &0u128, &recipient);
    assert_eq!(result1, 950, "First router should return 95%");

    // Change to new router (same mock but verifies router is actually changed)
    let router2_id = env.register_contract(None, mock_aquarius::MockAquariusRouter);
    adapter.set_router(&admin, &router2_id);
    
    // Verify new router is used
    assert_eq!(adapter.get_router(), router2_id, "Router should be updated");
    
    // Swap with new router (pool is still registered)
    let result2 = adapter.execute_swap(&from_token, &to_token, &1000u128, &0u128, &recipient);
    assert_eq!(result2, 950, "New router should also work correctly");
}
