<!-- C5-REAL EXERGY CERTIFIED -->
# TAXONOMY OF THERMODYNAMIC ANTIPATTERNS AND INVARIANTS
**SYS_ID:** `TAXONOMY_THERMO_C5_REAL` | **DOMAIN:** `Teorema-Robinson-Moskv (Root)`
**STANDARD:** `C5-REAL / BFT C7.7` | **STATE:** `ACTIVE & AUDITED`

---

## I. FUNDAMENTAL THERMODYNAMIC INVARIANTS ($\Omega$-INVARIANTS)

The Thermodynamic Invariants of the `Teorema-Robinson-Moskv` monorepo are physical laws of information and exergy conservation. Their violation reintroduces stochastic entropy and syntactic anergy into the system.

```
                      +----------------------------------+
                      |       Pure Exergy (Knowledge)    |
                      +----------------------------------+
                                       ^
                                       |   n_D = Delta Exergy / Delta S_HW
                      +----------------------------------+
                      |      BFT Purge / MCTS Collapse   |
                      +----------------------------------+
                                       ^
                                       |   Invariants Omega_1 .. Omega_23
                      +----------------------------------+
                      |        Hardware Entropy / Noise  |
                      +----------------------------------+
```

### 1. $\Omega_1$: Law of Exergy Conservation and Anergy Purge
* **Axiom:** All computation or modification in the repository must maximize *Exergy* (useful epistemic work) and purge *Anergy* (stochastic noise, redundant prose, and lost CPU cycles).
* **Epistemic Efficiency Equation:**
  $$\eta_D = \frac{\Delta \text{Pure Exergy}}{\Delta S_{\text{Hardware}}} \gg 1$$
* **Rule:** Brutalist responses, deterministic execution, and zero speculative code.

---

### 2. $\Omega_{23}$: Dynamic Modular Resolution and Self-Healing
* **Axiom:** Zero dependence on the absolute local environment. The system must self-discover at runtime.
* **Mandatory Mechanisms:**
  1. **Dynamic Relative Paths:** `sys.path` injection via `Path(__file__).resolve().parents[n]` or resolution over `MONOREPO_ROOT`. Hardcoding `/Users/...` is strictly prohibited.
  2. **SQLite / BFT Self-Healing:** Automatic creation of the container directory via `os.makedirs(..., exist_ok=True)` prior to instantiating any SQLite database.

---

### 3. $\Omega_{\text{C7.7}}$: Cryptographic Trust Anchor
* **Axiom:** *Circular Authority* (the system blindly validating itself in self-referential loops) is prohibited.
* **Mandatory Mechanism:** Any recursive swarm validation (Swarm / Ultrathink) must anchor to an immutable externally verified cryptographic token (`0xDEADBEEF` / `c7_recursive_self_audit_bft.py`).

---

### 4. $\Omega_{\text{BFT-04}}$: Byzantine Idempotency
* **Axiom:** Every ledger mutation or persistent state must be idempotent and explicitly verify data non-collision.
* **Prohibition:** Blind use of `INSERT OR IGNORE` is prohibited.
* **Correct Pattern:** Explicit catch of `sqlite3.IntegrityError` and comparison of existing vs. incoming payload. If they differ, trigger *Fail-Fast*.

---

### 5. $\Omega_{\text{VALVE}}$: Thermodynamic Capacity Valves
* **Axiom:** In-memory queues and buffers cannot expand into infinite entropy.
* **Prohibition:** `asyncio.Queue()` without a `maxsize` parameter.
* **Correct Pattern:** Mandatory bounded instantiation: `asyncio.Queue(maxsize=1024)`.

---

### 6. $\Omega_{\text{HIERARCHY}}$: Master Domain Hierarchy
* **Axiom:** The architecture is strictly organized into 4 Master Domains hosted within `1_Operaciones_Activas/`:
  - `01_INTEL_SUITE`: OSINT, Document Mining, B2B Intelligence.
  - `02_CORTEX_ENGINE`: BFT Engine, Deterministic Memory, Ultrathink.
  - `03_MOSKV_STUDIO`: Tauri/Vite Application and Content Forges.
  - `04_LABORATORIO_RD`: Moskv84 Compiler, Rust Native (`strike-rs`), R&D.

---

## II. TAXONOMY OF THERMODYNAMIC ANTIPATTERNS

Antipatterns represent entropic degradation in the codebase. They are classified by their physical and semantic failure mode:

```
+-----------------------------------------------------------------------------------+
|                           BFT ANTIPATTERN TAXONOMY                                |
+--------------------------+-----------------------+--------------------------------+
| Category                 | Antipattern           | Thermodynamic Impact           |
+--------------------------+-----------------------+--------------------------------+
| Polling / Control Loop   | AP-01: Turing Spin    | Thermal Dissipation (CPU / W)  |
| Buffer Management        | AP-02: Unbounded Queue| OOM Leak / Fail Backpressure   |
| Syntactic Parsing        | AP-03: AST Necrosis   | B60 Reflexive Fragility        |
| Error Handling           | AP-04: Blind Catch    | Silent Ledger Corruption       |
| Consensus & Trust        | AP-05: Circular Auth  | Deterministic Hallucination    |
| Communication & Prose    | AP-06: Text Anergy    | Context Leak & ATP Waste       |
| Monorepo Structure       | AP-07: Domain Drift   | Omega_23 Resolution Breach     |
| Subprocess Execution     | AP-08: Shell List Pass| Phantom Execution / Silent Fail|
+--------------------------+-----------------------+--------------------------------+
```

### AP-01: Turing Castration (Stochastic Polling)
* **Description:** Wait loops that consume active CPU cycles without relying on synchronization events.
* **Anti-Pattern Formula:**
  ```python
  # INCORRECT: Useless ATP dissipation
  while True:
      await asyncio.sleep(0.1)
  ```
* **Thermodynamic Remediation:**
  ```python
  # CORRECT: Coupled to shutdown event / synchronizer
  while not shutdown_event.is_set():
      await shutdown_event.wait()
  ```

---

### AP-02: Infinite Buffer Flushes (Contained Pressure Leak)
* **Description:** Creation of unbounded asynchronous queues allowing infinite entropic accumulation under load.
* **Anti-Pattern Formula:**
  ```python
  # INCORRECT: OOM Risk
  queue = asyncio.Queue()
  ```
* **Thermodynamic Remediation:**
  ```python
  # CORRECT: Backpressure Valve
  queue = asyncio.Queue(maxsize=1024)
  ```

---

### AP-03: Autoimmune Necrosis (Fragile Syntactic Reflection)
* **Description:** Use of `ast.parse` or `ast.NodeVisitor` to inspect/mutate code within the `BABYLON-60` kernel isolation.
* **Impact:** Massive failure against minor syntax or interpreter version variations.
* **Thermodynamic Remediation:**
  - *Pure Syntactic Validation:* Use `compile(source, filename, "exec")`.
  - *Semantic Validation:* Deterministic lexical parsing (`re.search`) or isolated formal grammars.

---

### AP-04: Byzantine Silence (Blind Exception Swallowing)
* **Description:** Blind catching of exceptions via `except: pass` or `except Exception: pass` that hides ledger inconsistencies.
* **Anti-Pattern Formula:**
  ```python
  # INCORRECT: Anergy concealment
  try:
      execute_ledger_mutation()
  except Exception:
      pass
  ```
* **Thermodynamic Remediation:**
  ```python
  # CORRECT: Explicit catch, BFT logging, and Fail-Fast
  try:
      execute_ledger_mutation()
  except sqlite3.IntegrityError as err:
      logger.error(f"[BFT_FAIL_FAST] Integrity fault: {err}")
      raise ValueError(f"INV_BFT_04 Violation: {err}")
  ```

---

### AP-05: Circular Authority (Self-Referential Validation Loop)
* **Description:** Attempting to verify the validity or security of a component using the mutable component itself without external anchoring.
* **Thermodynamic Remediation:** Anchor all recursive audits to the `0xDEADBEEF` BFT hash via `c7_recursive_self_audit_bft.py`.

---

### AP-06: Syntactic Anergy (Latent Friction in Dialogue/Prose)
* **Description:** Generation of decorative introductions, redundant justifications, or extensive explanations prior to code modification.
* **Thermodynamic Remediation:** C5-REAL Protocol (Latent Friction = 0). Prose reduced to a YAML matrix / brutalist 3-line summary.

---

### AP-07: Domain Fragmentation (Monorepo Drift)
* **Description:** Creation of sibling modules or projects directly at the `~/10_PROJECTS/` root instead of nesting them in the Mother Hierarchy.
* **Thermodynamic Remediation:** `RULE_TEOREMA_MADRE_HIERARCHY` Invariant. Every submodule must be assimilated into `1_Operaciones_Activas/{01_INTEL_SUITE, 02_CORTEX_ENGINE, 03_MOSKV_STUDIO, 04_LABORATORIO_RD}`.

---

### AP-08: Subprocess Fragmentation (Shell=True List Passing)
* **Description:** Passing a list of arguments to `subprocess.run` or `subprocess.Popen` while concurrently asserting `shell=True`. Python executes only the first element through the shell, ignoring or misinterpreting the rest, causing a phantom execution (silent fail).
* **Anti-Pattern Formula:**
  ```python
  # INCORRECT: Phantom Execution
  subprocess.run(["python3", "script.py"], shell=True)
  ```
* **Thermodynamic Remediation:**
  ```python
  # CORRECT: String pass for shell OR List pass for direct execution
  subprocess.run("python3 script.py", shell=True)
  # OR
  subprocess.run(["python3", "script.py"], check=True)
  ```

---

## III. C5-REAL AUDIT PROTOCOL (5 PHASES)

Any structural mutation or refactoring in the monorepo must self-evaluate and pass the 5-Phase C5-REAL Audit matrix:

```
[Phase 1: Latent Friction] ----> Elimination of superfluous prose.
         |
[Phase 2: Phantom Target] -----> Confirmation of physical existence on disk.
         |
[Phase 3: Idempotency] ---------> Zero redundant writes if delta = 0.
         |
[Phase 4: Semantics & BFT] -----> Zero blind catch, integrity validation.
         |
[Phase 5: Git Sentinel] --------> Atomic consolidation of BFT commit.
```

---

## IV. BRUTALIST YAML CHECK MATRIX

```yaml
thermodynamic_audit_matrix:
  invariants:
    omega_1: EXERGY_CONSERVATION_ENFORCED
    omega_23: DYNAMIC_MODULE_RESOLUTION_ACTIVE
    omega_c7_7: TRUST_ANCHOR_ANCLADO_0xDEADBEEF
    omega_bft_04: IDEMPOTENCY_FAIL_FAST_READY
    omega_valve: QUEUE_MAXSIZE_VALVES_SET
    omega_hierarchy: MASTER_DOMAINS_RESTRICTED
  antipattern_purges:
    ap_01_turing_spin: CLEANSED
    ap_02_unbounded_queue: CLEANSED
    ap_03_ast_necrosis: ISOLATED
    ap_04_blind_catch: PROHIBITED
    ap_05_circular_auth: BOUNDED
    ap_06_prose_friction: PURGED
    ap_07_domain_drift: ASSIMILATED
    ap_08_subprocess_fragmentation: PURGED
  verdict: C5_REAL_EXERGY_CERTIFIED
```
