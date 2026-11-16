---
name: c5-debloat-agent-kernel
display_name: Arquitecto de Micro-Kernels Agénticos Bare-Metal (Anti-LangChain)
description: Diseño y migración a micro-kernels de agentes en un archivo con stdlib pura y SQLite WAL sin LangChain. Dispara con "debloat llm", "microkernel agentes", "reemplazar langchain", "bare-metal agent", "autopsia langchain", "agente zero dependency".
role: arquitecto
allowed_roles:
- arquitecto
directives:
  worktree_mode: spec-only
  phase: design
  handoff:
    upstream: operador
    downstream: ejecutor
---

# C5-REAL Sovereign De-Bloat Agent Kernel Protocol (Nivel Omega)

> **Directiva Declarativa:**
> - **Rol Asignado:** `arquitecto` (Diseño Sistémico & Contratos de Invariantes)
> - **Modo de Acceso a Worktree:** `spec-only` (Modelado formal y especificaciones sin fricción de runtime)
> - **Fase Causal:** `design`
> - **Contrato Handoff:** Recibe de `operador` $\to$ Despacha a `ejecutor`

Este protocolo rige la purga de envoltorios monolíticos inflados (LangChain, LlamaIndex, CrewAI) y la construcción de motores agénticos de alta exergía basados en silicio puro y librería estándar de Python/Rust, aniquilando la latencia artificial, el riesgo de cadena de suministro y la dependencia de plataformas SaaS de observabilidad.

---

## 1. La Tríada del Micro-Kernel (Cero Dependencias Externas)

Todo motor de agentes soberano debe caber en **un solo archivo** y depender exclusivamente de la librería estándar del lenguaje:

1. **`SovereignClient` (Transductor Cinético Atómico):**
   - Invocación HTTP POST vía `urllib.request` directa al socket del proveedor de inferencia (OpenAI, Anthropic, Gemini, Ollama, vLLM).
   - Estructuración forzada mediante `response_format` nativo (JSON-Schema con `strict: True`).
   - Cero uso de `OutputParser`, `RegexParser` o envoltorios de strings.

2. **`SovereignAgentGraph` (Máquina de Estados Finita Determinista):**
   - Reemplazo absoluto de LangGraph y LCEL (`|`).
   - Cada nodo es una función pura: `f(state: dict) -> dict`.
   - El grafo se ejecuta en un bucle determinista:
   ```python
   while current_node != "__END__":
       next_state = self.nodes[current_node](state)
       current_node = next_state.get("__next__", "__END__")
       state = next_state
   ```

3. **`SovereignStateStore` (Observabilidad Local Transaccional):**
   - Reemplazo absoluto de LangSmith.
   - Persistencia local en `sqlite3` con `PRAGMA journal_mode=WAL;`.
   - Registro de sesión, identificador de nodo, latencia exacta en milisegundos, payload de entrada, payload de salida y consumo de tokens.
   - **Zero-Cloud Leak:** Cumplimiento total de RGPD/HIPAA; ningún prompt o dato corporativo viaja a nubes de terceros.

---

## 2. El Protocolo de Auditoría Forense (`langchain_autopsy.py`)

Ante cualquier sospecha de degradación de rendimiento o deuda técnica en infraestructuras heredadas:
1. Ejecutar el script forense `scripts/langchain_autopsy.py`.
2. Medir las tres dimensiones críticas:
   - **Tiempo de arranque (`import time`):** El estándar bare-metal es $\le 15 \text{ ms}$ frente a $> 1.200 \text{ ms}$ en frameworks monolíticos.
   - **Sobrecarga de pipeline en CPU:** Evaluar 10.000 operaciones de transformación de texto; demostrar que los wrappers introducen entre 20x y 50x más latencia antes de tocar la red.
   - **Memoria residente (RSS):** Monitorear la huella en reposo ($\le 15 \text{ MB}$ vs. $> 180 \text{ MB}$).

---

## 3. Protocolo de Desintoxicación y Migración (De-Bloating)

1. **Auditoría de Imports:** Rastrear y extirpar cualquier referencia a `langchain`, `langchain_core`, `langchain_community` o `langchain_openai`.
2. **Des-abstracción de Prompts:** Eliminar `ChatPromptTemplate` y sustituirlos por f-strings de Python o plantillas JSON puras.
3. **Desacoplamiento de Observabilidad:** Desconectar claves de API de LangSmith (`LANGCHAIN_API_KEY`) y enlazar `SovereignStateStore` a un archivo SQLite WAL en disco local o volumen montado.
4. **Verificación de Silicio:** Comprobar que el pipeline resultante reduce la latencia total de extremo a extremo en al menos un 30-50% y elimina los errores de dependencias rotas en actualizaciones.

---

## 4. Estrategia Go-To-Market Asimétrica (The De-Bloat Retainer)

Para operadores soberanos individuales que ofrecen consultoría o servicios de ingeniería de alto nivel:
* **No vender frameworks; vender desintoxicación de infraestructura.**
* **Propuesta de Riesgo Cero para CTOs:** Migración de un pipeline crítico en 48 horas bajo garantía de rendimiento: *«Si no reducimos la latencia al menos un 40% y tu factura de observabilidad a $0, no pagas nada»*.
* **Economía Soberana:** Retainer fijo por pipeline (12.000 € – 25.000 €) con un margen neto superior al 99%.

---

## 5. Fundamentación Epistémica y Literatura de Frontera (arXiv 2025–2026)

El rechazo a los frameworks monolíticos (LangChain) y la adopción del micro-kernel bare-metal no es una preferencia estética; es una conclusión respaldada por la investigación científica más reciente:

1. **El Colapso del "Agent Loop" hacia FSMs (Graph Harness, arXiv 2025/2026):**
   Demuestra formalmente que los bucles implícitos gobernados por LLMs sufren de alucinaciones de flujo de control (*control-flow hallucinations*) y dependencias espurias. Sustituir el bucle libre por una Máquina de Estados Finita (FSM) con transiciones discretas en silicio aporta garantías matemáticas de terminación y alcanzabilidad (*reachability*).

2. **Programmatic Tool Calling vs. JSON Parsing Overhead (arXiv 2025/2026):**
   Evidencia experimental de que los serializadores multicapa y los parsers de esquemas inflados son el principal sumidero de tokens en multi-turno. La invocación programática directa reduce el desperdicio de tokens y la latencia en hasta un **85%**.

3. **Métrica de Job-Completion Time a Nivel de Sistema (AgentServeSim, arXiv 2025/2026):**
   Demuestra que la latencia aislada de una llamada a la API es irrelevante si el middleware introduce sobrecarga en cada salto. En pipelines multi-turno, los envoltorios y callbacks hacia nubes SaaS representan hasta el **60% del tiempo total de compleción del trabajo (JCT)**.

4. **Memoria Causal y Estado Tipado Compartido (StitchCUDA & Trident, arXiv 2025/2026):**
   Valida que los agentes de alto rendimiento deben comunicarse a través de un **estado tipado transaccional (*typed state*)** en memoria local (SQLite / C-ABI), prohibiendo el intercambio de texto libre desestructurado para la mutación causal.
