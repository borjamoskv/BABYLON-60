---
id: f1e8c605-05c9-4131-b00c-86e509aa3c52
domain: BFT_CONSENSUS
name: "BFT_PREPARE_STORE_VOTE"
exergy_cost: 1.2
cortex_taint: CORTEX-TAINT:borjamoskv:batch_crystallize:2026-07-16T16:42:12.004135:0b094dca
---

# BFT_PREPARE_STORE_VOTE

## Causal Invariant
```text
PrepareMap[PeerId] == Vote
```

## Description
Persists verified PREPARE vote to local memory.
