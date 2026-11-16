---
name: c5-tri-provider-swarm
display_name: Orquestador de Enjambre Híbrido Tri-Provider (OpenAI ⊗ Qwen ⊗ Local
  vLLM/MLX)
description: Módulo CORTEX. Dispara con "enjambre híbrido", "tri provider swarm",
  "orquestador tres modelos", "tri-provider swarm".
role: ejecutor
allowed_roles:
- ejecutor
- arquitecto
directives:
  worktree_mode: read-write
  phase: implementation
  handoff:
    upstream: arquitecto
    downstream: auditor
---

# c5-tri-provider-swarm

> **Directiva Declarativa:** Alias compatible del hub CORTEX; conserva el contrato del módulo original.

## Cargar el módulo

Lee [las instrucciones originales](../c5-cortex-swarm-orchestrator/references/modules/c5-tri-provider-swarm/MODULE.md) antes de aplicar esta habilidad.
Conserva sus triggers, rol, restricciones, procedimiento y alcance.
Carga únicamente los recursos pertinentes a la petición.

## Recursos y rutas

Los recursos originales permanecen junto a este alias y se conservan completos dentro del hub.
Resuelve las referencias relativas desde el archivo del módulo que hayas leído.
Mantén el directorio de trabajo del proyecto elegido por el usuario.
Las rutas absolutas del paquete original continúan disponibles.

## Invocación

El comando `/c5-tri-provider-swarm` sigue disponible con el nombre original.
El hub se consulta con `/c5-cortex-swarm-orchestrator`.
La carga del alias no ejecuta agentes, scripts, purgas ni comunicaciones por sí misma.
El procedimiento del módulo se aplica únicamente dentro del trabajo solicitado.
