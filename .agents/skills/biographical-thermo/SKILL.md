---
name: biographical-thermo
canonical_alias: epistemic-biographical-thermo
display_name: Mapeo Termodinámico Biográfico e Histórico
description: Analiza trayectorias vitales, historia y filosofía mediante Mapeo Estructural
  C5-REAL (Termodinámica Discreta).
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

# biographical-thermo

> **Directiva Declarativa:** Alias generado; conserva rol y alcance del módulo.

Lee [el procedimiento especializado](../c5-epistemic-thermodynamics-project/references/modules/biographical-thermo/MODULE.md) solo cuando la petición requiera este dominio. Una coincidencia genérica como «itera», «sigue» o «auditoría» no activa el módulo. La carga no autoriza efectos externos.
