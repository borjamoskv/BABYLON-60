# Oracle Cache Poisoning via Incomplete Circuit Breaker Reset

## Severity: High

## Summary

`PriceOracleContract.reset_circuit_breaker` clears the `last_price` baseline but fails to clear the `last_price_data` TTL cache. After a circuit breaker reset, the oracle serves stale cached prices for up to `cache_ttl` seconds (max 3600s), causing incorrect price data for all downstream operations (liquidations, borrows, withdrawals).

## Vulnerability Detail

The price oracle implements a TTL-based cache (`last_price_data`) alongside a circuit breaker baseline (`last_price`). The `reset_circuit_breaker` function is designed to clear the circuit breaker baseline after legitimate large price movements, but it only clears `last_price` and **does not clear** `last_price_data`.

**Vulnerable function** (`price-oracle/src/contract.rs:613-618`):
```rust
pub fn reset_circuit_breaker(env: Env, caller: Address, asset: Asset) -> Result<(), OracleError> {
    admin::require_admin(&env, &caller).map_err(|_| OracleError::Unauthorized)?;
    caller.require_auth();
    storage::clear_last_price(&env, &asset);
    // BUG: Missing storage::clear_last_price_data(&env, &asset);
    Ok(())
}
```

The same issue exists in `reset_all_circuit_breakers` (`contract.rs:625-633`):
```rust
pub fn reset_all_circuit_breakers(env: Env, caller: Address) -> Result<(), OracleError> {
    // ...
    for i in 0..asset_list.len() {
        let asset = asset_list.get(i).ok_or(OracleError::AssetPriceNotFound)?;
        storage::clear_last_price(&env, &asset);
        // BUG: Missing storage::clear_last_price_data(&env, &asset);
    }
    Ok(())
}
```

Compare with `set_manual_override` which correctly clears **both** (`contract.rs:150`):
```rust
// Correct pattern used elsewhere:
storage::clear_last_price_data(&env, &asset);
```

**Cache serving path** (`contract.rs:366-379`):
```rust
let cache_ttl = storage::get_price_cache_ttl(&env);
if cache_ttl > 0 {
    if let Some(cached) = storage::get_last_price_data(&env, &asset) {
        let cache_age = current_time.saturating_sub(cached.cached_at);
        let price_age = current_time.saturating_sub(cached.timestamp);
        if cache_age <= cache_ttl && price_age <= oracle_config.price_staleness_threshold {
            // Returns stale cached price — was NOT cleared by reset_circuit_breaker
            return Ok(PriceData { price: cached.price, timestamp: cached.timestamp });
        }
    }
}
```

**Attack scenario:**

1. Asset X price is $100, stored as `last_price = 100` and `last_price_data = {price: 100, ...}`
2. Flash crash occurs — real price drops to $50
3. Circuit breaker blocks $50 price (>50% deviation from $100 baseline)
4. Admin calls `reset_circuit_breaker` to allow $50 through
5. `last_price` is cleared ✓, but `last_price_data` still holds `{price: 100}`
6. Next query within `cache_ttl` window returns `$100` from cache
7. `validate_price_change` passes for $100 (no baseline = any price accepted)
8. `$100` is set as the new `last_price` baseline
9. The actual fresh oracle price of `$50` is now **rejected** by the circuit breaker as >50% deviation from the $100 baseline that was just re-established from stale cache

The admin's reset action is effectively reversed by the stale cache.

## Impact

After circuit breaker reset, the oracle can serve **stale prices for up to 3600 seconds** (the maximum `cache_ttl`). During this window:

- **Liquidations operate on wrong prices**: Positions that should be liquidated at real market prices are evaluated using stale cached prices. Under-water positions remain unliquidated, accumulating bad debt.
- **New borrows use incorrect collateral valuation**: Users can borrow more than their collateral warrants.
- **The circuit breaker reset itself becomes unreliable**: The intended purpose (allowing a new price through after a large movement) is subverted by the stale cache re-establishing the old baseline.

This is particularly dangerous because `reset_circuit_breaker` is designed to be called during volatile market conditions — exactly when price accuracy matters most.

## Code Snippet

Missing cache clear in `reset_circuit_breaker`:
https://github.com/code-423n4/2026-04-k2/blob/main/contracts/price-oracle/src/contract.rs#L613-L618

Missing cache clear in `reset_all_circuit_breakers`:
https://github.com/code-423n4/2026-04-k2/blob/main/contracts/price-oracle/src/contract.rs#L625-L633

Correct pattern in `set_manual_override`:
https://github.com/code-423n4/2026-04-k2/blob/main/contracts/price-oracle/src/contract.rs#L150

Cache serving path that returns stale data:
https://github.com/code-423n4/2026-04-k2/blob/main/contracts/price-oracle/src/contract.rs#L366-L379

## Tool Used

Manual review

## Recommendation

Add `clear_last_price_data` to both reset functions:

```diff
 pub fn reset_circuit_breaker(env: Env, caller: Address, asset: Asset) -> Result<(), OracleError> {
     admin::require_admin(&env, &caller).map_err(|_| OracleError::Unauthorized)?;
     caller.require_auth();
     storage::clear_last_price(&env, &asset);
+    storage::clear_last_price_data(&env, &asset);
     Ok(())
 }

 pub fn reset_all_circuit_breakers(env: Env, caller: Address) -> Result<(), OracleError> {
     admin::require_admin(&env, &caller).map_err(|_| OracleError::Unauthorized)?;
     caller.require_auth();
     let asset_list = storage::get_asset_list(&env);
     for i in 0..asset_list.len() {
         let asset = asset_list.get(i).ok_or(OracleError::AssetPriceNotFound)?;
         storage::clear_last_price(&env, &asset);
+        storage::clear_last_price_data(&env, &asset);
     }
     Ok(())
 }
```
