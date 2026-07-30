<!-- C5-REAL EXERGY CERTIFIED -->
# ARCHITECTURE — cortex-persist (BABYLON-60 Substrate)

## Core Pipeline

```
Agent Intent
    │
    ▼
Validation Layer (schema + idempotency key)
    │
    ▼
Single-Writer Queue (asyncio.Queue)
    │
    ▼
BFTLedgerActor (ledger_actor.py)
    │         │
    ▼         ▼
SQLite WAL   BLAKE3 hash-chain
    │
    ▼
Causal Taint + Lamport timestamp
    │
    ▼
Git Sentinel (commit hook on mutation)
```

## Subsystems

### 1. Python SDK (`babylon60/`)

Primary interface layer. Handles validation, idempotency, and async queue management.

- `babylon60.api.client` — CortexClient public API
- `babylon60.api.server` — FastAPI/Uvicorn REST+WebSocket server
- `babylon60.bft.ledger_actor` — Single-writer actor serializing all DB writes
- `babylon60.database.core` — Async SQLite WAL pool (`busy_timeout=5000ms`)

### 2. Rust Core (`strike_rs/`)

Optional low-latency extension via PyO3/Maturin. Bypasses Python GIL for:
- BLAKE3 hash computation
- Batch cryptographic operations
- Parallel CPU-bound workloads

**Status: Alpha.** Do not use in production without benchmarking.

### 3. Sovereign Agentic IDE (`babylon60-ide/`)

A local-first environment designed for inspectability and low-latency interaction with the ledger.

*   **Tauri App Wrapper (`src-tauri/`):** Manages OS integration, native windows, and bridges local database state to the renderer thread via IPC command handlers.
*   **FastAPI Backend (`backend/`):** Exposes REST and WebSocket endpoints for ledger querying, BM25 searching, telemetry tracking, and local model generation.
*   **Vite Frontend (`frontend/`):** Built with Vanilla JS, styled with a high-contrast neuro-inclusive palette, and configured with keyboard-first navigation (Command Palette `Cmd+K`, Scratchpad `Cmd+Shift+Space`).
*   **Local Inference Module (`inference/`):** Confined to loopback endpoints (`127.0.0.1:11434` / `localhost`). Bridges the FastAPI server to local inference engines (Ollama, MLX, or the native Mamba SSM engine), ensuring zero data leak to public hyperscalers.

### 4. Ledger Contract

Every entry written to the ledger must satisfy:

```python
{
    "id": "uuid-v5",            # Idempotency key
    "prev_hash": "blake3-hex",  # Chain link to previous entry
    "payload": {...},           # Structured content
    "causal_taint": "...",      # Creation trace: who/when/why
    "lamport_t": int,           # Logical clock
    "agent_id": "str",          # Writer identity
}
```

Duplicate `id` → write is rejected (idempotent).
`prev_hash` mismatch → write aborted, chain integrity violated.

### 5. Consensus Topology (M12 Levels)

| Level | Mechanism | Scope |
|:---|:---|:---|
| L1 — AP/CRDT | Local caches, telemetry | Single node |
| L2 — CP single-writer | `master_ledger.db` WAL | Single process |
| L3 — External witness | Git Sentinel | Local repo |
| L4 — BFT quorum | N≥3f+1 swarm | **Prototype — distributed only** |
| L5 — Blockchain anchor | OTS / BTC OP_RETURN | **Research — not implemented** |

> [!NOTE]
> L4 and L5 are **not required** for local agent memory use cases. They are research extensions. The stable core uses L1–L3 only.

### 6. Git Sentinel

Each disk mutation triggers an automatic commit with Conventional Commit prefix and `CORTEX_TAINT` metadata injected into the commit message. This creates an auditable, human-readable history of all agent state changes.

### 7. Formal Proofs (`proof/lean/`)

**Status: Prototype.** Lean 4 theorem formalization of:
- Partial ordering invariant
- Non-equivocation in single-writer consensus
- BFT safety bounds (N≥3f+1)

Not integrated into CI. Research artifact only.

## Data Flow: Crash Recovery

1. Process killed mid-transaction → SQLite WAL rolls back automatically
2. Agent restarts → replays unconfirmed entries from WAL journal
3. Hash-chain continuity verified before replay is accepted
4. If chain is broken → entry is quarantined, not silently dropped

## Multi-Tenant Isolation

Each tenant receives an isolated SQLite database file. There is no shared table between tenants. Queries across tenants require explicit federation — not available in current stable API.

## Dependency Graph (Core Only)

```
aiosqlite  ──►  babylon60.database.core
pyyaml     ──►  babylon60.config
numpy      ──►  babylon60.memory (vector ops)
networkx   ──►  babylon60.graph (ontology)
cbor2      ──►  babylon60.ledger (binary encoding)
```

Optional extensions wire in: `cryptography`, `pynacl`, `sqlite-vec`, `faster-whisper`, `mlx-lm`.
