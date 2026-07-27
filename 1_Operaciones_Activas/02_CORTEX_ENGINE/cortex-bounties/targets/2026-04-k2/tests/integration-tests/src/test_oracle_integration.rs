#![cfg(test)]

use crate::price_oracle;
use crate::setup::deploy_test_protocol;
use soroban_sdk::Env;

#[test]
fn test_oracle_get_price() {
    let env = Env::default();
    env.mock_all_auths();
    
    let protocol = deploy_test_protocol(&env);
    
    let asset = price_oracle::Asset::Stellar(protocol.underlying_asset.clone());
    let price = protocol.price_oracle.get_asset_price(&asset);
    
    assert_eq!(price, 1_000_000_000_000_000u128, "Default price should be $1.00 (14 decimals). Expected: 1000000000000000, Got: {}", price);
    
    let price_data = protocol.price_oracle.get_asset_price_data(&asset);
    assert_eq!(price_data.price, price, "Price from get_asset_price should match get_asset_price_data. Price: {}, PriceData: {}", price, price_data.price);
}

#[test]
fn test_oracle_get_price_data() {
    let env = Env::default();
    env.mock_all_auths();
    
    let protocol = deploy_test_protocol(&env);
    
    let asset = price_oracle::Asset::Stellar(protocol.underlying_asset.clone());
    let price_data = protocol.price_oracle.get_asset_price_data(&asset);
    
    assert_eq!(price_data.price, 1_000_000_000_000_000u128, "Price must be exactly $1.00 (14 decimals). Expected: 1000000000000000, Got: {}", price_data.price);
    
    let current_timestamp = env.ledger().timestamp();
    assert!(price_data.timestamp <= current_timestamp, "Price timestamp must not be in the future. Timestamp: {}, Current: {}", price_data.timestamp, current_timestamp);
    assert!(price_data.timestamp > 0 || current_timestamp == 0, "Price timestamp must be positive unless ledger timestamp is zero. Timestamp: {}, Current: {}", price_data.timestamp, current_timestamp);
}

#[test]
fn test_oracle_pause_unpause() {
    let env = Env::default();
    env.mock_all_auths();
    
    let protocol = deploy_test_protocol(&env);
    
    let is_paused_initial = protocol.price_oracle.is_paused();
    assert_eq!(is_paused_initial, false, "Should not be paused initially. Got: {}", is_paused_initial);
    
    protocol.price_oracle.pause(&protocol.oracle_admin);
    let is_paused_after_pause = protocol.price_oracle.is_paused();
    assert_eq!(is_paused_after_pause, true, "Should be paused after pause(). Got: {}", is_paused_after_pause);
    assert_ne!(is_paused_initial, is_paused_after_pause, "Pause state should have changed");
    
    protocol.price_oracle.unpause(&protocol.oracle_admin);
    let is_paused_after_unpause = protocol.price_oracle.is_paused();
    assert_eq!(is_paused_after_unpause, false, "Should be unpaused after unpause(). Got: {}", is_paused_after_unpause);
    assert_eq!(is_paused_initial, is_paused_after_unpause, "Should return to initial unpaused state");
    assert_ne!(is_paused_after_pause, is_paused_after_unpause, "Unpause should have changed state from paused");
}

#[test]
fn test_oracle_config() {
    let env = Env::default();
    env.mock_all_auths();
    
    let protocol = deploy_test_protocol(&env);
    
    let config = protocol.price_oracle.get_oracle_config();
    
    assert_eq!(config.max_price_change_bps, 2000u32, "Max price change bps should be default 2000 (20%). Expected: 2000, Got: {}", config.max_price_change_bps);
    assert_eq!(config.price_staleness_threshold, 3600u64, "Price staleness threshold should be default 3600 seconds (1 hour). Expected: 3600, Got: {}", config.price_staleness_threshold);
    assert_eq!(config.price_precision, 14u32, "Price precision should be 14 decimals. Expected: 14, Got: {}", config.price_precision);
    assert_eq!(config.wad_precision, 18u32, "WAD precision should be 18 decimals. Expected: 18, Got: {}", config.wad_precision);
    assert_eq!(config.conversion_factor, 10_000u128, "Conversion factor should be 10000. Expected: 10000, Got: {}", config.conversion_factor);
    assert_eq!(config.basis_points, 10_000u128, "Basis points should be 10000. Expected: 10000, Got: {}", config.basis_points);
    
    let config_second_call = protocol.price_oracle.get_oracle_config();
    assert_eq!(config.max_price_change_bps, config_second_call.max_price_change_bps, "Config should be consistent across calls");
}

#[test]
fn test_oracle_manual_override() {
    let env = Env::default();
    env.mock_all_auths();
    
    let protocol = deploy_test_protocol(&env);
    
    let asset = price_oracle::Asset::Stellar(protocol.underlying_asset.clone());
    let initial_price = protocol.price_oracle.get_asset_price(&asset);
    assert_eq!(initial_price, 1_000_000_000_000_000u128, "Initial price should be $1.00. Expected: 1000000000000000, Got: {}", initial_price);
    
    let config = protocol.price_oracle.get_oracle_config();
    let max_change_bps = config.max_price_change_bps as u128;
    
    let new_price = 1_100_000_000_000_000u128;
    let price_change_bps = initial_price.abs_diff(new_price) * 10_000 / initial_price;
    assert!(price_change_bps <= max_change_bps, "Price change should be within circuit breaker limit. Change: {} bps, Max: {} bps", price_change_bps, max_change_bps);
    assert_ne!(initial_price, new_price, "Test prices must differ. Initial: {}, New: {}", initial_price, new_price);
    
    protocol.price_oracle.set_manual_override(&protocol.oracle_admin, &asset, &Some(new_price), &Some(env.ledger().timestamp() + 86400));
    
    let price_after_override = protocol.price_oracle.get_asset_price(&asset);
    assert_eq!(price_after_override, new_price, "Price should match manual override exactly. Expected: {}, Got: {}", new_price, price_after_override);
    assert_ne!(price_after_override, initial_price, "Price should have changed from initial. Initial: {}, After override: {}", initial_price, price_after_override);
    
    let price_data_after_override = protocol.price_oracle.get_asset_price_data(&asset);
    assert_eq!(price_data_after_override.price, new_price, "Price data should match override. Expected: {}, Got: {}", new_price, price_data_after_override.price);
    assert_eq!(price_data_after_override.price, price_after_override, "Price from get_asset_price and get_asset_price_data should match. Price: {}, PriceData: {}", price_after_override, price_data_after_override.price);
    
    let another_price = 1_050_000_000_000_000u128;
    let second_change_bps = new_price.abs_diff(another_price) * 10_000 / new_price;
    assert!(second_change_bps <= max_change_bps, "Second price change should be within circuit breaker limit. Change: {} bps, Max: {} bps", second_change_bps, max_change_bps);
    assert_ne!(another_price, new_price, "Second override price must differ. First: {}, Second: {}", new_price, another_price);
    assert_ne!(another_price, initial_price, "Second override price must differ from initial. Initial: {}, Second: {}", initial_price, another_price);
    
    protocol.price_oracle.set_manual_override(&protocol.oracle_admin, &asset, &Some(another_price), &Some(env.ledger().timestamp() + 86400));
    let price_after_change = protocol.price_oracle.get_asset_price(&asset);
    assert_eq!(price_after_change, another_price, "Should be able to change override. Expected: {}, Got: {}", another_price, price_after_change);
    assert_ne!(price_after_change, new_price, "Price should have changed from first override. First: {}, After change: {}", new_price, price_after_change);
    assert_ne!(price_after_change, initial_price, "Price should still differ from initial. Initial: {}, After change: {}", initial_price, price_after_change);
    
    let price_data_after_change = protocol.price_oracle.get_asset_price_data(&asset);
    assert_eq!(price_data_after_change.price, another_price, "Price data should match second override. Expected: {}, Got: {}", another_price, price_data_after_change.price);
    assert_eq!(price_data_after_change.price, price_after_change, "Price consistency check: get_asset_price and get_asset_price_data should match. Price: {}, PriceData: {}", price_after_change, price_data_after_change.price);
}

#[test]
fn test_oracle_circuit_breaker_enforcement() {
    let env = Env::default();
    env.mock_all_auths();
    
    let protocol = deploy_test_protocol(&env);
    
    let asset = price_oracle::Asset::Stellar(protocol.underlying_asset.clone());
    let initial_price = protocol.price_oracle.get_asset_price(&asset);
    assert_eq!(initial_price, 1_000_000_000_000_000u128, "Initial price must be exactly $1.00. Expected: 1000000000000000, Got: {}", initial_price);
    
    let config = protocol.price_oracle.get_oracle_config();
    let max_change_bps = config.max_price_change_bps as u128;
    assert_eq!(max_change_bps, 2000, "Max price change must be exactly 2000 bps (20%). Expected: 2000, Got: {}", max_change_bps);
    
    let valid_price = 1_100_000_000_000_000u128;
    let valid_price_change_bps = initial_price.abs_diff(valid_price) * 10_000 / initial_price;
    assert_eq!(valid_price_change_bps, 1000, "Valid price change must be exactly 1000 bps (10%). Expected: 1000, Got: {}", valid_price_change_bps);
    assert!(valid_price_change_bps <= max_change_bps, "Valid price change must be within limit. Change: {} bps, Max: {} bps", valid_price_change_bps, max_change_bps);
    
    protocol.price_oracle.set_manual_override(&protocol.oracle_admin, &asset, &Some(valid_price), &Some(env.ledger().timestamp() + 86400));
    let price_after_valid = protocol.price_oracle.get_asset_price(&asset);
    assert_eq!(price_after_valid, valid_price, "Valid override must succeed. Expected: {}, Got: {}", valid_price, price_after_valid);
    
    let last_price_after_valid = protocol.price_oracle.get_last_price(&asset);
    assert_eq!(last_price_after_valid, Some(valid_price), "Last price must be stored after override. Expected: Some({}), Got: {:?}", valid_price, last_price_after_valid);
    
    let extreme_price = 5_000_000_000_000_000u128;
    let extreme_price_change_bps = valid_price.abs_diff(extreme_price) * 10_000 / valid_price;
    assert!(extreme_price_change_bps > max_change_bps, "Extreme price change must exceed circuit breaker. Change: {} bps, Max: {} bps", extreme_price_change_bps, max_change_bps);
    
    let expiry = env.ledger().timestamp() + 86400; // 24 hours
    let override_result = protocol.price_oracle.try_set_manual_override(&protocol.oracle_admin, &asset, &Some(extreme_price), &Some(expiry));
    
    assert!(override_result.is_err(), "Setting override with price change exceeding circuit breaker must fail at set time. Change: {} bps, Max: {} bps, Last price: {:?}", extreme_price_change_bps, max_change_bps, last_price_after_valid);
    
    let price_after_failed_override = protocol.price_oracle.get_asset_price(&asset);
    assert_eq!(price_after_failed_override, valid_price, "Price must remain at last valid override after failed override attempt. Expected: {}, Got: {}", valid_price, price_after_failed_override);
    assert_ne!(price_after_failed_override, extreme_price, "Price must not be extreme price. Expected != {}, Got: {}", extreme_price, price_after_failed_override);
    
    let last_price_after_failed = protocol.price_oracle.get_last_price(&asset);
    assert_eq!(last_price_after_failed, Some(valid_price), "Last price must remain unchanged after failed query. Expected: Some({}), Got: {:?}", valid_price, last_price_after_failed);
}

#[test]
fn test_oracle_circuit_breaker_boundary_at_limit() {
    let env = Env::default();
    env.mock_all_auths();
    
    let protocol = deploy_test_protocol(&env);
    
    let asset = price_oracle::Asset::Stellar(protocol.underlying_asset.clone());
    let initial_price = protocol.price_oracle.get_asset_price(&asset);
    assert_eq!(initial_price, 1_000_000_000_000_000u128, "Initial price must be exactly $1.00");
    
    let config = protocol.price_oracle.get_oracle_config();
    let max_change_bps = config.max_price_change_bps as u128;
    assert_eq!(max_change_bps, 2000, "Max price change must be exactly 2000 bps (20%)");
    
    let price_at_limit = 1_200_000_000_000_000u128;
    let price_change_bps = initial_price.abs_diff(price_at_limit) * 10_000 / initial_price;
    assert_eq!(price_change_bps, 2000, "Price change must be exactly at limit. Expected: 2000 bps, Got: {} bps", price_change_bps);
    
    protocol.price_oracle.set_manual_override(&protocol.oracle_admin, &asset, &Some(price_at_limit), &Some(env.ledger().timestamp() + 86400));
    let price_after_at_limit = protocol.price_oracle.get_asset_price(&asset);
    assert_eq!(price_after_at_limit, price_at_limit, "Price change exactly at limit must be allowed. Expected: {}, Got: {}", price_at_limit, price_after_at_limit);
    
    let last_price_at_limit = protocol.price_oracle.get_last_price(&asset);
    assert_eq!(last_price_at_limit, Some(price_at_limit), "Last price must be updated to price at limit. Expected: Some({}), Got: {:?}", price_at_limit, last_price_at_limit);
    
    let price_just_over_limit = 1_441_000_000_000_000u128;
    let over_limit_change_bps = price_at_limit.abs_diff(price_just_over_limit) * 10_000 / price_at_limit;
    assert_eq!(over_limit_change_bps, 2008, "Price change must be just over limit. Expected: 2008 bps (20.08%), Got: {} bps", over_limit_change_bps);
    assert!(over_limit_change_bps > max_change_bps, "Price change must exceed limit. Change: {} bps, Max: {} bps", over_limit_change_bps, max_change_bps);
    
    let expiry = env.ledger().timestamp() + 86400; // 24 hours
    let override_result = protocol.price_oracle.try_set_manual_override(&protocol.oracle_admin, &asset, &Some(price_just_over_limit), &Some(expiry));
    assert!(override_result.is_err(), "Price change over limit must be rejected. Change: {} bps, Max: {} bps", over_limit_change_bps, max_change_bps);
    
    let price_after_failed_over_limit = protocol.price_oracle.get_asset_price(&asset);
    assert_eq!(price_after_failed_over_limit, price_at_limit, "Price must remain at limit price after failed over-limit attempt. Expected: {}, Got: {}", price_at_limit, price_after_failed_over_limit);
}

#[test]
fn test_oracle_circuit_breaker_price_decrease_rejection() {
    let env = Env::default();
    env.mock_all_auths();
    
    let protocol = deploy_test_protocol(&env);
    
    let asset = price_oracle::Asset::Stellar(protocol.underlying_asset.clone());
    let initial_price = protocol.price_oracle.get_asset_price(&asset);
    assert_eq!(initial_price, 1_000_000_000_000_000u128, "Initial price must be exactly $1.00");
    
    let config = protocol.price_oracle.get_oracle_config();
    let max_change_bps = config.max_price_change_bps as u128;
    
    let high_price = 1_200_000_000_000_000u128;
    let high_price_change_bps = initial_price.abs_diff(high_price) * 10_000 / initial_price;
    assert!(high_price_change_bps <= max_change_bps, "High price change must be within limit. Change: {} bps, Max: {} bps", high_price_change_bps, max_change_bps);
    
    protocol.price_oracle.set_manual_override(&protocol.oracle_admin, &asset, &Some(high_price), &Some(env.ledger().timestamp() + 86400));
    let price_after_high = protocol.price_oracle.get_asset_price(&asset);
    assert_eq!(price_after_high, high_price, "High price must be set. Expected: {}, Got: {}", high_price, price_after_high);
    
    let last_price_after_high = protocol.price_oracle.get_last_price(&asset);
    assert_eq!(last_price_after_high, Some(high_price), "Last price must be stored after high price. Expected: Some({}), Got: {:?}", high_price, last_price_after_high);
    
    let extreme_low_price = 960_000_000_000_000u128;
    let price_decrease_bps = high_price.abs_diff(extreme_low_price) * 10_000 / high_price;
    assert_eq!(price_decrease_bps, 2000, "Price decrease must be exactly at limit. Expected: 2000 bps (20%), Got: {} bps", price_decrease_bps);
    
    protocol.price_oracle.set_manual_override(&protocol.oracle_admin, &asset, &Some(extreme_low_price), &Some(env.ledger().timestamp() + 86400));
    let price_after_at_limit_decrease = protocol.price_oracle.get_asset_price(&asset);
    assert_eq!(price_after_at_limit_decrease, extreme_low_price, "Price decrease at limit must be allowed. Expected: {}, Got: {}", extreme_low_price, price_after_at_limit_decrease);
    
    let price_below_limit = 767_000_000_000_000u128;
    let below_limit_decrease_bps = extreme_low_price.abs_diff(price_below_limit) * 10_000 / extreme_low_price;
    assert!(below_limit_decrease_bps > max_change_bps, "Price decrease must exceed circuit breaker. Decrease: {} bps, Max: {} bps", below_limit_decrease_bps, max_change_bps);
    assert!(below_limit_decrease_bps >= 2000 && below_limit_decrease_bps <= 2100, "Price decrease must be just over limit (20-21%). Got: {} bps", below_limit_decrease_bps);
    
    let expiry = env.ledger().timestamp() + 86400; // 24 hours
    let override_result = protocol.price_oracle.try_set_manual_override(&protocol.oracle_admin, &asset, &Some(price_below_limit), &Some(expiry));
    assert!(override_result.is_err(), "Large price decrease must be rejected by circuit breaker. Decrease: {} bps, Max: {} bps", below_limit_decrease_bps, max_change_bps);
    
    let price_after_failed_decrease = protocol.price_oracle.get_asset_price(&asset);
    assert_eq!(price_after_failed_decrease, extreme_low_price, "Price must remain at limit price after failed decrease attempt. Expected: {}, Got: {}", extreme_low_price, price_after_failed_decrease);
}

#[test]
fn test_oracle_circuit_breaker_reset_functionality() {
    let env = Env::default();
    env.mock_all_auths();
    
    let protocol = deploy_test_protocol(&env);
    
    let asset = price_oracle::Asset::Stellar(protocol.underlying_asset.clone());
    let initial_price = protocol.price_oracle.get_asset_price(&asset);
    assert_eq!(initial_price, 1_000_000_000_000_000u128, "Initial price must be exactly $1.00");
    
    let config = protocol.price_oracle.get_oracle_config();
    let max_change_bps = config.max_price_change_bps as u128;
    
    let valid_price = 1_100_000_000_000_000u128;
    protocol.price_oracle.set_manual_override(&protocol.oracle_admin, &asset, &Some(valid_price), &Some(env.ledger().timestamp() + 86400));
    let price_after_valid = protocol.price_oracle.get_asset_price(&asset);
    assert_eq!(price_after_valid, valid_price, "Valid price must be set");
    
    let last_price_before_reset = protocol.price_oracle.get_last_price(&asset);
    assert_eq!(last_price_before_reset, Some(valid_price), "Last price must be stored. Expected: Some({}), Got: {:?}", valid_price, last_price_before_reset);
    
    protocol.price_oracle.reset_circuit_breaker(&protocol.oracle_admin, &asset);
    
    let last_price_after_reset = protocol.price_oracle.get_last_price(&asset);
    assert_eq!(last_price_after_reset, None, "Last price must be cleared after reset. Expected: None, Got: {:?}", last_price_after_reset);
    
    let extreme_price = 5_000_000_000_000_000u128;
    let extreme_price_change_bps = valid_price.abs_diff(extreme_price) * 10_000 / valid_price;
    assert!(extreme_price_change_bps > max_change_bps, "Extreme price change must exceed limit. Change: {} bps, Max: {} bps", extreme_price_change_bps, max_change_bps);
    
    protocol.price_oracle.set_manual_override(&protocol.oracle_admin, &asset, &Some(extreme_price), &Some(env.ledger().timestamp() + 86400));
    let price_after_reset = protocol.price_oracle.get_asset_price(&asset);
    assert_eq!(price_after_reset, extreme_price, "After reset, extreme price change must be allowed. Expected: {}, Got: {}", extreme_price, price_after_reset);
    
    let last_price_after_extreme = protocol.price_oracle.get_last_price(&asset);
    assert_eq!(last_price_after_extreme, Some(extreme_price), "Last price must be updated after extreme change. Expected: Some({}), Got: {:?}", extreme_price, last_price_after_extreme);
}

#[test]
fn test_oracle_circuit_breaker_multiple_valid_changes() {
    let env = Env::default();
    env.mock_all_auths();
    
    let protocol = deploy_test_protocol(&env);
    
    let asset = price_oracle::Asset::Stellar(protocol.underlying_asset.clone());
    let initial_price = protocol.price_oracle.get_asset_price(&asset);
    assert_eq!(initial_price, 1_000_000_000_000_000u128, "Initial price must be exactly $1.00");
    
    let config = protocol.price_oracle.get_oracle_config();
    let max_change_bps = config.max_price_change_bps as u128;
    
    let price1 = 1_050_000_000_000_000u128;
    let change1_bps = initial_price.abs_diff(price1) * 10_000 / initial_price;
    assert!(change1_bps <= max_change_bps, "First change must be within limit. Change: {} bps, Max: {} bps", change1_bps, max_change_bps);
    
    protocol.price_oracle.set_manual_override(&protocol.oracle_admin, &asset, &Some(price1), &Some(env.ledger().timestamp() + 86400));
    let price_after_1 = protocol.price_oracle.get_asset_price(&asset);
    assert_eq!(price_after_1, price1, "First price change must succeed. Expected: {}, Got: {}", price1, price_after_1);
    
    let price2 = 1_100_000_000_000_000u128;
    let change2_bps = price1.abs_diff(price2) * 10_000 / price1;
    assert!(change2_bps <= max_change_bps, "Second change must be within limit. Change: {} bps, Max: {} bps", change2_bps, max_change_bps);
    
    protocol.price_oracle.set_manual_override(&protocol.oracle_admin, &asset, &Some(price2), &Some(env.ledger().timestamp() + 86400));
    let price_after_2 = protocol.price_oracle.get_asset_price(&asset);
    assert_eq!(price_after_2, price2, "Second price change must succeed. Expected: {}, Got: {}", price2, price_after_2);
    
    let price3 = 1_150_000_000_000_000u128;
    let change3_bps = price2.abs_diff(price3) * 10_000 / price2;
    assert!(change3_bps <= max_change_bps, "Third change must be within limit. Change: {} bps, Max: {} bps", change3_bps, max_change_bps);
    
    protocol.price_oracle.set_manual_override(&protocol.oracle_admin, &asset, &Some(price3), &Some(env.ledger().timestamp() + 86400));
    let price_after_3 = protocol.price_oracle.get_asset_price(&asset);
    assert_eq!(price_after_3, price3, "Third price change must succeed. Expected: {}, Got: {}", price3, price_after_3);
    
    let last_price_final = protocol.price_oracle.get_last_price(&asset);
    assert_eq!(last_price_final, Some(price3), "Last price must be updated to final price. Expected: Some({}), Got: {:?}", price3, last_price_final);
}

#[test]
fn test_oracle_precision_normalization() {
    let env = Env::default();
    env.mock_all_auths();
    
    let protocol = deploy_test_protocol(&env);
    
    let config = protocol.price_oracle.get_oracle_config();
    assert_eq!(config.price_precision, 14u32, "Default precision should be 14 decimals");
    
    let reflector_contract = protocol.price_oracle.get_reflector_contract();
    assert!(reflector_contract.is_some(), "Reflector contract must be configured");
}
