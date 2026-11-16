# Contrato — Lote 5

Resultado: reproducir y corregir C0428/C0429/C0430. Única fuente productiva:
01_KISH_ENGINE/babylon60/bft/ledger_actor.py. Se permiten tests/evidencia/registro
y plan del Lote 6, sin aplicarlo. Preservar cambios ajenos y los consumidores.

Ring-0: SQLite WAL/synchronous=FULL, transacciones y cierre de recursos; Ring-1:
intercalados deterministas y carga acotada con warmup; Ring-2: Git/registro;
Ring-3: documentación. Conservar UUID, esquema y formato histórico de hash.
No migrar hashes/timestamps ni corregir get_state_attestation/C0431 en este lote.

Aceptación: red/green sobre SQLite temporal y Fernet sintético; barreras de
init/stop/append, idempotencia sin reescribir ciphertext, error SQL real seguido
de append válido; futuros terminales, reinicio y fallos fatales/cancelaciones.
Pruebas existentes, Ruff/MyPy, revisión independiente, registro y controles
locales. Sin ledgers/claves del operador, Rekor/red, IPC nativo ni ATTESTED.
Bloquear strike_rs explícitamente en fixtures. No certificar crash físico o
atomicidad del worktree. El grafo no está expuesto: descubrimiento acotado.
