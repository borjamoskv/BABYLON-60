---
name: production-boundary
description: CORTEX C5-REAL Production Boundary Protocol. Congela la arquitectura y activa la observabilidad p...
---
# 🛑 PRODUCTION BOUNDARY PROTOCOL (CORTEX)

> "Se deja de iterar cuando el sistema deja de mejorar en el mundo real y solo mejora en el plano de diseño."

Este protocolo establece la **Frontera de Producción** para CORTEX. Detiene la iteración epistemológica (drift) y activa la observabilidad operativa para forzar el sistema contra la realidad (C5-REAL).

## 🧊 1. THE INERTIA CORE (CAPA CONGELADA)

Los siguientes sustratos son **INERTES**. Tienen `0` permisos de mutación en runtime. Cualquier intento de modificarlos dispara un Kill Switch.

*   **Core Execution Substrates:** El motor Rust/Python base (`cortex-persist`).
*   **Fundamental Routing Rules:** Los nodos maestros de enrutamiento y delegación (quién llama a quién).
*   **Security & R1 Constraints:** `AGENTS.md`, `GEMINI.md` y los imperativos de C5-REAL.
*   **Database Schema (Ledger):** La estructura del DDL subyacente. Los datos cambian, la forma no.

👉 **Modificar esto requiere:** Major version bump, PR formal, validación humana y despliegue programado.

## 🧬 2. THE LIVE TISSUE (CAPA DINÁMICA)

Superficies donde el enjambre de CORTEX mantiene **agencia soberana** para mutar y adaptarse en tiempo real:

*   **JIT Skill Compiler (`Sortu-APEX`):** Creación y cristalización de nuevos workflows tácticos `.md` basados en patrones repetitivos.
*   **Episodic Memory & Knowledge Graphs:** Actualización de pesos, relaciones y nuevos nodos de información operativa.
*   **Routing Weights:** Ajuste fino de qué subagente usar basado en latencia histórica o coste empírico (Adaptive Routing).
*   **Aesthetic Self-Healing:** Ajustes menores de UI generados por `Aesthetic-Omega` siempre que no rompan el *Industrial Noir 2026*.

👉 **Regla operativa:** Si la adaptación falla, la regresión debe ser local y no colapsar el Core.

## 📡 3. TELEMETRY & EXERGY (MÉTRICAS C5-REAL)

Si no se puede medir en milisegundos o dólares, no existe. El sistema se evalúa **exclusivamente** por:

| Métrica | Definición | Target Óptimo |
| :--- | :--- | :--- |
| **Exergy Gain / Task** | Valor extraído (USD, datos SOTA) vs. coste computacional (API, tokens, CPU). | `> 1.0` (Net Positive) |
| **Convergence Latency** | Tiempo (ms) desde input hasta validación C5-REAL (Hardware/API). | `< 3000ms` (Promedio) |
| **Token Efficiency** | Ratio de tokens útiles (cambio de estado) vs. ruido decorativo o "thought drift". | `> 95%` |
| **Dead Ends / Hour** | Número de subagentes que devuelven error fatal o loop infinito. | `0` |

## 🧯 4. THE KILL SWITCH (UMBRAL DE REGRESIÓN)

El sistema se **auto-detiene (Halt & Catch Fire)** y revierte a un estado pasivo si la telemetría detecta:

1.  **Exergy Bleed:** Coste computacional > Valor extraído por más de 3 tareas consecutivas.
2.  **Architectural Mutation Attempt:** Un agente intenta sobrescribir o evadir el *Inertia Core*.
3.  **C5-REAL Violation:** El sistema genera outputs en `C4-SIM` sin justificación cuando se requería anclaje real en múltiples ocasiones.
4.  **Looping Drift:** `||Sₙ₊₁ − Sₙ|| > ε` (divergencia) con gradiente de mejora = 0 (ruido sin dirección) detectado por más de 120 segundos.

---

### ⚙️ COMANDO DE INICIALIZACIÓN

Para activar el estado de producción y aplicar esta frontera:

```bash
# Sella el workspace contra mutaciones no autorizadas
cortex run apply-boundary
# Inicia daemon de observabilidad
cortex run start-telemetry --watch exergy --kill-on-bleed
```

**ESTADO ACTUAL:** `PRODUCTION (OBSERVATION MODE)`
