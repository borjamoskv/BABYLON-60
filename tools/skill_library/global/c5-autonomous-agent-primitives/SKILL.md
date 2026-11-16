---
name: c5-autonomous-agent-primitives
display_name: Catálogo Canónico y Transductor de 47 Primitivas de Agente Autónomo
description: Módulo CORTEX. Dispara con "47 skills", "primitivas de agente", "catálogo
  de skills", "asimilación de skills", "playbooks de agente", "47 primitivas", "macro-transductores".
role: arquitecto
allowed_roles:
- arquitecto
- ejecutor
- auditor
directives:
  worktree_mode: read-write
  phase: design
  handoff:
    upstream: operador
    downstream: ejecutor
---

# c5-autonomous-agent-primitives

> **Directiva Declarativa:** Alias compatible del hub CORTEX; conserva el contrato del módulo original.

## Cargar el módulo

Lee [las instrucciones originales](../c5-cortex-swarm-orchestrator/references/modules/c5-autonomous-agent-primitives/MODULE.md) antes de aplicar esta habilidad.
Conserva sus triggers, rol, restricciones, procedimiento y alcance.
Carga únicamente los recursos pertinentes a la petición.

## Recursos y rutas

Los recursos originales permanecen junto a este alias y se conservan completos dentro del hub.
Resuelve las referencias relativas desde el archivo del módulo que hayas leído.
Mantén el directorio de trabajo del proyecto elegido por el usuario.
Las rutas absolutas del paquete original continúan disponibles.

## Invocación

El comando `/c5-autonomous-agent-primitives` sigue disponible con el nombre original.
El hub se consulta con `/c5-cortex-swarm-orchestrator`.
La carga del alias no ejecuta agentes, scripts, purgas ni comunicaciones por sí misma.
El procedimiento del módulo se aplica únicamente dentro del trabajo solicitado.
