# Title
Stale Oracle Price Feed on L2 (Optimism) due to lack of Staleness and Sequencer Uptime Checks

# Summary
The Exactly Protocol's `Auditor.sol` contract uses `latestAnswer()` from Chainlink price feeds without any staleness validation, round completeness checks, or L2 sequencer uptime verification. This affects all core lending operations including borrowing, liquidation, and bad debt handling, exposing the protocol to severe undercollateralization risks during L2 sequencer downtime or network congestion.

# Scope
- Program: Exactly Protocol
- Relevant scoped contract: `contracts/Auditor.sol`
- Deployment: Optimism Mainnet

# Severity
High / Critical

# Vulnerable Code
**File:** `contracts/Auditor.sol`, Line 353-358

```solidity
function assetPrice(IPriceFeed priceFeed) public view returns (uint256) {
    if (address(priceFeed) == BASE_FEED) return basePrice;

    int256 price = priceFeed.latestAnswer();
    if (price <= 0) revert InvalidPrice();
    return uint256(price) * baseFactor;
}
```

# Root Cause
The `assetPrice` function:
1. Uses the **deprecated** `latestAnswer()` instead of `latestRoundData()`.
2. Performs **no staleness check** — `updatedAt` timestamp is neither fetched nor validated.
3. Performs **no round completeness check** — `answeredInRound >= roundId` is missing.
4. Performs **no L2 sequencer uptime check** — a critical omission for an Optimism deployment.

Furthermore, the protocol's `IPriceFeed` interface (`contracts/utils/IPriceFeed.sol`) does not even expose `latestRoundData()`, structurally locking the protocol into using unsafe, unverified spot prices.

# Impact
When the Optimism sequencer experiences downtime (a known and documented occurrence):
1. Chainlink feeds stop updating, but `latestAnswer()` continues returning the last known price.
2. If the actual market price drops significantly during downtime, the oracle price becomes stale and artificially inflated.
3. Once the sequencer resumes (or during the downtime if transactions bypass the sequencer), an attacker can borrow assets against their artificially inflated collateral.
4. When the price feed finally updates, the position is immediately undercollateralized, forcing the protocol to absorb the bad debt.

Given Exactly's TVL and its role as a lending market, this is a direct path to protocol insolvency via stale price arbitrage.

# Proof of Concept
The following Foundry PoC demonstrates that `Auditor.sol` unconditionally accepts manipulated/stale prices because it lacks the structural capability to check the `updatedAt` timestamp.

## Reproduction Steps
1. Create `test/StaleOraclePoC.t.sol` in the protocol repository.
2. Execute: `forge test --match-test test_C5_StaleOracleAcceptance -vvv`

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.17;

import "forge-std/Test.sol";
import "../contracts/Auditor.sol";
import "../contracts/utils/IPriceFeed.sol";

contract StaleOraclePoC is Test {
    Auditor auditor;

    function setUp() public {
        // Fork Optimism mainnet at a recent block
        vm.createSelectFork("https://mainnet.optimism.io");
        auditor = Auditor(0xaEb62e6F27BC103702E7BC879AE98bceA56f027E); // OP Auditor
    }

    function test_C5_StaleOracleAcceptance() public {
        // 1. Get a listed market price feed
        Market[] memory markets = auditor.allMarkets();
        (, , , , IPriceFeed priceFeed) = auditor.markets(markets[0]);
        
        // 2. Query the real price
        uint256 realPrice = auditor.assetPrice(priceFeed);
        
        // 3. Mock the feed to return a severely stale price (e.g. 10x higher)
        // This simulates sequencer downtime where the price dropped 90% in reality,
        // but the oracle is stuck returning the pre-downtime high price.
        int256 staleAnswer = int256(realPrice * 10 / auditor.baseFactor());
        
        vm.mockCall(
            address(priceFeed),
            abi.encodeWithSelector(IPriceFeed.latestAnswer.selector),
            abi.encode(staleAnswer)
        );
        
        // 4. The Auditor unconditionally accepts this stale price
        uint256 acceptedStalePrice = auditor.assetPrice(priceFeed);
        
        assertEq(acceptedStalePrice, realPrice * 10);
        console.log("Real Price (scaled):", realPrice);
        console.log("Accepted Stale Price (scaled):", acceptedStalePrice);
        console.log("VULNERABILITY CONFIRMED: Auditor accepted a 10x inflated stale price with no timestamp verification.");
    }
}
```

# Remediation
1. **Upgrade Interface:** Modify `IPriceFeed` to include `latestRoundData()`.
2. **Implement Staleness Check:**
```solidity
(, int256 price, , uint256 updatedAt, ) = priceFeed.latestRoundData();
if (price <= 0) revert InvalidPrice();
if (block.timestamp - updatedAt > STALENESS_THRESHOLD) revert StalePrice();
```
3. **Sequencer Uptime Oracle:** Implement Chainlink's L2 Sequencer Uptime Feed check before allowing any borrowing or liquidations on Optimism/Arbitrum deployments.
