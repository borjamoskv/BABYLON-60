// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

/// @title Anvil Apoptosis Anchor (Trilingual Regime)
/// @dev Yunque de consenso determinista para asentar CORTEX-TAINT y colapsos C5-REAL
contract ApoptosisAnchor {
    bytes32 public currentHead;
    uint256 public latentSteps;
    address public immutable authority;
    
    event MembraneStateCommitted(bytes32 prevHead, bytes32 newHead, uint256 latentSteps);
    event ApoptosisLogged(bytes32 taint, string reason, string wormSnapshotCid, bytes signature);
    
    modifier onlyAuthority() {
        require(msg.sender == authority, "UNAUTHORIZED_ANCHOR_CALLER");
        _;
    }
    
    constructor(bytes32 genesisHash) {
        currentHead = genesisHash;
        latentSteps = 0;
        authority = msg.sender;
    }
    
    function commitState(bytes32 inputHash, bytes32 outputHash, uint256 steps) external onlyAuthority {
        require(currentHead == inputHash, "BFT_FORK_DETECTED: Input hash does not match current head");
        
        bytes32 prev = currentHead;
        currentHead = outputHash;
        latentSteps += steps;
        
        emit MembraneStateCommitted(prev, currentHead, latentSteps);
    }
    
    function logApoptosis(bytes32 taintLog, string calldata reason, string calldata wormSnapshotCid, bytes calldata signature) external onlyAuthority {
        currentHead = taintLog;
        latentSteps = 0; // Truncation
        emit ApoptosisLogged(taintLog, reason, wormSnapshotCid, signature);
    }
}
