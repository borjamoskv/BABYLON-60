// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

interface IPoolManager {
    function swap() external;
}

contract SecureHook {
    address public poolManager;
    mapping(bytes32 => bool) public authorizedPools;
    mapping(address => uint256) public balances;

    error OnlyPoolManager();
    error UnauthorizedPool();

    constructor(address _poolManager) {
        poolManager = _poolManager;
    }

    modifier onlyPoolManager() {
        if (msg.sender != poolManager) revert OnlyPoolManager();
        _;
    }

    // Secure implementation of beforeSwap: enforces both onlyPoolManager and authorizedPools validations
    function beforeSwap(address, bytes32 poolId, int256) external onlyPoolManager returns (bytes4) {
        if (!authorizedPools[poolId]) revert UnauthorizedPool();
        balances[msg.sender] += 100;
        return this.beforeSwap.selector;
    }

    // Secure implementation of afterSwap: enforces both onlyPoolManager and authorizedPools validations
    function afterSwap(address, bytes32 poolId, int256) external onlyPoolManager returns (bytes4) {
        if (!authorizedPools[poolId]) revert UnauthorizedPool();
        balances[msg.sender] += 50;
        return this.afterSwap.selector;
    }

    error ReentrantCall();

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

    // Secure EIP-1153 Transient Storage simulation (Transient Reentrancy Lock)
    function executeAction() external nonReentrant {
        // Simulates a state mutation protected by the transient lock
        balances[msg.sender] += 10;
    }
}
