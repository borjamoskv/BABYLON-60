// SPDX-License-Identifier: BUSL-1.1

pragma solidity 0.8.30;

import {SafeERC20, IERC20} from "openzeppelin-contracts/contracts/token/ERC20/utils/SafeERC20.sol";
import {IERC165} from "openzeppelin-contracts/contracts/utils/introspection/IERC165.sol";
import {ERC165} from "openzeppelin-contracts/contracts/utils/introspection/ERC165.sol";
import {IMigratorV1, IStakingV1} from "../../interfaces/IMigratorV1.sol";

/* @dev
    This smart-contract is testing mock for current version of staking, which
    can be the source of migration for MigratorV1 contract.
*/
contract StakingV1Mock is ERC165, IMigratorV1 {
    using SafeERC20 for IERC20;

    IERC20 public immutable TOKEN;
    mapping(address user => IStakingV1.UserStake[]) public userStakes;

    uint256 public mockAmountToTransfer;

    constructor(IERC20 token) {
        TOKEN = token;
    }

    function setMockAmountToTransfer(uint256 _mockAmountToTransfer) external {
        mockAmountToTransfer = _mockAmountToTransfer;
    }

    function setUserStakes(address user, IStakingV1.UserStake[] calldata _stakes) external {
        delete userStakes[user];

        for (uint256 i = 0; i < _stakes.length; i++) {
            userStakes[user].push(_stakes[i]);
        }
    }

    function migratePositionsFrom(address user) external override returns (UserStake[] memory) {
        uint256 amountToTransfer;
        IStakingV1.UserStake[] memory stakes = userStakes[user];
        for (uint8 i = 0; i < stakes.length; i++) {
            amountToTransfer += (stakes[i].amount + stakes[i].reward);
        }

        if (mockAmountToTransfer > 0) {
            amountToTransfer = mockAmountToTransfer;
        }

        delete userStakes[user];
        TOKEN.safeTransfer(msg.sender, amountToTransfer);
        return stakes;
    }

    function supportsInterface(bytes4 interfaceId) public view virtual override(ERC165, IERC165) returns (bool) {
        return interfaceId == type(IMigratorV1).interfaceId || super.supportsInterface(interfaceId);
    }

    // Unused functions

    function setMigrationPermit(address _migrator, bool _isMigrationPermitted) external pure {}

    function getStakingPeriods() external pure returns (StakingPeriod[] memory) {
        return new StakingPeriod[](0);
    }

    function getStakingPeriod(uint8) external pure returns (StakingPeriod memory) {
        return StakingPeriod({
            cap: 0, capUsed: 0, stakingDurationSeconds: 0, unlockDurationSeconds: 0, aprBps: 0, isActive: false
        });
    }

    function getUserStakes(address) external pure returns (UserStake[] memory) {
        return new UserStake[](0);
    }

    function getClaimable(address, uint8) external pure returns (uint256) {
        return 0;
    }

    function getUserStake(address, uint8) external pure returns (UserStake memory) {
        return UserStake({
            amount: 0,
            reward: 0,
            claimedAmount: 0,
            claimedReward: 0,
            aprBps: 0,
            stakeTime: 0,
            unlockTime: 0,
            unlockDuration: 0
        });
    }

    function stake(uint8, uint256, StakeParams calldata) external pure returns (uint8) {
        return 0;
    }

    function stakeWithPermit(uint8, uint256, StakeParams calldata, uint256, uint8, bytes32, bytes32)
        external
        pure
        returns (uint8)
    {
        return 0;
    }

    function withdraw(uint8) external pure returns (uint256) {
        return 0;
    }

    function addStakingPeriod(uint256, uint64, uint64, uint32, bool) external pure returns (uint8) {
        return 0;
    }
    function updateStakingPeriod(uint8, uint256, uint64, uint64, uint32, bool) external pure {}

    function activeTotalStaked() external pure returns (uint256) {
        return 0;
    }

    function activeTotalRewards() public pure returns (uint256) {
        return 0;
    }

    function paused() public view virtual returns (bool) {
        return false;
    }
}
