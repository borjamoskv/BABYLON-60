---
id: b0841f4c-f95d-4d75-9107-a516589ea7f0
domain: ASSET_ALLOCATION
name: "AA_COLLAPSE_TAIL_RISK_CONVEXITY"
exergy_cost: 35.78
cortex_taint: CORTEX-TAINT:borjamoskv:batch_crystallize:2026-07-16T16:39:31.363305:c0b0854b
---

# AA_COLLAPSE_TAIL_RISK_CONVEXITY

## Causal Invariant
```text
Drawdown_{max} < T
```

## Description
Collapse operation: Injects OTM put options to truncate left-tail drawdown.
