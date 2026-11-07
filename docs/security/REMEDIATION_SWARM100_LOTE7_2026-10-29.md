# Lote 7 ejecutado: gate y reporte sin falsas garantías — 29/10/2026

C0556 y C0557 pasan a FIXED para sus defectos de falso éxito y recibo
fabricado/sin vinculación al contenido. La única fuente productiva editada es
`scripts/c5_verifiers/fast_smt_gate.py`. El
[registro reconciliado](evidence/swarm100-round3-20261028/registry.json)
y la [validación final](evidence/swarm100-lot7-20261029/validation.json)
conservan estados, comandos, hashes y límites.

**Las 25 propiedades siguen NOT_EXECUTED: no se ha implementado un solver ni
un checker.** El gate bloquea el éxito mientras no existan comprobaciones
soportadas. Corregir una afirmación falsa de verificación no prueba las
invariantes del sistema.

## Reproducción y verificación

Las [siete reproducciones anteriores al parche](evidence/swarm100-lot7-20261029/before-tests.log)
fallaron contra el [hash previsto](evidence/swarm100-lot7-20261029/before-source-manifest.json).
Presencia de README/.agents, modos de salida, resultados/detalles alterados,
pseudo-firma y exportación vacía demostraban el defecto en una copia temporal.
No se ejecutó el mantenimiento ni se accedió a datos del operador.

**721 pruebas aprobadas y 1 omitida** en la suite relacionada final, incluidas
**71 regresiones del lote**. La omisión corresponde a strike_rs no compilado,
con el módulo bloqueado antes de recoger las pruebas. Pasan MyPy con
check-untyped-defs, Ruff y los controles documentales. Los hashes productivo y
de regresiones son idénticos antes y después de esa ejecución.

La [revisión independiente](evidence/swarm100-lot7-20261029/independent-review.json)
aprueba nueve controles propios (24 combinaciones de salida, 13 entradas
inválidas y 22 campos del cuerpo ligados) y repite las 71 regresiones. Conserva
sus límites y no deja hallazgos accionables abiertos en estos dos IDs. Detectó que
el primer exportador llamaba COLLECTED_READ_ONLY a observaciones meramente
aportadas por el caller. La versión final las etiqueta
REPORTED_OBSERVATIONS_NOT_PROOF; no infiere una lectura desde la función pura.
La evidencia anterior se conserva sin reinterpretarla como versión final.

| ID | Corrección | Aceptación observada |
| --- | --- | --- |
| C0556 | Inventario completo de estados explícitos y observaciones separadas; ningún PASS sin checker. | NOT_EXECUTED/UNKNOWN/FAIL o inventario inválido bloquean texto, JSON y --scitt, con y sin --strict. El consumidor presente rechaza el retorno no cero. |
| C0557 | Reporte v3 UNSIGNED y digest del cuerpo completo/configuración. | Cambiar resultado, detalle, descripción, configuración, observación, latencia o fecha con los mismos IDs cambia el digest. No se fabrica firma/compliance. |

## Contrato de salida

El perfil catalogue-only-v3 conserva los 25 IDs originales y exige todos una
sola vez, con campos y estados válidos. Rechaza inventarios vacíos/incompletos,
duplicados, IDs desconocidos, resultados booleanos y PASS no soportado. El
retorno normal es 2 si falta ejecución o hay UNKNOWN; 1 si se reporta FAIL o
el esquema es inválido. --strict no permite relajar el rechazo. --help conserva
el retorno informativo habitual y no representa una aprobación del gate.

--json y el alias legado --scitt emiten `babylon60.invariant-report.v3`.
`generate_scitt_receipt` conserva su nombre como alias de exportación sin
firma, pero rechaza los tuples booleanos del contrato anterior. Los consumidores
que interpreten el antiguo JSON deben migrar; los recibos históricos se
conservan, sin regenerarlos ni legitimarlos como firmas.

El cuerpo declara UNSIGNED, firma None, SCITT NOT_ISSUED, certificación NONE,
legal NOT_ASSESSED y hardware UNVERIFIED. Incluye todos los resultados,
configuración, observaciones, métricas y timestamp local no atestado. BLAKE3
con dominio y JSON canónico UTF-8 cubre ese cuerpo entero, excluyendo únicamente
su propio digest. Se contrasta con un recálculo independiente. El digest permite
comprobar consistencia del contenido; cualquiera que lo modifique puede
recalcularlo. No aporta autenticidad ni resistencia frente a esa sustitución.

Las rutas se observan por metadatos de entradas y tipo, sin leer contenido,
recurrir al workspace padre ni seguir enlaces de los marcadores. No demuestran
ninguna propiedad del DAG o de los agentes. La raíz explícita no es un sandbox
del sistema operativo. El exportador puro no hace lecturas de rutas ni presenta
observaciones aportadas como evidencia de ejecución. La latencia publicada es
de generación del reporte; smt_verification_latency_ms es None.

## Consumidor y límites

Se extrajo únicamente phase_4_quality_gates del consumidor a un namespace de
prueba. Tres dobles de subprocess observan el rechazo del código no cero del
gate presente; ningún auto-fixer ni canary real se ejecutó. El
[control de alcance](evidence/swarm100-lot7-20261029/scope-check.json)
confirma intactos daily_sovereign_maintenance, dependencias y lockfiles.
**Su rama que deja smt_ok=True si falta el script sigue fuera de este parche.**

Los tests usan copias temporales, HOME/root propios y TCP/DNS bloqueados. Las
32 exportaciones concurrentes comprueban determinismo con reloj fijado; no son
un benchmark ni una demostración de contención física. No hay claves reales,
SCITT, firma hardware, solver, mantenimiento completo, publicación o ATTESTED.
Se omite la telemetría global. No se ejecutaron pruebas Rust al no haber cambios
Rust ni dependencias. El grafo MCP no estaba expuesto; la exploración fue acotada.

## Registro y siguiente lote

Los 598 IDs originales quedan en 547 OPEN, 43 FIXED, 4 MITIGATED y
4 NOT_APPLICABLE. Entre los 582 pendientes iniciales: 542 OPEN, 33 FIXED,
3 MITIGATED y 4 NOT_APPLICABLE. Quedan **541 hallazgos únicos OPEN**:
59 P1, 472 P2 y 10 P3. No se cierran IDs adicionales por inferencia.
C0431 y C0135/C0136 siguen OPEN; C0460 sigue MITIGATED.
SW100-R3-0001 permanece FIXED fuera de los 598 IDs.

El [Lote 8 propuesto](PLAN_SWARM100_LOTE8_2026-10-29.md) agrupa C0499/C0500
en cortex_objectives_transducer.py. Su hash sigue intacto: solo se prepara.

Se consultó mediante Context7 el
[README oficial de BLAKE3](https://github.com/blake3-team/BLAKE3/blob/master/README.md)
para el algoritmo; esa fuente no acredita la API del wrapper Python. El uso de
la dependencia Python ya existente se verifica con ejecución y recálculo en
los arneses. No se modificaron dependencias.
