---
name: c5-wetware-and-venture-ops-project
canonical_alias: wetware-hub
display_name: Wetware Hub · Operaciones y Carga Cognitiva
description: Enruta el módulo del proyecto para el límite de disipación y el cron adaptativo. Dispara con "wetware project hub", "wetware-hub", "venture project hub", "hub wetware proyecto", "adaptive-cron".
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

# Wetware and Venture Ops

> **Directiva Declarativa:** Enruta módulos bajo demanda y conserva su ámbito y contrato.

## Selección

1. Identifica la petición y busca el alias en la tabla o en `references/aliases.json`.
2. Lee solo el módulo pertinente antes de seguir su procedimiento.
3. Conserva sus roles, restricciones y referencias a recursos.
4. Los nombres originales siguen disponibles mediante aliases y comandos independientes.
5. La carga del hub no inicia procedimientos, scripts, servicios externos ni cambios de documentos.
6. Cada procedimiento se ejecuta únicamente cuando lo requiere la petición del usuario.

## Desempate de triggers compartidos

`burnout cognitivo` también activa `cct-cognitive-theory-advisor` global. Usa este hub para límite de carga, planificación, descanso o cron adaptativo; usa esa habilidad global para teoría cognitiva. Si solo aparece el trigger y el tema no aclara el destino, pregunta antes de cargar procedimientos.

## Resolver aliases

Ejecuta `python3 scripts/route.py --query "frase o nombre original"` desde esta carpeta.
El resolver devuelve candidatos y rutas; no ejecuta los módulos.
Normaliza mayúsculas y acentos, prioriza coincidencias exactas y respeta límites de palabra.
Si devuelve varios módulos, lee solo los pertinentes sin sustituir sus contratos por similitud temática.
Los recursos de cada módulo se resuelven desde su carpeta preservada.

## Módulos de ámbito workspace

| Módulo completo | Nombres y triggers conservados |
| --- | --- |
| [adaptive-cron](references/modules/adaptive-cron/MODULE.md) | `adaptive-cron`, `/adaptive-cron`, `límite de disipación crítica`, `burnout cognitivo`, `cron adaptativo` |
