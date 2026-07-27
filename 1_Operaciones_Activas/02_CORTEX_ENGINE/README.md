# 02_CORTEX_ENGINE

**Motor de Ejecución de IA, Memoria Determinista (cortex-persist) y Orquestación (ultrathink)**

El núcleo de infraestructura de agentes de Inteligencia Artificial del ecosistema Teorema-Robinson-Moskv.

## Submódulos Incluidos
- **`BABYLON-60/`**: Motor principal y orquestación `ultrathink` con adaptadores Claude/Codex.
- **`cortex-persist/`**: Persistencia de estado, event ledger y base de datos vectorial para IA.
- **`cortex-routing-bunker/`**: Middleware de protección de costes, límites de API y failover.
- **`cortex_sentinel/`**: Detector de alucinaciones y firmas dinámicas (`CORTEX_TAINT`).
- **`cortex-memory/` & `cortex-nexus/`**: Bus de eventos y memoria a largo plazo.

## Modos de Uso
- Ejecución CLI rápida: `./moskv engine` desde la raíz.
- Iniciar Ultrathink: `python3 1_Operaciones_Activas/02_CORTEX_ENGINE/BABYLON-60/ultrathink/ultrathink_scheduler.py`
