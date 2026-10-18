---
name: wait-what
canonical_alias: epistemic-simplifier
display_name: Freno Epistémico & Traducción Simplificada (STE)
description: Módulo epistémico. Dispara con "epistemic-simplifier", "wait-what", "/wait-what", "freno epistémico",
  "explícalo simple", "no entiendo nada", "simplifica respuesta", "fuera de aqui todo
  esto", "fuera de aqui todo eto", "quita todo esto", "déjate de rollos".
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

# wait-what

> **Directiva Declarativa:** Alias compatible del hub epistémico; conserva el contrato del módulo original.

## Cargar el módulo

Lee [las instrucciones originales](../c5-epistemic-thermodynamics-project/references/modules/wait-what/MODULE.md) antes de aplicar esta habilidad.
Conserva sus triggers, rol, restricciones, procedimiento y alcance.
Carga únicamente los recursos pertinentes a la petición.

## Recursos y rutas

Los recursos originales permanecen junto a este alias y se conservan completos dentro del hub.
Resuelve las referencias relativas desde el archivo del módulo que hayas leído.
Mantén el directorio de trabajo del proyecto elegido por el usuario.
Las rutas absolutas del paquete original continúan disponibles.

## Invocación

El comando `/wait-what` sigue disponible con el nombre original.
El hub se consulta con `/c5-epistemic-thermodynamics-project`.
La carga del alias no ejecuta auditorías, scripts, búsquedas ni comunicaciones por sí misma.
El procedimiento del módulo se aplica únicamente dentro del trabajo solicitado.
