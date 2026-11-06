---
name: audiovisual-sota
canonical_alias: media-pipeline
display_name: Media Pipeline · Renderizado Audiovisual Determinista
description: Fuerza invariantes extremas en pipelines de renderizado audiovisual (FFmpeg/Remotion).
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

> **Directiva Declarativa:** Alias generado; conserva rol y alcance del módulo.

Lee [el procedimiento especializado](../c5-audiovisual-acreativo-sota-project/references/modules/audiovisual-sota/MODULE.md) solo cuando la petición requiera este dominio. Una coincidencia genérica como «itera», «sigue» o «auditoría» no activa el módulo. La carga no autoriza efectos externos.
