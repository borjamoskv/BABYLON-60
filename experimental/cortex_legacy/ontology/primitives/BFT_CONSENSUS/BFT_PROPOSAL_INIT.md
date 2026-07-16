---
id: 25993e8d-48d6-4fa3-bdb1-5dc86f681159
domain: BFT_CONSENSUS
name: "BFT_PROPOSAL_INIT"
exergy_cost: 2.5
cortex_taint: CORTEX-TAINT:borjamoskv:batch_crystallize:2026-07-16T16:42:12.004135:6e1c56ec
---

# BFT_PROPOSAL_INIT

## Causal Invariant
```text
Payload length > 0 AND Height == PrevHeight + 1
```

## Description
Constructs initial block payload from deterministic mempool DAG.
