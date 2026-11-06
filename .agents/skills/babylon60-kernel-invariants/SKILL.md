---
name: babylon60-kernel-invariants
canonical_alias: kernel-invariants-audit
description: Audita y prepara correcciones del kernel BABYLON-60 para SPSC, SQLite
  L0, relojes causales, consenso LARSA y correspondencia Rust–Lean. Usa el puente
  MCP local cuando esté disponible y distingue pruebas ejecutadas de obligaciones
  pendientes.
display_name: Auditoría de Invariantes del Kernel BABYLON-60
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

# babylon60-kernel-invariants

> **Directiva Declarativa:** Alias generado; conserva rol y alcance del módulo.

Lee [el procedimiento especializado](../c5-ring0-babylon-kernel-project/references/modules/babylon60-kernel-invariants/MODULE.md) solo cuando la petición requiera este dominio. Una coincidencia genérica como «itera», «sigue» o «auditoría» no activa el módulo. La carga no autoriza efectos externos.
