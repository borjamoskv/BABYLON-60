// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "forge-std/Test.sol";
import "../src/ApoptosisAnchor.sol";

contract ApoptosisAnchorTest is Test {
    ApoptosisAnchor public anchor;

    function setUp() public {
        anchor = new ApoptosisAnchor("GENESIS");
    }

    function testFuzz_CommitState(string calldata outputHash, uint256 steps) public {
        // Enforce basic invariants to prevent revert on empty string or overly massive steps
        vm.assume(bytes(outputHash).length > 0);
        vm.assume(steps < 1000000);

        string memory prevHead = anchor.currentHead();

        anchor.commitState(prevHead, outputHash, steps);

        assertEq(anchor.currentHead(), outputHash);
    }

    function testFuzz_ForkProtection(string calldata invalidInputHash, string calldata outputHash, uint256 steps) public {
        vm.assume(keccak256(abi.encodePacked(invalidInputHash)) != keccak256(abi.encodePacked(anchor.currentHead())));

        vm.expectRevert("BFT_FORK_DETECTED: Input hash does not match current head");
        anchor.commitState(invalidInputHash, outputHash, steps);
    }

    function testFuzz_ApoptosisTruncation(string calldata taint, string calldata reason) public {
        anchor.logApoptosis(taint, reason);
        assertEq(anchor.currentHead(), taint);
        assertEq(anchor.latentSteps(), 0);
    }
}
