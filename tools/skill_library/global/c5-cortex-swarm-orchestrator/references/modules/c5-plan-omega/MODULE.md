---
name: c5-plan-omega
display_name: Protocolo PLAN-Ω de Planificación Causal Determinista
description: 'Motor de planificación determinista en DAG (Protocolo PLAN-Ω). Sustituye checklists planas por matrices topológicas de 4 niveles, sondeo pre-flight en 60s, puertas Two-Way/One-Way con rollback y micro-gates Fail-Stop. Dispara con "plan omega", "c5 plan", "plan causal", "protocolo plan omega", "mejorar plan", "/plan-omega".'
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

# Protocolo PLAN-Ω: Planificación Causal Determinista (C5-REAL)

> **Directiva Declarativa (Orquestación en Árbol de Trabajo):**
> - **Rol Asignado:** `arquitecto` (Arquitecto (Diseño Sistémico & Contratos de Invariantes))
> - **Modo de Acceso a Worktree:** `spec-only` (spec-only (Lectura profunda y modelado formal; emisión de especificaciones sin mutación de código de producción))
> - **Fase Causal:** `design`
> - **Contrato Handoff:** Recibe de `operador` $\to$ Despacha a `ejecutor`

El **Protocolo PLAN-Ω** erradica el "vibe planning" estocástico en Antigravity, sustituyendo las listas planas secuenciales por matrices topológicas de dependencias causales (DAGs) y verificaciones inmediatas en silicio.

---

## 1. Clasificación de Canal: Fast-Path vs. Deep-Path

Al entrar en planificación o recibir la orden `/plan`:

1. **FAST-PATH (Zero-Nata):**
   - **Criterio:** Tareas atómicas o locales ($\le 2$ archivos modificados, cero impacto en Ring-0, esquemas SQL o C-ABI; totalmente reversible).
   - **Acción:**
     1. Un probe rápido de compilación (`cargo check`, `pytest`).
     2. Plan condensado de 1 bloque.
     3. Ejecución directa y verificación inmediata.

2. **DEEP-PATH (C5-Causal):**
   - **Criterio:** Mutaciones en Ring-0, migraciones de base de datos, concurrencia (Seqlocks/Atomics), o afectación a $>2$ subsistemas.
   - **Acción:** Aplicar la plantilla canónica completa PLAN-Ω en `implementation_plan.md`.

---

## 2. Plantilla Canónica de `implementation_plan.md`

Toda planificación en Deep-Path debe estructurarse con las siguientes secciones obligatorias:

### A. Ground Truth & Pre-Flight Probe (Sondeo en 60s)
- **Probe Command:** Comando activo para verificar que el entorno compila y las dependencias existen antes de planificar cambios.
- **Baseline de Estado:** Hash del commit actual, tests pasando (N/N) y warnings existentes.
- **Blast Radius:** Análisis mediante `git grep` de los símbolos que dependen de los archivos a modificar.

### B. Matriz Topológica de Ejecución (DAG Causal)
Organización estricta en 4 niveles de dependencia:
- **N0 (Ground Truth & Sondas):** Verificación de entorno, baseline de tests y backups de seguridad.
- **N1 (Core & Contratos de Tipos):** Estructuras de datos, esquemas de BD, interfaces C-ABI/Traits.
- **N2 (Lógica de Motor & Adaptadores):** Implementación de subsistemas, CLI, integración inter-componente.
- **N3 (Validación & Sellado):** Tests de estrés, suites de regresión y commits atómicos.

Cada bloque en la tabla especifica:
`| Bloque ID | Nivel DAG | Tipo de Puerta | Subsistema / Archivo | Mutación | Micro-Assert en Silicio | Depende De |`

### C. Demarcación de Puertas y Procedimiento de Rollback
- **Two-Way Doors (Reversibles):** Archivos nuevos, tests, diagnósticos.
- **One-Way Doors (Irreversibles):** Modificación de tablas SQL en producción, comandos destructivos (`rm`), despliegues externos.
  - *Requisito:* Comando explícito de rollback preparado con antelación + Gate Touch ID.

### D. Micro-Gates de Silicio Fail-Stop por Bloque
Cada bloque contiene la tupla:
- **Archivos:** `[MODIFY]` / `[NEW]` / `[DELETE]`
- **Diff de Interfaz:** Enfocado en tipos y firmas.
- **Micro-Assert en Silicio:** Comando determinista (ej. `cargo check --lib`, `pytest tests/test_unit.py -k ...`). Si falla, la ejecución se detiene de inmediato (Fail-Stop).

### E. Protocolo Anti-Thrashing (Regla de los 2 Intentos)
Si el Micro-Assert de un bloque falla 2 veces consecutivas:
1. Suspender mutaciones en caliente.
2. Congelar el bloque y marcarlo como `[BLOCKED]` en el documento del plan.
3. Proponer dos bifurcaciones alternativas (Fallback A / Fallback B) al Operador Raíz.
