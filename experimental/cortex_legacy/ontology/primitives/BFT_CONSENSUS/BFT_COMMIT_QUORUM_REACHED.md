---
id: 86027ef7-38bb-4396-a81b-3784c998f65b
domain: BFT_CONSENSUS
name: "BFT_COMMIT_QUORUM_REACHED"
exergy_cost: 0.3
cortex_taint: CORTEX-TAINT:borjamoskv:batch_crystallize:2026-07-16T16:42:12.004135:179114ad
---

# BFT_COMMIT_QUORUM_REACHED

## Causal Invariant
```text
Block.Status transits to FINALIZED
```

## Description
Flags block as finalized.
