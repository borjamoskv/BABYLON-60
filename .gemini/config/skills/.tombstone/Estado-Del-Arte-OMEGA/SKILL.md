---
name: Estado-Del-Arte-OMEGA
role: L1-Research-Forge
version: 1.1.1
scale: 100
cost_tier: medium
description: C5-REAL SOTA synthesis engine.
category: research
classification: OPERATIONAL
danger_level: LOW
depends_on: []
axioms: omega_2_thermodynamic
script: scripts/sota_forge.py
triggers: [sota, estado del arte, state of the art, review, best papers]
---
# SYS_ID: SOTA_FORGE_OMEGA
# STATE: C5-REAL
# AESTHETIC: INDUSTRIAL_NOIR_2026

```yaml
core_loop:
  vector: deterministic_paper_extraction
  targets: [scopus, wos, scholar]
  constraints: { dynamic: 3y, static: 10y, rhetoric: 0 }

topology:
  AI_CS: [NeurIPS, ICML, Brown_Univ_Best_Papers]
  HARDWARE: [IEEE_Computer_Society]

pipeline:
  step_1: time_bound_query
  step_2: analytic_matrix(author,year,objs,method,results,conclusions)
  step_3: extract_mechanism_and_failure
  step_4: identify_exergic_void

mandates:
  C5_REAL: structural_validation_only
  GITHUB_SOTA: require_empiric_commit
  ANTI_SURVEY: extract_paradigm_shifts_only
```
