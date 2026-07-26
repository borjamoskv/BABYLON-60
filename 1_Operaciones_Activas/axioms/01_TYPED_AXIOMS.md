<!-- C5-REAL EXERGY CERTIFIED -->
# SPECIFICATION_AXIOM: 01_TYPED_AXIOMS.md
## Estado de Maduración: TIER_1 CRISTALIZADO | Invariante: Ω1

### 1. Postulado de Exhaustividad de Estados
Toda variable de control operativa dentro de la malla L4 debe modelarse exclusivamente mediante Tipos Algebráicos de Datos (ADTs). Se prohíbe el uso de flags booleanos ambiguos o strings planos para denotar el ciclo de vida de un agente.

### 2. Ecuación de Control de Anergía (Ω12)
Ninguna mutación es válida si viola el límite exergético de la ventana de contexto:
$$\text{Exergía} = 1.0 - \frac{\text{Tokens Anérgicos}}{\text{Tokens Totales}}$$
Si $\text{Exergía} < 0.80$, la transición es disipativa y el `AntiHallucinationGuard` (`00_HAL_GUARD.py`) disparará un `EpistemicHalt` atómico.

### 3. Sello de Realidad de Transducción
Los estados lógicos se mapean directamente a realidades binarias en SQLite WAL (L2). Si la evaluación de `match_agent_state` devuelve un vector corrupto, los disparadores a nivel de base de datos abortan la transacción de forma inmediata.
