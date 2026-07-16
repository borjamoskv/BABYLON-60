---
id: ffe3f633-bee1-4958-95c8-dd20e36ff410
domain: CRYPTOGRAPHY
name: "THRESHOLD_SIGNATURE_COMBINE"
exergy_cost: 20.0
cortex_taint: CORTEX-TAINT:borjamoskv:batch_crystallize:2026-07-16T16:39:25.206640:f79555b4
---

# THRESHOLD_SIGNATURE_COMBINE

## Causal Invariant
```text
\sigma = TCombine(\{\sigma_{i_1}, ..., \sigma_{i_t}\})
```

## Description
Combine partial signatures to form a valid threshold signature.
