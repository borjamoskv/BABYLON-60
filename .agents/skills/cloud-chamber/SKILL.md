---
name: cloud-chamber
canonical_alias: epistemic-mdl-synthesizer
display_name: Metodología de Cámara de Niebla (Síntesis MDL)
description: Ejecuta la Metodología de Cámara de Niebla forzando síntesis de alta
  densidad topológica (MDL / Invariantes C5-REAL).
role: arquitecto
allowed_roles:
- arquitecto
directives:
  worktree_mode: spec-only
  phase: design
  handoff:
    upstream: operador
    downstream: ejecutor
---

# cloud-chamber

> **Directiva Declarativa:** Alias generado; conserva rol y alcance del módulo.

Lee [el procedimiento especializado](../c5-epistemic-thermodynamics-project/references/modules/cloud-chamber/MODULE.md) solo cuando la petición requiera este dominio. Una coincidencia genérica como «itera», «sigue» o «auditoría» no activa el módulo. La carga no autoriza efectos externos.
