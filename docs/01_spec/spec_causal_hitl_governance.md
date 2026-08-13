# Specification: Causal Human-in-the-Loop (HITL) Governance & Operational Workers

<div align="center">

[![C5-REAL Verified](https://img.shields.io/badge/C5--REAL-Verified-00F0FF?style=for-the-badge&logo=shield)](https://github.com/borjamoskv/BABYLON-60)
[![Régimen](https://img.shields.io/badge/Régimen-Causal--Determinist-7B1FA2?style=for-the-badge)](https://github.com/borjamoskv/BABYLON-60)

</div>

**Version:** 1.1.0  
**Status:** Canonical Standard  
**Governance Invariants:** `RULE[human_in_the_loop_causal_governance]`, `RULE[c5_real_invariants]`  
**Reference Implementation:** [scripts/poc_causal_hitl_agent.py](../../scripts/c5_cortex/)  

---

## 1. Executive Summary

Traditional LLM applications rely heavily on **Level 0 Conversational Interfaces** (chatbots/Custom GPTs) that operate in open-loop cycles without persistent state mutations. The **Causal HITL Governance Protocol** elevates agentic architectures to **Operational Workers** (Levels 1–3) capable of executing autonomous plan-tool loops while guaranteeing deterministic human oversight before high-impact state mutations occur.

---

## 2. Agentic Maturity Taxonomy (4-Level Framework)

| Level | Classification | State Abstraction | Control & Governance |
| :--- | :--- | :--- | :--- |
| **Nivel 0** | Chatbot Conversacional | Memoryless / Transient context | Open-loop, purely text-generative. |
| **Nivel 1** | Agente No-Code Operacional | Relational Tables / Key-Value | Tool-calling with synchronous UI modals for approval. |
| **Nivel 2** | Grafo de Estado Programático | `StateGraph`, VectorDBs, Memory Trees | Asynchronous interrupt hooks (`interrupt_before/after`). |
| **Nivel 3** | Gobernanza Causal & Formal | Invariant Proofs (Lean 4), Exergy Bounds | Non-blocking state snapshotting, causal gates & C-ABI SCITT receipts. |

---

## 3. Mathematical State Transition Model & Cryptographic Verification

Let $\mathcal{S}$ be the Dominio C5-REAL state space, $\mathcal{A}$ the set of agent actions, and $\mathcal{A}_{\text{critical}} \subset \mathcal{A}$ the subset of mutative actions requiring operator authorization.

The Dominio C5-REAL state transition function $\mathcal{T}: \mathcal{S} \times \mathcal{A} \rightarrow \mathcal{S}$ is governed by the causal gate operator $\mathcal{G}_{\text{human}}$:

$$\text{State}_{t+1} = \begin{cases} 
\mathcal{F}(\text{State}_t, a_t) & \text{if } a_t \notin \mathcal{A}_{\text{critical}} \lor \mathcal{G}_{\text{human}}(a_t, \text{State}_t) = \text{APPROVED} \\[8pt]
\text{PAUSED}(\text{State}_t, a_t) & \text{if } a_t \in \mathcal{A}_{\text{critical}} \land \mathcal{G}_{\text{human}}(a_t, \text{State}_t) = \text{PENDING} \\[8pt]
\text{ABORTED}(\text{State}_t, \text{reason}) & \text{if } \mathcal{G}_{\text{human}}(a_t, \text{State}_t) = \text{REJECTED}
\end{cases}$$

### Cryptographic Tamper-Evident SHA-256 Receipts (SCITT Profile)
Every state decision ($\text{APPROVED}$, $\text{REJECTED}$, $\text{PAUSED}$) emits a cryptographically linked block in the `audit_ledger`:

$$H_k = \text{SHA256}\Big(\text{exec\_id} \,||\, \text{action} \,||\, \text{criticality} \,||\, \text{decision} \,||\, \text{timestamp} \,||\, H_{k-1}\Big)$$

Where $H_0 = 0^{64}$. Any tampering or retro-active alteration of historical decisions invalidates the Merkle hash chain, failing `verify_ledger_integrity()`.

---

## 4. Key Architectural Properties

1. **Non-Blocking Suspension & Asynchronous Resume:**
   Pausing execution does NOT hold thread execution or consume CPU cycles. The state payload is serialized to a persistent SQLite WAL snapshot buffer (`state_snapshots`). The execution can be resumed asynchronously from a different shell or process using `worker.resume_execution(execution_id, decision)`.
2. **Action Criticality Scoping:**
   - `READ_ONLY`: Autonomous execution without interrupter gates.
   - `COMPUTE`: Deterministic, reversible computation (previews, simulations).
   - `MUTATIVE_CRITICAL`: High-impact state mutation requiring operator sign-off.

---

## 5. Multidisciplinary Domain Applications

The operational worker architecture bridges across diverse research and engineering domains:

### A. Business Operations & Data Processing
* **Autonomous Task:** Ingestion, enrichment, and qualification of records.
* **Critical Gate:** Dispatching external communications or committing financial record changes.

### B. Security & Codebase Auditing
* **Autonomous Task:** Static analysis, AST parsing, detection of hallucinated imports via `existence-gap-audit`.
* **Critical Gate:** Applying automated refactoring patches or running destructive git purges.

### C. Audiovisual & Motion Design Synthesis
* **Autonomous Task:** Timeline parsing, speech synthesis, and low-res frame preview generation (Remotion/Revideo).
* **Critical Gate:** Triggering full 4K ProRes master renders or remote CDN publication.

---

## 6. Reference Implementation & Usage

The SOTA implementation is available in `scripts/poc_causal_hitl_agent.py`.

### Verification Command:
```bash
python3 scripts/poc_causal_hitl_agent.py
```

### Asynchronous Execution & Resume Example:
```python
from scripts.poc_causal_hitl_agent import CausalHitlEngine, OperationalWorkerPoC, ActionCriticality, AgentState

engine = CausalHitlEngine(db_path="cortex_governance.db")
worker = OperationalWorkerPoC(
    execution_id="EXEC-CRM-2026",
    domain="Business_CRM_Operations",
    engine=engine
)

# 1. Asynchronous Execution (Pauses safely at MUTATIVE_CRITICAL step)
status = worker.execute_plan(workflow_steps, async_mode=True)

# 2. Resuming later via operator sign-off decision
if status == AgentState.PAUSED_AWAITING_SIGN_OFF:
    worker.resume_execution(decision="APPROVED", steps=workflow_steps)

# 3. Verifying Cryptographic Tamper-Evident Ledger
assert engine.verify_ledger_integrity() is True
```