# 🛡️ BABYLON-60 Sovereign IDE (`babylon60-ide/`)

[![Tauri v2](https://img.shields.io/badge/Tauri-v2.0-blue?style=for-the-badge&logo=tauri)](https://tauri.app/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18-blue?style=for-the-badge&logo=react)](https://react.dev/)
[![IPC](https://img.shields.io/badge/IPC-Iceoryx2_Zero--Copy-orange?style=for-the-badge)](https://github.com/eclipse-iceoryx/iceoryx2)
[![Epistemology](https://img.shields.io/badge/Epistemology-C5--REAL_Categories-green?style=for-the-badge)](../docs/00_MANIFESTO.md)

The **BABYLON-60 Sovereign IDE** is a dedicated, multi-platform desktop and mobile development workspace built on **Tauri v2** and **FastAPI** (v0.4.0). It combines an **Industrial Noir UI** with an **AUTO_SOTA Model Router**, **Dual-Model Arena comparison**, and **Iceoryx2 zero-copy IPC** for real-time local model interaction and WORM Quarantine inspection.

---

## 🧮 C5-REAL Epistemological Context: Zero-Copy Interprocess Isomorphisms

Under the **C5-REAL Epistemological Constitution**:
- **Zero-Copy Memory Isomorphisms**: Iceoryx2 shared memory IPC forms a **Natural Isomorphism** between the Rust process host and the FastAPI sidecar backend, transferring zero-copy state objects without data serialization.
- **Model Router as Polynomial Co-Algebra Policy**: The AUTO_SOTA Model Router operates as a polynomial functor policy ($\text{Input} \to \text{Model\_Candidate}$), dynamically selecting model inference paths to minimize Free Energy Principle (FEP) cost divergence.
- **WORM Quarantine Inspection**: The IDE's `/api/v1/ledger` router provides a direct optic into WORM cryptographic state freezes, allowing developers to audit immutable failure evidence.

---

## 🏗️ Architecture & Backend API Router Matrix

```
┌─────────────────────────────────────────────────────────────────┐
│              Multi-Platform UI (Desktop & Mobile)               │
│                   React 18 + Vite Frontend                      │
├─────────────────────────────────────────────────────────────────┤
│            Tauri v2 Rust Core (IPC / Iceoryx2 / WORM)           │
├─────────────────────────────────────────────────────────────────┤
│             FastAPI Backend (Port 8000 / Uvicorn)               │
│ - OpenRouter Native API Bridge & SOTA Model Classifier          │
│ - Dual-Model Arena Evaluation & Streaming Telemetry             │
└─────────────────────────────────────────────────────────────────┘
```

### FastAPI Endpoint Routers (`backend/routes/`)

| Router | Endpoint Domain | Purpose |
| :--- | :--- | :--- |
| **`inference`** | `/api/v1/inference` | OpenRouter native streaming bridge & AUTO_SOTA model classifier. |
| **`ledger`** | `/api/v1/ledger` | WORM hash-chain audit log inspector (`cortex_ledger.py`). |
| **`sentinel`** | `/api/v1/sentinel` | Git Sentinel external witness monitoring and branch verification. |
| **`telemetry`** | `/api/v1/telemetry` | Live token throughput, latency metrics, and exergy consumption. |
| **`ontology`** | `/api/v1/ontology` | C5-REAL threat model ontology and regulatory constraint inspector. |
| **`query`** | `/api/v1/query` | L1 Sink SQLite vector/graph query interface. |
| **`delegation`**| `/api/v1/delegation` | Multi-agent task delegation and swarm execution control. |
| **`analytics`** | `/api/v1/analytics` | System health, memory footprint, and Landauer energy audit metrics. |

---

## ⚡ Multi-Platform Build Pipeline

The IDE builds natively across 5 target operating systems:

```bash
cd babylon60-ide

# 1. Run Development Server (Frontend + Backend)
npm run dev

# 2. Build macOS Universal Binary (.dmg / .app)
npm run build:mac

# 3. Build Windows Installer (.msi / .exe NSIS)
npm run build:win

# 4. Build Android Package (.apk / .aab)
npm run build:android

# 5. Build iOS Application (.app / .ipa)
npm run build:ios
```

---

## 📁 Monorepo Structure

```
babylon60-ide/
├── backend/                # FastAPI Python sidecar engine
│   ├── routes/             # 8 API routers (inference, ledger, sentinel, telemetry...)
│   ├── services/           # OpenRouter client, cortex_ledger, SOTA router logic
│   ├── main.py             # Uvicorn app entrypoint (FastAPI v0.4.0)
│   └── pyproject.toml      # Backend dependencies
├── frontend/               # React + Vite Industrial Noir UI
│   ├── src/                # Components, hooks, and views
│   └── package.json        # Frontend NPM script definitions
├── src-tauri/              # Tauri v2 Rust native shell
│   ├── src/                # IPC commands, window management, Iceoryx2 bridge
│   ├── tauri.conf.json     # Multiplatform build permissions & capabilities
│   └── Cargo.toml          # Rust dependencies
├── mcp.json                # Local MCP server registry
└── package.json            # Workspace orchestration commands
```

---

<sub>BABYLON-60 Sovereign IDE · Tauri v2 Substrate & Zero-Copy Memory Isomorphisms · Borja Moskv</sub>
