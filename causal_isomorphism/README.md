# 🔀 Causal Isomorphism Transpiler (`causal_isomorphism/`)

[![Language](https://img.shields.io/badge/Source-F%23_Functional-purple?style=for-the-badge&logo=fsharp)](https://fsharp.org/)
[![Target](https://img.shields.io/badge/Target-Rust_%2F_Solidity-orange?style=for-the-badge)]()
[![Type System](https://img.shields.io/badge/Types-Linear_%26_Affine-brightgreen?style=for-the-badge)]()

The **Causal Isomorphism Transpiler** (`causal_isomorphism`) parses functional F# domain kernel specifications (`domain_kernel/*.fs`) into a linear Intermediate Representation (`ir.py`), verifies linear/affine resource invariants (`linear_checker.py`), and emits cryptographically isomorphic **Rust** (`emitter_rust.py`) and **Solidity** (`emitter_solidity.py`) target code.

---

## 🏗️ Transpilation Pipeline

```
┌─────────────────────────────────────────────────────────────┐
│             F# Domain Specification (*.fs)                  │
├─────────────────────────────────────────────────────────────┤
│   F# Lexer & AST Parser (parser_fsharp.py)                  │
├─────────────────────────────────────────────────────────────┤
│   Linear & Affine Type Checker (linear_checker.py)          │
├──────────────────────────────┬──────────────────────────────┤
│   Rust Code Emitter          │   Solidity Smart Contract    │
│   (emitter_rust.py)          │   (emitter_solidity.py)      │
└──────────────────────────────┴──────────────────────────────┘
```

---

## 🔬 Subsystem Components & Type Rules

### Static Linear & Affine Type Rules (`linear_checker.py`)

1. **Linear Constraints (`is_linear=True`)**: Parameters marked as linear must be consumed **EXACTLY ONCE** in the execution flow. Prevents resource leaks and double-spends.
2. **Affine Constraints (`is_affine=True`)**: Parameters marked as affine must be consumed **AT MOST ONCE**.
3. **Consuming Operations**: Passing as argument, pattern matching, returning, or binary expression consumption. Violations emit `LinearViolation(function_name, param_name, usage_count, violation_kind)`.

| File | Function |
| :--- | :--- |
| [`cli.py`](./cli.py) | CLI entrypoint for `transpile`, `validate`, and `inspect` commands. |
| [`parser_fsharp.py`](./parser_fsharp.py) | F# syntax parser extracting type declarations and state transition automata. |
| [`ir.py`](./ir.py) | `IRModule`, `IRFunction`, `IRExpr`, and `IRExprKind` data model. |
| [`linear_checker.py`](./linear_checker.py) | Static analysis pass enforcing linear and affine consumption rules. |
| [`regime_validator.py`](./regime_validator.py) | Regulatory constraint validator (EU AI Act, HIPAA, GDPR). |
| [`emitter_rust.py`](./emitter_rust.py) | Code generator for high-assurance Rust kernel crates. |
| [`emitter_solidity.py`](./emitter_solidity.py) | Code generator for EVM smart contract notarization layers. |

---

## ⚡ Quick Start

```bash
# Transpile F# domain kernel into Rust & Solidity targets
python3 -m causal_isomorphism.cli transpile domain_kernel/IRPAutomata.fs -o generated/

# Validate linear invariants on F# domain script
python3 -m causal_isomorphism.cli validate domain_kernel/IRPAutomata.fs

# Inspect AST and state machine representation
python3 -m causal_isomorphism.cli inspect domain_kernel/IRPAutomata.fs
```

---

<sub>BABYLON-60 Causal Isomorphism Substrate · F# Transpiler · Borja Moskv</sub>
