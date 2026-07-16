---
id: 045314af-fe20-4602-944c-9313d85d8264
domain: ASSET_ALLOCATION
name: "AA_COMPUTE_MEAN_VARIANCE_FRONTIER"
exergy_cost: 9.53
cortex_taint: CORTEX-TAINT:borjamoskv:batch_crystallize:2026-07-16T16:39:31.363305:d86f7cd9
---

# AA_COMPUTE_MEAN_VARIANCE_FRONTIER

## Causal Invariant
```text
min w^T \Sigma w s.t. w^T \mu = R^*
```

## Description
Compute operation: Solves quadratic programming for minimal variance at target return.
