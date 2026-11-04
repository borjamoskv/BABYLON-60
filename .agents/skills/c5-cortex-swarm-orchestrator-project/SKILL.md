---
name: c5-cortex-swarm-orchestrator-project
canonical_alias: swarm-hub
display_name: Swarm Hub · Orquestador CORTEX (Proyecto)
description: Enruta módulos del proyecto para minería LoRA con enjambres, instalación
  guiada y redacción para agentes. Dispara con "swarm-hub", "cortex project hub",
  "hub cortex proyecto", "swarm router proyecto", "lora swarm", "wizard", "writing-for-agents".
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

1. Identifica la petición y identifica la acción y el dominio, o una invocación explícita, en `references/aliases.json`.
2. Lee solo el módulo pertinente antes de seguir su procedimiento.
3. Conserva sus roles, restricciones y referencias a recursos.
4. Los nombres originales siguen disponibles mediante aliases y comandos independientes.
5. La carga del hub no inicia enjambres, scripts, llamadas a proveedores ni purgas.
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
| [lora-swarm-pipeline](references/modules/lora-swarm-pipeline/MODULE.md) | Pipeline de minería con enjambre de agentes, extracción N-Zonas (SHA-256), ShareGPT/ChatML y clustering semántico. |
| [wizard](references/modules/wizard/MODULE.md) | Transforma al agente en una máquina de estados determinista para instalaciones y configuración paso a paso. |
| [writing-for-agents](references/modules/writing-for-agents/MODULE.md) | Genera documentos y prompts para ingestión estricta por LLMs (M2M), incluyendo el sub-protocolo /sanitize-c5. |
