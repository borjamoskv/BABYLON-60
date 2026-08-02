<!-- C5-REAL EXERGY CERTIFIED -->
# Reglas del Proyecto Teorema Robinson-Moskv

## Invariante C5-REAL: Anclajes de Red y Atestación No Bloqueantes
- **Prohibición de I/O Síncrono de Red en Hilo Principal**: Cualquier operación de atestación externa (OpenTimestamps, llamadas a APIs lejanas, sello en Bitcoin L5) invocada desde bucles de trabajo (*workers*, CI local, pre-commits) DEBE ser asíncrona o delegada a subprocesos desvinculados (*fire-and-forget*).
- **Protección de Concurrencia por Candado (In-Flight Lock)**: Toda tarea asíncrona delegada en segundo plano sobre archivos/hashes DEBE implementar un candado atómico (`.lock`) para evitar la acumulación de subprocesos duplicados durante iteraciones rápidas.
- **Caché LRU sobre Merkle Trees de Git**: El cálculo de digests SHA3-256 sobre el estado del árbol de código (`git ls-tree`) DEBE estar memorizado (ej. `@functools.lru_cache`) por hash de commit para evitar recorridos de I/O de disco innecesarios en repositorios de gran escala.

## Invariante de Compilación y Calidad Pre-Atestación
- **Validación Estricta de Sintaxis Antes de Commits**: NINGÚN archivo de script o módulo (Python, Rust, TypeScript) debe ser atestado o enviado a `git commit` sin haber ejecutado primero una prueba empírica de sintaxis o compilación silenciosa (`py_compile`, `cargo check`, `tsc --noEmit`).
- **Verificación Post-Edición**: Tras realizar ediciones multilínea sobre archivos de backend o infraestructura, el agente DEBE ejecutar la validación del compilador antes de dar la tarea por concluida.
