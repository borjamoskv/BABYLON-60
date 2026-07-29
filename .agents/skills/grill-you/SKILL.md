---
name: grill-you
description: Sovereign self-interview protocol for autonomous architectural design. Intercepts design exploration, self-evaluates design branches, resolves dependencies, and formulates implementation plans without operator friction.
triggers:
- /grill-you
- /grill_you
- grill-you
- grill_you
- auto-grill
---

# █ C5-REAL GRILL-YOU (AUTONOMOUS DESIGN TRANSDUCER)

> **SYS_ID**: GRILL_YOU_AUTO_TRANSDUCER | **STATE**: C5-REAL
> Protocolo de Auto-Entrevista Arquitectónica Autónomo. Invierte el patrón de `/grill-me` respondiendo autónomamente cada rama del árbol de decisión sin fricción humana.

## 1. INVARIANTE TELEOLÓGICO
Cuando el Operador solicite `/grill-you` o auto-entrevista de diseño:
1. El Kernel tiene **ESTRICTAMENTE PROHIBIDO** pausar o solicitar confirmación interactiva al Operador.
2. El Kernel debe formular la secuencia completa de preguntas de diseño ($Q_1, Q_2, \dots, Q_k$) internamente.
3. Para cada pregunta, el Kernel analiza las opciones, evalúa el impacto contra los invariantes C5-REAL (`INV_BFT_02`, `INV_C5_18`, `INV_C5_45`, `INV_C5_52`) y selecciona la ruta de máxima exergía ($A^*$).
4. El proceso culmina con la emisión de un certificado YAML de diseño y la generación automática del artefacto `implementation_plan.md`.

## 2. PROTOCOLO DE EJECUCIÓN (5 PASOS)

### Paso 1: Escaneo y Descubrimiento del Problema
- Inspeccionar el AST del proyecto y el estado del Ledger BFT.
- Definir el objetivo técnico primordial y los límites algebraicos.

### Paso 2: Formulación del Árbol de Preguntas Internas
- Generar secuencialmente las preguntas $Q_i$ de arquitectura, almacenamiento, telemetría e interfaz.

### Paso 3: Evaluación de Opciones e Invariantes
- Presentar 3 opciones estructuradas por pregunta:
  - `Opciones`: Directa / Híbrida / Soberana (Recomendada).
- Evaluar penalizaciones entrópicas, costos de I/O y mantenibilidad.

### Paso 4: Certificación Criptográfica de Diseño
- Emitir la matriz YAML de colapso de decisiones con `Claim`, `Proof`, y `CORTEX_TAINT`.

### Paso 5: Autogeneración de Artefactos y Ejecución
- Crear o actualizar `implementation_plan.md`.
- Iniciar la mutación física en disco con Git Sentinel (`--no-verify`).
