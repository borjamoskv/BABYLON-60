---
name: lora-swarm-pipeline
canonical_alias: swarm-lora-pipeline
display_name: Pipeline de Minería Paralelizada con Enjambre LoRA
description: Pipeline de minería con enjambre de agentes, extracción N-Zonas (SHA-256),
  ShareGPT/ChatML y clustering semántico.
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

> **Directiva Declarativa:** Alias generado; conserva rol y alcance del módulo.

Lee [el procedimiento especializado](../c5-cortex-swarm-orchestrator-project/references/modules/lora-swarm-pipeline/MODULE.md) solo cuando la petición requiera este dominio. Una coincidencia genérica como «itera», «sigue» o «auditoría» no activa el módulo. La carga no autoriza efectos externos.
