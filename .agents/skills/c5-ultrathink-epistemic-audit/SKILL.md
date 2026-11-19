---
name: c5-ultrathink-epistemic-audit
canonical_alias: epistemic-audit
display_name: Epistemic Audit · Auditoría Epistémica Profunda
description: Auditoría epistémica profunda (ULTRATHINK) basada en el marco termodinámico
  C5-REAL. Ejecuta un desacople ontológico estricto entre "Estado/Memoria" y "Lógica/Cálculo",
  mapeando conceptos a invariantes termodinámicas (Curry-Howard, Landauer).
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

# c5-ultrathink-epistemic-audit

> **Directiva Declarativa:** Alias generado; conserva rol y alcance del módulo.

Lee [el procedimiento especializado](../c5-epistemic-thermodynamics-project/references/modules/c5-ultrathink-epistemic-audit/MODULE.md) solo cuando la petición requiera este dominio. Una coincidencia genérica como «itera», «sigue» o «auditoría» no activa el módulo. La carga no autoriza efectos externos.
