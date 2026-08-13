# ⚡ BABYLON-60 Sovereign Scripts Suite — Immutable Script Kernel (ISK)

> **Directorio de Automatización, Enjambres BFT, Calidad AST, Atestación SHA-256 y Preservación de Logs**  
> **Estándar:** C5-REAL | **Total Scripts:** 126 Python + 10 Shell | **Shebang Compliance:** 100.0%

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

## 📂 Catálogo Taxonómico por Dominios C5 (Atestación SHA3-256)

### 📁 Babylon60

| Script | Tipo | SHA3-256 | Descripción / Propósito |
| :--- | :--- | :--- | :--- |
| [`babylon60/oncology_primitives.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/babylon60/oncology_primitives.py) | `Python` | `deac167d7c82` | CORTEX / BABYLON-60 :: oncology_primitives |

### 🎨 Assets & Multimodal Generators

| Script | Tipo | SHA3-256 | Descripción / Propósito |
| :--- | :--- | :--- | :--- |
| [`c5_assets/gen_blip_assets.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_assets/gen_blip_assets.py) | `Python` | `b410d0bd405e` | Onda cuadrada |
| [`c5_assets/gen_voice_assets.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_assets/gen_voice_assets.py) | `Python` | `71370eb1320e` | Textos extraídos de GoedelBrosComposition.tsx |
| [`c5_assets/thermo_wallpaper.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_assets/thermo_wallpaper.py) | `Python` | `369756116a28` | Thermo Wallpaper Utility |

### 🎯 Entropy & Calibration Utilities

| Script | Tipo | SHA3-256 | Descripción / Propósito |
| :--- | :--- | :--- | :--- |
| [`c5_calibrations/calibrate_aphairesis.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_calibrations/calibrate_aphairesis.py) | `Python` | `ac0dd0a8ae6e` | calibrate_aphairesis.py — Generador de constantes axiomáticas para thermodynamics.rs (Capa 2) |
| [`c5_calibrations/calibrate_popperian_entropy.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_calibrations/calibrate_popperian_entropy.py) | `Python` | `b749c7d449e3` | [Causal-Determinist] Empirical Calibration Tool for Popperian Shannon Entropy Thresholds. |
| [`c5_calibrations/topological_calibration.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_calibrations/topological_calibration.py) | `Python` | `d7db79ee4129` | C5-REAL TOPOLOGICAL CALIBRATION PIPELINE — BABYLON-60 (Capa 2 Aphairesis) |

### ⚡ Centuria & Video Swarm Commanders

| Script | Tipo | SHA3-256 | Descripción / Propósito |
| :--- | :--- | :--- | :--- |
| [`c5_centuria/centuria_swarm_commander.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_centuria/centuria_swarm_commander.py) | `Python` | `d5f2da67a80b` | Centuria Swarm Commander Utility |
| [`c5_centuria/centuria_swarm_runner.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_centuria/centuria_swarm_runner.py) | `Python` | `818eb762f574` | Ensure root importability |
| [`c5_centuria/remotion_swarm_orchestrator.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_centuria/remotion_swarm_orchestrator.py) | `Python` | `c2baf7b03456` | Enforces: |

### 🖥️ CLI Tools & Native Hosts

| Script | Tipo | SHA3-256 | Descripción / Propósito |
| :--- | :--- | :--- | :--- |
| [`c5_cli/babylon_mail_cli.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_cli/babylon_mail_cli.py) | `Python` | `898105df2cc7` | BABYLONMAIL CLI & SUBAGENT INTERFACE |
| [`c5_cli/codex_virtual_hud.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_cli/codex_virtual_hud.py) | `Python` | `feef27f04d3b` | Codex Virtual Hud Utility |
| [`c5_cli/moskv_native_host.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_cli/moskv_native_host.py) | `Python` | `38bc450b229c` | MOSKV-1 APEX: Native Messaging Transducer (INV_C5_18 / INV_C5_THERMO_VALVE) |
| [`c5_cli/opsec_sentinel_c5.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_cli/opsec_sentinel_c5.py) | `Python` | `234a7f0f8ae8` | Opsec Sentinel C5 Utility |
| [`c5_cli/pty_tmux_bridge.sh`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_cli/pty_tmux_bridge.sh) | `Shell` | `26f72663e5fb` | 🛡️ TMUX-PTY-Bridge-OMEGA (C5-REAL v2.0) |

### 🌀 Cortex Memory & Auto-Consolidation

| Script | Tipo | SHA3-256 | Descripción / Propósito |
| :--- | :--- | :--- | :--- |
| [`c5_cortex/autoconsolidate.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_cortex/autoconsolidate.py) | `Python` | `ce8b2dcc235a` | Delete old entries, respecting INV_BFT_04 semantics |
| [`c5_cortex/bootstrap_cortex_memory.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_cortex/bootstrap_cortex_memory.py) | `Python` | `c74a843b1c6f` | Bootstrap Cortex Memory Utility |
| [`c5_cortex/consolidate_babylon_vault.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_cortex/consolidate_babylon_vault.py) | `Python` | `63153f75c1ef` | Causal-Determinist SOVEREIGN CONSOLIDATION PROTOCOL — BABYLON-60 MEMORY VAULT |
| [`c5_cortex/consolidate_dbs.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_cortex/consolidate_dbs.py) | `Python` | `f9d6fc45116a` | Consolidación BFT (Erradicación del Antipatrón de Dispersión SQLite) |
| [`c5_cortex/cortex_labs_poc.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_cortex/cortex_labs_poc.py) | `Python` | `7a748013aa8b` | Prueba de Concepto (PoC) Autónoma: Extracción Causal de Google Labs FX. |
| [`c5_cortex/cortex_objectives_transducer.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_cortex/cortex_objectives_transducer.py) | `Python` | `6e97f78d3195` | Cortex Objectives Transducer Utility |

### 🔬 C5 Demos & Proofs of Concept

| Script | Tipo | SHA3-256 | Descripción / Propósito |
| :--- | :--- | :--- | :--- |
| [`c5_demos/demo_exergy_poc.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_demos/demo_exergy_poc.py) | `Python` | `25b38eb08c2c` | [Causal-Determinist] Exergy Optimizer Agent Proof of Concept. |
| [`c5_demos/demo_logos_ethos_ship.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_demos/demo_logos_ethos_ship.py) | `Python` | `6c596ddbbe6f` | Demo Logos Ethos Ship Utility |
| [`c5_demos/poc_active_inference_efe.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_demos/poc_active_inference_efe.py) | `Python` | `d248422e45e7` | poc_active_inference_efe.py - PoC 4: Friston Active Inference Free Energy Scheduler |
| [`c5_demos/poc_axiom4_disintegration.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_demos/poc_axiom4_disintegration.py) | `Python` | `6b3013215809` | poc_axiom4_disintegration.py — Proof of Concept: Axiom 4 Bayesian Disintegration & Non-Hallucination |
| [`c5_demos/poc_browser_pipeline.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_demos/poc_browser_pipeline.py) | `Python` | `1b868cc3e1d4` | Poc Browser Pipeline Utility |
| [`c5_demos/poc_categorical_hallucination.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_demos/poc_categorical_hallucination.py) | `Python` | `8e7ce3e2fc6e` | poc_categorical_hallucination.py - PoC 2: Category-Theoretic Hallucination Audit Engine |
| [`c5_demos/poc_causal_hitl_agent.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_demos/poc_causal_hitl_agent.py) | `Python` | `86f951fdc476` | SOTA Proof of Concept (PoC): Operational Worker with Cryptographic Causal HITL Gate |
| [`c5_demos/poc_cta_comonad.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_demos/poc_cta_comonad.py) | `Python` | `a6b88cfa4ab2` | poc_cta_comonad.py - PoC 6: Event-Sourced Comonadic State Machine (CTA Algebra) |
| [`c5_demos/poc_epistemic_extinction.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_demos/poc_epistemic_extinction.py) | `Python` | `fc15baf1f2e2` | poc_epistemic_extinction.py - PoC 3: Epistemic Extinction & Dimensionality Reduction |
| [`c5_demos/poc_eu_ai_act_audit.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_demos/poc_eu_ai_act_audit.py) | `Python` | `b6ced8e27843` | poc_eu_ai_act_audit.py - PoC 5: Automated EU AI Act Risk & Compliance Auditor |
| [`c5_demos/poc_f60_time_domain.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_demos/poc_f60_time_domain.py) | `Python` | `fd737b94f127` | 32-byte hash commitment |
| [`c5_demos/poc_fast_failure_guard.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_demos/poc_fast_failure_guard.py) | `Python` | `9436741747af` | Poc Fast Failure Guard Utility |
| [`c5_demos/poc_graph_isomorphism_wl.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_demos/poc_graph_isomorphism_wl.py) | `Python` | `2edab23daed5` | [Causal-Determinist] Step 1 Proof of Concept: Graph Isomorphism WL Pre-Filter (INV_C5_28). |
| [`c5_demos/poc_logop_veto.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_demos/poc_logop_veto.py) | `Python` | `a0fad25be0df` | Ensure the module can be imported |
| [`c5_demos/poc_tonnetz_oversight.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_demos/poc_tonnetz_oversight.py) | `Python` | `3effe0d35dd2` | poc_tonnetz_oversight.py — Proof of Concept: Tonnetz Harmonic Oversight & Audio Engine |
| [`c5_demos/poc_two_tier_planner_worker.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_demos/poc_two_tier_planner_worker.py) | `Python` | `381494d74765` | MOSKV-1 APEX – Iteración 4 del PoC |
| [`c5_demos/poc_xenharmonic_swarm.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_demos/poc_xenharmonic_swarm.py) | `Python` | `fdf251e4caf6` | poc_xenharmonic_swarm.py - PoC 1: Swarm-Guided Xenharmonic Tuning Engine |
| [`c5_demos/run_commercial_bft.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_demos/run_commercial_bft.py) | `Python` | `b8343e7ee0d1` | Run Commercial Bft Utility |
| [`c5_demos/run_hero_demo.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_demos/run_hero_demo.py) | `Python` | `6c8eff684e07` | Simulates the live 60-second B2B Enterprise / Investor Demo in the terminal: |

### 🔧 Git Hooks & Commit Utilities

| Script | Tipo | SHA3-256 | Descripción / Propósito |
| :--- | :--- | :--- | :--- |
| [`c5_git_utils/commit_polisher.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_git_utils/commit_polisher.py) | `Python` | `b066567ccddf` | Continuous Commit Polisher Daemon. |
| [`c5_git_utils/install_git_hooks.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_git_utils/install_git_hooks.py) | `Python` | `e35fd1d51b9a` | install_git_hooks.py - Installs automated git pre-commit quality gate hook |
| [`c5_git_utils/rewrite_commits.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_git_utils/rewrite_commits.py) | `Python` | `979417bb780d` | Rewrite commit history to enforce Conventional Commits and BFT metadata. |

### 🧩 Categorical Isomorphisms & Engines

| Script | Tipo | SHA3-256 | Descripción / Propósito |
| :--- | :--- | :--- | :--- |
| [`c5_isomorphisms/c5_isomorphism_sabu_agent.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_isomorphisms/c5_isomorphism_sabu_agent.py) | `Python` | `194453b58c04` | C5 Isomorphism Sabu Agent Utility |
| [`c5_isomorphisms/c5_logos_ethos_ship_engine.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_isomorphisms/c5_logos_ethos_ship_engine.py) | `Python` | `a67ac83ddf0a` | C5 Logos Ethos Ship Engine Utility |
| [`c5_isomorphisms/c5_ultimate_causal_determinant.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_isomorphisms/c5_ultimate_causal_determinant.py) | `Python` | `0934e6c6a0e7` | Causal-Determinist Execution Engine: THE ULTIMATE DETERMINANT (V3 - SINGULARITY) |
| [`c5_isomorphisms/cancer_isomorphism_pipeline.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_isomorphisms/cancer_isomorphism_pipeline.py) | `Python` | `46f708ad2bbf` | Cancer Isomorphism Pipeline Utility |
| [`c5_isomorphisms/gen_oncology_primitives.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_isomorphisms/gen_oncology_primitives.py) | `Python` | `485c77934b2a` | Gen Oncology Primitives Utility |

### ⛓️ L1 Anchor & Ledger Engines

| Script | Tipo | SHA3-256 | Descripción / Propósito |
| :--- | :--- | :--- | :--- |
| [`c5_l1_ledger/anchor_l1_sink.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_l1_ledger/anchor_l1_sink.py) | `Python` | `02393235465f` | MOSKV-1 APEX: L1_sink Anchor & Verification Script (INV_C5_15) |
| [`c5_l1_ledger/bittensor_yuma_consensus_c5.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_l1_ledger/bittensor_yuma_consensus_c5.py) | `Python` | `bee3fd94b943` | Causal-Determinist BITTENSOR (TAO) YUMA CONSENSUS & EXERGY TRANSDUCER |
| [`c5_l1_ledger/l1_sink_bitcoin.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_l1_ledger/l1_sink_bitcoin.py) | `Python` | `e751b6d4e88f` | Control Flow Depth: 1 (FunctionDef) |
| [`c5_l1_ledger/ledger_snapshot_engine.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_l1_ledger/ledger_snapshot_engine.py) | `Python` | `d28c5f2e6520` | Incremental Ledger Snapshot Engine. |

### 🐝 Swarm & Legion Execution Engines

| Script | Tipo | SHA3-256 | Descripción / Propósito |
| :--- | :--- | :--- | :--- |
| [`c5_legion/agent_beeper.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_legion/agent_beeper.py) | `Python` | `33425b46e2af` | agent_beeper.py - C5-REAL Zero-Friction Agent Pager |
| [`c5_legion/auto_heal_hardcoded_paths.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_legion/auto_heal_hardcoded_paths.py) | `Python` | `fa8de2d67484` | auto_heal_hardcoded_paths.py - Sovereign AST-based Auto-Remediation Engine for hardcoded paths. |
| [`c5_legion/c5_legion_1000_workspace_swarm.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_legion/c5_legion_1000_workspace_swarm.py) | `Python` | `7bc9f12804a6` | c5_legion_1000_workspace_swarm.py - 1,000-Agent Parallel Swarm Auditor Engine |
| [`c5_legion/legion_10000_orchestrator.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_legion/legion_10000_orchestrator.py) | `Python` | `fce6adf2c84a` | Implements the Cognitive Transition Algebra (CTA) for massive parallel |
| [`c5_legion/legion_1000_audit_swarm.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_legion/legion_1000_audit_swarm.py) | `Python` | `259466861746` | MOSKV-1: Legion 1000 Audit Swarm Engine (INV_C5_18) |
| [`c5_legion/legion_21_agentes.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_legion/legion_21_agentes.py) | `Python` | `5bd515fec1bd` | MOSKV-1: Enjambre de 21 Agentes Paralelizados (C5-REAL Execution Engine) |
| [`c5_legion/legion_222_agentes.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_legion/legion_222_agentes.py) | `Python` | `50c21f916b0d` | LEGION MÁXIMO COGNITIVO - 222 Agentes Organizados |
| [`c5_legion/legion_swarm.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_legion/legion_swarm.py) | `Python` | `ebd798a50d5d` | legion_swarm.py - Unified Sovereign Swarm Orchestrator CLI |
| [`c5_legion/legion_swarm_core.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_legion/legion_swarm_core.py) | `Python` | `f80915c3eb86` | legion_swarm_core.py - Core Engine for Swarm Quantum Collapse |

### 📜 Log Custody & Forensic Attestation

| Script | Tipo | SHA3-256 | Descripción / Propósito |
| :--- | :--- | :--- | :--- |
| [`c5_log_custody/c5_organize_captures.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_log_custody/c5_organize_captures.py) | `Python` | `dbaa9d3e6344` | C5 Organize Captures Utility |
| [`c5_log_custody/c5_preserve_agent_local_logs.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_log_custody/c5_preserve_agent_local_logs.py) | `Python` | `3936411dad01` | c5_preserve_agent_local_logs.py - Wrapper delegando en c5_preserve_logs.py |
| [`c5_log_custody/c5_preserve_claude_local_logs.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_log_custody/c5_preserve_claude_local_logs.py) | `Python` | `606913512a4a` | c5_preserve_claude_local_logs.py - Wrapper delegando en c5_preserve_logs.py |
| [`c5_log_custody/c5_preserve_logs.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_log_custody/c5_preserve_logs.py) | `Python` | `ee71ad14a238` | c5_preserve_logs.py - Unified CLI log harvesting, dual cryptographic hashing |

### 🛡️ Quality Gates & AST Verification

| Script | Tipo | SHA3-256 | Descripción / Propósito |
| :--- | :--- | :--- | :--- |
| [`c5_quality_gates/audit_100_agents.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_quality_gates/audit_100_agents.py) | `Python` | `995b3dbcdaed` | AUDIT AND AUTO-NORMALIZATION OF THE 100 SOVEREIGN AGENTS |
| [`c5_quality_gates/audit_fixer.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_quality_gates/audit_fixer.py) | `Python` | `8e434463f25e` | Audit Fixer Utility |
| [`c5_quality_gates/audit_scripts_quality.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_quality_gates/audit_scripts_quality.py) | `Python` | `a13237b3aac5` | audit_scripts_quality.py - Pre-commit and CI Quality Gate Auditor & Auto-Healer for scripts/ |
| [`c5_quality_gates/check_depth.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_quality_gates/check_depth.py) | `Python` | `334b6be7c8cb` | Check Depth Utility |
| [`c5_quality_gates/extensions_apoptosis_auditor.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_quality_gates/extensions_apoptosis_auditor.py) | `Python` | `aa891d73ccb5` | extensions_apoptosis_auditor.py - Apoptosis & Pruning Analysis Engine for Issue #5. |
| [`c5_quality_gates/pre_push_ledger_guard.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_quality_gates/pre_push_ledger_guard.py) | `Python` | `b5ea46ed407e` | Ledger-Aware Pre-Push Guard. |
| [`c5_quality_gates/run_cache_audit.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_quality_gates/run_cache_audit.py) | `Python` | `b7d7b6c1c8ec` | Compiles and runs the empirical cache benchmark to demonstrate |
| [`c5_quality_gates/secret_swarm_auditor.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_quality_gates/secret_swarm_auditor.py) | `Python` | `1f3e496f0f94` | Causal-Determinist: Swarm Thread Dispatcher for TOP SECRET Auditing (ULTRATHINK P0 - ITERATION 3) |
| [`c5_quality_gates/swarm_lock_guard.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_quality_gates/swarm_lock_guard.py) | `Python` | `77dee64125a3` | MOSKV-1 APEX: Swarm Workspace Lock Guard (INV_C5_22) |
| [`c5_quality_gates/symlink_depth_auditor.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_quality_gates/symlink_depth_auditor.py) | `Python` | `150933d36465` | Symlink Depth Auditor (INV_C5_12 Enforcer). |
| [`c5_quality_gates/sync_docs_index.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_quality_gates/sync_docs_index.py) | `Python` | `8bf8ecf0bf12` | sync_docs_index.py - Autonomous Documentation Indexer & Link Verifier |
| [`c5_quality_gates/verify_distribution.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_quality_gates/verify_distribution.py) | `Python` | `d2dbc8cb1446` | C5-REAL Distribution Quality Gate: verify_distribution.py |

### ♾️ Autopoiesis & System Simulations

| Script | Tipo | SHA3-256 | Descripción / Propósito |
| :--- | :--- | :--- | :--- |
| [`c5_simulations/luhmann_autopoiesis_simulation.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_simulations/luhmann_autopoiesis_simulation.py) | `Python` | `e2ccbde04045` | Add project root to sys.path to allow absolute imports |
| [`c5_simulations/ouroboros_infinity.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_simulations/ouroboros_infinity.py) | `Python` | `c5665372960c` | Ouroboros Infinity Utility |
| [`c5_simulations/prigogine_boltzmann_simulation.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_simulations/prigogine_boltzmann_simulation.py) | `Python` | `044717904351` | Grid 10x10 (100 cells) |

### 🧠 Skill Synchronization & Ontology

| Script | Tipo | SHA3-256 | Descripción / Propósito |
| :--- | :--- | :--- | :--- |
| [`c5_skills_ontology/audit_skills_execution.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_skills_ontology/audit_skills_execution.py) | `Python` | `f650bbe54200` | audit_skills_execution.py - Comprehensive verification & benchmark suite for |
| [`c5_skills_ontology/optimize_all_skill_triggers.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_skills_ontology/optimize_all_skill_triggers.py) | `Python` | `89db083fbd34` | optimize_all_skill_triggers.py - Enriches and formats display names and trigger |
| [`c5_skills_ontology/sync_skills_registry.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_skills_ontology/sync_skills_registry.py) | `Python` | `b15d22d63ae2` | sync_skills_registry.py - Automated synchronization of physical skills (disk) |
| [`c5_skills_ontology/sync_vault_uuids.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_skills_ontology/sync_vault_uuids.py) | `Python` | `71561c349874` | Sync Vault Uuids Utility |

### 🧪 Unit Tests & Curvature Proofs

| Script | Tipo | SHA3-256 | Descripción / Propósito |
| :--- | :--- | :--- | :--- |
| [`c5_tests/test_discrete_curvature.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_tests/test_discrete_curvature.py) | `Python` | `9b7f88444892` | 1. Grafo Estrella (alta centralización, cuello de botella) |
| [`c5_tests/test_hitl_do_calculus.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_tests/test_hitl_do_calculus.py) | `Python` | `bea8cfb7db57` | MOCK para el entorno roto |
| [`c5_tests/test_merkle_pulse_fail_stop.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_tests/test_merkle_pulse_fail_stop.py) | `Python` | `92374ad5ab4e` | MOCK para el entorno roto de BABYLON-60 (paths.py no existe en el repo original) |

### 🔥 Thermodynamic Benchmarks & Exergy Optimizers

| Script | Tipo | SHA3-256 | Descripción / Propósito |
| :--- | :--- | :--- | :--- |
| [`c5_thermo/benchmark_ledger_throughput.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_thermo/benchmark_ledger_throughput.py) | `Python` | `2a60976b3c3e` | Pre-generar eventos para medir puramente el IO y el BFT Actor |
| [`c5_thermo/c5_exergy_optimizer_monitor.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_thermo/c5_exergy_optimizer_monitor.py) | `Python` | `853e3f7ef81c` | MOSKV-1 APEX SINGULARITY — Causal-Determinist STATE MONITOR (EXERGY_OPTIMIZER) |
| [`c5_thermo/cache_1000_memoization_bench.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_thermo/cache_1000_memoization_bench.py) | `Python` | `6ca5786bc13f` | Cache 1000 Memoization Bench Utility |
| [`c5_thermo/exergy_arbitrage_engine.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_thermo/exergy_arbitrage_engine.py) | `Python` | `c65f7aba1983` | Exergy Arbitrage Engine Utility |
| [`c5_thermo/exergy_dashboard_server.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_thermo/exergy_dashboard_server.py) | `Python` | `c4ae3427d446` | Exergy Dashboard Server (Causal-Determinist). |
| [`c5_thermo/exergy_optimizer_agent.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_thermo/exergy_optimizer_agent.py) | `Python` | `cafc71b6bcc4` | [Causal-Determinist] Exergy Optimizer Agent. |
| [`c5_thermo/stress_100m_bft.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_thermo/stress_100m_bft.py) | `Python` | `c7d68c858da0` | 100,000,000 STRESS TEST ENGINE — CORTEX PERSIST BFT LEDGER |
| [`c5_thermo/stress_10m.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_thermo/stress_10m.py) | `Python` | `9e7bf9890668` | Stress 10M Utility |
| [`c5_thermo/stress_sqlite_wal.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_thermo/stress_sqlite_wal.py) | `Python` | `65178e037bab` | Stress test for SQLite WAL and busy_timeout (INV_BFT_02). |

### 🛠️ Domain Helpers & Enforcers

| Script | Tipo | SHA3-256 | Descripción / Propósito |
| :--- | :--- | :--- | :--- |
| [`c5_utils/ddd_strangler.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_utils/ddd_strangler.py) | `Python` | `975ea8dac24b` | Utils |
| [`c5_utils/export_country_compliance.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_utils/export_country_compliance.py) | `Python` | `4990f9e54e21` | Generates localized EU AI Act / NIST AI RMF compliance reports for target countries. |
| [`c5_utils/fetch_missing_dates.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_utils/fetch_missing_dates.py) | `Python` | `e7b4a6d36bdf` | fetch_missing_dates.py — batch update dataset.json with enrollment_velocity. |
| [`c5_utils/python_spsc_reader.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_utils/python_spsc_reader.py) | `Python` | `d4efc03306eb` | python_spsc_reader.py — Consumidor Multiproceso Python Zero-Copy (C-ABI FFI) |
| [`c5_utils/quadrilingual_enforcer.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_utils/quadrilingual_enforcer.py) | `Python` | `2206fd22a86b` | Quadrilingual Enforcer Utility |

### ⚖️ Formal Verification & Axiom Oracles

| Script | Tipo | SHA3-256 | Descripción / Propósito |
| :--- | :--- | :--- | :--- |
| [`c5_verifiers/autodetect_invariants.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_verifiers/autodetect_invariants.py) | `Python` | `06050bdd0f05` | Autopoiesis Invariant Auditor. |
| [`c5_verifiers/axiom_verifier_z3.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_verifiers/axiom_verifier_z3.py) | `Python` | `39b6e7cbd8ad` | MOSKV-1 APEX — Axiom Verifier (Z3/SMT-free Pure-Python Implementation) |
| [`c5_verifiers/conformance_test.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_verifiers/conformance_test.py) | `Python` | `63af22cb2572` | Conformance Test Utility |
| [`c5_verifiers/deterministic_audit.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_verifiers/deterministic_audit.py) | `Python` | `dd3bad41d3a2` | Zero-Friction Mass Execution (F=0) |
| [`c5_verifiers/devsecops_attest.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_verifiers/devsecops_attest.py) | `Python` | `cc673910fcf1` | devsecops_attest.py — Sovereign DevSecOps & Zero-Trust Cryptographic Attestation Engine |
| [`c5_verifiers/fast_smt_gate.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_verifiers/fast_smt_gate.py) | `Python` | `38d7b4a89a6a` | fast_smt_gate.py - Ultra-fast SMT / Invariant verifier for CI/CD environments. |
| [`c5_verifiers/purge_residuals.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_verifiers/purge_residuals.py) | `Python` | `f21c054b6e65` | purge_residuals.py - Residual Artifact Purge Engine (Anergy Purge Protocol) |
| [`c5_verifiers/verify_agent_ontological_value.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_verifiers/verify_agent_ontological_value.py) | `Python` | `8f1db9c53c1c` | Oracle Verifier for Agent Ontological Value (V_A). |
| [`c5_verifiers/verify_anergy_token_purge.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_verifiers/verify_anergy_token_purge.py) | `Python` | `2d95d730278a` | Causal-Determinist SOVEREIGN ANERGY PURGE & AUTOCOGNITION-OMEGA ENGINE |
| [`c5_verifiers/verify_captures.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_verifiers/verify_captures.py) | `Python` | `1186fd310c60` | Verify Captures Utility |
| [`c5_verifiers/verify_causal_invariants.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_verifiers/verify_causal_invariants.py) | `Python` | `012b1240957f` | Oracle Verifier for Causal Invariants (Teorema Robinson-Moskv & Cortex Persist). |
| [`c5_verifiers/verify_claims.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_verifiers/verify_claims.py) | `Python` | `8237f47e118f` | verify_claims.py — Verificación paralela del report de arbitraje contra |
| [`c5_verifiers/verify_full_stack_health.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_verifiers/verify_full_stack_health.py) | `Python` | `06fe6b2b8b00` | Oracle Verifier for Full-Stack System Health across: |
| [`c5_verifiers/verify_oncology_primitives_dag.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_verifiers/verify_oncology_primitives_dag.py) | `Python` | `16055e765a62` | verify_oncology_primitives_dag.py — C5-REAL Causal Verifier for 300 Molecular Oncology Primitives |
| [`c5_verifiers/verify_tonnetz_falsification.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_verifiers/verify_tonnetz_falsification.py) | `Python` | `e5d4bd34ae90` | scripts/verify_tonnetz_falsification.py |
| [`c5_verifiers/verify_execution.sh`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_verifiers/verify_execution.sh) | `Shell` | `c075b209640b` | verify_execution.sh |
| [`c5_verifiers/verify_lean_proofs.sh`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_verifiers/verify_lean_proofs.sh) | `Shell` | `f1eea2de41fb` | Check for 'sorry' keyword in proof file |

### ⚡ Core Dispatchers & CLI Entrypoints

| Script | Tipo | SHA3-256 | Descripción / Propósito |
| :--- | :--- | :--- | :--- |
| [`canary_check.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/canary_check.py) | `Python` | `28f709e1bb26` | Ω-12 — canary_check: verifica que los señuelos canary siguen en el árbol. |
| [`gen_oncology_primitives.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/gen_oncology_primitives.py) | `Python` | `9f825d1057e3` | Generador y Exportador Ontológico de 300 Primitivas de Oncología Molecular |
| [`generate_scripts_readme.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/generate_scripts_readme.py) | `Python` | `53cd96c9e7d8` | generate_scripts_readme.py - Automated self-documenting catalog generator |
| [`inject_lean4_stubs.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/inject_lean4_stubs.py) | `Python` | `d5294a58cf86` | inject_lean4_stubs.py - Dynamic Lean 4 Stub Injector & Formal Proof Exporter |
| [`lint_doc_aesthetics.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/lint_doc_aesthetics.py) | `Python` | `5cc5235c9da3` | Audita archivos Markdown en docs/ para verificar invariantes visuales: |
| [`pipe_audit.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/pipe_audit.py) | `Python` | `c3dcd819e9ab` | Ω-15 — pipe_audit: proxy auditado de sustitución de intérprete. |
| [`refactor_agents_md.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/refactor_agents_md.py) | `Python` | `b8ad0e22786a` | scripts/refactor_agents_md.py — Deterministic AGENTS.md & ENVIRONMENT.md Refactoring Engine |
| [`runner.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/runner.py) | `Python` | `041ced863e50` | runner.py - Central CLI Dispatcher for BABYLON-60 Sovereign Scripts Suite |
| [`unified_legion.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/unified_legion.py) | `Python` | `8cbf279f42da` | scripts/unified_legion.py — Motor de la Legión Única C5-REAL (Swarm Orchestrator PxS) |
| [`verify_p0_rotation.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/verify_p0_rotation.py) | `Python` | `44aa581a13d4` | Ω-16 — verify_p0_rotation: certificador del estado opsec del linaje. |
| [`enforce_c5_rules.sh`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/enforce_c5_rules.sh) | `Shell` | `0961c5186b4e` | █ AUTOCOGNITION-Ω \| STATE: C5-REAL \| AESTHETIC: INDUSTRIAL_NOIR_2026 |

### 📁 Kimi Nexus

| Script | Tipo | SHA3-256 | Descripción / Propósito |
| :--- | :--- | :--- | :--- |
| [`kimi_nexus/kimi_nexus.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/kimi_nexus/kimi_nexus.py) | `Python` | `f06c851299a6` | Attempt to import FastMCP. If missing, we'll inform the user via logs. |

### 📦 Deployment & P0 Remediation Scripts

| Script | Tipo | SHA3-256 | Descripción / Propósito |
| :--- | :--- | :--- | :--- |
| [`c5_deploy/COLLAPSE_P0.sh`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_deploy/COLLAPSE_P0.sh) | `Shell` | `1951a942d4d8` | COLLAPSE_P0.sh — BABYLON-60 · P0 KEY-EXPOSURE REMEDIATION |
| [`c5_deploy/deploy.sh`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_deploy/deploy.sh) | `Shell` | `94c8b2c0780d` | C5-REAL: IGNITION PROTOCOL |
| [`c5_deploy/deploy_hotstuff.sh`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_deploy/deploy_hotstuff.sh) | `Shell` | `2f40652eeb00` | deploy_hotstuff.sh — Deployment script for HotStuff consensus engine. |
| [`c5_deploy/publish_crates.sh`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_deploy/publish_crates.sh) | `Shell` | `3325b7e8a380` | Publish Crates Utility |

### 🚀 Host & Repository Setup Scripts

| Script | Tipo | SHA3-256 | Descripción / Propósito |
| :--- | :--- | :--- | :--- |
| [`c5_setup/install_host.sh`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_setup/install_host.sh) | `Shell` | `71b8228b6009` | Registra moskv_native_host.py en Chrome/Brave en macOS |
| [`c5_setup/install_into_repo.sh`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_setup/install_into_repo.sh) | `Shell` | `05132535692a` | install_into_repo.sh |

---
*Catálogo auto-generado dinámicamente por `generate_scripts_readme.py` con atestación criptográfica SHA3-256.*