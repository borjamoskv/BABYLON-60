---
id: 1b3cf3dc-b591-48bf-87c8-194629fd172c
domain: CRYPTOGRAPHY
name: "SIGN_EDDSA"
exergy_cost: 4.0
cortex_taint: CORTEX-TAINT:borjamoskv:batch_crystallize:2026-07-16T16:39:25.206640:d96ff1ec
---

# SIGN_EDDSA

## Causal Invariant
```text
\sigma = Sign_{K_{priv}}(M)
```

## Description
Generate an EdDSA digital signature for a message using a private key.
