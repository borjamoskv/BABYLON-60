---
id: d778c897-8e52-40fc-b52e-b3d2a84bc569
domain: ASSET_ALLOCATION
name: "AA_FORCE_CREDIT_SPREAD_COMPRESSOR"
exergy_cost: 31.83
cortex_taint: CORTEX-TAINT:borjamoskv:batch_crystallize:2026-07-16T16:39:31.363305:0ff82a43
---

# AA_FORCE_CREDIT_SPREAD_COMPRESSOR

## Causal Invariant
```text
w_{HY} = f(Spread_{HY} - Spread_{IG})
```

## Description
Force operation: Rotates across IG and HY based on spread differentials.
