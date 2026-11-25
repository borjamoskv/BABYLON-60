# Escritores del ledger Python

Hay tres tablas. No son copias entre sí y no se fusionan en este documento.

## Escritor canónico de eventos de agente

`CortexPersistLedger` (`01_KISH_ENGINE/babylon60/bft/cortex_persist_ledger.py`) es el escritor canónico del historial de eventos de agente.

- Tabla: `cortex_ledger`.
- Un escritor a la vez: `BEGIN IMMEDIATE` y `PRAGMA synchronous=FULL` sobre SQLite WAL.
- Cada fila nueva lleva un digest SHA3-256 hexadecimal (`cortex_crypto_kernel`). Ese digest no pasa por `hash_registry.configure()`.
- Ed25519 no es una columna de la fila. Firmar la cabeza para Rekor usa `publish_rekor_anchor` y exige `BABYLON60_SIGNING_SEED`.

## Cola asíncrona, otro esquema

`BFTLedgerActor` (`ledger_actor.py`) es un único consumidor asyncio sobre otra tabla, `ledger_entries`.

- También es un solo escritor SQLite, con su propio sobre de hash.
- No replica `cortex_ledger` y no hay que leer una tabla para verificar la otra.
- El ancla Rekor es la misma función compartida y la misma exigencia de semilla.

## Mutaciones con quórum

`BFT_Ledger` / `BFT_Committer` (`consensus_ledger.py`, `consensus_committer.py`) persisten `state_log`.

- Cada mutación lleva votos Ed25519 comprobados por `consensus_validator.py`.
- El `flock` exclusivo es de este escritor, no de las otras dos tablas.
- No es el registro de eventos del agente.

## Qué no hace esta separación

Un checkpoint guardado fuera de SQLite (conteo y hash de cabeza) es el pin contra una cadena recalculada. Sin ese pin, reescribir un archivo y recomputar sus hashes no se distingue de un historial auténtico. El detalle de la versión 3 y de los sellos de observación está en el PR #79.
