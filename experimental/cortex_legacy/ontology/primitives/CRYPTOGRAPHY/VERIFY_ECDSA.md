---
id: 92a983eb-1aca-42a5-8a63-4a7b5156f9fb
domain: CRYPTOGRAPHY
name: "VERIFY_ECDSA"
exergy_cost: 7.0
cortex_taint: CORTEX-TAINT:borjamoskv:batch_crystallize:2026-07-16T16:39:25.206640:60835c64
---

# VERIFY_ECDSA

## Causal Invariant
```text
b = Verify_{K_{pub}}(H(M), \sigma) \in \{0,1\}
```

## Description
Verify an ECDSA digital signature for a message hash using a public key.
