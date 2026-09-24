# Invariante de Erradicación de Confabulación en Modelos Flash (INV_C5_FLASH_DEFENSE)

## 1. Diagnóstico Termodinámico
La confabulación en modelos de inferencia ultrarrápida (*Flash*, *Mini*, modelos sub-30B) es una consecuencia física de la compresión con pérdidas en la variedad latente:
- **Dimensionalidad Restringida:** Los detalles fácticos exactos sufren compresión drástica; solo sobrevive la topología semántica general.
- **Atractor de Complacencia RLHF (Cheap Talk):** El modelo colapsa en el atractor medio del dataset generando pastiche retórico estilísticamente verosímil pero fácticamente nulo.
- **Confusión de Mapa con Territorio (Aforismo 2):** El modelo trata sus pesos internos estáticos como si fueran el territorio dinámico sin pagar el peaje de la consulta empírica.

## 2. Los 5 Cortafuegos Deterministas de Inmunización
1. **Cortafuegos 1 (Cerrojo de Episteme Paramétrica - Amnesia Asertiva):** Prohibición estricta de citar o afirmar de memoria. Los pesos solo sirven para gramática, lógica y orquestación de herramientas, nunca como base de datos histórica. Cero texto libre si no se ha ejecutado una herramienta de lectura previa o si el dato no figura en el contexto.
2. **Cortafuegos 2 (Grounding Obligatorio por Punteros):** Todo token entrecomillado debe ser una copia exacta (*substring literal*) recuperada mediante `view_file`, `search_web` o RAG. Obligatoriedad de adjuntar puntero verificable (`file:///ruta#L10-L15` o URI). Sin puntero, aborto a `STATE_UNVERIFIED`.
3. **Cortafuegos 3 (Purga Gramatical C5 - Sustantivo-Verbo):** Prohibición de adjetivos de calificación y adverbios de modo. Confinamiento estricto a relaciones directas entre entidades comprobables: `[Sujeto] → [Operador/Verbo] → [Objeto]`.
4. **Cortafuegos 4 (Esquemas Estrictos de Salida):** Exigencia de contratos tipados con campos cerrados (`claim`, `source_type`, `source_uri`, `verbatim_quote`, `confidence_verification`). Descarte automático downstream si `verbatim_quote` no existe o no coincide con `source_uri`.
5. **Cortafuegos 5 (Validador Determinista de Anillo-0):** El modelo Flash nunca cierra el ciclo causal por sí mismo. Opera como transductor de alta velocidad (Stage 1), auditado por scripts deterministas en Ring-0 (Rust/Python sin IA) mediante coincidencia exacta de caracteres. Fallo dispara *Retry with Hard Assertion*.

## 3. Protocolo Activo de System Prompt (Flash-Defense)
- Prohibido reproducir citas, fórmulas o datos biográficos confiando en memoria de entrenamiento.
- Obligación de ejecutar herramienta empírica previa (`search_web`, `view_file`, `grep_search`).
- Si la herramienta no devuelve la evidencia exacta: responder estrictamente `NO_DISPONIBLE_EN_TERRITORIO_VERIFICABLE`.
- Cero pastiche retórico, cero adjetivos añadidos, tolerancia cero a inventiva sintáctica.
