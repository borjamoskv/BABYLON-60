# Tercera ronda: V07 y adjudicación del registro — 28/10/2026

## Contrato previo a las ediciones

Resultado esperado: corregir la promoción de conclusiones no demostradas de V07
y avanzar la adjudicación individual de los 582 candidatos pendientes. Una
clasificación, una reproducción y una corrección son estados distintos.

Rutas: `babylon60/autodidact/epistemology.py`, `engine.py`, exportaciones y pruebas
relacionadas; fuentes concretas referidas por el registro; herramientas de
auditoría y evidencia de esta ronda. Preservar cambios ajenos, correcciones
anteriores e informes históricos. Sin cambios de dependencias, commits,
despliegues ni ejecución contra datos del operador.

Aceptación:

| ID | Criterio | Estado inicial |
| --- | --- | --- |
| V07-A | Conclusión distinta de las premisas no recibe FormalProof ni CANONICAL | pending |
| V07-B | Identidad conserva justificación/confianza; Hume y premisas inválidas se rechazan | pending |
| V07-C | Rechazo no modifica registro ni DAG; regresiones y suites relacionadas pasan | pending |
| REG-A | Los 598 IDs originales aparecen exactamente una vez en el registro reconciliado | pending |
| REG-B | Cada estado nuevo remite a evidencia, alcance y hash vigente | pending |
| REG-C | Candidatos sin evaluación siguen pendientes; no se cierran por clasificación automática | pending |

Aplican los [contratos de lógica, persistencia y documentación](../03_guides/agent_contracts.md).
El MCP de grafo no está expuesto en esta sesión; el descubrimiento se limita a
las rutas referidas por los hallazgos y sus consumidores.

## Resultado

### Seguimiento documental inicial de C0279 (superado)

Tras la respuesta «no lo sé» del operador, se adopta como decisión local
reversible el uso observado: una difusión global por instancia, retenida para
agentes tardíos. Resultado esperado: documentar ese alcance en `AgentPager`,
resolver el dictamen y actualizar el registro; mensajes sucesivos requieren
otra instancia. Rutas: `scripts/c5_sharur/agent_beeper.py`, este informe y su
evidencia. Aceptación: AST ejecutable idéntico, comprobación aislada de difusión
y recepción tardía, hashes vigentes y controles documentales. C0278 permanece
abierto; se conservan los dictámenes históricos y la incertidumbre original.

Ese cierre documental se reabrió por instrucción del operador. La
[corrección ejecutable posterior de C0278 y C0279](REMEDIATION_AGENT_PAGER_2026-10-28.md)
impone el rechazo en código y sustituye sus estados anteriores.

**V07 corregido en el alcance reproducido. Los 582 candidatos están revisados
y tienen dictamen resuelto.** La revisión
no corrige por sí misma los defectos confirmados.

El [registro reconciliado](evidence/swarm100-round3-20261028/registry.json)
conserva los 598 IDs originales, sus observaciones históricas y el dictamen
vigente. Las dos rondas anteriores permanecen intactas. El
[resumen verificable](evidence/swarm100-round3-20261028/registry-summary.json)
y la [cola de corrección](evidence/swarm100-round3-20261028/remediation-queue.json)
permiten distinguir clasificación de remediación.

| Dictamen sobre los 582 pendientes iniciales | IDs |
| --- | ---: |
| Confirmado por inspección estática | 452 |
| Reproducido; sigue OPEN o MITIGATED | 53 |
| Resuelto por correcciones (`ALREADY_FIXED`) | 68 |
| Rechazado según el contrato vigente | 4 |
| Duplicado adicional | 5 |
| Contrato pendiente de validar | 0 |
| Total | 582 |

`ALREADY_FIXED` distingue correcciones y mitigaciones por rechazo explícito;
el campo `remediation_state` conserva esa diferencia. Entre esos 582 IDs quedan
**504 OPEN, 69 FIXED, 5 MITIGATED,
4 NOT_APPLICABLE y 0 UNKNOWN**. Los duplicados heredan el estado del canónico
salvo una superficie independiente revisada explícitamente como no corregida;
se preservan todas sus rutas afectadas.

En el inventario completo de 598 IDs hay **503 hallazgos únicos OPEN**:
25 P1, 468 P2 y 10 P3. Por separado quedan seis registros mitigados. C0279
se resuelve mediante rechazo ejecutable y regresiones, como se detalla abajo.
Estas cifras no constituyen un certificado de seguridad.

El [Lote 1 ejecutado](REMEDIATION_SWARM100_LOTE1_2026-10-28.md) corrige C0373,
C0501/C0264 y C0420/C0421 con 62 regresiones y firma positiva de fixture.
El [Lote 2 ejecutado](REMEDIATION_SWARM100_LOTE2_2026-10-28.md) corrige cuatro P1
y mitiga C0460 por rechazo antes de abrir la base. El
[Lote 3 ejecutado](REMEDIATION_SWARM100_LOTE3_2026-10-28.md) corrige C0413,
C0418 y SW100-R3-0001 (este último fuera de los 598 IDs). Pasan 393 casos distintos entre suite y regresiones finales
y se omite uno por strike_rs no compilado; hardware/push real NO_VERIFICADOS.
El [Lote 4 ejecutado](REMEDIATION_SWARM100_LOTE4_2026-10-28.md) corrige
cuatro P1 y dos P2 en tres fuentes: 496 pruebas pasan y una se omite por
strike_rs no compilado. C0135/C0136 históricos siguen OPEN. El
[Lote 5 ejecutado](REMEDIATION_SWARM100_LOTE5_2026-10-28.md) corrige
C0428/C0429/C0430 en ledger_actor.py: 536 pruebas pasan, una se omite con
IPC nativo bloqueado. C0431 sigue OPEN. El
[Lote 6 ejecutado el 29/10](REMEDIATION_SWARM100_LOTE6_2026-10-29.md) corrige
C0132/C0133 en swarm_orchestrator.py: 650 pruebas pasan y una se omite,
sin red real y con credenciales sintéticas. El
[Lote 7 ejecutado](REMEDIATION_SWARM100_LOTE7_2026-10-29.md) corrige
C0556/C0557 en fast_smt_gate.py: 721 pruebas pasan y una se omite. El gate
bloquea el éxito y emite reportes UNSIGNED; las 25 propiedades permanecen
NOT_EXECUTED, sin checker implementado. El
[Lote 8 ejecutado](REMEDIATION_SWARM100_LOTE8_2026-10-29.md) corrige C0499/C0500
en cortex_objectives_transducer.py: 782 pruebas pasan y una se omite, con Git
real solo en repositorios temporales. El informe conserva límites de hooks y
concurrencia sobre un mismo output. El
[Lote 9 ejecutado](REMEDIATION_SWARM100_LOTE9_2026-10-29.md) corrige C0438 en
c5_exergy_optimizer_monitor.py: 829 pruebas pasan y una se omite; se conservan
hooks/firma configurada y solo se crea un commit de STATUS en fixtures. Las
métricas y el SHA3 previo siguen fuera del cierre. El
[Lote 10 ejecutado](REMEDIATION_SWARM100_LOTE10_2026-10-29.md) corrige C0574/C0575
en purge_residuals.py: 889 pruebas pasan y una se omite. Preserva locks/bases y
solo limpia bytecode reconocido; las purgas se ejecutan únicamente en fixtures.
El informe conserva límites de cabecera y concurrencia stat/unlink. El
[Lote 11 ejecutado](REMEDIATION_SWARM100_LOTE11_2026-10-29.md) corrige
C0167/C0168/C0169 en core/cortex_persist.py: 944 pruebas pasan y una se omite.
Atomicidad por archivo, escritores cooperantes y UTC; tres archivos siguen
siendo tres commits, con parciales explícitos. El
[Lote 12 ejecutado](REMEDIATION_SWARM100_LOTE12_2026-10-30.md) procesa
30 hallazgos únicos (29 P1 y 1 P2) en las 29 fuentes previstas: 28 FIXED y
2 MITIGATED (C0294 y C0378). Pasan 1387 pruebas y se omiten dos por límites
de plataforma/extensión nativa. Seis revisiones independientes verifican los
hashes finales. C0461 conserva OPEN como copia secundaria de C0103 sin parche;
no hereda una corrección de un archivo distinto ni incrementa el conteo único.
El [Lote 13](PLAN_SWARM100_LOTE13_2026-10-30.md) queda solo preparado:
30 hallazgos, 25 P1 y 5 P2, en 23 fuentes principales más la copia pendiente
C0461 (24 fuentes totales), sin aplicarlo ni contarla de nuevo como hallazgo único.

## Correcciones de esta ronda

### V07 — SW100-C0303

`derive` admite identidad de contenido y modalidad, permitiendo reducir las
obligaciones pero no ampliarlas. Una conclusión distinta lanza
`UnprovenDerivationError`; no se fabrica `FormalProof`, confianza 1.0 ni estado
`CANONICAL`. Se conserva una copia independiente de la justificación y el
estado de la premisa elegida.

Las premisas con hash obsoleto, estado falsificado/desacreditado o dependencia
conocida como nogood se rechazan. La identidad conserva la ascendencia causal
sin crear una dependencia consigo misma. El motor solo reutiliza una entrada
del registro si coinciden contenido comprometido, evidencia, estado y
dependencias; el rechazo no modifica registro ni DAG.

La [primera reproducción](evidence/swarm100-round3-20261028/v07-before.log)
falló en diez casos. Una
[revisión independiente](evidence/swarm100-round3-20261028/independent-review-v07.json)
detectó dos problemas adicionales en la primera corrección: sustitución por una
entrada del registro y pérdida de ascendencia. Sus
[cinco regresiones](evidence/swarm100-round3-20261028/v07-independent-before.log)
fallaron antes del ajuste. Tras corregirlos pasan las 15 regresiones V07, las
suites relacionadas y las
[17 comprobaciones independientes](evidence/swarm100-round3-20261028/independent-review-v07-followup.json).

**Límite:** esto no implementa un demostrador de lógica en lenguaje natural ni
valida la autenticidad de etiquetas `FormalProof` aportadas externamente.
`verify` sigue comprobando obligaciones según el contrato heredado; identidad
no convierte ese contrato en una prueba formal de verdad.

### Copia empaquetada de la purga — SW100-C0242

La revisión encontró el mismo defecto de traversal de C0539 en una segunda
copia del script. Se propagó a ella la corrección ya probada: ID Chromium
estricto, directorios abiertos mediante descriptores, rechazo de symlinks y
copias de preferencias. La
[evidencia de propagación](evidence/swarm100-round3-20261028/purge-copy-remediation.json)
conserva ambos hashes; las ocho regresiones de purga se ejecutan ahora sobre
ambas rutas, siempre con perfiles temporales.

## Dictámenes que cambiaron el inventario

- C0197 y C0419 se rechazan porque sus recorridos de directorios sí llegan a la
  raíz correcta. C0361 se rechaza porque Lean permite cerrar un namespace al
  llegar al final del archivo. C0414 se rechaza porque su `--dry-run` documenta
  preparación local sin push, no ausencia de mutaciones locales.
- C0338 se vincula a C0049; C0562 a C0387; C0242 a C0539. Las copias de
  dispatcher simulado y purga WAL siguen abiertas; ambas copias de purga de
  extensiones quedaron corregidas. C0264 se vincula después a C0501 en la
  corrección de ambas copias SOCINT. C0388 se vincula a C0563 tras retirar el
  reset global de ambas purgas. Hay diez duplicados contando los cinco
  pares de la segunda ronda.
- C0162 se confirma mediante una incoherencia observable entre distribuciones
  de distintos tiempos en el consumidor por lotes, bajo su contrato de un
  único proceso conjunto. El
  [contraejemplo y alcance](evidence/swarm100-round3-20261028/root-followup-C0162.json)
  no suponen que todas las llamadas individuales sean incorrectas.
- C0185 permanece parcialmente mitigado: alta y revocación con memoria/ledger
  compartidos son atómicas, pero archivos separados y `retract_attribution`
  mantienen ventanas entre transacciones. No se declara cierre completo.
- C0279 quedó inicialmente `NEEDS_VALIDATION` tras
  [dos revisiones](evidence/swarm100-round3-20261028/root-followup-C0279.json).
  El operador no conocía el contrato esperado. Se adoptó como decisión local
  reversible el uso observado: una difusión global por instancia, retenida para
  agentes tardíos; otra ronda usa una instancia nueva. Se documentó ese alcance
  en la API y se [resolvió el dictamen](evidence/swarm100-round3-20261028/root-resolution-C0279.json)
  inicialmente como `REJECTED` bajo el contrato vigente. No se implementó entrega sucesiva.
  El [AST ejecutable idéntico y siete comprobaciones aisladas](evidence/swarm100-round3-20261028/C0279-contract-validation.json)
  acreditan únicamente la aclaración histórica. Ese cierre era insuficiente:
  la [intervención posterior](REMEDIATION_AGENT_PAGER_2026-10-28.md) impone una
  segunda difusión como error y repara el despertar unicast de C0278. Ambos
  pasan ahora 14 regresiones y quedan FIXED, con los dictámenes previos preservados.

La revisión también identificó
[SW100-R3-0001](evidence/swarm100-round3-20261028/additional-findings.json):
publicación mediante una referencia Git mutable después de autorizar otro árbol.
Está confirmado estáticamente, P1 y OPEN, **fuera de los 598 IDs originales**.
Requiere invocaciones concurrentes y las demás condiciones de publicación;
no se ejecutó Git push ni el gate biométrico. La cola incluye este hallazgo
adicional sin utilizarlo para validar la alegación distinta de C0414.

## Comprobaciones y trazabilidad

- [Batería inicial del cierre V07](evidence/swarm100-round3-20261028/root-tests-final.log):
  **166 passed, 1 skipped**, once archivos de pruebas. La omisión requiere
  `strike_rs`, extensión Rust no construida en este entorno.
- [Ruff](evidence/swarm100-round3-20261028/root-ruff.log): fuentes y pruebas
  modificadas más los scripts de evidencia de esta ronda.
- [MyPy](evidence/swarm100-round3-20261028/root-mypy.log): cuatro fuentes, con
  `--follow-imports=silent`; no certifica dependencias transitivas.
- [Validador del registro](evidence/swarm100-round3-20261028/reconcile_registry.py):
  cobertura exacta 582/582, unicidad de 598 IDs, hashes vigentes, rangos y
  archivos de evidencia, estados permitidos y ausencia de ciclos de duplicados.
- [Validación inicial](evidence/swarm100-round3-20261028/validation.json): comandos,
  salidas y hashes del cierre anterior. La
  [validación posterior del pager](evidence/swarm100-pager-20261028/validation.json)
  recoge ese cambio ejecutable. La
  [validación del Lote 1](evidence/swarm100-lot1-20261028/validation.json)
  registra ese cierre. La [validación del Lote 2](evidence/swarm100-lot2-20261028/validation.json)
  recoge las fuentes y controles actuales.

Veinte revisores trabajaron sobre particiones disjuntas tras autorización
explícita. Cada dictamen conserva comprobaciones de fuente, guardas, límites,
hash y evidencias. `runtime_executed=true` en sus JSON indica una reproducción
aislada descrita por el revisor; no acredita el sistema desplegado ni ejecución
nativa. No se ejecutaron operaciones sobre datos del operador.

Los criterios V07-A, V07-B, V07-C y REG-A están cumplidos. REG-B conserva los
hashes antiguos como historia y usa la adjudicación posterior cuando hubo una
corrección durante la revisión. REG-C preserva el dictamen inicialmente incierto
de C0279 y su posterior corrección ejecutable, con fuente y evidencia; ningún
candidato se cierra mediante clasificación automática.

Sin commits, push, despliegues ni cambios de dependencias o lockfiles. Los
controles documentales se limitan al workspace; la telemetría de ghost
listeners y la configuración global quedan fuera. Se preserva el árbol sucio
preexistente. La corrección de los restantes hallazgos abiertos continúa pendiente.
