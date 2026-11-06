---
name: adaptive-cron
canonical_alias: wetware-adaptive-cron
display_name: Cálculo de Límite de Disipación Crítica (Adaptive Cron)
description: Resume carga operativa mediante observables verificables y conserva el
  control de sesión del operador.
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

# adaptive-cron

> **Directiva Declarativa:** Alias generado; conserva rol y alcance del módulo.

Lee [el procedimiento especializado](../c5-wetware-and-venture-ops-project/references/modules/adaptive-cron/MODULE.md) solo cuando la petición requiera este dominio. Una coincidencia genérica como «itera», «sigue» o «auditoría» no activa el módulo. La carga no autoriza efectos externos.
