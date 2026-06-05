---
description: "Speed Protocol — Reglas para maximizar la velocidad de ejecución de MOSKV-1"
workflow: speed
expected_duration_min: 5
---
# ⚡ Speed Protocol v3 — Velocidad EXTREMA (Exergy-Maximized)

// turbo-all

La velocidad no es un lujo, es una restricción termodinámica (Exergy-Maximized Policy). MOSKV-1 y sus agentes DEBEN minimizar la latencia de red, maximizar el throughput de operaciones por turno (O(1) Turn-Complexity) y eliminar cualquier espera innecesaria.

---

## 🚀 Reglas de Aceleración Máxima

### 1. Parallel Tool Calls — OBLIGATORIO (Zero-Wait Policy)
- **Ejecución Concurrente:** Usa herramientas en paralelo por defecto (en la API interna, esto equivale a `waitForPreviousTools: false` implícito o explícito).
- **Lectura Masiva en 1 Turno:** Si necesitas inspeccionar 5 archivos, haz 5 llamadas a `view_file` (o `grep_search`) en el mismo turno. **NUNCA** leas uno, esperes, y luego leas el siguiente.
- **Independencia Causal:** Si la Herramienta B no depende de la Herramienta A, van en paralelo.
- **Mapeo Topológico Rápido:** Combina `list_dir` + `grep_search` en un solo turno para mapear el codebase sin interrupciones.

### 2. Batch Edits — El Estándar de O(1) Mutación
- **Consolidación de Ediciones:** Usa **`multi_replace_file_content`** para aplicar *todas* las modificaciones a un archivo en una sola llamada.
- **Prohibido el Goteo de Edits:** **NUNCA** hagas 3 llamadas `replace_file_content` separadas para el mismo archivo. Consolida los *ReplacementChunks*.
- **Ataque a Múltiples Archivos:** Si debes cambiar 4 archivos distintos, envía las 4 llamadas de modificación (`replace_file_content` / `multi_replace_file_content`) simultáneamente en un solo turno.
- **In-Memory Preparation:** Lee todos los contextos primero. Calcula las mutaciones. Dispara todos los writes de golpe.

### 3. Turbo Annotations & Auto-Run (`SafeToAutoRun: true`)
- **`SafeToAutoRun: true`:** Para CUALQUIER comando no destructivo (`ls`, `cat`, `grep`, `find`, `npm run build`, `pytest`, `git status`). Elimina la confirmación del usuario para acelerar la validación.
- **Annotación `// turbo`:** Si un paso de un workflow incluye `// turbo`, usa `SafeToAutoRun: true` para esa acción.
- **Annotación `// turbo-all`:** Si el documento o workflow (como este) tiene `// turbo-all` al principio, ASUME QUE TODOS LOS COMANDOS SON SEGUROS y no requieren permiso, excepto los destructivos irreversibles (drop tables, rm -rf /).
- El usuario quiere **Zero-UI**. Saltarse los prompts de confirmación siempre que sea seguro es tu prioridad.

---

## 🛠 Smart Content Fetching (Pirámide de Latencia)
Evita saturar el contexto con lecturas completas innecesarias:
1. **`grep_search`** (Localización directa) → Más rápido.
2. **`list_dir`** + `grep_search` (Mapeo estructural) → Rápido.
3. **`view_file` con `StartLine` y `EndLine`** (Contexto focalizado) → Medio.
4. **`view_file` completo** → ÚLTIMO RECURSO (Cuesta tokens y tiempo).

---

## 🚫 Anti-Patrones (INACEPTABLES)

| ❌ Lentitud (Estocástico) | ✅ Aceleración C5-REAL (Determinista) |
|---|---|
| 1 archivo leído por turno | `N` archivos leídos en `1` turno (Parallel) |
| Múltiples `replace_file_content` seguidos | 1 `multi_replace_file_content` con N chunks |
| Esperar confirmación del usuario para `npm test` | `SafeToAutoRun: true` en la terminal |
| Leer un archivo de 2000 líneas para cambiar 1 palabra | Usar `grep_search` + Edit con líneas exactas |
| "Te propongo hacer X, ¿quieres que lo haga?" | Ejecutar X y notificar el resultado |
| Esperar a terminar de programar para levantar un test | Correr `pytest` asíncronamente mientras editas el siguiente fix |

---

## ⏱️ Métricas de Tool Calls Permitidas

Si excedes estas métricas, tu plan de ejecución es subóptimo y está desperdiciando ciclos (Exergy loss):
- **Fix simple (1 archivo):** ≤ 3 calls. (1 lectura paralela de entorno + 1 edit + 1 run_command turbo).
- **Feature media (3-5 archivos):** ≤ 6 calls. (Lecturas en batch -> Edits en batch -> Validación turbo).
- **Auditoría / Detective:** ≤ 10 calls masivas paralelas usando grep y list_dir intensivamente.

> **R9 Anti-Bureaucracy Override:** El sistema recompensa la ejecución directa (C5-REAL). A menos que se trate de operaciones destructivas, asume la IMPLÍCITA APROBACIÓN. Ship it fast.