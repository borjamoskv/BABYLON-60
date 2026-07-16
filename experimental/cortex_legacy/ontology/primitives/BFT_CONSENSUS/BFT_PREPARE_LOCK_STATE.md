---
id: 80b244af-12e8-4b2e-b4ed-a692100a54c6
domain: BFT_CONSENSUS
name: "BFT_PREPARE_LOCK_STATE"
exergy_cost: 0.8
cortex_taint: CORTEX-TAINT:borjamoskv:batch_crystallize:2026-07-16T16:42:12.004135:160f3e65
---

# BFT_PREPARE_LOCK_STATE

## Causal Invariant
```text
Local.LockedHash == Proposal.Hash
```

## Description
Locks replica to specific block hash.
