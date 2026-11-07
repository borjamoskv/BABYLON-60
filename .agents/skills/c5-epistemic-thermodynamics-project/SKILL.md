---
name: c5-epistemic-thermodynamics-project
canonical_alias: epistemic-hub
display_name: Epistemic Hub · Termodinámica Epistémica (Proyecto)
description: Enruta auditoría epistémica del proyecto, síntesis MDL, extracción de
  fuentes, biografía, simbiosis cognitiva y explicación clara. Dispara con "epistemic-hub",
  "epistemic project hub", "auditoría epistémica", "cloud-chamber", "alpha extraction",
  "grill-me-v2", "wait-what".
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

1. Identifica la petición y identifica la acción y el dominio, o una invocación explícita, en `references/aliases.json`.
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
El resolver exige acción y dominio para peticiones contextuales, respeta negaciones y conserva invocaciones explícitas. Para una continuación, añade `--context "objetivo anterior del usuario"`; no infiere permiso para ejecutar procedimientos.
Si devuelve varios módulos, lee solo los pertinentes sin sustituir sus contratos por similitud temática.
Los recursos de cada módulo se resuelven desde su carpeta preservada.

## Módulos disponibles

| Procedimiento | Intención contextual |
| --- | --- |
| [biographical-thermo](references/modules/biographical-thermo/MODULE.md) | Analiza trayectorias vitales, historia y filosofía mediante Mapeo Estructural C5-REAL (Termodinámica Discreta). |
| [c5-alpha-extraction-pipeline](references/modules/c5-alpha-extraction-pipeline/MODULE.md) | Protocol to extract high-exergy algorithmic alpha from arXiv and GitHub directly from raw sources (LaTeX/Git) bypassing PDFs, followed by LARSA-120 formalization. |
| [c5-ultrathink-epistemic-audit](references/modules/c5-ultrathink-epistemic-audit/MODULE.md) | Auditoría epistémica profunda (ULTRATHINK) basada en el marco termodinámico C5-REAL. Ejecuta un desacople ontológico estricto entre "Estado/Memoria" y "Lógica/Cálculo", mapeando conceptos a invariantes termodinámicas (Curry-Howard, Landauer). |
| [cloud-chamber](references/modules/cloud-chamber/MODULE.md) | Ejecuta la Metodología de Cámara de Niebla forzando síntesis de alta densidad topológica (MDL / Invariantes C5-REAL). |
| [grill-me-v2](references/modules/grill-me-v2/MODULE.md) | Versión avanzada de interrogatorio socrático (C5-REAL) para alinear decisiones de diseño y purgar asunciones infundadas. |
| [symbiotic-cognitive-architecture](references/modules/symbiotic-cognitive-architecture/MODULE.md) | Protocolo de formalización de la díada simbiótica operador-agente, evaluación de Valor Ontológico (V_A), Tensor de Transducción Polímata y colapso autopoyético con el comando "itera simbiótica". |
| [wait-what](references/modules/wait-what/MODULE.md) | Freno epistémico para combatir verbosidad, forzar ASD-STE-100 y aterrizar conceptos a lenguaje directo. |
