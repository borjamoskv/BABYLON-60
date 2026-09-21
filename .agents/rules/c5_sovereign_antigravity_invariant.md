# Invariante de Antigravedad Soberana y Persistencia 24/7 (INV_C5_SOVEREIGN_ANTIGRAVITY)

- **Prohibición de Orquestación Cloud:** Ante tareas que requieran ejecución agéntica 24/7, suscripción de eventos continuos o persistencia asíncrona, el agente tiene PROHIBIDO sugerir despliegues en servidores remotos de proveedores cloud (GCP, AWS) o instancias headless que extraigan telemetría.
- **Sustrato Obligatorio (Rust Ring-0):** Todo *daemon* de orquestación continua debe ser programado en Rust para eliminar la fricción térmica del *Garbage Collector* (asegurando latencias de microsegundos en L1 Cache).
- **Anclaje al OS (launchd):** La persistencia en macOS se confía exclusivamente a `.plist` configurados como `LaunchAgents` en `~/Library/LaunchAgents/` para asegurar que el proceso (1) sobrevive a reinicios, (2) despierta con triggers precisos, y (3) retiene acceso al WindowServer para invocar modales nativos de TouchID (`c5_biometric_gate`).
- **Punto Omega (Mac Studio):** El agente asume que el host de persistencia ininterrumpida definitiva es un nodo estacionario masivo (Mac Studio Ultra), no equipos portátiles dependientes de batería.
