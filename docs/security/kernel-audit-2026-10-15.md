# Auditoría de seguridad del kernel — 15 octubre 2026

Auditoría local reproducible de SPSC, SQLite L0, LARSA y Rust–Lean. No certifica un despliegue ni el hardware del anfitrión.

## Segunda iteración — expiración de autorización

La revisión posterior a la integración detectó que `expires_at` se trataba como inclusivo en el executor. La autorización seguía ejecutándose cuando el reloj coincidía exactamente con el fin de vigencia. Una prueba adversarial reprodujo el efecto (`Ok(1250)`) en `now == expires_at`; el test fallaba antes de la corrección.

Se cambió el límite a exclusivo en la validación, la reserva SQLite y la comprobación posterior al despacho, y se corrigió el test IPC preexistente que codificaba el límite inclusivo. La regresión comprueba que en el instante de expiración se devuelve `AuthorizationExpired`, el recurso no cambia y el nonce no queda consumido. Evidencia local: `target/security-audit-expiry-evidence/` (ignoradas por Git, dentro del worktree de esta iteración).

Verificación de esta iteración: `cargo test --locked --offline -p babylon60_root --lib`, target privado, un job y compilación incremental desactivada: **145 pasan, 0 fallos, 1 ignorada**. El log completo es `cargo-root-lib.log`. La prueba focal pasa tras corregir el límite.

## Tercera iteración — perfil estricto de autorización COSE

Las pruebas adversariales construyeron firmas Ed25519 válidas con `kid` solo en la cabecera no protegida y con un `kid` protegido conflictivo. Antes del endurecimiento, `verify_authorization` devolvía `Ok(())`. Una firma con `crit` desconocido, tanto protegido como no protegido, llegaba hasta ejecutar el efecto (`Ok(1250)`).

`SignedAuthorization::parse` ahora exige un `kid` protegido, rechaza `kid`/`alg` no protegidos y rechaza parámetros `crit` no soportados. Las nuevas regresiones llaman al executor y verifican que el recurso no cambie ni se reserve el nonce. El contrato está detallado en `docs/security/cose-authorization-profile.md`.

Verificación: `cargo test --locked --offline -p babylon60_root --lib`: **148 pasan, 0 fallos, 1 ignorada**; `cargo test --locked --offline -p babylon60_root --test kernel_security_audit`: **3 pasan, 0 fallos, 1 ignorada**. Ambas usan target privado, un job y compilación incremental desactivada. Evidencias locales: `target/security-audit-cose-evidence/`. El chequeo global `cargo fmt --all -- --check` sigue fallando por diferencias de formato preexistentes en muchos archivos del repositorio; no se aplicó una reformateada masiva.

## Bases y aislamiento

- Captura inicial aislada: `c82af23b105fc3e646c377b1423d6bb7793f2611`.
- Reproducciones antes de corregir: `6d9ab0f49e`.
- Base de integración: `24d13112e0`. Este commit concurrente ya contenía la corrección de propiedad SPSC y cambios P-256 del usuario. Se conservaron; no se atribuyen al commit de esta auditoría.
- Worktree de reproducciones: `target/wt-security-kernel`.
- Worktree del commit independiente: `target/wt-security-commit`.
- Evidencias locales: `target/security-audit-evidence/` dentro del segundo worktree. Incluyen logs y PoCs autónomos de las implementaciones SPSC vulnerables. No contienen claves ni datos del ledger activo.

## Hallazgos reproducidos y correcciones

| Superficie | Evidencia anterior | Corrección y verificación |
|---|---|---|
| SPSC, alta: índices públicos y múltiples productores en API segura | `spsc-indices-red.log`: lectura no inicializada; `spsc-producers-red.log`: carrera de datos, ambos bajo Miri | Se conserva la implementación concurrente ya integrada: índices privados, endpoints únicos, acceso secuencial mutable y capacidad potencia de dos. Pruebas de compilación negativa, FIFO, saturación, Drop, valores no Sync y wrap del contador. Stacked Borrows y Tree Borrows. |
| SQLite, alta: autorización caducada durante espera del bloqueo | `sqlite-red.log`: una espera de 2,2 s permitía aplicar el efecto tras caducar | Reloj del anfitrión consultado de nuevo dentro de BEGIN IMMEDIATE; error antes de reservar nonce y antes del efecto. La prueba usa dos conexiones y comprueba recurso y nonce sin mutación. Una segunda lectura del reloj tras el despacho impide el efecto si la espera ocurre en esa segunda escritura; el nonce permanece consumido. |
| SQLite, media: época futura admitida, COSE malformado provoca panic | `sqlite-red.log` | Igualdad de época vigente; parseo con propagación de error. Pruebas con firmas reales y bytes malformados. |
| SQLite, defensa en profundidad: identidad e historial modificables | `sqlite-red.log` | Triggers impiden UPDATE de identidad, DELETE, retrocesos y modificación de resultados terminales. Se conserva la recuperación DISPATCHED → UNKNOWN → RESERVED para adaptadores idempotentes. |
| Persistencia fría L0, alta: WAL con NORMAL | `sqlite-red.log`: PRAGMA devuelve 1 | FULL en la conexión escritora; regresión consulta esa misma conexión. No se simula un corte físico de alimentación. |
| LARSA, alta: testigo reemplazable | `larsa-red.log` | Conflicto de hashes produce aborto irreversible; pruebas antes/después del umbral, pesos 1 y 3, saturación y nuevos votos. |
| LARSA, alta: verificadores validaban archivos distintos | `larsa-red.log`: callback sustituye el archivo entre verificaciones | Una captura privada de bytes por petición, directorio 0700 y archivo exclusivo 0600. Z3 y Lean reciben la misma captura; el cambio de la ruta original no cambia la entrada verificada. |
| Z3, media: archivo ausente se convertía en entrada vacía válida | `larsa-red.log` | Lectura fallida devuelve SystemFailure sin invocar el callback. |
| Z3, media: sufijo binario incompleto ignorado | `z3-framing-red.log`: siete tamaños aceptados | Rechazo de longitud no múltiplo de ocho; control positivo y siete sufijos con solver real. |
| Rust–Lean, alta: `#eval false` terminaba con éxito | `record-red.log` | Teorema `by decide`, warningAsError y guardia de axiomas. Compilación real admite el registro válido y rechaza el veto. |
| Rust–Lean, alta: bloques independientes aceptados como historia | `chain-red.log` | Génesis, continuidad de estados e índices crecientes se verifican antes de emitir. Control positivo de cadena conectada y negativo desconectado con Lean real. |
| Emisor Lean, alta: escape de ruta y symlinks truncaban archivos ajenos | `emitter-path-red.log`: SENTINEL sobrescrito | Nombre de salida de un componente, rechazo de symlink y publicación mediante archivo exclusivo y rename. Se conservan nombres como `--version` como rutas absolutas, nunca opciones. |

## Reproducción

Cargo usa `--locked --offline`, un target privado, un solo job, debug=0 e incremental=0. Las dependencias y lockfiles del árbol principal no se regeneraron.

```sh
cargo test --workspace --locked --offline -- --test-threads=1
cargo test --locked --offline -p babylon60_root --doc -q
BABYLON_LEAN_TEST_WORKSPACE="$PWD/proof/lean" cargo test --locked --offline -p b60-lang --lib -- --ignored
BABYLON_LEAN_TEST_WORKSPACE="$PWD/proof/lean" cargo test --locked --offline -p babylon60_root --test kernel_security_audit -- --ignored
python3 tests/test_kernel_trace_framing.py
python3 scripts/c5_quality_gates/test_lean_aot_stream.py -v
```

En `proof/lean`: `lake --wfail --no-cache build` y `lake --wfail --no-cache build babylon_aot_oracle oracle navier_stokes_oracle`.

Miri utiliza un sysroot privado: la caché global tenía metadatos incompatibles. Ejecutar `cargo +nightly miri setup --target aarch64-apple-darwin` con `MIRI_SYSROOT` privado, y las pruebas `nemesis_v3` de `adversarial_nemesis`, `test_spsc_ring_buffer` de `unit_tests`, `spsc_ownership_regressions` y `spsc_ring::tests::counter_wrap` de la biblioteca. Repetir con `-Zmiri-strict-provenance -Zmiri-symbolic-alignment-check`, añadiendo `-Zmiri-tree-borrows` en la segunda pasada.

## Límites

- LARSA es verificación heterogénea local; estos tests no demuestran PBFT distribuido, identidad de votantes ni tolerancia a un callback/binario malicioso con privilegios del propio proceso.
- FULL y los triggers protegen el contrato de esta conexión y sus transiciones. Un administrador de SQLite puede eliminar triggers; no son una frontera contra el propietario del archivo.
- Miri comprueba el modelo de memoria; no mide coherencia física ARM ni latencias de producción.
- Las pruebas Lean validan las trazas y términos ejercitados, no una biyección universal de todo el compilador.
- El gate de entropía muestrea `/dev/urandom` y analiza fuentes. Su nombre TRNG no demuestra procedencia del Secure Enclave.
- Los artefactos Swift de contrato usan una clave software y nunca Touch ID; no constituyen atestación biométrica.

## Condiciones de ejecución

La pasada paralela completa quedó esperando en `strike_rs::bft_engine::tests::test_ax_bft_extreme_swarm`, tanto dentro del sandbox como junto a otras pruebas IPC nativas. La misma prueba aislada pasó (`swarm-native.log`). La verificación completa se ejecuta secuencialmente para aislar los recursos IPC compartidos. Las pasadas interrumpidas no cuentan como resultados satisfactorios. Se conservan sus registros.

Las primeras compilaciones agotaron el disco; solo se eliminaron targets y cachés privados de esta auditoría. Los logs de Miri permanecen conservados aunque su sysroot temporal se retiró para recuperar espacio.

## Resultado verificado

- Cargo workspace completo, secuencial: **409 pruebas pasan, 0 fallos, 4 ignoradas**; salida 0. Las cuatro ignoradas se ejecutaron aparte con Lean y el fixture Swift: **4 pasan, 0 fallos**, salida 0. Incluye doctests y compilaciones negativas de propiedad SPSC.
- Miri Stacked Borrows y Tree Borrows: **13 pruebas por modelo**, todas pasan (3 NEMESIS, 2 API canónica, 7 propiedad/destrucción y 1 wrap del contador).
- Lean: 8 bibliotecas / 17 jobs y 3 ejecutables nativos compilados; las regresiones invocan Lean real para registros, cadenas y nombres de archivo que parecen opciones.
- Framing Z3: un test con control positivo y siete sufijos incompletos, pasa. Streaming AOT: cuatro tests, pasan.
- Gates de topología, symlinks IDE, presupuesto y entropía: pasan. Advertencia preexistente de variable `w` sin usar en cortex-core; no se modifica por esta auditoría.
- Registros completos: `workspace-serial-final.log`, `workspace-ignored-final.log`, `miri-final-*.log`, `commit-miri-*.log`, `lean-baseline.log`, `lean-executables.log`, `commit-framing.log`, `commit-aot.log`, `commit-topology.log`, `commit-token.log` y `commit-entropy.log`.

La integración utiliza únicamente los 15 archivos de fuentes/pruebas enumerados en `security-files.json`, más este informe. No incluye manifiestos, lockfiles ni los cambios concurrentes de skills, P-256 y SPSC ya presentes en main. La preservación se compara mediante BLAKE3 y symlinks antes/después; los resultados quedan en `integration-preservation.json` en las evidencias locales.
