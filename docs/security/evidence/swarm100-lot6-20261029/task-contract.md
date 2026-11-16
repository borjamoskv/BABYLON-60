# Contrato — Lote 6 (29/10/2026, Europe/Madrid)

Corregir C0132/C0133 únicamente en
01_KISH_ENGINE/babylon60/kernel/swarm_orchestrator.py. Tests/evidencia/registro
y plan del Lote 7 permitidos; Lote 7 no aplicado. Conservar cambios ajenos,
consumidores, límites de reintento/cancelación y circuit breaker.

Ring-0: frontera de autorización/destino; Ring-1: reproducciones y controles
acotados; Ring-2: Git/registro; Ring-3: CLI/documentación. Rechazar selector y URL
antes de cliente/credenciales/env; validar configuración explícita y despacho.
Retener API .api_key del consumidor. Snapshot por llamada y rechazo redirects.

Fixtures con entorno sintético y dotenv bloqueado antes de importar. HTTPX
MockTransport y bloqueo de sockets: ninguna red, proveedor/credencial real,
servicio nativo, hardware o ATTESTED. Los positivos solo prueban routing/headers
y comportamiento del SDK en memoria, no TLS/DNS/servicio remoto reales.

Aceptación: red/green por ID, URL malformada/userinfo/host/esquema/puerto,
valores locales/remotos válidos, mutación durante retry, 307 y proxy ambiental,
respuestas/errores sin eco de secretos. Suites relacionadas, revisión
independiente, Ruff/MyPy y controles documentales; registro con hashes.
Grafo no expuesto: búsquedas acotadas. Sin dependencias/lockfiles/commits/push.
