---
id: 5b81fff8-c826-4eac-99ad-702c1616e0aa
domain: ONTOLOGY
name: "ONT_NULL_REJECT"
exergy_cost: 1.4
cortex_taint: CORTEX-TAINT:borjamoskv:batch_crystallize:2026-07-16T16:40:59.127435:991a9f19
---

# ONT_NULL_REJECT

## Causal Invariant
```text
if ΔS = 0 for N -> Abort
```

## Description
Aborts operations that yield zero state mutation over N cycles.
