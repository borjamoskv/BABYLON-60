---
id: 2e42c325-587d-4a13-af34-dbcd2bc96236
domain: ASSET_ALLOCATION
name: "AA_TRANSDUCE_MEAN_VARIANCE_FRONTIER"
exergy_cost: 32.49
cortex_taint: CORTEX-TAINT:borjamoskv:batch_crystallize:2026-07-16T16:39:31.363305:32801d40
---

# AA_TRANSDUCE_MEAN_VARIANCE_FRONTIER

## Causal Invariant
```text
min w^T \Sigma w s.t. w^T \mu = R^*
```

## Description
Transduce operation: Solves quadratic programming for minimal variance at target return.
