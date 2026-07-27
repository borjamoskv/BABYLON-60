# Tolerancia a Fallos y Concurrencia (Motor 0-Lock)

- **Deadlock por Defecto**: Cualquier I/O síncrono en un loop asíncrono es un crimen contra el event loop.
- **Invariante de SQLite WAL**: journal_mode=WAL y busy_timeout=5000. Jamás se bloquea un lector por un escritor.
- **Cuarentena de Veneno (Dead-Letter)**: Las transacciones corruptas no se descartan, se aíslan para análisis forense.
- **Idempotencia Absoluta**: Ejecutar una operación 1 vez o 1,000 veces debe resultar en exactamente el mismo estado (Hash idéntico).
- **Invariante de Saga**: Todo avance (N) tiene su retroceso exacto (N-1) garantizado por el sistema.
- **Consenso Quorum (N=3)**: Ningún agente soberano altera el master ledger sin la validación matemática de al menos dos pares independientes.
- **Desacoplamiento Espacial**: Los hilos no comparten memoria; se comunican exclusivamente pasando mensajes inmutables.
- **Time-to-Recovery (TTR) < Time-to-Failure (TTF)**: El sistema debe reiniciar micro-servicios más rápido de lo que tardan en colapsar en cadena.
- **Throttling Estocástico**: Los reintentos sin backoff exponencial (Jitter) generan ataques DDoS autoinfligidos.
- **Circuit Breakers Agresivos**: Fallar rápido (Fail-Fast) es superior a esperar lentamente la muerte por timeout.
