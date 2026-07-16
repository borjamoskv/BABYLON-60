---
id: 5ce437af-3c64-4014-9eda-e8051757d8e8
domain: CRYPTOGRAPHY
name: "VERIFY_EDDSA"
exergy_cost: 5.0
cortex_taint: CORTEX-TAINT:borjamoskv:batch_crystallize:2026-07-16T16:39:25.206640:084762a9
---

# VERIFY_EDDSA

## Causal Invariant
```text
b = Verify_{K_{pub}}(M, \sigma) \in \{0,1\}
```

## Description
Verify an EdDSA digital signature for a message using a public key.
