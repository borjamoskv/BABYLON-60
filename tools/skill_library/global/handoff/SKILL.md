---
name: handoff
display_name: Protocolo Soberano de Traspaso de Contexto C5-REAL
description: Módulo CORTEX. Dispara con "handoff", "/handoff", "traspaso de contexto",
  "traspaso de sesión", "generar handoff", "traspaso formal", "context handover".
role: auditor
allowed_roles:
- auditor
- arquitecto
- ejecutor
directives:
  worktree_mode: audit-only
  phase: verification
  handoff:
    upstream: ejecutor
    downstream: operador
---

# handoff

> **Directiva Declarativa:** Alias compatible del hub CORTEX; conserva el contrato del módulo original.

## Cargar el módulo

Lee [las instrucciones originales](../c5-cortex-swarm-orchestrator/references/modules/handoff/MODULE.md) antes de aplicar esta habilidad.
Conserva sus triggers, rol, restricciones, procedimiento y alcance.
Carga únicamente los recursos pertinentes a la petición.

## Recursos y rutas

Los recursos originales permanecen junto a este alias y se conservan completos dentro del hub.
Resuelve las referencias relativas desde el archivo del módulo que hayas leído.
Mantén el directorio de trabajo del proyecto elegido por el usuario.
Las rutas absolutas del paquete original continúan disponibles.

## Invocación

El comando `/handoff` sigue disponible con el nombre original.
El hub se consulta con `/c5-cortex-swarm-orchestrator`.
La carga del alias no ejecuta agentes, scripts, purgas ni comunicaciones por sí misma.
El procedimiento del módulo se aplica únicamente dentro del trabajo solicitado.
