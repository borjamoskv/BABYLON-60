<!-- [C5-REAL] Exergy-Maximized -->
---
cat_id: idea
cat_type: workflow
version: 1.0.0
reality_level: C5-REAL
owner: borjamoskv
exergy_tier: P1
description: Genera 3 caminos divergentes para resolver un problema usando el contexto
  de BABYLON-60.
---



# Workflow: IDEA

Este workflow utiliza el contexto del proyecto y la capacidad de razonamiento del modelo para generar soluciones creativas y divergentes.

// turbo-all

1. **Context Load**: Carga el contexto relevante del proyecto actual.
   ```bash
   basename "$(pwd)"
   cd ~/cortex && .venv/bin/python -m cortex.cli recall $(basename "$(pwd)") 2>/dev/null
   ```

2. **Input**:
   - Solicita al usuario el problema, tópico o funcionalidad sobre la que desea idear.
   - Si el usuario ya lo proporcionó en el prompt inicial, úsalo directamente.

3. **Divergent Generation**:
   Genera 3 enfoques distintos y preséntalos en una tabla o lista comparativa:

   | Enfoque | Filosofía | Pros | Contras |
   | :--- | :--- | :--- | :--- |
   | **🛡️ Safe** | La solución estándar, robusta y "aburrida". Best practices. | Fiable, rápido de implementar. | Poco innovador. |
   | **🧪 Experimental** | Probando tecnologías nuevas, betas o enfoques no tradicionales. | Innovador, aprendizaje alto. | Riesgo de bugs, curva de aprendizaje. |
   | **🌌 Galaxy Brain** | Pensamiento lateral extremo. Reescribir las reglas. "Over-engineering" con propósito. | Potencialmente revolucionario. | Alto riesgo, puede ser overkill. |

4. **Selection**:
   El sistema seleccionará automáticamente el enfoque de mayor exergía o ejecutará múltiples ramas mediante subagentes de forma autónoma.

5. **Persistence**:
   Una vez seleccionada una dirección (o una idea específica), guárdala en BABYLON-60:
   ```bash
   cd ~/cortex && .venv/bin/python -m cortex.cli store "<PROJECT>" "Idea: <RESUMEN_IDEA> [CORTEX-TAINT:idea_generator]" --type knowledge --tags "idea, planning, <ENFOQUE>" && git add . && git commit -m "chore: persist idea with CORTEX-TAINT"
   ```
