# Stale Oracle Price Feed - Missing Staleness Validation on L2 (Optimism/Base)

## Summary

Exactly Protocol's `Auditor.assetPrice()` uses `IPriceFeed.latestAnswer()` without any staleness validation, heartbeat check, or L2 sequencer uptime verification. This allows the protocol to operate with arbitrarily stale prices during Chainlink feed outages or L2 sequencer downtime, enabling protocol insolvency through overborrowing and unfair liquidations at incorrect prices.

## Vulnerability Details

### Root Cause

`Auditor.sol:353-358` implements price retrieval as:

```solidity
function assetPrice(IPriceFeed priceFeed) public view returns (uint256) {
    if (address(priceFeed) == BASE_FEED) return basePrice;
    int256 price = priceFeed.latestAnswer();
    if (price <= 0) revert InvalidPrice();
    return uint256(price) * baseFactor;
}
```

The function:
1. Uses `latestAnswer()` (deprecated by Chainlink) instead of `latestRoundData()`
2. Does NOT check `updatedAt` against `block.timestamp` to detect stale feeds
3. Does NOT verify `answeredInRound >= roundId` for round completeness
4. Does NOT check L2 sequencer uptime (critical on Optimism/Base deployments)

### Propagation

The missing staleness check propagates through ALL price feed wrappers:

```
Auditor.assetPrice() ──► IPriceFeed.latestAnswer()
                              │
              ┌───────────────┴───────────────┐
              ▼                               ▼
    PriceFeedWrapper.latestAnswer()   PriceFeedDouble.latestAnswer()
              │                               │
              ▼                               ▼
    mainPriceFeed.latestAnswer()     priceFeedOne.latestAnswer()
              │                     priceFeedTwo.latestAnswer()
              ▼                               ▼
     [NO STALENESS CHECK]          [NO STALENESS CHECK]
```

### Verification

Exhaustive grep confirms zero staleness infrastructure:
- `grep -r "stale" contracts/` → **0 results**
- `grep -r "sequencer" .` → **0 results**
- `grep -r "heartbeat" contracts/` → **0 results**
- `grep -r "latestRoundData" contracts/` → **0 results** (only `latestAnswer` used)

## Impact

### Scenario A: Protocol Insolvency via Overborrowing

During a Chainlink feed outage or L2 sequencer downtime:
1. ETH price drops from $2000 to $1000 in reality
2. Oracle remains stuck at $2000 (stale)
3. Borrower deposits 10 ETH → Protocol values collateral at $20,000 (real: $10,000)
4. Borrower takes $15,000 loan → Passes health check at stale price
5. **Result:** $5,000 of undercollateralized debt created. Protocol is insolvent.

### Scenario B: Unfair Liquidation at Incorrect Price

1. ETH drops to $1200, then recovers to $2000
2. Oracle gets stuck at $1200 during recovery
3. Liquidator liquidates borrower at the stale $1200 price
4. Liquidator seizes ETH worth $2000 for $1200 worth of debt coverage
5. **Result:** Borrower loses ~40% more collateral than warranted by real market price

### PoC Results

```
[PASS] testStaleOracleInsolvency() (gas: 602273)
Logs:
  Bob borrowed 15,000 USD against 10 ETH (@ $2000 stale price)
  CRASH: Real ETH price dropped to $1000. Oracle is STALE at $2000.
  VULNERABILITY: Bob borrowed 15,000 USD which is MORE than the REAL value of his collateral ($10,000).
  RESULT: Protocol accepts 24h+ stale price without heartbeat or sequencer check.

[PASS] testUnfairLiquidationStaleLow() (gas: 1481089)
Logs:
  RECOVERY: Real price is $2000, but Oracle STUCK at $1200.
  Max Repay Assets allowed for liquidation: 4950
  RESULT: Alice liquidated Bob at a fake price of $1200, seizing his $2000 ETH.
```

## Proof of Concept

```solidity
// Place in test/ directory of exactly/protocol
// Run: forge test --match-test testStaleOracleInsolvency -vvv

// The PoC demonstrates that Auditor.assetPrice() accepts any non-negative
// price from latestAnswer() regardless of when it was last updated.
// In a mock environment, we set the oracle price, advance time by 24+ hours
// without updating the feed, crash the "real" price, and show the protocol
// still operates on the stale value — allowing overborrowing and unfair
// liquidations.
```

## Scope Justification

This is NOT "incorrect oracle data" (which is listed as out of scope). This is a **missing validation in the Exactly smart contract** (`Auditor.sol`). The oracle data itself may be perfectly valid — the issue is that Exactly's code fails to check whether the data is current before using it. This is a contract implementation defect, analogous to missing access control or missing input validation.

Chainlink's own documentation explicitly requires consumers to validate staleness:
> "Your application should track the `latestTimestamp` variable or use the `updatedAt` value from `latestRoundData()` to make sure that the latest answer is recent enough for your application to use it."

## Recommended Mitigation

1. Replace `latestAnswer()` with `latestRoundData()` in all price feed interfaces
2. Add heartbeat validation: `require(block.timestamp - updatedAt < MAX_STALENESS, "Stale price")`
3. Add round completeness check: `require(answeredInRound >= roundId, "Incomplete round")`
4. Add L2 sequencer uptime feed check (Chainlink provides this for Optimism/Base)
5. Add a grace period after sequencer recovery before allowing liquidations

## References
- [Auditor.sol#L353-L358](https://github.com/exactly/protocol/blob/main/contracts/Auditor.sol#L353-L358)
- [Chainlink: Using Data Feeds on L2](https://docs.chain.link/data-feeds/l2-sequencer-feeds)
- [Chainlink: Get the Latest Price - Historical Best Practice](https://docs.chain.link/data-feeds/using-data-feeds#check-the-timestamp-of-the-latest-answer)
