---
id: 561d082b-f262-4e2f-9d13-a375e5c9e933
domain: CRYPTOGRAPHY
name: "ATTRIBUTE_BASED_ENCRYPTION_KEYGEN"
exergy_cost: 50.0
cortex_taint: CORTEX-TAINT:borjamoskv:batch_crystallize:2026-07-16T16:39:25.206640:c08586ec
---

# ATTRIBUTE_BASED_ENCRYPTION_KEYGEN

## Causal Invariant
```text
sk_{S} = ABE_{keygen}(MSK, S)
```

## Description
Generate a private key for a set of attributes in ABE.
