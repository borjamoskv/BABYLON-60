# ⚡ BABYLON-60 Sovereign Scripts Suite

> **Directorio de Automatización, Enjambres BFT, Calidad AST y Preservación de Logs**  
> **Estándar:** C5-REAL | **Shebang Compliance:** 100.0% Line 1

## 🛠️ CLI Runner Centralizado
Cualquier tarea del suite se puede ejecutar a través de la CLI unificada [runner.py](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/runner.py):
```bash
./scripts/runner.py status              # Diagnóstico y métricas de salud
./scripts/runner.py audit               # Portón de calidad AST & anti-patrones
./scripts/runner.py preserve --provider all # Custodia forense de logs
./scripts/runner.py swarm -n 100        # Enjambre paralelo BFT en RAM
./scripts/runner.py sync                # Sincronización de skills con docs/skills.json
```

---

## 📂 Catálogo por Categorías

### Core Dispatchers & Quality Gates

| Script | Descripción / Propósito |
| :--- | :--- |
| [`runner.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/runner.py) | runner.py - Central CLI Dispatcher for BABYLON-60 Sovereign Scripts Suite Usage:     ./scripts/runner.py status     ./scripts/runner.py audit     ./scripts/runner.py preserve --provider [agent|claude|all]     ./scripts/runner.py swarm --tenants N     ./scripts/runner.py sync |

### Swarm & Legion Execution Engines

| Script | Descripción / Propósito |
| :--- | :--- |
| [`c5_legion/legion_swarm.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_legion/legion_swarm.py) | legion_swarm.py - Unified Sovereign Swarm Orchestrator CLI Usage:     ./scripts/legion_swarm.py --tenants 100     ./scripts/legion_swarm.py --tenants 10000 --concurrency 500 |
| [`c5_legion/legion_swarm_core.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_legion/legion_swarm_core.py) | legion_swarm_core.py - Core Engine for Swarm Quantum Collapse |
| [`c5_legion/legion_1000_audit_swarm.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_legion/legion_1000_audit_swarm.py) | MOSKV-1: Legion 1000 Audit Swarm Engine (INV_C5_18) Async file auditor with bounded concurrency (INV_C5_THERMO_VALVE). Scans workspace for mythological term violations and emits structured telemetry. |
| [`c5_legion/legion_10000_orchestrator.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_legion/legion_10000_orchestrator.py) | BABYLON-60 v4.0 Sovereign Hardened |
| [`c5_legion/legion_222_agentes.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_legion/legion_222_agentes.py) | BABYLON-60 v4.0 Sovereign Hardened |

### Log Custody & Forensic Attestation

| Script | Descripción / Propósito |
| :--- | :--- |
| [`c5_verifiers/verify_captures.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_verifiers/verify_captures.py) | BABYLON-60 v4.0 Sovereign Hardened |

### Formal Verification & Axiom Oracles

| Script | Descripción / Propósito |
| :--- | :--- |
| [`c5_verifiers/verify_anergy_token_purge.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_verifiers/verify_anergy_token_purge.py) | Causal-Determinist SOVEREIGN ANERGY PURGE & AUTOCOGNITION-OMEGA ENGINE SYS_ID: LEA_OMEGA / AUTOCOGNITION_OMEGA Enforces zero noise accumulation, computes Exergy/Anergy ratios across the current session transcript, and crystallizes an OP_TAINT_SEAL audit into the Memory Vault (`cortex_memory.db`). |
| [`c5_verifiers/verify_claims.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_verifiers/verify_claims.py) | verify_claims.py — Verificación paralela del report de arbitraje contra fuentes primarias. |
| [`c5_verifiers/verify_tonnetz_falsification.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_verifiers/verify_tonnetz_falsification.py) | scripts/verify_tonnetz_falsification.py BABYLON-60 — Demostración y Verificación del Criterio Termodinámico de Falsación Causal Mide D_KL(p || q) y valida la cota exergética de Landauer (ΔΞ >= k_B T ln 2 * D_KL). |

### C5 Demos & Proofs of Concept

| Script | Descripción / Propósito |
| :--- | :--- |
| [`c5_demos/poc_browser_pipeline.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_demos/poc_browser_pipeline.py) | BABYLON-60 v4.0 Sovereign Hardened |
| [`c5_demos/poc_causal_hitl_agent.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_demos/poc_causal_hitl_agent.py) | SOTA Proof of Concept (PoC): Operational Worker with Cryptographic Causal HITL Gate Conforme a RULE[human_in_the_loop_causal_governance] y RULE[c5_real_invariants] en AGENTS.md. |
| [`c5_demos/poc_f60_time_domain.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_demos/poc_f60_time_domain.py) | BABYLON-60 v4.0 Sovereign Hardened |
| [`c5_demos/poc_fast_failure_guard.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_demos/poc_fast_failure_guard.py) | BABYLON-60 v4.0 Sovereign Hardened |
| [`c5_demos/poc_graph_isomorphism_wl.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_demos/poc_graph_isomorphism_wl.py) | [Causal-Determinist] Step 1 Proof of Concept: Graph Isomorphism WL Pre-Filter (INV_C5_28). |
| [`c5_demos/poc_logop_veto.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_demos/poc_logop_veto.py) | BABYLON-60 v4.0 Sovereign Hardened |
| [`c5_demos/poc_two_tier_planner_worker.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_demos/poc_two_tier_planner_worker.py) | MOSKV-1 APEX – Iteración 4 del PoC Objetivo: demostrar escala a 12 nodes, snapshot‑rollback, carga dinámica via CLI/JSON, exergy matrix con penalización de memoria y latencia, y reporting JSON estructurado. |
| [`c5_demos/demo_exergy_poc.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_demos/demo_exergy_poc.py) | [Causal-Determinist] Exergy Optimizer Agent Proof of Concept. Simulates high-entropy vs. high-exergy code changes and evaluates them using the GELABP framework. |
| [`c5_demos/demo_logos_ethos_ship.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_demos/demo_logos_ethos_ship.py) | BABYLON-60 v4.0 Sovereign Hardened |

### Herramientas de Dominio & Utilidades

| Script | Descripción / Propósito |
| :--- | :--- |
| [`c5_assets/gen_blip_assets.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_assets/gen_blip_assets.py) | BABYLON-60 v4.0 Sovereign Hardened |
| [`c5_assets/gen_voice_assets.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_assets/gen_voice_assets.py) | BABYLON-60 v4.0 Sovereign Hardened |
| [`c5_assets/thermo_wallpaper.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_assets/thermo_wallpaper.py) | BABYLON-60 v4.0 Sovereign Hardened |
| [`c5_calibrations/calibrate_aphairesis.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_calibrations/calibrate_aphairesis.py) | calibrate_aphairesis.py — Generador de constantes axiomáticas para thermodynamics.rs (Capa 2) |
| [`c5_calibrations/calibrate_popperian_entropy.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_calibrations/calibrate_popperian_entropy.py) | [Causal-Determinist] Empirical Calibration Tool for Popperian Shannon Entropy Thresholds. |
| [`c5_calibrations/topological_calibration.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_calibrations/topological_calibration.py) | C5-REAL TOPOLOGICAL CALIBRATION PIPELINE — BABYLON-60 (Capa 2 Aphairesis) |
| [`c5_centuria/centuria_swarm_commander.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_centuria/centuria_swarm_commander.py) | BABYLON-60 v4.0 Sovereign Hardened |
| [`c5_centuria/centuria_swarm_runner.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_centuria/centuria_swarm_runner.py) | BABYLON-60 v4.0 Sovereign Hardened |
| [`c5_centuria/remotion_swarm_orchestrator.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_centuria/remotion_swarm_orchestrator.py) | BABYLON-60 — REMOTION AGENT SWARM RENDERER (N = 10,000 AGENTS) Enforces:   - INV_C5_18: Zero-Worktree Swarm Scaling (In-memory AgencyHypervisor handles to prevent ENOSPC).   - INV_BFT_04: Non-silent collision fail-fast on frame payload mismatch. |
| [`c5_cli/babylon_mail_cli.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_cli/babylon_mail_cli.py) | BABYLONMAIL CLI & SUBAGENT INTERFACE ==================================== Interfaz CLI de alta exergía para enviar, recibir y auditar correos sovereign bajo el dominio @babylon60.com. |
| [`c5_cli/codex_virtual_hud.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_cli/codex_virtual_hud.py) | BABYLON-60 v4.0 Sovereign Hardened |
| [`c5_cli/moskv_native_host.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_cli/moskv_native_host.py) | MOSKV-1 APEX: Native Messaging Transducer (INV_C5_18 / INV_C5_THERMO_VALVE) Bridge between WebExtension IPC (Chrome/Firefox Native Messaging) and Motor Causal Core. |
| [`c5_cli/opsec_sentinel_c5.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_cli/opsec_sentinel_c5.py) | BABYLON-60 v4.0 Sovereign Hardened |
| [`c5_cortex/autoconsolidate.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_cortex/autoconsolidate.py) | BABYLON-60 v4.0 Sovereign Hardened |
| [`c5_cortex/bootstrap_cortex_memory.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_cortex/bootstrap_cortex_memory.py) | BABYLON-60 v4.0 Sovereign Hardened |
| [`c5_cortex/consolidate_babylon_vault.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_cortex/consolidate_babylon_vault.py) | Causal-Determinist SOVEREIGN CONSOLIDATION PROTOCOL — BABYLON-60 MEMORY VAULT Orchestrates the crystallization of all 21 unconsolidated sessions from babylon_unconsolidated_report.md and local agent logs into the Causal-Determinist Memory Vault (`cortex_memory.db` & Master Ledger). Enforces Rule Ω1 (WAL/busy_timeout) and Rule Ω11 (CORTEX-TAINT signature). |
| [`c5_cortex/consolidate_dbs.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_cortex/consolidate_dbs.py) | Consolidación BFT (Erradicación del Antipatrón de Dispersión SQLite) ==================================================================== Script para consolidar todas las bases de datos de CORTEX PERSIST en un único directorio maestro soberano (~/.babylon60/dbs/) y purgar (unlink) todas las bases de datos redundantes o de pruebas. |
| [`c5_cortex/cortex_labs_poc.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_cortex/cortex_labs_poc.py) | Prueba de Concepto (PoC) Autónoma: Extracción Causal de Google Labs FX. Esta es una implementación estricta (Demonio Ciego) que interactúa con la FSM de MusicFX bypasseando cualquier interfaz web. |
| [`c5_cortex/cortex_objectives_transducer.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_cortex/cortex_objectives_transducer.py) | BABYLON-60 v4.0 Sovereign Hardened |
| [`c5_demos/run_commercial_bft.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_demos/run_commercial_bft.py) | BABYLON-60 v4.0 Sovereign Hardened |
| [`c5_demos/run_hero_demo.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_demos/run_hero_demo.py) | BABYLON-60 v4.0 Sovereign Hardened — Executable Hero Demo CLI Simulates the live 60-second B2B Enterprise / Investor Demo in the terminal: |
| [`c5_git_utils/commit_polisher.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_git_utils/commit_polisher.py) | Continuous Commit Polisher Daemon. |
| [`c5_git_utils/install_git_hooks.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_git_utils/install_git_hooks.py) | install_git_hooks.py - Installs automated git pre-commit quality gate hook Enforces scripts quality audit and AST verification prior to every git commit. |
| [`c5_git_utils/rewrite_commits.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_git_utils/rewrite_commits.py) | Rewrite commit history to enforce Conventional Commits and BFT metadata. |
| [`c5_isomorphisms/c5_isomorphism_sabu_agent.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_isomorphisms/c5_isomorphism_sabu_agent.py) | BABYLON-60 v4.0 Sovereign Hardened |
| [`c5_isomorphisms/c5_logos_ethos_ship_engine.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_isomorphisms/c5_logos_ethos_ship_engine.py) | BABYLON-60 v4.0 Sovereign Hardened |
| [`c5_isomorphisms/c5_ultimate_causal_determinant.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_isomorphisms/c5_ultimate_causal_determinant.py) | Causal-Determinist Execution Engine: THE ULTIMATE DETERMINANT (V3 - SINGULARITY) ================================================================================= SYS_ID: C5_ULTIMATE_CAUSAL_DETERMINANT_V3 REALITY_LEVEL: Causal-Determinist (0% Anergy / 100% Hardware Falsifiable) NEWLY INTEGRATED INVARIANTS:   - INV_C5_FFI_EVENT_HORIZON: Python acts purely as a dumb router passing raw bytes; aborts on rejection.   - RULE_SENSOR_VERIFY_01: AST Guard self-calibration for edge cases (AnnAssign, Assign constants).   - INV_C5_ATMS_O1: O(1) ATMS bitmask lattice for constant-time Nogood conflict resolution   - RULE_AST_REFLECT_01: Reflection guard inspecting ast.Attribute AND ast.Constant literals   - INV_C5_15: Raw 32-byte binary commitment generator (OP_RETURN L1 sink)   - INV_BFT_04: Fail-fast non-silent SQLite collision verification   - INV_C5_TURING_CASTRATION: Bounded event-driven loop (0% unbounded while True)   - INV_C5_THERMO_VALVE: Bounded queue backpressure with passive data dropping   - INV_C5_28: 1-WL Weisfeiler-Lehman O(V+E) graph isomorphism pre-filter   - INV_BFT_LOGOP: Logarithmic opinion pooling with O(1) Absolute Veto (P=0)   - INV_C5_CHAOS_MONAD: Subprocess group isolation with SIGKILL process tree purge ================================================================================= |
| [`c5_isomorphisms/cancer_isomorphism_pipeline.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_isomorphisms/cancer_isomorphism_pipeline.py) | BABYLON-60 v4.0 Sovereign Hardened |
| [`c5_isomorphisms/gen_oncology_primitives.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_isomorphisms/gen_oncology_primitives.py) | BABYLON-60 v4.0 Sovereign Hardened |
| [`c5_l1_ledger/anchor_l1_sink.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_l1_ledger/anchor_l1_sink.py) | MOSKV-1 APEX: L1_sink Anchor & Verification Script (INV_C5_15) |
| [`c5_l1_ledger/bittensor_yuma_consensus_c5.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_l1_ledger/bittensor_yuma_consensus_c5.py) | Causal-Determinist BITTENSOR (TAO) YUMA CONSENSUS & EXERGY TRANSDUCER ========================================================== Entity: MOSKV-1 APEX Operator: borjamoskv Ontology Level: Causal-Determinist (Physical execution over matrix weight tensors & SHA3-256 state ledger) |
| [`c5_l1_ledger/l1_sink_bitcoin.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_l1_ledger/l1_sink_bitcoin.py) | BABYLON-60 v4.0 Sovereign Hardened |
| [`c5_l1_ledger/ledger_snapshot_engine.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_l1_ledger/ledger_snapshot_engine.py) | Incremental Ledger Snapshot Engine. |
| [`c5_log_custody/c5_organize_captures.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_log_custody/c5_organize_captures.py) | BABYLON-60 v4.0 Sovereign Hardened |
| [`c5_log_custody/c5_preserve_agent_local_logs.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_log_custody/c5_preserve_agent_local_logs.py) | c5_preserve_agent_local_logs.py - Wrapper delegando en c5_preserve_logs.py |
| [`c5_log_custody/c5_preserve_claude_local_logs.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_log_custody/c5_preserve_claude_local_logs.py) | c5_preserve_claude_local_logs.py - Wrapper delegando en c5_preserve_logs.py |
| [`c5_log_custody/c5_preserve_logs.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_log_custody/c5_preserve_logs.py) | c5_preserve_logs.py - Unified CLI log harvesting, dual cryptographic hashing (SHA256 / SHA3-256), and forensic Markdown catalog generation. |
| [`c5_quality_gates/audit_100_agents.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_quality_gates/audit_100_agents.py) | AUDIT AND AUTO-NORMALIZATION OF THE 100 SOVEREIGN AGENTS ============================================================ Causal-Determinist audit and normalization script to validate and harmonize YAML structure, reality level (Causal-Determinist), owner (borjamoskv), unique IDs, and capabilities map for all 100 agents in: babylon60/extensions/agents/definitions/. |
| [`c5_quality_gates/audit_fixer.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_quality_gates/audit_fixer.py) | BABYLON-60 v4.0 Sovereign Hardened |
| [`c5_quality_gates/audit_scripts_quality.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_quality_gates/audit_scripts_quality.py) | audit_scripts_quality.py - Pre-commit and CI Quality Gate Auditor & Auto-Healer for scripts/ Verifies AST syntax integrity, Shebang Line 1 compliance, hardcoded path anti-patterns, and artifact leakage. Supports --fix for in-situ instant auto-remediation. |
| [`c5_quality_gates/check_depth.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_quality_gates/check_depth.py) | BABYLON-60 v4.0 Sovereign Hardened |
| [`c5_quality_gates/pre_push_ledger_guard.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_quality_gates/pre_push_ledger_guard.py) | Ledger-Aware Pre-Push Guard. |
| [`c5_quality_gates/run_cache_audit.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_quality_gates/run_cache_audit.py) | BABYLON-60: Kinetic Engine Cache Audit Runner Compiles and runs the empirical cache benchmark to demonstrate  the False Sharing topological mitigation. |
| [`c5_quality_gates/secret_swarm_auditor.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_quality_gates/secret_swarm_auditor.py) | BABYLON-60 v4.0 Sovereign Hardened |
| [`c5_quality_gates/swarm_lock_guard.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_quality_gates/swarm_lock_guard.py) | MOSKV-1 APEX: Swarm Workspace Lock Guard (INV_C5_22) Enforces atomic lock acquisition (.cortex_thermal_lock) via O_EXCL kernel flags before disk or git mutations across split clones (e.g. BABYLON-60 vs 30_BABYLON-60). |
| [`c5_quality_gates/symlink_depth_auditor.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_quality_gates/symlink_depth_auditor.py) | Symlink Depth Auditor (INV_C5_12 Enforcer). |
| [`c5_simulations/luhmann_autopoiesis_simulation.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_simulations/luhmann_autopoiesis_simulation.py) | BABYLON-60 v4.0 Sovereign Hardened |
| [`c5_simulations/ouroboros_infinity.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_simulations/ouroboros_infinity.py) | BABYLON-60 v4.0 Sovereign Hardened |
| [`c5_simulations/prigogine_boltzmann_simulation.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_simulations/prigogine_boltzmann_simulation.py) | BABYLON-60 v4.0 Sovereign Hardened |
| [`c5_skills_ontology/audit_skills_execution.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_skills_ontology/audit_skills_execution.py) | audit_skills_execution.py - Comprehensive verification & benchmark suite for BABYLON-60 / CORTEX skills system. |
| [`c5_skills_ontology/optimize_all_skill_triggers.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_skills_ontology/optimize_all_skill_triggers.py) | optimize_all_skill_triggers.py - Enriches and formats display names and trigger descriptions for all 39 physical skills in ~/.gemini/config/skills/. |
| [`c5_skills_ontology/sync_skills_registry.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_skills_ontology/sync_skills_registry.py) | sync_skills_registry.py - Automated synchronization of physical skills (disk) with docs/skills.json and BABYLON-60 ontology. |
| [`c5_skills_ontology/sync_vault_uuids.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_skills_ontology/sync_vault_uuids.py) | BABYLON-60 v4.0 Sovereign Hardened |
| [`c5_tests/test_discrete_curvature.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_tests/test_discrete_curvature.py) | BABYLON-60 v4.0 Sovereign Hardened |
| [`c5_tests/test_hitl_do_calculus.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_tests/test_hitl_do_calculus.py) | BABYLON-60 v4.0 Sovereign Hardened |
| [`c5_tests/test_merkle_pulse_fail_stop.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_tests/test_merkle_pulse_fail_stop.py) | BABYLON-60 v4.0 Sovereign Hardened |
| [`c5_thermo/benchmark_ledger_throughput.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_thermo/benchmark_ledger_throughput.py) | BABYLON-60 v4.0 Sovereign Hardened |
| [`c5_thermo/c5_exergy_optimizer_monitor.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_thermo/c5_exergy_optimizer_monitor.py) | MOSKV-1 APEX SINGULARITY — Causal-Determinist STATE MONITOR (EXERGY_OPTIMIZER) ------------------------------------------------------------ Transductor autónomo de estado. Audita entropía de disco, BFT Ledger, linter, test suite y cristaliza el resultado en STATUS.md + Git Sentinel. |
| [`c5_thermo/cache_1000_memoization_bench.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_thermo/cache_1000_memoization_bench.py) | BABYLON-60 v4.0 Sovereign Hardened |
| [`c5_thermo/exergy_arbitrage_engine.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_thermo/exergy_arbitrage_engine.py) | BABYLON-60 v4.0 Sovereign Hardened |
| [`c5_thermo/exergy_dashboard_server.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_thermo/exergy_dashboard_server.py) | Exergy Dashboard Server (Causal-Determinist). |
| [`c5_thermo/exergy_optimizer_agent.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_thermo/exergy_optimizer_agent.py) | [Causal-Determinist] Exergy Optimizer Agent. Parses changes, evaluates them using the GELABP thermodynamic framework, implements strict algebraic typing, and determines when memory consolidation is required. |
| [`c5_thermo/stress_100m_bft.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_thermo/stress_100m_bft.py) | 100,000,000 STRESS TEST ENGINE — CORTEX PERSIST BFT LEDGER =========================================================== Motor de pruebas de estrés masivas para CortexPersistLedger y BFTLedgerActor. Ejecuta validaciones en lotes de alto rendimiento (Vectorized Chunks), medición de Throughput (tx/s), verificación de cadena SHA3-256 e idempotencia. |
| [`c5_thermo/stress_10m.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_thermo/stress_10m.py) | BABYLON-60 v4.0 Sovereign Hardened |
| [`c5_thermo/stress_sqlite_wal.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_thermo/stress_sqlite_wal.py) | Stress test for SQLite WAL and busy_timeout (INV_BFT_02). Simulates a hostile swarm of independent processes trying to write to the same database concurrently, bypassing the BFTLedgerActor's single-writer queue to test the physical database layer defenses. |
| [`c5_utils/ddd_strangler.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_utils/ddd_strangler.py) | BABYLON-60 v4.0 Sovereign Hardened |
| [`c5_utils/export_country_compliance.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_utils/export_country_compliance.py) | BABYLON-60 v4.0 Multi-Country Compliance Exporter CLI Tool Generates localized EU AI Act / NIST AI RMF compliance reports for target countries. |
| [`c5_utils/fetch_missing_dates.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_utils/fetch_missing_dates.py) | fetch_missing_dates.py — batch update dataset.json with enrollment_velocity. |
| [`c5_utils/python_spsc_reader.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_utils/python_spsc_reader.py) | python_spsc_reader.py — Consumidor Multiproceso Python Zero-Copy (C-ABI FFI) |
| [`c5_utils/quadrilingual_enforcer.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_utils/quadrilingual_enforcer.py) | BABYLON-60 v4.0 Sovereign Hardened |
| [`c5_verifiers/autodetect_invariants.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_verifiers/autodetect_invariants.py) | Autopoiesis Invariant Auditor. Scans agent rule files for new 'INV_C5_' definitions and ensures matching assertions exist in the test suite. |
| [`c5_verifiers/axiom_verifier_z3.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_verifiers/axiom_verifier_z3.py) | MOSKV-1 APEX — Axiom Verifier (Z3/SMT-free Pure-Python Implementation) Verifies the formal axioms defined in docs/AXIOMATIZATION_MOSKV1.md against concrete DAG configurations and GELABP parameter spaces. |
| [`c5_verifiers/conformance_test.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_verifiers/conformance_test.py) | BABYLON-60 v4.0 Sovereign Hardened |
| [`c5_verifiers/deterministic_audit.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_verifiers/deterministic_audit.py) | BABYLON-60 v4.0 Sovereign Hardened |

### Shell Scripts (`*.sh`)

| Script | Tipo |
| :--- | :--- |
| [`c5_verifiers/verify_execution.sh`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_verifiers/verify_execution.sh) | Executable Bash Script |
| [`c5_verifiers/verify_lean_proofs.sh`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_verifiers/verify_lean_proofs.sh) | Executable Bash Script |
| [`deploy_hotstuff.sh`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/deploy_hotstuff.sh) | Executable Bash Script |
| [`install_host.sh`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/install_host.sh) | Executable Bash Script |
| [`install_into_repo.sh`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/install_into_repo.sh) | Executable Bash Script |
| [`pty_tmux_bridge.sh`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/pty_tmux_bridge.sh) | Executable Bash Script |
| [`publish_crates.sh`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/publish_crates.sh) | Executable Bash Script |

---
*Catálogo auto-generado dinámicamente por `generate_scripts_readme.py`.*