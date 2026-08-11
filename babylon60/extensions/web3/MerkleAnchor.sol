// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title MerkleAnchor (The Immutable Ledger Seal)
 * @dev Axiom Ω₅: Anchors the root of the Epistemic Dependency Graph (EDG) 
 * in a Web3 smart contract to guarantee global immutability and provenance tracking.
 */
contract MerkleAnchor {
    
    address public owner;
    
    // Maps each anchored Merkle Root to the block timestamp when it was sealed
    mapping(bytes32 => uint256) public anchoredRoots;
    
    // Sequence counter for anchored roots
    uint256 public totalAnchored;
    
    event RootAnchored(bytes32 indexed rootHash, uint256 indexed sequence, uint256 timestamp);
    
    modifier onlyOwner() {
        require(msg.sender == owner, "Only the authorized CORTEX authority can anchor roots.");
        _;
    }
    
    constructor() {
        owner = msg.sender;
    }
    
    /**
     * @dev Seals a new Merkle Root on-chain.
     * @param _rootHash The bytes32 Merkle root representing the swarm state.
     */
    function anchorRoot(bytes32 _rootHash) external onlyOwner {
        require(anchoredRoots[_rootHash] == 0, "This Merkle Root has already been anchored.");
        
        anchoredRoots[_rootHash] = block.timestamp;
        totalAnchored += 1;
        
        emit RootAnchored(_rootHash, totalAnchored, block.timestamp);
    }
    
    /**
     * @dev Verifies if a given Merkle Root has been anchored.
     * @param _rootHash The bytes32 Merkle root to check.
     */
    function isAnchored(bytes32 _rootHash) external view returns (bool) {
        return anchoredRoots[_rootHash] > 0;
    }

    /**
     * @dev Verifies a Merkle proof against an anchored root.
     * @param proof Array of sibling hashes in the Merkle tree.
     * @param root The anchored Merkle root.
     * @param leaf The leaf hash to verify.
     */
    function verifyProof(
        bytes32[] calldata proof,
        bytes32 root,
        bytes32 leaf
    ) external view returns (bool) {
        require(anchoredRoots[root] > 0, "Root is not anchored");
        bytes32 computedHash = leaf;

        for (uint256 i = 0; i < proof.length; i++) {
            bytes32 proofElement = proof[i];
            if (computedHash <= proofElement) {
                computedHash = keccak256(abi.encodePacked(computedHash, proofElement));
            } else {
                computedHash = keccak256(abi.encodePacked(proofElement, computedHash));
            }
        }

        return computedHash == root;
    }
}
