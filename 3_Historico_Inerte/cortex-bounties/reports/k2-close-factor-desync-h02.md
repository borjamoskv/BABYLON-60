# Close Factor Enforcement Inconsistency Between LiquidationEngine and KineticRouter

## Severity: High

## Summary

`LiquidationEngine.calculate_liquidation` enforces the close factor against the user's **total debt across all reserves** (`total_debt_base`), while `KineticRouter.validate_close_factor` enforces it against the **individual reserve debt** (`individual_debt_base`). For users with positions across multiple reserves, the effective maximum liquidatable amount differs between the two entry points, enabling exploitation of the inconsistency.

## Vulnerability Detail

The K2 protocol has two paths for liquidation, each with a different interpretation of "close factor base":

**LiquidationEngine** (`liquidation-engine/src/calculation.rs:49-56`):
```rust
let close_factor = storage::get_close_factor(env);
// Uses total_debt_base — sum of ALL user debt across ALL reserves
let debt_u256 = U256::from_u128(env, user_account_data.total_debt_base);
let factor_u256 = U256::from_u128(env, close_factor);
let bps_u256 = U256::from_u128(env, BASIS_POINTS_MULTIPLIER);
let max_liquidatable_debt_total = (debt_u256.mul(&factor_u256).div(&bps_u256))
    .to_u128()
    .ok_or(KineticRouterError::MathOverflow)?;
```

**KineticRouter** (`kinetic-router/src/liquidation.rs:225-237`):
```rust
// Uses individual_debt_base — debt in ONE reserve only
let individual_debt_base = calculation::value_in_base(
    env, safe_i128_to_u128(env, debt_balance), debt_price, oracle_to_wad, debt_decimals_pow,
)?;
let debt_to_cover_base = calculation::value_in_base(
    env, debt_to_cover, debt_price, oracle_to_wad, debt_decimals_pow,
)?;
validate_close_factor(
    env, user_account_data.health_factor,
    individual_debt_base, individual_collateral_base, debt_to_cover_base,
)?;
```

**Note the asymmetry:**
- The engine computes `close_factor × total_debt_base` — this is the global cap
- The router computes `close_factor × individual_debt_base` per reserve — this is a per-reserve cap
- Neither system coordinates with the other

**Exploitation path:**

Consider a borrower with positions across 3 debt reserves:
- Reserve A: $1,000 debt
- Reserve B: $1,000 debt
- Reserve C: $1,000 debt
- Total debt: $3,000
- Close factor: 50%

An attacker can use **both entry points** in a single transaction:

| Step | Entry Point | Reserve | Base Used | Max Allowed | Liquidated |
|:----:|:------------|:-------:|----------:|------------:|-----------:|
| 1 | Engine | A | $3,000 (total) | $1,500 | $1,000 (A fully) |
| 2 | Router | B | $1,000 (individual) | $500 | $500 |
| 3 | Router | C | $1,000 (individual) | $500 | $500 |

**Total liquidated: $2,000 of $3,000 debt = 66.7%** — exceeding the intended 50% cap.

If the attacker also exploits V-001 (no cumulative tracking in router), steps 2-3 can be iterated, pushing total liquidation toward ~83%+ in a single transaction.

## Impact

The close factor — the protocol's core borrower protection — becomes inconsistent:

1. **Multi-reserve positions are disproportionately vulnerable**: Users diversifying across reserves (the protocol's intended use case) face a higher effective close factor than users concentrated in a single reserve.
2. **Cumulative liquidation tracking is fragmented**: Engine tracks cumulative, router doesn't. An attacker can use the engine for the first liquidation (large base), then router for per-reserve liquidations (independent bases).
3. **Bad debt amplification**: Over-liquidation beyond 50% means more collateral seized with liquidation bonus, faster position deterioration, and higher probability of bad debt creation.

## Code Snippet

Engine using total debt base:
https://github.com/code-423n4/2026-04-k2/blob/main/contracts/liquidation-engine/src/calculation.rs#L49-L56

Router using individual debt base:
https://github.com/code-423n4/2026-04-k2/blob/main/contracts/kinetic-router/src/liquidation.rs#L225-L237

Router close factor validation function:
https://github.com/code-423n4/2026-04-k2/blob/main/contracts/kinetic-router/src/liquidation.rs#L12-L39

## Tool Used

Manual review

## Recommendation

Unify close factor enforcement:

1. **Both entry points must use the same debt base.** Recommend `total_debt_base` (matching Aave V3 design) for both engine and router.

2. **Share the cumulative accumulator.** The router must read and update `USER_LIQUIDATED_THIS_TX` from the engine's storage, or both must use a shared storage location.

```diff
 // In KineticRouter::validate_close_factor — use total debt, not individual
-let max_liquidatable_debt = individual_debt_base
+let max_liquidatable_debt = user_account_data.total_debt_base
     .checked_mul(close_factor)?
     .checked_div(BASIS_POINTS_MULTIPLIER)?;
```
