// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

/// @title Anvil Apoptosis Anchor (Trilingual Regime)
/// @dev Yunque de consenso determinista para asentar CORTEX-TAINT y colapsos C5-REAL
contract ApoptosisAnchor {
    string public currentHead;
    uint256 public latentSteps;
    address public immutable authority;
    
    event MembraneStateCommitted(string prevHead, string newHead, uint256 latentSteps);
    event ApoptosisLogged(string taint, string reason);
    
    modifier onlyAuthority() {
        require(msg.sender == authority, "UNAUTHORIZED_ANCHOR_CALLER");
        _;
    }
    
    constructor(string memory genesisHash) {
        currentHead = genesisHash;
        latentSteps = 0;
        authority = msg.sender;
    }
    
    function commitState(string calldata inputHash, string calldata outputHash, uint256 steps) external onlyAuthority {
        require(keccak256(abi.encodePacked(currentHead)) == keccak256(abi.encodePacked(inputHash)), "BFT_FORK_DETECTED: Input hash does not match current head");
        
        string memory prev = currentHead;
        currentHead = outputHash;
        latentSteps += steps;
        
        emit MembraneStateCommitted(prev, currentHead, latentSteps);
    }
    
    function logApoptosis(string calldata taintLog, string calldata reason) external onlyAuthority {
        currentHead = taintLog;
        latentSteps = 0; // Truncation
        emit ApoptosisLogged(taintLog, reason);
    }
}
