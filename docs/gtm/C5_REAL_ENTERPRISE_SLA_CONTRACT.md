<!-- C5-REAL EXERGY CERTIFIED -->
# C5-REAL Enterprise Master Services Agreement & SLA
## Provable Determinism, Contractual Liability Cap & EU AI Act High-Risk Compliance Framework

**Target Audience:** Enterprise CIOs, CISOs, General Counsels & Boards of Directors
**Commercial Model:** Enterprise Sovereign Runtime (€100,000 — €150,000 ARR / Account)
**Governance Standard:** C5-REAL Deterministic Runtime (Zero Marginal Cloud COGS)

---

## 1. Executive Summary & The 4 Core Value Vectors

This Master Services Agreement & Service Level Agreement ("Agreement") establishes the operational, regulatory, and legal framework under which the **C5-REAL Kernel** operates within the Customer's enterprise perimeter.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       THE 4 CIO COMMERCIAL VECTORS                          │
├────────────────────────────────┬────────────────────────────────────────────┤
│ 1. Legal Certainty & Compliance │ Zero personal liability under EU AI Act.   │
│    (Articles 14, 15, 28)       │ Provable SCITT immutable receipts.         │
├────────────────────────────────┼────────────────────────────────────────────┤
│ 2. Contractual Liability Cap   │ Strict risk containment (€100k-€150k ARR). │
│    (Declared Scope INV-1/INV-2)│ Vendor assumes full liability within scope.│
├────────────────────────────────┼────────────────────────────────────────────┤
│ 3. Zero Cloud Infrastructure   │ Edge/On-Premise WASM Sandbox execution.    │
│    Cost (€0.00 Marginal COGS)  │ No distant cloud compute or API markups.   │
├────────────────────────────────┼────────────────────────────────────────────┤
│ 4. Guaranteed Fail-Stop SLA    │ Deterministic sub-5ms Ring-0 gating.       │
│    (Epistemic Quarantine)      │ Infinite loop & stochastic drift immunity. │
└────────────────────────────────┴────────────────────────────────────────────┘
```

---

## 2. Invariant INV-1: Declared Scope & Deterministic Invariance

1. **Declared Scope (S):** The Provider guarantees that any model output evaluated by the C5-REAL Ring-0 Kernel will adhere strictly to the formal grammatical, relational, and business constraints declared in the Master Policy File (`EpochManifest`).
2. **Deterministic Attestation:** Every state transition passed to the execution environment is signed using an Ed25519 cryptographic receipt compliant with the IETF SCITT standard (RFC 9942 / RFC 9943) and recorded in the local tamper-evident ledger (`cortex_ledger.db`).
3. **Phenomenological Agnosticism:** The Provider makes no claims regarding internal machine cognition or subjective LLM intent. Operational certainty is enforced purely at the boundary layer through deterministic runtime policy checks and verifiable state transitions.

---

## 3. Invariant INV-2: Contractual Liability Cap & EU Regulatory Risk Shift

1. **Contractual Liability Cap:** The Provider's total aggregate liability arising out of or related to this Agreement shall be strictly capped at **100% of the Annual Recurring Revenue (ARR)** paid by the Customer during the preceding twelve (12) months.
2. **EU AI Act Article 28 Reclassification:** By deploying the C5-REAL Deterministic Runtime, the Customer satisfies the regulatory requirements for High-Risk AI Systems (EU AI Act Articles 14 and 15). The C5-REAL Kernel acts as the certified technical boundary, transferring operational liability for non-deterministic model drift from the Customer to the Provider within the Declared Scope.
3. **Defense Against Product Liability Directive (EU 2024/2853):** The cryptographically verifiable SCITT receipts generated at Ring-0 serve as **admissible forensic evidence**, legally refuting any presumption of defect or unpredictable stochastic behavior in corporate litigation.

---

## 4. Invariant INV-3: Zero Cloud COGS & Local Compute Sovereignty

1. **Sovereignty of Compute:** All verification, WASM sandboxing, and ledger operations execute exclusively inside the Customer’s virtual private cloud (VPC), local data center, or bare-metal edge hardware.
2. **Zero Marginal Infrastructure Cost (€0.00 / Tx):** Because the computational workload of verification and execution is hosted entirely on Customer-managed silicon, the Provider incurs zero marginal cloud infrastructure costs per transaction, guaranteeing enterprise margin sustainability (~95%+).

---

## 5. Invariant INV-4: ISO/IEC 42001 & ENISA Governance Auditability

1. **Management System Alignment:** The C5-REAL Kernel provides automated compliance controls mapped directly to **ISO/IEC 42001:2023** (Artificial Intelligence Management System) and **ENISA** cybersecurity guidelines.
2. **Continuous Auditability:** Enterprise compliance auditors can extract deterministic proof bundles at any time via the C5 CLI (`python3 -m c5real audit --export`), eliminating manual audit preparation costs.

---

## 6. Performance Metrics, SLA Carve-Outs & Credit Structure

### 6.1 SLA Performance Metrics

| Performance Metric | Target SLA | Guaranteed Operational Boundary |
| :--- | :---: | :---: |
| **System Uptime / Availability** | 99.99% | Monthly Uptime Percentage |
| **Effective Gating Latency (T_eff)** | < 2.0 ms | < 5.0 ms (Hard Ring-0 Limit) |
| **Reproducibility Coefficient (ρ)** | 100% | ρ ≥ 0.95 (Bootstrap N ≥ 100) |
| **Fail-Stop Quarantine Latency** | < 100 µs | Sub-millisecond CAS Epistemic Halt |
| **Marginal Cloud Infrastructure Cost** | **€0.00 / Tx** | Local Silicon Bound |

### 6.2 SLA Exemption for Preventive Regulatory Halts (Article 15)

- Under Article 15 of the EU AI Act, high-risk systems must prevent anomalous or hallucinatory behavior.
- When the Ring-0 Entropy Sentinel detects a statistical variance spike (`Var(H) > ε`) or an unhandled exception, it executes an immediate **Atomic Fail-Stop (CAS Epistemic Halt)** in sub-millisecond time.
- **Legal Protection & SLA Carve-Out:** Safety-induced halts are legally classified as *Preventive Regulatory Compliance Events* and are expressly excluded from system downtime calculations under the 99.99% Availability SLA.

### 6.3 Service Credits Schedule

If monthly system availability falls below the guaranteed 99.99% SLA (excluding Preventive Regulatory Compliance Events), Customer shall be entitled to the following Service Credits:

- **99.90% to 99.98% Availability:** 10% credit of monthly ARR fee.
- **99.50% to 99.89% Availability:** 25% credit of monthly ARR fee.
- **< 99.50% Availability:** 50% credit of monthly ARR fee.
- **Latency Violation (`T_eff > 5.0 ms` in > 0.1% transactions):** 15% credit of monthly ARR fee.

---

## 7. Data Sovereignty, Intellectual Property & Zero Model Training

1. **Absolute Data Sovereignty:** Customer retains exclusive ownership of all prompts, inputs, outputs, domain data, and enterprise policy configurations.
2. **Zero Model Training Guarantee:** Provider covenants and warrants that no Customer data, payloads, or telemetry will ever be transmitted outside the Customer perimeter, used for external model training, or retained by Provider.
3. **Zero-Knowledge Ledger Design:** The SCITT ledger (`cortex_ledger.db`) stores only cryptographic Merkle root hashes (SHA3-256) and COSE receipts. No cleartext Personally Identifiable Information (PII) or proprietary trade secrets are recorded in the ledger.

---

## 8. Zero-Trust Security, SOC 2 Alignment & Air-Gapped Operation

1. **Air-Gapped Execution:** The C5-REAL Kernel is fully operational in completely air-gapped environments with zero external network dependencies or internet egress requirements.
2. **SOC 2 Type II & ISO 27001 Controls:** The runtime implements strict access control, memory isolation (`WASM Sandbox`), and cryptographic audit trails mapped to SOC 2 Security & Confidentiality Trust Services Criteria.
3. **Incident Notification SLA:** Provider commits to notifying Customer's CISO within **exactly one (1) hour** of confirming any critical security flaw or cryptographic seal compromise in Ring-0.

---

## 9. Term, Commercial Consideration & Sovereign Exit Protocol

1. **Initial Term & ARR Fee:** The initial term of this Agreement shall be twelve (12) months at a fixed fee of **€100,000 — €150,000 ARR** per enterprise account.
2. **Sovereign Exit Guarantee (Anti-Lock-In):** Upon expiration or termination of this Agreement, Customer retains full, perpetual, offline ownership of all generated SCITT receipts, local SQLite ledgers, and WASM binary modules. No data extraction fee or proprietary lock-in shall apply.

---

## 10. Governing Law, Jurisdiction & Fast-Track Technical Arbitration

1. **Governing Law:** This Agreement shall be governed by and construed in accordance with the laws of the European Union and the jurisdiction of the Courts of Madrid, Spain (or Customer's designated EU Member State).
2. **Fast-Track Technical Arbitration:** Any dispute regarding SCITT receipt validity or SLA latency bounds shall be submitted to fast-track technical arbitration before an independent certified cryptographic expert agreed upon by the Parties.

---

## 11. Execution & Cryptographic Signature Block

Executed by authorized representatives of the Parties:

**CUSTOMER CIO / CHIEF LEGAL OFFICER:**

`Name: _________________________________`
`Title: ________________________________`
`Signature: ____________________________`
`Date: _______________`

**C5-REAL SYSTEM OPERATOR & LEAD ARCHITECT:**

`Name: Borja Fernández Angulo (@borjamoskv)`
`Title: Lead Architect & Chief Executive Operator`
`Signature: borjamoskv [MOSKV-1 APEX]`
`Date: 2026-08-13`
`SHA-256 System Seal: 1183271f5ab75be60a7daf7380cf6f187c034a586b2c0881112e74c9e568ceeb`
