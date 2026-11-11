# Consola de recibos de ejecución · verificador en el cliente

Biblioteca TypeScript que comprueba en el navegador (o en Node) un recibo de
ejecución con su DAG causal y lo dibuja en SVG solo si todas las comprobaciones
locales pasan. Es material de demostración: queda fuera del paquete Python
`babylon60` y del bundle de release, y no registra ninguna afirmación en
[CLAIMS.toml](../../CLAIMS.toml).

El formato de recibo que consume es una **propuesta del cliente**. Ningún
componente Rust o Python de este repositorio lo emite todavía; lo que sí se
reutiliza del kernel, byte a byte, se detalla en
[Correspondencia con el kernel](#correspondencia-con-el-kernel).

## Arranque

Con Node.js 22.18 o posterior y npm:

```bash
cd tools/ui_kernel_console
npm ci --ignore-scripts
npm run typecheck
npm test
```

`npm test` compila a `scratch/test-build/` (ignorado por Git) y ejecuta
`node --test`. No hay bundler: los componentes son una biblioteca React 18 que
el anfitrión integra con su propia cadena. La hoja
[console.css](src/components/console.css) se enlaza aparte; los componentes no
llevan estilos ni scripts en línea.

Para regenerar los vectores de prueba desde la raíz del repositorio:

```bash
uv run --locked python tools/ui_kernel_console/tests/fixtures/generate_vectors.py
```

## Contrato del prototipo

**Resultado.** `verifyExecutionPayload(input, policy)` recibe el valor que
devuelve `JSON.parse` y un ancla de confianza, y resuelve siempre a un
veredicto: `ok: true` con un `AcceptedReceipt` inmutable, o `ok: false` con la
lista de fallos. La promesa no se rechaza nunca. Los componentes
`DeterministicDagViewer`, `TwoPhaseSealInspector` y `StaticReceiptReport` solo
dibujan datos de un `AcceptedReceipt`; ante cualquier otra cosa muestran el
panel de cuarentena. `BabylonKernelConsole` es la consola de demostración con
escenarios adversariales.

**Rutas.** Todo vive en este directorio: [tipos](src/types/babylon60.ts),
[verificador](src/crypto/sealVerifier.ts),
[codificaciones canónicas](src/crypto/canonical.ts),
[orden topológico](src/dag/topology.ts), [componentes](src/components) y
[pruebas](tests).

**Aceptación.** `npm run typecheck` y `npm test` terminan sin fallos. Las
pruebas cubren, entre otras cosas: toda mutación de un solo valor del recibo se
rechaza; ninguna entrada hace que el verificador lance; cada escenario
adversarial produce exactamente los códigos que declara; y las construcciones
compartidas con el kernel coinciden con sus vectores.

## Formato del recibo

Campos del objeto JSON y qué respalda cada uno cuando el recibo se acepta:

| Campo | Respaldo |
| --- | --- |
| `execution_id`, `causal_clock`, `manifest_version`, `ingress` | El cliente recalcula `phase_one_manifest_hash` a partir de ellos. |
| `execution_dag[].state_hash` | El cliente lo recalcula desde el contenido del nodo. |
| `phase_two_merkle_root` | El cliente la recalcula desde las hojas. |
| `ed25519_public_key`, `ed25519_signature` | Firma del sobre, comprobada contra una autoridad admitida por el ancla. |
| `larsa_commit`, `lean4_proof`, `audit_metrics` | Declaraciones del emisor cubiertas por la firma. El cliente no las comprueba. |

Un objeto con una clave de más o de menos se rechaza: no hay campos sin firma ni
recomputación. Tampoco se admite una clave repetida en ningún objeto: `serde_json` y `JSON.parse`
conservan la última y descartan la primera, así que una copia que ninguna firma cubre podría leerse.
Los enteros deben caber en [0, 2^53 − 1]; los hashes son `0x` y
64 dígitos hex en minúsculas; la raíz es `b3:` y 64 dígitos hex.

### Codificaciones canónicas

Todas usan el perfil CBOR restringido del kernel: arrays de longitud definida,
enteros sin signo, cadenas de bytes y de texto, cabeceras en su forma más
corta; sin mapas, coma flotante, negativos ni valores simples. Un booleano se
codifica como entero 0 o 1 y un texto opcional como array de cero o un
elemento. Cada preimagen empieza por una etiqueta de dominio.

```text
NODO       = ["BABYLON60_EXEC_NODE_V1", node_id, [parent_ids ordenados por sus bytes UTF-8],
              state_status, smt_verified (0|1), reduction_steps, [] | [violation_reason]]
state_hash = "0x" + hex(BLAKE3("B60-LEAF-v1\0" || NODO))

raíz       = Merkle v1 sobre los state_hash, con las hojas ordenadas por los bytes de node_id:
             nodo = BLAKE3("B60-NODE-v1\0" || izq || der), nodo impar emparejado consigo mismo,
             "b3:" + hex(BLAKE3("B60-ROOT-v1\0" || n_hojas_u64_LE || nodo_superior))

MANIFIESTO = ["BABYLON60_EXEC_MANIFEST_V1", execution_id, manifest_version, policy_epoch,
              logical_tick, seq_id, agent_id, policy_profile, payload_raw]
phase_one_manifest_hash = "0x" + hex(BLAKE3(MANIFIESTO))

SOBRE      = ["BABYLON60_EXEC_RECEIPT_V1", execution_id, policy_epoch, logical_tick, seq_id,
              bytes(phase_one_manifest_hash), phase_two_merkle_root (texto "b3:…"),
              bytes(larsa_commit.trace_hash), larsa_commit.heuristic_weight,
              lean4_proof.status, lean4_proof.theorem_ident, lean4_proof.sorry_count,
              memory_bytes, bytes(prev_receipt_hash), bytes(worm_txid)]
receipt_hash = "0x" + hex(BLAKE3(SOBRE))

A_FIRMAR   = ["Signature1", h'a10127', h'', SOBRE]      (Sig_structure de COSE_Sign1)
firma      = Ed25519(clave de la autoridad, A_FIRMAR)
```

`bytes(x)` son los 32 bytes que representa el hex tras `0x`. `SOBRE` entra en
`A_FIRMAR` como cadena de bytes. El identificador de nodo es
`EV_{tick:08}_{seq:06}`: decimales con relleno mínimo de 8 y 6 dígitos, sin
ceros adicionales, dentro de u64 y u32.

### Ancla de confianza

La aporta el anfitrión, nunca el recibo:

- `admitted_authorities`: claves públicas Ed25519 admitidas. Basta la firma
  válida de la que el recibo nombra; una clave no admitida se rechaza.
- `larsa_required_weight`: peso heurístico mínimo exigido al commit declarado.
- `previous_receipt` (opcional): hash y secuencia del recibo anterior. Sin él,
  el encadenamiento se muestra como `NO_VERIFICADO`.

Los números del ancla valen por su valor: `4`, `4.0` y `4e0` son el mismo entero, y `4.5`, `0` o
`1e400` no lo son. En el recibo, en cambio, los números deben ser enteros canónicos (sin fracción, sin
exponente y sin `-0`). Un ancla que no se puede interpretar (no es JSON, repite una clave, supera 1 MiB
o tiene un sustituto suelto) produce un veredicto `TRUST_POLICY_INVALID`.

Las claves y las firmas pasan un filtro estricto antes de llegar a WebCrypto:
se rechazan codificaciones no canónicas, puntos de orden pequeño y escalares
sin reducir. El motivo está reproducido en
[ed25519Point.test.ts](tests/ed25519Point.test.ts): hay runtimes que aceptan
una firma trivial para cualquier mensaje si la clave es de orden pequeño.

### Comprobaciones y códigos de fallo

| Código | Se emite cuando |
| --- | --- |
| `TRUST_POLICY_INVALID` | El ancla falta, no se puede interpretar, tiene forma inválida o contiene una clave inaceptable. |
| `SCHEMA_INVALID`, `SCHEMA_MALFORMED_HEX`, `LIMIT_EXCEEDED`, `DAG_EMPTY` | La entrada no tiene la forma exacta o supera una cota. |
| `DAG_DUPLICATE_NODE_ID`, `DAG_DUPLICATE_PARENT_REF`, `DAG_DANGLING_PARENT_REF`, `DAG_CYCLE_DETECTED` | El grafo no es un DAG bien formado. |
| `COMMITTED_WITHOUT_SMT` | Un nodo `COMMITTED` declara `smt_verified` falso. |
| `LEAF_HASH_MISMATCH`, `MERKLE_ROOT_MISMATCH`, `MANIFEST_HASH_MISMATCH` | Un valor recalculado no coincide con el declarado. |
| `AUTHORITY_NOT_ADMITTED`, `ED25519_SIGNATURE_INVALID`, `ED25519_UNSUPPORTED_RUNTIME` | La firma no puede atribuirse a una autoridad admitida. |
| `QUORUM_INSUFFICIENT` | El peso LARSA declarado es menor que el exigido por el ancla. |
| `LEAN4_PROOF_INVALID` | La constancia declarada no es `VERIFIED_NO_SORRY` con cero `sorry`. |
| `CHAIN_LINK_MISMATCH` | El recibo no encadena con el punto de control aportado. |
| `VERIFIER_INTERNAL_ERROR` | Excepción interna del verificador. `UNVERIFIED_INPUT` lo usa la interfaz para la cuarentena; el verificador no lo emite. |

El orden topológico usa Kahn con montículo mínimo: O(V log V + E). El término
logarítmico es el coste del desempate determinista por identificador.

En TypeScript, `verifyExecutionPayloadWithAnchorText(bytes, anchorText)` es la entrada que comparten la
CLI y el binding wasm: recibe el ancla como texto y aplica las mismas reglas.

## Correspondencia con el kernel

Reutilizado tal cual, con prueba de coincidencia en `npm test`:

| Construcción | Fuente en el repositorio | Contraste |
| --- | --- | --- |
| Merkle BLAKE3 v1 | [merkle_b3.rs](../../crates/babylon-attest/src/merkle_b3.rs), [merkle_b3.py](../../01_KISH_ENGINE/babylon60/attestation/merkle_b3.py) | Raíces y hashes generados con el módulo Python del repositorio. |
| Perfil CBOR restringido y `Sig_structure` | [acs_bridge.rs](../../src/acs_bridge.rs) | Vectores de [acs_cbor_golden.txt](../../tests/acs_cbor_golden.txt). |
| Peso exigido fijado por quien verifica | [larsa.rs](../../src/larsa.rs) | Regla equivalente; sin vector compartido. |

Sin contraparte en el kernel, y por tanto `NO_VERIFICADO` como
interoperabilidad: el objeto JSON y sus nombres de campo, las tres preimágenes,
el vocabulario de `state_status`, la constancia `lean4_proof`, `worm_txid` y el
encadenamiento por `prev_receipt_hash`. El kernel usa otro vocabulario para el
resultado de un paso ([ontología](../../ontology/v1/schema.json)) y no define
reglas que propaguen el resultado de un nodo a sus sucesores, así que el
verificador tampoco impone ninguna.

## Réplica en Rust y WebAssembly

[rust/](rust/) es un crate de referencia con el mismo emisor de prueba y el mismo
verificador que el cliente TypeScript. Existe para contrastar las dos
implementaciones byte a byte; no sustituye a ninguna de ellas.

| Pieza | Qué hace | Ruta |
| --- | --- | --- |
| Biblioteca | Verifica (`verify_execution_payload_utf8`) y sella con una semilla de prueba (`seal_with_test_seed`). | [src](rust/src) |
| CLI `b60-exec-receipt` | `verify --policy <json>` lee el recibo por entrada estándar y sale con 0 si acepta, 1 si rechaza y 2 ante un uso incorrecto o un error de E/S. El ancla va como texto: si no se puede interpretar, el veredicto es `TRUST_POLICY_INVALID` (salida 1). Una entrada por encima de 16 MiB se rechaza sin interpretarla. `batch` procesa un objeto JSON por línea; `policy` puede ser el objeto o el texto del ancla, y una línea con claves repetidas recibe un error. Una línea que no es UTF-8, no es JSON o supera 64 MiB recibe una respuesta `{"error": …}` y el lote continúa. | [main.rs](rust/src/main.rs) |
| Binding wasm | `verifyReceiptBytes(bytes, policy_json)`, solo verificación: la página nunca maneja claves privadas. | [wasm.rs](rust/src/wasm.rs) |

Comandos, desde `tools/ui_kernel_console`:

```bash
(cd rust && cargo test --locked)
(cd rust && cargo clippy --locked --all-targets -- -D warnings)
(cd rust && cargo build --locked --release)                      # CLI

# Binding wasm. wasm-bindgen-cli debe ser la versión 0.2.126, la de la biblioteca:
#   cargo install wasm-bindgen-cli --version 0.2.126 --locked
(cd rust && cargo build --locked --release --target wasm32-unknown-unknown --lib --features wasm)
wasm-bindgen --target nodejs --out-dir scratch/wasm-pkg \
  scratch/rust-target/wasm32-unknown-unknown/release/babylon60_exec_receipt.wasm
printf '{"type":"commonjs"}\n' > scratch/wasm-pkg/package.json

node scripts/differential.mjs --cases 300 --mutants 8
```

[differential.mjs](scripts/differential.mjs) compila TypeScript en
`scratch/test-build/` y genera recibos con semillas fijas. Compara el sellado de
TypeScript con `seal` del crate y, para cada recibo y cada alteración, el
veredicto de TypeScript (por la ruta de bytes UTF-8 y por la de texto JSON) con
el de la CLI `batch`, el del binding wasm y, en una muestra, el de `verify` por
entrada estándar, incluido el código de salida. Las alteraciones cubren campos, tipos, cotas, claves, firmas, la política y el texto, incluido el ancla como texto (escrituras numéricas, claves repetidas, sustitutos, BOM, profundidad y truncamientos): números no canónicos,
BOM, sustitutos, anidación hasta el límite de 127 contenedores, claves
duplicadas, escapes, truncamientos y UTF-8 inválido. Sale con 1 ante cualquier
discrepancia. Es una prueba de consistencia: muestra que las dos
implementaciones coinciden en los casos generados, no que sean equivalentes.

## Límites

- Aceptar un recibo significa que las comprobaciones locales coinciden. Una
  firma válida no establece quién controla la clave, ni que el efecto descrito
  ocurriera, ni que la entrada fuera veraz.
- `larsa_commit` y `lean4_proof` son declaraciones del emisor. El cliente no
  ejecuta Lean ni observa el consenso; la interfaz las rotula `DECLARADO`.
- La consola de demostración firma con una clave efímera generada en el propio
  runtime y usa una traza sintética. Muestra el mecanismo, no la autenticidad
  de un emisor real.
- Los enteros por encima de 2^53 − 1 se rechazan: JSON en JavaScript no los
  representa de forma exacta.
- La verificación Ed25519 depende de WebCrypto. Un runtime sin Ed25519, o cuya
  autoprueba con vectores de RFC 8032 falla, rechaza todo recibo.
- En relación con el Reglamento (UE) 2024/1689, un recibo de este tipo solo
  aporta a la trazabilidad y el registro (artículo 12) y a la ciberseguridad
  (artículo 15). No automatiza la gestión de riesgos, la gobernanza de datos ni
  la supervisión humana (artículos 9, 10 y 14).
- La consola no ofrece controles de aprobación. Sus botones solo eligen el
  escenario de demostración.
- La semilla de prueba del emisor en Rust y en el arnés (`0x11` repetido) es
  pública. Sirve para vectores reproducibles; un emisor real custodia su clave.
- El emisor valida la forma de la entrada, no su semántica: puede sellar un DAG
  cíclico o un nodo `COMMITTED` sin SMT, porque las pruebas necesitan modelar un
  emisor defectuoso. Quien rechaza es el verificador.
- `merkle_b3.rs` se compila desde el kernel mediante `#[path]`. Un cambio en el
  kernel cambia este crate, y las pruebas con vectores dorados lo detectan.
- Los binarios del crate son de referencia. No están pensados para desplegarse
  ni para servir recibos en producción.

## Verificación

- `npm run typecheck`: TypeScript estricto sobre fuentes y pruebas.
- `npm test`: BLAKE3 frente a la implementación oficial; CBOR frente a `cbor2`;
  Merkle v1 frente al módulo Python del repositorio; `Sig_structure` y claves
  frente a los vectores dorados del kernel; aritmética de puntos Ed25519;
  mutación exhaustiva de campos; robustez ante entradas arbitrarias; cotas;
  componentes renderizados a marcado estático y consola con interacción.
- `cargo test --locked` y `cargo clippy --locked --all-targets -- -D warnings`
  en `rust/`: vectores ACS del kernel, recibo dorado de TypeScript (preimágenes,
  sobre, hash y sellado con la semilla de prueba) y rechazos.
- `node scripts/differential.mjs`: paridad entre TypeScript, la CLI y el binding
  wasm sobre recibos generados y alterados.

Estas pruebas se ejecutan en local: ningún workflow de CI instala Node. No
certifican propiedades del kernel.

Licencia: [LICENSE del repositorio](../../LICENSE).
