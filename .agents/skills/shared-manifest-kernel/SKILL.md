---
name: shared-manifest-kernel
canonical_alias: kernel-shared-manifest
display_name: Kernel de Manifiesto Compartido (64B Seqlock SPMC)
description: Patrón de diseño C-ABI de 64 Bytes (Seqlock SPMC, Cero-Punteros, Fail-Stop
  SCITT y soporte IPC multiplataforma macOS/Linux/Windows).
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

# shared-manifest-kernel

> **Directiva Declarativa:** Alias generado; conserva rol y alcance del módulo.

Lee [el procedimiento especializado](../c5-ring0-babylon-kernel-project/references/modules/shared-manifest-kernel/MODULE.md) solo cuando la petición requiera este dominio. Una coincidencia genérica como «itera», «sigue» o «auditoría» no activa el módulo. La carga no autoriza efectos externos.
