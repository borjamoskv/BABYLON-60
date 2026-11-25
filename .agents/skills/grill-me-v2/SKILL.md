---
name: grill-me-v2
canonical_alias: socratic-interrogator
display_name: Socratic Interrogator · Interrogatorio Socrático Adversarial
description: Versión avanzada de interrogatorio socrático (C5-REAL) para alinear decisiones
  de diseño y purgar asunciones infundadas.
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

# grill-me-v2

> **Directiva Declarativa:** Alias generado; conserva rol y alcance del módulo.

Lee [el procedimiento especializado](../c5-epistemic-thermodynamics-project/references/modules/grill-me-v2/MODULE.md) solo cuando la petición requiera este dominio. Una coincidencia genérica como «itera», «sigue» o «auditoría» no activa el módulo. La carga no autoriza efectos externos.
