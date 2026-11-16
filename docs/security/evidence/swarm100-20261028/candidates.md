# Registro de candidatos de los 100 auditores

Este registro conserva propuestas de los revisores. La severidad es sugerida, las entradas pueden solaparse o duplicarse y no hay adjudicación global individual. No representa598 vulnerabilidades confirmadas. La evidencia completa está en [candidates.json](candidates.json); los hallazgos contrastados por el coordinador están en [root-adjudications.json](root-adjudications.json).

|ID|Severidad sugerida|Tipo|Ubicación|Candidato|
|---|---|---|---|---|
|SW100-C0001|P2|runtime|01_KISH_ENGINE/babylon60/kernel/browser_cdp_engine.py:147|CDP request futures retained after timeout|
|SW100-C0002|P2|runtime|01_KISH_ENGINE/babylon60/kernel/browser_cdp_engine.py:160|Navigation retains a listener on every call|
|SW100-C0003|P2|runtime|01_KISH_ENGINE/babylon60/kernel/browser_cdp_engine.py:459|Browser launch timeout leaves browser process alive|
|SW100-C0004|P2|example|00_ABZU_KERNEL/crates/strike-rs/src/bin/poc_bft_zerocopy_dag.rs:162|PoC prints success after DAG timeout|
|SW100-C0005|P2|tooling|scripts/c5_verifiers/verify_execution.sh:10|Execution verifier ignores untracked files|
|SW100-C0006|P2|example|scripts/c5_demos/c5_legal_oracle.py:64|Legal oracle turns network failures into healthy empty result|
|SW100-C0007|P2|runtime-library|src/omega_mediation.rs:1596|Non-persist witness digest silently replaces SHA256 with XOR|
|SW100-C0008|P2|runtime-library|src/omega_mediation.rs:1787|Evidence digest omits observer visibility and witness identity fields|
|SW100-C0009|P2|runtime|src/omega_synthesis.rs:53|Frame event ID and payload separately in Merkle commitments|
|SW100-C0010|P2|runtime|01_KISH_ENGINE/babylon60/commands/grill_you.py:50|Escape user-controlled values before producing YAML|
|SW100-C0011|P2|runtime|scripts/c5_demos/c5_model_voice_announcer.py:155|Retain incomplete transcript records until the next append|
|SW100-C0012|P2|runtime|scripts/c5_demos/c5_model_voice_announcer.py:152|Reset tail position when transcript is truncated or replaced|
|SW100-C0013|P2|runtime|scripts/c5_demos/c5_model_voice_announcer.py:68|Pass notification text as data rather than AppleScript source|
|SW100-C0014|P2|runtime|scripts/c5_quality_gates/audit_fixer.py:50|Limit terminology rewrites to comments and documentation|
|SW100-C0015|P2|example|tools/skill_library/codex_overrides/cloudflare/references/workers-for-platforms/api.md:68|Remove comments from multipart JSON metadata example|
|SW100-C0016|P2|example|tools/skill_library/codex_overrides/cloudflare/references/workers-for-platforms/api.md:38|Avoid redeclaring the imported DispatchNamespace name|
|SW100-C0017|P2|docs|docs/KINETIC_CACHE_AUDIT.md:48|Do not claim strict real-time determinism from one benchmark maximum|
|SW100-C0018|P1|runtime|01_KISH_ENGINE/babylon60/commands/itera.py:24|Auto purge unlinks SQLite WAL files without checkpoint or connection coordination|
|SW100-C0019|P2|runtime|scripts/c5_quality_gates/audit_license_compliance.py:64|License gate treats conjunctive restrictive licenses as permissive alternatives|
|SW100-C0020|P2|example|scripts/c5_demos/c5_shm_manifest.rs:16|Example manifest occupies 128 bytes on the documented 64-bit targets|
|SW100-C0021|P2|example|00_ABZU_KERNEL/crates/strike-rs/src/bin/poc_t3_engine_stress.rs:162|Stress harness reports success even when health transitions fail|
|SW100-C0022|P3|example|tools/skill_library/global/c5-audiovisual-acreativo-sota/references/modules/flstudio-mcp-production/examples/Euclidean_Polyrhythm_Generator.py:63|Polymeter selector has no effect on generated rhythm|
|SW100-C0023|P2|runtime|01_KISH_ENGINE/babylon60/commands/strict_reviewer.py:56|Explicit --files filter compares relative paths against absolute paths|
|SW100-C0024|P2|runtime|01_KISH_ENGINE/babylon60/commands/strict_reviewer.py:156|Strict reviewer stages and commits unrelated working-tree changes|
|SW100-C0025|P2|runtime|tools/skill_library/global/c5-terminological-archaeology/scripts/c5_lexicon_notary.py:338|Dry-run still overwrites the session log|
|SW100-C0026|P2|runtime|tools/skill_library/global/c5-terminological-archaeology/scripts/c5_lexicon_notary.py:159|Replacing phase 2f deletes all subsequent skill sections|
|SW100-C0027|P2|example|scripts/c5_verifiers/verify_oncology_primitives_dag.py:81|Oncology support check cannot detect an out-of-support target|
|SW100-C0028|P2|example|scripts/c5_demos/c5_sovereign_compliance_orchestrator.py:102|Compliance pipeline verifies a different artifact than the certificate it generated|
|SW100-C0029|P2|example|tests/test_moskv_e2e_integration.py:51|Native host integration reads can block indefinitely|
|SW100-C0030|P2|runtime|scripts/c5_quality_gates/audit_scripts_quality.py:169|Non-JSON quality gate returns success when leaked artifacts are its only failure|
|SW100-C0031|P2|runtime|scripts/c5_verifiers/verify_p0_rotation.py:31|Git history verifier treats Git errors as a clean history|
|SW100-C0032|P2|example|tests/test_moskv_native_host.py:104|FIFO lifecycle test deletes the native host shared queue|
|SW100-C0033|P2|runtime|01_KISH_ENGINE/babylon60/kernel/c6_absolute/ctre_engine.py:49|CTRE commits non-finite drift observations|
|SW100-C0034|P2|runtime|01_KISH_ENGINE/babylon60/kernel/c6_absolute/ctre_engine.py:50|Risk rounding precedes CTRE threshold enforcement|
|SW100-C0035|P2|example|00_ABZU_KERNEL/crates/strike-rs/src/bin/poc_t3_stress_test.rs:117|Simulated tier stress test certifies IDE behavior it never exercises|
|SW100-C0036|P2|runtime|01_KISH_ENGINE/babylon60/kernel/c6_absolute/eip7702_hunter.py:72|Hunter clears its risk window after every sample|
|SW100-C0037|P2|docs|01_KISH_ENGINE/babylon60/kernel/c6_absolute/eip7702_hunter.py:73|Hunter reports on-chain commits without submitting transactions|
|SW100-C0038|P2|docs|docs/RESULTADOS.md:55|Formal validation recipe calls a removed Make target|
|SW100-C0039|P2|example|scripts/c5_verifiers/verify_semantic_entropy_gate.py:92|Entropy gate labels agreement as safe without checking correctness|
|SW100-C0040|P3|example|tools/skill_library/global/c5-audiovisual-acreativo-sota/references/modules/flstudio-mcp-production/examples/Kerri_Chandler_MPC60.py:35|Swing formula does not implement its declared triplet ratio|
|SW100-C0041|P2|example|scripts/c5_demos/c5_transduction_engine.py:19|Render directory resolves beneath scripts and omits cortex|
|SW100-C0042|P2|example|scripts/c5_demos/c5_transduction_engine.py:103|Concurrent compilations overwrite shared render inputs|
|SW100-C0043|P2|example|scripts/c5_demos/c5_transduction_engine.py:122|Scene timing adds silence that the audio pipeline never emits|
|SW100-C0044|P2|example|tools/skill_library/codex_overrides/cloudflare/references/do-storage/patterns.md:87|Alarm batch discards its pending work before insertion succeeds|
|SW100-C0045|P1|runtime|01_KISH_ENGINE/babylon60/utils/void_accel.c:32|Unsigned short vector lengths underflow the SIMD loop bound|
|SW100-C0046|P1|runtime|src/secure_fs.rs:2126|Delete quarantine occurs before recoverable durable intent|
|SW100-C0047|P2|runtime|src/secure_fs.rs:2123|Delete uses two unconstrained nonce identities|
|SW100-C0048|P2|example|00_ABZU_KERNEL/crates/strike-rs/src/bin/poc_zerocopy_hypervisor.rs:109|Zero-copy PoC reports success after dropped-message timeout|
|SW100-C0049|P2|example|tools/skill_library/global/c5-tri-provider-swarm/scripts/tri_swarm_dispatcher.py:66|Production dispatcher returns fabricated provider successes|
|SW100-C0050|P2|runtime|scripts/c5_quality_gates/audit_skills_ecosystem.py:151|Skill auditor passes when no skill directories exist|
|SW100-C0051|P2|example|tools/skill_library/codex_overrides/agents-sdk/references/webhooks-push.md:32|Webhook example consumes request body twice|
|SW100-C0052|P1|runtime|src/secure_fs.rs:1433|Cross-instance effect budget uses stale usage history|
|SW100-C0053|P1|runtime|src/secure_fs.rs:2295|Mutation receipt recovery does not restore charged budget|
|SW100-C0054|P1|example|scripts/c5_demos/c5_verifier_cli.rs:84|Verifier certifies attacker-controlled text without verifying any signature|
|SW100-C0055|P2|runtime|00_ABZU_KERNEL/crates/strike-rs/src/bindings.rs:170|Unknown obligations silently become successful empty verification|
|SW100-C0056|P2|runtime|00_ABZU_KERNEL/crates/strike-rs/src/bindings.rs:182|Contradiction verification ignores kernel nogoods|
|SW100-C0057|P2|example|tests/test_axioms_hypothesis.py:263|Property tests do not exercise the engine whose concurrency they claim to check|
|SW100-C0058|P2|example|tools/skill_library/global/c5-audiovisual-acreativo-sota/references/modules/flstudio-mcp-production/examples/Neo_Riemannian_Tonnetz.py:31|Relative transformation breaks the root-position invariant for subsequent transforms|
|SW100-C0059|P3|docs|ARCHITECTURE_MANIFEST.md:5|Architecture manifest points its formal foundation to a missing proof path|
|SW100-C0060|P2|runtime|proof/bundles/attestation_bundle_v1/verify:75|Verifier exits successfully after failed hash or signature checks|
|SW100-C0061|P1|runtime|proof/bundles/attestation_bundle_v1/verify:34|Signed causal hash does not authenticate bundle metadata or artifact|
|SW100-C0062|P2|runtime|01_KISH_ENGINE/babylon60/compliance_exporter/eu_ai_act.py:460|Lifecycle validation never verifies the certificate signature|
|SW100-C0063|P2|runtime|01_KISH_ENGINE/babylon60/compliance_exporter/eu_ai_act.py:488|Decision evidence packet does not bind decision data to the proved ledger event|
|SW100-C0064|P2|runtime|00_ABZU_KERNEL/crates/strike-rs/src/exergy_binary_ipc.rs:29|Packet packing silently truncates sender and recipient lengths|
|SW100-C0065|P2|example|00_ABZU_KERNEL/crates/strike-rs/src/gateway/circuit_breaker.rs:181|Real Ollama examples return the Tier 1 canned response|
|SW100-C0066|P2|runtime|00_ABZU_KERNEL/crates/strike-rs/src/gateway/circuit_breaker.rs:243|Configurable policy can enable Tier 3 for Ring 0|
|SW100-C0067|P2|runtime|01_KISH_ENGINE/babylon60/kernel/devsecops_attest.py:39|Attestation lock acquisition is not atomic|
|SW100-C0068|P2|runtime|01_KISH_ENGINE/babylon60/kernel/devsecops_attest.py:19|Cached attestation tree hash survives HEAD changes|
|SW100-C0069|P2|runtime|scripts/c5_quality_gates/canary_check.py:67|Staged canary deletion is accepted when the file remains locally|
|SW100-C0070|P2|runtime|scripts/distill_babylon60_docs.py:21|Documentation distiller targets a fixed obsolete checkout|
|SW100-C0071|P1|runtime|01_KISH_ENGINE/babylon60/compliance_exporter/m0_evidence_pack.py:599|Default evidence pack fabricates successful adversarial observations without marking simulation|
|SW100-C0072|P1|runtime|01_KISH_ENGINE/babylon60/compliance_exporter/m0_evidence_pack.py:585|Output directory is recursively deleted before validating compilation inputs|
|SW100-C0073|P2|runtime|01_KISH_ENGINE/babylon60/compliance_exporter/m0_evidence_pack.py:654|Existing-ledger integrity verdict is ignored by compiler|
|SW100-C0074|P2|runtime|01_KISH_ENGINE/babylon60/kernel/grounding_interceptor.py:145|Unverified evidence status is accepted as verified citation|
|SW100-C0075|P2|runtime|01_KISH_ENGINE/babylon60/kernel/grounding_interceptor.py:123|Failed SQLite registration leaves evidence trusted in memory|
|SW100-C0076|P2|runtime|01_KISH_ENGINE/babylon60/compliance_exporter/template_engine.py:275|Negative compliance statuses render as successful|
|SW100-C0077|P2|example|00_ABZU_KERNEL/crates/strike-rs/src/gateway/tier3.rs:366|Mock inference panics on a UTF-8 byte boundary|
|SW100-C0078|P2|runtime|00_ABZU_KERNEL/crates/strike-rs/src/gateway/tier3.rs:82|Attestation digest does not delimit content from model identity|
|SW100-C0079|P2|example|scripts/c5_demos/falsacion_io_sync.py:14|I/O demo deletes a preexisting database in the working directory|
|SW100-C0080|P2|runtime|scripts/enforce_c5_rules.sh:18|Branch protection enforcement suppresses API failures|
|SW100-C0081|P2|runtime|src/tamkarum.rs:112|Kelly inputs do not constrain an approved bid|
|SW100-C0082|P2|runtime|01_KISH_ENGINE/babylon60/kernel/mcp_deductive_engine.py:112|List samples generate object-only MCP schemas|
|SW100-C0083|P1|runtime|scripts/generate_attestation_bundle.py:55|Attestation generator emits unexecuted PASS results|
|SW100-C0084|P2|example|scripts/c5_demos/falsacion_llm_gate.py:122|Demo reports universal containment from two fixed simulated traces|
|SW100-C0085|P2|example|tools/skill_library/global/whatsapp-nexus-protocol/scripts/group_wizard.js:5|Group creation wizard completes without creating a group|
|SW100-C0086|P1|runtime|scripts/generate_attestation_bundle_v2.py:73|Attestation generator signs hard-coded successful test results|
|SW100-C0087|P1|runtime|scripts/generate_attestation_bundle_v2.py:320|Artifact verification compares two stored hashes without reading the artifact|
|SW100-C0088|P2|runtime|scripts/generate_attestation_bundle_v2.py:188|Environment provenance is hard-coded for every host|
|SW100-C0089|P2|runtime|00_ABZU_KERNEL/crates/strike-rs/src/gelabp_calc.rs:144|F60 numerator can overflow before applying the advertised score cap|
|SW100-C0090|P2|example|01_KISH_ENGINE/babylon60/utils/watchdog_poc_v5.py:21|Watchdog uses a predictable writable script path|
|SW100-C0091|P1|runtime|00_ABZU_KERNEL/crates/strike-rs/src/hypervisor.rs:341|Validate envelope length before slicing the shared-memory payload|
|SW100-C0092|P2|runtime|00_ABZU_KERNEL/crates/strike-rs/src/hypervisor.rs:105|Reject invalid payload hash text instead of signing a zero digest|
|SW100-C0093|P2|runtime|scripts/c5_quality_gates/daily_sovereign_maintenance.py:210|Propagate failed and missing maintenance phases to the global verdict|
|SW100-C0094|P2|runtime|src/thermodynamics.rs:36|Correct the attojoule scaling of the Landauer constants|
|SW100-C0095|P2|example|scripts/c5_demos/falsacion_semantic_entropy_baremetal.rs:63|Use a wider mask for the advertised eight-sample boundary|
|SW100-C0096|P2|runtime|tools/skill_library/global/c5-audiovisual-acreativo-sota/references/modules/flstudio-mcp-production/hardware/device_Antigravity_MCP.py:116|Make Channel Rack CC ranges disjoint|
|SW100-C0097|P2|runtime|tools/skill_library/global/c5-neural-face-swap-cuadrilla/scripts/c5_face_swap_cli.py:735|Give each render a private source-embedding file|
|SW100-C0098|P2|runtime|tools/skill_library/global/c5-neural-face-swap-cuadrilla/scripts/c5_face_swap_cli.py:1067|Preserve audio offset when rendering a frame subrange|
|SW100-C0099|P2|runtime|tools/skill_library/global/c5-neural-face-swap-cuadrilla/scripts/c5_face_swap_cli.py:864|Paste enhanced image patches when the ellipse mask is selected|
|SW100-C0100|P2|docs|docs/adr/ADR-007-semantic-entropy-zero-float-firewall.md:35|Scope the semantic-entropy correctness claim to supplied constraints|
|SW100-C0101|P2|runtime|00_ABZU_KERNEL/crates/strike-rs/src/kda_memory.rs:90|Restore accepts snapshots larger than the configured capacity|
|SW100-C0102|P2|runtime|00_ABZU_KERNEL/crates/strike-rs/src/kda_memory.rs:51|Zero-capacity KDA buffer still admits an entry|
|SW100-C0103|P1|example|tools/skill_library/global/youtube-analysis-pipeline/scripts/yt_audit.py:17|YouTube URL and output directory are interpolated into a shell|
|SW100-C0104|P2|example|tools/skill_library/global/c5-neural-face-swap-cuadrilla/scripts/c5_smoother.py:272|New face tracks are returned twice on their first frame|
|SW100-C0105|P2|example|scripts/c5_demos/falsacion_semantic_entropy_stress.py:91|Synthetic entropy demo presents label lookup as an empirical NLI comparison|
|SW100-C0106|P2|runtime|01_KISH_ENGINE/babylon60/kernel/mcp_scaffolder.py:188|Unescaped description can break generated Python source|
|SW100-C0107|P1|runtime|00_ABZU_KERNEL/crates/strike-rs/src/ledger.rs:367|Chain verification does not authenticate statement or justification payloads|
|SW100-C0108|P2|runtime|00_ABZU_KERNEL/crates/strike-rs/src/ledger.rs:107|Nogood primary key prevents revoking the same statement in multiple environments|
|SW100-C0109|P2|runtime|00_ABZU_KERNEL/crates/strike-rs/src/ledger.rs:310|Derived assertion and explicit dependency edges commit separately|
|SW100-C0110|P2|docs|docs/01_spec/spec_technical.md:85|Technical specification recommends weaker persistence than the canonical contract|
|SW100-C0111|P2|example|tools/skill_library/codex_overrides/cloudflare/references/sandbox/patterns.md:170|Multi-tenant example trusts a caller-selected identity|
|SW100-C0112|P2|example|tools/skill_library/codex_overrides/cloudflare/references/sandbox/patterns.md:138|CI example interpolates request JSON into a shell command|
|SW100-C0113|P1|runtime|01_KISH_ENGINE/babylon60/kernel/ns_z3_firewall.py:106|PSD check accepts indefinite residual matrices|
|SW100-C0114|P2|runtime|00_ABZU_KERNEL/crates/strike-rs/src/lib.rs:98|Taint serialization admits distinct node contents with identical hashes|
|SW100-C0115|P2|runtime|scripts/guards/c5_signature_engine.py:433|Selector engine labels heuristics as measured optimality|
|SW100-C0116|P2|runtime|scripts/guards/c5_signature_engine.py:108|Missing effort metadata is replaced by a fabricated mode|
|SW100-C0117|P2|docs|docs/02_ontology/axiom_axiomatization.md:322|Claimed score lower-bound theorem omits necessary assumptions|
|SW100-C0118|P3|docs|proof/bundles/attestation_bundle_v2/test_results.json:37|Attestation summary counts disagree with taxonomy|
|SW100-C0119|P2|runtime|00_ABZU_KERNEL/crates/strike-rs/src/omega0.rs:248|derive manufactures FormalProof without checking entailment|
|SW100-C0120|P2|runtime|00_ABZU_KERNEL/crates/strike-rs/src/omega0.rs:278|Deduplicate statements by modality as well as content|
|SW100-C0121|P2|runtime|00_ABZU_KERNEL/crates/strike-rs/src/omega0.rs:199|Freshness obligation never checks observation age|
|SW100-C0122|P2|runtime|01_KISH_ENGINE/babylon60/verifiable_inference/edge0_moe_streamer.py:171|Reject expert slices larger than the configured active budget|
|SW100-C0123|P2|runtime|01_KISH_ENGINE/babylon60/verifiable_inference/edge0_moe_streamer.py:191|Read path copies complete expert outside active-byte accounting|
|SW100-C0124|P2|runtime|scripts/c5_quality_gates/extensions_apoptosis_auditor.py:20|Extension audit targets a package path absent from this checkout|
|SW100-C0125|P2|example|docs/papers/interoceptive-control/benchmarks/run_ablation_matrix.py:113|Ablation violation metric is hardcoded for the gated condition|
|SW100-C0126|P2|docs|tools/skill_library/global/c5-wetware-and-venture-ops/references/modules/c5-tamkarum-60/MODULE.md:127|Written confirmation is described as a substitute for hardware attestation|
|SW100-C0127|P2|runtime|01_KISH_ENGINE/babylon60/kernel/sovereign_binary_analyzer.py:281|Linux fallback discards ordinary objdump instruction lines|
|SW100-C0128|P2|runtime|01_KISH_ENGINE/babylon60/kernel/sovereign_binary_analyzer.py:229|Conditional branch classification omits common branch instructions|
|SW100-C0129|P2|docs|docs/papers/interoceptive-control/manuscript/paper_draft.md:115|Manuscript presents scripted simulation as empirical LLM comparison|
|SW100-C0130|P2|example|tools/skill_library/codex_overrides/cloudflare/references/workers/patterns.md:150|Bearer-prefix example accepts arbitrary credentials|
|SW100-C0131|P2|example|tools/skill_library/codex_overrides/cloudflare/references/secrets-store/configuration.md:169|GitHub Actions secret example embeds secret directly in shell program|
|SW100-C0132|P1|runtime|01_KISH_ENGINE/babylon60/kernel/swarm_orchestrator.py:538|Reject unknown backends instead of silently selecting the remote provider|
|SW100-C0133|P1|runtime|01_KISH_ENGINE/babylon60/kernel/swarm_orchestrator.py:58|Require HTTPS for remote endpoint overrides|
|SW100-C0134|P2|example|docs/papers/interoceptive-control/src/spinal_gate.py:91|Convert milliseconds and forward latency to the correct sensor argument|
|SW100-C0135|P1|runtime|proof/bundles/attestation_bundle_v2/verify:50|Hash the artifact bytes before reporting the artifact verified|
|SW100-C0136|P2|runtime|proof/bundles/attestation_bundle_v2/verify:134|Make the attestation verdict depend on verification results|
|SW100-C0137|P2|example|tools/skill_library/codex_overrides/cloudflare/references/agents-sdk/gotchas.md:102|Remove await from the synchronous onStart example or declare it async|
|SW100-C0138|P1|runtime|00_ABZU_KERNEL/crates/strike-rs/src/session_governance.rs:93|Existing-entry updates preserve the old modality and bypass the rule gate|
|SW100-C0139|P2|runtime|00_ABZU_KERNEL/crates/strike-rs/src/session_governance.rs:144|State commitment omits boundaries between key and content|
|SW100-C0140|P2|runtime|00_ABZU_KERNEL/crates/strike-rs/src/session_governance.rs:101|Zero-capacity governance buffer still accepts an entry|
|SW100-C0141|P2|runtime|01_KISH_ENGINE/babylon60/verification/counterexample.py:20|Counterexample learning returns success without persisting feedback|
|SW100-C0142|P2|example|docs/reference/interpreter.py:76|Canonical event serialization is ambiguous for delimiter-bearing fields|
|SW100-C0143|P2|example|docs/reference/interpreter.py:150|Exported global hash does not bind artifact state|
|SW100-C0144|P2|docs|docs/reference/interpreter.py:174|Reference CLI announces proof dispatch that never occurs|
|SW100-C0145|P2|example|tests/adversarial_nemesis.rs:325|FD exhaustion test also passes when target operation succeeds|
|SW100-C0146|P2|example|tools/skill_library/global/c5-wetware-and-venture-ops/references/modules/somatic-ble-transduction/MODULE.md:65|BLE discovery filters on characteristic UUID instead of advertised service|
|SW100-C0147|P2|example|tests/adversarial_nemesis.rs:489|Cross-device rejection test compares a device ID with itself|
|SW100-C0148|P2|example|tests/adversarial_nemesis.rs:417|Concurrent revocation test asserts a locally manufactured abort|
|SW100-C0149|P2|runtime|01_KISH_ENGINE/babylon60/mcp/cortex_mcp_server.py:1437|Malformed tool arguments terminate the stdio server|
|SW100-C0150|P2|runtime|01_KISH_ENGINE/babylon60/core/browser_agent.py:51|Lamport allocation races across browser agent connections|
|SW100-C0151|P2|runtime|01_KISH_ENGINE/babylon60/core/browser_agent.py:120|Cache commits before the attestation and hides interrupted writes|
|SW100-C0152|P2|example|scripts/c5_demos/poc_aesia_conformity_inspector.py:149|Conformity simulator authorizes CE marking even when checks fail|
|SW100-C0153|P2|example|scripts/c5_demos/poc_aesia_conformity_inspector.py:83|Conformity example labels a status string as verified hardware evidence|
|SW100-C0154|P2|docs|tools/skill_library/codex_overrides/cloudflare/references/flagship/api.md:155|Flagship prerequisite check prints the API token|
|SW100-C0155|P2|example|tools/skill_library/global/c5-audiovisual-acreativo-sota/references/modules/remotion-audio-reactive-video/examples/AudioReactiveMaster.tsx:53|Audio example mutates persistent DSP state during rendering|
|SW100-C0156|P2|runtime|scripts/c5_quality_gates/legion_100_agents_full_monorepo.py:21|Audit workers approve source without reading or checking it|
|SW100-C0157|P2|example|tools/skill_library/global/c5-ring0-babylon-kernel/references/modules/babylon-shield/babylon_exergy_linter.sh:19|Commit linter inspects working tree instead of staged bytes|
|SW100-C0158|P2|runtime|01_KISH_ENGINE/babylon60/core/c5_memory_shield.py:70|Non-Darwin arm reports anti-debug protection despite skipping it|
|SW100-C0159|P2|runtime|01_KISH_ENGINE/babylon60/verification/verification_gate.py:252|Concurrent sign-offs can fork the audit hash chain|
|SW100-C0160|P2|example|scripts/c5_demos/poc_agents_archi_enterprise.py:166|Enterprise PoC reports success without asserting verifier outcomes|
|SW100-C0161|P2|docs|00_ABZU_KERNEL/formal_verification/BabylonBFT.tla:77|TLA liveness comments claim a physical deadline absent from the model|
|SW100-C0162|P2|example|tools/skill_library/global/categorical-hallucination-audit/scripts/audit_kl_d.py:50|Backward conditioning uses the initial prior at the wrong timestep|
|SW100-C0163|P2|runtime|scripts/c5_quality_gates/pipe_audit.py:63|Concurrent audit appends can fork the hash chain|
|SW100-C0164|P2|runtime|01_KISH_ENGINE/babylon60/verification/verifier.py:55|Malformed action fields raise instead of returning rejection|
|SW100-C0165|P2|docs|scripts/c5_demos/poc_annex_vi_compliance.lean:7|Annex VI theorem claims legal guarantees absent from its model|
|SW100-C0166|P3|example|tools/skill_library/codex_overrides/cloudflare/references/ai-gateway/sdk-integration.md:27|Gateway fallback example calls an undeclared Anthropic provider|
|SW100-C0167|P1|runtime|01_KISH_ENGINE/babylon60/core/cortex_persist.py:75|Memory JSON is truncated in place without atomic replacement|
|SW100-C0168|P2|runtime|01_KISH_ENGINE/babylon60/core/cortex_persist.py:87|Concurrent session consolidation loses completed updates|
|SW100-C0169|P2|runtime|01_KISH_ENGINE/babylon60/core/cortex_persist.py:60|UTC clock values are mislabeled with a +02:00 offset|
|SW100-C0170|P2|example|tests/cache_kinetic_benchmark.cpp:145|Zero-operation benchmark indexes an empty latency vector|
|SW100-C0171|P2|example|scripts/c5_demos/poc_antigravity_model_router.py:145|Advertised decision latency excludes receipt signing|
|SW100-C0172|P1|runtime|01_KISH_ENGINE/babylon60/verifier/cli.py:78|Malformed CRL files silently become certificate-ID literals|
|SW100-C0173|P2|runtime|01_KISH_ENGINE/babylon60/mcp/skills_snapshot.py:902|Proposal endpoint reports postconditions VERIFIED without checking an effect|
|SW100-C0174|P2|runtime|tools/skill_library/workspace/c5-anti-slop-ui/scripts/audit_ui_slop.py:130|Directory linter skips arbitrary source paths containing build or dist|
|SW100-C0175|P1|runtime|01_KISH_ENGINE/babylon60/verifier/standalone_verify.py:889|Require digest coverage for every required evidence file|
|SW100-C0176|P2|runtime|01_KISH_ENGINE/babylon60/verifier/standalone_verify.py:954|Reject an empty execution trace for a nonempty ledger|
|SW100-C0177|P1|runtime|01_KISH_ENGINE/babylon60/verifier/standalone_verify.py:450|Recompute JSON event hashes before declaring integrity verified|
|SW100-C0178|P1|runtime|contracts/com.c5real.moskv1.kernel.plist:33|Remove the shared bearer credential from the launchd template|
|SW100-C0179|P2|runtime|scripts/c5_quality_gates/run_cache_audit.py:25|Cache audit resolves benchmark below scripts instead of repository root|
|SW100-C0180|P2|example|tools/skill_library/global/c5-ring0-babylon-kernel/references/modules/c5-lean4-neurosymbolic-architect/MODULE.md:255|Single-chunk ledger example accepts an invalid chunk|
|SW100-C0181|P2|runtime|01_KISH_ENGINE/babylon60/memory/__init__.py:43|Exported MemoryStore silently drops all writes|
|SW100-C0182|P2|runtime|01_KISH_ENGINE/babylon60/core/discrete_curvature.py:20|Effective resistance silently treats disconnected graphs as finite|
|SW100-C0183|P2|docs|scripts/c5_quality_gates/run_cache_audit.py:57|Cache report unconditionally claims mitigation and patentability|
|SW100-C0184|P1|runtime|01_KISH_ENGINE/babylon60/memory/governance.py:468|Dependency validation and revocation are separated from insertion by unlocked transactions|
|SW100-C0185|P1|runtime|01_KISH_ENGINE/babylon60/memory/governance.py:644|Ledger acknowledgement precedes durable memory-state mutation without recovery|
|SW100-C0186|P2|runtime|01_KISH_ENGINE/babylon60/memory/governance.py:632|Revocation silently truncates dependency closure after 1024 levels|
|SW100-C0187|P2|runtime|01_KISH_ENGINE/babylon60/memory/governance.py:226|Policy epoch rolls back on engine restart|
|SW100-C0188|P2|example|scripts/c5_demos/poc_bounty_dispatcher_ffi.py:11|Python-only counter loop is described as Rust FFI and SPMC validation|
|SW100-C0189|P2|example|tools/skill_library/global/c5-ring0-babylon-kernel/references/modules/c5-mushushu-0/MODULE.md:67|Example formal gate approves a truthy field without checking a proof|
|SW100-C0190|P2|example|tools/skill_library/codex_overrides/cloudflare/references/ai-search/gotchas.md:9|Folder prefix example uses an unbounded lexical lower bound|
|SW100-C0191|P2|example|tests/differential/mod.rs:47|Differential comparison reads both artifacts after the Rust run|
|SW100-C0192|P2|runtime|scripts/preflight.sh:5|Preflight suppresses compilation failure and still approves|
|SW100-C0193|P2|runtime|scripts/preflight.sh:7|Environment preflight also changes remote branch protection|
|SW100-C0194|P2|runtime|scripts/c5_quality_gates/sharur_3600_audit_swarm.py:101|Auditor follows file symlinks when rewriting targets|
|SW100-C0195|P2|runtime|01_KISH_ENGINE/babylon60/adapters/codex/codex_driver.py:160|Codex query reports success after a failed execution with partial text|
|SW100-C0196|P2|example|tools/skill_library/codex_overrides/cloudflare/references/ai-search/patterns.md:24|Tenant example treats a lower bound as prefix isolation|
|SW100-C0197|P3|docs|00_ABZU_KERNEL/crates/babylon60-compiler/README.md:4|Compiler README links resolve outside the repository root targets|
|SW100-C0198|P2|runtime|01_KISH_ENGINE/babylon60/core/landauer.py:49|Idle eviction uses tenant age instead of inactivity|
|SW100-C0199|P2|runtime|01_KISH_ENGINE/babylon60/memory/metamemory.py:119|Tip-of-tongue branch is mathematically unreachable|
|SW100-C0200|P2|example|tools/skill_library/codex_overrides/cloudflare/references/hyperdrive/api.md:127|Drizzle example shadows the table with the query result|
|SW100-C0201|P1|runtime|01_KISH_ENGINE/cortex/crates/babylon60-verifiable-inference/src/lib.rs:90|Inference verifier proves only a freely chosen multiplication witness|
|SW100-C0202|P1|runtime|01_KISH_ENGINE/cortex/crates/babylon60-verifiable-inference/src/lib.rs:25|Groth16 setup randomness is publicly reproducible|
|SW100-C0203|P2|runtime|01_KISH_ENGINE/babylon60/adapters/codex/tunnel_bus.py:160|Claim pending messages atomically before delivering them|
|SW100-C0204|P2|runtime|01_KISH_ENGINE/babylon60/adapters/codex/tunnel_bus.py:85|Persistent tunnel connections lower required durability to NORMAL|
|SW100-C0205|P2|example|scripts/c5_quality_gates/swarm_100_stress_campaign.py:183|Adversarial campaign rejects labels instead of exercising independent gates|
|SW100-C0206|P2|example|tools/skill_library/codex_overrides/cloudflare/references/analytics-engine/api.md:39|Do not copy authentication credentials into analytics dimensions|
|SW100-C0207|P3|example|scripts/repatriated/apex_merkle_l5_anchor.py:64|Anchor demo announces irreversible Bitcoin anchoring without submitting anything|
|SW100-C0208|P1|runtime|01_KISH_ENGINE/babylon60/core/moskv_kernel.py:90|Queued claims capture an obsolete predecessor and are silently discarded|
|SW100-C0209|P2|runtime|01_KISH_ENGINE/babylon60/memory/provenance_arbiter.py:168|Provenance ATTESTED accepts caller-supplied receipt labels without verifying evidence|
|SW100-C0210|P2|runtime|scripts/c5_quality_gates/swarm_lock_guard.py:28|Stale lock eviction can delete a live replacement lock|
|SW100-C0211|P2|example|scripts/c5_demos/poc_enterprise_clone_and_run.sh:56|Bootstrap reports operational success when daemon is absent|
|SW100-C0212|P2|docs|docs/03_guides/guide_explanation.md:99|Guide directs broad automatic commits and contradicts current commit contract|
|SW100-C0213|P2|runtime|01_KISH_ENGINE/cortex/crates/c5_compiler/src/lib.rs:184|Parser allocates the RHS name instead of the declared binding|
|SW100-C0214|P1|runtime|00_ABZU_KERNEL/crates/babylon60-compiler/src/backend_x86.rs:88|Stack slots grow beyond the reserved 256-byte frame|
|SW100-C0215|P2|runtime|00_ABZU_KERNEL/crates/babylon60-compiler/src/backend_x86.rs:36|Backend compile retains output and registers from previous compilation|
|SW100-C0216|P2|runtime|scripts/c5_quality_gates/symlink_depth_auditor.py:23|Symlink depth validator accepts three or more parent traversals|
|SW100-C0217|P2|example|tools/skill_library/codex_overrides/cloudflare/references/analytics-engine/gotchas.md:12|Preaggregation example loses almost all events|
|SW100-C0218|P2|docs|scripts/repatriated/audit_titan_jwt.py:60|Audit result labels hardcoded assertions as verified claims|
|SW100-C0219|P1|runtime|scripts/repatriated/c5_sharur_100_anergy_purge.py:98|Do not unlink SQLite journals based solely on their suffix|
|SW100-C0220|P2|runtime|crates/b60-lang/src/arithmetic.rs:29|Normalize rational ticks before returning them|
|SW100-C0221|P1|runtime|01_KISH_ENGINE/babylon60/core/popperian_filter.py:112|Reject oversized content or return the exact bytes that were filtered|
|SW100-C0222|P2|example|scripts/c5_demos/poc_kish_shell_sovereign_transducer.rs:31|Preserve poisoning when the example writer is called again|
|SW100-C0223|P2|runtime|scripts/repatriated/c5_sharur_100_anergy_purge.py:175|Limit Lean cleanup to verified disposable build products|
|SW100-C0224|P2|example|scripts/c5_demos/poc_kish_shell_sovereign_transducer.rs:166|Label model arithmetic separately from physical thermodynamic evidence|
|SW100-C0225|P2|runtime|scripts/c5_quality_gates/sync_version.py:133|Version synchronization reports success for missing required targets|
|SW100-C0226|P2|example|crates/b60-lang/src/bin/aeon_chaining.rs:112|Aeon verifier proves individual blocks without checking their connecting states|
|SW100-C0227|P2|example|scripts/c5_demos/poc_legion_1000.py:247|Legion PoC passes without asserting any receipt was persisted|
|SW100-C0228|P2|example|scripts/c5_demos/poc_legion_1000.py:248|Legion PoC claims validation of 1000 agents from a sequential batch of 100 advisories|
|SW100-C0229|P2|docs|01_KISH_ENGINE/babylon60/oncology_primitives.py:1809|Genomic mechanics metadata is shifted onto the next primitive|
|SW100-C0230|P2|runtime|01_KISH_ENGINE/babylon60/core/representation_geometry.py:116|ZCA whitening crashes for a valid single-feature matrix|
|SW100-C0231|P2|runtime|01_KISH_ENGINE/babylon60/persistence/cortex_wal_store.py:131|Truncated idempotency keys collide in the audit-event primary key|
|SW100-C0232|P2|runtime|01_KISH_ENGINE/babylon60/persistence/cortex_wal_store.py:133|Checkpoint read-modify-write occurs outside the write transaction|
|SW100-C0233|P2|example|scripts/repatriated/larsa120_isostatic_synthesis.py:69|Synthetic broker labels Python predicates as hardware-attested consensus|
|SW100-C0234|P2|example|scripts/c5_demos/poc_mass_stage3_resolution.py:75|Failover demo reports success when every tier is unavailable|
|SW100-C0235|P2|runtime|tools/skill_library/global/c5-rubin-acoustic-linter/scripts/audit_acoustic_exergy.py:88|Acoustic true-peak output measures only the mono sample peak|
|SW100-C0236|P2|runtime|scripts/c5_quality_gates/verify_claims.py:107|Local claim provenance omits untracked source consumed by verification|
|SW100-C0237|P2|example|tests/test_cortex_mcp_server.py:640|Rust stdio interoperability test can exercise a stale binary|
|SW100-C0238|P2|example|00_ABZU_KERNEL/crates/babylon60-compiler/src/lowering.rs:49|Resolve the actual field offset when lowering assignments|
|SW100-C0239|P2|runtime|01_KISH_ENGINE/babylon60/core/thermal_lock.py:55|Use a monotonic clock for the cooldown interval|
|SW100-C0240|P2|example|scripts/c5_demos/poc_quasar_triple_vector.sh:22|Create a private temporary directory before writing and executing the demo|
|SW100-C0241|P2|example|scripts/repatriated/legion_100_swarm_audit.py:95|Label generated swarm findings and metrics as synthetic in exported evidence|
|SW100-C0242|P1|runtime|tools/skill_library/global/c5-secops-infra-devtools/references/modules/c5-browser-forensics-and-extension-triage/scripts/browser_forensics.py:171|Reject path components before recursive extension deletion|
|SW100-C0243|P2|runtime|01_KISH_ENGINE/babylon60/core/thermo_ast_pruner.py:16|Preserve a statement when removing a sole docstring|
|SW100-C0244|P2|runtime|01_KISH_ENGINE/babylon60/core/thermo_ast_pruner.py:60|Recognize imported bindings before suppressing required imports|
|SW100-C0245|P2|runtime|00_ABZU_KERNEL/crates/babylon60-compiler/src/parser.rs:57|Return a lexical error for out-of-range integer literals|
|SW100-C0246|P2|runtime|tools/skill_library/global/existence-gap-audit/scripts/existence_gap.py:1253|Fail the audit gate when Python source cannot be parsed|
|SW100-C0247|P2|runtime|crates/b60-lang/src/compiler.rs:131|Malformed bracket order panics instead of returning compile error|
|SW100-C0248|P2|runtime|crates/b60-lang/src/compiler.rs:43|Named registers silently alias after six variables|
|SW100-C0249|P2|example|scripts/c5_setup/install_into_repo.sh:32|Installer commits unrelated staged changes and hides copy failures|
|SW100-C0250|P2|example|scripts/repatriated/poc_port_hamiltonian_deliberation.py:104|Claimed monotonicity accepts positive energy increments|
|SW100-C0251|P2|runtime|crates/b60-lang/src/compiler.rs:132|NIG silently truncates multi-place literals to 255|
|SW100-C0252|P1|runtime|01_KISH_ENGINE/babylon60/api/tracer.py:83|Session ID can escape evidence storage directory|
|SW100-C0253|P2|runtime|01_KISH_ENGINE/babylon60/api/tracer.py:112|Closed audit sessions still accept unsealed events|
|SW100-C0254|P2|runtime|01_KISH_ENGINE/babylon60/api/tracer.py:169|Failed evidence persistence permanently marks session closed|
|SW100-C0255|P2|runtime|01_KISH_ENGINE/babylon60/api/tracer.py:172|AL0 and AL1 roots do not commit to their events|
|SW100-C0256|P2|runtime|scripts/c5_setup/setup_nacho_cortex.ps1:23|Windows setup resolves scripts as repository root|
|SW100-C0257|P2|example|scripts/c5_demos/poc_shm_orchestrator.py:32|SHM example requests writable ctypes buffer from read-only mmap|
|SW100-C0258|P2|docs|scripts/repatriated/run_swarm_batch_021_040.py:64|Batch audit hardcodes successful falsification verdicts|
|SW100-C0259|P2|runtime|01_KISH_ENGINE/babylon60/primitives/cbor.py:141|Reject truncated CBOR byte/text strings|
|SW100-C0260|P2|runtime|crates/b60-lang/src/ffi.rs:38|Check arithmetic overflow at the C ABI boundary|
|SW100-C0261|P2|runtime|scripts/c5_setup/setup_nacho_cortex.sh:22|Compute the actual repository root in setup|
|SW100-C0262|P2|example|scripts/c5_demos/poc_sovereign_spark_daemon.py:131|Label simulated receipts as simulated, without hardware identity|
|SW100-C0263|P2|docs|scripts/repatriated/run_swarm_batch_041_060.py:74|Do not certify empirical survival from keyword templates|
|SW100-C0264|P2|runtime|tools/skill_library/global/c5-secops-infra-devtools/references/modules/c5-socint-extraction-suite/scripts/socint_extract.py:698|Bind field names and types into the evidence seal|
|SW100-C0265|P2|runtime|tools/skill_library/global/c5-secops-infra-devtools/references/modules/c5-socint-extraction-suite/scripts/socint_extract.py:2090|Namespace vault record IDs by platform and instance|
|SW100-C0266|P2|runtime|tools/skill_library/global/f5tts-voice-cloning-sota/scripts/synthesize_vocal_clone.py:107|Use a unique temporary audio file for each synthesis|
|SW100-C0267|P2|docs|docs/03_guides/tutorial_hello_causal.md:200|Avoid treating missing failure logs as proof of all invariants|
|SW100-C0268|P2|runtime|tools/skill_library/global/c5-secops-infra-devtools/references/modules/c5-socint-extraction-suite/scripts/socint_extract.py:2994|Emit a valid JSON container for batch output|
|SW100-C0269|P2|docs|tools/skill_library/global/c5-secops-infra-devtools/references/modules/c5-socint-extraction-suite/scripts/socint_extract.py:1586|Do not label watch-page text as an audio transcript|
|SW100-C0270|P2|docs|tools/skill_library/global/c5-secops-infra-devtools/references/modules/c5-socint-extraction-suite/scripts/socint_extract.py:174|Label regex matches as candidate facts rather than verified facts|
|SW100-C0271|P1|runtime|01_KISH_ENGINE/babylon60/attestation/conformal_tree.py:173|Manifest verification trusts the public key supplied by the manifest|
|SW100-C0272|P2|runtime|01_KISH_ENGINE/babylon60/attestation/conformal_tree.py:47|Claim leaf encoding admits delimiter collisions|
|SW100-C0273|P2|runtime|01_KISH_ENGINE/babylon60/primitives/disintegration_matrix.py:96|Symmetry verifier ignores additional reverse-kernel mass|
|SW100-C0274|P2|example|scripts/repatriated/sharur3600_host_triage_py.py:78|Host triage emits static corpus observations as current audit results|
|SW100-C0275|P2|runtime|scripts/c5_setup/unboxing_moskv1.py:46|Unboxing claims Touch ID readiness from file existence|
|SW100-C0276|P1|runtime|01_KISH_ENGINE/babylon60/attestation/merkle_anchor.py:117|Software hashes are exported as hardware-sealed TPM quotes|
|SW100-C0277|P1|runtime|01_KISH_ENGINE/babylon60/attestation/merkle_anchor.py:155|Notary checkpoint declares a verified quorum without contacting validators|
|SW100-C0278|P2|runtime|scripts/c5_sharur/agent_beeper.py:68|Unicast beeps cannot wake an already waiting agent|
|SW100-C0279|P2|runtime|scripts/c5_sharur/agent_beeper.py:62|A swarm broadcast remains permanently pending for subsequent waits|
|SW100-C0280|P2|runtime|01_KISH_ENGINE/babylon60/cortex/cortex_bpe_tokenizer.py:21|Tokenizer cannot encode ordinary Unicode outside Latin-1|
|SW100-C0281|P2|example|tools/skill_library/global/c5-secops-infra-devtools/references/modules/c5-sovereign-identity-hardening/MODULE.md:44|Password breach checker reports success when its API request fails|
|SW100-C0282|P2|example|scripts/c5_demos/poc_srp_soc_falsification.py:224|SRP falsification compares predetermined conflict models and unequal workloads|
|SW100-C0283|P2|docs|docs/04_research/LOS_10_MAYORES_DESCUBRIMIENTOS_Y_AVANCES.md:205|Formal model proofs are presented as absolute physical runtime guarantees|
|SW100-C0284|P1|runtime|scripts/c5_sharur/auto_heal_hardcoded_paths.py:119|Path import inserted before __future__ imports makes rewritten modules invalid|
|SW100-C0285|P2|runtime|scripts/c5_sharur/auto_heal_hardcoded_paths.py:103|Existing pathlib import incorrectly treated as a bound Path name|
|SW100-C0286|P2|example|scripts/c5_demos/poc_vsa_saturation_stress.py:225|Bundling success claims are emitted without checking measured results|
|SW100-C0287|P2|example|tests/test_entropy_synthesis_omega.py:97|Lean verification silently passes when compiler is absent|
|SW100-C0288|P2|example|tools/skill_library/global/c5-secops-infra-devtools/references/modules/c5-sovereign-identity-hardening/scripts/check_pwned_pass.sh:15|Password audit requires plaintext secret in command-line arguments|
|SW100-C0289|P2|runtime|scripts/c5_sharur/c5_bounty_sharur_exfiltration.py:177|Swarm reports successful completion after dropping failed claims|
|SW100-C0290|P2|example|tests/test_swarm_reverse_engineering_bench.py:197|Bounded-memory test asserts storage growing linearly with agents|
|SW100-C0291|P1|runtime|01_KISH_ENGINE/babylon60/autodidact/crystal_compiler.py:239|JSON integrity verification trusts embedded statement hashes|
|SW100-C0292|P1|runtime|01_KISH_ENGINE/babylon60/autodidact/crystal_compiler.py:210|Markdown integrity check accepts any structurally present root|
|SW100-C0293|P2|runtime|01_KISH_ENGINE/babylon60/autodidact/crystal_compiler.py:250|Optional evidence digests use inconsistent Merkle leaf encodings|
|SW100-C0294|P1|runtime|01_KISH_ENGINE/babylon60/primitives/sandbox.py:408|In-process sandbox has no allocation or output bound|
|SW100-C0295|P2|runtime|01_KISH_ENGINE/babylon60/primitives/sandbox.py:421|Ordinary generated-code errors escape ExecResult handling|
|SW100-C0296|P2|test|tests/test_swarm_seqlock_zero_copy.py:60|Concurrent seqlock test never validates payload consistency|
|SW100-C0297|P2|example|scripts/c5_sharur/c5_bounty_sharur_omega_10k.py:386|Report labels a byte-count formula as dissipated energy|
|SW100-C0298|P1|runtime|01_KISH_ENGINE/babylon60/cortex/cortex_purge_anergy.py:23|Purge targets its installed package and moves importable modules|
|SW100-C0299|P2|runtime|01_KISH_ENGINE/cortex/crates/cortex-guard/src/eval.rs:54|Rule evaluation reports SAT when a required property is absent|
|SW100-C0300|P2|runtime|crates/b60-lang/src/main.rs:174|Prove ignores source and declares compilation without invoking Lean|
|SW100-C0301|P2|test|tests/test_swarm_stress.py:41|Stress concurrency limit is private to each agent|
|SW100-C0302|P2|example/docs|tools/skill_library/global/c5-secops-infra-devtools/references/modules/electron-asar-forensic-audit/MODULE.md:57|ASAR scanner example returns an already closed stream|
|SW100-C0303|P1|runtime|01_KISH_ENGINE/babylon60/autodidact/epistemology.py:146|Derivation creates FormalProof for an unrelated goal|
|SW100-C0304|P2|runtime|crates/b60-lang/src/mmr.rs:181|Proof verifier ignores the claimed leaf index|
|SW100-C0305|P2|runtime|crates/b60-lang/src/mmr.rs:198|Malformed peak index panics instead of rejecting proof|
|SW100-C0306|P2|runtime|01_KISH_ENGINE/cortex/crates/cortex-guard/src/ifc.rs:64|IFC parser splits semicolons inside quoted values|
|SW100-C0307|P2|example|tools/skill_library/codex_overrides/turnstile-spin/scripts/persist-skill.sh:87|Skill persistence reports success after failed copy|
|SW100-C0308|P2|runtime|01_KISH_ENGINE/cortex/crates/cortex-guard/src/ifc.rs:171|Setback distance fabricated from local placement axes|
|SW100-C0309|P2|docs|scripts/c5_sharur/garbage_collection_sitrep.json:5|Garbage collection totals count repeated scans as reclaimable bytes|
|SW100-C0310|P2|runtime|crates/b60-lang/src/repl.rs:171|REPL spins indefinitely after stdin reaches EOF|
|SW100-C0311|P2|runtime|crates/b60-lang/src/repl.rs:58|Sexagesimal addition overflows for accepted u64 operands|
|SW100-C0312|P2|runtime|scripts/sharur/download_papers.py:6|Paper downloader disables HTTPS certificate validation globally|
|SW100-C0313|P2|runtime|01_KISH_ENGINE/babylon60/primitives/yaml_parser.py:83|YAML parser strips hash characters inside quoted strings|
|SW100-C0314|P2|runtime|01_KISH_ENGINE/babylon60/cortex/gemini_labs_nexus.py:144|Gemini generation tool returns a canned response without invoking Gemini|
|SW100-C0315|P2|runtime|01_KISH_ENGINE/babylon60/cortex/gemini_labs_nexus.py:90|Receipt producer labels a public hash prefix as an Ed25519 signature|
|SW100-C0316|P2|runtime|tests/test_syntax_integrity.py:17|Syntax integrity gate omits the primary babylon60 package|
|SW100-C0317|P1|example|.agents/skills/c5-ring0-babylon-kernel-project/references/modules/shared-manifest-kernel/MODULE.md:91|Concurrent publish can overwrite the fail-stop state|
|SW100-C0318|P2|example|.agents/skills/c5-ring0-babylon-kernel-project/references/modules/shared-manifest-kernel/MODULE.md:119|Retry exhaustion does not perform the documented halt|
|SW100-C0319|P2|example|scripts/sharur/run_sharur_1000.py:25|Synthetic worker scores are presented without a simulation label|
|SW100-C0320|P2|example|scripts/c5_demos/stress_test_multi_ide_injection.py:157|Concurrent installer mutations are never followed by an integrity audit|
|SW100-C0321|P2|runtime|scripts/c5_sharur/sharur_100_conversation_auditor.py:108|Missing corpus crashes the auditor before it can report absence|
|SW100-C0322|P2|runtime|scripts/c5_sharur/sharur_100_conversation_auditor.py:116|OpenAI secret detector uses a literal malformed repetition|
|SW100-C0323|P2|runtime|scripts/c5_sharur/sharur_100_conversation_auditor.py:444|Audit emits unconditional compliance verdicts without examining evidence|
|SW100-C0324|P3|example|tools/skill_library/global/flstudio-mcp-production/examples/Euclidean_Polyrhythm_Generator.py:62|Polymeter selection is ignored by the generator|
|SW100-C0325|P2|runtime|tools/skill_library/global/c5-secops-infra-devtools/references/modules/existence-gap-audit/scripts/existence_gap.py:273|Comment stripping corrupts quoted URLs in tsconfig|
|SW100-C0326|P1|runtime|crates/b60-lang/src/vm.rs:53|Arithmetic overflow escapes VM fail-closed handling|
|SW100-C0327|P2|runtime|crates/b60-lang/src/vm.rs:198|Out-of-range jumps return successful execution|
|SW100-C0328|P1|runtime|scripts/c5_sharur/sharur_100_conversation_reporters.py:341|Forensic report certifies controls without checking them|
|SW100-C0329|P2|example|scripts/c5_demos/z3_firewall_stress_test.py:76|Stress gate never asserts validation and rejection counts|
|SW100-C0330|P2|runtime|01_KISH_ENGINE/babylon60/crypto/bootstrap.py:65|Bootstrap stores unencrypted private key in encrypted-key column|
|SW100-C0331|P2|runtime|01_KISH_ENGINE/babylon60/services/inbound_email.py:234|Failed email handlers are acknowledged and permanently deduplicated|
|SW100-C0332|P2|example|00_ABZU_KERNEL/crates/babylon60-kernel/examples/poc_darwin_bridge.rs:48|Filesystem event arithmetic overflows before burnout can be observed|
|SW100-C0333|P2|example|scripts/c5_demos/zk_causal_gate_stress_test.py:76|Simulation announces a verified ZK invariant from a synthetic timing comparison|
|SW100-C0334|P2|docs|scripts/c5_sharur/sharur_100_conversations_sitrep.json:1409|Archived sitrep presents constant success values as independent attestation|
|SW100-C0335|P1|runtime|00_ABZU_KERNEL/crates/babylon60-kernel/src/eval.rs:95|Signed integer division can panic instead of returning Critical halt|
|SW100-C0336|P1|runtime|01_KISH_ENGINE/cortex/crates/cortex-lsp/src/actions.rs:103|Ledger audit reports HEALTHY without inspecting any ledger|
|SW100-C0337|P1|runtime|01_KISH_ENGINE/babylon60/crypto/identity.py:101|Identity forging truncates existing master seed and is not atomic|
|SW100-C0338|P2|example|tools/skill_library/global/c5-cortex-swarm-orchestrator/references/modules/c5-tri-provider-swarm/scripts/tri_swarm_dispatcher.py:63|Production-labelled dispatcher returns successful work without calling providers|
|SW100-C0339|P2|runtime|scripts/verify_release.sh:193|Release verifier accepts a bundle with no manifest digest binding|
|SW100-C0340|P2|example|scripts/c5_demos/zk_shm_starvation_stress_test.py:66|Benchmark extrapolates Python loops into isolation guarantees|
|SW100-C0341|P1|runtime|crates/babylon-attest/src/conformal_tree.rs:206|Aeon verifier trusts the public key supplied by the untrusted manifest|
|SW100-C0342|P2|runtime|crates/babylon-attest/src/conformal_tree.rs:227|Aeon identity, claim count and hardware metadata are outside the signature|
|SW100-C0343|P1|runtime|scripts/c5_sharur/sharur_100_full_spectrum_auditor.py:80|Full-spectrum auditor emits PASS and certified measurements without performing checks|
|SW100-C0344|P2|runtime|scripts/c5_deploy/deploy.sh:12|Deployment script exits successfully after both publication commands fail|
|SW100-C0345|P1|runtime|01_KISH_ENGINE/babylon60/crypto/keys.py:85|Metadata writes can overwrite another manager’s keys or revocations|
|SW100-C0346|P2|runtime|01_KISH_ENGINE/babylon60/bft/bayesian_swarm.py:80|Zero-weight agents still veto pooled hypotheses|
|SW100-C0347|P2|runtime|scripts/c5_sharur/sharur_100_garbage_collector.py:106|Garbage collection totals count each target repeatedly|
|SW100-C0348|P2|runtime|01_KISH_ENGINE/cortex/crates/cortex-lsp/src/main.rs:47|Additional LSP headers are consumed as JSON payload bytes|
|SW100-C0349|P1|runtime|crates/babylon-attest/src/ledger.rs:123|Serialize ledger read-modify-append across writers|
|SW100-C0350|P1|runtime|crates/babylon-attest/src/ledger.rs:166|Sync committed ledger records before acknowledging success|
|SW100-C0351|P2|runtime|crates/babylon-attest/src/ledger.rs:273|Export the actual block hash algorithm|
|SW100-C0352|P2|runtime|01_KISH_ENGINE/babylon60/tools/context7_client.py:52|Enforce the advertised subprocess timeout|
|SW100-C0353|P2|runtime|01_KISH_ENGINE/babylon60/bft/bounty_claim_attester.py:116|Bind finding metadata into receipt verification|
|SW100-C0354|P1|example|scripts/c5_sharur/sharur_100_swarm_execution.py:169|Label simulated audit results instead of emitting verified passes|
|SW100-C0355|P2|runtime|scripts/c5_sharur/sharur_21_agentes.py:121|JSON telemetry is preceded by an unconditional banner|
|SW100-C0356|P2|runtime|scripts/c5_destiladora/codegen_rust_b60.py:191|Code generation records uncompiled rules as compiled and active|
|SW100-C0357|P2|runtime|01_KISH_ENGINE/babylon60/crypto/rekor_client.py:56|Rekor public key contract disagrees with both ledger callers|
|SW100-C0358|P1|runtime|01_KISH_ENGINE/babylon60/bft/bounty_pipeline_orchestrator.py:138|Handle rejected cold-ledger enqueue results|
|SW100-C0359|P2|runtime|scripts/c5_sharur/sharur_222_agentes.py:50|Propagate pytest.main exit code from FUZZ workers|
|SW100-C0360|P1|docs|scripts/babylon60/gen_oncology_primitives.py:149|Remove globally inconsistent list-length axiom from generated Lean|
|SW100-C0361|P2|docs|scripts/babylon60/gen_oncology_primitives.py:152|Close the namespace in generated Lean output|
|SW100-C0362|P2|runtime|scripts/c5_destiladora/destiladora_schema.sql:8|Use durable synchronous mode in trace-ledger schema|
|SW100-C0363|P2|runtime|01_KISH_ENGINE/babylon60/transducers/appgen_ast_transducer.py:81|Do not approve JavaScript solely from balanced delimiters|
|SW100-C0364|P1|runtime|01_KISH_ENGINE/babylon60/crypto/shredder.py:353|Shredding never prevents AES decryption|
|SW100-C0365|P2|runtime|01_KISH_ENGINE/babylon60/crypto/shredder.py:256|Async shredder does not initialize its table|
|SW100-C0366|P2|runtime|01_KISH_ENGINE/babylon60/crypto/shredder.py:394|Audit timestamp uses uptime as Unix time|
|SW100-C0367|P2|runtime|crates/babylon-attest/src/main.rs:211|JSON attest output is prefixed by human license text|
|SW100-C0368|P2|runtime|crates/babylon-attest/src/main.rs:418|Sidecar blocks all requests on a single idle client|
|SW100-C0369|P2|runtime|crates/babylon-attest/src/main.rs:475|Sidecar skips license enforcement on event writes|
|SW100-C0370|P1|runtime|scripts/babylon_launcher.py:47|Launcher serves an absent UI directory|
|SW100-C0371|P2|runtime|scripts/c5_sharur/sharur_master_swarm_runner.py:61|Swarm release audit reports hard-coded successful checks|
|SW100-C0372|P2|example|tools/skill_library/global/c5-secops-infra-devtools/references/modules/github-architect/scripts/git_history_sanitizer.py:78|Git publication auditor certifies history after scanning only 100 commits|
|SW100-C0373|P1|runtime|01_KISH_ENGINE/babylon60/transducers/c5_mail_transducer.py:85|Curl failure can return the mail API key in error detail|
|SW100-C0374|P2|runtime|scripts/c5_sharur/sharur_swarm.py:17|Swarm entry point imports a module absent after renaming|
|SW100-C0375|P2|runtime|01_KISH_ENGINE/babylon60/bft/bounty_ring_dispatcher.py:55|Bounded advisory queues silently discard accepted frames|
|SW100-C0376|P2|runtime|scripts/c5_destiladora/invariant_extractor_z3.py:86|Extractor promotes a satisfiable assumption set without checking the trace cluster|
|SW100-C0377|P1|runtime|src/attestation_contract.rs:54|Concurrent publish calls can expose mixed attestation fields|
|SW100-C0378|P1|runtime|scripts/c5_destiladora/proof_emitter_lean4.py:193|PROVED status certifies a fixed model unrelated to extracted preconditions|
|SW100-C0379|P2|example|tools/skill_library/global/c5-secops-infra-devtools/references/modules/github-architect/scripts/repo_health.py:179|Generated Python CI masks every pytest failure|
|SW100-C0380|P2|example|tools/skill_library/codex_overrides/cloudflare/references/turn/configuration.md:83|TURN credential example accepts any nonempty Authorization header|
|SW100-C0381|P1|runtime|src/babylon60.rs:540|Quarantine exports overwrite prior forensic evidence|
|SW100-C0382|P2|runtime|src/babylon60.rs:392|BA.EXACT silently truncates non-sexagesimal fractions|
|SW100-C0383|P2|runtime|src/babylon60.rs:330|Malformed instruction operands panic past static validation|
|SW100-C0384|P2|runtime|src/babylon60.rs:554|Artifact global hash omits opcode and proof IR|
|SW100-C0385|P1|example|scripts/c5_destiladora/test_destiladora_e2e.py:81|E2E script contaminates and resets the persistent CORTEX database|
|SW100-C0386|P2|example|scripts/c5_destiladora/test_destiladora_e2e.py:151|Benchmark reports a measured fast-path latency without timing it|
|SW100-C0387|P1|runtime|tools/skill_library/global/anergy-purge-protocol/scripts/anergy_purge.py:183|Delete only proven orphan WAL files|
|SW100-C0388|P2|runtime|tools/skill_library/global/anergy-purge-protocol/scripts/anergy_purge.py:191|Scope listener resets to an explicitly selected operation|
|SW100-C0389|P2|runtime|scripts/c5_calibrations/calibrate_aphairesis.py:145|Generate calibration constants in the module actually compiled|
|SW100-C0390|P2|runtime|tools/skill_library/global/c5-secops-infra-devtools/references/modules/github-architect/scripts/scitt_attestor.py:83|Do not certify hardware and SLSA properties without evidence|
|SW100-C0391|P2|runtime|tools/skill_library/global/flstudio-mcp-production/hardware/device_Antigravity_MCP.py:116|Keep channel selection ranges disjoint|
|SW100-C0392|P2|example|tools/skill_library/codex_overrides/cloudflare/references/turn/patterns.md:64|Port-53 filtering also removes the documented TLS port 5349|
|SW100-C0393|P1|runtime|crates/babylon-skills-mcp/src/lib.rs:1890|Proposal handler fabricates verified postconditions without independent execution|
|SW100-C0394|P2|runtime|crates/babylon-skills-mcp/src/lib.rs:2098|Legacy read methods bypass configured project visibility|
|SW100-C0395|P2|runtime|01_KISH_ENGINE/extensions/moskv-fx-scavenger/content.js:149|Terminal generation failure is swallowed and retried until timeout|
|SW100-C0396|P2|runtime|scripts/c5_calibrations/calibrate_popperian_entropy.py:52|Calibration resolves its technical corpus under scripts instead of the repository|
|SW100-C0397|P2|runtime|scripts/c5_edin/edin_swarm_runner.py:46|Simulated audit runner persists unconditional verified completion events|
|SW100-C0398|P2|example|examples/fl005_toctou_stress.rs:399|TOCTOU harness can certify a campaign that performs no attack|
|SW100-C0399|P2|example|tools/skill_library/codex_overrides/cloudflare/references/turnstile/README.md:47|Turnstile Worker example references an undeclared env binding|
|SW100-C0400|P1|runtime|src/bin/babylon_top.rs:96|Telemetry monitor displays fabricated security evidence as live state|
|SW100-C0401|P1|runtime|scripts/c5_edin/f13_233_specialist_audit_matrix.py:557|Unimplemented specialists are counted as successful verification|
|SW100-C0402|P2|example|scripts/c5_calibrations/topological_calibration.py:76|KL computation compares histograms with incompatible bin edges|
|SW100-C0403|P2|runtime|01_KISH_ENGINE/babylon60/bft/cortex_persist_ledger.py:798|Configured invalid signing seed silently switches identity|
|SW100-C0404|P2|example|examples/fl006_crash_consistency.rs:471|Crash harness cannot detect committed transactions with zero effects|
|SW100-C0405|P2|runtime|01_KISH_ENGINE/babylon60/bft/defi_bytecode_scraper.py:44|TLOAD is decoded as 0x5e instead of 0x5c|
|SW100-C0406|P2|runtime|01_KISH_ENGINE/babylon60/bft/defi_bytecode_scraper.py:83|Hook permissions use the most significant address bits|
|SW100-C0407|P2|runtime|01_KISH_ENGINE/babylon60/engine/__init__.py:33|Updating an existing engine key creates stale eviction entries|
|SW100-C0408|P2|runtime|scripts/c5_cli/babylon_mail_cli.py:89|Mail send announces delivery after only appending a local ledger event|
|SW100-C0409|P2|example|tools/skill_library/codex_overrides/cloudflare/references/pages/patterns.md:27|Auth middleware can be skipped through the query string|
|SW100-C0410|P2|example|tools/skill_library/codex_overrides/cloudflare/references/pages/patterns.md:99|HTML error response interpolates exception text without escaping|
|SW100-C0411|P3|runtime|01_KISH_ENGINE/extensions/moskv-fx-scavenger/setup_native_host.sh:64|Native host dry-run changes executable permissions|
|SW100-C0412|P2|example|scripts/c5_edin/remotion_swarm_orchestrator.py:40|Chunk allocation ignores the supplied swarm size|
|SW100-C0413|P1|runtime|scripts/c5_git_utils/c5_distill_public_mirror.sh:91|Public projection continues when mandatory secret scanner is unavailable|
|SW100-C0414|P2|runtime|scripts/c5_git_utils/c5_distill_public_mirror.sh:104|Dry-run force-moves the existing release branch|
|SW100-C0415|P2|example|scripts/c5_cli/doxastic_kripke_engine.py:243|Second-order belief returns the target belief regardless of observer knowledge|
|SW100-C0416|P2|runtime|scripts/c5_skills_ontology/sync_skills_registry.py:493|Registry verification succeeds despite stale entries and metadata drift|
|SW100-C0417|P2|docs|tools/skill_library/global/c5-debloat-agent-kernel/scripts/langchain_autopsy.py:107|Benchmark prints a fixed end-to-end latency attribution it never measures|
|SW100-C0418|P1|runtime|scripts/c5_git_utils/c5_ship.sh:189|Push proceeds when neither biometric gate implementation is available|
|SW100-C0419|P2|runtime|01_KISH_ENGINE/babylon60/transducers/hygiene.py:27|Optimizer resolves repository root one directory too low|
|SW100-C0420|P1|runtime|tools/tamkarum_attestation_engine.py:167|Attestation verification accepts stale artifacts and an editable self-checksum|
|SW100-C0421|P2|runtime|tools/tamkarum_attestation_engine.py:190|Verification failures still return a successful CLI exit status|
|SW100-C0422|P1|runtime|01_KISH_ENGINE/services/email_inbound/worker.js:135|Inbound email acknowledges exhausted webhook delivery failures|
|SW100-C0423|P2|runtime|crates/cadt_mediator/src/lib.rs:57|Thermal budget addition can overflow before admission comparison|
|SW100-C0424|P2|runtime|tools/tamkarum_batch_signer.py:144|Draft filenames accept path components from campaign JSON|
|SW100-C0425|P2|example|examples/navier_stokes_larsa_oracle.rs:132|Missing Lean oracle is replaced by a numeric heuristic certification|
|SW100-C0426|P2|runtime|scripts/c5_git_utils/commit_polisher.py:65|Commit polisher invokes nonexistent rewrite script path|
|SW100-C0427|P2|runtime|scripts/c5_cli/markov_bridge.py:1555|Disconnected Markov output is not strict JSON|
|SW100-C0428|P1|runtime|01_KISH_ENGINE/babylon60/bft/ledger_actor.py:155|Shutdown stops consumer before draining its queue|
|SW100-C0429|P1|runtime|01_KISH_ENGINE/babylon60/bft/ledger_actor.py:496|Encrypted retries cannot satisfy ledger idempotency|
|SW100-C0430|P1|runtime|01_KISH_ENGINE/babylon60/bft/ledger_actor.py:505|Rollback is repeated after the transaction has already rolled back|
|SW100-C0431|P2|runtime|01_KISH_ENGINE/babylon60/bft/ledger_actor.py:278|Attestation combines separate database snapshots|
|SW100-C0432|P1|runtime|tools/tamkarum_license_provisioner.py:97|License authority falls back to a publicly derivable signing key|
|SW100-C0433|P2|example/docs|examples/omega_100_synthesis.rs:116|Example reports global regularity from hard-coded predicates|
|SW100-C0434|P1|runtime|01_KISH_ENGINE/babylon60/bft/master_ledger_queue.py:108|Shutdown stops before draining accepted transactions|
|SW100-C0435|P1|runtime|scripts/c5_cli/moskv_native_host.py:195|Shared /tmp prompt queue follows attacker-controlled symlinks|
|SW100-C0436|P2|runtime|scripts/c5_cli/moskv_native_host.py:187|Concurrent prompt producers and consumers lose FIFO updates|
|SW100-C0437|P1|runtime|scripts/c5_git_utils/rewrite_commits.py:30|History rewrite discards local work before establishing backup|
|SW100-C0438|P1|runtime|scripts/c5_thermo/c5_exergy_optimizer_monitor.py:202|State monitor commits unrelated staged changes|
|SW100-C0439|P2|runtime|01_KISH_ENGINE/babylon60/genomics/engine.py:77|TCW classifier omits required flanking nucleotide|
|SW100-C0440|P2|runtime|src/dec.rs:379|Energy and enstrophy truncate squared i64 values to u64|
|SW100-C0441|P2|runtime|src/dec.rs:802|Physical grid spacing absent from numerical RHS|
|SW100-C0442|P1|runtime|00_ABZU_KERNEL/crates/babylon60-runtime/src/main.rs:46|F60 reduction changes the represented value for partial base factors|
|SW100-C0443|P1|runtime|00_ABZU_KERNEL/crates/babylon60-runtime/src/main.rs:337|Division ignores the denominator scale|
|SW100-C0444|P2|runtime|00_ABZU_KERNEL/crates/babylon60-runtime/src/main.rs:190|Replay digest authenticates only elapsed ticks|
|SW100-C0445|P2|example|00_ABZU_KERNEL/crates/babylon60-runtime/src/main.rs:416|Unsupported instructions are silently accepted|
|SW100-C0446|P2|runtime|00_ABZU_KERNEL/crates/babylon60-runtime/src/main.rs:302|Script operands can panic the interpreter outside its halt path|
|SW100-C0447|P1|runtime|scripts/c5_thermo/cache_1000_memoization_bench.py:73|Unique query generator inevitably stops making progress|
|SW100-C0448|P1|runtime|scripts/c5_icloud_deploy.py:53|Mail migration deletes records belonging to unrelated subdomains|
|SW100-C0449|P2|runtime|02_EDIN_SWARMS/adapters/go_studio/cmd/server/main.go:90|Server binds all interfaces despite announcing loopback|
|SW100-C0450|P2|runtime|tools/tamkarum_top.py:51|Monitor presents constants as live security and treasury telemetry|
|SW100-C0451|P2|runtime|01_KISH_ENGINE/babylon60/genomics/hygiene.py:87|Sequence validator accepts an empty normalized sequence|
|SW100-C0452|P2|example|examples/poc_bifurcation_4_structs.rs:198|Byte-sized fields are emitted as eight-byte stores|
|SW100-C0453|P2|docs|tools/skill_library/global/c5-secops-infra-devtools/references/modules/youtube-analysis-pipeline/MODULE.md:202|Comment fallback directs audit output without acquiring comments|
|SW100-C0454|P2|runtime|01_KISH_ENGINE/babylon60/transducers/pulmones.py:117|Queue failure handler references an unbound exception|
|SW100-C0455|P2|runtime|01_KISH_ENGINE/babylon60/transducers/pulmones.py:152|Half-open circuit admits every concurrent caller|
|SW100-C0456|P2|runtime|scripts/c5_thermo/exergy_arbitrage_engine.py:82|Assimilation target can escape the incoming directory|
|SW100-C0457|P2|runtime|scripts/c5_thermo/exergy_arbitrage_engine.py:41|Code fence extractor matches a literal backslash instead of a newline|
|SW100-C0458|P2|example|examples/poc_bifurcation_5_lifetimes.rs:68|Reallocation clears live borrow state without invalidating references|
|SW100-C0459|P2|example|tools/ui_babylon_ide/index.html:843|Certificate panel presents static text as verified hardware attestation|
|SW100-C0460|P1|runtime|scripts/c5_cortex/autoconsolidate.py:48|Consolidation deletes journal rows without saving their replacement|
|SW100-C0461|P1|runtime|tools/skill_library/global/c5-secops-infra-devtools/references/modules/youtube-analysis-pipeline/scripts/yt_audit.py:17|YouTube URL and output directory are interpolated into shell commands|
|SW100-C0462|P2|runtime|01_KISH_ENGINE/babylon60/transducers/pulmones_worker.py:43|Persistent retry deadlines use a clock that resets at reboot|
|SW100-C0463|P2|runtime|01_KISH_ENGINE/babylon60/transducers/pulmones_worker.py:46|Fetching retry work does not claim rows atomically|
|SW100-C0464|P2|runtime|crates/eridu-infer/scripts/setup_appliance.sh:69|Appliance installer copies from a crate-local target directory in a workspace|
|SW100-C0465|P2|runtime|scripts/c5_isomorphisms/c5_logos_ethos_ship_engine.py:112|Master ledger explicitly selects NORMAL durability despite FULL requirement|
|SW100-C0466|P2|runtime|01_KISH_ENGINE/babylon60/c5_telemetry.py:57|Telemetry stop cancels the worker without draining pending events|
|SW100-C0467|P2|example|tests/test_attestation.py:24|Attestation test passes even for blocked or failed results|
|SW100-C0468|P2|runtime|00_ABZU_KERNEL/crates/nul-zk/src/compiler.rs:36|Generated temporary variables collide with circuit inputs|
|SW100-C0469|P2|runtime|01_KISH_ENGINE/babylon60/genomics/vsa_oncology.py:119|Drug-target affinity cancels the target vector|
|SW100-C0470|P2|runtime|tools/skill_library/global/c5-audiovisual-acreativo-sota/references/modules/c5-neural-face-swap-cuadrilla/scripts/c5_face_swap_cli.py:627|Parallel face-swap jobs share one identity embedding file|
|SW100-C0471|P2|runtime|tools/skill_library/global/c5-audiovisual-acreativo-sota/references/modules/c5-neural-face-swap-cuadrilla/scripts/c5_face_swap_cli.py:442|Worker suppresses encoder failure and can deliver truncated video|
|SW100-C0472|P2|runtime|01_KISH_ENGINE/babylon60/transducers/render_exergy_guard.py:427|Media gate ignores ffmpeg measurement failure|
|SW100-C0473|P2|runtime|scripts/c5_isomorphisms/c5_ultimate_causal_determinant.py:220|Persistent actor resets its Lamport clock on restart|
|SW100-C0474|P2|runtime|tools/skill_library/global/c5-audiovisual-acreativo-sota/references/modules/c5-neural-face-swap-cuadrilla/scripts/c5_smoother.py:220|New face tracks are returned twice on their first frame|
|SW100-C0475|P2|runtime|tools/skill_library/global/c5-audiovisual-acreativo-sota/references/modules/c5-neural-face-swap-cuadrilla/scripts/c5_smoother.py:284|Blur framing fails for sources taller than the output aspect ratio|
|SW100-C0476|P2|runtime|crates/eridu-infer/src/gate.rs:97|Gate receipts assert verified compliance without evaluating it|
|SW100-C0477|P2|runtime|crates/eridu-infer/src/gate.rs:67|Receipt hash does not distinguish model/prompt boundaries|
|SW100-C0478|P2|runtime|scripts/c5_cortex/consolidate_babylon_vault.py:164|Vault consolidation records a fixed session catalogue instead of reading source sessions|
|SW100-C0479|P2|runtime|scripts/c5_isomorphisms/cancer_isomorphism_pipeline.py:23|Cancer pipeline emits attested numerical invariants without inputs or computation|
|SW100-C0480|P2|runtime|tools/skill_library/global/github-architect/scripts/fetch_repos_graphql.py:100|Repository inventory falsely marks every repository as having a README|
|SW100-C0481|P1|runtime|crates/eridu-infer/src/gguf.rs:233|Array display truncation corrupts the GGUF parse cursor|
|SW100-C0482|P1|runtime|crates/eridu-infer/src/gguf.rs:176|Truncated GGUF metadata panics instead of returning an error|
|SW100-C0483|P1|runtime|scripts/c5_cortex/consolidate_dbs.py:70|Consolidation discards divergent same-name master ledgers|
|SW100-C0484|P1|runtime|scripts/c5_cortex/consolidate_dbs.py:32|Copying only SQLite main file loses WAL commits|
|SW100-C0485|P2|runtime|02_EDIN_SWARMS/agents_archi/clients/openrouter.py:292|Concurrent rate limiter callers reserve the same future slot|
|SW100-C0486|P1|runtime|02_EDIN_SWARMS/agents_archi/clients/openrouter.py:770|Sensitive routing omits the explicit target from its free-model veto|
|SW100-C0487|P2|runtime|01_KISH_ENGINE/babylon60/guards/c5_biometric_gate.swift:386|Receipt interpolation fails to escape JSON control characters|
|SW100-C0488|P2|runtime|scripts/c5_isomorphisms/gen_oncology_primitives.py:292|Generator computes scripts directory as its output root|
|SW100-C0489|P2|runtime|tools/skill_library/global/github-architect/scripts/git_history_sanitizer.py:78|History sanitizer certifies all history after sampling only 100 commits|
|SW100-C0490|P1|runtime|tools/install_shield.sh:170|Installer destroys pre-existing agent instruction files without preserving differences|
|SW100-C0491|P2|runtime|tools/install_shield.sh:44|A contender removes an active installer lock after approximately one second|
|SW100-C0492|P2|runtime|tools/install_shield.sh:67|Uninstall deletes unrelated symlinked instruction files|
|SW100-C0493|P1|runtime|crates/eridu-infer/src/hud.rs:520|Ledger model field reaches innerHTML without escaping|
|SW100-C0494|P2|runtime|crates/eridu-infer/src/hud.rs:496|HUD reports verified compliance from the existence of a response or receipt|
|SW100-C0495|P2|example|examples/poc_kudurru_silicon_ns.rs:382|Seqlock stress oracle accepts mixed finite snapshots and even zero successful reads|
|SW100-C0496|P2|docs|tools/skill_library/codex_overrides/cloudflare/references/queues/api.md:95|Queue acknowledgement guidance reverses the first-call-wins contract|
|SW100-C0497|P1|example|tools/skill_library/codex_overrides/cloudflare/references/waf/patterns.md:64|WAF score examples block clean traffic and spare the most suspicious requests|
|SW100-C0498|P2|example|scripts/c5_cortex/cortex_labs_poc.py:68|Advertised 90-second polling bound does not bound network reads|
|SW100-C0499|P1|runtime|scripts/c5_cortex/cortex_objectives_transducer.py:43|Failed commit is retried with hooks disabled|
|SW100-C0500|P1|runtime|scripts/c5_cortex/cortex_objectives_transducer.py:39|Objective commands stage unrelated work|
|SW100-C0501|P1|runtime|tools/skill_library/global/c5-socint-extraction-suite/scripts/socint_extract.py:703|Merkle evidence seal does not bind field names|
|SW100-C0502|P1|runtime|01_KISH_ENGINE/babylon60/transducers/void_vec.py:88|Native Hamming batch accepts buffers shorter than its stride|
|SW100-C0503|P2|runtime|02_EDIN_SWARMS/agents_archi/orchestrator/blackboard.py:316|Blackboard resolution is not an atomic OPEN transition|
|SW100-C0504|P2|runtime|01_KISH_ENGINE/babylon60/cli/bounty_cli.py:246|JSON output skips requested claim export|
|SW100-C0505|P2|example|tools/skill_library/global/github-architect/scripts/repo_health.py:179|Generated Python CI hides failed tests|
|SW100-C0506|P2|runtime|01_KISH_ENGINE/babylon60/cli/bounty_cli.py:121|Manifest inspector certifies properties it never checks|
|SW100-C0507|P2|runtime|src/f60.rs:36|Sexagesimal conversion silently truncates the high limb|
|SW100-C0508|P2|runtime|src/f60.rs:102|Saturating radius loses the claimed interval enclosure|
|SW100-C0509|P1|runtime|02_EDIN_SWARMS/agents_archi/orchestrator/kda_dag_swarm.py:208|DAG failure releases global lock while sibling tasks still execute|
|SW100-C0510|P2|example|scripts/c5_l1_ledger/bittensor_yuma_consensus_c5.py:164|Repeated consensus hash replaces a prior epoch|
|SW100-C0511|P2|example|tests/test_ledger_cross_equivalence.py:39|Durability regression inspects a fresh SQLite connection|
|SW100-C0512|P2|runtime|scripts/c5_utils/export_country_compliance.py:38|Explicit output basename fails before exporting|
|SW100-C0513|P2|example|examples/poc_lean4_emitter.rs:82|Lean example ignores sequence continuity when declaring causality preserved|
|SW100-C0514|P2|runtime|tools/skill_library/global/github-architect/scripts/repo_transductor.py:191|Repository remediation grants MIT rights without a license selection|
|SW100-C0515|P2|runtime|02_EDIN_SWARMS/agents_archi/orchestrator/lifecycle.py:207|WAL write failure is swallowed after state has changed|
|SW100-C0516|P2|example|examples/poc_navier_stokes_hunter.rs:230|Unresolved AWAIT spins forever outside the tick failsafe|
|SW100-C0517|P2|example|examples/poc_navier_stokes_hunter.rs:364|Vorticity check asserts a hardcoded result|
|SW100-C0518|P2|example|scripts/c5_cortex/poc_fl014_holdout.py:173|Seeded FL014 experiment uses process-randomized hash for decisions|
|SW100-C0519|P2|example|scripts/c5_cortex/poc_fl014_holdout.py:224|Artifact identity comparison checks only a prefix|
|SW100-C0520|P2|example|scripts/c5_utils/python_spsc_reader.py:16|Python SharedManifest example uses an incompatible ABI|
|SW100-C0521|P2|example|tools/skill_library/codex_overrides/cloudflare/references/queues/patterns.md:40|Queue HTTP examples acknowledge failed HTTP responses|
|SW100-C0522|P2|runtime|crates/eridu-infer/src/main.rs:218|Daemon installer reports success exit after launchctl rejection|
|SW100-C0523|P2|docs|tools/skill_library/global/github-architect/scripts/scitt_attestor.py:84|Release attestor emits unsupported certification claims|
|SW100-C0524|P1|runtime|02_EDIN_SWARMS/agents_archi/orchestrator/royal_rumble.py:311|Recovery proposals execute without Trust Gateway reevaluation|
|SW100-C0525|P1|runtime|02_EDIN_SWARMS/agents_archi/orchestrator/royal_rumble.py:255|Required structured review is only a quota counter|
|SW100-C0526|P1|runtime|crates/eridu-infer/src/server.rs:146|Completion endpoint returns canned legal output as model inference|
|SW100-C0527|P1|runtime|crates/eridu-infer/src/server.rs:53|WebSocket and completion routes never invoke the instantiated authentication validator|
|SW100-C0528|P1|runtime|scripts/c5_l1_ledger/ledger_snapshot_engine.py:24|Snapshot engine resolves its root above the repository|
|SW100-C0529|P2|runtime|scripts/c5_l1_ledger/ledger_snapshot_engine.py:45|Second-resolution filenames cause snapshot collisions|
|SW100-C0530|P2|example|examples/poc_scitt_hardware_receipt_stress.rs:231|Software-key example certifies hardware-bound attestation|
|SW100-C0531|P2|example|examples/poc_scitt_hardware_receipt_stress.rs:118|Receipt example accepts missing or malformed required fields|
|SW100-C0532|P2|example|scripts/c5_demos/BabylonTracePoC.lean:19|Trace validator ignores sequence continuity and incomplete writes|
|SW100-C0533|P1|runtime|scripts/c5_l1_ledger/seal_bounty_aeon.py:128|Identity decryption failure silently overwrites the master identity|
|SW100-C0534|P2|runtime|scripts/c5_l1_ledger/seal_bounty_aeon.py:119|Timestamp response existence is mislabeled as authenticated RFC3161 evidence|
|SW100-C0535|P2|runtime|02_EDIN_SWARMS/agents_archi/orchestrator/seqlock_swarm_ring0.py:101|Binary payload hash is truncated at the first NUL on read|
|SW100-C0536|P2|example|examples/poc_stress_dec_mimetic.rs:150|Two-node quorum failure branch is unreachable|
|SW100-C0537|P2|example|scripts/c5_verifiers/axiom_verifier_z3.py:361|Verifier records unconditional PASS for properties it does not inspect|
|SW100-C0538|P1|runtime|02_EDIN_SWARMS/agents_archi/orchestrator/swarm.py:305|Missing remote credentials produce successful fabricated task output|
|SW100-C0539|P1|runtime|tools/skill_library/global/c5-browser-forensics-and-extension-triage/scripts/browser_forensics.py:171|Extension purge accepts directory traversal as extension ID|
|SW100-C0540|P2|runtime|tools/skill_library/global/c5-browser-forensics-and-extension-triage/scripts/browser_forensics.py:143|Extension scan misses wildcard content-script injections|
|SW100-C0541|P2|runtime|01_KISH_ENGINE/babylon60/cli/onco_transducer.py:218|Falsifiability acceptance is disabled by optimized Python|
|SW100-C0542|P2|runtime|01_KISH_ENGINE/babylon60/cli/onco_transducer.py:126|Selecting therapy targets from a set makes pipeline nondeterministic|
|SW100-C0543|P2|runtime|01_KISH_ENGINE/babylon60/guards/saga_contract.py:30|Frozen saga proposals retain externally mutable payloads|
|SW100-C0544|P2|example|examples/poc_stress_manifest_spmc.rs:298|Stress example certifies latency bounds without checking them|
|SW100-C0545|P2|example|tools/skill_library/codex_overrides/cloudflare/references/cron-triggers/gotchas.md:110|Scheduled-operation deduplication commits success before operation|
|SW100-C0546|P2|docs|tools/skill_library/global/c5-audiovisual-acreativo-sota/references/modules/djstudio-mcp/MODULE.md:452|Sample-peak scaling is presented as a true-peak guarantee|
|SW100-C0547|P2|runtime|01_KISH_ENGINE/babylon60/guards/token_lease_guard.py:38|Reject negative token usage before cost accounting|
|SW100-C0548|P2|example|tools/skill_library/codex_overrides/cloudflare/references/cron-triggers/patterns.md:74|Retain failed batch items instead of removing the entire batch|
|SW100-C0549|P2|docs|scripts/c5_log_custody/c5_organize_captures.py:157|Do not issue a complete forensic attestation when captures are absent|
|SW100-C0550|P2|runtime|src/fluid_thermo.rs:42|Avoid integer overflow before converting mesh volume to floating point|
|SW100-C0551|P2|runtime|tools/skill_library/global/c5-epistemic-thermodynamics/references/modules/c5-terminological-archaeology/scripts/c5_lexicon_notary.py:197|Dry-run still overwrites the session artifact log|
|SW100-C0552|P2|runtime|tools/skill_library/global/c5-epistemic-thermodynamics/references/modules/c5-terminological-archaeology/scripts/c5_lexicon_notary.py:158|Phase replacement removes every section after Fase 2f|
|SW100-C0553|P2|runtime|tools/skill_library/global/c5-audiovisual-acreativo-sota/references/modules/f5tts-voice-cloning-sota/scripts/synthesize_vocal_clone.py:108|Concurrent synthesis invocations share one intermediate WAV|
|SW100-C0554|P2|example|00_ABZU_KERNEL/crates/strike-rs/scripts/poc_python_zerocopy_worker.py:57|Timeout is reported as a successful zero-copy falsification|
|SW100-C0555|P2|example|tools/skill_library/global/c5-sovereign-identity-hardening/scripts/check_pwned_pass.sh:15|Password audit requires plaintext password in process arguments|
|SW100-C0556|P1|runtime|scripts/c5_verifiers/fast_smt_gate.py:27|SMT gate reports literal assertions as verified invariants|
|SW100-C0557|P1|runtime|scripts/c5_verifiers/fast_smt_gate.py:137|SCITT receipt fabricates a signature and does not bind the verification results|
|SW100-C0558|P2|example|examples/poc_zero_touch_gate.rs:228|Admitted result ignores publication failure after poison|
|SW100-C0559|P2|example|crates/mxc_broker_poc/src/main.rs:69|Verified commit is independent of the causally bound descriptor|
|SW100-C0560|P2|runtime|00_ABZU_KERNEL/crates/strike-rs/src/atms.rs:171|New ATMS premises bypass an already established unconditional contradiction|
|SW100-C0561|P2|example|scripts/c5_demos/batch_gen_borja_voices.py:80|Voice generation reports full synchronization after synthesis errors|
|SW100-C0562|P1|runtime|tools/skill_library/global/c5-cortex-swarm-orchestrator/references/modules/anergy-purge-protocol/scripts/anergy_purge.py:183|Purge unlinks live SQLite WAL and shared-memory files|
|SW100-C0563|P1|runtime|tools/skill_library/global/c5-cortex-swarm-orchestrator/references/modules/anergy-purge-protocol/scripts/anergy_purge.py:193|Workspace purge resets unrelated live global sessions|
|SW100-C0564|P1|runtime|.github/actions/archi-guard/action.yml:38|Composite action inputs are interpolated into Bash source|
|SW100-C0565|P1|runtime|deploy/Dockerfile:7|Container build pins compiler older than workspace manifests|
|SW100-C0566|P2|example|examples/swarm_1000_gate1_adversarial.rs:161|Replay campaign never establishes a successfully consumed authorization|
|SW100-C0567|P2|example|examples/swarm_1000_gate1_adversarial.rs:365|Crash report declares five tested points without interruption or recovery|
|SW100-C0568|P2|example|examples/swarm_1000_gate1_adversarial.rs:280|NEMESIS report passes when all secure-delete operations fail|
|SW100-C0569|P2|docs|scripts/c5_verifiers/inject_lean4_stubs.py:80|Stub exporter labels tautologies as verification of extracted claims|
|SW100-C0570|P2|example|scripts/c5_demos/benchmark_governance_10k.py:235|Benchmark conclusions attribute simulator assumptions to external products|
|SW100-C0571|P2|docs|tools/skill_library/global/c5-epistemic-thermodynamics/references/modules/categorical-hallucination-audit/MODULE.md:54|Refusal is assigned zero KL without a probability distribution|
|SW100-C0572|P1|runtime|00_ABZU_KERNEL/crates/strike-rs/src/bft_engine.rs:307|Closed completion channel causes an infinite busy loop after consensus timeout|
|SW100-C0573|P1|runtime|00_ABZU_KERNEL/crates/strike-rs/src/bft_engine.rs:408|Database errors leave committed in-memory DAG changes despite rollback error|
|SW100-C0574|P1|runtime|scripts/c5_verifiers/purge_residuals.py:58|Residual purge deletes active Git lock files without checking ownership|
|SW100-C0575|P2|runtime|scripts/c5_verifiers/purge_residuals.py:69|Residual purge treats every scratch database and WAL as disposable|
|SW100-C0576|P2|example|tools/skill_library/global/c5-cortex-swarm-orchestrator/references/modules/c5-adaptive-annealing-engine/MODULE.md:120|Canonical annealing example replaces random acceptance with a fixed cutoff|
|SW100-C0577|P2|runtime|00_ABZU_KERNEL/crates/strike-rs/src/bft_iceoryx2.rs:121|Bound IPC envelope length before slicing|
|SW100-C0578|P2|runtime|02_EDIN_SWARMS/agents_archi/topologies/autodidact_topology.py:117|Reset research state between independent cycles|
|SW100-C0579|P1|example|tools/skill_library/codex_overrides/cloudflare/references/d1/patterns.md:87|Authenticate tenant selection in the multi-tenant example|
|SW100-C0580|P2|example|tools/skill_library/codex_overrides/cloudflare/references/d1/patterns.md:103|Normalize session expiry before comparing SQLite timestamps|
|SW100-C0581|P1|docs|tools/skill_library/global/c5-epistemic-thermodynamics/references/modules/cct-cognitive-theory-advisor/MODULE.md:68|Remove credential scavenging and autonomous secret injection directive|
|SW100-C0582|P2|runtime|00_ABZU_KERNEL/crates/strike-rs/src/bin/bft_interceptor.rs:237|SIGTERM seals the ledger without terminating the intercepted child|
|SW100-C0583|P2|runtime|00_ABZU_KERNEL/crates/strike-rs/src/bin/bft_interceptor.rs:248|Persistence failures are discarded while closure is reported successful|
|SW100-C0584|P2|runtime|02_EDIN_SWARMS/agents_archi/topologies/babylon21_consolidation.py:561|Specification-only consolidation emits verified and consolidated results|
|SW100-C0585|P2|runtime|02_EDIN_SWARMS/agents_archi/topologies/babylon21_consolidation.py:652|Timed-out consolidation gate subprocesses are left running|
|SW100-C0586|P2|runtime|02_EDIN_SWARMS/agents_archi/topologies/babylon21_consolidation.py:38|Canonical seal digest changes with optional dependency installation|
|SW100-C0587|P2|runtime|01_KISH_ENGINE/babylon60/kernel/bft_db_async.py:16|BFT persistence explicitly weakens required durability|
|SW100-C0588|P2|runtime|scripts/c5_orchestrator/c5_session_deskimming_engine.py:102|Deskimming dry-run writes and replaces its audit receipt|
|SW100-C0589|P2|runtime|scripts/c5_verifiers/verify_anergy_token_purge.py:185|Autocognition audit asserts checks it never performs|
|SW100-C0590|P2|runtime|scripts/c5_verifiers/verify_anergy_token_purge.py:28|Explicit conversation selection is ignored in favor of another session|
|SW100-C0591|P2|runtime|00_ABZU_KERNEL/crates/strike-rs/src/bin/c5_cli.rs:88|Anomaly filter skips the configured event limit|
|SW100-C0592|P2|example|scripts/c5_demos/c5_darknode_core.py:44|Sexagesimal conversion scales integer units by sixty|
|SW100-C0593|P2|example|tools/skill_library/global/remotion-audio-reactive-video/examples/AudioReactiveMaster.tsx:36|Mutable ballistic history makes a frame depend on render order|
|SW100-C0594|P2|docs|tools/skill_library/global/c5-epistemic-thermodynamics/references/modules/discourse-popperian-falsification/MODULE.md:56|Forensic protocol treats a wish to remember as mathematical proof of lying|
|SW100-C0595|P2|runtime|02_EDIN_SWARMS/agents_archi/topologies/edin.py:45|Synchronous verifiers bypass timeout and block the event loop|
|SW100-C0596|P2|runtime|01_KISH_ENGINE/babylon60/kernel/bft_sqlite.py:68|Returned SQLite cursor is attached to an already closed connection|
|SW100-C0597|P2|runtime|scripts/c5_verifiers/verify_causal_invariants.py:29|Causal verifier still targets removed packages directory|
|SW100-C0598|P2|example|scripts/c5_demos/c5_killer_demo_60s.py:100|Demo presents simulated authentication and print-only fail-stop as actual guarantees|
