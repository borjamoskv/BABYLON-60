---
id: 127bb57f-f04d-4375-a51e-238bc8954e51
domain: ASSET_ALLOCATION
name: "AA_COMPUTE_FACTOR_MOMENTUM_TILT"
exergy_cost: 26.47
cortex_taint: CORTEX-TAINT:borjamoskv:batch_crystallize:2026-07-16T16:39:31.363305:13d5267a
---

# AA_COMPUTE_FACTOR_MOMENTUM_TILT

## Causal Invariant
```text
w_i = f(P_{t-1} / P_{t-12})
```

## Description
Compute operation: Overweights assets with positive cross-sectional momentum.
