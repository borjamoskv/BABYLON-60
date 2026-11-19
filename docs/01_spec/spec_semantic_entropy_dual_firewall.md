---
title: Entropía semántica Q16 y clasificación condicionada por señal externa
status: Dominio-y-estados-del-solver-validados-con-alcance-acotado
version: 3.2.0
crate: babylon60-kernel
ring: Ring-0 (categoria del proyecto)
---

# Entropía semántica Q16 y clasificación condicionada por señal externa

Revisión científica y reparación: 2026-10-26. Se mantienen retiradas «Production Ready», el sello genérico «Verified», la latencia de 1,92 ns y la garantía de detectar toda creencia errónea. Los fallos de dominio/partición se corrigen en §7; el rechazo explícito de UNKNOWN/error se documenta en §8 y el adaptador Z3 con consulta vinculada, en §9. Ring-0 es aquí una categoría del proyecto, no evidencia de ejecución privilegiada ni aislamiento del sistema operativo.

Fuentes locales: [módulo Rust](../../00_ABZU_KERNEL/crates/babylon60-kernel/src/semantic_entropy.rs), [modelo Lean](../../scripts/c5_demos/SemanticEntropyApoptosis.lean) y [test sintético de cuatro cuadrantes](../../00_ABZU_KERNEL/crates/babylon60-kernel/tests/stress_semantic_entropy_100k.rs). Identificador de diseño: `INV_C5_SEMANTIC_ENTROPY_DUAL_FIREWALL`.

## 1. Qué mide la entropía y qué significa SAT

La entropía semántica estima dispersión entre significados de respuestas muestreadas. Una entropía baja también es compatible con respuestas sistemáticamente equivocadas; una alta puede reflejar varias respuestas válidas o ambigüedad. El método de [Farquhar et al. (Nature, 2024)](https://doi.org/10.1038/s41586-024-07421-0) aborda confabulaciones, sin garantizar factualidad. [Kuhn, Gal y Farquhar (ICLR, 2023)](https://arxiv.org/abs/2302.09664) estudian la agrupación por significado y la utilidad predictiva de esa incertidumbre. Esos resultados no validan automáticamente este módulo ni un umbral universal.

Según [SMT-LIB 2.7, §4.2.5](https://smt-lib.org/papers/smt-lib-reference-v2.7-r2025-07-07.pdf), SAT indica existencia de un modelo de las fórmulas y supuestos suministrados; UNSAT indica que no lo hay y UNKNOWN que la búsqueda no concluyó. SAT no es un certificado general de verdad factual. Para demostrar una conclusión F desde supuestos T puede comprobarse la insatisfacibilidad de T ∧ ¬F; la consistencia de T y su correspondencia con el problema real siguen siendo obligaciones distintas.

El núcleo Rust recibe `SolverOutcome` del llamador, con `Sat`, `Unsat`, `Unknown` y `Error(SolverError)`. Los errores distinguen `Timeout`, `Transport`, `Protocol` y `Execution`; ninguno autoriza una variante positiva ni equivale a UNSAT. La API anterior aceptaba un booleano y no podía representar esa diferencia. El núcleo no invoca Z3; el adaptador host de §9 sí lo ejecuta y comprueba la vinculación local del resultado. Su etiqueta `VerifiedGenuine` no demuestra que una respuesta sea verdadera.

## 2. Modelo matemático y condiciones de la partición

Para n muestras y una partición válida en K clases no vacías, con tamaños cₖ tales que Σcₖ = n, el estimador empírico basado en frecuencias es:

$$\widehat H = -\sum_{k=1}^{K} p_k\log_2 p_k,\qquad p_k=\frac{c_k}{n},\qquad 1\le K\le n.$$

Se mide en bits y satisface 0 ≤ Ĥ ≤ log₂K ≤ log₂n. Para n ≤ 8 su máximo es 3 bits. Es un estimador finito de la distribución de clases, no una medición de verdad ni de energía física. La generación de muestras y la asignación de significado introducen errores y costes adicionales.

Una matriz E compactada en `u64` usa el índice `8i+j`, para 0 ≤ i,j < 8. Interpretarla como relación de equivalencia exige reflexividad, simetría y transitividad. Las predicciones de un clasificador NLI bidireccional no acreditan por sí mismas esas tres propiedades. La versión reparada valida la relación y rechaza los bits fuera de la submatriz declarada; no inventa equivalencias mediante un cierre transitivo.

Sus bucles de agrupación y suma realizan O(n) iteraciones con palabras de tamaño fijo y n acotado. Esto no incluye generación de texto, construcción de la matriz NLI, traducción a restricciones, solver, transporte o persistencia. La afirmación de «un ciclo de CPU» y la complejidad o latencia del pipeline completo quedan NO_VERIFICADAS.

## 3. Cuantización Q16 y límites de la implementación actual

La fórmula de referencia para una tabla con redondeo al entero más próximo es:

$$L[n,c]=\operatorname{round}\!\left[-\frac{c}{n}\log_2\!\left(\frac{c}{n}\right)2^{16}\right],\quad 1\le c\le n,\qquad L[n,0]=0.$$

$$\widehat H_{Q16}=\sum_{k=1}^{K} L[n,c_k],\qquad \widehat H_{\mathrm{bits}}=\frac{\widehat H_{Q16}}{65536}.$$

Es una aproximación entera del logaritmo real. Si cada término se redondea como indica la fórmula, el error absoluto de cuantización de la suma en bits es como máximo K/(2·65536). Esta cota presupone una partición válida; no corrige una agrupación equivocada. La comparación numérica local encuentra cero discrepancias entre las entradas válidas de la LUT actual y esa fórmula de redondeo.

En una partición válida de hasta ocho clases, el máximo ideal Q16 es 196608; Q16 designa la escala fraccionaria, no un límite de 65535 para toda entropía. El `u32` de Rust puede representar ese valor. El comentario anterior de Lean que limitaba `hSemScaled` a `[0..65535]` se corrigió: su tipo `Nat` no impone esa cota.

La auditoría inicial reprodujo estos defectos, corregidos en la fuente actual con los controles de §7. La tabla conserva la observación anterior, no el resultado posterior a la reparación:

| Entrada o condición | Resultado reproducido o límite |
| --- | --- |
| n = 8, admitido por el guard | `(1u8 << n) - 1` desborda el desplazamiento. El probe con comprobaciones activas hace panic; el optimizado sin ellas devuelve H = 0, K = 8 para un clique completo, que debería tener K = 1. No se generaliza ese comportamiento a todo compilador/target. |
| n = 0 o n > 8 | `compute_quotient_entropy` devuelve `(0,0)`; `evaluate(..., true)` puede retornar `VerifiedGenuine`, sin propagar una entrada inválida. |
| Relación simétrica no transitiva: filas binarias `011,111,110`, n = 3 | Se cuentan tamaños superpuestos 2 + 2, cuya suma excede n. El resultado 51114 no es la entropía de una partición válida de esas tres muestras. |

El cuerpo del módulo usa arrays locales y aritmética entera, y la crate declara `no_std` y lints de Clippy sobre flotantes. Esto no certifica ausencia global de asignaciones, comportamiento de todos los llamadores o disipación nula de Landauer. La reparación no cambia la LUT ni el umbral; corrige también los comentarios que confundían cuantización, clasificación y garantías físicas.

## 4. Clasificación y rechazos explícitos

Para una entrada válida, sea h el valor entero calculado y τ = `TAU_SEM_Q16 = 55706`, aproximadamente 0,850006 bits. Solo `Sat` permite una variante positiva; la entropía elige el subtipo de `Sat`/`Unsat`. Las entradas inválidas se rechazan antes de clasificar el resultado del solver, incluso si es `Unknown` o error.

| Variante Rust, con nombre histórico | Condición literal | Alcance del resultado |
| --- | --- | --- |
| `VerifiedGenuine` | h ≤ τ y `Sat` | Clasificación de baja dispersión con resultado externo afirmativo; no demuestra conocimiento genuino. |
| `VerifiedPolysemy` | h > τ y `Sat` | Clasificación de alta dispersión con resultado afirmativo; no demuestra polisemia legítima. |
| `ApoptosisConfabulation` | h > τ y `Unsat` | Devuelve el campo código `0xDEAD_6060`; no identifica por sí mismo una confabulación. |
| `ApoptosisIncorrectBelief` | h ≤ τ y `Unsat` | Devuelve el campo código `0xDEAD_6061`; no demuestra falsedad ni purga conocimiento. |
| `SolverUnknown` | Matriz válida y `Unknown` | Resultado inconcluso, rechazado; no expresa insatisfacibilidad. |
| `SolverFailure { error }` | Matriz válida y `Error(error)` | Conserva el tipo de fallo; rechazado sin atribuir un resultado lógico a la fórmula. |
| `InvalidInput { error }` | n o matriz inválidos, con cualquier `SolverOutcome` | Error tipado de dominio o relación con precedencia; nunca una variante positiva. |

La función retorna un enum. No ejecuta por sí misma aborto, cierre de canal, emisión de `CORTEX-TAINT`, admisión a Ring-1 o commit persistente. `STATUS_VERIFIED = 0x01` es una constante declarada; no es un código de proceso retornado por `evaluate`. Los efectos requieren un consumidor y evidencia independiente de su ejecución.

## 5. Alcance de la prueba Lean

El archivo Lean define un registro con enteros `hSemScaled`, `tauSem` y un `SolverOutcome` tipado. Cuatro teoremas evalúan registros concretos. El nombre histórico `falsity_never_reaches_ring1_commit` se conserva, pero su hipótesis actual es `solverOutcome = Unsat`: prueba rechazo de ese resultado suministrado, sin identificarlo con falsedad factual. El tipo no contiene una proposición factual, un solver, un estado Ring-1 real ni una operación de commit.

La regresión compila la fuente real copiada sin alteraciones y comprueba la equivalencia universal del modelo, junto con el rechazo universal de `Unknown` y de cualquier `Error(reason)`:

$$\operatorname{evaluateCausalGate}(c)=\operatorname{Verified}\quad\Longleftrightarrow\quad c.\operatorname{solverOutcome}=\operatorname{Sat}.$$

Esto delimita una propiedad universal del gate abstracto. Un registro con `Sat` puede ser `Verified` mientras una proposición externa, por ejemplo 1 + 1 = 3, es falsa: el modelo no contiene una relación entre ambos. La ausencia de tal relación impide convertir la clasificación en una prueba de no-alucinación.

La revisión inicial encontró τ = 22282 (~0,34 bits) y códigos abreviados distintos en Lean. El modelo reparado usa 55706 y los códigos completos de Rust; el ejemplo de entropía alta usa 63633. La regresión contrasta constantes/bordes contra Rust y exige dependencias de axiomas vacías para los diez teoremas del modelo y los 27 casos finitos añadidos. Eso no es un refinamiento completo: Lean recibe un resumen, no calcula ni valida la matriz/LUT ni modela `InvalidInput`. Los tests Rust verifican esa validación por separado.

## 6. Requisitos de diseño y evidencia pendiente

La prohibición de validar hechos solo por autoconsistencia se conserva como requisito. La condición histórica «SAT o testigo Lean» requiere precisar la fórmula, sus supuestos, la conclusión y la evidencia que conecta los datos con el problema; no debe usarse como autorización universal de afirmaciones factuales. Esta precisión documental no acredita una política productiva implementada.

El dominio, la matriz y los límites n = 0/8/9 se validan con errores tipados y regresiones. UNKNOWN/error tienen estados separados y rechazados. El adaptador de §9 añade ejecución real y vinculación local con la consulta esperada. Siguen pendientes autenticación del binario, integración en consumidores productivos y evaluación sobre datos etiquetados independientes. El umbral requiere calibración y tasas de error por tarea; no es una constante científica universal.

Los objetivos «1,92 ns» y «menos de 10 ns en ARM64/x86_64» quedan NO_VERIFICADOS aquí. El test enlazado repite cuatro entradas sintéticas n = 5 y divide el tiempo total multihilo entre operaciones: esa magnitud mide coste amortizado de throughput de esa carga, no latencia individual máxima ni precisión factual. No se reejecutó ese estrés ni se midieron energía o latencia en esta revisión. Un benchmark debe identificar hardware, compilador, opciones, carga no eliminable, warmup, método y distribución de tiempos.

Las copias iniciales, comandos, hashes, comprobación Lean y probes numéricos/Rust aislados se conservan en `.audit/scientific-guarantees-20261026/semantic/`. Un panic capturado por el probe queda registrado como fallo del caso, aunque el programa recolector termine con código 0. Los controles documentales de la auditoría principal no constituyen certificación del runtime.

## 7. Primera reparación: dominio y aritmética

La primera reparación cambió `compute_quotient_entropy` a `Result<(u32, u8), SemanticEntropyInputError>`. Los errores son `SampleCountOutOfRange`, `BitsOutsideDomain`, `NotReflexive`, `NotSymmetric` y `NotTransitive`. `evaluate` añadió `InvalidInput { error }`; no se sustituye una entrada inválida por entropía cero. Su argumento booleano se conservó en aquella campaña y se reemplaza en §8.

La máscara se construye en `u16`, de modo que desplazar por ocho es válido. Tras comprobar dominio, diagonal y simetría, exigir que cada par relacionado tenga filas iguales verifica transitividad en este dominio. Las clases resultantes son no vacías y disjuntas; el cálculo conserva la LUT Q16. Clique n = 8 da `(0,1)` e identidad n = 8 da `(196608,8)`.

Las [regresiones Rust](../../00_ABZU_KERNEL/crates/babylon60-kernel/tests/semantic_entropy_regressions.rs) comparan las 5295 particiones de n = 1..8 con una referencia numérica independiente y permutaciones seleccionadas. También contrastan las 65536 relaciones de n = 4 con la definición triple de equivalencia. Este barrido es exhaustivo en esos dominios, no en todas las relaciones de n = 8. Los cuatro casos nominales se conservan.

La [regresión de alineación Lean](../../tests/test_semantic_entropy_lean_alignment.py) fallaba con los cuatro umbrales y dos códigos originales; aquella campaña comprobó doce teoremas sin axiomas añadidos, incluidos los cinco originales y siete casos de alineación/borde. No demuestra factualidad de la señal externa ni equivalencia de la validación de matrices entre lenguajes. La [evidencia de esa reparación](evidence/algorithm-repairs-20261026.json) conserva sus fuentes/resultados históricos; §8 identifica la versión siguiente.

## 8. Resultado del solver explícito y regresiones

`evaluate(adj_matrix, n, outcome: SolverOutcome)` sustituye la API booleana, sin wrapper compatible ni conversión desde `bool`. Los llamadores deben preservar `Sat`, `Unsat`, `Unknown` y `Error(error)`, y tratar `SolverUnknown`/`SolverFailure` como rechazos distintos. Una llamada con el argumento `true` deja de compilar; el doctest `compile_fail` controla ese contrato. Los cuatro casos nominales, las regresiones de dominio y el test sintético se migran al tipo nuevo.

Las [regresiones de resultados](../../00_ABZU_KERNEL/crates/babylon60-kernel/tests/semantic_solver_outcomes.rs) recorren las 5295 particiones de n = 1..8 con los siete valores del tipo (SAT, UNSAT, UNKNOWN y cuatro errores). Comprueban que solo SAT admite, que los errores conservan su causa y que UNKNOWN no se convierte en UNSAT. Entradas inválidas con cualquiera de esos resultados conservan `InvalidInput`. Se mantienen la LUT, τ y los cuatro resultados anteriores para entradas válidas con SAT/UNSAT.

La prueba Lean comprueba además UNKNOWN y cada error en H = 0, τ, τ + 1 y 196608; sus pruebas universales no dependen de limitar H a esos valores. La [evidencia de estados del solver](evidence/solver-outcomes-20261026.json) y la [auditoría §6](AUDIT_SCIENTIFIC_GUARANTEES_2026.md#6-unknown-y-errores-del-solver--2026-10-26) registran aquella versión. Son garantías de clasificación de datos suministrados. Un llamador todavía puede mentir suministrando `Sat`; §9 añade un flujo concreto con solver, sin convertirlo en garantía universal de procedencia o factualidad.

## 9. Adaptador Z3 y consumo vinculado

El [adaptador host](../../00_ABZU_KERNEL/crates/babylon60-compiler/src/semantic_solver.rs) prepara una `EntropyQuery` inmutable, valida la matriz y restringe los comandos SMT-LIB. Vincula por BLAKE3 petición, matriz/n, entrada exacta y política, con longitudes explícitas. La política incluye límites y rutas locales. `solve` ejecuta un proceso Z3 nuevo por consulta y conserva UNKNOWN con su razón, o un error tipado; `receipt.evaluate(&expected_query)` rechaza cualquier identidad/digest distinto antes de clasificar. Los campos privados impiden construir o reetiquetar un recibo desde consumidores Rust seguros; no son autenticación criptográfica.

El flujo recomendado usa `receipt.evaluate`, no extraer el enum y reenviarlo al gate puro. Debe configurarse una ruta absoluta a un Z3 confiable y usar identificadores frescos. Una ruta no autentica el binario; mismo identificador y entrada siguen representando la misma consulta y no ofrecen antirreplay persistente. La matriz y la fórmula se asocian por declaración del llamador, sin demostrar equivalencia semántica.

Las [regresiones de integración](../../00_ABZU_KERNEL/crates/babylon60-compiler/tests/semantic_solver_adapter.rs) usan Z3 real para SAT/UNSAT/UNKNOWN y pruebas de cruce de consultas; los procesos de error simulados se identifican por separado. Se conserva el núcleo `no_std`, sin nuevas dependencias ni cambios en el modelo Lean. Este último sigue modelando resúmenes, no proceso, hash, parser o recibo. [Auditoría §7 y límites](AUDIT_SCIENTIFIC_GUARANTEES_2026.md#7-adaptador-real-y-vinculación-de-consultas--2026-10-26), [evidencia de esta versión](evidence/solver-adapter-20261026.json).
