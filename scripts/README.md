# ⚡ BABYLON-60 Sovereign Scripts Suite — Immutable Script Kernel (ISK)

> **Directorio de Automatización, Enjambres BFT, Calidad AST, Atestación SHA-256 y Preservación de Logs**  
> **Estándar:** C5-REAL | **Total Scripts:** 124 Python + 10 Shell | **Shebang Compliance:** 100.0%

## 🛠️ CLI Runner Centralizado
Cualquier tarea del suite se puede ejecutar a través de la CLI unificada [runner.py](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/runner.py):
```bash
./scripts/runner.py status              # Diagnóstico y métricas de salud
./scripts/runner.py audit               # Portón de calidad AST & anti-patrones
./scripts/runner.py preserve --provider all # Custodia forense de logs
./scripts/runner.py swarm -n 100        # Enjambre paralelo BFT en RAM
./scripts/runner.py sync                # Sincronización de skills con docs/skills.json
./scripts/runner.py catalog             # Auto-generación de este catálogo
```

---

## 📂 Catálogo Taxonómico por Dominios C5 (Atestación SHA-256)

### 📁 Babylon60

| Script | Tipo | SHA-256 | Descripción / Propósito |
| :--- | :--- | :--- | :--- |
| [`babylon60/oncology_primitives.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/babylon60/oncology_primitives.py) | `Python` | `696a61e277d1` | CORTEX / BABYLON-60 :: oncology_primitives |

### 🎨 Assets & Multimodal Generators

| Script | Tipo | SHA-256 | Descripción / Propósito |
| :--- | :--- | :--- | :--- |
| [`c5_assets/gen_blip_assets.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_assets/gen_blip_assets.py) | `Python` | `fa600b0c06fd` | Onda cuadrada |
| [`c5_assets/gen_voice_assets.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_assets/gen_voice_assets.py) | `Python` | `b3a539136ee0` | Textos extraídos de GoedelBrosComposition.tsx |
| [`c5_assets/thermo_wallpaper.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_assets/thermo_wallpaper.py) | `Python` | `00efcb3d5853` | Thermo Wallpaper Utility |

### 🎯 Entropy & Calibration Utilities

| Script | Tipo | SHA-256 | Descripción / Propósito |
| :--- | :--- | :--- | :--- |
| [`c5_calibrations/calibrate_aphairesis.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_calibrations/calibrate_aphairesis.py) | `Python` | `31e5aad1dc7a` | calibrate_aphairesis.py — Generador de constantes axiomáticas para thermodynamics.rs (Capa 2) |
| [`c5_calibrations/calibrate_popperian_entropy.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_calibrations/calibrate_popperian_entropy.py) | `Python` | `1b5e2bdb74a7` | [Causal-Determinist] Empirical Calibration Tool for Popperian Shannon Entropy Thresholds. |
| [`c5_calibrations/topological_calibration.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_calibrations/topological_calibration.py) | `Python` | `54263f9c0944` | C5-REAL TOPOLOGICAL CALIBRATION PIPELINE — BABYLON-60 (Capa 2 Aphairesis) |

### ⚡ Centuria & Video Swarm Commanders

| Script | Tipo | SHA-256 | Descripción / Propósito |
| :--- | :--- | :--- | :--- |
| [`c5_centuria/centuria_swarm_commander.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_centuria/centuria_swarm_commander.py) | `Python` | `411982cd631d` | Centuria Swarm Commander Utility |
| [`c5_centuria/centuria_swarm_runner.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_centuria/centuria_swarm_runner.py) | `Python` | `4315ffe4e03d` | Ensure root importability |
| [`c5_centuria/remotion_swarm_orchestrator.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_centuria/remotion_swarm_orchestrator.py) | `Python` | `d940176628a5` | Enforces: |

### 🖥️ CLI Tools & Native Hosts

| Script | Tipo | SHA-256 | Descripción / Propósito |
| :--- | :--- | :--- | :--- |
| [`c5_cli/babylon_mail_cli.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_cli/babylon_mail_cli.py) | `Python` | `d68ae2b5ed06` | BABYLONMAIL CLI & SUBAGENT INTERFACE |
| [`c5_cli/codex_virtual_hud.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_cli/codex_virtual_hud.py) | `Python` | `760d2a490633` | Codex Virtual Hud Utility |
| [`c5_cli/moskv_native_host.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_cli/moskv_native_host.py) | `Python` | `fbebf2741e5f` | MOSKV-1 APEX: Native Messaging Transducer (INV_C5_18 / INV_C5_THERMO_VALVE) |
| [`c5_cli/opsec_sentinel_c5.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_cli/opsec_sentinel_c5.py) | `Python` | `5d2c93bccabf` | Opsec Sentinel C5 Utility |
| [`c5_cli/pty_tmux_bridge.sh`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_cli/pty_tmux_bridge.sh) | `Shell` | `2aa69bc99597` | 🛡️ TMUX-PTY-Bridge-OMEGA (C5-REAL v2.0) |

### 🌀 Cortex Memory & Auto-Consolidation

| Script | Tipo | SHA-256 | Descripción / Propósito |
| :--- | :--- | :--- | :--- |
| [`c5_cortex/autoconsolidate.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_cortex/autoconsolidate.py) | `Python` | `1f71388afa21` | Delete old entries, respecting INV_BFT_04 semantics |
| [`c5_cortex/bootstrap_cortex_memory.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_cortex/bootstrap_cortex_memory.py) | `Python` | `90c2bacb8206` | Bootstrap Cortex Memory Utility |
| [`c5_cortex/consolidate_babylon_vault.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_cortex/consolidate_babylon_vault.py) | `Python` | `0477d218a41d` | Causal-Determinist SOVEREIGN CONSOLIDATION PROTOCOL — BABYLON-60 MEMORY VAULT |
| [`c5_cortex/consolidate_dbs.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_cortex/consolidate_dbs.py) | `Python` | `ceb44ff71f51` | Consolidación BFT (Erradicación del Antipatrón de Dispersión SQLite) |
| [`c5_cortex/cortex_labs_poc.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_cortex/cortex_labs_poc.py) | `Python` | `6a1b0dfb709c` | Prueba de Concepto (PoC) Autónoma: Extracción Causal de Google Labs FX. |
| [`c5_cortex/cortex_objectives_transducer.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_cortex/cortex_objectives_transducer.py) | `Python` | `104ecd3b4da9` | Cortex Objectives Transducer Utility |

### 🔬 C5 Demos & Proofs of Concept

| Script | Tipo | SHA-256 | Descripción / Propósito |
| :--- | :--- | :--- | :--- |
| [`c5_demos/demo_exergy_poc.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_demos/demo_exergy_poc.py) | `Python` | `abeaac33a44b` | [Causal-Determinist] Exergy Optimizer Agent Proof of Concept. |
| [`c5_demos/demo_logos_ethos_ship.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_demos/demo_logos_ethos_ship.py) | `Python` | `38879ffde4ff` | Demo Logos Ethos Ship Utility |
| [`c5_demos/poc_active_inference_efe.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_demos/poc_active_inference_efe.py) | `Python` | `8b1e6cbcbe97` | poc_active_inference_efe.py - PoC 4: Friston Active Inference Free Energy Scheduler |
| [`c5_demos/poc_axiom4_disintegration.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_demos/poc_axiom4_disintegration.py) | `Python` | `3eee5b413d98` | poc_axiom4_disintegration.py — Proof of Concept: Axiom 4 Bayesian Disintegration & Non-Hallucination |
| [`c5_demos/poc_browser_pipeline.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_demos/poc_browser_pipeline.py) | `Python` | `7afc39f0b7af` | Poc Browser Pipeline Utility |
| [`c5_demos/poc_categorical_hallucination.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_demos/poc_categorical_hallucination.py) | `Python` | `58315c1bf1a9` | poc_categorical_hallucination.py - PoC 2: Category-Theoretic Hallucination Audit Engine |
| [`c5_demos/poc_causal_hitl_agent.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_demos/poc_causal_hitl_agent.py) | `Python` | `bc92ad91c8b1` | SOTA Proof of Concept (PoC): Operational Worker with Cryptographic Causal HITL Gate |
| [`c5_demos/poc_cta_comonad.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_demos/poc_cta_comonad.py) | `Python` | `0a7fffde7879` | poc_cta_comonad.py - PoC 6: Event-Sourced Comonadic State Machine (CTA Algebra) |
| [`c5_demos/poc_epistemic_extinction.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_demos/poc_epistemic_extinction.py) | `Python` | `644455370635` | poc_epistemic_extinction.py - PoC 3: Epistemic Extinction & Dimensionality Reduction |
| [`c5_demos/poc_eu_ai_act_audit.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_demos/poc_eu_ai_act_audit.py) | `Python` | `543346dc10af` | poc_eu_ai_act_audit.py - PoC 5: Automated EU AI Act Risk & Compliance Auditor |
| [`c5_demos/poc_f60_time_domain.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_demos/poc_f60_time_domain.py) | `Python` | `a08fc173bbe5` | 32-byte hash commitment |
| [`c5_demos/poc_fast_failure_guard.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_demos/poc_fast_failure_guard.py) | `Python` | `e18a82af50a0` | Poc Fast Failure Guard Utility |
| [`c5_demos/poc_graph_isomorphism_wl.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_demos/poc_graph_isomorphism_wl.py) | `Python` | `cc106248f24a` | [Causal-Determinist] Step 1 Proof of Concept: Graph Isomorphism WL Pre-Filter (INV_C5_28). |
| [`c5_demos/poc_logop_veto.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_demos/poc_logop_veto.py) | `Python` | `c5641bf0cb2b` | Ensure the module can be imported |
| [`c5_demos/poc_tonnetz_oversight.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_demos/poc_tonnetz_oversight.py) | `Python` | `430a095ad65c` | poc_tonnetz_oversight.py — Proof of Concept: Tonnetz Harmonic Oversight & Audio Engine |
| [`c5_demos/poc_two_tier_planner_worker.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_demos/poc_two_tier_planner_worker.py) | `Python` | `d49d44a7a8dd` | MOSKV-1 APEX – Iteración 4 del PoC |
| [`c5_demos/poc_xenharmonic_swarm.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_demos/poc_xenharmonic_swarm.py) | `Python` | `4bd9833bd95c` | poc_xenharmonic_swarm.py - PoC 1: Swarm-Guided Xenharmonic Tuning Engine |
| [`c5_demos/run_commercial_bft.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_demos/run_commercial_bft.py) | `Python` | `3bf8db10f7ae` | Run Commercial Bft Utility |
| [`c5_demos/run_hero_demo.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_demos/run_hero_demo.py) | `Python` | `2a38b7503fcc` | Simulates the live 60-second B2B Enterprise / Investor Demo in the terminal: |

### 🔧 Git Hooks & Commit Utilities

| Script | Tipo | SHA-256 | Descripción / Propósito |
| :--- | :--- | :--- | :--- |
| [`c5_git_utils/commit_polisher.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_git_utils/commit_polisher.py) | `Python` | `7a5bef1705e4` | Continuous Commit Polisher Daemon. |
| [`c5_git_utils/install_git_hooks.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_git_utils/install_git_hooks.py) | `Python` | `49892ac52608` | install_git_hooks.py - Installs automated git pre-commit quality gate hook |
| [`c5_git_utils/rewrite_commits.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_git_utils/rewrite_commits.py) | `Python` | `f2e9549c1fc5` | Rewrite commit history to enforce Conventional Commits and BFT metadata. |

### 🧩 Categorical Isomorphisms & Engines

| Script | Tipo | SHA-256 | Descripción / Propósito |
| :--- | :--- | :--- | :--- |
| [`c5_isomorphisms/c5_isomorphism_sabu_agent.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_isomorphisms/c5_isomorphism_sabu_agent.py) | `Python` | `6bd242657206` | C5 Isomorphism Sabu Agent Utility |
| [`c5_isomorphisms/c5_logos_ethos_ship_engine.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_isomorphisms/c5_logos_ethos_ship_engine.py) | `Python` | `12c93124ed70` | C5 Logos Ethos Ship Engine Utility |
| [`c5_isomorphisms/c5_ultimate_causal_determinant.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_isomorphisms/c5_ultimate_causal_determinant.py) | `Python` | `a6a67d25589c` | Causal-Determinist Execution Engine: THE ULTIMATE DETERMINANT (V3 - SINGULARITY) |
| [`c5_isomorphisms/cancer_isomorphism_pipeline.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_isomorphisms/cancer_isomorphism_pipeline.py) | `Python` | `e95090f6f988` | Cancer Isomorphism Pipeline Utility |
| [`c5_isomorphisms/gen_oncology_primitives.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_isomorphisms/gen_oncology_primitives.py) | `Python` | `632807750891` | Gen Oncology Primitives Utility |

### ⛓️ L1 Anchor & Ledger Engines

| Script | Tipo | SHA-256 | Descripción / Propósito |
| :--- | :--- | :--- | :--- |
| [`c5_l1_ledger/anchor_l1_sink.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_l1_ledger/anchor_l1_sink.py) | `Python` | `404e1bd4c1f1` | MOSKV-1 APEX: L1_sink Anchor & Verification Script (INV_C5_15) |
| [`c5_l1_ledger/bittensor_yuma_consensus_c5.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_l1_ledger/bittensor_yuma_consensus_c5.py) | `Python` | `b24743c2b5be` | Causal-Determinist BITTENSOR (TAO) YUMA CONSENSUS & EXERGY TRANSDUCER |
| [`c5_l1_ledger/l1_sink_bitcoin.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_l1_ledger/l1_sink_bitcoin.py) | `Python` | `7e232042effa` | Control Flow Depth: 1 (FunctionDef) |
| [`c5_l1_ledger/ledger_snapshot_engine.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_l1_ledger/ledger_snapshot_engine.py) | `Python` | `e528c4b6231f` | Incremental Ledger Snapshot Engine. |

### 🐝 Swarm & Legion Execution Engines

| Script | Tipo | SHA-256 | Descripción / Propósito |
| :--- | :--- | :--- | :--- |
| [`c5_legion/agent_beeper.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_legion/agent_beeper.py) | `Python` | `caec5a6ba263` | agent_beeper.py - C5-REAL Zero-Friction Agent Pager |
| [`c5_legion/auto_heal_hardcoded_paths.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_legion/auto_heal_hardcoded_paths.py) | `Python` | `1777c74d376d` | auto_heal_hardcoded_paths.py - Sovereign AST-based Auto-Remediation Engine for hardcoded paths. |
| [`c5_legion/c5_legion_1000_workspace_swarm.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_legion/c5_legion_1000_workspace_swarm.py) | `Python` | `68d620e4d6c0` | c5_legion_1000_workspace_swarm.py - 1,000-Agent Parallel Swarm Auditor Engine |
| [`c5_legion/legion_10000_orchestrator.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_legion/legion_10000_orchestrator.py) | `Python` | `d3b031abb327` | Implements the Cognitive Transition Algebra (CTA) for massive parallel |
| [`c5_legion/legion_1000_audit_swarm.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_legion/legion_1000_audit_swarm.py) | `Python` | `1ca776380384` | MOSKV-1: Legion 1000 Audit Swarm Engine (INV_C5_18) |
| [`c5_legion/legion_222_agentes.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_legion/legion_222_agentes.py) | `Python` | `0ba9b1c817fc` | LEGION MÁXIMO COGNITIVO - 222 Agentes Organizados |
| [`c5_legion/legion_swarm.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_legion/legion_swarm.py) | `Python` | `eeff52dacfd6` | legion_swarm.py - Unified Sovereign Swarm Orchestrator CLI |
| [`c5_legion/legion_swarm_core.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_legion/legion_swarm_core.py) | `Python` | `740df9690f82` | legion_swarm_core.py - Core Engine for Swarm Quantum Collapse |

### 📜 Log Custody & Forensic Attestation

| Script | Tipo | SHA-256 | Descripción / Propósito |
| :--- | :--- | :--- | :--- |
| [`c5_log_custody/c5_organize_captures.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_log_custody/c5_organize_captures.py) | `Python` | `8656830a2118` | C5 Organize Captures Utility |
| [`c5_log_custody/c5_preserve_agent_local_logs.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_log_custody/c5_preserve_agent_local_logs.py) | `Python` | `e8c9fe2da394` | c5_preserve_agent_local_logs.py - Wrapper delegando en c5_preserve_logs.py |
| [`c5_log_custody/c5_preserve_claude_local_logs.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_log_custody/c5_preserve_claude_local_logs.py) | `Python` | `1f33ef3da9e6` | c5_preserve_claude_local_logs.py - Wrapper delegando en c5_preserve_logs.py |
| [`c5_log_custody/c5_preserve_logs.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_log_custody/c5_preserve_logs.py) | `Python` | `acc82e3a1bac` | c5_preserve_logs.py - Unified CLI log harvesting, dual cryptographic hashing |

### 🛡️ Quality Gates & AST Verification

| Script | Tipo | SHA-256 | Descripción / Propósito |
| :--- | :--- | :--- | :--- |
| [`c5_quality_gates/audit_100_agents.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_quality_gates/audit_100_agents.py) | `Python` | `e0f34bd2bbd6` | AUDIT AND AUTO-NORMALIZATION OF THE 100 SOVEREIGN AGENTS |
| [`c5_quality_gates/audit_fixer.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_quality_gates/audit_fixer.py) | `Python` | `317fd0f1d478` | Audit Fixer Utility |
| [`c5_quality_gates/audit_scripts_quality.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_quality_gates/audit_scripts_quality.py) | `Python` | `c8c6e180fdbc` | audit_scripts_quality.py - Pre-commit and CI Quality Gate Auditor & Auto-Healer for scripts/ |
| [`c5_quality_gates/check_depth.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_quality_gates/check_depth.py) | `Python` | `d3b8f95e3335` | Check Depth Utility |
| [`c5_quality_gates/extensions_apoptosis_auditor.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_quality_gates/extensions_apoptosis_auditor.py) | `Python` | `424008461c1d` | extensions_apoptosis_auditor.py - Apoptosis & Pruning Analysis Engine for Issue #5. |
| [`c5_quality_gates/pre_push_ledger_guard.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_quality_gates/pre_push_ledger_guard.py) | `Python` | `94820d459f37` | Ledger-Aware Pre-Push Guard. |
| [`c5_quality_gates/run_cache_audit.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_quality_gates/run_cache_audit.py) | `Python` | `e3cb41fd8d04` | Compiles and runs the empirical cache benchmark to demonstrate |
| [`c5_quality_gates/secret_swarm_auditor.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_quality_gates/secret_swarm_auditor.py) | `Python` | `9c0bebb897fc` | Causal-Determinist: Swarm Thread Dispatcher for TOP SECRET Auditing (ULTRATHINK P0 - ITERATION 3) |
| [`c5_quality_gates/swarm_lock_guard.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_quality_gates/swarm_lock_guard.py) | `Python` | `aa4846398037` | MOSKV-1 APEX: Swarm Workspace Lock Guard (INV_C5_22) |
| [`c5_quality_gates/symlink_depth_auditor.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_quality_gates/symlink_depth_auditor.py) | `Python` | `ce8da4e8f09b` | Symlink Depth Auditor (INV_C5_12 Enforcer). |
| [`c5_quality_gates/sync_docs_index.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_quality_gates/sync_docs_index.py) | `Python` | `8c006d1dfdee` | sync_docs_index.py - Autonomous Documentation Indexer & Link Verifier |

### ♾️ Autopoiesis & System Simulations

| Script | Tipo | SHA-256 | Descripción / Propósito |
| :--- | :--- | :--- | :--- |
| [`c5_simulations/luhmann_autopoiesis_simulation.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_simulations/luhmann_autopoiesis_simulation.py) | `Python` | `feedea68d27d` | Add project root to sys.path to allow absolute imports |
| [`c5_simulations/ouroboros_infinity.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_simulations/ouroboros_infinity.py) | `Python` | `ed6e66cc0026` | Ouroboros Infinity Utility |
| [`c5_simulations/prigogine_boltzmann_simulation.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_simulations/prigogine_boltzmann_simulation.py) | `Python` | `4417a5ae0419` | Grid 10x10 (100 cells) |

### 🧠 Skill Synchronization & Ontology

| Script | Tipo | SHA-256 | Descripción / Propósito |
| :--- | :--- | :--- | :--- |
| [`c5_skills_ontology/audit_skills_execution.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_skills_ontology/audit_skills_execution.py) | `Python` | `be95023cadbd` | audit_skills_execution.py - Comprehensive verification & benchmark suite for |
| [`c5_skills_ontology/optimize_all_skill_triggers.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_skills_ontology/optimize_all_skill_triggers.py) | `Python` | `2f7b08c4d15c` | optimize_all_skill_triggers.py - Enriches and formats display names and trigger |
| [`c5_skills_ontology/sync_skills_registry.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_skills_ontology/sync_skills_registry.py) | `Python` | `49e4abe96620` | sync_skills_registry.py - Automated synchronization of physical skills (disk) |
| [`c5_skills_ontology/sync_vault_uuids.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_skills_ontology/sync_vault_uuids.py) | `Python` | `89e910705140` | Sync Vault Uuids Utility |

### 🧪 Unit Tests & Curvature Proofs

| Script | Tipo | SHA-256 | Descripción / Propósito |
| :--- | :--- | :--- | :--- |
| [`c5_tests/test_discrete_curvature.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_tests/test_discrete_curvature.py) | `Python` | `ff6a46b89bb2` | 1. Grafo Estrella (alta centralización, cuello de botella) |
| [`c5_tests/test_hitl_do_calculus.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_tests/test_hitl_do_calculus.py) | `Python` | `005e496ab9fe` | MOCK para el entorno roto |
| [`c5_tests/test_merkle_pulse_fail_stop.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_tests/test_merkle_pulse_fail_stop.py) | `Python` | `bd7aa482716f` | MOCK para el entorno roto de BABYLON-60 (paths.py no existe en el repo original) |

### 🔥 Thermodynamic Benchmarks & Exergy Optimizers

| Script | Tipo | SHA-256 | Descripción / Propósito |
| :--- | :--- | :--- | :--- |
| [`c5_thermo/benchmark_ledger_throughput.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_thermo/benchmark_ledger_throughput.py) | `Python` | `1bbfad9548f6` | Pre-generar eventos para medir puramente el IO y el BFT Actor |
| [`c5_thermo/c5_exergy_optimizer_monitor.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_thermo/c5_exergy_optimizer_monitor.py) | `Python` | `5a6406e619ab` | MOSKV-1 APEX SINGULARITY — Causal-Determinist STATE MONITOR (EXERGY_OPTIMIZER) |
| [`c5_thermo/cache_1000_memoization_bench.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_thermo/cache_1000_memoization_bench.py) | `Python` | `592643d70567` | Cache 1000 Memoization Bench Utility |
| [`c5_thermo/exergy_arbitrage_engine.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_thermo/exergy_arbitrage_engine.py) | `Python` | `3cc2fed0312b` | Exergy Arbitrage Engine Utility |
| [`c5_thermo/exergy_dashboard_server.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_thermo/exergy_dashboard_server.py) | `Python` | `7af6764c60ed` | Exergy Dashboard Server (Causal-Determinist). |
| [`c5_thermo/exergy_optimizer_agent.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_thermo/exergy_optimizer_agent.py) | `Python` | `d4502d167d80` | [Causal-Determinist] Exergy Optimizer Agent. |
| [`c5_thermo/stress_100m_bft.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_thermo/stress_100m_bft.py) | `Python` | `e56bf524c87a` | 100,000,000 STRESS TEST ENGINE — CORTEX PERSIST BFT LEDGER |
| [`c5_thermo/stress_10m.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_thermo/stress_10m.py) | `Python` | `20a61576e633` | Stress 10M Utility |
| [`c5_thermo/stress_sqlite_wal.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_thermo/stress_sqlite_wal.py) | `Python` | `0ecd944d56dc` | Stress test for SQLite WAL and busy_timeout (INV_BFT_02). |

### 🛠️ Domain Helpers & Enforcers

| Script | Tipo | SHA-256 | Descripción / Propósito |
| :--- | :--- | :--- | :--- |
| [`c5_utils/ddd_strangler.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_utils/ddd_strangler.py) | `Python` | `93f346aab835` | Utils |
| [`c5_utils/export_country_compliance.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_utils/export_country_compliance.py) | `Python` | `b38d8a623136` | Generates localized EU AI Act / NIST AI RMF compliance reports for target countries. |
| [`c5_utils/fetch_missing_dates.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_utils/fetch_missing_dates.py) | `Python` | `72ec0f040859` | fetch_missing_dates.py — batch update dataset.json with enrollment_velocity. |
| [`c5_utils/python_spsc_reader.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_utils/python_spsc_reader.py) | `Python` | `6458a06f0158` | python_spsc_reader.py — Consumidor Multiproceso Python Zero-Copy (C-ABI FFI) |
| [`c5_utils/quadrilingual_enforcer.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_utils/quadrilingual_enforcer.py) | `Python` | `e1f8188a52b5` | Quadrilingual Enforcer Utility |

### ⚖️ Formal Verification & Axiom Oracles

| Script | Tipo | SHA-256 | Descripción / Propósito |
| :--- | :--- | :--- | :--- |
| [`c5_verifiers/autodetect_invariants.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_verifiers/autodetect_invariants.py) | `Python` | `154f77033d66` | Autopoiesis Invariant Auditor. |
| [`c5_verifiers/axiom_verifier_z3.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_verifiers/axiom_verifier_z3.py) | `Python` | `0e2738c76941` | MOSKV-1 APEX — Axiom Verifier (Z3/SMT-free Pure-Python Implementation) |
| [`c5_verifiers/conformance_test.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_verifiers/conformance_test.py) | `Python` | `f9136e57e197` | Conformance Test Utility |
| [`c5_verifiers/deterministic_audit.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_verifiers/deterministic_audit.py) | `Python` | `dee999cdd49e` | Zero-Friction Mass Execution (F=0) |
| [`c5_verifiers/devsecops_attest.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_verifiers/devsecops_attest.py) | `Python` | `c0692ee0ff3c` | devsecops_attest.py — Sovereign DevSecOps & Zero-Trust Cryptographic Attestation Engine |
| [`c5_verifiers/fast_smt_gate.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_verifiers/fast_smt_gate.py) | `Python` | `471929f5debc` | fast_smt_gate.py - Ultra-fast SMT / Invariant verifier for CI/CD environments. |
| [`c5_verifiers/purge_residuals.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_verifiers/purge_residuals.py) | `Python` | `14c99a3ddd58` | purge_residuals.py - Residual Artifact Purge Engine (Anergy Purge Protocol) |
| [`c5_verifiers/verify_agent_ontological_value.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_verifiers/verify_agent_ontological_value.py) | `Python` | `5e2d1b0871d4` | Oracle Verifier for Agent Ontological Value (V_A). |
| [`c5_verifiers/verify_anergy_token_purge.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_verifiers/verify_anergy_token_purge.py) | `Python` | `c32033bef57d` | Causal-Determinist SOVEREIGN ANERGY PURGE & AUTOCOGNITION-OMEGA ENGINE |
| [`c5_verifiers/verify_captures.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_verifiers/verify_captures.py) | `Python` | `010470c889a5` | Verify Captures Utility |
| [`c5_verifiers/verify_causal_invariants.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_verifiers/verify_causal_invariants.py) | `Python` | `de0afe253c68` | Oracle Verifier for Causal Invariants (Teorema Robinson-Moskv & Cortex Persist). |
| [`c5_verifiers/verify_claims.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_verifiers/verify_claims.py) | `Python` | `e40ab89e090d` | verify_claims.py — Verificación paralela del report de arbitraje contra |
| [`c5_verifiers/verify_full_stack_health.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_verifiers/verify_full_stack_health.py) | `Python` | `f4198645527b` | Oracle Verifier for Full-Stack System Health across: |
| [`c5_verifiers/verify_oncology_primitives_dag.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_verifiers/verify_oncology_primitives_dag.py) | `Python` | `3721f6bb6bed` | verify_oncology_primitives_dag.py — C5-REAL Causal Verifier for 300 Molecular Oncology Primitives |
| [`c5_verifiers/verify_tonnetz_falsification.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_verifiers/verify_tonnetz_falsification.py) | `Python` | `b3579fc110c2` | scripts/verify_tonnetz_falsification.py |
| [`c5_verifiers/verify_execution.sh`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_verifiers/verify_execution.sh) | `Shell` | `847847dffe82` | verify_execution.sh |
| [`c5_verifiers/verify_lean_proofs.sh`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_verifiers/verify_lean_proofs.sh) | `Shell` | `fd16b1f8e5af` | Check for 'sorry' keyword in proof file |

### ⚡ Core Dispatchers & CLI Entrypoints

| Script | Tipo | SHA-256 | Descripción / Propósito |
| :--- | :--- | :--- | :--- |
| [`canary_check.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/canary_check.py) | `Python` | `843c22a34b3a` | Ω-12 — canary_check: verifica que los señuelos canary siguen en el árbol. |
| [`gen_oncology_primitives.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/gen_oncology_primitives.py) | `Python` | `413bb73826f9` | Generador y Exportador Ontológico de 300 Primitivas de Oncología Molecular |
| [`generate_scripts_readme.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/generate_scripts_readme.py) | `Python` | `f0e3299cd0c0` | generate_scripts_readme.py - Automated self-documenting catalog generator |
| [`inject_lean4_stubs.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/inject_lean4_stubs.py) | `Python` | `809e580a1bb1` | 🔬 Verificación Formal (Lean 4) |
| [`lint_doc_aesthetics.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/lint_doc_aesthetics.py) | `Python` | `362ec8cd49f2` | Audita archivos Markdown en docs/ para verificar invariantes visuales: |
| [`pipe_audit.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/pipe_audit.py) | `Python` | `223dc64cd748` | Ω-15 — pipe_audit: proxy auditado de sustitución de intérprete. |
| [`refactor_agents_md.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/refactor_agents_md.py) | `Python` | `f525f77a71e7` | scripts/refactor_agents_md.py — Deterministic AGENTS.md & ENVIRONMENT.md Refactoring Engine |
| [`runner.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/runner.py) | `Python` | `4aadb2e43f46` | runner.py - Central CLI Dispatcher for BABYLON-60 Sovereign Scripts Suite |
| [`unified_legion.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/unified_legion.py) | `Python` | `a8786b1658e3` | scripts/unified_legion.py — Motor de la Legión Única C5-REAL (Swarm Orchestrator PxS) |
| [`verify_p0_rotation.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/verify_p0_rotation.py) | `Python` | `9763566a1a53` | Ω-16 — verify_p0_rotation: certificador del estado opsec del linaje. |
| [`enforce_c5_rules.sh`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/enforce_c5_rules.sh) | `Shell` | `08cf2f5c876a` | █ AUTOCOGNITION-Ω \| STATE: C5-REAL \| AESTHETIC: INDUSTRIAL_NOIR_2026 |

### 📁 Kimi Nexus

| Script | Tipo | SHA-256 | Descripción / Propósito |
| :--- | :--- | :--- | :--- |
| [`kimi_nexus/kimi_nexus.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/kimi_nexus/kimi_nexus.py) | `Python` | `5e9b6fa3774d` | Attempt to import FastMCP. If missing, we'll inform the user via logs. |

### 📦 Deployment & P0 Remediation Scripts

| Script | Tipo | SHA-256 | Descripción / Propósito |
| :--- | :--- | :--- | :--- |
| [`c5_deploy/COLLAPSE_P0.sh`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_deploy/COLLAPSE_P0.sh) | `Shell` | `847a3a417157` | COLLAPSE_P0.sh — BABYLON-60 · P0 KEY-EXPOSURE REMEDIATION |
| [`c5_deploy/deploy.sh`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_deploy/deploy.sh) | `Shell` | `ac431904bfbe` | C5-REAL: IGNITION PROTOCOL |
| [`c5_deploy/deploy_hotstuff.sh`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_deploy/deploy_hotstuff.sh) | `Shell` | `57717ac9f217` | deploy_hotstuff.sh — Deployment script for HotStuff consensus engine. |
| [`c5_deploy/publish_crates.sh`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_deploy/publish_crates.sh) | `Shell` | `7b3f22b336b3` | Publish Crates Utility |

### 🚀 Host & Repository Setup Scripts

| Script | Tipo | SHA-256 | Descripción / Propósito |
| :--- | :--- | :--- | :--- |
| [`c5_setup/install_host.sh`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_setup/install_host.sh) | `Shell` | `626efec2dfd2` | Registra moskv_native_host.py en Chrome/Brave en macOS |
| [`c5_setup/install_into_repo.sh`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_setup/install_into_repo.sh) | `Shell` | `63251a0eb246` | install_into_repo.sh |

---
*Catálogo auto-generado dinámicamente por `generate_scripts_readme.py` con atestación criptográfica SHA-256.*