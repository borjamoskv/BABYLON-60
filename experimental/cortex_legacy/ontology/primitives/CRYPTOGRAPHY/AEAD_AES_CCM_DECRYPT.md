---
id: a3ff8132-61a3-4a38-ad98-dbaa77f7a4ea
domain: CRYPTOGRAPHY
name: "AEAD_AES_CCM_DECRYPT"
exergy_cost: 3.5
cortex_taint: CORTEX-TAINT:borjamoskv:batch_crystallize:2026-07-16T16:39:25.206640:03cde3c8
---

# AEAD_AES_CCM_DECRYPT

## Causal Invariant
```text
P = AES\_CCM_{dec}(K, N, C, AAD, T) \lor \bot
```

## Description
Decrypt and verify authenticated data using AES-CCM.
