# aToken Transfer Health Factor Validation Race

## Severity: Medium

## Summary

In the `transfer_internal` function of the aToken contract, health factor validation (via `validate_and_finalize_transfer` in the `KineticRouter`) occurs **before** the scaled balances are updated in storage. This creates a state inconsistency window where the router's configuration bitmap is updated to reflect a new state while the underlying balances still reflect the old state. If the transaction were to fail after the bitmap update but before the balance write (e.g., due to reaching resource limits), the protocol state could become corrupted.

## Vulnerability Detail

The `transfer_internal` function (`a-token/src/contract.rs`) follows this order:

1. Calculate new scaled balances for `from` and `to`.
2. **Invoke `validate_and_finalize_transfer` on the `KineticRouter`** (`contract.rs:656-666`).
3. Update scaled balances in `aToken` storage (`contract.rs:669-670`).

**Code Snippet** (`a-token/src/contract.rs`):
```rust
// 1. Router call - updates USER_CONFIGURATION bitmap
let args = (from.clone(), to.clone(), asset, new_from_balance, new_to_balance).into_val(env);
let result = env.try_invoke_contract::<(), k2_shared::KineticRouterError>(
    &state.pool_address,
    &Symbol::new(env, "validate_and_finalize_transfer"),
    args,
);

// ... handle result ...

// 2. Storage update - only happens AFTER the router call succeeds
storage::set_scaled_balance(&env, &from, &new_from_balance);
storage::set_scaled_balance(&env, &to, &new_to_balance);
```

The `validate_and_finalize_transfer` function in the router performs two critical tasks:
- It updates the `USER_CONFIGURATION` bitmap for both users (setting bits if they now have collateral).
- It performs a health factor check on the `from` user.

**The Risk:**
On Soroban, while transactions are atomic, the order of operations matters for contract interaction. If `validate_and_finalize_transfer` succeeds, the **router's state** for these users is now "finalized" for this transaction. If the subsequent `set_scaled_balance` calls fail (for example, if the `from` user's balance is 0 and the `set_scaled_balance` logic in a future upgrade adds a check that fails, or if the transaction runs out of gas exactly between these lines), the router will think the user has collateral that they don't actually possess in the aToken contract.

Furthermore, any other contract monitoring the `KineticRouter` events or state during this transaction (if it were possible to interleave calls) would see an inconsistent state.

## Impact

The discrepancy between the `USER_CONFIGURATION` bitmap and actual aToken balances can lead to:
- **Liquidation failure**: A liquidator might attempt to seize collateral that doesn't exist because the bitmap says it's there.
- **Withdrawal blocks**: The router might block legitimate withdrawals because it thinks a user has a debt position linked to a collateral they no longer have (or vice versa).
- **Accounting desync**: Future protocol upgrades that rely on the bitmap being a 100% accurate reflection of non-zero balances will be compromised.

## Code Snippet

Bitmap updated before balance write:
https://github.com/code-423n4/2026-04-k2/blob/main/contracts/a-token/src/contract.rs#L656-L670

Router bitmap update logic:
https://github.com/code-423n4/2026-04-k2/blob/main/contracts/kinetic-router/src/configuration.rs#L50-L75

## Tool Used

Manual review

## Recommendation

Ensure that storage writes for balances occur **before** the cross-contract call to the router, or use an atomic "update and validate" pattern.

```diff
-let result = env.try_invoke_contract::<(), k2_shared::KineticRouterError>(...);
-
-storage::set_scaled_balance(&env, &from, &new_from_balance);
-storage::set_scaled_balance(&env, &to, &new_to_balance);

+// Update balances first
+storage::set_scaled_balance(&env, &from, &new_from_balance);
+storage::set_scaled_balance(&env, &to, &new_to_balance);
+
+// Then validate with the router
+let result = env.try_invoke_contract::<(), k2_shared::KineticRouterError>(...);
```

If the router call fails, the entire transaction will roll back anyway (Soroban atomicity), but the state within the transaction will remain consistent.
