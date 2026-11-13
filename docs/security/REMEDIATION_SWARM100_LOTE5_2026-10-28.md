# Lote 5 ejecutado: ciclo de vida y transacciones del ledger — 28/10/2026

> Alcance de la distribución pública: las referencias marcadas como material no distribuido identifican evidencia o herramientas excluidas deliberadamente de este checkout. Se conservan sus rutas y los resultados históricos; esos soportes no pueden verificarse desde esta distribución.

C0428, C0429 y C0430 pasan a FIXED. La única fuente productiva modificada es
`01_KISH_ENGINE/babylon60/bft/ledger_actor.py`; C0431 permanece OPEN.
El registro reconciliado (material no distribuido: `evidence/swarm100-round3-20261028/registry.json`)
y la validación final (material no distribuido: `evidence/swarm100-lot5-20261028/validation.json`)
conservan estados, comandos, hashes y alcance.

## Reproducción y verificación

Las tres reproducciones previas (material no distribuido: `evidence/swarm100-lot5-20261028/before-tests.log`)
fallaron contra el hash inicial (material no distribuido: `evidence/swarm100-lot5-20261028/before-source-manifest.json`):
stop dejó pendiente la cola, un retry Fernet rechazó el mismo evento y el
rollback repetido impidió procesar una solicitud válida posterior. Se utilizaron
SQLite real y claves Fernet sintéticas en directorios temporales.

**536 pruebas aprobadas y 1 omitida** en la suite final relacionada, con
hashes de fuente/test idénticos antes y después. Incluye **29 regresiones
nuevas**, las suites de resiliencia/vault, equivalencia de ledgers, checkpoints,
lecturas concurrentes y regresiones de los lotes anteriores. La extensión
strike_rs se bloqueó antes de la colección; el caso dependiente de ella quedó
omitido. No se infiere una verificación de IPC nativo.

Pasan Ruff y MyPy con check-untyped-defs. La
revisión independiente (material no distribuido: `evidence/swarm100-lot5-20261028/independent-review.json`)
repite las 29 regresiones y añade diez controles, incluidos 4096 futuros
aceptados con cola llena y cancelaciones repetidas durante una transacción.
Los intercalados se controlan con barreras y plazos de fixture, sin ocultar
bloqueos con sleeps. El warmup y las ráfagas de reintentos comprueban filas,
secuencia, Lamport y cadena; no son benchmarks de hardware.

| ID | Corrección | Resultado observado |
| --- | --- | --- |
| C0428 | Estado de admisión y señal de despertar; stop drena sin cancelar al consumidor. Salidas normales/fatales asientan la cola. | Stop/append/init intercalados, dos stop, cancelación de un caller, cancelación antes de iniciar el worker, fallo de init y reinicio entre tres loops dejan todos los futuros terminales. |
| C0429 | Comparación de plaintext autenticado y metadata persistida; devuelve la fila original. | Retry cifrado conserva ciphertext, fecha, seq, UUID y hash. Clave ausente/errónea o colisión rechaza sin reescribir; la siguiente solicitud válida funciona. |
| C0430 | Un único dueño de BEGIN/COMMIT/ROLLBACK; rollback solo con transacción activa. | CHECK SQL y commit rechazado realizan un rollback y permiten continuar. Rollback no confirmado termina el worker y falla su backlog. |

## Decisiones y compatibilidad

Start rechaza un segundo worker vivo. Después de completar el cierre, recrea
cola/señales para permitir la fachada que usa sucesivos asyncio.run(). Stop
cierra admisión antes de esperar y sus callers comparten el worker; cancelar
la espera de uno no cancela SQL. Si el worker recibe cancelación durante el
procesamiento, termina esa operación antes de cerrar y falla lo que no procesó.
Cancelar un Future de respuesta tampoco impide que una escritura ya aceptada
llegue a commit.

La identidad conserva el UUID histórico. Un retry compara payload canónico,
stream, entidad, tipo, origen y taint. La fecha explícita debe coincidir; None
o cadena vacía conservan la semántica de fecha autogenerada y reutilizan la
original. Se corrigió un caso intermedio donde vacío se trataba de manera
inconsistente. No se amplía el contrato histórico de agent_id ni se migran filas.

La transacción confirma o limpia el estado; _process ya no emite otro rollback.
Un rechazo recuperable con conexión limpia no mata al worker. Un fallo de
cleanup o estado incierto sí lo termina; no se informa éxito de una operación
sin resultado confirmado. Los pendientes que nunca se procesaron fallan
explícitamente y queue.join puede terminar.

El control de alcance por AST (material no distribuido: `evidence/swarm100-lot5-20261028/scope-check.json`)
confirma esquema/triggers, UUID, expresión de fecha, hashes y cuerpos de
verificación/atestación preservados. WAL y synchronous=FULL se comprobaron en
la conexión real del worker. Los consumidores, committer, kernel de hash,
dependencias/lockfiles y la fuente propuesta del Lote 6 conservan sus hashes.

## Límites y registro

- El actor requiere un solo event loop a la vez. El reinicio secuencial entre
  loops está probado; no se certifica uso simultáneo desde threads/loops ajenos.
- Payload y clave se capturan al procesar, no como snapshot al admitir. Stop
  espera operaciones aceptadas; no es un plazo físico para I/O ni una prueba
  de durabilidad ante crash, SIGKILL o corte eléctrico.
- La idempotencia probada es la fila y su resultado. El broadcast opcional
  posterior se conserva también en retries: no se afirma entrega externa
  exactamente una vez. IPC nativo, Rekor real, hardware y ATTESTED no se ejecutan.
- get_state_attestation sigue combinando snapshots distintos: C0431 continúa
  OPEN y su cuerpo es idéntico. C0357/C0397/C0408/C0511 mantienen estado OPEN;
  solo se refrescaron sus referencias a líneas del actor que se desplazaron.
- Sin datos/claves del operador, commits, publicación o cambios globales. La
  configuración y telemetría global quedan fuera de estos controles locales.

En los 598 IDs originales quedan 551 OPEN, 39 FIXED, 4 MITIGATED y
4 NOT_APPLICABLE. Entre los 582 pendientes iniciales: 546 OPEN, 29 FIXED,
3 MITIGATED y 4 NOT_APPLICABLE. Son **545 hallazgos únicos OPEN**:
63 P1, 472 P2 y 10 P3. SW100-R3-0001 permanece FIXED fuera de esos 598 IDs.

El [Lote 6 propuesto](PLAN_SWARM100_LOTE6_2026-10-28.md) agrupa C0132/C0133
en swarm_orchestrator.py. Conserva su hash y no se ha aplicado.

Se consultaron mediante Context7 las fuentes primarias de
[aiosqlite](https://github.com/omnilib/aiosqlite/blob/main/aiosqlite/core.py)
y [Fernet](https://github.com/pyca/cryptography/blob/main/docs/fernet.rst).
No había herramientas de grafo expuestas; se usaron búsquedas acotadas.
