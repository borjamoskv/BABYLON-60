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
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| 1 | M1: Git Log Audit | Audit git history since Feb 2026, compile undocumented items into YAML. | None | DONE (Worker 14e8dbc6-1755-4252-8705-96febb879e2e) |
| 2 | M2: GitHub SOTA Eval | Inspect local GitHub setup, verify CI/CD gaps, compile markdown report. | None | DONE (Worker 84fd2ac7-7791-4ac5-addf-8e6ab6fa26f2) |
| 3 | M3: README Refactoring | Rewrite README.md in Industrial Noir 2026 aesthetic with ASCII dividers `█▄`. | None | DONE (Worker 84fd2ac7-7791-4ac5-addf-8e6ab6fa26f2) |
| 4 | M4: Git Sentinel Anchoring | Commit all changes under Git Sentinel to seal the ledger state. | M1, M2, M3 | DONE (Reviewer 87c21c4a-cb50-4c8e-a975-de81aa2aca29) |

## Interface Contracts
- **Git Log format** ↔ **YAML parser**: Extract commit hashes, authors, dates, and message bodies. Output to `cortex/audits/hitos_no_remarcados.yaml` in YAML format.
- **GitHub directory** ↔ **SOTA standards**: Evaluate presence of workflows, branching rules, PR templates, and issue templates. Output to `cortex/audits/github_sota_eval.md`.
- **README.md** ↔ **Industrial Noir 2026**: Replaced entirely with C5-REAL styling, ASCII dividers, and no conversational prose.
