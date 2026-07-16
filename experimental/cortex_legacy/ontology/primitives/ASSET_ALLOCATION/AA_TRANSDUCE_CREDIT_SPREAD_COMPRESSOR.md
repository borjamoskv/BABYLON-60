---
id: 0e252f4e-d936-49b0-b3b5-5524a18a3cfa
domain: ASSET_ALLOCATION
name: "AA_TRANSDUCE_CREDIT_SPREAD_COMPRESSOR"
exergy_cost: 22.32
cortex_taint: CORTEX-TAINT:borjamoskv:batch_crystallize:2026-07-16T16:39:31.363305:2b3c3f7c
---

# AA_TRANSDUCE_CREDIT_SPREAD_COMPRESSOR

## Causal Invariant
```text
w_{HY} = f(Spread_{HY} - Spread_{IG})
```

## Description
Transduce operation: Rotates across IG and HY based on spread differentials.
