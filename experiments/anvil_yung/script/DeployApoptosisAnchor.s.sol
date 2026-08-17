// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import {Script} from "forge-std/Script.sol";
import {ApoptosisAnchor} from "../src/ApoptosisAnchor.sol";

/// @title DeployApoptosisAnchorScript — Foundry deployment script for ApoptosisAnchor
/// @dev Deploys ApoptosisAnchor with genesis hash on Anvil local or Testnet L2
contract DeployApoptosisAnchorScript is Script {
    ApoptosisAnchor public anchor;

    function setUp() public {}

    function run() public returns (address) {
        bytes32 genesisHash = vm.envOr("GENESIS_HASH", keccak256("GENESIS_C5_REAL_V4"));

        vm.startBroadcast();
        anchor = new ApoptosisAnchor(genesisHash);
        vm.stopBroadcast();

        return address(anchor);
    }
}
