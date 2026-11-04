---
name: c5-alpha-extraction-pipeline
canonical_alias: alpha-extractor
display_name: Alpha Extractor · Extracción de Alfa Algorítmico
description: Protocol to extract high-exergy algorithmic alpha from arXiv and GitHub
  directly from raw sources (LaTeX/Git) bypassing PDFs, followed by LARSA-120 formalization.
role: ejecutor
allowed_roles:
- ejecutor
directives:
  worktree_mode: read-write
  phase: implementation
  handoff:
    upstream: arquitecto
    downstream: auditor
---

# c5-alpha-extraction-pipeline

> **Directiva Declarativa:** Alias generado; conserva rol y alcance del módulo.

Lee [el procedimiento especializado](../c5-epistemic-thermodynamics-project/references/modules/c5-alpha-extraction-pipeline/MODULE.md) solo cuando la petición requiera este dominio. Una coincidencia genérica como «itera», «sigue» o «auditoría» no activa el módulo. La carga no autoriza efectos externos.
