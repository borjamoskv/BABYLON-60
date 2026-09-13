# 📚 BABYLON-60 — Master Documentation Index

> **Standard:** C5-REAL v4.3 | **Invariants:** 65 active, 35 vacant, 5 derived theorems  
> **Regime:** Causal-Determinist | **Formal Verification:** Lean 4 (BabylonTrace, 0 errors)

---

## 🗺️ Navigation by Role

<details open>
<summary><b>🏭 Enterprise / DevOps</b> — Deploy in production</summary>

1. [Enterprise Quickstart](./03_guides/QUICKSTART_ENTERPRISE.md) — Docker / Kubernetes sidecar
2. [Commercial License](./COMMERCIAL_LICENSE.md) — `BABYLON60_LICENSE_KEY` setup
3. [EU AI Act Compliance](./05_compliance_eu_ai_act.md) — Articles 9–14 certification
4. [Security Policy](../SECURITY.md) — Vulnerability SLA

</details>

<details>
<summary><b>🦀 Rust / Systems Engineer</b> — Ring-0 kernel work</summary>

1. [Architecture Manifest](../ARCHITECTURE_MANIFEST.md) — Full monorepo topology
2. [SharedManifest spec](./01_spec/spec_technical.md) — 64B Seqlock SPMC, C-ABI
3. [ADR-002: PyO3/Maturin FFI](./adr/ADR-002-pyo3-maturin-ffi-bridge.md) — Rust↔Python bridge
4. [BabylonTrace.lean](./proof/lean/BabylonTrace.lean) — Formal bisimulation proof
5. [Cryptographic Profile](./01_spec/spec_cryptographic_profile.md) — Ed25519, WORM, RFC 3161

</details>

<details>
<summary><b>🐍 Python Developer</b> — Orchestrator & agents</summary>

1. [Complete Dev Guide](./03_guides/guide_babylon60_complete.md) — Full architecture walkthrough
2. [Hello Causal Tutorial](./03_guides/tutorial_hello_causal.md) — First ledger event
3. [C5 Invariants Spec](./01_spec/spec_invariants.md) — 65 active invariants
4. [Swarm Orchestration](./03_guides/guide_swarm_pxs_orchestration.md) — P×S Legión patterns
5. [Axiom Verification](./03_guides/guide_c5_axiom_verification.md) — `test_c5_invariants.py`

</details>

<details>
<summary><b>🔬 Researcher / Formal Methods</b></summary>

1. [Formal Theory index](./06_theory/) — Robinson → Gödel → Turing → Lean 4
2. [Whitepaper](./WHITEPAPER.md) — Merkle DAG, Self-Falsification Engine, BFT
3. [C5-REAL Compendium](./06_theory/c5_thermodynamic_invariants_compendium.md) — All thermodynamic invariants
4. [Popperian LLM Eval 2026](./04_research/evaluacion_falsacion_llm_models_2026.md)
5. [ADR-001: Lean 4 over Coq/Isabelle](./adr/ADR-001-lean4-over-coq-isabelle.md)

</details>

<details>
<summary><b>⚖️ Legal / Compliance Auditor</b></summary>

1. [EU AI Act Whitepaper](./04_research/eu_ai_act_compliance_whitepaper.md) — Arts. 9–14 full mapping
2. [LegalTech Audit Guide](./03_guides/guide_legaltech_eu_ai_act.md)
3. [Compliance Framework](./05_compliance_eu_ai_act.md) — Cryptographic Merkle log verification
4. [Security Threat Model v4](./02_ontology/security_threat_model_v4.md)
5. [ADR-005: Sovereign Dual-License](./adr/ADR-005-sovereign-dual-license.md)

</details>

---

## ⚡ Sovereign Core & Executive

| Document | Purpose |
| :--- | :--- |
| [SPECIFICATION.md](./SPECIFICATION.md) | Operational semantics, B60 ISA, F60 exact arithmetic, Proof IR |
| [WHITEPAPER.md](./WHITEPAPER.md) | Deep tech: F60, Merkle DAG Ledger, Self-Falsification Engine |
| [KERNEL.md](./KERNEL.md) | Cross-cutting kernel invariants (transversal) |
| [COMMERCIAL_LICENSE.md](./COMMERCIAL_LICENSE.md) | Enterprise Tier commercial license |
| [CANARY_TOKENS.md](./CANARY_TOKENS.md) | Canary Tokens — Ω-11 honeypot |
| [KINETIC_CACHE_AUDIT.md](./KINETIC_CACHE_AUDIT.md) | False sharing mitigation audit |
| [cortex_lsp_setup.md](./cortex_lsp_setup.md) | LSP Paracortex sovereign integration |
| [RESULTADOS.md](./RESULTADOS.md) | Project status & results |

---

## 📋 Technical Specifications (`01_spec/`)

| Document | Purpose |
| :--- | :--- |
| [spec_invariants.md](./01_spec/spec_invariants.md) | 65 active C5-REAL domain invariants |
| [spec_babylon60.md](./01_spec/spec_babylon60.md) | Full formal specification v4.x Causal-Determinist |
| [spec_architecture.md](./01_spec/spec_architecture.md) | Async-persist ledger architecture |
| [spec_technical.md](./01_spec/spec_technical.md) | SharedManifest 64B, Seqlock SPMC, Ring-0 core |
| [spec_cryptographic_profile.md](./01_spec/spec_cryptographic_profile.md) | Ed25519, AES-GCM, RFC 3161 timestamp profile |
| [spec_security_model.md](./01_spec/spec_security_model.md) | Security model & attack boundary definitions |
| [spec_causal_hitl_governance.md](./01_spec/spec_causal_hitl_governance.md) | Human-in-the-Loop governance & operational workers |
| [spec_exergy_ontology.md](./01_spec/spec_exergy_ontology.md) | Exergy semantics & ontology |
| [spec_graph_canonical.md](./01_spec/spec_graph_canonical.md) | Canonical causal graph spec |
| [spec_proof_ir.md](./01_spec/spec_proof_ir.md) | Proof IR → Lean 4 emitter specification |
| [artifact_format_v1.md](./01_spec/artifact_format_v1.md) | Artifact format v1 |
| [audit_babylon60_v2.5.md](./01_spec/audit_babylon60_v2.5.md) | Causal-Determinist audit — v2.5.1 |

---

## 🧠 Axiomatic Ontology & Threat Models (`02_ontology/`)

| Document | Purpose |
| :--- | :--- |
| [axiom_ontology.md](./02_ontology/axiom_ontology.md) | Absolute semantic isomorphism ontology |
| [axiom_axiomatization.md](./02_ontology/axiom_axiomatization.md) | Motor Causal-1 APEX formal axiomatization |
| [security_threat_model_v4.md](./02_ontology/security_threat_model_v4.md) | v4.0 threat model & attack vector mitigation |
| [spec_c5_graph_isomorphism.md](./02_ontology/spec_c5_graph_isomorphism.md) | APEX structural isomorphism matrix |
| [axiom_oncologia_300_primitivas.md](./02_ontology/axiom_oncologia_300_primitivas.md) | 300 molecular oncology primitives |

---

## 📖 Guides & Tutorials (`03_guides/`)

| Document | Audience | Purpose |
| :--- | :--- | :--- |
| [QUICKSTART_ENTERPRISE.md](./03_guides/QUICKSTART_ENTERPRISE.md) | DevOps | Docker/K8s sidecar deployment |
| [tutorial_hello_causal.md](./03_guides/tutorial_hello_causal.md) | Developer | First causal ledger event |
| [guide_babylon60_complete.md](./03_guides/guide_babylon60_complete.md) | Developer | Full architecture & dev guide |
| [guide_c5_axiom_verification.md](./03_guides/guide_c5_axiom_verification.md) | Developer | Axiom injection & invariant verification |
| [guide_legaltech_eu_ai_act.md](./03_guides/guide_legaltech_eu_ai_act.md) | Legal | LegalTech audit & EU AI Act |
| [guide_swarm_pxs_orchestration.md](./03_guides/guide_swarm_pxs_orchestration.md) | Developer | Kimi K3 multi-agent swarm (P×S) |
| [guide_bio_silico_transduction.md](./03_guides/guide_bio_silico_transduction.md) | Researcher | Bio-Silicio transduction & causal graphs |
| [guide_commercial_license.md](./03_guides/guide_commercial_license.md) | Enterprise | License setup & enforcement |
| [guide_experimental.md](./03_guides/guide_experimental.md) | Developer | Experimental ledger extensions |
| [guide_explanation.md](./03_guides/guide_explanation.md) | All | Executive briefing: Motor Causal SINGULARITY |
| [guide_skill_arsenal_taxonomy.md](./03_guides/guide_skill_arsenal_taxonomy.md) | Developer | Skill arsenal taxonomy by exergy |
| [tonnetz_audit_guide.md](./03_guides/tonnetz_audit_guide.md) | Legal / Music | Harmonic oversight (EU Art. 14) |
| [guide_repository_source_of_truth.md](./03_guides/guide_repository_source_of_truth.md) | Developer | Repository canonical source of truth |

---

## 🔬 Research & SOTA (`04_research/`)

| Document | Purpose |
| :--- | :--- |
| [eu_ai_act_compliance_whitepaper.md](./04_research/eu_ai_act_compliance_whitepaper.md) | Causal determinism as EU AI Act compliance framework |
| [evaluacion_falsacion_llm_models_2026.md](./04_research/evaluacion_falsacion_llm_models_2026.md) | Popperian falsification of LLM model selection (2026) |
| [centuria_swarm_architecture.md](./04_research/centuria_swarm_architecture.md) | Centuria 100-agent swarm architecture |
| [legion_222_swarm_topology.md](./04_research/legion_222_swarm_topology.md) | Legión 222-agent topology (11 cores × 20 threads) |
| [sota_evolution_roadmap.md](./04_research/sota_evolution_roadmap.md) | SOTA architectural evolution roadmap |
| [sanedrin_reflexive_forking_audit.md](./04_research/sanedrin_reflexive_forking_audit.md) | Sanhedrín audit: reflexive forking |
| [sota/sota_cortex_persist_202607.md](./04_research/sota/sota_cortex_persist_202607.md) | SOTA: async-persist ledger positioning |
| [sota/sota_ssm_lnn_202600.md](./04_research/sota/sota_ssm_lnn_202600.md) | SOTA: SSM, LNN & transformer collapse |
| [README_APEX.md](./04_research/README_APEX.md) | APEX Trials index |

---

## ⚖️ Formal Theory (`06_theory/`)

Mathematical substrate from first principles to silicon realization.

| Document | Level | Purpose |
| :--- | :--- | :--- |
| [01_robinson_arithmetic.md](./06_theory/01_robinson_arithmetic.md) | Foundations | Robinson Arithmetic (Q) |
| [02_goedel_incompleteness.md](./06_theory/02_goedel_incompleteness.md) | Foundations | Gödel's Incompleteness Theorems |
| [03_computability_turing.md](./06_theory/03_computability_turing.md) | Foundations | Computability & Turing halting |
| [04_chaitin_kolmogorov.md](./06_theory/04_chaitin_kolmogorov.md) | Foundations | Chaitin, Kolmogorov & AIT |
| [05_model_theory.md](./06_theory/05_model_theory.md) | Foundations | Model Theory |
| [06_curry_howard.md](./06_theory/06_curry_howard.md) | Foundations | Curry-Howard-Lambek Correspondence |
| [07_cross_domain.md](./06_theory/07_cross_domain.md) | Synthesis | Cross-domain isomorphisms |
| [08_babylon60_architecture.md](./06_theory/08_babylon60_architecture.md) | Applied | BABYLON-60 system invariants |
| [09_formal_ontology_lean.md](./06_theory/09_formal_ontology_lean.md) | Applied | Formal ontology in Lean 4 |
| [10_physical_realization.md](./06_theory/10_physical_realization.md) | Applied | Physical realization in silicon |
| [AXIOMATIZATION_C5_REAL.md](./06_theory/AXIOMATIZATION_C5_REAL.md) | Core | Sealed C5-REAL axiomatic base |
| [TOPOLOGIA_MAESTRA.md](./06_theory/TOPOLOGIA_MAESTRA.md) | Core | Master topology C5-REAL (BABYLON-60/CORTEX) |
| [MOSKV_1_APEX_BLUEPRINT.md](./06_theory/MOSKV_1_APEX_BLUEPRINT.md) | Core | MOSKV-1 APEX manifest & consolidated architecture |
| [c5_thermodynamic_invariants_compendium.md](./06_theory/c5_thermodynamic_invariants_compendium.md) | Reference | All C5-REAL thermodynamic invariants & exergy layers |
| [axiom_cyclic_conformal_aeon.md](./06_theory/axiom_cyclic_conformal_aeon.md) | Theory | Penrose-Landauer theorem & Conformal Aeons (INV_C5_AEON) |
| [axiom_bayesian_disintegration.md](./06_theory/axiom_bayesian_disintegration.md) | Theory | Anti-hallucination formal axiomatization |
| [axiom_legion_swarm.md](./06_theory/axiom_legion_swarm.md) | Theory | Legión parallel workspace swarm |
| [axiom_tonnetz_oversight.md](./06_theory/axiom_tonnetz_oversight.md) | Theory | Neo-Riemannian Tonnetz harmonic oversight |
| [axiom_oncology_protocol.md](./06_theory/axiom_oncology_protocol.md) | Theory | Bio-Silicio transduction & tumoral ontology |
| [AUDIT_AXIOMS_2026.md](./06_theory/AUDIT_AXIOMS_2026.md) | Audit | Epistemic audit: C5-REAL axiomatization verdict |
| [AUDIT_VERDICT_C5_REAL.md](./06_theory/AUDIT_VERDICT_C5_REAL.md) | Audit | C4-SIM hologram collapse verification |
| [VECTOR_A_MASTER_LEDGER_DESIGN.md](./06_theory/VECTOR_A_MASTER_LEDGER_DESIGN.md) | Design | VECTOR A — Master Ledger & ATMS persistence |
| [STATUS_THEORY.md](./06_theory/STATUS_THEORY.md) | Status | Single Source of Truth — theory status |

---

## 🏗️ Architecture Decision Records (`adr/`)

| ADR | Status | Decision |
| :--- | :--- | :--- |
| [ADR-001](./adr/ADR-001-lean4-over-coq-isabelle.md) | ✅ Accepted | Lean 4 over Coq/Isabelle for formal verification |
| [ADR-002](./adr/ADR-002-pyo3-maturin-ffi-bridge.md) | ✅ Accepted | PyO3/Maturin FFI bridge for Rust↔Python runtime |
| [ADR-003](./adr/ADR-003-bft-attestation-architecture.md) | ✅ Accepted | BFT architecture & cryptographic attestation model |
| [ADR-004](./adr/ADR-004-taint-tracking-isolation.md) | ✅ Accepted | Taint tracking & isolation model |
| [ADR-005](./adr/ADR-005-sovereign-dual-license.md) | ✅ Accepted | Sovereign Dual-License v4.0 |
| [ADR-006](./adr/ADR-006-topologia-exposicion-repositorios.md) | ✅ Accepted | C5-REAL public/private repository topology |

---

## 🔐 Formal Proofs (`proof/`)

| File | Status | Content |
| :--- | :--- | :--- |
| [proof/lean/BabylonTrace.lean](./proof/lean/BabylonTrace.lean) | ✅ **0 errors, 0 warnings** | Seqlock SPMC bisimulation · Halt states · Aristotelian Triad in silicon |

---

## 📊 C5-REAL System State

| Dimension | Value |
| :--- | :--- |
| Active Invariants | **65** |
| Vacant slots | 35 |
| Derived Theorems | 5 (incl. Landauer Theorem) |
| Lean 4 formal proofs | ✅ Clean (`BabylonTrace.lean`) |
| Rust tests | ✅ 84 passed, 0 failed |
| Python C5 invariants | ✅ 19 passed, 1 skipped, 1 xfailed |
| Ruff (lint + format) | ✅ 0 errors |
| MyPy strict | ✅ 0 errors (272 files) |

---

<sub>Index maintained under C5-REAL standard. All paths are relative to `docs/`. Last sync: v4.3.0</sub>
