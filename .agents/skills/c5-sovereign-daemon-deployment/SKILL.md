---
name: c5-sovereign-daemon-deployment
canonical_alias: kernel-daemon-deploy
display_name: Despliegue del Sovereign Spark Daemon en Launchd
description: Protocolo estricto para desplegar el Sovereign Spark Daemon (Antigravity
  Engine en Rust) sobre el sistema init local de macOS (launchd) para ejecución 24/7
  ininterrumpida.
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

# c5-sovereign-daemon-deployment

> **Directiva Declarativa:** Alias generado; conserva rol y alcance del módulo.

Lee [el procedimiento especializado](../c5-ring0-babylon-kernel-project/references/modules/c5-sovereign-daemon-deployment/MODULE.md) solo cuando la petición requiera este dominio. Una coincidencia genérica como «itera», «sigue» o «auditoría» no activa el módulo. La carga no autoriza efectos externos.
