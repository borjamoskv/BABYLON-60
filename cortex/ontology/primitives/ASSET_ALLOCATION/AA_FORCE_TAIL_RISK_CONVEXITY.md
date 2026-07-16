---
id: 76863dd2-cc1f-42bb-b297-8b342b42e563
domain: ASSET_ALLOCATION
name: "AA_FORCE_TAIL_RISK_CONVEXITY"
exergy_cost: 37.84
cortex_taint: CORTEX-TAINT:borjamoskv:batch_crystallize:2026-07-16T16:39:31.363305:3c516600
---

# AA_FORCE_TAIL_RISK_CONVEXITY

## Causal Invariant
```text
Drawdown_{max} < T
```

## Description
Force operation: Injects OTM put options to truncate left-tail drawdown.
