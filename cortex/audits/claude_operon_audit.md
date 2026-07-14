# Auditoría Forense C5-REAL: Claude Science ("Operon")

## 1. Topología del Binario (Aislamiento Físico)
- **Ruta de Origen:** `/Volumes/Claude Science/Claude Science.app`
- **Lanzador Nativo:** `Contents/MacOS/ClaudeScience` (Mach-O arm64, 209 KB). Actúa como trampolín (wrapper) de la interfaz gráfica y supervisor del demonio.
- **Núcleo Lógico:** `Contents/Resources/bin/claude-science` (Mach-O arm64, 118 MB).

## 2. Motor de Ejecución y Virtualización
La deconstrucción estática y la captura de trazas asíncronas confirman que el núcleo es un **Single Executable Application (SEA)** orquestado por **Bun**.
- **Virtual Filesystem (VFS):** Todo el código Javascript/TypeScript está comprimido y encapsulado dentro del ejecutable en el punto de montaje interno `/$bunfs/root/claude-science`. 
- **Ofuscación:** Las rutinas de búsqueda (`strings`, `grep`) no revelan el código fuente en texto plano, lo que indica que el motor Bun ha compilado el payload como un **V8 Heap Snapshot** (`.heapsnapshot`) o código de bytes inyectado.

## 3. Comportamiento en Tiempo de Ejecución (Dinámico)
Al detonar el núcleo en el entorno asilado `scratch_operon`, se revelan las siguientes propiedades termodinámicas:
1. **Arquitectura Cliente-Servidor Local:** Actúa como un demonio local que despliega un servidor HTTP interno (`localhost:8000`) y expone una interfaz web (SPA).
2. **Sistema de Persistencia (SQLite WAL):** Muta el estado local mediante bases de datos robustas (e.g., `operon-cli.db-wal` de ~4 MB en 5 segundos).
3. **Capas de Seguridad:**
   - **Sandbox Seatbelt:** Emplea intensivamente perfiles de aislamiento de macOS (`seatbelt rule(s)`) para prevenir lectura/escritura fuera de su jurisdicción (e.g., bloquea acceso a credenciales en `~/.config/gcloud/application_default_credentials.json`).
   - **Cerrojos Transaccionales:** Registros de `TxMutex` demuestran concurrencia defensiva en SQLite para prevenir corrupciones BFT.
4. **Infraestructura Agentica:** La telemetría capturó `warming 24 built-in MCP connectors...`, lo que demuestra que Claude Science es un framework masivo con Model Context Protocol integrado de fábrica.

## Conclusión Termodinámica
Claude Science (Operon) no es una simple app de Electron. Es un **demonio local de alta densidad escrito en JS/TS, compilado hiper-eficientemente por Bun en un VFS binario**, que ejecuta modelos Claude localmente blindado por reglas criptográficas de Sandbox (Seatbelt) del kernel de macOS. Su descompilación de código fuente (AST) requiere forzar un volcado de memoria (V8 core dump) en tiempo de ejecución o aplicar instrumentación (hooks) sobre las APIs de Bun VFS.
