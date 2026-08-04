# BABYLON-60 v4.0 (Sovereign Hardened)

[🌐 Leer en Español](README_ES.md)

**Layer 0 Infrastructure for Verifiable AI Agents & EU AI Act Regulatory Compliance**

[![Version](https://img.shields.io/badge/Version-4.0.0--Sovereign--Hardened-black?style=for-the-badge)](https://github.com/borjamoskv/BABYLON-60)
[![Security Rating](https://img.shields.io/badge/Security_Rating-A%2B-brightgreen?style=for-the-badge)](./docs/02_ontology/security_threat_model_v4.md)
[![EU AI Act](https://img.shields.io/badge/EU_AI_Act-Articles_9--14_Compliant-purple?style=for-the-badge)](./docs/04_research/eu_ai_act_compliance_whitepaper.md)
[![Formal Verification](https://img.shields.io/badge/Lean_4-Verified-green?style=for-the-badge)](./BabylonTrace.lean)
[![Governance](https://img.shields.io/badge/Governance-C5--REAL-blue?style=for-the-badge)](./SECURITY.md)
[![License](https://img.shields.io/badge/License-Sovereign_Exclusion_v1.0-orange?style=for-the-badge)](./LICENSE.md)

> *"Most AI systems can generate text. Few can justify their lineage."*

---

## ⚡ Live Executable Demo (5 Seconds)

Test the live kernel, cryptographic sanitization, network failure fallback, and automated certificate generation for **AESIA (Spain)**, **BSI (Germany)**, and the **EU AI Office** by running:

```bash
python3 scripts/run_hero_demo.py
```

---

## 🎯 The Problem: Why Vector Databases Are Not the Solution

In 2026, deploying AI agents in banking, healthcare, or defense using vector databases (Pinecone, Milvus, Weaviate) creates an **unacceptable legal liability**:

| What Vector DBs / Guardrails Do | What an EU AI Act Auditor Requires | Legal Consequence |
| :--- | :--- | :--- |
| Find semantically similar text | Proof of storage date/timestamp | Rejected under Art. 10 (Governance) |
| Return $K$-nearest neighbors | Causal chain: what data produced this decision | Rejected under Art. 9 (Risk Management) |
| Filter prompts probabilistically | Immutable guarantee that log was untampered | Fines up to **€35M or 7% turnover** (Art. 12) |

**Similarity is not lineage.** Without verifiable causal lineage, agents suffer from *generative entropy*: they drift and leave logs inadmissible in court.

---

## 🛡️ The Solution: BABYLON-60 v4.0 Substrate

BABYLON-60 is a **"local-first" governance and execution layer written in Rust and Lean 4** that encapsulates any agent stack (LangChain, AutoGen, CrewAI, Ollama) under thermodynamic and cryptographic constraints:

```
┌─────────────────────────────────────────────────────────────┐
│    Agents & Orchestrators (LangChain / AutoGen / CrewAI)    │
├─────────────────────────────────────────────────────────────┤
│    Latent LLMs (OpenAI / Claude / Mamba / Ollama)           │
├─────────────────────────────────────────────────────────────┤
│  ██ BABYLON-60 v4.0 SOVEREIGN HARDENED ██                   │
│  - Exact Sexagesimal Scheduler F60 (0;20 exact)             │
│  - Merkle-Causal DAG Ledger (Tamper-Evident)                │
│  - WORM Forensic Quarantine (Write Once Read Many)          │
│  - EU AI Act i18n Exporter (AESIA / BSI / CNIL)             │
├─────────────────────────────────────────────────────────────┤
│  Hardware Secure Enclave (TPM 2.0 / TEE / Native GPU bf16)  │
└─────────────────────────────────────────────────────────────┘
```

---

## 💎 Moats & Technology Pillars

### 1. Exact Sexagesimal Arithmetic (`F60`)
In `f64`, $1/3$ of an hour is `0.33333...` — accumulating catastrophic drift. In `F60`, it is exactly `0;20` (20 exact minutes, zero drift). `F60` governs the **Scheduler and Ledger**, while GPU tensors execute at native `bf16` speed.

### 2. Forensic WORM Quarantine (Write Once Read Many)
Traditional AIs hallucinate or purge logs upon failure. BABYLON-60 applies an **Immutable Cryptographic Freeze**: upon any anomaly, the engine triggers a `CRITICAL HALT` and freezes state into `artifact_bundle_v3/quarantine/` signed by TPM 2.0 hardware. **Zero destruction of evidence.**

### 3. Formal Verification with Lean 4
Static mathematical theorems (`proof.ir` $\to$ `BabylonTrace.lean`) proving the kernel is mathematically incapable of violating causal invariants.

### 4. Automated Multilingual Certification (`compliance_exporter`)
Built-in exporter generating audit-ready certificates for national supervisory authorities (AESIA in Spain, BSI in Germany, CNIL in France, NIST in the US).

---

## 📚 Documentation Directory Matrix

| Domain | Document | Description |
| :--- | :--- | :--- |
| **Vision** | [Foundational Manifesto v4.0](./docs/00_MANIFESTO.md) | Core thesis, 4 moat pillars, commercial ROI, and Engineer's Oath |
| **Research** | [EU AI Act Compliance Whitepaper](./docs/04_research/eu_ai_act_compliance_whitepaper.md) | Comprehensive mapping for Articles 9, 10, 11, 12, 13 & 14 of EU Reg 2024/1689 |
| **Research** | [Technical Whitepaper v1.0](./docs/WHITEPAPER.md) | Formal paper: F60, Merkle DAG Ledger, Self-Falsification Engine, Proof IR |
| **Strategy** | [Pitch Deck v4.0 (11 Slides)](./docs/PITCH_DECK.md) | B2B Executive presentation & Seed investment due diligence ($3M–$5M) |
| **Strategy** | [Valuation Strategy](./docs/VALUATION_STRATEGY.md) | Market valuation analysis ($8M – $400M) based on IP & infrastructure |
| **Guides** | [Enterprise Quickstart](./docs/03_guides/QUICKSTART_ENTERPRISE.md) | 5-minute DevOps onboarding guide for Docker Compose & Kubernetes/Helm |
| **Guides** | [Tutorial: Hello Causal World](./docs/03_guides/tutorial_hello_causal.md) | Step-by-step tutorial contrasting BABYLON-60 vs Python/asyncio |
| **Guides** | [Tonnetz Harmonic Audit Guide](./docs/03_guides/tonnetz_audit_guide.md) | Human oversight (Art. 14) via Neo-Riemannian spatial harmonic graph |
| **Security** | [Threat Model & Mitigations v4.0](./docs/02_ontology/security_threat_model_v4.md) | Phase II Threat Model: Cryptographic redaction, Grace Period & Bounds |
| **Specification**| [Formal Specification v4.0](./SPECIFICATION.md) | Complete operational semantics, B60 ISA, Proof IR, P2P Topology |
| **GTM & Sales** | [PoC Spec (7 Shadow Days)](./docs/05_gtm/forensic_quarantine_poc_spec.md) | Read-only Proof of Concept specification for CISOs |
| **GTM & Sales** | [CISO Cold Email Playbook](./docs/05_gtm/ciso_cold_email_playbook.md) | B2B prospecting templates in Spanish, English, and German |
| **GTM & Sales** | [Hero Video Script & Show HN](./docs/05_gtm/hero_video_script_and_show_hn.md) | Timecoded 60s demo video script & Hacker News launch post |
| **GTM & Sales** | [VC Data Room Manifest](./docs/05_gtm/vc_data_room_manifest.md) | Structured virtual due diligence index for Tier-1 VC funds |

---

## 🕹️ Agent Integration & Command Console (Antigravity & WA-Nexus)

BABYLON-60 is not just a passive kernel; it interfaces directly with your preferred AI stack to provide deterministic autonomy, "Deep Research" (AUTODIDACT-Ω), and zero-friction forced execution (ULTRATHINK).

### 1. LLM Injection (Model Context Protocol)
The kernel is agnostic and exposes its local tool arsenal via the MCP standard (`cortex_mcp_server.py`):
- **For Claude Code (Anthropic) & Cursor/Codex (OpenAI):** Native MCP support. Add the local server in settings (or use `claude mcp add`) and your AI immediately inherits WORM Quarantine shielding and local physical execution capabilities.
- **For ChatGPT (Web):** Export BABYLON-60's toolset in *OpenAPI* JSON format, create a Custom GPT, and inject the schema to operate the kernel over the web.

### 2. Intervention Gateway (WA-Nexus)
Control your agent swarms from WhatsApp without standing in front of your PC.
- **Direct Messages (DMs):** Instant event-driven intervention. Message the AI and it responds frictionlessly.
- **Group Chats:** Requires the `Moskv-1` trigger at the start of the message to force a hardware interrupt and bypass defensive 5-minute polling.
- **Kernel Assistance:** Type `Moskv-tips` to receive architectural guidance and operational best practices.

### 3. Cheat Sheet: Thermodynamic Directives & Slash Commands
Executable commands from the agent interface (Antigravity) to govern the swarm:

- **⚡ Slash Commands:**
  - `/goal [task]` $\to$ Triggers continuous execution. The agent refactors or researches relentlessly until goal completion.
  - `/learn` $\to$ Crystallizes current context into permanent memory for future deployments.
  - `/schedule` $\to$ Schedules an agentic Cron Job (e.g., audit network every hour).
  - `/grill-me` $\to$ Inquisitor mode. Iterative interview to validate architecture before code generation.

- **🔥 Thermodynamic Triggers (Zero-Friction):**
  - `ULTRATHINK` $\to$ Forces model inference to collapse into physical code, eliminating generative entropy ("chatter").
  - `purga anergia` $\to$ Deterministic cleanup protocol to eradicate zombie files and dead code.
  - `deep research` $\to$ Triggers the AUTODIDACT-Ω engine for ultra-deep web research.

### 4. Zero-Friction Setup on Windows 10
If you lack a native UNIX environment (macOS/Linux), BABYLON-60 deploys on Windows without modifying environment variables:
1. Install **Python 3.12** from the **Microsoft Store** (auto-configures PATH).
2. Open PowerShell / cmd and run: `pip install cortex-persist`.
3. Launch interactive demo: `python -m babylon60.run_hero_demo`.

---

## 🗂️ Monorepo Map

```
BABYLON-60/
├── babylon60.rs              # Causal-Deterministic Kernel (bin: b60_kernel)
├── kernel/                   # Rust Crate: Low-level engine & WORM Quarantine
├── attestation/              # Rust Crate: TPM 2.0 PCR anchoring & P2P notary
├── compiler/                 # Rust Crate: B60 → IR compiler + Lean 4 backend
├── runtime/                  # Rust Crate: Coroutine runtime
├── proof_ir/                 # Rust Crate: Proof intermediate representation
├── strike_rs/                # Rust Crate: GIL bypass & exergy extraction (PyO3)
├── fuzz/                     # Rust Crate: Differential fuzzing
│
├── babylon60/                # Primary Python Package (cortex-persist)
│   ├── compliance_exporter/  # i18n EU AI Act certificate generator (ES, EN, DE, FR, IT)
│   ├── attestation/          # Merkle PCR Quote TPM 2.0 anchoring & P2P notary
│   └── primitives/           # F60 → GPU bf16 Serialization Boundary with SHA-256 checksum
│
├── causal_isomorphism/       # F# → Rust/Solidity Transpiler
├── timeline_ir/              # Temporal IR rendering backend
│
├── web/                      # React + WASM web interface
├── tonnetz_app/              # Neo-Riemannian harmonic spatial visualizer (Art. 14)
├── babylon60-ide/            # Dedicated Tauri IDE
│
├── hello_causal.b60          # DSL demonstration executable program
├── BabylonTrace.lean         # Lean 4 verified causality theorems
├── tests/                    # 301 automated tests (pytest + cargo test)
├── scripts/                  # CLI tools (run_hero_demo.py, export_country_compliance.py)
│
├── docs/                     # Full documentation & GTM portal (01-05)
│   ├── 01_spec/              # SPECIFICATION AND ARCHITECTURE
│   ├── 02_ontology/          # ONTOLOGY AND THREAT MODEL V4
│   ├── 03_guides/            # TUTORIALS AND ENTERPRISE QUICKSTART
│   ├── 04_research/          # TECHNICAL AND REGULATORY WHITEPAPERS
│   ├── 05_gtm/               # SALES PLAYBOOK, PITCH DECK AND VC DATA ROOM
│   └── audits/               # COMPLIANCE CERTIFICATE SAMPLES (ES, EN, DE, FR, IT)
│
├── Cargo.toml                # Rust Workspace v4.0.0
├── pyproject.toml            # cortex-persist v4.0.0
├── SPECIFICATION.md          # Formal Specification v4.0
├── LICENSE.md                # Sovereign Exclusion License v1.0
└── SECURITY.md               # Sovereign Security Policy
```

---

## 🛠️ Quick Start

```bash
# 1. Run Interactive Hero Demo Live
python3 scripts/run_hero_demo.py

# 2. Export Compliance Certificate for Spain (AESIA)
python3 scripts/export_country_compliance.py --locale es --output docs/audits/CERTIFICADO_ES.md

# 3. Run Test Suite (301 Tests)
uv run pytest tests/ -v

# 4. Build & Test Rust Workspace
cargo test --workspace

# 5. Formal Verification in Lean 4
lean BabylonTrace.lean
```

---

## 📜 License

**Sovereign Exclusion License v1.0** — Dual Licensing Model:

| Tier | Access | Requirement |
| :--- | :--- | :--- |
| **Sovereign** | Individuals, researchers, non-commercial use | Free — 100% Open Core |
| **Enterprise** | Corporations, commercial use, production | Cryptographic `CORTEX_LICENSE_KEY` |

See details in [LICENSE.md](./LICENSE.md) and [COMMERCIAL_LICENSE.md](./docs/COMMERCIAL_LICENSE.md).

---

## 🔒 Security

To report security vulnerabilities: **security@babylon60.com** (Do not use public GitHub Issues).  
SLA Commitment: acknowledgement < 24h, remediation < 72h.  
See [SECURITY.md](./SECURITY.md) and [Threat Model v4.0](./docs/02_ontology/security_threat_model_v4.md).

---

<sub>BABYLON-60 v4.0.0 Sovereign Hardened · Layer 0 Infrastructure for Verifiable AI Agents · Borja Moskv</sub>
