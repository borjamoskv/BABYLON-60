---
name: adaptive-cron
canonical_alias: wetware-adaptive-cron
display_name: Cálculo de Límite de Disipación Crítica (Adaptive Cron)
description: Módulo Wetware/Venture. Dispara con "wetware-adaptive-cron", "adaptive-cron", "/adaptive-cron",
  "límite de disipación crítica", "burnout cognitivo", "cron adaptativo".
role: arquitecto
allowed_roles:
- arquitecto
directives:
  worktree_mode: spec-only
  phase: design
  handoff:
    upstream: operador
    downstream: ejecutor
---

# adaptive-cron

> **Directiva Declarativa:** Alias compatible del hub Wetware/Venture; conserva el contrato del módulo original.

## Cargar el módulo

Lee [las instrucciones originales](../c5-wetware-and-venture-ops-project/references/modules/adaptive-cron/MODULE.md) antes de aplicar esta habilidad.
Conserva sus triggers, rol, restricciones, procedimiento y alcance.
Carga únicamente los recursos pertinentes a la petición.

## Recursos y rutas

Los recursos originales permanecen junto a este alias y se conservan completos dentro del hub.
Resuelve las referencias relativas desde el archivo del módulo que hayas leído.
Mantén el directorio de trabajo del proyecto elegido por el usuario.
Las rutas absolutas del paquete original continúan disponibles.

## Invocación

El comando `/adaptive-cron` sigue disponible con el nombre original.
El hub se consulta con `/c5-wetware-and-venture-ops-project`.
La carga del alias no ejecuta procedimientos, scripts, búsquedas ni comunicaciones por sí misma.
El procedimiento del módulo se aplica únicamente dentro del trabajo solicitado.
