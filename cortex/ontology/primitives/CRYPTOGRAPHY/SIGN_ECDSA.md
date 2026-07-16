---
id: 0740c46c-a697-4d11-93de-9a3a23717b55
domain: CRYPTOGRAPHY
name: "SIGN_ECDSA"
exergy_cost: 6.0
cortex_taint: CORTEX-TAINT:borjamoskv:batch_crystallize:2026-07-16T16:39:25.206640:430fa249
---

# SIGN_ECDSA

## Causal Invariant
```text
\sigma = Sign_{K_{priv}}(H(M))
```

## Description
Generate an ECDSA digital signature for a message hash using a private key.
