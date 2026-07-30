# Swap Collateral Interest Rates Computed with Stale Supply Data

## Severity: Medium

## Summary

`swap_collateral` calls `update_state_without_store` at the beginning, then performs `burn_scaled_and_transfer_to` and `mint_scaled` operations that modify `total_supply_scaled` in the aToken contracts. At the end, `update_interest_rates_and_store` is called with the original (now stale) reserve data, passing `None` for the `a_token_scaled_total` parameter. This causes interest rates to be computed against pre-operation supply values.

## Vulnerability Detail

The `swap_collateral` function (`kinetic-router/src/swap.rs`) deliberately uses `update_state_without_store` to avoid writing intermediate index values:

```rust
// swap.rs:96-99 — State computed but NOT stored
let updated_from_reserve_data =
    calculation::update_state_without_store(&env, &from_reserve_data)?;
let updated_to_reserve_data =
    calculation::update_state_without_store(&env, &to_reserve_data)?;
```

Subsequently, the function calls `burn_scaled_and_transfer_to` on the source aToken (which modifies `total_supply_scaled` by subtracting burned scaled units) and `mint_scaled` on the destination aToken (which modifies `total_supply_scaled` by adding minted scaled units):

```rust
// swap.rs:131-142 — Burns from source aToken, modifying its total_supply_scaled
let (new_user_scaled_balance, from_supply_scaled, actual_amount) = 
    burn_scaled_and_transfer_to(...)?;

// swap.rs:305-316 — Mints to destination aToken, modifying its total_supply_scaled  
let (to_user_new_scaled_balance, to_supply_scaled) = 
    mint_scaled(...)?;
```

Both operations return the post-operation `total_supply_scaled` values (`from_supply_scaled` and `to_supply_scaled`). However, these values are **never passed** to `update_interest_rates_and_store`:

```rust
// swap.rs:366-367 — Interest rates computed with stale data (None = re-read from storage)
calculation::update_interest_rates_and_store(
    &env, &from_asset, &updated_from_reserve_data, None, None)?;
calculation::update_interest_rates_and_store(
    &env, &to_asset, &updated_to_reserve_data, None, None)?;
```

The `None` for `a_token_scaled_total` causes `update_interest_rates_and_store` to query the aToken contract for `total_supply` via a cross-contract call. While this re-read should normally get the correct post-operation value, the `updated_from_reserve_data` struct still contains the pre-burn `liquidity_index` that was computed via `update_state_without_store`. The interest rate calculation uses this stale index to convert scaled supply into underlying, which mismatches the actual token state.

Compare with `liquidation.rs`, which correctly passes the known totals:

```rust
// liquidation.rs:668-683 — CORRECT pattern: passes known post-operation totals
calculation::update_interest_rates_and_store(
    env, &debt_asset, &post_burn_debt_reserve,
    a_token_scaled_total, debt_token_scaled_total, // ← Passes actual values
)?;
```

## Impact

Interest rates for both source and destination reserves will be temporarily mispriced after each `swap_collateral` operation. The utilization calculation uses `total_supply` and `total_borrows` — if `total_supply` is stale-high (pre-burn for source) or stale-low (pre-mint for destination), the resulting utilization and thus the variable borrow rate will be incorrect.

In high-volume swap scenarios, this creates a window where:
- Borrowers on the source reserve pay incorrect (likely lower) rates
- Suppliers on the destination reserve earn incorrect rates  
- MEV extractors can time borrows to coincide with stale rate windows

The magnitude scales with swap volume relative to reserve size.

## Code Snippet

Stale state used for interest rate computation:
https://github.com/code-423n4/2026-04-k2/blob/main/contracts/kinetic-router/src/swap.rs#L96-L99

Return values containing correct post-op totals (ignored):
https://github.com/code-423n4/2026-04-k2/blob/main/contracts/kinetic-router/src/swap.rs#L137
https://github.com/code-423n4/2026-04-k2/blob/main/contracts/kinetic-router/src/swap.rs#L311

Interest rate computation with None (stale):
https://github.com/code-423n4/2026-04-k2/blob/main/contracts/kinetic-router/src/swap.rs#L366-L367

Correct pattern in liquidation.rs:
https://github.com/code-423n4/2026-04-k2/blob/main/contracts/kinetic-router/src/liquidation.rs#L668-L683

## Tool Used

Manual review

## Recommendation

Pass the known post-operation scaled totals to `update_interest_rates_and_store`:

```diff
-calculation::update_interest_rates_and_store(&env, &from_asset, &updated_from_reserve_data, None, None)?;
-calculation::update_interest_rates_and_store(&env, &to_asset, &updated_to_reserve_data, None, None)?;
+// Convert i128 scaled totals to u128 for the interest rate function
+let from_a_token_total = Some(safe_i128_to_u128(&env, from_supply_scaled));
+let to_a_token_total = Some(safe_i128_to_u128(&env, to_supply_scaled));
+calculation::update_interest_rates_and_store(&env, &from_asset, &updated_from_reserve_data, from_a_token_total, None)?;
+calculation::update_interest_rates_and_store(&env, &to_asset, &updated_to_reserve_data, to_a_token_total, None)?;
```

This follows the same pattern already used in `liquidation.rs:668-683`.
