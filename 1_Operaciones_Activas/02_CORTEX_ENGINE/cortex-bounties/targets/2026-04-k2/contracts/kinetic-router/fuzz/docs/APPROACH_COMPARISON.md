# Fuzzing Approach Comparison

**Status:** Both approaches now coexist in the `fuzzy-test-merger` branch.

The K2 protocol uses **11 fuzz targets** combining two complementary approaches for comprehensive coverage.

---

## Executive Summary

| Aspect | Tena (Monolithic) | Ijonas (Specialized) |
|--------|-------------------|----------------------|
| **Architecture** | 1 fuzzer, 85+ ops | 10 fuzzers, ~80 ops total |
| **Invariant Checks** | 25+ types | ~40 across all fuzzers |
| **State-Aware Gen** | Yes | No (simple random) |
| **Auth Testing** | Uses mock_all_auths | Dedicated no-mock fuzzer |
| **Adversarial Patterns** | 7 attack types | Price-focused |
| **Audit Coverage** | General | HAL-01 to HAL-05, HAL-40 |

---

## How to Run Both

```bash
cd contracts/kinetic-router/fuzz

# List all 11 fuzzers
cargo +nightly fuzz list

# Run Tena's monolithic fuzzer (from kinetic-router, not fuzz dir)
cd ..
RUSTFLAGS="-Cunsafe-allow-abi-mismatch=sanitizer" \
  cargo +nightly fuzz run --sanitizer=thread fuzz_target_1 -- -max_total_time=900

# Run any of Ijonas's specialized fuzzers
cd fuzz
cargo +nightly fuzz run fuzz_lending_operations --sanitizer=none -- -max_total_time=900
```

---

## Architecture Comparison

### Tena's Approach: Monolithic with Shared Modules

```
fuzz_targets/
├── fuzz_target_1.rs          # Single comprehensive fuzzer
└── common/
    ├── mod.rs
    ├── constants.rs          # Shared constants
    ├── executor.rs           # Operation execution
    ├── invariants.rs         # 25+ invariant checks
    ├── mocks.rs              # Mock contracts
    ├── operations.rs         # 85+ operations with state-aware generation
    ├── setup.rs              # Test environment setup
    ├── snapshot.rs           # Protocol state snapshots
    └── stats.rs              # Statistics tracking
```

**Strengths:**
- Single corpus builds comprehensive coverage over time
- State-aware operation generation produces more meaningful sequences
- Shared code reduces duplication
- Built-in statistics for coverage analysis

### Ijonas's Approach: Specialized Fuzzers

```
fuzz_targets/
├── fuzz_auth_boundaries.rs       # Authorization testing (NO mock_all_auths)
├── fuzz_lending_operations.rs    # Core lending + accounting
├── fuzz_flash_loan.rs            # Flash loan mechanics
├── fuzz_liquidation.rs           # Liquidation mechanics
├── fuzz_multi_asset.rs           # Cross-asset interactions
├── fuzz_price_scenarios.rs       # Price manipulation resistance
├── fuzz_economic_invariants.rs   # Interest rate model
├── fuzz_admin_ops.rs             # Admin configuration
├── fuzz_admin_transfer.rs        # Two-step admin transfer
└── fuzz_reserve_config.rs        # Reserve configuration

src/
├── lib.rs                        # Shared library
├── invariants.rs                 # Shared invariant checks
└── bin/generate_seeds.rs         # Seed corpus generator
```

**Strengths:**
- Each fuzzer deeply explores specific functionality
- Easier to reason about failures
- Dedicated auth testing without mock bypasses
- Direct mapping to audit findings

---

## Operation Coverage Comparison

### Tena's Operations (85+ types)

| Category | Operations |
|----------|------------|
| **Core Lending** | Supply, SupplyOnBehalf, Withdraw, WithdrawAll, WithdrawToRecipient, Borrow, BorrowToRecipient, Repay, RepayAll, RepayOnBehalf, SetCollateral, SwapCollateral, TransferAToken |
| **Liquidation** | Liquidate, LiquidateReceiveAToken, PrepareLiquidation, ExecuteLiquidation, CreateAndLiquidate, MultiAssetLiquidation, FullMultiAssetLiquidation, SelfLiquidationAttempt, PriceCrashLiquidation |
| **Flash Loans** | FlashLoan (6 receiver types), MultiAssetFlashLoan, FlashLoanWhilePaused |
| **Edge Cases** | ZeroAmount (Supply/Borrow/Withdraw/Repay), Dust (Supply/Borrow/Withdraw/Repay), MaxAmount (Supply/Borrow), DrainLiquidity, MaxUtilization |
| **Oracle** | PriceChange, PriceToZero, PriceToMax, OracleStale, PriceVolatility |
| **Adversarial** | FirstDepositorAttack, DonationAttack, SandwichPriceChange, InterestAccrualExploit, RapidSupplyWithdraw, RapidBorrowRepay, BorrowMaxWithdrawAttempt, BadDebtScenario |
| **Admin** | UpdateReserveConfiguration, UpdateReserveRateStrategy, DropReserve, SetReserveSupplyCap, SetReserveBorrowCap, SetReserveDebtCeiling, SetReserveWhitelist/Blacklist, SetLiquidationWhitelist/Blacklist, ProposePoolAdmin, AcceptPoolAdmin, SetReserveActive, SetReserveFrozen, PauseProtocol, UnpauseProtocol, CollectProtocolReserves |
| **Time** | TimeWarp, ExtremeTimeWarp (up to 10 years) |

### Ijonas's Operations (Distributed across 10 fuzzers)

| Fuzzer | Operations |
|--------|------------|
| **fuzz_auth_boundaries** | SetFlashLoanPremium, SetTreasury, SetDexRouter, SetPoolConfigurator, SetIncentivesContract, SetFlashLiquidationHelper, Pause, Unpause, ProposeAdmin, AcceptAdmin, CancelAdminProposal, Supply, Borrow, Repay, Withdraw (with OnBehalf variants), FlashLoan |
| **fuzz_lending_operations** | Supply, Borrow, Repay, Withdraw, AdvanceTime, SetPrice, Liquidate, SetCollateralEnabled |
| **fuzz_liquidation** | Supply, Borrow, SetPrice, Liquidate, AdvanceTime |
| **fuzz_flash_loan** | Supply, FlashLoan, AdvanceTime, SetPrice |
| **fuzz_multi_asset** | Supply, Borrow, Repay, Withdraw, CrossAssetBorrow, CrossAssetLiquidate, SetPrice (per asset) |
| **fuzz_price_scenarios** | Supply, Borrow, SetPrice (FlashCrash, Spike, GradualDecline, Oscillate, ExtremeLow/High), SandwichLiquidation, FrontRunBorrow, PriceOscillation |
| **fuzz_economic_invariants** | Supply, Borrow, Repay, Withdraw, AdvanceTime, BorrowToUtilization, LargeSupply, RepayAll, WithdrawAll |
| **fuzz_admin_ops** | Various admin parameter updates |
| **fuzz_admin_transfer** | ProposeAdmin, AcceptAdmin, CancelProposal, CheckPendingAdmin |
| **fuzz_reserve_config** | LTV, liquidation thresholds, caps, flags |

---

## Invariant Coverage Comparison

### Tena's Invariants (25+ types)

```
Core Invariants (every operation):
├── OperationInvariants
├── FailedOperationUnchanged
├── ProtocolInvariants
├── ProtocolSolvency
├── TreasuryAccrual
├── UtilizationInvariants
├── LiquidationInvariants
├── IndexMonotonicity
├── AccruedTreasuryMonotonicity
├── DebtCeilingInvariants
└── ReserveFactorInvariants

Conditional Invariants:
├── FlashLoanPremium (on flash loan)
├── FlashLoanRepayment (on flash loan)
├── InterestInvariants (when time passes)
├── InterestMath (when time passes)
├── FeeCalculationInvariants (when time passes)
├── LiquidationFairness (on liquidation)
├── NoRateManipulation
├── OracleSanity
├── NoValueExtraction (every 5 ops)
└── AdminCannotSteal (every 5 ops)

Final Invariants:
├── FinalInvariants
├── CumulativeRounding
├── DustAccumulation
├── LiquidationBonusInvariants
├── PauseStateInvariant
├── AccessControlInvariants
└── ParameterBounds
```

### Ijonas's Invariants (Distributed)

| Fuzzer | Key Invariants |
|--------|----------------|
| **fuzz_auth_boundaries** | Unauthorized operations must fail, dual auth for on_behalf_of, state unchanged on auth failure |
| **fuzz_lending_operations** | Token conservation, index monotonicity, rate relationship (supply <= borrow), health factor validity |
| **fuzz_liquidation** | Debt reduction, collateral reduction, HF improvement, close factor (50% max), liquidator receives collateral |
| **fuzz_flash_loan** | Pool balance conservation, treasury premium, premium distribution, atomic rollback on failure |
| **fuzz_multi_asset** | Reserve isolation, cross-asset HF calculation, index independence |
| **fuzz_price_scenarios** | Price bounds, oracle consistency, HF direction, no profit extraction, protocol solvency |
| **fuzz_economic_invariants** | Utilization bounds (0-100%), rate relationship, rate bounds, index monotonicity, treasury non-decreasing, rate-utilization monotonicity |
| **fuzz_admin_transfer** | Only admin can propose, only pending can accept, state consistency |

---

## Key Differentiators

### 1. State-Aware Operation Generation (Tena's Advantage)

Tena's fuzzer maintains a `SimulatedState` that tracks:
- User balances (underlying, collateral, debt)
- Pool liquidity
- Health factors
- Pause state

Operations are generated based on this state:
```rust
// Example: Early phase builds state aggressively
match phase {
    0..=30 => {
        categories.push((OperationCategory::Supply, 5));
        if has_collateral {
            categories.push((OperationCategory::Borrow, 4));
        }
    }
    // Later phases stress test
    _ => {
        categories.push((OperationCategory::Adversarial, 3));
        categories.push((OperationCategory::Liquidation, 5));
    }
}
```

This produces more meaningful operation sequences (e.g., supply before borrow, build positions before liquidation attempts).

### 2. Authorization Testing Without Mocks (Ijonas's Advantage)

Ijonas's `fuzz_auth_boundaries` is the only fuzzer that tests authorization **without** `mock_all_auths()`:

```rust
// We specifically mock individual auths to test access control
ctx.env.mock_auths(&[soroban_sdk::testutils::MockAuth {
    address: caller_addr,
    invoke: &soroban_sdk::testutils::MockAuthInvoke {
        contract: ctx.router_addr,
        fn_name: "set_flash_loan_premium",
        args: ...,
        sub_invokes: &[],
    },
}]);

let result = ctx.router_client.try_set_flash_loan_premium(&premium);

// Verify unauthorized callers are rejected
if !is_authorized {
    assert!(result.is_err(), "Non-admin should fail");
}
```

This directly validates HAL-01 through HAL-05 audit findings.

### 3. Flash Loan Receiver Types (Tena's Advantage)

Tena tests 6 malicious flash loan receiver types:

| Receiver Type | Attack Vector |
|---------------|---------------|
| `Standard` | Normal operation |
| `Reentrant` | Attempts reentrant calls |
| `ReentrantRepayLiquidation` | Reentrant liquidation during repay |
| `NonRepaying` | Doesn't repay the loan |
| `StateManipulating` | Tries to manipulate protocol state |
| `OracleManipulating` | Attempts to manipulate oracle prices |

Ijonas's approach uses a configurable receiver with different behaviors (ExactRepay, Overpay, Underpay, NoRepay, Panic, ReturnFalse).

### 4. Adversarial Attack Patterns (Tena's Advantage)

Tena explicitly tests known DeFi attack patterns:

| Attack | Description |
|--------|-------------|
| `FirstDepositorAttack` | Exploit rounding in first deposit |
| `DonationAttack` | Donate to aToken to manipulate exchange rate |
| `SandwichPriceChange` | Front-run/back-run price changes |
| `InterestAccrualExploit` | Extract value from interest timing |
| `RapidSupplyWithdraw` | Rapid cycling to extract rounding |
| `BorrowMaxWithdrawAttempt` | Borrow max then try to escape |

### 5. Statistics and Coverage Tracking (Tena's Advantage)

Tena tracks operation execution statistics:
```rust
// Prints every 100 runs
[FUZZ] === 100 successful fuzz runs completed ===
Operations: Supply: 45 (42 success), Borrow: 30 (25 success), ...
Invariants: ProtocolSolvency: 100, IndexMonotonicity: 100, ...
```

This helps identify untested code paths.

---

## Coverage Gap Analysis

### Areas Better Covered by Tena

| Area | Coverage |
|------|----------|
| Edge case amounts (zero, dust, max) | Dedicated operations |
| Malicious flash loan receivers | 6 receiver types |
| Known DeFi attacks | 7 attack patterns |
| Interest math precision | InterestMath invariant |
| Cumulative rounding errors | Rounding tracking |
| State-aware sequences | Simulated state |

### Areas Better Covered by Ijonas

| Area | Coverage |
|------|----------|
| Authorization without mock bypasses | Dedicated fuzzer |
| Halborn audit findings (HAL-01 to HAL-05) | Direct targeting |
| Two-step admin transfer (HAL-40) | Dedicated fuzzer |
| Interest rate parameter validation | Economic invariants fuzzer |
| Cross-asset isolation | Multi-asset fuzzer |

---

## Recommended Usage

Both approaches now coexist in the `fuzzy-test-merger` branch. The recommended testing strategy is:

| Fuzzer | Purpose | Run Time |
|--------|---------|----------|
| `fuzz_target_1` | Broad coverage, attack patterns, state-aware testing | Long (hours) |
| `fuzz_lending_operations` | Core lending validation | Medium (15-60 min) |
| `fuzz_liquidation` | Liquidation edge cases | Medium |
| `fuzz_flash_loan` | Flash loan atomicity | Medium |
| `fuzz_auth_boundaries` | Authorization without mocks | Short (10-30 min) |
| `fuzz_multi_asset` | Cross-asset isolation | Medium |
| `fuzz_price_scenarios` | Price manipulation resistance | Medium |
| `fuzz_economic_invariants` | Interest rate model | Medium |
| `fuzz_admin_ops` | Admin operation safety | Short |
| `fuzz_admin_transfer` | Two-step admin transfer | Short |
| `fuzz_reserve_config` | Reserve configuration bounds | Short |

**CI/CD Strategy:**
1. Run Tena's fuzzer for broad coverage (longer runs)
2. Run Ijonas's fuzzers for targeted audit validation (shorter, focused runs)

```bash
#!/bin/bash
# Run all fuzzers in CI
cd contracts/kinetic-router/fuzz

# Tena's fuzzer (5 min)
cd ..
RUSTFLAGS="-Cunsafe-allow-abi-mismatch=sanitizer" \
  cargo +nightly fuzz run --sanitizer=thread fuzz_target_1 -- -max_total_time=300
cd fuzz

# Ijonas's fuzzers (5 min each)
for target in fuzz_lending_operations fuzz_liquidation fuzz_flash_loan \
              fuzz_auth_boundaries fuzz_multi_asset fuzz_price_scenarios \
              fuzz_economic_invariants fuzz_admin_ops fuzz_admin_transfer \
              fuzz_reserve_config; do
  cargo +nightly fuzz run "$target" --sanitizer=none -- -max_total_time=300
done
```
