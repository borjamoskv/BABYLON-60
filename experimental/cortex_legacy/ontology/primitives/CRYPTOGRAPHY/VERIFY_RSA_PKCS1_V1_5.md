---
id: f212a85b-6664-46a5-9378-bc6bb64198cf
domain: CRYPTOGRAPHY
name: "VERIFY_RSA_PKCS1_V1_5"
exergy_cost: 3.0
cortex_taint: CORTEX-TAINT:borjamoskv:batch_crystallize:2026-07-16T16:39:25.206640:7e1f74a8
---

# VERIFY_RSA_PKCS1_V1_5

## Causal Invariant
```text
b = RSA\_Verify_{PKCS1\_v1\_5}(pk, M, \sigma) \in \{0,1\}
```

## Description
Verify an RSA signature using PKCS#1 v1.5 padding.
