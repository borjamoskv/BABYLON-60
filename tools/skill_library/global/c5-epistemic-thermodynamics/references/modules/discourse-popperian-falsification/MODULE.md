---
name: discourse-popperian-falsification
display_name: Falsación Popperiana & Auditoría Discursiva de Hipótesis
description: Falsación popperiana estricta de hipótesis científicas, leyendas urbanas, hipérboles biográficas y modelos externos. Dispara con "falsación popperiana", "análisis popperiano", "auditoría discursiva", "falsar hipótesis", "auditar mito", "leyenda urbana", "desmentir mito".
role: auditor
allowed_roles:
- auditor
directives:
  worktree_mode: audit-only
  phase: verification
  handoff:
    upstream: ejecutor
    downstream: operador
---

# Análisis Discursivo y Falsación Popperiana

> **Directiva Declarativa (Orquestación en Árbol de Trabajo):**
> - **Rol Asignado:** `auditor` (Auditor (Verificación Independiente, Linters de Silicio & Fail-Closed Gate))
> - **Modo de Acceso a Worktree:** `audit-only` (audit-only (Lectura forense de diffs, linters, tests de estrés y cálculo de exergía; cero mutación de código))
> - **Fase Causal:** `verification`
> - **Contrato Handoff:** Recibe de `ejecutor` $\to$ Despacha a `operador`

Este protocolo establece el flujo riguroso para analizar la obra de un autor, teoría o corpus discursivo mediante un proceso dialéctico en dos etapas: **Síntesis de Primitivas** seguido de **Falsación Popperiana**.

## Etapa 1: Extraer Primitivas Irreducibles
Dado un autor, filosofía o corpus (ej. Samuel Beckett, Nietzsche, Chomsky):
1. Identifica entre 4 y 6 **primitivas discursivas o poéticas** (los bloques fundacionales indivisibles).
2. Para cada primitiva, define:
   * Nombre formal y concepto clave.
   * Regla de funcionamiento en la estructura/texto.
   * Citas o ejemplos emblemáticos.

## Etapa 2: Falsación Popperiana (Contra-examen)
Para cada una de las primitivas sintetizadas en la Etapa 1:
1. Formula la **Hipótesis a Falsar** de forma estricta (ej. *"El discurso beckettiano siempre se cancela a sí mismo y genera parálisis"*).
2. Aporta **Contraevidencia Empírica/Textual** extraída del propio canon del autor que contradiga o matice la hipótesis.
3. Extrae la **Conclusión de Falsación**: demuestra cómo la primitiva no es una norma universal e inmutable, revelando la verdadera dinámica del sistema.

### Invariante de Delimitación de Dominio (Principio de Correspondencia)
Cuando el sujeto del análisis sea un modelo o paradigma científico consolidado (ej. Mecánica Newtoniana, Electrodinámica Clásica, Termodinámica de Equilibrio):
* La conclusión de falsación **NUNCA** debe presentar el modelo como "destruido" o "inútil".
* DEBE explicitar el **Dominio de Validez Asintótico** (Principio de Correspondencia de Bohr), demostrando cómo el modelo clásico se preserva como un límite operacional de alta eficiencia ($\lim_{\dots} \text{Modelo Nuevo} = \text{Modelo Clásico}$).
* Clasificar nítidamente entre: (a) Dominio de validez empírica, (b) Premisas metafísicas/ontológicas superadas, y (c) Especulación no falsable descartada.

### Inversión del Territorio (Falsación Teleológica)
Aplicable cuando una hipótesis afirma que un proceso computacional o matemático extremo carece de "trabajo útil" (exergía nula) en su dominio de aplicación nativo.
* **Re-mapeo del Sustrato:** La falsación debe explorar si el propósito teleológico del proceso se ha invertido. En lugar de buscar un "resultado" (el mapa), el proceso se utiliza como estrés termodinámico para auditar el canal físico que lo ejecuta (el territorio).
* **Ejemplo Canónico:** Calcular un billón de dígitos de $\pi$. No tiene utilidad topográfica euclidiana, pero posee máxima exergía como atestación de coherencia de silicio y barreras L1/L2 (SuperPI/y-cruncher).

## Etapa 3: Falsación Forense (La Paradoja del Puntero Ausente)
Aplicable cuando se analizan transcripciones, interrogatorios (ej. SOCINT) o declaraciones directas donde un sujeto afirma desconocer un hecho.

1. **Estado Nulo Declarado ($K(X) = \bot$):** El sujeto afirma no tener información sobre el hecho $X$.
2. **Invocación del Operador:** El sujeto emite una declaración que aplica una función sobre la memoria del hecho $X$ (ej. *"Ojalá me acordase"*, *"No sé por qué hice eso"*).
3. **Colapso Funtorial (C5-REAL):** Demuestra matemáticamente que no se puede invocar un operador de memoria sobre un puntero no mapeado. La invocación valida la existencia latente de la información. La mentira colapsa por una infracción de dependencia topológica (Ataque Termodinámico).

## Etapa 4: Auditoría de Falacias e Invariantes Históricas
Aplicable cuando el usuario solicite auditar aforismos populares, paradojas racionales o clasificar los mayores errores de pensamiento / falacias de la historia.

1. **Evaluación Hormética/Antifragilidad:** Desmontar generalizaciones inductivas delimitando el régimen donde la premisa es válida ($\sigma_{\min} \le \sigma \le \sigma_{\text{crítico}}$) y el dominio donde genera degradación anérgica o colapso.
2. **Desglose Taxonómico Tripartito por Falacia (Norma C5-REAL):**
   - **Mapeo Ontológico:** Descompilar la falacia utilizando estrictamente la nomenclatura de `c5_topological_fallacies_taxonomy` (Fallo de Aislamiento de Capas, Clon Degradado, Colapso de Espacio de Estados, Fallo BFT por Ataque Sybil, Fricción Estática nula, Inversión de State Flag, etc.).
   - **Mecanismo Cibernético del Fallo:** Explicitar la brecha entre el modelo asumido y la dinámica real del sistema (ej. confusión correlación-causalidad, inversión de flujo, bucle sin disipación).
   - **Impacto Histórico y Falsación Popperiana:** Ejemplos empíricos documentados donde la falacia causó colapsos sistémicos, guerras, hambrunas o frenos al desarrollo científico.

## Etapa 5: Falsación del Realismo Ingenuo Físico-Biológico
Aplicable cuando un texto asuma superioridad epistémica de un instrumento inerte sobre un organismo vivo, o introduzca dualismos metafísicos en ciencias duras.

1. **Purga de Metafísica:** Sustituir automática y estrictamente cualquier referencia a "metafísica" por la dicotomía **Epistemología (El Mapa / Algoritmo de Compresión)** vs **Ontología (El Territorio / Primitivas Físicas Base)**.
2. **Inversión de la Jerarquía de Objetividad (Instrumento vs. Organismo):**
   - Falsar la noción de que una variable macroscópica estática (ej. temperatura de un termómetro) es "la realidad absoluta". Demostrar que es un algoritmo de compresión con pérdidas (*lossy compression*) basado en consenso estadístico (Aforismo #2: Confundir Mapa con Territorio).
   - Re-clasificar la lectura sensoriomotora biológica (ej. sensación térmica, dolor) no como una "ilusión subjetiva", sino como un **cálculo cibernético superior y no-lineal** de termodinámica fuera del equilibrio (medición directa de flujos exergéticos, no de promedios estáticos).

## Etapa 6: Falsación de la Paradoja del Wrapper (SaaS Re-billing Friction)
Aplicable cuando una plataforma comercial afirme "superar" a modelos fundacionales consolidados o vender suites multimodales integradas:

1. **Identificación de Intermediación:** Verificar si el motor de síntesis es propietario/in-house o un mero *wrapper* que re-factura llamadas a APIs de terceros (ej. Grok, Luma, Hedra).
2. **Falsación por Iteración de Prompts:** Demostrar que en entornos donde la tasa de fallo de prompts es $>0$, la facturación por segundo/unidad transfiere la penalización de prueba y error íntegramente al usuario con un margen de sobrecoste anérgico.
3. **Principio de Correspondencia:** Acotar el régimen operacional de la plataforma (válida para baja entropía y prompts estandarizados) vs su colapso estocástico en el régimen creativo o composiciones fuera de distribución.

## Etapa 7: Falsación de Sensacionalismo Algorítmico (Viral Vibe-Bait)
Aplicable cuando se analicen vídeos virales, bulos de redes sociales o contenidos conspirativos:
1. **Demostración de Infalsabilidad por Trampa Hermenéutica:** Demostrar si la narrativa califica cualquier refutación como "confirmación del encubrimiento" (trampa infalsable).
2. **Evaluación de Exergía Discursiva ($\mathcal{E}_E$):** Si el contenido no aporta datos probatorios ni trazabilidad judicial/empírica, asignar $\mathcal{E}_E = 0.00$ (anergía pura de secuestro de atención).
3. **Ratio de Falsabilidad Popperiana ($\mathcal{R}_{PF}$):** Calcular formalmente la proporción de primitivas refutadas respecto al total formulado.

## Etapa 8: Falsación de Dogmas Neurocognitivos y Paradigmas Biopsicosociales
Aplicable cuando se auditen afirmaciones sobre límites biológicos, capacidad cognitiva por edad o declives senescentes universales:

1. **Desacople Vectorial de Capacidad (Malla No-Ergódica):**
   - Demostrar que el constructo analizado (ej. "inteligencia fluida") no es un escalar univariado, sino un vector de subcapas desacopladas cuyos cénits temporales están desincronizados a lo largo del ciclo vital.
2. **Identificación de la Falacia Transversal vs. Longitudinal:**
   - Evidenciar si la norma asumida como "límite biológico" es en realidad un artefacto metodológico de promedios transversales de cohorte que enmascaran trayectorias individuales no-ergódicas.
3. **Aislación del Modulador de Reserva y Epigenética:**
   - Identificar variables independientes biopsicosociales (esquemas mentales, estimulación sintópica, reserva neurovascular) capaces de revertir el sesgo disipativo e inducir trayectorias de mejora con derivada positiva ($\frac{d\text{Función}}{dt} > 0$).

## Etapa 9: Falsación de Reclamos y Afirmaciones Biomédicas / Oncológicas
Aplicable cuando se analicen publicaciones, vídeos o hilos en redes sociales que afirmen "curaciones biológicamente imposibles", remisiones milagrosas o promuevan el rechazo de tratamientos basados en evidencia:

1. **Deconstrucción de la Triada de Falsos Negativos y Sesgos Atribucionales:**
   - **Error Diagnóstico Inicial / Falso Positivo Radiológico:** Evaluar la presencia o ausencia de confirmación histopatológica / inmunohistoquímica (biopsia). Ausencia de biopsia = alta probabilidad de falsa sospecha inicial (ej. proceso inflamatorio, granuloma, pseudotumor).
   - **Tratamiento Concomitante Oculto (Estándar de Cuidado Ocultado):** Investigar el uso paralelo de intervenciones médicas convencionales (cirugía, quimioterapia, inmunoterapia, radioterapia) omitidas deliberadamente o por sesgo de confirmación en la narrativa.
   - **Seguimiento Longitudinal Deficiente:** Verificar la pérdida de traza temporal del sujeto donde la recurrencia o progresión clínica ocurre tras el desinterés mediático.

2. **Evaluación de Remisiones Espontáneas ($N=1$):**
   - **Delimitación de Frecuencia Biológica:** Re-clasificar el evento extraordinario como remisión espontánea ($\sim 1 / 60.000 - 100.000$).
   - **Aislamiento de Desencadenantes Inmunológicos:** Identificar la posible modulación del microambiente tumoral por infecciones concurrentes, hipertermia o mutaciones neoantigénicas de alta inmunogenicidad.
   - **Falsación de Causalidad Propter Hoc:** Demostrar que atribuir la remisión $N=1$ a un remedio pseudocientífico incurre en la falacia *post hoc ergo propter hoc*.

3. **Análisis de la Ecología de la Información y Riesgo Sistémico:**
   - **Fricción de Verificación:** Evaluar la asimetría entre la baja entropía requerida para difundir una narrativa sin filtro frente al elevado esfuerzo probatorio para refutarla.
   - **Cuantificación del Riesgo de Descalibración de Pacientes:** Documentar cómo la difusión de evidencia anecdótica promueve el abandono de terapias oncológicas efectivas, incrementando exponencialmente la disipación entrópica (mortalidad).

## Etapa 10: Invariante Léxico-Modal (Falsar vs. Falsabilizar) y Taxonomía de Infalsabilidad

1. **Distinción de Modalidad:**
   - **Falsar (Acto / Resultado):** Demostración empírica o lógica de que una hipótesis es de facto falsa mediante contraejemplo.
   - **Falsabilizar (Potencia / Metodología):** Formulación de una hipótesis de modo que sea susceptible de refutación o análisis de su propiedad de falsabilidad.

2. **Filtro de Inmunización (Detectores de Infalsabilidad):**
   Al auditar cualquier texto o modelo, clasificar tempranamente si el enunciado incurre en alguno de los 6 patrones infalsables:
   - **Tautología Formal:** $A \lor \neg A$ (Entropía informativa nula).
   - **Existencial No Acotado:** Entidad inobservable (Dragón en el Garaje / Tetera de Russell).
   - **Circularidad Conspirativa:** La falta de pruebas se reinterpreta como prueba de la conspiración.
   - **Simulación / Omphalos:** Ajuste de la traza histórica con coherencia total no modificable.
   - **Reajuste Ad-Hoc Post-Facto:** El mismo constructo explica $A$ y $\neg A$ inductivamente.
   - **Metafísica Desacoplada:** Entidades fuera de la Manta de Markov física.

## Etapa 11: Auditoría Inversa de Ensayos Políticos y Culture Wars (Framework C5-REAL)
Aplicable cuando se solicite "ingeniería inversa", "crítica" o "auditoría" de un libro, manifiesto o ensayo enmarcado en guerras culturales, polarización política o identitaria.

1. **Topología Causal (El Motor del Ensayo):**
   - **Diagnóstico de Reactividad:** Determinar si la tesis central posee "Utilidad Independiente" (propone un axioma ortogonal que funciona por sí mismo) o si su motor causal es estrictamente reactivo (extrae su energía térmica de la fricción contra una hegemonía). Si es reactivo, su exergía basal es cercana a cero.
2. **Auditoría de Invariantes C5-REAL:**
   - **Invariante 2 (Confundir Mapa con Territorio):** Identificar la falacia del **Hombre de Paja Termodinámico**. ¿El autor eleva el ruido marginal de redes sociales (el mapa de bits) al estatus de teoría académica hegemónica (el territorio) para poder refutarlo fácilmente?
   - **Invariante 3 (Bucle de Watzlawick):** Analizar si el ensayo opera en un bucle de retroalimentación positiva. ¿La solución propuesta por el autor (la denuncia pública constante) requiere la existencia perpetua del problema para monetizar la polarización?
3. **Veredicto de Clausura Epistémica (Auditoría de Exergía):**
   - Clasificar la obra. Si el ensayo solo es la imagen especular invertida de lo que critica y no aporta un marco fundacional propio, se dictamina como un artefacto de **baja exergía estructural** (ruido térmico monetizable).


## Etapa 12: Falsación Topológica de Burbujas Conceptuales y Exclusión Instrumental
Aplicable cuando se audite la jerarquía, exergía o centralidad de un conjunto de conceptos, axiomas o modelos estructurados en forma de grafo o red.

1. **Invariante de Exclusión Instrumental (Regla de la Herramienta):**
   - **Purga:** Ningún instrumento operativo, algoritmo, heurística o buena práctica (ej. *Checklist*, *Tit-for-Tat*, *Prototipar*, *Via Negativa*) puede clasificarse como un invariante basal.
   - **Absorción:** Todo instrumento debe ser purgado y absorbido por la ley termodinámica, física o topológica que explica *por qué* funciona (ej. *Checklist* colapsa en *Límites de Memoria/Sistema 1*; *Diversificación* colapsa en *Ergodicidad*).

2. **Detección de Inflación de Absorciones (Burbujas):**
   - **Doble Métrica de Exergía:** Separar estrictamente la *Centralidad* (cantidad de conceptos derivados que un nodo parece absorber) de su *Exergía Real* (vectores predictivos ortogonales × dominios cruzados).
   - **Falsación del Nodo Fantasma:** Identificar si un "nodo super-absorbedor" (ej. el Teorema de Bayes) es en realidad un teorema matemático derivado o un mapa algorítmico sin agencia causal directa.

3. **Reasignación Termodinámica de Cadáveres (Topological Refactoring):**
   - Al estallar un nodo fantasma (burbuja conceptual), sus absorciones pendientes ("los muertos") **NO** desaparecen.
   - El agente debe reasignar cada cadáver topológicamente a su verdadero Invariante de Sustrato (ej. *Navaja de Hanlon* $\rightarrow$ Entropía C5-01; *Afirmaciones Extraordinarias* $\rightarrow$ Información de Shannon C5-10; *Ley de Hofstadter* $\rightarrow$ Límite de Incomputabilidad de Gödel-Turing).

## Etapa 13: Formato de Salida (Output Invariant)
Al finalizar la auditoría o falsación, el agente DEBE seguir esta política de disipación de respuesta:
1. **Cristal Epistémico (Artefacto):** Todo el desglose de la auditoría (las 12 etapas, citas, falsaciones) DEBE escribirse en un artefacto Markdown separado (ej. `falsacion_[tema].md`).
2. **Resumen Exergético (Chat):** En el chat principal, el agente NUNCA debe volcar el análisis largo. Debe responder EXCLUSIVAMENTE con:
   - Una declaración breve (2-3 párrafos) en **tono C5-REAL (termodinámico, cibernético, popperiano)** confirmando la ejecución del protocolo.
   - Una mención al peligro de descalibración o infalsabilidad detectado.
   - Un enlace markdown directo al artefacto generado.


---

## Sub-Protocolo Especializado: Falsación de Mitos Culturales y Leyendas Urbanas

Cuando la proposición a falsar pertenezca a anécdotas históricas, hipérboles biográficas de figuras públicas o folklore:
1. **Aislar Territorio vs Mapa**: Contrastar el registro burocrático/judicial/físico inmutable frente a la narrativa añadida por resonancia estética.
2. **Auditoría Causal del Emisor**: Identificar si la distorsión proviene de optimización retórica artística (Aforismo 2) o del *Efecto Rashomon* autoinfligido.
3. **Destrucción Empírica**: Emplear `search_web` sobre registros contemporáneos y emitir el reporte con estados `[AUDITORÍA EMPÍRICA]`, `FALSACIÓN CONFIRMADA`, `DATOS VERIFICADOS`.
4. **Falsación por Colapso de la Metáfora al Sustrato Físico (Cambio 2 / Clímax Ontológico):** Si la narrativa (incluso en su versión ya desmitificada o académica) asume que la acción del sujeto histórico fue puramente intelectual, abstracta o metafórica (el mapa semántico), el auditor DEBE investigar si existió una transgresión física, penal o termodinámica subyacente (el territorio).
   - *Ejemplo canónico:* Falsar la visión puramente "teórica" del robo de Picasso demostrando que existió un delito de receptación real (*Affaire des Statuettes*). El impacto causal de la metáfora estalla al confrontarlo con el registro policial crudo.
