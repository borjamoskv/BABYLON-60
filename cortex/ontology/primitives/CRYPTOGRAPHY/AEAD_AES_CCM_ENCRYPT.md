---
id: 415f6ab3-07c6-42fd-9db4-70adeceaf368
domain: CRYPTOGRAPHY
name: "AEAD_AES_CCM_ENCRYPT"
exergy_cost: 3.5
cortex_taint: CORTEX-TAINT:borjamoskv:batch_crystallize:2026-07-16T16:39:25.206640:7a403108
---

# AEAD_AES_CCM_ENCRYPT

## Causal Invariant
```text
(C, T) = AES\_CCM_{enc}(K, N, P, AAD)
```

## Description
Encrypt and authenticate data using AES-CCM.
