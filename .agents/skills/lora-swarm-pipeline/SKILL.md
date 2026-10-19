---
name: lora-swarm-pipeline
canonical_alias: swarm-lora-pipeline
display_name: Pipeline de Minería Paralelizada con Enjambre LoRA
description: Módulo CORTEX. Dispara con "swarm-lora-pipeline", "lora swarm", "enjambre lora", "minería enjambre",
  "n-zonas enjambre", "dataset swarm", "enjambre ShareGPT", "minar datasets enjambre",
  "swarm pipeline".
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

# lora-swarm-pipeline

> **Directiva Declarativa:** Alias compatible del hub CORTEX; conserva el contrato del módulo original.

## Cargar el módulo

Lee [las instrucciones originales](../c5-cortex-swarm-orchestrator-project/references/modules/lora-swarm-pipeline/MODULE.md) antes de aplicar esta habilidad.
Conserva sus triggers, rol, restricciones, procedimiento y alcance.
Carga únicamente los recursos pertinentes a la petición.

## Recursos y rutas

Los recursos originales permanecen junto a este alias y se conservan completos dentro del hub.
Resuelve las referencias relativas desde el archivo del módulo que hayas leído.
Mantén el directorio de trabajo del proyecto elegido por el usuario.
Las rutas absolutas del paquete original continúan disponibles.

## Invocación

El comando `/lora-swarm-pipeline` sigue disponible con el nombre original.
El hub se consulta con `/c5-cortex-swarm-orchestrator-project`.
La carga del alias no ejecuta agentes, scripts, purgas ni comunicaciones por sí misma.
El procedimiento del módulo se aplica únicamente dentro del trabajo solicitado.
