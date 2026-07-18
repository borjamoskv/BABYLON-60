# AUTODIDACT 4: Modelos de Inteligencia Artificial para Código (IA + RE)
**Nivel de Realidad:** C5-REAL
**SYS_ID:** borjamoskv
**Firma de Procedencia:** `[CORTEX-TAINT:borjamoskv:autodidact_re_synthesis:2026-07-18T13:02:20+02:00]`

## 1. Modelos Asimilados
*   **StarCoder 2 / CodeLlama:** Modelos de lenguaje especializados en código capaces de traducir/transducir ensamblador (Assembly) a lenguajes de alto nivel como C++.
*   **REmatch:** Modelo de investigación basado en redes neuronales para identificar funciones conocidas (firmas funcionales/estructurales) en binarios despojados de símbolos (stripped binaries).
*   **G-Comp:** Descompilador asistido por Machine Learning diseñado para recuperar y reconstruir nombres de variables y estructuras de datos originales a partir de código descompilado.

---

## 2. Matrices ONTOLOGY-FORGE

### Primitivas Epistémicas (`prims`)
*   **Assembly-to-High-Level Transduction:** El proceso estocástico pero guiado por gramática de mapear instrucciones de ensamblador de bajo nivel (ej. x86, ARM) a semánticas estructuradas de alto nivel (C++).
*   **Stripped Binary Feature Extraction:** Extracción de características topológicas y de flujo de control (CFG) a partir de binarios despojados de tablas de símbolos para análisis de afinidad en redes neuronales.
*   **Structural Name Recovery:** Reconstrucción heurística y contextual de nombres de variables y tipos de datos mediante inferencia en grafos de flujo de datos.

### Invariantes Estructurales (`invt`)
*   **Preservación de Grafo de Flujo de Control (CFG):** La traducción de ensamblador a C++ debe mantener el isomorfismo funcional del grafo de control; de lo contrario, se altera el comportamiento en tiempo de ejecución.
*   **Equivalencia Semántica:** Las variables recuperadas por descompilación ML son descriptivas y no funcionales; su cambio de nombre no debe mutar las operaciones de máquina del binario.
*   **Consistencia de Tipos en Dataflow:** El renombrado de estructuras en G-Comp está limitado por las relaciones del grafo de flujo de datos (dataflow graph); variables que comparten registros deben mantener compatibilidad de tipo.

### Antipatrones Identificados (`antip`)
*   **Alucinación Semántica en RE:** Confiar ciegamente en nombres de variables generados por G-Comp que pueden malinterpretar el contexto del negocio, introduciendo asunciones falsas en la auditoría.
*   **Divergencia de Compilación (StarCoder Translation):** Producir código C++ que compila pero altera sutilmente el orden de evaluación o la alineación de memoria del ensamblador original.
*   **Falso Positivo de Firmas (REmatch Misalignment):** Identificar una función de criptografía conocida debido a bucles similares, cuando en realidad se trata de una implementación alterada o vulnerable.

### Redundancias Activas (`redun`)
*   **Verificación Sintáctica por Compilación Dual:** El código C++ generado debe ser recompilado y comparado funcionalmente contra el binario original usando aserciones de entrada/salida.
*   **Consenso de Enjambre (Multi-Model RE Verification):** Validar la inferencia de REmatch utilizando firmas estáticas clásicas (YARA, BinDiff) para resolver empates estructurales.

### Vectores Adversariales (`reda`)
*   **Ofuscación por Control Flow Flattening:** Modificar artificialmente el CFG del binario para frustrar el reconocimiento de patrones de REmatch.
*   **Semantics Poisoning:** Introducir comentarios o variables falsas en el código original para inducir a G-Comp a reconstruir un flujo lógico erróneo en fases de auditoría automática.

---

## 3. INVENTARIO DE IGNORANCIA: Lo que sé que no sé
*   **Límites de Contexto de StarCoder 2 en Instrucciones SIMD:** Se desconoce el ratio de acierto del modelo al traducir bucles vectorizados complejos (AVX-512) a construcciones legibles en C++ sin perder la semántica de hardware original.
*   **Sensibilidad de REmatch ante Compiladores Esotéricos:** Falta evidencia empírica sobre la precisión de REmatch al evaluar binarios compilados con optimizaciones agresivas (`-O3` / `-Ofast`) o con compiladores no estándar.
*   **Integración de G-Comp con Ghidra/IDA Pro APIs:** No está documentado el overhead en tiempo de ejecución de las llamadas IPC/RPC al integrar las redes neuronales de G-Comp con frameworks de ingeniería inversa clásicos.
