---
id: 06fccd8e-468c-4165-b286-57111569dc3b
domain: CRYPTOGRAPHY
name: "IDENTITY_BASED_ENCRYPTION_DECRYPT"
exergy_cost: 35.0
cortex_taint: CORTEX-TAINT:borjamoskv:batch_crystallize:2026-07-16T16:39:25.206640:85410c13
---

# IDENTITY_BASED_ENCRYPTION_DECRYPT

## Causal Invariant
```text
M = IBE_{dec}(sk_{ID}, C)
```

## Description
Decrypt an IBE ciphertext using the identity's private key.
