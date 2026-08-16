// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

/// @title Anvil Apoptosis Anchor (Trilingual Regime — EIP-712 Hardened)
/// @dev Yunque de consenso determinista para asentar CORTEX-TAINT y colapsos C5-REAL con verificación EIP-712
contract ApoptosisAnchor {
    bytes32 public currentHead;
    uint256 public latentSteps;
    uint256 public nonce;
    address public immutable authority;
    
    bytes32 public immutable DOMAIN_SEPARATOR;
    
    bytes32 public constant EIP712_DOMAIN_TYPEHASH = 
        keccak256("EIP712Domain(string name,string version,uint256 chainId,address verifyingContract)");
        
    bytes32 public constant APOPTOSIS_TYPEHASH = 
        keccak256("Apoptosis(bytes32 taintLog,string reason,string wormSnapshotCid,uint256 nonce)");
    
    event MembraneStateCommitted(bytes32 prevHead, bytes32 newHead, uint256 latentSteps);
    event ApoptosisLogged(bytes32 taint, string reason, string wormSnapshotCid, bytes signature, uint256 nonce);
    
    modifier onlyAuthority() {
        require(msg.sender == authority, "UNAUTHORIZED_ANCHOR_CALLER");
        _;
    }
    
    constructor(bytes32 genesisHash) {
        currentHead = genesisHash;
        latentSteps = 0;
        nonce = 0;
        authority = msg.sender;
        
        DOMAIN_SEPARATOR = keccak256(
            abi.encode(
                EIP712_DOMAIN_TYPEHASH,
                keccak256(bytes("ApoptosisAnchor")),
                keccak256(bytes("1")),
                block.chainid,
                address(this)
            )
        );
    }
    
    function commitState(bytes32 inputHash, bytes32 outputHash, uint256 steps) external onlyAuthority {
        require(currentHead == inputHash, "BFT_FORK_DETECTED: Input hash does not match current head");
        
        bytes32 prev = currentHead;
        currentHead = outputHash;
        latentSteps += steps;
        
        emit MembraneStateCommitted(prev, currentHead, latentSteps);
    }
    
    function logApoptosis(
        bytes32 taintLog, 
        string calldata reason, 
        string calldata wormSnapshotCid, 
        bytes calldata signature
    ) external onlyAuthority {
        bytes32 structHash = keccak256(
            abi.encode(
                APOPTOSIS_TYPEHASH,
                taintLog,
                keccak256(bytes(reason)),
                keccak256(bytes(wormSnapshotCid)),
                nonce
            )
        );
        
        bytes32 digest = keccak256(abi.encodePacked("\x19\x01", DOMAIN_SEPARATOR, structHash));
        address signer = recoverSigner(digest, signature);
        require(signer == authority, "INVALID_APOPTOSIS_SIGNATURE");
        
        uint256 currentNonce = nonce;
        nonce += 1;
        currentHead = taintLog;
        latentSteps = 0; // Truncation
        
        emit ApoptosisLogged(taintLog, reason, wormSnapshotCid, signature, currentNonce);
    }
    
    function recoverSigner(bytes32 digest, bytes memory signature) public pure returns (address) {
        if (signature.length != 65) {
            return address(0);
        }
        bytes32 r;
        bytes32 s;
        uint8 v;
        assembly {
            r := mload(add(signature, 0x20))
            s := mload(add(signature, 0x40))
            v := byte(0, mload(add(signature, 0x60)))
        }
        if (v < 27) {
            v += 27;
        }
        if (v != 27 && v != 28) {
            return address(0);
        }
        return ecrecover(digest, v, r, s);
    }
}
