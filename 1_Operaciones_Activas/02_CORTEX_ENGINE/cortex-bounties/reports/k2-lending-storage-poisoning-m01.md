# [M-01] Storage Poisoning in Liquidation Engine allows DoS

## Severity
Medium

## Description
The K2 Lending protocol's `LiquidationEngine` contract exposes a `calculate_liquidation` function intended for quoting or calculating liquidation parameters before execution. However, this function incorrectly mutates state related to the `close_factor` limits.

In `contracts/liquidation-engine/src/calculation.rs`:
```rust
pub fn calculate_liquidation(
    env: &Env,
    collateral_asset: Address,
    debt_asset: Address,
    user: Address,
    debt_to_cover: u128,
) -> Result<LiquidationCalculation, KineticRouterError> {
    // ...
    // Calculate remaining liquidatable amount based on already_liquidated_this_tx
    
    let actual_debt_to_cover = if debt_to_cover_base > remaining_liquidatable {
        remaining_liquidatable
    } else {
        debt_to_cover_base
    };

    // Track cumulative liquidation for this transaction
    if actual_debt_to_cover > 0 {
        storage::add_user_liquidated_this_tx(env, &user, actual_debt_to_cover); // <-- STATE MUTATION
    }
    // ...
}
```

The `storage::add_user_liquidated_this_tx` function uses Soroban's `temporary()` storage, which persists across the entirety of a transaction. Because `calculate_liquidation` increments this counter without actually executing any liquidation or debt repayment, an attacker can artificially "fill up" the close factor tracking for a user.

## Impact
A borrower (or an attacker) can front-run a legitimate liquidation transaction by invoking `calculate_liquidation` on themselves multiple times within the same transaction. This poisons the `temporary()` storage counter `USER_LIQUIDATED_THIS_TX`. When the legitimate liquidator's transaction (or a subsequent call in the same bundle) attempts to execute the real liquidation, the `close_factor` limit will appear to be exhausted, causing the liquidation to fail or be capped at 0. This results in a targeted Denial of Service (DoS) against liquidators, preventing the protocol from clearing bad debt.

## Proof of Concept
1. **Setup**: Borrower A is underwater. Liquidator B submits a transaction to liquidate Borrower A.
2. **Attack**: Borrower A monitors the mempool (or submits a bundle/atomic transaction) that calls `calculate_liquidation(Borrower A)` first.
3. **Execution**: The `calculate_liquidation` call succeeds and increments `USER_LIQUIDATED_THIS_TX` up to the max `close_factor` limit.
4. **Failure**: Liquidator B's call to `execute_liquidation` runs in the same transaction block/sequence. It checks `USER_LIQUIDATED_THIS_TX`, sees the limit is reached, and fails the liquidation.
5. **Result**: Borrower A successfully avoids liquidation at no cost.

## Recommended Mitigation
Remove the state mutation from `calculate_liquidation`. The `USER_LIQUIDATED_THIS_TX` accumulator should *only* be updated inside the actual `execute_liquidation` flow after debt has successfully been repaid and collateral seized.

```rust
// In calculation.rs
// REMOVE:
// if actual_debt_to_cover > 0 {
//     storage::add_user_liquidated_this_tx(env, &user, actual_debt_to_cover);
// }
```

Move the update logic to the point of execution where the state change is final.

---
**Crystallized by:** Antigravity (CORTEX Swarm)
**Protocol:** K2 Lending (Soroban)
**Validation:** C5-REAL
