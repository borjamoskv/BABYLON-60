---
title: Proof-carrying execution: modelo y evidencia pendiente
status: Diseno-con-fuentes-formales-acotadas
version: 2.1.0
---

# Proof-carrying execution: modelo y evidencia pendiente

Revisión inicial: 2026-10-24; seguimiento: 2026-10-26. Estatus: **Diseno-con-fuentes-formales-acotadas**. El sello histórico de verificación y el axioma genérico de validez documental no acreditaban el contenido. [Revisión inicial](AUDIT_SCIENTIFIC_STATUS_2026.md) · [Alcance Lean actualizado](AUDIT_LEAN_SCOPE_2026.md) · [Garantías de las especificaciones](../01_spec/AUDIT_SCIENTIFIC_GUARANTEES_2026.md).

## 1. Qué existe y qué no se certifica

Existen [BabylonTrace.lean](../../proof/lean/BabylonTrace.lean), [BabylonAOTOracle.lean](../../proof/lean/BabylonAOTOracle.lean), [lakefile.toml](../../proof/lean/lakefile.toml) y [fsm_poc.rs](../../crates/b60-lang/src/bin/fsm_poc.rs). Su presencia no demuestra despliegue de producción ni reproduce los cuatro vuelos históricos.

| Cifra histórica | Estatus de esta revisión |
| --- | --- |
| 3 eventos, 840/790 ms en JIT | Registro narrativo sin logs y configuración reproducidos aquí; NO_VERIFICADO. |
| 1.000.002 eventos, 566,69 ms y 1,76 M tx/s en AOT | Medición histórica declarada, no benchmark actual certificado. |
| Aborto en secuencia 333333, 288,80 ms | No se repitió la traza; no se infiere detección universal de corrupción. |
| 113–155 M msg/s y 2.142 M msg/s SIMD | No comparables al checker sin carga, unidades y método comunes; NO_VERIFICADOS aquí. |

Se retiran la garantía matemática absoluta «sin asunciones humanas» y las versiones de herramientas usadas como prueba de ejecución actual.

## 2. Proposición formal frente a efecto físico

El checker abstracto evalúa secuencias declaradas y autor del escritor. En una lectura comprueba paridad de `event.seq` y que no sea futura; no comprueba payload ni dos versiones de un snapshot. Puede aceptar una secuencia de lectura par anterior aun cuando la secuencia del estado escritor sea impar. Se corrige la afirmación de que rechaza toda lectura durante escritura.

Un teorema sobre ese modelo no demuestra orden de memoria en Rust, ausencia de torn reads físicos ni validez de los datos declarados en la traza. Para ello hacen falta instrumentación confiable, semántica y refinamiento. Una firma de la traza tampoco prueba que la traza cubra todos los efectos.

## 3. Verificador AOT y coste

El bloque histórico `consumeStream` de esta página era un fragmento CSV dependiente de tipos y parser externos, no un archivo compilable. Hay dos recorridos diferentes: [BabylonOracle](../../proof/lean/BabylonOracle.lean) procesa CSV y [BabylonAOTOracle](../../proof/lean/BabylonAOTOracle.lean) procesa bloques binarios de 8192 bytes, conserva el resto y rechaza un registro truncado al EOF. El harness fsm_poc usa el contrato del ejecutable CSV, no el parser binario. La descripción del formato y los códigos esperados deben identificar el recorrido concreto.

Un buffer acotado no demuestra memoria total O(1): estado, contador Nat, parser, asignaciones y recursos del runtime tienen que incluirse en el modelo de coste. `partial def` y compilar a C no prueban ausencia de garbage collection ni corrección del compilador o del protocolo.

## 4. Estado de verificación

El 24 se comprobaron Babylon y BabylonTrace con Lean 4.35.0; no se hizo entonces el build Lake fijado. El [seguimiento del 26](AUDIT_LEAN_SCOPE_2026.md) registra el build por defecto con Lean 4.34.0-rc2, los controles temporales de oráculos y el endurecimiento del harness. Su opción preferida `--lean-only` ejecuta verificación Lean bajo demanda: exige prueba de true nominal y false negativo, salida 0 y marcador exacto. Los errores de infraestructura no cuentan como rechazo certificado. `--jit-only` queda como alias histórico.

Esos controles sintéticos y secuenciales no reproducen los benchmarks históricos de la tabla ni demuestran payload atómico, memoria Rust o integración productiva fuera de la ruta crítica. Las cifras históricas mantienen su estatus no revalidado. No se modifican validadores ni dependencias mediante esta rectificación documental.
