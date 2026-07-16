---
id: 924f4f4a-0d9b-429f-a98a-06bf284e3b0e
domain: BFT_CONSENSUS
name: "BFT_MEMPOOL_GARBAGE_COLLECT"
exergy_cost: 4.5
cortex_taint: CORTEX-TAINT:borjamoskv:batch_crystallize:2026-07-16T16:42:12.004135:86d50819
---

# BFT_MEMPOOL_GARBAGE_COLLECT

## Causal Invariant
```text
Mempool memory footprint reduced
```

## Description
Removes expired or committed Txs from mempool.
