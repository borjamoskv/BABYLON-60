# 📦 Time Capsule: anvil-lang

## Resumen
Formal verification toolchain and custom language compilation engine utilizing Z3 for proving smart contract invariants. Features structured SMT encoding, type checking warnings, and a rate-limited/authenticated Axum-based verification server.

## Stack
- Rust (Cargo)
- Z3 Solver (z3 crate)
- Axum (SaaS endpoints)
- SQLx + SQLite (API key authorization)

## Lo que funcionó
- **SSA Translation:** Statically Single Assigning variables to fresh solver bitvectors successfully eliminated contradictory constraints from value mutations.
- **Vacuous Assertion Safeguard:** Prefiltering preconditions through an UNSAT check prevents false positives on faulty contract models.
- **Robust Key Check Query:** Parameterized SQLx query validates ACTIVE keys without exposure to injection vectors or logs.

## Lo que NO funcionó
- **Node Modules in vs code extension:** The subproject vscode folder node_modules directory was originally included in the repository index, causing clean state warnings. Kept unmodified to prevent breaking VS Code developer configurations.

## Duración real
- 1.5 Days (Audited, tested, and sealed)

## Siguiente iteración
- Integrate Z3 proof logging support to export verified counter-examples or invariants in standard SMT-LIB v2 format.
