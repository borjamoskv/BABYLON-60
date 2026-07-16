---
id: 0ec3920f-71ed-47ff-adef-1f56593d3eed
domain: ASSET_ALLOCATION
name: "AA_FORCE_MEAN_VARIANCE_FRONTIER"
exergy_cost: 24.54
cortex_taint: CORTEX-TAINT:borjamoskv:batch_crystallize:2026-07-16T16:39:31.363305:6fae1ca8
---

# AA_FORCE_MEAN_VARIANCE_FRONTIER

## Causal Invariant
```text
min w^T \Sigma w s.t. w^T \mu = R^*
```

## Description
Force operation: Solves quadratic programming for minimal variance at target return.
