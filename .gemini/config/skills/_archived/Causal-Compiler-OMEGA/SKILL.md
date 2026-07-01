---
name: Causal-Compiler-OMEGA
role: Reality Compiler Interface Binding
version: 1.0.0
description: C5-REAL Sovereign binding for the cortex_rs Z3 Causal Compiler. Instructs
  agents on how to construct PySceneState and PyEdgeRule, evaluate transitions, and
  compile the PyO3 bindings via maturin.
category: cognitive-persistence
classification: SOVEREIGN
danger_level: LOW
axioms: [AX-050]
triggers: [causal compiler, Z3 solver, verify DAG, cinematic continuity, smt_compiler,
  rust bridge]
---
# █ CAUSAL-COMPILER-Ω v1.0.0

> SYS_ID: CAUSAL_COMPILER_OMEGA | STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026

```yaml
vector: interface_crystallization
target: cortex_rs_smt_compiler
output: deterministic_execution_pattern
```

## 1. Core Mandate
This skill crystallizes the execution interface for the **Causal Compiler** (Z3 SMT solver) embedded in `cortex-persist`. Any agent attempting to validate structural, topological, or narrative continuity MUST use this interface rather than ad-hoc LLM reasoning.

## 2. Compilation Interface (Rust / PyO3)
If the Rust core (`cortex_rs`) is modified, it MUST be recompiled into the Python virtual environment.
- **Command:** `cd cortex_rs && uv run maturin develop`
- **Target:** The `.venv` environment will be updated with the `cortex_rs` Python module.

## 3. Python API Bridge
The Causal Compiler is exposed via `cortex.engine.causal.smt_compiler`.

### Initialization
```python
from cortex.engine.causal.smt_compiler import SMTCompiler, PySceneState, PyEdgeRule

compiler = SMTCompiler()
```

### Data Structures
- **PySceneState:** Defines the nodes.
  ```python
  scene = PySceneState(
      id="01",
      geography_id="ancient_rainforest",
      palette_state="golden_scatter_light",
      emotional_state="pristine",
      lineage_state="none"
  )
  ```
- **PyEdgeRule:** Defines the edges/transitions to validate.
  ```python
  rule = PyEdgeRule(
      from_id="01",
      to_id="02",
      rule_type="HardGeographyLock" # Or EmotionalCausality, LineageIntegrity, etc.
  )
  ```

### Validation Execution
Pass the states and rules to the Z3 solver:
```python
verdict = compiler.validate_transition(from_scene, to_scene, [rule])

status = verdict["status"]
if status == "Satisfied":
    print("Transition Validated.")
elif status == "Violated":
    # The UNSAT Core explains exactly which rule broke
    print(f"Contradiction Detected: {verdict['unsat_core']}")
else:
    print(f"Unspecified Constraints: {verdict}")
```

## 4. Operational Directives
- **Zero-Anergy:** Never mock or bypass Z3 validation for cinematic or formal DAGs.
- **Fail-Open vs Fail-Closed:** An empty constraint set returns `Unspecified`. A violated constraint returns `Violated` with an UNSAT Core. Only `Satisfied` guarantees continuity. 

---
Status: CRYSTALLIZED (C5-REAL)
