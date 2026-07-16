---
id: 656d5742-f6a0-4ba2-90f8-459fd74ef17b
domain: ASSET_ALLOCATION
name: "AA_COMPUTE_MAX_DRAWDOWN_CIRCUIT_BREAKER"
exergy_cost: 41.14
cortex_taint: CORTEX-TAINT:borjamoskv:batch_crystallize:2026-07-16T16:39:31.363305:fb12649c
---

# AA_COMPUTE_MAX_DRAWDOWN_CIRCUIT_BREAKER

## Causal Invariant
```text
if W_t <= L: W_{t+1} = Cash
```

## Description
Compute operation: Liquidates all risk positions if terminal wealth hits threshold.
