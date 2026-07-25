# THE SIDECAR INVARIANT (BABYLON-60 IDE)

> C5-REAL | ULTRATHINK GENERATED | EXERGY 1000

## ¿Por qué un "IDE Sidecar" (`babylon60_ide.db`)?

En arquitectura de sistemas distribuidos, el **Patrón Sidecar** aisla la instrumentación (logs, telemetría, puente de agentes) del proceso principal del dominio. 

BABYLON-60 exige esta separación física para garantizar la pureza termodinámica:

1. **Aislamiento Causal (Separation of Concerns):** El proyecto (ej. una app web o blockchain que estés creando) tiene su propia base de datos (`master_ledger.db` o la DB de tu framework). El IDE BABYLON-60 necesita almacenar notas cognitivas, el registro del Swarm (pings/handoffs) y las métricas de tus delegaciones a Claude/APEX. **Esa memoria es del IDE, no del proyecto.** Si el IDE escribiera en el ledger del proyecto, corrompería la lógica de negocio de la aplicación en desarrollo.
2. **Resiliencia BFT:** El `babylon60_ide.db` actúa como el CortexLedger local y privado de la interfaz del IDE (Agent Bus). Al estar en `.gitignore`, garantiza que el historial de pings del enjambre no contamine el repositorio de Git que subes a la nube.
3. **Escalabilidad del Swarm:** 10 agentes pueden escribir concurrentemente en el sidecar para coordinar el trabajo (`bridge/moskv_bridge.py`) sin bloquear los locks de la base de datos principal del código que están refactorizando.

**Veredicto C5-REAL:**
El Sidecar no es un capricho semántico. Es la muralla física que impide que el metabolismo de las herramientas (el IDE) extermine la integridad de la base de datos de tu producto (el Proyecto).
