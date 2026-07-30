# Invariant Documentation

This document provides detailed explanations of the invariants checked in the DLMM fuzzing suite.

## What Are Invariants?

Invariants are properties that must always hold true, regardless of the sequence of operations. They represent fundamental correctness guarantees of the system.

## Swap Invariants

### LP Supply Conservation

**Invariant**: LP supply must remain unchanged during swaps.

**Why it matters**: Swaps should not mint or burn LP tokens. LP tokens represent ownership of liquidity, and swaps only exchange tokens, not ownership.

**Violation impact**: Critical - would allow manipulation of pool ownership.

### Balance Changes

**Invariant**: Bin balances must change correctly:
- Input token balance increases by (input - fees)
- Output token balance decreases by output

**Why it matters**: Ensures tokens are correctly accounted for and fees are properly deducted.

**Violation impact**: Critical - could lead to incorrect accounting or fee calculation errors.

### User Balance Changes

**Invariant**: User balances must change by exactly the amounts swapped:
- Input token decreases by input amount
- Output token increases by output amount

**Why it matters**: Users should receive exactly what they're owed, no more, no less.

**Violation impact**: Critical - could lead to loss of user funds or unfair advantages.

### Protocol Fees

**Invariant**: Protocol fees must increase (or stay the same) during swaps.

**Why it matters**: Protocol fees should accumulate correctly and never decrease.

**Violation impact**: High - could lead to incorrect fee accounting.

### Non-Negative Balances

**Invariant**: All balances must remain non-negative.

**Why it matters**: Negative balances are impossible and indicate a critical bug.

**Violation impact**: Critical - indicates a fundamental accounting error.

## Liquidity Invariants

### LP Supply Changes

**Invariant**: LP supply must increase when adding liquidity and decrease when removing.

**Why it matters**: LP tokens represent ownership, so supply must track liquidity changes.

**Violation impact**: Critical - would break the ownership model.

### Proportional Changes

**Invariant**: When moving liquidity, changes must be proportional to the amount moved.

**Why it matters**: Ensures liquidity moves correctly between bins without creating or destroying value.

**Violation impact**: High - could lead to incorrect liquidity distribution.

### Minimum Amounts

**Invariant**: LP tokens minted/burned and tokens received must meet minimum requirements.

**Why it matters**: Protects users from receiving less than expected due to rounding.

**Violation impact**: Medium - could lead to small losses for users.

## Pool Creation Invariants

### Pool Initialization

**Invariant**: Pool must be properly initialized with valid parameters.

**Why it matters**: Ensures pools start in a valid state.

**Violation impact**: Critical - invalid pools could cause all operations to fail.

## Testing Invariants

Invariants are checked in fuzz tests by:
1. Capturing state before an operation
2. Executing the operation
3. Capturing state after the operation
4. Verifying all invariants hold

See [fuzz/properties/README.md](../fuzz/properties/README.md) for usage examples.

