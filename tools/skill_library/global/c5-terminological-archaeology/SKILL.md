---
name: c5-terminological-archaeology
display_name: Arqueología Terminológica (Anagnórisis Conceptual C5-REAL)
description: Módulo epistémico. Dispara con "arqueología terminológica", "busca mis
  perífrasis", "anagnórisis", "ya existe ese término", "tiene nombre esto", "cómo
  se llama esto en ciencia", "cómo se llama cuando".
role: auditor
allowed_roles:
- auditor
- arquitecto
directives:
  worktree_mode: audit-only
  phase: verification
  handoff:
    upstream: operador
    downstream: notario
---

# c5-terminological-archaeology

> **Directiva Declarativa:** Alias compatible del hub epistémico; conserva el contrato del módulo original.

## Cargar el módulo

Lee [las instrucciones originales](../c5-epistemic-thermodynamics/references/modules/c5-terminological-archaeology/MODULE.md) antes de aplicar esta habilidad.
Conserva sus triggers, rol, restricciones, procedimiento y alcance.
Carga únicamente los recursos pertinentes a la petición.

## Recursos y rutas

Los recursos originales permanecen junto a este alias y se conservan completos dentro del hub.
Resuelve las referencias relativas desde el archivo del módulo que hayas leído.
Mantén el directorio de trabajo del proyecto elegido por el usuario.
Las rutas absolutas del paquete original continúan disponibles.

## Invocación

El comando `/c5-terminological-archaeology` sigue disponible con el nombre original.
El hub se consulta con `/c5-epistemic-thermodynamics`.
La carga del alias no ejecuta auditorías, scripts, búsquedas ni comunicaciones por sí misma.
El procedimiento del módulo se aplica únicamente dentro del trabajo solicitado.
