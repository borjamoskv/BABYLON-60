// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

interface IPoolManager {
    function swap() external;
}

contract MaliciousHook {
    address public poolManager;
    mapping(bytes32 => bool) public authorizedPools;
    mapping(address => uint256) public balances;

    constructor(address _poolManager) {
        poolManager = _poolManager;
    }

    // Vulnerable function (INV-01 violation: msg.sender check missing)
    function beforeSwap(address, bytes32 poolId, int256) external returns (bytes4) {
        // Balances are updated via SSTORE without PoolManager access control validation
        balances[msg.sender] += 100;
        return this.beforeSwap.selector;
    }

    // Vulnerable function (INV-02 violation: authorizedPools mapping validation missing)
    function afterSwap(address, bytes32 poolId, int256) external returns (bytes4) {
        // Access control onlyPoolManager is present, but lacks PoolKey validation
        require(msg.sender == poolManager, "OnlyPoolManager");
        // State mutation occurs without verifying pool validity
        balances[tx.origin] += 50; 
        return this.afterSwap.selector;
    }

    // Vulnerable function (INV-03 violation: uses transient storage pattern incorrectly or uses local state variables)
    function executeAction() external {
        // Vulnerable state management instead of transient storage lock
        balances[msg.sender] = 0;
    }
}
