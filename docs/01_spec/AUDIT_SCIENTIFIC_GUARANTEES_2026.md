---
title: Auditoría científica de garantías técnicas y evidencia
status: Auditoria-acotada-con-contraejemplos
version: 1.3.0
---

# Garantías técnicas: qué se demuestra y qué queda pendiente

Fecha: 2026-10-26. Esta ampliación revisa siete especificaciones de `docs/01_spec`, tres declaraciones seleccionadas de `CLAIMS.toml`, la presentación pública y la página de proof-carrying execution. Continúa la [auditoría de teoría](../06_theory/AUDIT_SCIENTIFIC_STATUS_2026.md) y la [de fuentes Lean](../06_theory/AUDIT_LEAN_SCOPE_2026.md). No certifica todo BABYLON-60 ni revalida todas sus campañas históricas.

> Seguimiento de reparación: los apartados 1–4 registran la auditoría inicial y sus fuentes anteriores. El apartado 5 documenta la primera reparación de aritmética y grafos; el 6, la API con UNKNOWN/error explícitos. El apartado 7 registra el adaptador Z3 real y la vinculación de resultados a consultas. Cada JSON conserva sus hashes y resultados históricos; no se reescribe como si correspondiera a la versión siguiente.

## 1. Criterio y alcance

Se distinguen resultado matemático condicional, propiedad de un modelo formal, observación finita, inspección estática, requisito normativo, hipótesis y metáfora. **NO_VERIFICADO no significa falso**. Una implicación refutada por un contraejemplo no invalida las propiedades más débiles que sí se demostraron.

La auditoría inicial conservó código y modelos Lean y corrigió la interpretación de sus garantías. Los apartados 5 y 6 registran reparaciones posteriores de código con evidencia propia. Se preservan dependencias, lockfiles y JSON históricos; los requisitos de rechazo, autoridad y persistencia siguen vigentes.

El grafo `babylon-60` se actualizó antes de la inspección. La cobertura parcial de Lean y una arista de llamada que no correspondía al uso literal de la fuente se trataron como límites del índice; las conclusiones se apoyan en la fuente inspeccionada, no en una inferencia de ausencia desde el grafo.

## 2. Seis postulados auditados

| ID | Garantía retirada o acotada | Estatus y evidencia |
| --- | --- | --- |
| SG-1 | SAT o el constructor `Verified` demuestran verdad factual y ausencia de alucinaciones | Implicación general REFUTADA; el modelo prueba una condición sobre el resultado suministrado, no el hecho externo. Defectos de dominio reparados en §5; UNKNOWN/error explícitos en §6. |
| SG-2 | Igualdad 1-WL/grados certifica isomorfismo; el hash es independiente del orden | REFUTADO en dos funciones concretas mediante contraejemplos aislados. El uso como filtro requiere condiciones adicionales. |
| SG-3 | Estilo de nombres reduce BPE/caché/compilación y permite búsquedas O(1) | NO_VERIFICADO: se retiran cifras sin tokenizer, corpus, método y benchmark. Se conservan convenciones de legibilidad. |
| SG-4 | Pruebas Lean, layout 64 B o ley de Little garantizan comportamiento físico y deadlines | Se conservan paridad y cota del autómata, tamaño/alineación y heurística de admisión. La extensión a payload atómico, caché o latencia real no está demostrada. |
| SG-5 | Hash, firma, WAL, fecha Git o loopback bastan para integridad histórica, autoría, exactly-once y cero fugas | Garantías universales retiradas. Mecanismos condicionales y controles requeridos separados; inspección de código sin nueva campaña de runtime. |
| SG-6 | Sello «Verified», fórmula normativa o receta de tests equivalen a evidencia actual y perfil criptográfico único | Certificación genérica retirada. Declaraciones históricas, formatos versionados y resultados efectivamente observados se separan. |

### SG-1. Dispersión semántica y satisfacibilidad

En la auditoría inicial, la [especificación corregida](spec_semantic_entropy_dual_firewall.md) distinguía la entropía empírica de clases y el Bool externo recibido por el módulo; §6 registra su sustitución posterior por estados tipados. SAT describe satisfacibilidad de las restricciones; para una consecuencia lógica se necesita la relación entre supuestos y conclusión, y para un hecho externo, evidencia de su correspondencia. [SMT-LIB 2.7 §4.2.5](https://smt-lib.org/papers/smt-lib-reference-v2.7-r2025-07-07.pdf).

Se compila una copia intacta del demo Lean y se añaden dos controles: `Verified ↔ isZ3Sat = true`, y un registro Verified junto a una proposición externa falsa. Los cinco teoremas originales no dependen de axiomas; la equivalencia añadida usa `propext` y el segundo control no añade axiomas. Esto delimita el modelo, sin crear una prueba de conocimiento genuino.

El estimador válido satisface `0 ≤ H ≤ log₂ K ≤ log₂ n`; para ocho clases puede llegar a 3 bits, es decir 196608 en escala Q16. La LUT inspeccionada coincide numéricamente con el redondeo declarado: no se la etiqueta como tabla errónea. La partición y el dominio sí fallan en los probes de la fuente Rust intacta:

- Con n = 8, el desplazamiento de `u8` hace panic con overflow checks; el probe optimizado sin checks devuelve una máscara incorrecta. Son observaciones de esas compilaciones, no de todo target.
- Con n = 0 o 9 y señal externa true puede devolverse `VerifiedGenuine`.
- La relación simétrica no transitiva de filas `011,111,110` cuenta clases superpuestas de tamaños 2 + 2 para tres muestras.

La fuente Lean y Rust también difieren en umbrales y códigos. El retorno de un enum no acredita aborto, persistencia o cierre de una frontera. Las promesas de 1,92 ns y disipación nula quedan NO_VERIFICADAS. El resultado estadístico de [Farquhar et al., Nature 2024](https://doi.org/10.1038/s41586-024-07421-0) no es una garantía factual universal ni valida este prototipo.

### SG-2. 1-WL, canonicidad y Merkle

La [especificación de grafos](spec_graph_canonical.md) separa serialización determinista de canonización por isomorfismo. 1-WL es un filtro incompleto; igualdad de firmas deja un par indeterminado. Sus límites son parte de la literatura sobre [color refinement, Arvind et al.](https://arxiv.org/abs/1502.01255), no un defecto particular de una función hash.

Se extraen únicamente funciones sin ejecutar los módulos completos. El demo `verify_isomorphism` acepta dos DAG de ocho nodos y ocho aristas; uno tiene una componente débil y el otro dos. Sus hashes WL coinciden. La diferencia de conectividad demuestra que no son isomorfos. Otro método `compute_1wl_hash` cambia su digest al permutar el orden de los nodos de un mismo camino a → b → c. Estos casos refutan las garantías fuertes de esas funciones; no describen todas las implementaciones del proyecto.

Se corrigen además costes de rondas, ordenaciones y bytes: comparar dos digests fijos es distinto de construirlos. Un digest plano del archivo tampoco ofrece las pruebas de inclusión de un árbol con formato definido; véase [RFC 9162 §2.1.1](https://www.rfc-editor.org/rfc/rfc9162.html#section-2.1.1). No se ejecuta ni se certifica un anclaje Bitcoin por localizar un script dry-run.

### SG-3. Nombres y costes

La [ontología de nombrado](spec_exergy_ontology.md) conserva intención de claridad, efectos y unidades. Se retiran los conteos 6/3 tokens, el efecto físico atribuido al límite de 24 caracteres y la búsqueda O(1) deducida de prefijos. [BPE, Sennrich et al. 2016](https://aclanthology.org/P16-1162/) depende del vocabulario y preprocesamiento; no demuestra una superioridad universal de snake_case. La eficacia de cada convención queda como hipótesis que exige medición comparable.

### SG-4. Modelo formal y límites de recursos

En [CLAIMS.toml](../../CLAIMS.toml) se acotan tres entradas conservando sus identificadores y obligaciones de release:

- `inv_01_manifest_layout`: el test inspeccionado comprueba tamaño, alineación y offsets. No mide coherencia, tráfico RFO ni topología de caché del target; la etiqueta «Zero-Split Coherence» no se deduce de ese test.
- `lean4_formal_trace`: `no_torn_reads_universal` tiene conclusión `TraceReadsEven`, sobre secuencias declaradas de trazas aceptadas. AX0 limita `countDispatches` a uno desde Proposed. Los enunciados no contienen payload, atomics Rust o una prueba de refinamiento del ejecutable. Se fija la toolchain del comando de reproducción.
- `FL_007_admission_bounded_liveness`: el código compara profundidad y una estimación configurada multiplicada por `current as u32`, con saturación de Duration; no es un producto matemático irrestricto sobre usize. Los dos tests citados comprueban capacidad 3, rechazo del cuarto slot, readmisión tras release y rechazo por presupuesto estimado; no observan tiempos de espera reales.

La ley de Little `L = λW` relaciona promedios bajo hipótesis, no establece un deadline individual. Una pausa arbitraria del servicio sigue siendo compatible con una estimación pequeña y con el chequeo de admisión: la garantía temporal necesita supuestos adicionales de servicio y planificación. [Little, Operations Research 1961](https://doi.org/10.1287/opre.9.3.383). No se comunica un fallo físico de cola ni una medición de latencia en esta revisión.

### SG-5. Seguridad condicionada a fronteras y referencias

El [modelo de seguridad](spec_security_model.md) y la [arquitectura](spec_architecture.md) pasan de garantías absolutas a condiciones verificables. Los hashes pueden comprobar coherencia respecto a un compromiso confiable; campos de taint/autor son declaraciones hasta que una frontera los autentique. Un checkpoint conservado aparte es necesario para evaluar sustitución coherente del historial. UUID/UNIQUE del ledger no establecen ejecución exactamente una vez de un efecto externo.

Loopback define direcciones locales, no controles de egress de todo el servicio. [RFC 1122 §3.2.1.3](https://www.rfc-editor.org/rfc/rfc1122.html#section-3.2.1.3). WAL y FULL mantienen su obligación, con los supuestos del motor/almacenamiento; recuperación transaccional no equivale a replay de intents. [SQLite WAL](https://www.sqlite.org/wal.html). Las fechas configurables de Git no constituyen un testigo temporal independiente. [Git commit-tree](https://git-scm.com/docs/git-commit-tree#_date_formats).

La API documentada de `verify_chain` se corrige al método asíncrono real y se retiran números prefijados presentados como salida observada. No se han ejecutado aquí las campañas de ledger, confinamiento, pérdida de alimentación o presencia humana.

### SG-6. Declaración, perfiles y evidencia

Se retiran los sellos de certificación genérica de las siete especificaciones y del índice maestro. En [invariantes](spec_invariants.md), las obligaciones normativas no se presentan como teoremas del kernel. En CLAIMS se precisa que `root_axiom` es un requisito; `status` y `evidence_suite` por sí solos no son recibos de una ejecución nueva. Los estados no revisados permanecen como declaraciones históricas, sin ascenderlos a evidencia actual.

El [perfil criptográfico](spec_cryptographic_profile.md) distingue BLAKE3, SHA-256 y SHA3-256 legacy, y JSON de CBOR. Se corrige la descripción de los prefijos BLAKE3 observados: son las cadenas completas `B60-LEAF-v1\0`, `B60-NODE-v1\0` y `B60-ROOT-v1\0`, con cardinalidad y etiqueta `b3:`, no bytes únicos `0x00`/`0x01`. No se migran formatos mediante prosa.

CBOR necesita un perfil de codificación explícito y comprobado, no solo la palabra «canónico». [RFC 8949 §4.2](https://www.rfc-editor.org/rfc/rfc8949.html#section-4.2). Una firma válida tampoco determina por sí sola autoridad de la identidad firmante; esas comprobaciones corresponden a la aplicación. [RFC 9052 §4.4](https://www.rfc-editor.org/rfc/rfc9052.html#section-4.4).

## 3. Evidencia y reproducción

El [registro estructurado](evidence/scientific-guarantees-20261026.json) conserva entradas exactas de los contraejemplos, salidas, comandos, dependencias de axiomas y hashes de las fuentes inspeccionadas. Copias iniciales y comprobaciones completas quedan en `.audit/scientific-guarantees-20261026/`, con subdirectorios `semantic`, `graph` y `security`. Se conservan también los fallos iniciales de scripts de auditoría: se distinguen de los defectos del componente.

Las comprobaciones numéricas/Rust incluyen únicamente la fuente de aritmética en probes aislados. Se captura el panic deliberado como dato; que el recolector termine 0 no significa que el caso n = 8 haya pasado. Los contraejemplos de grafos extraen funciones para evitar efectos del módulo completo. Ninguno de esos procedimientos mide energía o rendimiento productivo.

La aceptación documental requiere enlaces/anclas, TOML válido y listado declarativo compatible, tests existentes de contratos públicos, preservación de código/lockfiles/evidencia histórica y gates de semántica, presupuesto y topología del workspace. Estas comprobaciones no convierten hipótesis en teoremas ni reemiten recibos de release. Al cambiar CLAIMS, cualquier evidencia de release vinculada al manifiesto anterior sigue perteneciendo a aquella versión; no se regenera ni se firma un paquete nuevo en esta revisión.

Resultado local: pasan cuatro tests de contratos públicos, la compilación de BabylonTrace y AX0 con Lean 4.34.0-rc2, los siete teoremas inspeccionados del fixture semántico, la comparación numérica de LUT, los probes aislados y las aserciones de ambos contraejemplos de grafos. Los probes confirman fallos del componente; su salida 0 solo indica que se recogió la observación esperada. Pasan 375 enlaces locales, la cobertura de los 14 Markdown de especificaciones y los 31 de teoría en los índices aplicables, diff y los tres gates documentales. Se comprueba la preservación de 44 artefactos, incluidos fuentes, lockfiles y JSON históricos. Se corrigió además un enlace previo del índice a STATUS inexistente. No se inspeccionan reglas globales ni telemetría de ghost listeners.

## 4. Pendiente y fuera de alcance

En la auditoría inicial quedaron pendientes los límites de entropía y las dos funciones de grafos refutadas; el apartado 5 registra su reparación. El apartado 6 trata UNKNOWN/error en el clasificador, y el 7 añade ejecución real de Z3 y vinculación local de consulta/resultado. Siguen pendientes autenticación del ejecutable, integración en consumidores productivos, correspondencia completa Rust–Lean, calibración factual, benchmarks identificados y evaluación de todas las integraciones de autoridad/egress/durabilidad.

Esta ampliación no revisa las demás especificaciones como si hubieran pasado, ni certifica todos los estados de CLAIMS, el runtime o la configuración global. No se despliega, publica, ejecuta efecto protegido ni modifica dependencias. Los índices describen cobertura y estatus, sin «100 % synchronized» como sustituto de una comprobación.

## 5. Reparación de algoritmos y regresiones — 2026-10-26

### Cambios y alcance de las API

El [núcleo de entropía](../../00_ABZU_KERNEL/crates/babylon60-kernel/src/semantic_entropy.rs) corrige la máscara n = 8 y valida tamaño, bits fuera de dominio, reflexividad, simetría y transitividad antes de formar clases. `compute_quotient_entropy` devuelve `Result<(u32,u8), SemanticEntropyInputError>`; `evaluate` conserva argumentos y añade `InvalidInput { error }`, que no puede confundirse con una variante positiva bajo ninguno de los dos valores del Bool. Se mantienen LUT, umbral 55706 y resultados válidos. Los consumidores con matches exhaustivos deben manejar la nueva variante.

El [comprobador de grafos](../../scripts/c5_demos/poc_graph_isomorphism_wl.py) usa colores simultáneos dirigidos con multiplicidad y bucles como filtro, y exige una biyección exacta para aceptar. La búsqueda iterativa tiene presupuesto de extensiones candidatas; agotarlo genera `IsomorphismSearchLimitExceeded`, nunca una falsa prueba de no isomorfismo. La construcción de candidatos y el preprocesamiento no quedan acotados por ese presupuesto. El [segundo método](../../scripts/c5_isomorphisms/c5_ultimate_causal_determinant.py) conserva el dominio no dirigido y usa una ronda simultánea con entradas validadas.

Los hashes cambian de perfil: `WL1_V2:` para el filtro dirigido y `b60-wl-undirected-v2` dentro del hash del segundo método. La salida de este último mantiene 64 hexadecimales; esa longitud no identifica su versión. Solo son comparables digests con el mismo perfil y parámetros. La reparación no migra compromisos históricos ni ejecuta el demo que escribe SQLite.

El [demo Lean](../../scripts/c5_demos/SemanticEntropyApoptosis.lean) alinea el umbral y los códigos completos con Rust, conserva los nombres de sus cinco teoremas y retira las interpretaciones de verdad/efecto físico de sus comentarios. El modelo sigue recibiendo un resumen: no valida la matriz, no implementa un solver ni modela el nuevo error de entrada de Rust.

### Regresiones que detectaban los fallos anteriores

- Siete casos Rust compilaban y fallaban por comportamiento con la fuente original: n = 8, tamaños inválidos, diagonal ausente, asimetría, no transitividad y bits fuera de filas/columnas declaradas. No se cuenta un error de compilación por cambiar una API como evidencia de esa reproducción.
- Los dos controles originales de grafos demostraban el falso positivo de los DAG y varios digests para las seis permutaciones de un camino. Los nuevos tests exigen rechazo exacto e invariancia; añaden prisma triangular/K₃,₃ para que una comprobación de componentes no baste para ocultar el defecto.
- La regresión Lean compilaba la fuente real y fallaba en seis proposiciones: cuatro umbrales y dos códigos distintos de Rust. Tras alinear las constantes, comprueba siete casos de alineación/borde y los cinco teoremas originales mediante guards de axiomas.

### Evidencia de la versión reparada

Las [once regresiones Rust](../../00_ABZU_KERNEL/crates/babylon60-kernel/tests/semantic_entropy_regressions.rs) incluyen las 5295 particiones de n = 1..8, referencia numérica independiente y permutaciones seleccionadas; las 65536 relaciones de n = 4 se contrastan con la definición de equivalencia. Ese segundo barrido no cubre todas las relaciones de n = 8. Los cuatro tests nominales siguen comprobándose.

Los [tests de grafos](../../tests/test_graph_isomorphism_regressions.py) comparan 2080 pares del corpus completo de grafos dirigidos simples de tres nodos y 105 pares de un corpus de multigrafos de cuatro nodos con un oráculo por permutaciones. Cubren dirección, multiplicidad, bucles, inputs inválidos, renombrado y agotamiento de presupuesto. El test anterior de un stub local se sustituye por una llamada a la API real. La [prueba Lean](../../tests/test_semantic_entropy_lean_alignment.py) requiere ejecución real en la receta de aceptación y verifica doce teoremas sin axiomas añadidos.

El [registro de reparación](evidence/algorithm-repairs-20261026.json) conserva comandos, resultados, controles anteriores y hashes de las fuentes actuales. Los detalles locales están en `.audit/algorithm-repairs-20261026/`. Los JSON históricos y lockfiles se preservan. Las recetas actuales son:

```sh
cargo check -q --locked -p babylon60-kernel
cargo test --locked -p babylon60-kernel --lib semantic_entropy::tests
cargo test --locked -p babylon60-kernel --test semantic_entropy_regressions
cargo test --locked -p babylon60-kernel --release --test semantic_entropy_regressions
BABYLON_REQUIRE_LEAN=1 uv run --locked pytest tests/test_graph_isomorphism_regressions.py tests/test_inv_c5_28_falsification.py tests/test_semantic_entropy_lean_alignment.py tests/test_audit_public_claims.py -q
```

Estos resultados delimitan la validación de aritmética/dominio, el chequeo exacto implementado y los casos de alineación. No convierten el booleano externo de aquella versión en verdad, no prueban refinamiento universal Rust–Lean y no aportan rendimiento, energía ni seguridad de producción. UNKNOWN/error quedaron fuera de aquella reparación y se abordan en §6; la calibración factual sigue pendiente.

Aceptación de la reparación: pasan `cargo check --locked`, cuatro tests Rust nominales, once regresiones Rust en debug y release, y 49 tests Python/Lean de la receta anterior: 64 tests distintos, con once repetidos en release. Pasan Ruff, formato Rust, ejecución del demo de grafos pequeño, 389 enlaces y los gates documentales del workspace. El test de estrés se compila sin ejecutarlo; no se interpreta como benchmark. Lockfiles, manifiestos y JSON históricos permanecen intactos; se omiten reglas globales y telemetría de ghost listeners.

## 6. UNKNOWN y errores del solver — 2026-10-26

### Contrato de rechazo y compatibilidad

El [módulo Rust](../../00_ABZU_KERNEL/crates/babylon60-kernel/src/semantic_entropy.rs) sustituye el argumento booleano por `SolverOutcome::{Sat, Unsat, Unknown, Error(SolverError)}`. `SolverError` distingue `Timeout`, `Transport`, `Protocol` y `Execution`. Una entrada válida con `Unknown` devuelve `SolverUnknown`; con `Error(error)`, `SolverFailure { error }`. Ninguna de esas variantes es `VerifiedGenuine`/`VerifiedPolysemy`, ni se reutilizan los códigos de UNSAT para un resultado inconcluso o un fallo operativo. La matriz se valida primero: `InvalidInput` conserva precedencia para cualquiera de los siete valores del tipo.

Los cuatro resultados válidos de SAT/UNSAT conservan la LUT, el umbral 55706 y los códigos anteriores. Se migran los llamadores locales y el test sintético; no se añade wrapper booleano ni conversión desde `bool`. **La API es incompatible con llamadas que pasaban `true`/`false` y con matches exhaustivos que omitan las variantes nuevas.** Los productores deben conservar el estado lógico/operativo real; convertir UNKNOWN o error a `Sat` violaría el contrato, aunque un llamador puede construir ese valor y el tipo por sí solo no autentica su origen.

En aquella campaña, la búsqueda de llamadores usó el grafo `babylon-60` actualizado y la comprobación literal de imports/firmas. Se descartaron aristas espurias hacia otro `evaluate` de cortex-guard. Los usos reales encontrados eran pruebas del clasificador; el adaptador se incorpora después en §7.

### Regresiones y modelo formal

El doctest `compile_fail` conserva una llamada a la API con `true`. Antes del cambio tipado fallaba el test porque esa llamada compilaba; después exige que sea rechazada por el compilador. Esa es una reproducción del contrato ausente, sin contar errores por tipos todavía inexistentes como fallos de comportamiento.

Las [regresiones nuevas](../../00_ABZU_KERNEL/crates/babylon60-kernel/tests/semantic_solver_outcomes.rs) recorren 5295 particiones válidas con los siete valores del tipo: 37065 combinaciones. Comprueban admisión solo para SAT, conservación de la causa del error y separación de UNKNOWN/UNSAT; añaden casos inválidos bajo todos los resultados y repetición determinista de extremos. Las once regresiones de aritmética/dominio se conservan y migran a la nueva API. El barrido de 65536 relaciones de n = 4 sigue verificando el dominio de matrices, sin pretender cubrir todo `u64`.

El [modelo Lean](../../scripts/c5_demos/SemanticEntropyApoptosis.lean) sustituye el Bool por los mismos estados tipados. Prueba `Verified ↔ solverOutcome = Sat` y rechazo universal de UNKNOWN y de cualquier error para sus resúmenes. La [regresión de alineación](../../tests/test_semantic_entropy_lean_alignment.py) compila la fuente real con la toolchain fijada y exige dependencias de axiomas vacías en diez teoremas del modelo y 27 casos finitos: 37 guards. Estos casos incluyen H = 0, τ, τ + 1 y 196608 para UNKNOWN y cada error; las pruebas universales no se restringen a esos valores.

Los primeros intentos de escribir la prueba Lean nueva fallaron por elaboración y después por una obsolescencia tratada como error con `warningAsError`. Los guards detectaron también `sorryAx` producido por los errores del primer intento. Se conservan como fallos de implementación, separados del control rojo sobre la API anterior; no fueron pruebas aceptadas ni evidencia sobre el solver. La versión corregida compila sin diagnósticos y pasa los guards sin axiomas. Context7 no pudo consultarse por cuota agotada; se comprobaron los nombres vigentes en `Init/Core.lean` de la toolchain instalada.

### Evidencia y límites

El [registro de esta ampliación](evidence/solver-outcomes-20261026.json) identifica comandos, fallos previos, resultados posteriores y hashes; el detalle local queda en `.audit/solver-outcomes-20261026/`. Los JSON anteriores se conservan byte por byte y sus hashes de fuentes siguen siendo históricos. La receta de reproducción incluye:

```sh
cargo check -q --locked -p babylon60-kernel
cargo test --locked -p babylon60-kernel --lib semantic_entropy::tests
cargo test --locked -p babylon60-kernel --test semantic_entropy_regressions --test semantic_solver_outcomes
cargo test --locked -p babylon60-kernel --release --test semantic_entropy_regressions --test semantic_solver_outcomes
cargo test --locked -p babylon60-kernel --doc semantic_entropy
BABYLON_REQUIRE_LEAN=1 uv run --locked pytest tests/test_semantic_entropy_lean_alignment.py tests/test_audit_public_claims.py -q
```

**Estatus científico de esa versión:** rechazo tipado con evidencia de regresión y propiedad universal del modelo de resúmenes. No probó refinamiento completo del cálculo Rust en Lean, corrección/procedencia de un solver real, correspondencia con hechos externos ni ejecución de un efecto de bloqueo productivo. El retorno de un enum sigue siendo una clasificación pura. El test de estrés se compiló sin medirlo; no aportó latencia, energía o factualidad.

Aceptación de esta ampliación: pasan `cargo check --locked`, 20 tests Rust en debug y release (cuatro nominales, once de dominio/aritmética y cinco de resultados del solver), un doctest de rechazo booleano y cinco tests Python/Lean: 26 tests distintos y 20 repeticiones en release. Pasan los 37 guards Lean, Ruff, formato Rust, 397 enlaces locales, cobertura de índices (14 especificaciones y 31 documentos de teoría), diff y los tres gates documentales del workspace. El estrés solo se compila en ambos perfiles. Se comprueban 16 archivos preservados, incluidos fuentes de grafos, manifiestos, lockfiles y JSON históricos; no se inspeccionan reglas globales ni telemetría de ghost listeners.

## 7. Adaptador real y vinculación de consultas — 2026-10-26

El [adaptador Z3](../../00_ABZU_KERNEL/crates/babylon60-compiler/src/semantic_solver.rs) reside en la crate de compilación, con `std`; el núcleo conserva `no_std` y solo añade `solver_query_digest`. No cambia dependencias. Cada consulta validada conserva en campos privados la petición, matriz, n, entrada SMT-LIB completa y política. BLAKE3, con dominio `B60-SEMANTIC-SOLVER-QUERY-v1\0`, enteros little-endian y campos variables precedidos por su longitud, vincula esos datos. La política incluye versión de formato, límites y bytes de las rutas del ejecutable y directorio temporal. Es una identidad local de consulta, no una firma ni una autenticación del binario.

`adapter.solve(&query)` ejecuta un proceso nuevo con ruta absoluta, sin shell ni entorno heredado. El recibo privado conserva identidad, digest, resultado tipado, salida/diagnóstico acotados y razón de UNKNOWN. `receipt.evaluate(&expected_query)` compara petición y digest antes de llamar al núcleo; una consulta diferente devuelve `QueryMismatch`. Ejecutar con otro adaptador o política devuelve error de protocolo. El flujo completo probado usa ese método; extraer `.outcome()` y pasarlo manualmente al gate puro pierde la comprobación y no está cubierto por esta garantía.

El perfil de entrada admite declaraciones, definiciones, `set-logic` y aserciones, con al menos una aserción. Rechaza comandos de control/salida (`check-sat`, `echo`, `reset`, `exit`, `include`, `set-option`, consultas de modelo) y secuencias mal formadas. El adaptador añade sus opciones, un único `check-sat` y `get-info :reason-unknown`. No es un parser completo de SMT-LIB: fórmulas semánticamente inválidas se dejan rechazar por Z3. La salida debe contener exactamente SAT/UNSAT/UNKNOWN y un único campo de razón; errores, respuestas adicionales, stderr, truncamiento o exceso de salida impiden admitir SAT.

UNKNOWN conserva su razón textual y no se deduce UNSAT ni timeout a partir de ella. Un límite de tiempo observado por el supervisor devuelve `Error(Timeout)`; fallo de lanzamiento/exit no cero, `Execution`; fallo de ficheros/espera, `Transport`; respuesta/política inválida, `Protocol`. Todos esos resultados quedan vinculados a la consulta y se clasifican como rechazo. Los [parámetros oficiales de Z3](https://microsoft.github.io/z3guide/programming/Parameters/) distinguen `timeout` de `rlimit`; aquí se conserva además el plazo del supervisor.

### Evidencia finita y controles negativos

Las [regresiones](../../00_ABZU_KERNEL/crates/babylon60-compiler/tests/semantic_solver_adapter.rs) ejercitan Z3 real **4.15.4**, cuya huella de binario se recoge en la [evidencia](evidence/solver-adapter-20261026.json). SAT y UNSAT llegan a las cuatro variantes históricas. Con `rlimit = 1`, `(declare-const x Int) (assert (> x 0))` devuelve UNKNOWN con razón `max. resource limit exceeded`, observado repetidamente en esa versión. No se presenta como resultado estable de toda versión futura.

Se comprueban cruces de petición, fórmulas distintas con igual SAT, bytes distintos, matriz/tamaño y política —incluidos nanosegundos—, así como aislamiento entre consultas SAT/UNSAT consecutivas. Fixtures negativos de procesos, identificados como simulaciones aisladas, producen salida ambigua, SAT seguido de error, stderr, exit no cero, ausencia de ejecutable, fallo de transporte, exceso de salida y un proceso que no lee la entrada. Estos fixtures prueban el rechazo del adaptador, no comportamiento real de Z3 en cada error. Los resultados reales y simulados se registran por separado.

Dos mutantes aislados de la fuente nueva compilan y fallan por aserción: eliminar la comprobación de vinculación permite consumir un recibo de otra consulta; forzar SAT en el parser admite una salida con dos respuestas. Los tests detectan ambos. Estos controles comprueban sensibilidad de las regresiones, no reproducen fallos de un adaptador anterior inexistente. Las fuentes activas y lockfiles se conservan durante la mutación.

### Límites que siguen vigentes

La asociación matriz/fórmula es suministrada por el llamador; no se prueba que la fórmula exprese el significado de las muestras ni una proposición factual. El recibo es un objeto local inmutable en Rust seguro, sin firma, persistencia ni resistencia frente a código comprometido en el mismo proceso. Se requieren identificadores frescos para consultas nuevas; reutilizar la misma identidad y entrada no constituye un token de un solo uso. La ruta del solver no autentica su contenido ni evita su sustitución. Los digests incluyen rutas locales y no son compromisos portables entre plataformas.

El plazo supervisa el proceso después de `spawn`; no acota de forma dura la preparación de ficheros, `spawn`, planificación, `kill` o `wait`. Las lecturas usan un centinela de un byte sobre el límite; el control por sondeo puede observar un exceso en disco después de que ya ocurra. La terminación y limpieza son intentos sobre el hijo y sus temporales, sin sandbox de descendientes, prueba de borrado físico ni garantía de limpieza tras un crash. No se certifican tiempo real, consumo, factualidad, solver correcto para toda fórmula, refinamiento Lean de este adaptador ni un bloqueo productivo.

Receta dirigida, con Z3 instalado y su ruta absoluta en `BABYLON_Z3_BIN`:

```sh
cargo check -q --locked -p babylon60-kernel -p babylon60-compiler
cargo test --locked -p babylon60-compiler --test semantic_solver_adapter
cargo test --locked -p babylon60-compiler --release --test semantic_solver_adapter
```

Las comprobaciones del núcleo, Lean, índices y controles documentales se conservan en el registro nuevo, junto a comandos, hashes y resultados; los JSON anteriores permanecen byte por byte. No se despliega ni ejecuta un efecto protegido.

Aceptación dirigida: pasan 15 tests nuevos de adaptador y 20 del núcleo en debug y release, un doctest y cinco tests Python/Lean: 41 tests distintos, con 35 repeticiones en release, y 37 guards Lean sin axiomas. El primer chequeo de formato sobre `lib.rs` recorrió también módulos heredados y falló por diferencias de formato ajenas al cambio. Se conserva el fallo y se comprueban las cuatro fuentes afectadas sin recursión ni reordenación de módulos; pasan sin reformatear los otros archivos. Se validan 404 enlaces, cobertura de índices (14 especificaciones y 31 documentos de teoría), diff y los tres gates documentales. Quince artefactos seleccionados, incluidos manifiestos, lockfiles, Lean y JSON históricos, permanecen intactos. Se omiten reglas globales y telemetría de ghost listeners.
