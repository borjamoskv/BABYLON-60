---
name: c5-epistemic-thermodynamics-project
canonical_alias: epistemic-hub
display_name: Epistemic Hub · Termodinámica Epistémica (Proyecto)
description: Enruta auditoría epistémica del proyecto, síntesis MDL, extracción de fuentes, biografía, simbiosis cognitiva y explicación clara. Dispara con "epistemic-hub", "epistemic project hub", "auditoría epistémica", "cloud-chamber", "alpha extraction", "grill-me-v2", "wait-what".
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

# Epistemic Thermodynamics

> **Directiva Declarativa:** Enruta módulos bajo demanda y conserva su ámbito y contrato.

## Selección

1. Identifica la petición y busca el alias en la tabla o en `references/aliases.json`.
2. Lee solo el módulo pertinente antes de seguir su procedimiento.
3. Conserva sus roles, restricciones y referencias a recursos.
4. Los nombres originales siguen disponibles mediante aliases y comandos independientes.
5. La carga del hub no inicia auditorías, scripts, búsquedas externas ni cambios de documentos.
6. Cada procedimiento se ejecuta únicamente cuando lo requiere la petición del usuario.

## Desempate de triggers compartidos

`tensor de transducción` también activa `c5-gemini-api-2026-standards` global. Usa este hub para arquitectura cognitiva y colaboración agente-persona; usa esa habilidad global para Gemini API, claves, cuotas o esquemas JSON. Si solo aparece el trigger y el tema no aclara el destino, pregunta antes de cargar procedimientos.

## Resolver aliases

Ejecuta `python3 scripts/route.py --query "frase o nombre original"` desde esta carpeta.
El resolver devuelve candidatos y rutas; no ejecuta los módulos.
Normaliza mayúsculas y acentos, prioriza coincidencias exactas y respeta límites de palabra.
Si devuelve varios módulos, lee solo los pertinentes sin sustituir sus contratos por similitud temática.
Los recursos de cada módulo se resuelven desde su carpeta preservada.

## Módulos de ámbito workspace

| Módulo completo | Nombres y triggers conservados |
| --- | --- |
| [c5-ultrathink-epistemic-audit](references/modules/c5-ultrathink-epistemic-audit/MODULE.md) | `c5-ultrathink-epistemic-audit`, `/c5-ultrathink-epistemic-audit`, `auditoría epistémica`, `postmortem mcts`, `desacople ontológico`, `auditoría ultrathink` |
| [cloud-chamber](references/modules/cloud-chamber/MODULE.md) | `cloud-chamber`, `/cloud-chamber`, `cámara de niebla`, `máxima densidad topológica`, `colapso mdl` |
| [c5-alpha-extraction-pipeline](references/modules/c5-alpha-extraction-pipeline/MODULE.md) | `c5-alpha-extraction-pipeline`, `/c5-alpha-extraction-pipeline`, `extraer alfa algorítmico`, `alpha extraction`, `larsa 120 alpha` |
| [biographical-thermo](references/modules/biographical-thermo/MODULE.md) | `biographical-thermo`, `/biographical-thermo`, `biografía termodinámica`, `trayectoria termodinámica`, `análisis biográfico termodinámico` |
| [symbiotic-cognitive-architecture](references/modules/symbiotic-cognitive-architecture/MODULE.md) | `symbiotic-cognitive-architecture`, `/symbiotic-cognitive-architecture`, `tú y yo`, `simbiosis cognitiva`, `valor ontológico agente`, `tensor de transducción`, `itera simbiótica` |
| [grill-me-v2](references/modules/grill-me-v2/MODULE.md) | `grill-me-v2`, `/grill-me-v2`, `socratic audit`, `interrogatorio socrático` |
| [wait-what](references/modules/wait-what/MODULE.md) | `wait-what`, `/wait-what`, `freno epistémico`, `explícalo simple`, `no entiendo nada`, `simplifica respuesta`, `fuera de aqui todo esto`, `fuera de aqui todo eto`, `quita todo esto`, `déjate de rollos` |
