---
id: eb60e35a-b11b-42c3-be32-e79e6129fb35
domain: BFT_CONSENSUS
name: "BFT_VIEW_CHANGE_BROADCAST"
exergy_cost: 3.2
cortex_taint: CORTEX-TAINT:borjamoskv:batch_crystallize:2026-07-16T16:42:12.004135:3f12f1d0
---

# BFT_VIEW_CHANGE_BROADCAST

## Causal Invariant
```text
VIEW_CHANGE packet added to network outbox
```

## Description
Gossips VIEW_CHANGE to all replicas.
