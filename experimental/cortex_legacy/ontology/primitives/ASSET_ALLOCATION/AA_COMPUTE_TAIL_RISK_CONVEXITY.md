---
id: a4223c10-81e5-4be9-a22a-ac05938e5c01
domain: ASSET_ALLOCATION
name: "AA_COMPUTE_TAIL_RISK_CONVEXITY"
exergy_cost: 18.96
cortex_taint: CORTEX-TAINT:borjamoskv:batch_crystallize:2026-07-16T16:39:31.363305:95b6419f
---

# AA_COMPUTE_TAIL_RISK_CONVEXITY

## Causal Invariant
```text
Drawdown_{max} < T
```

## Description
Compute operation: Injects OTM put options to truncate left-tail drawdown.
