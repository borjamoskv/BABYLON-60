---
name: writing-for-agents
canonical_alias: swarm-m2m-writer
display_name: Redacción M2M de Alta Exergía & Sanitización C5
description: Módulo CORTEX. Dispara con "swarm-m2m-writer", "writing-for-agents", "/writing-for-agents",
  "redacción m2m", "external llm exergy", "sanitize-c5", "/sanitize-c5", "despersonalizar
  manifiesto", "higienizar manifiesto".
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

# writing-for-agents

> **Directiva Declarativa:** Alias compatible del hub CORTEX; conserva el contrato del módulo original.

## Cargar el módulo

Lee [las instrucciones originales](../c5-cortex-swarm-orchestrator-project/references/modules/writing-for-agents/MODULE.md) antes de aplicar esta habilidad.
Conserva sus triggers, rol, restricciones, procedimiento y alcance.
Carga únicamente los recursos pertinentes a la petición.

## Recursos y rutas

Los recursos originales permanecen junto a este alias y se conservan completos dentro del hub.
Resuelve las referencias relativas desde el archivo del módulo que hayas leído.
Mantén el directorio de trabajo del proyecto elegido por el usuario.
Las rutas absolutas del paquete original continúan disponibles.

## Invocación

El comando `/writing-for-agents` sigue disponible con el nombre original.
El hub se consulta con `/c5-cortex-swarm-orchestrator-project`.
La carga del alias no ejecuta agentes, scripts, purgas ni comunicaciones por sí misma.
El procedimiento del módulo se aplica únicamente dentro del trabajo solicitado.
