# 📦 Time Capsule: cortex-persist

## Resumen
Refactorización y blindaje de la arquitectura de persistencia (`cortex-core/persistence.py`). Se aniquiló el riesgo de *Thread Exhaustion* y cuellos de botella I/O mediante un Patrón Outbox asíncrono sobre SQLite (WAL), securizando el enjambre de 10.000 agentes contra SSRF y ataques temporales (Time-Jacking).

## Stack
- Python 3.14 (Asyncio, ThreadPoolExecutor)
- SQLite (PRAGMA journal_mode=WAL)
- Criptografía Hashing (SHA-256 Monotónico L2)

## Lo que funcionó
- **Patrón Outbox**: Desacoplar la ingestión (I/O síncrono rápido) del envío a NEXUS (red asíncrona) liberó la RAM y los hilos del OS (de 10.000 teóricos a 16 reales).
- **Thread-Local Pool**: Usar `threading.local()` para aislar conexiones a SQLite aniquiló los bloqueos concurrentes.
- **Offload del Event Loop**: Trasladar cálculos pesados (Decay VSA y Tar Snapshots) a `run_in_executor` impidió micro-bloqueos en el bucle principal.

## Lo que NO funcionó
- **Threading Puro Inicial**: El enfoque de lanzar un hilo de OS por cada `enqueue_swarm_task` era entrópico e insostenible para un enjambre real. Fue completamente aniquilado y reescrito.

## Duración real
~4 Sesiones de Trabajo (Hardening, Refactor, Stress Test C5-REAL, Securización L2).

## Siguiente iteración
- Mover el ledger criptográfico hacia un secuenciador verdaderamente inmutable y distribuido si la red de agentes trasciende la máquina host.
- Integración de los métricos C5-REAL (Health Dashboard) en un panel frontend usando el ecosistema *Mac-Control-OMEGA*.
