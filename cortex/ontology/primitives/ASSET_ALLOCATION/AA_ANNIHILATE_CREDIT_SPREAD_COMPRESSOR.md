---
id: 79d808e4-71fb-439d-9980-6ad1ac1ae57f
domain: ASSET_ALLOCATION
name: "AA_ANNIHILATE_CREDIT_SPREAD_COMPRESSOR"
exergy_cost: 18.06
cortex_taint: CORTEX-TAINT:borjamoskv:batch_crystallize:2026-07-16T16:39:31.363305:8064b901
---

# AA_ANNIHILATE_CREDIT_SPREAD_COMPRESSOR

## Causal Invariant
```text
w_{HY} = f(Spread_{HY} - Spread_{IG})
```

## Description
Annihilate operation: Rotates across IG and HY based on spread differentials.
