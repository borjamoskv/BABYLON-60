---
id: bd6db939-4ee4-497a-8061-7a820a6e28c1
domain: CRYPTOGRAPHY
name: "KEY_DERIVATION_SCRYPT"
exergy_cost: 50.0
cortex_taint: CORTEX-TAINT:borjamoskv:batch_crystallize:2026-07-16T16:39:25.206640:33fe6872
---

# KEY_DERIVATION_SCRYPT

## Causal Invariant
```text
K = scrypt(P, S, N, r, p, L)
```

## Description
Derive a key from a password using scrypt.
