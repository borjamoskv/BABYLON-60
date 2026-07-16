---
id: 6a1d40f4-1e36-4d0f-a5ef-9309236ac881
domain: THERMODYNAMICS
name: "CARNOT_CYCLE_LIMITER"
exergy_cost: 0.1
cortex_taint: CORTEX-TAINT:borjamoskv:batch_crystallize:2026-07-16T16:41:38.421161:ee4ecb42
---

# CARNOT_CYCLE_LIMITER

## Causal Invariant
```text
eta <= 1 - T_c/T_h
```

## Description
Imposes the absolute upper bound on efficiency for any thermodynamic cycle between two reservoirs.
