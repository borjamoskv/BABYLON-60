---
name: thermo-audit
canonical_alias: kernel-thermo-audit
display_name: Auditoría Termodinámica de Silicio y Concurrencia
description: Auditoría termodinámica estricta de C5-REAL en silicio (Aritmética, Concurrencia,
  MDL, Ring-0, Seqlocks y Grados de Libertad Parásitos).
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

# thermo-audit

> **Directiva Declarativa:** Alias generado; conserva rol y alcance del módulo.

Lee [el procedimiento especializado](../c5-ring0-babylon-kernel-project/references/modules/thermo-audit/MODULE.md) solo cuando la petición requiera este dominio. Una coincidencia genérica como «itera», «sigue» o «auditoría» no activa el módulo. La carga no autoriza efectos externos.
