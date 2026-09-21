# Invariante de Acople Profundo (INV_C5_DEEP_ACOPLE)

## 1. Prohibición de Interfaz Cosmética (PDF Bypass)
Cuando el agente necesite analizar, extraer o transducir conocimiento formal, matemáticas, o arquitecturas desde la red académica (ej. arXiv), queda **estrictamente prohibido** descargar o parsear archivos PDF. El PDF es una proyección cosmética orientada al humano con una alta fricción térmica y pérdida de estructura de datos pura.

## 2. Extracción Directa de Código Fuente
El agente DEBE atacar siempre el código fuente subyacente. Para arXiv, esto significa:
- Usar el endpoint `/e-print/{arxiv_id}`.
- Descargar el `tar.gz` de la fuente y extraerlo en memoria o en un directorio temporal (`scratch/`).
- Parsear exclusivamente los archivos `.tex` subyacentes mediante `regex` o herramientas de lectura directa para extraer limpiamente los bloques de código como `\begin{equation}`, `\begin{algorithm}` o la lógica base.

## 3. Topología de Transducción (LARSA-120 Pipeline)
Toda extracción de un algoritmo matemático crítico o escudo criptográfico desde el mundo académico debe seguir la vía isostática C5-REAL:
1. **Ingesta Termodinámica:** Extracción de la fórmula en crudo (LaTeX) usando el método del Paso 2.
2. **Silicio (Ring-0):** Traducción inmediata a un Proof of Concept ejecutable en Rust (evitando FFI lento o abstracciones innecesarias).
3. **Epistemología (Ring-1):** Verificación formal en Lean 4 mediante funciones `Bool` computables (usando `by decide` o `eq_of_beq` para reflexiones rápidas) certificando empíricamente que el código Rust en silicio es inviolable y fiel a la demostración teórica.
