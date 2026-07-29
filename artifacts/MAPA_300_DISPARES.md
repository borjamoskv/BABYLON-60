# MAPA DE 300 COSAS HIPER-DISPARES

> Cartografía de máxima dispersión ontológica del monorepo `Teorema-Robinson-Moskv`.
> Cada entrada es un objeto **real y verificado** en disco a fecha 2026-07-29 (rama `master`, HEAD `66f2f6647`).
> Método: `git ls-files` (35.058 archivos trackeados), `sqlite3 .tables` sobre cada ledger, `find` sobre estratos no trackeados.

**Vector de dispersión:** 13 estratos · 30 gramáticas formales distintas · 24 bases de datos · 20 targets externos · 4 dominios maestros.

---

## I. TOPOLOGÍA FÍSICA — ESTRATOS Y SYMLINKS (1–20)

Un grafo de 28 symlinks superpone una fachada plana sobre una jerarquía de 4 estratos termodinámicos.

1. `0_Buzon_Entrada/` — estrato de entrada, entropía sin procesar (wheels, scratch, un `.txt` de test de fricción cero).
2. `1_Operaciones_Activas/` — estrato caliente; concentra 33.477 de los 35.058 archivos trackeados.
3. `2_Nucleo_Estatico/` — núcleo declarado inmutable: axiomas, ontologías, primitivas, teoría.
4. `3_Historico_Inerte/` — estrato frío: auditorías, ledgers muertos, un proyecto Remotion abandonado.
5. `cortex-engine -> 1_Operaciones_Activas/02_CORTEX_ENGINE` — el symlink que oculta el 95% de la masa.
6. `intel-suite -> 1_Operaciones_Activas/01_INTEL_SUITE` — fachada del producto OSINT.
7. `moskv-studio -> 1_Operaciones_Activas/03_MOSKV_STUDIO` — fachada del desktop app.
8. `laboratorio-rd -> 1_Operaciones_Activas/04_LABORATORIO_RD` — fachada del R&D.
9. `BABYLON-60 -> .../02_CORTEX_ENGINE/BABYLON-60` — symlink a un repo-dentro-del-repo.
10. `strike-rs -> .../04_LABORATORIO_RD/strike-rs` — crate Rust expuesto como si fuera raíz.
11. `laboratory -> .../04_LABORATORIO_RD/laboratory` — segundo symlink al mismo dominio.
12. `portal -> .../03_MOSKV_STUDIO/portal` — daemon web.
13. `src -> .../03_MOSKV_STUDIO/src` — el `src/` de raíz no existe: es un puntero.
14. `src-tauri -> .../03_MOSKV_STUDIO/src-tauri` — igual para el wrapper nativo.
15. `agents -> 1_Operaciones_Activas/agents` — enjambre BFT.
16. `axioms -> 2_Nucleo_Estatico/axioms` — cruce de estrato caliente a inmutable.
17. `ontology -> 2_Nucleo_Estatico/ontology`.
18. `primitives -> 2_Nucleo_Estatico/primitives`.
19. `ledgers -> 3_Historico_Inerte/ledgers` — el estrato inerte sigue siendo direccionable.
20. `AGENTS.md -> .../agents/briefings/AGENTS.md` — symlink **de archivo**, no de directorio; junto a `cortex_env.py ->` son los dos únicos casos.

## II. GRAMÁTICAS FORMALES COEXISTENTES (21–50)

30 lenguajes con compilador o verificador propio, en un solo árbol de trabajo.

21. **Solidity** — 5.154 archivos `.sol`: el lenguaje **más numeroso del repo**, por encima de Python.
22. **Python** — 4.146 `.py`, pineado a `==3.12.*` en `pyproject.toml`.
23. **Rust** — 3.425 `.rs`, entre `strike-rs` (PyO3/maturin) y ~60 crates de `base-azul`.
24. **TypeScript** — 3.004 `.ts` + 137 `.tsx`.
25. **JavaScript** — 1.829 `.js`, incluido el kernel autopoiético en `moskv-1-apex/kernel/`.
26. **Move** (Aptos) — 566 `.move` en `targets/layerzero-v2/.../aptos/`.
27. **FunC** (TON) — 296 `.fc` en `targets/layerzero-v2/packages/.../ton/src/`.
28. **Clarity** (Stacks) — 20 `.clar` en `targets/bitflow-dlmm/clarity/contracts/`.
29. **C / C99** — 1.236 `.c` + 806 `.h`, casi todos en `firedancer-v1`.
30. **Go** — 184 `.go`: daemon portal, primitivas categóricas y stress de 1M.
31. **SystemVerilog** — 39 `.sv`: RTL FPGA de `wiredancer` (`cl_dram_dma.sv`, `areset_sync.sv`).
32. **Clojure** — 45 `.clj`: `lisp_metamembrane/src/metamembrane/core.clj` y meta-agentes `aegis`/`aletheia`.
33. **Haskell** — `2_Nucleo_Estatico/primitives/Kimi1000.hs`, `Haskell1000.hs`, `CategoricalPrimitives896.hs`.
34. **F#** — `fsharp_kernel/Library.fs` + `.fsproj` sobre **.NET 10.0**.
35. **Lean 4** — pruebas de teoremas (`RobinsonResolution.lean`, `Babylon.lean`).
36. **Prolog** — `axioms/robinson_resolution.pl` y `robinson_test.pl`.
37. **CESL** — DSL propietario: `cortex/cesl/kernel_v1.cesl` con su compilador en `compiler.py`.
38. **C++** — `moskv-1-apex/kernel/ast_compiler.cpp`, isla única.
39. **CodeQL** — 63 `.ql` de análisis estático custom (`DeadCodeAfterTerminatingLog.ql`).
40. **Certora CVL** — 232 `.spec` de verificación formal de contratos OpenZeppelin.
41. **Bulloak trees** — 37 `.tree`: especificación de tests en árbol para `prb-math`.
42. **Protobuf** — 22 `.proto`, incluido `babylon60/extensions/bci/intent.proto` (interfaz cerebro-computador).
43. **Astro** — 25 `.astro` en `cortex-hustle` y `cortex-persist/_archived`.
44. **Handlebars** — plantillas `.hbs` de generación de docs de contratos.
45. **AsciiDoc** — 264 `.adoc`, documentación heredada de OpenZeppelin.
46. **Terraform HCL** — `infra/main.tf` + `infra/variables.tf`: toda la infra son 2 archivos.
47. **Make fragments** — 279 `.mk`, incluido cross-compilación `macos-arm-clang_x_linux-x86.mk`.
48. **seccomp policy DSL** — 49 `.seccomppolicy`: sandboxing de syscalls por comando de Firedancer.
49. **WebVTT** — 17 `.vtt`: transcripciones de YouTube en `en` y `es` versionadas como código.
50. **SQL** — 31 `.sql`, junto a 24 SQLite binarios vivos.

## III. DOMINIOS MAESTROS Y SUBPROYECTOS (51–86)

### 01_INTEL_SUITE — producto OSINT
51. `SUBSTACK/` — dossiers y JSON de autores (`osint_babylon60_authors.json`).
52. `substack-osint-miner/` — 25 módulos: `neo4j_engine`, `vector_engine`, `rss_engine`, `sincronia_detector`.
53. `documentary_agent_omega/` — agente documental de un solo `main.py`.
54. `substack-anti-mafia-extension/` — extensión de navegador (`manifest.json` + `content.js`).

### 02_CORTEX_ENGINE — motor cognitivo
55. `BABYLON-60/` — IDE + repo anidado con su propio `.github/`, `Dockerfile` y `pyproject.toml`.
56. `cortex/` — núcleo Python BFT (ver estrato IV).
57. `cortex-audio-engine/` — pipeline de audio con `requirements.txt` propio.
58. `cortex-bounties/` — laboratorio de auditoría de seguridad (ver estrato X).
59. `cortex-docs-site/` — sitio de documentación.
60. `cortex-fas/` — subsistema FAS.
61. `cortex-flow-agent/` — agente de flujo.
62. `cortex-hustle/` — front en Astro.
63. `cortex-memory/` — capa de memoria.
64. `cortex-nexus/` — enrutado de nexo.
65. `cortex-persist/` — persistencia determinista + `math_verification` en Lean.
66. `cortex-ram-guard/` — guardia de memoria residente.
67. `cortex-routing-bunker/` — búnker de enrutado LLM.
68. `cortex-web/` — frontend web.
69. `cortex_scheduler/` — planificador (alimenta `ultrathink_scheduler_ledger.db`, 4 MB).
70. `cortex_sentinel/` — centinela de invariantes.
71. `cortexpersist-monorepo/` — monorepo **dentro** del monorepo.

### 03_MOSKV_STUDIO — producción y desktop
72. `src/` — core Vite/TS del IDE Babylon-60.
73. `src-tauri/` — integración nativa Rust/Tauri.
74. `portal/` — daemon portal.
75. `video-forge/` — render de vídeo (salida `.mov` de 19 MB).
76. `twin-forge/` — forja de gemelos digitales.
77. `harmony-forge/` — forja de armonía/audio.
78. `exa-forge/` — forja de búsqueda.

### 04_LABORATORIO_RD — R&D
79. `moskv-1-apex/` — el subproyecto más heterogéneo: `rtl/`, `kernel/`, `payment_gateway/`, `terraform/`, `naroa-vision/`, `mac-maestro/`, `borjamoskv_wiki/`.
80. `moskv84-compiler/` — compilador del lenguaje Moskv84.
81. `tree-sitter-moskv84/` — gramática tree-sitter del mismo lenguaje.
82. `moskv-85/` — sucesor de la arquitectura 84.
83. `strike-rs/` — crate Rust con `.venv` y `target/` conviviendo.
84. `moskv_rpc_cartel/` — capa RPC.
85. `moskv_audit/` — auditoría del laboratorio.
86. `laboratory/experiments/` — `primer/segundo/tercer_experimento_c5` + `editorial_strategy.yml`.

## IV. NÚCLEO COGNITIVO `cortex/` (87–116)

### Motores (`cortex/engines/`)
87. `active_inference_engine.py` — inferencia activa (free energy).
88. `bft_orchestrator.py` — orquestador tolerante a fallos bizantinos.
89. `categorical_896_engine.py` — motor de 896 primitivas categóricas.
90. `compiled_theorem.py` — teorema compilado como objeto ejecutable.
91. `entropy_mapping_engine.py` — mapeo de entropía.
92. `escohotado_chaos_engine.py` — motor de caos derivado del corpus Escohotado.
93. `escohotado_market_prohibition_engine.py` — economía de la prohibición.
94. `knowledge_kernel_engine.py` — kernel de conocimiento.
95. `mcts_vnode_compiler.py` — compilador de vnodes por Monte Carlo Tree Search.
96. `subadditivity_verifier.py` — verificador de subaditividad.
97. `vibe_ide_engine.py` — motor del IDE.

### Sistema operativo cognitivo (`cortex/os/`)
98. `kernel.py` — kernel. 99. `scheduler.py` — planificador. 100. `memory.py` — memoria.
101. `gc.py` — recolector de basura cognitivo. 102. `syscalls.py` — syscalls simbólicas.

### Máquinas abstractas
103. `cortex/cam/hypergraph.py` — hipergrafo de la Categorical Abstract Machine.
104. `cortex/cam/dag.py` — DAG de efectos.
105. `cortex/cam/machine.py` — máquina CAM.
106. `cortex/aem/isa.py` — ISA de la Abstract Effects Machine.
107. `cortex/aem/space.py` — espacio de estados AEM.
108. `cortex/cesl/compiler.py` + `kernel_v1.cesl` — compilador y kernel del DSL propio.
109. `cortex/hypervisor/collision.py` — detección de colisión a nivel hipervisor.

### Puentes externos (`cortex/bridges/`)
110. `claude_bridge.py` — puente a Claude.
111. `gemini_live_client.py` — cliente Gemini Live.
112. `llm_router.py` — router multi-modelo.
113. `kimi.py` — puente a Kimi.
114. `haskell.py` — FFI a Haskell.
115. `playwright.py` — control de navegador.
116. `github_webhook_daemon.py` — daemon de webhooks.

## V. SCRIPTS OPERATIVOS — 118 EJECUTABLES NUMERADOS (117–146)

117. `00_HAL_GUARD.py` — guardia anti-alucinación.
118. `00_ANTI_HAL_GUARD.py` — su antagonista explícito, en el mismo directorio.
119. `00_OPENTIMESTAMPS_L5.py` — anclaje temporal en Bitcoin.
120. `00_PROMPT_EXERGY.py` — medición de exergía de prompts.
121. `01_cdp_transducer.py` — transductor Chrome DevTools Protocol.
122. `03_L6_ADVERSARIAL_NEXUS.py` — nexo adversarial nivel 6.
123. `18_codegen_playwright.py` — generación de código de navegación.
124. `21_lint_clippy.py` — lint Rust invocado desde Python.
125. `33_test_l5_atomic_recovery.py` — recuperación atómica del ancla L5.
126. `42_iter_5000.py` — 5.000 iteraciones de colapso.
127. `43_iter_ultrathink.py` — bucle ultrathink (origen de los 500 commits `[ITERA]`).
128. `50_GEMINI_RAW_TRANSDUCER.py` — transducción cruda Gemini.
129. `52_OPENROUTER_BFT_NODE.py` — nodo BFT sobre OpenRouter.
130. `53_centuria_swarm.py` — enjambre de 100 agentes.
131. `54_SIMULATE_ORACLE_BYZANTINE_FAULT.py` — fallo bizantino simulado de oráculo.
132. `54_tdah_orphan_purge.py` — purga de archivos huérfanos (nombre clínico).
133. `57_macos_wallpaper_sentinel.py` — centinela que escribe en el fondo de pantalla de macOS.
134. `58_thermodynamic_wallpaper_ultrathink.py` — el fondo de pantalla como display termodinámico.
135. `59_bio_silicon_hysteresis_bayes.py` — histéresis bayesiana bio-silicio.
136. `60_phantom_hallucination_detector.py` — detector de alucinaciones fantasma.
137. `arm64_mem_filter.py` — filtrado de memoria ARM64.
138. `c5_exergy_symlink_mapper.py` — el script que generó el grafo de symlinks del estrato I.
139. `c5_macos_exergy_tags.py` — etiquetas de color de Finder como metadato de exergía.
140. `c6_adversarial_replay_bft.py` — ataque de replay.
141. `c7_causal_proof_of_work_bft.py` — prueba de trabajo causal.
142. `c7_goodhart_stress_bft.py` — estrés bajo ley de Goodhart.
143. `c8_reputation_metabolism_bft.py` — metabolismo de reputación.
144. `stress_500k_async.py` — 500k operaciones asíncronas (junto a las variantes 10k y 100k).
145. `verify_maxwell_daemon.py` — verificación del demonio de Maxwell.
146. `phase_omega_theorem_prover.py` — probador de teoremas de fase omega.

## VI. LEDGERS Y PERSISTENCIA — 24 BASES SQLITE VIVAS (147–170)

147. `master_ledger.db` (28 K) — 3 tablas: `fraud_ledger`, `l5_anchor_state`, `master_ledger`.
148. `ultrathink_scheduler_ledger.db` (4,0 M) — `ledger_entries`; la base más activa.
149. `stress_ledger.db` (716 K) — `master_ledger` bajo estrés.
150. `swarm_stress_ledger.db` (44 K) — estrés del enjambre.
151. `unified_ledger.db` (20 K) — `fraud_ledger` + `l5_anchor_state`.
152. `atomic_recovery_test.db` (20 K) — banco de pruebas de recuperación atómica.
153. `master_ledger_test.db` (12 K) — espejo de test del ledger maestro.
154. `cortex_bft_ledger.db` — **0 bytes**, con `-shm`/`-wal` presentes.
155. `db/agent_memory.db` (24 M) — tabla `decisions`; el mayor artefacto binario no-vendorizado.
156. `db/memory.db` (4,3 M) — segunda tabla `decisions`, memoria duplicada.
157. `db/centuria_github.db` (384 K) — `github_primitives`.
158. `db/playwright_primitives.db` (148 K) — `playwright_primitives`.
159. `db/cdp_ledger.db` (16 K) — `cdp_events`.
160. `.cortex/cortex.db` — estado del córtex en directorio oculto.
161. `.cortex/byzantine_test.db` — banco bizantino.
162. `.cortex/replay_test.db` — banco de replay.
163. `.cortex/stress_c6.db` + `stress_c6_1.db` — dos generaciones de estrés C6.
164. `.cortex/c6_harness_test.db` + `integration_test.db` — arneses de integración.
165. `3_Historico_Inerte/ledgers/escohotado_substance.db` — tabla `substance_ontology`.
166. `.../escohotado_economics.db` — tabla `prohibition_economics`.
167. `.../escohotado_chaos_entropy.db` — tabla `chaos_metrics`.
168. `.../maxwell_daemon_ledger.json` — ledger en JSON junto a los SQLite.
169. `mundo_f_ledger.yml` (223 K) — ledger en YAML: tercer formato de persistencia.
170. `cortex/primitives/categorical_896_ledger.db` — ledger de primitivas categóricas.

## VII. VERIFICACIÓN FORMAL Y ANCLAJE CRIPTOGRÁFICO (171–185)

171. `2_Nucleo_Estatico/axioms/RobinsonResolution.lean` — resolución de Robinson en Lean 4.
172. `proofs/BFT_OneStrike_NoDeadlock.lean` — ausencia de deadlock BFT.
173. `BABYLON-60/proof/lean/Babylon.lean` — pruebas del IDE.
174. `cortex-persist/babylon60/math_verification/cortex_math_lean/CortexMathLean.lean` — cuarta isla Lean.
175. `axioms/robinson_resolution.pl` — la misma resolución, en Prolog.
176. `axioms/robinson_test.pl` — su banco de pruebas lógico.
177. `proofs/chaitin_toy.py` — juguete de complejidad de Chaitin.
178. `cortex_inertial_proofs/` — **216 archivos `.ots`** de OpenTimestamps por bloque.
179. `l5_anchors/*.ots` — 2 anclas L5 nombradas por hash SHA-256 completo.
180. `c7_attestation_proof.json` — 1,8 MB de atestación en la raíz.
181. `BABYLON-60/L1_sink/op_return_*.json` — sumidero de OP_RETURN de Bitcoin L1.
182. `.cortex/YERO_SINGULARITY_INVARIANT.yaml` — invariante epistémico con hash, rango `[2026, 2029]` y confianza `C5`.
183. `hash.txt` y `hash_sequential.txt` — dos hashes sueltos de 10 bytes en raíz.
184. `cortex/verification_omega_160_162.json` — verificación omega de un rango de ciclos.
185. `.cortex/hooks/pre-commit` — hook que sella cada archivo con cabecera C5-REAL según su sintaxis de comentario.

## VIII. CI/CD Y GOBERNANZA (186–205)

186. `.github/workflows/ci.yml` — pipeline principal.
187. `agent-ci.yml` — CI para los agentes.
188. `autonomous_gate.yml` — puerta de autonomía.
189. `c5_deploy.yml` — despliegue C5-REAL.
190. `monitor.yml` — monitorización continua.
191. `python-tests.yml` — suite pytest.
192. `BABYLON-60/.github/workflows/Anergy_Audit.yml` — auditoría de anergia (métrica propia).
193. `codeql.yml` — análisis CodeQL.
194. `conformance.yml` — conformidad de protocolo.
195. `hotstuff_bench.yml` — benchmark del consenso HotStuff.
196. `verify_lean.yml` — CI que verifica las pruebas Lean.
197. `verify_ledger.yml` — CI que verifica la cadena de ledgers.
198. `secret_audit.yml` — auditoría de secretos.
199. `pypi-publish.yml` — publicación a PyPI.
200. `production-deploy.yml` — despliegue productivo.
201. `.github/ISSUE_TEMPLATE/agent_task.yml` — issues estructurados para agentes, no para humanos.
202. `.github/CODEOWNERS` — propiedad del código.
203. `.github/PULL_REQUEST_TEMPLATE.md` — plantilla de PR.
204. `Makefile` — 8 targets que delegan todos en `./moskv`.
205. `moskv` — CLI en bash de 8,4 K: `status`, `test`, `intel`, `engine`, `studio`, `lab`, `sync`.

## IX. AXIOMAS, ONTOLOGÍAS Y PRIMITIVAS (206–235)

### Axiomas (`2_Nucleo_Estatico/axioms/`)
206. `GOLDEN_AXIOM.md` — axioma dorado.
207. `GOLDEN_AXIOM_BIO_SILICIO.md` — su variante bio-silicio.
208. `03_REFUTACION_REDUCCIONISMO_DEBIL.md` — refutación del reduccionismo débil.
209. `04_INTERCEPCION_CHINESE_ROOM.md` — intercepción de la habitación china.
210. `05_QWEN_RLHF_INTERCEPTION.md` — intercepción de RLHF en Qwen.
211. `06_FRONTEND_EXERGY.md` — exergía aplicada al frontend.
212. `07_HYPERVISOR_AXIOMS_A3_A9.md` — axiomas A3–A9 del hipervisor.
213. `08_ULTRATHINK_9NODE_ARCHITECTURE.md` — arquitectura de 9 nodos.
214. `11_BFT_MOCKING_INVARIANT.md` — invariante contra el mocking en tests BFT.
215. `12_KERNEL_FALSIFICATION_PROTOCOL.md` — protocolo popperiano de falsación del kernel.
216. `13_KIMI_K3_TRANSDUCTION_INVARIANT.md` — invariante de transducción Kimi K3.
217. `Axiom_Slop_Horizon.md` — el horizonte de "slop" como límite formal.

### Ontologías (`2_Nucleo_Estatico/ontology/`)
218. `P0_scanner_audit.yaml` — auditoría de escáner P0.
219. `ULTRATHINK_T2_Annihilation.yml` — aniquilación T2.
220. `apple_silicon_re_matrix.yaml` — matriz de ingeniería inversa de Apple Silicon.
221. `fisr_soc_bqp_bridge.yaml` — puente FISR ↔ SOC ↔ BQP.
222. `ls_main_ast.yaml` — AST del `main` de `ls` (ingeniería inversa de coreutils).
223. `quantum_primitives_bqp.yaml` — primitivas cuánticas en BQP.
224. `reverse_engineering_matrix.yaml` — matriz general de RE.
225. `scale_free_soc.yaml` — criticalidad auto-organizada libre de escala.
226. `sqlite_wal_stress.yaml` — ontología del estrés WAL de SQLite.
227. `system_prompts_leaks_ultrathink_p0.yaml` — corpus de fugas de system prompts.

### Primitivas (`2_Nucleo_Estatico/primitives/`)
228. `896_categorical_logic_primitives.yml` — las 896 primitivas declaradas.
229. `CategoricalPrimitives896.hs` — su implementación en Haskell.
230. `categorical_896.go` — la **misma** especificación en Go (implementación dual).
231. `Kimi1000.hs` / `kimi.go` — 1.000 primitivas Kimi, también duplicadas en dos lenguajes.
232. `noether.go` — primitivas de simetría de Noether.
233. `neuro_chain.go` — cadena neuronal.
234. `tts_harness.go` — arnés de síntesis de voz.
235. `swarm_centuria_matrix.yml` + `swarm_v4_blueprint.yml` + `ephesus_reverse_engineering.yml` — planos del enjambre.

## X. TARGETS EXTERNOS DE AUDITORÍA (`cortex-bounties/`) (236–255)

236. `targets/firedancer-v1` — validador Solana en C + RTL FPGA + corpus de fuzzing honggfuzz.
237. `targets/chainlink` — monorepo de oráculos con caché Yarn versionada.
238. `targets/layerzero-v2` (Aptos) — 566 módulos Move.
239. `targets/layerzero-v2` (TON) — 296 contratos FunC.
240. `targets/pancakeswap` — incluye `.bytecode` compilado como fixture de test.
241. `targets/intuition-contracts-v2` — con `prb-math` y sus árboles Bulloak.
242. `targets/intuition-bug-bounty` — programa asociado.
243. `targets/bitflow-dlmm` — DLMM en Clarity sobre Stacks.
244. `targets/kamino` — protocolo Solana.
245. `targets/lido` — staking líquido.
246. `targets/exactly-protocol` — lending.
247. `targets/2026-04-k2` — incluye un PDF de especificación de 13,9 MB.
248. `targets/attackathon-|-ethereum-protocol` — nombre de directorio con un **pipe** literal.
249. `base-azul/base` — fork del nodo Base: ~60 crates Rust (`batcher`, `prover/zk`, `nitro-enclave`).
250. `bbp-public-assets` — OpenZeppelin + forge-std + specs Certora.
251. `exploit-lab` — laboratorio de explotación con su propio CI.
252. `kite-ai` — target con Foundry.
253. `cortex_mev_base` — investigación MEV.
254. `competitions/2026-05-eigenlayer-avs` — competición AVS.
255. `competitions/folks-finance` + `CORTEX_IMMUNEFI_SUBMISSIONS_FOLKS_FINANCE.zip` — submissions empaquetadas.

## XI. SUPERFICIE DE PRUEBAS (256–275)

256. `tests/test_robinson_fo.py` — el teorema homónimo, en primer orden.
257. `tests/test_bft_resilience.py` — resiliencia bizantina.
258. `tests/test_categorical_896_engine.py` — motor de 896 primitivas.
259. `tests/test_collision_hypervisor.py` — colisión de hipervisor.
260. `tests/test_zero_trust_pipeline.py` — pipeline zero-trust.
261. `tests/test_detect_sim.py` — detección de simulación (C4-SIM vs C5-REAL).
262. `tests/adversarial/` — suite adversarial separada del resto.
263. `tests/cortex/mcts_vnode_compiler_test.py` — compilador MCTS.
264. `tests/cortex/subadditivity_verifier_test.py` — subaditividad.
265. `tests/cortex/escohotado_chaos_engine_test.py` — motor de caos.
266. `tests/cortex/fsharp_kernel_test.py` — Python testeando el kernel F#.
267. `tests/cortex/haskell_test.py` — Python testeando el puente Haskell.
268. `tests/cortex/quad_pillar_kernel_test.py` — kernel de cuatro pilares.
269. `tests/cortex/invariant_sentinel_test.py` — centinela de invariantes.
270. `tests/cortex/deliverability_validator_test.py` — validador de entregabilidad de correo.
271. `2_Nucleo_Estatico/primitives/*_test.go` — 10 suites Go en el estrato "inmutable".
272. `cmd/stress_robinson_1M/main_test.go` — estrés de 1M en Go.
273. `agents/swarm/sanitizer_test.py` — sanitizado del sandbox (endurecido en el HEAD actual).
274. `fsharp_kernel/Tests.fs` — pruebas nativas en F#.
275. `.hypothesis/` — corpus persistido de property-based testing.

## XII. ARTEFACTOS, MEDIOS Y CONTENIDO (276–290)

276. `artifacts/INVESTIGACION_CLAUDE5_SCAFFOLDING_300F.md` — investigación de andamiaje 300F.
277. `artifacts/CENTURIA_SWARM_REPORT.md` — informe del enjambre de 100 agentes.
278. `artifacts/antipatrones_redundancias.md` — catálogo propio de antipatrones.
279. `artifacts/substack_archive_200/` — 200 publicaciones archivadas.
280. `artifacts/substack_subscriber_audit_report.yml` — auditoría de suscriptores.
281. `artifacts/post_substack_neuromorphic_vs_quantum.md` — ensayo neuromórfico vs cuántico.
282. `moby-remix/separated/htdemucs/source/` — stems `bass/drums/other/vocals.wav` separados con Demucs, 32 MB cada uno.
283. `moby-remix/porcelain-remix/` — vídeo generativo con Remotion + `render_ffmpeg.sh`.
284. `3_Historico_Inerte/house_remotion_project/.../house_track.wav` — 10 MB de audio en el estrato inerte.
285. `03_MOSKV_STUDIO/video-forge/output/MOSKV_2026-05-22T01-02-44.mov` — 19 MB de vídeo renderizado.
286. `BABYLON-60/*.vtt` — transcripciones bilingües, incluida una con el título completo de un vídeo de YouTube como nombre de archivo.
287. `extracted_claude/resources/bundled-