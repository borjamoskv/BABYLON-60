# Alcance de las fuentes Lean

Revisión: 2026-10-26. [Informe de auditoría](../../docs/06_theory/AUDIT_LEAN_SCOPE_2026.md) · [Inventario y axiomas](../../docs/06_theory/evidence/lean-scope-20261025.json).

Las 23 fuentes directas contienen modelos abstractos, codecs, ejemplos finitos, parsers IO y un widget. Los nombres heredados no certifican propiedades físicas ni del código Rust. Se preservan API, definiciones, tácticas, validadores y códigos de salida. La revisión del 25 corrigió comentarios; la del 26 corrige también los mensajes de los ejemplos, sin atribuirles garantías físicas.

`lake --no-cache --wfail build` pasa con Lean 4.34.0-rc2 para los targets por defecto. La clasificación individual distingue veinte fuentes que compilan en el entorno habitual, dos fixtures cuyo rechazo semántico es esperado y un widget comprobado con cinco módulos locales de ProofWidgets compilados en un temporal. El build por defecto no cubre por sí solo estos últimos casos.

| Fuente | Estatus de esta revisión |
| --- | --- |
| [AX0.lean](AX0.lean) | Compila; alcance del modelo |
| [AcsEnvelope.lean](AcsEnvelope.lean) | Compila; alcance del modelo |
| [Babylon.lean](Babylon.lean) | Compila; alcance del modelo |
| [BabylonAOTOracle.lean](BabylonAOTOracle.lean) | Compila; alcance del modelo |
| [BabylonAeonChain.lean](BabylonAeonChain.lean) | Compila; alcance del modelo |
| [BabylonAeonStress.lean](BabylonAeonStress.lean) | Compila; alcance del modelo |
| [BabylonAutoTrace.lean](BabylonAutoTrace.lean) | Fixture negativo: rechazo semántico esperado y comprobado |
| [BabylonOracle.lean](BabylonOracle.lean) | Compila; alcance del modelo |
| [BabylonStressCorrupt.lean](BabylonStressCorrupt.lean) | Fixture negativo: rechazo semántico esperado y comprobado |
| [BabylonStressTrace.lean](BabylonStressTrace.lean) | Compila; alcance del modelo |
| [BabylonTrace.lean](BabylonTrace.lean) | Compila; alcance del modelo |
| [C5Affine.lean](C5Affine.lean) | Compila; alcance del modelo |
| [C5PortHamiltonian.lean](C5PortHamiltonian.lean) | Compila; alcance del modelo |
| [CanonicalEnvelope.lean](CanonicalEnvelope.lean) | Compila; alcance del modelo |
| [CanonicalHead.lean](CanonicalHead.lean) | Compila; alcance del modelo |
| [Destiladora_838c463da193b48f.lean](Destiladora_838c463da193b48f.lean) | Compila; alcance del modelo |
| [HolographicPoC.lean](HolographicPoC.lean) | Compila con imports locales precompilados en temporal; no verificado visualmente |
| [MolochLandauer.lean](MolochLandauer.lean) | Compila; alcance del modelo |
| [NavierStokesBKM.lean](NavierStokesBKM.lean) | Compila; alcance del modelo |
| [NavierStokesOracle.lean](NavierStokesOracle.lean) | Compila; alcance del modelo |
| [NavierStokesSobolevKato.lean](NavierStokesSobolevKato.lean) | Compila; alcance del modelo |
| [NemesisWave4.lean](NemesisWave4.lean) | Compila; alcance del modelo |
| [TicketEnvelope.lean](TicketEnvelope.lean) | Compila; alcance del modelo |

No hay instalación/actualización de paquetes; se ejecutan los oráculos únicamente sobre fixtures sintéticos temporales. Las dependencias de los 121 teoremas inspeccionados en fuentes compiladas son vacías o contienen propext/Quot.sound; los campos exigidos a registros y las hipótesis locales siguen siendo supuestos. Los mensajes de los tres oráculos y del widget describen ahora el resultado del modelo o una vista de ejemplo. Se verifican 13 casos de mensajes/códigos de salida, dos rechazos semánticos con control nominal y compilación aislada del widget.

## Harness Rust y controles de rechazo

[fsm_poc](../../crates/b60-lang/src/bin/fsm_poc.rs) y [fsm_stress](../../crates/b60-lang/src/bin/fsm_stress.rs) usan un [runner compartido](../../crates/b60-lang/src/bin/support/lean_harness.rs). Generan una fuente temporal que demuestra `validateTrace trace = true` para el control nominal o `= false` para el negativo, mediante `decide`. Exigen exit 0, marcador único y stderr vacío; comprueban también que el teorema cerrado no depende de axiomas. Un error de imports, sintaxis, ejecución, timeout o expectativa incompatible hace fallar el programa. Los fixtures negativos guardados con `= true` se conservan como casos distintos de rechazo del compilador.

Este recorrido se denomina **verificación Lean bajo demanda**: invoca `lake env lean` sobre una fuente temporal durante el test. Sus mensajes llevan `[LEAN_CHECK]` y la opción preferida de fsm_poc es `--lean-only`; `--jit-only` se conserva como alias histórico compatible. Estos programas no implementan un compilador JIT de BABYLON-60. El requisito de mantener la verificación fuera del bucle crítico de producción es una obligación de arquitectura; estos controles de prueba no acreditan por sí mismos todos los recorridos de una integración productiva.

Comprobación acotada desde la raíz, tras preparar los imports con el build Lake:

```sh
cargo test --locked -p b60-lang --features stress-bins --bin fsm_poc --bin fsm_stress --test lean_harness
cargo test --locked -p b60-lang --features stress-bins --test lean_harness real_lean -- --ignored
cargo run --locked -p b60-lang --features stress-bins --bin fsm_poc -- --lean-only
cargo run --locked -p b60-lang --features stress-bins --bin fsm_stress -- --quick
```

El primer comando prueba el protocolo con sustitutos de proceso aislados; el segundo ejecuta Lean real y falla si falta el entorno requerido. Los otros dos ejecutan ambos controles a través de las CLI reales, con Lean local.

El CSV AOT interpreta 0 como aceptación y 2 como rechazo del modelo; otros códigos o errores son fallos del harness. Esto depende del contrato del ejecutable suministrado, sin comprobación de prueba por entrada en el kernel de Lean. Las trazas son sintéticas y secuenciales; no prueban correspondencia con ejecución concurrente Rust. El límite de cada proceso es 120 s: en Unix se termina su grupo al vencer, en otras plataformas solo el hijo directo. Es supervisión de herramientas confiables, no confinamiento de procesos hostiles. [Evidencia del protocolo](../../docs/06_theory/evidence/lean-harness-20261026.json) · [Seguimiento de nomenclatura y alias](../../docs/06_theory/evidence/lean-naming-20261026.json) · [Censo reconciliado 26 módulos / 144 teoremas / 228 construcciones](../../docs/06_theory/evidence/lean-census-372-v511.json).
