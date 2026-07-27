# Staking Contract

A fixed-APR ERC-20 staking protocol with linear unlock, migration support, and on-chain reward reservation guarantees.

---

## Table of Contents

- [Overview](#overview)
- [Usage](#usage)
- [Key Properties](#key-properties)
- [Contracts](#contracts)
- [Staking Mechanics](#staking-mechanics)
    - [Depositing](#depositing)
    - [Reward Calculation](#reward-calculation)
    - [Linear Unlock & Withdrawal](#linear-unlock--withdrawal)
- [Migration](#migration)
- [Balance Protection & Recovery](#balance-protection--recovery)

---

## Overview

Users deposit an ERC-20 token into the staking contract for a fixed duration and earn a pre-determined APR-based reward. Rewards are **reserved at deposit time** — the contract rejects new deposits if it cannot cover the promised payout from its current balance. When the staking period ends, both principal and reward unlock **linearly** over a separate unlock duration, allowing partial withdrawals at any point.

The contract also supports a **migration mechanism** that allows users to opt-in to having their open positions moved to a next-version staking contract, with all position data and tokens transferred atomically.

---

## Usage

We use default [Foundry](https://www.getfoundry.sh/forge) setup.

```shell
# Install dependencies
forge install

# Build
forge build

# Test
forge test

# Format code
forge fmt
```

---

## Key Properties

- **Fixed APR**: Reward is computed once at deposit and never changes for that stake.
- **Reward reservation**: Deposits are rejected if contract token balance is not enough to repay principal and reward for the stake. This guarantees the contract can always pay out.
- **Linear unlock**: After the staking period ends, principal and reward become claimable linearly over a configurable unlock duration. Users may withdraw multiple times.
- **User-controlled migration**: Users grant migration permission per-migrator explicitly. No migration can happen without the user's active approval.
- **Pausable staking**: New deposits can be paused for emergencies. Withdrawals are always available regardless of pause state, so users can always exit.

---

## Contracts

| Contract | Description                                                                                                                                                                                                                                                                          |
|---|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `Staking.sol` | Core staking contract. Manages periods, stakes, deposits and withdrawals.                                                                                                                                                                                                            |
| `MigratorV1.sol` | Example implementation of migration orchestrator. Pulls positions from a V1 staking contract and pushes them to a V2 receiver. This is simple implementation, detailed implementation (including permissioned/permissionless execution) will depend on needs of future V2 contracts. |
| `IMigratorV1.sol` | Interface that a staking contract must implement to act as a migration source.                                                                                                                                                                                                       |
| `IMigratorReceiverV2.sol` | Interface that a V2 contract must implement to act as a migration destination.                                                                                                                                                                                                       |
| `IStakingV1.sol` | Shared data types, events, and errors used across all staking V1 contracts.                                                                                                                                                                                                          |

---

## Staking Mechanics

### Depositing

```solidity
// Option 1: approve first, then stake
token.approve(address(staking), amount);
staking.stake(periodIndex, amount, IStakingV1.StakeParams({
    maxStakingDurationSeconds: maxDuration,
    maxUnlockDurationSeconds: maxUnlockDuration,
    minAprBps: minApr,
    referrer: referrerAddress   // address(0) if none
}));

// Option 2: use EIP-2612 permit in a single transaction
staking.stakeWithPermit(periodIndex, amount, IStakingV1.StakeParams({
    maxStakingDurationSeconds: maxDuration,
    maxUnlockDurationSeconds: maxUnlockDuration,
    minAprBps: minApr,
    referrer: referrerAddress   // address(0) if none
}), deadline, v, r, s);
```

Both functions are protected against reentrancy and respect the `whenNotPaused` modifier. They return the `stakeIndex` assigned to the new position within the user's stakes array.
The contract never accepts a deposit it cannot guarantee to pay out.

User can have up to 100 stakes (`MAX_STAKES_PER_USER`). Fully withdrawn stakes continue to occupy slots in the array and count toward this limit.

Manager supposed to set reasonable staking parameters: cap limit, APR, staking duration and unlock duration.

### Reward Calculation

Rewards follow a simple fixed-APR formula computed once at deposit time:

```
reward = (amount * aprBps * stakingDurationSeconds) / (10_000 * 365 days)
```

Where `aprBps` is the annual percentage rate in basis points (e.g. `1000` = 10% APR, `550` = 5.5% APR).

The computed `reward` is stored immutably in the `UserStake` struct. It is never recalculated or affected by any subsequent changes to the staking period's parameters.

**Example**: Staking 1000 tokens at 10% APR for 30 days:
```
reward = (1000 * 1000 * 30 days) / (10_000 * 365 days) = 8.219 tokens
```

### Linear Unlock & Withdrawal

Tokens do not become instantly available when the staking period ends. Instead, they unlock linearly over the period's `unlockDurationSeconds` starting from `unlockTime`.
This rule applies to both principal and reward. Users may call `withdraw(stakeIndex)` at any time after `unlockTime` to claim whatever has accrued since their last withdrawal.

```solidity
staking.withdraw(stakeIndex);
```

---

## Migration

Migration related contracts listed in `/src/test` folder are example of such mechanism implementation and are subjects of change in future (for example can be set permissioned, or activation during specific period of time etc.). 

Migration allows a user's open positions in this contract (V1) to be atomically transferred to a new staking contract (V2), along with the underlying tokens. The `MigratorV1` contract verifies balance consistency: if `migratePositionsTo` pulls a different token amount than was transferred from V1, the entire transaction reverts.

### User Flow

1. **Grant permission** to a specific migrator contract:
   ```solidity
   staking.setMigrationPermit(migratorAddress, true);
   ```
   The migrator must hold the `MIGRATOR_ROLE` in the staking contract. The permission can be revoked at any time by calling `setMigrationPermit(migratorAddress, false)`.

2. **Trigger migration**:
   ```solidity
   migrator.migrate(userAddress);
   ```

3. **Result**: All open (not fully withdrawn) stakes are removed from V1 and recreated in V2. The corresponding tokens are transferred from `V1 -> MigratorV1 -> V2` atomically. Fully withdrawn stakes remain in V1 as historical records.

---

## Balance Protection & Recovery

### Protection Mechanism

The contract maintains two accumulators that track all outstanding obligations:

- `activeTotalStaked` — sum of all principal not yet withdrawn
- `activeTotalRewards` — sum of all rewards not yet withdrawn

Every new deposit checks that the contract's current balance (before receiving the new deposit) is enough to cover all existing obligations plus the newly promised reward:
```solidity
require(activeTotalStaked + activeTotalRewards + reward <= contractBalance);
```

Because the user's `amount` is transferred in during the same transaction, the contract balance grows by `amount` while the new total obligation grows by `amount + reward`. The check only needs to verify the protocol can cover `reward` — the principal is self-funded by the depositor.

This ensures the contract always holds sufficient tokens to pay every current and future obligation. The staking token must be a standard ERC-20: fee-on-transfer and rebasing tokens would break this invariant.

### Recovering Excess Tokens

The `MANAGER_ROLE` can recover tokens accidentally sent to the contract:

```solidity
staking.recoverERC20(tokenAddress, amount);
```

For the staking token, only the **excess** above `activeTotalStaked + activeTotalRewards` can be recovered. This prevents any recovery that would leave the contract unable to meet its obligations. For other ERC-20 tokens, the full balance can be recovered.

---

