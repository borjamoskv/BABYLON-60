---
id: 76bee990-dd1f-4c68-8ac2-10940bacd0a7
domain: BFT_CONSENSUS
name: "BFT_CHECKPOINT_VERIFY"
exergy_cost: 2.1
cortex_taint: CORTEX-TAINT:borjamoskv:batch_crystallize:2026-07-16T16:42:12.004135:082b1a7d
---

# BFT_CHECKPOINT_VERIFY

## Causal Invariant
```text
Peer.StateHash == Local.StateHash
```

## Description
Validates peer checkpoint state hash matches local.
