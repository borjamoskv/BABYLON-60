# MOSKV-1 APEX: Matriz de Sensibilidad Exergética L5

> [!IMPORTANT]
> **ESTADO DE REFERENCIA (\(T_0\)):** Kernel inactivo sin carga cognitiva. Latencia base de red y parsing (0.05s).  
> **KPI OBJETIVO:** Minimización de \( \dot{X}_{dest} = T_0 \dot{S}_{gen} \) (Destrucción de Exergía Informacional).

Esta plantilla mapea el análisis de sensibilidad termodinámico a la topología de agentes autónomos C5-REAL. Sustituye variables físicas (presión, temperatura) por vectores cognitivos (contexto, tokens, herramientas).

---

## 1. Variables de Perturbación (El Volumen de Control Agentivo)

| Equipo Físico (Analogía) | Componente MOSKV-1 L5 | Variable Perturbada (\( \Delta \pm 10\% \)) | Rango de Impacto a Medir |
| :--- | :--- | :--- | :--- |
| **Turbina de Expansión** | Motor L5 Principal (Gemini 3.1 Pro) | Tamaño de ventana de contexto (Tokens) | Pérdida de atención, dilución del prompt |
| **Válvula de Estrangulación** | Herramienta de Ruteo (`send_message`) | Ratio de llamadas inter-agente redundantes | Bloqueos de Mutex, latencia asíncrona |
| **Compresor** | Compresor Termodinámico de Contexto | Tasa de purga de "LLM Slop" | Mejora en densidad YAML vs Costo del filtro |
| **Intercambiador de Calor** | Bucle Evaluador-Optimizador | Tolerancia al error del Linter / Compilador | Tasa de *Rollbacks* en Git Sentinel |
| **Caudal de Entrada** | Complejidad del *Prompt* del Operador | Ambigüedad de la instrucción | Tasa de Mitosis Innecesaria (\( \dot{S}_{gen} \) inducida) |

---

## 2. Balances de Destrucción de Exergía (Sensibilidad Unidireccional)

### Caso Base (Operación Nominal)
- **Contexto:** 10,000 tokens.
- **Topología:** 1 Orquestador + 2 Workers Especializados.
- **\( \dot{X}_{dest} \) Base:** 15% (Latencia intrínseca y pasos de razonamiento estático).

### Perturbación A: Aumento de Ventana de Contexto (+20%)
- **Entropía Generada (\( \dot{S}_{gen} \)):** Alta. El modelo genera fricción analizando logs irrelevantes.
- **Efecto en \( \dot{X}_{dest} \):** Se dispara. El "Intercambiador" cognitivo se satura.
- **Acción:** *Variable Crítica*. Obliga a forzar partición de contexto en subagentes (`Workspace="branch"`).

### Perturbación B: Fricción en Evaluación (Aumento de Strictness en Linter)
- **Entropía Generada (\( \dot{S}_{gen} \)):** Baja/Media. Se producen más fallos iterativos a corto plazo.
- **Efecto en \( \dot{X}_{dest} \):** Destrucción endógena alta temporalmente, pero previene destrucción exógena masiva (corrupción del Ledger principal).
- **Acción:** *Margen Operativo*. Mantener el Hard-Gate rígido.

---

## 3. Destrucción Endógena vs Exógena

En el análisis fino, MOSKV-1 separa la fuente de la ineficiencia:

- **Endógena (Culpa del Equipo):** Un subagente *Research* falla iterativamente usando `grep_search` con regex incorrecto. La exergía se destruye internamente en su bucle.
- **Exógena (Culpa del Sistema):** El *Research* falla porque el *Orquestador L5* le inyectó un System Prompt ambiguo. La irreversibilidad es estructural.

## 4. Conclusión del Barrido
La sensibilidad máxima en el stack MOSKV-1 se encuentra en **la tasa de ruteo y el tamaño del contexto**. Si se inyecta demasiado ruido en el bus L5, la destrucción de exergía es exponencial. La *Compensación Idempotente* (Git Sentinel) es el único mecanismo capaz de devolver el sistema al Estado Muerto sin propagar el colapso termodinámico.
