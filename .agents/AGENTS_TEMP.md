<!-- C5-REAL EXERGY CERTIFIED -->
## Invariante de Aritmética Determinista en Ring-0 (Prohibición de f32/f64)
- **Prohibición de Punto Flotante:** Queda estrictamente prohibido el uso de tipos de punto flotante (`f32`, `f64`) en cualquier estructura de datos, cálculo de métricas (ej. riesgo) o lógica de estado que forme parte del Kernel Rust (Ring-0) o que deba ser atestada criptográficamente (SCITT).
- **Justificación Termodinámica:** La aritmética IEEE 754 introduce entropía no determinista dependiente del compilador y el hardware (redondeos espurios, manejo de NaN). Esto corrompe el isomorfismo estricto de transición y rompe el consenso de firmas criptográficas entre nodos.
- **Resolución Obligatoria:** Toda variable continua DEBE mapearse inexcusablemente a **aritmética de punto fijo (Fixed-point)** o **enteros escalados (`u32`, `u64`, `u128`)**, garantizando reproducibilidad bit a bit (bit-perfect determinism) en todas las arquitecturas (`x86_64`, `aarch64`, WASM).
