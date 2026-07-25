// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

/// @title MaxRouterAnchor
/// @notice C5-REAL Sovereign Attestation Anchor. Preserves temporal evidence and integrity of Max Router request batches via Merkle Roots.
/// @dev Uses EIP-1153 transient storage for reentrancy protection (INV_C5_08)
contract MaxRouterAnchor {
    /// @notice Address of the contract owner
    address public owner;
    
    /// @notice Mapping of authorized attesters
    mapping(address => bool) private _authorized;
    
    /// @notice Mapping of anchored Merkle roots
    mapping(bytes32 => bool) public anchoredRoots;

    // --- Errors ---
    /// @notice Thrown when caller is not authorized
    error Unauthorized();
    
    /// @notice Thrown when address is zero
    error InvalidAddress();
    
    /// @notice Thrown when a batch has invalid timestamps
    error InvalidBatchTimestamps();
    
    /// @notice Thrown when root is already anchored
    error RootAlreadyAnchored();
    
    /// @notice Thrown on reentrant call
    error ReentrancyGuard();

    // --- Events ---
    /// @notice Emitted when a batch is anchored
    /// @param merkleRoot The Merkle root of the batch
    /// @param policyHash The hash of the router policy
    /// @param batchStart UTC Timestamp of the first request
    /// @param batchEnd UTC Timestamp of the last request
    /// @param metadataURI URI pointing to the encrypted batch manifest
    /// @param attester Address of the attester
    event BatchAnchored(
        bytes32 indexed merkleRoot,
        bytes32 indexed policyHash,
        uint64 batchStart,
        uint64 batchEnd,
        bytes32 metadataURI,
        address indexed attester
    );

    /// @notice Emitted when an attester is added
    /// @param attester Address of the new attester
    event AttesterAdded(address indexed attester);
    
    /// @notice Emitted when an attester is removed
    /// @param attester Address of the removed attester
    event AttesterRemoved(address indexed attester);
    
    /// @notice Emitted when ownership is transferred
    /// @param previousOwner Address of the old owner
    /// @param newOwner Address of the new owner
    event OwnershipTransferred(address indexed previousOwner, address indexed newOwner);

    // --- Modifiers ---
    /// @notice Reverts if caller is not the owner
    modifier onlyOwner() {
        if (msg.sender != owner) revert Unauthorized();
        _;
    }

    /// @notice Reverts if caller is not an authorized attester
    modifier onlyAuthorized() {
        if (!_authorized[msg.sender]) revert Unauthorized();
        _;
    }

    /// @notice Reentrancy protection via EIP-1153 transient storage (INV_C5_08)
    modifier nonReentrant() {
        uint256 locked;
        assembly {
            locked := tload(0)
        }
        if (locked != 0) revert ReentrancyGuard();
        assembly {
            tstore(0, 1)
        }
        _;
        assembly {
            tstore(0, 0)
        }
    }

    /// @notice Initializes the contract setting the deployer as owner and attester
    constructor() {
        owner = msg.sender;
        _authorized[msg.sender] = true;
    }

    // --- Core Logic ---
    /// @notice Anchors a batch of LLM attestations to the blockchain
    /// @dev Uses EIP-1153 transient storage for reentrancy protection (INV_C5_08)
    /// @param merkleRoot The Merkle root of the batch.
    /// @param policyHash The hash of the router policy used for this batch.
    /// @param batchStart UTC Timestamp of the first request in the batch.
    /// @param batchEnd UTC Timestamp of the last request in the batch.
    /// @param metadataURI URI pointing to the encrypted batch manifest.
    function anchorBatch(
        bytes32 merkleRoot,
        bytes32 policyHash,
        uint64 batchStart,
        uint64 batchEnd,
        bytes32 metadataURI
    ) external onlyAuthorized nonReentrant {
        if (anchoredRoots[merkleRoot]) revert RootAlreadyAnchored();
        if (batchStart > batchEnd) revert InvalidBatchTimestamps();

        anchoredRoots[merkleRoot] = true;

        emit BatchAnchored(
            merkleRoot,
            policyHash,
            batchStart,
            batchEnd,
            metadataURI,
            msg.sender
        );
    }

    // --- Administration ---
    /// @notice Añade un nuevo attester al quorum
    /// @dev Solo callable por owner. El attester debe ser una address válida
    /// @param attester Dirección del nuevo attester
    function addAttester(address attester) external onlyOwner {
        if (attester == address(0)) revert InvalidAddress();
        _authorized[attester] = true;
        emit AttesterAdded(attester);
    }

    /// @notice Elimina un attester del quorum
    /// @dev Solo callable por owner
    /// @param attester Dirección del attester a eliminar
    function removeAttester(address attester) external onlyOwner {
        _authorized[attester] = false;
        emit AttesterRemoved(attester);
    }
    
    /// @notice Transfiere la propiedad del contrato
    /// @dev Solo el owner actual puede llamar esta función
    /// @param newOwner Dirección del nuevo propietario
    function transferOwnership(address newOwner) external onlyOwner {
        if (newOwner == address(0)) revert InvalidAddress();
        address oldOwner = owner;
        owner = newOwner;
        emit OwnershipTransferred(oldOwner, newOwner);
    }
    
    /// @notice Checks if an address is an authorized attester
    /// @param attester Address to check
    /// @return True if authorized, false otherwise
    function isAuthorized(address attester) external view returns (bool) {
        return _authorized[attester];
    }
}
