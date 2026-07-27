#[cfg(test)]
mod test {
    #[test]
    fn test_price_calculation_no_overflow() {
        let user_balance: u128 = 10000000000000;
        let asset_price: u128 = 1000000;
        let asset_decimals: u32 = 7;

        let product = user_balance.checked_mul(asset_price);
        assert!(product.is_some(), "Product should not overflow");

        let divisor = 10_u128.pow(asset_decimals);
        let collateral_value_base = product.unwrap().checked_div(divisor);
        assert!(collateral_value_base.is_some(), "Division should not fail");

        // Convert to WAD (multiply by 10^12 to go from 6 decimals to 18)
        let collateral_value = collateral_value_base
            .unwrap()
            .checked_mul(1_000_000_000_000);
        assert!(
            collateral_value.is_some(),
            "WAD conversion should not overflow"
        );

        assert_eq!(collateral_value.unwrap(), 1_000_000_000_000_000_000_000_000);
    }

    #[test]
    fn test_large_values() {
        let user_balance: u128 = 1000000000000000;
        let asset_price: u128 = 1000000;
        let asset_decimals: u32 = 7;

        let product = user_balance.checked_mul(asset_price);
        assert!(product.is_some(), "Product should not overflow");

        let divisor = 10_u128.pow(asset_decimals);
        let collateral_value_base = product.unwrap().checked_div(divisor);
        assert!(collateral_value_base.is_some());

        let collateral_value = collateral_value_base
            .unwrap()
            .checked_mul(1_000_000_000_000);
        assert!(collateral_value.is_some(), "Should handle 100M USDC");
    }

    #[test]
    fn test_different_decimals() {
        let user_balance: u128 = 1000000000000;
        let asset_price: u128 = 1000000;
        let asset_decimals: u32 = 6;

        let product = user_balance.checked_mul(asset_price);
        assert!(product.is_some());

        let divisor = 10_u128.pow(asset_decimals);
        let collateral_value_base = product.unwrap().checked_div(divisor);
        assert!(collateral_value_base.is_some());

        let collateral_value = collateral_value_base
            .unwrap()
            .checked_mul(1_000_000_000_000);
        assert!(collateral_value.is_some());

        assert_eq!(collateral_value.unwrap(), 1_000_000_000_000_000_000_000_000);
    }
}
