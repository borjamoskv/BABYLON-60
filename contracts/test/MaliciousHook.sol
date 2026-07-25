// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

/// @title IPoolManager
/// @notice Interface for a Pool Manager
interface IPoolManager {
    /// @notice Performs a swap
    function swap() external;
}

/// @title MaliciousHook
/// @notice A mock vulnerable hook contract for testing violations
contract MaliciousHook {
    /// @notice The address of the pool manager
    address public poolManager;
    
    /// @notice Mapping of authorized pool identifiers
    mapping(bytes32 => bool) public authorizedPools;
    
    /// @notice Mapping of user balances
    mapping(address => uint256) public balances;

    /// @notice Initializes the hook with a pool manager address
    /// @param _poolManager Address of the pool manager
    constructor(address _poolManager) {
        poolManager = _poolManager;
    }

    /// @notice Vulnerable function executed before a swap (INV-01 violation: msg.sender check missing)
    /// @param sender Address of the sender
    /// @param poolId Identifier of the pool
    /// @param amount Amount to swap
    /// @return bytes4 Selector of this function
    function beforeSwap(address sender, bytes32 poolId, int256 amount) external returns (bytes4) {
        // Balances are updated via SSTORE without PoolManager access control validation
        balances[msg.sender] += 100;
        return this.beforeSwap.selector;
    }

    /// @notice Vulnerable function executed after a swap (INV-02 violation: authorizedPools mapping validation missing)
    /// @param sender Address of the sender
    /// @param poolId Identifier of the pool
    /// @param amount Amount swapped
    /// @return bytes4 Selector of this function
    function afterSwap(address sender, bytes32 poolId, int256 amount) external returns (bytes4) {
        // Access control onlyPoolManager is present, but lacks PoolKey validation
        require(msg.sender == poolManager, "OnlyPoolManager");
        // State mutation occurs without verifying pool validity
        balances[msg.sender] += 50; 
        return this.afterSwap.selector;
    }

    /// @notice Vulnerable state execution logic (INV-03 violation: uses transient storage pattern incorrectly or uses local state variables)
    function executeAction() external {
        // Vulnerable state management instead of transient storage lock
        balances[msg.sender] = 0;
    }
}
