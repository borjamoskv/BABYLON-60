---
id: f56ab9a5-0e21-4815-9e19-885b6c83b060
domain: BFT_CONSENSUS
name: "BFT_CHECKPOINT_STORE"
exergy_cost: 1.2
cortex_taint: CORTEX-TAINT:borjamoskv:batch_crystallize:2026-07-16T16:42:12.004135:1a3fad41
---

# BFT_CHECKPOINT_STORE

## Causal Invariant
```text
CheckpointMap[Height][PeerId] == Signature
```

## Description
Records verified checkpoint signature.
