# 📜 BABYLON-60 DSL & Proof Compiler (`compiler/`)

[![Compiler](https://img.shields.io/badge/Language-Rust_5.0-orange?style=for-the-badge&logo=rust)](https://www.rust-lang.org/)
[![Lean 4 Backend](https://img.shields.io/badge/Lean_4-Formal_Proof_Emitter-green?style=for-the-badge)](../BabylonTrace.lean)
[![Target](https://img.shields.io/badge/Target-B60_Bytecode_IR-blue?style=for-the-badge)]()

The **Compiler Module** (`compiler`) transforms high-level `.b60` DSL domain scripts into executable B60 Bytecode Intermediate Representation (IR) containing exact bytecode instructions (`HALT`, `CRITICAL_HALT`, `FORK`, `LOADIMM`) while automatically emitting formal Lean 4 trace theorems for mathematical causality verification.

---

## 🏗️ Compiler Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                 .b60 DSL Domain Specification               │
├─────────────────────────────────────────────────────────────┤
│   Lexer & Parser (src/parser.rs: parse -> Result<AST, Err>) │
├─────────────────────────────────────────────────────────────┤
│   Abstract Syntax Tree (src/ast.rs: AST { instructions })   │
├──────────────────────────────┬──────────────────────────────┤
│  B60 Bytecode IR Artifact    │  Lean 4 Proof Theorem        │
│  (src/artifact.rs)           │  (lean_backend.py)           │
└──────────────────────────────┴──────────────────────────────┘
```

---

## 🔬 Subsystem Components & Opcodes

| Component | File | Description / Opcodes |
| :--- | :--- | :--- |
| **Parser** | [`src/parser.rs`](./src/parser.rs) | Parses `.b60` lines into opcode instructions. Rejects unknown opcodes with `ParseError::UnknownOpcode`. |
| **AST** | [`src/ast.rs`](./src/ast.rs) | `struct AST { pub instructions: Vec<Instruction> }`. |
| **ISA Opcodes** | [`kernel::isa`](../kernel/src/isa.rs) | `HALT`, `CRITICAL_HALT`, `FORK(label)`, `LOADIMM(reg, val)`. |
| **Artifact** | [`src/artifact.rs`](./src/artifact.rs) | Packages bytecode into executable binary artifacts. |
| **Proof Generator** | [`src/static_proofs.rs`](./src/static_proofs.rs) | Validates static causal invariants prior to bytecode emission. |
| **Lean Transpiler** | [`lean_backend.py`](./lean_backend.py) | Transpiles AST traces into verified Lean 4 theorems (`BabylonTrace.lean`). |

---

## ⚡ Example `.b60` Script & Usage

```b60
// Example hello_causal.b60
LOADIMM 42
FORK checkpoint_alpha
HALT
```

```bash
# Run compiler tests
cargo test -p babylon60_compiler

# Transpile B60 script into Lean 4 formal proof theorem
python3 compiler/lean_backend.py hello_causal.b60 --output BabylonTrace.lean

# Verify generated theorem with Lean 4 CLI
lean BabylonTrace.lean
```

---

<sub>BABYLON-60 Compiler Substrate · Formal Proof Emitter · Borja Moskv</sub>
