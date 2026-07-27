// SPDX-License-Identifier: BUSL-1.1

pragma solidity 0.8.30;

import {SafeERC20, IERC20} from "openzeppelin-contracts/contracts/token/ERC20/utils/SafeERC20.sol";
import {ERC165Checker} from "openzeppelin-contracts/contracts/utils/introspection/ERC165Checker.sol";
import {ReentrancyGuard} from "openzeppelin-contracts/contracts/utils/ReentrancyGuard.sol";
import {IMigratorV1, IStakingV1} from "../interfaces/IMigratorV1.sol";
import {IMigratorReceiverV2} from "../interfaces/IMigratorReceiverV2.sol";

/**
 *     @dev Example implementation of Migrator contract.
 *          Detailed implementation (including permissioned/permissionless execution) will depend
 *          on needs of future V2 contracts.
 */
contract MigratorV1 is ReentrancyGuard {
    using SafeERC20 for IERC20;

    IMigratorV1 public immutable FROM;
    IMigratorReceiverV2 public immutable TO;

    error PositionsNotFound(address user);
    error InconsistentBalance(uint256 balanceBefore, uint256 balanceAfter);
    error DifferentStakingTokens(IERC20 senderToken, IERC20 receiverToken);
    error InterfaceNotSupported(address contractAddress, bytes4 interfaceId);

    event Migrated(address user, IMigratorV1 from, IMigratorReceiverV2 to);

    constructor(IMigratorV1 _from, IMigratorReceiverV2 _to) {
        bytes4 fromInterfaceId = type(IMigratorV1).interfaceId;
        if (!ERC165Checker.supportsInterface(address(_from), fromInterfaceId)) {
            revert InterfaceNotSupported(address(_from), fromInterfaceId);
        }

        bytes4 toInterfaceId = type(IMigratorReceiverV2).interfaceId;
        if (!ERC165Checker.supportsInterface(address(_to), toInterfaceId)) {
            revert InterfaceNotSupported(address(_to), toInterfaceId);
        }

        FROM = _from;
        TO = _to;
    }

    function migrate(address user) external nonReentrant {
        IERC20 senderToken = FROM.TOKEN();
        IERC20 receiverToken = TO.TOKEN();
        if (address(senderToken) != address(receiverToken)) revert DifferentStakingTokens(senderToken, receiverToken);

        uint256 tokenBalanceBefore = senderToken.balanceOf(address(this));
        IStakingV1.UserStake[] memory userStakes = FROM.migratePositionsFrom(user);

        if (userStakes.length == 0) revert PositionsNotFound(user);
        uint256 transferredBalance = senderToken.balanceOf(address(this)) - tokenBalanceBefore;
        senderToken.forceApprove(address(TO), transferredBalance);
        TO.migratePositionsTo(user, userStakes);

        uint256 tokenBalanceAfter = senderToken.balanceOf(address(this));
        if (tokenBalanceBefore != tokenBalanceAfter) revert InconsistentBalance(tokenBalanceBefore, tokenBalanceAfter);

        emit Migrated(user, FROM, TO);
    }
}
