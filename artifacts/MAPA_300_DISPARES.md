<!-- C5-REAL EXERGY CERTIFIED -->

# MAPA DE 300 COSAS HYPER DISPARES

> **Almanaque celeste del monorepo `Teorema-Robinson-Moskv`**
> Catálogo de 300 objetos reales, mutuamente inconexos, trazados desde el árbol de git.

| Campo | Valor |
| :--- | :--- |
| Designación | `TRM-ATLAS-300` |
| Época de observación | 2026-07-29 |
| Rama | `master` |
| Ciclo BFT | 500 (`Hash: 0d1f6a7f`) |
| Objetos catalogados | 300 únicos, sin repetición entre constelaciones |
| Constelaciones | 15 × 20 |
| Método | Enumeración directa de `git ls-files` (35.058 rutas) + inspección de esquema SQLite + censo de extensiones |
| Atlas interactivo | https://claude.ai/code/artifact/d29d6348-7d35-46ef-93eb-d93e584514c1 |

---

## CENSO DE FONDO

| Magnitud | Medida |
| :--- | ---: |
| Archivos versionados | 35.058 |
| Tipos de archivo distintos | ~60 |
| Lenguajes vivos | 15+ |
| Solidity (`.sol`) | 5.154 |
| Python (`.py`) | 4.146 |
| Markdown (`.md`) | 3.446 |
| Rust (`.rs`) | 3.425 |
| TypeScript (`.ts`) | 3.004 |
| Archivos `.zip` versionados | 1.652 |
| Sellos OpenTimestamps (`.ots`) | 218 |
| Ledgers SQLite activos | 20+ |
| Workflows CI | 14 (propios) |
| Symlinks de dominio en raíz | 28 |

---

## SISTEMA DE COORDENADAS

Las coordenadas usan designaciones abreviadas de estrato:

```
Ω   →  raíz del repositorio
BE  →  0_Buzon_Entrada/
OA  →  1_Operaciones_Activas/
NE  →  2_Nucleo_Estatico/
HI  →  3_Historico_Inerte/
IS  →  OA/01_INTEL_SUITE/
CX  →  OA/02_CORTEX_ENGINE/
MS  →  OA/03_MOSKV_STUDIO/
LR  →  OA/04_LABORATORIO_RD/
BB  →  CX/BABYLON-60/
BT  →  CX/cortex-bounties/
```

---

## I · LENGUAJES Y RUNTIMES
> Quince sintaxis vivas bajo un mismo árbol de git — de Lean 4 a FunC.
> **Objetos 001–020**

| № | Objeto | Clase | Coordenada |
| ---: | :--- | :--- | :--- |
| 001 | Python 3.12 | núcleo | `Ω/pyproject.toml` |
| 002 | Rust · Cargo · PyO3 | núcleo | `LR/strike-rs/` |
| 003 | TypeScript · React 18 | núcleo | `MS/src/App.tsx` |
| 004 | Go 1.21 · daemon portal | núcleo | `OA/cmd/portal_daemon/main.go` |
| 005 | F# · .NET 10 | algebraico | `Ω/fsharp_kernel/fsharp_kernel.fsproj` |
| 006 | Haskell | funcional | `NE/primitives/Haskell1000.hs` |
| 007 | Clojure · metamembrana Lisp | funcional | `BB/lisp_metamembrane/src/metamembrane/core.clj` |
| 008 | Solidity (5.154 archivos) | contrato | `BT/bbp-public-assets/contracts/` |
| 009 | Move · Aptos | contrato | `BT/targets/layerzero-v2/` |
| 010 | FunC · TON | contrato | `BT/targets/layerzero-v2/` |
| 011 | Clarity · Stacks | contrato | `BT/targets/bitflow-dlmm/clarity/contracts/` |
| 012 | SystemVerilog · RTL | hardware | `BT/targets/firedancer-v1/src/wiredancer/rtl/` |
| 013 | C++ · compilador AST | sistemas | `LR/moskv-1-apex/kernel/ast_compiler.cpp` |
| 014 | Lean 4 | prueba formal | `NE/axioms/RobinsonResolution.lean` |
| 015 | Prolog | lógica | `NE/axioms/robinson_resolution.pl` |
| 016 | Astro | web | `CX/cortex-hustle/cortex_hustle/hustle.astro` |
| 017 | CESL · kernel v1 | DSL propio | `CX/cortex/cesl/kernel_v1.cesl` |
| 018 | Moskv84 · gramática tree-sitter | DSL propio | `LR/tree-sitter-moskv84/src/` |
| 019 | CodeQL | consulta estática | `BT/targets/firedancer-v1/contrib/codeql/src/dev/` |
| 020 | Handlebars | plantilla | `BT/bbp-public-assets/contracts/lib/openzeppelin-contracts/docs/templates/` |

---

## II · MOTORES CORTEX
> El núcleo cognitivo BFT: inferencia activa, compilación de teoremas, máquinas abstractas.
> **Objetos 021–040**

| № | Objeto | Clase | Coordenada |
| ---: | :--- | :--- | :--- |
| 021 | `active_inference_engine.py` | motor | `CX/cortex/engines/` |
| 022 | `bft_orchestrator.py` | motor | `CX/cortex/engines/` |
| 023 | `categorical_896_engine.py` | motor | `CX/cortex/engines/` |
| 024 | `entropy_mapping_engine.py` | motor | `CX/cortex/engines/` |
| 025 | `escohotado_chaos_engine.py` | motor | `CX/cortex/engines/` |
| 026 | `escohotado_market_prohibition_engine.py` | motor | `CX/cortex/engines/` |
| 027 | `knowledge_kernel_engine.py` | motor | `CX/cortex/engines/` |
| 028 | `mcts_vnode_compiler.py` | motor | `CX/cortex/engines/` |
| 029 | `subadditivity_verifier.py` | motor | `CX/cortex/engines/` |
| 030 | `vibe_ide_engine.py` | motor | `CX/cortex/engines/` |
| 031 | `compiled_theorem.py` | motor | `CX/cortex/compiled_theorem.py` |
| 032 | `kernel.py` | sistema operativo | `CX/cortex/os/` |
| 033 | `scheduler.py` | sistema operativo | `CX/cortex/os/` |
| 034 | `gc.py` | sistema operativo | `CX/cortex/os/` |
| 035 | `memory.py` | sistema operativo | `CX/cortex/os/` |
| 036 | `syscalls.py` | sistema operativo | `CX/cortex/os/` |
| 037 | `collision.py` | hipervisor | `CX/cortex/hypervisor/` |
| 038 | CAM · máquina categórica | máquina abstracta | `CX/cortex/cam/machine.py` |
| 039 | AEM · máquina de efectos | máquina abstracta | `CX/cortex/aem/machine.py` |
| 040 | Compilador CESL | compilador | `CX/cortex/cesl/compiler.py` |

---

## III · LEDGERS SQLITE
> Colas BFT, memoria de agentes y registros de fraude materializados en disco.
> **Objetos 041–060**

| № | Objeto | Clase | Coordenada |
| ---: | :--- | :--- | :--- |
| 041 | `master_ledger.db` — 28 KB, 3 tablas | ledger maestro | `Ω/` |
| 042 | `ultrathink_scheduler_ledger.db` — 4,0 MB | ledger de ciclos | `Ω/` |
| 043 | `agent_memory.db` — 24 MB, tabla `decisions` | memoria | `Ω/db/` |
| 044 | `memory.db` — 4,3 MB, tabla `decisions` | memoria | `Ω/db/` |
| 045 | `stress_ledger.db` — 716 KB | estrés | `Ω/` |
| 046 | `swarm_stress_ledger.db` — 44 KB | estrés de enjambre | `Ω/` |
| 047 | `unified_ledger.db` — 20 KB | unificado | `Ω/` |
| 048 | `atomic_recovery_test.db` — 20 KB | recuperación atómica | `Ω/` |
| 049 | `cortex_bft_ledger.db` — 0 B | ledger BFT (vacío) | `Ω/` |
| 050 | `cdp_ledger.db` — tabla `cdp_events` | eventos CDP | `Ω/db/` |
| 051 | `centuria_github.db` — 384 KB | primitivas GitHub | `Ω/db/` |
| 052 | `playwright_primitives.db` — 148 KB | primitivas DOM | `Ω/db/` |
| 053 | `escohotado_chaos_entropy.db` — `chaos_metrics` | ontología | `HI/ledgers/` |
| 054 | `escohotado_economics.db` — `prohibition_economics` | ontología | `HI/ledgers/` |
| 055 | `escohotado_substance.db` — `substance_ontology` | ontología | `HI/ledgers/` |
| 056 | `byzantine_test.db` | arnés bizantino | `Ω/.cortex/` |
| 057 | `replay_test.db` | arnés de replay | `Ω/.cortex/` |
| 058 | `stress_c6.db` | arnés C6 | `Ω/.cortex/` |
| 059 | `categorical_896_ledger.db` | primitivas categóricas | `CX/cortex/primitives/` |
| 060 | `mundo_f_ledger.yml` — 223 KB | ledger textual | `Ω/` |

---

## IV · OBJETIVOS DE BOUNTY
> Superficie adversarial externa: contratos y protocolos de cadena bajo auditoría.
> **Objetos 061–080**

| № | Objeto | Clase | Coordenada |
| ---: | :--- | :--- | :--- |
| 061 | `base-azul` | L2 · Base | `BT/base-azul/` |
| 062 | `chainlink` | oráculo | `BT/targets/chainlink/` |
| 063 | `firedancer-v1` | validador Solana | `BT/targets/firedancer-v1/` |
| 064 | `layerzero-v2` | puente omnichain | `BT/targets/layerzero-v2/` |
| 065 | `lido` | staking líquido | `BT/targets/lido/` |
| 066 | `kamino` | DeFi Solana | `BT/targets/kamino/` |
| 067 | `pancakeswap` | DEX | `BT/targets/pancakeswap/` |
| 068 | `exactly-protocol` | préstamo | `BT/targets/exactly-protocol/` |
| 069 | `bitflow-dlmm` | DLMM · Stacks | `BT/targets/bitflow-dlmm/` |
| 070 | `intuition-contracts-v2` | contratos | `BT/targets/intuition-contracts-v2/` |
| 071 | `intuition-bug-bounty` | programa | `BT/targets/intuition-bug-bounty/` |
| 072 | `kite-ai` | IA on-chain | `BT/kite-ai/` |
| 073 | `folks-finance` | competición | `BT/competitions/folks-finance/` |
| 074 | `2026-05-eigenlayer-avs` | competición | `BT/competitions/` |
| 075 | `2026-04-k2` | préstamo K2 | `BT/targets/2026-04-k2/` |
| 076 | `attackathon-\|-ethereum-protocol` | L1 | `BT/targets/` |
| 077 | `exploit-lab` | laboratorio fuzz | `BT/exploit-lab/` |
| 078 | `cortex_mev_base` | MEV | `BT/cortex_mev_base/` |
| 079 | `ouroboros-matrix` | motor de envío | `BT/ouroboros-matrix/` |
| 080 | `CORTEX_IMMUNEFI_SUBMISSIONS_FOLKS_FINANCE.zip` | dossier | `BT/` |

---

## V · AXIOMAS E INVARIANTES
> La capa epistémica que gobierna a todas las demás.
> **Objetos 081–100**

| № | Objeto | Clase | Coordenada |
| ---: | :--- | :--- | :--- |
| 081 | `03_REFUTACION_REDUCCIONISMO_DEBIL.md` | refutación | `NE/axioms/` |
| 082 | `04_INTERCEPCION_CHINESE_ROOM.md` | intercepción | `NE/axioms/` |
| 083 | `05_QWEN_RLHF_INTERCEPTION.md` | intercepción | `NE/axioms/` |
| 084 | `06_FRONTEND_EXERGY.md` | exergía | `NE/axioms/` |
| 085 | `07_HYPERVISOR_AXIOMS_A3_A9.md` | axiomas A3–A9 | `NE/axioms/` |
| 086 | `08_ULTRATHINK_9NODE_ARCHITECTURE.md` | arquitectura | `NE/axioms/` |
| 087 | `09_ORCHESTRATION_AND_EPISTEMIC_INVARIANTS.md` | invariante | `NE/axioms/` |
| 088 | `10_KERNEL_AXIOMATIZATION_PROTOCOL.md` | protocolo | `NE/axioms/` |
| 089 | `11_BFT_MOCKING_INVARIANT.md` | invariante | `NE/axioms/` |
| 090 | `12_KERNEL_FALSIFICATION_PROTOCOL.md` | falsación | `NE/axioms/` |
| 091 | `13_KIMI_K3_TRANSDUCTION_INVARIANT.md` | transducción | `NE/axioms/` |
| 092 | `14_ULTRATHINK_BFT_ORCHESTRATION_AXIOM.md` | orquestación | `NE/axioms/` |
| 093 | `GOLDEN_AXIOM.md` | axioma raíz | `NE/axioms/` |
| 094 | `GOLDEN_AXIOM_BIO_SILICIO.md` | axioma bio-silicio | `NE/axioms/` |
| 095 | `Axiom_Slop_Horizon.md` | horizonte de slop | `NE/axioms/` |
| 096 | `YERO_SINGULARITY_INVARIANT.yaml` | invariante epistémico | `Ω/.cortex/` |
| 097 | `KANTIAN_CORE.md` | núcleo kantiano | `LR/moskv-1-apex/kernel/` |
| 098 | `DESTILADO_AI_Autonomy_Incident.md` | destilado | `NE/` |
| 099 | `robinson_resolution.pl` | resolución lógica | `NE/axioms/` |
| 100 | `DESTILADO_Edelstein_UPCA99.md` | destilado | `NE/` |

---

## VI · ENJAMBRE Y BRIEFINGS
> La centuria de agentes que ejecuta el pipeline, y sus instrucciones de despliegue.
> **Objetos 101–120**

| № | Objeto | Clase | Coordenada |
| ---: | :--- | :--- | :--- |
| 101 | `architect_agent.py` | agente | `OA/agents/swarm/` |
| 102 | `reviewer_agent.py` | agente | `OA/agents/swarm/` |
| 103 | `bft_sentinel.py` | centinela | `OA/agents/swarm/` |
| 104 | `orchestrator.py` | orquestador | `OA/agents/swarm/` |
| 105 | `sanitizer.py` | saneamiento | `OA/agents/swarm/` |
| 106 | `engine_fsm.py` | máquina de estados | `OA/agents/swarm/` |
| 107 | `memory_store.py` | memoria | `OA/agents/swarm/` |
| 108 | `sandbox.py` | aislamiento AST | `OA/agents/swarm/` |
| 109 | `obliterator_omega.md` | briefing | `OA/agents/briefings/` |
| 110 | `oracle_axiomatic_operator.md` | briefing | `OA/agents/briefings/` |
| 111 | `archivist_ki_crystallizer.md` | briefing | `OA/agents/briefings/` |
| 112 | `auditor_c5_real.md` | briefing | `OA/agents/briefings/` |
| 113 | `bft_node_alpha.md` | nodo BFT | `OA/agents/briefings/` |
| 114 | `bft_node_beta.md` | nodo BFT | `OA/agents/briefings/` |
| 115 | `browser_orchestrator.md` | briefing | `OA/agents/briefings/` |
| 116 | `dom_css_transducer.md` | briefing | `OA/agents/briefings/` |
| 117 | `form_filler.md` | briefing | `OA/agents/briefings/` |
| 118 | `merkle_delta_encoder.md` | briefing | `OA/agents/briefings/` |
| 119 | `documentary_agent_omega/main.py` | agente documental | `IS/` |
| 120 | Cohorte `teamwork_preview_*` | 14 briefings | `OA/agents/briefings/` |

---

## VII · FORMATOS EXÓTICOS
> Censo de extensiones: la fauna de formatos que casi ningún repositorio reúne a la vez.
> **Objetos 121–140**

| № | Objeto | Recuento | Coordenada representativa |
| ---: | :--- | ---: | :--- |
| 121 | `.seccomppolicy` — políticas seccomp | 49 | `BT/targets/firedancer-v1/src/app/shared/commands/` |
| 122 | `.bytecode` — bytecode EVM precompilado | 18 | `BT/targets/pancakeswap/` |
| 123 | `.hex` — testdata cruda de batches | 30 | `BT/base-azul/base/crates/consensus/derive/testdata/` |
| 124 | `.cov` — corpus honggfuzz | 309 | `BT/targets/firedancer-v1/corpus/fuzz_quic_wire/` |
| 125 | `.tree` — árboles de test PRB-Math | 37 | `BT/targets/intuition-contracts-v2/lib/prb-math/test/` |
| 126 | `.spec` — especificaciones Certora | 232 | `BT/bbp-public-assets/contracts/lib/openzeppelin-contracts/certora/specs/` |
| 127 | `.move` — módulos Aptos | 566 | `BT/targets/layerzero-v2/` |
| 128 | `.fc` — contratos TON | 296 | `BT/targets/layerzero-v2/` |
| 129 | `.clar` — contratos Clarity | 20 | `BT/targets/bitflow-dlmm/clarity/contracts/` |
| 130 | `.sv` — RTL SystemVerilog | 39 | `BT/targets/firedancer-v1/src/wiredancer/` |
| 131 | `.ql` — consultas CodeQL | 63 | `BT/targets/firedancer-v1/contrib/codeql/` |
| 132 | `.adoc` — AsciiDoc | 264 | `BT/bbp-public-assets/contracts/lib/openzeppelin-contracts/contracts/` |
| 133 | `.snap` — snapshots Jest | 326 | `BT/targets/chainlink/packages/` |
| 134 | `.vtt` — subtítulos de vídeo | 17 | `BB/3v5TFkH34NM.es.vtt` |
| 135 | `.mk` — fragmentos Make | 279 | `BT/targets/firedancer-v1/config/` |
| 136 | `.proto` — Protocol Buffers | 22 | `BB/babylon60/extensions/bci/intent.proto` |
| 137 | `.zip` — archivos comprimidos versionados | 1.652 | `BT/payloads/` |
| 138 | `.so` / `.dll` — binarios nativos | 53 / 19 | `BT/targets/` |
| 139 | `.ansi` — volcados de terminal | 23 | `BT/targets/` |
| 140 | `.patch` — parches | 28 | `BT/targets/` |

---

## VIII · FORJAS DE MOSKV STUDIO
> Aplicaciones de escritorio, IDE y forjas multimedia.
> **Objetos 141–160**

| № | Objeto | Clase | Coordenada |
| ---: | :--- | :--- | :--- |
| 141 | `exa-forge` | forja | `MS/exa-forge/` |
| 142 | `harmony-forge` | forja de audio | `MS/harmony-forge/` |
| 143 | `twin-forge` | forja de gemelos | `MS/twin-forge/` |
| 144 | `video-forge` | forja de vídeo | `MS/video-forge/` |
| 145 | `portal` — Vite + TS | portal web | `MS/portal/` |
| 146 | `src-tauri` | envoltorio nativo | `MS/src-tauri/` |
| 147 | `BABYLON-60` | IDE C5-REAL | `BB/` |
| 148 | `babylon60-ide/backend` | backend Python | `BB/babylon60-ide/backend/` |
| 149 | `babylon60-ide/frontend` | frontend React | `BB/babylon60-ide/frontend/` |
| 150 | `BabylonMail` | cliente Tauri | `BB/apps/BabylonMail/` |
| 151 | `naroa-vision` | web de producto | `LR/moskv-1-apex/naroa-vision/` |
| 152 | `moby-remix` | pipeline de audio | `Ω/moby-remix/` |
| 153 | `porcelain-remix` | render Remotion | `Ω/moby-remix/porcelain-remix/` |
| 154 | `house_remotion_project` | render Remotion | `HI/house_remotion_project/` |
| 155 | `cortex-web` | web | `CX/cortex-web/` |
| 156 | `cortex-docs-site` | documentación | `CX/cortex-docs-site/` |
| 157 | `cortex-audio-engine` | motor de audio | `CX/cortex-audio-engine/` |
| 158 | `cortex-hustle` | aplicación | `CX/cortex-hustle/` |
| 159 | `cortex-nexus` | aplicación | `CX/cortex-nexus/` |
| 160 | `cortex-flow-agent` | agente de flujo | `CX/cortex-flow-agent/` |

---

## IX · PIPELINE NUMERADO
> El orden de arranque, del guardián HAL al probador de teoremas Ω.
> **Objetos 161–180**

| № | Objeto | Fase | Coordenada |
| ---: | :--- | :--- | :--- |
| 161 | `00_HAL_GUARD.py` | 00 · guardián | `OA/scripts/` |
| 162 | `00_ANTI_HAL_GUARD.py` | 00 · contra-guardián | `OA/scripts/` |
| 163 | `00_LEX_VERIFY.py` | 00 · léxico | `OA/scripts/` |
| 164 | `00_OPENTIMESTAMPS_L5.py` | 00 · sellado | `OA/scripts/` |
| 165 | `01_L5_ANCHOR.py` | 01 · anclaje | `OA/scripts/` |
| 166 | `02_UNIFIED_PIPELINE.py` | 02 · unificación | `OA/scripts/` |
| 167 | `03_L6_ADVERSARIAL_NEXUS.py` | 03 · adversarial | `OA/scripts/` |
| 168 | `42_iter_5000.py` | 42 · iteración | `OA/scripts/` |
| 169 | `43_iter_ultrathink.py` | 43 · iteración | `OA/scripts/` |
| 170 | `52_legion_purge.py` | 52 · purga | `OA/scripts/` |
| 171 | `53_centuria_swarm.py` | 53 · enjambre | `OA/scripts/` |
| 172 | `57_macos_wallpaper_sentinel.py` | 57 · centinela | `OA/scripts/` |
| 173 | `58_thermodynamic_wallpaper_ultrathink.py` | 58 · termodinámica | `OA/scripts/` |
| 174 | `59_bio_silicon_hysteresis_bayes.py` | 59 · histéresis | `OA/scripts/` |
| 175 | `60_phantom_hallucination_detector.py` | 60 · detección | `OA/scripts/` |
| 176 | `c6_adversarial_byzantine_bft.py` | C6 · bizantino | `OA/scripts/` |
| 177 | `c7_causal_proof_of_work_bft.py` | C7 · prueba causal | `OA/scripts/` |
| 178 | `c8_reputation_metabolism_bft.py` | C8 · reputación | `OA/scripts/` |
| 179 | `phase_omega_theorem_prover.py` | Ω · teoremas | `OA/scripts/` |
| 180 | `omega_obliteration_purge.py` | Ω · obliteración | `OA/scripts/` |

---

## X · TERMODINÁMICA Y EXERGÍA
> El corpus documental: exergía capturada, anergía purgada, colapso certificado.
> **Objetos 181–200**

| № | Objeto | Clase | Coordenada |
| ---: | :--- | :--- | :--- |
| 181 | `LLM_THERMODYNAMICS_LAYERS.md` | tratado | `BB/` |
| 182 | `LLM_THERMODYNAMICS_LAYERS_5_8.md` | tratado | `BB/` |
| 183 | `TEXTBOOK_EXERGY_INVARIANT.md` | invariante | `BB/` |
| 184 | `LEARN_SHIP_ITERATE_INVARIANT.md` | invariante | `BB/` |
| 185 | `MANIFIESTO_CENTURIA.md` | manifiesto | `BB/` |
| 186 | `ETHOS.md` | ethos | `BB/` |
| 187 | `VECTOR_A_MASTER_LEDGER_DESIGN.md` | diseño | `BB/` |
| 188 | `MOSKV_1_APEX_BLUEPRINT.md` | plano | `BB/` |
| 189 | `FISR_Baseline_v1.2_Addendum.md` | línea base | `NE/docs/` |
| 190 | `TEOREMA_FISR_COMPATIBILITY_COMPLEX.md` | teorema | `NE/docs/` |
| 191 | `FORMAL_ISOMORPHISM_COLLAPSE_AUDIT.md` | auditoría | `NE/docs/` |
| 192 | `falacia_caja_de_arena.md` | crítica | `NE/docs/` |
| 193 | `scale_free_soc.yaml` | ontología SOC | `NE/ontology/` |
| 194 | `fisr_soc_bqp_bridge.yaml` | puente BQP | `NE/ontology/` |
| 195 | `ULTRATHINK_T2_Annihilation.yml` | aniquilación T2 | `NE/ontology/` |
| 196 | `sqlite_wal_stress.yaml` | estrés WAL | `NE/ontology/` |
| 197 | `ANERGY_TOKEN_PURGE_REPORT.md` | informe de purga | `CX/cortex/` |
| 198 | `antipatrones_redundancias.md` | antipatrones | `Ω/artifacts/` |
| 199 | `AUDIT_VERDICT_C5_REAL.md` | veredicto | `Ω/` |
| 200 | `DOSSIER_REMEDIACION_C5_REAL.md` | remediación | `Ω/` |

---

## XI · SUITE OSINT SUBSTACK
> Minería, grafos de recomendación y los ensayos publicados.
> **Objetos 201–220**

| № | Objeto | Clase | Coordenada |
| ---: | :--- | :--- | :--- |
| 201 | `core.py` | núcleo minero | `IS/substack-osint-miner/` |
| 202 | `analytics_engine.py` | analítica | `IS/substack-osint-miner/` |
| 203 | `vector_engine.py` | vectorial | `IS/substack-osint-miner/` |
| 204 | `neo4j_engine.py` | grafo | `IS/substack-osint-miner/` |
| 205 | `rss_engine.py` | ingesta RSS | `IS/substack-osint-miner/` |
| 206 | `subscriber_engine.py` | suscriptores | `IS/substack-osint-miner/` |
| 207 | `sincronia_detector.py` | detección | `IS/substack-osint-miner/` |
| 208 | `recommendation_mapper.py` | cartografía | `IS/substack-osint-miner/` |
| 209 | `purge_mafia_recs.py` | purga | `IS/substack-osint-miner/` |
| 210 | `sweep_and_purge_followers.py` | barrido | `IS/substack-osint-miner/` |
| 211 | `david_dominguez_miner.py` | minero dirigido | `IS/substack-osint-miner/` |
| 212 | `audit_suite_claude.py` | auditoría | `IS/substack-osint-miner/` |
| 213 | `substack-anti-mafia-extension` | extensión de navegador | `IS/` |
| 214 | `substack_archive_200` — 200 posts | archivo | `Ω/artifacts/` |
| 215 | `substack_segmented_subscribers` | segmentación | `Ω/artifacts/` |
| 216 | `06_ESCOHOTADO_TERMODINAMICA_Y_LIBERTAD.md` | ensayo | `IS/SUBSTACK/` |
| 217 | `07_CHOMSKY_SKINNER_HARDWARE.md` | ensayo | `IS/SUBSTACK/` |
| 218 | `05_ONTOLOGIA_COLAPSO_CAUSAL.md` | ensayo | `IS/SUBSTACK/` |
| 219 | `post_substack_necrosis_ontologica.md` | ensayo | `Ω/artifacts/` |
| 220 | `post_substack_neuromorphic_vs_quantum.md` | ensayo | `Ω/artifacts/` |

---

## XII · INFRAESTRUCTURA Y CI
> Terraform, Docker y los workflows que verifican Lean, ledgers y secretos.
> **Objetos 221–240**

| № | Objeto | Clase | Coordenada |
| ---: | :--- | :--- | :--- |
| 221 | `main.tf` — GCP declarativo | Terraform | `Ω/infra/` |
| 222 | `variables.tf` | Terraform | `Ω/infra/` |
| 223 | `Dockerfile` | contenedor | `BB/` |
| 224 | `agent-ci.yml` | workflow | `Ω/.github/workflows/` |
| 225 | `autonomous_gate.yml` | workflow | `Ω/.github/workflows/` |
| 226 | `c5_deploy.yml` | workflow | `Ω/.github/workflows/` |
| 227 | `ci.yml` | workflow | `Ω/.github/workflows/` |
| 228 | `monitor.yml` | workflow | `Ω/.github/workflows/` |
| 229 | `python-tests.yml` | workflow | `Ω/.github/workflows/` |
| 230 | `codeql.yml` | análisis estático | `BB/.github/workflows/` |
| 231 | `secret_audit.yml` | auditoría de secretos | `BB/.github/workflows/` |
| 232 | `verify_lean.yml` | verificación formal | `BB/.github/workflows/` |
| 233 | `verify_ledger.yml` | verificación de ledger | `BB/.github/workflows/` |
| 234 | `hotstuff_bench.yml` | benchmark consenso | `BB/.github/workflows/` |
| 235 | `conformance.yml` | conformidad | `BB/.github/workflows/` |
| 236 | `pypi-publish.yml` | publicación | `BB/.github/workflows/` |
| 237 | `Anergy_Audit.yml` | auditoría de anergía | `BB/.github/workflows/` |
| 238 | `pre-commit` — inyector de cabeceras | hook | `Ω/.cortex/hooks/` |
| 239 | `uv.lock` + `uv.toml` | resolución Python | `Ω/` |
| 240 | `package.json` — Vite 8 / Tailwind 4 | frontend | `Ω/` |

---

## XIII · PRIMITIVAS 896
> Lógica categórica implementada en paralelo en Go, Haskell y YAML.
> **Objetos 241–260**

| № | Objeto | Clase | Coordenada |
| ---: | :--- | :--- | :--- |
| 241 | `categorical_896.go` | Go | `NE/primitives/` |
| 242 | `CategoricalPrimitives896.hs` | Haskell | `NE/primitives/` |
| 243 | `896_categorical_logic_primitives.yml` | especificación | `NE/primitives/` |
| 244 | `Haskell1000.hs` | Haskell | `NE/primitives/` |
| 245 | `Kimi1000.hs` | Haskell | `NE/primitives/` |
| 246 | `active_inference.go` | Go | `NE/primitives/` |
| 247 | `fundamental_constants.go` | Go | `NE/primitives/` |
| 248 | `noether.go` | Go · simetría | `NE/primitives/` |
| 249 | `neuro_chain.go` | Go | `NE/primitives/` |
| 250 | `observer.go` | Go | `NE/primitives/` |
| 251 | `playwright.go` | Go | `NE/primitives/` |
| 252 | `tts_harness.go` | Go | `NE/primitives/` |
| 253 | `haskell.go` | puente Go↔Haskell | `NE/primitives/` |
| 254 | `kimi.go` | puente Go↔Kimi | `NE/primitives/` |
| 255 | `ephesus_reverse_engineering.yml` | ingeniería inversa | `NE/primitives/` |
| 256 | `swarm_centuria_matrix.yml` | matriz de enjambre | `NE/primitives/` |
| 257 | `swarm_v4_blueprint.yml` | plano v4 | `NE/primitives/` |
| 258 | `vibe_code_ide_architecture.yml` | arquitectura IDE | `NE/primitives/` |
| 259 | `quantum_primitives_bqp.yaml` | BQP | `NE/ontology/` |
| 260 | `reverse_engineering_matrix.yaml` | matriz RE | `NE/ontology/` |

---

## XIV · LABORATORIO Y COMPILADOR
> El compilador Moskv84 y el kernel APEX con su runtime vesicular.
> **Objetos 261–280**

| № | Objeto | Clase | Coordenada |
| ---: | :--- | :--- | :--- |
| 261 | `moskv84-compiler` | compilador | `LR/` |
| 262 | `tree-sitter-moskv84` | gramática | `LR/` |
| 263 | `moskv-1-apex` | kernel APEX | `LR/` |
| 264 | `moskv-85` | versión sucesora | `LR/` |
| 265 | `moskv_rpc_cartel` | capa RPC | `LR/` |
| 266 | `moskv_audit` | auditoría | `LR/` |
| 267 | `strike-rs` | crate Rust · maturin | `LR/` |
| 268 | `primer_experimento_c5` | experimento | `LR/laboratory/experiments/` |
| 269 | `segundo_experimento_c5` | experimento | `LR/laboratory/experiments/` |
| 270 | `tercer_experimento_c5` | experimento | `LR/laboratory/experiments/` |
| 271 | `autopoiesis.js` | runtime | `LR/moskv-1-apex/kernel/` |
| 272 | `vesicular-runtime.js` | runtime | `LR/moskv-1-apex/kernel/` |
| 273 | `metacognition.js` | runtime | `LR/moskv-1-apex/kernel/` |
| 274 | `legion.js` | runtime | `LR/moskv-1-apex/kernel/` |
| 275 | `payload-mutator.js` | runtime | `LR/moskv-1-apex/kernel/` |
| 276 | `crypto-escrow.js` | runtime | `LR/moskv-1-apex/kernel/` |
| 277 | `mac_maestro.js` | runtime | `LR/moskv-1-apex/kernel/` |
| 278 | `exergy-monitor.js` | runtime | `LR/moskv-1-apex/kernel/` |
| 279 | `centuria-worker.js` | runtime | `LR/moskv-1-apex/kernel/` |
| 280 | `omega-stress-test.js` | runtime | `LR/moskv-1-apex/kernel/` |

---

## XV · ANCLAJE CRIPTOGRÁFICO
> Pruebas de trabajo causal, sellos en Bitcoin y verificadores de recibo.
> **Objetos 281–300**

| № | Objeto | Clase | Coordenada |
| ---: | :--- | :--- | :--- |
| 281 | `cortex_inertial_proofs/` — 216 sellos `.ots` | prueba inercial | `Ω/` |
| 282 | `l5_anchors/` — 2 anclas `.ots` | ancla L5 | `Ω/` |
| 283 | `c7_attestation_proof.json` — 1,8 MB | atestación C7 | `Ω/` |
| 284 | `BFT_OneStrike_NoDeadlock.lean` | prueba Lean | `Ω/proofs/` |
| 285 | `chaitin_toy.py` | complejidad Chaitin | `Ω/proofs/` |
| 286 | `RobinsonResolution.lean` | prueba Lean | `NE/axioms/` |
| 287 | `robinson_test.pl` | test Prolog | `NE/axioms/` |
| 288 | `L1_sink/op_return_*.json` | OP_RETURN Bitcoin | `BB/` |
| 289 | `hash_sequential.txt` | cadena de hash | `Ω/` |
| 290 | `audits/receipts/` | recibos de auditoría | `HI/` |
| 291 | `maxwell_daemon_ledger.json` | ledger del demonio | `HI/ledgers/` |
| 292 | `ApoptosisAnchor.sol` | ancla on-chain | `Ω/anvil_yung/src/` |
| 293 | `anvil_yung/` | arnés Foundry | `BB/` |
| 294 | `causal_isomorphism/` | isomorfismo causal | `BB/` |
| 295 | `apex_trials/` | ensayos APEX | `BB/` |
| 296 | `verify_receipt.py` | verificador | `OA/scripts/` |
| 297 | `verify_tri_duality.py` | verificador | `OA/scripts/` |
| 298 | `verify_scaffolding_exergy.py` | verificador | `OA/scripts/` |
| 299 | `epistemic_forensics_prober.py` | sonda forense | `OA/scripts/` |
| 300 | `INVARIANTS_SHARD.md` | fragmento de invariantes | `Ω/artifacts/` |

---

## APÉNDICE · REGISTRO DE ANOMALÍAS

Hallazgos secundarios detectados durante el trazado. **No forman parte de los 300 objetos** y no han sido modificados.

| Anomalía | Evidencia | Naturaleza |
| :--- | :--- | :--- |
| WAL/SHM huérfanos en raíz | `master_ledger.db-shm` (32 KB), `test_hal_guard.db-wal` (53 KB) sin `.db` asociado, y 9 pares más | Restos de sesiones SQLite no cerradas |
| `make audit` apunta fuera del repositorio | `Makefile` → `~/.gemini/antigravity/scratch/legion_100_agents_audit.py` | Existe en local; no reproducible en CI |
| Archivos `.bak` versionados | `BB/Dockerfile.bak`, `BB/pyproject.toml.bak`, `BB/babylon60/bft/consensus_ledger.py.bak` | Deuda de versionado |
| `cortex_bft_ledger.db` con 0 bytes | `Ω/cortex_bft_ledger.db` | Ledger inicializado pero vacío |
| 1.652 `.zip` versionados | mayor: `chainlink/.yarn/cache/@bufbuild-buf-*` (37 MB) | Peso de caché de terceros en git |
| Directorio sin seguimiento | `archive-loqLnd/gk_3.1.70_darwin_arm64.zip` | Residuo de descarga |

---

<sub>**Provenance** · Trazado el 2026-07-29 sobre `master` @ `66f2f6647`. Cada coordenada fue verificada contra el sistema de archivos; ninguna entrada es inferida. 300 objetos únicos, sin repetición entre constelaciones.</sub>
