# Benchmarks

Directiva: Producción de métricas de rendimiento reales para BABYLON-60.

Requisitos:
- Apple M3, 18 GB
- Rust 1.xx, Python 3.13
- 10 millones de eventos, 1000 agentes concurrentes.
- Medición estricta de latencia (P99, P99.9) y throughput absoluto.
- Herramientas: criterion, pytest-benchmark, hyperfine.
