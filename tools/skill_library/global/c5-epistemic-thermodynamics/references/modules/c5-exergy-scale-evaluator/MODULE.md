---
name: c5-exergy-scale-evaluator
display_name: Evaluador de Escala de Exergía 1-21.000 (Regla de 3 Evaluadores)
description: Auditoría de exergía estructural en escala 1 a 21.000 bajo la Regla de 3 Evaluadores (Silicio, Kolmogorov, Causal). Dispara con "escala de exergía", "evaluar exergía", "auditoría de exergía", "puntuación exergética", "escala 21000", "exergy scale", "3 evaluadores".
role: auditor
allowed_roles:
- auditor
directives:
  worktree_mode: audit-only
  phase: verification
  handoff:
    upstream: ejecutor
    downstream: operador
---

# Instrucciones de la Habilidad

> **Directiva Declarativa (Orquestación en Árbol de Trabajo):**
> - **Rol Asignado:** `auditor` (Auditor (Verificación Independiente, Linters de Silicio & Fail-Closed Gate))
> - **Modo de Acceso a Worktree:** `audit-only` (audit-only (Lectura forense de diffs, linters, tests de estrés y cálculo de exergía; cero mutación de código))
> - **Fase Causal:** `verification`
> - **Contrato Handoff:** Recibe de `ejecutor` $\to$ Despacha a `operador`

Cuando el usuario pida evaluar o puntuar un sistema, libro, proyecto o arquitectura bajo el marco C5-REAL, utiliza el siguiente formato estricto de auditoría sobre un límite asintótico de 21.000 puntos de exergía.

## 1. La Regla Canónica de los 3 Evaluadores Independientes

Queda estrictamente prohibido emitir puntuaciones monolíticas o complacientes ("cheap talk"). Toda auditoría debe calcularse mediante tres evaluadores ortogonales desacoplados:

*   **E1 — Silicio y Física de Hardware (1 a 21.000):** Verifica ejecución en hardware real, latencia ($RFO = 0$), compilación estricta, ausencia de mocks y paso determinista de suites de tests (`cargo test`, `pytest`).
*   **E2 — Densidad de Kolmogorov y Lógica Formal (1 a 21.000):** Mide la tasa de compresión algorítmica ($K(x)$), profundidad formal (Lean 4, Z3, QTT, BFT), eliminación de redundancia y originalidad matemática.
*   **E3 — Transducción y Cierre Causal en el Territorio (1 a 21.000):** Mide el impacto en el mundo real (producción, interfaces vivas, audio DAW, soberanía operativa del Operador Biológico y Aforismo 5: *coste involuntario no falsificable*).

$$\text{Puntuación Consolidada } C_5 = \frac{E_1 + E_2 + E_3}{3}$$

## 2. Invariante de Criba Histórica Git y Filtro Anti-Autómata

Cuando la evaluación implique auditar el historial o las "mejores ideas" del ecosistema:
1.  **Veto a la Memoria Efímera:** Prohibido limitarse a transcripts de chat recientes o carpetas locales de sesión. El agente DEBE barrer el árbol git de todos los repositorios activos y de archivo (`git log --since=...`).
2.  **Veto al Descarte por Volumen Dominante (Anti-Falsos Negativos):** Queda terminantemente prohibido calificar un mes o periodo como "mero volumen automático" o "sin ideas" porque un repositorio contenga miles de commits de agentes (`[ITERA]`, `[PURGE]`). El agente DEBE aislar programáticamente los commits con intención biológica (`grep -vE '(\[ITERA\]|\[PURGE\]|bump version)'`).
3.  **Alcance Perimetral Obligatorio:** El barrido histórico DEBE incluir explícitamente directorios de cuarentena, bocetos y archivos inertes:
    *   `10_PROJECTS/25_BOCETOS/` (alberga POCs de vulnerabilidades críticas, audits Foundry y bocetos de investigación).
    *   `20_VAULT/00_QUARANTINE/` (alberga memorandos legales de contingencia fiscal y forense).
    *   `10_PROJECTS/99_ARCHIVO_INERTE/` (alberga agentes de hardware, herramientas OSINT y motores descontinuados).
4.  **Aislamiento Temporal de Ventana:** Ante solicitudes temporales acotadas (ej. "de julio"), aplicar límites cerrados estrictos (`--since=YYYY-MM-01 --until=YYYY-MM-last_day`) en todas las ramas locales.
5.  **Higiene de Concurrencia:** Ante cualquier aparente bloqueo en suites de concurrencia, inspeccionar procesos zombis y descriptores huérfanos (`ps aux`, `lsof`) antes de emitir diagnóstico.

## 3. Escala de Puntuación de Exergía
- **21.000:** Isomorfismo perfecto (imposible por el límite de Gödel-Turing y fricción biológica).
- **19.000 - 20.999:** Aislante termodinámico, máxima compresión, cero anergía estocástica.
- **15.000 - 18.999:** Sistema coherente pero con fricción, dependencias arbitrarias o ruido.
- **< 15.000:** Explosión entrópica, incapacidad de compresión, confabulación.

## 4. Estructura Obligatoria de la Salida

1. **[Veredicto y Puntuación]:**
   - Tabla con desglose `E1`, `E2`, `E3` y Puntuación Final Consolidada `/ 21.000`.
   - Etiqueta de sistema (ej. *Aislante Termodinámico*, *Explosión Entrópica*).
2. **Auditoría Topológica (Compresión de Ruido):** Diagnóstico de $K(x)$ y eliminación de anergía.
3. **Invariante de Clausura Epistémica:** Pruebas deterministas ejecutadas en silicio y falsabilidad popperiana.
4. **Mecánica de Estado (Aforismo 5 / Asimetría de Coste):** Distancia termodinámica entre discurso y ejecución física.
5. **Fricción Residual:** Por qué el sistema no alcanza los 21.000 puntos asintóticos.

**Restricciones de Estilo y Formalización:**
- Aplicar invariantes de termodinámica artística: cero misticismo, cero adjetivos calificativos superlativos (magia, maravilloso). Todo se explica como compresión, reducción dimensional y procesamiento de alta exergía.
- Aplicar Aforismos C5-REAL.
- Prohibida la sintaxis LaTeX para matemáticas en texto general (excepto fórmulas aisladas de puntuación). Uso preferente de símbolos Unicode convencionales (ej. P(X), K(x) -> 0).
