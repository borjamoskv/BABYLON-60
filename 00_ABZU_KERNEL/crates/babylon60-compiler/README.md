# 📜 BABYLON-60 DSL & Proof Compiler (`00_ABZU_KERNEL/crates/babylon60-compiler/`)

[![Compiler](https://img.shields.io/badge/Language-Rust_≥1.89-orange?style=for-the-badge&logo=rust)](https://www.rust-lang.org/)
[![Lean 4 Backend](https://img.shields.io/badge/Lean_4-Trace_Emitter-green?style=for-the-badge)](../../../proof/lean/BabylonTrace.lean)
[![Epistemology](https://img.shields.io/badge/Claims-CLAIMS.toml-purple?style=for-the-badge)](../../../CLAIMS.toml)

The **`babylon60-compiler`** crate transforms `.b60` DSL scripts into B60 Bytecode Intermediate Representation (IR) (`HALT`, `CRITICAL_HALT`, `FORK`, `LOADIMM`) and includes a Python helper (`lean_backend.py`) for emitting Lean 4 trace specifications. *(Note: the normative `L1_FORMAL` proofs verified in `CLAIMS.toml` are maintained in [`proof/lean/BabylonTrace.lean`](../../../proof/lean/BabylonTrace.lean) and [`proof/lean/AX0.lean`](../../../proof/lean/AX0.lean)).*

---

## 🧮 Categorical Design Context

- **Programs as Morphisms**: A `.b60` script is modeled as a sequence of typed transitions ($A \to B$).
- **Static Invariant Checks**: `static_proofs.rs`, `borrowck.rs`, and `types.rs` validate structural constraints before emitting bytecode artifacts.
- **Trace Transpilation**: `lean_backend.py` maps `.b60` AST instruction sequences into Lean 4 trace definitions.

---

## 🏗️ Compiler Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                 .b60 DSL Domain Specification               │
├─────────────────────────────────────────────────────────────┤
│   Lexer & Parser (src/parser.rs: parse -> Result<AST, Err>) │
├─────────────────────────────────────────────────────────────┤
│   AST & Type/Borrow Check (src/ast.rs, types.rs, borrowck.rs)│
├──────────────────────────────┬──────────────────────────────┤
│  B60 Bytecode IR & Lowering  │  Lean 4 Trace Emitter        │
│  (src/ir.rs, artifact.rs)    │  (lean_backend.py)           │
└──────────────────────────────┴──────────────────────────────┘
```

---

## 🔬 Subsystem Components & Opcodes

| Component | File | Description / Opcodes |
| :--- | :--- | :--- |
| **Parser** | [`src/parser.rs`](./src/parser.rs) | Parses a small ISA subset; unknown opcodes return `ParseError::UnexpectedToken`. The alloc/assign/free frontend is separate. |
| **AST & Types** | [`src/ast.rs`](./src/ast.rs) · [`src/types.rs`](./src/types.rs) | AST representation and static type definitions. |
| **Borrow & Layout** | [`src/borrowck.rs`](./src/borrowck.rs) · [`src/layout.rs`](./src/layout.rs) | Experimental ownership and memory layout analysis. |
| **IR & Lowering** | [`src/ir.rs`](./src/ir.rs) · [`src/lowering.rs`](./src/lowering.rs) · [`src/backend_x86.rs`](./src/backend_x86.rs) | Intermediate representation, lowering passes, and code generation. |
| **ISA Opcodes** | [`babylon60-kernel::isa`](../babylon60-kernel/src/isa.rs) | `HALT`, `CRITICAL_HALT`, `FORK(label)`, `LOADIMM(reg, val)`. |
| **Artifact** | [`src/artifact.rs`](./src/artifact.rs) | Packages bytecode into binary artifacts. |
| **Proof Check** | [`src/static_proofs.rs`](./src/static_proofs.rs) | Generates abstract proof obligations; emitted obligations are not themselves a runtime refinement proof. |
| **Lean Emitter** | [`lean_backend.py`](./lean_backend.py) | Emits Lean 4 trace snippets from `.b60` scripts. |

---

The bytecode parser accepts HALT, CRITICAL_HALT, FORK and LOADIMM.
It does not accept the runtime's AFTER or BA.EXACT syntax. The memory frontend
and textual Lean IR emitter are separate paths; no full compiler/kernel/runtime
semantic equivalence is established.

## ⚡ Example `.b60` Script & Usage

```b60
// Example hello_causal.b60
LOADIMM 42
FORK checkpoint_alpha
HALT
```

```bash
# Run compiler tests
cargo test --locked -p babylon60-compiler

# Transpile B60 script into a Lean 4 trace file
python3 00_ABZU_KERNEL/crates/babylon60-compiler/lean_backend.py hello_causal.b60 --output /tmp/HelloTrace.lean
```

---

<sub>BABYLON-60 Compiler Substrate · DSL & Trace Emitter · Borja Moskv</sub>
