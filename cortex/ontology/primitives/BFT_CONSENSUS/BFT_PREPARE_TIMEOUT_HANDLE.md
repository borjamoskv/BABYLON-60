---
id: a22ba71b-ffa4-4eb7-8755-8f695f43df0c
domain: BFT_CONSENSUS
name: "BFT_PREPARE_TIMEOUT_HANDLE"
exergy_cost: 0.5
cortex_taint: CORTEX-TAINT:borjamoskv:batch_crystallize:2026-07-16T16:42:12.004135:54bff63a
---

# BFT_PREPARE_TIMEOUT_HANDLE

## Causal Invariant
```text
ConsensusState transits to VIEW_CHANGE
```

## Description
Handles failure to reach PREPARE quorum.
