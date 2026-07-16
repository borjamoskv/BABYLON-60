---
id: 6a4a0733-2520-4679-867b-db10139b4e99
domain: BFT_CONSENSUS
name: "BFT_COMMIT_INIT"
exergy_cost: 0.5
cortex_taint: CORTEX-TAINT:borjamoskv:batch_crystallize:2026-07-16T16:42:12.004135:3c2f1ecf
---

# BFT_COMMIT_INIT

## Causal Invariant
```text
Vote.Type == COMMIT AND PrepareQuorum == TRUE
```

## Description
Constructs COMMIT vote after PREPARE quorum.
