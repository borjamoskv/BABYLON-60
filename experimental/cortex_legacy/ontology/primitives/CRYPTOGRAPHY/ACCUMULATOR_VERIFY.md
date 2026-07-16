---
id: 5232acae-d667-49c3-b72a-713fc4ff841b
domain: CRYPTOGRAPHY
name: "ACCUMULATOR_VERIFY"
exergy_cost: 10.0
cortex_taint: CORTEX-TAINT:borjamoskv:batch_crystallize:2026-07-16T16:39:25.206640:46940e56
---

# ACCUMULATOR_VERIFY

## Causal Invariant
```text
b = AccumulateVerify(A, x, \pi_x) \in \{0,1\}
```

## Description
Verify membership of an element in a cryptographic accumulator.
