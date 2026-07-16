---
id: 876fc9e4-aaca-496a-be92-9c5beba8f6c0
domain: CRYPTOGRAPHY
name: "DECRYPT_ASYMMETRIC"
exergy_cost: 12.0
cortex_taint: CORTEX-TAINT:borjamoskv:batch_crystallize:2026-07-16T16:39:25.206640:1ad3e90a
---

# DECRYPT_ASYMMETRIC

## Causal Invariant
```text
P = D_{K_{priv}}(C)
```

## Description
Decrypt a ciphertext payload using the corresponding private key.
