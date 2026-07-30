// SPDX-License-Identifier: BUSL-1.1

pragma solidity 0.8.30;

import {IERC20} from "openzeppelin-contracts/contracts/token/ERC20/utils/SafeERC20.sol";

interface IStakingV1 {
    struct StakingPeriod {
        uint256 cap;
        uint256 capUsed;
        uint64 stakingDurationSeconds;
        uint64 unlockDurationSeconds;
        uint32 aprBps; // APR (365 days = 31536000 seconds) in bps. E.g. 1000 = 10%, 550 = 5.5%
        bool isActive;
    }

    struct UserStake {
        uint256 amount;
        uint256 reward;
        uint256 claimedAmount;
        uint256 claimedReward;
        uint32 aprBps;
        uint64 stakeTime;
        uint64 unlockTime;
        uint64 unlockDuration;
    }

    struct StakeParams {
        uint64 maxStakingDurationSeconds;
        uint64 maxUnlockDurationSeconds;
        uint32 minAprBps;
        address referrer;
    }

    event StakingPeriodAdded(
        uint8 indexed periodIndex,
        uint256 cap,
        uint64 stakingDurationSeconds,
        uint64 unlockDurationSeconds,
        uint32 aprBps,
        bool isActive
    );
    event StakingPeriodUpdated(
        uint8 indexed periodIndex,
        uint256 cap,
        uint64 stakingDurationSeconds,
        uint64 unlockDurationSeconds,
        uint32 aprBps,
        bool isActive
    );
    event Staked(
        address indexed user,
        uint8 indexed periodIndex,
        address indexed referrer,
        uint8 stakeIndex,
        uint256 amount,
        uint256 reward
    );
    event Withdrawn(address indexed user, uint8 stakeIndex, uint256 amount, uint256 reward);
    event Recovered(address indexed token, address indexed recipient, uint256 amount);
    event MigrationPermitUpdated(address indexed migrator, address indexed user, bool isMigrationPermitted);
    event MigratedFrom(
        address indexed migrator,
        address indexed user,
        uint8 migratedCount,
        uint256 unclaimedUserAmount,
        uint256 unclaimedUserRewards
    );

    error CannotStakeZero();
    error StakingDurationCannotBeZero();
    error UnlockDurationCannotBeZero();
    error StakingCapReached(uint256 cap);
    error StakingPeriodInactive(uint8 periodIndex);
    error StakingPeriodStakingDurationDiffer(
        uint8 periodIndex, uint64 expectedMaxStakingDuration, uint64 periodStakingDuration
    );
    error StakingPeriodUnlockDurationDiffer(
        uint8 periodIndex, uint64 expectedMaxUnlockDuration, uint64 periodUnlockDuration
    );
    error StakingPeriodAprDiffer(uint8 periodIndex, uint32 expectedMinApr, uint32 periodApr);
    error MaxStakingPeriodsReached();
    error MaxUserStakesReached(uint8 maxStakes);
    error NotEnoughContractBalance(address token, uint256 balance, uint256 requiredBalance);
    error NotEnoughBalanceToRecover(address token, uint256 toRecover, uint256 maxToRecover);
    error RewardsNotAvailableYet(uint64 currentTime, uint64 availableTime);
    error AlreadyWithdrawn(uint8 stakeIndex);
    error PeriodNotFound();
    error StakeNotFound();
    error MigratorNotFound(address migrator);
    error MigratorNotPermitted(address migrator, address user);

    function stake(uint8 periodIndex, uint256 amount, StakeParams calldata params) external returns (uint8);
    function stakeWithPermit(
        uint8 periodIndex,
        uint256 amount,
        StakeParams calldata params,
        uint256 deadline,
        uint8 v,
        bytes32 r,
        bytes32 s
    ) external returns (uint8);
    function withdraw(uint8 stakeIndex) external returns (uint256);

    function addStakingPeriod(
        uint256 _cap,
        uint64 _stakingDurationSeconds,
        uint64 _unlockDurationSeconds,
        uint32 _aprBps,
        bool _isActive
    ) external returns (uint8);
    function updateStakingPeriod(
        uint8 periodIndex,
        uint256 _cap,
        uint64 _stakingDurationSeconds,
        uint64 _unlockDurationSeconds,
        uint32 _aprBps,
        bool _isActive
    ) external;

    function TOKEN() external view returns (IERC20);
    function getStakingPeriods() external view returns (StakingPeriod[] memory);
    function getStakingPeriod(uint8 periodIndex) external view returns (StakingPeriod memory);
    function getUserStakes(address user) external view returns (UserStake[] memory);
    function getUserStake(address user, uint8 stakeIndex) external view returns (UserStake memory);
    function getClaimable(address user, uint8 stakeIndex) external view returns (uint256);
    function activeTotalStaked() external view returns (uint256);
    function activeTotalRewards() external view returns (uint256);
    function paused() external view returns (bool);
}
