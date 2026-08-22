# BABYLON-60

[🌐 Leer en Español](README_ES.md)

**The cryptographic "Black Box Flight Recorder" for autonomous AI agents.**

[![Version](https://img.shields.io/badge/version-4.0.0-black?style=flat-square)](https://github.com/borjamoskv/BABYLON-60)
[![License](https://img.shields.io/badge/license-Sovereign_Dual--License-orange?style=flat-square)](./LICENSE)
[![Python](https://img.shields.io/badge/python-≥3.10-blue?style=flat-square)](./pyproject.toml)
[![Rust](https://img.shields.io/badge/rust-≥1.77-orange?style=flat-square)](./Cargo.toml)
[![EU AI Act](https://img.shields.io/badge/EU_AI_Act-Articles_9--14_Compliant-purple?style=flat-square)](./docs/04_research/eu_ai_act_compliance_whitepaper.md)

---

## ⏱️ 10-Second Summary

**What is it?**  
Just as airplanes use a black box to record flight telemetry, **BABYLON-60** is a local, tamper-evident logbook for AI agents. Every decision, tool invocation, and prompt response your agent executes is cryptographically chained and sealed in a local database.

**Why do you need it?**  
When autonomous agents run actions in production (e.g., executing code, placing orders, reading files), you need **proof of what happened** that cannot be altered retroactively—whether by an external attacker or a rogue process. BABYLON-60 gives you automated auditability and regulatory compliance (EU AI Act) with zero cloud lock-in.

---

## 💡 Demystifying the Jargon

If you are new to audit ledgers or low-level systems, here is how to understand the key terms:

| Technical Term | Plain Language Analogy | How BABYLON-60 Uses It |
| :--- | :--- | :--- |
| **Tamper-evident** | **Tamper Seal Sticker:** You can open a jar, but the broken seal reveals it was opened. | If anyone edits past agent logs in the database, the hash chain breaks instantly and alerts you. |
| **Hash Chain** | **Domino Line:** Each domino is linked to the position of the previous one. | Every agent event contains the SHA3-256 fingerprint of the previous event. |
| **Single-writer WAL** | **Single Queue Line:** Only one person writes to the logbook at a time to prevent collisions. | Uses SQLite Write-Ahead Logging to guarantee zero database corruption even under concurrency. |
| **Lamport Clock** | **Numbered Sequence Tickets:** Standardizes "Event 1 happened before Event 2". | Enforces strict causal chronological order across agent actions. |
| **Local-First** | **On-Prem Vault:** All data stays on your machine (`$BABYLON_HOME/`). | No cloud server dependencies, complete data sovereignty. |

---

## ⚡ Quick Start in 3 Steps

### Step 1: Install & Set Environment

```bash
git clone https://github.com/borjamoskv/BABYLON-60.git
cd BABYLON-60

# Set the required home directory for databases
export BABYLON_HOME="$HOME/.babylon60"
mkdir -p "$BABYLON_HOME"

# Install Python dependencies (uv is recommended)
uv sync

# (Optional) Verify Rust workspace kernel
cargo test --workspace
```

### Step 2: Run the Demo Script

Run the automated hero demo to see event logging, PII redaction, and compliance certificate generation in action:

```bash
PYTHONPATH=packages python3 scripts/c5_demos/run_hero_demo.py
```

### Step 3: Append an Event (5-Line Python API)

Wrap your AI agent calls with 5 lines of code:

```python
from babylon60.bft.cortex_persist_ledger import CortexPersistLedger, CortexEvent

# 1. Initialize local ledger
ledger = CortexPersistLedger("$BABYLON_HOME/dbs/my_agent.db")

# 2. Record an agent decision
event = CortexEvent(
    event_type="AGENT_ACTION",
    payload={"tool": "sql_query", "query": "SELECT * FROM users"},
    cortex_taint="session:abc123"
)
ledger.append(event)

# 3. Verify that nobody modified history
assert ledger.verify_integrity() == True
```

---

## 🎯 Who Is BABYLON-60 For?

### 🤖 For AI Engineers & Developers
- **Problem:** Debugging non-deterministic agent workflows or proving a hallucinated action was not caused by human code.
- **Solution:** Every prompt, tool output, and state transition is captured in an append-only sequence with `verify_integrity()` functions.

### 🏛️ For Compliance & Legal Officers (EU AI Act)
- **Problem:** Articles 9–14 of the EU AI Act mandate technical documentation, logging, and human oversight for high-risk AI.
- **Solution:** Export regulatory audit certificates with one CLI command:
  ```bash
  uv run babylon60-compliance --bundle artifact_bundle_v3 --locale en --format html --output audit_cert.html
  ```

### 🔒 For Security & Forensic Teams
- **Problem:** Preventing prompt injection attacks from altering local historical agent memory.
- **Solution:** Triggers at the database engine level block `UPDATE` and `DELETE` queries, backed by a Rust kernel IPC fail-stop slot (`SharedManifest`).

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│   Your AI Agent Framework (LangChain / AutoGen / CrewAI / Ollama / Custom)  │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │ Log Event / Action
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                       BABYLON-60 Accountability Layer                       │
│                                                                             │
│   🐍 Python Core (packages/babylon60/)                                      │
│   ├── bft/                 Hash-Chained Ledger (SHA3-256)                   │
│   ├── crypto/              AES-256-GCM, Ed25519 & Hash Registry             │
│   ├── database/            Single-Writer SQLite/WAL Connector               │
│   ├── attestation/         Merkle DAG State Anchoring                       │
│   └── compliance_exporter/ EU AI Act Certificate Generator                  │
│                                                                             │
│   🦀 Rust Kernel (src/ + crates/)                                           │
│   ├── SharedManifest       64-Byte Lock-Free Shared Memory IPC              │
│   ├── seqlock              Zero-Contention Multi-Reader Locks               │
│   └── halt                 Fail-Stop Hardware Circuit Breaker              │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │ Encrypted & Chained Write
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                Local SQLite WAL Ledger ($BABYLON_HOME/dbs/)                 │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 🛡️ Security & Integrity Matrix

| Feature | How It Works | What It Prevents / Protects |
| :--- | :--- | :--- |
| **Hash Chaining** | Each entry stores `SHA3-256(previous_hash + current_data)`. | Prevents retroactive log alteration or reordering. |
| **Immutable Triggers** | SQLite `BEFORE UPDATE` and `BEFORE DELETE` triggers raise SQL exceptions. | Prevents accidental or malicious modification via SQL queries. |
| **Single-Writer WAL** | Strict `PRAGMA journal_mode=WAL` with `busy_timeout=5000ms`. | Prevents database corruption or lock errors under heavy concurrency. |
| **External Witnessing** | Git Sentinel tags commits with `Ledger-Head` and `Ledger-Seq` trailers. | Ensures off-site verification via CI/CD runners. |

---

## 📂 Monorepo Structure

```
BABYLON-60/
├── packages/
│   ├── babylon60/         # Core Python engine (ledger, crypto, database, compliance)
│   └── cortex/            # Cognitive memory substrate & MCP Server integration
├── crates/
│   ├── babylon60-kernel/  # Low-level Rust #![no_std] execution engine
│   ├── babylon60-compiler/# .b60 DSL parser & Lean 4 proof emitter
│   └── strike-rs/         # PyO3 native Rust-Python bridge & shared memory
├── apps/
│   ├── babylon60-ide/     # Desktop Tauri v2 Developer IDE
│   ├── web/               # Telemetry visualizer (React 18)
│   └── tonnetz_app/       # Neo-Riemannian harmonic visualizer (EU AI Act Art. 14)
├── scripts/               # Demos, benchmark suites, and CLI verification tools
├── docs/                  # Specifications, whitepapers, and regulatory guides
└── proof/                 # Lean 4 formal mathematical verification proofs
```

---

## ⚙️ Configuration & Environment Variables

| Variable | Required | Default | Purpose |
| :--- | :---: | :--- | :--- |
| `BABYLON_HOME` | **Yes** | *None* | Root folder for databases (`$BABYLON_HOME/dbs/`). Must be explicitly set. |
| `BABYLON60_LICENSE_KEY` | Commercial | *None* | Cryptographic Enterprise license key. |
| `BABYLON60_LICENSE_SALT` | Commercial | *None* | Secret HMAC salt for license verification. |

---

## 🧪 Testing & Verification

```bash
# Run Python test suite (377+ tests)
export BABYLON_HOME=/tmp/babylon_test
uv run pytest tests/ -v

# Run Rust kernel tests
cargo test --workspace

# Run full quality check (lint + format + typecheck + tests)
make all
```

---

## 📄 License & Commercial Support

**Sovereign Dual-License v4.0:**
- **Sovereign Tier:** Free & Open Core for individuals, researchers, and non-commercial projects.
- **Enterprise Tier:** Required for commercial production deployments. Contact for enterprise license keys.

See [LICENSE](./LICENSE) and [COMMERCIAL_LICENSE.md](./docs/COMMERCIAL_LICENSE.md).

---

## 🛡️ Security Vulnerability Reporting

Report security issues confidentially to **security@babylon60.com**. Do not open public GitHub issues for security vulnerabilities.  
*Response SLA: Acknowledgment < 24 hours, Patch < 72 hours.* See [SECURITY.md](./SECURITY.md).

---

<sub>BABYLON-60 v4.0.0 · Cryptographic Ledger for Autonomous AI Agents · Borja Moskv</sub>
