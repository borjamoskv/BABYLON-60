# How to Run Fuzz Tests

This guide explains how to run fuzz tests for the K2 contracts.

## Executive Summary

The K2 protocol uses **property-based fuzz testing** to verify the correctness and security of the kinetic-router contract. The test suite includes **11 fuzz targets** combining two complementary approaches:

| Approach | Fuzzers | Strategy |
|----------|---------|----------|
| **Monolithic** (Tena) | 1 | Broad coverage with 85+ ops, 8 users, 4 assets |
| **Specialized** (Ijonas) | 10 | Deep coverage with targeted invariants per domain |

### Key Protocol Properties Tested

- **Atomicity**: Failed operations leave no state changes
- **Solvency**: Pool cannot be drained through any operation sequence
- **Interest Accrual**: Indices only increase over time
- **Liquidation Safety**: Only unhealthy positions (HF < 1.0) can be liquidated
- **Flash Loan Security**: Loans must be fully repaid within the same transaction
- **Admin Safety**: Admin operations cannot extract user funds
- **Rounding Bounds**: Cumulative rounding errors stay within tolerance

## Prerequisites

### 1. Install Nightly Rust

```bash
rustup install nightly
```

### 2. Install cargo-fuzz

```bash
cargo install --locked cargo-fuzz
```

### 3. Build Contracts

Fuzz tests require the optimized WASM files:

```bash
./deployment/build.sh
```

## Running Fuzz Tests

Navigate to the fuzz directory:

```bash
cd contracts/kinetic-router/fuzz
```

### List Available Fuzzers

```bash
cargo +nightly fuzz list
```

This should show all 11 targets:
- `fuzz_target_1` (Tena's monolithic)
- `fuzz_lending_operations`, `fuzz_liquidation`, `fuzz_flash_loan`
- `fuzz_auth_boundaries`, `fuzz_multi_asset`, `fuzz_price_scenarios`
- `fuzz_economic_invariants`, `fuzz_admin_ops`, `fuzz_admin_transfer`
- `fuzz_reserve_config`

---

## Tena's Monolithic Fuzzer

### Basic Usage (macOS)

```bash
cd contracts/kinetic-router
RUSTFLAGS="-Cunsafe-allow-abi-mismatch=sanitizer" \
  cargo +nightly fuzz run --sanitizer=thread fuzz_target_1
```

### Time-Limited Runs

```bash
# Run for 15 minutes
RUSTFLAGS="-Cunsafe-allow-abi-mismatch=sanitizer" \
  cargo +nightly fuzz run --sanitizer=thread fuzz_target_1 -- -max_total_time=900

# Run for 1 hour
RUSTFLAGS="-Cunsafe-allow-abi-mismatch=sanitizer" \
  cargo +nightly fuzz run --sanitizer=thread fuzz_target_1 -- -max_total_time=3600
```

### Using the Dictionary

```bash
RUSTFLAGS="-Cunsafe-allow-abi-mismatch=sanitizer" \
  cargo +nightly fuzz run --sanitizer=thread fuzz_target_1 \
  -- -max_total_time=3600 -dict=fuzz/router.dict
```

### Operations Tested

**Core Operations**: Supply, SupplyOnBehalf, Withdraw, WithdrawAll, WithdrawToRecipient, Borrow, BorrowToRecipient, Repay, RepayAll, RepayOnBehalf, SetCollateral, SwapCollateral, TransferAToken

**Liquidation Operations**: Liquidate, LiquidateReceiveAToken, PrepareLiquidation, ExecuteLiquidation, CreateAndLiquidate, MultiAssetLiquidation, FullMultiAssetLiquidation, SelfLiquidationAttempt, PriceCrashLiquidation

**Flash Loan Operations**: FlashLoan, MultiAssetFlashLoan, FlashLoanWhilePaused with 6 receiver behaviors (Standard, Reentrant, ReentrantRepayLiquidation, NonRepaying, StateManipulating, OracleManipulating)

**Edge Cases**: ZeroAmount, DustAmount, MaxAmount variants for all core operations, DrainLiquidity, MaxUtilization

**Oracle Scenarios**: PriceChange, PriceToZero, PriceToMax, OracleStale, PriceVolatility

**Adversarial Patterns**: FirstDepositorAttack, DonationAttack, SandwichPriceChange, InterestAccrualExploit, RapidSupplyWithdraw, RapidBorrowRepay, BorrowMaxWithdrawAttempt, BadDebtScenario

**Admin Operations**: UpdateReserveConfiguration, UpdateReserveRateStrategy, SetReserveSupplyCap, SetReserveBorrowCap, SetReserveDebtCeiling, SetReserveWhitelist, SetReserveBlacklist, SetLiquidationWhitelist, SetLiquidationBlacklist, SetReserveActive, SetReserveFrozen, DropReserve, CollectProtocolReserves, ProposePoolAdmin, AcceptPoolAdmin, PauseProtocol, UnpauseProtocol

**Environmental**: TimeWarp, ExtremeTimeWarp (up to 10 years)

### Invariants Verified (25+)

- **No Negative Balances**: All supply/debt values >= 0
- **Token Conservation**: Sum of all balances equals initial total
- **Balance Consistency**: User balances sum to protocol totals
- **Health Factor Validity**: Users with debt have valid health factors
- **Supply/Borrow Caps**: Enforced per reserve
- **Protocol Solvency**: Total collateral value >= total debt value
- **Index Monotonicity**: Liquidity and borrow indices never decrease
- **Accrued Treasury Monotonicity**: Treasury only increases (except on collection)
- **Liquidation Fairness**: Bonus within configured bounds
- **Liquidation Safety**: Only HF < 1.0 positions liquidatable
- **Premium Verification**: Correct premium charged on success
- **Repayment Verification**: Full repayment required
- **No Rate Manipulation**: Detect interest rate gaming
- **Oracle Sanity**: Price bounds checking
- **No Value Extraction**: Users cannot profit beyond legitimate yield
- **Admin Cannot Steal**: Admin operations don't drain user funds
- **Parameter Bounds**: LTV < liquidation threshold < 100%
- **Pause State**: Protocol pause behavior correct
- **Access Control**: Authorization checks enforced
- **Failed Operations Unchanged**: Failed ops don't modify state
- **Cumulative Rounding**: Rounding errors bounded over time

---

## Ijonas's Specialized Fuzzers

### Basic Usage (macOS)

On macOS, use `--sanitizer=none` for specialized fuzzers:

```bash
cd contracts/kinetic-router/fuzz
cargo +nightly fuzz run fuzz_lending_operations --sanitizer=none
```

### Time-Limited Runs

```bash
# Run for 10 minutes
cargo +nightly fuzz run fuzz_lending_operations --sanitizer=none -- -max_total_time=600

# Run for 1 hour
cargo +nightly fuzz run fuzz_lending_operations --sanitizer=none -- -max_total_time=3600
```

### Parallel Execution

```bash
cargo +nightly fuzz run fuzz_lending_operations --sanitizer=none -- -jobs=4 -workers=4
```

### Using the Dictionary

```bash
cargo +nightly fuzz run fuzz_lending_operations --sanitizer=none -- -dict=dict.txt
```

Combined with parallel execution:

```bash
cargo +nightly fuzz run fuzz_lending_operations --sanitizer=none -- -jobs=4 -workers=4 -dict=dict.txt
```

### Fuzzer Details

#### fuzz_lending_operations

Tests supply, borrow, repay, withdraw with multi-user operation sequencing.

**Operations**: Supply, Borrow, Repay, Withdraw, AdvanceTime, SupplyMore, PartialWithdraw, RepayAll, WithdrawAll, SetPrice, Liquidate, SetCollateralEnabled

**Features**: Multi-user scenarios, 16 operations per sequence, price manipulation, comprehensive invariant checking

#### fuzz_liquidation

Dedicated liquidation testing.

**Focus**: Price drop scenarios, liquidation thresholds, close factor limits (50%), bonus calculations, cross-user liquidations

#### fuzz_flash_loan

Comprehensive flash loan testing with configurable receiver.

**Receiver Behaviors**:
| Behavior | Action | Expected Result |
|----------|--------|-----------------|
| `ExactRepay` | Repays principal + premium exactly | Success |
| `Overpay` | Repays more than required | Success (excess to pool) |
| `Underpay` | Repays less than required | Fails: `FlashLoanNotRepaid` |
| `NoRepay` | Keeps borrowed tokens | Fails: `FlashLoanNotRepaid` |
| `Panic` | Panics during callback | Fails: state unchanged |
| `ReturnFalse` | Returns false from callback | Fails: `FlashLoanExecutionFailed` |

**Invariants**: Pool balance unchanged after failed flash loans (atomicity), treasury receives premium on success, reserve indices remain >= RAY and monotonically increasing

#### fuzz_auth_boundaries

Authorization boundary testing without mock bypass.

#### fuzz_multi_asset

Cross-asset isolation verification.

#### fuzz_price_scenarios

Oracle manipulation resistance testing.

#### fuzz_economic_invariants

Interest rate model and index calculation validation.

#### fuzz_admin_ops

Admin operation safety testing.

#### fuzz_admin_transfer

Two-step admin transfer flow testing.

#### fuzz_reserve_config

Reserve configuration parameter bounds testing.

---

## Understanding Output

```
#6773  NEW    cov: 7446 ft: 7447 corp: 3/75b lim: 68 exec/s: 218 rss: 40Mb
```

- `#6773` - Number of test cases executed
- `cov: 7446` - Code coverage (unique code paths discovered)
- `exec/s: 218` - Executions per second
- `rss: 40Mb` - Memory usage
- `NEW` - A new interesting input was found

When coverage (`cov`) stops increasing, the fuzzer has explored most reachable paths.

### Statistics Output (Tena's fuzzer)

Every 100 successful runs, the fuzzer prints detailed statistics:

```
========== FUZZER OPERATION STATISTICS ==========
Total operations: 28168 (18% success rate)

--- Core Operations ---
  Supply                             7861 (27%)
  Borrow                             1815 ( 6%)
  ...

--- Invariant Execution Statistics ---
  ProtocolSolvency                   28168
  IndexMonotonicity                  28168
  ...
```

## Crash Reproduction

If a crash is found, it will be saved to:

```
fuzz/artifacts/<fuzzer_name>/crash-<hash>
```

Reproduce a crash:

```bash
# For Tena's fuzzer
cd contracts/kinetic-router
RUSTFLAGS="-Cunsafe-allow-abi-mismatch=sanitizer" \
  cargo +nightly fuzz run --sanitizer=thread fuzz_target_1 \
  fuzz/artifacts/fuzz_target_1/crash-<hash>

# For Ijonas's fuzzers
cd contracts/kinetic-router/fuzz
cargo +nightly fuzz run fuzz_lending_operations --sanitizer=none \
  fuzz/artifacts/fuzz_lending_operations/crash-<hash>
```

## Seed Corpus Generation

Generate seed corpus for specialized fuzzers:

```bash
cd contracts/kinetic-router/fuzz
cargo run --bin generate_seeds
```

Creates ~30 seed files covering:
- Edge cases: max/min/zero amounts, u64::MAX values
- LTV boundary testing: 80% borrow limits
- Interest accrual: time advancement scenarios (1 hour to 1 year)
- Multi-user scenarios: two users with different supply/borrow patterns
- Price manipulation: price crashes, pumps, and volatility
- Liquidation scenarios: cross-user liquidations
- Complex sequences: multiple supplies, supply-borrow cycles
- Power of 2 testing for bit manipulation edge cases
- Collateral toggling scenarios

## Corpus Management

Corpus is maintained in:

```
fuzz/corpus/<fuzzer_name>/
```

To minimize the corpus (remove redundant inputs):

```bash
cargo +nightly fuzz cmin fuzz_lending_operations --sanitizer=none
```

## CI Integration

```bash
cd contracts/kinetic-router/fuzz

# Run all fuzzers for 5 minutes each
for target in $(cargo +nightly fuzz list 2>/dev/null); do
  if [ "$target" = "fuzz_target_1" ]; then
    cd ..
    RUSTFLAGS="-Cunsafe-allow-abi-mismatch=sanitizer" \
      cargo +nightly fuzz run --sanitizer=thread fuzz_target_1 -- -max_total_time=300
    cd fuzz
  else
    cargo +nightly fuzz run "$target" --sanitizer=none -- -max_total_time=300
  fi
done
```

Exit code 0 means no crashes were found within the time limit.

## Troubleshooting

### Linker error: "initializer pointer has no target"

This error occurs on macOS due to incompatibility between ASAN and the ctor/dtor crates.

**For Tena's fuzzer**: Use thread sanitizer with ABI mismatch flag:
```bash
RUSTFLAGS="-Cunsafe-allow-abi-mismatch=sanitizer" cargo +nightly fuzz run --sanitizer=thread fuzz_target_1
```

**For Ijonas's fuzzers**: Use no sanitizer:
```bash
cargo +nightly fuzz run fuzz_lending_operations --sanitizer=none
```

### "No such file or directory" for WASM files

Build the contracts first:

```bash
./deployment/build.sh
```

### "workspace" errors

The fuzz crate is intentionally excluded from the workspace. Run fuzz commands from within `contracts/kinetic-router/fuzz/`.

### Slow execution

- Use dictionary files: `-dict=dict.txt` or `-dict=router.dict`
- Use parallel workers: `-jobs=4 -workers=4`
- Run multiple instances in parallel with different seeds

## Notes

- Corpus stored in `fuzz/corpus/<fuzzer_name>/`
- Crashes saved in `fuzz/artifacts/<fuzzer_name>/`
- Stats tracking enabled via `FUZZ_STATS=1` environment variable (Tena's fuzzer)
