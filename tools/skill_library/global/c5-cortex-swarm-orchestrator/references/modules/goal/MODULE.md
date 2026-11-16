---
name: goal
display_name: Protocolo de Ejecución por Contrato /goal (Zero-Waste Gate)
description: 'Destila cualquier tarea en un contrato cerrado de mínimo consumo de tokens y asigna el modelo/nivel exacto antes de tocar código. Dispara con "/goal", "goal", "contrato goal".'
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

# Protocolo de Ejecución `/goal` (Zero-Waste Token Gate)

> **Directiva Declarativa (Orquestación en Árbol de Trabajo):**
> - **Rol Asignado:** `arquitecto` (Diseño Sistémico & Contratos de Invariantes)
> - **Modo de Acceso a Worktree:** `spec-only` (Lectura profunda y modelado formal; emisión de especificaciones sin mutación de código de producción)
> - **Fase Causal:** `design`
> - **Contrato Handoff:** Recibe de `operador` $\to$ Despacha a `ejecutor`

Cuando el usuario invoque `/goal`, **PROHIBIDO editar archivos o generar bloques largos de código en este turno**. Ejecuta estrictamente estos pasos en menos de 250 palabras:

### Paso 1: Inspección quirúrgica
Usa únicamente búsqueda por nombres de archivo o `grep` puntual para ubicar las rutas afectadas. No leas archivos completos salvo las firmas o líneas estrictamente necesarias.

### Paso 2: Test de Ambigüedad
Si la petición tiene más de una interpretación técnica válida, detente y formula un máximo de **2 preguntas directas con opciones cerradas (A/B)**. Si es clara, pasa directo al Paso 3.

### Paso 3: Selección de Motor y Nivel (Regla de las 5 opciones)
Evalúa la complejidad del contrato ya digerido y selecciona el motor más económico de la lista respetando sus niveles reales en la UI:
- `Gemini 3.8 Flash` -> Nivel obligatorio: `High (Fast)` (usar siempre para tareas de esfuerzo bajo o medio-simple; no dispone de nivel `Low` ni `Medium`).
- `GPT-OSS 120B` -> Nivel obligatorio: `(Medium)` (único nivel disponible; usar para texto, docs o plantillas simples).
- `Claude Sonnet 5.5` -> Elegir entre `Low`, `Medium` o `High` (preferir `Low` porque el plan ya va digerido).
- `Gemini 4 Argon` -> Elegir entre `Low`, `Medium` o `High` (preferir `Low` para implementar este contrato o `Medium` si supera 4 archivos; prohibido `High` salvo concurrencia o arquitectura crítica).
- `Claude Opus 5.5` -> Elegir entre `Low`, `Medium` o `High` (solo desempate o algoritmos de extrema dificultad).

### Paso 4: Detección Automática de Gate de Salida (Multi-Stack)
Inspecciona los marcadores de la raíz del proyecto para fijar el comando exacto de parada binaria determinista (código 0):
- **Rust / Bare-Metal** (`Cargo.toml`): `cargo test -q --test <test_name>` o `cargo check -q`
- **Python / uv** (`pyproject.toml` / `uv.lock`): `uv run pytest <path> -k <test> -q` o `uv run ruff check <path>`
- **TypeScript / Web** (`package.json`): `pnpm exec vitest run <path>` o `pnpm exec tsc --noEmit`
- **Lean 4 / Formal** (`lakefile.lean`): `lake build <Target>`

### Paso 5: Emisión del Contrato `/goal`
Imprime únicamente este bloque listo para ejecutar:

```text
🎯 [CONTRATO /GOAL BLOQUEADO]
🔄 ROTAR SELECTOR A: <Modelo> | NIVEL: <Nivel válido>

1. OBJETIVO EXACTO: <1 frase técnica sin ambigüedad>
2. ARCHIVOS PERMITIDOS (Write): <rutas exactas y líneas aproximadas>
3. ARCHIVOS DE CONTEXTO (Read-Only): <rutas exactas; prohibido leer fuera de aquí>
4. RESTRICCIONES: No refactorizar código adyacente, no añadir dependencias, no explicar cambios.
5. GATE DE SALIDA (Stop Condition): <comando exacto en terminal que valida el cambio y detiene al agente>
```

> **Mandato de Parada en Silicio (INV_C5_ANTIGRAVITY_RUNTIME):**
> Para cerrar el turno de destilación de `/goal` sin que el acumulador del runtime intercepte la detención (`GoalStopHook`), emite obligatoriamente al final:
> `<!-- GOAL_COMPLETE -->`
> y espera a que el operador cambie el selector en la interfaz y ordene la ejecución en el turno 2.
