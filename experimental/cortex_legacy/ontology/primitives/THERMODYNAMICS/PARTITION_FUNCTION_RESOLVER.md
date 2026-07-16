---
id: cb28a400-e9f8-4416-9e62-3b6983e56c73
domain: THERMODYNAMICS
name: "PARTITION_FUNCTION_RESOLVER"
exergy_cost: 4.0
cortex_taint: CORTEX-TAINT:borjamoskv:batch_crystallize:2026-07-16T16:41:38.421161:de1aa2b5
---

# PARTITION_FUNCTION_RESOLVER

## Causal Invariant
```text
Z = sum(exp(-E_i/kT))
```

## Description
Sums over all microstates to normalize probabilities and derive macroscopic properties.
