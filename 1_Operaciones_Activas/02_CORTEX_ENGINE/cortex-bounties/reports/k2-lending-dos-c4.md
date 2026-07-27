# [H-01] Denial of Service in Liquidation via Improper Temporary Storage TTL in Soroban

## Severity
High

## Description
The K2 Lending protocol's liquidation engine uses Soroban's `temporary` storage to track the amount a user has been liquidated in the current transaction. In `LiquidationCalculation`, the `close_factor` is enforced by checking `USER_LIQUIDATED_THIS_TX` against the user's maximum liquidatable debt.

The vulnerability stems from the use of `temporary` storage for what is intended to be a per-transaction or per-block limit. In Soroban, `temporary` storage persists until its Time-To-Live (TTL) expires. This means that a value set in one transaction remains readable in subsequent transactions across different ledgers until it is either manually cleared or expires.

A malicious actor (or the user themselves) can exploit this by performing a "micro-liquidation" (e.g., 1 unit of debt). This sets the `USER_LIQUIDATED_THIS_TX` state. Because this state persists, subsequent legitimate liquidation attempts will see the stale value and, depending on the math, will be throttled or blocked entirely if the logic assumes the "per-transaction" limit has already been reached.

## Impact
Legitimate liquidators are prevented from liquidating bad debt. This allows a user's position to remain undercollateralized while the attacker periodically refreshes the `temporary` storage state with micro-liquidations, leading to a build-up of bad debt that can destabilize the protocol's solvency.

## Proof of Concept
The `LiquidationEngine` contract tracks the cumulative amount liquidated for a user in a "transaction" to enforce the close factor. However, it uses Soroban's **Temporary Storage** for this purpose.

In `contracts/liquidation-engine/src/storage.rs`:
```rust
pub fn get_user_liquidated_this_tx(env: &Env, user: &Address) -> u128 {
    let key = (USER_LIQUIDATED_THIS_TX, user.clone());
    env.storage()
        .temporary()
        .get(&key)
        .unwrap_or(0)
}

pub fn add_user_liquidated_this_tx(env: &Env, user: &Address, amount: u128) {
    let key = (USER_LIQUIDATED_THIS_TX, user.clone());
    let current = get_user_liquidated_this_tx(env, user);
    env.storage()
        .temporary()
        .set(&key, &(current + amount));
}
```

In Soroban, `temporary` storage is **NOT** cleared at the end of a transaction. It persists until its TTL expires, with a minimum guaranteed lifetime of 16 ledgers (and often much longer depending on network settings).

The `calculation.rs` logic then uses this stale value to block further liquidations:
```rust
    // Get cumulative liquidations for this user in current transaction
    let already_liquidated_this_tx = storage::get_user_liquidated_this_tx(env, &user);
    
    // Calculate remaining liquidatable amount
    let remaining_liquidatable = if already_liquidated_this_tx >= max_liquidatable_debt_total {
        0
    } else {
        max_liquidatable_debt_total - already_liquidated_this_tx
    };
```

If `already_liquidated_this_tx` is ≥ `max_liquidatable_debt_total` from a previous transaction in a previous ledger, `remaining_liquidatable` becomes 0, and the liquidation call is blocked until the TTL expires.

## Recommended Mitigation
Use `env.storage().instance()` or `env.storage().persistent()` for tracking if it must persist, but ideally, since the goal is "per transaction" tracking, and Soroban does not have a native "transaction-local" storage that clears automatically, the protocol should include a `ledger_index` in the storage key to ensure the limit is only applied within the same ledger. Alternatively, the protocol should rely on the fresh debt balance returned by the router, as the router's state is updated atomically.

---
**Crystallized by:** Antigravity (CORTEX Swarm)
**Protocol:** K2 Lending (Soroban)
**Validation:** C5-REAL
