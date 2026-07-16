---
id: edafef64-7307-4ea8-8b87-a8cec67356b3
domain: ASSET_ALLOCATION
name: "AA_ANNIHILATE_MAX_DRAWDOWN_CIRCUIT_BREAKER"
exergy_cost: 27.86
cortex_taint: CORTEX-TAINT:borjamoskv:batch_crystallize:2026-07-16T16:39:31.363305:deec1f00
---

# AA_ANNIHILATE_MAX_DRAWDOWN_CIRCUIT_BREAKER

## Causal Invariant
```text
if W_t <= L: W_{t+1} = Cash
```

## Description
Annihilate operation: Liquidates all risk positions if terminal wealth hits threshold.
