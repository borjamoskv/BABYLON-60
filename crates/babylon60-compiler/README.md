# 📜 BABYLON-60 DSL & Proof Compiler (`compiler/`)

[![Compiler](https://img.shields.io/badge/Language-Rust_5.0-orange?style=for-the-badge&logo=rust)](https://www.rust-lang.org/)
[![Lean 4 Backend](https://img.shields.io/badge/Lean_4-Formal_Proof_Emitter-green?style=for-the-badge)](../BabylonTrace.lean)
[![Epistemology](https://img.shields.io/badge/Epistemology-C5--REAL_Categories-purple?style=for-the-badge)](../docs/00_MANIFESTO.md)

The **Compiler Module** (`compiler`) transforms high-level `.b60` DSL domain scripts into executable B60 Bytecode Intermediate Representation (IR) containing exact bytecode instructions (`HALT`, `CRITICAL_HALT`, `FORK`, `LOADIMM`) while automatically emitting formal Lean 4 trace theorems for mathematical causality verification.

---

## 🧮 C5-REAL Epistemological Context: Morphisms & Proof Transpilation

In alignment with the **C5-REAL Epistemological Constitution**:
- **Programs as Free Categories**: A `.b60` script is not a sequence of commands; it is a free category whose statements are **Morphisms** ($A \to B$).
- **State as Lawvere Fixed Point**: State is evaluated as a Lawvere fixed point ($T(X) \cong X$) verified statically by `static_proofs.rs`.
- **Proof Emission as Natural Transformation**: `lean_backend.py` acts as a natural transformation mapping the execution category $\mathcal{C}_{\text{B60}}$ to the proof category $\mathcal{C}_{\text{Lean4}}$ (`BabylonTrace.lean`), proving that no state transition violates causal acyclicity.

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

<sub>BABYLON-60 Compiler Substrate · C5-REAL Category Theory & Formal Proof Emitter · Borja Moskv</sub>
