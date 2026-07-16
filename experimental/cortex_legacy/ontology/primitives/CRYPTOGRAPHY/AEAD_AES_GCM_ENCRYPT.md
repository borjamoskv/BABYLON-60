---
id: dadcde26-04b3-4329-8ff1-14f135082c66
domain: CRYPTOGRAPHY
name: "AEAD_AES_GCM_ENCRYPT"
exergy_cost: 3.0
cortex_taint: CORTEX-TAINT:borjamoskv:batch_crystallize:2026-07-16T16:39:25.206640:ad2eba41
---

# AEAD_AES_GCM_ENCRYPT

## Causal Invariant
```text
(C, T) = AES\_GCM_{enc}(K, IV, P, AAD)
```

## Description
Encrypt and authenticate data using AES-GCM.
