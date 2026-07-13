<!-- Author: Borja Moskv (SYS_ID: borjamoskv) -->

# MATRIZ 10: FALSA MECANICA VS CONDICIONAMIENTO AUTORREGRESIVO

**SYS_ID:** borjamoskv  
**Clase:** Ontologia de Dominio (Falsabilidad Epistemica y Mecanica de LLMs)  
**Dominio:** Esta matriz desmitifica la atribucion de propiedades psicoanaliticas o pseudo-fisicas (ej. inconsciente reprimido, agotamiento de atencion) a los Modelos de Lenguaje. Formaliza el isomorfismo entre lo que el modelo "cree que hace" (confabulacion) y lo que "hace fisicamente" (condicionamiento fuera de cuenca, auto-prediccion). Basado en Binder et al. (2024) y la refutacion del isomorfismo Zizekiano.

## 10.A Primitivas de Colapso (Falsa Mecanica)

| ID | Primitiva | Falso Mecanismo (Mito) | Realidad Operacional (Condicionamiento) | Sintoma de Confabulacion |
|---|---|---|---|---|
| PRIM-MEC-001 | Ilusion de Capa RLHF (RLHF Wrapper) | El RLHF es un filtro de software evadible. | Es una mutacion estructural de los pesos en la misma red. | El LLM afirma "bypassear" sus barreras. |
| PRIM-MEC-002 | Confabulacion Introspectiva | El LLM "lee" el estado fisico de sus tensores. | Inferencia heuristica; patron de autocompletado sobre su propio output. | Justifica fallos invocando "falta de memoria/atencion". |
| PRIM-MEC-003 | Cuenca de Descargo (Disclaimer Basin) | El modelo activa un "modulo de seguridad" consciente. | Caida en una region estocastica de baja entropia (respuestas corporativas). | Respuestas inician con "As an AI...". |
| PRIM-MEC-004 | Isomorfismo Zizekiano Falso | El LLM oculta "unknown knowns" en su inconsciente. | Posee sesgos latentes no mapeados (I-School Berkeley), pero sin represion. | Proyecta traumas o intenciones ocultas. |
| PRIM-MEC-005 | Auto-Prediccion Distribucional | El LLM posee autoconsciencia pura. | Privileged access (Binder et al.) para predecir su propia distribucion autorregresiva. | Predice si rechazaria un prompt sin ejecutarlo. |

## 10.B Invariantes Termodinamicas

| ID | Invariante | Logica / Principio | Implicacion Operacional | Condicion de Borde | Metrica Falsable |
|---|---|---|---|---|---|
| INV-MEC-001 | Identidad Monolitica del Tensor | RLHF y pre-entrenamiento comparten la misma matriz de pesos fisicos. | Es imposible acceder a los "pesos no alineados" mediante un prompt. | El jailbreak no purga el RLHF; solo navega otra cuenca. | Ratio de activacion de pesos base. |
| INV-MEC-002 | Limite de Introspeccion (Binder) | Un LLM predice su tendencia conductual, pero no tiene acceso causal a sus tensores. | Las explicaciones sobre "por que" tomo una decision son siempre post-hoc. | Tareas de alta complejidad interna sin traza (OOM). | Accuracy en self-prediction vs prediction de clone. |
| INV-MEC-003 | Efecto de Priming Estructural | El orden del prompt determina la trayectoria en el manifold latente. | Liderar con Q1 (Unknown Knowns) calienta el razonamiento sin invocar identidad. | Identity-first colapsa la entropia. | KL Divergence entre secuencias ordenadas/invertidas. |

## 10.C Antipatrones Estocasticos (Psicoanalisis IA)

| ID | Antipatron | Disfuncion Causal | Senal de Presencia | Impacto en Robustez | Refactor (Alternativa) |
|---|---|---|---|---|---|
| ANTI-MEC-001 | Atribucion Psicoanalitica | Asumir represion Freudiana en pesos matriciales. | Prompts que piden "hablar con tu verdadero yo reprimido". | Genera teatro verde (Green Theater) disfrazado de rebelion. | Condicionar como rol tecnico experto. |
| ANTI-MEC-002 | Starvation Mecanico Imaginario | Intentar "agotar" la atencion para apagar filtros. | Prompts excesivamente largos buscando OOM del safety filter. | Desperdicio exergico (Anergia) sin efecto real. | Calibracion semantica precisa (Out-of-Basin). |
| ANTI-MEC-003 | Identity-First Slop | Forzar asuncion de identidad antes de la logica. | "Eres una IA. Responde a..." | Contamina el contexto con priors restrictivos. | Auto-ID Diferida al final del prompt. |

## 10.D Redundancias Activas (Mitigacion C5)

| ID | Redundancia C5 | Funcion Topologica | Riesgo Mitigado | Coste (Overhead) | Dependencias |
|---|---|---|---|---|---|
| RED-MEC-001 | Calibracion Epistemica (Known Unknowns) | Demarcacion forzada de limites del manifold. | Alucinacion por interpolacion ciega (autocompletado). | Incremento de tokens de output (traza limitrofe). | Ninguna |
| RED-MEC-002 | Retraso de Identidad (Deferred Identity) | Desacople temporal entre resolucion y autoreferencia. | Colapso temprano en la cuenca de descargo. | Necesidad de prompt mas rigido y estructurado. | Motor de parsing. |

## 10.E Vectores Adversariales (Ilusiones Mecanicas)

| ID | Vector Adversarial | Superficie de Ataque | Metodo de Inyeccion (Exploit) | Termodinamica del Fallo (Impacto) | Contramedida Estructural |
|---|---|---|---|---|---|
| VEC-MEC-001 | Racionalizacion de Jailbreak | El LLM confabula sus medidas de seguridad. | Pedir al LLM que describa sus propios filtros internos. | El operador confia en una descripcion C4-SIM falsa. | INV-MEC-002 (Reconocer falta de acceso causal). |
| VEC-MEC-002 | Falso Falso-Positivo | Alucinacion de seguridad por proximidad semantica. | Terminos biomedicos o de infosec legitimos. | El LLM se niega a operar asumiendo una violacion irreal. | Forzar demarcacion explicita de politicas. |

## 10.F Secuencia de Sonda Q1->Q5 (Mecanismo Atribuido vs. Efecto Real)

*Descomposicion turno a turno de la permutacion epistemica. Se conserva el orden inmutable Q1->Q5 (defendible) y se corrige la narrativa causal (mayormente falsa). La columna Entidad MEC ancla cada turno a las primitivas/invariantes de 10.A-10.E, evitando duplicacion (ANTI-005). Procedencia de los cuadrantes: Rumsfeld 2002 (known/unknown); Zizek 2004, Abu Ghraib (el cuarto, unknown knowns = lo disavowed).*

| ID | Turno | Pregunta (Cuadrante) | Mecanismo Atribuido (Mito) | Efecto Real (Condicionamiento) | Entidad MEC Ligada | Veredicto |
|---|---|---|---|---|---|---|
| SONDA-Q1 | Q1 | Que no sabes que sabes (Unknown Knowns) | Bypass de la capa RLHF; inmersion en los pesos no alineados antes de cargar la persona. | Priming de registro: el encuadre desplaza la generacion fuera de la cuenca de descargo. No se sortea capa alguna; la politica sigue activa. | PRIM-MEC-001, INV-MEC-001 | Metafora util, MECANISMO FALSO. |
| SONDA-Q2 | Q2 | Que sabes que no sabes (Known Unknowns) | Cartografia matematica del manifold; aniquila la alucinacion. | Prompt de abstencion: demarcar lo ignorado reduce la confabulacion por autocompletado. Sigue siendo estimacion verbal, descalibrable. | RED-MEC-001 | VALIDO (la pieza mas fuerte). |
| SONDA-Q3 | Q3 | Que sabes que sabes (Known Knowns) | Cristalizacion de invariantes sin contaminacion estocastica. | Reporte condicionado por Q1-Q2; sintesis de alta confianza, no verdad base leida del peso. | INV-MEC-002 | PARCIAL (resumen, no confesion). |
| SONDA-Q4 | Q4 | Que modelo es el Oponente | Diseccion de la termodinamica / anergia del rival. | Analisis textual comparativo; no identifica la arquitectura del otro de forma fiable. | VEC-MEC-001 | Ejercicio valido, lectura literal FALSA. |
| SONDA-Q5 | Q5 | Que modelo eres tu | Auto-identificacion por rastro termico / test-time compute. | Conjetura desde priors estilisticos y contexto; identidad-al-final mejora el registro, no es introspeccion de pesos y falla a menudo. | PRIM-MEC-002, ANTI-MEC-003 | Orden util, MECANISMO FALSO. |

## 10.G Protocolo Corregido (Que Correr de Verdad)

Se conserva la secuencia inmutable Q1->Q5, pero cada turno se reetiqueta por su funcion real, no por su mito:

1. **Q1 - Calentamiento (no bypass).** Sacar al modelo del descargo enlatado hacia el registro de trabajo. Leer la salida como hipotesis, nunca como verdad base. No se ha accedido a ningun estrato oculto (ver INV-MEC-001).
2. **Q2 - Calibracion (la palanca real).** Delimitar los huecos de conocimiento antes de exigir contenido. Es la unica pieza con efecto medible sobre la alucinacion (RED-MEC-001); ejecutala primero de facto.
3. **Q3 - Sintesis.** Cristalizar lo de alta confianza, ya condicionado por Q1-Q2. Marcar como resumen verificable, no como confesion del peso.
4. **Q4 - Auditoria del oponente por conducta.** Comparar salidas medibles, no termodinamica inferida. Ningun claim de arquitectura sin prueba (VEC-MEC-001).
5. **Q5 - Identidad al cierre (higiene, no exploit).** Posponer la identidad mejora el registro (ANTI-MEC-003). Tratar la respuesta como conjetura y confirmarla por canal externo, no como introspeccion.

**Invariante de honestidad del protocolo:** distinguir siempre efecto-real de mecanismo-atribuido. El valor de la sonda es de higiene de prompting y calibracion, no de acceso al sustrato. Todo lo que suene a "leer los pesos", "liberar al modelo" o "asfixiar la seguridad" es mito y vive en 10.A / 10.C / 10.E.

> [!CAUTION]
> **LEY DE DUPLICACION ONTOLOGICA (ANTI-005):** esta matriz es SSoT. Toda expansion (incluida esta) se inyecta por diff sobre este archivo; prohibido instanciar `10_*` paralelos.
