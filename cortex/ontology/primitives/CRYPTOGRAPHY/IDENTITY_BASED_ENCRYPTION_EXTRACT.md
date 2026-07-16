---
id: 8c45ce01-2cc2-4a3b-b621-a8b2e0867fc1
domain: CRYPTOGRAPHY
name: "IDENTITY_BASED_ENCRYPTION_EXTRACT"
exergy_cost: 40.0
cortex_taint: CORTEX-TAINT:borjamoskv:batch_crystallize:2026-07-16T16:39:25.206640:2d8aeff4
---

# IDENTITY_BASED_ENCRYPTION_EXTRACT

## Causal Invariant
```text
sk_{ID} = IBE_{extract}(MSK, ID)
```

## Description
Extract a private key for an identity in IBE.
