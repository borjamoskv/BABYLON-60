---
name: c5-audiovisual-acreativo-sota-project
canonical_alias: media-hub
display_name: Media Hub · Audiovisual Acreativo (Proyecto)
description: Enruta módulos del proyecto para pipelines audiovisuales y auditoría
  de interfaces. Dispara con "media-hub", "audiovisual project hub", "hub audiovisual
  proyecto", "media router proyecto", "audiovisual-sota", "anti-slop ui".
role: arquitecto
allowed_roles:
- arquitecto
- ejecutor
- auditor
directives:
  worktree_mode: spec-only
  phase: design
  handoff:
    upstream: operador
    downstream: ejecutor
---

# Audiovisual Acreativo SOTA

> **Directiva Declarativa:** Enruta módulos bajo demanda y conserva su ámbito y contrato.

## Selección

1. Identifica la petición y identifica la acción y el dominio, o una invocación explícita, en `references/aliases.json`.
2. Lee solo el módulo pertinente antes de seguir su procedimiento.
3. Conserva sus roles, restricciones y referencias a recursos.
4. Los nombres originales siguen disponibles mediante aliases y comandos independientes.
5. La carga del hub no inicia renders, scripts, servicios externos ni cambios de documentos.
6. Cada procedimiento se ejecuta únicamente cuando lo requiere la petición del usuario.

## Resolver aliases

Ejecuta `python3 scripts/route.py --query "frase o nombre original"` desde esta carpeta.
El resolver devuelve candidatos y rutas; no ejecuta los módulos.
El resolver exige acción y dominio para peticiones contextuales, respeta negaciones y conserva invocaciones explícitas. Para una continuación, añade `--context "objetivo anterior del usuario"`; no infiere permiso para ejecutar procedimientos.
Si devuelve varios módulos, lee solo los pertinentes sin sustituir sus contratos por similitud temática.
Los recursos de cada módulo se resuelven desde su carpeta preservada.

## Módulos disponibles

| Procedimiento | Intención contextual |
| --- | --- |
| [audiovisual-sota](references/modules/audiovisual-sota/MODULE.md) | Fuerza invariantes extremas en pipelines de renderizado audiovisual (FFmpeg/Remotion). |
| [c5-anti-slop-ui](references/modules/c5-anti-slop-ui/MODULE.md) | Revisa diseño y accesibilidad de interfaces; distingue comprobaciones léxicas parciales de verificación sobre la interfaz renderizada. |
