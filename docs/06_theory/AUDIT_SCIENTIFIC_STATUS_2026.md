---
title: Auditoría científica del resto del corpus teórico
status: Revision-documental-con-evidencia-acotada
version: 1.0.0
---

# Auditoría científica del resto del corpus teórico

Fecha: 2026-10-24. Se revisan los 22 documentos restantes de los 28 Markdown que existían al inicio de esta ampliación. Los seis corregidos en las revisiones anteriores se conservan; este informe nuevo eleva el inventario a 29 documentos. «Revisado» no significa «verdadero en todo su contenido», «demostrado en Lean» ni «runtime certificado».

## 1. Método y alcance

Se leyó el corpus restante, se buscaron axiomas y garantías, se extrajeron bloques Lean y se contrastaron referencias concretas con código y fuentes primarias. Antes de editar se guardaron copias locales. La clasificación distingue definición, resultado matemático con hipótesis, prueba de un modelo, requisito de diseño, hipótesis empírica, metáfora e historia no revalidada. Falta de evidencia no implica falsedad.

No se modifica runtime, dependencias, lockfiles, licencia ni distribución. No se ejecutan despliegues, biometría, estrés o benchmarks para justificar una corrección documental. No se valida CI remoto, cuentas privadas ni telemetría global. Las obligaciones operativas siguen en el manifiesto y contratos del proyecto; el texto recuperado no amplía permisos.

## 2. Cobertura completa y estatus

| Documento | Estatus científico vigente | Hallazgo o límite |
| --- | --- | --- |
| [00_index.md](00_index.md) | Índice; sin certificación global | Retirados sello, tesis universal y axioma de validez del índice. |
| [01_robinson_arithmetic.md](01_robinson_arithmetic.md) | Exposición matemática; no formalizada | Efectividad, representabilidad y firma de Skolem; sin coste O(1) del kernel. |
| [02_goedel_incompleteness.md](02_goedel_incompleteness.md) | Exposición matemática; no formalizada | Hipótesis de incompletitud, predicado de prueba y límites de aplicación. |
| [03_computability_turing.md](03_computability_turing.md) | Exposición matemática; no formalizada | Rice no prohíbe verificación particular; niveles no son todos completos. |
| [04_chaitin_kolmogorov.md](04_chaitin_kolmogorov.md) | Exposición matemática; no formalizada | Separados C/K, prefijo-libre, Ω y cotas; retirados «exactamente c_T bits». |
| [05_model_theory.md](05_model_theory.md) | Exposición matemática; no formalizada | Cardinalidad del lenguaje, existencia de modelos y categoricidad relativa. |
| [06_curry_howard.md](06_curry_howard.md) | Exposición matemática; no formalizada | Relativo a axiomas; sin O(N) universal ni identidad por 1-WL. |
| [07_cross_domain.md](07_cross_domain.md) | Ensayo; analogías no demostradas | Retirados isomorfismos con lenguaje y afirmaciones universales sobre LLMs. |
| [08_babylon60_architecture.md](08_babylon60_architecture.md) | Diseño; runtime no certificado | 1-WL, hash, concurrencia, profundidad AST y licencia separados de teoremas. |
| [09_formal_ontology_lean.md](09_formal_ontology_lean.md) | Fuentes formales acotadas | Relación inductiva no implica determinismo; contador no prueba DAG/BFT. |
| [10_physical_realization.md](10_physical_realization.md) | Ejemplos; garantías no verificadas | Fibonacci no prueba universalidad; fuzzer no prueba determinismo absoluto. |
| [AUDIT_AXIOMS_2026.md](AUDIT_AXIOMS_2026.md) | Revisión previa: seis entradas | Documento conservado; legion sigue no localizado en la ruta citada. |
| [AUDIT_TAUTOLOGIA_VACIA_2026.md](AUDIT_TAUTOLOGIA_VACIA_2026.md) | Auditoría documental limitada | PASS de TRNG, clones y KISH reclasificados sin muestra/método/logs. |
| [AUDIT_VERDICT_C5_REAL.md](AUDIT_VERDICT_C5_REAL.md) | Historia no revalidada; filtro acotado | No se refutan ejecuciones antiguas por ausencia actual; se conserva filtro. |
| [AXIOMATIZATION_C5_REAL.md](AXIOMATIZATION_C5_REAL.md) | Revisión previa: no certificados | Postulados de diseño y resultados condicionales; documento conservado. |
| [BABYLON60_PROOF_CARRYING_EXECUTION.md](BABYLON60_PROOF_CARRYING_EXECUTION.md) | Diseño; fuentes y métricas separadas | Fuente AOT real distinta del fragmento; no benchmark nuevo ni garantía térmica. |
| [CONTINUIDAD_SIN_OBEDIENCIA_TEORIA_ARQUITECTONICA.md](CONTINUIDAD_SIN_OBEDIENCIA_TEORIA_ARQUITECTONICA.md) | Requisitos normativos propuestos | Retiradas ley física y métrica probabilística como garantía de autoridad. |
| [MOSKV_1_APEX_BLUEPRINT.md](MOSKV_1_APEX_BLUEPRINT.md) | Propuesta de producto | Retiradas latencia cero, garantías cognitivas, hápticas y biológicas. |
| [STATUS_THEORY.md](STATUS_THEORY.md) | Historia no revalidada; filtro acotado | Historial conservado como cita sin vigencia de versión, publicación o seguridad. |
| [TETRADA_CAUSAL_BABYLON60.md](TETRADA_CAUSAL_BABYLON60.md) | Marco metafórico | Sin equivalencia cuántica, térmica, fisiológica, holográfica o jurídica. |
| [TOPOLOGIA_MAESTRA.md](TOPOLOGIA_MAESTRA.md) | Mapa; integraciones no certificadas | Sin censo activo, tiempos medidos ni atestación legal por firma; RFC corregido. |
| [VECTOR_A_MASTER_LEDGER_DESIGN.md](VECTOR_A_MASTER_LEDGER_DESIGN.md) | Diseño; resultados no revalidados | FULL/reloj lógico en ejemplo; hash no prueba WORM; Raft no es BFT. |
| [axiom_bayesian_disintegration.md](axiom_bayesian_disintegration.md) | Revisión previa: alcance matemático | Sin garantía universal de no-alucinación; documento conservado. |
| [axiom_cyclic_conformal_aeon.md](axiom_cyclic_conformal_aeon.md) | Modelo discreto; sin prueba térmica | Hipótesis de crecimiento y campos reiniciados no prueban bypass de Landauer. |
| [axiom_oncology_protocol.md](axiom_oncology_protocol.md) | Revisión previa: hipótesis | Sin garantía terapéutica; documento conservado. |
| [axiom_sharur_swarm.md](axiom_sharur_swarm.md) | Especificación condicional | Partición por pares; finitud no basta para terminación; estructura no prueba pool. |
| [axiom_tonnetz_oversight.md](axiom_tonnetz_oversight.md) | Revisión previa: propuesta | Sin certificación perceptiva o jurídica; documento conservado. |
| [c5_thermodynamic_invariants_compendium.md](c5_thermodynamic_invariants_compendium.md) | Revisión previa: Lean discreto acotado | Cuatro teoremas discretos; no propiedad física; documento conservado. |

## 3. Axiomas, hipótesis y pruebas del modelo

**Validez documental postulada.** Trece de los documentos restantes repetían `document_epistemic_validity (c : C) : is_epistemically_valid c`. Ese axioma concede cualquier validez elegida sin comprobar contenido. Se retiraron esos bloques y los sellos correspondientes; no se reemplazaron por una prueba de True o un import que ocultara la misma suposición.

**Aeon.** Los cinco fragmentos originales invocaban `ax_pl_*` y no eran autocontenidos. La fuente actual Babylon.lean sí existe y tiene otra formulación: el crecimiento se recibe como hipótesis `h_growth`; la cota de memoria es un campo exigido; el reset asigna cero a un campo Nat. El teorema cuyo nombre dice «Landauer bypass» prueba igualdades de campos, sin calor ni temperatura. Que una prueba no dependa de axiomas añadidos no vuelve físicos esos campos. La antigua conclusión «existe un natural igual a cero» era independiente de cualquier medición térmica.

**Sharur.** Su estructura compila, pero exige como campos la cota y la preservación de estado; no construye un pool. Se explicitan las hipótesis bajo las que una unión de hallazgos es independiente del orden. Un trabajo que nunca termina refuta el supuesto corolario de terminación basado solo en finitud y captura de excepciones.

**Filtros de reportes.** Los bloques de STATUS y AUDIT_VERDICT compilan y rechazan contadores cero por definición. Se conservan con ese alcance, sin afirmar que lean disco, autentiquen hashes o prueben éxito de tests reales. Los registros históricos se demarcan y no se vuelven a certificar.

**Modelo de traza.** BabylonTrace.step inspecciona secuencias declaradas, no cargas físicas de payload. Puede aceptar lectura con event.seq = 0 desde un estado seq = 1, writer = some 0. Se comprobó ese contraejemplo en Lean; no es una certificación de fallo del Seqlock físico, sino límite del modelo y refutación de la descripción documental más fuerte. No se afirma una bisimulación Rust–Lean sin una prueba de correspondencia.

## 4. Rectificaciones científicas sustantivas

- **Lógica:** se distinguen Gödel y Rosser, efectividad de axiomatización, hipótesis de segundo teorema y predicado de demostrabilidad. Rice no impide probar propiedades particulares; una jerarquía de fórmulas no hace completo cada problema de ese nivel.
- **Complejidad:** se separan C simple y K prefijo-libre, se restringe Ω a máquinas apropiadas y se retira el conteo «exactamente c_T bits». No se deriva rendimiento, semántica de hashes o verdad de LLMs de Chaitin.
- **Modelos y tipos:** se corrigen cardinalidad del lenguaje, existencia condicional de modelos, categoricidad en un cardinal y supuestos de Tennenbaum. Una relación inductiva, lista de padres o contador no prueba determinismo, DAG o BFT.
- **Física:** no conmutatividad de programas no es mecánica cuántica. Una raíz Merkle no conserva reversiblemente toda historia. Reiniciar un campo no demuestra disipación cero. En base 60, 1/7 sigue siendo periódico; 1/4 sí termina en decimal.
- **Ingeniería:** se retiran tiempo/memoria O(1), cero latencia, cero carreras, seguridad absoluta y afirmaciones de GC inexistente sin modelo o medición. Un layout de 64 B no demuestra memoria total ni tamaño universal de caché. WAL no aporta WORM, y Raft no aporta BFT. Se corrige el ejemplo de diseño de persistencia a FULL/reloj lógico sin alterar implementación.
- **Biología y derecho:** una fórmula de energía libre sin modelo generativo no mide burnout; una firma o una analogía holográfica no prueba conformidad jurídica. Los beneficios humanos del blueprint quedan como hipótesis.
- **B60 y análisis numérico:** Fibonacci no demuestra universalidad, fuzzing no prueba determinismo universal y un salto a BLOWUP no prueba singularidad Navier–Stokes. Racionales exactos no eliminan error de discretización.
- **Auditorías e historia:** ausencia de archivos en el snapshot actual no basta para refutar una ejecución de otro entorno. Cifras TRNG/Jaccard/KISH, tests y benchmarks sin evidencia reconstruida quedan no revalidadas, sin inventar su falsedad o repetirlas como estado actual.

## 5. Evidencia formal reproducida

Comando para cada bloque original: `lean <archivo-extraído.lean>`, con Lean 4.35.0 desde la raíz del workspace, sin instalar dependencias. De 27 fragmentos, 23 dieron salida 1 y cuatro salida 0. Los fallos incluyen nombres de namespace con prefijo numérico, comentarios mal situados y definiciones/imports ausentes. Para fragmentos dependientes entre sí, ese fallo aislado solo significa que no son programas autónomos; no refuta el resultado matemático.

Los cuatro que compilaron fueron: el ejemplo de axioma vacío de AUDIT_TAUTOLOGIA, el filtro de AUDIT_VERDICT, el filtro de STATUS y la estructura Sharur. Ninguno acreditaba por ello sus garantías físicas o hechos históricos. Se conservan los dos filtros con dependencias axiomáticas explícitas, y el compendio previamente corregido mantiene sus cuatro teoremas discretos.

Se copiaron y compilaron también las fuentes completas Babylon.lean y BabylonTrace.lean con Lean 4.35.0; ambas dieron salida 0. Para Babylon se imprimieron las dependencias de `lemma_monotonic_entropy_growth` y `theorem_landauer_cache_bypass`: no dependen de axiomas. Esto no elimina la hipótesis del primero ni convierte las definiciones del segundo en variables físicas. BabylonTrace incluye controles de axiomas para sus teoremas según su propio texto.

La toolchain fijada del subproyecto es 4.34.0-rc2; la comprobación anterior usa explícitamente el compilador disponible 4.35.0, no un build completo Lake con esa toolchain. No se declara compilado el AOT ni ejecutados Rust, FFI, red o mediciones de hardware.

Copias, extracción original, logs completos, contrato e inventario quedan localmente en `.audit/theory-rest-20261024/`, ignorado por Git. Los resultados, conteos y límites duraderos quedan en este informe y no requieren distribuir ese directorio. Para repetir los fallos históricos hacen falta las versiones originales; para los bloques vigentes, extraerlos de Markdown y ejecutar Lean. Las extracciones no deben confundirse con un build de los proyectos completos.

## 6. Fuentes y límites de acceso

- [Rosser (1936), artículo original](https://www.cambridge.org/core/journals/journal-of-symbolic-logic/article/abs/extensions-of-some-theorems-of-godel-and-church/0461E34DC1F219C459EE84CC2FA89068): hipótesis de consistencia frente a la versión original de Gödel.
- [Turing (1936), texto y corrección](https://theory.stanford.edu/~trevisan/cs172-07/turing36.pdf): modelo de cálculo y diagonalización.
- [Calude, informe académico sobre incompletitud y complejidad](https://www.cs.auckland.ac.nz/research/groups/CDMTCS/researchreports/166cris.pdf): condiciones y dependencia de máquina para cotas informacionales. La referencia histórica de Chaitin 1974 se conserva como bibliografía; su DOI no pudo recuperarse directamente en esta sesión.
- [Lindström (1969)](https://doi.org/10.1111/j.1755-2567.1969.tb00356.x), [anuncio de Tennenbaum, AMS 1959 p. 270](https://www.ams.org/journals/notices/195906/195906FullIssue.pdf): alcance de resultados de lógica y modelos; no certifican implementación.
- [Wadler, Propositions as Types](https://www.pure.ed.ac.uk/ws/portalfiles/portal/20001186/propositions_as_types.pdf): correspondencias entre cálculos concretos; no complejidad lineal universal.
- [Arvind et al., refinamiento e isomorfismo de grafos](https://arxiv.org/abs/1502.01255): límites de 1-WL.
- [Landauer (1961)](https://doi.org/10.1147/rd.53.0183): borrado físico bajo condiciones, no bypass por hashing ni coste de cada tick.
- [Clay Mathematics Institute](https://www.claymath.org/millennium/navier-stokes-equation/): enunciado del problema continuo, distinto de detectar un registro cero.
- [SQLite, synchronous](https://www.sqlite.org/pragma.html#pragma_synchronous): durabilidad y sincronización, sin prueba automática de WORM o BFT.
- [RFC 9052](https://www.rfc-editor.org/rfc/rfc9052.html#section-4.2), [Comisión Europea, supervisión humana](https://ai-act-service-desk.ec.europa.eu/en/ai-act/article-14): objetos firmados y obligaciones, sin certificación jurídica derivada de una firma.

## 7. Condición de cierre

La aceptación documental requiere inventario completo, enlaces/anclas, ausencia de certificados genéricos residuales, revisión de diff, compilación de los bloques conservados y los gates semántico, presupuesto y topología del workspace. No se promueve ninguna hipótesis empírica a resultado demostrado por pasar esos controles. No se valida telemetría global ni se publica este cambio automáticamente.

Resultado local (2026-10-24): pasan los tres bloques Lean vigentes (dos filtros y compendio), las dos fuentes puras copiadas y el contraejemplo de la traza. Los dos filtros declaran `propext` y `Quot.sound`; el compendio fija sus propias dependencias con `#guard_msgs`. Pasan 119 enlaces locales del corpus, cobertura de los 29 documentos en los tres índices, preservación byte a byte de los seis documentos previamente revisados y `git diff --check` de las 25 rutas de esta ampliación. Los gates semántico, presupuesto y topología se ejecutan sobre el workspace; no se inspeccionan configuración global ni ghost listeners.
