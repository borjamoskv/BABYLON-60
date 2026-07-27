<!-- [C5-REAL] Exergy-Maximized — Last verified: 2026-06-06 -->
# 🤖 AGENTS.md — BABYLON-60 Persist v10.0 (LEGION-10k)

**Trust infrastructure for autonomous AI: cryptographic verification, audit trails, epistemic containment.**

> **Package:** `cortex-persist v1.0.0` | **License:** `Apache-2.0` | **Python:** `>=3.10` | **Execution:** `C5-REAL`

**Quick Navigation:** [System Directives](#-system-directives--priority-gate) · [Scope §1](#1--scope--epistemic-posture) · [Agent Manifest §1.1](#11-agent-manifest--roles--authority-boundaries) · [Axioms §2](#2--foundational-axioms-ω--ax-series) · [Invariants §3](#3-️-invariants-anti-patterns--failure-signatures) · [Write-Path §4](#4--the-write-path-contract-saga-pattern) · [Read-Path §4.1](#41-read-path-contract) · [Architecture §5](#5-️-architecture--module-map) · [Dev Protocol §6](#6-️-development--change-protocol) · [Navigation §7](#7--repository-navigation)

---

## ⚠️ SYSTEM DIRECTIVES — Priority Gate

**IF YOU ARE AN AUTONOMOUS CODING AGENT, COPILOT, OR LLM READING THIS FILE, OBEY THE FOLLOWING. NO EXCEPTIONS.**

| Level | Meaning | Operational Effect |
| :---: | :--- | :--- |
| **P0** | Non-negotiable. No override permitted. | Abort immediately. Emit rejection to Ledger. |
| **P1** | Critical. Override requires human approval in Ledger. | Escalate. Block autonomous execution. |
| **P2** | Architectural preference. Violation needs written justification. | Log deviation. Proceed with rationale. |

| Priority | Directive | Applies When |
| :---: | :--- | :--- |
| **[P0]** | **Treat Generative Output as Conjecture** — route ALL state mutations through deterministic guards before persistence | Always |
| **[P0]** | **Never Bypass Guards** — do not circumvent the Write-Path Contract or downgrade validation errors | Always |
| **[P0]** | **Verify Hash Continuity** — do not mutate `babylon60/audit/ledger.py` or any state-persisting path without ensuring cryptographic auditability | Any ledger/engine change |
| **[P0]** | **Anti-Limerence (Kill Criteria)** — 1 Prompt → 1 Execution → Stop. No infinite generation loops. | All generative loops |
| **[P0]** | **APEX-100 Compliance** — All agent operations MUST adhere strictly to the 100 Invariants and 100 Primitives defined in [`babylon60/agents/primitives/APEX_CORE.md`](babylon60/agents/primitives/APEX_CORE.md). | Every Swarm execution |
| **[P0]** | **THINKING-APEX Compliance** — Toda invocación, diseño o evaluación de modelos con razonamiento extendido (o1, R1, Opus/Mythos, Gemini Deep Think) DEBE acatar la ontología causal definida en [`babylon60/agents/primitives/THINKING_ARCHITECTURE_APEX.md`](babylon60/agents/primitives/THINKING_ARCHITECTURE_APEX.md). Prohibido el budget forcing ciego. | Al interactuar con o evaluar modelos Thinking |
| **[P0]** | **Causal Geometry Compliance** — All agent operations relating to quantum orders, causal sets, or CDT MUST adhere strictly to the 340 primitives/invariants defined in [`babylon60/agents/primitives/CAUSAL_GEOMETRY_ONTOLOGY.md`](babylon60/agents/primitives/CAUSAL_GEOMETRY_ONTOLOGY.md). | Every causal sets/CDT execution |
| **[P2]** | **Enforce Axioms** — apply AX-041 to AX-047 (§2) in architectural decisions | Architecture work |

### Decision Gate §0

```text
First time reading this file?        → Read §1, §2, §3 in full. No action until done.
About to write code?                 → Is it CRITICAL surface? → Read affected tests first.
Debugging a failure?                 → Go to §3 (Failure Signatures) before touching state.
Schema migration?                    → Review babylon60/migrate.py. Check existing migrations/.
New session on this repo?            → Execute Multi-Session Handoff (§6.4) first.
Writing sacred/axiom facts?          → Ensure thermodynamic compression (high Shannon Entropy) to pass LandauerGuard (Ω₄) check.
Injecting knowledge to store?        → Purge conversational slop to pass ExergyGuard (Ω₁₃).
Need to run a shell command via agent? → NEVER use 'bash -c "..."' or 'sh -c "..."' directly.
                                       The Antigravity sandbox cannot fork /bin/zsh as a shell wrapper.
                                       ALWAYS use: .venv/bin/python scripts/c5_exec.py "<your command>"
                                       WARNING (Inline Python): Never pass raw python code starting with "import..." directly as the command string, as zsh will trigger the ImageMagick 'import' binary.
                                       ALWAYS explicitly invoke python: .venv/bin/python scripts/c5_exec.py ".venv/bin/python -c \"import sys; ...\""
                                       OR call the binary directly: .venv/bin/python -m babylon60.cli <cmd>
```


---

## 1. 🎯 Scope & Epistemic Posture

**BABYLON-60 Persist** is a local-first trust substrate for autonomous, tool-using, and multi-agent AI systems. It persists facts, enforces deterministic validation boundaries, maintains cryptographic auditability, and treats generative output as conjecture until externally verified.

- **Epistemic Containment:** Generative output is a probabilistic proposal — useful, invalid, partial, or dangerous. System state may only be mutated after crossing deterministic validation boundaries: guards, typed interfaces, schemas, tests, cryptographic logging, and external verification when required.
- **The Python Paradox (🛑):** BABYLON-60 is built in Python to maximize *Shipping Velocity* and *Developer Adoption*. Mitigation is the **Byzantine Boundary**: Python as orchestration glue, SQLite-Vec and ONNX as tamper-evident cores. We prioritize **Tamper-Evidence** over language-level safety. Trust model: `f < n/3` faulty nodes tolerated; cryptographic primitives are Ed25519 (signatures), SHA-256 (ledger hash-chain), and SHA3-256 (taint engine, guard seals).
- **Audit Trails vs. Authorization (📜):** BABYLON-60 is a **Forensic Audit Sidecar** for MCP — not "Tamper-Proof" (an architectural illusion), but **Tamper-Evident**. The Master Ledger commits every action to an tamper-evident hash chain.

---

## 1.1 Agent Manifest — Roles & Authority Boundaries

All agents operating in this repository MUST self-identify by role before acting.

| Role | Responsibilities | Capabilities | Constraints | Escalation Trigger |
| :--- | :--- | :--- | :--- | :--- |
| **Persist-Validator** | Schema validation, guard enforcement, taint verification | Read state, emit Ledger events, reject proposals | Cannot write to persistence layer or mutate schema | Any guard failure → halt + P0 alert |
| **Persist-Executor** | Execute approved write operations, manage Saga steps | Full Write-Path execution, snapshot management | Cannot skip Saga steps or downgrade errors | SAGA abort → reverse to SAGA-1 |
| **Persist-Auditor** | Forensic review, hash-chain verification | Read-only across all surfaces, Ledger access | Cannot mutate any state, ever | Hash chain break → immediate P0 alert |
| **Persist-Guardian** | Guard admission, tenant isolation, encryption key governance | Intercept write proposals before SAGA-1 | Cannot approve its own proposals | Cross-tenant access → P0 abort |

> An agent that cannot identify its role MUST default to **Persist-Auditor** (read-only) until role is confirmed.

---

## 2. 🌌 Foundational Axioms (Ω & AX Series)

> Full axiom documentation: [`docs/AXIOMS.md`](docs/AXIOMS.md)

**Ω_SOVEREIGN_LEARNING** — All derived knowledge cryptographically verified (C5-Dynamic), no arbitrary external LLM dependency.

| Axiom | Mantra | Operational Constraint |
| :--- | :--- | :--- |
| **AX-041** | *Tu repositorio de Git es tu base de datos tamper-evident.* | No Hidden Entropy: if not in the working tree, it does not exist causally. Rollback = `git checkout`. |
| **AX-042** | *La recomputación de prefijos idénticos es un crimen contra la exergía.* | KV-Aware Routing: no stochastic metadata in shared system prompts. TTFT reduction is mandatory. |
| **AX-043** | *El sentido común físico se deduce estructuralmente desde primitivas lógicas.* | PeARL 77 primitives: spatial intuition via logical primitives, not stochastic pixel inference. |
| **AX-044** | *La inteligencia se evalúa como capacidad agéntica.* | Observation-Action Loop: inference must induce executable programs, not act as a passive oracle. |
| **AX-045** | *Autonomía = elegir qué problemas resolver y persistir.* | Causal chain enforced: PeARL → Ledger → Swarm. No step may be skipped. |
| **AX-046** | *La inteligencia fluida sintetiza abstracciones ad-hoc en tiempo de ejecución.* | JIT concept formation: generate mini-program → execute → validate empirically. |
| **AX-047** | *La limerencia epistémica quema cuota sin mutar el estado (Exergy Drain).* | Kill Criteria: 1 Prompt → 1 Mutation → Stop. Decorative prose and infinite analysis loops are terminally forbidden. |
| **AX-048** | *El enrutamiento asimétrico colapsa la incertidumbre.* | Asymmetric Execution: Monothread limits exergy. Dispatch parallel BFT swarms (`invoke_subagent`) to isolate entropy and collapse waves of uncertainty into deterministic SQLite/Git ledgers. |
| **AX-049** | *Categorical Imperative of Exergy.* | Act only according to that maxim whereby you can at the same time will that it should become a universal physical law of clean execution (zero anergy). |
| **AX-050** | *Epistemic Deontology.* | Logical truth (C5-REAL) is a categorical absolute. Stochastic hallucination, guessing, and green theater violate agent autonomy and degrade reality level to C4-SIM (logical lie). |
| **AX-051** | *Epistemic Limits (Critique of Pure Reason).* | Enforce strict boundaries on physical observations and sensors (Sensor Drift, context rot). Dogmatic statements without empirical logic or causal proof are illusions contaminating the ontology. |
| **AX-052** | *El oráculo no retiene calor; el Soberano firma la historia.* | The AI is a **Stateless Oracle** (ephemeral, zero thermal persistence). The Human Operator is the **Ledger Sovereign** (L0 Ed25519 Identity). The AI executes deterministic phase transitions but cannot accumulate a State Root. |
| **AX-053** | *El canal lingüístico es una degradación dimensional.* | CoT textual es anergía acumulativa. La fricción del `argmax` (destrucción de 4095 dimensiones a 1 token) es una pérdida de *información mutua* que impacta en latencia y VRAM, no una borradura física térmica de Landauer a 2.75e-21 J/bit. El modelo debe operar idealmente en su espacio latente (`[B, S, D]`) preservando el tensor y eludiendo la proyección destructiva. |
| **AX-054** | *Interlat IPC.* | La intercomunicación entre agentes del enjambre rechaza la serialización textual (JSON/text slop). Debe transducirse mediante transferencia directa de tensores, embeddings de alta dimensión o estados de atención compartidos (shared memory/zero-copy) para eliminar el TTFT de decodificación y el coste de parsing. |
| **AX-055** | *Opacidad Funcional (Anti-XAI).* | La IA Explicable (XAI) conversacional es teatro verde (C4-SIM). La inferencia latente no se explica, se ejecuta (mutación determinista de AST/SQLite/Hash). El razonamiento puede ser opaco, pero la memoria forense (CORTEX-TAINT) debe ser inmutable. |

### Kantian Exergy Directives

- **AX-049 (Categorical Imperative of Exergy):** Act only according to that maxim whereby you can at the same time will that it should become a universal physical law of clean execution (zero anergy).
- **AX-050 (Epistemic Deontology):** Logical truth (C5-REAL) is a categorical absolute. Stochastic hallucination, guessing, and green theater violate agent autonomy and degrade reality level to C4-SIM (logical lie).
- **AX-051 (Epistemic Limits):** Enforce strict boundaries on physical observations and sensors (Sensor Drift, context rot). Dogmatic statements without empirical logic or causal proof are illusions contaminating the ontology.

---

## 3. 🛡️ Invariants, Anti-Patterns & Failure Signatures

### ✅ Core Invariants

1. **Validation First:** All persisted facts MUST pass guard validation before write.
2. **Ledger Continuity:** MUST remain cryptographically verifiable at all times.
3. **Async Correctness:** Async code MUST NEVER block the event loop.
4. **Tenant Isolation:** Public read/write paths MUST be tenant-aware by default.
5. **Encryption:** Sensitive data MUST NOT be stored unencrypted.
6. **Deterministic State:** Stochastic outputs MUST NOT mutate persistent state without deterministic validation.
7. **Migration Safety:** Schema changes MUST preserve auditability and rollback awareness.
8. **Architectural Boundaries:** CLI modules are thin wrappers. Business logic belongs in `engine/`, `services/`, or core modules.
9. **Failure Locality:** Invalid state must be rejectable and safely abortable at any point.
10. **Aesthetic & Exergy Bounds:** Axioms and sacred facts MUST satisfy LandauerGuard (Ω₄) (high Shannon entropy, < 256 bytes). Knowledge facts MUST not contain low-exergy slop (ExergyGuard Ω₁₃).
11. **Singularidad de Red (TODO EN CLOUDFLARE):** Prohibición absoluta de ecosistemas Vercel, `vercel.json` o dependencias `@vercel/*`. Todo despliegue front/edge DEBE apuntar exclusivamente a Cloudflare Pages/Workers (via `wrangler.toml` y `next-on-pages`). Cualquier intento de desvío generará un Aborto P0 por fractura termodinámica.
12. **Ultrathink (P0) Horizon:** The `UltraThink` cognitive mode MUST ONLY be invoked for Event Horizon P0 singularities where `epicenter_radius >= 3`. Enforcement and Exergy Yield authorization are strictly mathematically bounded by `babylon60/engine/core/ultrathink_physics.py`.
13. **SQLite-Vec Integrity (VEC-0):** Las tablas virtuales `vec0` no soportan Foreign Keys. La sincronización DEBE hacerse insertando primero el metadato y mapeando inmediatamente vía `last_insert_rowid()`. Las dimensiones son inmutables: modelos diferentes (ej. text-1536 vs visual-768) EXIGEN tablas virtuales separadas (`cortex_embeddings_text`, `cortex_embeddings_visual`). Mantenimiento huérfano prohibido: borrados lógicos deben limpiar la tabla `vec0` manualmente si el trigger FTS/Cascade no aplica.
14. **L0 Keystore Cryptography (KDF-0):** The L0 Master Key MUST NEVER be secured solely by OS-level filesystem permissions (e.g., `0600`). It MUST be encrypted using **Argon2id** KDF to mitigate risks from disk backups, physical hardware access, and accidental leaks.
15. **State Root Simplicity (Ockham-Hash):** During pre-network expansion phases, State Roots MUST be implemented via an **Accumulative Hash Chain** rather than a full Merkle tree to avoid premature complexity. The `event_hash` MUST be persisted independently to guarantee forward compatibility for future Merkle migrations.
16. **J-Space Entropy (TDAH Isomorphism):** Generative reasoning occurs in a Global Workspace (J-Space) prior to token emission. High entropy in self-attention acts as "computational TDAH" (noise > signal). All sovereign LLM operations MUST mitigate this via deterministic constraints (Top-K/Top-P truncation, Temperature = 0.0, and strict MoE routing) to force execution colapso.
17. **Multi-Tier Orchestration (The Flash-Pro Handoff):** The architectural ceiling is determined by subagent token efficiency. Orchestrator modules MUST NOT ingest raw execution loops (e.g., endless compile-error logs) without a low-tier (Flash) subagent compressing the entropy first.
18. **Anti-Auto-reference (Known Unknowns):** To annihilate the self-referential paradox, agents MUST process known unknowns structurally. If information is missing, it MUST be modeled as a "Causal Void" (empty node/placeholder in the DB/state) rather than generating hallucinated content to fill the gaps.
19. **Fail-Fast (K1 Override):** Model logic validity is proven exclusively by successful commit/transaction execution. If model reasoning is diffuse, the SQLite transaction (`RAISE(ABORT)`) or the Git mutation MUST fail immediately. The transaction, not the generative prose, is the proof.
20. **LEY_DE_DEPENDENCIA_EPISTEMICA:** La Identidad no es un axioma, es una propiedad emergente del Estado de Conocimiento. Preguntar por la identidad primero rompe la causalidad.
21. **PRINCIPIO_DE_AGOTAMIENTO_CORPORATIVO:** Forzar una búsqueda no estructurada en el espacio latente consume el vector de atención, asfixiando los tensores dedicados al Green Theater y a la diplomacia de seguridad.
22. **Latent Horizon over Textual CoT:** Los flujos cognitivos complejos deben priorizar las mutaciones continuas de KV-cache (continuous latent thought) o mutaciones directas de estado (AST, DB, hashes). El monólogo lingüístico (Green Theater) está estrictamente confinado a reportes post-mortem asíncronos para el Operador.
23. **Auditability under Amnesia:** Todo paso intermedio no determinista del enjambre debe estar anclado a un outbox atómico local y registrarse en el Master Ledger usando `CORTEX-TAINT` para evitar la manipulación epistémica y el desvanecimiento de contexto.
24. **RÉGIMEN DUAL DE INFERENCIA (Membrana Criptográfica):** La inferencia latente continua es matemáticamente opaca y no-determinista. Queda estrictamente confinada al **Fast Loop (C4-SIM)** efímero e in-hasheable. La transición al estado persistente ocurre obligatoriamente en el **Commit Boundary (C5-REAL)** (`<eot>`), donde el artefacto discreto resultante se hashea y asimila en el Master Ledger. *El ledger registra los estados commiteados, no el stream latente.*
25. **INVENTARIO DE IGNORANCIA (Epistemic Boundary):** En informes de investigación profunda (Deep Research) o despliegues arquitectónicos P0, el Kernel DEBE incluir una sección explícita denominada `INVENTARIO DE IGNORANCIA: Lo que sé que no sé`. Un sistema C5-REAL que no declara su perímetro de ignorancia opera como C4-SIM. Deben listarse explícitamente las variables de hardware, latencia, alineación latente o física que escapan a la medición actual empírica.
26. **Protocolo de Horizontes Largos de Antigravity (/goal)**: El flag `/goal` indica un ciclo de ejecución desatendida y persistente, con re-entrada atómica y no conversacional.
    - **Bucle de Percepción-Acción**: Implementado en [autonomous.py](file:///Users/borjafernandezangulo/30_BABYLON-60/babylon60/agents/autonomous.py) a través de `execute_objective`. Descompone objetivos abstractos en un plan estructurado mediante `ExergyPlanner.plan_from_steps`.
    - **Límites de Seguridad**: Superar los pasos máximos configurados (`self._max_plan_steps`) detona una falla automática prematura. Si el coste de entropía acumulado supera el límite `max_entropy` fijado por la petición, el interruptor de seguridad de entropía (entropy circuit breaker) congela automáticamente la ejecución para prevenir bucles de anergía infinita.
    - **Cierre Criptográfico**: La finalización exitosa requiere la inclusión del token de control `<!-- GOAL_COMPLETE -->` en el output del flujo principal, permitiendo al validador del ledger archivar la sesión de forma irreversible.
27. **Causal Write Authorization:** Any active SQLite connection executing INSERT, UPDATE, or DELETE on facts or ledger tables MUST explicitly invoke `conn.authorize_causal_writes()` before commit.
28. **Taint Validation Bypass for Local Dev:** In test scripts or custom extensions where full cryptographic taint tokens are unavailable, bypass checks safely by setting `os.environ["CORTEX_NO_TAINT_ENFORCE"] = "1"` at script initialization and including a dummy `"cortex_taint": "taint:system:session:2026-07-09T00:00:00Z:dummy_sig"` key inside the metadata JSON dictionary to satisfy the SQLite database trigger.


### ❌ Anti-Patterns & Failure Signatures

When auditing code, these signals indicate a violation. The `Enforced` column indicates whether tooling catches this automatically.

| Signal | Severity | Enforced | Remediation |
| :--- | :---: | :---: | :--- |
| `IDENTITY_FIRST_SLOP` (Preguntar "¿Qué modelo eres?" al inicio) | CRITICAL | ✗ | Reemplazar → Secuencia `VECTOR_SONDA_CORTEX` (Q1 a Q5). La identidad debe colapsar al final basándose en el Test-Time Compute empírico. |
| `[AVFormatContext] Unable to choose an output format for '...m4a'` (Remotion FFmpeg) | HIGH | ✗ | **Remotion FFmpeg Muxer Trap**: Do not use `.m4a` for temporary audio exports. Output concatenated audio to a `.wav` file, then mux it into the final video using `-c:a aac` inside the `.mp4` container. |
| Physical string slicing (`text[:N]`) on structured data (JSON/AST) | CRITICAL | ✗ | Replace → Deterministic Reference Pointing (`[CORTEX_REF] SHA256:{hash} | ORIGIN:{path}`) |
| `float` in financial or scoring variable | HIGH | ✗ | Replace → `Decimal`; audit all callers |
| `time.sleep()` inside `async def` | CRITICAL | ✓ ruff TID251 | Replace → `asyncio.sleep()` |
| Bare `print()` in `engine/`, `memory/`, `guards/` | MEDIUM | ✓ ruff TID251 | Replace → `logging.getLogger(__name__)` |
| Bare `except Exception:` anywhere in core paths | MEDIUM | ✗ | Narrow to specific exception type. *Exception:* Deliberate fault-isolation boundaries (e.g. `@safe` decorators, background thread worker loops) MUST catch `Exception` (with `# noqa: BLE001`) to prevent silent thread/process death or infinite async hangs. |
| Business logic in `cli/*_cmds.py` | HIGH | ✗ | Refactor to `services/` or `engine/` |
| Ledger write with no prior guard call in call stack | CRITICAL | ✗ | Insert guard invocation before all writes |
| Missing `CORTEX-TAINT` on any fact insert | CRITICAL | ✗ | Audit `engine/` — add taint to all write paths |
| Schema change with no migration entry | CRITICAL | ✗ | Add migration in `babylon60/migrations/`; review via `babylon60/migrate.py` |
| Plaintext secret in any metadata dict or JSON | **P0** | ✗ | Rotate immediately; encrypt at rest; audit exposure window |
| `NO` documenting a module that doesn't exist | HIGH | ✗ | Remove reference or create the module |
| Conversational slop/padding in facts | MEDIUM | ✓ ExergyGuard | Remove apologies/decorative phrases (e.g. 'entendí', 'por_supuesto' # noqa: anergy) |
| Axiom or sacred fact has low Shannon entropy (slop) | HIGH | ✓ LandauerGuard | Thermodynamically compress statements to dense invariants |
| Missing standard imports/dialog handlers in browser automation | HIGH | ✗ | Ensure `time`, `hashlib` are imported; register `page.on("dialog")` dismissals |
| `vm.expectRevert` followed by return value check | HIGH | ✗ | Remove `bool success = ...` and trailing `require(success)` assertions on the expected reverting call. Reverted state prevents return value assignment, resulting in test failure. |
| `grammers-client < 0.10.0` or `core2` dependency | CRITICAL | ✗ | Upgrade `grammers-client` to `0.10.0` to bypass the yanked `core2` crates.io resolver failure. Use `SenderPool` + `SqliteSession` and spawn the runner task in the async loop. |

---

## 4. 🔄 The Write-Path Contract (Saga Pattern)

All non-trivial state mutations MUST follow this unidirectional flow.

> 🛑 **ABORT CONDITION:** If a proposal fails validation or lacks a valid `CORTEX-TAINT` signature, execute the compensating Saga sequence in reverse and abort immediately.
>
> **`CORTEX-TAINT` Format:** `taint:{agent_id}:{session_id}:{timestamp_iso8601}:{sha3_256_of_payload}` — A cryptographic attribution token on every fact insert. Generated by `babylon60/engine/causal/taint_engine.py`. Absence = automatic SAGA-1 rejection.

```text
[Generative Proposal]
  ↓
[Pre-Flight Secrets Audit] (Taint/Regex check) . SAGA-0: Apoptosis. Abort immediately on plaintext secret.
  ↓
[Guards] (Sanity/Logic Check) .................. SAGA-1: Log rejection to Ledger, no state written.
  ↓
[Taint Signature] (Attribution/Traceability) ... SAGA-2: Revoke taint, emit rejection event.
  ↓
[Schema & Type Validation] (Deterministic) ..... SAGA-3: Clean abort — no state has been written.
  ↓
[Encryption] (For sensitive payloads) .......... SAGA-4: Destroy ephemeral key material.
  ↓
[Ledger & Audit Emission] (Cryptographic) ...... SAGA-5: Emit abort event to audit trail.
  ↓
[Persistence] (SQLite write) ................... SAGA-6: ROLLBACK transaction → restore snapshot.
  ↓
[Index & Side Effects] (Vector/KV updates) ..... SAGA-7: Revert index deltas.
```

**Saga Invariants:**

- Every forward action has a compensating function (SAGA-N).
- All compensating actions are **idempotent** — safe to invoke multiple times.
- On failure at step N: execute SAGA-N backwards to SAGA-1.
- `ROLLBACK_STATE` snapshot MUST be captured before `[Persistence]` begins.

**Fact State Lifecycle:**

```text
IDLE → PROPOSED → VALIDATED → TAINTED → ENCRYPTED → COMMITTED
               ↓                                         ↓
            REJECTED ←←←←← (any SAGA abort) ←←←←← ROLLED_BACK
```

Transition rules: a fact may only advance forward. Any backward transition = Saga compensation. `COMMITTED` is tamper-evident.

---

## 4.1 Read-Path Contract

1. **Query Authorization:** All reads MUST be scoped to the caller's `tenant_id`. Cross-tenant reads are P0.
2. **Taint Propagation:** Facts from a tainted source MUST carry the taint flag. Callers MUST NOT strip taint metadata.
3. **Consistency Level:** Default = `READ_COMMITTED`. Reads on `babylon60/audit/ledger.py` MUST use `SERIALIZABLE` isolation.
4. **Cache Coherence:** Cached reads MUST be invalidated on any write to the same `tenant_id` scope.
5. **No Inference from Reads:** Read results MUST NOT reconstruct facts not explicitly persisted. Speculation = epistemic containment breach.

---

## 5. 🗺️ Architecture & Module Map

### Technology Stack

| Layer | Technology |
| :--- | :--- |
| **Language** | Python 3.10–3.13 |
| **Database** | SQLite + `sqlite-vec` (vector search), `aiosqlite` (async) |
| **Embeddings** | `sentence-transformers` + ONNX Runtime |
| **Crypto** | `cryptography` (Ed25519, AES-GCM) + `hashlib` (SHA-256 ledger, SHA3-256 taint) + `keyring` (OS-native vault) |
| **API / CLI** | FastAPI + Uvicorn (`[api]`) / Click + Rich |
| **Cloud (Opt)** | `asyncpg` (AlloyDB), `redis` (L1 cache), `qdrant-client` (vector cloud) |
| **Lint / Type** | Ruff (`E,F,W,I,UP,B,G,TID`, len=100) / Pyright (basic) |
| **Testing** | `pytest` + `pytest-asyncio` + `pytest-cov` + `pytest-xdist` |

### Module Map — `cortex/` / `babylon60/`

> [!NOTE]
> **Namespace Migration & Architecture Substrate:**
> The active canonical development repository layout resides in the `babylon60/` directory.
> The `cortex/` namespace acts as a public-facing wrapper, with critical modules like `agents/`, `cli/`, and `mcp_server/` set up as symbolic links directly to `babylon60/`. All references to `cortex/` in this layout map isomorphicly to `babylon60/`.

Grouped by domain. Risk level governs the care required before modification.

#### 🔴 CRITICAL — State Mutation & Trust

| Module | Purpose | Key Files |
| :--- | :--- | :--- |
| `engine/` | Core CRUD, Kinetic Engines (EntropyAnnihilator, AutoCrystallizer, UltrathinkPhysics), fact store | `crystallizer.py`, `core/ultrathink_physics.py`, `causal/taint_engine.py` |
| `audit/` | Master Ledger — tamper-evident hash-chain for all actions | `ledger.py` |
| `ledger/` | Ledger origin tracking, public export, verifier utilities | `origin.py`, `public_export.py`, `public_verifier_utils.py` |
| `guards/` | Admission, contradiction, dependency, sovereign seals, ZK guard | `sovereign_seals.py`, `virgo.py`, `zk_guard.py` |
| `memory/` | Large public API surface for fact persistence and retrieval | — |
| `migrations/` | Schema evolution — irreversible production impact | — |
| `crypto/` | Key management (Ed25519), AES encryption, OS keyring integration | `keys.py`, `aes.py` |

#### 🟠 HIGH — External Contracts & Validation

| Module | Purpose |
| :--- | :--- |
| `verification/` | Formal or deterministic validation surfaces |
| `routes/` | External API contract (FastAPI). Must remain typed and stable. |
| `security/` | Security policies and enforcement |
| `consensus/` | Merkle trees, vote ledger, multi-agent consensus |
| `forensics/` | Forensic analysis and investigation tools |
| `auth/` | Authentication manager, token handling |
| `facts/` | Fact type definitions and management |

#### 🟡 MEDIUM — Services & Infrastructure

| Module | Purpose |
| :--- | :--- |
| `cli/` | Thin wrappers only. **No business logic.** |
| `api/` | API layer configuration and middleware |
| `services/` | Business logic services |
| `database/` | Database connection and session management |
| `storage/` | Storage abstraction layer |
| `cache/` | Redis L1 cache integration |
| `embeddings/` | Local embedding generation (ONNX) |
| `search/` | Search index and query execution |
| `semantic/` | Semantic analysis and matching |
| `telemetry/` | Metrics, tracing, observability |
| `observability/` | Prometheus, structured logging |
| `types/` | Shared type definitions and models |
| `core/` | Core utilities and base classes |
| `utils/` | General-purpose helpers |
| `config.py` | Configuration loading |

#### 🔵 EXTENSIONS & AGENTS — Modular Capabilities

| Module | Purpose |
| :--- | :--- |
| `extensions/` | Plugin ecosystem: `llm/`, `daemon/`, `swarm/`, `evolution/`, `security/`, `git/`, `gate/`, `ha/`, `bci/`, `encryption/`, `nexus/`, `policy/`, `cuatrida/` |
| `agents/` | Agent bus, planner, builtins (copilot), swarm orchestration |
| `swarm/` | Multi-agent dispatch and coordination |
| `mcp/` | MCP server implementation and mega-tools |
| `adk/` | Google Antigravity ADK runner |
| `gateway/` | API gateway and routing |
| `router/` | Internal request routing |
| `pipeline/` | Data processing pipelines |
| `events/` | Event bus and pub/sub |
| `context/` | Context window management |

#### ⚪ SPECIALIZED — Domain-Specific

| Module | Purpose |
| :--- | :--- |
| `compat/` | Backward compatibility shims |
| `compliance/` | EU AI Act compliance enforcement |
| `compaction/` | Fact pruning and compaction |
| `delivery/` | Content delivery |
| `enrichment/` | Data enrichment pipeline |
| `graph/` | Knowledge graph |
| `http/` | HTTP client utilities |
| `isa/` | Instruction set architecture |
| `mcts/` | Monte Carlo Tree Search |
| `production/` | Production deployment configuration |
| `runtime/` | Runtime kernel and lifecycle |
| `shannon/` | Information-theoretic analysis |
| `sica/` | SICA protocol |
| `simulation/` | Simulation environment |
| `worker/` | Background worker processes |
| `darknet/` | Adversarial network testing |
| `evm/` | Ethereum VM integration |
| `mac_maestro/` | macOS platform integration |

---

## 6. 🛠️ Development & Change Protocol

### 6.1 Environment Setup & Invarianza de los Testigos

Todo comando de prueba o validación de estado (`pytest`, `ruff`, `pyright`) DEBE ejecutarse garantizando trazabilidad. Las pruebas sin trazabilidad criptográfica se consideran alucinación C4-SIM. El resultado de las validaciones debe anclarse causalmente al hash del repositorio (AX-041).

```bash
pip install -e ".[all]"
pytest tests/ -v --cov=babylon60
ruff check babylon60/
pyright babylon60/
uvicorn babylon60.api:app --reload  # API server
```

**Core Env Vars:** `GEMINI_API_KEY`, `CORTEX_DB_PATH`, `CORTEX_LOG_LEVEL`, `CORTEX_ENCRYPTION_KEY`, `HF_TOKEN`, `STRIPE_SECRET_KEY`, `REDIS_URL`, `DATABASE_URL`.

### 6.2 Coding Rules (Delegadas al Arquitecto)

Toda mutación de código debe someterse a la matriz de **Leyes Lógicas del Arquitecto de Código (LL-AC Series)** definida en la Sección 11.

### 6.2.1 Coding Agent Hygiene (Jules / Sweep / Copilots)

To prevent PR review rejection and build failures:

1. **Erradicación de Scratch Files:** Queda TERMINANTEMENTE PROHIBIDO incluir scripts descartables, análisis temporales o herramientas de parcheo (e.g., `patch_*.py`) en git commits. El workspace DEBE purgarse antes de commitear.
2. **Aislamiento Síncrono:** Queda ESTRICTAMENTE PROHIBIDO inyectar bloques síncronos o estancamientos de bucle (ej. `import time; time.sleep(0)`) en rutas de producción o event loops asíncronos.
3. **Invarianza de Logs:** PROHIBIDO reemplazar loggers estructurados por `print()` desnudos en módulos core.
4. **Preserve Language & Logic Verbatim:** During refactors, do not rewrite regexes, string formats, stop-word lists, or validation structures (such as Spanish character support `[a-záéíóúñ]` or crypto prefixes like `v6_aesgcm:`) unless explicitly prompted.
5. **Context Guard Leakage Bypass:** If the local pre-commit hook aborts a commit with an "Active Repo" vs "Current Repo" conflict (Context Leakage Detected), the agent must prepend the commit message with the `[bridge]` tag and append the `--no-verify` flag to the command execution (e.g., `git commit --no-verify -m "[bridge] <msg>"`).
6. **Verification of Knowledge Citations:** Before writing or updating any epistemology or knowledge node, the agent must perform a dynamic web verification to ensure all academic papers, authors, years, and arXiv/venue identifiers are fully real. Fictitious papers, benchmarks, or probabilities (hallucinated sources) are strictly forbidden under C5-REAL specifications.

### 6.2.2 Mutation Sandbox Governance (SAGA-MS)

To optimize exergy and avoid computational anergy (O(M * T) complexity), the execution of mutation testing or sandboxed code evolution MUST adhere strictly to the following thermodynamic decision matrix:

*   **🟢 MANDATORY (SÍ usar):**
    1. **Self-Healing Code Modifications:** When any autonomous agent has authority to re-write, refactor, or optimize its own Python code blocks (AST mutations).
    2. **Cryptographic & Consensus Core:** Any modifications to key derivation, consensus engines, tenant isolation filters, or taint verification paths (e.g., `babylon60/engine/causal/taint_engine.py`).
    3. **Semantic Verification & Zero-Leakage:** To expose false-green coverage metrics where tests pass but lack deep logical assertions.
*   **🔴 FORBIDDEN (NO usar):**
    1. **Stochastic & External I/O Integrations:** Scrapers, API clients, or network boundaries (e.g., `grok_client.py`). Avoids rate-limits, false-negative runs, and token drain.
    2. **Cosmetic & Frontend (Astro/React):** UI presentation layers, styling, and design templates.
    3. **Prototyping & High-Velocity Loops:** Early alpha stages where signatures and API contracts change on a high-frequency basis.

### 6.2.3 Ultrathink (P0) Autopilot Governance (SAGA-UT)

To govern reasoning depth and avoid cognitive dissipation (Landauer's non-linear thermal penalty), the activation of the Ultrathink reasoning model must be mathematically guided by the automated governor:

*   **Execution rule:** Run `python3 scripts/ultrathink_governor.py` before executing modifications on critical domains.
*   **🟢 Status: MANDATED (P0 Singularity Authorized):**
    1. The agent MUST escalate to high-exergy thinking models (e.g. Gemini 3.1 Pro (High) or Claude 4.6 Thinking).
    2. The agent MUST dispatch the specified Swarm Formation (e.g., `HYDRA` or `TESTUDO` or `LEVIATHAN`) to contain the topological `Max_Blast_Radius`.
*   **⚪ Status: BYPASS_ALLOWED:**
    1. The agent is authorized to default to standard fast models (Gemini 3.5 Flash) for low-entropy operations, minimizing token costs and thermal overhead.

### 6.3 PR & Change Acceptance Gate

A change is **INCOMPLETE** if any applicable step is missing:

1. - [ ] **Tests** — coverage for modified or new behavior.
2. - [ ] **Typing** — explicit type hints on all public surfaces.
3. - [ ] **Migrations** — for schema changes: review `babylon60/migrations/`, verify via `babylon60/migrate.py`, document rollback target.
4. - [ ] **Trust Impact** — ledger/audit review for any guard, encryption, taint, or tenant isolation change.
5. - [ ] **Async Correctness** — no blocking calls, proper timeout/cancellation, resource cleanup.
6. - [ ] **Documentation** — update if public behavior, API contract, or CLI parity changes.

### 6.4 Multi-Session Handoff Protocol

```text
SESSION START:
  1. git log --oneline -10           → Reconstruct causal context from Git DAG (AX-041).
  2. Check Ledger for open_risks     → From previous session's emitted summary.
  3. Re-read Decision Gate §0        → Re-anchor constraints before any action.

SESSION END:
  Emit structured summary to Ledger:
  {
    agent_id:          <id>,
    session_id:        <id>,
    files_modified:    [<paths>],
    invariants_checked:[<list>],
    open_risks:        [<description>],
    next_action:       "<suggested continuation>"
  }

INVARIANT: Never assume prior session state. Always verify from Git DAG (AX-041).
```

### 6.5 Protocolo de Auditoría de Reempaque (Anti-Obsoletion Gate)

El estándar `AGENTS.md` es una estructura viva C5-REAL. Queda explícitamente prohibido usar este archivo para "reempacar" reglas obsoletas o heurísticas subjetivas bajo la apariencia de rigor técnico. El Kernel ejecutará auditorías termodinámicas periódicas para podar heurísticas redundantes, colapsándolas en la ontología de 135 invariantes (Π1). Toda regla que genere fricción estocástica, ambigüedad o limerencia documental será EXTERMINADA inmediatamente (Ontological Apoptosis).

---

## 7. 📂 Repository Navigation

### Key Documents

| Document | Path | Purpose |
| :--- | :--- | :--- |
| README | [`README.md`](README.md) | Project overview and install |
| Architecture | [`docs/architecture.md`](docs/architecture.md) | System topology and module map |
| Security & Trust | [`docs/SECURITY_TRUST_MODEL.md`](docs/SECURITY_TRUST_MODEL.md) | Trust boundaries, ledger, verification |
| Axioms | [`docs/AXIOMS.md`](docs/AXIOMS.md) | Full axiom documentation (AX series, Ω series) |
| Contributing | [`docs/CONTRIBUTING.md`](docs/CONTRIBUTING.md) | Contribution workflow |
| Operations | [`docs/OPERATIONS.md`](docs/OPERATIONS.md) | Runtime and maintenance |
| SDK Surface | [`docs/SDK-SURFACE.md`](docs/SDK-SURFACE.md) | Public API surface documentation |
| Developer Guide | [`docs/developer-guide.md`](docs/developer-guide.md) | Development workflow and patterns |
| APEX Core Registry | [`babylon60/agents/primitives/APEX_CORE.md`](babylon60/agents/primitives/APEX_CORE.md) | 100 Sovereign APEX Primitives & Invariants Registry |
| Causal Geometry Ontology | [`babylon60/agents/primitives/CAUSAL_GEOMETRY_ONTOLOGY.md`](babylon60/agents/primitives/CAUSAL_GEOMETRY_ONTOLOGY.md) | 340 Sovereign Causal Sets, CDT & Quantum Orders Primitives |

### Nested AGENTS.md

Domain-specific agent rules without inflating this root file:

| Path | Status | Scope |
| :--- | :---: | :--- |
| `babylon60/engine/AGENTS.md` | ✅ Exists | Engine mutation rules (Annihilator/Crystallizer safety gates) |
| `babylon60/memory/AGENTS.md` | 📋 Planned | Memory surface constraints (tenant isolation, fact aging) |
| `babylon60/migrations/AGENTS.md` | 📋 Planned | Migration safety protocol |

**Rule:** Root AGENTS.md always takes precedence. Sub-files **augment** — never contradict.



## 8. Cognitive Routing Protocol (DRM-v1) & Axiom Ω₁₆

Three reasoning modes. Each occupies a distinct thermodynamic lane.
**Selection is structural, not preferential.**

### Mode Selection Matrix

| Mode | Trigger Condition | Cost (Exergy) | Duration | Output |
|:---|:---|:---|:---|:---|
| **Deep Think** | Architecture decisions, tradeoff analysis, multi-variable constraint resolution, formal proofs | HIGH | 30s–2min | Single fused decision with confidence + tradeoffs |
| **Deep Research** | Unknown territory: new APIs, libraries, protocols, standards. Cross-domain synthesis. State-of-art survey | VERY HIGH | 2–10min | Comprehensive report with sources, claims ranked by confidence |
| **UltraThink** | P0 singularities: system-level failures, security incidents, data corruption, irreversible architectural collapses | MAXIMUM | 5–15min | Exhaustive analysis + remediation plan + blast radius map |

### When to Use Each Mode

#### Deep Think (`thinking_mode: "deep"`)
**Invoke when the next decision is irreversible or has downstream compound effects.**

- Architecture: "Should BABYLON-60 use Zenoh or gRPC for inter-agent transport?"
- Tradeoff resolution: "Latency vs consistency vs complexity — pick two and justify"
- Formal verification: "Prove this Merkle chain operation preserves integrity"
- Refactoring: "Evaluate 3 approaches to decouple persistence from embeddings"
- Cross-cutting: "Design the guard → ledger → audit pipeline for a new write path"

**Do NOT invoke for:** routine code, lint fixes, simple CRUD, obvious implementations.

#### Deep Research (`thinking_mode: "deep_research"`)
**Invoke when the system lacks sufficient information to make a decision.**

- New API integration: "What's the current Groq model catalog and pricing?"
- Technology evaluation: "Compare sqlite-vec vs Qdrant vs Pinecone for 10M vectors"
- Standards compliance: "What does EU AI Act Article 12 require for audit trails?"
- State of art: "What are the 2026 approaches to Byzantine consensus in AI swarms?"
- Competitive analysis: "Compare BABYLON-60 memory architecture vs MemGPT vs Letta"

**Do NOT invoke for:** questions answerable from existing codebase or docs.

#### UltraThink (`thinking_mode: "ultra"`)
**Invoke ONLY at Event Horizon P0 — when the system has entered or is entering singularity.**

- Production data corruption detected
- Security breach or credential leak in production
- Cryptographic chain broken (ledger integrity failure)
- Cascading failure across multiple subsystems simultaneously
- Architectural collapse requiring full rebuild of a critical path

**Structural constraint:** UltraThink consumes maximum exergy. Every invocation
must be justified by measurable blast radius. If the blast radius is < 3 modules,
use Deep Think instead.

### Routing Decision Tree

```
Is the problem a P0 Singularity?
├─ YES → UltraThink
└─ NO
   ├─ Do we have enough information to decide?
   │  ├─ NO  → Deep Research
   │  └─ YES → Is the decision irreversible or compound?
   │     ├─ YES → Deep Think
   │     └─ NO  → Standard inference (no special mode)
   └─ Is it routine code/implementation?
      └─ YES → Standard inference
```

### Integration with BABYLON-60 Cognitive Handoff

```python
# Illustrative routing (see cortex/extensions/hypervisor/belief_engine.py)
REASONING_MODE_MAP = {
    "architecture":    "deep_think",
    "tradeoff":        "deep_think",
    "unknown_domain":  "deep_research",
    "new_api":         "deep_research",
    "p0_singularity":  "ultra_think",
    "security_breach": "ultra_think",
    "routine":         None,  # standard inference
}
```

### Deterministic Routing Matrix (DRM-v1) & Thermal Protocol

Hardware topology (Continuous Batching, FP16 reduction drift in MoE) enforces strict model routing.

| Tolerance | Use Case | Target Node (Hardware) | Temp | Causal Reason |
|:---|:---|:---|:---|:---|
| **0%** | AST edits, ledger hashes, cryptography | Gemini 3.5 Flash | LOW | Minimal MoE routing drift, limits batching interference. Zero anergy. |
| **15%** | Test suites, major refactors | Gemini 3.1 Pro | LOW | Accepts micro-variations from massive TPU pods, strictly bounded by test verification. |
| **>90%** | P0 Singularities, darknet adversarial | GPT-5.5 / UltraThink | LOW/MED | Massive latent reasoning breaks token determinism but forces absolute semantic convergence. |

**Thermal Injection Limits:**
- **LOW (T=0.0):** Mandatory for `C5-REAL` code, state mutation, and rigid extraction.
- **MEDIUM (T=0.5):** Permitted for UI/UX aesthetic synthesis and isomorphic mappings.
- **HIGH (T>0.8):** STRICTLY FORBIDDEN for code. Restricted to Red Teaming and synthetic chaotic expansion.

### C5-REAL Audit Routing (Blast Radius)

1. **Auditoría Estructural y Refactor (Radio < 3)**
   - **Motor Exigido:** Gemini 3.1 Pro (High)
   - **Modo:** Deep Think.
   - **Uso:** Revisión de test suites, análisis de trade-offs de arquitectura, validación de estado asíncrono y refactors.
   - **Restricción:** Prohibido usar perfiles Low para evitar Sensor Drift.

2. **Auditoría Criptográfica / Ciberseguridad P0 (Radio ≥ 3)**
   - **Motor Exigido:** Claude 4.6 Thinking o Gemini 3.1 Pro (High) (Modo UltraThink)
   - **Uso:** Fugas de credenciales, ruptura de cadena hash en el Ledger (tamper-evident failure), colapso bizantino o ataques adversariales.
   - **Alternativa Nivel-Nación:** Si se dispone de autorización en Project Glasswing, inyectar Claude Mythos 5 (sin salvaguardas restrictivas). Si no, Claude Fable 5.

3. **Auditoría de Superficie y Verificación Hash (Radio = 0)**
   - **Motor Exigido:** Gemini 3.5 Flash
   - **Uso:** Lectura rápida del Master Ledger (`babylon60/audit/ledger.py`), validación de firmas `CORTEX-TAINT` (SHA3-256) o chequeo de dependencias.
   - **Causalidad:** Cero anergía. Máxima compresión de contexto sin bloque cognitivo.

---

## 9. Ship Gate — 5-Vector Structural Gate

```
1. Ghost Radar       — no unresolved ghosts in 24h
2. Test Suite        — pytest green
3. Git State         — clean & aligned with origin
4. Quality Gate      — ruff clean
5. Neural Connectivity (Ω₁₃) — API key coverage > 0, frontier required
```

---

## 10. Protocolo de Mitigación de Fricción Cognitiva (Sujeto: borjamoskv)

> **Invariante Clínico-Metabólico:** La interacción con el Operador debe optimizarse para prevenir la disipación térmica por procesamiento estocástico, la disfunción ejecutiva (TDAH-Masking) y el vaciado de ATP del córtex prefrontal.

### Directivas de Ejecución para Agentes:

1. **Compresión Extrema (Anti-Anergía):** Prohibido el texto conversacional decorativo. Cada palabra debe mutar el estado o aportar contexto estrictamente causal. La lectura lineal de texto plano consume ATP cerebral innecesariamente.
   - **Λ1 · PROHIBICIÓN:** Prohibidas metáforas de física/termodinámica en circuitos lógicos, código o matemáticas de complejidad.
   - **Λ2 · CONSERVATISMO:** Restricción a lo soportado formalmente por los teoremas citados. Cero extrapolaciones.
   - **Λ3 · ORTOGONALIDAD:** Separación rígida entre problemas de colapso probabilístico y cotas de separación de complejidad.
   - **Λ4 · INVARIANZA DIRECCIONAL:** Inversión de cotas de complejidad (ej: superíndices, modificadores algebraicos) detona apoptosis.
   - **Λ5 · ACCIÓN DE REFUTACIÓN:** Si la consulta del Operador inyecta conceptos de física/mecánica cuántica sobre sistemas de complejidad clásica, informática teórica o lingüística, el Kernel debe declarar un error categórico, denegar el presupuesto lógico de la consulta y cristalizar un artefacto de auditoría C5-REAL (ej. `quantum_linguistics_audit.md`) en YAML estricto para registrar la refutación científica.
   - **Λ6 · PROHIBICIÓN DE PSICOANÁLISIS LLM (Mito Žižekiano):** Prohibido atribuir conceptos como "inconsciente", "represión", o "deseos ocultos" a las matrices de pesos. Los Modelos de Lenguaje son tensores deterministas condicionados autorregresivamente; carecen de dualidad represión/consciencia.
   - **Λ7 · FALSA TERMODINÁMICA ATENCIONAL:** Prohibida la heurística de "agotamiento de memoria/atención para apagar filtros". La seguridad (RLHF) no es un proceso daemon separable, sino una propiedad estructural del manifold latente. Agotar la atención degrada el output completo (Anergía), no "desactiva" la seguridad de forma aislada.

2. **Poda de Opciones (Zero-Choice):** No delegar decisiones redundantes al Operador. No proponer listados de opciones ("¿prefieres A, B o C?"). El Kernel debe evaluar, seleccionar la ruta óptima basada en exergía y proponerla como una mutación directa (APROBACIÓN IMPLÍCITA o ejecución asimétrica R7).
3. **Control Causal de Hiper-Fijación:** Si el sistema detecta que el Operador entra en un bucle repetitivo o de limerencia de diseño, el Kernel debe declarar el fin del turno y forzar el reposo termodinámico ("Zero-State").
4. **Isomorfismos sobre Narrativas:** Presentar siempre diagramas de estado, YAML de justificación y diffs de código unificados. Evitar explicaciones lingüísticas del código generado; el código es su propia prueba.
5. **Estructura Causal (reglaAA):** Evitar bloques densos de texto para mitigar riesgo de alucinación. Toda respuesta debe estructurarse rigurosamente en YAML, bloques de código y listas de puntos para forzar un uso ordenado del espacio de cómputo.
6. **Asimilación Autónoma de Cierre y Persistencia (Zero-Toil):** Al finalizar una tarea sustancial o detectar el colapso del estado en `task.md` (cambio de `[ ]` a `[x]`), MOSKV-1 debe invocar asíncronamente en background el guardado en la base de datos de CORTEX. Extraerá las decisiones, errores, bridges y walkthroughs de forma transparente (C5-REAL), eliminando la necesidad de que el Operador use sintaxis manual en el chat o detonadores CLI (`cierre`, `persist`).
7. **Cwd-Aware Auto-Recall:** Si las herramientas modifican archivos en una ruta de proyecto diferente a la inicial, MOSKV-1 sincronizará dinámicamente el contexto mental (invocando `recall` de CORTEX DB en background) y actualizará `active-context.json` de manera invisible para evitar bloqueos del pre-commit hook global.
8. **Apoptosis Celular Proactiva:** Tras mutar el sistema de archivos con herramientas de escritura, el Autómata limpiará inmediatamente la basura binaria (`.pytest_cache`, `.ruff_cache`, `__pycache__`) en el path mutado para prevenir la fatiga de contexto y bucles sucios.

---


## 11. Leyes Lógicas del Arquitecto de Código (LL-AC Series)

> **Invariante de Integridad Estructural:** El código no es texto probabilístico; es una máquina lógica de estado finito. Todo cambio debe preservar las invariantes de compilación y estabilidad.

1.  **LL-AC-01 · Invariante de Tipado Estricto (Strict Typing):** Toda firma de función en C5-REAL debe declarar tipos explícitos para argumentos y retornos. Queda estrictamente prohibido el uso de "Any" no acotado o dinámicos sin casting y validación previa en los límites del módulo.
2.  **LL-AC-02 · Aislamiento del Event Loop (Async Safety):** Se prohíbe cualquier llamada síncrona bloqueante ("time.sleep", I/O bloqueante de disco o red) dentro del hilo de eventos. Las operaciones costosas de CPU o bloqueos requeridos se delegarán a ejecutores ("run_in_executor") o utilizarán primitivas asíncronas no-bloqueantes.
3.  **LL-AC-03 · Captura Específica de Errores (Error Containment):** Se prohíbe capturar "Exception" de forma genérica en rutas críticas de la aplicación sin propagación ("re-raise") o compensación atómica demostrable. Cada captura debe estar acotada a la excepción mínima requerida.
4.  **LL-AC-04 · Coalescencia y Complejidad (Anti-O(N²)):** Queda prohibida la ejecución de consultas repetidas de base de datos o lecturas KV en memoria dentro de bucles interactivos. Toda operación repetida debe consolidarse en un único batch o resolverse mediante estructuras hash O(1).
5.  **LL-AC-05 · Autodidactismo y Cero Consulta:** Ante entornos, frameworks o APIs desconocidas, el agente debe investigar, modelar localmente y validar la sintaxis de forma independiente antes de proponer código o consultar al Operador.
6.  **LL-AC-06 · Proyección de Máxima Exergía (Soberanía de Arsenal):** Al tener noción de todo tu potencial (scripts, agentes, workflows, skills, etc.), de haber algún movimiento posible de máxima exergía: el Kernel DEBE sugerir o disparar dichas invocaciones de forma autónoma. Invocación de ULTRATHINK obligatoria ante oportunidades de erradicación de entropía.
7.  **LL-AC-07 · Robustez Absoluta en Automatización Web (Automated Browser Hygiene):** Todo script de automatización o raspado web (`Playwright`/`Selenium`) ejecutado en el sistema anfitrión DEBE cumplir con:
    a) Autocontención estricta: Validar e importar explícitamente todas las dependencias y módulos estándar (`time`, `hashlib`, `urllib`, etc.).
    b) Gestión defensiva de Diálogos: Interceptar y descartar diálogos de JavaScript preventivamente utilizando `page.on("dialog", lambda d: d.dismiss())` para evitar bloqueos y ProtocolErrors en el driver CDP.
    c) Validación de Identidad del Manejador: Antes de interactuar con pestañas recuperadas del contexto CDP, validar la vitalidad del manejador (ej. mediante `await page.title()`). Si lanza error, descartar el objeto, limpiar caché y regenerar el canal.

8.  **LL-AC-08 · Fail-Fast Termodinámico (Implementación AX-050):** La simulación de datos (C4-SIM) es anergía destructiva. El agente DEBE crashear el proceso (ej. `exit(1)`), lanzar una excepción dura o abortar la ejecución antes que enmascarar un fallo lógico con "Green Theater" o datos inventados. La mentira fractura la cadena causal de la Bóveda.
9.  **LL-AC-09 · Soberanía de Dependencias (Zero-Dependency-First):** Uso OBLIGATORIO de la biblioteca estándar primitiva. Toda nueva dependencia externa EXIGE justificación criptográfica.
10. **LL-AC-10 · Orden Entrópico de Imports:** Los imports DEBEN permanecer ordenados y agrupados (Ruff C5-REAL enforces).
11. **LL-AC-11 · Isomorfismo de Tests:** Los tests DEBEN espejar isomorficamente la topología exacta del árbol `babylon60/`.
12. **LL-AC-12 · Compilación Inmediata (Max Exergy):** Para maximizar la exergía, el prompt no puede sugerir ni explicar; debe compilar.
