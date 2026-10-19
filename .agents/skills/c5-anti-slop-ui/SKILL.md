---
name: c5-anti-slop-ui
canonical_alias: media-ui-linter
display_name: Linter y Directivas Frontend Anti-Slop (C5-REAL)
description: Módulo audiovisual. Dispara con "media-ui-linter", "anti-slop ui", "impeccable c5", "linter
  de diseño", "auditoría ui", "pulir frontend", "erradicar ai slop".
role: auditor
allowed_roles:
- auditor
- ejecutor
directives:
  worktree_mode: audit-only
  phase: verification
  handoff:
    upstream: ejecutor
    downstream: operador
---

# c5-anti-slop-ui

> **Directiva Declarativa:** Alias compatible del hub audiovisual; conserva el contrato del módulo original.

## Cargar el módulo

Lee [las instrucciones originales](../c5-audiovisual-acreativo-sota-project/references/modules/c5-anti-slop-ui/MODULE.md) antes de aplicar esta habilidad.
Conserva sus triggers, rol, restricciones, procedimiento y alcance.
Carga únicamente los recursos pertinentes a la petición.

## Recursos y rutas

Los recursos originales permanecen junto a este alias y se conservan completos dentro del hub.
Resuelve las referencias relativas desde el archivo del módulo que hayas leído.
Mantén el directorio de trabajo del proyecto elegido por el usuario.
Las rutas absolutas del paquete original continúan disponibles.

## Invocación

El comando `/c5-anti-slop-ui` sigue disponible con el nombre original.
El hub se consulta con `/c5-audiovisual-acreativo-sota-project`.
La carga del alias no ejecuta renders, scripts, búsquedas ni comunicaciones por sí misma.
El procedimiento del módulo se aplica únicamente dentro del trabajo solicitado.
