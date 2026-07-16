---
id: a3a4a555-bc76-4ae7-bfe5-7f2355ceab77
domain: ASSET_ALLOCATION
name: "AA_COLLAPSE_MEAN_VARIANCE_FRONTIER"
exergy_cost: 46.09
cortex_taint: CORTEX-TAINT:borjamoskv:batch_crystallize:2026-07-16T16:39:31.363305:a0fd6270
---

# AA_COLLAPSE_MEAN_VARIANCE_FRONTIER

## Causal Invariant
```text
min w^T \Sigma w s.t. w^T \mu = R^*
```

## Description
Collapse operation: Solves quadratic programming for minimal variance at target return.
