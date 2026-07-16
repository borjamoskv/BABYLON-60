---
id: 8ce7fda6-0c65-4557-ae9a-4442a8a6ac07
domain: ASSET_ALLOCATION
name: "AA_FORCE_MACHINE_LEARNING_RIDGE_ALLOCATOR"
exergy_cost: 41.52
cortex_taint: CORTEX-TAINT:borjamoskv:batch_crystallize:2026-07-16T16:39:31.363305:8f82bbd5
---

# AA_FORCE_MACHINE_LEARNING_RIDGE_ALLOCATOR

## Causal Invariant
```text
min ||y - Xw||_2^2 + \lambda ||w||_2^2
```

## Description
Force operation: Allocates weights via Ridge penalized linear regression on factors.
