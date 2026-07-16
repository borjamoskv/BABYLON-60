---
id: 766aeff8-bd10-4784-893d-f5e327cc4f24
domain: ASSET_ALLOCATION
name: "AA_COMPUTE_COVARIANCE_MATRIX_SHRINKAGE"
exergy_cost: 46.98
cortex_taint: CORTEX-TAINT:borjamoskv:batch_crystallize:2026-07-16T16:39:31.363305:9aa89bbd
---

# AA_COMPUTE_COVARIANCE_MATRIX_SHRINKAGE

## Causal Invariant
```text
\Sigma_{LW} = \delta F + (1-\delta) S
```

## Description
Compute operation: Regularizes sample covariance using Ledoit-Wolf shrinkage.
