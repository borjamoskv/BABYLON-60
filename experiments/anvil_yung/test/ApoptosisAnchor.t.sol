// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "forge-std/Test.sol";
import "../src/ApoptosisAnchor.sol";

contract ApoptosisAnchorTest is Test {
    ApoptosisAnchor public anchor;
    bytes32 public constant GENESIS = keccak256("GENESIS");
    
    uint256 public authorityPrivateKey = 0xA11CE;
    address public authorityAddress;
    
    function setUp() public {
        authorityAddress = vm.addr(authorityPrivateKey);
        vm.prank(authorityAddress);
        anchor = new ApoptosisAnchor(GENESIS);
    }
    
    function _signApoptosis(
        uint256 pk,
        bytes32 taint,
        string memory reason,
        string memory cid,
        uint256 nonce
    ) internal view returns (bytes memory) {
        bytes32 structHash = keccak256(
            abi.encode(
                anchor.APOPTOSIS_TYPEHASH(),
                taint,
                keccak256(bytes(reason)),
                keccak256(bytes(cid)),
                nonce
            )
        );
        
        bytes32 digest = keccak256(abi.encodePacked("\x19\x01", anchor.DOMAIN_SEPARATOR(), structHash));
        (uint8 v, bytes32 r, bytes32 s) = vm.sign(pk, digest);
        return abi.encodePacked(r, s, v);
    }
    
    function testFuzz_CommitState(bytes32 outputHash, uint256 steps) public {
        vm.assume(steps < 1000000);
        
        bytes32 prevHead = anchor.currentHead();
        
        vm.prank(authorityAddress);
        anchor.commitState(prevHead, outputHash, steps);
        
        assertEq(anchor.currentHead(), outputHash);
    }
    
    function testFuzz_ForkProtection(bytes32 invalidInputHash, bytes32 outputHash, uint256 steps) public {
        vm.assume(invalidInputHash != anchor.currentHead());
        
        vm.prank(authorityAddress);
        vm.expectRevert("BFT_FORK_DETECTED: Input hash does not match current head");
        anchor.commitState(invalidInputHash, outputHash, steps);
    }
    
    function testFuzz_ValidEIP712ApoptosisSignature(bytes32 taint, string calldata reason, string calldata cid) public {
        uint256 nonce = anchor.nonce();
        bytes memory signature = _signApoptosis(authorityPrivateKey, taint, reason, cid, nonce);
        
        vm.prank(authorityAddress);
        anchor.logApoptosis(taint, reason, cid, signature);
        
        assertEq(anchor.currentHead(), taint);
        assertEq(anchor.latentSteps(), 0);
        assertEq(anchor.nonce(), nonce + 1);
    }

    function testFuzz_ForgedSignatureReverts(bytes32 taint, string calldata reason, string calldata cid, uint256 attackerPk) public {
        vm.assume(attackerPk != 0 && attackerPk != authorityPrivateKey);
        attackerPk = bound(attackerPk, 1, 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364140);
        
        uint256 nonce = anchor.nonce();
        bytes memory forgedSignature = _signApoptosis(attackerPk, taint, reason, cid, nonce);
        
        vm.prank(authorityAddress);
        vm.expectRevert("INVALID_APOPTOSIS_SIGNATURE");
        anchor.logApoptosis(taint, reason, cid, forgedSignature);
    }

    function test_UnauthorizedCallerReverts() public {
        address unauthorized = address(0xDEAD);
        bytes memory dummySig = new bytes(65);
        
        vm.prank(unauthorized);
        vm.expectRevert("UNAUTHORIZED_ANCHOR_CALLER");
        anchor.logApoptosis(keccak256("TAINT"), "ATTACK_REASON", "ipfs://cid", dummySig);
    }
}
