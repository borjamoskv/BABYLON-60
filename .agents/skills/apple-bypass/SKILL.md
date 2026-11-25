---
name: apple-bypass
canonical_alias: kernel-apple-bypass
display_name: Bypass Termodinámico para LLMs en Apple Silicon
description: Mitigación de presión de memoria para LLMs locales en Apple Silicon.
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

# apple-bypass

> **Directiva Declarativa:** Alias generado; conserva rol y alcance del módulo.

Lee [el procedimiento especializado](../c5-ring0-babylon-kernel-project/references/modules/apple-bypass/MODULE.md) solo cuando la petición requiera este dominio. Una coincidencia genérica como «itera», «sigue» o «auditoría» no activa el módulo. La carga no autoriza efectos externos.
