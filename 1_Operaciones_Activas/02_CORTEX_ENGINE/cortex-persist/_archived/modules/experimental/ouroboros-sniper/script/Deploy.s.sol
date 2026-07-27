// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.8.24;

import {Script, console} from "forge-std/Script.sol";
import {OuroborosExecutor} from "../src/OuroborosExecutor.sol";

contract DeployOuroboros is Script {
    function run() external {
        // Leer clave privada desde entorno (NUNCA hardcodear — Ley Ω₉)
        uint256 deployerPrivateKey = vm.envUint("SOVEREIGN_PRIVATE_KEY");

        vm.startBroadcast(deployerPrivateKey);

        OuroborosExecutor executor = new OuroborosExecutor();

        console.log(">>> OuroborosExecutor desplegado en:", address(executor));
        console.log(">>> Sovereign (Owner):", vm.addr(deployerPrivateKey));

        vm.stopBroadcast();
    }
}
