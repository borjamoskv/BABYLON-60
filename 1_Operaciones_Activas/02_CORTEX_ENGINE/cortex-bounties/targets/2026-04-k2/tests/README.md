# K2 Tests

Test suite for K2 smart contracts using WASM-backed testing for resource measurement.

## Overview

- Unit Tests (`tests/unit-tests`): Contract-specific tests using WASM imports
- Integration Tests (`tests/integration-tests`): Multi-contract workflow tests
- Resource Analysis: Tools for measuring resource consumption

## Building Contracts

Build contracts before running tests:

```bash
# Build all contracts
stellar contract build

# Build specific contract
cd contracts/treasury && stellar contract build
```

## Running Tests

### Unit Tests

Unit tests use WASM-backed contract registration for resource measurement:

```bash
# Build contracts first
stellar contract build

# Run all unit tests
cargo test --package k2-unit-tests

# Run tests for a specific contract
cargo test --package k2-unit-tests treasury_test
cargo test --package k2-unit-tests kinetic_router_test
cargo test --package k2-unit-tests price_oracle_test

# Run with output to see resource usage
cargo test --package k2-unit-tests -- --nocapture
```

### Integration Tests

Integration tests require WASM files and run with `--release`:

```bash
# Build contracts first
stellar contract build

# Run all integration tests
cargo test --package k2-integration-tests --release

# Run specific test
cargo test --package k2-integration-tests --release test_lending_flow

# Run with output to see resource analysis
cargo test --package k2-integration-tests --release -- --nocapture

# Force rebuild if tests fail after contract changes
rm -rf target/release/deps/k2_integration*
cargo test --package k2-integration-tests --release
```

### Resource Analysis Tests

Run resource analysis tests:

```bash
# Build contracts first
stellar contract build

# Run resource analysis tests
cargo test --package k2-integration-tests --release test_resource_analysis -- --nocapture

# Run specific resource analysis test
cargo test --package k2-integration-tests --release test_resource_analysis_supply_operation -- --nocapture
```

## Understanding Resource Consumption

### WASM-Backed Testing

Direct Rust registration (`env.register(Contract, ())`):
- Excludes VM instantiation cost
- Produces unrealistic resource measurements
- Misses the main cost factor

WASM-backed registration (`env.register(contract::WASM, ())`):
- Includes VM instantiation (about 10M CPU per contract)
- Matches Futurenet and Mainnet behavior
- Produces accurate resource measurements

### Resource Attribution

Soroban charges for storage and contract operations, not computation:

| Operation | Typical Cost | Notes |
|-----------|--------------|-------|
| VM Instantiation | 10M+ CPU | Per unique contract per transaction |
| Cross-Contract Call | 10M+ CPU | Each unique target creates new VM instantiation |
| Storage Read | ~100k CPU | Per ledger entry |
| Storage Write | ~200k CPU | Per ledger entry |
| Computation | Variable | Loops, calculations, validation |

### Resource Analysis Tools

```bash
# Analyze deployed contract resources
./scripts/analyze_transaction_resources.sh CONTRACT_ID function_name

# Check WASM sizes
./scripts/check_wasm_sizes.sh

# Run resource analysis tests
cargo test --package k2-integration-tests --release test_resource_analysis -- --nocapture
```

### Optimization Workflow

1. Measure baseline:
   ```bash
   cargo test --release test_supply_operation -- --nocapture
   # Note CPU instructions used
   ```

2. Optimize WASM:
   ```bash
   stellar contract optimize --wasm target/wasm32v1-none/release/k2_kinetic_router.wasm
   ```

3. Rebuild and re-measure:
   ```bash
   stellar contract build
   cargo test --release test_supply_operation -- --nocapture
   # Compare CPU instructions
   ```

4. Verify improvement:
   - WASM optimization reduces costs by 5-15%
   - Architectural changes produce larger reductions

## Test Files

### Unit Tests (`tests/unit-tests/src/`)

| File | Contract |
|------|----------|
| `treasury_test.rs` | Treasury |
| `kinetic_router_test.rs` | Kinetic Router |
| `price_oracle_test.rs` | Price Oracle |
| `incentives_test.rs` | Incentives |
| `liquidation_engine_test.rs` | Liquidation Engine |
| `pool_configurator_test.rs` | Pool Configurator |
| `interest_rate_strategy_test.rs` | Interest Rate Strategy |
| `a_token_test.rs` | A-Token |
| `debt_token_test.rs` | Debt Token |

### Integration Tests (`tests/integration-tests/src/`)

| File | Purpose |
|------|---------|
| `test_lending_flow.rs` | Supply, borrow, repay, withdraw |
| `test_liquidation_flow.rs` | Liquidation scenarios |
| `test_flash_loan.rs` | Flash loan operations |
| `test_incentives.rs` | Reward distribution |
| `test_resource_analysis.rs` | Resource measurement examples |

## Resource Analysis Examples

See `tests/integration-tests/src/test_resource_analysis.rs` for examples:

- `test_resource_analysis_supply_operation` - Basic resource tracking
- `test_resource_analysis_vm_instantiation` - VM instantiation costs
- `test_resource_analysis_cross_contract_calls` - Cross-contract call analysis
- `test_resource_analysis_storage_operations` - Storage operation costs
- `test_resource_analysis_full_workflow` - Complete workflow analysis
- `test_resource_comparison_optimization` - Before and after optimization comparison

## Troubleshooting

### Tests fail with "file not found" errors

Build WASM files first:

```bash
stellar contract build
```

### Tests show unrealistic resource usage

Verify tests use WASM imports, not direct Rust registration. Check test file imports: use `crate::contract_name::WASM`.

### Integration tests fail after contract changes

Force rebuild of test dependencies:

```bash
rm -rf target/release/deps/k2_integration*
stellar contract build
cargo test --package k2-integration-tests --release
```

## Additional Resources

- [Resource Analysis Report](../RESOURCE_ANALYSIS_REPORT.md) - Contract analysis
- [Stellar Resource Limits](https://developers.stellar.org/docs/networks/resource-limits-fees)
- [Soroban Examples](https://github.com/stellar/soroban-examples)
