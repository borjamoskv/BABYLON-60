---
id: 3e92d108-879e-4be5-ab0b-e39870603112
domain: ASSET_ALLOCATION
name: "AA_ANNIHILATE_TAIL_RISK_CONVEXITY"
exergy_cost: 26.25
cortex_taint: CORTEX-TAINT:borjamoskv:batch_crystallize:2026-07-16T16:39:31.363305:31077227
---

# AA_ANNIHILATE_TAIL_RISK_CONVEXITY

## Causal Invariant
```text
Drawdown_{max} < T
```

## Description
Annihilate operation: Injects OTM put options to truncate left-tail drawdown.
