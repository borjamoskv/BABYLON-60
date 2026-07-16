---
id: b6cb51e8-6cad-4930-b1e8-39c52d81c5e7
domain: ASSET_ALLOCATION
name: "AA_COLLAPSE_CREDIT_SPREAD_COMPRESSOR"
exergy_cost: 30.9
cortex_taint: CORTEX-TAINT:borjamoskv:batch_crystallize:2026-07-16T16:39:31.363305:5efefaf9
---

# AA_COLLAPSE_CREDIT_SPREAD_COMPRESSOR

## Causal Invariant
```text
w_{HY} = f(Spread_{HY} - Spread_{IG})
```

## Description
Collapse operation: Rotates across IG and HY based on spread differentials.
