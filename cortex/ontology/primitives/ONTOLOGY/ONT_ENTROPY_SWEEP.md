---
id: b5c9f26d-c2fc-4324-9b70-e2e7e45fd20b
domain: ONTOLOGY
name: "ONT_ENTROPY_SWEEP"
exergy_cost: 4.5
cortex_taint: CORTEX-TAINT:borjamoskv:batch_crystallize:2026-07-16T16:40:59.127435:449402ec
---

# ONT_ENTROPY_SWEEP

## Causal Invariant
```text
∀ Node(i) : degree(i) > 0
```

## Description
Scans the ontological graph for disconnected or self-referential clusters and marks them for deletion.
