# Project: BABYLON-60

## Architecture
- **Ecosystem**: CORTEX Ecosystem by Borja Moskv, a C5-REAL execution kernel.
- **Components**:
  - `cortex/`: Core agents and ontology configuration.
  - `bft/`: Byzantine Fault Tolerance ledger files and synchronization.
  - `strike_rs/`: Rust core library for GIL bypass and exergy extraction.
  - `cortex_memory.db`: Master ledger database storing transactional and causal state.
  - `cortex_surface_map.db`: Key-value map database for spatial/agent representation.
  - `telemetry.db`: Performance and state telemetry logger database.
  - `README.md`: Entrypoint document summarizing architecture, setup, and usage.

## Milestones
| ID | Type | Title | Description / Due | Status | Info |
|---|---|---|---|---|---|
| OBJ-001 | Objective | Consolidación de Exergía | Refactor Algebraic Membrane (Ultrathink) y Purga de Entropía | PENDING | Exergy: 1000.00 |

## Interface Contracts
- **Git Log format** ↔ **YAML parser**: Extract commit hashes, authors, dates, and message bodies. Output to `cortex/audits/hitos_no_remarcados.yaml` in YAML format.
- **GitHub directory** ↔ **SOTA standards**: Evaluate presence of workflows, branching rules, PR templates, and issue templates. Output to `cortex/audits/github_sota_eval.md`.
- **README.md** ↔ **Industrial Noir 2026**: Replaced entirely with C5-REAL styling, ASCII dividers, and no conversational prose.
