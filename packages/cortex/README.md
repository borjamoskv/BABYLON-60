# 🧠 CORTEX Substrate (`packages/cortex/`)

[![PyPI Version](https://img.shields.io/badge/PyPI-cortex--persist-blue?style=for-the-badge&logo=pypi)](https://pypi.org/project/cortex-persist/)
[![MCP Server](https://img.shields.io/badge/MCP-Model_Context_Protocol-purple?style=for-the-badge)](../babylon60/mcp/cortex_mcp_server.py)
[![AST Markov Blanket](https://img.shields.io/badge/Markov_Blanket-Chaos_Monad_AST-orange?style=for-the-badge)](../babylon60/cortex/cortex_chaos_monad.py)
[![Epistemology](https://img.shields.io/badge/Epistemology-Store_Comonad-green?style=for-the-badge)](../../docs/00_MANIFESTO.md)

**CORTEX** (`cortex-persist`) is the Python persistence, AST Markov Blanket isolation, and cognitive memory substrate for **BABYLON-60**. It provides autopoietic swarm orchestration (`moskv-swarm`), vector/graph comonadic memory (`L1_sink`), the **Chaos Monad AST Markov Blanket** (`cortex_chaos_monad.py`), and the Model Context Protocol (MCP) Markov Blanket interface (`cortex_mcp_server.py`) for Claude Code, Cursor, and ChatGPT.

---

## 🧮 C5-REAL Epistemological Context: Store Comonad & Chaos Monad Sandbox

Under the **C5-REAL Epistemological Constitution**:
- **Memory as a Store Comonad**: Memory is not a static disk container; it is the execution of a **Store Comonad** (`get/set` operators). Remembering is the amalgamation of past trajectories into an emergent **Colimit** without storing static spatial copies.
- **Chaos Monad AST Sandbox (`cortex_chaos_monad.py`)**: Before code execution reaches the Rust kernel, Python source input passes through `validate_ast_sandbox()`. It enforces `RULE_AST_REFLECT_01`, rejecting introspection escapes, dunder attribute access (`__class__`, `__subclasses__`), and forbidden reflection functions (`eval`, `exec`, `getattr`, `setattr`), emitting structured `ScittResult` receipts.
- **Context as a Bayesian Lens**: Context is a **Fibrated Projection (Adjoint Functor)** filtering relevant topological submanifolds without breaking structural integrity.

---

## 🎯 Architecture & Components

```
┌─────────────────────────────────────────────────────────────┐
│           Model Context Protocol (MCP Markov Blanket)       │
├─────────────────────────────────────────────────────────────┤
│   Chaos Monad AST Sandbox (cortex_chaos_monad.py)           │
│   - validate_ast_sandbox() & RULE_AST_REFLECT_01           │
│   - ScittResult: ["Success", "SecurityError", "Falsified"]  │
├─────────────────────────────────────────────────────────────┤
│               Moskv-Swarm Autopoietic Orchestrator          │
├──────────────────────────────┬──────────────────────────────┤
│  L1 Sink Deterministic Store │ Vector & Graph Topological DB│
│  (SQLite WAL + Hash-Chain)   │  (cortex_memory.db)          │
└──────────────────────────────┴──────────────────────────────┘
```

- **Chaos Monad Sandbox (`cortex_chaos_monad.py`)**: Static AST analyzer blocking memory escapes and introspection injections before kernel evaluation.
- **Moskv Swarm (`agents/` & `moskv-swarm/`)**: Orchestrates autopoietic swarm tasks with deterministic exergy bounds.
- **L1 Sink Persistence (`L1_sink/`)**: Single-writer SQLite WAL causal ledger holding the Merkle-Causal DAG log.
- **Cortex MCP Server (`cortex_mcp_server.py`)**: Standard MCP Markov Blanket exposing WORM Quarantine, F60 scheduling, and exergic physical tool execution to AI agents.

---

## 🚀 Quick Start

### Installation

```bash
# Install via pip
pip install cortex-persist

# Run Cortex MCP Server
python3 -m babylon60.cortex_mcp_server

# Run AST Sandbox Evasion Test Suite (18 Tests)
pytest tests/test_ast_sandbox_evasion.py
```

---

## 📁 Subdirectory Map

```
packages/cortex/
├── agents/             # Autopoietic agent definitions & prompt templates
├── audits/             # YAML audit reports of Causal-Determinist consolidations (C5-REAL)
├── engine/             # Core BFT causal ledgers (nexus_anchors.db)
├── infra/              # Low-level SQLite database connectors & WAL triggers
├── L1_sink/            # Primary persistent storage sink (Colimit Event Sourcing)
└── moskv-swarm/        # Autopoietic swarm coordination protocols (Polynomial Functors)
```

---

<sub>BABYLON-60 Cortex Substrate · Cognitive Store Comonad & Chaos Monad Sandbox · Borja Moskv</sub>
