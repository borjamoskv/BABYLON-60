---
id: 33e34570-bca1-4545-9e69-a8bb67a1d30e
domain: BFT_CONSENSUS
name: "BFT_PREPARE_CHECK_QUORUM"
exergy_cost: 0.4
cortex_taint: CORTEX-TAINT:borjamoskv:batch_crystallize:2026-07-16T16:42:12.004135:3fc2a55e
---

# BFT_PREPARE_CHECK_QUORUM

## Causal Invariant
```text
Count(PrepareMap) >= 2f + 1
```

## Description
Evaluates if PREPARE votes exceed 2f.
