# BABYLON-60/Cortex: cierre local — 30/10/2026

Estado: **aceptación local aprobada, incluida la prueba hardware**.
El candidato ejecutado fue `b9640a52ca031d1978232255d31e69efb011f9b9`.
El commit posterior de evidencia solo añade documentación y resultados; no cambia
las fuentes ni los binarios ensayados.

## Resultado observado

CLI y MCP prepararon una acción concreta. Una única aprobación mediante el gate
nativo y Touch ID produjo una firma P-256 del Secure Enclave ligada al payload
causal exacto. El broker Rust admitió un evento en un ledger temporal. Cinco
procesos observadores comprobaron ausencia de efecto durante preparación y
aprobación, un evento tras ejecución, persistencia tras reiniciar y replay
rechazado. Una comprobación separada con la tarea original confirmó que el consumo
persistido impide volver a ejecutar, independientemente del cambio de sesión MCP.

El [verificador independiente](evidence/local-core-20261030/review/hardware-final-review.json)
aprobó firma, operador, bytes almacenados, efecto y consumo: **una aprobación,
un evento, un consumo y un intento biométrico**. Hash causal SHA-256:
`14a9dcf83236795386c679ead54f1b3e4fda32f66650c877bd267908e557274e`.
La clave pública fue confirmada expresamente por el operador y fijada solo en
los procesos de aceptación. Su registro conserva hash, inodo, tamaño, modo y fecha.
No se cambiaron clave, pin global ni gate instalado.

## Conservación y equipo

La captura fijó la base `28257bd74fce31446b0350d094e9dab148a1aea7`: **1048 rutas**,
917 diferencias versionadas y 131 sin seguimiento. El checkout original avanzó
externamente a `71a4d56a059f5709882e6ee628f2bc890ad4f18a`; ninguna de las 1048
rutas capturadas perdió o cambió sus bytes durante nuestra comprobación final.
Contenido, tipo y modo fueron contrastados; ACL/xattrs no se han certificado.

La [partición revisada](evidence/local-core-20261030/partition-review.json)
seleccionó 29 archivos en ocho commits y preservó otros 1019 fuera del hito.
Se separó `work_run_checks`, perteneciente a Babylon Work. Las correcciones de
llm_attest permanecen con sus pruebas fuera de este recorrido.

| Agente | Propiedad |
| --- | --- |
| Integrador | Captura, partición, Git, perfil de sesión y evidencia transversal. |
| Ring-0 | Kernel, recuperación, gate Swift canónico y pruebas de su contrato. |
| Ring-1 | Harness fsm y modelos BabylonTrace, AX0 y NemesisWave4. |
| Ring-2 | Conexiones, consenso, ledger Cortex y memoria JSON. |
| Ring-3 | MCP/dispatch y recorrido manual CLI/MCP con observadores. |
| Verificador | Reproducción y aceptación independientes; sin editar producción. |

Los especialistas partieron del commit común `eb28fa97bb0440d59878b955222aa0617a1c236b`
en worktrees aislados, después de aprobar la partición. La
[secuencia de consolidación](evidence/local-core-20261030/consolidation.json) y los
[hashes importados](evidence/local-core-20261030/imported.json) permiten reconstruirla.

## Cambios adicionales verificados

- El ledger cierra sus conexiones propias incluso ante error de configuración;
  conserva commit/rollback y conexiones prestadas. Reproducción: 15 fallos antes,
  17 regresiones correctas después.
- El gate inspecciona únicamente una clave existente, sin interacción, firma ni
  provisión. Rust utiliza `--no-sound`.
- La aceptación hardware sale del descubrimiento ordinario de pytest. El runner
  manual verifica identidad, tarea canónica, firma, evento, consumo y reinicio;
  limita tamaño y tiempo del mensaje MCP completo. La revisión independiente
  reprodujo y corrigió tres falsos positivos/bloqueos del comprobador.
- El perfil de sesión pasa de 2432 a 1932 bytes conservando sus reglas. El bloque
  instalado ocupa como máximo 1994 bytes, dentro del límite de 2000.

## Comprobaciones

| Ámbito | Evidencia y resultado |
| --- | --- |
| Candidato integrado independiente | [135 PASS, 0 fallos, 0 skips](evidence/local-core-20261030/review/final-native-run/report.json); 27 casos nativos obligatorios ejecutados. Un test de otro servidor MCP Rust fue excluido explícitamente. |
| Recuperación Rust | [77 pruebas](evidence/local-core-20261030/ring0/run-summary.json); 15 de enclave/COSE adicionales y check/build con features Python. |
| Persistencia | [210 pruebas](evidence/local-core-20261030/ring2/manifest.json); bases temporales y variantes de fallo/rollback/recuperación. |
| Lean real | [Tres modelos y harness](evidence/local-core-20261030/ring1/status.json); prueba ignorada por defecto ejecutada expresamente y ambas CLI con nominal/negativo. |
| Onboarding | [29 pruebas](evidence/local-core-20261030/integration/onboarding-final.json): instalación aislada, idempotencia y retirada conservan preferencias ajenas. |
| Calidad | [Ruff y MyPy](evidence/local-core-20261030/integration/final-quality.json) correctos; diez fuentes comprobadas por tipos. Semántica, presupuesto y topología locales correctos. |
| Hardware | [Recibo](evidence/local-core-20261030/hardware-final/hardware-receipt.json), [proof exacto](evidence/local-core-20261030/hardware-final/signed-proof.json) y [aceptación independiente](evidence/local-core-20261030/review/hardware-final-review.json). |

Los conteos de suites se solapan y no se suman. Todos los
[criterios fijados](evidence/local-core-20261030/criteria.json) tienen evidencia.
Los [hashes del gate y biblioteca](evidence/local-core-20261030/candidate-b9640a52ca/artifacts.json)
permanecieron intactos durante las pruebas. Los procesos Python, incluidos los
hijos con `-I`, importaron desde el worktree candidato.

## Reproducción y límites

Los comandos exactos, toolchains y resultados quedan en los manifiestos enlazados.
El [lanzamiento hardware registrado](evidence/local-core-20261030/hardware-launch.json)
es evidencia del único intento realizado; no es una instrucción de reintento.
Las bases SQLite, WAL y binarios se conservan fuera de Git en la ubicación del
[registro de retención](evidence/local-core-20261030/retention.json). No se copió
material privado de la clave. El [comprobador independiente](evidence/local-core-20261030/review/independent_evidence_check.py)
permite revisar el proof y las bases conservadas sin invocar biometría.

La aceptación cubre este recorrido local en este host y candidato. No constituye
certificado remoto de atestación, prueba de corte eléctrico, aislamiento contra
kernel hostil ni sandbox universal. La memoria JSON conserva atomicidad por
archivo; no hay transacción conjunta ni autoridad retroactiva para datos
históricos. Lean verifica modelos y trazas sintéticas, no equivalencia con toda
la concurrencia Rust. Publicación, CI remota, Babylon Work y ampliaciones teóricas
siguen fuera de alcance. No se modificaron dependencias ni lockfiles. Los controles
documentales excluyen configuración global y telemetría de ghost listeners.
