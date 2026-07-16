---
id: 7478a3e3-d214-4bdb-a7a1-74f5761dee23
domain: ASSET_ALLOCATION
name: "AA_COLLAPSE_MACHINE_LEARNING_RIDGE_ALLOCATOR"
exergy_cost: 45.28
cortex_taint: CORTEX-TAINT:borjamoskv:batch_crystallize:2026-07-16T16:39:31.363305:4372db94
---

# AA_COLLAPSE_MACHINE_LEARNING_RIDGE_ALLOCATOR

## Causal Invariant
```text
min ||y - Xw||_2^2 + \lambda ||w||_2^2
```

## Description
Collapse operation: Allocates weights via Ridge penalized linear regression on factors.
