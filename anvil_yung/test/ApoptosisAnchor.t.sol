// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "forge-std/Test.sol";
import "../src/ApoptosisAnchor.sol";

contract ApoptosisAnchorTest is Test {
    ApoptosisAnchor public anchor;
    bytes32 public constant GENESIS = keccak256("GENESIS");
    
    function setUp() public {
        anchor = new ApoptosisAnchor(GENESIS);
    }
    
    function testFuzz_CommitState(bytes32 outputHash, uint256 steps) public {
        // Enforce basic invariants to prevent overly massive steps
        vm.assume(steps < 1000000);
        
        bytes32 prevHead = anchor.currentHead();
        
        anchor.commitState(prevHead, outputHash, steps);
        
        assertEq(anchor.currentHead(), outputHash);
    }
    
    function testFuzz_ForkProtection(bytes32 invalidInputHash, bytes32 outputHash, uint256 steps) public {
        vm.assume(invalidInputHash != anchor.currentHead());
        
        vm.expectRevert("BFT_FORK_DETECTED: Input hash does not match current head");
        anchor.commitState(invalidInputHash, outputHash, steps);
    }
    
    function testFuzz_ApoptosisTruncation(bytes32 taint, string calldata reason, string calldata cid, bytes calldata signature) public {
        anchor.logApoptosis(taint, reason, cid, signature);
        assertEq(anchor.currentHead(), taint);
        assertEq(anchor.latentSteps(), 0);
    }

    function test_UnauthorizedCallerReverts() public {
        address unauthorized = address(0xDEAD);
        vm.prank(unauthorized);
        vm.expectRevert("UNAUTHORIZED_ANCHOR_CALLER");
        anchor.logApoptosis(keccak256("TAINT"), "ATTACK_REASON", "ipfs://cid", bytes("sig"));
    }
}
