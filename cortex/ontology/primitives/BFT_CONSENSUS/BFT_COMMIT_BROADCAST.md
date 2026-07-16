---
id: 19ea6499-cbce-462d-8878-29520b1dd3a4
domain: BFT_CONSENSUS
name: "BFT_COMMIT_BROADCAST"
exergy_cost: 3.2
cortex_taint: CORTEX-TAINT:borjamoskv:batch_crystallize:2026-07-16T16:42:12.004135:04f3db2e
---

# BFT_COMMIT_BROADCAST

## Causal Invariant
```text
Egress queue receives N-1 COMMIT packets
```

## Description
Transmits COMMIT vote to network.
