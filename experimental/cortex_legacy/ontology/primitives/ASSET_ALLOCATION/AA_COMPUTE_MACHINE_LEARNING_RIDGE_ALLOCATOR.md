---
id: b0d6b2a1-41c9-42cb-9c82-67049c5023da
domain: ASSET_ALLOCATION
name: "AA_COMPUTE_MACHINE_LEARNING_RIDGE_ALLOCATOR"
exergy_cost: 17.4
cortex_taint: CORTEX-TAINT:borjamoskv:batch_crystallize:2026-07-16T16:39:31.363305:dbc8f54d
---

# AA_COMPUTE_MACHINE_LEARNING_RIDGE_ALLOCATOR

## Causal Invariant
```text
min ||y - Xw||_2^2 + \lambda ||w||_2^2
```

## Description
Compute operation: Allocates weights via Ridge penalized linear regression on factors.
