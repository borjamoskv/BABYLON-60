# Versiones del hash en BFTLedgerActor

El actor Python distingue los compromisos históricos de las entradas nuevas.
La versión pertenece al formato de este actor; no identifica el formato de
`CortexPersistLedger` ni permite intercambiar registros entre ambos.

## Datos existentes

Los ledgers sin tablas de versión se interpretan como versión 1. Se conserva
exactamente el sobre SHA3-256 anterior, incluidos `created_at` y los bytes
almacenados del payload. Por eso una historia V1 cifrada mantiene su
verificación de integridad sin la clave del vault.

La inicialización añade `ledger_entry_hashes` y `ledger_hash_policy` dentro de
una transacción `BEGIN IMMEDIATE`. Registra el límite y el hash final de la
historia V1, sin recalcular entradas, secuencias ni raíces. La tabla
`ledger_entries` conserva sus 15 columnas. Los marcadores de versión son
inmutables y la política impide que un escritor antiguo añada entradas V1
después del corte.

Una migración incompleta, versiones desconocidas, marcadores ausentes,
metadatos huérfanos o una degradación de versión producen rechazo. El lector
no prueba formatos alternativos hasta encontrar uno que acepte un hash.

## Entradas nuevas

V2 usa BLAKE3 con dominios explícitos para el payload canónico y el sobre de
entrada. Compromete el contenido semántico, la identidad del evento, sus
metadatos causales, el tick lógico y el hash predecesor. La fecha de observación
y los bytes aleatorios de Fernet quedan fuera de ese compromiso.

`created_at` se conserva como metadato almacenado. Variar esa fecha o volver
a cifrar el mismo payload no cambia el hash causal V2 para el mismo estado
predecesor y tick. Esto no autoriza a alterar filas históricas ni sustituye
las comprobaciones de idempotencia.

Los agregadores Merkle/MMR históricos del actor se conservan. Este cambio no
migra todos los árboles del repositorio a BLAKE3 ni acredita resistencia a
colisiones de un modelo formal abstracto.

## Claves y verificación

Para una entrada V2 cifrada, `verify_chain` necesita la clave original mediante
`CORTEX_VAULT_KEY`: descifra y comprueba que el contenido corresponde al
compromiso. Sin esa clave, o con una clave incorrecta, rechaza. Un checksum del
ciphertext no se usa como sustituto de esa autenticación.

Antes de aceptar otra escritura cifrada V2, la transacción comprueba la
continuidad con la última entrada cifrada V2. Una clave incompatible rechaza
la escritura sin consumir una secuencia; el actor puede continuar una vez
restaurada la clave correcta. Esto no implementa rotación de claves ni un
keyring. La configuración sin clave conserva la escritura sin cifrar; verificar
una cadena que contenga entradas V2 cifradas sigue requiriendo su clave.

Las entradas V1 mantienen su contrato previo. Una cadena mixta verifica cada
fila con su versión explícita y comprueba el límite de migración. La detección
de rollback de una historia completa requiere un checkpoint confiable externo.

## Comprobación reproducible

Con el entorno bloqueado del proyecto:

```sh
uv run --locked pytest tests/test_ledger_actor_hash_versions.py tests/test_ledger_vault_verify.py tests/test_ledger_cross_equivalence.py tests/test_ledger_resilience.py tests/test_swarm100_lot5_regressions.py -q
```

Las pruebas de compatibilidad construyen historias V1 anteriores al cambio y
comparan filas, secuencias, hashes y raíces antes y después de abrirlas. Cubren
append V2, reinicio, reintento, rechazo de alteraciones, fechas distintas,
cifrado aleatorio y continuidad de clave.

El código está en [ledger_actor.py](../../01_KISH_ENGINE/babylon60/bft/ledger_actor.py).
La [PR #48](https://github.com/borjamoskv/BABYLON-60/pull/48) registra el commit
revisado, los resultados de ejecución y sus límites. El contrato de tiempo
lógico está en [Ring-0](agent_contracts.md#ring-0).
