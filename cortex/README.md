# 🧠 CORTEX Substrate (`cortex/`)

[![PyPI Version](https://img.shields.io/badge/PyPI-cortex--persist-blue?style=for-the-badge&logo=pypi)](https://pypi.org/project/cortex-persist/)
[![MCP Server](https://img.shields.io/badge/MCP-Model_Context_Protocol-purple?style=for-the-badge)](../docs/03_guides/cortex_mcp_guide.md)
[![Python 3.12](https://img.shields.io/badge/Python-3.12%2B-blue?style=for-the-badge&logo=python)](https://www.python.org/)

**CORTEX** (`cortex-persist`) is the Python persistence and cognitive memory substrate for **BABYLON-60**. It provides multi-agent swarm orchestration (`moskv-swarm`), vector/graph persistent memory (`L1_sink`), and the Model Context Protocol (MCP) server interface (`cortex_mcp_server.py`) for Claude Code, Cursor, and ChatGPT.

---

## 🎯 Architecture & Components

```
┌─────────────────────────────────────────────────────────────┐
│                 Model Context Protocol (MCP Server)         │
├─────────────────────────────────────────────────────────────┤
│                 Moskv-Swarm Agent Orchestrator              │
├──────────────────────────────┬──────────────────────────────┤
│  L1 Sink Persistent Store    │  Vector & Graph Memory DB    │
│  (SQLite WAL + Hash-Chain)   │  (cortex_memory.db)          │
└──────────────────────────────┴──────────────────────────────┘
```

- **Moskv Swarm (`agents/` & `moskv-swarm/`)**: Orchestrates multi-agent swarm tasks with deterministic exergy bounds.
- **L1 Sink Persistence (`L1_sink/`)**: Single-writer SQLite WAL storage engine holding the Merkle-Causal DAG log.
- **Cortex MCP Server (`cortex_mcp_server.py`)**: Standard MCP protocol server exposing WORM Quarantine, F60 scheduling, and physical tool execution to AI agents.

---

## 🚀 Quick Start

### Installation

```bash
# Install via pip
pip install cortex-persist

# Run Cortex MCP Server
python3 -m babylon60.cortex_mcp_server
```

---

## 📁 Subdirectory Map

```
cortex/
├── agents/             # Autonomous agent role definitions & prompt templates
├── infra/              # Low-level SQLite database connectors & WAL triggers
├── L1_sink/            # Primary persistent storage sink
└── moskv-swarm/        # Distributed swarm coordination protocols
```

---

<sub>BABYLON-60 Cortex Substrate · Cognitive Memory Engine · Borja Moskv</sub>
