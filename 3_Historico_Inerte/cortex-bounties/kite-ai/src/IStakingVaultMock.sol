// SPDX-License-Identifier: MIT
pragma solidity 0.8.25;

/// @dev Minimal interfaces to compile Kite AI PoC tests without the full dependency tree

interface IStakingVaultOperations {
    function prepareWithdrawals() external;
    function harvest() external returns (uint256);
    function initiateValidatorRegistration(
        bytes memory nodeID,
        bytes memory blsPublicKey,
        address remainingBalanceOwner,
        address disableOwner,
        uint256 amount
    ) external returns (bytes32 validationID);
    function completeValidatorRemoval(uint32 messageIndex) external returns (bytes32);
    function initiateValidatorRemoval(bytes32 validationID) external;
    function initiateDelegatorRegistration(bytes32 validationID, uint256 amount) external returns (bytes32 delegationID);
    function completeDelegatorRegistration(bytes32 delegationID, uint32 messageIndex, uint32 uptimeMessageIndex) external;
    function initiateDelegatorRemoval(bytes32 delegationID) external;
    function completeDelegatorRemoval(bytes32 delegationID, uint32 messageIndex) external;
    function claimOperatorFees() external;
    function addOperator(address operator, uint256 allocationBips, address feeRecipient) external;
    function removeOperator(address operator) external;
    function updateOperatorAllocations(address[] calldata operators, uint256[] calldata newBips) external;
    function setOperatorFeeRecipient(address feeRecipient) external;
    function harvestValidators(uint256 operatorIndex, uint256 start, uint256 batchSize) external returns (uint256);
    function harvestDelegators(uint256 operatorIndex, uint256 start, uint256 batchSize) external returns (uint256);
}

interface IStakingVaultView {
    function inFlightExitingAmount() external view returns (uint256);
    function totalValidatorStake() external view returns (uint256);
    function totalDelegatedStake() external view returns (uint256);
    function vaultAccountedBalance() external view returns (uint256);
    function totalPooledStake() external view returns (uint256);
    function pendingWithdrawalStake() external view returns (uint256);
    function operatorExitDebt(address operator) external view returns (uint256);
    function totalExitDebt() external view returns (uint256);
    function totalShares() external view returns (uint256);
    function totalAccruedOperatorFees() external view returns (uint256);
}

/// @dev Mock staking manager for PoC simulation
/// Simulates the KiteStakingManager external state machine
contract MockStakingManager {
    enum DelegatorStatus { Unknown, PendingAdded, Active, PendingRemoved }
    
    struct DelegatorInfo {
        bytes32 validationID;
        uint8 status;
        uint256 amount;
        uint64 startTime;
    }

    struct ValidatorInfo {
        address owner;
        uint8 status;
        uint256 amount;
        uint64 startTime;
    }

    mapping(bytes32 => DelegatorInfo) public delegators;
    mapping(bytes32 => ValidatorInfo) public validators;
    uint256 private _nonce;

    address public vault;
    uint256 public rewardPerHarvest; // simulated reward per claim

    constructor(address _vault) {
        vault = _vault;
    }

    function setRewardPerHarvest(uint256 amount) external {
        rewardPerHarvest = amount;
    }

    // ============ Validator lifecycle ============

    function initiateValidatorRegistration(
        bytes memory, bytes memory, address, address,
        uint16, uint64, address
    ) external payable returns (bytes32 validationID) {
        validationID = keccak256(abi.encodePacked("validator", ++_nonce));
        validators[validationID] = ValidatorInfo({
            owner: msg.sender,
            status: 1, // PendingAdded
            amount: msg.value,
            startTime: 0
        });
    }

    function completeValidatorRegistration(uint32) external returns (bytes32 validationID) {
        // For simplicity, return the most recently created validator
        validationID = keccak256(abi.encodePacked("validator", _nonce));
        validators[validationID].status = 2; // Active
        validators[validationID].startTime = uint64(block.timestamp - 1 days);
    }

    function forceInitiateValidatorRemoval(bytes32 validationID, bool, uint32) external {
        validators[validationID].status = 3; // PendingRemoved
    }

    function completeValidatorRemoval(uint32) external returns (bytes32 validationID) {
        validationID = keccak256(abi.encodePacked("validator", _nonce));
        uint256 amount = validators[validationID].amount;
        validators[validationID].status = 0; // Unknown/removed
        // Return stake to vault
        payable(vault).transfer(amount);
    }

    // ============ Delegator lifecycle ============

    function initiateDelegatorRegistration(bytes32 validationID, address) external payable returns (bytes32 delegationID) {
        delegationID = keccak256(abi.encodePacked("delegator", ++_nonce));
        delegators[delegationID] = DelegatorInfo({
            validationID: validationID,
            status: 1, // PendingAdded
            amount: msg.value,
            startTime: 0
        });
    }

    function completeDelegatorRegistration(bytes32 delegationID, uint32, uint32) external {
        delegators[delegationID].status = 2; // Active
        delegators[delegationID].startTime = uint64(block.timestamp - 1 days);
    }

    function forceInitiateDelegatorRemoval(bytes32 delegationID, bool, uint32) external {
        if (delegators[delegationID].status == 2) {
            delegators[delegationID].status = 3; // PendingRemoved
        }
        // Don't transfer yet — async
    }

    function completeDelegatorRemoval(bytes32 delegationID, uint32) external {
        uint256 amount = delegators[delegationID].amount;
        delegators[delegationID].status = 0;
        payable(vault).transfer(amount + rewardPerHarvest);
    }

    // ============ Reward harvest ============

    function claimValidatorRewards(bytes32, bool, uint32) external returns (uint256 reward) {
        reward = rewardPerHarvest;
        if (reward > 0) {
            payable(vault).transfer(reward);
        }
    }

    function claimDelegatorRewards(bytes32, bool, uint32) external returns (uint256 reward) {
        reward = rewardPerHarvest;
        if (reward > 0) {
            payable(vault).transfer(reward);
        }
    }

    // ============ View ============

    function getPoSValidatorInfo(bytes32 validationID) external view returns (
        address owner, uint16 delegationFeeBips, uint64 minStakeDuration,
        uint64 uptimeSeconds, uint64 lastRewardClaimTime, uint64 lastClaimUptimeSeconds
    ) {
        ValidatorInfo storage v = validators[validationID];
        return (v.owner, 100, 1 days, 0, 0, 0);
    }

    function getValidatorStartTime(bytes32 validationID) external view returns (uint64) {
        return validators[validationID].startTime;
    }

    function getDelegationInfo(bytes32 delegationID) external view returns (
        bool success, uint8 status, uint256 amount, uint64 startTime
    ) {
        DelegatorInfo storage d = delegators[delegationID];
        return (d.amount > 0, d.status, d.amount, d.startTime);
    }

    receive() external payable {}
}
