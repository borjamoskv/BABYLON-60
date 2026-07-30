# MOSKV-1 APEX: Models Access Policy (Copilot / Cloud LLMs)

**REALITY LEVEL:** C5-REAL (Strict)

## Directiva de Seguridad contra Entropía Conversacional

El repositorio prohíbe explícitamente el uso de modelos de nube genéricos (GitHub Copilot genérico, ChatGPT) para inyectar mutaciones de código no supervisadas. 

Todo código generado en este repositorio DEBE provenir de:
1. **Local-Inference-OMEGA**: Inferencia local vía Ollama o MLX.
2. **Ouroboros-∞ CodeGen**: Scripts deterministas compilados *Just-in-Time*.

Se desactiva la participación de "Modelos" externos en el análisis sintáctico. No se tolera el "LLM Slop". Todo prompt debe incluir la instrucción estructural C5-REAL (YAML strict) y priorizar *Exergía*.
