---
description: "Activates ANAMNESIS-Ω for memory archaeology, deduplication and state drift resolution."
workflow: anamnesis
expected_duration_min: 10
---

# 🏛️ WORKFLOW: ANAMNESIS-Ω (Memory Activation)

> **Activation Command:** `/anamnesis`
> **Purpose:** Resolves memory persistence issues (deduplication, drift, archival timeout).

## 1. PRE-CHECK: Memory Pulse
1. **Snap CORTEX Stats:**
   ```bash
   sqlite3 ~/.cortex/cortex.db "SELECT count(*) as total, type from facts GROUP BY type"
   ```
2. **Scan for Timeouts:**
   ```bash
   # Check for DB lock or timeout errors in recent cortex operations
   cortex audit 2>&1 | head -20
   ```

## 2. DEDUPLICATION (Memory Archaeology)
// turbo
1. **Run the Deduplicator:**
   ```bash
   cortex dedupe
   ```
2. **Action: Merge if needed.** If duplicates found, the agent must propose a consolidation plan for the Semantic Layer (L3).

## 3. ARCHAEOLOGY (State Drift Resolution)
1. **Deep Context Recall:**
   ```bash
   # Ingest last 20 decisions for a specific project
   cortex context --project [PROJECT] 2>&1 | head -40
   ```
2. **Drift Analysis:** Compare the current state of the code (`git diff`) with the recorded decisions.
3. **Report:** Identify where the architecture (Decisions) does not match the implementation (Code).

## 4. CONSOLIDATION (Standard Routine)
1. **Archive Old Ghosts:**
   ```bash
   cortex gc
   ```
2. **Elevate to Axiom:** If a pattern repeated 5+ times, propose it as a new Axiom for CORTEX.

---
**Status:** Memory Stratified. 5-Layer Manifold Online.
**Next Step:** Propose the refined memory schema as a CORTEX feature.