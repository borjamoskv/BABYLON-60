---
id: 6674d74e-baa2-4b89-a2a1-9cbe6a40f387
domain: CRYPTOGRAPHY
name: "AEAD_AES_GCM_DECRYPT"
exergy_cost: 3.0
cortex_taint: CORTEX-TAINT:borjamoskv:batch_crystallize:2026-07-16T16:39:25.206640:1bccf08a
---

# AEAD_AES_GCM_DECRYPT

## Causal Invariant
```text
P = AES\_GCM_{dec}(K, IV, C, AAD, T) \lor \bot
```

## Description
Decrypt and verify authenticated data using AES-GCM.
