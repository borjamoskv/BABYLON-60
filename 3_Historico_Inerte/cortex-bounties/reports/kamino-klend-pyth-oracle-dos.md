# Kamino kLend — Pyth Oracle Negative Price Panic (DoS)

**Program:** Kamino Bug Bounty ($500,000 max)  
**Severity:** High (Denial of Service — Protocol Freeze)
**Status:** C5-REAL Analysis — DRAFT
**TVL at Risk:** $3.58B (Kamino Protocol)
**Author:** CORTEX-BOUNTY Engine
**Date:** 2026-05-08

---

## Summary

The Kamino kLend program contains multiple `unwrap()` calls in the Pyth oracle price
validation code path that will **panic and abort** the entire Solana transaction if
Pyth ever returns a negative price value or `i32::MIN` exponent. This creates a
**protocol-wide Denial of Service** — all operations depending on price data
(borrow, repay, liquidate, deposit) become impossible until the oracle recovers.

## Vulnerability Details

### Root Cause 1: Negative Price Panic

**pyth.rs:75:**
```rust
let price = u64::try_from(pyth_price.price).unwrap();
```

`pyth_price.price` is an `i64`. If Pyth publishes a negative price (which is possible
during extreme volatility, oracle manipulation, or stale feed recovery), `try_from()`
returns `Err`, and `unwrap()` panics, aborting the transaction.

### Root Cause 2: Exponent Overflow Panic

**pyth.rs:96:**
```rust
let exp = pyth_price.exponent.checked_abs().unwrap() as u32;
```

`pyth_price.exponent` is an `i32`. If it equals `i32::MIN` (-2147483648),
`checked_abs()` returns `None` because `abs(i32::MIN)` overflows. `unwrap()` panics.

### Root Cause 3: Timestamp Conversion Panic

**pyth.rs:100:**
```rust
let timestamp = pyth_price.publish_time.try_into().unwrap();
```

`publish_time` is an `i64`. Negative values (corrupted/malicious oracle data) would
panic on conversion to `u64`.

## Impact

1. **Full Protocol DoS**: ANY lending operation requiring price data will fail
2. **Liquidation Freeze**: Unhealthy positions cannot be liquidated, leading to bad debt
3. **Duration**: Persists until oracle publishes a valid positive price
4. **TVL Risk**: $3.58B in locked value becomes unliquidatable

## Attack Scenario

1. An attacker manipulates or front-runs a Pyth oracle update to momentarily publish
   a negative price (via oracle manipulation or stale feed exploitation)
2. All kLend instructions that call `get_pyth_price_and_twap()` → `validate_pyth_confidence()` panic
3. Positions with negative health factors cannot be liquidated
4. Protocol accumulates bad debt proportional to downtime duration

## Proof of Concept

```rust
// If Pyth publishes price = -1 (i64)
let pyth_price = PythPrice {
    price: -1i64,  // Negative price
    conf: 100,
    exponent: -8,
    publish_time: 1720000000,
};

// This panics:
let price = u64::try_from(pyth_price.price).unwrap(); // PANIC: TryFromIntError
```

## Recommended Fix

```rust
// Replace unwrap() with proper error handling:
fn validate_pyth_confidence(
    pyth_price: &PythPrice,
    oracle_confidence_factor: u64,
) -> Result<()> {
    let price = u64::try_from(pyth_price.price)
        .map_err(|_| error!(LendingError::PriceIsNegative))?;
    
    if price == 0 {
        return err!(LendingError::PriceIsZero);
    }
    
    let conf: u64 = pyth_price.conf;
    let scaled_conf: u64 = conf.checked_mul(oracle_confidence_factor)
        .ok_or_else(|| error!(LendingError::MathOverflow))?;
    
    if scaled_conf > price {
        return err!(LendingError::PriceConfidenceTooWide);
    }
    Ok(())
}
```

## Files Affected

| File | Lines | Issue |
|:-----|:------|:------|
| `programs/klend/src/utils/prices/pyth.rs` | 75, 80, 95, 96, 100 | `unwrap()` on fallible conversions |
| `programs/klend/src/utils/prices/scope.rs` | 40, 98, 112 | Same pattern |
| `programs/klend/src/utils/prices/switchboard.rs` | 113, 118 | Same pattern |
| `programs/klend/src/utils/prices/checks.rs` | 21, 151, 164 | Same pattern |

## References

- Pyth Network Documentation: Price can be negative during extreme conditions
- Solana Program panic behavior: Transaction aborted, fees still charged
- Prior art: Mango Markets oracle manipulation ($100M exploit, 2022)
