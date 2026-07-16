---
id: 2839492f-48e1-4f53-b03c-a4d0ac50e46a
domain: CRYPTOGRAPHY
name: "BLIND_SIGNATURE_UNBLIND"
exergy_cost: 2.0
cortex_taint: CORTEX-TAINT:borjamoskv:batch_crystallize:2026-07-16T16:39:25.206640:cf3dd0df
---

# BLIND_SIGNATURE_UNBLIND

## Causal Invariant
```text
\sigma = Unblind(\sigma', r)
```

## Description
Unblind a signature to obtain a valid signature on the original message.
