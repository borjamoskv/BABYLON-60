#![cfg(test)]

//! Integration tests for official RedStone adapter + feed wrapper architecture
//!
//! Tests the new architecture:
//! - Official RedStone adapter (from monorepo)
//! - Per-asset feed wrappers that bridge to K2 Price Oracle interface
//! - Price Oracle consuming wrappers via custom oracle interface

use soroban_sdk::{
    testutils::Address as _,
    Address, Env, String,
};

/// Import official RedStone adapter
pub mod redstone_adapter {
    soroban_sdk::contractimport!(
        file = "../../target/wasm32v1-none/release/redstone_adapter.optimized.wasm"
    );
}

/// Import RedStone feed wrapper
pub mod redstone_feed_wrapper {
    soroban_sdk::contractimport!(
        file = "../../target/wasm32v1-none/release/redstone_feed_wrapper.optimized.wasm"
    );
}

#[test]
fn test_redstone_official_adapter_initialization() {
    let env = Env::default();
    env.mock_all_auths();

    let admin = Address::generate(&env);

    // Deploy official RedStone adapter
    let adapter_id = env.register(redstone_adapter::WASM, ());
    let adapter_client = redstone_adapter::Client::new(&env, &adapter_id);

    // Initialize adapter with owner
    adapter_client.init(&admin);

    println!("✓ Official RedStone adapter initialized successfully");
}

#[test]
fn test_redstone_feed_wrapper_initialization() {
    let env = Env::default();
    env.mock_all_auths();

    let admin = Address::generate(&env);
    let adapter_addr = Address::generate(&env);
    let feed_id = String::from_str(&env, "BTC");

    // Deploy feed wrapper
    let wrapper_id = env.register(redstone_feed_wrapper::WASM, ());
    let wrapper_client = redstone_feed_wrapper::Client::new(&env, &wrapper_id);

    // Initialize wrapper
    wrapper_client.initialize(&admin, &adapter_addr, &feed_id);

    // Verify configuration
    assert_eq!(wrapper_client.get_adapter(), adapter_addr);
    assert_eq!(wrapper_client.get_feed_id(), feed_id);
    assert_eq!(wrapper_client.decimals(), 8);

    println!("✓ RedStone feed wrapper initialized successfully");
    println!("  Adapter: {}", adapter_addr);
    println!("  Feed ID: {}", feed_id);
    println!("  Decimals: 8");
}

#[test]
fn test_redstone_wrapper_architecture() {
    let env = Env::default();
    env.mock_all_auths();

    let admin = Address::generate(&env);

    // 1. Deploy official RedStone adapter
    let adapter_id = env.register(redstone_adapter::WASM, ());
    let adapter_client = redstone_adapter::Client::new(&env, &adapter_id);
    adapter_client.init(&admin);

    // 2. Deploy BTC feed wrapper
    let btc_wrapper_id = env.register(redstone_feed_wrapper::WASM, ());
    let btc_wrapper = redstone_feed_wrapper::Client::new(&env, &btc_wrapper_id);
    btc_wrapper.initialize(&admin, &adapter_id, &String::from_str(&env, "BTC"));

    // 3. Deploy ETH feed wrapper
    let eth_wrapper_id = env.register(redstone_feed_wrapper::WASM, ());
    let eth_wrapper = redstone_feed_wrapper::Client::new(&env, &eth_wrapper_id);
    eth_wrapper.initialize(&admin, &adapter_id, &String::from_str(&env, "ETH"));

    // Verify both wrappers point to same adapter
    assert_eq!(btc_wrapper.get_adapter(), adapter_id);
    assert_eq!(eth_wrapper.get_adapter(), adapter_id);

    // Verify feed IDs are different
    assert_eq!(btc_wrapper.get_feed_id(), String::from_str(&env, "BTC"));
    assert_eq!(eth_wrapper.get_feed_id(), String::from_str(&env, "ETH"));

    println!("✓ RedStone wrapper architecture validated");
    println!("  Official adapter: {}", adapter_id);
    println!("  BTC wrapper: {}", btc_wrapper_id);
    println!("  ETH wrapper: {}", eth_wrapper_id);
    println!("\n  Architecture:");
    println!("    Price Oracle → BTC Wrapper → Official Adapter");
    println!("    Price Oracle → ETH Wrapper → Official Adapter");
}

#[test]
#[ignore = "Requires real RedStone price data to be written to adapter"]
fn test_redstone_wrapper_price_query() {
    let env = Env::default();
    env.mock_all_auths();

    let admin = Address::generate(&env);

    // Deploy adapter and wrapper
    let adapter_id = env.register(redstone_adapter::WASM, ());
    let adapter_client = redstone_adapter::Client::new(&env, &adapter_id);
    adapter_client.init(&admin);

    let wrapper_id = env.register(redstone_feed_wrapper::WASM, ());
    let wrapper_client = redstone_feed_wrapper::Client::new(&env, &wrapper_id);
    wrapper_client.initialize(&admin, &adapter_id, &String::from_str(&env, "BTC"));

    // Note: In production, RedStone price pusher writes prices to adapter
    // Then wrapper reads from adapter and converts format for K2 Price Oracle
    
    // Query price (will return None without real data)
    let btc_asset = k2_shared::Asset::Stellar(Address::generate(&env));
    let price_data = wrapper_client.lastprice(&btc_asset);

    // Without real price data, this returns None
    // In production with real data, it would return Some(PriceData)
    assert!(price_data.is_none(), "No price data without RedStone updates");

    println!("✓ Price query interface validated");
    println!("  Note: Requires RedStone price pusher in production");
}
