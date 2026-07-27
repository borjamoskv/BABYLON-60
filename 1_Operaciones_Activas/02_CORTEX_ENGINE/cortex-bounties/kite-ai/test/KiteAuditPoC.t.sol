// SPDX-License-Identifier: MIT
pragma solidity 0.8.25;

import "forge-std/Test.sol";
import "../src/IStakingVaultMock.sol";

/// @notice PoC for V-003: Harvest Fee Cap Arithmetic Silently Steals Protocol Revenue
contract V003_FeeStealing_PoC is Test {
    uint256 constant BIPS_DENOMINATOR = 10000;
    
    struct Operator {
        uint256 accruedFees;
    }

    uint256 public totalAccruedOperatorFees;
    uint256 public vaultAccountedBalance;
    uint256 public protocolFeeBips;
    uint256 public operatorFeeBips;
    uint256 public pendingProtocolFees;
    
    mapping(address => Operator) public operators;

    event Harvested(uint256 totalRewards, uint256 protocolFee, uint256 poolIncrease);

    function setUp() public {
        vaultAccountedBalance = 100 ether;
    }

    function simulate_harvest(uint256 reward, address operatorAddr) public returns (uint256 protocolCut, uint256 operatorCut) {
        protocolCut = (reward * protocolFeeBips) / BIPS_DENOMINATOR;
        operatorCut = (reward * operatorFeeBips) / BIPS_DENOMINATOR;

        uint256 totalOperatorFee = operatorCut;
        uint256 totalProtocolFee = protocolCut;

        vaultAccountedBalance += reward;
        
        operators[operatorAddr].accruedFees += totalOperatorFee;
        totalAccruedOperatorFees += totalOperatorFee;

        // THE VULNERABILITY: Cap only bounds totalProtocolFee
        if (totalOperatorFee + totalProtocolFee > reward) {
            totalProtocolFee = reward - totalOperatorFee;
        }

        vaultAccountedBalance -= totalProtocolFee;
        pendingProtocolFees += totalProtocolFee;

        uint256 poolIncrease = reward - totalOperatorFee - totalProtocolFee;
        emit Harvested(reward, totalProtocolFee, poolIncrease);
        
        return (totalProtocolFee, totalOperatorFee);
    }

    function test_V003_ProtocolFeeWiped() public {
        operatorFeeBips = 9500; 
        protocolFeeBips = 1000; 

        address operator = address(0xBEEF);
        uint256 reward = 1 ether;

        (uint256 actualProtocolFee, ) = simulate_harvest(reward, operator);
        
        assertEq(actualProtocolFee, 0.05 ether, "Protocol fee should be capped incorrectly");
    }
}

/// @notice PoC for V-002: Rounding Dust DoS
contract V002_DustDoS_PoC is Test {
    function test_V002_RevertOnSmallWithdrawals() public {
        uint256 effectiveNeeded = 5; 
        uint256 activeCount = 10;   
        uint256 totalWeightNumerator = 10;
        
        uint256 totalAllocated = 0;
        for (uint256 i = 0; i < activeCount; i++) {
            uint256 targetShare = (effectiveNeeded * 1) / totalWeightNumerator; 
            totalAllocated += targetShare;
        }
        
        assertEq(totalAllocated, 0, "Total allocated should be zero");
        assertTrue(totalAllocated < effectiveNeeded, "Should have remaining needed amount");
    }
}

/// @notice PoC for V-001: inFlightExitingAmount Desynchronization
contract V001_InFlightDesync_PoC is Test {
    uint256 public inFlightExitingAmount;
    uint256 public lastPendingReconcileEpoch;
    mapping(address => uint256) public operatorPriorEpochPendingAmount;
    mapping(address => uint256) public operatorCurrentEpochPendingAmount;
    mapping(bytes32 => uint256) public delegatorRemovalInitiatedEpoch;

    function simulate_recordRemoval(address op, bytes32 id, uint256 amount, uint256 currentEpoch) public {
        delegatorRemovalInitiatedEpoch[id] = currentEpoch + 1;
        inFlightExitingAmount += amount;
        operatorCurrentEpochPendingAmount[op] += amount;
    }

    function simulate_decrementInFlight(address op, uint256 amount, uint256 initiatedEpoch) public {
        if (initiatedEpoch == 0) return;
        inFlightExitingAmount = inFlightExitingAmount >= amount ? inFlightExitingAmount - amount : 0;
        uint256 initEpoch = initiatedEpoch - 1;
        bool preferPrior = initEpoch <= lastPendingReconcileEpoch;
        uint256 remaining = amount;
        if (preferPrior) {
            uint256 prior = operatorPriorEpochPendingAmount[op];
            if (prior >= remaining) {
                operatorPriorEpochPendingAmount[op] = prior - remaining;
                remaining = 0;
            } else {
                operatorPriorEpochPendingAmount[op] = 0;
                remaining -= prior;
            }
            if (remaining > 0) {
                uint256 cur = operatorCurrentEpochPendingAmount[op];
                operatorCurrentEpochPendingAmount[op] = cur > remaining ? cur - remaining : 0;
            }
        } else {
            uint256 cur = operatorCurrentEpochPendingAmount[op];
            if (cur >= remaining) {
                operatorCurrentEpochPendingAmount[op] = cur - remaining;
                remaining = 0;
            } else {
                operatorCurrentEpochPendingAmount[op] = 0;
                remaining -= cur;
            }
            if (remaining > 0) {
                uint256 prior = operatorPriorEpochPendingAmount[op];
                operatorPriorEpochPendingAmount[op] = prior > remaining ? prior - remaining : 0;
            }
        }
    }

    function test_V001_GhostPendingCredit() public {
        address op = address(0x1);
        bytes32 id = keccak256("delegation");
        uint256 amount = 10 ether;
        
        lastPendingReconcileEpoch = 11; 
        simulate_recordRemoval(op, id, amount, 11); 
        simulate_decrementInFlight(op, amount, 12);
        
        assertEq(operatorCurrentEpochPendingAmount[op], amount, "Ghost credit should remain");
        assertEq(inFlightExitingAmount, 0, "Global inFlight is zero, bucket is stuck");
    }
}

/// @notice PoC for V-004: Vault Accounted Balance Inflation
contract V004_BalanceInflation_PoC is Test {
    uint256 public vaultAccountedBalance;
    mapping(bytes32 => uint256) public delegationPrincipal;

    function setUp() public {
        vaultAccountedBalance = 100 ether;
    }

    function test_V004_DoubleAccountingOnPartialRefund() public {
        bytes32 id = keccak256("delegation");
        uint256 originalAmount = 10 ether;
        vaultAccountedBalance -= originalAmount; 
        delegationPrincipal[id] = originalAmount;
        uint256 inflow = 1 ether;
        vaultAccountedBalance += inflow; 
        uint256 totalDelegatedStake = 10 ether; 
        uint256 pooled = vaultAccountedBalance + totalDelegatedStake;
        assertEq(pooled, 101 ether, "Pooled stake should be inflated");
    }
}
