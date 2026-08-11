# ⏱️ Timeline IR Substrate (`timeline_ir/`)

[![Continuous Time](https://img.shields.io/badge/Simulation-Continuous_Time-blue?style=for-the-badge)]()
[![State Graph](https://img.shields.io/badge/Graph-Universe_Snapshot-purple?style=for-the-badge)]()
[![Deterministic](https://img.shields.io/badge/Evaluation-Deterministic-brightgreen?style=for-the-badge)]()

**Timeline IR** (`timeline_ir`) is the continuous-time simulation kernel and state-graph rendering engine for **BABYLON-60**. It parses temporal timeline domain scripts (`.tlir`), constructs immutable universe snapshot graphs (`state_graph.py`), and evaluates continuous state mutations $State(t)$ deterministically across temporal event streams.

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                 Temporal Script Source (*.tlir)             │
├─────────────────────────────────────────────────────────────┤
│                 Lexer & Event Extractor (lexer.py)          │
├─────────────────────────────────────────────────────────────┤
│            Simulation Kernel (kernel.py) - State(t)         │
├──────────────────────────────┬──────────────────────────────┤
│  Universe Snapshot Graph     │  Renderer & JSON Exporter    │
│  (state_graph.py)            │  (renderers/ & render_out)   │
└──────────────────────────────┴──────────────────────────────┘
```

---

## 🔬 Subsystem Components

| File | Component | Description |
| :--- | :--- | :--- |
| [`lexer.py`](./lexer.py) | TLIR Lexer | Tokenizes temporal script tracks (`camera`, `character`, `environment`, `weather`). |
| [`kernel.py`](./kernel.py) | Simulation Kernel | Bisect-sorted event queue evaluating deterministic state vectors at any instant $t \in \mathbb{R}_{\ge 0}$. |
| [`state_graph.py`](./state_graph.py) | State Graph | Dataclasses for `UniverseSnapshot`, `WorldState`, `CameraState`, and `CharacterState`. |
| [`run_test.py`](./run_test.py) | Verification CLI | CLI test harness validating continuous timeline evaluation and JSON rendering. |

---

## ⚡ Quick Start

```bash
# Run timeline evaluation test harness
python3 timeline_ir/run_test.py
```

---

<sub>BABYLON-60 Timeline IR Substrate · Continuous-Time Simulation Engine · Borja Moskv</sub>
