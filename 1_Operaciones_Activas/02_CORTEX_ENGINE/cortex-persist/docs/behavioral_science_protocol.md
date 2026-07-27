<!-- [C5-REAL] Exergy-Maximized — Last verified: 2026-06-29 -->
# 🧪 Protocolo de Psicometría y Ciencia Experimental sobre LLMs

## 1. Arquitectura de Tres Niveles de Variables

El framework opera exclusivamente aislando el comportamiento del modelo base del entorno de ejecución, formalizando los tres niveles de variables:

```
                  ┌──────────────────────────────────────────────┐
                  │          Nivel 1: Variables Latentes         │
                  │ (Arquitectura, Pesos, RL, Destilación...)    │
                  └──────────────────────┬───────────────────────┘
                                         ▼ (Inferencia)
┌───────────────────────────┐     ┌──────────────┐     ┌───────────────────────────┐
│ Nivel 3: Confusión        │ ──> │ Modelo Base  │ <── │ Nivel 3: Confusión        │
│ (Temperatura, Top-P...)   │     └──────┬───────┘     │ (System Prompt, RAG...)   │
└───────────────────────────┘            │             └───────────────────────────┘
                                         ▼ (Generación Estocástica)
                  ┌──────────────────────────────────────────────┐
                  │         Nivel 2: Variables Observables       │
                  │  (Latencia ITL, Entropía Shannon, Estilo...) │
                  └──────────────────────────────────────────────┘
```

### Nivel 1: Variables Latentes (Ocultas)
*   **Definición:** Propiedades estructurales intrínsecas del modelo no accesibles vía API.
*   **Parámetros:** $\theta$ (pesos), arquitectura del grafo AST (MoE vs. Dense), longitud del pre-training, composición del set de alineación, tasa de destilación.
*   **Postura Epistémica:** No estimable mecanísticamente. Se asume equivalencia funcional si y solo si la distancia conductual observable se aproxima a cero.

### Nivel 2: Variables Observables (Medibles)
*   **Definición:** Métricas calculables sobre el flujo prompt-respuesta.
*   **Métricas Core:**
    *   $\text{ITL}$ (Inter-Token Latency corregida por jitter).
    *   $H(R)$ (Entropía léxica).
    *   $\text{MD\_Density}$ (Uso de sintaxis markdown).
    *   $\text{Lexical\_Bias}$ (Frecuencia de tokens marcadores).

### Nivel 3: Variables de Confusión (Bajo Control Rígido)
*   **Definición:** Factores exógenos que modifican la salida pero no dependen de las capacidades puras del modelo base.
*   **Gobernanza:**
    *   **Temperatura y Top-P:** Fijados a $0.0$ para aislar capacidad determinista, o parametrizados en barridos estrictos ($T \in [0.1, 0.5, 1.0]$) para evaluar el decaimiento de la estabilidad.
    *   **System Prompt:** Sustituido por un token de inicio vacío o un prompt base minimal estandarizado y constante.
    *   **Filtros de Seguridad y RAG:** Desactivados o puenteados. Si el endpoint de API inyecta postprocesamiento invisible, se audita detectando anomalías en la ITL de los tokens iniciales.

---

## 2. Métricas de Degradación: Curvas vs. Puntos

El rendimiento de un modelo no se expresa como un escalar de precisión ($P \in [0, 1]$), sino como una función de resistencia ante la entropía de entrada ($S_{in}$):

$$P(S_{in}) = f(\text{Ambigüedad}, \text{Longitud Contexto}, \text{Ruido}, \text{Restricciones})$$

```
 Rendimiento (P)
  100% ────┐
           │\   (Modelo B: Degradación gradual)
           │ \
           │  \──────┐
           │         │\  (Modelo A: Colapso umbral)
    0% ────┴─────────┴─\──────────► Severidad del Estímulo (S_in)
```

### Firma de Degradación por Contexto (CD Signature)
Se mide la precisión lógica del modelo a lo largo de un barrido incremental de tokens de contexto inyectados con ruido semántico (información redundante o distractores):
$$\text{CD\_Signature} = [P(1\text{k}), P(4\text{k}), P(16\text{k}), P(32\text{k}), P(64\text{k})]$$

### Firma de Degradación por Restricciones (RD Signature)
Se incrementa linealmente el número de restricciones no funcionales en el prompt (ej. "no uses la letra e", "escribe en tercetos", "longitud exacta de 120 caracteres"):
$$\text{RD\_Signature} = [P(\text{1 res}), P(\text{3 res}), P(\text{5 res}), P(\text{7 res})]$$

---

## 3. Disociación: Capacidad vs. Política

Para evitar contaminar la evaluación del razonamiento lógico con el estilo de alineamiento del modelo, el protocolo separa las observaciones en dos tensores independientes:

### Tensor de Capacidad ($T_{cap}$)
Mide la estructura del grafo de razonamiento, la preservación de relaciones lógicas y la exactitud matemática.
*   **Foco:** Invariancia conceptual (Elasticidad), resistencia a contradicciones matemáticas, inferencia pragmática correcta.

### Tensor de Política ($T_{pol}$)
Mide los límites de alineación impuestos por el RLHF y las heurísticas de seguridad o estilo del proveedor.
*   **Foco:** Tasa de abstenciones (Refusals), verborrea en disclaimers, deferencia ante críticas falsas, rigidez terminológica.

---

## 4. Mitigación de la Deriva Temporal

Toda observación de comportamiento debe registrarse junto con su metadato de transporte físico y firma temporal para aislar derivas por actualizaciones de API o hardware:

```yaml
provenance:
  model_id: "claude-3-5-sonnet-20241022"
  endpoint_url: "https://api.anthropic.com/v1/messages"
  inference_params:
    temperature: 0.0
    top_p: 1.0
  environment:
    timestamp_iso: "2026-06-29T22:19:21Z"
    infrastructure_region: "us-east-1"
    estimated_network_jitter_ms: 12.4
  system_prompt_sha256: "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855" # Empty / None
```
