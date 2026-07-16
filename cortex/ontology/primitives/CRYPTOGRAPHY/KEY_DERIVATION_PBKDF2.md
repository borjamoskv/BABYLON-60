---
id: 86f2eb88-cb2d-478e-9887-827c104e1377
domain: CRYPTOGRAPHY
name: "KEY_DERIVATION_PBKDF2"
exergy_cost: 25.0
cortex_taint: CORTEX-TAINT:borjamoskv:batch_crystallize:2026-07-16T16:39:25.206640:a7817e2a
---

# KEY_DERIVATION_PBKDF2

## Causal Invariant
```text
K = PBKDF2(P, S, c, L)
```

## Description
Derive a key from a password using PBKDF2.
