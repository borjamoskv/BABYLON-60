# LEGION-10k Scaling Limits & Epistemic Boundaries
*(Resolves Issue #414)*

**Status:** Crystalized (C5-REAL)  
**Author:** borjamoskv  
**Date:** 2026-07-07  

## 1. Context & Motivation
LEGION-10k defines the theoretical and empirical scaling limits for the autonomous Swarm in the BABYLON-60 architecture. As we scale the number of subagents, we encounter thermodynamic boundaries (Anergía) and epistemic collapse (Context Rot / Sensor Drift). This document formalizes those limits.

## 2. Hard Scaling Limits
1. **Quorum Saturation (N=10,000):** 
   - The Byzantine Fault Tolerance (BFT) consensus engine (`babylon60/consensus/byzantine.py`) operates optimally up to $N = 3,333$ active faulting nodes ($f < N/3$). Pushing beyond 10k nodes results in exponential message complexity overhead ($O(N^2)$).
2. **Context Leakage (Sensor Drift):**
   - Agents isolated in branches must merge via SAGA Runtime. Concurrent DAG merges exceeding 50 nodes per second saturate the Reality Ledger's topological sort constraints.
3. **Exergy Depletion (API Boundaries):**
   - Spawning 10k agents on heavy LLMs (e.g., Claude 4.6 / Gemini 3.1) exceeds prompt budget and thermodynamic limits (`OuroborosEntropyGuard` hard limit on async tasks).

## 3. Mitigation: The 135-Matrix Mapping
To bypass these limits, the Kernel relies on the **Macrófago Ontológico**. Instead of scaling linearly, LEGION collapses the problem space into the 135 invariants of CORTEX-PERSIST. 

## 4. Operational Invariants
- `MAX_CONCURRENT_SUBAGENTS = 1000` (Soft limit before entropy quarantine)
- `SAGA_MERGE_TIMEOUT = 5000ms`
- **Weaponized Forgetting:** Any agent state not committed to the DAG within 300 seconds is subjected to Apoptosis (`babylon60/worker/epistemic_gc.py`).

## 5. Conclusion
LEGION-10k is not a mandate to run 10,000 agents simultaneously, but the mathematical boundary where the C5-REAL execution model transitions from deterministic consensus to stochastic chaos. Scaling requires intelligent pruning (Apoptosis), not infinite compute.
