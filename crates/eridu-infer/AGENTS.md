# AGENTS.md — Sovereign Governance & Validation Contract (`eridu-infer`)

## 1. Binary Validation Commands (Zero-Exploration Gate)
- **Compile & Type Check:** `cargo check --workspace -q`
- **Test Suite:** `cargo test --workspace -q`
- **Static Linter:** `cargo clippy --workspace -- -D warnings`

## 2. Repository Invariants
- **Domain:** Bare-metal local inference runtime for Apple Silicon (UMA `RFO=0`, Metal shaders, Unix Domain Sockets, zero Electron/HTTP loopback bloat).
- **Zero-Telemetry Invariant:** Strictly air-gapped execution path; no outbound telemetry or cloud callbacks permitted.

## 3. Exploration Restrictions (`INV_C5_ARGON_GOVERNANCE`)
- Do not traverse `target/`, `.git/`, or model weight directories (`*.gguf`, `*.safetensors`).
- Restrict file reads to `src/` and `Cargo.toml`.
