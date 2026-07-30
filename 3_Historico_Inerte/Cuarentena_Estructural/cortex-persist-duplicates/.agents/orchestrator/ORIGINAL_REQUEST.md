# Original User Request

## Initial Request — 2026-06-28T14:40:16Z

Upgrade the current `IHelpPurgeDaemon` to a dynamic, high-performance T-Cell monitoring daemon that targets all 50+ nodes in `BASE_MAFIA_NODES` (imported dynamically from `babylon60.routes.telemetry`). The system must execute high-concurrency parallel checks (simulating a swarm-like structure of up to 10,000 sub-threads/agents) to verify the status, RSS feeds, and active antigens of these targets, logging all occurrences in the Master Ledger.

Working directory: `/Users/borjafernandezangulo/`
Integrity mode: development

## Requirements

### R1. Dynamic Antigen Ingestion (MHC-TCell Binding)
- Refactor `babylon60/extensions/daemon/t_cell_ihelp_purge.py` to dynamically load target entities from `BASE_MAFIA_NODES` inside `babylon60/routes/telemetry.py`.
- Do not hardcode regex patterns for David Dominguez or ihelp; construct the `antigen_signature` regex dynamically from the list of nodes.
- Ensure the registration with `MHCAntigenRouter` is clean and does not break existing test cases.

### R2. High-Concurrency Swarm Monitoring (Forensic Scanning)
- Implement a script/daemon method to perform parallel checkouts (DNS resolution, RSS feed validation, and HTTP response check) of all active Mafia URLs in `BASE_MAFIA_NODES`.
- The checks must run concurrently using `asyncio` to handle large numbers of tasks without stalling the main loop.
- Any detected active antigen (e.g., matching keywords in the latest post content or feed) must trigger phagocytosis and write an event payload to the Master Ledger (`babylon60/audit/ledger.py`).

### R3. Validation and Fallback (Fail-Closed)
- Implement a comprehensive unit test suite in `tests/extensions/daemon/test_mafia_t_cell.py` verifying that the dynamic regex successfully matches variants of all base nodes.
- Ensure proper error handling: if a domain check fails (e.g. DNS timeout), log it as a forensic anomaly in the ledger but do not stop the execution loop.

## Acceptance Criteria

### AST and Type Integrity
- [ ] No type annotations or compilation errors when running `ruff check` and `pyright`.
- [ ] Imports from `babylon60.routes.telemetry` do not create circular dependency loops.

### Swarm & Ledger Execution
- [ ] Test coverage in `tests/extensions/daemon/` passes successfully (`pytest`).
- [ ] Master Ledger records events using SHA3-256 signatures with proper `BABYLON60-TAINT` metadata.
