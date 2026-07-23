# AGENTS.md — cortex-persist Operational Rules

> Version: 1.1.0 | Scope: Agent and contributor behavior within this repository.
> Architecture details → [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
> Security model → [docs/SECURITY_MODEL.md](docs/SECURITY_MODEL.md)
> Experimental features → [docs/EXPERIMENTAL.md](docs/EXPERIMENTAL.md)

---

## Core Rules (Non-Negotiable)

### Database Writes
- **INV_BFT_02:** Never call `sqlite3` synchronously inside an async event loop. Use `babylon60.database.core.connect` with WAL mode and `busy_timeout=5000ms`.
- **INV_BFT_03:** Every insert must include `causal_taint` (who/when/why).
- **INV_BFT_04:** Use UUID v5 idempotency keys. Reject duplicates silently, do not raise.
- **Lamport ordering:** All concurrent writes must include a `lamport_t` value. Use `MAX(lamport_t) + 1` from disk before writing.
- **Single writer:** All DB mutations go through `BFTLedgerActor`. Direct multi-threaded writes are prohibited.

### Code Quality
- **No broad except:** `except Exception:` is prohibited. Let failures propagate to Git Sentinel.
- **Strict typing:** Use type hints everywhere. `dict` without parameterization is prohibited (`dict[str, Any]` minimum).
- **No circular imports:** Module dependency graph must be a DAG.
- **DRY:** Any block repeated 3+ times must be extracted to a shared utility.
- **Recursion bound:** Recursive functions must have a hard limit of N ≤ 120 iterations.

### Commits (Git Sentinel)
- After any disk mutation (code, DB, config), commit immediately: `git add . && git commit -m "<Conventional Commit>"`.
- If pre-commit hooks block on unrelated linting, use `--no-verify` and document in the commit message.
- Never use lightweight tags for releases: `git tag -a vX.X.X -m "Release"` only.
- **Stale Git Locks:** After a system/server restart, check for and manually remove any stale `.git/*.lock` files (such as `.git/index.lock` or `.git/HEAD.lock`) that prevent write mutations in C5-REAL.

### Authorship
- All generated code carries authorship: **Borja Moskv (`borjamoskv`)**.

---

## Execution Protocol

### Reality Levels
- `C5-REAL`: Physical disk write, actual test pass, verified commit hash.
- `C4-SIM`: In-memory simulation, mocked test, unverified claim.
- Never present C4-SIM output as C5-REAL.

### Diagnostic Status (Emoji Protocol)
| Emoji | Meaning |
|:---:|:---|
| 🟢 | Operation complete — exergy gained |
| 🔍 | Reading disk / parsing AST |
| ⚙️ | Reasoning / compute-intensive step |
| 💾 | Physical write — SQLite WAL or Git commit |
| 🟡 | Warning — recoverable friction |
| 🔴 | Fatal — state purge or structural violation |

Emojis indicate hardware/ledger state only. Never use for sentiment.

### Validation Before Action
Before any high-exergy operation (mass refactor, schema migration, destructive purge), declare in visible output:
- `[Vector]`: What is being mutated
- `[Blast Radius]`: What could break
- `[Target Invariant]`: What we are preserving

---

## Filesystem Boundaries

- **Working space:** `~/10_PROJECTS/` and `20_VAULT/`
- **Read-only / immutable:** `cortex.db` central database — use sidecar DBs for mutations
- **Do not touch:** `/private/var/db`, `/System`, `Mobile Documents`, virtualization disks

---

## Concurrency Rules

- SQLite WAL + `busy_timeout=5000ms` on all connections.
- Use `asyncio.Queue` with a single writer coroutine.
- No blocking `time.sleep()` in async context — use `asyncio.sleep()`.
- Validate socket/IPC readiness with `await` before serving clients.

---

## Module Boundaries

| Module | Stability | Notes |
|:---|:---:|:---|
| `babylon60.api.*` | Beta | Public SDK surface |
| `babylon60.bft.*` | Beta | Ledger core — breaking changes require migration |
| `babylon60.database.*` | Beta | Connection pool — do not bypass |
| `babylon60.memory.*` | Alpha | Vector search — API unstable |
| `babylon60.experimental.*` | Prototype | Do not import from stable paths |

---

## Added Session Invariants (2026-07-17)

### Solidity EIP-1153 Transient Reentrancy Locks
- **INV_C5_08:** Any EIP-1153 transient reentrancy lock must read the status slot via `tload`, revert with custom errors on collision, and clear the slot via `tstore(slot, 0)` upon execution exit. Storing values without validation is prohibited.

### Python 3.12+ Testing Environment Isolation
- **INV_C5_09:** Test execution must run against `.venv` (Python 3.12) synced with `uv sync --all-extras` and executed with `BypassSandbox: true` to bypass dynamic loading limitations.

### Memory Vault Session Synchronizer
- **INV_C5_15:** The memory vault session synchronizer script `scripts/sync_vault_uuids.py` must exist, be executable, and maintain deterministic synchronization between unconsolidated brain conversation logs and `~/.gemini/config/.cortex/memory_vault/`.

### PyO3 Forward ABI Compatibility (Anti-Deadlock)
- **Ω30 · PYO3 FORWARD ABI INVARIANT:** Queda estrictamente prohibido ejecutar validaciones `cargo check` o compilaciones `cargo build` en repositorios mixtos Rust/Python sin la declaración explícita de `PYO3_USE_ABI3_FORWARD_COMPATIBILITY=1`. La omisión causa necrosis de compilación al resolver contra intérpretes 3.14+ o sandboxes de `uv`, considerándose Anergía clase C4-SIM.

### BFT Deterministic Float Exclusion
- **INV_C5_18:** Floating-point numbers (`float`) are strictly prohibited in BFT consensus payloads, state mutation timestamps, and cryptographic serialization due to IEEE 754 non-determinism. Timestamps must use `int` or `INTEGER` columns, and `canonicalize_cbor` must recursively enforce float exclusion.

### Root Cause Epistemology (Causal Stratification)
- **Ω138 · CAUSAL STRATIFICATION INVARIANT (TOPOLOGY ≺ MECHANISM ≺ ETIOLOGY ≺ REMEDIATION):** La confianza pertenece a cada proposición individual, no al diagnóstico completo ($C(\phi_i) \neq C(\phi_j)$). El diagnóstico se estructura en cuatro estratos independientes: **Topología** (¿Dónde ocurre la observación?), **Mecanismo** (¿Cuál es la cadena causal inmediata observada?), **Etiología** (¿Cuál es la inferencia sobre por qué se alcanzó ese estado?), y **Remediación** (¿Qué acción candidata mitiga el fallo?). Queda estrictamente prohibido usar el éxito de una remediación como demostración incondicional de una etiología, o colapsar la confianza de un mecanismo observado sobre una etiología inferida.
- **Ω152 · DISCRIMINATORY MEASUREMENT INVARIANT (TRANSITION RULE):** C4/C5 clasifica el tipo de evidencia (Inferencia vs Observación), no la realidad del fenómeno. Una medición $M$ solo promueve una hipótesis $H$ si reduce el conjunto de hipótesis compatibles ($|H_{t+1}| < |H_t|$) o reduce la incertidumbre ($H(M) > 0$). Si $M$ solo añade detalle descriptivo sin alterar las probabilidades relativas de la matriz de hipótesis ($P(M|H_i) \approx P(M|H_j)$), el test se refuta por falta de poder discriminatorio. La etiología permanece en estrato C4-SIM hasta que una medición discriminatoria muta la confianza física a C5-REAL.
- **Ω153 · EVIDENCE SEPARATION INVARIANT:** Las proposiciones deben separar estrictamente la evidencia observacional bruta (ej. el símbolo terminal en un backtrace) de su interpretación topológica (ej. la región de fallo localizada). Ninguna interpretación puede sustituir a la evidencia bruta en el ledger.
- **Ω154 · CONFIDENCE TRACEABILITY INVARIANT:** Todo valor de confianza declarado en el ledger (ej. `high`, `low`) debe estar anclado explícitamente a artefactos observacionales concretos (`supported_by`). La confianza sin soporte rastreable es estocástica (C4-SIM) y debe ser purgada.
- **Ω155 · EPISTEMIC MONOTONICITY INVARIANT:** La evolución del estado epistemológico es monótona bajo la evidencia. Toda transición regresiva (ej. degradar de C5 a C4) exige un registro físico (evento de revocación) que documente la medida contradictoria que invalidó la confianza previa. El ledger es una máquina de estados, no una colección de opiniones mutables.
- **Ω156 · PHYSICAL POSTERIOR INVARIANT:** La distribución posterior de hipótesis no es un string descriptivo, sino un objeto físico (distribución probabilística) cuyas probabilidades relativas suman 1.0. Todo experimento altera esta distribución ($P_{antes} \to P_{después}$); si la distribución no muta, la medición careció de exergía ($H(M) = 0$).
- **Ω157 · A PRIORI DISCRIMINATORY POWER INVARIANT:** Toda medición propuesta debe declarar su ganancia de información esperada ($EIG$) *antes* de la ejecución, y registrar su ganancia real ($AIG$) *después*. Esto purga los tests estocásticos que prometen mucho pero discriminan poco.
- **Ω158 · EVIDENCE LINEAGE INVARIANT (SYNTHESIS):** Ningún incremento de confianza, cambio de estrato, o modificación de la distribución posterior es válido sin trazabilidad. Todo avance epistémico debe trazar ininterrumpidamente hasta uno o más artefactos observacionales mediante una cadena de soporte explícita.
