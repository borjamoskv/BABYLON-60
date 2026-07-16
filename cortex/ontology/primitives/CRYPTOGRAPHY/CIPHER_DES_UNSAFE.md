---
id: 0a91b284-5d2d-4fbc-93b1-42fb738df27b
domain: CRYPTOGRAPHY
name: "CIPHER_DES_UNSAFE"
exergy_cost: 2.0
cortex_taint: CORTEX-TAINT:borjamoskv:batch_crystallize:2026-07-16T16:39:25.206640:71c7e69c
---

# CIPHER_DES_UNSAFE

## Causal Invariant
```text
C = DES_{K}(P)
```

## Description
Encrypt data using DES (Unsafe, for legacy support only).
