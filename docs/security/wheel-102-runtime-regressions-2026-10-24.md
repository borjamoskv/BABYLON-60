# Regresiones del runtime de la wheel 1.0.2

Contraste local del 24 de octubre de 2026, Europe/Madrid. Referencia histórica:
`babylon60-1.0.2-py3-none-any.whl`, SHA-256
`44277399fe60ebe93779dc45510233e9787d5405eafcdd7e95378d1020b3b86f`.
La corrección se aplica al checkout candidato 5.0.1. No reemplaza la wheel
publicada ni constituye una publicación, firma de release o certificación BFT.

## Alcance y contraste previo

Contrato: reproducir los fallos de autorización, auditoría, truncación, JCS e
imports; corregir los activos; conservar cambios ajenos y dependencias; aceptar
solo mediante regresiones y controles locales. Los tests emplean claves Ed25519
software reales y bases temporales, sin efectos protegidos sobre datos productivos.

| Hallazgo histórico | Estado del checkout antes del cambio | Tratamiento |
| --- | --- | --- |
| `f=-1`, booleanos y otros presupuestos inválidos | Ya rechazados por `BFT_Validator`; además exige población suficiente y quórum N-f | Se conserva y ejecuta su suite existente. |
| Una clave registrada bajo varios nombres cuenta varias veces | Presente | El registro se copia y exige claves públicas distintas, comparadas como bytes. |
| Votos válidos reutilizables con otro autor, fecha o traza | Presente | Los votos v1 vinculan todo el sobre de mutación y el presupuesto `f`. |
| Payload y hash reescritos; metadatos alterados; inserción SQL sin votos | Los cuatro casos reproducidos devolvían `True` | Se persiste el certificado de votos y se verifica contra el registro de claves suministrado por el operador. |
| Borrado de todas las filas de `state_log` | Reproducido: `True` | Se comprueban secuencia, marca máxima de SQLite y checkpoint opcional externo. |
| Truncación del final de `BFTLedgerActor` tras eliminar el trigger | Presente | Misma comprobación de marca máxima y comparación opcional con checkpoint externo. Se conserva el encadenamiento existente. |
| JCS: cero negativo, floats enteros, Unicode, NaN e Infinity | Presente en las dos CLI de atestación | Serializador compartido con orden UTF-16 y formato numérico ECMAScript; rechazo de valores no finitos, surrogates aislados, claves repetidas y enteros fuera del rango seguro. |
| `babylon60.types` importa un módulo inexistente | Ya corregido mediante reexports desde `c5_types.algebraic` | Regresión de identidad y uso de los tipos, sin alterar la implementación. |
| Import opcional de VF2 sin `networkx` | Ese módulo de la wheel ya no existe en este checkout | No se añade una dependencia obligatoria. |
| Ausencia de `__all__` en la raíz | No acredita ausencia de API | No requiere una corrección del runtime. |

## Protocolo de votos y datos históricos

[StateMutation](../../01_KISH_ENGINE/babylon60/bft/consensus_committer.py)
expone `signing_hash(f)`. Los votantes deben firmar ese digest, que incluye un
identificador de esquema, payload, autor, timestamp declarado, traza y `f`.
No se obtiene la fecha del reloj del anfitrión para construir ese mensaje.
El campo heredado `signature` no sustituye al certificado de votos del comité.
La fachada toma una copia del payload y los votos antes de verificar y persistir.

```python
votes = {node: signer.sign(mutation.signing_hash(f)) for node, signer in signers.items()}
ledger.invoke_subagent(mutation, f, votes)
checkpoint = ledger.get_checkpoint()
```

La migración añade columnas de prueba sin modificar las filas anteriores. Una
fila antigua sin certificado verificable hace que `audit_integrity()` devuelva
`False`; nunca se fabrican votos para presentarla como autenticada. Las firmas
históricas calculadas solamente sobre el payload deben sustituirse por nuevos
votos sobre el mensaje v1. Esto cambia el protocolo de admisión deliberadamente.
El replay idempotente exige el mismo sobre y certificado; una fila existente
con otros metadatos o una prueba alterada se rechaza. El timestamp cero negativo
se normaliza antes de firmar para conservar su valor al persistirlo en SQLite.

## Checkpoints y límite de confianza

[LedgerCheckpoint](../../01_KISH_ENGINE/babylon60/bft/integrity.py) contiene
el número de entradas y el hash de cabecera. Puede obtenerse de una lectura
verificada y conservarse en un dominio independiente de la base y sus backups.
Los dos ledgers permiten comprobarlo al reabrir:

```python
ledger.audit_integrity(expected_checkpoint=checkpoint)
await actor.verify_chain(expected_checkpoint=actor_checkpoint)
```

Sin referencia externa, la marca `sqlite_sequence` detecta los borrados probados,
pero quien puede reescribir toda la base puede restaurar también esa marca. La
comparación con un checkpoint retenido fuera de ese dominio detecta ese rollback.
No se presenta un checkpoint leído de la misma base modificable como autoridad
independiente. Los lectores comprueban filas y marca máxima en una sola transacción.

## Evidencia y aceptación

Antes de corregir, las nuevas pruebas JCS fallaron con los ejemplos de cero
negativo, float entero y notación decimal. La reproducción local adicional del
ledger aceptó payload/hash reescritos, metadatos alterados, borrado completo e
inserción sin votos. Después de corregir, la suite dirigida pasa 127 casos:

```sh
uv run --locked pytest tests/test_wheel_runtime_regressions.py tests/test_jcs_regressions.py tests/test_audit_consensus_quorum.py tests/test_itera2_invariants.py tests/test_ledger_resilience.py tests/test_ledger_vault_verify.py tests/test_ledger_cross_equivalence.py tests/test_master_ledger_queue.py tests/test_cortex_crypto_kernel.py tests/test_crypto_canonical.py -q
```

Incluye reapertura de bases, migración sin pruebas inventadas, idempotencia,
firmas modificadas, presupuestos inválidos, corrupción, truncación, rollback con
marca interna restaurada y pin externo, y recibos JCS con firmas reales. El
estrés acotado realiza 65 commits de consenso y 49 del actor, con calentamiento
previo y lectores concurrentes. No mide rendimiento ni simula un corte eléctrico.

Los vectores normativos de [RFC 8785](https://www.rfc-editor.org/rfc/rfc8785.html)
se complementaron con 10.000 doubles finitos de semilla fija, comparados contra
`JSON.stringify` de Node: cero divergencias observadas. Es una prueba acotada,
no una demostración universal del serializador. Los enteros Python fuera de
`[-(2**53-1), 2**53-1]` requieren representación como cadena.

Ruff y MyPy se ejecutan sobre los archivos afectados. También se comprueban
enlaces, semántica, presupuesto y topología locales; se omiten explícitamente
configuración global y telemetría Ghost Listeners. Los tests no certifican
aislamiento del sistema operativo, presencia humana, consenso distribuido ni
resistencia a una restauración conjunta de la base y su referencia externa.

## Iteración del 26 de octubre de 2026

Se revisaron arranque, recuperación, pertenencia de las transacciones y formatos
de evidencia de las correcciones anteriores. El alcance sigue siendo local, sin
subagentes, publicación ni modificación de dependencias o lockfiles. Las pruebas
utilizan archivos temporales, conexiones SQLite reales y claves software reales.

| Reproducción | Corrección |
| --- | --- |
| Una ruta `.lock` simbólica truncaba su destino; un lock existente también perdía su contenido. | Apertura con `os.open`, `O_NOFOLLOW`, sin `O_TRUNC`, y comprobación del descriptor como archivo regular. |
| Dos rutas relativas desde distintos directorios, o una relativa y otra absoluta, podían tomar locks distintos para la misma base centralizada. | El committer resuelve primero la ruta usada por `database.core` y sitúa el lock junto a esa base. |
| Un error real de esquema mantenía el lock mientras el traceback conservaba el constructor fallido. | Cierre explícito y liberación del lock en el fallo de inicialización, sin depender del recolector. |
| Auditar dentro de una transacción abierta revertía silenciosamente trabajo del llamador; un commit podía devolver éxito antes de que ese llamador confirmase la transacción. | Auditoría, checkpoints y commits rechazan la transacción externa antes de modificarla. La aplicación conserva su responsabilidad de commit o rollback. |
| Se aceptaban bytes extra tras un objeto CBOR y mapas de longitud indefinida equivalentes a los originales. | El payload y el certificado deben coincidir byte a byte con su recodificación CBOR canónica antes de verificar votos. |
| Se aceptaban caracteres ajenos a Base64url, padding extra y pad bits no canónicos. Una firma válida con prefijo y sin padding podía fallar. | Decodificación estricta, longitudes Ed25519 exactas, comprobación de recodificación y eliminación del prefijo antes de calcular padding. |
| Una prueba Merkle de una hoja aceptaba índice 99; un índice fuera del árbol podía compartir los bits examinados con otro válido. | Se exige un índice entero no negativo dentro de la altura de la prueba y hashes hexadecimales canónicos de 32 bytes. |

Antes de corregir fallaron 35 de los 41 nuevos casos; seis controles ya pasaban.
Después pasan los 42 casos de las dos suites nuevas, incluido un ensayo adicional
de calentamiento, ocho rechazos de contención y readquisición del lock. La suite
combinada con las regresiones anteriores pasa **169 tests**:

```sh
uv run --locked pytest tests/test_consensus_recovery_regressions.py tests/test_attest_proof_regressions.py tests/test_wheel_runtime_regressions.py tests/test_jcs_regressions.py tests/test_audit_consensus_quorum.py tests/test_itera2_invariants.py tests/test_ledger_resilience.py tests/test_ledger_vault_verify.py tests/test_ledger_cross_equivalence.py tests/test_master_ledger_queue.py tests/test_cortex_crypto_kernel.py tests/test_crypto_canonical.py -q
```

Ruff y MyPy pasan para los archivos afectados. Se comprueban de nuevo los enlaces
de este informe y los tres controles documentales locales. La configuración global
y la telemetría Ghost Listeners permanecen explícitamente fuera del alcance.

Los ensayos de locks usan `fcntl` real y se omiten en plataformas sin ese módulo;
no acreditan soporte Windows ni aislamiento frente a un proceso con capacidad
para sustituir todo el directorio de la base. La exigencia del checkpoint externo
para detectar rollback completo permanece. Rechazar una codificación malformada
no demuestra un ataque contra Ed25519 ni resuelve por sí solo la confianza en la
identidad del emisor.

Context7 respondió que su cuota mensual estaba agotada. Las APIs se contrastaron
con la documentación oficial de Python para
[descriptores y flags de apertura](https://docs.python.org/3.12/library/os.html)
y [decodificación Base64 estricta](https://docs.python.org/3.10/library/base64.html).

## Segunda iteración del 26 de octubre de 2026

Se mantuvo el alcance local y sin subagentes ni publicación. Esta pasada revisó
el resultado físico del commit y el cierre de recursos cuando una operación
falla. Se preservaron los cambios anteriores y ajenos; no se tocaron dependencias
ni lockfiles. Rutas afectadas: `bft/consensus_committer.py`, `database/core.py` y
dos nuevas suites de regresión. Aceptación: reproducción negativa, rechazo con
estado previo conservado, conexión reutilizable y regresiones anteriores válidas.

| Fallo reproducido | Cambio y comprobación |
| --- | --- |
| Un trigger `RAISE(IGNORE)` suprimía la inserción pero el committer devolvía `True`. Triggers AFTER podían borrar o modificar la fila aceptada. | `BEGIN IMMEDIATE`, comprobación de número de filas afectadas, rowid y contenido completo antes de COMMIT. Una diferencia provoca rollback. Se prueban siete variantes de supresión o alteración. |
| Un trigger con `RAISE(FAIL)` podía dejar cambios parciales y confundirse con una repetición válida al capturar indiscriminadamente `IntegrityError`. | La idempotencia se comprueba antes del INSERT bajo el mismo bloqueo transaccional. Los errores del INSERT se propagan y se revierte la transacción, incluidas las modificaciones parciales del trigger probado. |
| Un cierre desde otro hilo era rechazado por SQLite, pero liberaba el lock, permitiendo un segundo escritor mientras la conexión original seguía abierta. | El lock se libera después de cerrar SQLite con éxito. Una prueba con un hilo real confirma que el rechazo conserva el lock y permite seguir usando al propietario. |
| Si fallaba un PRAGMA durante la configuración, los helpers síncrono y asíncrono dejaban conexiones abiertas. | Ambos cierran la conexión antes de propagar el error. La inyección de fallos usa el authorizer de SQLite sobre conexiones reales, en cada uno de los cuatro PRAGMAs; no sustituye la base por respuestas ficticias. |
| `2**53` y `2**53+1` como timestamps enteros producían el mismo digest al redondear a REAL; un entero enorme causaba `OverflowError`. | Se rechazan enteros que no sobreviven exactamente a la conversión a binary64 y los desbordamientos se comunican como `ValueError`. Los floats finitos y enteros representables conservan su protocolo. |

Los 25 casos iniciales dieron **20 fallos y 5 controles correctos** antes de
corregir. Después pasan esos casos y un ensayo adicional de 16 ciclos de rechazo,
rollback, commit válido e idempotencia, precedidos de un commit de calentamiento.
La suite acumulada pasa **195 tests**:

```sh
uv run --locked pytest tests/test_consensus_atomic_commit.py tests/test_database_config_cleanup.py tests/test_consensus_recovery_regressions.py tests/test_attest_proof_regressions.py tests/test_wheel_runtime_regressions.py tests/test_jcs_regressions.py tests/test_audit_consensus_quorum.py tests/test_itera2_invariants.py tests/test_ledger_resilience.py tests/test_ledger_vault_verify.py tests/test_ledger_cross_equivalence.py tests/test_master_ledger_queue.py tests/test_cortex_crypto_kernel.py tests/test_crypto_canonical.py -q
```

Las pruebas verifican también, con otra conexión SQLite, la fila persistida y la
marca de secuencia después del rechazo. Ruff, MyPy, enlaces del informe y los tres
controles documentales locales pasan. Se excluyen configuración global y
telemetría Ghost Listeners. Los límites de checkpoint externo y de los locks POSIX
de la iteración previa permanecen; estas pruebas no acreditan confinamiento frente
a cualquier cambio de esquema ni un corte eléctrico.

La semántica de los fallos parciales se contrastó con la documentación primaria de
[triggers](https://www.sqlite.org/lang_createtrigger.html) y
[transacciones de SQLite](https://www.sqlite.org/lang_transaction.html). El criterio
de aceptación es la observación reproducida del estado de la base, además del
valor de retorno de la API.

## Tercera iteración del 26 de octubre de 2026

Contrato: revisar el commit atómico, la propiedad del lock y la recuperación,
reproducir fallos antes de editar y conservar la evidencia previa. Se modifican
el committer y una nueva suite; se preservan cambios ajenos, dependencias y
lockfiles. Todo se mantiene local, sin subagentes ni publicación. Aceptación:
rechazo con estado previo intacto, lock exclusivo conservado y recuperación
observable después de la muerte del proceso.

| Reproducción | Corrección |
| --- | --- |
| Un trigger conservaba la nueva fila aprobada, pero borraba o cambiaba otra; el commit devolvía `True`. También aceptaba cambios en otra tabla, en `sqlite_sequence` o una inserción adicional sin votos. | Además del contenido y rowid, se exige exactamente un cambio de datos en la conexión durante el INSERT. Los seis casos probados provocan rollback y conservan el checkpoint anterior. |
| Si fallaba el rollback, la conexión seguía abierta con cambios pendientes y el error original quedaba oculto. | Se cierra la conexión antes de liberar el lock; el error de rollback se encadena al fallo original. Las pruebas deniegan realmente ROLLBACK mediante el authorizer de SQLite y verifican desde una conexión nueva que no quedan los efectos pendientes. |
| Tras `fork`, el hijo podía usar la conexión heredada y su cierre ejecutaba `LOCK_UN` sobre el lock compartido con el padre. | Se registra el PID propietario. El acceso a la conexión heredada se rechaza; el hijo solo cierra su copia del descriptor, sin desbloquear al padre ni invocar métodos de SQLite. |

Antes del parche, los once casos nuevos produjeron **9 fallos y 2 controles
correctos**. Los controles que ya pasaban matan un proceso real con SIGKILL en
dos puntos: con una inserción pendiente y después del commit. Se comprueba la
señal de salida, la recuperación de filas y secuencia, el lock liberado por el SO
y el comportamiento del replay. No se simula ni se certifica un corte eléctrico.

Después pasan los doce casos, incluido un ensayo adicional de ocho ciclos de
rechazo por efectos secundarios y commits válidos tras un calentamiento previo.
El contador de cambios se toma de nuevo en cada operación, porque incluye también
cambios que luego fueron revertidos. La suite acumulada pasa **207 tests**:

```sh
uv run --locked pytest tests/test_consensus_fault_recovery.py tests/test_consensus_atomic_commit.py tests/test_database_config_cleanup.py tests/test_consensus_recovery_regressions.py tests/test_attest_proof_regressions.py tests/test_wheel_runtime_regressions.py tests/test_jcs_regressions.py tests/test_audit_consensus_quorum.py tests/test_itera2_invariants.py tests/test_ledger_resilience.py tests/test_ledger_vault_verify.py tests/test_ledger_cross_equivalence.py tests/test_master_ledger_queue.py tests/test_cortex_crypto_kernel.py tests/test_crypto_canonical.py -q
```

Ruff, MyPy y los controles documentales locales pasan. Se siguen excluyendo
configuración global y telemetría Ghost Listeners. Los hijos deben cerrar las
copias heredadas y abrir conexiones nuevas cuando el lock esté disponible; esta
regresión prueba ese cierre explícito, no una reutilización segura de SQLite
entre procesos. La protección completa frente a rollback sigue requiriendo una
referencia independiente. Tampoco se acredita confinamiento frente a código
arbitrario del anfitrión o a toda modificación posible del esquema.

Fuentes primarias consultadas: [contador de cambios de SQLite](https://www.sqlite.org/c3ref/total_changes.html)
y [semántica de los descriptores de flock](https://man7.org/linux/man-pages/man2/flock.2.html).
Los casos de fork se ejecutan en un intérprete aislado y los de SIGKILL sobre
bases temporales con claves de software, sin afectar bases del operador.
