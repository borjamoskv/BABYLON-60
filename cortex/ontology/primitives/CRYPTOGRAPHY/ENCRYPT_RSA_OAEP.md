---
id: 8ccf2ebe-3c38-47a2-9351-7f3246485c87
domain: CRYPTOGRAPHY
name: "ENCRYPT_RSA_OAEP"
exergy_cost: 10.0
cortex_taint: CORTEX-TAINT:borjamoskv:batch_crystallize:2026-07-16T16:39:25.206640:974ad4c9
---

# ENCRYPT_RSA_OAEP

## Causal Invariant
```text
C = RSA\_Enc_{OAEP}(pk, P)
```

## Description
Encrypt data using RSA with OAEP padding.
