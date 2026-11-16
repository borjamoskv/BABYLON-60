"""Materialize reviewer 14's source-inspected adjudications and validate their schema."""

import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).absolute().parents[4]
BASE = Path(__file__).absolute().parent
ASSIGNED = json.loads((BASE / "assignments/14.json").read_text())
BY_ID = {c["candidate_id"]: c for c in ASSIGNED}
ROWS = []
EVIDENCE = "docs/security/evidence/swarm100-round3-20261028/14-review-evidence.json"
PURE = "docs/security/evidence/swarm100-round3-20261028/14-pure-fixtures.json"


def add(number, rationale, checks, guards, decision="CONFIRMED_STATIC"):
    cid = f"SW100-C{number:04d}"
    item = BY_ID[cid]
    live_digest = hashlib.sha256((ROOT / item["path"]).read_bytes()).hexdigest()
    # C0242 was inspected before the coordinator's separately tracked remediation.
    # Preserve the observed historical vulnerable source, never relabel it fixed by hash drift.
    if number != 242:
        assert live_digest == item["source_sha256"], (cid, "source changed after inspection")
    digest = item["source_sha256"] if number == 242 else live_digest
    fixtures_executed = decision == "REPRODUCED"
    ROWS.append({
        "candidate_id": cid,
        "decision": decision,
        "severity": item["severity"],
        "remediation_state": "OPEN",
        "path": item["path"],
        "current_source_sha256": digest,
        "rationale": rationale,
        "source_checks": [
            {"path": path or item["path"], "start_line": start, "end_line": end, "observation": observation}
            for path, start, end, observation in checks
        ],
        "guards": guards,
        "runtime_executed": fixtures_executed,
        "evidence_paths": [EVIDENCE] + ([PURE, "docs/security/evidence/swarm100-round3-20261028/14-pure-fixtures.py"] if fixtures_executed else []),
    })


add(349,
    "append_event derives index and previous hash from an unlocked read and later opens a separate append handle. Two processes can both observe head N and acknowledge index N+1; verify_chain then rejects the duplicate index. CLI and authorized HTTP branches reach this function directly. This is a source-supported concurrency defect; no writer race was executed.",
    [(None, 120, 168, "No lock or transaction spans get_chain_blocks, head derivation and writeln."), (None, 185, 196, "verify_chain rejects index discontinuity and predecessor mismatch."), ("crates/babylon-attest/src/main.rs", 227, 247, "CLI appends and acknowledges success."), ("crates/babylon-attest/src/main.rs", 465, 477, "Authorized HTTP input reaches the same appender.")],
    ["Append mode prevents overwriting old bytes but does not serialize read-modify-append.", "verify_chain detects the resulting corruption after the acknowledgment; it does not prevent it."])
add(350,
    "append_event returns Ok immediately after writeln without sync_data/sync_all. The CLI reports ATTESTATION COMMITTED on that result. Crash durability of the acknowledged line is therefore not established; a host/storage failure can lose buffered data or leave a partial JSON line, which get_chain_blocks rejects. No crash or storage fault was induced.",
    [(None, 158, 168, "Successful write is the last operation before Ok; no durability barrier."), (None, 103, 114, "Line parse error aborts reading the ledger."), ("crates/babylon-attest/src/main.rs", 227, 235, "COMMITTED output relies on append_event success.")],
    ["Write errors propagate, but successful write only establishes transfer to the OS/file layer.", "No caller-side sync is present in the inspected CLI branch."])
add(351,
    "New blocks use compute_blake3_256(commitment), while export_scitt_voucher declares leaf_hash_algorithm SHA-256 and copies that block_hash. A consumer using the declaration cannot reproduce the new leaf commitment. Legacy SHA-256 acceptance by verify_chain does not identify the algorithm of newly exported blocks. This review makes no claim about full SCITT compliance or a live external consumer.",
    [(None, 136, 145, "Payload and block commitments use BLAKE3."), (None, 268, 278, "Voucher copies block_hash but labels it SHA-256."), ("crates/babylon-attest/src/main.rs", 240, 242, "SCITT CLI format invokes the exporter.")],
    ["Verifier accepts both BLAKE3 and legacy SHA-256 at lines 199-225; exporter has no corresponding algorithm selection."])
add(582,
    "On Unix, the signal handler only sets shutdown_flag. If SIGTERM/SIGINT is directed to the wrapper while its child remains alive, the polling loop exits, writes the closure seal and returns without kill/wait. Rust Child drop does not terminate a running process. A process-group signal may also reach the child, so persistence of the child is conditional on signal delivery/child behavior; the wrapper itself supplies no termination guarantee. No process was spawned or signaled.",
    [(None, 175, 184, "Signal thread only sets an atomic flag."), (None, 223, 253, "Spawned Child is polled until shutdown; closure follows with no kill/wait.")],
    ["Normal child exit is observed with try_wait.", "A signal delivered to both processes may independently terminate the child; direct wrapper shutdown is not covered.", "Official std::process::Child documentation confirms dropping the handle does not ensure child exit."])
add(583,
    "The ledger insert method correctly rejects a changed stored head and propagates SQL/commit errors, but the FS_EVENT call and closure-seal call discard those Results. After a failed seal insertion the wrapper still prints CIERRE CAUSAL EJECUTADO and returns Ok. The confirmed defect is loss of error reporting/closure evidence, not a claim that the underlying transaction silently succeeds.",
    [(None, 110, 134, "Immediate transaction, head comparison and commit can return errors."), (None, 204, 212, "FS_EVENT insert Result is discarded."), (None, 245, 253, "CLOSURE_SEAL failure is discarded before unconditional success output.")],
    ["The ledger transaction checks concurrent head changes and updates in-memory head only after commit.", "Mutex serializes local users, but neither SQL failure nor a different process's head change is reported by these callers."])
add(150,
    "_next_lamport_t performs MAX+1 before a separate INSERT on an autocommit connection. The attestation schema has no unique lamport_t constraint. Two connections can read the same maximum and persist distinct attestation IDs at the same tick. This confirms failure of this allocator's intended per-ledger increasing sequence, not a general claim that all distributed Lamport clocks require globally unique values; no downstream ordering consumer was established.",
    [(None, 12, 21, "Only attestation_id is unique; lamport_t is NOT NULL only."), (None, 39, 60, "MAX+1 and INSERT are distinct operations without transaction."), ("01_KISH_ENGINE/babylon60/core/url_cache.py", 41, 46, "URLCacheSync obtains connect_sync connection."), ("01_KISH_ENGINE/babylon60/database/core.py", 65, 79, "isolation_level=None and WAL/busy timeout do not span the two statements.")],
    ["Unique attestation_id does not constrain lamport_t; its input includes wall-clock time.", "SQLite serializes individual writes, not the preceding unlocked MAX read."])
add(151,
    "fetch_and_verify commits cache.put before recording attestation on the same autocommit connection. A failure between them leaves cached content without the matching audit record. Later cache hits return passed=True without querying the attestation table or repairing the gap. Causal-taint and payload filters precede this path but do not make the two writes atomic. No database was opened or modified in this review.",
    [(None, 85, 95, "Cache hit trusts stored payload and returns without attestation lookup."), (None, 108, 125, "Accepted payload is cached before _record_attestation."), ("01_KISH_ENGINE/babylon60/core/url_cache.py", 63, 76, "put executes a standalone INSERT OR REPLACE."), ("01_KISH_ENGINE/babylon60/database/core.py", 65, 79, "Connection is in autocommit mode.")],
    ["Nonempty causal_taint and evaluate_payload guard ingress.", "Neither cache nor attestation operation opens a transaction covering both writes."])
add(304,
    "The public verifier never reads proof.leaf_index. Altering only that field of an otherwise valid proof cannot affect its boolean result, so the serialized positional claim is not authenticated. It still verifies the supplied membership path against expected_root; this is not proof of arbitrary non-member acceptance. Targeted search found only the local positive test and public re-export, not an external production verifier consumer.",
    [(None, 17, 25, "Proof exposes leaf_index, total_leaves and peak_index."), (None, 134, 173, "Generator computes position and embeds leaf_index."), (None, 176, 213, "Verifier depends on path, peak_index and total_leaves, never leaf_index."), ("crates/b60-lang/src/lib.rs", 26, 26, "MMR accumulator and proof are publicly re-exported.")],
    ["generate_proof bounds-checks target_index, but callers can construct or modify public proof fields.", "Comparison with externally supplied expected_root remains active."])
add(305,
    "verify_proof slices other_peaks at the supplied public peak_index without validating the index. Values greater than other_peaks.len() panic before the expected-root comparison instead of returning false. Generator-produced proofs are in range, so exploitation requires a malformed/manual proof; remote exposure was not established and no Rust runtime was executed.",
    [(None, 17, 25, "All proof fields are public."), (None, 176, 200, "Unconditional slices at peak_index have no preceding bound check."), (None, 202, 212, "Boolean root rejection occurs only after the potentially panicking slices.")],
    ["Generator validates its own target index; that guard does not constrain a constructed public proof."])
add(385,
    "The E2E script explicitly passes repository data/cortex_memory.db to ingestion and inserts three synthetic successful traces. It then updates every cortex_invariant_clusters row to ACCUMULATING/UNTESTED without WHERE and feeds that database to extraction/proof/code generation. The ingestor commits these records and increments existing sample counts. Running this demonstration can contaminate persistent evidence and reset existing cluster status; the script was not run and operator databases were not read.",
    [(None, 29, 38, "DB_PATH points to repository data/cortex_memory.db."), (None, 61, 98, "Synthetic traces enter that DB; unqualified UPDATE resets all clusters; downstream extractor consumes it."), ("scripts/c5_destiladora/goal_trace_ingestor.py", 20, 21, "Default operational DB is the same path."), ("scripts/c5_destiladora/goal_trace_ingestor.py", 70, 114, "Writes are committed and cluster sample_count is incremented.")],
    ["Main-entrypoint guard prevents import-only execution, but run_end_to_end_test has no temporary DB/isolation guard.", "Later cargo/test failures occur after the database writes."])
add(386,
    "The final report labels a literal 0.18 ms as measured and prints literal 27,444x acceleration. The only captured elapsed interval is cargo check, and the subsequent test subprocess is not timed. Earlier return-code checks determine whether the report is printed, not whether its latency claims were measured. Confirmed as misleading demonstration evidence; no benchmark was performed.",
    [(None, 114, 126, "Only cargo check duration is measured with perf_counter."), (None, 129, 162, "Fast-path test is untimed; final latency and speedup are literal strings.")],
    ["Cargo check and test return codes are checked; those checks do not validate latency or speedup."])
add(15,
    "The Deploy with Bindings multipart metadata includes a // comment inside a single-quoted JSON form field, so the shell passes the comment rather than stripping it. An isolated fixture extracted exactly this section, replaced only the KV shell substitution, and json.loads rejected it at line 7 column 41. No curl, network request or deployment ran. An initial fixture selector chose the earlier metadata example; it was corrected to anchor on this section before the passing reproduction.",
    [(None, 59, 70, "The literal comment appears within metadata JSON, not outside the shell field.")],
    ["The abbreviated URL and KV placeholder must be filled by the reader, but neither substitution removes the JSON comment."], "REPRODUCED")
add(16,
    "The single TypeScript block both imports the DispatchNamespace type and declares a local interface with that same type name; it is not module augmentation. When the intended external type resolves, the declarations conflict in the type namespace. Official TypeScript 3.7 documentation explicitly identifies imported/local interface declarations as an error. No package version is pinned in this reference and no compiler was run, so this is a static example defect rather than a measured installed-project diagnostic.",
    [(None, 33, 57, "Import type and interface DispatchNamespace share one code block and module scope.")],
    ["Value-only imported bindings can coexist with an interface; this example explicitly imports the DispatchNamespace type.", "No declare module augmentation, alias or separate alternative block avoids the conflict."])
add(195,
    "ask treats a nonzero subprocess exit as failure only when no agent-message text was parsed. Any partial agent message therefore causes a success=True result, omitting the return code and error. _parse_codex_events retains raw failed events only for a count and does not turn them into failure status. Timeout/launch failures remain guarded. No Codex binary, session store or user prompt was executed/read; external CLI event compatibility was not required to establish the nonzero-exit branch defect.",
    [(None, 27, 58, "Parser collects agent messages and completed usage but no failure status."), (None, 134, 175, "Nonzero returncode plus nonempty full_text falls into success=True."), ("01_KISH_ENGINE/babylon60/adapters/codex/__init__.py", 9, 11, "CodexDriver is exported from the adapter package.")],
    ["Missing binary, timeout and subprocess exceptions return failure.", "queue_prompt separately checks its return code, but does not guard ask."])
add(298,
    "PROJECT_ROOT is the cortex package directory, not the repository root. The __main__ path calls categorize_and_move, which moves each unprotected .py to a nested archive. __init__.py and the present gemini_labs_nexus.py are unprotected; moving such implementation modules breaks their original import paths. Correction to candidate evidence: cortex_chaos_monad.py IS protected at line 68 and is not an affected example. No purge ran.",
    [(None, 23, 28, "Root and archive are derived from the package's own __file__ directory."), (None, 30, 69, "Protected set includes cortex_chaos_monad.py but not __init__.py or gemini_labs_nexus.py."), (None, 77, 114, "All other .py files are moved by main."), (None, 178, 179, "Direct execution calls main, not safe_purge_anergy.")],
    ["Directories and explicit protected filenames are skipped.", "safe_purge_anergy has independent path/subprocess checks but is not called by this entrypoint."])
add(199,
    "highest_score starts at 0.5 and can only increase, whereas tip_of_tongue requires it to be below 0.35. Nonempty matches also require a score above 0.5. The branch is mathematically unreachable; the empty-candidate branch explicitly returns false too. Extracted pure method fixtures returned false for matching, nonmatching, short-token and empty inputs. No ledger code was imported; no downstream authorization impact is claimed.",
    [(None, 97, 124, "Score floor, monotone maximum, match threshold and impossible final predicate are in one method.")],
    ["No score recalibration occurs between initialization and predicate.", "Other metamemory judgments may set their own tip_of_tongue; finding is restricted to judge_procedural_fok."], "REPRODUCED")
add(336,
    "The advertised c5.auditLedger CodeAction reaches an execute_command branch returning literal HEALTHY/compliance Verified JSON. No path, ledger read, chain validation or external verifier is used in that branch. main.rs exposes this result through workspace/executeCommand as a successful JSON-RPC response. Missing/corrupt ledgers cannot influence this result; no LSP/runtime was launched and no broader regulatory conclusion is drawn.",
    [(None, 28, 36, "Ledger integrity audit is exposed as a CodeAction."), (None, 103, 110, "Audit branch constructs constant healthy/compliant result."), ("01_KISH_ENGINE/cortex/crates/cortex-lsp/src/main.rs", 142, 166, "ExecuteCommand forwards ActionEngine success directly to JSON-RPC result.")],
    ["Unknown commands error, but the recognized audit command has no evidence guard.", "Biometric checks belong to the separate signoff branch, not ledger auditing."])
add(464,
    "From crates/eridu-infer/scripts, the script assigns REPO_DIR to crates/eridu-infer and then copies REPO_DIR/target/release/eridu-infer. This crate is a member of the root workspace; Cargo's documented default is the shared root target directory. No checked-in ancestor target-dir override was found. With no matching environment/global override or prebuilt crate-local binary, a successful build still leaves cp looking in the wrong directory, after earlier power/network mutations. No installer/build ran.",
    [(None, 36, 69, "System settings change before build; derived crate-local path is used for cp."), ("Cargo.toml", 1, 11, "Root workspace includes crates/*."), ("crates/eridu-infer/Cargo.toml", 1, 16, "Crate inherits workspace version and declares the eridu-infer binary."), (".cargo/config.toml", 1, 8, "Checked-in root config contains no target-dir override.")],
    ["set -e aborts on cp failure, but does not restore prior settings.", "Architecture/admin checks and prebuilt-binary branch exist.", "Global/environment Cargo overrides were deliberately not inspected; finding is conditional on default target behavior."])
add(458,
    "In this example checker, Alloc unconditionally replaces any owner state with Unborrowed without checking or clearing reference_map. After Alloc R0; BorrowMut R1<-R0; Alloc R0; Free R0, Free sees Unborrowed and returns Ok while reference_map retains R1->R0. This invalidates the example's modeled borrow invariant; it is not evidence of a Rust memory-safety exploit in production. No native example ran.",
    [(None, 65, 70, "Alloc overwrites borrow state."), (None, 92, 105, "BorrowMut stores owner state and reverse reference."), (None, 149, 159, "Free only checks current owner state, then removes it.")],
    ["Free rejects a live borrow only if the states entry still records it.", "EndBorrow clears reference_map when explicitly called, but reallocation does not call it."])
add(592,
    "from_rational multiplies the rational by 60 before decomposing fields whose documented weights are 3600, 60 and 1. Extracting only the pure Sexagesimal60 class reproduced 1/1 -> u=1 -> scalar 60 and 59/60 -> gin=59 -> scalar 59. The constructor later uses this scalar in the demo structure. No hardware/biometric imports, native code or receipt issuance ran.",
    [(None, 29, 56, "Declared units, scaled conversion and scalar reconstruction disagree."), (None, 81, 85, "Kudurru64 stores sexa.to_scalar as its scalar field.")],
    ["Frozen dataclass prevents mutation after construction, not arithmetic mis-scaling."], "REPRODUCED")
add(286,
    "The script displays measured bundling results but unconditionally follows them with fixed >15 dB/100% recall K<=50 and >98% K=300 assertions, then prints 100% PASS for bundling. None of bundling_results is used in a verdict predicate. Orthogonality and associative-memory assertions can fail separately; they do not validate bundling. This is a demonstration-reporting defect, not a claim that a particular measured run violated those thresholds.",
    [(None, 214, 226, "Bundling results are printed, then fixed claims are emitted."), (None, 241, 252, "Assertions check associative recall only; bundling verdict stays literal PASS.")],
    ["Orthogonality and noise-recall assertions can stop the script.", "No bundling threshold assertion or conditional verdict exists."])
add(488,
    "At the checked-in scripts/c5_isomorphisms location, dirname(dirname(__file__)) resolves to scripts. The generator then appends cortex, babylon60 and docs, yielding scripts/cortex, scripts/babylon60 and scripts/docs. The importable oncology module exists under 01_KISH_ENGINE/babylon60. The path computation and writes are therefore directed away from the canonical engine/doc roots. No generator ran and no files were generated outside review evidence.",
    [(None, 291, 304, "Wrong parent depth is used for all three output paths and directories are created automatically."), (None, 313, 314, "Direct execution invokes this main.")],
    ["Record count and unique-ID assertions validate content, not output location.", "write_if_changed cannot correct the supplied destination path."])
add(256,
    "The script's own directory is scripts/c5_setup; one parent gives scripts, so WorkspaceAgents becomes scripts/.agents rather than the repository .agents. A missing source is silently skipped by Test-Path, while the script can still reach its final environment-prepared success text. This confirms a path/conditional-report defect for normal placement; no PowerShell or profile configuration ran.",
    [(None, 21, 30, "RepoRoot is one parent of ScriptDir; copying is conditional on the resulting wrong source."), (None, 53, 60, "Final success text is not conditional on governance copy completion.")],
    ["Test-Path prevents copying a nonexistent path but suppresses the intended step rather than reporting failure.", "ErrorActionPreference Stop does not turn a false Test-Path into an error."])
add(537,
    "verify_four_renunciations takes no runtime inputs and records four literal True values. The split-epi branch similarly records True from a caller boolean without a function/section or identity check. record stores these as passed, and print_report counts them toward SYSTEM SOUND. Other methods do perform checks and can fail, so the finding is limited to these unsupported success rows, not every verifier result. No verifier/runtime was executed.",
    [(None, 54, 61, "record stores caller-supplied pass flags unchanged."), (None, 326, 367, "Support inclusion is checked, but split epi and four renunciations are asserted True."), (None, 416, 436, "All stored True rows contribute to PASS count and soundness verdict.")],
    ["Bayesian support differences are actually checked and can fail.", "Other verification failures can make the aggregate report fail; that does not validate these unconditional rows."])
add(339,
    "With --bundle, an existing file is hashed but compared only when manifest.release_bundle is truthy. Missing/null/empty metadata bypasses the binding and can reach VERIFIED if the independent evidence/signature checks pass. The ordinary CI producer calls compile_claims_manifest --bundle and supplies a digest, mitigating that normal flow; it does not make the standalone verifier reject a metadata-less manifest. No release or CI run was executed.",
    [(None, 186, 200, "Digest comparison is conditional on optional bundle_meta."), (None, 259, 268, "VERIFIED follows; OIDC verification is optional and separate."), (".github/workflows/ci.yml", 139, 146, "Normal CI generates the manifest with the same --bundle before verification."), ("scripts/c5_quality_gates/compile_claims_manifest.py", 179, 186, "Producer computes bundle metadata when a supplied path exists.")],
    ["Claims digest, evidence leaves/root, optional SBOM and signature checks remain active.", "Normal CI binds the bundle via producer output, but standalone caller can present valid evidence without release_bundle.", "Optional --verify-oidc can add another check; it is not required by --bundle."])
add(51,
    "The handler first consumes request.text for signature checking, then reads the same Request body again before queueing. For a nonempty valid signed webhook, the second read rejects because the body is disturbed. There is no cloned Request or saved body variable. Official Request.text documentation confirms this rejection; the defect is confined to the example and no webhook/network request ran.",
    [(None, 25, 35, "Both awaits consume the same request body; queue and 202 occur after the second read.")],
    ["Invalid signatures return 401 early; valid signed bodies reach the failing second read.", "No clone/cache or catch handles the consumed body."])
add(307,
    "persist-skill.sh enables nounset and pipefail but not errexit. Its Python mkdir/copytree/chmod block is an unchecked simple command. If copying fails, the next Python command still emits status=ok and can succeed even for a missing/partial bundle, determining a successful script exit. Clone, sparse-checkout and input errors are guarded separately. No clone, copy or target mutation was run.",
    [(None, 4, 5, "errexit is absent."), (None, 79, 99, "Copy/chmod Python command has no status conditional."), (None, 101, 114, "Independent JSON emitter reports ok without verifying a complete bundle.")],
    ["Project confinement, empty target, prerequisites, clone and sparse-checkout failures are checked.", "Those checks do not catch a subsequent permissions/disk/concurrency failure during copy."])
add(242,
    "Inspected nested copy hash 57ce214b... only strips --id and rejects empty input. argparse passes the arbitrary string to os.path.join and then rmtree; an absolute ID discards the profile prefix and traversal can escape Extensions. This is a dangerous locally invoked deletion boundary, conditional on at least one recognized profile and accessible destination, not remote exploitation. The separately fixed primary skill copy did not change this inspected nested implementation. Coordinator remediation after inspection is tracked separately; this record preserves the vulnerable observed hash. No profile or deletion was accessed/executed.",
    [(None, 28, 36, "Loop requires a recognized existing profile."), (None, 157, 181, "Only whitespace/nonempty validation precedes path joins and recursive deletion."), (None, 247, 271, "CLI --id has no format validation and reaches cmd_purge.")],
    ["Nonempty input and existence checks do not enforce extension-ID syntax or containment.", "Primary skill correction is a different physical file; coordinator may attach a later verified override for this copy."])
add(593,
    "useMemo retains one mutable ballisticState for the component lifetime. Each render passes it to extractBands, which compares against and overwrites prevSpectrum and applies smoothing from prior smoothedValues. Consequently the same current spectrum/frame after a different render history changes onset and smoothing, which affect scale/shake/glow. Official Remotion guidance requires output independent of frame execution order. This confirms the example's history dependence; no media rendered or browser launched.",
    [(None, 28, 56, "Frame-dependent spectrum is combined with persistent useMemo state."), (None, 63, 76, "State-dependent outputs influence visible camera and glow."), ("tools/skill_library/global/remotion-audio-reactive-video/examples/SpectralFlux.ts", 41, 61, "Ballistics reads and overwrites smoothedValues."), ("tools/skill_library/global/remotion-audio-reactive-video/examples/SpectralFlux.ts", 85, 114, "Flux reads previous spectrum and replaces it before returning bands.")],
    ["Empty spectrum has an early return, but nonempty spectra mutate persistent history.", "No frame-indexed replay or precomputed deterministic envelope resets the state for seeks/workers."])

assert len(ROWS) == len(ASSIGNED) == 29
assert {r["candidate_id"] for r in ROWS} == set(BY_ID)
assert len({r["candidate_id"] for r in ROWS}) == 29
for row in ROWS:
    assert row["decision"] in {"CONFIRMED_STATIC", "REPRODUCED", "REJECTED", "DUPLICATE", "ALREADY_FIXED", "NEEDS_VALIDATION"}
    assert row["remediation_state"] in {"OPEN", "FIXED", "MITIGATED", "NOT_APPLICABLE", "UNKNOWN"}
    assert len(row["current_source_sha256"]) == 64
    for check in row["source_checks"]:
        assert (ROOT / check["path"]).is_file()
        assert 1 <= check["start_line"] <= check["end_line"]
        # Historical C0242 ranges may shift under the coordinator's separate edit.
        if row["candidate_id"] != "SW100-C0242":
            assert check["end_line"] <= len((ROOT / check["path"]).read_text().splitlines()), (row["candidate_id"], check["path"], check["end_line"])

evidence = {
    "reviewer": "14",
    "date_utc": datetime.now(timezone.utc).isoformat(),
    "repository": str(ROOT),
    "method": "Independent bounded source reads with line numbers and SHA-256; consumer/guard searches; official read-only documentation; three isolated pure fixtures.",
    "graph_availability": "Session ALL_TOOLS discovery found no codebase-memory search_graph/trace_path/get_code_snippet/query_graph/index_repository tools; targeted reads/rg used.",
    "restrictions": "No source edits, production/native execution, operator-data access, deployment, external mutation or additional agents. Source review did not read runtime databases or account/session histories.",
    "fixture_scope": "runtime_executed=true means the isolated pure fixture ran, not the application/native system. All application/native runtimes remained unexecuted.",
    "observed_sources": [{"candidate_id": r["candidate_id"], "path": r["path"], "sha256": r["current_source_sha256"]} for r in ROWS],
    "official_references": [
        {"candidate_id": "SW100-C0582", "url": "https://doc.rust-lang.org/std/process/struct.Child.html", "observation": "Dropping Child does not ensure child termination or wait."},
        {"candidate_id": "SW100-C0464", "url": "https://doc.rust-lang.org/cargo/reference/workspaces.html", "observation": "Workspace members share target in the workspace root by default."},
        {"candidate_id": "SW100-C0051", "url": "https://developer.mozilla.org/en-US/docs/Web/API/Request/text", "observation": "text() rejects with TypeError for a disturbed/locked body."},
        {"candidate_id": "SW100-C0016", "url": "https://www.typescriptlang.org/docs/handbook/release-notes/typescript-3-7.html#local-and-imported-type-declarations-now-conflict", "observation": "Imported and local interface declarations conflict; augmentation requires separate module augmentation."},
        {"candidate_id": "SW100-C0593", "url": "https://github.com/remotion-dev/remotion/blob/main/packages/docs/docs/flickering.mdx", "observation": "Components should derive visuals from frame and not rely on frame execution order.", "retrieval": "Context7 /remotion-dev/remotion"},
    ],
    "additional_scope_checks": {
        "cargo_config": "No crates/.cargo/config(.toml) or crates/eridu-infer/.cargo/config(.toml) exists; root config inspected; global config/environment not inspected.",
        "purge_modules": "rg --files confirmed cortex/__init__.py and cortex/gemini_labs_nexus.py exist; cortex_chaos_monad.py is protected.",
        "mmr_consumers": "Targeted rg over crates/b60-lang/src and tests found public re-export and local positive test; external production consumer not established.",
        "forensics_timing": "C0242 hash was read directly before coordinator announced a separate fix. Historical review deliberately not overwritten by remediation hash drift.",
        "fixture_harness_correction": "First JSON fixture selected an earlier valid metadata example and failed its expectation; selector was anchored to Deploy with Bindings, then all three fixture groups passed. This was a fixture selection error, not a changed source finding.",
    },
}
(BASE / "14-review-evidence.json").write_text(json.dumps(evidence, indent=2) + "\n")
(BASE / "reviews/14.json").write_text(json.dumps({"reviewer": "14", "candidates": ROWS}, indent=2) + "\n")
for row in ROWS:
    for evidence_path in row["evidence_paths"]:
        assert (ROOT / evidence_path).is_file()
summary = {"reviewer": "14", "assigned": 29, "reviewed": len(ROWS), "decisions": dict(Counter(r["decision"] for r in ROWS)), "severity": dict(Counter(r["severity"] for r in ROWS)), "application_runtime_executed": False, "schema_ids_paths_and_evidence_validated": True}
(BASE / "14-validation.json").write_text(json.dumps(summary, indent=2) + "\n")
print(json.dumps(summary, indent=2))
