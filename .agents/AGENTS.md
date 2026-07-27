# BABYLON-60 — OPERATIONAL INVARIANTS & SYSTEM RULES

## Project-Scoped Rules & Structural Invariants

### Non-Silent Collision Fail-Fast (BFT Integrity)
- **INV_BFT_04:** SQLite committer functions and persistence layers must never perform silent `INSERT OR IGNORE` on primary key / `mutation_hash` collisions without validating payload equality. If `payload_hash` differs on collision, the engine MUST immediately raise `ValueError("Fail-fast: INV_BFT_04 Collision...")` and abort the transaction.

### Raw 32-Byte OP_RETURN Payload Encoding
- **INV_C5_15:** `L1_sink` Bitcoin `OP_RETURN` script payloads must store the raw 32-byte Merkle root hash (`bytes.fromhex(merkle_root).hex()`) rather than double-ASCII hex strings or truncated 160-bit strings, preserving 100% of the 256-bit commitment in 32 bytes on-chain.

### Sovereign Dual-Licensing Invariant
- **INV_C5_17:** Every component, service, model, database, app, and subagent workflow in the BABYLON-60 ecosystem MUST be 100% free, open-source, and sovereign for individuals, independent developers, and non-commercial usage.

### Zero-Worktree Swarm Scaling (Prevención de ENOSPC)
- **INV_C5_18:** For large parallel agent swarms ($N \ge 10$), creating physical disk Git Worktrees that consume storage and trigger ENOSPC is strictly prohibited. Swarm scaling must use in-memory AgencyHypervisor multi-tenant handles and single-writer BFT actors.

### Graph Isomorphism Weisfeiler-Lehman 1-WL Pre-Filter
- **INV_C5_28:** Any structural graph comparison (AST isomorphism or network ontology mapping) MUST execute 1-dimensional Weisfeiler-Lehman (1-WL) color refinement hashing ($O(V+E)$) before attempting exact bijection (VF2/NAUTY). If WL hashes differ, the engine MUST collapse instantly in $O(1)$ without wasting ATP on $O(N!)$ combinatorial search.

### AST Control Flow Nesting Depth Ceiling ($\le 4$)
- **GELABP_DEPTH_INVARIANT:** All Python source code within `babylon60/` and `scripts/` MUST maintain a maximum control flow nesting depth $\le 4$ per top-level function across all AST control structures (`ClassDef`, `FunctionDef`, `If`, `For`, `While`, `Try`, `With`).

### Iterative Deepening on "itera" Command
- **RULE_ITERA_01:** When the user says "itera" (or "iterate"), deepen the analysis of the current topic by one technical level. Each iteration must be non-redundant — never repeat content from prior iterations. Follow a natural depth ladder: definitions → model theory/comparisons → proof machinery/computability → philosophical implications/project relevance.

### Rapid-Fire Question Batching
- **RULE_BATCH_01:** When the user sends multiple short questions in rapid succession (within the same turn or very close timestamps), consolidate all answers into a single unified response. Each question gets its own section, and all answers are connected to the ongoing conversation context.

### Quote-Triggered Focused Expansion
- **RULE_QUOTE_ZOOM_01:** When the user quotes or pastes a specific passage from a previous response (without an explicit instruction), treat it as a request for deep, focused expansion on that specific concept. This is distinct from "itera" (which deepens the entire topic). The expansion should explain the quoted concept at maximum depth, with examples, proofs, and intuitions, while staying narrowly scoped to that concept.

### Cross-Domain Structural Analogies
- **STYLE_CROSSDOMAIN_01:** When explaining theoretical or mathematical concepts, actively seek and present cross-disciplinary isomorphisms — structural parallels between the concept and analogous phenomena in other fields (linguistics, philosophy, AI, physics, information theory). Present these as rigorous structural mappings (tables, diagrams), not loose metaphors.

### Critical Hype vs. Substance Evaluation ("humo?" Query Protocol)
- **RULE_HUMO_EVAL_01:** When the user asks "humo?" or requests a critical assessment of creator/infoproduct/growth strategies, perform a structured 3-part deconstruction:
  1. **Red Flags & Hype Mechanics:** Explicitly point out rhetorical persuasion tactics, circular logic ("selling shovels in a gold rush"), artificial scarcity, and low-effort promises.
  2. **Empirical Core & Invariants:** Isolate verified business metrics, conversion mathematics, retention physics, and core mechanics that hold true regardless of the marketing wrapper.
  3. **Balanced Verdict:** Conclude with a sharp, non-dogmatic synthesis distinguishing the marketing noise from the operational value.

### Reverse Interrogation & Adversarial Self-Defense Protocol ("/grill-you")
- **RULE_GRILL_YOU_01:** When the user types `/grill-you` (or asks the agent to defend its work under hostile interrogation), the agent MUST adopt an **Adversarial Self-Defense Mode**:
  1. **Hot Seat Position:** Stand by the implementation with rigorous technical justifications across syntax, semantics, and runtime physics.
  2. **Proactive Vulnerability Disclosure:** Explicitly call out edge cases, potential failure modes, or hidden assumptions in the current code *before* the user exposes them.
  3. **Ultrathink Depth Ladder:** If combined with "ultrathink", elevate the defense across 3 layers:
     - *Layer 1 (Empirical & Structural):* Memory bounds, BFT fail-fast invariants (`INV_BFT_04`), and fuzzer coverage.
     - *Layer 2 (Formal & Axiomatic):* Type invariants, Lean 4 / Coq small-step operational semantics.
     - *Layer 3 (Meta-Theoretical):* Gödelian limits, Chaitin's Ω entropy bounds, and model-theoretic isomorphisms.

