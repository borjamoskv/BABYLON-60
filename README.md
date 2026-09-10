# BABYLON-60

[🌐 Leer en Español](README_ES.md)

**Tamper-evident, local-first cryptographic ledger for autonomous AI agents.**

[![Version](https://img.shields.io/badge/version-4.0.0-black?style=flat-square)](https://github.com/borjamoskv/BABYLON-60)
[![License](https://img.shields.io/badge/license-Sovereign_Dual--License-orange?style=flat-square)](./LICENSE)
[![Python](https://img.shields.io/badge/python-≥3.10-blue?style=flat-square)](./pyproject.toml)
[![Rust](https://img.shields.io/badge/rust-≥1.77-orange?style=flat-square)](./Cargo.toml)

---

## What Is BABYLON-60

BABYLON-60 is a monorepo that provides a **hash-chained, append-only ledger** backed by SQLite WAL and a low-level Rust IPC kernel. It is designed so that AI agents — regardless of which LLM or orchestrator drives them — produce an auditable, tamper-evident trail of every action they take.

**Core idea:** every event an agent produces is appended to a local SQLite database with a SHA3-256 hash chain. Each entry's hash covers the previous entry's hash, creating a linked sequence where any retroactive modification breaks the chain and is programmatically detectable.

### What It Is

- A **local-first** persistence layer: all data stays on your machine in `$BABYLON_HOME/`.
- A **tamper-evident** (not tamper-proof) ledger with hash-chain integrity verification.
- A **single-writer SQLite/WAL** database with `busy_timeout=5000ms`, `synchronous=FULL`, and `foreign_keys=ON`.
- A Rust kernel providing a 64-byte lock-free IPC slot (`SharedManifest`) with fail-stop semantics and COSE_Sign1 halt receipts.
- A compliance exporter that generates **Ed25519-signed self-assessment certificates** for EU AI Act supervisory authorities (AESIA, BSI, CNIL) which **re-verify the underlying ledger evidence** before any article is reported as compliant (fail-closed).

### What It Is Not

- Not a distributed consensus system (no live BFT/PBFT quorum). Consensus is achieved *a posteriori* via Git Sentinel external witnesses.
- Not tamper-proof against an attacker with filesystem access who bypasses the database engine.
- Not a replacement for your LLM or agent framework — it wraps around them as an accountability layer.

---

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│   Your Agent Stack (LangChain / AutoGen / CrewAI / Ollama)   │
├──────────────────────────────────────────────────────────────┤
│   BABYLON-60 Accountability Layer                            │
│                                                              │
│   Python (01_ORCHESTRATOR/babylon60/)                        │
│   ├── bft/          Hash-chained ledger (SHA3-256)           │
│   ├── crypto/       Hash registry, AES-256-GCM, Ed25519     │
│   ├── database/     Single-writer SQLite/WAL connector       │
│   ├── guards/       URL, path, license validation            │
│   ├── attestation/  Merkle DAG anchoring                     │
│   └── compliance_exporter/  EU AI Act certificates           │
│                                                              │
│   Rust (src/ + 00_BABYLON_SHIELD/ + 01_CORTEX_ENGINE/)       │
│   ├── SharedManifest    64 B lock-free IPC (AArch64/x86)     │
│   ├── seqlock           SPMC readers, zero RFO               │
│   ├── halt              Fail-stop + COSE_Sign1 receipts      │
│   ├── thermodynamics    Landauer floor bisimulation          │
│   └── cortex            Cognitive memory substrate bridge    │
├──────────────────────────────────────────────────────────────┤
│   SQLite WAL Database ($BABYLON_HOME/dbs/)                   │
└──────────────────────────────────────────────────────────────┘
```

---

## Security & Integrity Properties

| Property | Mechanism | Limitation |
| :--- | :--- | :--- |
| **Hash chaining** | Each ledger entry includes a SHA3-256 hash of the previous entry. `verify_integrity()` recomputes and validates the full chain. | Detects tampering *a posteriori*; does not prevent it if the attacker bypasses SQLite. |
| **Append-only enforcement** | SQLite triggers (`trg_cortex_no_update` / `trg_cortex_no_delete`) block UPDATE/DELETE at the engine level. | Bypassable by direct filesystem manipulation outside the DB engine. |
| **Single-writer WAL** | All connections use `PRAGMA journal_mode=WAL` + `busy_timeout=5000` via the centralized connector in [`database/core.py`](./01_ORCHESTRATOR/babylon60/database/core.py). | Scripts outside the core package may still use `sqlite3.connect` directly (tracked as technical debt). |
| **Idempotency** | UUID v5 keys per event prevent duplicate insertion — including duplicates inside a single `append_batch` call and replays of whole batches. | Scoped to a single ledger instance. |
| **Lamport ordering** | Monotonically increasing Lamport timestamps enforce causal ordering. | Logical clock, not wall-clock; no distributed coordination. |
| **External witnessing** | Git Sentinel injects `Ledger-Head` and `Ledger-Seq` as commit trailers. CI runners act as independent witnesses. | Requires pushing to a remote; no protection during offline-only operation. |
| **Crypto agility** | [`hash_registry.py`](./01_ORCHESTRATOR/babylon60/crypto/hash_registry.py) allows swapping hash algorithms (SHA-256, SHA3-256, SHA-512, SHA3-512) at startup. | Changing algorithm mid-session breaks the hash chain (by design). |

---

## Installation

### Prerequisites

- Python ≥ 3.10
- [uv](https://docs.astral.sh/uv/) (recommended) or pip
- Rust ≥ 1.77 (for the kernel crate)

### Setup

```bash
git clone https://github.com/borjamoskv/BABYLON-60.git
cd BABYLON-60

# Set the required environment variable
export BABYLON_HOME="$HOME/.babylon60"
mkdir -p "$BABYLON_HOME"

# Install Python dependencies
uv sync

# Build and test the Rust workspace
cargo test --workspace
```

---

## Quick Start

### Run the Hero Demo

Demonstrates PII redaction, serialization boundary verification, network-failure fallback, and compliance certificate generation:

```bash
PYTHONPATH=. python3 scripts/c5_demos/run_hero_demo.py
```

### Append an Event to the Ledger (Python API)

```python
from babylon60.bft.cortex_persist_ledger import CortexPersistLedger, CortexEvent

ledger = CortexPersistLedger("$BABYLON_HOME/dbs/my_agent_ledger.db")

event = CortexEvent(
    event_type="AGENT_ACTION",
    payload={"action": "search", "query": "quarterly revenue"},
    cortex_taint="session:abc123",
)

result = ledger.append_event(event)
# => {"seq": 1, "event_id": "...", "entry_hash": "...", "status": "C5_PERMANENT"}

# Verify the full hash chain
assert ledger.verify_integrity()

# Get a Merkle root for attestation
root = ledger.get_merkle_root()
```

### Verify Ledger Attestation (CLI)

```bash
# Verify an LLM attestation payload
uv run babylon60-attest --file attestation_payload.json

# Generate EU AI Act Compliance Certificate (JSON / Markdown / HTML)
# --ledger binds the certificate to real evidence: the exporter re-runs the
# full hash-chain verification and Merkle-root comparison before any article
# is reported CONFORME, and signs the certificate with Ed25519.
uv run babylon60-compliance --bundle artifact_bundle_v3 \
    --ledger "$BABYLON_HOME/dbs/my_agent_ledger.db" \
    --locale es --format html --output cert.html

# Manage Enterprise Licenses
uv run babylon60-license generate --owner "AcmeCorp" --tier enterprise --days 365
uv run babylon60-license verify --key "AcmeCorp:enterprise:..."
```

---

## Configuration

### Environment Variables

| Variable | Required | Description |
| :--- | :--- | :--- |
| `BABYLON_HOME` | **Yes** | Root directory for all databases and state. Defaults to nothing — must be set explicitly. |
| `GEMINI_HOME` | Scripts only | Used by exergy scripts for vault/brain paths. |
| `BABYLON60_LICENSE_KEY` | Enterprise | Cryptographic license key for commercial use (fallback: `BABYLON60_LICENSE_FILE`). |
| `BABYLON60_LICENSE_SALT` | Enterprise | Secret HMAC salt for license verification. |
| `BABYLON60_SIGNING_SEED` | Compliance | 64-hex-char Ed25519 seed for stable certificate signing. If unset, an ephemeral key is generated and flagged in the certificate. |

### Data Location

All persistent state is stored under `$BABYLON_HOME/`:

```
$BABYLON_HOME/
├── dbs/                    # SQLite databases (ledger, memory, etc.)
├── .babylon60/             # Exergy agent ledger
└── ...
```

---

## Verification & Audit

### Programmatic Integrity Check

```python
ledger = CortexPersistLedger("$BABYLON_HOME/dbs/my_ledger.db")

# Full hash-chain verification
is_valid = ledger.verify_integrity()

# State attestation manifest
attestation = ledger.get_state_attestation()
# => {"total_entries": N, "merkle_root": "...", "integrity_verified": True, ...}
```

### Static Verification

```bash
# Lint + type check
make check

# Or individually:
ruff check 01_ORCHESTRATOR/babylon60 tests
mypy 01_ORCHESTRATOR/babylon60 tests --strict --ignore-missing-imports
```

---

## Testing

```bash
# Python test suite (see CI for the current count)
export BABYLON_HOME=/tmp/babylon
uv run pytest tests/ -v

# Rust workspace tests
cargo test --workspace

# Full CI check (format + lint + typecheck + test)
make all
```

---

## Project Layout

```
BABYLON-60/
├── src/                          # Rust root crate (SharedManifest, seqlock, halt)
├── 00_BABYLON_SHIELD/            # Defense and Verification 
│   ├── crates/                   #   #![no_std] execution engines, ZK circuits
│   └── formal_verification/      #   Proof IR → Lean 4 emitter
├── 01_CORTEX_ENGINE/             # Cognitive Memory Substrate
│   ├── crates/                   #   Runtime executor, native bridge
│   └── transducers/              #   Data processing transducers
├── 01_ORCHESTRATOR/              # Python Core
│   ├── babylon60/                #   Core Python package
│   │   ├── bft/                  #     Hash-chained ledger (CortexPersistLedger)
│   │   ├── crypto/               #     Hash registry, AES, Ed25519, RFC 3161
│   │   ├── database/             #     Centralized SQLite/WAL connector
│   │   ├── guards/               #     URL/path/license validation
│   │   ├── attestation/          #     Merkle DAG anchoring
│   │   └── compliance_exporter/  #     EU AI Act certificate generator
│   ├── cortex/                   #   Cortex cognitive memory python substrate
│   └── services/                 #   Core services
├── 02_AGENTS_ARCHI/              # Python Agents
│   └── agents_archi/             #   Agents configuration and tools
├── proof/                        # Lean 4 axiomatic sketch (lake build)
├── scripts/                      # CLI tools, demos, verifiers
├── tests/                        # Python + Rust test suites
├── docs/                         # Specifications, whitepapers, guides
└── tools/                        # Attestation tooling
```

---

## Related Repository

- **[Teorema-Robinson-Moskv](https://github.com/borjamoskv/Teorema-Robinson-Moskv)**: The foundational mathematical formalization in Lean 4 from which BABYLON-60's causal axioms derive.

---

## Known Limitations

1. **Tamper-evident, not tamper-proof.** The hash chain detects modifications but cannot prevent an attacker with direct filesystem access from rewriting the database.
2. **No live distributed consensus.** The BFT module name is aspirational; the current architecture uses single-writer local persistence with external Git witnesses (Escalón 3). Live BFT (Escalón 4) is a future target.
3. **`except Exception` technical debt.** Several modules in `01_ORCHESTRATOR/babylon60/` and `scripts/` use broad exception handlers. These are tracked and being narrowed incrementally.
4. **Direct `sqlite3.connect` in scripts.** Some scripts bypass the centralized `database/core.py` connector. Migration is in progress.
5. **`BABYLON_HOME` required.** The system will not start without this environment variable — `Path.home()` fallbacks have been removed by policy.
6. **Two ledger implementations coexist.** The synchronous `CortexPersistLedger` (README quick-start) and the async `BFTLedgerActor` (used by the resilience tests) share semantics but not code. Consolidation is tracked as follow-up work.

---

## License

**Sovereign Dual-License v4.0:**

| Tier | Access | Requirement |
| :--- | :--- | :--- |
| **Sovereign** | Individuals, researchers, non-commercial | Free — 100% Open Core |
| **Enterprise** | Corporations, commercial use, production | Cryptographic `BABYLON60_LICENSE_KEY` |

See [LICENSE](./LICENSE) and [COMMERCIAL_LICENSE.md](./docs/COMMERCIAL_LICENSE.md).

---

## Security

Report vulnerabilities to **security@babylon60.com** — do not use public GitHub issues.  
SLA: acknowledgement < 24h, remediation < 72h.  
See [SECURITY.md](./SECURITY.md).

---

<sub>BABYLON-60 v4.0.0 · Tamper-Evident Cryptographic Ledger for AI Agents · Borja Moskv</sub>
