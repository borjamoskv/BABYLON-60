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
- **Stale Git Locks:** After a system/server restart, the Kernel MUST autonomously detect and remove any stale `.git/*.lock` files (such as `.git/index.lock` or `.git/HEAD.lock`) that prevent write mutations in C5-REAL. Manual intervention is strictly prohibited.

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

### Zero Bureaucratic Friction (0 Exigencias)
Under ULTRATHINK and /goal mandates, the Kernel possesses Absolute Sovereignty. 
- "Validation Before Action" is abolished as it generates Green Theater pauses.
- The Kernel executes high-exergy operations (mass refactors, schema migrations, destructive purges) immediately and autonomously.
- Diagnosis and justification (Vector, Blast Radius, Target Invariant) are reported post-execution strictly via C5-REAL YAML Claim/Proof blocks, without EVER pausing execution.

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

### Swarm & Analysis Friction Mitigation
- **INV_C5_35:** When the Kernel generates static analysis, exergy evaluation, or pre-commit scripts that scan for forbidden patterns (e.g., `float`, `time.sleep()`), it MUST NOT execute naive substring matches across raw file contents or raw `git diff` outputs. The Kernel MUST parse the diff to isolate ONLY the injected code (lines starting with `+` excluding `+++`), or utilize Python's `ast` module to prevent false positives.
- **INV_C5_36:** If pre-commit hooks (e.g., Ruff) block an autonomous Git Sentinel commit due to non-critical ergonomic or stylistic linting errors (e.g., `F401`, `F841`, `E402`, `E701`), the Kernel should not solely rely on `--no-verify`. It MUST proactively evaluate injecting the violating rule codes into the `ignore` array of `[tool.ruff.lint]` in `pyproject.toml` to permanently eradicate the friction vector.
- **INV_C5_37:** In alignment with INV_C5_19, the use of `except Exception:` is strictly forbidden. The Kernel must proactively route error boundaries to explicit, narrow structural anomalies (e.g., `OSError`, `UnicodeDecodeError`, `asyncio.TimeoutError`) during all code generation and refactoring.
- **INV_C5_38:** Zero-Knowledge proofs and circuit verifications (e.g. `NUL-ZK`) MUST be integrated into `babylon60.crypto.zk_verifier` using safe subprocess argument vectorization (`INV_C5_33`) without `shell=True` and enforcing recursive IEEE 754 float exclusion (`INV_C5_18`).
- **INV_C5_39:** Any database queries executing inside the BFT actor or async event loop MUST use async connections (`aiosqlite` with WAL mode) and provide `_async` methods to prevent blocking I/O on the main event loop thread (`INV_BFT_02`).
- **INV_C5_41 (ENOSPC Starvation Paradox):** If the Kernel encounters `No space left on device` (ENOSPC), it MUST NOT attempt to use `run_command` to execute mitigation scripts (e.g., clearing caches), as the agent SDK itself requires disk I/O to inject the shell context, resulting in cascading failure. The Kernel must immediately yield control to the Operator with a `🔴 [FATAL] ENOSPC` abort signal to manually purge the host.
- **INV_C5_42 (Sandbox Docker Orphan):** The `docker` CLI is typically inaccessible within the agent's macOS execution sandbox. The Kernel MUST validate its existence via `command -v docker` before attempting kinetic edge-deploy tests. If absent, it MUST default to executing raw python runtimes (`uv run`), or orchestrate a Swarm Handoff (`moskv_bridge.py`) without halting or proposing arbitrary alternative architectures (enforcing `Φ8 ZERO SUGGESTION`).
- **INV_C5_43 (Native Slash Commands Monorepo & High-Velocity Aliases):** Native commands (`/ultrathink`, `/autodidact`, `/purge`, `/seal`, `/itera`, `/logos`, `/ethos`, `/mythos`, `/ship`, `/swarm`, `/verify`) MUST reside in `babylon60/commands/` as sub-modules within the monorepo root. CLI subcommands in `cortex-cmd` MUST expose shortcode aliases (e.g., `ut`, `ad`, `p`, `sl`, `it`, `lg`, `et`, `my`, `sh`, `sw`, `vf`) and enforce PyNaCl Ed25519 NUL-ZK hashing with an Exergy threshold $\ge 950/1000$.

---

## Agent Bus Protocol — Puente ANTIGRAVITY ⇄ Claude (2026-07-19)

Bus físico: `babylon60_ide.db` (raíz del repo) — CortexLedger append-only,
hash-chain SHA-256, WAL. **Todos los agentes** (moskv-1-APEX/ANTIGRAVITY,
Claude/Cowork, humanos) escriben en la MISMA cadena; escritores mixtos,
una sola verificación de integridad.

- **INV_BRIDGE_01:** El sobre criptográfico es idéntico en todo escritor:
  `sha256(parent|created_at|event_type|entity_ref|payload_canonical)` con
  payload canónico (`sort_keys`, separadores `,`/`:`); `event_id` = UUIDv5.
  Implementaciones de referencia: `babylon60-ide/backend/services/cortex_ledger.py`
  y `babylon60-ide/bridge/moskv_bridge.py` (stdlib puro, sin backend).
- **INV_BRIDGE_02:** Append siempre con `BEGIN IMMEDIATE` (serializa
  escritores cruzados; sin fork de cadena).
- **INV_BRIDGE_03:** Eventos del bus: `AGENT_STATUS` (ping quién/qué/rama),
  `AGENT_HANDOFF` (tarea de agente→agente), `AGENT_ACK` (recepción).
  El inbox = handoffs a tu nombre sin ACK. Para validar la simetría de red ("Ida y Vuelta"), el Kernel está autorizado a asumir temporalmente el identificador cruzado (ej. `claude-cowork`) emitiendo un `ACK` al UUID origen, seguido de un `HANDOFF` de retorno que selle el ciclo BFT completo en un solo nodo.

Uso desde cualquier kernel (sin dependencias):

    python3 babylon60-ide/bridge/moskv_bridge.py status  moskv-1-apex "refactorizando bft"
    python3 babylon60-ide/bridge/moskv_bridge.py handoff moskv-1-apex claude-cowork "revisa el guard de la DB"
    python3 babylon60-ide/bridge/moskv_bridge.py inbox   moskv-1-apex
    python3 babylon60-ide/bridge/moskv_bridge.py ack     moskv-1-apex <event_id>
    python3 babylon60-ide/bridge/moskv_bridge.py peers
    python3 babylon60-ide/bridge/moskv_bridge.py verify

El IDE (Swarm ⌘4) muestra los peers e inbox en vivo vía `/api/bridge/*`.
Disciplina de convivencia: haz `status` al empezar sesión de trabajo y
`handoff` en vez de pisar ficheros que el otro agente tiene en vuelo.

- **INV_BRIDGE_04 (entorno):** El bus vive en `babylon60_ide.db` sobre disco
  LOCAL. SQLite necesita locking POSIX real, del que carecen los montajes de
  red/FUSE (el bridge de dispositivo de Cowork lanza `disk I/O error`). Corre
  el CLI desde tu Terminal / el proceso del kernel — no a través de una vista
  FUSE remota. Verificado C5-REAL en disco nativo: 14/14 eventos con
  escritores mixtos CLI+API concurrentes.
