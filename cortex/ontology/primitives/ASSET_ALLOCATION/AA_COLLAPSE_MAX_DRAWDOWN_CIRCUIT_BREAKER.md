---
id: 5c90197b-9553-4b6f-a28c-050a920c9bea
domain: ASSET_ALLOCATION
name: "AA_COLLAPSE_MAX_DRAWDOWN_CIRCUIT_BREAKER"
exergy_cost: 19.4
cortex_taint: CORTEX-TAINT:borjamoskv:batch_crystallize:2026-07-16T16:39:31.363305:55e49f56
---

# AA_COLLAPSE_MAX_DRAWDOWN_CIRCUIT_BREAKER

## Causal Invariant
```text
if W_t <= L: W_{t+1} = Cash
```

## Description
Collapse operation: Liquidates all risk positions if terminal wealth hits threshold.
