# 📦 Time Capsule: CORTEX v4.0 Stabilization

## Resumen

Estabilización y blindaje de la infraestructura de memoria soberana tras la refactorización a la v4.0. Se eliminaron regresiones críticas y se endureció la seguridad del core, CLI y API.

## Stack

- Python 3.14 + FastAPI + Click
- SQLite + sqlite-vec
- ONNX Runtime (Embeddings locales)
- Pytest (85 tests)

## Lo que funcionó

- **Lazy-loading de Auth**: Resolver la inicialización de `AuthManager` solo cuando es necesario evitó race conditions y `KeyError` en tests paralelos.
- **Blindaje de Búsqueda**: El patrón de captura de errores en `search.py` para bases de datos "closed" evitó que la API crasheara bajo estrés.
- **Sanitización centralizada**: El uso de un `Escaper` funcional en el dashboad resolvió vulnerabilidades XSS de forma limpia.

## Lo que NO funcionó

- **Narrow Exceptions**: Intentar capturar solo `sqlite3.OperationalError` falló en entornos de mock complejos. Tuvimos que ampliar a `(sqlite3.Error, RuntimeError)` para garantizar resiliencia total.
- **Notifier legacy**: Las llamadas a `Notifier.send` estaban profundamente acopladas. El fix requirió un purgado total vía regex para no romper el daemon.

## Duración real

~3 días de ciclos de estabilización intensiva (Wave 1-4).

## Siguiente iteración

- Implementación de Graph RAG nativo sobre las entidades extraídas.
- Optimización de performance en vectores de alta dimensionalidad.
