---
name: categorical-hallucination-audit
display_name: Auditoría Categórica de Alucinación & Cota Kl(D)
description: Módulo epistémico. Dispara con "alucinación categórica", "cota de confabulación",
  "desintegración bayesiana", "Kl(D) audit", "Myhill-Nerode estocástico", "cota de
  lipschitz", "mean shift 1d".
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

# categorical-hallucination-audit

> **Directiva Declarativa:** Alias compatible del hub epistémico; conserva el contrato del módulo original.

## Cargar el módulo

Lee [las instrucciones originales](../c5-epistemic-thermodynamics/references/modules/categorical-hallucination-audit/MODULE.md) antes de aplicar esta habilidad.
Conserva sus triggers, rol, restricciones, procedimiento y alcance.
Carga únicamente los recursos pertinentes a la petición.

## Recursos y rutas

Los recursos originales permanecen junto a este alias y se conservan completos dentro del hub.
Resuelve las referencias relativas desde el archivo del módulo que hayas leído.
Mantén el directorio de trabajo del proyecto elegido por el usuario.
Las rutas absolutas del paquete original continúan disponibles.

## Invocación

El comando `/categorical-hallucination-audit` sigue disponible con el nombre original.
El hub se consulta con `/c5-epistemic-thermodynamics`.
La carga del alias no ejecuta auditorías, scripts, búsquedas ni comunicaciones por sí misma.
El procedimiento del módulo se aplica únicamente dentro del trabajo solicitado.
