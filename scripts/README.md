# ⚡ BABYLON-60 Sovereign Scripts Suite — Immutable Script Kernel (ISK)

> **Directorio de Automatización, Enjambres BFT, Calidad AST, Atestación SHA-256 y Preservación de Logs**  
> **Estándar:** C5-REAL | **Total Scripts:** 193 Python + 20 Shell | **Shebang Compliance:** 100.0%

## 🛠️ CLI Runner Centralizado
Cualquier tarea del suite se puede ejecutar a través de la CLI unificada [runner.py](runner.py):
```bash
./scripts/runner.py status              # Diagnóstico y métricas de salud
./scripts/runner.py audit               # Portón de calidad AST & anti-patrones
./scripts/runner.py preserve --provider all # Custodia forense de logs
./scripts/runner.py swarm -n 100        # Enjambre paralelo BFT en RAM
./scripts/runner.py sync                # Sincronización de skills con docs/skills.json
./scripts/runner.py catalog             # Auto-generación de este catálogo
```

---

Los periféricos retirados del catálogo activo se conservan en el
[archivo de periféricos](../examples/archived_peripherals/README.md), con sus
rutas anteriores y hashes de contenido.

## 📂 Catálogo Taxonómico por Dominios C5 (Atestación SHA3-256)

### 📁 Babylon60

| Script | Tipo | SHA3-256 | Descripción / Propósito |
| :--- | :--- | :--- | :--- |
| [`babylon60/gen_oncology_primitives.py`](babylon60/gen_oncology_primitives.py) | `Python` | a73762b97d3a | Generador y Exportador Ontológico de 300 Primitivas de Oncología Molecular |

### ⚡ Core Dispatchers & CLI Entrypoints

| Script | Tipo | SHA3-256 | Descripción / Propósito |
| :--- | :--- | :--- | :--- |
| [`babylon_launcher.py`](babylon_launcher.py) | `Python` | 2a2753ccca26 | Author: Borja Fernández Angulo (borjamoskv) |
| [`c5_icloud_deploy.py`](c5_icloud_deploy.py) | `Python` | c12f9288eeb3 | C5 Icloud Deploy Utility |
| [`dispatch_daily_ai_report.py`](dispatch_daily_ai_report.py) | `Python` | 119ff644286c | Despachador Headless de Reporte Diario C5-REAL (Anti-Focus Stealing) |
| [`distill_babylon60_docs.py`](distill_babylon60_docs.py) | `Python` | 9f7d54561d7b | scripts/distill_babylon60_docs.py |
| [`docs_lint.py`](docs_lint.py) | `Python` | db6103ef9882 | Enforces DOCS_GRAMMAR.md invariants mechanically. |
| [`generate_attestation_bundle.py`](generate_attestation_bundle.py) | `Python` | 59bf0ab6fe50 | Assembles reproducible cryptographic evidence bundle for external, zero-trust verification. |
| [`generate_attestation_bundle_v2.py`](generate_attestation_bundle_v2.py) | `Python` | 7a6aa4e63495 | Assembles reproducible cryptographic evidence bundle under schema `babylon60.attestation.v2` |
| [`generate_scripts_readme.py`](generate_scripts_readme.py) | `Python` | 38cfeca0bce0 | ruff: noqa: E402 |
| [`lead_data_policy.py`](lead_data_policy.py) | `Python` | 4719ae7e7a9a | Private storage and provenance boundaries for synthetic and commercial records. |
| [`outreach_cockpit.py`](outreach_cockpit.py) | `Python` | 219223ab4da0 | OUTREACH COCKPIT · TUI de Telemetría y Monitorización de Prospección BABYLON-60 |
| [`partition_campaigns.py`](partition_campaigns.py) | `Python` | 9233ef91d84a | PARTITION CAMPAIGNS · Particionador Estratégico de Campañas para BABYLON-60 |
| [`runner.py`](runner.py) | `Python` | 7d32901ad426 | runner.py - Central CLI Dispatcher for BABYLON-60 Sovereign Scripts Suite |
| [`verify_claims.py`](verify_claims.py) | `Python` | 5e4d5a1dcbac | Modes: |
| [`zero_touch_fundraising_poc.py`](zero_touch_fundraising_poc.py) | `Python` | dc316d29678d | Zero-Touch Fundraising Proof of Concept (PoC) |
| [`zero_touch_onboarding_daemon.py`](zero_touch_onboarding_daemon.py) | `Python` | fbe663b0237b | Author: Borja Fernández Angulo (borjamoskv) |
| [`c5_deploy_pipeline.sh`](c5_deploy_pipeline.sh) | `Shell` | fd08aabed385 | 1. Verificación Estructural |
| [`create_macos_app.sh`](create_macos_app.sh) | `Shell` | 5839b13cede7 | Cero dependencias externas. Genera un bundle .app compatible con Finder y Dock. |
| [`enforce_c5_rules.sh`](enforce_c5_rules.sh) | `Shell` | 382a23cde402 | Apply branch protection via GitHub API |
| [`package_release.sh`](package_release.sh) | `Shell` | eca632510630 | Empaqueta el bundle completo (Babylon60.app, Instalar-Babylon60.command, |
| [`preflight.sh`](preflight.sh) | `Shell` | f3e15916a937 | Preflight Utility |
| [`protect_main.sh`](protect_main.sh) | `Shell` | dd47f1f1302c | Protect Main Utility |

### 🎨 Assets & Multimodal Generators

| Script | Tipo | SHA3-256 | Descripción / Propósito |
| :--- | :--- | :--- | :--- |
| [`c5_assets/gen_blip_assets.py`](c5_assets/gen_blip_assets.py) | `Python` | 3861e59d2ade | Onda cuadrada |
| [`c5_assets/gen_voice_assets.py`](c5_assets/gen_voice_assets.py) | `Python` | 71370eb1320e | Textos extraídos de GoedelBrosComposition.tsx |
| [`c5_assets/thermo_wallpaper.py`](c5_assets/thermo_wallpaper.py) | `Python` | 25616d2c1bf2 | Thermo Wallpaper Utility |

### 🎯 Entropy & Calibration Utilities

| Script | Tipo | SHA3-256 | Descripción / Propósito |
| :--- | :--- | :--- | :--- |
| [`c5_calibrations/calibrate_aphairesis.py`](c5_calibrations/calibrate_aphairesis.py) | `Python` | 246145492144 | calibrate_aphairesis.py — Generador de constantes axiomáticas para thermodynamics.rs (Capa 2) |
| [`c5_calibrations/calibrate_popperian_entropy.py`](c5_calibrations/calibrate_popperian_entropy.py) | `Python` | b749c7d449e3 | [Causal-Determinist] Empirical Calibration Tool for Popperian Shannon Entropy Thresholds. |
| [`c5_calibrations/topological_calibration.py`](c5_calibrations/topological_calibration.py) | `Python` | d7db79ee4129 | C5-REAL TOPOLOGICAL CALIBRATION PIPELINE — BABYLON-60 (Capa 2 Aphairesis) |

### 🖥️ CLI Tools & Native Hosts

| Script | Tipo | SHA3-256 | Descripción / Propósito |
| :--- | :--- | :--- | :--- |
| [`c5_cli/babylon_mail_cli.py`](c5_cli/babylon_mail_cli.py) | `Python` | 29f4f1e3ed85 | BABYLONMAIL CLI & SUBAGENT INTERFACE |
| [`c5_cli/moskv_native_host.py`](c5_cli/moskv_native_host.py) | `Python` | 6529ef2ae314 | MOSKV-1 APEX: Native Messaging Transducer (INV_C5_18 / INV_C5_THERMO_VALVE) |
| [`c5_cli/opsec_sentinel_c5.py`](c5_cli/opsec_sentinel_c5.py) | `Python` | c0d2f15cc115 | Bootstrap sys.path para resolución determinista de babylon60 (Invariante Clone & Run) |
| [`c5_cli/pty_tmux_bridge.sh`](c5_cli/pty_tmux_bridge.sh) | `Shell` | 26f72663e5fb | 🛡️ TMUX-PTY-Bridge-OMEGA (C5-REAL v2.0) |

### 🌀 Cortex Memory & Auto-Consolidation

| Script | Tipo | SHA3-256 | Descripción / Propósito |
| :--- | :--- | :--- | :--- |
| [`c5_cortex/autoconsolidate.py`](c5_cortex/autoconsolidate.py) | `Python` | 8c33ce79a9d4 | ruff: noqa: E402 |
| [`c5_cortex/bootstrap_cortex_memory.py`](c5_cortex/bootstrap_cortex_memory.py) | `Python` | c74a843b1c6f | Bootstrap Cortex Memory Utility |
| [`c5_cortex/consolidate_babylon_vault.py`](c5_cortex/consolidate_babylon_vault.py) | `Python` | fe38ed8d6bec | Causal-Determinist SOVEREIGN CONSOLIDATION PROTOCOL — BABYLON-60 MEMORY VAULT |
| [`c5_cortex/consolidate_dbs.py`](c5_cortex/consolidate_dbs.py) | `Python` | f9d6fc45116a | Consolidación BFT (Erradicación del Antipatrón de Dispersión SQLite) |
| [`c5_cortex/cortex_labs_poc.py`](c5_cortex/cortex_labs_poc.py) | `Python` | cd605d2e32b1 | Prueba de Concepto (PoC) Autónoma: Extracción Causal de Google Labs FX. |
| [`c5_cortex/cortex_objectives_transducer.py`](c5_cortex/cortex_objectives_transducer.py) | `Python` | 0858ce007b50 | Cortex Objectives Transducer Utility |

### 🔬 C5 Demos & Proofs of Concept

| Script | Tipo | SHA3-256 | Descripción / Propósito |
| :--- | :--- | :--- | :--- |
| [`c5_demos/batch_gen_borja_voices.py`](c5_demos/batch_gen_borja_voices.py) | `Python` | 5b70690488b4 | Pre-renderiza en segundo plano las firmas acústicas de las topologías de Antigravity |
| [`c5_demos/benchmark_governance_10k.py`](c5_demos/benchmark_governance_10k.py) | `Python` | 9e89159c3acc | benchmark_governance_10k.py |
| [`c5_demos/c5_alpha_hunter.py`](c5_demos/c5_alpha_hunter.py) | `Python` | 9c3192ebb9b8 | C5 Alpha Hunter Utility |
| [`c5_demos/c5_auto_router.py`](c5_demos/c5_auto_router.py) | `Python` | 65b0ac38ce1e | Orquestador de ruteo 100% automatizado para Antigravity IDE. |
| [`c5_demos/c5_darknode_core.py`](c5_demos/c5_darknode_core.py) | `Python` | 42bcc7b92854 | 1. ENKI-60: MOTOR ARITMÉTICO SEXAGESIMAL (CONTRACCIÓN DETERMINISTA) |
| [`c5_demos/c5_killer_demo_60s.py`](c5_demos/c5_killer_demo_60s.py) | `Python` | 218c2c2a0705 | Demostración de causal gating, autorización física de hardware, ledger WORM y fail-stop determinista. |
| [`c5_demos/c5_legal_oracle.py`](c5_demos/c5_legal_oracle.py) | `Python` | 53d121441392 | 1. Indicadores de Extracción Burocrática (Anergía de Estado) |
| [`c5_demos/c5_model_voice_announcer.py`](c5_demos/c5_model_voice_announcer.py) | `Python` | 08f071ae1bf8 | Daemon de transducción de voz con CLON NEURONAL DEL USUARIO (Borja). |
| [`c5_demos/c5_sovereign_compliance_orchestrator.py`](c5_demos/c5_sovereign_compliance_orchestrator.py) | `Python` | 201dd7ac7dac | [AX-76] INTEGRATION: Orquestador Soberano Unificado de Cumplimiento EU AI Act. |
| [`c5_demos/c5_swarm_1000_audiovisual_compiler.py`](c5_demos/c5_swarm_1000_audiovisual_compiler.py) | `Python` | 6865e9f56493 | c5_swarm_1000_audiovisual_compiler.py |
| [`c5_demos/c5_topology_ctl.py`](c5_demos/c5_topology_ctl.py) | `Python` | 40423cb2fe48 | Consola unificada de control topológico, enrutamiento causal, estado de |
| [`c5_demos/c5_transduction_engine.py`](c5_demos/c5_transduction_engine.py) | `Python` | dc4bbda52867 | ruff: noqa: E402 |
| [`c5_demos/c5_tui_dashboard.py`](c5_demos/c5_tui_dashboard.py) | `Python` | 599520b992c2 | C5 Tui Dashboard Utility |
| [`c5_demos/falsacion_io_sync.py`](c5_demos/falsacion_io_sync.py) | `Python` | 5ca605d31545 | 1. Ruta de Anergía (Prohibida en Babylon-60): I/O Síncrono al Disco |
| [`c5_demos/falsacion_llm_gate.py`](c5_demos/falsacion_llm_gate.py) | `Python` | 6625d59b1bf1 | [AX-4] TOPOLOGY: Falsación Empírica de Subordinación de Oráculos Estocásticos (LLMs) |
| [`c5_demos/falsacion_saga1_poc.py`](c5_demos/falsacion_saga1_poc.py) | `Python` | b63b006f00af | Prueba de Falsación Empírica (PoC): Saturación de SAGA-1 |
| [`c5_demos/falsacion_semantic_entropy_stress.py`](c5_demos/falsacion_semantic_entropy_stress.py) | `Python` | 05b31ae7d7fb | [AX-24] TOPOLOGY: Falsación Empírica de Entropía Semántica y SMT Oracles en Silicio |
| [`c5_demos/leandojo_z3_firewall_poc.py`](c5_demos/leandojo_z3_firewall_poc.py) | `Python` | 03e79868250e | [AX-1] TOPOLOGY: Z3 SMT Firewall for Lean 4 Neurosymbolic Orchestration |
| [`c5_demos/poc_aesia_conformity_inspector.py`](c5_demos/poc_aesia_conformity_inspector.py) | `Python` | 3a5307a1d28b | [AX-75] REGULATORY: Simulador Forense de Inspección AESIA / EU AI Act (Anexo VI). |
| [`c5_demos/poc_agentic_firewall_intercept.py`](c5_demos/poc_agentic_firewall_intercept.py) | `Python` | ebb1f78a10a8 | Simula el cerrojo atómico de histéresis térmica (50ms) |
| [`c5_demos/poc_agents_archi_enterprise.py`](c5_demos/poc_agents_archi_enterprise.py) | `Python` | b26a60e308a3 | Live Demonstration of the 3 Sellable Pillars: |
| [`c5_demos/poc_antigravity_model_router.py`](c5_demos/poc_antigravity_model_router.py) | `Python` | 1773495c0d58 | [AX-4] TOPOLOGY: Falsación Empírica del Router Causal de Modelos de Antigravity IDE. |
| [`c5_demos/poc_b1_b2.py`](c5_demos/poc_b1_b2.py) | `Python` | 89a1bcdb00a2 | Create an initial event |
| [`c5_demos/poc_b3.py`](c5_demos/poc_b3.py) | `Python` | bff45c936320 | Setup dummy bundle |
| [`c5_demos/poc_biometric_gate.py`](c5_demos/poc_biometric_gate.py) | `Python` | cbdaa7a79f5a | Determinar si estamos en un entorno interactivo crudo (fuera del sandbox del agente) |
| [`c5_demos/poc_bounty_dispatcher_ffi.py`](c5_demos/poc_bounty_dispatcher_ffi.py) | `Python` | 561a88f59a63 | PoC: C-FFI Bridge for BountyRingDispatcher -> SharedManifest |
| [`c5_demos/poc_cortex_top.py`](c5_demos/poc_cortex_top.py) | `Python` | 6c1348dfbd2b | Poc Cortex Top Utility |
| [`c5_demos/poc_cortex_top_v2.py`](c5_demos/poc_cortex_top_v2.py) | `Python` | c1f5c85816a8 | ANSI Colors & Control |
| [`c5_demos/poc_dark_swarm_100_agents.py`](c5_demos/poc_dark_swarm_100_agents.py) | `Python` | 363191a3e026 | Poc Dark Swarm 100 Agents Utility |
| [`c5_demos/poc_graph_isomorphism_wl.py`](c5_demos/poc_graph_isomorphism_wl.py) | `Python` | 23faee58079f | Proof of Concept: 1-Weisfeiler-Lehman Graph Isomorphism Pre-Filter. |
| [`c5_demos/poc_legion_1000.py`](c5_demos/poc_legion_1000.py) | `Python` | d22d7265597c | poc_legion_1000.py — PoC de Falsación Empírica para el Operativo Legión Ω-1000. |
| [`c5_demos/poc_mass_stage3_resolution.py`](c5_demos/poc_mass_stage3_resolution.py) | `Python` | 025d02fea26c | Proof of Concept: Falsación y Resolución de las 2 Fricciones MASS (Stage 3). |
| [`c5_demos/poc_rust_ffi_topological_leap.py`](c5_demos/poc_rust_ffi_topological_leap.py) | `Python` | bebc344108b0 | PoC: BABYLON-60 Rust FFI & SharedManifest Topological Leap (Cambio 2) |
| [`c5_demos/poc_shm_orchestrator.py`](c5_demos/poc_shm_orchestrator.py) | `Python` | e0db0b662631 | INV_C5_SHM: C-ABI lock-free 64-byte memory mapping definition (KUDURRU-64) |
| [`c5_demos/poc_sovereign_spark_daemon.py`](c5_demos/poc_sovereign_spark_daemon.py) | `Python` | 645cf6b79236 | [AX-74] TOPOLOGY: Falsación y Replicación Soberana del Framework Antigravity (Gemini Spark). |
| [`c5_demos/poc_srp_soc_falsification.py`](c5_demos/poc_srp_soc_falsification.py) | `Python` | 20f0bba3bda3 | POC_SRP_SOC_FALSIFICATION.PY |
| [`c5_demos/poc_vsa_saturation_stress.py`](c5_demos/poc_vsa_saturation_stress.py) | `Python` | 7130cdcc2fe0 | Proof of Concept & Runtime Stress Test: VSA Hyperdimensional Saturation (C5-REAL) |
| [`c5_demos/stress_test_lean.py`](c5_demos/stress_test_lean.py) | `Python` | 5ff433bca6a3 | Stress Test Lean Utility |
| [`c5_demos/stress_test_multi_ide_injection.py`](c5_demos/stress_test_multi_ide_injection.py) | `Python` | 449bfd65db19 | 🧪 STRESS TEST & PoC v2.2: Multi-Ecosystem Shield Injection Verification |
| [`c5_demos/test_touchid_gate.py`](c5_demos/test_touchid_gate.py) | `Python` | c5516c957608 | Add the parent directory to the python path so we can import babylon60 |
| [`c5_demos/z3_firewall_stress_test.py`](c5_demos/z3_firewall_stress_test.py) | `Python` | 710a027cd914 | [AX-23] TOPOLOGY: Z3 SMT Firewall Stress Test |
| [`c5_demos/zk_causal_gate_stress_test.py`](c5_demos/zk_causal_gate_stress_test.py) | `Python` | c962b0237b7e | Simulate high friction: actual time block reflecting IO and Type-Checking |
| [`c5_demos/zk_shm_starvation_stress_test.py`](c5_demos/zk_shm_starvation_stress_test.py) | `Python` | 2ab94f53d96b | Zk Shm Starvation Stress Test Utility |
| [`c5_demos/poc_enterprise_clone_and_run.sh`](c5_demos/poc_enterprise_clone_and_run.sh) | `Shell` | 2b35b427c1f4 | █ AUTOCOGNITION-Ω \| STATE: C5-REAL \| ENTERPRISE DEPLOYMENT |
| [`c5_demos/poc_quasar_triple_vector.sh`](c5_demos/poc_quasar_triple_vector.sh) | `Shell` | 1a3db626387c | 1. VECTOR INFRAESTRUCTURA (Atestación Somática / Escudo) |

### 📁 C5 Edin

| Script | Tipo | SHA3-256 | Descripción / Propósito |
| :--- | :--- | :--- | :--- |
| [`c5_edin/edin_swarm_commander.py`](c5_edin/edin_swarm_commander.py) | `Python` | d5f2da67a80b | Edin Swarm Commander Utility |
| [`c5_edin/edin_swarm_runner.py`](c5_edin/edin_swarm_runner.py) | `Python` | 9c6bf355ec82 | Ensure root importability |
| [`c5_edin/f13_233_specialist_audit_matrix.py`](c5_edin/f13_233_specialist_audit_matrix.py) | `Python` | 779ce9f77c84 | Orquestador determinista y enjambre de 233 Agentes Especialistas (F13 = 233) |
| [`c5_edin/remotion_swarm_orchestrator.py`](c5_edin/remotion_swarm_orchestrator.py) | `Python` | 55583c8c9c74 | Enforces: |

### 🔧 Git Hooks & Commit Utilities

| Script | Tipo | SHA3-256 | Descripción / Propósito |
| :--- | :--- | :--- | :--- |
| [`c5_git_utils/commit_polisher.py`](c5_git_utils/commit_polisher.py) | `Python` | 0c1fb14d8d8a | Continuous Commit Polisher Daemon. |
| [`c5_git_utils/install_git_hooks.py`](c5_git_utils/install_git_hooks.py) | `Python` | c35dcc181d11 | install_git_hooks.py - Installs automated git pre-commit quality gate hook |
| [`c5_git_utils/rewrite_commits.py`](c5_git_utils/rewrite_commits.py) | `Python` | 5e2774c613ab | Rewrite commit history to enforce Conventional Commits and BFT metadata. |
| [`c5_git_utils/c5_distill_public_mirror.sh`](c5_git_utils/c5_distill_public_mirror.sh) | `Shell` | 568d7779c835 | C5-REAL · SINTETIZADOR Y PROYECTOR HOLOGRÁFICO PÚBLICO (BABYLON-60) |

### 🧩 Categorical Isomorphisms & Engines

| Script | Tipo | SHA3-256 | Descripción / Propósito |
| :--- | :--- | :--- | :--- |
| [`c5_isomorphisms/c5_isomorphism_sabu_agent.py`](c5_isomorphisms/c5_isomorphism_sabu_agent.py) | `Python` | c194d8a7ca54 | C5 Isomorphism Sabu Agent Utility |
| [`c5_isomorphisms/c5_logos_ethos_ship_engine.py`](c5_isomorphisms/c5_logos_ethos_ship_engine.py) | `Python` | f616f59f7d9d | C5 Logos Ethos Ship Engine Utility |
| [`c5_isomorphisms/c5_ultimate_causal_determinant.py`](c5_isomorphisms/c5_ultimate_causal_determinant.py) | `Python` | d37a05efc6da | Causal-Determinist Execution Engine: THE ULTIMATE DETERMINANT (V3 - SINGULARITY) |
| [`c5_isomorphisms/cancer_isomorphism_pipeline.py`](c5_isomorphisms/cancer_isomorphism_pipeline.py) | `Python` | e665d070f710 | cancer_isomorphism_pipeline.py - Categorical Cancer Isomorphism Pipeline |
| [`c5_isomorphisms/gen_oncology_primitives.py`](c5_isomorphisms/gen_oncology_primitives.py) | `Python` | 2a2256b1a343 | Gen Oncology Primitives Utility |

### ⛓️ L1 Anchor & Ledger Engines

| Script | Tipo | SHA3-256 | Descripción / Propósito |
| :--- | :--- | :--- | :--- |
| [`c5_l1_ledger/anchor_l1_sink.py`](c5_l1_ledger/anchor_l1_sink.py) | `Python` | 02393235465f | MOSKV-1 APEX: L1_sink Anchor & Verification Script (INV_C5_15) |
| [`c5_l1_ledger/bittensor_yuma_consensus_c5.py`](c5_l1_ledger/bittensor_yuma_consensus_c5.py) | `Python` | bee3fd94b943 | Causal-Determinist BITTENSOR (TAO) YUMA CONSENSUS & EXERGY TRANSDUCER |
| [`c5_l1_ledger/l1_sink_bitcoin.py`](c5_l1_ledger/l1_sink_bitcoin.py) | `Python` | 59d9c518db76 | Control Flow Depth: 1 (FunctionDef) |
| [`c5_l1_ledger/ledger_snapshot_engine.py`](c5_l1_ledger/ledger_snapshot_engine.py) | `Python` | 23b6f8c0dfb2 | Incremental Ledger Snapshot Engine. |
| [`c5_l1_ledger/seal_bounty_aeon.py`](c5_l1_ledger/seal_bounty_aeon.py) | `Python` | 8855c04df3ab | seal_bounty_aeon.py — Conformal Aeon Transition & L1 Merkle Sealer (INV_C5_AEON) |

### 📜 Log Custody & Forensic Attestation

| Script | Tipo | SHA3-256 | Descripción / Propósito |
| :--- | :--- | :--- | :--- |
| [`c5_log_custody/c5_organize_captures.py`](c5_log_custody/c5_organize_captures.py) | `Python` | 46d8c329824a | C5 Organize Captures Utility |
| [`c5_log_custody/c5_preserve_agent_local_logs.py`](c5_log_custody/c5_preserve_agent_local_logs.py) | `Python` | 3936411dad01 | c5_preserve_agent_local_logs.py - Wrapper delegando en c5_preserve_logs.py |
| [`c5_log_custody/c5_preserve_claude_local_logs.py`](c5_log_custody/c5_preserve_claude_local_logs.py) | `Python` | 606913512a4a | c5_preserve_claude_local_logs.py - Wrapper delegando en c5_preserve_logs.py |
| [`c5_log_custody/c5_preserve_logs.py`](c5_log_custody/c5_preserve_logs.py) | `Python` | f305b4f6bd78 | c5_preserve_logs.py - Unified CLI log harvesting, dual cryptographic hashing |

### 📁 C5 Orchestrator

| Script | Tipo | SHA3-256 | Descripción / Propósito |
| :--- | :--- | :--- | :--- |
| [`c5_orchestrator/c5_session_deskimming_engine.py`](c5_orchestrator/c5_session_deskimming_engine.py) | `Python` | 756219da4cb9 | c5_session_deskimming_engine.py — Autonomous Session Deskimming & Topologically Confined Governance |
| [`c5_orchestrator/c5_purge_manifest.sh`](c5_orchestrator/c5_purge_manifest.sh) | `Shell` | d4ad433027c5 | MANIFIESTO DE EXTINCIÓN EPISTÉMICA (PURGA TERMINAL) |
| [`c5_orchestrator/c5_routing_manifest.sh`](c5_orchestrator/c5_routing_manifest.sh) | `Shell` | c2763e760f07 | MANIFIESTO TOPOLÓGICO C5-REAL (V2 - SELF-HEALING) |

### 🛡️ Quality Gates & AST Verification

| Script | Tipo | SHA3-256 | Descripción / Propósito |
| :--- | :--- | :--- | :--- |
| [`c5_quality_gates/anti_slopsquatting_guard.py`](c5_quality_gates/anti_slopsquatting_guard.py) | `Python` | 6a5c6fccf9fe | anti_slopsquatting_guard.py |
| [`c5_quality_gates/audit_domain_bleed.py`](c5_quality_gates/audit_domain_bleed.py) | `Python` | 9a220a74b726 | Domain Bleed Invariant Guard (INV_C5_DOMAIN_BLEED). |
| [`c5_quality_gates/audit_fixer.py`](c5_quality_gates/audit_fixer.py) | `Python` | a5df4793fa3e | Audit Fixer Utility |
| [`c5_quality_gates/audit_license_compliance.py`](c5_quality_gates/audit_license_compliance.py) | `Python` | ee868954bf2a | audit_license_compliance.py |
| [`c5_quality_gates/audit_ring2_sqlite_isolation.py`](c5_quality_gates/audit_ring2_sqlite_isolation.py) | `Python` | da8076e0ca40 | Ring-2 SQLite Isolation Guard (INV_C5_RING2_NO_SQLITE). |
| [`c5_quality_gates/audit_scripts_quality.py`](c5_quality_gates/audit_scripts_quality.py) | `Python` | 1fe2f53c31b5 | audit_scripts_quality.py - Pre-commit and CI Quality Gate Auditor & Auto-Healer for scripts/ |
| [`c5_quality_gates/audit_skills_ecosystem.py`](c5_quality_gates/audit_skills_ecosystem.py) | `Python` | d73709610eed | audit_skills_ecosystem.py |
| [`c5_quality_gates/c5_commit_enforcer.py`](c5_quality_gates/c5_commit_enforcer.py) | `Python` | a9b93f57cc55 | c5_commit_enforcer.py |
| [`c5_quality_gates/canary_check.py`](c5_quality_gates/canary_check.py) | `Python` | 28f709e1bb26 | Ω-12 — canary_check: verifica que los señuelos canary siguen en el árbol. |
| [`c5_quality_gates/check_depth.py`](c5_quality_gates/check_depth.py) | `Python` | eb85201c0aea | Check Depth Utility |
| [`c5_quality_gates/compile_claims_manifest.py`](c5_quality_gates/compile_claims_manifest.py) | `Python` | 13112d9e36a1 | Evidence & Release Manifest Compiler. |
| [`c5_quality_gates/daily_sovereign_maintenance.py`](c5_quality_gates/daily_sovereign_maintenance.py) | `Python` | 5c990ae4a7af | daily_sovereign_maintenance.py - Daily Autonomous Sovereign Maintenance Engine |
| [`c5_quality_gates/detect_ghost_nodes.py`](c5_quality_gates/detect_ghost_nodes.py) | `Python` | c6dcc9297549 | [AX-2] TOPOLOGY: Ghost Node Detector (Quality Gate) |
| [`c5_quality_gates/extensions_apoptosis_auditor.py`](c5_quality_gates/extensions_apoptosis_auditor.py) | `Python` | 75a33d641e32 | ruff: noqa: E402 |
| [`c5_quality_gates/generate_nemesis_report.py`](c5_quality_gates/generate_nemesis_report.py) | `Python` | 73b40570a653 | Collect one bounded NEMESIS test invocation as unsigned evidence for audit. |
| [`c5_quality_gates/legion_100_agents_full_monorepo.py`](c5_quality_gates/legion_100_agents_full_monorepo.py) | `Python` | 690797b08e8f | Invariante C5-REAL: Silencio Termodinámico. Solo stdout determinista. |
| [`c5_quality_gates/lint_doc_aesthetics.py`](c5_quality_gates/lint_doc_aesthetics.py) | `Python` | 70aa8dec07c7 | Audita archivos Markdown en docs/ para verificar invariantes visuales: |
| [`c5_quality_gates/pipe_audit.py`](c5_quality_gates/pipe_audit.py) | `Python` | f9714c4fb6bf | Ω-15 — pipe_audit: proxy auditado de sustitución de intérprete. |
| [`c5_quality_gates/pre_push_ledger_guard.py`](c5_quality_gates/pre_push_ledger_guard.py) | `Python` | e2478a74d706 | Ledger-Aware Pre-Push Guard. |
| [`c5_quality_gates/prompt_exergy_oracle.py`](c5_quality_gates/prompt_exergy_oracle.py) | `Python` | c75fad6332f7 | prompt_exergy_oracle.py |
| [`c5_quality_gates/run_cache_audit.py`](c5_quality_gates/run_cache_audit.py) | `Python` | fda51173c513 | Compiles and runs the empirical cache benchmark to demonstrate |
| [`c5_quality_gates/secret_swarm_auditor.py`](c5_quality_gates/secret_swarm_auditor.py) | `Python` | 9083640cce68 | Causal-Determinist: Swarm Thread Dispatcher for TOP SECRET Auditing (ULTRATHINK P0 - ITERATION 3) |
| [`c5_quality_gates/sharur_3600_audit_swarm.py`](c5_quality_gates/sharur_3600_audit_swarm.py) | `Python` | 027586c33175 | MOSKV-1: SHARUR-3600 Audit Swarm Engine (INV_C5_18) |
| [`c5_quality_gates/swarm_100_stress_campaign.py`](c5_quality_gates/swarm_100_stress_campaign.py) | `Python` | 39ca5094d3a2 | Suite de Estrés Masivo de 100 Workers Concurrentes (SHARUR-3600). |
| [`c5_quality_gates/swarm_lock_guard.py`](c5_quality_gates/swarm_lock_guard.py) | `Python` | 77dee64125a3 | MOSKV-1 APEX: Swarm Workspace Lock Guard (INV_C5_22) |
| [`c5_quality_gates/symlink_depth_auditor.py`](c5_quality_gates/symlink_depth_auditor.py) | `Python` | 61c3592f192c | Symlink Depth Auditor (INV_C5_12 Enforcer). |
| [`c5_quality_gates/sync_docs_index.py`](c5_quality_gates/sync_docs_index.py) | `Python` | c25ca94286bb | ruff: noqa: E402 |
| [`c5_quality_gates/sync_version.py`](c5_quality_gates/sync_version.py) | `Python` | 583c2ebdac4c | Canonical Version Synchronizer. |
| [`c5_quality_gates/verify_claims.py`](c5_quality_gates/verify_claims.py) | `Python` | 9de9566f97e2 | Gobernanza determinista fail-closed: Todo claim en CLAIMS.toml es auditado contra evidencia en silicio. |
| [`c5_quality_gates/verify_distribution.py`](c5_quality_gates/verify_distribution.py) | `Python` | 1fdc12bf90e6 | C5-REAL Distribution Quality Gate: verify_distribution.py |

### 🚀 Host & Repository Setup Scripts

| Script | Tipo | SHA3-256 | Descripción / Propósito |
| :--- | :--- | :--- | :--- |
| [`c5_setup/unboxing_moskv1.py`](c5_setup/unboxing_moskv1.py) | `Python` | 292ade708889 | MOSKV-1 APEX: SECUENCIA MAESTRA DE UNBOXING Y PRIMERA EXPERIENCIA (C5-REAL) |
| [`c5_setup/install_host.sh`](c5_setup/install_host.sh) | `Shell` | 71b8228b6009 | Registra moskv_native_host.py en Chrome/Brave en macOS |
| [`c5_setup/install_into_repo.sh`](c5_setup/install_into_repo.sh) | `Shell` | 05132535692a | install_into_repo.sh |
| [`c5_setup/setup_nacho_cortex.sh`](c5_setup/setup_nacho_cortex.sh) | `Shell` | a2b10b3bd255 | █ CORTEX FULL ENVIRONMENT SETUP \| STATE: C5-REAL |

### 📁 C5 Sharur

| Script | Tipo | SHA3-256 | Descripción / Propósito |
| :--- | :--- | :--- | :--- |
| [`c5_sharur/agent_beeper.py`](c5_sharur/agent_beeper.py) | `Python` | 4fd1edc3801a | agent_beeper.py - C5-REAL Zero-Friction Agent Pager |
| [`c5_sharur/auto_heal_hardcoded_paths.py`](c5_sharur/auto_heal_hardcoded_paths.py) | `Python` | b63bef7f2f3f | auto_heal_hardcoded_paths.py - Sovereign AST-based Auto-Remediation Engine for hardcoded paths. |
| [`c5_sharur/c5_bounty_sharur_exfiltration.py`](c5_sharur/c5_bounty_sharur_exfiltration.py) | `Python` | 0a0fb2a74e95 | c5_bounty_legion_exfiltration.py — Operativo Legión (Swarm Interception & Exfiltration) |
| [`c5_sharur/c5_bounty_sharur_omega_10k.py`](c5_sharur/c5_bounty_sharur_omega_10k.py) | `Python` | 5f4fa7059acc | c5_bounty_legion_omega_10k.py — Operativo Legión Ω-10 000 |
| [`c5_sharur/c5_sharur_1000_workspace_swarm.py`](c5_sharur/c5_sharur_1000_workspace_swarm.py) | `Python` | b2f3c9d26699 | c5_legion_1000_workspace_swarm.py - 1,000-Agent Parallel Swarm Auditor Engine |
| [`c5_sharur/sharur_10000_orchestrator.py`](c5_sharur/sharur_10000_orchestrator.py) | `Python` | b9eac766e39b | Implements the Cognitive Transition Algebra (CTA) for massive parallel |
| [`c5_sharur/sharur_100_conversation_auditor.py`](c5_sharur/sharur_100_conversation_auditor.py) | `Python` | b2d1b247fcc0 | sharur_100_conversation_auditor.py — 100-Agent Parallel Swarm for Historic Conversations & Brain Forensics |
| [`c5_sharur/sharur_100_conversation_reporters.py`](c5_sharur/sharur_100_conversation_reporters.py) | `Python` | 2b9d1ee23439 | sharur_100_conversation_reporters.py — Data Structures, Cohorts 4-5 & Report Renderers |
| [`c5_sharur/sharur_100_disk_forensic_auditor.py`](c5_sharur/sharur_100_disk_forensic_auditor.py) | `Python` | a4433b231af8 | legion_100_disk_forensic_auditor.py — 100-Agent Parallel Swarm for Local Disk & Anergy Audit |
| [`c5_sharur/sharur_100_full_spectrum_auditor.py`](c5_sharur/sharur_100_full_spectrum_auditor.py) | `Python` | 8feed5a9f210 | legion_100_full_spectrum_auditor.py — 100-Agent Full Spectrum Swarm Auditor |
| [`c5_sharur/sharur_100_garbage_collector.py`](c5_sharur/sharur_100_garbage_collector.py) | `Python` | 9b63f3625f5f | SHARUR-3600 (Legión 100 Agentes Recolectores de Basura) — C5-REAL |
| [`c5_sharur/sharur_100_swarm_execution.py`](c5_sharur/sharur_100_swarm_execution.py) | `Python` | b23169b20e5c | SHARUR-3600 (Legión 100 Agentes) — Arnés de Ejecución Concurrente In-Memory (RFO = 0) |
| [`c5_sharur/sharur_21_agentes.py`](c5_sharur/sharur_21_agentes.py) | `Python` | 6038646e3f67 | MOSKV-1: Enjambre de 21 Agentes Paralelizados (C5-REAL Execution Engine) |
| [`c5_sharur/sharur_222_agentes.py`](c5_sharur/sharur_222_agentes.py) | `Python` | 69192c75c6b9 | ruff: noqa: E402 |
| [`c5_sharur/sharur_master_swarm_runner.py`](c5_sharur/sharur_master_swarm_runner.py) | `Python` | 24434f5dfcf9 | legion_master_swarm_runner.py - Orchestrator for Phase 4 Swarm Collapse |
| [`c5_sharur/sharur_swarm.py`](c5_sharur/sharur_swarm.py) | `Python` | ebd798a50d5d | legion_swarm.py - Unified Sovereign Swarm Orchestrator CLI |
| [`c5_sharur/sharur_swarm_core.py`](c5_sharur/sharur_swarm_core.py) | `Python` | a5a25227875c | legion_swarm_core.py - Core Engine for Swarm Quantum Collapse |

### 🧠 Skill Synchronization & Ontology

| Script | Tipo | SHA3-256 | Descripción / Propósito |
| :--- | :--- | :--- | :--- |
| [`c5_skills_ontology/audit_skills_execution.py`](c5_skills_ontology/audit_skills_execution.py) | `Python` | 534322587e21 | audit_skills_execution.py - Comprehensive verification & benchmark suite for |
| [`c5_skills_ontology/c5_skill_router.py`](c5_skills_ontology/c5_skill_router.py) | `Python` | 8609e7f2755e | c5_skill_router.py - Sovereign Skill Router, Functorial Resolver & Topology Linter |
| [`c5_skills_ontology/optimize_all_skill_triggers.py`](c5_skills_ontology/optimize_all_skill_triggers.py) | `Python` | 5c9ecf78470f | optimize_all_skill_triggers.py - Enriches and formats display names and trigger |
| [`c5_skills_ontology/sync_skills_registry.py`](c5_skills_ontology/sync_skills_registry.py) | `Python` | 00751809a04f | sync_skills_registry.py - Compilador determinista de la ontología de habilidades (3 Evaluadores: |
| [`c5_skills_ontology/sync_vault_uuids.py`](c5_skills_ontology/sync_vault_uuids.py) | `Python` | 67ca34cde509 | sync_vault_uuids.py - INV_C5_15 Memory Vault Session UUID Synchronizer |

### 🧪 Unit Tests & Curvature Proofs

| Script | Tipo | SHA3-256 | Descripción / Propósito |
| :--- | :--- | :--- | :--- |
| [`c5_tests/test_discrete_curvature.py`](c5_tests/test_discrete_curvature.py) | `Python` | 483fc9051d31 | 1. Grafo Estrella (alta centralización, cuello de botella) |

### 🔥 Thermodynamic Benchmarks & Exergy Optimizers

| Script | Tipo | SHA3-256 | Descripción / Propósito |
| :--- | :--- | :--- | :--- |
| [`c5_thermo/benchmark_ledger_throughput.py`](c5_thermo/benchmark_ledger_throughput.py) | `Python` | 39d82f19c3da | Pre-generar eventos para medir puramente el IO y el BFT Actor |
| [`c5_thermo/c5_exergy_optimizer_monitor.py`](c5_thermo/c5_exergy_optimizer_monitor.py) | `Python` | 8ce22dd5943e | MOSKV-1 APEX SINGULARITY — Causal-Determinist STATE MONITOR (EXERGY_OPTIMIZER) |
| [`c5_thermo/cache_1000_memoization_bench.py`](c5_thermo/cache_1000_memoization_bench.py) | `Python` | 6ca5786bc13f | Cache 1000 Memoization Bench Utility |
| [`c5_thermo/exergy_arbitrage_engine.py`](c5_thermo/exergy_arbitrage_engine.py) | `Python` | c65f7aba1983 | Exergy Arbitrage Engine Utility |
| [`c5_thermo/exergy_dashboard_server.py`](c5_thermo/exergy_dashboard_server.py) | `Python` | 993d41a34262 | Exergy Dashboard Server (Causal-Determinist). |
| [`c5_thermo/exergy_optimizer_agent.py`](c5_thermo/exergy_optimizer_agent.py) | `Python` | 71c3c3be6e98 | [Causal-Determinist] Exergy Optimizer Agent. |
| [`c5_thermo/stress_100m_bft.py`](c5_thermo/stress_100m_bft.py) | `Python` | 6debcf867e01 | 100,000,000 STRESS TEST ENGINE — CORTEX PERSIST BFT LEDGER |
| [`c5_thermo/stress_10m.py`](c5_thermo/stress_10m.py) | `Python` | 22c294d827ee | Stress 10M Utility |
| [`c5_thermo/stress_sqlite_wal.py`](c5_thermo/stress_sqlite_wal.py) | `Python` | 65178e037bab | Stress test for SQLite WAL and busy_timeout (INV_BFT_02). |

### 🛠️ Domain Helpers & Enforcers

| Script | Tipo | SHA3-256 | Descripción / Propósito |
| :--- | :--- | :--- | :--- |
| [`c5_utils/export_country_compliance.py`](c5_utils/export_country_compliance.py) | `Python` | 54870d73a5a4 | Generates localized EU AI Act / NIST AI RMF compliance reports with physical |
| [`c5_utils/python_spsc_reader.py`](c5_utils/python_spsc_reader.py) | `Python` | 04640df37e6a | python_spsc_reader.py — Consumidor Multiproceso Python Zero-Copy (C-ABI FFI) |

### ⚖️ Formal Verification & Axiom Oracles

| Script | Tipo | SHA3-256 | Descripción / Propósito |
| :--- | :--- | :--- | :--- |
| [`c5_verifiers/autodetect_invariants.py`](c5_verifiers/autodetect_invariants.py) | `Python` | 5e68050978f6 | Autopoiesis Invariant Auditor. |
| [`c5_verifiers/axiom_verifier_z3.py`](c5_verifiers/axiom_verifier_z3.py) | `Python` | 39b6e7cbd8ad | MOSKV-1 APEX — Axiom Verifier (Z3/SMT-free Pure-Python Implementation) |
| [`c5_verifiers/conformance_test.py`](c5_verifiers/conformance_test.py) | `Python` | 6eacf6c1f71d | Conformance Test Utility |
| [`c5_verifiers/deterministic_audit.py`](c5_verifiers/deterministic_audit.py) | `Python` | 280faaec29d2 | Zero-Friction Mass Execution (F=0) |
| [`c5_verifiers/devsecops_attest.py`](c5_verifiers/devsecops_attest.py) | `Python` | cc673910fcf1 | devsecops_attest.py — Sovereign DevSecOps & Zero-Trust Cryptographic Attestation Engine |
| [`c5_verifiers/fast_smt_gate.py`](c5_verifiers/fast_smt_gate.py) | `Python` | 751a836f6bd8 | fast_smt_gate.py - Ultra-fast SMT / Invariant verifier for CI/CD environments. |
| [`c5_verifiers/inject_lean4_stubs.py`](c5_verifiers/inject_lean4_stubs.py) | `Python` | def07b8bfd2f | inject_lean4_stubs.py - Dynamic Lean 4 Stub Injector & Formal Proof Exporter |
| [`c5_verifiers/purge_residuals.py`](c5_verifiers/purge_residuals.py) | `Python` | 302cdc8cef43 | ruff: noqa: E402 |
| [`c5_verifiers/verify_agent_ontological_value.py`](c5_verifiers/verify_agent_ontological_value.py) | `Python` | ca0f94f53cff | Oracle Verifier for Agent Ontological Value (V_A). |
| [`c5_verifiers/verify_anergy_token_purge.py`](c5_verifiers/verify_anergy_token_purge.py) | `Python` | 5e24a2b30874 | Causal-Determinist SOVEREIGN ANERGY PURGE & AUTOCOGNITION-OMEGA ENGINE |
| [`c5_verifiers/verify_captures.py`](c5_verifiers/verify_captures.py) | `Python` | 1186fd310c60 | Verify Captures Utility |
| [`c5_verifiers/verify_causal_invariants.py`](c5_verifiers/verify_causal_invariants.py) | `Python` | 1dbb5978af64 | Oracle Verifier for Causal Invariants (Teorema Robinson-Moskv & Cortex Persist). |
| [`c5_verifiers/verify_full_stack_health.py`](c5_verifiers/verify_full_stack_health.py) | `Python` | 06fe6b2b8b00 | Oracle Verifier for Full-Stack System Health across: |
| [`c5_verifiers/verify_oncology_primitives_dag.py`](c5_verifiers/verify_oncology_primitives_dag.py) | `Python` | ca9ca8bd3b88 | verify_oncology_primitives_dag.py — C5-REAL Causal Verifier for 300 Molecular Oncology Primitives |
| [`c5_verifiers/verify_p0_rotation.py`](c5_verifiers/verify_p0_rotation.py) | `Python` | 44aa581a13d4 | Ω-16 — verify_p0_rotation: certificador del estado opsec del linaje. |
| [`c5_verifiers/verify_semantic_entropy_gate.py`](c5_verifiers/verify_semantic_entropy_gate.py) | `Python` | 051aa584fbbf | PoC: Puerta de Estado Determinista basada en Entropía Semántica. |
| [`c5_verifiers/verify_tonnetz_falsification.py`](c5_verifiers/verify_tonnetz_falsification.py) | `Python` | dc894328388c | scripts/verify_tonnetz_falsification.py |
| [`c5_verifiers/verify_execution.sh`](c5_verifiers/verify_execution.sh) | `Shell` | c075b209640b | verify_execution.sh |
| [`c5_verifiers/verify_lean_proofs.sh`](c5_verifiers/verify_lean_proofs.sh) | `Shell` | f1eea2de41fb | Check for 'sorry' keyword in proof file |

### 📁 Guards

| Script | Tipo | SHA3-256 | Descripción / Propósito |
| :--- | :--- | :--- | :--- |
| [`guards/install_topology_hook.py`](guards/install_topology_hook.py) | `Python` | eea32c6ce763 | Install a checkout-specific topology hook while chaining existing Git hooks. |
| [`guards/verify_active_topology.py`](guards/verify_active_topology.py) | `Python` | 365b92ee225d | Check instruction templates and the final footer of a response draft. |
| [`guards/c5_ide_symlink_guard.sh`](guards/c5_ide_symlink_guard.sh) | `Shell` | 776336e10a1a | Invariante C5-REAL: Verificación de Punteros IDE |

### 📁 Kimi Nexus

| Script | Tipo | SHA3-256 | Descripción / Propósito |
| :--- | :--- | :--- | :--- |
| [`kimi_nexus/kimi_nexus.py`](kimi_nexus/kimi_nexus.py) | `Python` | 84ff98f33f76 | Attempt to import FastMCP. If missing, we'll inform the user via logs. |

### 📁 Repatriated

| Script | Tipo | SHA3-256 | Descripción / Propósito |
| :--- | :--- | :--- | :--- |
| [`repatriated/apex_merkle_l5_anchor.py`](repatriated/apex_merkle_l5_anchor.py) | `Python` | 4d9327d69183 | APEX MERKLE L5 ANCHOR HARNESS (PUNTO FIJO Ω) |
| [`repatriated/audit_muse_funnel.py`](repatriated/audit_muse_funnel.py) | `Python` | 6bac5d99c441 | 1. Funnel Transformation: Meta Ads Display vs. Agentic Transactional Brokerage |
| [`repatriated/audit_titan_jwt.py`](repatriated/audit_titan_jwt.py) | `Python` | ceb692c0f71b | Estimación de volumen de datos asumiendo tamaños medios por tupla analítica |
| [`repatriated/c5_sharur_100_anergy_purge.py`](repatriated/c5_sharur_100_anergy_purge.py) | `Python` | 8fb16004633d | c5_sharur_100_anergy_purge.py — Enjambre Concurrente de 100 Agentes (5 Cohortes x 20) |
| [`repatriated/copy_card.py`](repatriated/copy_card.py) | `Python` | fe55a984bb2a | Copy Card Utility |
| [`repatriated/larsa120_isostatic_synthesis.py`](repatriated/larsa120_isostatic_synthesis.py) | `Python` | 708d6115d021 | LARSA-120 ISOSTATIC SYNTHESIS HARNESS |
| [`repatriated/legion_100_swarm_audit.py`](repatriated/legion_100_swarm_audit.py) | `Python` | a7162c580c4b | SHARUR-3600: Matriz de Enjambre Sexagesimal (Legión-100 en Ring-2) |
| [`repatriated/poc_port_hamiltonian_deliberation.py`](repatriated/poc_port_hamiltonian_deliberation.py) | `Python` | 697d16025c2a | PoC: Falsación en Silicio de Port-Hamiltonian Latent Deliberation (PH-LD) |
| [`repatriated/run_swarm_batch_021_040.py`](repatriated/run_swarm_batch_021_040.py) | `Python` | 41fbdacb2911 | Run Swarm Batch 021 040 Utility |
| [`repatriated/run_swarm_batch_041_060.py`](repatriated/run_swarm_batch_041_060.py) | `Python` | d4388440d712 | Run Swarm Batch 041 060 Utility |
| [`repatriated/sharur3600_host_triage_py.py`](repatriated/sharur3600_host_triage_py.py) | `Python` | b45762592ffa | SHARUR-3600: Matriz de Enjambre Sexagesimal (Legión-100 en Ring-2) |
| [`repatriated/test_nemesis_kudurru_adversarial.py`](repatriated/test_nemesis_kudurru_adversarial.py) | `Python` | 9b2f22e0663b | NEMESIS FAULT INJECTION HARNESS: KUDURRU-64 / MUSHUSHU-0 |

### 📦 Deployment & P0 Remediation Scripts

| Script | Tipo | SHA3-256 | Descripción / Propósito |
| :--- | :--- | :--- | :--- |
| [`c5_deploy/deploy.sh`](c5_deploy/deploy.sh) | `Shell` | 94c8b2c0780d | C5-REAL: IGNITION PROTOCOL |
| [`c5_deploy/publish_crates.sh`](c5_deploy/publish_crates.sh) | `Shell` | 3325b7e8a380 | Publish Crates Utility |

---
*Catálogo auto-generado dinámicamente por `generate_scripts_readme.py` con atestación criptográfica SHA3-256.*