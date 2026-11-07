---
name: c5-anti-slop-ui
canonical_alias: media-ui-linter
display_name: Linter y Directivas Frontend Anti-Slop (C5-REAL)
description: Revisa diseño y accesibilidad de interfaces; distingue comprobaciones
  léxicas parciales de verificación sobre la interfaz renderizada.
role: auditor
allowed_roles:
- auditor
- ejecutor
directives:
  worktree_mode: audit-only
  phase: verification
  handoff:
    upstream: ejecutor
    downstream: operador
---

# c5-anti-slop-ui

> **Directiva Declarativa:** Alias generado; conserva rol y alcance del módulo.

Lee [el procedimiento especializado](../c5-audiovisual-acreativo-sota-project/references/modules/c5-anti-slop-ui/MODULE.md) solo cuando la petición requiera este dominio. Una coincidencia genérica como «itera», «sigue» o «auditoría» no activa el módulo. La carga no autoriza efectos externos.
