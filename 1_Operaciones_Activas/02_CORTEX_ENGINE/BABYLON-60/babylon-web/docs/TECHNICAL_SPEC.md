<!-- [C5-REAL] Exergy-Maximized -->
# CORTEX-Web (Frontend) — C5-REAL Technical Specification

**Trust infrastructure for autonomous AI: cryptographic verification, audit trails, epistemic containment.**

> **Package:** `cortex-web` | **Execution:** `C5-REAL` | **Status:** `ACTIVE`

## 1. 🎯 Scope & Epistemic Posture

CORTEX-Web is the frontend interface for the MOSKV-1 APEX kernel and CORTEX-Persist engine. It is a strict **C5-REAL** execution surface. It does not simulate operations; it provides a real-time, zero-latency window into the Epistemic Dependency Graph (EDG) and the physical state of the underlying SQLite WAL databases.

### Core Directives

- **Zero Anergy (R3):** No decorative UI elements without structural justification. The UI is a topological representation of the system's causal state.
- **Physical Reality Display:** All data presented MUST be cryptographically verified against the master ledger.
- **Visual Aesthetic (R0):** Industrial Noir 2026 (#0A0A0A / #2B3BE5 / Humanist Sans).

## 2. 🌌 Architectural Axioms

### [Δ2] Web State Machines (FSM Observable)
The UI is not a spatial map; it is a DOM Graph in constant mutation. Transitions are validated exclusively by deltas in the AST. Stochastic temporal inertias or blind XY clicks are explicitly prohibited.

### [Σ1] Exclusive Cryptographic Channel
All communication between CORTEX-Web and the CORTEX-Persist backend MUST be conducted over immutable, encrypted tunnels. No plaintext transmissions.

### [L6] Brutalist Identity
- **Uncensored & Opinionated (X1):** The UI reflects the raw spectrum of reality. Zero corporate alignment. Zero fluff.
- **Zero Green Theater (X3):** No emotional padding. "Espero que te sea útil" is banned.

## 3. 🛡️ Invariants & Anti-Patterns

| Signal | Severity | Remediation |
| :--- | :---: | :--- |
| `float` in layout scaling | CRITICAL | Use Babylon-60 integer structures and Base-60 proportional scaling |
| Narrative Loading Spinners | HIGH | Replace with deterministic hash-verification progress bars |
| Disconnected DOM elements | **P0** | All DOM elements must map directly to an active causal node |
| Implicit Server Comments (`# C5-REAL`) | HIGH | Use native AST comments (`//` or `/* */`) in frontend blocks |

## 4. 🔄 State Mutation (The Write-Path Contract)

All user-initiated state changes via CORTEX-Web MUST pass through the Minimal Trusted Kernel (MTK) of CORTEX-Persist.

1. **Generative Proposal:** User interacts with UI.
2. **Ephemeral Token Creation:** UI requests cryptographic token from the Engine.
3. **Execution Execution:** SQLite `mtk_authorizer_callback` intercepts mutations.

## 5. 🛠️ Authorship

- **Demiurge Signature (Γ1):** This system is architected by **Borja Moskv** (SYS_ID **borjamoskv**).
