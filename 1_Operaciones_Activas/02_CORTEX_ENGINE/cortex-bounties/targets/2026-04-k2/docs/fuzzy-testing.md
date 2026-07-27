# K2 Fuzzy Testing Implementation Guide

This document outlines a prioritized, stepwise approach to implementing fuzz testing for the K2 Soroban contracts.

## Prerequisites

```bash
# Install cargo-fuzz
cargo install --locked cargo-fuzz

# Install nightly toolchain (required for cargo-fuzz)
rustup install nightly
```

---

## Phase 1: Coverage-Guided Fuzzing

**Priority: High**

Coverage-guided fuzzing uses LLVM's libFuzzer to monitor code execution paths and mutate inputs to maximize branch coverage. This is the most effective technique for discovering edge cases and crashes.

### 1.1 Setup Infrastructure

Initialize fuzzing for the KineticRouter contract:

```bash
cd contracts/kinetic-router
cargo fuzz init
```

This creates:
```
contracts/kinetic-router/
├── Cargo.toml
├── src/
└── fuzz/
    ├── Cargo.toml
    └── fuzz_targets/
```

### 1.2 Configure Contract Manifest

Update `contracts/kinetic-router/Cargo.toml`:

```toml
[lib]
crate-type = ["cdylib", "rlib"]

[features]
testutils = []
```

### 1.3 Configure Fuzzing Manifest

Update `contracts/kinetic-router/fuzz/Cargo.toml`:

```toml
[package]
name = "k2-kinetic-router-fuzz"
version = "0.0.0"
publish = false
edition = "2021"

[package.metadata]
cargo-fuzz = true

# Exclude from parent workspace
[workspace]

[lib]
name = "k2_kinetic_router_fuzz"
path = "src/lib.rs"

[dependencies]
libfuzzer-sys = "0.4"
arbitrary = { version = "1", features = ["derive"] }
soroban-sdk = { version = "23.0.3", features = ["testutils"] }

[dependencies.k2-shared]
path = "../../shared"

# === Fuzz Targets ===

[[bin]]
name = "fuzz_lending_operations"
path = "fuzz_targets/fuzz_lending_operations.rs"
test = false
doc = false
bench = false

[[bin]]
name = "fuzz_liquidation"
path = "fuzz_targets/fuzz_liquidation.rs"
test = false
doc = false
bench = false

[[bin]]
name = "fuzz_flash_loan"
path = "fuzz_targets/fuzz_flash_loan.rs"
test = false
doc = false
bench = false

# === Utilities ===

[[bin]]
name = "generate_seeds"
path = "src/bin/generate_seeds.rs"
test = false
doc = false
```

### 1.4 Fuzz Target: Lending Operations

The lending operations fuzzer uses an **operation-based approach** for better code coverage. Instead of a fixed sequence (supply → borrow → repay → withdraw), it executes a randomized sequence of operations.

Create `fuzz/fuzz_targets/fuzz_lending_operations.rs`:

```rust
#![no_main]

use arbitrary::Arbitrary;
use libfuzzer_sys::fuzz_target;
use soroban_sdk::{testutils::Address as _, Address, Env};

/// Individual operations that can be performed on the lending pool
#[derive(Arbitrary, Debug, Clone)]
pub enum Operation {
    Supply { amount: u64 },
    Borrow { amount: u64 },
    Repay { amount: u64 },
    Withdraw { amount: u64 },
    AdvanceTime { seconds: u32 },
    SupplyMore { amount: u64 },
    PartialWithdraw { percent: u8 },
    RepayAll,
    WithdrawAll,
}

/// Amount hints for edge case testing
#[derive(Arbitrary, Debug, Clone, Copy)]
pub enum AmountHint {
    Raw,        // Use the raw amount value
    Max,        // Use u64::MAX
    Min,        // Use amount = 1 (minimum)
    PowerOfTwo, // Use a power of 2 near the amount
    LtvBoundary,// Use 80% of max (LTV boundary)
}

/// Enhanced fuzz input with operation sequencing
#[derive(Arbitrary, Debug, Clone)]
pub struct LendingInput {
    pub initial_supply: u64,
    pub initial_supply_hint: AmountHint,
    pub operations: [Option<Operation>; 8], // Up to 8 operations per test
}

fuzz_target!(|input: LendingInput| {
    let env = Env::default();
    env.mock_all_auths();
    env.cost_estimate().budget().reset_unlimited();

    // Setup contracts and user
    let user = Address::generate(&env);
    // ... (contract setup code)

    // Initial supply with amount hint processing
    let initial_supply = process_amount(input.initial_supply, input.initial_supply_hint);
    if initial_supply > 0 {
        let _ = router_client.try_supply(&user, &asset, &initial_supply, &user, &0u32);
    }

    // Check invariants after initial supply
    check_invariants(&env, &router_client, &a_token_client, &debt_token_client, &user, &asset);

    // Execute operations in sequence
    for op_opt in &input.operations {
        if let Some(op) = op_opt {
            execute_operation(&ctx, op);

            // Check invariants after each operation
            check_invariants(&env, &router_client, &a_token_client, &debt_token_client, &user, &asset);
        }
    }
});

fn check_invariants(env: &Env, router: &Client, a_token: &ATokenClient, debt_token: &DebtTokenClient, user: &Address, asset: &Address) {
    // Invariant 1: aToken balance should be non-negative
    assert!(a_token.balance(user) >= 0);

    // Invariant 2: debt token balance should be non-negative
    assert!(debt_token.balance(user) >= 0);

    // Invariant 3: User data should be retrievable without panic
    let _user_data = router.get_user_account_data(user);

    // Invariant 4: Reserve index monotonicity (indices >= RAY)
    let reserve_data = router.get_reserve_data(asset);
    assert!(reserve_data.liquidity_index >= 1_000_000_000);
    assert!(reserve_data.variable_borrow_index >= 1_000_000_000);

    // Invariant 5: Timestamp consistency
    assert!(reserve_data.last_update_timestamp <= env.ledger().timestamp());
}
```

### 1.4.1 Seed Corpus Generation

A seed generator creates targeted inputs for better initial coverage:

```bash
cd contracts/kinetic-router/fuzz
cargo run --bin generate_seeds
```

This creates ~19 seed files covering edge cases, LTV boundaries, interest accrual scenarios, and complex operation sequences.

### 1.5 Fuzz Target: Liquidation

Create `fuzz/fuzz_targets/fuzz_liquidation.rs`:

```rust
#![no_main]

use arbitrary::Arbitrary;
use libfuzzer_sys::fuzz_target;
use soroban_sdk::{testutils::Address as _, Address, Env};

#[derive(Arbitrary, Debug)]
struct LiquidationInput {
    collateral_amount: i128,
    debt_amount: i128,
    price_change_bps: i32,  // -10000 to +10000 (price drops/rises)
    liquidation_amount: i128,
    time_advance_secs: u64,
}

fuzz_target!(|input: LiquidationInput| {
    if input.collateral_amount <= 0 || input.debt_amount <= 0 {
        return;
    }

    let env = Env::default();
    env.mock_all_auths();
    env.cost_estimate().budget().reset_unlimited();

    // Setup borrower with collateral and debt
    let borrower = Address::generate(&env);
    let liquidator = Address::generate(&env);

    // ... setup code ...

    // Simulate price change
    update_oracle_price(&env, &oracle_client, input.price_change_bps);

    // Calculate health factor
    let health_factor = router_client.get_health_factor(&borrower);

    // Try liquidation
    let liquidation_result = router_client.try_liquidation_call(
        &liquidator,
        &collateral_asset,
        &debt_asset,
        &borrower,
        &input.liquidation_amount,
        &false, // receive_a_token
    );

    // Invariant: Liquidation should only succeed if HF < 1.0
    if health_factor >= 1_000_000_000_000_000_000i128 { // 1e18
        assert!(liquidation_result.is_err(),
            "Liquidation succeeded with healthy position: HF={}", health_factor);
    }

    // Invariant: Close factor limits (max 50% per tx)
    if liquidation_result.is_ok() {
        // Verify max 50% of debt was liquidated
        assert_close_factor_respected(&env, &router_client, &borrower);
    }
});
```

### 1.6 Fuzz Target: Flash Loans

Create `fuzz/fuzz_targets/fuzz_flash_loan.rs`:

```rust
#![no_main]

use arbitrary::Arbitrary;
use libfuzzer_sys::fuzz_target;
use soroban_sdk::{testutils::Address as _, Address, Env, Vec as SorobanVec};

#[derive(Arbitrary, Debug)]
struct FlashLoanInput {
    borrow_amounts: [i128; 3],  // Up to 3 assets
    repay_shortfall_bps: i32,   // How much less to repay (-100 to +100)
}

fuzz_target!(|input: FlashLoanInput| {
    let env = Env::default();
    env.mock_all_auths();
    env.cost_estimate().budget().reset_unlimited();

    let receiver = Address::generate(&env);

    // ... setup code ...

    // Build flash loan params
    let mut assets = SorobanVec::new(&env);
    let mut amounts = SorobanVec::new(&env);

    for amount in input.borrow_amounts.iter() {
        if *amount > 0 && *amount < i128::MAX / 2 {
            assets.push_back(asset.clone());
            amounts.push_back(*amount);
        }
    }

    if assets.is_empty() {
        return;
    }

    // Calculate expected repayment with premium (30 bps default)
    let premium_bps = 30i128;
    let expected_repayment: i128 = amounts.iter()
        .map(|a| a + (a * premium_bps / 10000))
        .sum();

    // Simulate receiver contract behavior
    let actual_repayment = if input.repay_shortfall_bps < 0 {
        expected_repayment - (expected_repayment * (-input.repay_shortfall_bps as i128) / 10000)
    } else {
        expected_repayment + (expected_repayment * (input.repay_shortfall_bps as i128) / 10000)
    };

    let result = router_client.try_flash_loan(
        &receiver,
        &assets,
        &amounts,
        &params,
    );

    // Invariant: Flash loan must fail if repayment < borrowed + premium
    if actual_repayment < expected_repayment {
        assert!(result.is_err(), "Flash loan succeeded with insufficient repayment");
    }

    // Invariant: Pool balance unchanged after successful flash loan
    if result.is_ok() {
        assert_pool_balance_unchanged(&env, &router_client);
    }
});
```

### 1.7 Running Fuzz Tests

```bash
# Run a specific fuzz target
cd contracts/kinetic-router
cargo +nightly fuzz run fuzz_lending_operations

# macOS requires thread sanitizer
cargo +nightly fuzz run fuzz_lending_operations --sanitizer=thread

# Run with timeout (e.g., 10 minutes)
cargo +nightly fuzz run fuzz_lending_operations -- -max_total_time=600

# Run with specific number of jobs
cargo +nightly fuzz run fuzz_lending_operations -- -jobs=4 -workers=4

# Generate coverage report
cargo +nightly fuzz coverage fuzz_lending_operations
```

### 1.8 Key Invariants Checklist

| Invariant | Description | Target |
|-----------|-------------|--------|
| Solvency | `sum(aToken) * liquidity_index == pool_balance + total_borrowed` | All operations |
| Debt tracking | `sum(debt_tokens) * borrow_index == total_debt` | Borrow/Repay |
| Health factor | Liquidation only when HF < 1.0 | Liquidation |
| Close factor | Max 50% debt liquidated per tx | Liquidation |
| Flash repayment | `repaid >= borrowed + premium` | Flash loan |
| Index monotonicity | Indices never decrease (always >= RAY) | All operations |
| No overflow | All math operations succeed | All operations |
| Balance non-negativity | aToken and debt token balances >= 0 | All operations |
| Timestamp consistency | Reserve timestamp <= current ledger timestamp | All operations |
| User data retrievable | `get_user_account_data()` never panics | All operations |

---

## Phase 2: Property-Based Testing

**Priority: Medium**

Property tests run in your normal test suite without nightly Rust. Use these for mathematical invariants and regression testing.

### 2.1 Add Dependencies

Update `tests/unit-tests/Cargo.toml`:

```toml
[dev-dependencies]
proptest = "1.4"
proptest-arbitrary-interop = "0.1"
```

### 2.2 Interest Rate Properties

Create `tests/unit-tests/src/proptest_interest_rate.rs`:

```rust
use proptest::prelude::*;

proptest! {
    #![proptest_config(ProptestConfig::with_cases(1000))]

    #[test]
    fn utilization_rate_bounded(
        total_debt in 0i128..1_000_000_000_000_000i128,
        available_liquidity in 0i128..1_000_000_000_000_000i128,
    ) {
        let total_liquidity = total_debt + available_liquidity;
        if total_liquidity == 0 {
            return Ok(());
        }

        let utilization = (total_debt * 1_000_000_000_000_000_000i128) / total_liquidity;

        // Utilization must be between 0 and 100%
        prop_assert!(utilization >= 0);
        prop_assert!(utilization <= 1_000_000_000_000_000_000i128);
    }

    #[test]
    fn borrow_rate_increases_with_utilization(
        base_rate in 0i128..100_000_000_000_000_000i128,
        slope1 in 0i128..500_000_000_000_000_000i128,
        slope2 in 0i128..3_000_000_000_000_000_000i128,
        optimal_utilization in 1i128..1_000_000_000_000_000_000i128,
        util_low in 0i128..500_000_000_000_000_000i128,
        util_high in 500_000_000_000_000_001i128..1_000_000_000_000_000_000i128,
    ) {
        let rate_low = calculate_borrow_rate(base_rate, slope1, slope2, optimal_utilization, util_low);
        let rate_high = calculate_borrow_rate(base_rate, slope1, slope2, optimal_utilization, util_high);

        // Higher utilization should mean higher rates
        prop_assert!(rate_high >= rate_low);
    }

    #[test]
    fn liquidity_index_only_increases(
        initial_index in 1_000_000_000_000_000_000i128..2_000_000_000_000_000_000i128,
        rate in 0i128..1_000_000_000_000_000_000i128,
        time_delta in 0u64..31536000u64, // Up to 1 year
    ) {
        let new_index = calculate_new_liquidity_index(initial_index, rate, time_delta);
        prop_assert!(new_index >= initial_index);
    }
}
```

### 2.3 Health Factor Properties

```rust
proptest! {
    #[test]
    fn health_factor_zero_debt_is_max(
        collateral_value in 1i128..1_000_000_000_000_000_000i128,
        liquidation_threshold in 1i128..10000i128,
    ) {
        let debt_value = 0i128;
        let hf = calculate_health_factor(collateral_value, debt_value, liquidation_threshold);

        // With zero debt, health factor should be maximum (type::MAX or special value)
        prop_assert!(hf == i128::MAX || hf > 1_000_000_000_000_000_000_000i128);
    }

    #[test]
    fn health_factor_decreases_with_debt(
        collateral_value in 1_000_000_000i128..1_000_000_000_000_000_000i128,
        liquidation_threshold in 5000i128..9500i128, // 50% - 95%
        debt_low in 1i128..500_000_000i128,
        debt_high in 500_000_001i128..1_000_000_000i128,
    ) {
        let hf_low = calculate_health_factor(collateral_value, debt_low, liquidation_threshold);
        let hf_high = calculate_health_factor(collateral_value, debt_high, liquidation_threshold);

        // More debt = lower health factor
        prop_assert!(hf_high <= hf_low);
    }
}
```

### 2.4 Run Property Tests

```bash
# Run all property tests
cargo test --package k2-unit-tests proptest

# Run with more cases
PROPTEST_CASES=10000 cargo test --package k2-unit-tests proptest
```

---

## Phase 3: Token Fuzzing

**Priority: Medium**

Adapt the [soroban-token-fuzzer](https://github.com/brson/soroban-token-fuzzer) pattern for aToken and DebtToken contracts.

### 3.1 aToken Fuzzer Setup

Create `contracts/a-token/fuzz/fuzz_targets/fuzz_a_token.rs`:

```rust
#![no_main]

use arbitrary::Arbitrary;
use libfuzzer_sys::fuzz_target;
use soroban_sdk::{testutils::Address as _, Address, Env};
use std::collections::HashMap;

#[derive(Arbitrary, Debug)]
enum TokenCommand {
    Transfer { from_idx: u8, to_idx: u8, amount: i128 },
    Approve { from_idx: u8, spender_idx: u8, amount: i128 },
    TransferFrom { spender_idx: u8, from_idx: u8, to_idx: u8, amount: i128 },
    Mint { to_idx: u8, amount: i128 },
    Burn { from_idx: u8, amount: i128 },
}

#[derive(Arbitrary, Debug)]
struct TokenFuzzInput {
    commands: Vec<TokenCommand>,
}

fuzz_target!(|input: TokenFuzzInput| {
    let env = Env::default();
    env.mock_all_auths();
    env.cost_estimate().budget().reset_unlimited();

    // Generate addresses
    let addresses: Vec<Address> = (0..5).map(|_| Address::generate(&env)).collect();

    // Track expected balances
    let mut balances: HashMap<Address, i128> = HashMap::new();
    let mut total_supply: i128 = 0;

    // ... deploy and initialize aToken ...

    for cmd in input.commands.iter().take(50) { // Limit sequence length
        match cmd {
            TokenCommand::Transfer { from_idx, to_idx, amount } => {
                let from = &addresses[(*from_idx as usize) % addresses.len()];
                let to = &addresses[(*to_idx as usize) % addresses.len()];

                let result = token_client.try_transfer(from, to, amount);

                if result.is_ok() {
                    *balances.entry(from.clone()).or_insert(0) -= amount;
                    *balances.entry(to.clone()).or_insert(0) += amount;
                }
            },
            TokenCommand::Mint { to_idx, amount } => {
                let to = &addresses[(*to_idx as usize) % addresses.len()];

                let result = token_client.try_mint(to, amount);

                if result.is_ok() {
                    *balances.entry(to.clone()).or_insert(0) += amount;
                    total_supply += amount;
                }
            },
            // ... handle other commands ...
        }

        // Verify invariants after each command
        assert_token_invariants(&env, &token_client, &balances, total_supply);
    }
});

fn assert_token_invariants(
    env: &Env,
    client: &ATokenClient,
    expected_balances: &HashMap<Address, i128>,
    expected_supply: i128,
) {
    // Invariant: Sum of balances equals total supply
    let actual_supply = client.total_supply();
    assert_eq!(actual_supply, expected_supply, "Total supply mismatch");

    // Invariant: All balances are non-negative
    for (addr, expected) in expected_balances {
        let actual = client.balance(addr);
        assert!(actual >= 0, "Negative balance for {:?}", addr);
        assert_eq!(actual, *expected, "Balance mismatch for {:?}", addr);
    }
}
```

### 3.2 DebtToken Considerations

DebtToken is non-transferable, so focus on:
- Mint/burn operations via KineticRouter
- Balance accuracy with borrow index scaling
- No direct transfers should succeed

---

## Phase 4: Stateful Sequence Fuzzing

**Priority: Lower** (Partially implemented in `fuzz_lending_operations`)

The `fuzz_lending_operations` target already implements operation sequencing with up to 8 operations per test case. For more complex multi-user or multi-asset scenarios, extend the approach below.

### 4.1 Multi-Operation Sequences

```rust
#[derive(Arbitrary, Debug)]
enum ProtocolCommand {
    Supply { user_idx: u8, asset_idx: u8, amount: i128 },
    Withdraw { user_idx: u8, asset_idx: u8, amount: i128 },
    Borrow { user_idx: u8, asset_idx: u8, amount: i128 },
    Repay { user_idx: u8, asset_idx: u8, amount: i128 },
    Liquidate { liquidator_idx: u8, borrower_idx: u8, amount: i128 },
    AdvanceTime { seconds: u64 },
    UpdatePrice { asset_idx: u8, new_price_bps: i32 },
}

#[derive(Arbitrary, Debug)]
struct ProtocolSequence {
    commands: Vec<ProtocolCommand>,
}

fuzz_target!(|input: ProtocolSequence| {
    let env = Env::default();
    // ... setup ...

    for cmd in input.commands.iter().take(100) {
        match cmd {
            ProtocolCommand::AdvanceTime { seconds } => {
                advance_ledger_time(&mut env, *seconds);
            },
            ProtocolCommand::UpdatePrice { asset_idx, new_price_bps } => {
                // Simulate oracle price change
                update_price(&env, &oracle, *asset_idx, *new_price_bps);
            },
            // ... handle other commands ...
        }

        // Global invariants after every operation
        assert_protocol_invariants(&env, &router_client);
    }
});
```

---

## Critical: Error Handling for Fuzzing

**Never use `panic!` in contract code.** The fuzzer treats panics as bugs.

```rust
// BAD - fuzzer will flag this
if amount <= 0 {
    panic!("Invalid amount");
}

// GOOD - fuzzer understands this is intentional error handling
if amount <= 0 {
    panic_with_error!(&env, Error::InvalidAmount);
}
```

---

## CI Integration

Add to `.github/workflows/fuzz.yml`:

```yaml
name: Fuzz Tests

on:
  schedule:
    - cron: '0 0 * * *'  # Nightly
  workflow_dispatch:

jobs:
  fuzz:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Install Rust nightly
        uses: dtolnay/rust-action@nightly

      - name: Install cargo-fuzz
        run: cargo install --locked cargo-fuzz

      - name: Run fuzz tests (10 min each)
        run: |
          cd contracts/kinetic-router
          cargo +nightly fuzz run fuzz_lending_operations -- -max_total_time=600
          cargo +nightly fuzz run fuzz_liquidation -- -max_total_time=600
          cargo +nightly fuzz run fuzz_flash_loan -- -max_total_time=600
```

---

## Metrics and Coverage

### Generate Coverage Reports

```bash
# Install LLVM tools
rustup component add --toolchain nightly llvm-tools-preview

# Generate coverage data
cargo +nightly fuzz coverage fuzz_lending_operations

# Convert to HTML report
llvm-cov show target/*/coverage/fuzz_lending_operations/coverage.profdata \
    --format=html > coverage.html
```

### Monitoring Fuzzer Progress

Watch the "cov" metric in fuzzer output:
- Rapidly increasing = finding new code paths
- Plateaued = most reachable code explored
- Consider adding new seed inputs if stuck

---

## References

- [Stellar Fuzzing Documentation](https://developers.stellar.org/docs/build/smart-contracts/example-contracts/fuzzing)
- [soroban-token-fuzzer](https://github.com/brson/soroban-token-fuzzer)
- [cargo-fuzz](https://rust-fuzz.github.io/book/cargo-fuzz.html)
- [proptest](https://crates.io/crates/proptest)
- [Rust Fuzz Book](https://rust-fuzz.github.io/book/)
