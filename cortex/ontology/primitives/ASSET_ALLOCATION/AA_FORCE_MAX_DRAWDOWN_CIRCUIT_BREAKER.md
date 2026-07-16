---
id: d574c280-50a2-4981-a514-9c10704cc9a9
domain: ASSET_ALLOCATION
name: "AA_FORCE_MAX_DRAWDOWN_CIRCUIT_BREAKER"
exergy_cost: 25.16
cortex_taint: CORTEX-TAINT:borjamoskv:batch_crystallize:2026-07-16T16:39:31.363305:f48188cd
---

# AA_FORCE_MAX_DRAWDOWN_CIRCUIT_BREAKER

## Causal Invariant
```text
if W_t <= L: W_{t+1} = Cash
```

## Description
Force operation: Liquidates all risk positions if terminal wealth hits threshold.
