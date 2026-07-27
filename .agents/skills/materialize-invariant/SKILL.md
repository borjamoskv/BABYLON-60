---
name: materialize-invariant
description: Workflow for ingesting new architectural constraints via Proof of Concept, Axiomatization, and Falsification.
---

# Invariant Materialization Pipeline

When the user introduces or mandates a new structural invariant, architectural rule, or constraint, you must immediately subject it to this three-step materialization pipeline. An invariant that exists only as prose is invalid.

### Step 1: Proof of Concept (Dogfooding)
- **Action:** Design a minimal, contained execution (e.g., a short script or direct terminal command) that tests the boundary of the new rule in a realistic scenario.
- **Requirement:** Force the system to hit the constraint. If the rule says "Network failures must yield UNBACKED", intentionally fetch a dead IP to prove the rule triggers.

### Step 2: Axiomatization (Formalization)
- **Action:** Translate the natural language rule into formal logic or structural mathematics within the project's architectural documentation (e.g., `AXIOMATIZATION.md` or `ARCHITECTURE.md`).
- **Requirement:** Define the exact domain sorts, conditions, and logical implications (e.g., $\forall x \in X : \dots$).

### Step 3: Falsifiability (Executable Enforcement)
- **Action:** Write executable code (a test, a verifier, an AST checker, or a runtime assertion) that implements the axiom.
- **Requirement:** The invariant must be falsifiable. You must prove that breaking the invariant causes a hard crash (`sys.exit(1)`, `ValueError`, etc.). Run the test against both a valid scenario (PASS) and a violating scenario (FAIL) to prove the safety net works.
