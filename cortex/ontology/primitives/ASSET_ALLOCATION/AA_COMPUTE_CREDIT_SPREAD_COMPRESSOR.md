---
id: 331ffa85-b063-4fa7-b318-4f7b716a88e3
domain: ASSET_ALLOCATION
name: "AA_COMPUTE_CREDIT_SPREAD_COMPRESSOR"
exergy_cost: 25.02
cortex_taint: CORTEX-TAINT:borjamoskv:batch_crystallize:2026-07-16T16:39:31.363305:46192ebb
---

# AA_COMPUTE_CREDIT_SPREAD_COMPRESSOR

## Causal Invariant
```text
w_{HY} = f(Spread_{HY} - Spread_{IG})
```

## Description
Compute operation: Rotates across IG and HY based on spread differentials.
