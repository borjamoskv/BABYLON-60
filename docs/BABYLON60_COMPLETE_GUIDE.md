# BABYLON·60 — COMPLETE ARCHITECTURE & DEVELOPER GUIDE
## v1.1.0 · Sovereign Agentic IDE & Monorepo Ecosystem

This document serves as the absolute single source of truth for the architecture, capabilities, layout, API contracts, and packaging workflow of the **BABYLON·60** ecosystem.

---

## 🏛️ 1. PHILOSOPHY & DESIGN SYSTEM

BABYLON·60 is built under the **Industrial Noir 2026** design aesthetic, prioritizing high cognitive focus, minimal distraction, and rich tactile feedback.

### 🎨 YInMn Blue Color System & Luminance Tokens
The interface utilizes a curated palette derived from YInMn Blue, optimized to prevent contrast glare while maintaining crisp definition:

* **Backgrounds (Surfaces)**:
  * `--bitumen: #090B19` (The primary dark workspace void, preventing pixel halation).
  * `--kiln: #0F1226` (Sidebar and navigation background).
  * `--tablet: #151A33` (Card and panel backgrounds).
  * `--tablet-2: #1D2342` / `--tablet-3: #262E52` (Accent surfaces and active states).
* **Borders & Dividers**:
  * `--edge: #2E3866` (High-definition borders).
  * `--edge-soft: #20274D` (Subtle internal division lines).
* **Text & Contrast Elements**:
  * `--dust: #FFFFFF` (Pure white for maximum readability).
  * `--dust-dim: #B4B9DF` (Muted gray/blue for secondary information).
  * `--dust-faint: #676E99` (Disabled or meta descriptions).
  * `--dust-ghost: #3E4473` (Decorative details and labels).
* **Accents & Glowing Semantics**:
  * `--lapis: #3B4DFF` (Brighter accent cobalt blue).
  * `--lapis-bright: #7080FF` (Highlight accent).
  * `--lapis-glow: rgba(59, 77, 255, 0.22)`.
  * `--gold: #F59E0B` (Warning/Ledger state badge).
  * `--verify: #10B981` (C5-REAL verification green).
  * `--break: #EF4444` (Assertion failure / compile breakage red).

---

## 🧠 2. DUAL COGNITIVE ARCHITECTURE (TDAH + AACC)

The frontend implements two discrete cognitive modes to accommodate different developer neurologies, toggled dynamically via **`⌘⇧E`** or the status bar switch.

### ◐ MODE 2E (Doble Excepcionalidad / ADHD + AACC)
Designed for developers requiring continuous peripheral feedback and flow state guards:
* **Ambient Tachometer**: A 3px top-screen bar that reflects agent state in real-time (`indexing` = breathing blue, `working` = scanning cobalt, `alert` = fast breathing gold, `done` = fading green).
* **Icon-Only Spine**: Sidebar navigation is icon-only to eliminate text-label noise. Labels are revealed as tooltips or hover effects.
* **Onboarding & Quick Presets**: Built-in template buttons to bypass the cold-start problem of empty inputs.
* **Intervention Guard**: Proactive modal overlays that lock input and alert the user if an infinite loop or duplicate operations are detected.

### ○ MODE NT (Neurotypical)
A traditional, standard-density layout:
* Navigation elements include both icons and text labels.
* Ambient signals (Tachometer, intervention banners) are hidden.
* Standard desktop spacing.

---

## 🛜 3. BACKEND ROUTES & API CONTRACTS

The backend is built with FastAPI and runs on a local loopback address, enforcing the **Zero-Network Policy** (no outbound telemetry or external internet calls).

### ⧉ Ledger Inspection (`/api/ledger/*`)
* `GET  /api/ledger/stats`
  * Returns: `{exists: bool, db_path: str, entries: int, latest: {entry_hash: str, lamport_t: int, created_at: str}}`
* `GET  /api/ledger/entries?limit=N&offset=M`
  * Returns a paginated list of all state transition ledger entries.
* `GET  /api/ledger/entry/{seq}`
  * Retrieves the full raw payload and cryptographic signatures of a specific block sequence.
* `POST /api/ledger/verify`
  * Triggers a sychronous validation of all hashes in the ledger chain. Returns sequence breakage index if corrupted.

### ⛁ Ontologies & Databases (`/api/databases/*`)
* `GET  /api/databases`
  * Lists all local database ontologies, paths, and human-readable sizes.
* `GET  /api/databases/{db}/tables`
  * Lists all tables and row counts inside a specific database file.
* `GET  /api/databases/{db}/schema/{table}`
  * Retrieves details for all columns (Primary Keys, nullability, data types).
* `POST /api/query`
  * Body: `{database: str, sql: str}`
  * Executes a read-only SQL query against the selected database and returns structured table rows.

### ◈ Local Inference API (`/api/inference/*`)
* `GET  /api/inference/local/status`
  * Checks if local inference services (such as Ollama daemon) are active, returning list of downloaded models.
* `POST /api/inference/local/generate`
  * Body: `{prompt: str, model: str, max_tokens: int}`
  * Connects to local model provider (Ollama/MLX) and stream-generates output text.
* `POST /api/inference/local/mamba/generate`
  * Body: `{prompt: str, max_tokens: int}`
  * Directly drives the local **Mamba SSM Ledger Engine** and logs generated state nodes into the GraphLedger.

---

## ⚡ 4. LOCAL INFERENCE CONSOLE & USABILITY FEATURES

Accessible via **`⌘ 8`** or by clicking the diamond icon (`◈`) in the sidebar, the **Local Inference Console** is optimized for immediate, intuitive testing of silicon models:

### 🧩 Core UX Features
* **Click-to-Load Preset Templates**: Includes 3 ready-made presets below the prompt label:
  * `⚡ Robinson Theorem`: Fills prompt with: *"Explain the core of the Robinson-Moskv theorem"*
  * `🛡 Attest Ledger`: Fills prompt with: *"Attest current ledger transaction status"*
  * `◈ Self-Audit`: Fills prompt with: *"Run self-audit loop on active workspace"*
* **Fast Submit Keybinding**: Pressing **`Enter`** in the prompt textarea triggers immediate prompt execution. Pressing **`Shift + Enter`** inserts a standard newline.
* **Onboarding Help Widget**: The right-hand column presents a visual card detailing step-by-step instructions on how local generation works and how each token is verified to the tamper-evident state chain.
* **Real-time Performance Tachometer**: Displays the throughput (tokens per second) and latency (in milliseconds) of the local execution.

---

## 📦 5. MAC APP PACKAGING & DMG BUILD PIPELINE

BABYLON·60 is compiled into a standalone desktop application using **Tauri v2** and **Rust**.

### ⚙️ Build Requirements
* The Tauri configuration is stored in [babylon60-ide/src-tauri/tauri.conf.json](file:///Users/borjafernandezangulo/10_PROJECTS/Teorema-Robinson-Moskv/babylon60-ide/src-tauri/tauri.conf.json).
* A unique bundle identifier is required: `"identifier": "com.babylon60.ide"`.
* System icons must be generated from the square source image `public/logo_icon.jpg` using the Tauri CLI:
  ```bash
  cd babylon60-ide && npx --package @tauri-apps/cli tauri icon ../public/logo_icon.jpg
  ```
  This generates all PNG sizes, `icon.icns` for macOS, and `icon.ico` for Windows in `src-tauri/icons/`.

### 🏗️ Compilation & DMG Generation Command
The release build compiles all Rust crate dependencies in release mode and packages the macOS bundle:
```bash
cd babylon60-ide && npx --package @tauri-apps/cli tauri build
```
The output assets are compiled to:
* **macOS Bundle**: `babylon60-ide/src-tauri/target/release/bundle/macos/BABYLON60.app`
* **DMG Installer**: `babylon60-ide/src-tauri/target/release/bundle/dmg/BABYLON60_0.1.0_aarch64.dmg`

---

## 🛡️ 6. SECURITY & EPISTEMIC AUDITING

The repository enforces strict BFT (Byzantine Fault Tolerance) consistency checks to protect against code-injection and credential leakage:

### 🔍 Secret Swarm Auditor (`scripts/secret_swarm_auditor.py`)
Scans all active project directories (excluding `.venv`, `node_modules`, `dist`, and `target`) for high-entropy strings and hardcoded credentials (AWS, RSA private keys, JWTs, Github tokens, Google APIs).
* Run command: `python3 scripts/secret_swarm_auditor.py`
* Enforces entropy threshold $> 4.8$ for any word token longer than 20 characters.

### 🧪 Test & Regress Verification
The entire test suite compiles and runs against the isolated virtual environment `.venv` interpreter (Python 3.12/3.14):
* **Execution**: `.venv/bin/pytest tests/ -v`
* Evaluates 195 test files verifying state nodes, memory shields, Mamba layer integration, and F# domain automata.
