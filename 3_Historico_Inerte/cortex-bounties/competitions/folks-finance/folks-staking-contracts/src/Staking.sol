// SPDX-License-Identifier: BUSL-1.1

pragma solidity 0.8.30;

import {SafeERC20, IERC20} from "openzeppelin-contracts/contracts/token/ERC20/utils/SafeERC20.sol";
import {IERC165} from "openzeppelin-contracts/contracts/utils/introspection/IERC165.sol";
import {ReentrancyGuard} from "openzeppelin-contracts/contracts/utils/ReentrancyGuard.sol";
import {Pausable} from "openzeppelin-contracts/contracts/utils/Pausable.sol";
import {
    AccessControlDefaultAdminRules
} from "openzeppelin-contracts/contracts/access/extensions/AccessControlDefaultAdminRules.sol";
import {IERC20Permit} from "openzeppelin-contracts/contracts/token/ERC20/extensions/ERC20Permit.sol";
import {Math} from "@openzeppelin/contracts/utils/math/Math.sol";
import {IStakingV1} from "./interfaces/IStakingV1.sol";
import {IMigratorV1} from "./interfaces/IMigratorV1.sol";

/**
 *     @title Fixed APR staking contract
 */
contract Staking is IMigratorV1, Pausable, ReentrancyGuard, AccessControlDefaultAdminRules {
    using SafeERC20 for IERC20;

    bytes32 public constant MANAGER_ROLE = keccak256("MANAGER");
    bytes32 public constant PAUSER_ROLE = keccak256("PAUSER");
    bytes32 public constant MIGRATOR_ROLE = keccak256("MIGRATOR");

    uint8 public constant MAX_STAKES_PER_USER = 100;

    // staking and reward token are the same and can be set only once during deployment
    // we assume ERC20 doesn't have any fee on transfer or rebasing logic
    IERC20 public immutable TOKEN;

    uint256 public activeTotalStaked;
    uint256 public activeTotalRewards;

    StakingPeriod[] public stakingPeriods;
    mapping(address user => UserStake[]) public userStakes;
    mapping(address migrator => mapping(address user => bool isAuthorized)) public migrationPermits;

    constructor(address _admin, address _manager, address _pauser, address _token)
        AccessControlDefaultAdminRules(1 days, _admin)
    {
        TOKEN = IERC20(_token);
        _grantRole(MANAGER_ROLE, _manager);
        _grantRole(PAUSER_ROLE, _pauser);
    }

    function stake(uint8 periodIndex, uint256 amount, StakeParams calldata params)
        external
        nonReentrant
        whenNotPaused
        returns (uint8)
    {
        return _stake(periodIndex, amount, params);
    }

    function stakeWithPermit(
        uint8 periodIndex,
        uint256 amount,
        StakeParams calldata params,
        uint256 deadline,
        uint8 v,
        bytes32 r,
        bytes32 s
    ) external nonReentrant whenNotPaused returns (uint8) {
        // try catch for avoiding frontrun griefing
        // https://github.com/OpenZeppelin/openzeppelin-contracts/blob/master/contracts/token/ERC20/extensions/IERC20Permit.sol#L14
        try IERC20Permit(address(TOKEN)).permit(msg.sender, address(this), amount, deadline, v, r, s) {} catch {}
        return _stake(periodIndex, amount, params);
    }

    // user allowed to withdraw when contract is paused
    function withdraw(uint8 stakeIndex) external nonReentrant returns (uint256) {
        return _withdraw(stakeIndex);
    }

    function setMigrationPermit(address _migrator, bool _isMigrationPermitted) external {
        if (migrationPermits[_migrator][msg.sender] == _isMigrationPermitted) return;
        if (_isMigrationPermitted && !hasRole(MIGRATOR_ROLE, _migrator)) revert MigratorNotFound(_migrator);

        migrationPermits[_migrator][msg.sender] = _isMigrationPermitted;
        emit MigrationPermitUpdated(_migrator, msg.sender, _isMigrationPermitted);
    }

    function addStakingPeriod(
        uint256 _cap,
        uint64 _stakingDurationSeconds,
        uint64 _unlockDurationSeconds,
        uint32 _aprBps,
        bool _isActive
    ) external onlyRole(MANAGER_ROLE) returns (uint8) {
        if (_stakingDurationSeconds == 0) revert StakingDurationCannotBeZero();
        if (_unlockDurationSeconds == 0) revert UnlockDurationCannotBeZero();
        if (stakingPeriods.length > type(uint8).max) revert MaxStakingPeriodsReached();

        // to simplify logic, we don't set restrictions on non-zero rewards
        uint8 periodIndex = uint8(stakingPeriods.length);
        stakingPeriods.push(
            StakingPeriod({
                cap: _cap,
                capUsed: 0,
                stakingDurationSeconds: _stakingDurationSeconds,
                unlockDurationSeconds: _unlockDurationSeconds,
                aprBps: _aprBps,
                isActive: _isActive
            })
        );

        emit StakingPeriodAdded(periodIndex, _cap, _stakingDurationSeconds, _unlockDurationSeconds, _aprBps, _isActive);
        return periodIndex;
    }

    function updateStakingPeriod(
        uint8 periodIndex,
        uint256 _cap,
        uint64 _stakingDurationSeconds,
        uint64 _unlockDurationSeconds,
        uint32 _aprBps,
        bool _isActive
    ) external onlyRole(MANAGER_ROLE) {
        if (_stakingDurationSeconds == 0) revert StakingDurationCannotBeZero();
        if (_unlockDurationSeconds == 0) revert UnlockDurationCannotBeZero();
        if (periodIndex >= stakingPeriods.length) revert PeriodNotFound();
        StakingPeriod storage stakingPeriod = stakingPeriods[periodIndex];

        // we allow to set cap lower than is currently being used
        stakingPeriod.cap = _cap;
        stakingPeriod.stakingDurationSeconds = _stakingDurationSeconds;
        stakingPeriod.unlockDurationSeconds = _unlockDurationSeconds;
        stakingPeriod.aprBps = _aprBps;
        stakingPeriod.isActive = _isActive;

        emit StakingPeriodUpdated(
            periodIndex, _cap, _stakingDurationSeconds, _unlockDurationSeconds, _aprBps, _isActive
        );
    }

    function pause() external onlyRole(PAUSER_ROLE) {
        _pause();
    }

    function unpause() external onlyRole(PAUSER_ROLE) {
        _unpause();
    }

    /**
     *     @dev manager allowed to recover full amount of any ERC20 token accidentally sent to staking contract
     *          except staking token itself. In case of staking token - manager allowed to recover only
     *          extra amount (which is not supposed to be distributed to users)
     */
    function recoverERC20(address tokenAddress, uint256 tokenAmount) external nonReentrant onlyRole(MANAGER_ROLE) {
        if (tokenAddress == address(TOKEN)) {
            uint256 requiredBalance = activeTotalStaked + activeTotalRewards;
            uint256 contractTokenBalance = TOKEN.balanceOf(address(this));
            if (contractTokenBalance < requiredBalance + tokenAmount) {
                // invariant contractTokenBalance >= requiredBalance so can't underflow
                revert NotEnoughBalanceToRecover(tokenAddress, tokenAmount, contractTokenBalance - requiredBalance);
            }
        }

        emit Recovered(tokenAddress, msg.sender, tokenAmount);
        IERC20(tokenAddress).safeTransfer(msg.sender, tokenAmount);
    }

    /**
     *     @dev fully withdrawn stakes are not getting migrated
     */
    function migratePositionsFrom(address user)
        external
        nonReentrant
        onlyRole(MIGRATOR_ROLE)
        returns (UserStake[] memory)
    {
        if (!migrationPermits[msg.sender][user]) revert MigratorNotPermitted(msg.sender, user);

        UserStake[] memory stakes = userStakes[user];

        uint256 stakesToMigrateCount;
        // Count migratedStakes array size
        for (uint256 i = 0; i < stakes.length; i++) {
            if (stakes[i].claimedAmount + stakes[i].claimedReward < stakes[i].amount + stakes[i].reward) {
                stakesToMigrateCount++;
            }
        }
        UserStake[] memory migratedStakes = new UserStake[](stakesToMigrateCount);
        delete userStakes[user];

        uint8 migratedCount;
        uint256 unclaimedUserAmount;
        uint256 unclaimedUserRewards;
        for (uint256 i = 0; i < stakes.length; i++) {
            if (stakes[i].claimedAmount + stakes[i].claimedReward >= stakes[i].amount + stakes[i].reward) {
                continue;
            }
            unclaimedUserAmount += stakes[i].amount - stakes[i].claimedAmount;
            unclaimedUserRewards += stakes[i].reward - stakes[i].claimedReward;

            migratedStakes[migratedCount] = stakes[i];
            migratedCount++;
        }

        // The capUsed is intentionally not decremented for migrated positions. Migration is a terminal operation:
        // the manager will deactivate all staking periods or pauser will pause the contract before migration begins
        activeTotalStaked -= unclaimedUserAmount;
        activeTotalRewards -= unclaimedUserRewards;

        emit MigratedFrom(msg.sender, user, migratedCount, unclaimedUserAmount, unclaimedUserRewards);
        TOKEN.safeTransfer(msg.sender, unclaimedUserAmount + unclaimedUserRewards);
        return migratedStakes;
    }

    function getStakingPeriods() external view returns (StakingPeriod[] memory) {
        return stakingPeriods;
    }

    function getStakingPeriod(uint8 periodIndex) external view returns (StakingPeriod memory) {
        if (periodIndex >= stakingPeriods.length) revert PeriodNotFound();
        return stakingPeriods[periodIndex];
    }

    function getUserStakes(address user) external view returns (UserStake[] memory) {
        return userStakes[user];
    }

    function getUserStake(address user, uint8 stakeIndex) external view returns (UserStake memory) {
        if (stakeIndex >= userStakes[user].length) revert StakeNotFound();
        return userStakes[user][stakeIndex];
    }

    function getClaimable(address user, uint8 stakeIndex) external view returns (uint256) {
        if (stakeIndex >= userStakes[user].length) revert StakeNotFound();

        UserStake memory userStake = userStakes[user][stakeIndex];

        if (block.timestamp <= userStake.unlockTime) return 0;

        (uint256 amountToClaim, uint256 rewardToClaim) = _getClaimableAmounts(userStake);
        return amountToClaim + rewardToClaim;
    }

    function paused() public view virtual override(IStakingV1, Pausable) returns (bool) {
        return super.paused();
    }

    function supportsInterface(bytes4 interfaceId)
        public
        view
        virtual
        override(AccessControlDefaultAdminRules, IERC165)
        returns (bool)
    {
        return interfaceId == type(IMigratorV1).interfaceId || interfaceId == type(IStakingV1).interfaceId
            || super.supportsInterface(interfaceId);
    }

    function _stake(uint8 periodIndex, uint256 amount, StakeParams calldata params) internal returns (uint8) {
        if (amount == 0) revert CannotStakeZero();
        if (periodIndex >= stakingPeriods.length) revert PeriodNotFound();

        StakingPeriod storage stakingPeriod = stakingPeriods[periodIndex];
        if (!stakingPeriod.isActive) revert StakingPeriodInactive(periodIndex);

        // ensuring that staking period conditions were not updated in front of this operation
        if (stakingPeriod.stakingDurationSeconds > params.maxStakingDurationSeconds) {
            revert StakingPeriodStakingDurationDiffer(
                periodIndex, params.maxStakingDurationSeconds, stakingPeriod.stakingDurationSeconds
            );
        }
        if (stakingPeriod.unlockDurationSeconds > params.maxUnlockDurationSeconds) {
            revert StakingPeriodUnlockDurationDiffer(
                periodIndex, params.maxUnlockDurationSeconds, stakingPeriod.unlockDurationSeconds
            );
        }
        if (stakingPeriod.aprBps < params.minAprBps) {
            revert StakingPeriodAprDiffer(periodIndex, params.minAprBps, stakingPeriod.aprBps);
        }

        uint256 updatedCapUsed = stakingPeriod.capUsed + amount;
        if (stakingPeriod.cap < updatedCapUsed) revert StakingCapReached(stakingPeriod.cap);
        if (userStakes[msg.sender].length >= MAX_STAKES_PER_USER) revert MaxUserStakesReached(MAX_STAKES_PER_USER);

        uint256 rewardBpsDenominator = 1e4 * 365 days;
        uint256 reward = (amount * stakingPeriod.aprBps * stakingPeriod.stakingDurationSeconds) / rewardBpsDenominator;
        uint256 contractBalance = TOKEN.balanceOf(address(this));
        uint256 requiredBalance = activeTotalStaked + activeTotalRewards + reward;
        // ensure that smart-contract balance is enough to pay reward
        if (requiredBalance > contractBalance) {
            revert NotEnoughContractBalance(address(TOKEN), contractBalance, requiredBalance);
        }

        activeTotalStaked += amount;
        activeTotalRewards += reward;
        stakingPeriod.capUsed = updatedCapUsed;

        uint8 stakeIndex = uint8(userStakes[msg.sender].length);
        userStakes[msg.sender].push(
            UserStake({
                amount: amount,
                reward: reward,
                claimedAmount: 0,
                claimedReward: 0,
                aprBps: stakingPeriod.aprBps,
                stakeTime: uint64(block.timestamp),
                unlockTime: uint64(block.timestamp) + stakingPeriod.stakingDurationSeconds,
                unlockDuration: stakingPeriod.unlockDurationSeconds
            })
        );

        emit Staked(msg.sender, periodIndex, params.referrer, stakeIndex, amount, reward);
        TOKEN.safeTransferFrom(msg.sender, address(this), amount);
        return stakeIndex;
    }

    /**
     *     @notice withdraw linear unlock mechanism
     *             staked amount and reward accrued linearly during unlock period
     *             user can withdraw multiple times
     */
    function _withdraw(uint8 stakeIndex) internal returns (uint256) {
        if (stakeIndex >= userStakes[msg.sender].length) revert StakeNotFound();

        UserStake storage userStake = userStakes[msg.sender][stakeIndex];
        if (block.timestamp <= userStake.unlockTime) {
            revert RewardsNotAvailableYet(uint64(block.timestamp), userStake.unlockTime);
        }
        if (userStake.claimedAmount + userStake.claimedReward >= userStake.amount + userStake.reward) {
            revert AlreadyWithdrawn(stakeIndex);
        }

        (uint256 amountToClaim, uint256 rewardToClaim) = _getClaimableAmounts(userStake);
        uint256 totalToWithdraw = amountToClaim + rewardToClaim;

        activeTotalStaked -= amountToClaim;
        activeTotalRewards -= rewardToClaim;
        userStake.claimedAmount += amountToClaim;
        userStake.claimedReward += rewardToClaim;

        emit Withdrawn(msg.sender, stakeIndex, amountToClaim, rewardToClaim);
        TOKEN.safeTransfer(msg.sender, totalToWithdraw);
        return totalToWithdraw;
    }

    function _getAccrued(uint256 amount, uint256 duration, uint256 elapsed) internal pure returns (uint256) {
        return Math.mulDiv(amount, Math.min(elapsed, duration), duration);
    }

    function _getClaimableAmounts(UserStake memory userStake)
        internal
        view
        returns (uint256 claimableAmount, uint256 claimableReward)
    {
        uint256 elapsed = block.timestamp - userStake.unlockTime;
        uint256 accruedAmount = _getAccrued(userStake.amount, userStake.unlockDuration, elapsed);
        uint256 accruedReward = _getAccrued(userStake.reward, userStake.unlockDuration, elapsed);

        claimableAmount = accruedAmount - userStake.claimedAmount;
        claimableReward = accruedReward - userStake.claimedReward;
    }
}
