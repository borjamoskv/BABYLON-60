---
id: 06f8ba64-6d35-4b3c-8432-27713b67ff15
domain: CRYPTOGRAPHY
name: "AEAD_CHACHA20_POLY1305_ENCRYPT"
exergy_cost: 2.5
cortex_taint: CORTEX-TAINT:borjamoskv:batch_crystallize:2026-07-16T16:39:25.206640:dec27ef6
---

# AEAD_CHACHA20_POLY1305_ENCRYPT

## Causal Invariant
```text
(C, T) = ChaCha20Poly1305_{enc}(K, N, P, AAD)
```

## Description
Encrypt and authenticate data using ChaCha20-Poly1305.
