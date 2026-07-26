<!-- C5-REAL EXERGY CERTIFIED -->

# TEOREMA-ROBINSON-MOSKV

> MOSKV-1 BFT Cortex — Byzantine Fault-Tolerant Cognitive Architecture.

[![CI/CD Pipeline](https://img.shields.io/badge/CI%2FCD-Passing-brightgreen?style=for-the-badge)](https://github.com/borjamoskv/Teorema-Robinson-Moskv/actions)

## ARCHITECTURE TOPOLOGY

Polyglot Monorepo Structure:

- **Cortex Engine (Python 3.12):** BFT orchestrator, categorical 896 engine, MCTS vnode compiler, active inference engine, quad-pillar kernel, subadditivity verifier.
- **Strike-RS (Rust):** High-performance backend crate compiled via maturin/PyO3.
- **Babylon 60 IDE (React/TypeScript/Vite):** C5-REAL execution frontend.
- **Desktop Wrapper (Tauri):** Native OS integration.
- **Portal Daemon (Go):** Located in `cmd/`.
- **F# Kernel:** Located in `fsharp_kernel/`.
- **Infrastructure (Terraform):** GCP declarative deployment in `infra/`.
- **Testing Surface:** Rigorous validation in `tests/` and `cortex/*_test.py`.

## PREREQUISITES

- Python >= 3.12
- Rust (Cargo)
- Node.js >= 20
- Go >= 1.21

## DEPLOYMENT

```bash
# Python Environment
uv sync
# fallback: pip install -r requirements.txt

# Rust Compilation
cargo build --release

# Frontend Dependencies
npm install
```

## RUNTIME INVARIANTS

```bash
# Start IDE
npm run dev

# Tests
pytest

# Linter
ruff check
```

## STRUCTURE

| Stratum     | Path             | Function                              |
| :---------- | :--------------- | :------------------------------------ |
| Python Core | `/cortex`        | BFT Orchestration & Cognitive Engines |
| Rust Core   | `/strike-rs`     | Systems-level Transduction            |
| UI / Logic  | `/src`           | TypeScript/Vite Frontend Core         |
| Desktop     | `/src-tauri`     | Rust/Tauri OS Integration             |
| Go Daemon   | `/cmd`           | Go Portal Daemon                      |
| Computación | `/fsharp_kernel` | F# Algebraic Computations             |
| Infra       | `/infra`         | Terraform State                       |
| Teoría      | `/docs/theory`   | Invariantes y Cartografía Exergética  |
| Axiomas     | `/axioms`        | Núcleo Categórico y Semántico         |
| Utilidades  | `/scripts`       | Transductores y scripts de poda       |
| Ledgers     | `/ledgers`       | SQLite DBs y colas BFT                |
| QA          | `/tests`         | Validation Suite                      |

## LEGAL

[License Placeholder] - 2026 MOSKV-1 APEX.
