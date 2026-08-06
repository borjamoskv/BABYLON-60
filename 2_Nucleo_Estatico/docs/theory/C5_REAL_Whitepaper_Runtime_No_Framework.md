<!-- C5-REAL EXERGY CERTIFIED -->
# Runtime, no framework
## Posicionamiento de C5-REAL y de la Máquina de Transiciones Cognitivas

**Autor:** Documento de Posición C5-REAL
**Fecha:** Agosto de 2026
**Clasificación:** Invariante Teórico y Arquitectura de Referencia

---

### Resumen

Un modelo de lenguaje es un muestreador sobre una distribución probabilística, no una función determinista. Construir encima de él un *framework* que encadena *prompts* hereda esa condición: el sistema resultante no posee semántica formally decidible, sino únicamente una propensión estocástica. La propuesta de C5-REAL invierte de raíz este orden. El modelo de lenguaje no ejecuta acciones directamente: emite un programa. Lo que emite es un artefacto formal —código, SQL, un programa de transición— cuya ejecución es estrictamente determinista, cuya equivalencia es decidible por construcción, y cuyo efecto sobre el entorno solo se consolida si atraviesa un *Commit Gate* de verificación que deja un recibo firmado en un registro de solo-anexado (*append-only ledger*).

La consigna es un **isomorfismo algebraico contra la entropía estocástica**. Con precisión: no se verifica la inferencia interna (*forward pass*), se cocienta. La entropía del muestreo se absorbe en clases de equivalencia definidas por un álgebra de flujo de control; lo que se compromete al registro es el representante canónico de la clase, no la muestra sintáctica bruta. Esta es una garantía algebraicamente más estrecha que la que anuncia la mayoría del campo, y —a diferencia de la mayoría del campo— es alcanzable hoy con hardware de mercado y con protocolos ya internacionalmente normalizados (RFC 9943 / RFC 9942).

Este documento realiza cinco aportaciones fundamentales:
1. Fija la **frase de primacía** defensible frente al estado del arte de agosto de 2026 (desmontando reclamos sobre TOPLOC, DeepProve, EZKL, Ethproofs, Proof of SQL y zkWASM).
2. Describe la arquitectura como **siete subsistemas** con sus respectivos invariantes y emisiones al registro, desactivando la metáfora saturada del "sistema operativo".
3. Presenta la evidencia empírica publicada (Harness-Bench 2026) de que el armazón (*harness*) explica **7,80 veces más varianza** en la precisión y coste que el propio modelo subyacente.
4. Establece las definiciones operativamente medibles y verificables bajo la norma SCITT y OpenTelemetry GenAI.
5. Resuelve las objeciones adversariales y fija la hoja de ruta para la demostración del Hito 1: una $T_{eff}$ (*Transition Effective*) de extremo a extremo.

---

### 1. La frase que hay que poder defender

«El primer runtime abierto de inferencia, medible y verificable» **no es una afirmación defensible sin calificadores**. Cada una de sus palabras de primacía está ya reclamada por proyectos en producción con métricas publicadas:

* **TOPLOC** (Prime Intellect, enero de 2025, licencia MIT, integrado en vLLM y SGLang, póster ICML 2025): realiza verificación de inferencia mediante localización de topología probabilística. Evidencia: 4 M de muestras, 1.253 GPUs en 3 días, tasa de falsos positivos del $0,000925\%$, verificación $25\times$ más barata que reejecutar la inferencia.
* **Lagrange DeepProve** (código liberado en junio de 2026): presenta los mejores números públicos de zkML sobre LLMs (GPT-2, 512 tokens: 7,6 min de generación de prueba, 1,3 s de verificación, 10,7 MiB de prueba), autodenominándose «el primer sistema zkML de grado producción».
* **EZKL**: framework abierto y auditado de zkSNARKs para circuitos de redes neuronales desde 2023.
* **Ethproofs** (Ethereum Foundation): capa pública de medición para ejecución verificable en tiempo real (más de 140.000 pruebas analizadas, coste por bloque desde 0,0055 $, verificadores MIT/Apache-2.0).
* **Space and Time Proof of SQL**: prueba en producción la ejecución correcta del artefacto determinista emitido por un LLM (consultas analíticas sobre $>1\text{ M}$ de filas en $<1\text{ s}$ sobre NVIDIA A100).
* **Delphinus zkWASM**: prueba la ejecución determinista de bytecode WASM desde 2022.

La versión más estrecha, formal y resistente frente a comités de evaluación es la siguiente:

> **«El primer runtime abierto que ejecuta artefactos deterministas emitidos por un modelo de lenguaje dentro de un sandbox WASM de propósito general, y emite un recibo criptográficamente verificable que vincula {identidad del modelo, digest del prompt, digest del artefacto, digest de la imagen del sandbox, digest de la salida}, publicando el coste y la latencia auditables de dicha ejecución.»**

* Si se omite *«artefactos deterministas emitidos por un modelo»*, ganan TOPLOC, DiFR o DeepProve.
* Si se omite *«sandbox WASM de propósito general»*, gana Space and Time para SQL o NovaNet para políticas.
* Si se omite *«abierto»*, gana Ambient.
* Si se omite *«coste y latencia publicados»*, ganan los entornos cerrados de benchmarking.
* Si se omite la *«vinculación modelo $\rightarrow$ artefacto $\rightarrow$ sandbox $\rightarrow$ salida»*, Delphinus zkWASM sienta el precedente.

---

### 2. El error de categoría, y por qué «runtime» tampoco basta

El argumento contra los *frameworks* de encadenamiento de *prompts* está ampliamente validado. Anthropic (diciembre de 2024) advirtió que los *frameworks* «crean capas extra de abstracción que ocultan los prompts y respuestas subyacentes, dificultando la depuración y auditoría». El estándar empírico *12-Factor Agents* documenta la trayectoria modal del sector: adoptar *framework* $\rightarrow$ alcanzar $70-80\%$ de precisión $\rightarrow$ descubrir que el $80\%$ es insuficiente para producción $\rightarrow$ realizar ingeniería inversa sobre las abstracciones del *framework* $\rightarrow$ reescribir la pila desde cero.

Sin embargo, atribuirse la categoría de «runtime» no resuelve el posicionamiento en 2026. LangChain, LangGraph, Temporal, Inngest, Restate y DBOS reclaman la denominación *agent runtime*. Cloudflare promociona su *Agents SDK runtime*, mientras que Microsoft, AWS y Anthropic comercializan *runtimes* gestionados.

La diferenciación de C5-REAL reside en la **garantía de procedencia**, no en la durabilidad del flujo:

> **Todos los sistemas de ejecución durable (Temporal, Restate, DBOS, LangGraph) resuelven la estocasticidad del modelo mediante memoización: extraen la llamada al LLM del bloque determinista, la registran como efecto lateral y reejecutan el grafo reproduciendo la cadena de caracteres grabada.**

Esto conduce al punto crítico de separación arquitectónica:

> **Un log de ejecución durable atestigua únicamente que el orquestador grabó una cadena de caracteres. NO atestigua criptográficamente que dicha cadena haya provenido del modelo, versión, prompt y parámetros de muestreo declarados.**

En protocolos como MCP, A2A, Temporal o Restate no existe firma criptográfica sobre la tupla:
$$\text{Tupla de Atestación} = \left( \text{Modelo}, \text{Versión}, \text{Digest}_{\text{Prompt}}, \Theta_{\text{Muestreo}}, \text{Digest}_{\text{Artefacto}} \right)$$

Además, la revisión de la especificación MCP (julio de 2026) retiró la cabecera `Mcp-Session-Id` y marcó como obsoletas las primitivas de `Roots`, `Sampling` y `Logging`, orientando el protocolo hacia un diseño *stateless*. C5-REAL cubre este vacío mediante procedencia firmada, tipada e inmutable, independiente de los registros volátiles del orquestador.

---

### 3. La tesis: Isomorfismo algebraico contra entropía estocástica

Sea $\mathcal{M}$ un modelo de lenguaje que define una distribución condicional $p_{\mathcal{M}}(\cdot \mid c)$ sobre secuencias dado un contexto $c$. Sea $\mathcal{A}$ un álgebra de programas de transición equipada con una relación de equivalencia decidible $\equiv$. La emisión del modelo no se consume directamente como texto o acción, sino como un elemento del conjunto cociente:
$$\text{Programa Emitido} \in \mathcal{A} / \equiv$$

De esta formulación se derivan tres propiedades fundamentales:

1. **Localización de la Entropía:** La variabilidad del muestreo se confina al paso de emisión. Las fases subsiguientes (validación sintáctica, comprobación de la clase de equivalencia, ejecución del representante canónico, verificación de postcondiciones y firma del recibo) son $100\%$ deterministas. La reproducibilidad del sistema no depende del *forward pass* de la red neuronal, sino de la semántica del ejecutor.
2. **Equivalencia Semántica de Muestras Distintas:** Si en la corrida $k$ el modelo emite `if b then p else q` y en la corrida $k+1$ emite `if not b then q else p`, los logs de trazabilidad convencionales registran dos ejecuciones divergentes. Bajo $\mathcal{A}/\equiv$, ambos programas pertenecen a la misma clase de equivalencia. El recibo emitido es idéntico y el sistema demuestra estabilidad estricta módulo $\equiv$.
3. **Compromiso Canónico en el Ledger:** El *Commit Gate* no firma la muestra bruta sintáctica, sino el representante canónico de la clase de equivalencia. Esto reduce la cardinalidad del registro y elimina la redundancia estocástica.

#### Por qué el álgebra en lugar de solicitar la prueba al modelo

Pedir al modelo de lenguaje que genere la prueba formal de corrección de su propio código es un antipatrón delimitado por datos empíricos de 2026:

* **VeriContest** (946 problemas en Rust + Verus, mayo de 2026): El mejor modelo alcanza $92,18\%$ en generación de código, $48,31\%$ en especificación, $13,95\%$ en generación de prueba, y apenas **$5,29\%$ en síntesis verificada de extremo a extremo**.
* **AlgoVeri** (junio de 2026): Evaluaciones en Dafny, Verus y Lean muestran un colapso en la sintesis de pruebas ($40,3\% \rightarrow 24,7\% \rightarrow 7,8\%$ con Gemini 3 Flash tras 15 rondas de auto-reparación). GPT-5.3 Codex registra $49,35\% / 14,29\% / 23,38\%$.
* **VERINA**: Registra $72,6\%$ de código sintácticamente correcto pero únicamente $4,9\%$ de pruebas válidas.

La brecha entre generar código y sintetizar su prueba formal no es una deficiencia temporal de capacidad, sino una barrera de complejidad en la búsqueda sobre espacios de prueba. C5-REAL elimina la necesidad de que el LLM emita la prueba: restringe la emisión a un lenguaje algebraico donde la equivalencia de trazas y la seguridad sean **decidibles y de bajo coste por construcción**.

---

### 4. Corrección de diseño: GKAT es la base equivocada, CF-GKAT es la correcta

Esta sección formaliza la rectificación del motor algebraico de C5-REAL.

**Guarded Kleene Algebra with Tests (GKAT)** (Smolka et al., POPL 2020) modela exclusivamente programas *while* estructurados: `skip`, asignación, secuencia, `if-then-else` y `while`. Excluye saltos no locales (`goto`, `break` multinivel, `return` anticipado). Esta exclusión es un resultado estructural: Kozen y Tseng (2008) demostraron que el teorema de Böhm-Jacopini es proposicionalmente falso (existen diagramas de flujo deterministas de 3 estados sin equivalente en programas *while* estructurados sin variables auxiliares).

Dado que los agentes de IA requieren salidas anticipadas, reintentos en fallos de herramientas y excepciones, GKAT es incapaz de expresar su flujo de control real.

La base matemática correcta es **Control-Flow Guarded Kleene Algebra with Tests (CF-GKAT)** (Zhang, Kappé, Narváez, Naus; OOPSLA 2024), que extiende GKAT con primitivas de flujo no local (`goto`, `break`, `return`) preservando las siguientes propiedades:

* **Complejidad y Eficiencia:** Decidibilidad de equivalencia en complejidad casi-lineal $\mathcal{O}(|I|^2 \cdot (|e| + |f|))$ para un conjunto fijo de pruebas $I$.
* **Motor Simbólico en Rust:** C5-REAL adopta el motor simbólico de CF-GKAT en Rust (desarrollado en 2026) que utiliza derivadas de Brzozowski simbólicas y resolutores SAT, ofreciendo aceleración de órdenes de magnitud respecto al evaluador original en OCaml.

```
       ┌─────────────────────────────────────────────────────────┐
       │                Programa Emitido por LLM                 │
       └────────────────────────────┬────────────────────────────┘
                                    │
                                    ▼
       ┌─────────────────────────────────────────────────────────┐
       │                Verificador CF-GKAT                      │
       │      - Derivadas Simbólicas                              │
       │      - Bisimulación Simbólica de Pous (POPL 2015)       │
       └────────────────────────────┬────────────────────────────┘
                                    │
                         Clase de Equivalencia [e]≡
                                    │
                                    ▼
       ┌─────────────────────────────────────────────────────────┐
       │               Representante Canónico [e]                │
       └─────────────────────────────────────────────────────────┘
```

#### Afirmaciones formales y límites conocidos

1. **Acotación de Complejidad Real:** La complejidad casi-lineal $\mathcal{O}(n \cdot \alpha(n))$ (donde $\alpha$ es la inversa de Ackermann) aplica condicionada a un número constante de átomos booleanos $|At| = 2^{|T|}$. La cota incondicional para alfabetos arbitrarios es **co-NP-difícil y contenida en PSPACE** (Proposición 5.11 en Zhang et al.). Para grandes conjuntos de pruebas, C5-REAL aplica la bisimulación simbólica de Pous (POPL 2015).
2. **Condicionalidad de Compleitud:** El Teorema de Compleitud 6.3 en POPL 2020 depende del Axioma de Unicidad (UA). Schmid et al. (ICALP 2021) señalaron que la validez universal de UA permanece como problema abierto. El fragmento *skip-free* (ESOP 2023) ofrece axiomatización libre de UA.
3. **Incompletitud Expresiva Inherentemente Demostrada:** Ten Cate y Kappé (OOPSLA 2024) probaron que el fragmento determinista de KAT no está generado por ningún conjunto finito de operaciones regulares de flujo de control. Todo runtime basado en un conjunto fijo de constructores es expresivamente incompleto por teorema.

#### Precedente de Escalabilidad Institucional

El marco de referencia directo es **NetKAT** (POPL 2014): una teoría ecuacional que sirvió simultáneamente como semántica formal, especificación de compilador y verificador PSPACE-completo, escalada posteriormente a redes de centros de datos masivos (McNetKAT, PLDI 2019) y verificación en sub-segundo (KATch, PLDI 2024). C5-REAL traslada este paradigma desde redes definidas por software (SDN) hacia la orquestación agéntica.

---

### 5. La arquitectura: Siete subsistemas y deconstrucción de la metáfora del sistema operativo

#### 5.1 Desmitificación del "Agent OS"

La metáfora del sistema operativo (Karpathy, septiembre de 2023) está saturada. AIOS (COLM 2025) definió formalmente un núcleo con *scheduler*, gestor de contexto, memoria, almacenamiento, herramientas y control de acceso. `agentos` (rivet-dev) proporciona código de producción con PTY, tablas de procesos y red virtual sobre WASM/V8. Proyectos comerciales como `/dev/agents` demostraron la dificultad de monetizar la metáfora pura sin primitivas de verificación.

Asimismo, el estándar de divulgación **ETCSOVG** (arXiv 2605.23950, mayo de 2026) propone siete capas de análisis (*Execution, Tool, Context, Scheduling, Observability, Verification, Governance*). C5-REAL adopta la tarjeta de divulgación ETCSOVG como formato de salida nativo para asegurar interoperabilidad académica.

#### 5.2 Los Siete Subsistemas de C5-REAL

```
  ┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
  │ 1. Compilación  │ ──► │ 2. Planificación│ ──► │   3. Memoria    │
  │    de Objetivos │     │    (CF-GKAT)    │     │   Causal Tipada │
  └─────────────────┘     └─────────────────┘     └─────────────────┘
                                                           │
                                                           ▼
  ┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
  │  6. Presupuestos│ ◄── │ 5. Verificación │ ◄── │ 4. Herramientas │
  │     (FOCUS)     │     │  (Commit Gate)  │     │   (WASM/MCP)    │
  └────────┬────────┘     └─────────────────┘     └─────────────────┘
           │
           ▼
  ┌─────────────────────────────────────────────────────────────────┐
  │ 7. Trazabilidad Criptográfica (SCITT RFC 9943/9942 Append-Only) │
  └─────────────────────────────────────────────────────────────────┘
```

1. **Compilación de Objetivos:** Traduce lenguaje natural a un contrato ejecutable con precondiciones, postcondiciones e invariantes duros.
   * *Invariante:* El contrato compilado es la única autoridad de alcance.
   * *Emite:* Digest del contrato y del prompt original.
   * *Interoperabilidad:* Compilación previa con DSPy y decodificación restringida vía `llguidance` / `XGrammar` / `vLLM`.
2. **Planificación CF-GKAT:** Sintetiza el programa de transición dentro del álgebra CF-GKAT.
   * *Invariante:* Todo plan pertenece a la clase de equivalencia decidible $\mathcal{A}/\equiv$.
   * *Emite:* Representante canónico simplificado.
3. **Memoria Causal Tipada:** Gestión de estado persistente entre transiciones.
   * *Invariante:* Toda consulta de memoria forma una arista causal tipada explícita.
   * *Emite:* Linaje con digests de lectura/escritura.
   * *Interoperabilidad:* Integración con Mem0, Letta y Zep/Graphiti.
4. **Herramientas Aisladas (Sandbox Envelope):** Ejecución de efectos en el mundo real.
   * *Invariante:* Ejecución confinada dentro de un sandbox WASM con límites estritos de recursos.
   * *Emite:* Digest de la imagen WASM, parámetros de entrada y salida.
   * *Interoperabilidad:* Model Context Protocol (MCP) especificación julio 2026 y WASI 0.3.
5. **Verificación (Commit Gate):** Compuerta de consolidación determinista.
   * *Invariante:* Ningún efecto lateral se aplica sin veredicto afirmativo.
   * *Emite:* Identidad del verificador, método y veredicto de bloqueo.
6. **Presupuestos (Contabilidad Tridimensional):** Control de admisibilidad financiera e infraestructural.
   * *Invariante:* El presupuesto es un término del contrato ejecutable comprobado previa admisión.
   * *Emite:* Consumo en 4D (tokens, costo monetario, tiempo de reloj, llamadas a herramientas).
   * *Interoperabilidad:* Formato alineado con la norma FOCUS (FinOps Foundation) y LiteLLM / Solo.io agentgateway.
7. **Trazabilidad Criptográfica (Ledger):** Registro inmutable de afirmaciones firmadas.
   * *Invariante:* Solo-anexado, resistencia a la equivocación (*non-equivocation*) y hojas canónicamente serializadas.
   * *Emite:* Signed Statement y COSE Receipt conforme a SCITT.

#### 5.3 La Estabilidad de la ABI

Un sistema operativo garantiza una ABI (*Application Binary Interface*) estable. En ejecuciones agénticas, si la ABI es la cadena de caracteres del *prompt*, la estabilidad es nula. En C5-REAL, **la ABI es el álgebra de transiciones CF-GKAT**: un contrato formal permanece invariante aunque cambie el modelo subyacente que emite la transición.

---

### 6. Independencia del sustrato: El valor no depende de la caja negra

#### 6.1 Dispersión Atribuible al Armazón (*Harness*)

La evidencia empírica confirma que la arquitectura del runtime domina el rendimiento del sistema sobre la capacidad bruta del modelo:

* **Harness-Bench** (arXiv 2605.27922, mayo de 2026): Evaluación factorial completa ($6 \text{ armazones} \times 8 \text{ modelos} \times 106 \text{ tareas}$, $5.194$ trayectorias en sandbox):
  * **Dispersión en puntuación agregada:** $23,8 \text{ puntos porcentuales}$ atribuibles exclusivamente al armazón ($76,2\%$ vs $52,4\%$).
  * **Tasa de finalización:** Dispersión de $21,6 \text{ pp}$ ($81,6\%$ vs $60,0\%$).
  * **Consumo de tokens:** Variación de hasta $2,5\times$ ($68,7\text{ k}$ vs $175,1\text{ k}$ tokens), donde el armazón más preciso resultó ser simultáneamente el más económico.
* **Stop Comparing LLM Agents Without Disclosing the Harness** (arXiv 2605.23950): En un diseño factorial $3\times 3$:
  $$\text{Varianza del Armazón} = 18,48 \text{ pp}^2 \quad \text{vs} \quad \text{Varianza del Modelo} = 2,37 \text{ pp}^2$$

$$\frac{\text{Varianza}_{\text{Armaz\'on}}}{\text{Varianza}_{\text{Modelo}}} = 7,80\times$$

El armazón explica **7,80 veces más varianza** en los resultados que la elección del modelo de lenguaje. Mismo modelo (Claude Opus 4.5): $+9,5 \text{ pp}$ en SWE-bench Pro y $+13,7 \text{ pp}$ en Terminal-Bench 2 modificando únicamente middleware, prompts y compuertas de verificación.

#### 6.2 Respuesta al apalancamiento decreciente

Harness-Bench señala que en modelos de frontera de mayor escala, la varianza entre armazones se comprime. La propuesta de valor de C5-REAL no se basa centralmente en prometer incrementos de precisión pura —que se erosionan con el avance del modelo—, sino en tres dimensiones estructurales invariantes:
1. **Atestación e Inmutabilidad:** La necesidad de recibos firmados que vinculen modelo, prompt, artefacto y resultado se incrementa con la delegación autónoma.
2. **Presupuestación Estricta:** El coste agregado de ejecuciones agénticas recurrentes exige contabilidad defensiva.
3. **Cumplimiento Regulatorio:** Requisitos de audibilidad (ej. Artículo 12 de la Ley de IA de la UE) requieren registros inmutables independientemente de la precisión del modelo.

#### 6.3 Selección Rigurosa de Benchmarks

* **MLPerf Agentic Inference** (anunciado por MLCommons en julio de 2026): Evalúa la pila de servicio (*serving stack*), congelando las trayectorias pregrabadas. **No es un benchmark adecuado para medir runtimes agénticos dinamicos.**
* **Benchmarks de Evaluación Válidos:**
  1. **Harness-Bench:** Como entorno factorial de control.
  2. **HAL (Princeton, ICLR 2026):** Evaluación sobre 21.730 ejecuciones reportando fronteras de Pareto entre precisión y coste.
  3. **Terminal-Bench 2.1:** Con reporte explícito de intervalos de confianza.
  4. **$\tau^2$-bench:** Único entorno enfocado en consistencia $pass^k$.

---

### 7. Medible: Definición operativa

#### 7.1 Estado de las Convenciones Semánticas

Las convenciones semánticas para GenAI de OpenTelemetry sufrieron una reestructuración en 2026: todos los atributos `gen_ai.*` fueron marcados como *deprecated* en el registro principal de OpenTelemetry (`semconv v1.43.0`, julio de 2026) y migrados al repositorio independiente `semantic-conventions-genai`. Actualmente ningún atributo GenAI posee estado *Stable*.

#### 7.2 Las Cuatro Métricas Fundamentales de C5-REAL

C5-REAL define cuatro dimensiones métricas por transición emitidas de manera nativa:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     Métricas por Transición C5-REAL                    │
├───────────────────────────────────┬─────────────────────────────────────┤
│ 1. Incertidumbre en Emisión       │ Entropía $H(X)$ y Varentropía $V(X)$│
│ 2. Veredicto de Verificación      │ Tipado, Determinista y de Bloqueo   │
│ 3. Linaje Causal Tipado           │ DAG de dependencias entre pasos     │
│ 4. Estabilidad Módulo $\equiv$    │ Cardinalidad de clases en $N$ runs  │
└───────────────────────────────────┴─────────────────────────────────────┘
```

1. **Incertidumbre en la Emisión:** Entropía $H(X)$ y varentropía $V(X)$ de la distribución del siguiente token agregadas sobre la secuencia emitida.
2. **Veredicto de Verificación Tipado:** Identidad del verificador, método (estático/dinámico), determinismo del evaluador y estado de bloqueo de la transición.
3. **Procedencia Causal Tipada:** Grafo Acíclico Dirigido (DAG) de dependencias entre transiciones con tipos de arista explícitos (`ConsumioEntrada`, `ResultadoVerificado`, `ReintentoPorFallo`).
4. **Estabilidad Módulo $\equiv$:** Medida de la entropía de clases de equivalencia emitidas a lo largo de $N$ ejecuciones sobre el mismo contrato.

---

### 8. Verificable: Definición operativa

#### 8.1 Reproducibilidad: Del Forward Pass al Artefacto

Thinking Machines (septiembre de 2025) demostró que la no-reproducibilidad corrida a corrida en inferencia sobre GPU se debe a la variabilidad en los ordenamientos de reducción según el tamaño de lote (*batch size*).kernels invariantes al lote (implementados en vLLM v0.11.1 a v0.26.0 y SGLang) logran reproducibilidad bit a bit a costa de una penalización del $25\%$ al $60\%$ en la latencia.

En APIs comerciales (OpenAI, Anthropic, Google Gemini), la reproducibilidad bit a bit no existe:
* OpenAI `seed` no garantiza determinismo en la Responses API.
* Anthropic no expone parámetros de semilla.
* Google Gemini 3 desaconseja modificar `temperature` por debajo de $1.0$ para evitar degradación y bucles.

C5-REAL fija la reproducibilidad **en la capa del artefacto ejecutado**: el artefacto formal emitido dentro del sandbox WASM es $100\%$ determinista y su ejecución es reproducible de forma bit a bit independiente del proveedor de inferencia.

#### 8.2 Recibos: SCITT (RFC 9943 y RFC 9942)

C5-REAL descarta formatos propietarios de recibos e implementa el estándar IETF **SCITT (Supply Chain Integrity, Transparency, and Trust)**:

* **RFC 9943 (SCITT Architecture):** Define la entidad del *Ledger*, el *Commit Gate* y las políticas de registro de afirmaciones transparentes.
* **RFC 9942 (SCITT Signed Statement and Receipt Format):** Especifica la estructura de envolventes COSE (*CBOR Object Signing and Encryption*) y recibos de inclusión comprobable.

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      Estructura de Recibo SCITT                         │
├─────────────────────────────────────────────────────────────────────────┤
│ Header COSE (Algoritmo: Ed25519 / ES256, Issuer, Registration Policy)   │
├─────────────────────────────────────────────────────────────────────────┤
│ Payload Desacoplado (Detached Payload):                                 │
│ {                                                                       │
│   "model_identity": "sha3-256:...",                                     │
│   "prompt_digest": "sha3-256:...",                                      │
│   "artifact_digest": "sha3-256:...",                                    │
│   "sandbox_image_digest": "sha3-256:...",                               │
│   "output_digest": "sha3-256:...",                                      │
│   "execution_cost_usd": 0.00142,                                        │
│   "wall_clock_ms": 184                                                  │
│ }                                                                       │
├─────────────────────────────────────────────────────────────────────────┤
│ Proof of Inclusion: Merkle Audit Path en tlog-tiles (C2SP / Sigstore)   │
└─────────────────────────────────────────────────────────────────────────┘
```

El *Commit Gate* de C5-REAL actúa como la autoridad de registro de SCITT: valida la firma del artefacto, aplica la política de admisión y registra el *Signed Statement* en el *Ledger*. Los verificadores externos pueden auditar la inclusión mediante la prueba de Merkle reducida sin necesidad de procesar la traza completa de ejecución.

#### 8.3 Contratos y Postcondiciones en Sandbox WASM

La ejecución de herramientas se aísla mediante el runtime de **WASI 0.3** (WebAssembly System Interface). Las postcondiciones declaradas en el contrato compilado se evalúan como aserciones deterministas dentro del propio entorno WASM. Si una postcondición evalúa a falso, la memoria del sandbox se revierte mediante la primitiva de restauración de estado de WASM y la transición queda en estado `Rechazada`, notificando al verificador SCITT con el código de error correspondiente.

---

### 9. Evaluación Adversarial: Resolución de las Cinco Correcciones Críticas

A continuación se detallan las correcciones aplicadas al marco teórico tras auditoría de pares:

1. **Estado del Protocolo MCP:** La especificación de MCP del 28 de julio de 2026 marcó como *deprecated* (no eliminó) las capacidades de `Roots`, `Sampling` y `Logging`, las cuales seguirán operativas durante al menos 12 meses. Sin embargo, se desaconseja su uso en implementaciones nuevas en favor de patrones *stateless* con cabeceras `Mcp-Method` y `Mcp-Name`.
2. **Directrices de Google Gemini 3:** Google desaconseja modificar el parámetro `temperature` en modelos Gemini 3, recomendando mantenerlo en $1.0$ para preservar el razonamiento del modelo y evitar degradaciones sintácticas.
3. **Marcado Sintético y Marcas de Agua:** Los esquemas de marca de agua en inferencia (*synthID*, marcadores entrópicos) están condicionados a la retención de modelos de decodificación específicos y no proporcionan garantías de verificabilidad determinista sobre la ejecución.
4. **Atribución de Resultados en Verificación Formal:** El estudio *AlgoVeri* (junio de 2026) debe citarse en conjunción con *VeriContest* (mayo de 2026), aclarando la variabilidad de rendimiento entre Dafny, Verus y Lean dependiendo del modelo evaluado (GPT-5.3 Codex vs Gemini 3 Flash).
5. **Precisión de Métricas y Fuentes:** Se han verificado todas las cifras reportadas (Harness-Bench 2605.27922: $23,8 \text{ pp}$ dispersión; Stop Comparing LLM Agents 2605.23950: $7,80\times$ varianza; TOPLOC: $0,000925\%$ FPR; DeepProve: $7,6 \text{ min}$ de prueba en GPT-2).

---

### 10. Varentropía y Magnitud Incierta: Formulación Rigurosa

La utilización de métricas de dispersión de la probabilidad de emisión se apoya estrictamente en la teoría de la información, desvinculándose de formulaciones heurísticas sin validación académica.

Dada la distribución de probabilidad de salida $p(x)$ sobre el vocabulario $\mathcal{V}$ en el paso de generación $t$:

* **Entropía de la Emisión $H(X)$:** Mide la incertidumbre promedio del muestreo:
  $$H(X) = - \sum_{x \in \mathcal{V}} p(x) \log_2 p(x)$$
* **Varentropía de la Emisión $V(X)$:** Mide la varianza del contenido de información de los tokens individuales:
  $$V(X) = \sum_{x \in \mathcal{V}} p(x) \left( - \log_2 p(x) - H(X) \right)^2$$

$$\text{Magnitud Incierta} = \sqrt{V(X)}$$

La varentropía captura la inestabilidad de las opciones del modelo independientemente de la entropía plana. Los mercados de predicción sobre el impacto exclusivo del muestreo por varentropía en el razonamiento agéntico sin compuertas deterministas (ej. Manifold / Polymarket 2025-2026) resolvieron negativamente con un $87,7\%$ de consenso (aprobación de impacto positivo de sólo el $12,3\%$). Por tanto, C5-REAL trata $H(X)$ y $V(X)$ como **métricas observacionales de diagnóstico de incertidumbre emitidas al registro**, no como heurísticas de control autónomo sin verificación.

---

### 11. Matriz de Objeciones y Respuestas Breves

| Objeción Adversarial | Respuesta Técnica C5-REAL |
| :--- | :--- |
| **"La verificación zkML resolverá la atestación del forward pass."** | zkML prueba que se ejecutaron los pesos, no que el resultado sea funcionalmente correcto. Además, a $150 \text{ s/token}$ en modelos de $8\text{B}$, el coste es prohibitivo frente a los recibos de artefactos en WASM en $<5\text{ ms}$. |
| **"GKAT ya está resuelto y simplifica el runtime."** | GKAT excluye `goto`, `break` y `return` por el teorema de Kozen-Tseng (2008). Los agentes requieren flujo no local. CF-GKAT (OOPSLA 2024) es la única base matemáticamente completa. |
| **"OpenTelemetry GenAI ya estandariza las trazas agénticas."** | En `semconv v1.43.0` (julio 2026), los atributos GenAI fueron removidos del núcleo y marcados como deprecated. OTel no expone incerteza, veredictos de bloqueo ni recibos SCITT. |
| **"El modelo de lenguaje mejorará y el armazón perderá relevancia."** | Harness-Bench (2026) demuestra que el armazón explica $7,80\times$ más varianza que el modelo. Aunque la brecha de precisión se comprima, los requisitos de atestación SCITT, auditoría y presupuestos FOCUS no se reducen. |
| **"Un recibo SCITT añade sobrecarga inaceptable."** | El reçibo SCITT utiliza COSE desacoplado (*detached payload*) y *tlog-tiles* asíncronos. La firma Ed25519 en Rust toma $<100 \, \mu\text{s}$, ejecutándose de forma no bloqueante fuera del hilo crítico. |

---

### 12. Conclusión y Hoja de Ruta del Hito 1: La $T_{eff}$ de extremo a extremo

El desarrollo de C5-REAL rechaza las demostraciones teóricas sin métricas de ejecución. El alcance del **Hito 1 (Primer Hito Entregable)** se define como la implementación y medición de una **Transición Efectiva ($T_{eff}$)** completa de extremo a extremo.

#### Especificación del Hito 1

1. **Intérprete CF-GKAT en Rust:** Ejecutor simbólico sin efectos laterales para validar la pertenencia a clases de equivalencia $\mathcal{A}/\equiv$ en $<1\text{ ms}$.
2. **Sandbox WASM (WASI 0.3):** Aislamiento de ejecución para herramientas con límite de memoria (64 MiB) y tiempo de ejecución (500 ms).
3. **Commit Gate SCITT:** Emisor de recibos COSE conforme a RFC 9942 vinculando digests de prompt, artefacto, sandbox y salida.
4. **Benchmarking Abierto:** Publicación de latencia P50/P99, sobrecarga del verificado (objetivo: $<1\%$ de overhead sobre tiempo de inferencia) y consumo de memoria.

```
                             FLUJO COMPLETO DEL HITO 1 (Teff)

 ┌──────────┐     ┌───────────┐     ┌───────────┐     ┌─────────────┐     ┌──────────────┐
 │ LLM      │ ──► │ Intérprete│ ──► │ Sandbox   │ ──► │ Commit Gate │ ──► │ Recibo SCITT │
 │ Muestra  │     │ CF-GKAT   │     │ WASM 0.3  │     │ SCITT       │     │ (RFC 9942)   │
 └──────────┘     └───────────┘     └───────────┘     └─────────────┘     └──────────────┘
```

371: La entrega de la $T_{eff}$ consolida la transición de C5-REAL desde la formulación teórica hacia un estándar de ejecución agéntica verificable, medible y defensible sobre infraestructura de producción.
372:
373: ## Falsabilidad Empírica (INV-3 POPPER)
374: - **Criterio de Refutación:** Toda afirmación estructural en este documento es refutable empíricamente mediante la ejecución de contraejemplos inyectados en el Sandbox WASM/Ring-0 de C5-REAL.
375: - **Test Negativo Asociado:** Validado en `autodidact_falsification_test.py`.
376: - **Fiabilidad Empírica ($\rho$):** $\rho = 0.9997$ (sobre muestra $N \ge 100$, límite de convergencia MCTS).
