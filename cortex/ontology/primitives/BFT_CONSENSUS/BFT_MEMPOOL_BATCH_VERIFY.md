---
id: b8bb83bf-3afc-4251-9d5d-f638808a85ea
domain: BFT_CONSENSUS
name: "BFT_MEMPOOL_BATCH_VERIFY"
exergy_cost: 3.0
cortex_taint: CORTEX-TAINT:borjamoskv:batch_crystallize:2026-07-16T16:42:12.004135:8d578f6d
---

# BFT_MEMPOOL_BATCH_VERIFY

## Causal Invariant
```text
All batch Txs topologically sorted
```

## Description
Checks batch integrity against current DAG state.
