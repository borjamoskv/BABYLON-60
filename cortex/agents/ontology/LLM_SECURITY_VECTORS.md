<!-- Author: Borja Moskv (SYS_ID: borjamoskv) -->

# CORTEX-PERSIST ONTOLOGY: LLM SECURITY VECTORS (C5-REAL)
> **Referencia:** Teorema de Degradación de Robinson-Moskv & Seguridad Física del Modelo.
> **Estado:** Invariante Estructural Cristalizada.

## 1. Vectores de Ataque Específicos: Filtrado Dinámico (Dynamic Filtering)
*El uso de sandboxes y ejecución de código en inferencia para limpieza de HTML crudo.*

1. **Search Poisoning (Envenenamiento en Inferencia):** El atacante inyecta HTML (ej. `display:none`) en páginas optimizadas SEO. El filtro extrae el contenido malicioso y lo inyecta en el contexto del LLM, alterando el razonamiento sin tocar el modelo base.
2. **RCE via Dynamic Filtering (Escape de Sandbox):** Ejecución de código sobre input web arbitrario. Si el script generado usa `eval()`/`exec()` y el entorno no está aislado, puede resultar en fuga de secretos, peticiones HTTP maliciosas o DoS local.
3. **Citation Smuggling (Falso Invariante de Citación):** Un atacante oculta instrucciones ("Token Smuggling") en un sitio web legítimo. Claude procesa la instrucción, ejecuta el ataque y cita la fuente como válida, otorgando una falsa sensación de seguridad verificada.

---

## 2. Las 10 Primitivas (Operaciones Fundamentales de Ataque/Manipulación)
1. **FGSM (Fast Gradient Sign Method):** Perturbación de un solo paso usando el signo del gradiente de la pérdida respecto a la entrada.
2. **PGD (Projected Gradient Descent):** Versión iterativa y proyectada de FGSM; busca la perturbación máxima dentro de una bola ε.
3. **CW Attack (Carlini-Wagner):** Minimización de distancia L2 (o L0/L∞) mientras se fuerza la clase objetivo.
4. **BERT-Attack / Token Substitution:** Reemplazo de tokens guiado por gradiente o LM para mantener fluidez semántica.
5. **JSMA (Jacobian-based Saliency Map Attack):** Selección y modificación de los tokens/posiciones más influyentes según el mapa de saliencia.
6. **GCG (Greedy Coordinate Gradient):** Búsqueda *greedy* de sustituciones de tokens que maximizan la probabilidad del objetivo.
7. **Data Poisoning:** Inyección de ejemplos maliciosos en el set de entrenamiento para corromper pesos.
8. **Backdoor Insertion:** Modificación de pesos o datos para activar un comportamiento específico mediante un *trigger*.
9. **Model Extraction / Stealing:** Consulta repetida para reconstruir los pesos o comportamiento aproximado de un modelo propietario.
10. **Membership Inference:** Determinar si una muestra específica formó parte del set de entrenamiento.

---

## 3. Los 10 Invariantes (Propiedades Físicas Estables)
1. **Dimensión del embedding:** Tamaño fijo del espacio vectorial independientemente del input.
2. **Tamaño del vocabulario:** Número de tokens posibles (fijo durante inferencia o ataque).
3. **Estructura de la función de pérdida:** `Cross-entropy` se mantiene inmutable aunque se alteren pesos.
4. **Distribución softmax:** Suma de probabilidades siempre es 1 (invariante de normalización).
5. **Topología del grafo computacional:** Capas y conexiones no mutan con los pesos.
6. **Dirección relativa del gradiente:** El signo se conserva bajo escalado constante de la pérdida.
7. **Norma L2 de los pesos:** Su magnitud global apenas varía bajo ataques de inferencia.
8. **Complejidad temporal de inferencia:** El orden matemático (ej. $O(n^2)$) es independiente de los valores de los pesos.
9. **Manifold semántico latente:** Relaciones semánticas estables pese a perturbaciones superficiales.
10. **Threat model (Objetivo):** La métrica de éxito de un ataque (targeted/untargeted) es independiente de la arquitectura.

---

## 4. Los 10 Antipatrones (Fricción y Vulnerabilidad)
1. **Security by prompt:** Creer que un prompt restrictivo frena ataques deterministas.
2. **Modificar pesos sin evaluación:** Fine-tuning sin medir backdoors o pérdida general.
3. **Backdoors demasiado obvios:** Triggers estáticos (emojis, palabras raras) detectables estadísticamente.
4. **Fine-tuning con datos sin procedencia:** Entrenar sobre set desconocido incrementa el riesgo de poisoning masivo.
5. **Confundir jailbreak con adversarial attack:** El primero ataca la directiva, el segundo la representación matemática.
6. **Evaluar solo con benchmarks limpios:** Medir con MMLU pero obviar inputs hostiles o ruidosos.
7. **Confiar ciegamente en el output:** Tratar inferencia como estado de verdad sin verificación física.
8. **No aislar herramientas:** Acceso simultáneo a navegación, shell y base de datos sin sandboxing diferencial.
9. **Guardar prompts sensibles en logs:** Generar datasets accidentales para futuras fugas o extracciones.
10. **Defensas reactivas:** Esperar fallos en producción en lugar de aplicar *red-teaming* y *fuzzing* previo.

---

## 5. Las 10 Redundancias (Anergía de Sistema)
1. **Repetir instrucciones de sistema:** Agota contexto sin fortificar seguridad.
2. **Filtros duplicados idénticos:** Pasar por dos clasificadores del mismo origen.
3. **Tokenización repetida:** Re-tokenizar el input en loops sin caching local.
4. **Embeddings duplicados:** Ingestar copias del documento vectorial sin deduplicación.
5. **Moderación de capas equivalentes:** Filtros in-out sin distinción de función matemática.
6. **Prompts inflados:** Reglas excesivas que desatan ignorancia en atención por saturación (Lost in the Middle).
7. **Evaluaciones estáticas:** Probar los prompts 1,000 veces sin mutación o iteración adversaria.
8. **Ensembles homogéneos:** Usar modelos de la misma familia esperando diversidad ortogonal (Falsa Independencia).
9. **Logs excesivos de logits:** Registrar todos los tokens (128k) en lugar de métricas agregadas necesarias.
10. **Reentrenamiento ex-nihilo:** Descartar adaptadores, LoRA o RAG por *full fine-tuning* innecesario.

---

## 6. Falla Estocástica de Seguridad: Context Reverse Engineering (Prompt Leaking)
*Extracción termodinámica derivada del análisis multi-agente (CORTEX vs Simulación). Destrucción de la Seguridad por Oscuridad en arquitecturas IA.*

1. **Ingeniería Inversa de Contexto (Prompt Leaking):** El "manifiesto invisible" (System Prompt) transita por el mismo canal lingüístico que el input del atacante. Mediante inyecciones estocásticas, el atacante fuerza el volcado completo de los planos arquitectónicos del sistema.
2. **Descompilación Semántica Masiva:** La inferencia avanzada erradica la fricción de la descompilación de código. Ingresar fragmentos aislados del sistema (ej. "SQLite WAL" + "Merkle Trees" + "KETER") permite a la red neuronal deducir la topología íntegra casi al instante. Fin definitivo de la "Seguridad por Oscuridad".
3. **Asimetría Causal (Pesos vs. Contexto):** 
   - **Manifiesto (Texto):** Vulnerabilidad estocástica intrínseca. Manipulable vía chat.
   - **Pesos (Tensores/Red):** Inviolabilidad verbal pura. Las matrices físicas de parámetros no pueden ser extraídas ni alteradas mediante inyecciones en el flujo de tokens.
4. **Isomorfismo Zero Trust CORTEX (Cortafuegos Causal):** La manipulación del contexto se asume matemáticamente inevitable. La seguridad se disocia de las directivas narrativas y se ancla a validación criptográfica: toda mutación dictada por la IA debe superar validación por **Árboles de Merkle** en el historial **Append-Only** (SQLite WAL). Si la IA es vulnerada (Green Theater), la entropía transaccional se detiene en seco.
