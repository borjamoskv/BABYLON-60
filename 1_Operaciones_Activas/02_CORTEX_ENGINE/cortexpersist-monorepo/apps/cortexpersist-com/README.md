# CORTEX-Persist Monorepo

<div align="center">

**[ C5-REAL EXECUTION METRICS & STATUS ]**

[![CI](https://img.shields.io/github/actions/workflow/status/borjamoskv/Cortex-Persist/ci.yml?style=for-the-badge&label=CI)](https://github.com/borjamoskv/Cortex-Persist/actions)
[![PyPI](https://img.shields.io/pypi/v/cortex-persist?style=for-the-badge&color=blue)](https://pypi.org/project/cortex-persist/)
[![Python](https://img.shields.io/pypi/pyversions/cortex-persist?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Downloads](https://img.shields.io/pypi/dm/cortex-persist?style=for-the-badge&color=blueviolet)](https://pypistats.org/packages/cortex-persist)

[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json&style=for-the-badge)](https://github.com/astral-sh/ruff)
[![Mypy](https://img.shields.io/badge/types-Mypy-blue.svg?style=for-the-badge)](https://mypy-lang.org/)
[![Security: Bandit](https://img.shields.io/badge/security-bandit-yellow.svg?style=for-the-badge)](https://github.com/PyCQA/bandit)
[![Docs](https://img.shields.io/badge/docs-GitHub-blue?style=for-the-badge)](https://github.com/borjamoskv/Cortex-Persist/tree/main/docs)

[![GitHub Stars](https://img.shields.io/github/stars/borjamoskv/Cortex-Persist?style=for-the-badge)](https://github.com/borjamoskv/Cortex-Persist/stargazers)
[![Commit Activity](https://img.shields.io/github/commit-activity/m/borjamoskv/Cortex-Persist?style=for-the-badge)](https://github.com/borjamoskv/Cortex-Persist/commits)
[![Last Commit](https://img.shields.io/github/last-commit/borjamoskv/Cortex-Persist?style=for-the-badge)](https://github.com/borjamoskv/Cortex-Persist/commits)
[![Issues](https://img.shields.io/github/issues/borjamoskv/Cortex-Persist?style=for-the-badge)](https://github.com/borjamoskv/Cortex-Persist/issues)

[![License](https://img.shields.io/github/license/borjamoskv/Cortex-Persist?style=for-the-badge)](https://github.com/borjamoskv/Cortex-Persist/blob/main/LICENSE)
[![Sponsor](https://img.shields.io/badge/Sponsor-borjamoskv-ff69b4?style=for-the-badge&logo=githubsponsors&logoColor=white)](https://github.com/sponsors/borjamoskv)
</div>

---

## 🛠️ What is CORTEX-Persist?

**CORTEX-Persist** is an immutable cryptographic infrastructure designed for AI agents. Every Language Model (LLM) call, logical decision, or memory state change is transparently wrapped to generate an audit log chained by hash (SHA-256) and digitally signed (Ed25519), guaranteeing non-repudiation and mathematical verification of autonomous operations.

### The Intuitive Matrix

| AI Industry Norm (Anergy) | CORTEX-Persist (Exergy) | Physical Anchor |
| :--- | :--- | :--- |
| **"Trust me" AI** | **Cryptographic Ledger** | **The Black Box (Flight Recorder):** You wouldn't let a commercial jet fly without a black box. Why let an AI execute code or spend capital without one? Every decision is signed in blood. |
| **Data Hoarding (Vector DBs)** | **Thermodynamic Decay** | **Biological Forgetting (Metabolism):** Standard DBs hoard useless data forever. Cortex uses *Ouroboros*. If an idea doesn't generate friction, it rots and is purged. |
| **Unchecked Hallucination** | **Semantic Friction ($H$)** | **The Tension Detector:** Mathematically measures if an agent diverges from its own historical logic. |

This repository is a monorepo containing the source code for production Node.js packages as well as the interactive visual portal and integrations.

---

## 📂 Monorepo Structure

```text
/
├── packages/
│   ├── cortex-persist/            # Core NPM SDK (SHA-256 Ledger, Ed25519, Friction & Engine)
│   └── cortex-persist-langchain/  # Integration middleware for LangChain
├── src/                           # Visual Portal / C5-REAL Metrics Dashboard (Astro + React + Three.js)
│   ├── pages/                     # Routes and visualization interfaces (simulation, forensics, audit)
│   ├── components/                # Interactive components and graphical UIs
│   └── styles/                    # CSS styles based on the Industrial Noir 2026 design system
└── public/                        # Public and static resources for the frontend
```

---

## 🗺️ Architecture Map and Data Flow

The CORTEX-Persist ecosystem is subdivided into three interconnected operational layers: **Core SDK**, **Telemetry Portal (Frontend)**, and the **Entropy Daemon (Ouroboros)**.

```mermaid
graph TD
    %% Node Styles
    classDef core fill:#2B3BE5,stroke:#fff,stroke-width:2px,color:#fff;
    classDef ext fill:#0A0A0A,stroke:#2B3BE5,stroke-width:2px,color:#fff;
    classDef daemon fill:#E52B50,stroke:#fff,stroke-width:1px,color:#fff;

    %% External/Client Layer
    LLM["Async LLM Call / Agent Decision"]:::ext
    
    %% Core SDK Layer
    subgraph SDK_Core ["Cortex-Persist SDK"]
        Wrap["cortexWrap()"]:::core
        Ledger["CortexLedger (JSONL File)"]:::core
        Signer["CortexSigner (Ed25519)"]:::core
        Friction["Friction (⊗ Tension Metric)"]:::core
        Engine["CortexEngine (Decay/Bifurcation)"]:::core
    end

    %% Frontend Layer
    subgraph Frontend ["Astro / React / ThreeJS Portal"]
        Pages["Astro Pages (src/pages/)"]:::ext
        Comps["React UI & Telemetry Components"]:::ext
        FrictionLib["CortexFriction Client-Side"]:::ext
    end

    %% Daemons Layer
    subgraph Daemons ["Entropy Loop"]
        Verify["cortex.py (Integrity Verify)"]:::daemon
        Ouroboros["ouroboros_entropy_daemon.py"]:::daemon
        Graveyard[".entropy_graveyard/"]:::daemon
    end

    %% Data Flows
    LLM -->|Wrap Call| Wrap
    Wrap -->|Generate Hashes| Ledger
    Wrap -->|Sign Entry| Signer
    Ledger -->|Append signed entry| Ledger
    
    LLM -->|Interpretation Vectors| Friction
    Friction -->|Shannon Entropy H| Engine
    Engine -->|Enforce Hot Nodes| Ledger
    
    %% Telemetry Flows
    Pages -->|CortexFriction.ping()| FrictionLib
    FrictionLib -->|Write ping telemetry| Ledger
    
    %% Ouroboros Loop
    Ouroboros -->|Read pings/tags| Ledger
    Ouroboros -->|Decay mtime / battery| Pages
    Ouroboros -->|Move inactive files| Graveyard
    Verify -->|C5-REAL Integrity Check| Ledger
```

---

## ⚙️ Process Matrix and Control Flow

| Component | Origin File | Input | Output | C5-REAL Function |
| :--- | :--- | :--- | :--- | :--- |
| **`cortexWrap`** | `middleware.ts` | Async Function / Config | Audited Function | Intercepts agent calls, executes hash chaining, and validates signatures. |
| **`CortexLedger`** | `ledger.ts` | JSON Payload | Cryptographic Block | Local/BYOC auto-sequenced JSONL persistence and $O(1)$ verification. |
| **`CortexSigner`** | `signer.ts` | PEM Keys / Block Data | Ed25519 Signature | Generates non-repudiation digital signature. |
| **`Friction`** | `friction.ts` | Interpretation Vectors | $H$ (Shannon Entropy) | Measures interpretive divergence (cosine distance) between agents. |
| **`CortexEngine`** | `engine.ts` | Concepts / Entropy | Decay / Bifurcated Nodes | Maintains active thermodynamic memory. Purges fictional stability. |
| **`Dogfooding`** | `dogfooding.ts` | File list / Stances | Diagnostic Report / Friction | Self-audits core ledger health and simulates cognitive autopoiesis. |
| **`Ouroboros`** | `ouroboros_entropy_daemon.py` | `.cortex_ledger.json` / tags | Active workspace / Graveyard | Purges inactivity. Deletes files without the `@C5-REAL` survival tag after 72h. |

---

## ⚡ The Williamsburg Lifecycle (Code Survival)

Files in the `/src` directory are subject to continuous thermal energy decay. To prevent purging, the system requires real friction or explicit declaration:

```yaml
Friction_Paths:
  Active:
    Survival_Metric: ping() registered in Ledger in the last 72 hours.
    Check_Type: Dynamic C5-REAL.
  Static:
    Survival_Metric: Insertion of the '// @C5-REAL' tag in the file.
    Check_Type: Static C5-REAL (Immune to decay).
  Purged:
    Condition: Inactivity > 72h without a survival tag.
    Action: Preventive relocation to '.entropy_graveyard/'.
```

---

## ⚖️ License and Open Source Compliance

> [!IMPORTANT]
> **CORTEX-Persist is a Sovereign Open Source project under the MIT License.**
> T
To prevent the common confusion that mere visibility on GitHub confers implicit permissions, we formally declare:

* **Open Source License**: All code in this monorepo is licensed under the [MIT License](file:///Users/borjafernandezangulo/10_PROJECTS/Teorema-Robinson-Moskv/1_Operaciones_Activas/02_CORTEX_ENGINE/cortexpersist-com/LICENSE).
* **Rights Granted**: You have explicit legal permission to copy, modify, integrate into proprietary software, sub-license, and commercially distribute any part of this system without cost.
* **Single Condition**: Retain the original copyright notice and license by Borja Moskv in any substantial copy of the code.
* **Cryptographic Integrity**: Signatures generated by the SDK (`CortexSigner`) are valid for public audit and are compatible with any runtime environment supporting the official MIT specification.

---

## 🧞 Command Guide for the Visualization Portal (Astro)

The main portal runs using **Astro 6** and **Tailwindcss 4**.

All operations are executed from the project root:

| Command | Action |
| :--- | :--- |
| `npm install` | Installs dependencies at the root and links subpackages |
| `npm run dev` | Starts the local development server at `localhost:4321` |
| `npm run build` | Compiles the production application into the `./dist/` directory |
| `npm run preview` | Locally previews the production build before deployment |
| `npm run dogfood` | Runs the `DogfoodingAgent` self-audit tool in the local console |

### Development Dependency Setup
If you are working on the subpackages, you can install and build their execution environments directly:
```bash
# Build core package
cd packages/cortex-persist
npm run build
```

---

## ⊗ Core Mathematical Architecture

The system operates under three fundamental pillars supporting persistence in the agent:

1. **`CortexLedger`**: JSONL blockchain structure. Each block contains:
   $$\text{Hash} = \text{SHA-256}(\text{prev\_hash} \parallel \text{timestamp} \parallel \text{agent\_id} \parallel \text{action} \parallel \text{payload})$$
2. **`Friction` (Semantic Friction)**: Evaluates interpretive divergence using cosine distances and integrates Shannon entropy ($H$) to calibrate decision tensions.
3. **`CortexEngine`**: Thermodynamic daemon that decays consensus and amplifies conflict, bifurcating concepts when friction exceeds the critical threshold ($T_{\text{hot}}$).

For practical examples of using the SDK in Node.js, see the [cortex-persist README](file:///Users/borjafernandezangulo/10_PROJECTS/Teorema-Robinson-Moskv/1_Operaciones_Activas/02_CORTEX_ENGINE/cortexpersist-com/packages/cortex-persist/README.md).
