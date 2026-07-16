---
id: 1c869e7d-7789-4c7d-85d2-8b6087f3dc80
domain: ASSET_ALLOCATION
name: "AA_ANNIHILATE_MEAN_VARIANCE_FRONTIER"
exergy_cost: 48.5
cortex_taint: CORTEX-TAINT:borjamoskv:batch_crystallize:2026-07-16T16:39:31.363305:b2c70a13
---

# AA_ANNIHILATE_MEAN_VARIANCE_FRONTIER

## Causal Invariant
```text
min w^T \Sigma w s.t. w^T \mu = R^*
```

## Description
Annihilate operation: Solves quadratic programming for minimal variance at target return.
