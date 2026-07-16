---
id: 024f013a-d639-44a5-b3f4-a639058b61fd
domain: ASSET_ALLOCATION
name: "AA_TRANSDUCE_MACHINE_LEARNING_RIDGE_ALLOCATOR"
exergy_cost: 43.23
cortex_taint: CORTEX-TAINT:borjamoskv:batch_crystallize:2026-07-16T16:39:31.363305:15ffa251
---

# AA_TRANSDUCE_MACHINE_LEARNING_RIDGE_ALLOCATOR

## Causal Invariant
```text
min ||y - Xw||_2^2 + \lambda ||w||_2^2
```

## Description
Transduce operation: Allocates weights via Ridge penalized linear regression on factors.
