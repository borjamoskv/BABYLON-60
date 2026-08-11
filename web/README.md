# 🌐 BABYLON-60 Web Substrate (`web/`)

[![Framework](https://img.shields.io/badge/React-18.3-blue?style=for-the-badge&logo=react)](https://react.dev/)
[![Build Tool](https://img.shields.io/badge/Vite-5.4-purple?style=for-the-badge&logo=vite)](https://vitejs.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.5-blue?style=for-the-badge&logo=typescript)](https://www.typescriptlang.org/)
[![WASM Engine](https://img.shields.io/badge/WASM-Rust_Core-orange?style=for-the-badge)](../rust-core)

The **BABYLON-60 Web Dashboard** is a high-performance, **Industrial Noir** web interface engineered with React 18, TypeScript, and WebAssembly (WASM). It provides real-time causal graph rendering, local file system mounting via the File System Access API, and direct telemetry bridges to the **Cortex Engine** (`lm-bridge.ts`).

---

## 🎯 Architecture & Client Features

```
┌─────────────────────────────────────────────────────────────┐
│                   React 18 / Vite Client                    │
├──────────────────────────────┬──────────────────────────────┤
│   Canvas UI (ADHD Mode)      │   FileSystem Access (FSA API)│
├──────────────────────────────┼──────────────────────────────┤
│   Cortex SSE Stream Bridge   │   Rust WASM Telemetry Core   │
│   (cortex/lm-bridge.ts)      │   (rust-core)                │
└──────────────────────────────┴──────────────────────────────┘
```

- **Industrial Noir Canvas UI (`ui/Canvas.tsx`)**: Real-time interactive spatial canvas rendering state transitions, timeline IR nodes, and causal graphs.
- **Local File System Access (`io/fs-access.ts`)**: Frictionless local workspace mounting using native browser FS APIs (`Cmd + O` / `Ctrl + O`).
- **Cortex Neural Bridge (`cortex/lm-bridge.ts`)**: Direct connectivity to local LLMs (LM Studio / Ollama / Cortex MCP Server at `http://localhost:1234/v1`).
  - `checkCortexStatus()`: Instant heartbeat status polling.
  - `streamCompletion(messages, signal, onChunk)`: Zero-latency Server-Sent Events (SSE) chat completion stream parser.
- **Rust WASM Acceleration (`rust-core`)**: In-browser zero-copy evaluation of Merkle DAG chains and sexagesimal arithmetic checks.

---

## 🚀 Quick Start

### Prerequisites
- **Node.js**: `>= 18.0.0`
- **npm**: `>= 9.0.0`

### Installation & Run

```bash
# Navigate to web directory
cd web

# Install dependencies
npm install

# Start Vite Development Server
npm run dev
```

Open [http://localhost:5173](http://localhost:5173) in your browser.

---

## ⌨️ Keyboard Shortcuts

| Shortcut | Action |
| :--- | :--- |
| <kbd>Cmd</kbd> + <kbd>O</kbd> / <kbd>Ctrl</kbd> + <kbd>O</kbd> | Mount local workspace folder via File System Access API (`mountProject`) |
| <kbd>Esc</kbd> | Reset canvas layout / center view |

---

## 📁 Directory Structure

```
web/
├── public/                 # Static assets & WASM binaries
├── rust-core/              # Rust WASM compilation target
├── src/
│   ├── assets/             # Branding icons & SVGs
│   ├── cortex/             # lm-bridge.ts (SSE streaming client & status checker)
│   ├── io/                 # fs-access.ts (File System Access API wrappers)
│   ├── ui/                 # Canvas.tsx components & telemetry widgets
│   ├── App.css             # Tailwind/Custom Industrial Noir styling
│   ├── App.tsx             # Main layout & event router
│   └── main.tsx            # React entrypoint
├── package.json            # Node project configuration
└── vite.config.ts          # Vite build & WASM plugin config
```

---

## 🛠️ Production Build

```bash
# Build static assets & WASM bundle
npm run build

# Preview production build locally
npm run preview
```

---

<sub>BABYLON-60 Web Substrate · Industrial Noir UI · Borja Moskv</sub>
