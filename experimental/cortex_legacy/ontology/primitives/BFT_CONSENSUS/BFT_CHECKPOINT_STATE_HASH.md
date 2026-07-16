---
id: e8487bec-f9c7-488a-9214-54c9c7a9b81f
domain: BFT_CONSENSUS
name: "BFT_CHECKPOINT_STATE_HASH"
exergy_cost: 12.0
cortex_taint: CORTEX-TAINT:borjamoskv:batch_crystallize:2026-07-16T16:42:12.004135:fcd68b75
---

# BFT_CHECKPOINT_STATE_HASH

## Causal Invariant
```text
StateHash reflects exact VM state at Height
```

## Description
Computes Merkle root of entire state at checkpoint.
