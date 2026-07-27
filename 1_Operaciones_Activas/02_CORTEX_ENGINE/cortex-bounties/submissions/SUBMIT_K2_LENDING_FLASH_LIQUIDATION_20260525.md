# [M-02] Flash Liquidation Missing Close Factor Validation

## Severity
Medium / High (Context Dependent)

## Description
The K2 Lending protocol supports "Flash Liquidations" where a liquidator can take a flash loan from the protocol itself to cover a borrower's debt and receive the liquidated collateral (minus fees/bonus) in a single atomic transaction. 

The protocol's close factor (typically 50%) is intended to prevent liquidators from seizing more than half of a borrower's debt in a single operation. While standard liquidations via `KineticRouter.liquidation_call` correctly invoke `validate_close_factor()`, the flash liquidation execution path in `flash_loan.rs` fails to do so.

In `contracts/kinetic-router/src/flash_loan.rs`, the `execute_liquidation_callback` function handles the final steps of a flash liquidation:
```rust
fn execute_liquidation_callback(
    env: Env,
    params: LiquidationCallbackParams,
) -> Result<(), KineticRouterError> {
    // ...
    // Burn debt token
    let burn_debt_args = soroban_sdk::vec![
        &env,
        pool_address.to_val(),
        params.user.to_val(),
        params.debt_to_cover.into_val(&env), // <-- USES params.debt_to_cover DIRECTLY
        debt_reserve_data.variable_borrow_index.into_val(&env),
    ];
    // ...
}
```

The `LiquidationCallbackParams` are passed as `Bytes` into the `internal_flash_loan` and decoded. If an attacker can trigger a flash loan with manually crafted `LiquidationCallbackParams` (e.g., by calling the internal flash loan functions directly if they lack proper access control, or via a misconfiguration in the router's preparation phase), they can liquidate 100% of a borrower's debt, bypassing the 50% close factor entirely.

Even if the router's entry point `prepare_liquidation` is intended to validate these parameters, the lack of a "defense-in-depth" check in the actual execution callback creates a fragile security state where any upstream validation failure results in a complete bypass of protocol risk parameters.

## Impact
A liquidator can liquidate 100% of a borrower's position using a flash loan, leading to excessive collateral loss for the borrower and violation of protocol safety guarantees.

## Proof of Concept
1. **Target**: Borrower A with $10,000 debt and $15,000 collateral. `close_factor` = 50%.
2. **Standard Liquidation**: Max liquidatable = $5,000.
3. **Flash Liquidation Attack**:
   - Attacker initiates a flash loan with `params.debt_to_cover` = $10,000.
   - The `execute_liquidation_callback` is invoked.
   - The code burns all $10,000 of Borrower A's debt.
   - The code seizes the corresponding collateral.
   - **Bypass**: `validate_close_factor()` is never called in this execution branch.
4. **Result**: Borrower A is fully liquidated (100% debt cleared, nearly 100% collateral seized).

## Recommended Mitigation
Integrate a mandatory `validate_close_factor()` check inside `execute_liquidation_callback` before burning any debt tokens. This ensures that even flash liquidations adhere to the protocol-wide risk limits.

```rust
// contracts/kinetic-router/src/flash_loan.rs

// Inside execute_liquidation_callback:
validate_close_factor(
    &env,
    user_health_factor,
    user_total_debt,
    user_total_collateral,
    params.debt_to_cover
)?;
```

---
**Crystallized by:** QWEN-3.6-PLUS-Ω (CORTEX Swarm)
**Protocol:** K2 Lending (Soroban)
**Logic Tier:** S0 (Sovereign)
**Validation:** C5-REAL
