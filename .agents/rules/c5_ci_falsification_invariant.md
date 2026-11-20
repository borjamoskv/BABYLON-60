---
name: c5_ci_falsification_invariant
description: Verificar CI cuando la tarea evalúe su estado o una revisión concreta; los badges no son evidencia suficiente.
trigger: "model_decision"
---

# Invariante de Falsación Empírica de CI (INV_C5_CI_FALSIFICATION)

## 1. El Mapa no es el Territorio (Veto a Badges y Markdown)

Un badge, manifiesto o informe histórico no demuestra el estado actual de CI. Esta regla aplica cuando se evalúe CI o se afirme que una revisión ha superado sus checks; no exige consultar GitHub en cualquier análisis documental.

## 2. Atestación Obligatoria en Silicio (`gh run view`)

El título heredado identifica este apartado; consultar CI no constituye atestación hardware. Usar el conector disponible o `gh run list` y `gh run view`, acotados al repositorio, revisión y ejecución pertinentes. Registrar commit, fecha, estado y enlace o logs. Las tres últimas ejecuciones de otra revisión no certifican la evaluada.

## 3. Precedencia de la Fricción Real (Punto Ω)

Informar fallos, checks pendientes y limitaciones de acceso. Si no se puede consultar CI, marcar su estado `NO_VERIFICADO` y continuar las comprobaciones locales independientes. No sustituir el resultado de una ejecución por la narrativa de la documentación.
