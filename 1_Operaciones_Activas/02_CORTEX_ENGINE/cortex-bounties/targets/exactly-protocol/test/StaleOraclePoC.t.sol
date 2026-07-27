// SPDX-License-Identifier: MIT
pragma solidity ^0.8.17;

import { Test, console } from "forge-std/Test.sol";
import { Auditor, IPriceFeed } from "../contracts/Auditor.sol";
import { ERC1967Proxy } from "@openzeppelin/contracts-v4/proxy/ERC1967/ERC1967Proxy.sol";

contract MockStalePriceFeed is IPriceFeed {
    uint8 public decimals = 18;
    int256 public price;
    uint256 public updatedAt;

    function setPrice(int256 _price, uint256 _updatedAt) external {
        price = _price;
        updatedAt = _updatedAt;
    }

    function latestAnswer() external view returns (int256) {
        return price;
    }
}

contract StaleOraclePoC is Test {
    Auditor internal auditor;
    MockStalePriceFeed internal priceFeed;

    function setUp() public {
        vm.warp(10 days);
        auditor = Auditor(address(new ERC1967Proxy(address(new Auditor(18)), "")));
        auditor.initialize(Auditor.LiquidationIncentive(0.09e18, 0.01e18));
        priceFeed = new MockStalePriceFeed();
    }

    function test_poc_auditorAcceptsStalePrice() public {
        int256 oldPrice = 100e18;
        uint256 staleTimestamp = block.timestamp - 2 days;
        priceFeed.setPrice(oldPrice, staleTimestamp);

        // Auditor should ideally revert if price is stale, but it doesn't check
        uint256 price = auditor.assetPrice(priceFeed);
        
        assertEq(price, uint256(oldPrice));
        // If we were at 2 days later, we still get the 2-day old price without any error
        console.log("Price accepted despite being 2 days stale:", price);
    }
}
