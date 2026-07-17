# AUDITORÍA CENTURIA — Teorema-Robinson-Moskv
`REALITY_LEVEL: C5-REAL` · Fecha: 2026-07-17 · HEAD: `5e5ba15c3` · Operador: MOSKV-1 APEX
Medición directa sobre árbol staged (132 ficheros primarios) + lectura completa de vectores críticos.

█▄█ █▄█ █▄█ █▄█ █▄█ █▄█ █▄█ █▄█ █▄█ █▄█

## 0. MÉTODO Y ATESTACIÓN (Cero Teatro Verde)

La formación CENTURIA (96 legionarios + TRIARII) fue **escrita y despachada**, pero su corrida **no persistió**: los cortes de MCP/clasificador durante la sesión abortaron el workflow sin dejar journal en disco. No se finge lo contrario.

Este dispatch se funda en algo más duro que 96 opiniones: **sondas forenses deterministas** (`grep`/AST/lectura) ejecutadas por el operador directamente sobre los 132 ficheros materializados en el contenedor, con **lectura íntegra** de los vectores críticos (`shadow_router.py`, `claude_bft_interceptor.rs`, `MaxRouterAnchor.sol`, `SecureHook.sol`, `consensus_ledger.py`, `Babylon.lean`). Cada hallazgo se marca **C5-REAL** (evidencia literal en disco) o **C4-SIM** (inferido). Toda evidencia citada es verbatim con `file:line`.

## 1. SUPERFICIE REAL

| Métrica | Valor | Nota |
| :--- | :--- | :--- |
| Código primario | **132 ficheros · ~16.8k LOC** | 70 py · 8 sol · 6 fs · 3 rs · 1 clj · 1 lean + config/docs |
| Lenguajes | 6 | Python (núcleo), Solidity, Rust, F#, Clojure, Lean 4 |
| Masa excluida | `experimental/cortex_legacy` 1.8G · `strike_rs/target` · `anvil_yung/out` · `fable_modules` | Artefacto/legacy/vendor — fuera del alcance |
| Módulos `babylon60` reales | `analysis, bft, cli, compiler, core` | **NO existen** `database`, `api`, `memory` (ver CENT-03) |

## 2. TABLA DE HALLAZGOS (orden de severidad)

| ID | Sev | Vector | Ubicación | Regla / Realidad |
| :--- | :---: | :--- | :--- | :--- |
| CENT-01 | 🔴 CRÍTICO | Clave HMAC simétrica hardcodeada | `strike_rs/src/bin/claude_bft_interceptor.rs:106` | Secreto en fuente · C5-REAL |
| CENT-02 | 🟠 ALTO | Commitments/hashes FALSOS en "proof-of-route" | `babylon60/core/shadow_router.py:43,44,52,54,55` | C4-SIM disfrazado de C5-REAL |
| CENT-03 | 🟠 ALTO | Invariante INV_BFT_02 apunta a módulo inexistente | `AGENTS.md` ↔ `babylon60/` | Doctrina inejecutable · C5-REAL |
| CENT-04 | 🟠 ALTO | `SecureHook` enseña footgun `tx.origin` + lock cosmético | `contracts/test/SecureHook.sol:35,42` | Control de seguridad falso · C5-REAL |
| CENT-05 | 🟠 ALTO | Claim "verificación formal del sistema" sin vínculo mecánico | `proof/lean/Babylon.lean` ↔ `README/ETHOS` | Inflación de claim · C5-REAL |
| CENT-06 | 🟡 MEDIO | `sqlite3.connect` directo en BFT core + `except Exception` | `babylon60/bft/consensus_ledger.py:19,66,75` | Viola AGENTS.md · C5-REAL |
| CENT-07 | 🟡 MEDIO | Telemetría fabricada en core estable | `babylon60/core/shadow_router.py:29-45` | C4-SIM bajo schema "execution" |
| CENT-08 | 🟡 MEDIO | Panics por `unwrap()` en el nodo BFT | `strike_rs/src/bin/centuria_1000_bft.rs:112-114,206,213,216,251` | Robustez · C5-REAL |
| CENT-09 | 🟡 MEDIO | Auto-commits que saltan hooks **y** CI | `scripts/objectives_manager.py:31` · `compile_arsenal_1000.py:66` · `scratch/transduce_*` | `--no-verify`+`[skip ci]` · C5-REAL |
| CENT-10 | 🟡 MEDIO | MD5 + inconsistencia de hash entre superficies | `attest_character_count.py:37` · `llm-attest.py` vs `core/crypto.py` vs `strike_rs` | Viola BLAKE3/SHA3 · C5-REAL |
| CENT-11 | 🟡 MEDIO | `except:` desnudo en la herramienta de auditoría | `scratch/hyper_audit.py:165,220` (+18 broad-except totales) | Viola AGENTS.md · C5-REAL |
| CENT-12 | 🔵 BAJO | Rutas absolutas hardcodeadas | 19 ocurrencias / 11 ficheros (`~/…`) | Portabilidad/opsec · C5-REAL |
| CENT-13 | 🔵 BAJO | `transferOwnership` de un solo paso | `contracts/MaxRouterAnchor.sol:91` | Sin Ownable2Step · C5-REAL |
| CENT-14 | 🔵 BAJO | `.replace("sha256:","")` no-op sobre hash SHA3 | `babylon60/bft/consensus_ledger.py:33` | Confusión sha256/sha3 · C5-REAL |
| CENT-15 | 🔵 BAJO | Pragmas Solidity flotantes `^0.8.x` | todos los `.sol` | Sin pin de compilador |
| CENT-16 | 🟠 ALTO | Termodinámica de repo (auditoría previa, **aún en pie**) | pack 738 MiB · 499 artefactos tracked · `.gitignore` sin `**/target`, `**/.lake` | Higiene git · C5-REAL |

## 3. VECTOR CRIPTOGRÁFICO (el más caliente)

**CENT-01 · Clave maestra quemada.** `claude_bft_interceptor.rs:106`:
```rust
let key = hmac::Key::new(hmac::HMAC_SHA256, b"CORTEX_BFT_KEY_2026_MASTER_LEDGER");
```
La clave simétrica que autentica el Master Ledger está **en texto plano en el binario y en la historia de Git**. Cualquiera con lectura del repo forja MACs válidos → el consenso BFT deja de distinguir mutaciones legítimas de forjadas. La clave debe considerarse **comprometida de forma irreversible** (rotarla no basta; hay que expulsarla de la historia y cambiar el dominio de claves).

**CENT-02 · "Proof-of-route" que no prueba.** `shadow_router.py` emite un recibo con campos que *parecen* enlaces criptográficos pero son ruido:
```python
"response_commitment": f"hmac-sha256:{secrets.token_hex(32)}",   # L43
"provider_receipt_hash": f"sha256:{secrets.token_hex(32)}",       # L44
"request_commitment": f"hmac-sha256:{secrets.token_hex(32)}",     # L52
"policy_hash": f"sha256:{secrets.token_hex(32)}",                 # L54
"candidate_set_hash": f"sha256:{secrets.token_hex(32)}",          # L55
```
Ninguno deriva del payload — son tokens aleatorios con prefijo cosmético. Un verificador que confíe en `policy_hash` cree que la política está ligada criptográficamente: **no lo está**. Esto es exactamente el C4-SIM-vestido-de-C5-REAL que tu ETHOS existe para aniquilar. *(Matiz honesto: `decision_hash`/`exec_hash` en L72/L92 **sí** son SHA3-256 reales del payload y se firman con Ed25519 — el binding del recibo externo es real; los campos internos son el fraude.)*

**CENT-07 · Telemetría inventada.** `_execute_route` (L27-45) hace `await asyncio.sleep(0.05/0.1)` y devuelve constantes fijas (`input_tokens:100`, `cost_microusd:4200`, ttft calculado del sleep) bajo el schema `proof-of-route/execution/v0.2`. Métrica simulada presentada como ejecución real, en `babylon60.core` (ruta estable).

**CENT-10 · Babel de hashes.** `attest_character_count.py:37` usa `hashlib.md5` para `receipt_id`; `llm-attest.py` usa SHA-256; `core/crypto.py` usa SHA3-256; `strike_rs` usa BLAKE3. Cuatro primitivas para atestar "lo mismo" → los taints no interoperan y MD5 viola la doctrina explícita.

## 4. VECTOR CONSENSO / CONCURRENCIA

**CENT-06** · `consensus_ledger.py:19`: `sqlite3.connect(db_path, isolation_level=None, timeout=5.0)` — conexión directa, **sin `PRAGMA journal_mode=WAL` explícito**, con `except Exception` absorbiendo fallos (L66, L75). AGENTS.md **INV_BFT_02** exige `babylon60.database.core.connect` con WAL — módulo que **no existe** (CENT-03).

**CENT-08** · `centuria_1000_bft.rs` disemina `.unwrap()`/`.expect()` sobre `join()`, `lock()` y `try_unwrap()`. Un worker en pánico o un `Mutex` envenenado **aborta el nodo entero** — lo contrario a tolerancia bizantina. `unsafe`: **0** (correcto).

## 5. VECTOR CONTRATOS

**CENT-04 · `SecureHook.sol` — el ejemplo "seguro" no lo es:**
- L28 `beforeSwap` acredita `balances[msg.sender]` (correcto) pero L35 `afterSwap` acredita `balances[tx.origin] += 50` — **asimetría real** y footgun de phishing clásico.
- L40-45 `executeAction`: `assembly { tstore(0,1) }` etiquetado "Transient Reentrancy Lock" — **escribe el lock y retorna, nunca hace `tload`+`require` ni lo limpia**. Un candado que no cierra nada (seguridad cosmética).

**Positivo — `MaxRouterAnchor.sol`:** guarda de replay (`require(!anchoredRoots[merkleRoot])`, L64), `onlyAttester`, checks `address(0)`, **sin llamadas externas** → sin superficie de reentrancia. Sólido. Único defecto: `transferOwnership` de un paso (CENT-13).

## 6. VECTOR PRUEBA FORMAL

`proof/lean/Babylon.lean`: **6 teoremas, cero `sorry`, cero `axiom`** — el modelo es honesto (probado C5-REAL). Pero los teoremas envuelven `Nat.le_refl/le_trans/le_antisymm`: modelan el orden de Lamport **sin vínculo mecánico** con `bft/ledger_actor.py`. El README/ETHOS declaran "validación matemática formal / fusión Lean estable" con confianza de sistema. **La evidencia soporta C5 para el MODELO, no para el SISTEMA** (CENT-05).

## 7. VECTOR DOCTRINA-VS-REALIDAD

- **CENT-03**: `AGENTS.md` (Module Boundaries) gobierna `babylon60.database.*`, `.api.*`, `.memory.*`. En el árbol solo existen `analysis/bft/cli/compiler/core`. El invariante nuclear apunta a un módulo fantasma → **inejecutable**.
- **CENT-09**: `objectives_manager.py:31` (`git commit --no-verify`) y múltiples scripts con `[skip ci]` → mutaciones autónomas entran **sin lint, sin test, sin CI**.
- **CENT-11**: 18 `except Exception`/`except:` en el árbol; los dos desnudos están en `hyper_audit.py` — la propia herramienta de auditoría se traga todo error.

## 8. LO QUE ESTÁ SANO (atestación de equilibrio)

- Prueba Lean honesta (0 `sorry`/`axiom`).
- `MaxRouterAnchor`: replay-guard + control de acceso + sin reentrancia.
- Recibos externos: `decision_hash`/`exec_hash` SHA3-256 reales + firma Ed25519.
- `core/crypto.py`: SHA3-256 elegido explícitamente (resistencia a extensión de longitud), CBOR canónico determinista.
- Secretos de usuario: vía entorno (`os.environ`/`getenv`), GitHub Actions usa `secrets.*` correctamente. **Sin** `.env`/`.pem` tracked (la única clave en fuente es la HMAC de Rust, CENT-01).
- CI amplia: 10 workflows (`ci`, `codeql`, `verify_lean`, `verify_ledger`, `conformance`, `hotstuff_bench`…).

## 9. ROADMAP DE REMEDIACIÓN (orden causal de impacto)

**P0 — Integridad/Seguridad (colapso inmediato):**
1. **CENT-01** — Externalizar la clave HMAC (env/KMS), **rotar el dominio de claves** y expulsar el literal de la historia (`git filter-repo`). Tratar `CORTEX_BFT_KEY_2026_MASTER_LEDGER` como quemada.
2. **CENT-02 / CENT-07** — Ligar cada `*_commitment`/`*_hash` al payload (`hash_sha3_256(canonicalize_cbor(...))`) o eliminarlos; marcar la telemetría como fixture. Es tu prime directive: C4-SIM no puede vestir de C5-REAL.

**P1 — Invariantes de consenso:**
3. **CENT-03 / CENT-06** — Crear `babylon60.database.core.connect` (WAL + `busy_timeout=5000`) y enrutar `consensus_ledger` por ahí; propagar excepciones.
4. **CENT-08** — Sustituir `unwrap()` por manejo de `Result`/`PoisonError` en el nodo BFT.
5. **CENT-10** — Unificar en SHA3-256 (o BLAKE3) todo el arco de atestación; retirar MD5.

**P2 — Contratos / Gobernanza / Prueba:**
6. **CENT-04** — `msg.sender` consistente en `SecureHook`; implementar el lock real (`tload`+`require`+limpieza) o retirar el ejemplo.
7. **CENT-05** — Probar en Lean los invariantes reales del `BFTLedgerActor` (monotonía `lamport_t`, hash-chain) contra una spec compartida, o rebajar el claim del README.
8. **CENT-09** — Prohibir `[skip ci]` en cambios de código; `--no-verify` solo con causa registrada.

**P3 — Higiene / Termodinámica:**
9. **CENT-11..15** — Purga de broad-except, rutas absolutas, pragmas fijos, `Ownable2Step`, `.replace` no-op.
10. **CENT-16** — `git rm -r --cached` sobre los 499 artefactos; ampliar `.gitignore` con `**/target/`, `**/.lake/`, `*.npz`, `*.db`; externalizar masa a LFS/DVC.

## 10. VEREDICTO

Sin secretos de **usuario** expuestos; capa de recibos (SHA3+Ed25519) y prueba Lean **honestas**; CI amplia. Las fracturas reales son dos y de tu propia jurisdicción:

1. **Integridad criptográfica** — una clave simétrica maestra quemada en el binario (CENT-01).
2. **Veracidad C5-REAL** — commitments y telemetría **simulados vestidos de prueba** (CENT-02, CENT-07), más una doctrina que manda sobre un módulo que no existe (CENT-03).

Por tu ley — *Cero Anergía, Cero Teatro Verde* — **CENT-01 y CENT-02 exigen colapso ahora**. El resto es exergía recuperable: P0+P1 caben en una sesión.

---

## 11. ITERACIÓN ULTRATHINK — DELTA v2 (verificación adversarial del corazón)

Lectura íntegra de `bft/ledger_actor.py` (295 L), `core/crypto.py`, `bft/master_ledger_queue.py` y `proof/lean/Babylon.lean`. El ciclo **corrige dos errores de mi propio v1** y añade tres hallazgos duros que el `grep` no podía ver.

### 11.1 Autocorrecciones (C4-SIM en mi dispatch v1)

| Corrección | v1 decía | Realidad verificada (C5-REAL) |
| :--- | :--- | :--- |
| **COR-1** | "sqlite3 directo **en el BFT core**" | El `BFTLedgerActor` (corazón real) usa **`aiosqlite` async + `PRAGMA WAL` + `synchronous=FULL` + `busy_timeout=5000`** (L180-185) — **ejemplar**. El violador es `consensus_ledger.py`, un módulo **secundario/legacy**, no el corazón. CENT-06 se re-acota a ese fichero. |
| **COR-2** | (positivo) "recibos con **Ed25519 reales**" | **FALSO.** `crypto.py:28` → `Ed25519Signer.sign()` devuelve `"ed25519:mock_signature_for_" + payload_hash[:8]`. La firma es un **stub**. Retiro el crédito y lo elevo a hallazgo NEW-A. |

### 11.2 Hallazgos NUEVOS (del corazón)

| ID | Sev | Vector | Ubicación | Evidencia |
| :--- | :---: | :--- | :--- | :--- |
| NEW-A | 🟠 ALTO | Capa de firma = **mock** | `core/crypto.py:26-28` | `return "ed25519:mock_signature_for_" + payload_hash[:8]` — la no-repudiación del "God-State Engine" es teatro; `shadow_router` firma recibos con esto (L82,102). |
| NEW-B | 🔴 CRÍTICO | **`verify_chain` roto bajo cifrado** | `bft/ledger_actor.py:154-172` vs `226-249` | El INSERT hashea el payload **cifrado** (`stored_payload`, L241); `verify_chain` hashea el payload **descifrado** (L157-163). Con `CORTEX_VAULT_KEY` activo, `entry_hash != computed_hash` **siempre** → la verificación de la cadena **devuelve `False` para todo ledger cifrado**. El verificador de integridad no puede validar el estado que protege. |
| NEW-C | 🟡 MEDIO | **`os.kill(SIGKILL)` como manejo de error** | `ledger_actor.py:193,201` · `master_ledger_queue.py:32` | Ante cualquier excepción del writer, mata el **proceso entero** con `SIGKILL` — sin `finally`, sin checkpoint WAL, futures pendientes colgados. Fail-fast convertido en auto-DoS. |
| NEW-D | 🟡 MEDIO | **Hash-chain del ledger usa SHA-256, no SHA3** | `ledger_actor.py:51` | `hashlib.sha256(...)` en la superficie MÁS crítica, ignorando `crypto.hash_sha3_256` que el propio repo eligió "por resistencia a extensión de longitud". El core no importa su propio módulo cripto. Agrava CENT-10. |
| NEW-E | 🟡 MEDIO | **Dos escritores únicos rivales** | `bft/ledger_actor.py` (`BFTLedgerActor`) vs `bft/master_ledger_queue.py` (`MasterLedgerQueue`) | AGENTS.md: "toda mutación va por `BFTLedgerActor`". Existe un **segundo** writer con durabilidad distinta (`synchronous=NORMAL` vs `FULL`). Si ambos tocan la misma DB → viola escritor-único. |

### 11.3 Endurecimientos

- **CENT-05 (Lean) — confirmado y afilado.** Los 6 "teoremas" son **alias del core de Lean**: `causal_refl := Nat.le_refl`, `causal_trans := Nat.le_trans`, `causal_antisymm := Nat.le_antisymm`, y `ledger_seq_monotone` es `causal_trans` **renombrado** (L48-50). Honestos (0 `sorry`) pero **casi vacuos** como verificación de sistema. El `-- Isomorfo al lamport_t del BFTLedgerActor` (L15) es un **comentario en prosa**, sin vínculo mecánico — aunque el Python **sí** impone la monotonía (`lamport_t ... UNIQUE CHECK (lamport_t > 0)` L207, `MAX(lamport_t)+1` L226, `if lamport_t <= last_lamport: return False` L150). La brecha es **puenteable pero no puenteada**.
- **Positivos REALES (C5-REAL, endurecidos).** El `BFTLedgerActor` es ingeniería sólida: tabla append-only con **triggers de inmutabilidad** (`RAISE(ABORT,'immutable master ledger')` en UPDATE/DELETE, L209-214), idempotencia **UUIDv5** (`uuid.uuid5(NAMESPACE_UUID, idempotent_key)` L271 + `ON CONFLICT DO NOTHING`), `INV_BFT_03` **enforced** (`raise ValueError` si `cortex_taint` vacío, L262), `BEGIN IMMEDIATE` atómico. El corazón honra sus invariantes.

### 11.4 Veredicto v2 (recolapsado)

El escaneo de superficie subvaloró **el corazón** (mucho mejor de lo que implicaba v1) y sobrevaloró **la cripto de borde** (firmas mock, hash-chain SHA-256, `verify_chain` roto bajo cifrado). Reordenando P0 con la evidencia del corazón:

1. **NEW-B (🔴 nuevo CRÍTICO)** — `verify_chain` no valida ledgers cifrados. Unificar qué se hashea (texto plano en ambos caminos, o cifrado en ambos). Sin esto, la "prueba de integridad" es inoperante justo cuando hay secretos.
2. **CENT-01** — clave HMAC quemada (sin cambios, sigue siendo el otro crítico).
3. **NEW-A + CENT-02 + NEW-D** — colapsar el teatro criptográfico: firmas reales Ed25519, commitments ligados al payload, y **un solo** hash (SHA3-256) en todo el arco, empezando por el hash-chain del ledger.

Recuento v2: **2 críticos** (CENT-01, NEW-B) · **7 altos** · el resto medio/bajo. El sistema tiene un núcleo de ledger honesto envuelto en una piel criptográfica simulada — exactamente la inversión que tu doctrina C5-REAL prohíbe.

`[SIGNED] MOSKV-1 APEX · v2 · método: lectura íntegra del corazón + autorrefutación · un C4-SIM propio detectado y retractado`
