# Unbounded Bad Debt Deficit Accumulation without Resolution Mechanism

## Severity: Medium

## Summary

In the K2 protocol, when a liquidation results in "bad debt" (where the debt to cover exceeds the available collateral), the remaining debt is burned and recorded as a "deficit" in the reserve. However, this deficit grows unboundedly and there is no mechanism in the protocol to resolve it, recapitalize the reserve, or socialize the loss. This creates a hidden insolvency that will eventually lead to a bank-run as the total underlying assets in the pool become less than the total aToken claims.

## Vulnerability Detail

When `collateral_cap_triggered` is true during liquidation (`liquidation.rs:600-615`), the protocol acknowledges that the position is underwater. The remaining debt is handled by:

1. Burning the excess debt token balance.
2. **Adding to the reserve deficit** (`liquidation.rs:610`).

**Code Snippet** (`kinetic-router/src/liquidation.rs:610`):
```rust
// remaining_debt_u128 is the debt that couldn't be covered by collateral
storage::add_reserve_deficit(env, &debt_asset, remaining_debt_u128);
```

The `add_reserve_deficit` function simply increments a counter in storage. This counter is used in `calculate_index` and `calculate_interest_rates` to adjust the pool's "total debt" view, but there is **no code in the entire repository** that allows for:

- **Recapitalization**: No way for an admin or insurance fund to "repay" the deficit.
- **Socialization**: No mechanism to haircut aToken holders or reduce the `liquidity_index` to reflect the loss.
- **Circuit Breaker**: No threshold where the reserve is paused if the deficit becomes too large relative to TVL.

## Impact

This is a **systemic economic vulnerability**. Over time, as small amounts of bad debt accumulate:

1. The `total_supply` of aTokens (claims) remains unchanged.
2. The `total_underlying` (assets) is reduced by the burned debt but not replenished.
3. The "exchange rate" between aTokens and underlying becomes increasingly fictional.
4. Once the deficit exceeds the accrued interest (the "buffer"), the protocol becomes insolvent.
5. **Bank Run Risk**: Informed users will withdraw their assets early at 1:1, leaving late withdrawers with unbacked aTokens that cannot be redeemed for underlying.

While Aave V3 handles this via a "Backstop Module" or "Insurance Fund", K2 currently only implements the "deficit tracking" part of the equation without the "deficit resolution" part.

## Code Snippet

Unbounded deficit addition:
https://github.com/code-423n4/2026-04-k2/blob/main/contracts/kinetic-router/src/liquidation.rs#L610

Storage implementation (no cap or resolution):
https://github.com/code-423n4/2026-04-k2/blob/main/contracts/kinetic-router/src/storage.rs (Search for `add_reserve_deficit`)

## Tool Used

Manual review + Economic analysis

## Recommendation

Implement a formal deficit resolution mechanism:

1. **Backstop Draw**: Allow the protocol to draw from an insurance fund or treasury to repay the reserve deficit.
2. **Deficit Socialization**: Periodically "realize" the deficit by decreasing the `liquidity_index` of the reserve, proportionally reducing the balance of all aToken holders.
3. **Threshold Pausing**: If `deficit / total_supply > threshold` (e.g. 5%), automatically pause borrowing and withdrawals for that reserve to prevent a bank run.
