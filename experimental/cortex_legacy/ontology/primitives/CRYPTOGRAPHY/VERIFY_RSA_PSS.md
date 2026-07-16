---
id: 593d304c-e25b-4462-bb8c-4673995aacab
domain: CRYPTOGRAPHY
name: "VERIFY_RSA_PSS"
exergy_cost: 4.0
cortex_taint: CORTEX-TAINT:borjamoskv:batch_crystallize:2026-07-16T16:39:25.206640:6428cfe6
---

# VERIFY_RSA_PSS

## Causal Invariant
```text
b = RSA\_Verify_{PSS}(pk, M, \sigma) \in \{0,1\}
```

## Description
Verify an RSA signature using PSS padding.
