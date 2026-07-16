---
id: c3aec8bd-88cb-4b9b-904d-d5258223d002
domain: ASSET_ALLOCATION
name: "AA_TRANSDUCE_TAIL_RISK_CONVEXITY"
exergy_cost: 45.45
cortex_taint: CORTEX-TAINT:borjamoskv:batch_crystallize:2026-07-16T16:39:31.363305:e6919601
---

# AA_TRANSDUCE_TAIL_RISK_CONVEXITY

## Causal Invariant
```text
Drawdown_{max} < T
```

## Description
Transduce operation: Injects OTM put options to truncate left-tail drawdown.
