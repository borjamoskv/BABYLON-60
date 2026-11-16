---
name: c5-epistemic-thermodynamics
display_name: Epistemic Thermodynamics
description: Enruta axiomas, léxico, termodinámica de información, modelos cognitivos,
  síntesis y falsación de afirmaciones. Dispara con "epistemic hub", "termodinámica
  epistémica", "axiomas", "anagnórisis", "falsación", "investigación profunda", "peer
  review".
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

`tensor de transducción` también activa `symbiotic-cognitive-architecture` en el ámbito del proyecto. Usa este hub para teoría cognitiva y análisis conceptual; usa la habilidad del proyecto para arquitectura cognitiva y colaboración agente-persona. Si solo aparece el trigger y el tema no aclara el destino, pregunta antes de cargar procedimientos.

`burnout cognitivo` también activa `adaptive-cron` del proyecto. Usa este hub para teoría cognitiva; usa `adaptive-cron` para planificar carga de trabajo, descanso o límites de disipación. Si solo aparece el trigger y el tema no aclara el destino, pregunta antes de cargar procedimientos.

## Resolver aliases

Ejecuta `python3 scripts/route.py --query "frase o nombre original"` desde esta carpeta.
El resolver devuelve candidatos y rutas; no ejecuta los módulos.
El resolver exige acción y dominio para peticiones contextuales, respeta negaciones y conserva invocaciones explícitas. Para una continuación, añade `--context "objetivo anterior del usuario"`; no infiere permiso para ejecutar procedimientos.
Si devuelve varios módulos, lee solo los pertinentes sin sustituir sus contratos por similitud temática.
Los recursos de cada módulo se resuelven desde su carpeta preservada.

<!-- skill-library:module-table -->
