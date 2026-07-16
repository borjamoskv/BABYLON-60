---
id: 661f6a05-3a1f-4e8c-a484-8ae0c6328fb1
domain: CRYPTOGRAPHY
name: "KEY_DERIVATION_ARGON2"
exergy_cost: 60.0
cortex_taint: CORTEX-TAINT:borjamoskv:batch_crystallize:2026-07-16T16:39:25.206640:712c268f
---

# KEY_DERIVATION_ARGON2

## Causal Invariant
```text
K = Argon2(P, S, t, m, p, L)
```

## Description
Derive a key from a password using Argon2.
