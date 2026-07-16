---
id: 5f6d3491-0b72-47c7-90be-70649d11dec6
domain: CRYPTOGRAPHY
name: "CIPHER_RC4_UNSAFE"
exergy_cost: 1.0
cortex_taint: CORTEX-TAINT:borjamoskv:batch_crystallize:2026-07-16T16:39:25.206640:16b0ca7c
---

# CIPHER_RC4_UNSAFE

## Causal Invariant
```text
C = RC4_{K}(P)
```

## Description
Encrypt data using RC4 (Unsafe, for legacy support only).
