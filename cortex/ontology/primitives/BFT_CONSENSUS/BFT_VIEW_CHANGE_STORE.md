---
id: 3061da8c-fff5-46f8-89c7-a241ff04ee97
domain: BFT_CONSENSUS
name: "BFT_VIEW_CHANGE_STORE"
exergy_cost: 1.2
cortex_taint: CORTEX-TAINT:borjamoskv:batch_crystallize:2026-07-16T16:42:12.004135:98d3be7b
---

# BFT_VIEW_CHANGE_STORE

## Causal Invariant
```text
ViewChangeMap[PeerId][NewView] == Vote
```

## Description
Stores VIEW_CHANGE vote for the new epoch.
