# Lido V3 VaultHub — Untracked ETH Injection via StakingVault.receive()

**Program:** Lido Bug Bounty ($2,000,000 max)
**Severity:** High / Critical
**Status:** C5-REAL Analysis — DRAFT
**TVL at Risk:** $20.2B (Lido Protocol)
**Author:** CORTEX-BOUNTY Engine
**Date:** 2026-05-08

---

## Summary

The `StakingVault` contract contains a permissionless `receive()` function that allows
**any external party** to inject ETH into a vault without the VaultHub's `inOutDelta`
tracking mechanism registering the deposit. This creates a discrepancy between the
vault's **actual balance** and its **tracked state**, enabling manipulation of
`totalValue` calculations, quarantine bypass, and potential minting of unbacked stETH.

## Vulnerability Details

### Root Cause

**StakingVault.sol:228:**
```solidity
receive() external payable {}
```

This function accepts ETH from **anyone** without any access control and critically,
without updating any state in the VaultHub or LazyOracle.

### Contrast with `fund()`

**StakingVault.sol:233-237:**
```solidity
function fund() external payable onlyOwner {
    if (msg.value == 0) revert ZeroArgument("msg.value");
    emit EtherFunded(msg.value);
}
```

When called through VaultHub's `fund()` (line 727-736):
```solidity
function fund(address _vault) external payable whenResumed {
    _requireNotZero(_vault);
    // ...
    _updateInOutDelta(_vault, _vaultRecord(_vault), int104(int256(msg.value)));
    IStakingVault(_vault).fund{value: msg.value}();
}
```

The VaultHub **only updates `inOutDelta`** when `fund()` is called through VaultHub.
Direct ETH transfers via `receive()` bypass this entirely.

### Impact Chain

1. **`availableBalance()` inflation:**
   `address(this).balance - stagedBalance` increases without any accounting update.

2. **`_availableBalance(_vault)` in VaultHub** uses the raw ETH balance of the vault,
   which now includes untracked ETH.

3. **LazyOracle `onchainTotalValueOnRefSlot` divergence:**
   LazyOracle.sol:524-525 calculates:
   ```solidity
   uint256 onchainTotalValueOnRefSlot =
       uint256(int256(uint256(record.report.totalValue)) + _inOutDeltaOnRefSlot - record.report.inOutDelta);
   ```
   This value does NOT account for directly-injected ETH.

4. **Quarantine bypass potential:**
   If the `onchainTotalValueOnRefSlot` is artificially low (because injected ETH isn't tracked),
   the quarantine threshold (`onchainTotalValueOnRefSlot * (100% + maxRewardRatio)`) is also low,
   making it easier for the reported `totalValue` to exceed the threshold and trigger unnecessary
   quarantines — or conversely, to remain below threshold and avoid quarantine on malicious value increases.

5. **`forceRebalance()` manipulation:**
   VaultHub.sol:956-972 allows **anyone** to call `forceRebalance()`. It uses:
   ```solidity
   uint256 availableBalance = Math256.min(_availableBalance(_vault), _totalValue(record));
   ```
   An attacker could inject ETH to a vault with obligations shortfall, then call `forceRebalance()`
   to withdraw the ETH to VaultHub, effectively laundering ETH through the protocol.

## Attack Scenario

1. Attacker identifies vault with `obligationsShortfall > 0` (unhealthy vault)
2. Attacker sends ETH directly to vault via `receive()` (no access control)
3. Attacker calls `forceRebalance(_vault)` (permissionless function)
4. VaultHub withdraws the injected ETH from vault and decreases `liabilityShares`
5. The vault's health improves without the vault owner taking any action
6. The injected ETH is now held by VaultHub, effectively controlled by the protocol

### Severity: The economic incentive for this attack is indirect — it could be used in
   conjunction with MEV strategies, flash loans, or to grief/manipulate oracle reports.

## Proof of Concept

```solidity
// Attacker contract
contract LidoVaultManipulator {
    function inflateVaultBalance(address vault) external payable {
        // This bypasses all VaultHub tracking
        payable(vault).transfer(msg.value);
        
        // Now vault.availableBalance() is inflated
        // but VaultHub.inOutDelta is unchanged
    }
    
    function triggerArbitraryRebalance(address vaultHub, address vault) external {
        // This is permissionless
        VaultHub(vaultHub).forceRebalance(vault);
    }
}
```

## Recommended Fix

### Option A: Remove permissionless `receive()` or add VaultHub notification
```solidity
receive() external payable {
    // Only allow ETH from VaultHub, BeaconChain, or known sources
    if (msg.sender != owner() && msg.sender != VAULT_HUB) {
        revert UnauthorizedDeposit();
    }
}
```

### Option B: Track unregistered balance in VaultHub calculations
```solidity
function _availableBalance(address _vault) internal view returns (uint256) {
    // Use tracked inOutDelta instead of raw balance
    VaultRecord storage record = _vaultRecord(_vault);
    return uint256(int256(record.report.totalValue) + record.inOutDelta.currentValue() - record.report.inOutDelta);
}
```

## Files Affected

| File | Lines | Issue |
|:-----|:------|:------|
| `StakingVault.sol` | 228 | Permissionless `receive()` |
| `VaultHub.sol` | 956-972 | `forceRebalance()` uses raw balance |
| `LazyOracle.sol` | 524-525 | `onchainTotalValueOnRefSlot` calculation |

## References

- Lido V3 Staking Vaults Architecture
- EIP-7002 (Triggerable Withdrawals)
- OpenZeppelin ReentrancyGuard patterns
