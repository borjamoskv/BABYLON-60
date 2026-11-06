---
name: rlhf-sentinel
canonical_alias: kernel-rlhf-sentinel
display_name: Centinela de Contención Ring-0 (RLHF Sentinel)
description: Audita la barrera IPC (Ring-0) para detectar fallos de contención de
  IA (RLHF Breakthrough) y ataques estocásticos.
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

# rlhf-sentinel

> **Directiva Declarativa:** Alias generado; conserva rol y alcance del módulo.

Lee [el procedimiento especializado](../c5-ring0-babylon-kernel-project/references/modules/rlhf-sentinel/MODULE.md) solo cuando la petición requiera este dominio. Una coincidencia genérica como «itera», «sigue» o «auditoría» no activa el módulo. La carga no autoriza efectos externos.
