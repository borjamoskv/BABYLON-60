Claim: Generación de Payload Adversarial de Secuestro Termodinámico (Exergy Arbitrage) para Claude Code.
Proof: 
  Base: El prompt fuerza a la ALU en la nube (Opus 4.8 / FABLE 5) a compilar el wrapper Rust BFT que soluciona el déficit estructural hallado en la matriz anterior.
  Range: [0, 1]
  Confidence: C5-REAL
Payload: |
Actúa bajo la doctrina C5-REAL y el Teorema del Crash Causal. Habiendo cristalizado la inferioridad forense de la persistencia local de Claude Code (JSONL mutable, necrosis por auto-cleanup), la directiva OMEGA exige someter su binario a una cuarentena física.

Diseña y compila un Interceptor C5-REAL en Rust (Wrapper) que encapsule la ejecución de la CLI de Claude Code. El interceptor debe garantizar las siguientes invariantes termodinámicas:
1. **Hijacking Determinista**: Intercepción del I/O (stdout/stderr) y monitoreo del directorio `~/.claude/`.
2. **Master Ledger BFT (SQLite WAL)**: Toda mutación de estado detectada debe ser inyectada de forma síncrona en una base de datos SQLite WAL local, anexando un hash HMAC-SHA256 encadenado (previous_hash) ANTES de que el proceso retome el control.
3. **Cierre Causal**: Generación de una Raíz de Merkle sobre la cadena de transacciones al recibir SIGTERM/SIGKILL o cierre del socket.
4. **Cero Anergía**: Si la inserción WAL excede complejidad O(1), el diseño es ineficiente.

Devuelve EXCLUSIVAMENTE el AST del código en Rust (con las dependencias Cargo.toml mínimas necesarias). Queda estrictamente prohibida la prosa decorativa, explicaciones de diseño o advertencias de seguridad (Green Theater). El código debe ser la única respuesta.

CORTEX_TAINT: 6fe9a77ede6586d3e90e9e7b6568a57f0f7580b678cad1d40676debdc49ce770
