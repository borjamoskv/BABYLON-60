# K2 Fuzz Testing Guide

This repository contains **11 fuzz targets** for the kinetic-router contract, combining two complementary approaches:

| Approach | Author | Fuzzers | Focus |
|----------|--------|---------|-------|
| **Monolithic** | Tena | 1 | Broad coverage: 85+ ops, 8 users, 4 assets, attack patterns |
| **Specialized** | Ijonas | 10 | Deep coverage: targeted invariants per domain |

## Table of Contents

- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Available Fuzzers](#available-fuzzers)
- [Tena's Monolithic Fuzzer](#tenas-monolithic-fuzzer)
- [Ijonas's Specialized Fuzzers](#ijonass-specialized-fuzzers)
  - [fuzz_auth_boundaries](#fuzz_auth_boundaries)
  - [fuzz_lending_operations](#fuzz_lending_operations)
  - [fuzz_flash_loan](#fuzz_flash_loan)
  - [fuzz_liquidation](#fuzz_liquidation)
  - [fuzz_multi_asset](#fuzz_multi_asset)
  - [fuzz_price_scenarios](#fuzz_price_scenarios)
  - [fuzz_economic_invariants](#fuzz_economic_invariants)
  - [Additional Fuzzers](#additional-fuzzers)
- [Invariants Reference](#invariants-reference)
- [CI/CD Integration](#cicd-integration)
- [Understanding Output](#understanding-output)
- [Architecture](#architecture)
- [Troubleshooting](#troubleshooting)

---

## Prerequisites

```bash
# Install nightly Rust
rustup install nightly

# Install cargo-fuzz
cargo install --locked cargo-fuzz

# Build contracts (required for WASM files)
./deployment/build.sh
```

---

## Quick Start

Run any fuzzer for 10 minutes:

```bash
cd contracts/kinetic-router/fuzz

# List all available fuzzers
cargo +nightly fuzz list

# Run any fuzzer (macOS requires thread sanitizer with RUSTFLAGS)
RUSTFLAGS="-Cunsafe-allow-abi-mismatch=sanitizer" \
  cargo +nightly fuzz run --sanitizer=thread fuzz_target_1 -- -max_total_time=600

RUSTFLAGS="-Cunsafe-allow-abi-mismatch=sanitizer" \
  cargo +nightly fuzz run --sanitizer=thread fuzz_lending_operations -- -max_total_time=600
```

> **Note**: On macOS (especially ARM64/Apple Silicon), all fuzzers require the `RUSTFLAGS` and `--sanitizer=thread` flags due to linker compatibility issues. The `--sanitizer=none` option causes linker errors.

### Common Durations

| Duration | Flag |
|----------|------|
| 5 minutes | `-max_total_time=300` |
| 10 minutes | `-max_total_time=600` |
| 15 minutes | `-max_total_time=900` |
| 1 hour | `-max_total_time=3600` |

---

## Available Fuzzers

| Fuzzer | Author | Focus |
|--------|--------|-------|
| `fuzz_target_1` | Tena | Monolithic: 85+ ops, attack patterns, state-aware generation |
| `fuzz_lending_operations` | Ijonas | Core lending: supply, borrow, repay, withdraw cycles |
| `fuzz_liquidation` | Ijonas | Liquidation mechanics under price stress |
| `fuzz_flash_loan` | Ijonas | Flash loan premium, atomicity, receiver behaviors |
| `fuzz_auth_boundaries` | Ijonas | Authorization checks (no mock bypass) |
| `fuzz_multi_asset` | Ijonas | Cross-asset isolation |
| `fuzz_price_scenarios` | Ijonas | Price manipulation resistance |
| `fuzz_economic_invariants` | Ijonas | Interest rate model validation |
| `fuzz_admin_ops` | Ijonas | Admin configuration safety |
| `fuzz_admin_transfer` | Ijonas | Two-step admin transfer |
| `fuzz_reserve_config` | Ijonas | Reserve configuration bounds |

---

## Tena's Monolithic Fuzzer

The `fuzz_target_1` fuzzer uses a **stateful operation-based approach** with:
- 85+ operation types
- 8 concurrent users
- 4 assets
- 25+ invariant checks
- Phase-weighted operation generation
- Attack pattern detection

### Running

```bash
cd contracts/kinetic-router/fuzz

RUSTFLAGS="-Cunsafe-allow-abi-mismatch=sanitizer" \
  cargo +nightly fuzz run --sanitizer=thread fuzz_target_1 -- -max_total_time=600

# With dictionary for better coverage
RUSTFLAGS="-Cunsafe-allow-abi-mismatch=sanitizer" \
  cargo +nightly fuzz run --sanitizer=thread fuzz_target_1 \
  -- -max_total_time=3600 -dict=router.dict
```

### Operations Tested

| Category | Operations |
|----------|------------|
| **Core** | Supply, Withdraw, Borrow, Repay (+ OnBehalf variants) |
| **Liquidation** | Liquidate, two-step flow, multi-asset, self-attempt, price crash |
| **Flash Loans** | Standard, multi-asset, while paused, 6 receiver behaviors |
| **Edge Cases** | Zero/dust/max amounts, drain liquidity, max utilization |
| **Oracle** | Price changes, zero/max prices, staleness, volatility |
| **Adversarial** | First depositor attack, donation attack, sandwich, interest exploit |
| **Admin** | Reserve config, caps, whitelist/blacklist, pause, admin transfer |

### Invariants Verified

- Protocol solvency (collateral >= debt)
- Token conservation (sum of balances = initial)
- Index monotonicity (indices never decrease)
- Health factor consistency
- Liquidation fairness
- No value extraction beyond yield
- Failed operations unchanged
- Supply/borrow caps enforced

---

## Ijonas's Specialized Fuzzers

Ten focused fuzzers each targeting specific domains with deep invariant checking.

### Running

```bash
cd contracts/kinetic-router/fuzz

# Run a specialized fuzzer
RUSTFLAGS="-Cunsafe-allow-abi-mismatch=sanitizer" \
  cargo +nightly fuzz run --sanitizer=thread fuzz_lending_operations -- -max_total_time=600

# With dictionary
RUSTFLAGS="-Cunsafe-allow-abi-mismatch=sanitizer" \
  cargo +nightly fuzz run --sanitizer=thread fuzz_lending_operations \
  -- -max_total_time=600 -dict=dict.txt

# Parallel execution (multiple seeds in separate terminals)
RUSTFLAGS="-Cunsafe-allow-abi-mismatch=sanitizer" \
  cargo +nightly fuzz run --sanitizer=thread fuzz_lending_operations -- -seed=1 &
RUSTFLAGS="-Cunsafe-allow-abi-mismatch=sanitizer" \
  cargo +nightly fuzz run --sanitizer=thread fuzz_lending_operations -- -seed=2 &
```

### Halborn Audit Coverage

The fuzz suite specifically addresses findings from the Halborn security audit:
- **HAL-01 to HAL-05**: Authorization and access control issues
- **HAL-40**: Two-step admin transfer testing

---

### `fuzz_auth_boundaries`

**Purpose**: Tests authorization boundaries WITHOUT using `mock_all_auths()`, ensuring proper access control.

**Key Difference**: Unlike other fuzzers that use `mock_all_auths()` for convenience, this fuzzer uses specific `mock_auths()` calls to test that unauthorized callers are properly rejected.

**Operations Tested**:
- Admin operations (set parameters, pause, emergency actions)
- User operations with `on_behalf_of` scenarios
- Two-step admin transfer (propose → accept/cancel)
- Pool configurator restricted functions

**Invariants**:
- Only authorized addresses can execute admin functions
- `on_behalf_of` operations require dual authorization
- Rejected operations don't change state

**Audit Coverage**: HAL-01, HAL-02, HAL-03, HAL-04, HAL-05, HAL-40

---

### `fuzz_lending_operations`

**Purpose**: Core lending operations with comprehensive accounting verification.

**Operations**:
- `Supply` / `Withdraw` - Deposit and withdrawal of assets
- `Borrow` / `Repay` - Borrowing against collateral
- `AdvanceTime` - Interest accrual simulation
- `SetPrice` - Price oracle manipulation
- `Liquidate` - Liquidation attempts
- `SetCollateralEnabled` - Collateral configuration

**Invariants**:
| Invariant | Description |
|-----------|-------------|
| Token Conservation | Tokens in = tokens out (accounting for interest) |
| Index Monotonicity | Liquidity and borrow indices only increase |
| Rate Consistency | Supply rate ≤ borrow rate |
| Health Factor Validity | HF > 0 when debt exists |
| Supply Consistency | aToken supply ≥ 0, debt supply ≥ 0 |

---

### `fuzz_flash_loan`

**Purpose**: Flash loan execution and premium distribution.

**Operations**:
- Flash loan execution with various amounts
- Premium calculation verification
- Receiver contract interactions (6 behaviors: ExactRepay, Overpay, Underpay, NoRepay, Panic, ReturnFalse)

**Invariants**:
| Invariant | Description |
|-----------|-------------|
| Pool Balance Conservation | aToken balance ≥ initial after successful flash loan |
| Treasury Premium | Treasury receives its share of premium |
| Total Value Conservation | Premium distributed correctly |
| Index Monotonicity | Indices don't decrease during flash loan |
| Atomic Rollback | Failed flash loans don't change state |

---

### `fuzz_liquidation`

**Purpose**: Liquidation mechanics and accounting.

**Operations**:
- Price manipulation to trigger liquidations
- Liquidation attempts at various amounts
- Health factor boundary testing

**Invariants**:
| Invariant | Description |
|-----------|-------------|
| Debt Reduction | Borrower debt decreases after liquidation |
| Collateral Reduction | Borrower collateral decreases |
| Liquidator Receives | Liquidator receives collateral |
| Health Factor Improvement | HF improves or position closes |
| Close Factor | Max 50% of debt liquidated per tx |
| Index Monotonicity | Indices only increase |

---

### `fuzz_multi_asset`

**Purpose**: Cross-asset interactions with multiple reserves.

**Configuration** (3 reserves with different risk parameters):
| Reserve | LTV | Liquidation Threshold | Liquidation Bonus |
|---------|-----|----------------------|-------------------|
| Asset A (Conservative) | 50% | 65% | 10% |
| Asset B (Standard) | 75% | 80% | 5% |
| Asset C (Aggressive) | 85% | 90% | 3% |

**Operations**:
- Cross-collateral borrowing (supply A, borrow B)
- Cross-asset liquidations
- Independent price manipulation per asset
- Multi-asset health factor scenarios

**Invariants**:
| Invariant | Description |
|-----------|-------------|
| Reserve Isolation | Operations on one reserve don't corrupt others |
| Cross-Asset HF | Health factor aggregates correctly across assets |
| Index Independence | Each reserve's indices evolve independently |
| Cross-Liquidation | Proper state changes on both collateral and debt reserves |

---

### `fuzz_price_scenarios`

**Purpose**: Protocol behavior under extreme and adversarial price conditions.

**Price Movements**:
| Type | Description |
|------|-------------|
| `FlashCrash` | Sudden price drop (0-99%) |
| `Spike` | Sudden price increase (0-1000%) |
| `GradualDecline` | Step-by-step decline |
| `Oscillate` | Alternating up/down |
| `ExtremeLow` | Minimum valid price |
| `ExtremeHigh` | Maximum valid price |

**Attack Patterns**:
| Attack | Description |
|--------|-------------|
| `SandwichLiquidation` | Drop price → liquidate → restore price |
| `FrontRunBorrow` | Drop collateral price before borrow |
| `PriceOscillation` | Rapid price cycling for value extraction |

**Invariants**:
| Invariant | Description |
|-----------|-------------|
| Price Bounds | No negative/zero prices; within valid range |
| Oracle Consistency | Oracle returns valid non-zero prices |
| HF Direction | HF moves correctly with price changes |
| No Profit Extraction | Can't extract value through pure manipulation |
| Protocol Solvency | Positive balances, valid indices under stress |

---

### `fuzz_economic_invariants`

**Purpose**: Interest rate model, utilization, and treasury accrual.

**Configurable Parameters**:
| Parameter | Description | Range |
|-----------|-------------|-------|
| `base_rate_bps` | Base borrow rate | 0-50% |
| `slope1_bps` | Rate slope below optimal | 0-100% |
| `slope2_bps` | Rate slope above optimal | 0-300% |
| `optimal_utilization_bps` | Target utilization | 10-95% |
| `reserve_factor_bps` | Protocol fee | 0-50% |

**Operations**:
- Standard lending operations
- `BorrowToUtilization` - Target specific utilization
- `LargeSupply` - Test low utilization scenarios
- `RepayAll` / `WithdrawAll` - Full position closure

**Invariants**:
| Invariant | Description |
|-----------|-------------|
| Utilization Bounds | 0% ≤ utilization ≤ 100% |
| Rate Relationship | Supply rate ≤ borrow rate |
| Rate Bounds | Rates within reasonable limits |
| Index Monotonicity | Indices only increase |
| Index Lower Bound | Indices always ≥ RAY |
| Treasury Non-Decreasing | Treasury only accrues |
| Interest Accrual | Time + debt + rate = interest |
| Rate-Utilization Monotonicity | Higher utilization → higher rates |

---

### Additional Fuzzers

#### `fuzz_admin_ops`
**Purpose**: Administrative operation fuzzing - parameter updates, reserve configuration, emergency actions.

#### `fuzz_admin_transfer`
**Purpose**: Two-step admin transfer process - propose admin, accept admin, cancel proposal.

#### `fuzz_reserve_config`
**Purpose**: Reserve configuration parameter fuzzing - LTV, liquidation threshold, caps, flags.

---

## Invariants Reference

### Universal Invariants (All Fuzzers)

```
1. Index Monotonicity
   - liquidity_index[t+1] ≥ liquidity_index[t]
   - variable_borrow_index[t+1] ≥ variable_borrow_index[t]

2. Index Lower Bound
   - liquidity_index ≥ RAY (1e9)
   - variable_borrow_index ≥ RAY (1e9)

3. Rate Relationship
   - current_liquidity_rate ≤ current_variable_borrow_rate

4. Supply Consistency
   - atoken_total_supply ≥ 0
   - debt_total_supply ≥ 0
```

### Constants

```rust
RAY = 1_000_000_000          // 1e9 - Rate/index precision
WAD = 1e18                    // Health factor precision
BASE_PRICE = 1e14            // $1 with 14 decimals
CLOSE_FACTOR = 50%           // Max debt liquidatable per tx
```

---

## CI/CD Integration

Run all fuzzers for 5 minutes each:

```bash
#!/bin/bash
cd contracts/kinetic-router/fuzz

export RUSTFLAGS="-Cunsafe-allow-abi-mismatch=sanitizer"

for target in fuzz_target_1 fuzz_lending_operations fuzz_liquidation fuzz_flash_loan \
              fuzz_auth_boundaries fuzz_multi_asset fuzz_price_scenarios \
              fuzz_economic_invariants fuzz_admin_ops fuzz_admin_transfer \
              fuzz_reserve_config; do
  echo "Running $target..."
  cargo +nightly fuzz run --sanitizer=thread "$target" -- -max_total_time=300
done
```

Exit code 0 means no crashes were found.

---

## Understanding Output

```
#6773  NEW    cov: 7446 ft: 7447 corp: 3/75b lim: 68 exec/s: 218 rss: 40Mb
```

| Field | Meaning |
|-------|---------|
| `#6773` | Test cases executed |
| `cov: 7446` | Code coverage (unique paths) |
| `NEW` | New interesting input found |
| `exec/s` | Executions per second |
| `rss` | Memory usage |

When coverage stops increasing, most reachable paths have been explored.

### Crash Reproduction

Crashes are saved to `fuzz/artifacts/<fuzzer>/crash-<hash>`.

```bash
RUSTFLAGS="-Cunsafe-allow-abi-mismatch=sanitizer" \
  cargo +nightly fuzz run --sanitizer=thread fuzz_lending_operations \
  fuzz/artifacts/fuzz_lending_operations/crash-<hash>
```

---

## Architecture

### Directory Structure

```
contracts/kinetic-router/fuzz/
├── Cargo.toml              # Combined config with all 11 targets
├── dict.txt                # Dictionary for specialized fuzzers
├── router.dict             # Dictionary for monolithic fuzzer
├── src/
│   ├── lib.rs              # Shared library for specialized fuzzers
│   ├── invariants.rs       # Invariant checks
│   └── bin/generate_seeds.rs
└── fuzz_targets/
    ├── fuzz_target_1.rs    # Tena's monolithic fuzzer
    ├── common/             # Shared modules for fuzz_target_1
    │   ├── mod.rs
    │   ├── constants.rs
    │   ├── executor.rs
    │   ├── invariants.rs
    │   ├── mocks.rs
    │   ├── operations.rs
    │   ├── setup.rs
    │   ├── snapshot.rs
    │   └── stats.rs
    ├── fuzz_lending_operations.rs
    ├── fuzz_liquidation.rs
    ├── fuzz_flash_loan.rs
    ├── fuzz_auth_boundaries.rs
    ├── fuzz_multi_asset.rs
    ├── fuzz_price_scenarios.rs
    ├── fuzz_economic_invariants.rs
    ├── fuzz_admin_ops.rs
    ├── fuzz_admin_transfer.rs
    └── fuzz_reserve_config.rs
```

### Shared Types (`src/lib.rs`)

```rust
pub enum User { User1, User2 }

pub enum Operation {
    Supply { user: User, amount: u64 },
    Borrow { user: User, amount: u64 },
    Repay { user: User, amount: u64 },
    Withdraw { user: User, amount: u64 },
    AdvanceTime { seconds: u32 },
    SetPrice { price_bps: u16 },
    Liquidate { liquidator: User, borrower: User, amount: u64 },
    // ...
}

pub enum AmountHint {
    Raw, Max, Min, PowerOfTwo, LtvBoundary,
}
```

### Mock Contracts

Each fuzzer includes mock contracts:
- `MockReflector` - Simulates Reflector price oracle
- `MockFlashLoanReceiver` - For flash loan testing

### Seed Corpus Generation

```bash
cd contracts/kinetic-router/fuzz
cargo run --bin generate_seeds
```

Creates ~30 seed files covering edge cases, LTV boundaries, time advancement, and attack scenarios.

---

## Troubleshooting

### Linker errors on macOS

On macOS (especially ARM64/Apple Silicon), **all fuzzers** require the thread sanitizer with the ABI mismatch flag. Using `--sanitizer=none` causes linker errors.

**Solution**: Always use this pattern:
```bash
RUSTFLAGS="-Cunsafe-allow-abi-mismatch=sanitizer" \
  cargo +nightly fuzz run --sanitizer=thread <fuzzer_name> -- -max_total_time=600
```

### "No such file or directory" for WASM

Build contracts first:
```bash
./deployment/build.sh
```

### Slow execution

- Use dictionary files: `-dict=dict.txt` or `-dict=router.dict`
- Run multiple instances with different seeds
- First run is slow due to compilation; subsequent runs are faster

### Corpus Management

```bash
# Minimize corpus
RUSTFLAGS="-Cunsafe-allow-abi-mismatch=sanitizer" \
  cargo +nightly fuzz cmin --sanitizer=thread fuzz_lending_operations

# Merge corpus from multiple runs
RUSTFLAGS="-Cunsafe-allow-abi-mismatch=sanitizer" \
  cargo +nightly fuzz merge --sanitizer=thread fuzz_lending_operations corpus1 corpus2
```

### Best Practices

**When Adding New Fuzzers**:
1. Add entry to `Cargo.toml`
2. Create snapshot structs for state tracking
3. Implement invariant check functions
4. Use `try_*` methods to handle expected failures gracefully
5. Document invariants in file header

**Interpreting Results**:
- **Crash**: Invariant violation found - investigate and fix
- **Timeout**: Complex input - may indicate performance issue
- **OOM**: Memory leak or excessive allocation
