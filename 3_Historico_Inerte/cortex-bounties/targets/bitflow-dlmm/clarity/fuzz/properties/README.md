# Invariants

This directory contains invariant definitions for DLMM contract operations. Invariants are properties that must always hold true, regardless of the sequence of operations.

## Available Invariants

### Swap Invariants

#### `checkSwapXForYInvariants`
Verifies invariants for X-for-Y swaps:
- LP supply remains unchanged
- Bin X balance increases (by input - fees)
- Bin Y balance decreases (by output)
- User X balance decreases by input amount
- User Y balance increases by output amount
- Protocol fees increase (if applicable)
- All balances remain non-negative

#### `checkSwapYForXInvariants`
Verifies invariants for Y-for-X swaps:
- LP supply remains unchanged
- Bin Y balance increases (by input - fees)
- Bin X balance decreases (by output)
- User Y balance decreases by input amount
- User X balance increases by output amount
- Protocol fees increase (if applicable)
- All balances remain non-negative

### Liquidity Invariants

#### `checkAddLiquidityInvariants`
Verifies invariants for adding liquidity:
- LP supply increases
- Bin X/Y balances increase (if amounts > 0)
- User LP balance increases
- User X/Y balances decrease (if amounts > 0)
- LP tokens minted > 0
- LP tokens minted >= minDlp
- All balances remain non-negative

#### `checkWithdrawLiquidityInvariants`
Verifies invariants for withdrawing liquidity:
- LP supply decreases
- Bin X/Y balances decrease (if present)
- User LP balance decreases
- User X/Y balances increase (if withdrawn)
- LP tokens burned > 0
- X/Y amounts received >= minXAmount/minYAmount
- All balances remain non-negative

#### `checkMoveLiquidityInvariants`
Verifies invariants for moving liquidity between bins:
- Source bin LP supply decreases
- Destination bin LP supply increases
- Source bin X/Y balances decrease proportionally
- Destination bin X/Y balances increase proportionally
- User LP balance in source bin decreases
- User LP balance in destination bin increases
- LP tokens moved > 0
- LP tokens minted >= minDlp
- All balances remain non-negative

### Pool Creation Invariants

#### `checkCreatePoolInvariants`
Verifies invariants for pool creation:
- Pool is created (poolCreated = true)
- Pool ID is assigned (non-zero)
- Initial liquidity is added to active bin
- LP tokens are minted
- Pool status is set correctly
- Active bin ID is in valid range

## Usage

```typescript
import {
  checkSwapXForYInvariants,
  captureBinState,
  captureUserState,
  captureProtocolFeesState
} from './invariants';

// Before operation
const beforeBin = captureBinState(binId);
const beforeUser = captureUserState(user, binId);
const beforeFees = captureProtocolFeesState(poolId);

// Execute operation
const result = await swapXForY(...);

// After operation
const afterBin = captureBinState(binId);
const afterUser = captureUserState(user, binId);
const afterFees = captureProtocolFeesState(poolId);

// Check invariants
const check = checkSwapXForYInvariants(
  beforeBin, afterBin,
  beforeUser, afterUser,
  beforeFees, afterFees,
  xAmount, result
);

if (!check.passed) {
  console.error('Invariant violation:', check.errors);
}
```

## State Capture Functions

- `captureBinState(binId)`: Captures bin balances and LP supply
- `captureUserState(user, binId?)`: Captures user token and LP balances
- `captureProtocolFeesState(poolId)`: Captures protocol fee state

## Why These Invariants Matter

These invariants ensure:
1. **Conservation**: No tokens are created or destroyed unexpectedly
2. **Correctness**: Operations behave as specified
3. **Security**: No exploits through balance manipulation
4. **Consistency**: Pool state remains consistent across operations

Violations of these invariants indicate potential bugs or security issues in the contract implementation.

