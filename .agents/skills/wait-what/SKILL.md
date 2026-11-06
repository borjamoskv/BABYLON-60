---
name: wait-what
canonical_alias: epistemic-simplifier
display_name: Freno Epistémico & Traducción Simplificada (STE)
description: Freno epistémico para combatir verbosidad, forzar ASD-STE-100 y aterrizar
  conceptos a lenguaje directo.
role: auditor
allowed_roles:
- auditor
directives:
  worktree_mode: audit-only
  phase: verification
  handoff:
    upstream: ejecutor
    downstream: operador
---

# wait-what

> **Directiva Declarativa:** Alias generado; conserva rol y alcance del módulo.

Lee [el procedimiento especializado](../c5-epistemic-thermodynamics-project/references/modules/wait-what/MODULE.md) solo cuando la petición requiera este dominio. Una coincidencia genérica como «itera», «sigue» o «auditoría» no activa el módulo. La carga no autoriza efectos externos.
