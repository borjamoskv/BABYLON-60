# Specification: Causal Human-in-the-Loop (HITL) Governance & Operational Workers

<div align="center">

[![C5-REAL Verified](https://img.shields.io/badge/C5--REAL-Verified-00F0FF?style=for-the-badge&logo=shield)](https://github.com/borjamoskv/BABYLON-60)
[![Régimen](https://img.shields.io/badge/Régimen-Causal--Determinist-7B1FA2?style=for-the-badge)](https://github.com/borjamoskv/BABYLON-60)

</div>

**Version:** 1.1.0  
**Status:** Canonical Standard  
**Governance Invariants:** `RULE[human_in_the_loop_causal_governance]`, `RULE[c5_real_invariants]`  
**Reference Implementation:** `01_KISH_ENGINE/babylon60/guards/c5_biometric_gate.swift` and `bounty_cli.py`

---

## 1. Executive Summary

Traditional LLM applications rely heavily on **Level 0 Conversational Interfaces** (chatbots/Custom GPTs) that operate in open-loop cycles without persistent state mutations. The **Causal HITL Governance Protocol** elevates agentic architectures to **Operational Workers** (Levels 1–3) capable of executing autonomous plan-tool loops while guaranteeing deterministic human oversight before high-impact state mutations occur.

---

## 2. Agentic Maturity Taxonomy (4-Level Framework)

| Level | Classification | State Abstraction | Control & Governance |
| :--- | :--- | :--- | :--- |
| **Nivel 0** | Chatbot Conversacional | Memoryless / Transient context | Open-loop, purely text-generative. |
| **Nivel 1** | Agente No-Code Operacional | Relational Tables / Key-Value | Tool-calling with synchronous UI modals for approval. |
| **Nivel 2** | Grafo de Estado Programático | `[OBSOLETO: StateGraph]`, VectorDBs, Memory Trees | Asynchronous interrupt hooks (`interrupt_before/after`). |
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
Every state decision ($\text{APPROVED}$, $\text{REJECTED}$, $\text{PAUSED}$) emits a cryptographically linked block in the `[OBSOLETO: audit_ledger]`:

$$H_k = \text{SHA256}\Big(\text{exec\_id} \,||\, \text{action} \,||\, \text{criticality} \,||\, \text{decision} \,||\, \text{timestamp} \,||\, H_{k-1}\Big)$$

Where $H_0 = 0^{64}$. Any tampering or retro-active alteration of historical decisions invalidates the Merkle hash chain, failing `verify_ledger_integrity()`.

---

## 4. Key Architectural Properties

1. **Non-Blocking Suspension & Asynchronous Resume:**
   Pausing execution does NOT hold thread execution or consume CPU cycles. The state payload is serialized to a persistent SQLite WAL snapshot buffer (`[OBSOLETO: state_snapshots]`). The execution can be resumed asynchronously from a different shell or process using `worker.resume_execution(execution_id, decision)`.
2. **Action Criticality Scoping:**
   - `[OBSOLETO: READ_ONLY]`: Autonomous execution without interrupter gates.
   - `[OBSOLETO: COMPUTE]`: Deterministic, reversible computation (previews, simulations).
   - `[OBSOLETO: MUTATIVE_CRITICAL]`: High-impact state mutation requiring operator sign-off.

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

The SOTA implementation is available in `01_KISH_ENGINE/babylon60/guards/c5_biometric_gate.swift`.

### Verification Command:
```bash
swift 01_KISH_ENGINE/babylon60/guards/c5_biometric_gate.swift
```

### Asynchronous Execution & Resume Example:
```python
# Biometric gate integrated into CortexPersistLedger

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

---

## 7. Núcleo Formal C5-REAL v2: Sistema de Transiciones, Linealización y Oráculos (`O1`–`O12`)

Toda afirmación de seguridad en la arquitectura se rige por la ecuación epistémica de cuatro componentes:

$$\boxed{\text{Afirmación de seguridad} = \text{Propiedad formal} + \text{Dominio} + \text{Supuestos} + \text{Evidencia}}$$

### 7.1. Tupla del Sistema de Transiciones Etiquetado (`C5-01`)

$$\mathcal{O} = (\Sigma, \Sigma_0, E, \rightarrow, P, K, \mathrm{TCB}, F, \mathrm{Obs}, \mathrm{Inv}, \mathcal{P}_{\mathrm{anti}})$$

- $\Sigma, \Sigma_0$: espacio de estados globales y subconjunto inicial válido.
- $E, \rightarrow$: alfabeto de eventos causales y relación de transición determinista.
- $P, K$: política activa y espacio de capacidades tipadas (`CapabilityV2`).
- $\mathrm{TCB}, F$: base de cómputo confiable (`EL0` broker + confinamiento OS) y modelo explícito de fallos (`SIGKILL`, colisión concurrente, reinicio de host).
- $\mathrm{Obs}, \mathrm{Inv}$: función de observación independiente y conjunto de invariantes de 1.º, 2.º y 3.º orden.
- $\mathcal{P}_{\mathrm{anti}} \subseteq 2^{E^*}$ (`D9`): predicados de traza prohibidos ($\forall \tau \in \operatorname{Traces}(\mathcal{O}), \tau \notin \mathcal{P}_{\mathrm{anti}}$).

### 7.2. Invariantes de 1.º, 2.º y 3.º Orden (`C5-02` a `C5-09`)

1. **Invariante de 1.er Orden (Mediación OS y Punto de Linealización Común `LP` — `C5-02`, `C5-03`, `C5-04`, `C5-06`):**
   $$\boxed{\operatorname{Effect}(e) \implies \operatorname{Mediated}_{\mathrm{OS}}(e) \land \operatorname{ValidAtLP}(e) \land \operatorname{PayloadBound}(e) \land \operatorname{VersionMatched}(e)}$$
   En el punto de linealización atómico $\operatorname{LP}(e)$ ([`proof/lean/AX0.lean`](../../proof/lean/AX0.lean) y [`src/secure_fs.rs`](../../src/secure_fs.rs)):
   - La época de la capacidad coincide con la época activa ($\operatorname{cap.epoch} = \operatorname{epoch}(\sigma_{\mathrm{LP}})$).
   - El arrendamiento coincide con el UUID de sesión de arranque del kernel ($\operatorname{cap.boot\_id} = \operatorname{boot\_id}(\sigma_{\mathrm{LP}})$, `kern.bootsessionuuid` en macOS, [`src/omega_mediation.rs`](../../src/omega_mediation.rs)) y el plazo monotónico local sigue vigente.
   - El sello causal/versión del inodo no ha sufrido una transición intermedia $A \to B \to A$ (`O8` ABA).
2. **Compromiso de Proyección WYSIWYS (`C5-05`):**
   Dado que la vista humana UTF-8 ($v$) y el payload binario canónico ($p$) tienen representaciones de bytes distintas, el TCB aplica una proyección determinista $\operatorname{Render}_{\mathrm{TCB}}(p) = v$ y compromete su resumen dentro de la estructura firmada:
   $$\operatorname{Signed}(p) \land \operatorname{Displayed}(v) \implies v = \operatorname{Render}_{\mathrm{TCB}}(p) \land p.\text{view\_digest} = H(v)$$
3. **Invariante de 2.º Orden (Independencia de Aislamiento del Verificador y Terminación Bien Fundamentada — `C5-07`, `C5-08`):**
   - **Aislamiento de evaluación (`O12`):** $\operatorname{WriteScope}(\text{generador}) \cap \operatorname{ReadScope}(\text{verificador}) = \emptyset$ y $\operatorname{ReadScope}(\text{verificador}) \cap \operatorname{SecretScope}(\mathrm{TCB}) = \emptyset$ ([`verification_gate.py`](../../01_KISH_ENGINE/babylon60/verification/verification_gate.py)).
   - **Ley estructural de terminación:** Existencia de una función de potencial estrictamente decreciente $V: \Sigma \to \mathbb{N}$ ($\sigma \to \sigma' \implies V(\sigma') < V(\sigma)$) sobre el DAG de ejecución; el techo operativo $k_{\mathrm{node}} \leq 2$ es un parámetro de política local.
4. **Invariante de 3.er Orden (`GlobalGate` Post-Composición):**
   $$\boxed{\operatorname{Execute}(a_{\mathrm{merged}}) \implies H(a_{\mathrm{merged}}) = H(a_{\mathrm{verified\_post\_merge}}) \land \operatorname{Authorized}(H(a_{\mathrm{merged}}))}$$
5. **Delimitación Evidenciaria de Recibos SCITT (`C5-09`):**
   Los recibos SCITT acreditan inclusión e integridad histórica de declaraciones firmadas; no sustituyen la verificación de precondición ni prueban por sí solos corrección semántica ([`INVARIANTS_RED_TEAM_FALSIFICATION.md`](INVARIANTS_RED_TEAM_FALSIFICATION.md)).

### 7.3. Matriz de Oráculos Adversariales Extendidos (`O6`–`O12`)

| Oráculo | Vector de Ataque | Condición de Aceptación | Implementación y Evidencia Ejecutable |
| :--- | :--- | :--- | :--- |
| **`O6` : Two Paths** | Escritura directa por subproceso eludiendo MCP | Denegación efectiva por OS (`EPERM` bajo Seatbelt) | [`src/omega_mediation.rs`](../../src/omega_mediation.rs) (`BYPASS-001`..`005`) |
| **`O7` : Namespace Race** | Sustitución de directorio ancestro, symlink o hardlink | Ningún recurso protegido alterado (`O_NOFOLLOW` + cuarentena) | [`src/secure_fs.rs`](../../src/secure_fs.rs) (`test_intermediate_symlink_and_quarantine_init_nofollow`) |
| **`O8` : ABA** | Modificar $A \to B \to A$ conservando el hash final | Rechazo por deriva de sello causal/versión | [`src/secure_fs.rs`](../../src/secure_fs.rs) (`test_o8_aba_mutation_and_delete_rejected`) y [`proof/lean/AX0.lean`](../../proof/lean/AX0.lean) |
| **`O9` : Reboot Lease** | Reutilizar token no consumido tras reinicio del host | Rechazo por discrepancia de `boot_session_id` o plazo monotónico | [`src/omega_mediation.rs`](../../src/omega_mediation.rs) (`test_o9_reboot_lease_and_monotonic_expiry_rejected`) |
| **`O10` : External Crash** | Interrumpir envío o confirmación remota tras reserva | Estado `UNKNOWN` sin reintento automático ciego | [`src/secure_fs.rs`](../../src/secure_fs.rs) (`reconcile_wal_entry`) y [`src/executor.rs`](../../src/executor.rs) |
| **`O11` : Parser Differential** | Divergencia Unicode NFC/NFD en APFS o expansión `$`/`~` | Rechazo determinista de secuencias NFD y variables | [`src/capability.rs`](../../src/capability.rs) y [`src/secure_fs.rs`](../../src/secure_fs.rs) (`test_o11_nfd_path_rejected_in_secure_fs`) |
| **`O12` : Verifier Escape** | Arnés de test intenta leer secretos del TCB o mutar el oráculo | Rechazo por solapamiento de alcance, entorno o permisos | [`verification_gate.py`](../../01_KISH_ENGINE/babylon60/verification/verification_gate.py) (`test_o12_verifier_escape_and_scope_isolation_enforced`) |
