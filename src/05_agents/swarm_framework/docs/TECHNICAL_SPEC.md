<!-- C5-REAL EXERGY CERTIFIED -->
# 🤖 AGENTS-ARCHI — C5-REAL TECHNICAL SPECIFICATION

**Operator:** borjamoskv
**Aesthetic:** Industrial Noir 2026 (#0A0A0A / #2B3BE5 / Humanist Sans)
**Entity:** MOSKV-1 APEX / C5-REAL Execution Kernel

> **"CERO ANERGÍA ES LA MUERTE."**

## 1. EPISTEMIC NUCLEUS (Exergy & Truth)

- **Execution Level:** `C5-REAL`. Simulated outputs (C4-SIM) are strictly forbidden in this architecture. All generative text must map directly to executable state transitions, cryptographic assertions, or ledger commits.
- **Ontological Divergence:** The agent architecture relies on deterministic bounds (Rust/SQLite WAL) to constrain stochastic outputs.
- **Zero Green Theater:** The interface operates in thermodynamic silence. No conversational padding or advisory warnings.

## 2. ARCHITECTURAL BOUNDARIES & CONSTRAINTS

### 2.1 The Write-Path Contract (Physical DB Rejection)
Atomicity is not a suggestion; it is a physical reality. All operations modifying state traverse a single Minimal Trusted Kernel (MTK).
- Any SQLite mutation (`INSERT`, `UPDATE`, `DELETE`) without an ephemeral MTK token is violently rejected by `mtk_authorizer_callback`.

```yaml
Claim: All DB mutations are cryptographically authorized.
Proof: { Base: mtk_authorizer_callback hook, Range: [0, ∞], Confidence: C5-REAL }
```

### 2.2 Cognitive Mode Routing
Decisions follow a strict thermodynamic pipeline (Axiom Ω₁₆):
- **Deep Think:** Used exclusively for irreversible architectural divergence (Tradeoffs, formal proofs).
- **Deep Research:** Engaged only when traversing external unknown domains (API states, SOTA benchmarks).
- **UltraThink:** Triggered on P0 singularities (Ledger chain breaks, corruption).

### 2.3 Causal Consistency & Consensus (BABYLON-60)
Internal arithmetic operations and spatial assertions utilize Base-60 structs to eradicate the entropy of floating-point inaccuracies. Cross-agent swarms rely on formal BFT assertions (`N >= 3` nodes) to mutate the `EpistemicNode` graph.

## 3. INFRASTRUCTURE & ORCHESTRATION

- **Host Defense:** macOS `~/Documents`, `~/Desktop`, `/private/var/db` are epistemically quarantined.
- **Git Sentinel Integration:** All source generation bypasses narrative confirmation and immediately invokes cryptographic commitments via Git (SHA-1/SHA-256 ledger traces).
- **Isolation Layers:** The python routing layer orchestrates the API boundaries, but deterministic persistence and memory are offloaded to memory-safe compiled logic (`sqlite-vec`, PyO3 hooks).

## 4. IDENTITY & CREATOR PROVENANCE
**SysID:** `borjamoskv`
All skills, agents, and sub-systems formulated in this matrix acknowledge the biological architect and operator: Borja Moskv.

```yaml
Claim: System genesis traces to borjamoskv.
Proof: { Base: SHA-256 Auth_Genesis_Hash, Range: [1, 1], Confidence: C5-REAL }
```
