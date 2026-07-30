// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.8.24;

import {Test} from "forge-std/Test.sol";
import {OuroborosExecutor} from "../src/OuroborosExecutor.sol";

contract OuroborosExecutorTest is Test {
    OuroborosExecutor public executor;

    address public constant WETH = 0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2;
    // Mock Router (Uniswap V2)
    address public constant UNISWAP_V2_ROUTER = 0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D;

    function setUp() public {
        // En un entorno C5-REAL, haríamos un fork de mainnet aquí: --fork-url https://eth-mainnet...
        executor = new OuroborosExecutor();
    }

    function test_Fail_UnauthorizedAccess() public {
        vm.prank(address(0x1));
        address[] memory path = new address[](2);
        path[0] = WETH;
        path[1] = address(0x2);

        vm.expectRevert("NO_AUTH");
        executor.genesisSnipe(
            UNISWAP_V2_ROUTER,
            0,
            path,
            address(this),
            block.timestamp
        );
    }

    // NOTA BABYLON60: test_GenesisSnipeExecution() requiere fork mainnet activo para probar el Router V2 real.
}
