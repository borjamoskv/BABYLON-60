---
id: fba6b97d-0ba1-408f-b846-34837c6b7a5a
domain: ASSET_ALLOCATION
name: "AA_TRANSDUCE_MAX_DRAWDOWN_CIRCUIT_BREAKER"
exergy_cost: 8.62
cortex_taint: CORTEX-TAINT:borjamoskv:batch_crystallize:2026-07-16T16:39:31.363305:acf0fe97
---

# AA_TRANSDUCE_MAX_DRAWDOWN_CIRCUIT_BREAKER

## Causal Invariant
```text
if W_t <= L: W_{t+1} = Cash
```

## Description
Transduce operation: Liquidates all risk positions if terminal wealth hits threshold.
