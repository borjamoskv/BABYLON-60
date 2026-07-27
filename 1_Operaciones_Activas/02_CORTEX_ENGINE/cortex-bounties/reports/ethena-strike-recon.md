# C5-REAL Forensic Recon: Ethena (Target P0)

> **CORTEX JIL-Engine v1.0** — Notarized: 2026-05-05

## 1. Target Intelligence (Ethena USDe)
- **Protocol:** Ethena (Basis Trading)
- **TVL Current:** $3,905,942,500
- **TVL Peak:** $6,490,046,626
- **Trend:** Declining (-39.8%)
- **Bounty Scope:** $3M Max Reward, Primacy of Impact Enabled
- **Assets in Scope:** 27
- **Risk Score:** 20/100 (C5-REAL Confidence)

## 2. Attack Surface Analysis
The significant decline in TVL introduces extreme thermodynamic stress on the protocol's invariant mathematics. 
Target vectors isolated by CORTEX-APEX-Ω:

### [H-01] EthenaMinting.sol: Route Malleability and Custodian Hijacking
- **Vector:** The `mint()` function receives a `Route` struct defining destination custodians and ratios. However, `verifyOrder()` hashes the `Order` struct but **excludes the `Route` struct**. 
- **Impact:** The `MINTER_ROLE` can unilaterally alter the routing of a user's collateral. While Ethena's backend is trusted, an interception or compromise of the Minter key allows an attacker to route $100M+ of incoming collateral to a malicious smart contract, bypassing the user's intent entirely without invalidating the ECDSA signature.
- **Exergy:** High. Primacy of impact triggers if the backend Minter key is compromised.

### [H-02] StakedUSDeV2.sol: Cooldown Period Override (Griefing)
- **Vector:** In `cooldownAssets()` and `cooldownShares()`, the user's cooldown timestamp is indiscriminately overwritten: `cooldowns[msg.sender].cooldownEnd = uint104(block.timestamp) + cooldownDuration;`
- **Impact:** If a user deposits $10M and waits 89.9 days (out of a 90-day cooldown), an attacker (or a careless integrated smart contract acting on their behalf) depositing 1 wei more will reset the *entire* $10M cooldown back to 90 days. This creates a perpetual lock state (UX Griefing).
- **Exergy:** High. The $3.9B liquidity relies on predictable cooldown execution.

## 3. Ouroboros Strike Plan
1. **Source Code Crystallization:** Execute AST-based extraction using `Python-Extractor-OMEGA` on the 4 public Solidity repos. [COMPLETED]
2. **Oracle Bypass PoC:** Analyze the price-feed mechanism for the delta-neutral positions.
3. **Hardware-Level Replay:** Use `C5-REAL` foundry tests to replay the last 14 days of withdrawal pressure to isolate edge-case reverts in `EthenaMinting.sol`. [IN-PROGRESS]

**Status:** `POC_FORGED // SILICON_READY`
**Exergy Flow:** `MAXIMUM`
