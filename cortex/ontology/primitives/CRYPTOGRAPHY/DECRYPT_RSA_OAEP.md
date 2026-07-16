---
id: 0b06d273-965d-441c-b8e8-75a3ce747053
domain: CRYPTOGRAPHY
name: "DECRYPT_RSA_OAEP"
exergy_cost: 25.0
cortex_taint: CORTEX-TAINT:borjamoskv:batch_crystallize:2026-07-16T16:39:25.206640:56b7c35e
---

# DECRYPT_RSA_OAEP

## Causal Invariant
```text
P = RSA\_Dec_{OAEP}(sk, C) \lor \bot
```

## Description
Decrypt data using RSA with OAEP padding.
