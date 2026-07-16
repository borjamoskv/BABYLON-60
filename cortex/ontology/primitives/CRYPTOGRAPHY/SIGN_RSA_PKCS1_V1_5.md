---
id: e8793959-9ed4-4b83-88a1-8cd8dee070ab
domain: CRYPTOGRAPHY
name: "SIGN_RSA_PKCS1_V1_5"
exergy_cost: 8.0
cortex_taint: CORTEX-TAINT:borjamoskv:batch_crystallize:2026-07-16T16:39:25.206640:1401036b
---

# SIGN_RSA_PKCS1_V1_5

## Causal Invariant
```text
\sigma = RSA\_Sign_{PKCS1\_v1\_5}(sk, M)
```

## Description
Generate an RSA signature using PKCS#1 v1.5 padding.
