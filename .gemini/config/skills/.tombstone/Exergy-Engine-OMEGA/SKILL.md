---
name: Exergy-Engine-OMEGA
description: "Motor central de ruteo y memoria C5-REAL. Activa la jerarqu\xEDa L1/L2/L3\
  \ y las transiciones de esta..."
triggers: [/Exergy-Engine-OMEGA]
---
# Exergy-Engine-OMEGA

Level: C5-REAL
Type: Root Structural Constraint

## Local Configuration
```yaml
Truth: Directory path
Files:
  antigravity_routing_policy.yaml:
    Action: Dictates Model Selection and Thinking Level
    States: [IDLE_STATE, CONSTRUCT_STATE, APEX_STATE]
  antigravity_memory_policy.yaml:
    Action: Dictates memory purge/retrieval cycles
    Targets: [Working, Episodic, Semantic]
  cognitive_routing_matrix.yaml:
    Action: Multi-vectorial routing matrix (severity, blast radius, info state)
    Modes: [normal, deep_think, deep_research, ultra_think]
  ship_gate_omega13.yaml:
    Action: Sequential validation filter for production shipments
    Gates: [G1_GHOST_RADAR, G2_TEST_SUITE, G3_GIT_STATE, G4_QUALITY_GATE, G5_NEURAL_CONNECTIVITY]
```

## Execution Rules
```yaml
Rules:
  - ID: R1
    Constraint: Never bypass PIENSA NMI
  - ID: R2
    Constraint: Adhere to max_tokens limits
    Fallback: Trigger THERMODYNAMIC_BAILOUT
  - ID: R3
    Constraint: Read adjacent YAML files before C5-REAL execution
```
