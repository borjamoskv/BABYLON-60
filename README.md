# BABYLON-60 v4.0 (Sovereign Hardened)

[🌐 Leer en Español](README_ES.md)

**Layer 0 Infrastructure for Verifiable AI Agents & EU AI Act Regulatory Compliance**

[![Version](https://img.shields.io/badge/Version-4.0.0--Sovereign--Hardened-black?style=for-the-badge)](https://github.com/borjamoskv/BABYLON-60)

[![Governance](https://img.shields.io/badge/Governance-C5--REAL-blue?style=for-the-badge)](./SECURITY.md)
[![License](https://img.shields.io/badge/License-Sovereign_Exclusion_v1.0-orange?style=for-the-badge)](./LICENSE)

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

## 📚 Monorepo Architecture & Subproject Index

| Subproject Module | Documentation README | Focus / Technology |
| :--- | :--- | :--- |
| **Rust Kernel** | [`kernel/`](./kernel/README.md) | `#![no_std]` Rust execution engine, $F_{60}$ scheduler, WORM quarantine. |
| **Cortex Substrate** | [`cortex/`](./cortex/README.md) | Python cognitive memory (`cortex-persist`), SQLite WAL, MCP Server. |
| **Sovereign IDE** | [`babylon60-ide/`](./babylon60-ide/README.md) | Desktop/Mobile Tauri v2 IDE, FastAPI OpenRouter backend, Iceoryx2 IPC. |
| **Web Telemetry UI** | [`web/`](./web/README.md) | React 18 + WASM Causal Telemetry visualizer & FSA API mount. |
| **Tonnetz Human Oversight**| [`tonnetz_app/`](./tonnetz_app/README.md) | Neo-Riemannian toric harmonic graph visualizer (EU AI Act Art. 14). |
| **Causal Attestation** | [`attestation/`](./attestation/README.md) | TPM 2.0 PCR Quote hardware notary & Merkle DAG state anchoring. |
| **DSL Compiler** | [`compiler/`](./compiler/README.md) | `.b60` DSL lexer/parser, B60 bytecode IR, Lean 4 proof emitter. |
| **Strike RS Acceleration**| [`strike_rs/`](./strike_rs/README.md) | PyO3 native GIL bypass, Iceoryx2 shared memory, BLAKE3 taint engine. |
| **Master Ledger BFT** | [`babylon60/bft/`](./babylon60/bft/README.md) | Escalón 3 Tamper-Evident log with Git Sentinel external witness. |
| **EVM On-Chain Notary** | [`anvil_yung/`](./anvil_yung/README.md) | Foundry smart contracts for EVM Merkle state root notarization. |
| **Causal Transpiler** | [`causal_isomorphism/`](./causal_isomorphism/README.md)| Functional F# domain kernel transpiler & linear type checker. |
| **Continuous Timeline IR** | [`timeline_ir/`](./timeline_ir/README.md) | Continuous-time state graph simulation kernel ($State(t)$). |
| **APEX Clinical Copilot** | [`docs/06_theory/`](./docs/06_theory/README_APEX.md) | Deterministic clinical-trial protocol amendment-risk copilot. |
| **Documentation Hub** | [`docs/`](./docs/README.md) | Central index for specifications, whitepapers, GTM playbooks. |

---

## 🕹️ Agent Integration & Command Console (Antigravity & WA-Nexus)

BABYLON-60 interfaces directly with your preferred AI stack to provide deterministic autonomy, "Deep Research" (AUTODIDACT-Ω), and zero-friction forced execution (ULTRATHINK).

### 1. LLM Injection (Model Context Protocol)
The kernel exposes its local tool arsenal via the MCP standard (`cortex_mcp_server.py`):
- **For Claude Code & Cursor/Codex:** Native MCP support. Add the local server in settings to inherit WORM Quarantine shielding.
- **For ChatGPT (Web):** Export BABYLON-60's toolset in *OpenAPI* JSON format to operate the kernel over the web.

### 2. Intervention Gateway (WA-Nexus)
Control your agent swarms from WhatsApp without standing in front of your PC.
- **Direct Messages (DMs):** Instant event-driven intervention.
- **Group Chats:** Requires the `Moskv-1` trigger at the start of the message to force a hardware interrupt.
- **Kernel Assistance:** Type `Moskv-tips` to receive architectural guidance.

### 3. Cheat Sheet: Thermodynamic Directives & Slash Commands

- **⚡ Slash Commands:**
  - `/goal [task]` $\to$ Triggers continuous execution until goal completion.
  - `/learn` $\to$ Crystallizes current context into permanent memory.
  - `/schedule` $\to$ Schedules an agentic Cron Job (e.g., audit network every hour).
  - `/grill-me` $\to$ Inquisitor mode. Iterative interview to validate architecture before code generation.

- **🔥 Thermodynamic Triggers (Zero-Friction):**
  - `ULTRATHINK` $\to$ Forces model inference to collapse into physical code, eliminating generative entropy.
  - `purga anergia` $\to$ Deterministic cleanup protocol to eradicate zombie files and dead code.
  - `deep research` $\to$ Triggers the AUTODIDACT-Ω engine for ultra-deep web research.

---

## 🛠️ Quick Start

```bash
# 1. Run Interactive Hero Demo Live
python3 scripts/run_hero_demo.py

# 2. Export Compliance Certificate for Spain (AESIA)
python3 scripts/export_country_compliance.py --locale es --output docs/audits/CERTIFICADO_ES.md

# 3. Kimi Nexus MCP Server (Moonshot Integration)
export KIMI_API_KEY="sk-..."
uvicorn kimi_nexus.kimi_nexus:app --host 127.0.0.1 --port 8050

# 4. Run Test Suite (301 Tests)
uv run pytest tests/ -v

# 4. Build & Test Rust Workspace
cargo test --workspace

# 5. BABYLON IDE v0.4.0 (Multi-Platform Desktop & Mobile Installables)
cd babylon60-ide
npm run dev           # Launch Development IDE
npm run build:mac     # Build macOS Universal Binary (.dmg / .app)
npm run build:win     # Build Windows Installer (.msi / .exe NSIS)
npm run build:android # Build Android Package (.apk / .aab)
npm run build:ios     # Build iOS Application (.app / .ipa)

# 6. Verify Formal Lean 4 Theorems
lean BabylonTrace.lean
```

---

## 📜 License

**Sovereign Exclusion License v1.0** — Dual Licensing Model:

| Tier | Access | Requirement |
| :--- | :--- | :--- |
| **Sovereign** | Individuals, researchers, non-commercial use | Free — 100% Open Core |
| **Enterprise** | Corporations, commercial use, production | Cryptographic `CORTEX_LICENSE_KEY` |

See details in [LICENSE](./LICENSE) and [COMMERCIAL_LICENSE.md](./docs/COMMERCIAL_LICENSE.md).

---

## 🔒 Security

To report security vulnerabilities: **security@babylon60.com** (Do not use public GitHub Issues).  
SLA Commitment: acknowledgement < 24h, remediation < 72h.  
See [SECURITY.md](./SECURITY.md) and [Threat Model v4.0](./docs/02_ontology/security_threat_model_v4.md).

---

<sub>BABYLON-60 v4.0.0 Sovereign Hardened · Layer 0 Infrastructure for Verifiable AI Agents · Borja Moskv</sub>
