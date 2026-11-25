---
name: c5-rea-clean-room
canonical_alias: kernel-rea-clean-room
display_name: Suite C5-REA de Ingeniería Inversa en Sala Limpia y Firewall Existence-Gap
description: Disección binaria AOT/Mach-O y Electron ASAR en memoria (<15ms), síntesis
  Clean-Room (TS/Rust/Python) y firewall Popperiano Existence-Gap.
role: auditor
allowed_roles:
- arquitecto
- ejecutor
- auditor
directives:
  worktree_mode: audit-only
  phase: verification
  handoff:
    upstream: ejecutor
    downstream: operador
---

# c5-rea-clean-room

> **Directiva Declarativa:** Alias generado; conserva rol y alcance del módulo.

Lee [el procedimiento especializado](../c5-ring0-babylon-kernel-project/references/modules/c5-rea-clean-room/MODULE.md) solo cuando la petición requiera este dominio. Una coincidencia genérica como «itera», «sigue» o «auditoría» no activa el módulo. La carga no autoriza efectos externos.
