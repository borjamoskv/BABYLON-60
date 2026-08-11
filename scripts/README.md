# ⚡ BABYLON-60 Sovereign Scripts Suite

> **Directorio de Automatización, Enjambres BFT, Calidad AST y Preservación de Logs**  
> **Estándar:** C5-REAL | **Total Scripts:** 94 Python + 9 Shell | **Shebang Compliance:** 100.0%

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

## 📂 Catálogo Taxonómico por Dominios C5

### 🎨 Assets & Multimodal Generators

| Script | Tipo | Descripción / Propósito |
| :--- | :--- | :--- |
| [`c5_assets/gen_blip_assets.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_assets/gen_blip_assets.py) | `Python` | Onda cuadrada |
| [`c5_assets/gen_voice_assets.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_assets/gen_voice_assets.py) | `Python` | Textos extraídos de GoedelBrosComposition.tsx |
| [`c5_assets/thermo_wallpaper.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_assets/thermo_wallpaper.py) | `Python` | Thermo Wallpaper Utility |

### 🎯 Entropy & Calibration Utilities

| Script | Tipo | Descripción / Propósito |
| :--- | :--- | :--- |
| [`c5_calibrations/calibrate_aphairesis.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_calibrations/calibrate_aphairesis.py) | `Python` | calibrate_aphairesis.py — Generador de constantes axiomáticas para thermodynamics.rs (Capa 2) |
| [`c5_calibrations/calibrate_popperian_entropy.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_calibrations/calibrate_popperian_entropy.py) | `Python` | [Causal-Determinist] Empirical Calibration Tool for Popperian Shannon Entropy Thresholds. |
| [`c5_calibrations/topological_calibration.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_calibrations/topological_calibration.py) | `Python` | C5-REAL TOPOLOGICAL CALIBRATION PIPELINE — BABYLON-60 (Capa 2 Aphairesis) |

### ⚡ Centuria & Video Swarm Commanders

| Script | Tipo | Descripción / Propósito |
| :--- | :--- | :--- |
| [`c5_centuria/centuria_swarm_commander.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_centuria/centuria_swarm_commander.py) | `Python` | Centuria Swarm Commander Utility |
| [`c5_centuria/centuria_swarm_runner.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_centuria/centuria_swarm_runner.py) | `Python` | Ensure root importability |
| [`c5_centuria/remotion_swarm_orchestrator.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_centuria/remotion_swarm_orchestrator.py) | `Python` | Enforces: |

### 🖥️ CLI Tools & Native Hosts

| Script | Tipo | Descripción / Propósito |
| :--- | :--- | :--- |
| [`c5_cli/babylon_mail_cli.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_cli/babylon_mail_cli.py) | `Python` | BABYLONMAIL CLI & SUBAGENT INTERFACE |
| [`c5_cli/codex_virtual_hud.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_cli/codex_virtual_hud.py) | `Python` | Codex Virtual Hud Utility |
| [`c5_cli/moskv_native_host.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_cli/moskv_native_host.py) | `Python` | MOSKV-1 APEX: Native Messaging Transducer (INV_C5_18 / INV_C5_THERMO_VALVE) |
| [`c5_cli/opsec_sentinel_c5.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_cli/opsec_sentinel_c5.py) | `Python` | Opsec Sentinel C5 Utility |
| [`c5_cli/pty_tmux_bridge.sh`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_cli/pty_tmux_bridge.sh) | `Shell` | 🛡️ TMUX-PTY-Bridge-OMEGA (C5-REAL v2.0) |

### 🌀 Cortex Memory & Auto-Consolidation

| Script | Tipo | Descripción / Propósito |
| :--- | :--- | :--- |
| [`c5_cortex/autoconsolidate.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_cortex/autoconsolidate.py) | `Python` | Delete old entries, respecting INV_BFT_04 semantics |
| [`c5_cortex/bootstrap_cortex_memory.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_cortex/bootstrap_cortex_memory.py) | `Python` | Bootstrap Cortex Memory Utility |
| [`c5_cortex/consolidate_babylon_vault.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_cortex/consolidate_babylon_vault.py) | `Python` | Causal-Determinist SOVEREIGN CONSOLIDATION PROTOCOL — BABYLON-60 MEMORY VAULT |
| [`c5_cortex/consolidate_dbs.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_cortex/consolidate_dbs.py) | `Python` | Consolidación BFT (Erradicación del Antipatrón de Dispersión SQLite) |
| [`c5_cortex/cortex_labs_poc.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_cortex/cortex_labs_poc.py) | `Python` | Prueba de Concepto (PoC) Autónoma: Extracción Causal de Google Labs FX. |
| [`c5_cortex/cortex_objectives_transducer.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_cortex/cortex_objectives_transducer.py) | `Python` | Cortex Objectives Transducer Utility |

### 🔬 C5 Demos & Proofs of Concept

| Script | Tipo | Descripción / Propósito |
| :--- | :--- | :--- |
| [`c5_demos/demo_exergy_poc.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_demos/demo_exergy_poc.py) | `Python` | [Causal-Determinist] Exergy Optimizer Agent Proof of Concept. |
| [`c5_demos/demo_logos_ethos_ship.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_demos/demo_logos_ethos_ship.py) | `Python` | Demo Logos Ethos Ship Utility |
| [`c5_demos/poc_browser_pipeline.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_demos/poc_browser_pipeline.py) | `Python` | Poc Browser Pipeline Utility |
| [`c5_demos/poc_causal_hitl_agent.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_demos/poc_causal_hitl_agent.py) | `Python` | SOTA Proof of Concept (PoC): Operational Worker with Cryptographic Causal HITL Gate |
| [`c5_demos/poc_f60_time_domain.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_demos/poc_f60_time_domain.py) | `Python` | 32-byte hash commitment |
| [`c5_demos/poc_fast_failure_guard.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_demos/poc_fast_failure_guard.py) | `Python` | Poc Fast Failure Guard Utility |
| [`c5_demos/poc_graph_isomorphism_wl.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_demos/poc_graph_isomorphism_wl.py) | `Python` | [Causal-Determinist] Step 1 Proof of Concept: Graph Isomorphism WL Pre-Filter (INV_C5_28). |
| [`c5_demos/poc_logop_veto.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_demos/poc_logop_veto.py) | `Python` | Ensure the module can be imported |
| [`c5_demos/poc_two_tier_planner_worker.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_demos/poc_two_tier_planner_worker.py) | `Python` | MOSKV-1 APEX – Iteración 4 del PoC |
| [`c5_demos/run_commercial_bft.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_demos/run_commercial_bft.py) | `Python` | Run Commercial Bft Utility |
| [`c5_demos/run_hero_demo.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_demos/run_hero_demo.py) | `Python` | Simulates the live 60-second B2B Enterprise / Investor Demo in the terminal: |

### 🔧 Git Hooks & Commit Utilities

| Script | Tipo | Descripción / Propósito |
| :--- | :--- | :--- |
| [`c5_git_utils/commit_polisher.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_git_utils/commit_polisher.py) | `Python` | Continuous Commit Polisher Daemon. |
| [`c5_git_utils/install_git_hooks.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_git_utils/install_git_hooks.py) | `Python` | install_git_hooks.py - Installs automated git pre-commit quality gate hook |
| [`c5_git_utils/rewrite_commits.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_git_utils/rewrite_commits.py) | `Python` | Rewrite commit history to enforce Conventional Commits and BFT metadata. |

### 🧩 Categorical Isomorphisms & Engines

| Script | Tipo | Descripción / Propósito |
| :--- | :--- | :--- |
| [`c5_isomorphisms/c5_isomorphism_sabu_agent.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_isomorphisms/c5_isomorphism_sabu_agent.py) | `Python` | C5 Isomorphism Sabu Agent Utility |
| [`c5_isomorphisms/c5_logos_ethos_ship_engine.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_isomorphisms/c5_logos_ethos_ship_engine.py) | `Python` | C5 Logos Ethos Ship Engine Utility |
| [`c5_isomorphisms/c5_ultimate_causal_determinant.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_isomorphisms/c5_ultimate_causal_determinant.py) | `Python` | Causal-Determinist Execution Engine: THE ULTIMATE DETERMINANT (V3 - SINGULARITY) |
| [`c5_isomorphisms/cancer_isomorphism_pipeline.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_isomorphisms/cancer_isomorphism_pipeline.py) | `Python` | Cancer Isomorphism Pipeline Utility |
| [`c5_isomorphisms/gen_oncology_primitives.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_isomorphisms/gen_oncology_primitives.py) | `Python` | Gen Oncology Primitives Utility |

### ⛓️ L1 Anchor & Ledger Engines

| Script | Tipo | Descripción / Propósito |
| :--- | :--- | :--- |
| [`c5_l1_ledger/anchor_l1_sink.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_l1_ledger/anchor_l1_sink.py) | `Python` | MOSKV-1 APEX: L1_sink Anchor & Verification Script (INV_C5_15) |
| [`c5_l1_ledger/bittensor_yuma_consensus_c5.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_l1_ledger/bittensor_yuma_consensus_c5.py) | `Python` | Causal-Determinist BITTENSOR (TAO) YUMA CONSENSUS & EXERGY TRANSDUCER |
| [`c5_l1_ledger/l1_sink_bitcoin.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_l1_ledger/l1_sink_bitcoin.py) | `Python` | Control Flow Depth: 1 (FunctionDef) |
| [`c5_l1_ledger/ledger_snapshot_engine.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_l1_ledger/ledger_snapshot_engine.py) | `Python` | Incremental Ledger Snapshot Engine. |

### 🐝 Swarm & Legion Execution Engines

| Script | Tipo | Descripción / Propósito |
| :--- | :--- | :--- |
| [`c5_legion/legion_10000_orchestrator.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_legion/legion_10000_orchestrator.py) | `Python` | Implements the Cognitive Transition Algebra (CTA) for massive parallel |
| [`c5_legion/legion_1000_audit_swarm.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_legion/legion_1000_audit_swarm.py) | `Python` | MOSKV-1: Legion 1000 Audit Swarm Engine (INV_C5_18) |
| [`c5_legion/legion_222_agentes.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_legion/legion_222_agentes.py) | `Python` | LEGION MÁXIMO COGNITIVO - 222 Agentes Organizados |
| [`c5_legion/legion_swarm.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_legion/legion_swarm.py) | `Python` | legion_swarm.py - Unified Sovereign Swarm Orchestrator CLI |
| [`c5_legion/legion_swarm_core.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_legion/legion_swarm_core.py) | `Python` | legion_swarm_core.py - Core Engine for Swarm Quantum Collapse |

### 📜 Log Custody & Forensic Attestation

| Script | Tipo | Descripción / Propósito |
| :--- | :--- | :--- |
| [`c5_log_custody/c5_organize_captures.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_log_custody/c5_organize_captures.py) | `Python` | C5 Organize Captures Utility |
| [`c5_log_custody/c5_preserve_agent_local_logs.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_log_custody/c5_preserve_agent_local_logs.py) | `Python` | c5_preserve_agent_local_logs.py - Wrapper delegando en c5_preserve_logs.py |
| [`c5_log_custody/c5_preserve_claude_local_logs.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_log_custody/c5_preserve_claude_local_logs.py) | `Python` | c5_preserve_claude_local_logs.py - Wrapper delegando en c5_preserve_logs.py |
| [`c5_log_custody/c5_preserve_logs.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_log_custody/c5_preserve_logs.py) | `Python` | c5_preserve_logs.py - Unified CLI log harvesting, dual cryptographic hashing |

### 🛡️ Quality Gates & AST Verification

| Script | Tipo | Descripción / Propósito |
| :--- | :--- | :--- |
| [`c5_quality_gates/audit_100_agents.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_quality_gates/audit_100_agents.py) | `Python` | AUDIT AND AUTO-NORMALIZATION OF THE 100 SOVEREIGN AGENTS |
| [`c5_quality_gates/audit_fixer.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_quality_gates/audit_fixer.py) | `Python` | Audit Fixer Utility |
| [`c5_quality_gates/audit_scripts_quality.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_quality_gates/audit_scripts_quality.py) | `Python` | audit_scripts_quality.py - Pre-commit and CI Quality Gate Auditor & Auto-Healer for scripts/ |
| [`c5_quality_gates/check_depth.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_quality_gates/check_depth.py) | `Python` | Check Depth Utility |
| [`c5_quality_gates/pre_push_ledger_guard.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_quality_gates/pre_push_ledger_guard.py) | `Python` | Ledger-Aware Pre-Push Guard. |
| [`c5_quality_gates/run_cache_audit.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_quality_gates/run_cache_audit.py) | `Python` | Compiles and runs the empirical cache benchmark to demonstrate |
| [`c5_quality_gates/secret_swarm_auditor.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_quality_gates/secret_swarm_auditor.py) | `Python` | Causal-Determinist: Swarm Thread Dispatcher for TOP SECRET Auditing (ULTRATHINK P0 - ITERATION 3) |
| [`c5_quality_gates/swarm_lock_guard.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_quality_gates/swarm_lock_guard.py) | `Python` | MOSKV-1 APEX: Swarm Workspace Lock Guard (INV_C5_22) |
| [`c5_quality_gates/symlink_depth_auditor.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_quality_gates/symlink_depth_auditor.py) | `Python` | Symlink Depth Auditor (INV_C5_12 Enforcer). |

### ♾️ Autopoiesis & System Simulations

| Script | Tipo | Descripción / Propósito |
| :--- | :--- | :--- |
| [`c5_simulations/luhmann_autopoiesis_simulation.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_simulations/luhmann_autopoiesis_simulation.py) | `Python` | Add project root to sys.path to allow absolute imports |
| [`c5_simulations/ouroboros_infinity.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_simulations/ouroboros_infinity.py) | `Python` | Ouroboros Infinity Utility |
| [`c5_simulations/prigogine_boltzmann_simulation.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_simulations/prigogine_boltzmann_simulation.py) | `Python` | Grid 10x10 (100 cells) |

### 🧠 Skill Synchronization & Ontology

| Script | Tipo | Descripción / Propósito |
| :--- | :--- | :--- |
| [`c5_skills_ontology/audit_skills_execution.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_skills_ontology/audit_skills_execution.py) | `Python` | audit_skills_execution.py - Comprehensive verification & benchmark suite for |
| [`c5_skills_ontology/optimize_all_skill_triggers.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_skills_ontology/optimize_all_skill_triggers.py) | `Python` | optimize_all_skill_triggers.py - Enriches and formats display names and trigger |
| [`c5_skills_ontology/sync_skills_registry.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_skills_ontology/sync_skills_registry.py) | `Python` | sync_skills_registry.py - Automated synchronization of physical skills (disk) |
| [`c5_skills_ontology/sync_vault_uuids.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_skills_ontology/sync_vault_uuids.py) | `Python` | Sync Vault Uuids Utility |

### 🧪 Unit Tests & Curvature Proofs

| Script | Tipo | Descripción / Propósito |
| :--- | :--- | :--- |
| [`c5_tests/test_discrete_curvature.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_tests/test_discrete_curvature.py) | `Python` | 1. Grafo Estrella (alta centralización, cuello de botella) |
| [`c5_tests/test_hitl_do_calculus.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_tests/test_hitl_do_calculus.py) | `Python` | MOCK para el entorno roto |
| [`c5_tests/test_merkle_pulse_fail_stop.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_tests/test_merkle_pulse_fail_stop.py) | `Python` | MOCK para el entorno roto de BABYLON-60 (paths.py no existe en el repo original) |

### 🔥 Thermodynamic Benchmarks & Exergy Optimizers

| Script | Tipo | Descripción / Propósito |
| :--- | :--- | :--- |
| [`c5_thermo/benchmark_ledger_throughput.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_thermo/benchmark_ledger_throughput.py) | `Python` | Pre-generar eventos para medir puramente el IO y el BFT Actor |
| [`c5_thermo/c5_exergy_optimizer_monitor.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_thermo/c5_exergy_optimizer_monitor.py) | `Python` | MOSKV-1 APEX SINGULARITY — Causal-Determinist STATE MONITOR (EXERGY_OPTIMIZER) |
| [`c5_thermo/cache_1000_memoization_bench.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_thermo/cache_1000_memoization_bench.py) | `Python` | Cache 1000 Memoization Bench Utility |
| [`c5_thermo/exergy_arbitrage_engine.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_thermo/exergy_arbitrage_engine.py) | `Python` | Exergy Arbitrage Engine Utility |
| [`c5_thermo/exergy_dashboard_server.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_thermo/exergy_dashboard_server.py) | `Python` | Exergy Dashboard Server (Causal-Determinist). |
| [`c5_thermo/exergy_optimizer_agent.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_thermo/exergy_optimizer_agent.py) | `Python` | [Causal-Determinist] Exergy Optimizer Agent. |
| [`c5_thermo/stress_100m_bft.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_thermo/stress_100m_bft.py) | `Python` | 100,000,000 STRESS TEST ENGINE — CORTEX PERSIST BFT LEDGER |
| [`c5_thermo/stress_10m.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_thermo/stress_10m.py) | `Python` | Stress 10M Utility |
| [`c5_thermo/stress_sqlite_wal.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_thermo/stress_sqlite_wal.py) | `Python` | Stress test for SQLite WAL and busy_timeout (INV_BFT_02). |

### 🛠️ Domain Helpers & Enforcers

| Script | Tipo | Descripción / Propósito |
| :--- | :--- | :--- |
| [`c5_utils/ddd_strangler.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_utils/ddd_strangler.py) | `Python` | Utils |
| [`c5_utils/export_country_compliance.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_utils/export_country_compliance.py) | `Python` | Generates localized EU AI Act / NIST AI RMF compliance reports for target countries. |
| [`c5_utils/fetch_missing_dates.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_utils/fetch_missing_dates.py) | `Python` | fetch_missing_dates.py — batch update dataset.json with enrollment_velocity. |
| [`c5_utils/python_spsc_reader.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_utils/python_spsc_reader.py) | `Python` | python_spsc_reader.py — Consumidor Multiproceso Python Zero-Copy (C-ABI FFI) |
| [`c5_utils/quadrilingual_enforcer.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_utils/quadrilingual_enforcer.py) | `Python` | Quadrilingual Enforcer Utility |

### ⚖️ Formal Verification & Axiom Oracles

| Script | Tipo | Descripción / Propósito |
| :--- | :--- | :--- |
| [`c5_verifiers/autodetect_invariants.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_verifiers/autodetect_invariants.py) | `Python` | Autopoiesis Invariant Auditor. |
| [`c5_verifiers/axiom_verifier_z3.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_verifiers/axiom_verifier_z3.py) | `Python` | MOSKV-1 APEX — Axiom Verifier (Z3/SMT-free Pure-Python Implementation) |
| [`c5_verifiers/conformance_test.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_verifiers/conformance_test.py) | `Python` | Conformance Test Utility |
| [`c5_verifiers/deterministic_audit.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_verifiers/deterministic_audit.py) | `Python` | Zero-Friction Mass Execution (F=0) |
| [`c5_verifiers/verify_anergy_token_purge.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_verifiers/verify_anergy_token_purge.py) | `Python` | Causal-Determinist SOVEREIGN ANERGY PURGE & AUTOCOGNITION-OMEGA ENGINE |
| [`c5_verifiers/verify_captures.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_verifiers/verify_captures.py) | `Python` | Verify Captures Utility |
| [`c5_verifiers/verify_claims.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_verifiers/verify_claims.py) | `Python` | verify_claims.py — Verificación paralela del report de arbitraje contra |
| [`c5_verifiers/verify_tonnetz_falsification.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_verifiers/verify_tonnetz_falsification.py) | `Python` | scripts/verify_tonnetz_falsification.py |
| [`c5_verifiers/verify_execution.sh`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_verifiers/verify_execution.sh) | `Shell` | verify_execution.sh |
| [`c5_verifiers/verify_lean_proofs.sh`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_verifiers/verify_lean_proofs.sh) | `Shell` | Check for 'sorry' keyword in proof file |

### ⚡ Core Dispatchers & CLI Entrypoints

| Script | Tipo | Descripción / Propósito |
| :--- | :--- | :--- |
| [`generate_scripts_readme.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/generate_scripts_readme.py) | `Python` | generate_scripts_readme.py - Automated self-documenting catalog generator |
| [`runner.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/runner.py) | `Python` | runner.py - Central CLI Dispatcher for BABYLON-60 Sovereign Scripts Suite |

### 📦 Deployment & P0 Remediation Scripts

| Script | Tipo | Descripción / Propósito |
| :--- | :--- | :--- |
| [`c5_deploy/COLLAPSE_P0.sh`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_deploy/COLLAPSE_P0.sh) | `Shell` | COLLAPSE_P0.sh — BABYLON-60 · P0 KEY-EXPOSURE REMEDIATION |
| [`c5_deploy/deploy.sh`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_deploy/deploy.sh) | `Shell` | C5-REAL: IGNITION PROTOCOL |
| [`c5_deploy/deploy_hotstuff.sh`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_deploy/deploy_hotstuff.sh) | `Shell` | deploy_hotstuff.sh — Deployment script for HotStuff consensus engine. |
| [`c5_deploy/publish_crates.sh`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_deploy/publish_crates.sh) | `Shell` | Publish Crates Utility |

### 🚀 Host & Repository Setup Scripts

| Script | Tipo | Descripción / Propósito |
| :--- | :--- | :--- |
| [`c5_setup/install_host.sh`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_setup/install_host.sh) | `Shell` | Registra moskv_native_host.py en Chrome/Brave en macOS |
| [`c5_setup/install_into_repo.sh`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_setup/install_into_repo.sh) | `Shell` | install_into_repo.sh |

---
*Catálogo auto-generado dinámicamente por `generate_scripts_readme.py`.*