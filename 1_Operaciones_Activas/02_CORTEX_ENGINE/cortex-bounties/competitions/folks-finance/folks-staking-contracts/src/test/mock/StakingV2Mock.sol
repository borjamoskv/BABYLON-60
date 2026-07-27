// SPDX-License-Identifier: BUSL-1.1

pragma solidity 0.8.30;

import {SafeERC20, IERC20} from "openzeppelin-contracts/contracts/token/ERC20/utils/SafeERC20.sol";
import {IERC165} from "openzeppelin-contracts/contracts/utils/introspection/IERC165.sol";
import {ERC165} from "openzeppelin-contracts/contracts/utils/introspection/ERC165.sol";
import {IStakingV1} from "../../interfaces/IMigratorV1.sol";
import {IMigratorReceiverV2} from "../../interfaces/IMigratorReceiverV2.sol";

/* @dev
    This smart-contract is testing mock for next version of staking, which
    can receive funds and positions from MigratorV1 contract.
*/
contract StakingV2Mock is ERC165, IMigratorReceiverV2 {
    using SafeERC20 for IERC20;

    IERC20 public immutable TOKEN;
    uint256 public mockAmountToTransfer;

    constructor(IERC20 token) {
        TOKEN = token;
    }

    function setMockAmountToTransfer(uint256 _mockAmountToTransfer) external {
        mockAmountToTransfer = _mockAmountToTransfer;
    }

    function migratePositionsTo(address, IStakingV1.UserStake[] memory _userStakes) external override {
        uint256 amountToTransfer;
        for (uint8 i = 0; i < _userStakes.length; i++) {
            amountToTransfer += (_userStakes[i].amount
                    + _userStakes[i].reward
                    - _userStakes[i].claimedAmount
                    - _userStakes[i].claimedReward);
        }

        if (mockAmountToTransfer > 0) {
            amountToTransfer = mockAmountToTransfer;
        }

        TOKEN.safeTransferFrom(msg.sender, address(this), amountToTransfer);
    }

    function supportsInterface(bytes4 interfaceId) public view virtual override(ERC165, IERC165) returns (bool) {
        return interfaceId == type(IMigratorReceiverV2).interfaceId || super.supportsInterface(interfaceId);
    }

    // Unused functions

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

    function activeTotalRewards() external pure returns (uint256) {
        return 0;
    }

    function paused() public view virtual returns (bool) {
        return false;
    }
}
