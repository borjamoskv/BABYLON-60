# 📜 BABYLON-60 DSL & Proof Compiler (`compiler/`)

[![Compiler](https://img.shields.io/badge/Language-Rust_5.0-orange?style=for-the-badge&logo=rust)](https://www.rust-lang.org/)
[![Lean 4 Backend](https://img.shields.io/badge/Lean_4-Formal_Proof_Emitter-green?style=for-the-badge)](../BabylonTrace.lean)
[![Target](https://img.shields.io/badge/Target-B60_Bytecode_IR-blue?style=for-the-badge)]()

The **Compiler Module** (`compiler`) transforms high-level `.b60` DSL domain scripts into executable B60 Bytecode Intermediate Representation (IR) while automatically emitting formal Lean 4 trace theorems for mathematical causality verification.

---

## 🏗️ Compiler Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                 .b60 DSL Domain Specification               │
├─────────────────────────────────────────────────────────────┤
│   Lexer & Recursive Descent Parser (src/parser.rs)          │
├─────────────────────────────────────────────────────────────┤
│   Abstract Syntax Tree (src/ast.rs) & Static Proof Checker   │
├──────────────────────────────┬──────────────────────────────┤
│  B60 Bytecode IR Artifact    │  Lean 4 Proof Theorem        │
│  (src/artifact.rs)           │  (lean_backend.py)           │
└──────────────────────────────┴──────────────────────────────┘
```

---

## 🔬 Substrate Components

| File | Subsystem | Function |
| :--- | :--- | :--- |
| [`parser.rs`](./src/parser.rs) | Syntax Engine | Zero-copy string lexing and recursive descent parsing of `.b60` DSL programs. |
| [`ast.rs`](./src/ast.rs) | AST Definition | Typed node structures representing causal coroutines, assertions, and state guards. |
| [`artifact.rs`](./src/artifact.rs) | IR Emitter | Binary artifact packager serializing B60 bytecode for execution in `kernel`. |
| [`static_proofs.rs`](./src/static_proofs.rs) | Proof IR | Static analyzer validating causal invariants prior to bytecode emission. |
| [`lean_backend.py`](./lean_backend.py) | Lean 4 Transpiler | Transpiles AST traces into verified Lean 4 code (`BabylonTrace.lean`). |

---

## ⚡ Quick Start

```bash
# Test compiler crate
cargo test -p babylon60_compiler

# Transpile B60 program into Lean 4 trace
python3 compiler/lean_backend.py hello_causal.b60 --output BabylonTrace.lean

# Verify generated proof with Lean 4 CLI
lean BabylonTrace.lean
```

---

<sub>BABYLON-60 Compiler Substrate · Formal Proof Emitter · Borja Moskv</sub>
