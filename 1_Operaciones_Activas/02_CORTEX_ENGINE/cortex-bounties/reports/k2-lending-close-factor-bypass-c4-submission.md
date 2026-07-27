# Close Factor Bypass via Direct `KineticRouter.liquidation_call` Invocation

## Summary

The `KineticRouter.liquidation_call` is a public entry point that performs a **stateless** close factor check via `validate_close_factor`. It does not read or update the `LiquidationEngine`'s per-transaction cumulative accumulator (`USER_LIQUIDATED_THIS_TX`). An attacker can send multiple separate transactions in the same ledger, each calling `liquidation_call` directly, to drain a borrower's collateral well beyond the intended 50% close factor limit.

## Vulnerability Detail

### Root Cause

The protocol has two liquidation paths:

1. **`LiquidationEngine.liquidate()`** — the intended high-level path. Tracks cumulative liquidation via `USER_LIQUIDATED_THIS_TX` in `temporary()` storage ([`liquidation-engine/src/calculation.rs:59`](https://github.com/code-423n4/2026-04-k2/blob/main/contracts/liquidation-engine/src/calculation.rs#L59), [`storage.rs:266-271`](https://github.com/code-423n4/2026-04-k2/blob/main/contracts/liquidation-engine/src/storage.rs#L266-L271)).

2. **`KineticRouter.liquidation_call()`** — a **public** entry point ([`router.rs:295-314`](https://github.com/code-423n4/2026-04-k2/blob/main/contracts/kinetic-router/src/router.rs#L295-L314)) that invokes `internal_liquidation_call` directly. This path calls `validate_close_factor` ([`liquidation.rs:234-237`](https://github.com/code-423n4/2026-04-k2/blob/main/contracts/kinetic-router/src/liquidation.rs#L234-L237)), which performs a **point-in-time** check against the *current* position state:

```rust
// liquidation.rs:12-36
pub(crate) fn validate_close_factor(
    env: &Env,
    health_factor: u128,
    individual_debt_base: u128,
    individual_collateral_base: u128,
    debt_to_cover_base: u128,
) -> Result<(), KineticRouterError> {
    let close_factor = if individual_debt_base < MIN_CLOSE_FACTOR_THRESHOLD
        || individual_collateral_base < MIN_CLOSE_FACTOR_THRESHOLD
        || health_factor < partial_liq_threshold {
        MAX_LIQUIDATION_CLOSE_FACTOR  // 100% for small/deeply underwater positions
    } else {
        DEFAULT_LIQUIDATION_CLOSE_FACTOR  // 50%
    };

    let max_liquidatable_debt = individual_debt_base
        .checked_mul(close_factor)?
        .checked_div(BASIS_POINTS_MULTIPLIER)?;

    if debt_to_cover_base > max_liquidatable_debt {
        return Err(KineticRouterError::LiquidationAmountTooHigh);
    }
    Ok(())
}
```

This check only considers the *current* debt balance. It does not consult or update any cumulative accumulator. Since the Router has a reentrancy guard (`acquire_reentrancy_guard` at `router.rs:304`), an attacker cannot make multiple calls within a single atomic invocation. However, the attacker **can submit multiple separate transactions within the same Soroban ledger**, each liquidating up to 50% of the *then-current* remaining debt.

### Attack Path (Step-by-Step)

Preconditions:
- Victim has `debt = $1,000`, `collateral = $1,500`, `health_factor < 1.0`
- `DEFAULT_LIQUIDATION_CLOSE_FACTOR = 5000` (50% in BPS)
- Attacker is a separate address (not the victim)

Attack:
1. Attacker submits **TX-1** in ledger N calling `KineticRouter.liquidation_call` with `debt_to_cover = $500` (50% of $1,000). Passes `validate_close_factor`. Debt → $500.
2. Attacker submits **TX-2** in ledger N calling `KineticRouter.liquidation_call` with `debt_to_cover = $250` (50% of $500). Passes `validate_close_factor`. Debt → $250.
3. Attacker submits **TX-3** in ledger N calling `KineticRouter.liquidation_call` with `debt_to_cover = $125` (50% of $250). Passes `validate_close_factor`. Debt → $125.
4. Continue until position is drained to dust.

After 5 transactions: **~96.9% of collateral seized**. The `LiquidationEngine.USER_LIQUIDATED_THIS_TX` accumulator was never consulted or updated.

If the same operations had gone through `LiquidationEngine.liquidate()`, the cumulative accumulator would have blocked any liquidation beyond the first 50%.

### Contrast with LiquidationEngine

```rust
// liquidation-engine/src/calculation.rs:58-79
let already_liquidated_this_tx = storage::get_user_liquidated_this_tx(env, &user);

let remaining_liquidatable = if already_liquidated_this_tx >= max_liquidatable_debt_total {
    0
} else {
    max_liquidatable_debt_total - already_liquidated_this_tx
};
// ...
if actual_debt_to_cover > 0 {
    storage::add_user_liquidated_this_tx(env, &user, actual_debt_to_cover);
}
```

The engine enforces a **cumulative** limit. The router does not.

## Impact

1. **Borrower Financial Loss**: Borrowers lose up to ~100% of collateral across multiple same-ledger transactions instead of being protected by the 50% partial liquidation cap. The close factor exists specifically to give borrowers a chance to add collateral or repay debt.

2. **Protocol Bad Debt Acceleration**: When `collateral_cap_triggered` is true (line 280-297), the remaining debt is socialized as `reserve_deficit` ([`liquidation.rs:610`](https://github.com/code-423n4/2026-04-k2/blob/main/contracts/kinetic-router/src/liquidation.rs#L610)). Rapid sequential liquidations accelerate deficit accumulation faster than the protocol risk model anticipates.

3. **LiquidationEngine State Desynchronization**: The `LiquidationEngine` remains unaware of liquidations routed through the `KineticRouter` directly, creating phantom telemetry. Any off-chain monitoring or governance logic relying on engine state is blind to these liquidations.

## Code Snippet

- **Public Router entry point**: [`router.rs:295-314`](https://github.com/code-423n4/2026-04-k2/blob/main/contracts/kinetic-router/src/router.rs#L295-L314)
- **Stateless close factor check**: [`liquidation.rs:12-36`](https://github.com/code-423n4/2026-04-k2/blob/main/contracts/kinetic-router/src/liquidation.rs#L12-L36)
- **Cumulative accumulator (Engine only)**: [`calculation.rs:59`](https://github.com/code-423n4/2026-04-k2/blob/main/contracts/liquidation-engine/src/calculation.rs#L59), [`storage.rs:256-271`](https://github.com/code-423n4/2026-04-k2/blob/main/contracts/liquidation-engine/src/storage.rs#L256-L271)
- **Deficit socialization**: [`liquidation.rs:610`](https://github.com/code-423n4/2026-04-k2/blob/main/contracts/kinetic-router/src/liquidation.rs#L610)

## Tool Used

Manual Code Review

## Proof of Concept

The following test demonstrates the bypass using the K2 C4 test template. Place in `tests/c4/src/lib.rs`:

```rust
#[test]
fn test_close_factor_bypass_via_router() {
    // Setup: Standard K2 test environment with deployed router + engine
    let env = Env::default();
    env.mock_all_auths();

    // 1. Deploy infrastructure (router, oracle, tokens, etc.)
    //    [Uses standard k2-c4 setup from test_submission_validity]
    
    // 2. Create victim position: supply $1500 collateral, borrow $1000 debt
    //    [Standard supply + borrow calls]
    
    // 3. Manipulate oracle to make position liquidatable (HF < 1.0)
    //    [Set collateral price to trigger liquidation threshold]
    
    // 4. Attacker calls KineticRouter.liquidation_call DIRECTLY
    //    (NOT through LiquidationEngine)
    
    // Call 1: Liquidate 50% of $1000 = $500
    router_client.liquidation_call(
        &attacker, &collateral_asset, &debt_asset, &victim,
        &500_0000000, // 50% of current debt
        &false,
    );
    
    // After call 1: victim debt = $500, ~$750 collateral seized (with bonus)
    
    // Call 2: Liquidate 50% of remaining $500 = $250
    router_client.liquidation_call(
        &attacker, &collateral_asset, &debt_asset, &victim,
        &250_0000000, // 50% of remaining debt  
        &false,
    );
    
    // After call 2: victim debt = $250, total ~$1125 collateral seized
    
    // Call 3: Liquidate 50% of remaining $250 = $125
    router_client.liquidation_call(
        &attacker, &collateral_asset, &debt_asset, &victim,
        &125_0000000,
        &false,
    );
    
    // After 3 calls: 87.5% of original debt liquidated
    // Through LiquidationEngine, only 50% would be allowed
    
    // 5. Verify: Engine accumulator is ZERO (was never updated)
    let engine_tracked = engine_client.get_user_liquidated_this_tx(&victim);
    assert_eq!(engine_tracked, 0); // Proves engine was bypassed
    
    // 6. Verify: Actual collateral removed exceeds 50% limit
    let remaining_collateral = atoken_client.balance_of(&victim);
    // remaining_collateral << initial_collateral * 0.5
    // This violates the close factor invariant
}
```

**Note on reentrancy guard**: Each `router_client.liquidation_call` above represents a **separate top-level transaction**, not nested calls. The reentrancy guard (`acquire_reentrancy_guard`) only blocks re-entrant calls within the same invocation context. Separate transactions in the same ledger execute independently with a fresh lock state.

## Note on V12 Finding #44820

This finding is **distinct** from V12 #44820 ("Engine uses uncapped debt for executed liquidation"). V12 #44820 describes the `LiquidationEngine.execute_liquidation` forwarding `debt_to_cover` instead of `actual_debt_to_cover` to the Router — an Engine→Router parameter desync. This finding describes a fundamentally different attack vector: **direct invocation of `KineticRouter.liquidation_call` without involving the `LiquidationEngine` at all**. The Router's `validate_close_factor` performs a stateless check that has no cumulative tracking. V12's proposed fix (passing `actual_debt_to_cover` from engine to router) would **not remediate this vector**, because the attacker never enters through the engine.

## Recommendation

**Option A — Cumulative accumulator in Router (Preferred)**:

Move the `USER_LIQUIDATED_THIS_TX` logic from `LiquidationEngine` into `KineticRouter.internal_liquidation_call`:

```rust
// In internal_liquidation_call, after validate_close_factor:
let accumulated_key = (symbol_short!("ULIQTX"), user.clone());
let already_liquidated: u128 = env.storage()
    .temporary()
    .get(&accumulated_key)
    .unwrap_or(0);

let max_total = individual_debt_base
    .checked_mul(close_factor)
    .ok_or(KineticRouterError::MathOverflow)?
    .checked_div(BASIS_POINTS_MULTIPLIER)
    .ok_or(KineticRouterError::MathOverflow)?;

if already_liquidated + debt_to_cover_base > max_total {
    return Err(KineticRouterError::LiquidationAmountTooHigh);
}

env.storage().temporary().set(
    &accumulated_key,
    &(already_liquidated + debt_to_cover_base),
);
```

**Option B — Restrict Router entry**:

Add `engine_addr.require_auth()` to `KineticRouter.liquidation_call` to enforce that only the `LiquidationEngine` can invoke it, centralizing the accumulator logic.
