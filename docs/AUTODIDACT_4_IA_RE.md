# AUTODIDACT 4: Modelos de Inteligencia Artificial para Código (IA + RE)
**Nivel de Realidad:** C5-REAL
**SYS_ID:** borjamoskv
**Firma de Procedencia:** `[CORTEX-TAINT:borjamoskv:autodidact_re_synthesis:2026-07-18T13:02:20+02:00]`

## 1. Modelos Asimilados
*   **StarCoder 2 / CodeLlama:** Modelos de lenguaje especializados en código capaces de traducir/transducir ensamblador (Assembly) a lenguajes de alto nivel como C++.
*   **REmatch:** Modelo de investigación basado en redes neuronales para identificar funciones conocidas (firmas funcionales/estructurales) en binarios despojados de símbolos (stripped binaries).
*   **G-Comp:** Descompilador asistido por Machine Learning diseñado para recuperar y reconstruir nombres de variables y estructuras de datos originales a partir de código descompilado.
*   **LLM4Decompile:** Modelo especializado entrenado directamente en decompilación masiva, refinando código ensamblador decompilado hacia código C compilable con alta fidelidad sintáctica.
*   **r2ai / Gepetto / Sidekick:** Frameworks de integración (Radare2, IDA Pro, Binary Ninja) que interactúan localmente o mediante APIs con LLMs para realizar renombrado contextual, análisis heurístico de flujos y generación de explicaciones de algoritmos complejos.
*   **DecompAI (Agentic RE):** Orquestador agéntico basado en grafos de ejecución (como LangGraph) que acopla LLMs con herramientas dinámicas y estáticas (`gdb`, `objdump`) para validar comportamientos de binarios de forma autónoma.

---

## 2. Matrices ONTOLOGY-FORGE

### Primitivas Epistémicas (`prims`)
*   **Assembly-to-High-Level Transduction:** Mapeo de secuencias de instrucciones de bajo nivel a código fuente estructurado de alto nivel preservando el comportamiento.
*   **Stripped Binary Feature Extraction:** Aislamiento de firmas y patrones de flujo sin metadatos simbólicos.
*   **Structural Name Recovery:** Inferencia predictiva de variables y layouts de tipos basada en el flujo de datos.
*   **Iterative Compile-Feedback Decompilation:** Bucle agéntico que compila el código generado por la IA, mide los deltas de comportamiento y re-inyecta el error al modelo hasta converger en semántica correcta.

### Invariantes Estructurales (`invt`)
*   **Preservación de Grafo de Flujo de Control (CFG):** La transducción no debe alterar las bifurcaciones y loops lógicos del binario original.
*   **Equivalencia Semántica:** Las variables inferidas en el mismo registro o slot de memoria deben conservar coherencia algebraica.
*   **Fidelidad de Compilación:** Todo código generado bajo `LLM4Decompile` debe poder ser compilado con el mismo compilador de origen (`gcc`, `clang`) sin provocar errores sintácticos de nivel de AST.

### Antipatrones Identificados (`antip`)
*   **Alucinación Semántica:** Confiar ciegamente en nombres de variables o explicaciones algorítmicas generadas por LLMs sin validación dinámica.
*   **Divergencia Funcional de Re-compilación:** Código generado por IA que es sintácticamente válido pero altera el comportamiento lógico en tiempo de ejecución (ej. condiciones de carrera o desalineación de bytes).
*   **Context Exhaustion:** Sobrecargar la ventana de contexto del LLM inyectando binarios completos en lugar de fragmentar subrutinas aisladas mediante el flujo del CFG.

### Redundancias Activas (`redun`)
*   **Verificación por Compilación Dual:** El código generado se compila y compara funcionalmente mediante casos de prueba automatizados contra el binario original.
*   **Consenso de Enjambre (Multi-Agent Consensus):** Uso de múltiples modelos (ej. Claude 3.7 + GPT-4o) para validar explicaciones de funciones críticas en canales adversariales.

### Vectores Adversariales (`reda`)
*   **Control Flow Flattening:** Ofuscación artificial del flujo para distorsionar la extracción de características de REmatch.
*   **Obfuscated Prompt Injection:** Malware diseñado con payloads que explotan el analizador de código de la IA para comprometer el runtime del host durante la ingeniería inversa automática.

---

## 3. INVENTARIO DE IGNORANCIA: Lo que sé que no sé
*   **Límites de Contexto en Instrucciones SIMD:** Eficacia de StarCoder 2 al traducir bucles vectorizados complejos (AVX-512) a C++.
*   **Sensibilidad ante Compiladores Esotéricos:** Precisión de REmatch/G-Comp en código compilado con optimizaciones agresivas (`-O3`) o arquitecturas no-x86/non-ARM.
*   **Overhead de Ejecución IPC en Ghidra/IDA Plugins:** Retardo en milisegundos de las llamadas de inferencia locales mediante r2ai bajo análisis interactivo en tiempo real.
