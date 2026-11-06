---
name: babylon60-architecture
canonical_alias: kernel-ide-architecture
display_name: Arquitectura y Patrones BABYLON-60 IDE
description: Patrones de arquitectura de Babylon60 IDE (instaladores 1-clic autorreparables,
  tokens Ed25519 SCITT, OpenRouter Gateway, SSO corporativo y escala exérgica 1-21000).
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

# babylon60-architecture

> **Directiva Declarativa:** Alias generado; conserva rol y alcance del módulo.

Lee [el procedimiento especializado](../c5-ring0-babylon-kernel-project/references/modules/babylon60-architecture/MODULE.md) solo cuando la petición requiera este dominio. Una coincidencia genérica como «itera», «sigue» o «auditoría» no activa el módulo. La carga no autoriza efectos externos.
