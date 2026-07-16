---
id: e41bded0-7d77-46e0-9bff-495e6872b9d6
domain: CRYPTOGRAPHY
name: "SECURE_MULTIPARTY_COMPUTATION_STEP"
exergy_cost: 100.0
cortex_taint: CORTEX-TAINT:borjamoskv:batch_crystallize:2026-07-16T16:39:25.206640:72bc92bb
---

# SECURE_MULTIPARTY_COMPUTATION_STEP

## Causal Invariant
```text
S_{i+1} = MPC_{step}(S_i, m_{in})
```

## Description
Execute a step in an MPC protocol.
