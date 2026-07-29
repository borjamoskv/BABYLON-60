// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title MaxRouterAnchor
 * @dev C5-REAL Sovereign Attestation Anchor
 * Preserves temporal evidence and integrity of Max Router request batches via Merkle Roots.
 * Deliberately simple: preserves evidence, does not execute routing logic.
 */
contract MaxRouterAnchor {
    
    // --- Roles ---
    address public owner;
    mapping(address => bool) public authorizedAttesters;

    // --- Events ---
    event BatchAnchored(
        bytes32 indexed merkleRoot,
        bytes32 indexed policyHash,
        uint64 batchStart,
        uint64 batchEnd,
        string metadataURI,
        address indexed attester
    );
    
    event AttesterAdded(address indexed attester);
    event AttesterRemoved(address indexed attester);
    event OwnershipTransferred(address indexed previousOwner, address indexed newOwner);

    // --- State ---
    mapping(bytes32 => bool) public anchoredRoots;

    // --- Modifiers ---
    modifier onlyOwner() {
        require(msg.sender == owner, "Unauthorized: Owner only");
        _;
    }

    modifier onlyAttester() {
        require(authorizedAttesters[msg.sender], "Unauthorized: Attester only");
        _;
    }

    constructor() {
        owner = msg.sender;
        authorizedAttesters[msg.sender] = true;
    }

    // --- Core Logic ---
    /**
     * @notice Anchors a batch of LLM attestations to the blockchain.
     * @param merkleRoot The Merkle root of the batch.
     * @param policyHash The hash of the router policy used for this batch.
     * @param batchStart UTC Timestamp of the first request in the batch.
     * @param batchEnd UTC Timestamp of the last request in the batch.
     * @param metadataURI IPFS/Arweave URI pointing to the encrypted batch manifest.
     */
    function anchorBatch(
        bytes32 merkleRoot,
        bytes32 policyHash,
        uint64 batchStart,
        uint64 batchEnd,
        string calldata metadataURI
    ) external onlyAttester {
        require(!anchoredRoots[merkleRoot], "Root already anchored");
        require(batchStart <= batchEnd, "Invalid batch timestamps");

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
        require(attester != address(0), "Invalid address");
        authorizedAttesters[attester] = true;
        emit AttesterAdded(attester);
    }

    /// @notice Elimina un attester del quorum
    /// @dev Solo callable por owner
    /// @param attester Dirección del attester a eliminar
    function removeAttester(address attester) external onlyOwner {
        authorizedAttesters[attester] = false;
        emit AttesterRemoved(attester);
    }
    
    /// @notice Transfiere la propiedad del contrato
    /// @dev Solo el owner actual puede llamar esta función
    /// @param newOwner Dirección del nuevo propietario
    function transferOwnership(address newOwner) external onlyOwner {
        require(newOwner != address(0), "Invalid address");
        address oldOwner = owner;
        owner = newOwner;
        emit OwnershipTransferred(oldOwner, newOwner);
    }
}
