# 🛡️ BABYLON-60 Sovereign IDE (`babylon60-ide/`)

[![Tauri v2](https://img.shields.io/badge/Tauri-v2.0-blue?style=for-the-badge&logo=tauri)](https://tauri.app/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18-blue?style=for-the-badge&logo=react)](https://react.dev/)
[![IPC](https://img.shields.io/badge/IPC-Iceoryx2_Zero--Copy-orange?style=for-the-badge)](https://github.com/eclipse-iceoryx/iceoryx2)

The **BABYLON-60 Sovereign IDE** is a dedicated, multi-platform desktop and mobile development workspace built on **Tauri v2** and **FastAPI**. It combines an **Industrial Noir UI** with an **AUTO_SOTA Model Router**, **Dual-Model Arena comparison**, and **Iceoryx2 zero-copy IPC** for real-time local model interaction and WORM Quarantine inspection.

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│              Multi-Platform UI (Desktop & Mobile)               │
│                   React 18 + Vite Frontend                      │
├─────────────────────────────────────────────────────────────────┤
│            Tauri v2 Rust Core (IPC / Iceoryx2 / WORM)           │
├─────────────────────────────────────────────────────────────────┤
│             FastAPI Backend (Port 8000 / Uvicorn)               │
│ - OpenRouter Native API Bridge                                  │
│ - AUTO_SOTA Model Classifier & Cost Optimizer                   │
│ - Dual-Model Arena Evaluation & Streaming Telemetry             │
└─────────────────────────────────────────────────────────────────┘
```

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

## 🎯 Key Features

1. **AUTO_SOTA Classifier**: Automatically selects the optimal AI model (Claude 3.5 Sonnet, GPT-4o, DeepSeek R1) based on task complexity, token count, and cost efficiency.
2. **Dual-Model Arena**: Run parallel prompts across two model candidates simultaneously with side-by-side diffing and zero-latency streaming.
3. **Iceoryx2 Zero-Copy IPC**: Shared-memory microsecond messaging between Rust process host and Python sidecar backend.
4. **Model Context Protocol (MCP) Integration**: Native loader for local MCP servers (`mcp.json`).

---

## 📁 Monorepo Structure

```
babylon60-ide/
├── backend/                # FastAPI Python sidecar engine
│   ├── routes/             # API endpoints (completion, routing, arena)
│   ├── services/           # OpenRouter client & SOTA router logic
│   ├── main.py             # Uvicorn app entrypoint
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

<sub>BABYLON-60 Sovereign IDE · Tauri v2 Substrate · Borja Moskv</sub>
