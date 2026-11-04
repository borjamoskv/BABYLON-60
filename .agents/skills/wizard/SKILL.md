---
name: wizard
canonical_alias: swarm-state-wizard
display_name: Asistente de Instalación Determinista (Wizard)
description: Transforma al agente en una máquina de estados determinista para instalaciones
  y configuración paso a paso.
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

# wizard

> **Directiva Declarativa:** Alias generado; conserva rol y alcance del módulo.

Lee [el procedimiento especializado](../c5-cortex-swarm-orchestrator-project/references/modules/wizard/MODULE.md) solo cuando la petición requiera este dominio. Una coincidencia genérica como «itera», «sigue» o «auditoría» no activa el módulo. La carga no autoriza efectos externos.
