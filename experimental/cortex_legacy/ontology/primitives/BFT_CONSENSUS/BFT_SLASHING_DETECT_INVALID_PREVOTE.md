---
id: 2cbb82be-4a28-439f-a4ea-6a19c671b2a2
domain: BFT_CONSENSUS
name: "BFT_SLASHING_DETECT_INVALID_PREVOTE"
exergy_cost: 1.2
cortex_taint: CORTEX-TAINT:borjamoskv:batch_crystallize:2026-07-16T16:42:12.004135:42817f94
---

# BFT_SLASHING_DETECT_INVALID_PREVOTE

## Causal Invariant
```text
Vote references non-existent or invalid block
```

## Description
Finds prepare vote without valid proposal.
