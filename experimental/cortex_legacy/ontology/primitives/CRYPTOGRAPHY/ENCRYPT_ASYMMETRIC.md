---
id: 8d1d34bc-734a-4edb-b65b-c826f0a67f9d
domain: CRYPTOGRAPHY
name: "ENCRYPT_ASYMMETRIC"
exergy_cost: 8.0
cortex_taint: CORTEX-TAINT:borjamoskv:batch_crystallize:2026-07-16T16:39:25.206640:50839d4a
---

# ENCRYPT_ASYMMETRIC

## Causal Invariant
```text
C = E_{K_{pub}}(P)
```

## Description
Encrypt a plaintext payload using a recipient's public key.
