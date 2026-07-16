---
id: 046d2ae9-53f2-4779-869f-ae0f21ec1271
domain: ASSET_ALLOCATION
name: "AA_COLLAPSE_FACTOR_MOMENTUM_TILT"
exergy_cost: 41.23
cortex_taint: CORTEX-TAINT:borjamoskv:batch_crystallize:2026-07-16T16:39:31.363305:9f56bc70
---

# AA_COLLAPSE_FACTOR_MOMENTUM_TILT

## Causal Invariant
```text
w_i = f(P_{t-1} / P_{t-12})
```

## Description
Collapse operation: Overweights assets with positive cross-sectional momentum.
