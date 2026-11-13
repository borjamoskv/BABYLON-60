# BABYLON-60 Sovereign Dual-License · Enterprise Commercial Agreement (v5.0)

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

## 2. Commercial Grant of Rights
Subject to payment of the agreed licensing fees (Pilot Tier: 15.000 €; Production Cluster: 60.000 €/year per clúster), Licensor grants Licensee a non-exclusive, non-transferable, worldwide commercial license to:
1. Embed and execute the native Ring-0 C-ABI kernel (`libbabylon60_kernel`) within Licensee's agentic pipelines (LangChain, AutoGen, CrewAI, Custom MCP).
2. Utilize the `SharedManifest` (64-byte L1 cache-line lock-free protocol) for high-frequency inter-process communication ($RFO = 0$).
3. Emit and sign RFC 9942 `COSE_Sign1` receipts and WORM SQLite WAL traces for compliance with European Union Regulation (EU) 2024/1689 (EU Artificial Intelligence Act, Articles 12, 14, 15).

---

## 3. Compliance & Governance Guarantees in Silicon
Licensor guarantees that BABYLON-60 complies with its audited silicon specifications:
- **Article 12 (Continuous Traceability):** Every tool execution dispatched through BABYLON generates a tamper-evident cryptographic receipt and Merkle state root inclusion proof.
- **Article 14 (Human Oversight):** Authorization gates designed to require a hardware signature before autonomous irreversible execution beyond defined capability envelopes. Evidence status as of 2026-11-11: on `darwin-arm64`, the `Secure Enclave Touch ID P-256` gate (`allowableReuseDuration = 0`) has one historical local signature, recorded on 2026-10-30 for the regulatory gate ([record](../docs/security/EU_AI_ACT_NATIVE_2026-10-30.md)); automated suites use software keys, and the gate is otherwise `NO_VERIFICADO`. On headless `linux-x86_64` / `aarch64` clusters, `TPM 2.0` and AWS Nitro gate backends exist in source (`src/ring0.rs`) with no recorded hardware run (`NO_VERIFICADO`); `FIDO2 / YubiKey` and `Cloud KMS (PKCS#11)` are not implemented.
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
- **Self-Contained Implementation:** Key concurrency and consensus primitives, including `src/seqlock.rs` (derived conceptually from author's foundational research in `borjamoskv/axiom-0` [Wait-Free SeqlockCell / QTT]) and `src/larsa_bft.rs` (derived conceptually from `borjamoskv/teorema-robinson-moskv` [LARSA BFT / Isostatic Triad Consensus]), are 100% native, self-contained implementations internalized directly into BABYLON-60.
- **Sole Authorship & Unencumbered Rights:** All ancestral conceptual repositories and their internalized production counterparts are the sole, original work of Borja Fernández Angulo (`borjamoskv`). Licensor holds full, exclusive, and unencumbered commercial copyright and relicensing authority with zero third-party claims, upstream viral copyleft contamination, or external licensing restrictions.

---

## 7. Technical Annex A: Cross-Silicon Parity Matrix (Pilot Workstation ↔ Production Cluster)

Transitioning from the **Enterprise Pilot Tier (15.000 €)** on local evaluation workstations (`darwin-arm64`) to the **Production Cluster Tier (60.000 €/year per cluster)** on headless data-center infrastructure (`linux-x86_64` / `aarch64`) preserves a security invariant only where the table below says so. The table states, per invariant, what is implemented and evidenced on each platform as of 2026-11-11; `NO_VERIFICADO` marks a cell without recorded evidence:

| Security Invariant | Local Workstation (`darwin-arm64` / macOS) | Enterprise Production Cluster (`linux-x86_64` / `aarch64`) | Implementation & Licensing Scope |
| :--- | :--- | :--- | :--- |
| **1. Lock-Free Shared Memory & 7-Tuple Arbitration (`Layer-0 EL0`)** | 64-byte `SharedManifest` (`#[repr(C, align(64))]`), SPMC Seqlock protocol, and 7-tuple deterministic capability check in Rust. | Identical user-space (`EL0`) Rust binary operating over L1 cache-line atomic directives on `x86_64` and `ARM64` (`RFO = 0`). | **100% Native Cross-Platform** (Verified under `loom` concurrency checker in `seqlock_loom`). |
| **2. Anti-TOCTOU Atomic Quarantine** | `renameatx_np(RENAME_EXCL \| RENAME_NOFOLLOW_ANY)` + `st_dev`, `st_ino`, and SHA-256 verification prior to `unlinkat`. | `renameat2(RENAME_NOREPLACE)` on same-device `0700` file descriptors + `st_dev`, `st_ino`, and SHA-256 verification. | **100% Implemented in Silicon** across both POSIX/Darwin and Linux VFS paths. |
| **3. Agent Process Confinement (`L3_ISOLATION`)** | macOS Seatbelt (`sandbox-exec`) process-group (`P1`) containment and descriptor isolation. | Not implemented on public `main` (`daa0a84`) as of 2026-11-11. Draft [PR #62](https://github.com/borjamoskv/BABYLON-60/pull/62), not merged, adds Landlock filesystem read/write rules for terminal agents (`babylon60 run`, `01_KISH_ENGINE/babylon60/confine/`) and a `seccomp` filter limited to `TIOCSTI`/`TIOCLINUX` terminal injection plus foreign-ABI syscalls; it records Linux x86_64 demo and stress runs (`reports/confine/`). No `cgroups v2`, network or mount namespaces are implemented; network access and path-named Unix sockets are declared limits. | `NO_VERIFICADO` for production clusters. `deploy/` contains a `babylon-attest` container image without agent-confinement settings; container runtime isolation is not BABYLON-60 agent confinement and is untested here. |
| **4. Cryptographic Human / Hardware Authorization Witness** | Physical Touch ID biometric sensor in Apple Secure Enclave (`NIST P-256`, `allowableReuseDuration = 0`). One historical local signature, recorded on 2026-10-30 for the regulatory gate; automated suites use software keys; otherwise `NO_VERIFICADO`. | `TPM 2.0` (`/dev/tpmrm0`) and AWS Nitro (`/dev/nsm`) gate backends exist in source (`src/ring0.rs`); no run on TPM or Nitro hardware is recorded (`NO_VERIFICADO`), and [QUICKSTART_ENTERPRISE](../docs/03_guides/QUICKSTART_ENTERPRISE.md) lists TPM 2.0 anchoring as roadmap. **FIDO2 / YubiKey** and **Cloud KMS (PKCS#11)** are not implemented. | **Headless authorization without Mac hardware:** a goal, not an evidenced capability (`NO_VERIFICADO`). |
| **5. WORM Persistence & Byzantine Cluster Consensus** | Single-writer `cortex-persist` over SQLite WAL + 154-byte `.effect_wal.bin` (`BLAKE3`). | Multi-node state replication and Byzantine fault-tolerant witness quorum via native `larsa-bft` (`src/larsa_bft.rs`) and Merkle trees (`merkle_b3.rs`). | **Core Cluster Scope:** Directly governs the per-cluster annual production license (`60.000 €/year`). |

---

**Institutional Licensing & Due Diligence Contact:** `access@babylon60.com`

**Licensor:**  
**Borja Fernández Angulo**  
*Complex Systems Researcher & Root Sovereign Operator*
