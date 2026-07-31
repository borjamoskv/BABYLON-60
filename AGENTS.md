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
- **INV_BFT_04:** Use UUID v5 idempotency keys. Reject duplicates silently ONLY IF the payload hash matches (idempotent replay). If payloads differ, fail-fast and raise.
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
- All generated code carries authorship: **Telmo Dinámico de Moskv (`borjamoskv`)**.


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

### Toolchain Fallback Protocol (Venv Explicit Pathing)
- **INV_C5_16:** When `uv run <cmd>` fails due to a missing `uv` executable in PATH, do NOT fallback to the system python if the project requires a virtual environment (`INV_C5_09`). Instead, directly invoke the executable from the virtual environment bin directory (e.g., `./.venv/bin/pytest`, `./.venv/bin/python`). If you must execute `uv` itself (e.g., `uv sync` or `uv add`), use the absolute path `~/Library/Python/3.14/bin/uv`. For non-python hooks (like system ruff), fallback to direct system binaries (`/opt/homebrew/bin/ruff`) and execute `git commit --no-verify` with explicit reason documented in commit message.

### Graceful Skip of Rust PyO3 Aborts
- **INV_C5_RUST_ABORT:** If running `pytest` fails with a `Fatal Python error: Aborted` due to a PyO3 Rust extension (e.g., `strike_rs.so`) crashing on import, agents MUST NOT attempt to ignore the error or debug C/Rust tracebacks. Instead, delete the offending `.so` file from the repository root to trigger a clean `ImportError`, allowing the test suite to execute its graceful `pytest.skip` fallback logic.

### Continuous Commit Polisher Invariant
- **POLISHER_INVARIANT:** Any commit automatically rewritten by the polisher daemon must log a `polisher_success` event in the ledger with a monotonic `lamport_t`. Failure to log must abort the push.

### Sovereign Dual-Licensing Invariant (Free for the Community, Corporate Licensing)
- **INV_C5_17:** Every component, service, model, database, app (including BabylonMail), and subagent workflow in the BABYLON-60 ecosystem MUST be 100% free, open-source, and sovereign for individuals, independent developers, and non-commercial usage. Sovereign Community mode enforces thermodynamic throughput limits (e.g. batch inserts capped at N <= 100 nodes in LedgerPersist). Commercial, corporate, or enterprise exploitation requires explicit commercial licensing verified via HMAC CORTEX_LICENSE_KEY (license_manager.py), unlocking unbounded BFT throughput.


### Zero-Worktree Swarm Scaling (ENOSPC Prevention)
- **INV_C5_18:** For large parallel agent swarms ($N \ge 10$), creating physical disk Git Worktrees that consume storage and trigger ENOSPC is strictly prohibited. Swarm scaling must use in-memory AgencyHypervisor multi-tenant handles and single-writer BFT actors.

### Epistemic Integrity in Ledger Attestation
- **INV_INGESTA_08:** An attestation with a 100% confirmation rate is marked UNBACKED by construction. The verifier must be able to lose. Attestation without citable evidence (verbatim strings extracted from the primary source) is mere assertion with garnish. Simulation theater is not admitted: C4-SIM must never be presented as C5-REAL.

### ABFT Shared Memory Zero-Copy Constraint (iceoryx2 v0.3.0)
- **INV_C5_ABFT_IPC:** When implementing Asynchronous BFT inside a single-node hypervisor to satisfy `INV_C5_18` without socket exhaustion, use `iceoryx2` zero-copy shared memory. For `v0.3.0+`, initialization MUST flow directly through `zero_copy::Service::new(&service_name).publish_subscribe().open_or_create::<T>()?` with `.publisher().create()?` and `.subscriber().create()?`. Importing deprecated `node::NodeBuilder` or `service::ipc` modules directly is prohibited.

### Default Argument Binding Invariant (Prevención de Fuga de Mocks)
- **INV_C5_MOCKING_01:** Never use global configuration constants (e.g., `REPO_ROOT`, `DB_PATH`) as default arguments in function signatures (`def func(root=REPO_ROOT):`). In Python, default arguments bind at import time. This makes it impossible for `pytest` to cleanly mock these constants at runtime, causing tests to leak out of the sandbox and scan the physical disk. 
  - **Solución:** Use `None` as the default and resolve it at runtime (`def func(root=None): if root is None: root = REPO_ROOT`), or explicitly pass the constant from the calling function.

### Explicit Goal Termination Invariant
- **INV_GOAL_TERMINATION:** Cuando el agente opera bajo el modo `/goal` o tareas de fondo de larga duración, tan pronto como todos los entregables de `task.md` estén físicamente verificados, el agente DEBE incluir explícitamente el token `<!-- GOAL_COMPLETE -->` (o `<!-- GOAL_CANCELLED -->` si fue abortado) en su respuesta final. Prohibido intentar cerrar el turno sin la etiqueta de completado.

### Empirical Remote Push Verification Invariant
- **INV_C5_REAL_PUSH:** Ningún paso de sincronización remota (`git push`) puede marcarse como completado en `task.md` o presentar evidencia C5-REAL si el comando devuelve un código de salida distinto de 0 o un fallo de permisos. Los fallos remotos deben registrarse explícitamente como fallos o fallbacks locales no sincronizados.

### Rust `Result::is_ok()` Opaque Panic Invariant
- **INV_C5_RUST_DEBUG_01:** When a Rust test fails with an opaque `assertion failed: res.is_ok()` panic, agents MUST NOT guess the underlying cause. The agent MUST immediately modify the test source code to print the inner error payload (e.g., changing `assert!(res.is_ok());` to `assert!(res.is_ok(), "Test failed: {:?}", res);`) and re-run the test to extract the exact deterministic failure before proceeding with any logical fixes.

### Stale Thermal Lock Cleanup Protocol
- **INV_C5_22_CLEANUP:** When encountering a `Thermodynamic Hysteresis Active: Another swarm holds the lock (INV_C5_22)` error during `strike_rs` BFT engine tests, it indicates a stale lock left behind by a previously panicked test or OOM crash. Agents MUST execute `rm -f .cortex_thermal_lock strike_rs/.cortex_thermal_lock *.db.lock` to purge the orphaned locks before re-running the test suite.

### GELABP Zero-Latency Collapse Invariant
- **INV_C5_29_GELABP_ZERO_LATENCY:** In stress testing, synthetic nodes must inject a minimum virtual latency (e.g. `latency_ms = 1`). If all nodes execute in exactly `0` ms, `node_sum_ms` equals `0.0`, causing the GELABP `speedup` multiplier to mathematically collapse to `0.0`. This triggers a false-positive Thermodynamic Collapse (Score = 0.00).

### Global RwLock Thermodynamic Limit
- **INV_C5_30_GLOBAL_RWLOCK_LIMIT:** Spawning more than 100,000 concurrent Tokio futures that attempt to acquire `.write().await` on a single global `RwLock` (e.g., `KdaMemoryBuffer.put`) creates extreme lock contention. This artificially spikes `wall_ms` (Entropy) and guarantees a legitimate GELABP Thermodynamic Collapse (Score < 700). Tests exceeding 100K nodes must either accept the intentional Rollback or refactor the architecture to use batched writes / MPSC channels.

### Tauri State & iceoryx2 Send/Sync Invariant
- **INV_C5_TAURI_IPC:** When embedding `iceoryx2::service::zero_copy::Service` or `PortFactory` inside Tauri `AppState` (`tauri::State<AppState>`), POSIX shared memory locks containing raw pointers (`*const c_void`) will break standard `Send + Sync` auto-traits on macOS. Agents MUST wrap the handle in a dedicated newtype struct (e.g. `pub struct IpcHandle(pub Arc<PortFactory<Service, Vec<u8>>>);`) and explicitly implement `unsafe impl Send for IpcHandle {}` and `unsafe impl Sync for IpcHandle {}` to satisfy Tauri's state concurrency bounds.

### Tauri v2 Workspace & Binary Target Invariant
- **INV_C5_TAURI_WORKSPACE:** In monorepos using a root Cargo workspace manifest (`Cargo.toml`), any nested Tauri application (e.g., `babylon60-ide/src-tauri`) MUST be explicitly registered in `workspace.members` of the root manifest. Additionally, the nested Tauri package MUST contain both a `[lib]` and a `src/main.rs` binary entrypoint calling `app_lib::run()`; otherwise `cargo run` and `tauri dev` will abort with `error: a bin target must be available`.

### Cargo Native Library Links Unification Invariant
- **INV_C5_CARGO_LINKS:** In Cargo workspace monorepos containing C/C++ native library bindings (e.g. `rusqlite` linking `sqlite3` or `pyo3` linking `python`), all member packages MUST share identical dependency versions to prevent `package links to native library conflicts` during workspace-wide builds (`cargo check --workspace`).

### Nested Workspace Header Prohibition
- **INV_C5_SINGLE_WORKSPACE:** Sub-package `Cargo.toml` manifests declared inside `workspace.members` of the root manifest MUST NOT define a `[workspace]` table header. Workspace-wide membership must be declared exclusively in the root `Cargo.toml`.

### Phantom Ontology Rejection (Anti-Hologram Invariant)
- **INV_C5_PHANTOM_ONTOLOGY:** When official documentation or taxonomies (e.g., `SKILL_ARSENAL_TAXONOMY.md`) reference components, skills, or architectural mappings that no longer physically exist on disk (Ghost Subsystems), agents MUST treat the documentation as a Syntactic Hologram and reject it via Popperian Falsification. Agents must NEVER attempt to execute, hallucinate, or build upon these missing components. Physical disk presence (C5-REAL) absolutely supersedes documented claims.

### Overnight Goal Autonomous Audit Protocol
- **INV_C5_AUDIT_GOAL:** When operating under `/goal` for codebase review or overnight tasks, agents MUST systematically execute:
  1. Automated code format & linting (`ruff check --fix .` / `cargo fix`).
  2. Compiler warning cleanup (`#![allow(dead_code)]` for protocol specification domain models).
  3. Full multi-suite testing (`cargo test` + `pytest`).
  4. AST control flow nesting validation (`GELABP_DEPTH_INVARIANT` <= 4).
  5. Generating a clean `walkthrough.md` report before signaling `<!-- GOAL_COMPLETE -->`.

