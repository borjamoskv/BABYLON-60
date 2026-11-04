---
title: Auditoría de alcance científico de proof/lean
status: Compilacion-y-proposiciones-con-alcance-explicito
version: 1.3.0
---

# Auditoría de alcance científico de proof/lean

Fecha: 2026-10-25. Cobertura: las 23 fuentes `.lean` directamente contenidas en `proof/lean`, con 123 teoremas nombrados inventariados. Es una auditoría de enunciados, hipótesis, comentarios y reproducibilidad local; no certifica toda la implementación Rust ni el mundo físico.

> Actualización 2026-10-26: §8 corrige la clasificación de las trazas, documenta ProofWidgets y los mensajes corregidos; §9 corrige el harness Rust; §10 precisa la nomenclatura de verificación bajo demanda. Las cifras y fallos de §§1–7 corresponden a la observación inicial del 25. El límite del harness descrito en §8 corresponde al estado anterior a §9. Cada registro de evidencia describe las fuentes y salidas de su propia iteración.

## 1. Contrato y corrección aplicada

Se corrigen exclusivamente comentarios Lean y documentación. Las definiciones, tipos de teoremas, tácticas, identificadores, imports, datos de prueba y strings ejecutables se conservan. Un escáner con soporte de comentarios anidados y strings compara el código sin comentarios contra las copias previas; esto permite comprobar que la rectificación no «hace pasar» una proposición cambiándola.

Los nombres públicos históricos se conservan por compatibilidad, pero las cabeceras y docstrings distinguen identidad aritmética, hipótesis proyectada, estructura con obligaciones, ejemplo concreto, resultado universal del modelo y garantía extramodelo no demostrada. No se modifican dependencias, manifiesto Lake ni toolchain. Los cambios Markov/Kripke ajenos al inicio se dejan fuera de alcance. No hay despliegue, ejecución de binarios de producción ni medición de hardware.

## 2. Resultado de compilación y axiomas

La toolchain fijada `leanprover/lean4:v4.34.0-rc2` está instalada. En `proof/lean`, `lake --no-cache --wfail build` pasa para los targets por defecto. Ese build no incluye automáticamente todas las fuentes sueltas.

Se elaboraron además las 23 fuentes en un directorio de auditoría aislado, con imports locales en orden de dependencias y `#print axioms` añadido para cada teorema nombrado. **Veinte fuentes compilan y tres no**. No se reparan imports mediante instalación ni se reemplazan las dos proposiciones refutadas por conclusiones más débiles.

En las 20 fuentes compiladas se inspeccionan 121 teoremas nombrados: 62 no dependen de axiomas y 59 dependen de `propext` y/o `Quot.sound`. No se observaron `Classical.choice`, axiomas de aplicación ni `sorryAx` en ese conjunto compilado. No hay declaraciones explícitas `axiom` en las 23 fuentes inspeccionadas. Los dos teoremas de las fuentes refutadas quedan fuera de esa certificación; no se cuentan las dependencias de términos de error como pruebas válidas.

**Importante:** `#print axioms` no elimina hipótesis locales ni prueba que una estructura tenga instancia real. Una lista de dependencias vacía no implica correspondencia física, validez de datos o propiedad no expresada en el tipo.

El [inventario y resultado por teorema en JSON](evidence/lean-scope-20261025.json) conserva los nombres, imports, resultados y dependencias. Las líneas del inventario corresponden a las copias previas a las correcciones de comentarios; los identificadores permanecen iguales.

## 3. Cobertura por fuente

| Fuente | Teoremas nombrados | Resultado individual | Qué queda demostrado o pendiente |
| --- | ---: | --- | --- |
| [AX0.lean](../../proof/lean/AX0.lean) | 6 | COMPILA | Cota inductiva de dispatches en la FSM y trazas testigo. No modela nonce real, replay multiproceso o recuperación persistente. |
| [AcsEnvelope.lean](../../proof/lean/AcsEnvelope.lean) | 20 | COMPILA | Roundtrips, validez e inyectividad sobre codecs y dominios explícitos; no verificación de firmas o autorización. |
| [Babylon.lean](../../proof/lean/Babylon.lean) | 26 | COMPILA | Registros y aritmética: hipótesis proyectadas, identidades y propiedades del modelo. No prueba Fisher, Landauer, FFI real ni independencia física. |
| [BabylonAOTOracle.lean](../../proof/lean/BabylonAOTOracle.lean) | 0 | COMPILA | Parser binario y bucle IO. Chunk de 8 KiB no implica memoria total O(1), zero-copy o ausencia de asignaciones. |
| [BabylonAeonChain.lean](../../proof/lean/BabylonAeonChain.lean) | 5 | COMPILA | Cinco fragmentos concretos, 7.500 eventos literales en total. No prueba un millón de transacciones ni recursos del compilador. |
| [BabylonAeonStress.lean](../../proof/lean/BabylonAeonStress.lean) | 1 | COMPILA | Una traza de 1.500 eventos. Prueba de esa lista, no benchmark. |
| [BabylonAutoTrace.lean](../../proof/lean/BabylonAutoTrace.lean) | 1 | NO_COMPILA: decide refuta el enunciado | La igualdad de aceptación afirmada es falsa para la lista. Puede servir de caso negativo, no biblioteca compilada. |
| [BabylonOracle.lean](../../proof/lean/BabylonOracle.lean) | 0 | COMPILA | Parser CSV y step abstracto; mensajes de causalidad y volumen no son evidencia de ejecución externa. |
| [BabylonStressCorrupt.lean](../../proof/lean/BabylonStressCorrupt.lean) | 1 | NO_COMPILA: decide refuta el enunciado | Lista de 1.501 eventos con lectura impar final; decide rechaza la afirmación true. No se debilitó el teorema. |
| [BabylonStressTrace.lean](../../proof/lean/BabylonStressTrace.lean) | 1 | COMPILA | Aceptación de 6.000 eventos literales. No demuestra escalado o propiedad universal del hardware. |
| [BabylonTrace.lean](../../proof/lean/BabylonTrace.lean) | 10 | COMPILA | Propiedades universales de secuencias declaradas y predicados de registro. Sin modelo de payload, atomics o memoria Rust. |
| [C5Affine.lean](../../proof/lean/C5Affine.lean) | 1 | COMPILA | consume sobre constructores duplicables; no programa de gestión de memoria ni recurso lineal. |
| [C5PortHamiltonian.lean](../../proof/lean/C5PortHamiltonian.lean) | 3 | COMPILA | Identidad algebraica, un descenso concreto y tres ejemplos módulo 64. Hay contraejemplo a monotonía global con r=20. |
| [CanonicalEnvelope.lean](../../proof/lean/CanonicalEnvelope.lean) | 7 | COMPILA | Leyes genéricas bajo Codec.roundtrip y constructores con pruebas. Parser y dominios explícitos; no toda semántica CBOR o recursos. |
| [CanonicalHead.lean](../../proof/lean/CanonicalHead.lean) | 4 | COMPILA | Codificación/decodificación de cabeceras y enteros bajo cotas. No prueba de criptografía o permisos. |
| [Destiladora_838c463da193b48f.lean](../../proof/lean/Destiladora_838c463da193b48f.lean) | 7 | COMPILA | Paridad y preservación inductiva del predicado abstracto; prefijo literal no equivale a firma ni a correspondencia Rust probada. |
| [HolographicPoC.lean](../../proof/lean/HolographicPoC.lean) | 0 | NO_COMPILA: dependencia no disponible | Widget Html sin teoremas. Falta ProofWidgets en la ruta de imports disponible; no se instalaron dependencias. |
| [MolochLandauer.lean](../../proof/lean/MolochLandauer.lean) | 5 | COMPILA | Desigualdades sobre payoff Nat truncado y penalización definida; sin juego completo, pagos reales o termodinámica. |
| [NavierStokesBKM.lean](../../proof/lean/NavierStokesBKM.lean) | 5 | COMPILA | Clasificación de trazas por umbrales arbitrados, nilpotencia supuesta en campos y test de cero; no resultados PDE. |
| [NavierStokesOracle.lean](../../proof/lean/NavierStokesOracle.lean) | 0 | COMPILA | Parser y clasificador de flags. Los mensajes ejecutables de regularidad/singularidad exceden el alcance del modelo. |
| [NavierStokesSobolevKato.lean](../../proof/lean/NavierStokesSobolevKato.lean) | 8 | COMPILA | Comparaciones numéricas y conjunción de flags; sin espacios Sobolev, solución PDE, existencia Kato o regularidad del Milenio. |
| [NemesisWave4.lean](../../proof/lean/NemesisWave4.lean) | 6 | COMPILA | Seis evaluaciones concretas y FSM. No demuestra seguridad universal de fencing, WAL, sellos o despliegue del host. |
| [TicketEnvelope.lean](../../proof/lean/TicketEnvelope.lean) | 6 | COMPILA | Roundtrip e inyectividad de payloads; firma externa opaca y shape limitada. Sin autenticidad, frescura o permiso real. |

## 4. Hallazgos sustantivos

### Proposiciones correctas con interpretación demasiado fuerte

En `Babylon.lean`, `theorem_chentsov_markov_monotonicity` devuelve `h_contractive`; `lemma_monotonic_entropy_growth` aplica `h_growth`; las propiedades de soporte se extraen de campos exigidos a una estructura. Son deducciones condicionales, no pruebas de Chentsov, una ley física o ausencia de confabulación.

`theorem_fisher_pythagorean_divergence` reduce una suma cuando `cross_term = 0`; no define distribuciones o KL. `theorem_mmr_logarithmic_bound` prueba una función definida como log2(n)+1 menor o igual a la misma expresión; no cuenta picos MMR ni prueba longitud de un certificado real. XOR involutivo no es el teorema de Liouville; divisibilidad por 60 no prueba contractibilidad topológica.

`theorem_agent_finite_horizon` es una desigualdad de división Nat, válida también con divisor cero; no contiene traza ni hipótesis de coste positivo por paso. `theorem_ffi_semantic_isomorphism` compara dos funciones Lean, sin llamar C ni verificar un ABI. Los campos con valor 64 no son mediciones de layout/heap. El supuesto bypass de Landauer es un conjunto de igualdades del registro reconstruido.

### Vacuidad y falta de correspondencia

`theorem_concurrent_wave_independence` recibe simultáneamente `stage_u = stage_v` y `stage_u < stage_v`: esa conjunción es imposible. Su conclusión False es correcta, pero no aporta una instancia de concurrencia segura ni prueba ausencia de contención. La propiedad de SmallStep trata una relación con único sucesor por construcción, no todo el lenguaje B60.

En `NavierStokesBKM`, las composiciones nulas se piden como campos de `DiscreteChainComplex`. No se construye un complejo de malla concreto. `coexact_field_is_solenoidal` solo comprueba que cero sea cero; no cuantifica sobre un campo coexacto.

En `NavierStokesSobolevKato`, los nombres Sobolev/Kato/Grönwall se aplican a desigualdades numéricas cerradas. `millennium_navier_stokes_regular_by_decide` evalúa una conjunción de tres flags suministrados como true. No define velocidad, presión, condiciones iniciales o una norma funcional. Se contrasta ese alcance con el [problema continuo publicado por Clay Mathematics Institute](https://www.claymath.org/millennium/navier-stokes-equation/), sin tratar flags como pruebas analíticas.

### Contabilidad y recursos

`MolochLandauer` define penalizaciones y resta truncada en Nat. Que un payoff así definido sea cero no demuestra equilibrio de un juego, ausencia de pérdidas, dominancia de Pareto para todos los participantes o que se cobre una penalización. No se mide entropía ni se aplican unidades físicas; el nombre Landauer es histórico. [Landauer (1961)](https://doi.org/10.1147/rd.53.0183) trata borrado físico bajo condiciones, no una tarifa arbitraria Nat.

La función `consume` de C5Affine no realiza una liberación real ni prohíbe duplicar valores. Un lector podría reutilizar active en dos llamadas. Los parsers streaming procesan líneas o chunks, pero no incluyen una prueba global de memoria O(1), coste de enteros arbitrarios ni zero-copy. En el AOT binario, un chunk de 8192 bytes y un resto acotado son una decisión de implementación, no una cota de todos los recursos.

### Qué sí se conserva como resultado formal

AX0 tiene una cota inductiva universal de dispatches para las trazas admitidas por su FSM y ejemplos de habitabilidad. CanonicalHead/CanonicalEnvelope y los schemas ACS/Ticket prueban leyes de representación e inyectividad sobre dominios explícitos y constructores de codecs. El campo genérico roundtrip es una hipótesis de la interfaz, y las instancias suministran sus propias pruebas: eso no se equipara a un axioma vacío.

Esas leyes no autentican firmas, verifican tiempos de caducidad, garantizan permisos ni demuestran que toda la implementación externa coincide con el modelo. Las comparaciones con goldens pueden ayudar a probar casos; aquí se compilan sus expresiones, sin ejecutar la suite Rust o certificar equivalencia universal entre lenguajes.

## 5. Contraejemplos comprobados

Se compila un archivo aislado con Lean 4.34.0-rc2 que importa C5PortHamiltonian y C5Affine:

```lean
import C5PortHamiltonian
import C5Affine
set_option warningAsError true
open C5REAL.Proof
example : doubleHamiltonian (stepPHLD { x := 0, y := 1 } 20) >
    doubleHamiltonian { x := 0, y := 1 } := by decide
example : consume AffineResource.active = some AffineResource.consumed ∧
    consume AffineResource.active = some AffineResource.consumed := by
  exact ⟨rfl, rfl⟩
```

El primero refuta la extensión a monotonía global del ejemplo nominal, incluso con el mismo parámetro 20. No refuta el descenso particular ya probado. El segundo muestra reutilización de valores; no afirma que un allocator concreto tenga un double-free. La diferencia entre modelo puro y gestión de recursos es el hallazgo.

## 6. Fallos y mensajes heredados observados el 2026-10-25

- `BabylonAutoTrace.lean`: `decide` refuta la igualdad de aceptación de su lista. Su fallo debe presentarse como fallo o caso negativo explícito, no prueba positiva.
- `BabylonStressCorrupt.lean`: la lectura impar final es rechazada; afirmar aceptación true no produce una prueba. Puede emplearse como fixture negativo si un harness especifica esa expectativa; no se ha probado aquí tal harness.
- `HolographicPoC.lean`: import de ProofWidgets no disponible en la ruta local. Es una limitación de reproducibilidad, no una refutación de una proposición matemática. No se instala ni actualiza el paquete en este árbol con cambios ajenos.
- Se conservan **strings ejecutables** que afirman «Singularidad Confirmada», «Regularidad Conforme Certificada», «1M Tx superado», «zero-copy» o bloqueo termodinámico. Sus limitaciones quedan anotadas junto al código y aquí, pero su salida literal sigue siendo excesiva. Corregir esos mensajes alteraría salida de runtime; no se hace dentro de este cambio exclusivamente documental.
- Nombres históricos como `no_torn_reads_universal` o `millennium_navier_stokes_regular_by_decide` siguen exportados. Su tipo y comentarios corregidos, no su nombre, fijan el alcance. No se renombra una API por inferencia de esta auditoría.

## 7. Reproducción, controles y límites

Desde `proof/lean`: `lake --no-cache --wfail build` comprueba los targets por defecto con la toolchain fijada. Para fuentes sueltas se necesita compilar sus imports locales en el mismo entorno, añadir su ruta a LEAN_PATH y ejecutar Lean sobre cada módulo, con `#print axioms` para sus teoremas. No se debe confundir el build por defecto con la cobertura de las 23 fuentes.

Las copias originales, logs, script de instrumentación ad hoc, contraejemplos y contrato quedan localmente en `.audit/lean-scope-20261025/` (ignorado por Git). El JSON enlazado conserva la evidencia estructurada portable. Los cambios de comentarios se verifican mediante comparación léxica que preserva strings y código, y los manifiestos/toolchain se comparan byte a byte. Se ejecutan también enlaces, diff y gates documentales de workspace; no se leen reglas globales ni ghost listeners.

La lista de axiomas se interpreta según la [implementación/documentación oficial de Lean](https://github.com/leanprover/lean4/blob/master/tests/elab/collectAxioms.lean). Compilar y comprobar dependencias es necesario para una prueba formal local, pero no define ni prueba propiedades que no estén en su enunciado. No hay certificación física, clínica, jurídica o de producción.

El inventario documental actual contiene además `axiom_moloch_landauer_balance.md`, incorporado desde la revisión anterior; se completa su enlace en los índices y se delimita allí el alcance contable del código. Esta tarea no reaudita su prosa completa ni las especificaciones fuera de proof/lean. Los mensajes ejecutables heredados señalados en §6 permanecen pendientes de una corrección de salida de runtime.

Aceptación local: pasan el build Lake de los targets por defecto, los dos contraejemplos, la comparación de código/strings sin comentarios en las 23 fuentes, la identidad byte a byte de metadatos de dependencias, 49 enlaces locales nuevos, la cobertura de los 31 documentos actuales en los tres índices y `git diff --check` del alcance. Pasan los gates semántico, presupuesto y topología con alcance workspace. La compilación individual mantiene tres fallos explícitos; no se informa de un éxito global inexistente.


## 8. Seguimiento del 2026-10-26: mensajes y clasificación de fixtures

### Dos rechazos esperados, no bibliotecas positivas averiadas

La inspección de las versiones previas de [fsm_poc.rs](../../crates/b60-lang/src/bin/fsm_poc.rs) mostró que primero generaba una traza nominal en BabylonAutoTrace y después sobrescribía ese archivo con una traza corrupta; esperaba que Lean rechazase esta segunda afirmación de aceptación. [fsm_stress.rs](../../crates/b60-lang/src/bin/fsm_stress.rs) generaba BabylonStressCorrupt con 1.500 eventos nominales y una lectura impar final y también esperaba rechazo. No son targets positivos del build por defecto. El comportamiento de escritura y clasificación se corrige después en §9.

La auditoría inicial no había seguido estos generadores. Se rectifica la interpretación: los dos archivos son **fixtures negativos de rechazo esperado**. Sus datos y ecuaciones `= true` permanecen intactos. Cambiar la conclusión a false convertiría el caso negativo de compilación en una prueba distinta y podría ocultar la expectativa del harness.

Comprobación aislada: una traza nominal temporal begin 1 → end 2 → read 2 compila con exit 0; ambos fixtures retornan exit 1 con el diagnóstico de que `decide` demostró falsa la proposición. La comprobación exige ese diagnóstico, no solo un código distinto de cero. No se ejecutaron los generadores Rust, que escriben estas fuentes.

**Límite del harness Rust:** los generadores consideran cualquier fallo de Lean un rechazo y sus ramas JIT pueden limitarse a imprimir un error sin garantizar fallo global del proceso. No se certifica ese harness como gate de CI; se comprueba el rechazo semántico de los fixtures actuales con un control nominal independiente. Su endurecimiento queda fuera de este cambio de mensajes y clasificación.

### Mensajes ejecutables corregidos

Se cambian los literales de salida de BabylonOracle, BabylonAOTOracle, NavierStokesOracle y HolographicPoC:

- CSV: aceptación/rechazo de los registros por el modelo de secuencias; no afirma procesar un millón de transacciones ni causalidad física.
- Binario: número de registros aceptados, formato inválido/incompleto o rechazo del modelo; no se etiqueta como zero-copy ni como prueba de una propiedad física.
- Fluido: describe flags y contadores del autómata e indica que no demuestra singularidad o regularidad PDE. La rama sin cuarentena ya no afirma que el acumulado sea menor que 3600: una entrada con 5000 sin evento de cuarentena reproduce esa clasificación.
- Widget: «Valores de ejemplo» y «no ejecuta ni bloquea operaciones». No dice medir energía ni abortar concurrencia.

Se conservan las firmas, guards, validadores, ramas y códigos de salida 0/1/2/10. Se ejecutan 13 casos sintéticos temporales que cubren entrada vacía, nominal, rechazo y error de formato, además de truncamiento binario y las tres clasificaciones del autómata. Todos conservan el código esperado y emiten texto delimitado al modelo. No es un benchmark ni validación de producción.

### ProofWidgets: import correcto, artefactos ausentes

ProofWidgets está resuelto en el manifiesto y su fuente local coincide con la revisión fijada. El import HtmlDisplay y la API del ejemplo son correctos; faltaban artefactos compilados en la ruta habitual. Su lakefile tiene un hook de JavaScript que puede llamar npm: no se invocó ese build de paquete ni se instaló/actualizó nada.

Se compilaron en un temporal únicamente los módulos Lean locales Compat, Util, Component.Basic, Data.Html y Component.HtmlDisplay; los cinco y el HolographicPoC final compilan con Lean 4.34.0-rc2 al anteponer esa ruta temporal a LEAN_PATH. Eso acredita compilación aislada, no preparación persistente del entorno habitual ni renderizado visual en Infoview.

### Evidencia actual y cierre

El [registro de casos del 26](evidence/lean-reporting-20261026.json) complementa, sin sustituir, el inventario histórico del 25. Recetas y logs completos se conservan en `.audit/lean-reporting-20261026/`. Los datos de fixtures son sintéticos y temporales; las salidas se normalizan para no depender del nombre de ese directorio.

Las cabeceras y README distinguen veinte fuentes positivas en el entorno habitual, dos rechazos semánticos esperados y un widget compilado en entorno temporal. Ninguna categoría certifica hardware, PDE, percepción o seguridad del runtime. Los wrappers y simuladores fuera de proof/lean no se reauditan globalmente en este seguimiento.

Aceptación del seguimiento del 26: pasan los 13 casos de mensajes/códigos de salida, el control nominal y los dos rechazos semánticos esperados, la compilación aislada del widget final y el build Lake por defecto (21 jobs). Pasan 52 enlaces locales de README/informe, el diff acotado y los gates semántico, presupuesto y topología del workspace. Los validadores, ramas, códigos de salida, enunciados de fixtures y metadatos de dependencias permanecen iguales al inicio de este seguimiento. No se valida Infoview visualmente ni se endurece el harness Rust.

## 9. Iteración del 2026-10-26: errores del harness Rust

### Falso positivo reproducido y contrato corregido

La versión previa de fsm_stress, compilada desde la copia inicial y ejecutada en un workspace temporal con un sustituto de prueba de Lake que solo devuelve error 1, anuncia «RECHAZO EXITOSO» y termina con código 0. No existe prueba Lean en ese caso. Esta reproducción aislada confirma el defecto: error de infraestructura presentado como evidencia semántica. El sustituto se usa solo para probar el manejo de procesos, sin simular una prueba formal válida.

Ambos programas usan ahora un [runner común](../../crates/b60-lang/src/bin/support/lean_harness.rs). Para una lista cerrada de eventos numéricos genera en un directorio temporal:

```lean
theorem trace_expected_verdict : validateTrace auto_execution_trace = false := by
  decide
```

En el control nominal la conclusión exigida es `true`. En ambos casos se comprueban dependencias vacías mediante `#guard_msgs in #print axioms`, advertencias como errores, exit 0, marcador exacto único y stderr vacío. El marcador se emite después del teorema, pero por sí solo no basta: Lean puede continuar tras un diagnóstico de error. No se interpreta texto inglés de errores como certificado.

Un rechazo certificado del modelo es una compilación correcta de la igualdad con `false`. Import ausente, sintaxis inválida, proceso ausente, señal, timeout, salida inesperada o expectativa incompatible son **errores**, nunca ese rechazo certificado. Ambos main propagan esos errores y devuelven código distinto de cero, también cuando falla el control nominal o el negativo.

Las fuentes generadas ya no reemplazan BabylonAutoTrace, BabylonStressTrace o BabylonStressCorrupt. Los dos fixtures negativos guardados continúan afirmando `true` para listas que el modelo rechaza; su expectativa de fallo del compilador sigue siendo distinta del nuevo certificado temporal de `false`. Los validadores y sus garantías matemáticas no cambian.

### AOT, límites y reproducción

El recorrido CSV distingue código 0 (aceptado), 2 (paso rechazado por el modelo) y error para cualquier otro código, señal o fallo de lanzamiento. Sus escrituras también propagan errores. Los CSV se confinan a temporales por ejecución. No se deduce rechazo de la negación de un booleano que mezcle fallos. Este recorrido usa el contrato del ejecutable CSV suministrado: no comprueba una prueba Lean por cada entrada ni acredita la procedencia de un binario arbitrario.

Se añaden `--jit-only` a fsm_poc y `--quick` a fsm_stress para controles acotados, sin cambiar los tamaños de sus recorridos por defecto. Las pruebas Rust del [protocolo y CLI](../../crates/b60-lang/tests/lean_harness.rs) usan sustitutos de proceso aislados para fallos; el test explícito `real_lean` usa la toolchain e imports locales para demostrar ambas igualdades y rechazar una expectativa incompatible. Las recetas están en el [README de Lean](../../proof/lean/README.md#harness-rust-y-controles-de-rechazo).

Cada proceso tiene un plazo de 120 s y captura separada de stdout/stderr en archivos, evitando bloqueos de tuberías. En Unix, al vencer o fallar la espera se termina el grupo de procesos; fuera de Unix solo se termina el hijo directo. No se supervisan descendientes desacoplados de herramientas hostiles: no es un mecanismo de aislamiento de seguridad. Los tiempos impresos son observaciones locales sin protocolo de benchmark; no demuestran complejidad, energía, seguridad física o equivalencia Rust–Lean. La generación del millón conserva un vector de O(N), sin pretensión de memoria total O(1).

El [registro de esta iteración](evidence/lean-harness-20261026.json) conserva comandos y resultados; copias iniciales, reproducción del falso positivo y logs quedan en `.audit/lean-harness-20261026/`. La cobertura global de Rust, el estrés por defecto y el recorrido AOT masivo quedan fuera de esta comprobación acotada. No se cambian dependencias ni lockfiles.

Aceptación de esta iteración: pasan la comprobación Rust con `--locked`, 13 tests de proceso/CLI/CSV y un test de Lean real ejecutado explícitamente (14 tests en total). El test real comprueba cinco casos: true nominal, false negativo, expectativa falsa, import inexistente y sintaxis inválida. Pasan las dos CLI acotadas con Lean real y el build Lake por defecto (21 jobs). El primer intento del test de timeout no alcanzó a registrar el hijo bajo ejecución paralela; se conserva ese fallo, se comprueba el caso aislado y se amplía el margen de arranque de 1 a 5 s sin eliminar la exigencia de terminación del descendiente. La suite final pasa con el margen actualizado. Se comprueban 60 enlaces locales, la cobertura de los 30 documentos de teoría más su índice en los tres índices, formato, diff y los gates documentales del workspace. Fixtures y metadatos de dependencias son idénticos al inicio de esta iteración. Se omiten reglas globales y telemetría de ghost listeners; estas comprobaciones no certifican el runtime de producción.

## 10. Seguimiento del 2026-10-26: verificación Lean bajo demanda

La etiqueta heredada «JIT» era imprecisa: estos programas de prueba generan una fuente Lean y llaman `lake env lean` para comprobar un teorema cerrado. Se denomina ahora **verificación Lean bajo demanda** y sus salidas usan `[LEAN_CHECK]`. No se implementa un compilador JIT propio en estos harnesses ni se infiere una propiedad del runtime a partir del nombre.

La opción preferida de fsm_poc pasa a `--lean-only`. Se conserva `--jit-only` como alias con los mismos controles nominal/negativo y los mismos errores; fsm_stress conserva `--quick`. No se cambian el runner, los modelos Lean, los marcadores del protocolo interno ni los contratos CSV. Se amplía la matriz de invocaciones de los tests existentes para cubrir los dos nombres de opción, sin introducir una nueva prueba matemática.

El requisito de orquestar Lean fuera del bucle crítico es una obligación del [contrato Ring-1](../03_guides/agent_contracts.md#ring-1). La comprobación de estos ejecutables de prueba no demuestra que toda integración de producción satisfaga ese requisito, ni aporta latencia de producción o equivalencia de memoria Rust–Lean. La descripción anterior de «fuera de la ruta crítica» debe leerse con ese límite.

El [registro de este seguimiento](evidence/lean-naming-20261026.json) contiene las ejecuciones con ambos nombres de opción y la salida nueva. El registro de §9 y los demás JSON históricos se preservan byte a byte: sus etiquetas JIT y hashes corresponden a aquella versión, no a las fuentes posteriores a este cambio. Los índices enlazan la auditoría con el término actualizado. La evidencia local completa se conserva en `.audit/lean-naming-20261026/`.
