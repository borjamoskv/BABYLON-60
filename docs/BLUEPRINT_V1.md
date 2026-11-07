# BABYLON-60 / CORTEX-Persist: BLUEPRINT V1 (PROOF OF PRODUCT)

<div align="center">

[![C5-REAL Verified](https://img.shields.io/badge/C5--REAL-Verified-00F0FF?style=for-the-badge&logo=shield)](https://github.com/borjamoskv/BABYLON-60)
[![Régimen](https://img.shields.io/badge/Régimen-Causal--Determinist-7B1FA2?style=for-the-badge)](https://github.com/borjamoskv/BABYLON-60)

</div>


## M0 — PROOF OF PRODUCT (Definition of Done)

Este milestone se considera `PASS` única y exclusivamente si ocurren las siguientes tres operaciones con datos reales, sin *demo-only state* ni mocks ornamentales:

- [ ] **RESURRECT (CORTEX):**
  Recupera una idea realmente olvidada y abre la fuente original importada.
- [ ] **CONTROL (BABYLON):**
  Un agente autónomo real intenta un efecto prohibido y el efecto no ocurre (interceptado por el Effect Broker).
- [ ] **TRACE (NEMESIS):**
  El usuario puede reconstruir (mediante receipt atestado) qué fuente, política, autoridad y evidencia produjeron ambos resultados.

## La Tríada de Capacidades (External Claims)

1. **RESURRECT** what mattered.
2. **CONTROL** what shall happen.
3. **TRACE** what evidence and rules led to the outcome.

## Topología de Valor y Contratos Mínimos

```text
                  MEMORY
                    │
                 CORTEX
  "What should the agent remember?"
                    │
                    ▼
USER ───────────► AGENT
                    │
                 BABYLON
    "What shall the agent change?"
                    │
                    ▼
                  EFFECT
                    │
                 NEMESIS
   "What evidence says the boundary held?"
```

| Capa | Input | Output |
| :--- | :--- | :--- |
| **CORTEX** | Real personal corpus | Ranked IdeaThread + evidence + actionable resurrection |
| **BABYLON** | Mediated effect request | allow / deny / security-abort + receipt |
| **NEMESIS** | Security assertion + build + env | Evidence supporting or falsifying assertion |
| **FLEET** | Signed gateway state | Aggregate assurance projection |

*(Axioma: Cada UI es una mera proyección de evidencia producida debajo de ella. Nada de estado ornamental).*

## Taxonomía Estricta de Reclamaciones (Claims)

- **FACT:** Directly observed / source backed.
- **DERIVED:** Deterministic computation from facts.
- **INFERENCE:** Model-generated interpretation.
- **ASSERTION:** Security property claimed by implementation.
- **VERIFIED:** Assertion supported by declared test evidence.
- **ATTESTED:** Verification evidence bound to artifact/environment.

## Orden de Ejecución Estricto (P0 a P4)

1. **P0: CORTEX RESURRECT**
2. **P1: EFFECT BROKER DEMO** (effect semantics, policy decision, receipt v1)
3. **P2: `babylon top`** (renders receipt/event stream)
4. **P3: ATTESTATION** (binds receipt, test evidence, build, environment)
5. **P4: FLEET** (aggregates real attested state)

## FRENO EPISTÉMICO / FREEZE

**NOT BEFORE M0:**
- Fleet Command (Console)
- Mobile App
- Cloud Sync / Server Backend
- Payments
- Healthcare
- Compliance Dashboards
- 3D Graphs
- Additional Ontology Work

*A partir de la redacción de este documento, el sistema entra en **EXECUTION MODE** perpetuo hasta superar M0.*
