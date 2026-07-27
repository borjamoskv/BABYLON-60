# Fuzzing Guide

This document explains the fuzzing methodology used in this repository.

## What is Fuzzing?

Fuzzing (or fuzz testing) is a testing technique that involves providing random, unexpected, or invalid inputs to a program to find bugs, security vulnerabilities, or unexpected behavior.

## Our Fuzzing Approach

### Property-Based Testing

We use property-based testing where we:
1. Generate random sequences of operations
2. Check invariants after each operation
3. Verify that properties always hold

### Random Operation Generation

Fuzz tests generate random sequences of:
- Swaps (x-for-y, y-for-x)
- Liquidity operations (add, remove, move)
- Pool operations (create, configure)

### Invariant Checking

After each operation, we verify:
- Balance conservation
- LP supply consistency
- Fee accumulation
- Non-negative balances
- Correct state transitions

## Fuzz Targets

### Comprehensive Fuzz Test

The main fuzz test (`comprehensive.test.ts`) performs:
- Random sequences of all operation types
- State tracking across operations
- Invariant verification
- Violation logging

### Quote Engine Validation

Validates swap calculations against the production quote engine:
- Compares contract output to expected output
- Detects exploits (contract returning more than allowed)
- Tests both single-bin and multi-bin swaps

### Bin Traversal

Tests edge cases in bin traversal:
- Moving between bins
- Boundary conditions
- Empty bins
- Full bins

### Zero-Fee Exploit

Specifically tests for rounding exploits:
- Repeated small swaps
- Zero-fee scenarios
- Rounding differences

## Reproducibility

All fuzz tests use seeded random number generators:
- Same seed = same sequence of operations
- Allows reproducing bugs
- Enables regression testing

## Coverage

Fuzz tests aim to achieve:
- **Operation coverage**: All operation types tested
- **Bin coverage**: Operations across different bins
- **Edge case coverage**: Boundary conditions and unusual inputs
- **State space coverage**: Different pool states and configurations

## Best Practices

1. **Use seeds**: Always use seeds for reproducibility
2. **Check invariants**: Verify invariants after each operation
3. **Log violations**: Capture all violations with context
4. **Test edge cases**: Include boundary values and unusual inputs
5. **Monitor coverage**: Track which code paths are exercised

## Interpreting Results

### No Violations

If no violations are found:
- The tested properties hold for the generated inputs
- This doesn't guarantee correctness for all inputs
- Consider increasing fuzz size or adding more test cases

### Violations Found

If violations are found:
1. **Reproduce**: Use the seed to reproduce the issue
2. **Analyze**: Understand why the invariant was violated
3. **Fix**: Address the root cause
4. **Verify**: Re-run fuzz test to ensure fix works
5. **Document**: Add to crashes/ directory

## Extending Fuzzing

To add new fuzz targets:
1. Create test file in `fuzz/`
2. Generate random operations
3. Check relevant invariants
4. Log violations
5. Add to package.json scripts

See [CONTRIBUTING.md](../CONTRIBUTING.md) for detailed instructions.

