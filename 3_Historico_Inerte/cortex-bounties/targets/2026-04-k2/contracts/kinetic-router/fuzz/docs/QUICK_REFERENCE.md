# K2 Fuzz Testing Quick Reference

## Running Fuzzers

```bash
cd contracts/kinetic-router/fuzz
cargo +nightly fuzz run <fuzzer_name> --sanitizer=none
```

## Fuzz Targets Summary

| Fuzzer | Phase | Focus | Key Invariants |
|--------|-------|-------|----------------|
| `fuzz_auth_boundaries` | 1 | Authorization | Access control, dual auth, admin transfer |
| `fuzz_lending_operations` | 2 | Core lending | Token conservation, index monotonicity |
| `fuzz_flash_loan` | 2 | Flash loans | Premium distribution, atomic rollback |
| `fuzz_liquidation` | 2 | Liquidations | Close factor, HF improvement, debt reduction |
| `fuzz_multi_asset` | 3 | Cross-asset | Reserve isolation, cross-collateral HF |
| `fuzz_price_scenarios` | 4 | Price attacks | Sandwich attacks, manipulation resistance |
| `fuzz_economic_invariants` | 5 | Economics | Rate model, utilization, treasury accrual |
| `fuzz_admin_ops` | - | Admin ops | Parameter bounds, configuration |
| `fuzz_admin_transfer` | - | Admin transfer | Two-step process |
| `fuzz_reserve_config` | - | Reserve config | LTV, thresholds, caps |

## Key Constants

```
RAY = 1e9           # Rate/index precision
WAD = 1e18          # Health factor precision
CLOSE_FACTOR = 50%  # Max liquidation per tx
```

## Universal Invariants

1. **Index Monotonicity**: `index[t+1] ≥ index[t]`
2. **Index Lower Bound**: `index ≥ RAY`
3. **Rate Relationship**: `supply_rate ≤ borrow_rate`
4. **Supply Consistency**: `supply ≥ 0`

## Common Commands

```bash
# List all fuzzers
cargo +nightly fuzz list

# Run for 5 minutes
cargo +nightly fuzz run fuzz_lending_operations --sanitizer=none -- -max_total_time=300

# Run with 4 parallel jobs
cargo +nightly fuzz run fuzz_lending_operations --sanitizer=none -j4

# Minimize corpus
cargo +nightly fuzz cmin fuzz_lending_operations --sanitizer=none
```

## Audit Coverage

| Finding | Fuzzer |
|---------|--------|
| HAL-01 to HAL-05 | `fuzz_auth_boundaries` |
| HAL-40 (Admin Transfer) | `fuzz_auth_boundaries`, `fuzz_admin_transfer` |
