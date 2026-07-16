---
id: 000d9a38-40bb-4b75-bcef-bb7aad91b5a5
domain: ONTOLOGY
name: "ONT_SIMULATION_HALT"
exergy_cost: 5.2
cortex_taint: CORTEX-TAINT:borjamoskv:batch_crystallize:2026-07-16T16:40:59.127435:79334770
---

# ONT_SIMULATION_HALT

## Causal Invariant
```text
C4_SIM -> SIGKILL
```

## Description
Detects if a process is looping in C4-SIM and forcefully kills it to restore C5-REAL dominance.
