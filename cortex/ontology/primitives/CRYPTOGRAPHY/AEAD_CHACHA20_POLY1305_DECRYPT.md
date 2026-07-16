---
id: 9e2b56b2-33f2-4fe3-839c-cbaf23e454e0
domain: CRYPTOGRAPHY
name: "AEAD_CHACHA20_POLY1305_DECRYPT"
exergy_cost: 2.5
cortex_taint: CORTEX-TAINT:borjamoskv:batch_crystallize:2026-07-16T16:39:25.206640:d4400d66
---

# AEAD_CHACHA20_POLY1305_DECRYPT

## Causal Invariant
```text
P = ChaCha20Poly1305_{dec}(K, N, C, AAD, T) \lor \bot
```

## Description
Decrypt and verify authenticated data using ChaCha20-Poly1305.
