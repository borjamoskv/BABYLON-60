"""Materialize reviewer 17 adjudications and bounded, current-source evidence."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
BASE = Path(__file__).resolve().parent
ASSIGNED = json.loads((BASE / "assignments/17.json").read_text())
BY_ID = {x["candidate_id"]: x for x in ASSIGNED}
ROWS = []


def check(path, start, end, observation):
    return {"path": path, "start_line": start, "end_line": end, "observation": observation}


def add(number, rationale, spans, guards, decision="CONFIRMED_STATIC", state="OPEN"):
    cid = "SW100-C" + number
    original = BY_ID[cid]
    path = original["path"]
    checks = [check(path if p is None else p, a, b, o) for p, a, b, o in spans]
    evidence = [str((BASE / "17-source-evidence.json").relative_to(ROOT))]
    if decision == "REPRODUCED":
        evidence += [str((BASE / name).relative_to(ROOT)) for name in ("17-pure-checks.py", "17-pure-checks.json")]
    ROWS.append({"candidate_id": cid, "decision": decision, "severity": original["severity"], "remediation_state": state,
                 "path": path, "current_source_sha256": hashlib.sha256((ROOT / path).read_bytes()).hexdigest(),
                 "rationale": rationale, "source_checks": checks, "guards": guards,
                 "runtime_executed": decision == "REPRODUCED", "evidence_paths": evidence})


add("0566", "Replay vector signs a zero precondition and discards the first execution result. The actual adapter computes a domain-separated resource hash and the executor verifies it before reserving a nonce. Any error on the second call counts as replay rejection. The harness therefore never establishes successful first consumption or a replay-specific error; this is coverage failure, not a demonstrated executor replay bypass.", [
    (None, 88, 96, "Each vector starts with a new resource at counter 100."),
    (None, 151, 168, "Zero precondition; first result ignored before asserted nonce consumption."),
    (None, 188, 217, "Any error increments named rejection count and feeds report."),
    ("src/executor_ipc.rs", 167, 172, "Actual precondition is computed from resource state."),
    ("src/executor.rs", 1015, 1024, "Authorization checked before nonce reservation.")],
    ["Signer, policy and expiry do not validate the zero resource digest.", "Executor guards remain present; harness does not distinguish which rejected."])

add("0567", "Crash cohort does uninterrupted quarantine, verification and destruction with one orchestrator. Its report declares five crash points and SIGKILL_SIMULATED from a counter of verification errors, without interruption, restart, durable reload or recovery invocation. Current recover_quarantined requires a durable matching intent. The report overstates coverage; the observed source supports only sequential filesystem operations.", [
    (None, 317, 355, "Full cohort has no interruption or recovery call."),
    (None, 356, 369, "Literal crash-point list and PASS verdict from verification counter."),
    ("src/secure_fs.rs", 2316, 2354, "Actual recovery API checks durable intent and identity.")],
    ["unwrap failures abort ordinary operations, without testing restart recovery.", "Recovery guards exist but are not exercised here."])

add("0568", "The harness ignores all secure_delete errors and bases PASS solely on zero unauthorized effects, without requiring honest commits or attack rejections. In current source the called compatibility API always returns MissingAuthorization, so every call reaching it enters the ignored branch. This is a vacuous harness success, not a bypass of the separately authorized scoped deletion API.", [
    (None, 261, 281, "Legacy call and wildcard error suppression."),
    (None, 287, 303, "Join checked, but PASS has no coverage minimum."),
    ("src/secure_fs.rs", 2055, 2065, "Legacy API unconditionally rejects missing authority."),
    ("src/secure_fs.rs", 2084, 2121, "Scoped API validates epoch, effect, nonce and budget.")],
    ["Setup/pinning failures may abort earlier.", "MissingAuthorization is fail-closed; report misclassifies its outcome."])

add("0077", "Mock infer slices a Rust string at byte min(len,32). A 31-byte ASCII prefix followed by a multibyte character places byte 32 inside that character and panics. Engine forwards the prompt under timeout without character normalization or panic handling. Scope is the mock backend selected by tests/PoCs, not a demonstrated production inference outage.", [
    (None, 347, 375, "Zero failure rate reaches unchecked byte slice."),
    (None, 232, 249, "Engine passes original prompt to backend."),
    (None, 398, 415, "Mock consumer test uses short ASCII input.")],
    ["Short input and character-aligned byte 32 are safe.", "Cooldown or stochastic failure can stop earlier, but does not validate boundaries."])

add("0078", "attested hashes content then model_id without framing. Pairs (ab,c) and (a,bc) feed identical bytes abc and receive identical content_hash without a cryptographic collision. Mock output uses the constructor; determinism test changes model while holding content fixed. Confirmed scope is ambiguous pair binding; no production authorization consumer was established by scoped search.", [
    (None, 67, 94, "Public constructor concatenates independently variable fields."),
    (None, 365, 375, "Mock output uses attested constructor."),
    (None, 482, 491, "Current test misses ambiguous content/model boundaries.")],
    ["BLAKE3 cannot distinguish identical encoded bytes.", "Default mock model is fixed, but public constructor accepts arbitrary model IDs."])

add("0365", "Original shred_fact_async missing-table failure is removed from that call path: current method returns an unsuccessful CRYPTO_ERASURE_UNSUPPORTED result without querying shredded_keys. Constructor still skips async schema and historical read APIs still query it. The reported shred-call defect is mitigated by fail-closed refusal; real async erasure remains unavailable.", [
    (None, 69, 103, "Only sync connections get automatic schema."),
    (None, 132, 138, "Historical marker reader still depends on table existence."),
    (None, 169, 189, "Async shredding returns explicit unsupported failure without SQL."),
    (None, 208, 229, "Batch consumer records unsuccessful results as failures.")],
    ["Wrong connection kind still intentionally raises TypeError.", "Does not claim fresh-database historical reads or actual erasure now work."], "ALREADY_FIXED", "MITIGATED")

add("0366", "Current audit_timestamp uses time.time() as UTC epoch seconds instead of time.monotonic(). The original uptime-as-calendar-time expression is absent from the inspected function. This is a source-confirmed timestamp correction only; no compliance, erasure or protected-runtime certification is inferred.", [
    (None, 231, 260, "Report now calls datetime.fromtimestamp(time.time(), tz=timezone.utc)."),
    ("tests/test_swarm100_round2_regressions.py", 314, 325, "Existing audit consumer checks compliant=False, not timestamp correctness.")],
    ["Audit still needs a sync database with schema.", "No protected erasure subsystem execution performed."], "ALREADY_FIXED", "FIXED")

add("0341", "Verifier gets its only public key from the same untrusted manifest containing the signature. There is no externally trusted key comparison, and CLI accepts only a manifest path. Signature validity plus caller-supplied FROZEN_C5_REAL status drives kernel attestation success and zero exit. This establishes embedded-key self-consistency, not authorized operator identity.", [
    (None, 194, 219, "Status/key parsing guards, but key trust source is manifest itself."),
    (None, 224, 245, "overall_valid is root signature plus status."),
    ("crates/babylon-attest/src/main.rs", 83, 88, "CLI has no separate trusted-key argument."),
    ("crates/babylon-attest/src/main.rs", 519, 540, "Consumer presents successful kernel verification and exits zero.")],
    ["Ed25519 signature and public-key length checks exist.", "Those checks do not establish signer authorization."])

add("0342", "Only decoded merkle_root bytes enter signature verification. aeon_id, claim count and hardware_uuid are copied from unsigned fields and printed in the successful attestation report; signed_payload is parsed but unused. Changing those fields does not alter root signature validity. Confirmed issue is metadata authenticity in the report, while the root itself still receives signature verification.", [
    (None, 163, 181, "Manifest separates metadata and root, with unused signed_payload."),
    (None, 224, 245, "Only root verified; unsigned metadata returned."),
    ("crates/babylon-attest/src/main.rs", 521, 537, "Report displays metadata alongside formal attestation success.")],
    ["Root changes require a valid signature.", "Literal status validation is not cryptographic metadata binding."])

add("0533", "Sealer catches every identity-load exception and calls forge_identity at the same storage path. Corrupt JSON or failed AEAD decryption can therefore cause a fresh random seed to truncate master_seed.enc, if forging subsequently succeeds. New key signs the root and enters the artifact. No operator identity data was accessed and no identity operation was executed.", [
    (None, 123, 135, "Broad load-error handler forges new identity."),
    ("01_KISH_ENGINE/babylon60/crypto/identity.py", 53, 62, "Both paths target master_seed.enc."),
    ("01_KISH_ENGINE/babylon60/crypto/identity.py", 75, 109, "Fresh random seed written with mode w to same path."),
    ("01_KISH_ENGINE/babylon60/crypto/identity.py", 111, 131, "Corruption or wrong passphrase raises."),
    (None, 162, 165, "Artifact consumes new public key/signature.")],
    ["AEAD correctly rejects corruption; caller reacts destructively.", "Earlier ledger/hardware stages can fail first, but no load-error classification protects existing seed."])

add("0534", "TSA authentication label depends solely on presence of tsr_b64. Client returns that field for any HTTP 200 body, without parsing timestamp status, signature, certificate trust or message imprint; sealer persists the label and token. Malformed or rejection bodies can be labeled authenticated. No TSA network request or remote mutation was performed.", [
    (None, 115, 121, "Field presence determines authenticated label."),
    ("01_KISH_ENGINE/babylon60/crypto/rfc3161.py", 85, 119, "HTTP 200 body is directly base64-encoded."),
    (None, 146, 165, "Artifact stores response and authentication label."),
    (None, 179, 180, "Artifact persisted without token validation.")],
    ["Missing/failed response gets offline label.", "HTTP success and transport security do not verify RFC3161 token signature or imprint."])

add("0474", "New assigned track is appended but never added to matched_tracks. Lost-track loop then increments its lost count and appends it again with default max_extrapolate=2. CLI iterates assignments without deduplication, allowing the same eligible face to be swapped twice. Scope is enabled tracking, assigned identity and a face passing size filters.", [
    (None, 95, 106, "Default extrapolation limit is two frames."),
    (None, 153, 182, "Only previously matched tracks enter matched_tracks."),
    (None, 191, 228, "New track later treated as lost and emitted again."),
    ("tools/skill_library/global/c5-audiovisual-acreativo-sota/references/modules/c5-neural-face-swap-cuadrilla/scripts/c5_face_swap_cli.py", 277, 305, "CLI consumes every assignment with identity/size filters.")],
    ["Negative identity is not emitted.", "Disabled tracking or small-face filtering can avoid the swap; neither deduplicates eligible new tracks."])

add("0475", "Blur mode sizes foreground from target width without fitting target height. A 1080x2400 source into 1080x1920 gives scaled_h=2400 and y_offset=-240, leaving only the final 240 destination rows for 2400 foreground rows. Assignment cannot fit. CLI passes actual source dimensions and blur mode through; no native imaging pipeline was run.", [
    (None, 236, 246, "Constructor preserves actual source dimensions."),
    (None, 264, 285, "Blur scaling and negative-offset assignment have no fit/crop guard."),
    ("tools/skill_library/global/c5-audiovisual-acreativo-sota/references/modules/c5-neural-face-swap-cuadrilla/scripts/c5_face_swap_cli.py", 450, 460, "Consumer constructs tracker from video dimensions."),
    ("tools/skill_library/global/c5-audiovisual-acreativo-sota/references/modules/c5-neural-face-swap-cuadrilla/scripts/c5_face_swap_cli.py", 498, 500, "Consumer directly writes reframed output.")],
    ["Crop mode takes a separate resize path.", "Missing tracker is skipped, but available tracker accepts tall aspect ratios."])

add("0358", "All three risk loops append receipts before enqueue and ignore its boolean result. Ledger returns False on full queue or shutdown, while report and CLI still include the receipt as a normal sealed claim. Worker failure exceptions now propagate but do not cover false returns. This is unreported persistence rejection; even true enqueue alone is not a durability acknowledgement.", [
    (None, 125, 166, "Three domains ignore enqueue acceptance."),
    ("01_KISH_ENGINE/babylon60/bft/bounty_cold_ledger.py", 103, 121, "Failed worker raises; closed/full queue returns False."),
    (None, 184, 195, "Report includes all generated receipts."),
    ("01_KISH_ENGINE/babylon60/cli/bounty_cli.py", 270, 279, "CLI displays/exports receipts without persistence status.")],
    ["Risk threshold and auto-attest gate generation.", "Failure exceptions protect a different path than boolean backpressure rejection."])

add("0345", "Manager loads a full metadata snapshot once and rewrites it using mode w without lock, reload or atomic replacement. A stale manager can overwrite another manager revocation or key addition; later is_revoked reads restored stale metadata. Revocation separately deletes private key material, limiting direct key resurrection, but does not preserve metadata or concurrent additions.", [
    (None, 70, 87, "Snapshot plus full truncate-and-rewrite."),
    (None, 119, 125, "Generation saves complete cached metadata."),
    (None, 164, 185, "Revocation saves metadata then attempts key deletion."),
    (None, 187, 206, "Consumers use cached revocation/expiration/key records.")],
    ["OS keyring protection is independent of metadata concurrency.", "Deleting private key can prevent signing; it does not prevent stale revocation metadata restoration."])

add("0259", "Pure execution of current decoder accepts 4378 as b'x' and 6378 as 'x' although each header declares length three; 0001 returns zero and ignores trailing item. Byte/text reads do not enforce length and loads does not require end-of-input. Public cbor_loads export and valid-roundtrip consumer were inspected; no production authorization exploit is claimed.", [
    (None, 127, 153, "Initial-byte EOF checked, payload length unchecked."),
    (None, 156, 161, "Top-level loads returns after one item."),
    ("01_KISH_ENGINE/babylon60/primitives/__init__.py", 5, 16, "Decoder exposed as cbor_loads."),
    ("tests/babylon60/primitives/test_sovereign_primitives.py", 18, 27, "Consumer covers valid roundtrip.")],
    ["Empty initial input and invalid UTF-8 can raise.", "These checks do not reject truncated valid text/bytes or trailing data."], "REPRODUCED")

add("0411", "--dry-run promises no disk writes, but unconditional chmod +x occurs before the dry-run return. An existing nonexecutable kernel script has its permissions changed by preview. Native host setup was not run.", [
    (None, 18, 24, "Help promises nonwriting preview."),
    (None, 59, 64, "Existence check followed by unconditional chmod."),
    (None, 132, 140, "Dry-run only guards later manifest writes.")],
    ["Missing script aborts before chmod.", "Already executable files may show no mode difference; nonexecutable trigger remains valid."])

add("0565", "Docker pins rust:1.80-alpine and builds the copied workspace. Workspace members declare edition 2024; official Rust release notes place stabilization at 1.85. Root also declares rust-version 1.89. Current manifests therefore exceed the builder toolchain. No Docker build, install or deployment was performed.", [
    (None, 6, 14, "Pinned builder copies workspace and runs Cargo."),
    ("Cargo.toml", 1, 20, "Workspace includes member globs; root rust-version is 1.89."),
    ("00_ABZU_KERNEL/crates/strike-rs/Cargo.toml", 1, 6, "Member edition 2024."),
    ("crates/cadt_mediator/Cargo.toml", 1, 6, "Member edition 2024.")],
    ["Selecting -p does not remove workspace manifest discovery.", "No toolchain upgrade appears before build."])

add("0536", "Every multiple of 50 takes the preceding modulo-10 branch, making the two-failure branch unreachable. quorum_poisoned_events cannot increment, but output certifies BFT stability after only a final RUNNING assertion. This is a test-coverage/reporting defect, not demonstrated consensus rejection failure.", [
    (None, 137, 160, "Branch order prevents two-node-failure execution."),
    (None, 161, 168, "Counter printed without coverage assertion; success certified.")],
    ["Single-failure and ordinary RUNNING assertions still execute.", "They do not substitute for unreachable POISONED assertion."])

add("0020", "On ordinary documented 64-bit C layout, AtomicU16 ends at offset 46, AtomicU32 aligns to 48 and ends at 52, then padding ends at 66. align(64) rounds size to 128, contradicting validate_alignment's size 64 assertion. Related Python example maps only 64 bytes. Scope is the standalone example, not canonical production manifest; no native compilation or mmap was run.", [
    (None, 1, 20, "Field order needs padding before ebr_ticket."),
    (None, 36, 44, "Validator asserts 64-byte size and describes ctypes mapping."),
    ("scripts/c5_demos/poc_shm_orchestrator.py", 11, 32, "Related example repeats fields and maps 64 bytes.")],
    ["align(64) cannot shrink 66 bytes of laid-out fields.", "Scoped symbol search did not establish production use of this example struct."])

add("0333", "Simulated validators always accept: sleep then True, or hash-expression or True. Timing consumers discard even those results, then claim surviving O(1) invariant and no deadlocks solely from speedup >50. Explicit simulator names do not justify final certification language. Confirmed issue is misleading demonstration evidence, not an actual ZK verifier defect.", [
    (None, 10, 30, "Always-true simulated validators and timing-only consumers."),
    (None, 65, 81, "Speedup condition controls invariant/deadlock claims; main runs benchmark.")],
    ["Function docstrings call the operations simulations.", "No real verifier or malformed-proof rejection is exercised."])

add("0588", "Module import creates audit directories. run_deskimming always truncates fixed deskimming_receipt.json regardless of dry_run; flag gates copying/chmod only. Preview can overwrite a prior real receipt despite CLI promise to simulate without writes. No operator brain directories or previous receipts were accessed.", [
    (None, 25, 31, "Import-time mkdir operations."),
    (None, 57, 78, "Dry-run gates copy/chmod only."),
    (None, 90, 115, "Unconditional receipt write and contradictory CLI promise.")],
    ["Missing source scripts change actions, not receipt write.", "A dry_run field labels the replacement but does not preserve prior evidence."])

add("0289", "Future exceptions are logged and omitted from result list; only successes increase completed count. Export contains only that filtered list with no failed claim or completeness status, then function announces successful closure and returns normally. Empty-input return is separate. No remote client or operator ledger was accessed.", [
    (None, 154, 177, "Per-future exceptions are swallowed without result record."),
    (None, 195, 218, "Filtered summary/export and unconditional successful closure."),
    (None, 259, 273, "CLI calls operation without checking missing task outcomes.")],
    ["Exceptions are logged, but not preserved in exported results.", "Offline fallback can handle ordinary failed responses, not exceptions bypassing it."])

add("0005", "Verifier checks only tracked worktree/index diffs. With untracked files alone both succeed and it prints repository clean and execution audited. Later log and last-commit hashing also omit untracked additions. Scope is inaccurate verifier output; no Git mutation was performed.", [
    (None, 5, 20, "No untracked status check before clean claim."),
    (None, 22, 34, "Only prior-commit paths hashed before final audit claim.")],
    ["Tracked or staged differences correctly fail.", "set -e catches command failures, not untracked files invisible to diff."])

add("0550", "Cubing mesh_n occurs in usize before f64 conversion without a bound. On 64-bit targets 4194304 cubed is 2^66, overflowing usize: checked arithmetic panics, unchecked arithmetic wraps to zero and returns the wrong floor. Module is public; inspected example uses a small mesh, so large-input production reachability is not established.", [
    (None, 36, 46, "Unchecked integer cube before floating cast."),
    ("src/lib.rs", 99, 99, "Public module export."),
    ("examples/omega_100_synthesis.rs", 74, 91, "Consumer uses floor and asserts only positivity.")],
    ["Small input meshes do not overflow.", "Function exposes no validation or checked multiplication."])

add("0190", "Example labels a single gte comparison as starts-with. Later unrelated paths docs/zzz/ and private/ satisfy the same lower bound. Official current Cloudflare filtering docs require lower and upper range bounds for folder prefix. Confirmed scope is documentation/retrieval example, not tenant authorization; no service query was executed.", [
    (None, 10, 13, "Prefix claim has only lower bound."),
    ("tools/skill_library/codex_overrides/cloudflare/references/ai-search/README.md", 118, 132, "Reference index routes consumers to gotchas.")],
    ["No tenant boundary behavior demonstrated.", "Filter syntax can vary by API version; missing upper bound remains corroborated by official semantics."])

add("0022", "Current AST-selected rhythm functions generated exactly the same 48 notes and attributes for mode 0 and 1 using synthetic in-memory Score/Note objects. Mode is never read and both layers scale to BAR, despite UI forwarding selection. Missing functionality reproduced without loading FL Studio or calling an app.", [
    (None, 51, 69, "Two mode UI choices and mode argument."),
    (None, 71, 108, "Fixed BAR scaling; apply forwards unused mode.")],
    ["Host-module availability gates dialog but does not add generator mode logic.", "Fixture verifies note computation only, not app integration."], "REPRODUCED")

add("0302", "Documented scanner executed on a tiny synthetic archive returns a closed stream; documented seek then raises ValueError: seek of closed file. Returning inside with open closes the stream before caller use. This reproduces example lifecycle failure independently of full ASAR-format correctness; no application archive was opened.", [
    (None, 37, 58, "Returns file handle from within context manager."),
    (None, 132, 141, "Documented consumer seeks/reads returned stream.")],
    ["Malformed headers may fail earlier.", "Valid synthetic header reaches return; consumer never reopens file."], "REPRODUCED")

add("0174", "Direct inspection of synthetic HTML text-[17px] reports C5-UI-002, but directory audit of the same file under build-review/src returns no findings. Ignore logic searches substrings of full ancestor path. main treats empty findings as compliant without scanned-file coverage. Isolated pure source execution reproduces the missed lint coverage.", [
    (None, 92, 101, "Fixture violates font-size rule."),
    (None, 123, 138, "Full-path substring match skips tree."),
    (None, 146, 159, "Existing path plus no findings produces compliance/exit zero.")],
    ["Direct file audit bypasses directory exclusion and catches violation.", "Intended build-output exclusions overmatch arbitrary ancestor components."], "REPRODUCED")

assert len(ROWS) == 29 and {r["candidate_id"] for r in ROWS} == set(BY_ID)
sources = {}
for row in ROWS:
    for c in row["source_checks"]:
        raw = (ROOT / c["path"]).read_bytes()
        lines = raw.decode().splitlines()
        assert 1 <= c["start_line"] <= c["end_line"] <= len(lines), c
        entry = sources.setdefault(c["path"], {"sha256": hashlib.sha256(raw).hexdigest(), "ranges": []})
        span = {"start_line": c["start_line"], "end_line": c["end_line"], "text": "\n".join(lines[c["start_line"]-1:c["end_line"]])}
        if span not in entry["ranges"]:
            entry["ranges"].append(span)

evidence = {
    "reviewer": "17",
    "scope": "Current working tree; bounded static inspection and four isolated pure Python reproductions. No product source edits, native product execution, operator data access, deployment, or remote mutation.",
    "graph_availability": "Native session exposed no codebase-memory/search_graph/index_repository tool. Used scoped rg and source reads. Missing guessed test/example directories were not treated as absence proof.",
    "sources": sources,
    "assignment_hash_comparison": {r["candidate_id"]: {"assignment_sha256": BY_ID[r["candidate_id"]]["source_sha256"], "current_sha256": r["current_source_sha256"], "unchanged": BY_ID[r["candidate_id"]]["source_sha256"] == r["current_source_sha256"]} for r in ROWS},
    "external_documentation": [
        {"tool": "Context7 resolve_library_id then query_docs", "library_id": "/websites/developers_cloudflare_ai-search", "url": "https://developers.cloudflare.com/ai-search/configuration/retrieval/filtering", "candidate_id": "SW100-C0190", "observation": "Official prefix filter uses both gte and lt bounds to exclude lexically later unrelated folders."},
        {"tool": "Context7 resolve_library_id then query_docs", "library_id": "/rust-lang/rust", "url": "https://github.com/rust-lang/rust/blob/main/RELEASES.md", "candidate_id": "SW100-C0565", "observation": "Rust 1.85.0 release dated 2025-02-20 stabilized the 2024 edition."},
    ],
}
(BASE / "17-source-evidence.json").write_text(json.dumps(evidence, indent=2, ensure_ascii=False) + "\n")
(BASE / "reviews/17.json").write_text(json.dumps({"reviewer": "17", "candidates": ROWS}, indent=2, ensure_ascii=False) + "\n")
print(json.dumps({"candidates": len(ROWS), "source_files": len(sources), "decisions": {d: sum(r["decision"] == d for r in ROWS) for d in sorted({r["decision"] for r in ROWS})}}))
