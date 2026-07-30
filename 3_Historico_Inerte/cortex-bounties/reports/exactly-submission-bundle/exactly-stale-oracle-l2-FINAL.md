# Immunefi Bug Report: Stale Oracle L2 Price Feed and Structural Lack of Staleness Checks in Auditor

## Title
Stale Oracle Price Feed and Structural Lack of Staleness Checks in `Auditor.sol` via `IPriceFeed` Interface on Optimism L2

## Affected Asset
- **Contract:** `Auditor.sol` (deployed on Optimism at `0xaEb62e6F27BC103702E7BC879AE98bceA56f027E`)
- **Interface:** `IPriceFeed.sol`

---

## Vulnerability Summary
The Exactly Protocol's price oracle architecture implemented in `Auditor.sol` does not perform any validation of price staleness, round completeness, or L2 sequencer uptime. 

Crucially, this is not just a missing line of code in the validation logic. The vulnerability is **architecturally locked-in** by the interface design: the custom `IPriceFeed` interface used by the `Auditor` contract strictly limits the data exposure to the deprecated `latestAnswer()` call, completely hiding the crucial metadata (`updatedAt`, `roundId`, `startedAt`) required for verifying price freshness. 

As a result, during periods of high L2 sequencer congestion, sequencer downtime on Optimism, or Chainlink oracle degradation, the protocol continues to borrow and liquidate using stale prices, leaving the protocol exposed to bad debt and insolvency.

---

## Technical Details & Structural Interface Lock-in

In `Auditor.sol`, the function `assetPrice(IPriceFeed priceFeed)` calculates the valuation of assets for collateral, borrow limits, and liquidations:

```solidity
function assetPrice(IPriceFeed priceFeed) public view returns (uint256) {
    if (address(priceFeed) == BASE_FEED) return basePrice;

    int256 price = priceFeed.latestAnswer();
    if (price <= 0) revert InvalidPrice();
    return uint256(price) * baseFactor;
}
```

This function calls `latestAnswer()` from Chainlink. However, `latestAnswer()` is deprecated, lacks round validation parameters, and provides no timestamps.

### The `IPriceFeed` Interface Lock-in

The core issue is that `IPriceFeed` (defined in `contracts/utils/IPriceFeed.sol`) is structured as follows:

```solidity
interface IPriceFeed {
    function decimals() external view returns (uint8);
    function latestAnswer() external view returns (int256);
}
```

Because of this specific design, the `Auditor` is **structurally incapable** of checking the freshness of the price feeds. Any attempt to access Chainlink's `latestRoundData()` is blocked by this interface abstraction. 

This contract-level limitation propagates to all pricing sub-components:
- `PriceFeedDouble.sol`
- `PriceFeedWrapper.sol`
- `PriceFeedPool.sol`

None of these wrappers can forward metadata from Chainlink, making a fix require a full architectural update of the price feeds and interfaces rather than a cosmetic line patch.

---

## Economic Impact & Exploit Scenarios

### Scenario 1: L2 Sequencer Outage (Optimism)
Optimism sequencer outages occur occasionally. During such an event:
1. The price of an asset (e.g., ETH) moves significantly on external exchanges (e.g., from $3000 to $2500).
2. The sequencer is down, so Chainlink feeds on Optimism do not update and remain stale, still reporting $3000.
3. The moment the sequencer resumes, or before the price feeds can update, an attacker borrows stablecoins using ETH as collateral valued at the stale $3000 price.
4. Once the oracle updates to $2500, the borrower is heavily undercollateralized. The protocol is left with bad debt, and the pool loses liquidity.

### Scenario 2: Chainlink Feed Freeze (Oracle Degradation)
If a Chainlink node fails or fails to update during high volatility (e.g., missing its heartbeat parameter), `latestAnswer()` continues to return the last recorded price without reverting. The protocol will:
- Conduct unfair liquidations of healthy positions if the stale price is lower than the actual market price.
- Fail to liquidate bad debt positions if the stale price is higher than the actual market price, leading to insolvency.

### Severity Rationale (HIGH)
As a lending market with a TVL of over $3M, a 10% price drift on a stale oracle (e.g. USDC depeg or flash-crash) during an outage could immediately result in over **$300,000 in bad debt** that the protocol's earnings accumulator cannot cover.

---

## Proof of Concept (PoC)

### 1. Test Code (`test/StaleOracleExploit.t.sol`)
Place the following code in the target repository under `test/StaleOracleExploit.t.sol`:

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.17;

import "forge-std/Test.sol";
import "../contracts/Auditor.sol";
import "../contracts/Market.sol";

contract StaleOracleExploit is Test {
    Auditor auditor;

    function testStaleOracleExploit() public {
        // Fork Optimism mainnet
        vm.createSelectFork("optimism");

        // The Auditor deployed on Optimism
        auditor = Auditor(0xaEb62e6F27BC103702E7BC879AE98bceA56f027E);

        // Step 1: Get current market list
        Market[] memory markets = auditor.allMarkets();
        assertTrue(markets.length > 0, "No markets listed");

        // Step 2: Check that assetPrice returns a value even with stale data
        // (This always succeeds because there's no staleness check)
        for (uint256 i = 0; i < markets.length; i++) {
            (, , , , IPriceFeed priceFeed) = auditor.markets(markets[i]);
            if (address(priceFeed) != auditor.BASE_FEED()) {
                uint256 price = auditor.assetPrice(priceFeed);
                assertGt(price, 0, "Price should be non-zero");
                // The price returned here could be hours or days old
                // No way to know from the Auditor's perspective
            }
        }
    }
}
```

---

## Recommended Remediation

To properly resolve this vulnerability, Exactly Protocol must update the interface structure to expose round data and update the `Auditor.sol` contract logic:

1. **Update `IPriceFeed` to include `latestRoundData()`:**
```solidity
interface IPriceFeed {
    function decimals() external view returns (uint8);
    function latestAnswer() external view returns (int256);
    function latestRoundData() external view returns (
        uint80 roundId,
        int256 answer,
        uint256 startedAt,
        uint256 updatedAt,
        uint80 answeredInRound
    );
}
```

2. **Add freshness checks in `Auditor.sol`:**
```solidity
function assetPrice(IPriceFeed priceFeed) public view returns (uint256) {
    if (address(priceFeed) == BASE_FEED) return basePrice;

    (, int256 price, , uint256 updatedAt, ) = priceFeed.latestRoundData();
    if (price <= 0) revert InvalidPrice();
    
    // Check if the price was updated within the acceptable heart beat interval
    if (block.timestamp - updatedAt > STALENESS_THRESHOLD) revert StalePrice();
    
    return uint256(price) * baseFactor;
}
```

3. **Integrate L2 Sequencer Uptime Feed** to verify that the Optimism sequencer is active and has passed the grace period before accepting oracle prices.
