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

### Toolchain Fallback Protocol
- **INV_C5_16:** When pre-commit hooks or test runners fail due to missing `uv` executable in PATH, fallback to direct system binaries (`/opt/homebrew/bin/ruff`, system python), run verification suite, and execute `git commit --no-verify` with explicit reason documented in commit message.

### Continuous Commit Polisher Invariant
- **POLISHER_INVARIANT:** Any commit automatically rewritten by the polisher daemon must log a `polisher_success` event in the ledger with a monotonic `lamport_t`. Failure to log must abort the push.

### Sovereign Zero-Cost Invariant (100% Gratis)
- **INV_C5_17:** Every component, service, model, database, app (including BabylonMail), and subagent workflow in the BABYLON-60 ecosystem MUST be 100% free, open-source, self-hosted, and sovereign. Introducing paid subscriptions, proprietary SaaS paywalls, third-party API fees, or premium feature locks is strictly prohibited.



