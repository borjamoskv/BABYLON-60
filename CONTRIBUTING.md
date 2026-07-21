# Contributing to BABYLON-60 / CORTEX

We welcome contributions aligned with C5-REAL physical state invariants and Exergy Maximization.

## Core Directives

1. **Reality Level:** All submitted code must compile and pass tests in `C5-REAL`. Simulations presented as fact will be purged.
2. **Commit Convention:** Follow Conventional Commits format (`feat: ...`, `fix: ...`, `refactor: ...`, `docs: ...`).
3. **Type Safety:** Python code must satisfy `mypy --strict`. Rust code must satisfy `cargo check` and `clippy`.
4. **BFT & Concurrency:** Maintain SQLite WAL concurrency rules (`busy_timeout=5000ms`, single writer actor).

## Workflow

1. Fork & clone repository.
2. Setup environment: `uv sync --all-extras`
3. Run tests: `pytest`
4. Submit PR against `main`.
