"""Build reviewer 03 artifacts from independently inspected source spans."""

import hashlib
import json
from pathlib import Path

BASE = Path("docs/security/evidence/swarm100-round3-20261028")
ASSIGNED = json.loads((BASE / "assignments/03.json").read_text())
BY_ID = {c["candidate_id"]: c for c in ASSIGNED}
RECORDS = []


def add(number, rationale, guards, checks, reproduced=False, severity=None):
    candidate_id = f"SW100-C{number:04d}"
    original = BY_ID[candidate_id]
    primary = original["path"]
    RECORDS.append({
        "candidate_id": candidate_id,
        "decision": "REPRODUCED" if reproduced else "CONFIRMED_STATIC",
        "severity": severity or original["severity"],
        "remediation_state": "OPEN",
        "path": primary,
        "current_source_sha256": hashlib.sha256(Path(primary).read_bytes()).hexdigest(),
        "rationale": rationale,
        "source_checks": [
            {"path": path or primary, "start_line": start, "end_line": end, "observation": observation}
            for path, start, end, observation in checks
        ],
        "guards": guards,
        "runtime_executed": reproduced,
        "runtime_scope": "Only AST-selected Python source or expressions in a synthetic isolated fixture; no product/native service, hardware gate, network or operator data." if reproduced else "Static review only; any supporting model is identified separately and does not execute the product runtime.",
        "evidence_paths": [str(BASE / "03-source-evidence.json")],
    })


add(428,
    "stop() sets the termination event before queue.join(), while the worker only enters its consume loop when that event is unset. A queued item present before the worker reaches the loop remains unfinished, so join and the item's future can remain pending. The task-done guard in append only rejects later appends; it does not drain or fail already queued futures. This is a current static shutdown defect, not an observed production hang.",
    ["Queue capacity is bounded to 4096.", "append rejects an absent or already terminated worker, but does not reject shutdown-in-progress.", "Worker task_done runs only after an item has been acquired."],
    [(None, 143, 172, "stop sets _stop_event before awaiting join; append has no stopping-state check."),
     (None, 363, 397, "Worker exits its while condition without acquiring or task_done-ing remaining queued items.")])

add(429,
    "The idempotency key is computed from plaintext, but every encrypted append creates fresh Fernet ciphertext and the duplicate-event path compares that ciphertext byte-for-byte. A repeat of the same event therefore collides when its randomized ciphertext differs. Rollback amplification is separately tracked by SW100-C0430; this record is the independently actionable encrypted-idempotency defect. No encrypted production ledger was opened.",
    ["Encryption is conditional on CORTEX_VAULT_KEY; plaintext retries are not affected by this mismatch.", "event_id uniqueness and the payload comparison reject mismatches but do not compare decrypted plaintext or a canonical payload digest."],
    [(None, 425, 437, "Existing event IDs compare stored_payload directly to the persisted payload_json."),
     (None, 480, 502, "UUID key uses canonical plaintext, then Fernet.encrypt runs anew before each transaction.")])

add(430,
    "_execute_insert_tx rolls back on transaction exceptions, then _process executes ROLLBACK again without checking transaction state. After a successful first rollback, the second can fail because no transaction exists; the handler closes the connection and raises RuntimeError, which terminates the worker and leaves later queued requests unresolved. The collision branch also rolls back before entering the same transaction exception handler. The issue remains open independently of encrypted retries.",
    ["The worker normally treats ValueError as an item-level error.", "Cascading Rollback Defense closes the connection on rollback failure, but converts an already handled SQL error into a fatal worker error.", "Later append calls detect a dead worker; queued futures are not failed in bulk."],
    [(None, 431, 437, "Collision path performs an explicit rollback then raises."),
     (None, 464, 478, "Transaction exception handler unconditionally performs rollback."),
     (None, 500, 512, "Caller performs another rollback and closes the connection when it fails."),
     (None, 385, 397, "Non-ValueError process exceptions terminate the worker.")])

add(431,
    "get_state_attestation obtains aggregates and leaves in separate SELECTs without an explicit read transaction, then verifies integrity through verify_chain's separate connection/snapshot. Concurrent appends can make total_entries/max_seq and the roots refer to different states. The isolated in-memory SQLite model confirms that this SELECT sequence can observe count 1 and two leaves after an intervening commit; the actual asynchronous ledger was not executed. anchor_to_rekor consumes the mixed fields without a snapshot/checkpoint comparison.",
    ["verify_chain now verifies its own transaction snapshot, but that snapshot is separate from the attestation aggregates and roots.", "Errors during chain verification set integrity_verified false; successful verification is not bound to the earlier reported head."],
    [(None, 269, 307, "Attestation lacks BEGIN and calls verify_chain after closing the aggregate/root connection."),
     (None, 174, 178, "Chain verification helper starts its own BEGIN on a new connection."),
     (None, 239, 247, "verify_chain checks only its own returned checkpoint unless an external checkpoint is passed."),
     (None, 319, 327, "Rekor head serializes roots and counts taken from get_state_attestation.")])

add(271,
    "verify_manifest authenticates the root against the public key embedded in that same manifest. It has no expected-key or trusted-identity parameter. With no db_path, tree_valid remains None and does not prevent overall_valid; the hardware UUID comparison is informational and excluded from the verdict. A self-signed root with the required status therefore satisfies this verifier without proving the advertised L0/sovereign identity. The CLI reports success from overall_valid. No protected runtime authorization bypass or native attestation execution is established.",
    ["Ed25519 signature validity is checked against the supplied key.", "A supplied database must match root and claim count.", "Required status is FROZEN_C5_REAL.", "Origin-host comparison is reported but not an acceptance condition."],
    [(None, 142, 159, "Verifier signature accepts any supplied Ed25519 key; manifest API has no trust-anchor input."),
     (None, 165, 207, "Key/signature come from JSON, database is optional, and overall_valid omits pinned identity and host match."),
     ("01_KISH_ENGINE/babylon60/cli/bounty_cli.py", 132, 167, "CLI prints verified and returns zero solely from report overall_valid.")])

add(272,
    "The exported claim leaf helper concatenates five unrestricted strings with colons. AST-selected evaluation of its actual preimage expression gives the identical string for (claim_id='a:b', advisory_id='c') and (claim_id='a', advisory_id='b:c') with the other fields fixed. Identical hash input entails identical BLAKE3 output without any cryptographic collision. Verifier recomputation uses this helper, and the inspected ledger schema has no delimiter restriction. Reachability through every upstream claim producer was not established; confirmation is limited to this public encoding and verifier boundary.",
    ["The digest is BLAKE3, but the preimage encoding is not injective.", "The database imposes a primary key and NOT NULL fields, not a delimiter grammar.", "No full upstream ingestion/exploitation claim is made."],
    [(None, 39, 48, "Leaf fields are joined with unescaped colons."),
     (None, 187, 203, "Manifest recomputation passes persisted claim strings into that helper."),
     ("01_KISH_ENGINE/babylon60/bft/bounty_cold_ledger.py", 41, 54, "Claim/advisory strings are TEXT without colon restrictions."),
     ("01_KISH_ENGINE/babylon60/attestation/__init__.py", 1, 19, "Helper is exported by the attestation package.")], reproduced=True)

add(74,
    "The registry accepts and retains arbitrary EvidenceRecord.status values, and all citation branches trust any lookup hit. In an isolated execution of the source classes, a synthetic DOI record marked REVOKED passed STRICT_ABORT, appeared in verified_citations and produced COMMITTED. This proves the status-enforcement defect without making any claim that the synthetic citation is real or that a production registry was changed.",
    ["register validates digest presence/length and rejects the empty digest.", "STRICT_ABORT rejects missing citations and synthetic placeholders, but does not inspect record.status."],
    [(None, 115, 148, "register validates only digest and lookup returns cached entries regardless of status."),
     (None, 256, 278, "Patent acceptance checks only record truthiness."),
     (None, 300, 331, "arXiv and DOI acceptance also check only record truthiness."),
     (None, 342, 365, "No unverified items produces COMMITTED and the record is returned as verified.")], reproduced=True)

add(75,
    "register mutates _cache before opening or committing SQLite, with no compensating cache restoration when durable registration raises. An isolated source-class fixture injected connect failure before any database opened; register raised, but lookup still returned the attempted record. A caller that catches the exception and retains the registry can trust a record absent from a later reopened registry. No production database or filesystem failure was induced.",
    ["The SQLite context manager controls transaction rollback only.", "Digest validation happens before the cache write, but persistence failure does not undo it."],
    [(None, 120, 144, "Cache assignment precedes connection and transaction and has no error compensation."),
     (None, 146, 169, "Runtime lookup uses cache; reopening loads durable rows separately.")], reproduced=True)

add(493,
    "A successful chat request's model string flows from req.model to receipt.model_id and then to the receipts JSON. HUD fetchReceipts interpolates it into tbody.innerHTML without escaping. A caller able to reach the chat endpoint can therefore supply active HTML markup for later rendering in the HUD origin. The inspected router adds no authentication or CSP middleware, and the gate's success guard does not constrain model text. This is a static stored-markup injection trace; no server, browser or exploit was run, and network exposure beyond an accessible local endpoint is not asserted.",
    ["The normal UI selects a model from a list, but direct JSON requests are accepted as String values.", "The causal gate can reject publication when the manifest is poisoned; successful publication stores model unchanged.", "The prompt response uses textContent, which does not protect the separate ledger table sink."],
    [(None, 506, 524, "Receipt model_id is interpolated into innerHTML."),
     ("crates/eridu-infer/src/server.rs", 53, 74, "Router exposes chat and receipt endpoints; receipt handler returns the stored receipt list."),
     ("crates/eridu-infer/src/server.rs", 118, 141, "Chat handler forwards req.model directly to evaluate_and_seal."),
     ("crates/eridu-infer/src/gate.rs", 85, 105, "Successful gate stores model.to_string() in recent_receipts without HTML encoding.")])

add(494,
    "The response badge prints CONFORME EU AI ACT whenever choices[0] exists, and every rendered receipt prints VERIFICADO (ART. 12-14). No verification status is consulted. The gate itself assigns a constant compliance_status after hashing/publication. These operations do not constitute a compliance assessment, so this UI overstates what its code establishes. Confirmation concerns unconditional product claims, not a legal conclusion about the system's actual compliance.",
    ["The response badge is conditional on a returned choice.", "Receipt generation requires successful manifest publication, but no compliance evidence is evaluated."],
    [(None, 491, 497, "Success response unconditionally receives the conformity label."),
     (None, 516, 524, "Every receipt receives a hardcoded verified badge."),
     ("crates/eridu-infer/src/gate.rs", 85, 105, "Receipt compliance_status is a constant after publication."),
     ("crates/eridu-infer/src/server.rs", 144, 160, "Response branch formats a template; it does not validate the badge's asserted compliance.")])

add(456,
    "The CLI documents --target-name as a filename inside _incoming_forge but passes it unchanged to INCOMING_DIR / target_filename and write_text. Absolute paths discard the base and ../ components can escape it; neither syntax validation nor the ledger insert enforces containment. This confirms an overwrite hazard for an authorized local CLI caller supplying such a path. No remote caller, privilege escalation or outside-tree write was exercised.",
    ["Python/JSON targets receive syntax validation, which does not validate paths.", "Writes still require operating-system access to the selected parent directory."],
    [(None, 69, 88, "Target is joined and written directly after content syntax validation."),
     (None, 104, 114, "CLI forwards target-name without basename or containment checks.")])

add(457,
    "The extractor pattern encodes a literal backslash followed by n rather than an actual newline. Isolated execution of the unchanged source on a normal Python Markdown fence retained all fence lines; verify_ast_syntax then returned false. The fallback strips a few prose prefixes but does not remove fences. Python/JSON ingestion can therefore reject the ordinary fenced output requested by the prompt wrapper.",
    ["Syntax validation prevents invalid fenced Python/JSON from being written.", "Other extensions accept any nonempty text and can retain the fence markup."],
    [(None, 18, 18, "Wrapper asks for output inside a Markdown code block."),
     (None, 40, 66, "Regex matches literal backslash-n and fallback retains Markdown fence lines."),
     (None, 72, 77, "Assimilation raises when the retained fenced code fails syntax verification.")], reproduced=True)

add(420,
    "verify_attestation reads all component digest strings and the expected compound hash from the same editable JSON. It never recomputes current artifact digests, obtains current HEAD or verifies a signature. A synthetic in-memory statement with arbitrary edited commit text and a recomputed unkeyed compound checksum was accepted by the isolated source function. This confirms self-consistency only and cannot support its printed 100% causal-integrity/provenance claim; stale source-artifact detection is absent from the inspected function. No real campaign or compliance artifact was read.",
    ["The function detects an inconsistent compound checksum.", "This checksum is unkeyed and supplied alongside the values it summarizes; it is not a provenance trust anchor."],
    [(None, 158, 180, "Verification reads only the saved statement and hashes its own supplied fields."),
     (None, 183, 196, "CLI --verify directly uses this verifier.")], reproduced=True)

add(421,
    "verify_attestation returns False for a missing statement or checksum mismatch, but main ignores that boolean and returns normally. Those handled verification failures therefore produce the interpreter's normal successful exit, preventing shell callers from using the process status as a verification verdict. Parse exceptions can still exit nonzero; the finding is limited to the explicitly handled false-result paths.",
    ["Human-readable output reports failure.", "Unhandled parsing/I/O errors may fail the process, but do not correct the ignored False paths."],
    [(None, 158, 180, "Missing statement and mismatch are represented as False."),
     (None, 183, 196, "main discards the result and invokes no sys.exit failure mapping.")])

add(18,
    "run_auto_purge recursively unlinks every *.db-shm and *.db-wal beneath the working directory with no database ownership, checkpoint or connection coordination. A live WAL can contain committed pages not yet in the main database, so this deletion can lose committed state or disrupt other clients. strict_reviewer invokes the helper before committing, although earlier reviewer work can itself fail; public helper reachability alone is sufficient for the hazard. No purge or database deletion was executed.",
    ["OS permissions limit which files find can delete.", "The helper uses check=False, with no liveness or checkpoint guard.", "The caller stopping its own ledger does not establish exclusive ownership of every database under cwd."],
    [(None, 16, 30, "Unqualified recursive find deletes WAL/SHM files as cache material."),
     ("01_KISH_ENGINE/babylon60/commands/strict_reviewer.py", 144, 160, "Reviewer stops its own actor and later invokes the global purge before Git add/commit.")])

add(487,
    "The successful signing path constructs JSON by interpolating strings after replacing quotes only. CLI action/prompt/scope accept raw strings; backslashes, newlines and other control characters are not JSON encoded. An authorized successful invocation with such input can emit malformed JSON or decode to altered field values. The signing and causal-hash controls do not sanitize these serialization fields. This is static analysis of receipt emission; no biometrics, Secure Enclave operation or native binary was run.",
    ["Actual signing verifies its signature before receipt emission.", "Quote replacement covers only double quotes.", "Causal hash is required outside preview, but does not constrain action/prompt/scope characters."],
    [(None, 167, 205, "CLI stores raw action, prompt, scope and agent arguments."),
     (None, 236, 240, "Causal-hash requirement is distinct from text serialization."),
     (None, 377, 405, "Receipt uses manually interpolated JSON with quote-only escaping.")])

add(373,
    "dispatch embeds the bearer token in curl's command list. On CalledProcessError with empty stderr it returns str(exception), which includes that list. An isolated source-class fixture injected exactly that failure using a synthetic token and confirmed the token in returned detail. This establishes a credential-disclosure path to callers/logs, without reading any real credential or executing curl, Keychain or network operations.",
    ["Missing keys return before curl.", "Nonempty stderr replaces the command-bearing fallback, so the demonstrated branch requires empty stderr.", "No redaction is applied before returning exception detail."],
    [(None, 41, 67, "API key is inserted into the command's Authorization header."),
     (None, 69, 87, "check=True error is returned with str(e.stderr or e), exposing the command on empty stderr.")], reproduced=True)

add(535,
    "payload_hash is a ctypes c_char[16] structure field, which yields a NUL-terminated byte string on attribute access. read wraps that already truncated result in bytes. An isolated instance of the actual source structure assigned a 16-byte synthetic digest containing NUL and returned only the first three bytes. The channel write method accepts arbitrary binary digest bytes and supplies no encoding guard. No shared memory, native service or concurrent writer was exercised.",
    ["write truncates/pads input to exactly 16 bytes.", "Sequence equality checks protect consistency of the fields but cannot restore bytes already discarded by C-string access."],
    [(None, 29, 36, "payload_hash is c_char * 16."),
     (None, 68, 87, "write assigns binary digest bytes, including embedded zero bytes."),
     (None, 89, 107, "read obtains the field via NUL-terminated attribute access before bytes().")], reproduced=True)

add(17,
    "The document displays two finite aggregate benchmark runs and then calls the result mathematical proof, strict real-time determinism and a highly patentable invention. The displayed measurements include an observed maximum but no worst-case execution-time derivation, hardware scheduling bound or independent patentability assessment. The conclusion exceeds the evidence in this artifact. This is an evidentiary/documentation defect; no legal determination or claim that the shown measurements themselves are fabricated is made.",
    ["The results are labeled empirical and include sample operation counts.", "No qualification in the inspected conclusion limits determinism to the observed sample."],
    [(None, 10, 33, "Only two aggregate benchmark result sets are displayed."),
     (None, 35, 50, "Conclusion escalates observed latency maxima to mathematical proof, strict determinism and patentability.")])

add(396,
    "run_calibration computes its root as the parent of scripts/c5_calibrations, i.e. scripts. Four configured corpus paths do not exist under that root; scripts/README.md does exist and is selected instead of the repository README. Missing inputs only emit warnings, while final thresholds are still calculated and returned. Read-only existence checks verified this current layout. The calibration itself and its imported filter were not run, and import availability remains a prerequisite to reaching this defect.",
    ["Missing files print warnings.", "calculate_stats returns all-zero statistics for an empty list, allowing thresholds even with no technical samples.", "No expected corpus-size or path-origin guard exists in run_calibration."],
    [(None, 18, 27, "Configured corpus paths are relative strings intended for the package/repository layout."),
     (None, 37, 63, "Root resolves one level up and missing files do not abort."),
     (None, 69, 84, "Thresholds are printed and returned regardless of missing technical inputs.")])

add(105,
    "The so-called Oxford/NLI path groups supplied integer semantic_id labels, and the probe uses seeded random weights against synthetic hidden activations. The reporting compares their timings as Oxford NLI versus SEP acceleration and describes empirical detection conclusions. Those measurements can characterize this synthetic harness but do not validate actual NLI or trained-probe implementations. The generator does identify its data as synthetic, which limits the claim; the benchmark labeling still attributes results beyond what is executed. No NLI model, benchmark or kernel was run in this review.",
    ["Scenario generator is explicitly named synthetic.", "Seeded weights make a fixture repeatable but do not establish trained/calibrated probe performance.", "Assertions check prescribed scenario behavior, not correspondence to an external NLI implementation."],
    [(None, 44, 58, "Evaluator claims NLI/SEP and initializes random probe weights."),
     (None, 69, 110, "Semantic equivalence is integer label equality; probe is a linear projection."),
     (None, 217, 224, "Stress-test contract claims comparative empirical certification."),
     (None, 259, 273, "Labels timing of this grouping as NLI clustering and SEP."),
     (None, 338, 361, "Reports SEP acceleration and Oxford detection conclusions from the synthetic run.")])

add(378,
    "The emitter selects z3_precondition but never uses it to instantiate the Lean proof. Every cluster receives the fixed state-machine template parameterized by signature prefix/file count, and successful Lean exit marks the cluster PROVED. Its claimed Rust-isomorphic gate checks poisoned, sequence and writer state, while downstream codegen consumes PROVED rows and emits only full signature/file-count checks. Thus neither the extracted precondition nor the implementation correspondence is established by the generated proof. No Lean compiler, generated binary or database mutation was executed.",
    ["Lean exit status must be zero before the row is marked PROVED.", "The template contains actual theorem/axiom checks, but only for its fixed model.", "The codegen checks full signature length/value and file count; this differs from the modeled state conditions."],
    [(None, 54, 92, "Fixed Lean model includes poison/sequence/writer conditions and a signature prefix."),
     (None, 164, 198, "z3_precondition is queried but omitted from the template parameters."),
     (None, 203, 220, "Lean compilation success updates proof and cluster status to PROVED."),
     ("scripts/c5_destiladora/codegen_rust_b60.py", 28, 65, "Generator selects PROVED rows and builds signature/file-count specs."),
     ("scripts/c5_destiladora/codegen_rust_b60.py", 124, 134, "Generated function checks only signature and file count.")])

add(93,
    "The global health verdict considers only phase_4 FAIL and phase_1 isolation FAIL. Failed log custody, synchronization and vault consolidation become WARN, and absent quality gates start/stay true. Those states can still emit HEALTHY_OPTIMAL, clear an existing alert and return zero. Detailed phase data retains some warnings, so failures are not completely hidden, but the top-level success signal does not represent all configured maintenance obligations. The maintenance command, notifications, purge and report writes were not executed.",
    ["Phase 4 failures and phase 1 isolation failures produce CRITICAL_ANOMALY/nonzero exit.", "Detailed phase reports retain WARN/SKIP states for some phases.", "Missing quality-gate files have no failure/skip guard because booleans default to true."],
    [(None, 103, 149, "Log/sync command failures map to WARN and absent sync scripts leave success booleans true."),
     (None, 152, 195, "Quality gates default true when absent; consolidation can WARN or SKIP."),
     (None, 209, 226, "Only two failure conditions determine the global verdict."),
     (None, 240, 251, "A noncritical global verdict removes an existing alert."),
     (None, 305, 325, "The global verdict alone determines process exit status.")])

add(347,
    "Twenty workers per cohort select their rule by sub_idx modulo rule count. Current rule counts are 6, 6, 9, 5 and 6, so each configured target/pattern is scanned repeatedly. Aggregation sums all results; its set deduplicates only target labels, not file or byte totals. Any matched file therefore contributes multiple times to reported total_anergy_bytes and total_files_audited. This confirms inaccurate unique cleanup-capacity reporting, not repeated deletion: this inspected script only scans and writes a report. No operator data was scanned.",
    ["Nonexistent target directories contribute zero.", "A target-label set exists but is not used to deduplicate the byte/file sums.", "This script's inspected execution is reporting, not purge execution."],
    [(None, 16, 88, "Five cohorts define fewer than twenty rules each."),
     (None, 95, 138, "Twenty workers per cohort select rules cyclically and return full scan totals."),
     (None, 141, 175, "All worker file/byte counts are summed; only target labels are deduplicated.")])

add(83,
    "The generator writes freshly timestamped PASS values and fixed gate counts without executing those gates. It also reuses a fixed causal hash, signature/key and timestamp while taking the current Git commit and artifact bytes for other fields. The resulting bundle cannot establish that those current-checkout gates passed or that fixed signing material binds this new snapshot. The manifest explicitly marks hardware UNVERIFIED and certification NONE, which limits certification claims but does not qualify the fabricated PASS fields. No generator or external signing action was executed.",
    ["Manifest says hw_provenance UNVERIFIED and certification NONE.", "Actual git rev-parse and selected artifact hashing populate some snapshot fields.", "No subprocess or function invocation supplies the hardcoded gate results."],
    [(None, 15, 30, "Current commit and selected artifact bytes are read for some fields."),
     (None, 54, 68, "test-results.json receives constant PASS outcomes/counts with current timestamp."),
     (None, 70, 101, "Fixed signing material/timestamp coexist with current snapshot fields and explicit uncertified metadata.")])

add(467,
    "The collected async test prints the returned status/receipt and branches only to print more text. It contains no assertion on Success, signature, receipt or error. Any dictionary representing a handled failure or blocked result can complete this test successfully; exceptions still fail it. This is a regression-test oracle gap, not proof that the underlying attestation runtime fails. The chaos monad and its payload were not executed.",
    ["Exceptions from opening the payload or invoking the monad still fail the test.", "There is no assertion validating a handled result dictionary."],
    [(None, 7, 29, "All result-status branches merely print; none asserts or raises on failure.")])

add(44,
    "The published BatchProcessor example copies pending into a local batch and clears the only retained queue before SQL insertion. If that insertion throws, the method has no restoration or durable pending record. A later invocation on the same object sees an empty batch and builds a VALUES clause with no rows. This confirms an error-handling defect in the example, not an observed Cloudflare deployment or an assertion about a particular platform retry schedule.",
    ["The alarm is scheduled only when absent.", "Neither pending nor the copied batch is persisted before processing.", "No try/catch restoration or empty-batch guard follows the insert."],
    [(None, 76, 91, "alarm clears in-memory pending before the only SQL insertion and has no restoration.")])

add(576,
    "The documented criterion compares exp(-dE/T) to fixed 0.5, making a fixed uphill proposal always accepted or always rejected at a fixed positive temperature. It does not draw a random uniform threshold, despite being labeled Metropolis-Hastings. The separate candidate generator may be stochastic, but that does not make this conditional an acceptance-probability draw. Scope is the canonical documented example; no optimization result or production runtime was tested.",
    ["Downhill moves are accepted and zero temperature rejects uphill moves.", "A duplicate-candidate hash check is present, but does not implement stochastic acceptance."],
    [(None, 90, 108, "Temperature schedule and collision filter do not produce an acceptance random variate."),
     (None, 110, 122, "Metropolis-Hastings-labeled branch compares to literal 0.5.")])

add(501,
    "compute_merkle_root hashes values without their field names and then sorts the hashes. Isolated execution of the exact function confirms identical roots after swapping author/text values or renaming their keys while preserving the value multiset. Thus semantically different records can carry the same advertised evidence seal without a SHA-256 collision. main stores this root as merkle_seal. No social content, live account, extraction API or operator data was accessed.",
    ["Nested dictionaries/lists use deterministic JSON serialization.", "Sorting dictionary keys does not preserve field binding after the value-only leaves are independently sorted.", "A stronger outside signature/trust layer was not established in this local seal path."],
    [(None, 689, 719, "Leaf hashes omit key names and are sorted before Merkle reduction."),
     (None, 2935, 2940, "main saves the computed root and leaf count as merkle_seal.")], reproduced=True)

fixture_ids = {r["candidate_id"] for r in json.loads((BASE / "03-isolated-fixtures.json").read_text())["checks"]}
for record in RECORDS:
    if record["candidate_id"] in fixture_ids:
        record["evidence_paths"].extend([str(BASE / "03-isolated-fixtures.py"), str(BASE / "03-isolated-fixtures.json")])

assert len(RECORDS) == len(ASSIGNED) == 29
assert [r["candidate_id"] for r in RECORDS] == [r["candidate_id"] for r in ASSIGNED]
evidence = {"reviewer": "03", "discovery": "No codebase-memory graph tools were exposed in the native session tool inventory; targeted source reads were used.", "scope": "Source audit plus isolated synthetic Python checks. No protected/native product effects, network, operator data or production source edits.", "sources": {}}
for record in RECORDS:
    for check in record["source_checks"]:
        path = check["path"]
        data = Path(path).read_bytes()
        lines = data.decode("utf-8").splitlines()
        assert 1 <= check["start_line"] <= check["end_line"] <= len(lines), check
        source = evidence["sources"].setdefault(path, {"sha256": hashlib.sha256(data).hexdigest(), "snippets": []})
        source["snippets"].append({"candidate_id": record["candidate_id"], **check, "text": "\n".join(f"{i + 1}: {lines[i]}" for i in range(check["start_line"] - 1, check["end_line"]))})
    assert hashlib.sha256(Path(record["path"]).read_bytes()).hexdigest() == record["current_source_sha256"]

(BASE / "03-source-evidence.json").write_text(json.dumps(evidence, indent=2, ensure_ascii=False) + "\n")
(BASE / "reviews").mkdir(exist_ok=True)
(BASE / "reviews/03.json").write_text(json.dumps({"reviewer": "03", "candidates": RECORDS}, indent=2, ensure_ascii=False) + "\n")
print(json.dumps({"reviewer": "03", "count": len(RECORDS), "reproduced": sum(r["decision"] == "REPRODUCED" for r in RECORDS), "confirmed_static": sum(r["decision"] == "CONFIRMED_STATIC" for r in RECORDS), "remediation_open": sum(r["remediation_state"] == "OPEN" for r in RECORDS)}))
