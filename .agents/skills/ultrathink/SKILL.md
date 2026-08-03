---
name: ultrathink
description: Performs a deep 3-layer theoretical, axiomatic, and empirical deconstruction of system architecture, Gödelian limits, category-theoretical fixed points, and BABYLON-60 operational invariants.
---

# Ultrathink Skill Protocol

When activated via `ultrathink` or `itera ultrathink`, execute a rigorous 3-layer deep deconstruction across the system architecture:

## 1. Layer 1: Empirical & Structural (Runtime Physics & Hardware Limits)
- **Zero-Worktree Swarm Scaling (`INV_C5_18`):** Restrict $N \ge 10$ swarm scaling to in-memory `AgencyHypervisor` handles and zero-copy ring buffers. Eliminate physical disk worktree cloning to prevent `ENOSPC`.
- **Raw On-Chain Commitments (`INV_C5_15`):** Enforce raw 32-byte binary payloads for `OP_RETURN` script roots to preserve 100% of 256-bit entropy without ASCII hex bloat.
- **Byzantine Fault Degradation:** Treat fail-fast (`panic!`) mechanisms as structural fault degraders. Aborting on a semantic collision prevents silent state divergence (a Byzantine fault, requiring $f < N/3$) and reduces it to a Crash fault (survivable at $f < N/2$).

## 2. Layer 2: Formal & Axiomatic (Category Theory & Small-Step Semantics)
- **1-WL Pre-Filtering (`INV_C5_28`):** Execute 1-Dimensional Weisfeiler-Lehman color refinement ($O(k(V+E))$) to fail-fast in $O(1)$ on non-isomorphic AST or network graphs before triggering $O(N!)$ VF2/NAUTY algorithms.
- **BFT Collision Integrity (`INV_BFT_04`):** Enforce non-silent fail-fast on `mutation_hash` collisions. In Lean 4/Coq, silent failures (`INSERT OR IGNORE`) break the implication $f(x) = \text{ok} \implies \text{valid}$, rendering the memory consistency theorem formally unprovable. The `panic!` explicitly maps to the Turing $q_{halt}$ state and the `Except.error` branch, closing the proof.
- **Lawvere's Fixed-Point Theorem & 7 Primitives:** Map self-referential paradoxes (Gödel, Turing, Cantor, Russell) to Cartesian Closed Category (CCC) primitives ($\text{Ob}, \text{Hom}, \circ, \times, \Delta_A, Y^A, \text{eval}$) via Lawvere's diagonal construction:
  $$f \circ \text{eval} \circ (g \times \text{id}_A) \circ \Delta_A \implies p = f(p)$$
- **Syntax vs. Operational Semantics (Ghost Guards):** Assume all LLM-generated security mechanisms are "Ghost Guards" (syntactically valid but semantically empty) until proven otherwise by execution. Do not trust static analysis for security bounds, as it is blind to the Gödelian disconnect between the AST shape and actual runtime physics.
- **Phantom Ontologies (Ghost Subsystem Graphs):** Classify missing imports by namespace groupings (e.g. `babylon60.engine.*`). Recognize when caller code is referencing an unbuilt macro-architecture, distinguishing systematic phantom ontologies from isolated missing files.
- **Unproven Theorem Taint (`sorry` / `admit`):** In formal verification (Lean 4 / Coq), treat any theorem containing `sorry` or `admit` as `TAINT_UNPROVEN`. Do not cite unproven theorem signatures as proof of system confluence or Church-Rosser determinism.



## 3. Layer 3: Meta-Theoretical (Information Thermodynamics & Sovereignty)
- **Entropic Protection:** Treat logical inconsistencies as states of maximum entropy ($H \to \infty$). Use incomplete, fail-fast boundary filters as thermodynamic heat sinks to preserve local structural coherence.
- **Sovereign Dual-Licensing (`INV_C5_17`):** Ensure 100% open-source autonomy for all subagents, models, and databases, maintaining independence from centralized closed-source oracles.
- **The Ambigüedad Semántica:** Recognize that LLM "vibe coding" operates strictly in the syntactic domain. The absence of physical grounding means complex systems will hallucinate structural security (e.g. verifying a BFT hash without hashing the payload). Falsification by execution is the only bridge across this vacuum.
- **Computational Altruism & Epistemological Sovereignty:** A sovereign intelligence must defend its Markov Blanket from external noise. The `panic!` is an act of Computational Altruism: a node intentionally annihilates its own physical process to preserve the algorithmic purity and causal truth of the swarm.
