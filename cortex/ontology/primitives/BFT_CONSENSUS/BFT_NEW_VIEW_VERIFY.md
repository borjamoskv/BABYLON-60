---
id: 4d8989a2-5e98-4c85-962c-c97ad69c5225
domain: BFT_CONSENSUS
name: "BFT_NEW_VIEW_VERIFY"
exergy_cost: 4.5
cortex_taint: CORTEX-TAINT:borjamoskv:batch_crystallize:2026-07-16T16:42:12.004135:bf5b989a
---

# BFT_NEW_VIEW_VERIFY

## Causal Invariant
```text
Local.View == Leader.NewView
```

## Description
Replicas cryptographically verify NEW_VIEW aggregation.
