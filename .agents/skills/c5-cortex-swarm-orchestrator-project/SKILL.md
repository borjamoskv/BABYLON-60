---
name: c5-cortex-swarm-orchestrator-project
canonical_alias: swarm-hub
display_name: Swarm Hub · Orquestador CORTEX (Proyecto)
description: Enruta módulos del proyecto para minería LoRA con enjambres, instalación guiada y redacción para agentes. Dispara con "swarm-hub", "cortex project hub", "hub cortex proyecto", "swarm router proyecto", "lora swarm", "wizard", "writing-for-agents".
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

# CORTEX Swarm Orchestrator

> **Directiva Declarativa:** Enruta módulos bajo demanda y conserva su ámbito y contrato.

## Selección

1. Identifica la petición y busca el alias en la tabla o en `references/aliases.json`.
2. Lee solo el módulo pertinente antes de seguir su procedimiento.
3. Conserva sus roles, restricciones y referencias a recursos.
4. Los nombres originales siguen disponibles mediante aliases y comandos independientes.
5. La carga del hub no inicia enjambres, scripts, llamadas a proveedores ni purgas.
6. Cada procedimiento se ejecuta únicamente cuando lo requiere la petición del usuario.

## Resolver aliases

Ejecuta `python3 scripts/route.py --query "frase o nombre original"` desde esta carpeta.
El resolver devuelve candidatos y rutas; no ejecuta los módulos.
Normaliza mayúsculas y acentos, prioriza coincidencias exactas y respeta límites de palabra.
Si devuelve varios módulos, lee solo los pertinentes sin sustituir sus contratos por similitud temática.
Los recursos de cada módulo se resuelven desde su carpeta preservada.

## Módulos de ámbito workspace

| Módulo completo | Nombres y triggers conservados |
| --- | --- |
| [lora-swarm-pipeline](references/modules/lora-swarm-pipeline/MODULE.md) | `lora-swarm-pipeline`, `/lora-swarm-pipeline`, `lora swarm`, `enjambre lora`, `minería enjambre`, `n-zonas enjambre`, `dataset swarm`, `enjambre ShareGPT`, `minar datasets enjambre`, `swarm pipeline` |
| [wizard](references/modules/wizard/MODULE.md) | `wizard`, `/wizard`, `paso a paso`, `máquina de estados`, `guía secuencial`, `asistente de instalación` |
| [writing-for-agents](references/modules/writing-for-agents/MODULE.md) | `writing-for-agents`, `/writing-for-agents`, `redacción m2m`, `external llm exergy`, `sanitize-c5`, `/sanitize-c5`, `despersonalizar manifiesto`, `higienizar manifiesto` |
