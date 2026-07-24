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

## Active C5 Invariant Registry (INV_C5_01 — INV_C5_23)

Full definitions and execution protocols are synchronized between `ETHOS.md` and `.agents/AGENTS.md`.

### Core System & BFT Invariants
- **INV_BFT_02:** Never call `sqlite3` synchronously inside an async event loop (WAL + `busy_timeout=5000ms`).
- **INV_BFT_03:** Every insert must include `causal_taint` (`who/when/why`).
- **INV_BFT_04:** Use UUID v5 idempotency keys. Reject duplicates silently.
- **INV_C5_01 – INV_C5_07:** Cryptographic truth, sovereign keys, single hash primitive, Ed25519 signatures, live validator, Lean model linkage, loud failure.
- **INV_C5_08:** EIP-1153 transient reentrancy locks (`tload`/`tstore` validation).
- **INV_C5_09:** Python 3.12+ testing isolation via `.venv` and `BypassSandbox: true`.
- **INV_C5_10 – INV_C5_23:** PyNaCl serialization, remote purge, symlink depth, autopoiesis alignment, exergy agent, vault sync, seal protocol, ultrathink, BFT float exclusion, fail-fast orchestration, kinetic purge, `/goal` exergy maximization, Kimi K3 interleaved execution, and semi-formal epistemic grounding (see `.agents/AGENTS.md`).
- **Ω30 · PYO3 FORWARD ABI INVARIANT:** Enforce `PYO3_USE_ABI3_FORWARD_COMPATIBILITY=1` on mixed Rust/Python builds.


### Proof Kernel Specification
El núcleo epistemológico ha sido extraído a su propia especificación formal (Proof Assistant Kernel).
Consultar en: [docs/BABYLON_PROOF_KERNEL_SPEC.md](docs/BABYLON_PROOF_KERNEL_SPEC.md).

Invariantes definidos:
- Ω138 · Causal Stratification
- Ω152 · Discriminatory Measurement
- Ω153 · Evidence Separation
- Ω154 · Confidence Traceability
- Ω155 · Epistemic Monotonicity
- Ω156 · Physical Posterior
- Ω157 · A Priori Discriminatory Power
- Ω158 · Evidence Lineage
- Ω159 · Dependency Closure
- Ω160 · Propagated Invalidation
- Ω161 · Absent Evidence Statistical
- Ω162 · Falsification Power
- Ω163 · Residual Entropy
- Ω164 · Ontology vs Epistemology Separation
- Ω165 · Reversible Ledger
- Ω166 · Pure Inference (Referential Transparency)
- Ω167 · Semantic Preservation
- Ω168 · Canonical Representation
- Ω169 · Proof-Carrying Diagnosis
- Ω170 · Minimality
- Ω171 · Completeness Certificate
- Ω172 · Replay Determinism
- Ω173 · Kernel Minimality
- Ω174 · Versioned Semantics
- Ω175 · Soundness Boundary
- Ω176 · Completeness Boundary
