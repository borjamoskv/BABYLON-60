<!-- C5-REAL EXERGY CERTIFIED -->
# Reglas del Proyecto Teorema Robinson-Moskv

## Invariante C5-REAL: Anclajes de Red y Atestación No Bloqueantes
- **Prohibición de I/O Síncrono de Red en Hilo Principal**: Cualquier operación de atestación externa (OpenTimestamps, llamadas a APIs lejanas, sello en Bitcoin L5) invocada desde bucles de trabajo (*workers*, CI local, pre-commits) DEBE ser asíncrona o delegada a subprocesos desvinculados (*fire-and-forget*).
- **Protección de Concurrencia por Candado (In-Flight Lock)**: Toda tarea asíncrona delegada en segundo plano sobre archivos/hashes DEBE implementar un candado atómico (`.lock`) para evitar la acumulación de subprocesos duplicados durante iteraciones rápidas.
- **Caché LRU sobre Merkle Trees de Git**: El cálculo de digests SHA3-256 sobre el estado del árbol de código (`git ls-tree`) DEBE estar memorizado (ej. `@functools.lru_cache`) por hash de commit para evitar recorridos de I/O de disco innecesarios en repositorios de gran escala.
