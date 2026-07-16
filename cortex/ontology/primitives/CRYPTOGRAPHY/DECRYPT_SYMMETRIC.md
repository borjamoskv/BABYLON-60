---
id: 74e39d68-2413-46c7-b703-22aca645d756
domain: CRYPTOGRAPHY
name: "DECRYPT_SYMMETRIC"
exergy_cost: 2.5
cortex_taint: CORTEX-TAINT:borjamoskv:batch_crystallize:2026-07-16T16:39:25.206640:381f5fab
---

# DECRYPT_SYMMETRIC

## Causal Invariant
```text
P_{payload} = D_k(C_{payload})
```

## Description
Perform symmetric decryption on a ciphertext payload using an established key.
