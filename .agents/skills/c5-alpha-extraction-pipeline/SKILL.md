---
name: c5-alpha-extraction-pipeline
canonical_alias: alpha-extractor
display_name: Alpha Extractor · Extracción de Alfa Algorítmico
description: Módulo epistémico. Dispara con "alpha-extractor", "c5-alpha-extraction-pipeline", "extraer alfa algorítmico", "alpha extraction", "deep research arxiv", "larsa 120 alpha".
role: ejecutor
allowed_roles:
- ejecutor
directives:
  worktree_mode: read-write
  phase: implementation
  handoff:
    upstream: arquitecto
    downstream: auditor
---

# c5-alpha-extraction-pipeline

> **Directiva Declarativa:** Alias compatible del hub epistémico; conserva el contrato del módulo original.

## Cargar el módulo

Lee [las instrucciones originales](../c5-epistemic-thermodynamics-project/references/modules/c5-alpha-extraction-pipeline/MODULE.md) antes de aplicar esta habilidad.
Conserva sus triggers, rol, restricciones, procedimiento y alcance.
Carga únicamente los recursos pertinentes a la petición.

## Recursos y rutas

Los recursos originales permanecen junto a este alias y se conservan completos dentro del hub.
Resuelve las referencias relativas desde el archivo del módulo que hayas leído.
Mantén el directorio de trabajo del proyecto elegido por el usuario.
Las rutas absolutas del paquete original continúan disponibles.

## Invocación

El comando `/c5-alpha-extraction-pipeline` sigue disponible con el nombre original.
El hub se consulta con `/c5-epistemic-thermodynamics-project`.
La carga del alias no ejecuta auditorías, scripts, búsquedas ni comunicaciones por sí misma.
El procedimiento del módulo se aplica únicamente dentro del trabajo solicitado.
