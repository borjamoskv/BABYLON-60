---
id: 8066b54e-cf2a-4bed-9367-3445e500a23b
domain: ONTOLOGY
name: "ONT_EXERGY_DRAIN"
exergy_cost: 3.0
cortex_taint: CORTEX-TAINT:borjamoskv:batch_crystallize:2026-07-16T16:40:59.127435:456170aa
---

# ONT_EXERGY_DRAIN

## Causal Invariant
```text
if d(State)/dt = 0 -> SIGKILL
```

## Description
Identifies systems that consume computation without mutating state, and terminates them.
