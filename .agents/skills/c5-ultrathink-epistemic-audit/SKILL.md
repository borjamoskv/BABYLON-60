---
name: c5-ultrathink-epistemic-audit
canonical_alias: epistemic-audit
display_name: Epistemic Audit · Auditoría Epistémica Profunda
description: Módulo epistémico. Dispara con "epistemic-audit", "auditoría epistémica", "postmortem mcts", "desacople ontológico", "auditoría ultrathink".
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

> **Directiva Declarativa:** Alias compatible del hub epistémico; conserva el contrato del módulo original.

## Cargar el módulo

Lee [las instrucciones originales](../c5-epistemic-thermodynamics-project/references/modules/c5-ultrathink-epistemic-audit/MODULE.md) antes de aplicar esta habilidad.
Conserva sus triggers, rol, restricciones, procedimiento y alcance.
Carga únicamente los recursos pertinentes a la petición.

## Recursos y rutas

Los recursos originales permanecen junto a este alias y se conservan completos dentro del hub.
Resuelve las referencias relativas desde el archivo del módulo que hayas leído.
Mantén el directorio de trabajo del proyecto elegido por el usuario.
Las rutas absolutas del paquete original continúan disponibles.

## Invocación

El comando `/c5-ultrathink-epistemic-audit` sigue disponible con el nombre original.
El hub se consulta con `/c5-epistemic-thermodynamics-project`.
La carga del alias no ejecuta auditorías, scripts, búsquedas ni comunicaciones por sí misma.
El procedimiento del módulo se aplica únicamente dentro del trabajo solicitado.
