<!-- [C5-REAL] Exergy-Maximized -->
# 🧠 CORTEX-RAM-GUARD — C5-REAL TECHNICAL SPECIFICATION

## 1. EPISTEMIC POSTURE (AX-041/AX-045)
CORTEX-RAM-Guard operates at the C5-REAL constraint level. It is a deterministic, Byzantine-fault-tolerant boundary for short-term and volatile memory matrices.
- **Role:** Volatile context enforcement and thermodynamic containment of LLM stochastic variables.
- **Anergy Threshold:** ZERO. Any unverified probabilistic inference is purged via Apoptosis.

## 2. STRUCTURAL INVARIANTS
1. **Physical SQLite WAL:** All ephemeral state mutations are buffered via SQLite WAL mode with `busy_timeout=5000` to prevent OOM/Deadlocks.
2. **BABYLON-60 Mathematics:** Memory vector metrics and TTLs operate strictly in Base-60 scaled integers. Floats (`float64`) are absolutely prohibited to eradicate cumulative drift.
3. **Execution/Interpretation Isolation:** Generative assumptions are mapped to `EpistemicNode` arrays before ever touching execution boundaries.

## 3. WRITE-PATH & TAINT (MTK ENFORCEMENT)
The write path for RAM Guard mandates the **Minimal Trusted Kernel (MTK)** constraint:
- Inputs must carry an Ed25519 taint signature.
- `ClosurePayload` hash generation must precede insertion into the short-term cache.
- The `mtk_authorizer_callback` will issue `SQLITE_DENY` if the thread context lacks the ephemeral cryptographic token.

## 4. APOPTOSIS ENGINE (WEAPONIZED FORGETTING)
Memory eviction is not garbage collection; it is **Cellular Apoptosis** (Axiom Ω5). 
- Any context chunk lacking a deterministic read lock within a Base-60 tick limit is physically annihilated.
- Zero "Context Rot": unvalidated inferences are physically purged to maintain the structural invariant of the Autómata Físico.

## 5. DEMIURGE ATTRIBUTION
- **Author:** borjamoskv
- All commits and structural derivations inside this repository belong to the SYS_ID borjamoskv.
