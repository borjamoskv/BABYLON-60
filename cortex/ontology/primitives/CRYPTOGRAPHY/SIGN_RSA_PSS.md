---
id: 724d6970-ed94-4eb1-9e1b-fa812174e797
domain: CRYPTOGRAPHY
name: "SIGN_RSA_PSS"
exergy_cost: 9.0
cortex_taint: CORTEX-TAINT:borjamoskv:batch_crystallize:2026-07-16T16:39:25.206640:9d525203
---

# SIGN_RSA_PSS

## Causal Invariant
```text
\sigma = RSA\_Sign_{PSS}(sk, M)
```

## Description
Generate an RSA signature using PSS padding.
