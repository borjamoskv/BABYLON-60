# REVERSE ENGINEERING MODEL TAXONOMY (C5-REAL)

**Traza CORTEX**: `[CORTEX-TAINT:borjamoskv:model_taxonomy:2026-07-17]`
**Métrica Base**: `MCTS-Test-Time-Compute-Decompilation` y `Latent-Space-Entropy-Sinks`

## 1. Claude Sonnet 4.6 (Thinking)
- **Rol**: Micro-Lógica y Depuración Iterativa.
- **Caso de uso**: Ingeniería inversa a nivel micro, scripts rápidos, traducción de ASM a C, y rastreo preciso de transiciones de punteros/stack.
- **Ventaja**: Menor TTFT (Time-to-First-Token) y menor latencia con emulación mental MCTS paso a paso.

## 2. Claude Opus 4.6 (Thinking)
- **Rol**: Síntesis Conceptual y Ofuscación Avanzada.
- **Caso de uso**: Desplegar únicamente ante cuellos de botella arquitectónicos (reconstrucción de protocolos indocumentados o romper capas complejas de ofuscación).
- **Ventaja**: Máxima densidad conceptual. Extrae el diseño teleológico a partir de pseudocódigo caótico. Penaliza con mayor latencia.

## 3. Gemini 3.1 Pro (High)
- **Rol**: Macro-Contexto.
- **Caso de uso**: Auditoría de bases de código descompiladas extensas (Ghidra/IDA) y correlación de trazas masivas.
- **Ventaja**: Ventana de contexto masiva que permite ingerir repositorios enteros sin truncamiento, mapeando relaciones cruzadas dispersas.

## 4. Gemini 3.5 Flash (High)
- **Rol**: Automatización Reactiva.
- **Caso de uso**: Scripts de Frida, parsing de cabeceras, automatización headless.
- **Desventaja**: Carece de la profundidad atencional requerida para resolver ingeniería inversa adversarial.
