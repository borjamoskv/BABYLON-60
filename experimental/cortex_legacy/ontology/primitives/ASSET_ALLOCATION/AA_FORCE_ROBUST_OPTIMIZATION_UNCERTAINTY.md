---
id: fdd8105d-0030-4d4f-8854-b49e41981099
domain: ASSET_ALLOCATION
name: "AA_FORCE_ROBUST_OPTIMIZATION_UNCERTAINTY"
exergy_cost: 40.7
cortex_taint: CORTEX-TAINT:borjamoskv:batch_crystallize:2026-07-16T16:39:31.363305:21efb600
---

# AA_FORCE_ROBUST_OPTIMIZATION_UNCERTAINTY

## Causal Invariant
```text
max_w min_{\Sigma \in U} w^T \Sigma w
```

## Description
Force operation: Minmax allocation against worst-case covariance ellipse.
