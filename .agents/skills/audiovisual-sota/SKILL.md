---
name: audiovisual-sota
canonical_alias: media-pipeline
display_name: Media Pipeline · Renderizado Audiovisual Determinista
description: Módulo audiovisual. Dispara con "media-pipeline", "audiovisual-sota", "/audiovisual-sota", "pipeline audiovisual", "invariantes remotion ffmpeg".
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

# audiovisual-sota

> **Directiva Declarativa:** Alias compatible del hub audiovisual; conserva el contrato del módulo original.

## Cargar el módulo

Lee [las instrucciones originales](../c5-audiovisual-acreativo-sota-project/references/modules/audiovisual-sota/MODULE.md) antes de aplicar esta habilidad.
Conserva sus triggers, rol, restricciones, procedimiento y alcance.
Carga únicamente los recursos pertinentes a la petición.

## Recursos y rutas

Los recursos originales permanecen junto a este alias y se conservan completos dentro del hub.
Resuelve las referencias relativas desde el archivo del módulo que hayas leído.
Mantén el directorio de trabajo del proyecto elegido por el usuario.
Las rutas absolutas del paquete original continúan disponibles.

## Invocación

El comando `/audiovisual-sota` sigue disponible con el nombre original.
El hub se consulta con `/c5-audiovisual-acreativo-sota-project`.
La carga del alias no ejecuta renders, scripts, búsquedas ni comunicaciones por sí misma.
El procedimiento del módulo se aplica únicamente dentro del trabajo solicitado.
