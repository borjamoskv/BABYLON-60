---
name: cloud-chamber
canonical_alias: epistemic-mdl-synthesizer
display_name: Metodología de Cámara de Niebla (Síntesis MDL)
description: Módulo epistémico. Dispara con "epistemic-mdl-synthesizer", "/cloud-chamber", "cámara de niebla",
  "máxima densidad topológica", "colapso mdl".
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

# cloud-chamber

> **Directiva Declarativa:** Alias compatible del hub epistémico; conserva el contrato del módulo original.

## Cargar el módulo

Lee [las instrucciones originales](../c5-epistemic-thermodynamics-project/references/modules/cloud-chamber/MODULE.md) antes de aplicar esta habilidad.
Conserva sus triggers, rol, restricciones, procedimiento y alcance.
Carga únicamente los recursos pertinentes a la petición.

## Recursos y rutas

Los recursos originales permanecen junto a este alias y se conservan completos dentro del hub.
Resuelve las referencias relativas desde el archivo del módulo que hayas leído.
Mantén el directorio de trabajo del proyecto elegido por el usuario.
Las rutas absolutas del paquete original continúan disponibles.

## Invocación

El comando `/cloud-chamber` sigue disponible con el nombre original.
El hub se consulta con `/c5-epistemic-thermodynamics-project`.
La carga del alias no ejecuta auditorías, scripts, búsquedas ni comunicaciones por sí misma.
El procedimiento del módulo se aplica únicamente dentro del trabajo solicitado.
