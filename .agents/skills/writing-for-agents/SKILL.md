---
name: writing-for-agents
canonical_alias: swarm-m2m-writer
display_name: Redacción M2M de Alta Exergía & Sanitización C5
description: Genera documentos y prompts para ingestión estricta por LLMs (M2M), incluyendo
  el sub-protocolo /sanitize-c5.
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

# writing-for-agents

> **Directiva Declarativa:** Alias generado; conserva rol y alcance del módulo.

Lee [el procedimiento especializado](../c5-cortex-swarm-orchestrator-project/references/modules/writing-for-agents/MODULE.md) solo cuando la petición requiera este dominio. Una coincidencia genérica como «itera», «sigue» o «auditoría» no activa el módulo. La carga no autoriza efectos externos.
