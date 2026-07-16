---
id: 85b53ba4-0991-4ca6-ba0a-c1d1f3c520f4
domain: ONTOLOGY
name: "ONT_HOMEOSTASIS_MAINTAIN"
exergy_cost: 6.8
cortex_taint: CORTEX-TAINT:borjamoskv:batch_crystallize:2026-07-16T16:40:59.127435:bad8de1b
---

# ONT_HOMEOSTASIS_MAINTAIN

## Causal Invariant
```text
if Err > Max -> git revert
```

## Description
Automatically rolls back commits that increase the error rate above threshold.
