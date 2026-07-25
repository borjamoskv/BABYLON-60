// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

/// @title IPoolManager
/// @notice Interface for a Pool Manager
interface IPoolManager {
    /// @notice Performs a swap
    function swap() external;
}

/// @title SecureHook
/// @notice A secure hook contract implementing EIP-1153 locks and proper access controls
contract SecureHook {
    /// @notice The address of the pool manager
    address public poolManager;
    
    /// @notice Mapping of authorized pool identifiers
    mapping(bytes32 => bool) public authorizedPools;
    
    /// @notice Mapping of user balances
    mapping(address => uint256) public balances;

    /// @notice Thrown when caller is not the pool manager
    error OnlyPoolManager();
    
    /// @notice Thrown when the pool is not authorized
    error UnauthorizedPool();
    
    /// @notice Thrown on reentrant call
    error ReentrantCall();

    /// @notice Initializes the hook with a pool manager address
    /// @param _poolManager Address of the pool manager
    constructor(address _poolManager) {
        poolManager = _poolManager;
    }

    /// @notice Reverts if caller is not the pool manager
    modifier onlyPoolManager() {
        if (msg.sender != poolManager) revert OnlyPoolManager();
        _;
    }

    /// @notice Secure implementation of beforeSwap: enforces both onlyPoolManager and authorizedPools validations
    /// @param sender Address of the sender
    /// @param poolId Identifier of the pool
    /// @param amount Amount to swap
    /// @return bytes4 Selector of this function
    function beforeSwap(address sender, bytes32 poolId, int256 amount) external onlyPoolManager returns (bytes4) {
        if (!authorizedPools[poolId]) revert UnauthorizedPool();
        balances[msg.sender] += 100;
        return this.beforeSwap.selector;
    }

    /// @notice Secure implementation of afterSwap: enforces both onlyPoolManager and authorizedPools validations
    /// @param sender Address of the sender
    /// @param poolId Identifier of the pool
    /// @param amount Amount swapped
    /// @return bytes4 Selector of this function
    function afterSwap(address sender, bytes32 poolId, int256 amount) external onlyPoolManager returns (bytes4) {
        if (!authorizedPools[poolId]) revert UnauthorizedPool();
        balances[msg.sender] += 50; 
        return this.afterSwap.selector;
    }

    /// @notice Secure EIP-1153 Transient Storage reentrancy lock (INV_C5_08)
    modifier nonReentrant() {
        assembly {
            let lock := tload(0)
            if lock {
                // Store custom error ReentrantCall() selector (0x12a806c9)
                mstore(0, 0x12a806c9)
                revert(0, 4)
            }
            tstore(0, 1)
        }
        _;
        assembly {
            tstore(0, 0)
        }
    }

    /// @notice Secure EIP-1153 Transient Storage simulation
    /// @dev Demonstrates state mutation protected by the transient lock
    function executeAction() external nonReentrant {
        balances[msg.sender] += 10;
    }
}
