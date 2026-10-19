---
name: c5-sovereign-daemon-deployment
canonical_alias: kernel-daemon-deploy
display_name: Despliegue del Sovereign Spark Daemon en Launchd
description: Módulo Ring-0. Dispara con "kernel-daemon-deploy", "c5-sovereign-daemon-deployment", "desplegar
  sovereign daemon", "launchd rust daemon", "daemon 24/7".
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

> **Directiva Declarativa:** Alias compatible; conserva el contrato del módulo original.

## Cargar el módulo

Lee [las instrucciones originales](../c5-ring0-babylon-kernel-project/references/modules/c5-sovereign-daemon-deployment/MODULE.md) antes de aplicar esta habilidad.
El módulo conserva íntegros el frontmatter, los triggers, las instrucciones y los recursos.
Aplica su rol, restricciones y procedimiento únicamente a la tarea solicitada.

## Recursos y rutas

Los recursos originales permanecen en esta carpeta y también se conservan dentro del hub.
Resuelve las referencias relativas desde el archivo del módulo que hayas leído.
Mantén el directorio de trabajo del proyecto elegido por el usuario.
Las rutas absolutas originales continúan siendo válidas.

## Selección

Este alias conserva el nombre original y sus frases de activación.
Para selección explícita usa `/c5-sovereign-daemon-deployment`.
Para consultar el hub usa `/c5-ring0-babylon-kernel-project`.
No cargues otros módulos sin relación con la petición.
