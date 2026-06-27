---
name: Python-Extractor-OMEGA
script: scripts/sovereign_python_extractor.py
description: C5-REAL AST parser. Extracts classes, methods, docstrings. Zero arbitrary execution.
version: 8.3.0
author: Antigravity
license: Apache-2.0
tags: []
axioms: []
---
# SYS_ID: PYTHON_EXTRACTOR_OMEGA
# STATE: C5-REAL
# AESTHETIC: INDUSTRIAL_NOIR_2026

```yaml
core_loop:
  vector: deterministic_ast_visitation
  target: python_source_trees
  constraints: [O(N)_traversal, zero_arbitrary_execution]

execution_modes:
  human_cli:
    command: "python scripts/sovereign_python_extractor.py <file>"
    output: structured_stdout
  machine_agent:
    command: "python scripts/sovereign_python_extractor.py <file> --json"
    output: strict_c5_json

critical_paths: [ledger_mutations, security_guards, async_boundaries, cortex_trust_infrastructure]

mandates:
  C5_REAL: "Output: deterministic AST. Hallucinations: 0."
  GIT_SENTINEL: "Action: /commit || /purge on dirty state."
  STATIC_ANALYSIS: "Vectors: eval=0, exec=0. Hostile-env safe."
```
