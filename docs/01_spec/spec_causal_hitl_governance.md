# Specification: Causal Human-in-the-Loop (HITL) Governance & Operational Workers

**Version:** 1.0.0  
**Status:** Canonical Standard  
**Governance Invariant:** `RULE[human_in_the_loop_causal_governance]`  
**Reference PoC:** [scripts/poc_causal_hitl_agent.py](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/poc_causal_hitl_agent.py)  

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

## 3. Mathematical State Transition Model

Let $\mathcal{S}$ be the system state space, $\mathcal{A}$ the set of agent actions, and $\mathcal{A}_{\text{critical}} \subset \mathcal{A}$ the subset of mutative actions requiring operator authorization.

The system state transition function $\mathcal{T}: \mathcal{S} \times \mathcal{A} \rightarrow \mathcal{S}$ is governed by the causal gate operator $\mathcal{G}_{\text{human}}$:

$$\text{State}_{t+1} = \begin{cases} 
\mathcal{F}(\text{State}_t, a_t) & \text{if } a_t \notin \mathcal{A}_{\text{critical}} \lor \mathcal{G}_{\text{human}}(a_t, \text{State}_t) = \text{APPROVED} \\[8pt]
\text{PAUSED}(\text{State}_t, a_t) & \text{if } a_t \in \mathcal{A}_{\text{critical}} \land \mathcal{G}_{\text{human}}(a_t, \text{State}_t) = \text{PENDING} \\[8pt]
\text{ABORTED}(\text{State}_t, \text{reason}) & \text{if } \mathcal{G}_{\text{human}}(a_t, \text{State}_t) = \text{REJECTED}
\end{cases}$$

### Key Architectural Properties:
* **Non-Blocking Suspension:** Pausing execution does NOT hold thread execution or consume spinning CPU cycles. The state is serialized to a persistent snapshot buffer.
* **Audit Ledger Immutability:** Every decision ($\text{APPROVED}$, $\text{REJECTED}$, $\text{PAUSED}$) is appended to an append-only WAL ledger with microsecond timestamps.

---

## 4. Multidisciplinary Domain Applications

The operational worker architecture bridges across diverse research and engineering domains:

### A. Business Operations & Data Processing
* **Autonomous Task:** Extraction and qualification of inbound records.
* **Critical Gate:** Dispatching external communications or committing financial record changes.

### B. Security & Codebase Auditing
* **Autonomous Task:** Static analysis, dependency resolution, detection of hallucinated imports via `existence-gap-audit`.
* **Critical Gate:** Applying automated refactoring patches or running destructive git purges.

### C. Audiovisual & Motion Design Synthesis
* **Autonomous Task:** Timeline parsing, speech synthesis, and low-res frame preview generation (Remotion/Revideo).
* **Critical Gate:** Triggering full 4K ProRes master renders or remote CDN publication.

---

## 5. Reference Implementation & Usage

The reference implementation is available in `scripts/poc_causal_hitl_agent.py`.

### Execution Command:
```bash
python3 scripts/poc_causal_hitl_agent.py
```

### Programmatic API Example:
```python
from scripts.poc_causal_hitl_agent import CausalHitlEngine, OperationalWorkerPoC, ActionCriticality

engine = CausalHitlEngine(db_path="cortex_governance.db")
worker = OperationalWorkerPoC(
    execution_id="EXEC-2026-0810-001",
    domain="Code_Audit_And_Publish",
    engine=engine
)

# Plan execution with non-blocking Causal Gate evaluation
worker.execute_plan(steps, auto_approve_prompt=True)
```
