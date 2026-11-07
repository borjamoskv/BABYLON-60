# Lote 5 ejecutado: ciclo de vida y transacciones del ledger — 28/10/2026

Estado: ejecutado por autorización posterior del operador; véase el
[informe de corrección](REMEDIATION_SWARM100_LOTE5_2026-10-28.md). Se agruparon
tres P1 inicialmente CONFIRMED_STATIC/OPEN de `01_KISH_ENGINE/babylon60/bft/ledger_actor.py`.
La [selección con hash y evidencia](evidence/swarm100-lot4-20261028/lot5-selection.json)
fijó la única fuente productiva editada. Se prioriza la afinidad del módulo;
no quedan P1 abiertos con reproducción previa en la cola actual.

| ID | Fallo a reproducir | Aceptación propuesta |
| --- | --- | --- |
| C0428 | stop señala terminación antes de drenar la cola y puede dejar join/futuros pendientes | Cierre acotado: las solicitudes aceptadas se completan o fallan explícitamente; append durante cierre se rechaza. |
| C0429 | El mismo evento cifrado con Fernet produce ciphertext distinto y se trata como colisión | Reintento de igual contenido conserva identidad/resultado sin comparar ciphertext aleatorio; distinto contenido conserva rechazo. |
| C0430 | Rollback repetido falla y termina el worker, dejando solicitudes posteriores pendientes | Un responsable de la transacción; un error recuperable no mata al worker ni abandona futuros. |

Primero convertir cada observación en regresión con SQLite temporal y claves
Fernet sintéticas. Programar el intercalado stop/append/worker con barreras y
plazos, sin sleeps que oculten un bloqueo. Comparar tablas, futuros, estados de
transacción y funcionamiento de una solicitud posterior al error. No abrir el
ledger del operador ni modificar datos persistentes reales.

Diseño pendiente de validar: estado explícito del ciclo de vida, frontera de
admisión/cierre, idempotencia sobre contenido canónico antes de cifrar y un solo
responsable de commit/rollback. Preservar WAL, synchronous=FULL, formato y DAG
causal aplicables; cualquier migración de esquema necesita análisis propio.
No ampliar este lote automáticamente a consensus_committer/cortex_persist.

Aceptar solo con red/green por ID, pruebas existentes relacionadas, warmup y
carga concurrente acotada sobre fixtures, revisión independiente, Ruff/MyPy,
registro reconciliado y controles documentales. No afirmar durabilidad ante
crash físico ni garantías fuera de las fronteras medidas.

La ejecución posterior se limitó a ledger_actor.py y fixtures temporales,
sin servicios, hardware o despliegues.
C0460 sigue MITIGATED; C0135/C0136 del verificador histórico v2 siguen OPEN y
necesitan un lote propio. No quedan corregidos por la evolución del generador.
