// SPDX-License-Identifier: BUSL-1.1

pragma solidity 0.8.30;

import {IERC165} from "openzeppelin-contracts/contracts/utils/introspection/IERC165.sol";
import {IStakingV1} from "./IStakingV1.sol";

interface IMigratorReceiverV2 is IERC165, IStakingV1 {
    function migratePositionsTo(address _user, IStakingV1.UserStake[] memory _userStakes) external;
}
