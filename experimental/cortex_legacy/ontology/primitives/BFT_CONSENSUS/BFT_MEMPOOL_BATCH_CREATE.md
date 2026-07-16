---
id: 21b09f07-8433-42fd-8c36-a2a378965eec
domain: BFT_CONSENSUS
name: "BFT_MEMPOOL_BATCH_CREATE"
exergy_cost: 2.5
cortex_taint: CORTEX-TAINT:borjamoskv:batch_crystallize:2026-07-16T16:42:12.004135:5b726875
---

# BFT_MEMPOOL_BATCH_CREATE

## Causal Invariant
```text
Batch size <= MaxBlockSize
```

## Description
Aggregates Txs into execution batch.
