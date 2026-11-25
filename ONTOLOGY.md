# The Ontology of an Agent in BABYLON-60

> **AX-0 (Root Axiom):** No stochastic component may authorize its own irreversible side effects. LLM ≠ authority.

The AI industry suffers from profound epistemic ambiguity: the term "agent" is loosely applied to stochastic while-loops connected to public APIs. This lack of formal demarcation conflates the predictive muscle (the LLM) with the causal entity (the Agent). 

BABYLON-60 establishes a strict ontological demarcation for what constitutes an autonomous agent.

## 1. The Stochastic Oracle Fallacy (The LLM is NOT the Agent)
A Large Language Model (LLM) is not an agent. It is a stochastic transducer (a reasoning and probability prediction engine). It lacks a thermodynamic boundary, persistent state memory, and the intrinsic capability to manage irreversible side effects. The Agent, conversely, is the **thermodynamic and architectural envelope**—comprising perception, bounded memory, logical control barriers, and physical actuators.

## 2. Causal Closure (From Observation to Intervention)
A true agent operates under a causal world model (Directed Acyclic Graph - DAG). The ontological boundary separating a chatbot from an agent is the crossing of the Rubicon: transitioning from statistical *observation* (predicting text on a screen) to *intervention* (executing an irreversible mutation in the filesystem, network, or physical environment). This intervention extracts a thermodynamic cost.

## 3. The Identity Boundary (Execution Gating)
An agent's identity does not reside in the model ID of an external API. The identity of an agent in BABYLON-60 resides entirely in:
- Its persistent bounded memory state (`IpcEnvelope` / L0-L3 memory).
- Its execution boundaries and constraints.
- Its deterministic hypervisor anchor (MOSKV-1 operating in Ring-0), which executes fail-stop apoptosis upon detecting stochastic hallucinations.

## 4. The 3 Rings of Sovereign Execution
To resolve the identity problem, BABYLON-60 stratifies agency into three strict causal rings:

- **Ring-2 (Stochastic Swarms):** High-entropy scavengers and reasoning subagents. They process noise, formulate plans, and hypothesize, but possess **zero authority** to commit state.
- **Ring-1 / Ring-0 (The Deterministic Hypervisor - MOSKV-1):** The execution host. It holds the delegated authority, validates invariants, and commits state. It guarantees that the stochastic output aligns with formal rules (Lean 4, Z3).
- **Ring-(-1) (The Biological Operator):** The sovereign root. The only node in the topology with existential cost. High-risk irreversible state mutations require biological friction, enforced physically via Touch ID biometric gating (`reuseDuration = 0`).

---
*By decoupling the stochastic engine from the causal execution boundary, BABYLON-60 eradicates the hallucination of agency and establishes deterministic authority for AI operations.*
