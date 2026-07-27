# Submission Manifest: HIGH: Stale Oracle Price Feed on L2 (Optimism) due to lack of Staleness and Sequencer Uptime Checks
ID: exactly_stale_oracle_l2
Status: VERIFIED
Severity: High

## Vulnerability

Exactly Protocol's `Auditor.sol:assetPrice()` uses deprecated `latestAnswer()` from Chainlink without staleness validation, round completeness checks, or L2 sequencer uptime verification. The `IPriceFeed` interface structurally prevents staleness checks. Deployed on Optimism with $3.3M TVL exposure.

**Root Cause:** `contracts/Auditor.sol` L353-358 — `priceFeed.latestAnswer()` called without `updatedAt` timestamp validation.

**Impact:** Direct fund loss via undercollateralized borrowing during L2 sequencer downtime events. Estimated max extractable: $330K per staleness event.

**PoC:** Foundry fork test against Optimism mainnet deployment `0xaEb62e6F27BC103702E7BC879AE98bceA56f027E` confirms `assetPrice()` returns values without staleness guard.

**Contract:** Auditor (0xaEb62e6F27BC103702E7BC879AE98bceA56f027E) — Optimism

[FORENSIC DATA ATTACHED]
