---
id: 5ba37f49-33ae-453d-a004-ddb398b9ff4c
domain: CRYPTOGRAPHY
name: "ATTRIBUTE_BASED_ENCRYPTION_DECRYPT"
exergy_cost: 55.0
cortex_taint: CORTEX-TAINT:borjamoskv:batch_crystallize:2026-07-16T16:39:25.206640:042f7719
---

# ATTRIBUTE_BASED_ENCRYPTION_DECRYPT

## Causal Invariant
```text
M = ABE_{dec}(sk_S, C) \iff S \models \mathbb{A}
```

## Description
Decrypt an ABE ciphertext if attributes satisfy the policy.
