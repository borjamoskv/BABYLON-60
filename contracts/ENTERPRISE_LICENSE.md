# BABYLON-60 Sovereign Dual-License · Enterprise Commercial Agreement (v5.1)

**Licensor:** Borja Fernández Angulo (`borjamoskv`)  
**Ecosystem:** BABYLON-60 Sovereign Agent Trust Kernel (`00_ABZU_KERNEL` / `01_KISH_ENGINE`)  
**Jurisdiction:** Neutral International Commercial Arbitration & Delaware / Basque Autonomous Law  
**Root Invariant:** Axiom AX-0 (*No stochastic component may authorize its own irreversible side effects*)  

---

## 1. Preamble & Ontological Demarcation
BABYLON-60 is distributed under the **Sovereign Dual-License v4.0 (`INV_C5_17`)** defined in the repository root [LICENSE](../LICENSE):
1. **Sovereign Tier (100% Free / Gratis):** Permission is granted free of charge to any individual, independent developer, student, researcher, or non-commercial entity to use, copy, modify, merge, publish, distribute, sublicense, and run this software for any non-commercial purpose, as well as for security auditing, formal verification (Lean 4 / Z3), independent test reproduction, and pre-procurement source code inspection.
2. **Enterprise Commercial Tier:** Mandatory for any commercial, corporate, or enterprise exploitation by corporations, entities with annual revenue exceeding $1M USD, or commercial SaaS providers where autonomous agents interact with filesystems, networks, financial transactions, or production systems.

---

## 2. Commercial Grant of Rights & Three-Tier Licensing Schedule
Subject to payment of the applicable licensing tier below, Licensor grants Licensee a non-exclusive, non-transferable, worldwide commercial license to:
1. Embed and execute the native Ring-0 C-ABI kernel (`libbabylon60_kernel`) within Licensee's agentic pipelines (LangChain, AutoGen, CrewAI, Custom MCP).
2. Utilize the `SharedManifest` (64-byte L1 cache-line lock-free protocol) for high-frequency inter-process communication ($RFO = 0$).
3. Emit and sign RFC 9942 `COSE_Sign1` receipts and WORM SQLite WAL traces for compliance with European Union Regulation (EU) 2024/1689 (EU Artificial Intelligence Act, Articles 12, 14, 15).

| Commercial Tier | Annual / Fixed Fee | Deployment Substrate & Scope | Procurement & Settlement Rule |
| :--- | :--- | :--- | :--- |
| **Tier 1 · Enterprise Pilot** (*Phase Land · 60 Days*) | **15.000 €** *(one-off fixed fee)* | Baseline forensic audit (`c5-codebase-valuation-audit` + `c5-rea`), ring-scoped `AGENTS.md`, and single-workflow `EL0` / WORM confinement. | Direct discretionary approval (below standard corporate RFP thresholds); 100% payable upon order signature. |
| **Tier 2 · Production Cluster** (*Phase Expand · Standard*) | **60.000 € / year** *(per cluster)* | Full production deployment across Licensee's headless `linux-x86_64` / `aarch64` or `darwin-arm64` cluster (`larsa-bft` quorum + HSM/TPM/KMS `COSE_Sign1`). | Annual cryptographic license renewal under this standard adhesion agreement; zero per-seat or token-volume surcharges. |
| **Tier 3 · Sovereign On-Premise Hardware Appliance** (*Turnkey Air-Gapped Node*) | **95.000 € – 120.000 € / year** *(+ 100% upfront hardware pass-through)* | Dedicated high-density Apple Silicon Ultra appliance (up to 256 GB unified RAM) with Zero-Touch provisioning, factory Secure Enclave TRNG/P-256 custody, local LLM/System-1 inference, and WORM `cortex-persist` ledger. | **100% upfront financing by Licensee** (hardware + annual license settled prior to provisioning); standard master adhesion contract with zero recurring legal intermediary tolls. |

### 2.1 Technical Anatomy of a Billable Production Cluster (`60.000 € / year`)

For enterprise security licensing and audit demarcation, **one (1) BABYLON-60 Production Cluster (`60.000 € / year`)** is contractually and cryptographically defined as **one independent WORM cryptographic chain of custody (1 Merkle Evidence Root + 1 Monotonic KUDURRU-64 Epoch Domain)**:

| Cluster Component | Monorepo Primitive (`BABYLON-60`) | Technical & Cryptographic Licensing Boundary (`60.000 € / year`) |
| :--- | :--- | :--- |
| **1. Primary Epoch Arbiter (`Layer-0 EL0`)** | 64-byte `SharedManifest` (`#[repr(C, align(64))]`) + SPMC Seqlock protocol + `babylon_top` binary. | One cluster corresponds to **1 authority domain and monotonic epoch** ($\mathcal{T}_{\text{auth}}$ 7-tuple). Environments with distinct security policies (*Development/CI*, *Staging/Pre-Production*, *Critical Production*) cannot share the same shared-memory manifest or epoch without violating `L3_ISOLATION`. |
| **2. Deterministic Witness Quorum (`LARSA-BFT`)** | `src/larsa_bft.rs` (`feature = "larsa-bft"`) + neuro-symbolic firewall. | Strictly segregates stochastic proposal generators (`ProposedIntent`) from the deterministic verification witness quorum within the cluster boundary. |
| **3. WORM Persistence Substrate (`cortex-persist`)** | Single-writer SQLite WAL (`PRAGMA synchronous = FULL`) + 154-byte `.effect_wal.bin` (`SHA-256` precondition / `BLAKE3` on-wire & Merkle) + `SourceRecords` (`SHA3-256`). | By architectural design, the `cortex-persist` ledger enforces single-writer SQLite WAL serialization with hash-chaining and Merkle trees (`merkle_b3.rs`). **Each independent WORM database instance with its own evidence root constitutes one (1) billable Cluster.** |
| **4. EU AI Act Forensic Receipt Emitter** | `halt-receipt` (`coset` + `ciborium`, RFC 9942 `COSE_Sign1`) + `auditoria_ai_act.md`. | Emits cryptographic receipts bound to the specific cluster identity to support technical traceability, human-oversight gating, and fail-stop robustness under EU AI Act Articles 12, 14, and 15 (subject to Licensee's organizational procedures). |

#### Natural Account Expansion Schedule (Regulated Enterprise Topology)
Because each cluster is cryptographically bound to a single SQLite WAL writer and an `L3_ISOLATION` boundary, regulated entities (banking, defense, healthcare, telecommunications, critical infrastructure) cannot commingle test traces with production ledgers or merge departments with distinct security classifications:
- **1 Sandbox / CI Integration Cluster:** `60.000 € / year`
- **1 Pre-Production / Compliance & Red-Team QA Cluster:** `60.000 € / year`
- **1 to 2 Critical Production Clusters (Core Operations):** `60.000 € – 120.000 € / year`
- **Standard Enterprise Annual Contract Value (ACV):** **`180.000 € – 240.000 € / year` per Enterprise Account.**

---

## 3. Compliance & Governance Guarantees in Silicon
Licensor guarantees that BABYLON-60 complies with its audited silicon specifications:
- **Article 12 (Continuous Traceability):** Every tool execution dispatched through BABYLON generates a tamper-evident cryptographic receipt and Merkle state root inclusion proof.
- **Article 14 (Human Oversight):** Hardware-enforced authorization gates — via local `Secure Enclave Touch ID P-256` (`allowableReuseDuration = 0`) on `darwin-arm64` workstations or via `FIDO2 / YubiKey HSM`, server `TPM 2.0`, or `Cloud KMS (PKCS#11)` emitting RFC 9942 `COSE_Sign1` receipts on headless `linux-x86_64` / `aarch64` clusters — prevent autonomous irreversible execution beyond defined capability envelopes.
- **Article 15 (Fail-Stop Robustness):** Any capability violation or invariant breach triggers immediate deterministic apoptosis (`POISONED = 0xDEAD_6060`), halting the node within bounded nanoseconds before side-effect propagation.

---

## 4. Air-Gap Humano & Asynchronous Interface SLA
To preserve the operational entropy and biological integrity of the Licensor:
1. **Asynchronous Interface:** All technical support, upgrades, and verification evidence shall be exchanged exclusively via secure asynchronous machine protocols (Signed GitHub commits, PGP-encrypted mail, CLI test suites).
2. **Air-Gap:** No synchronous meetings, video calls, or physical presence of the Licensor shall be demanded or provided. Verification is strictly objective and checked in silicon.
3. **Escrow & Determinism:** Licensee is provided with full reproducible builds verified by SHA-256 digests and machine-checked Lean 4 trace invariants (`BabylonTrace.lean`).

---

## 5. Settlement & Treasury Mechanics
- Payments may be remitted in EUR, USD (via Licensor's vehicular operating entity) or directly in Bitcoin (L1 on-chain settlement to Licensor's multisig cold storage sink).
- All licenses are subject to annual cryptographic renewal receipts signed by Licensor's Sovereign P-256 key.

---

## 6. Native IP Provenance & Internalized Ancestral Lineage
- **Seqlock.** Borja Fernández Angulo identifies his work on `SeqlockCell` in `borjamoskv/axiom-0` as the conceptual basis for BABYLON-60's coherent snapshot protocol. BABYLON-60 implements the protocol in its own `SharedManifest`. See the [seqlock implementation and Git history](IP_PROVENANCE.md#seqlock-y-axiom-0).
- **Consensus.** `src/larsa_bft.rs` is a native, self-contained implementation derived conceptually from `borjamoskv/teorema-robinson-moskv` (LARSA BFT / Isostatic Triad Consensus).
- **Sole Authorship & Unencumbered Rights:** All ancestral conceptual repositories and their internalized production counterparts are the sole, original work of Borja Fernández Angulo (`borjamoskv`). Licensor holds full, exclusive, and unencumbered commercial copyright and relicensing authority with zero third-party claims, upstream viral copyleft contamination, or external licensing restrictions.

---

## 7. Technical Annex A: Cross-Silicon Parity Matrix (Pilot Workstation ↔ Production Cluster)

Transitioning from the **Enterprise Pilot Tier (15.000 €)** on local evaluation workstations (`darwin-arm64`) to the **Production Cluster Tier (60.000 €/year per cluster)** on headless data-center infrastructure (`linux-x86_64` / `aarch64`) preserves 100% of the kernel's deterministic security invariants:

| Security Invariant | Local Workstation (`darwin-arm64` / macOS) | Enterprise Production Cluster (`linux-x86_64` / `aarch64`) | Implementation & Licensing Scope |
| :--- | :--- | :--- | :--- |
| **1. Lock-Free Shared Memory & 7-Tuple Arbitration (`Layer-0 EL0`)** | 64-byte `SharedManifest` (`#[repr(C, align(64))]`), SPMC Seqlock protocol, and 7-tuple deterministic capability check in Rust. | Identical user-space (`EL0`) Rust binary operating over L1 cache-line atomic directives on `x86_64` and `ARM64` (`RFO = 0`). | **100% Native Cross-Platform** (Verified under `loom` concurrency checker in `seqlock_loom`). |
| **2. Anti-TOCTOU Atomic Quarantine** | `renameatx_np(RENAME_EXCL \| RENAME_NOFOLLOW_ANY)` + `st_dev`, `st_ino`, and SHA-256 verification prior to `unlinkat`. | `renameat2(RENAME_NOREPLACE)` on same-device `0700` file descriptors + `st_dev`, `st_ino`, and SHA-256 verification. | **100% Implemented in Silicon** across both POSIX/Darwin and Linux VFS paths. |
| **3. Agent Process Confinement (`L3_ISOLATION`)** | macOS Seatbelt (`sandbox-exec`) process-group (`P1`) containment and descriptor isolation. | **Landlock LSM / `seccomp-bpf`** profiles + `cgroups v2` and network/mount namespaces on container or bare-metal Linux nodes. | **Production Cluster Differentiator:** Packaged for headless enterprise deployment (`deploy/`). |
| **4. Cryptographic Human / Hardware Authorization Witness** | Physical Touch ID biometric sensor in Apple Secure Enclave (`NIST P-256`, `allowableReuseDuration = 0`). | Remote or local hardware attestation via **FIDO2 / YubiKey HSM**, server **TPM 2.0**, or **Cloud KMS (PKCS#11)** emitting RFC 9942 `COSE_Sign1` receipts (`coset` / `ciborium`). | **Headless Server Enabler:** Allows CISOs and security officers to authorize critical mutations without physical Mac hardware in the data center. |
| **5. WORM Persistence & Byzantine Cluster Consensus** | Single-writer `cortex-persist` over SQLite WAL + 154-byte `.effect_wal.bin` (`SHA-256` / `BLAKE3`). | Multi-node state replication and Byzantine fault-tolerant witness quorum via native `larsa-bft` (`src/larsa_bft.rs`) and Merkle trees (`merkle_b3.rs`). | **Core Cluster Scope:** Directly governs the per-cluster annual production license (`60.000 €/year`). |

---

## 8. Technical Annex B: 30-Day Enterprise Pilot Statement of Work (Zero-Bloat SOW · `15.000 €`)

To eliminate bespoke consultancy drift and guarantee deterministic delivery within **30 calendar days**, the **Tier 1 Enterprise Pilot (`15.000 €`)** is 100% standardized across four fixed weekly milestones executed asynchronously via BABYLON-60's native verification toolchain:

| Pilot Milestone (30-Day Fixed Scope) | Concrete Deliverable for Licensee | Automated BABYLON-60 Tooling Executed |
| :--- | :--- | :--- |
| **Week 1: Baseline Forensic Audit** (*Days 1–5*) | Epistemic risk report, technical debt inventory, slopsquatting detection, and COCOMO II replacement-cost valuation of Licensee's current agent repository. | `c5-codebase-valuation-audit` + `c5-rea` (`< 15 ms` existence-gap scan) + `audit_token_budget.py` over Licensee's target tree. |
| **Week 2: EL0 Broker & Ring Contract Deployment** (*Days 6–12*) | Installation of the `terminal-mcp` profile (`./install.sh --profile terminal-mcp`), ring-scoped governance contracts (`Ring-0` to `Ring-3`), and `.babylon60rules`. | `./install.sh`, symlinked IDE contracts (`AGENTS.md`, `.cursorrules`, `CLAUDE.md`), and policy declarations in `babylon.toml`. |
| **Week 3: Adversarial Acceptance Simulation (The 5 Proofs)** (*Days 13–20*) | Reproducible execution for Licensee's CISO of the **5 Adversarial Acceptance Proofs** (malicious prompt injection veto, unauthorized deletion interception `AUTH_002`/`AUTH_007`, TOCTOU race immunity, and `SIGKILL` crash idempotency `AUTH_003`/`AUTH_006`). | Automated suites `admission_capability_test` (`test_fl008`), `nemesis_wave4`, and atomic `0700` quarantine `.babylon/quarantine/` with RFC 9942 `COSE_Sign1` receipts. |
| **Week 4: EU AI Act Evidence Package & Production Handover** (*Days 21–30*) | Delivery of the cryptographically verifiable technical dossier (`./verify.sh`, Merkle root, `reports/eu_ai_act_compliance_pack.json`, and `auditoria_ai_act.md` supporting EU AI Act Articles 12, 14, and 15) and Production Cluster sizing (`60.000 €/year` per cluster). | Forensic exporter `babylon60-compliance`, standalone verifier `./verify.sh`, and `auditoria_ai_act.md` technical annex. |
| **PILOT TOTAL (`15.000 €` Fixed Fee)** | **Bounded Production Node + Verifiable EU AI Act Technical Dossier** | **100% Deterministic Delivery over Audited v5.1.1 Monorepo** |

> **Scope Demarcation (`INV_C5_ENTERPRISE_OFFER`):** Technical controls verified during the Pilot attest to BABYLON-60's audited silicon and software boundary (traceability under Art. 12, hardware/cryptographic authorization gating under Art. 14, and fail-stop robustness under Art. 15). Full organizational compliance with Regulation (EU) 2024/1689 remains subject to Licensee's internal governance, human-supervisor training, and data-retention policies.

---

**Institutional Licensing & Due Diligence Contact:** `access@babylon60.com`

**Licensor:**  
**Borja Fernández Angulo**  
*Complex Systems Researcher & Root Sovereign Operator*
