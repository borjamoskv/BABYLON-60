"""Create the reviewer-owned adjudication and immutable source excerpts."""
import hashlib
import json
from pathlib import Path

BASE = Path(__file__).absolute().parent
ROOT = BASE.parents[3]
assignments = json.loads((BASE / "assignments/15.json").read_text())
by_id = {item["candidate_id"]: item for item in assignments}
reviews = {}


def add(number, rationale, checks, guards, decision="CONFIRMED_STATIC", severity=None):
    candidate_id = "SW100-C" + number
    original = by_id[candidate_id]
    normalized = []
    for path, first, last, observation in checks:
        normalized.append({"path": path or original["path"], "start_line": first,
                           "end_line": last, "observation": observation})
    reproduced = decision == "REPRODUCED"
    reviews[candidate_id] = {
        "candidate_id": candidate_id, "decision": decision,
        "severity": severity or original["severity"],
        "remediation_state": "UNKNOWN" if decision == "NEEDS_VALIDATION" else "OPEN",
        "path": original["path"],
        "current_source_sha256": hashlib.sha256((ROOT / original["path"]).read_bytes()).hexdigest(),
        "rationale": rationale, "source_checks": normalized, "guards": guards,
        "runtime_executed": reproduced,
        "evidence_paths": [str((BASE / "15-source-evidence.json").relative_to(ROOT))]
        + ([str((BASE / "15-pure-checks.py").relative_to(ROOT)),
            str((BASE / "15-pure-checks.json").relative_to(ROOT))] if reproduced else [])}


add("0367", "Confirmed in the current CLI: successful license checks unconditionally print ANSI human text before Attest selects Json or Scitt serialization. A successful JSON command therefore emits a prefix plus a document, not one JSON document. No ledger command was executed.",
    [(None,143,178,"Active and evaluation-success branches use println! on stdout."),
     (None,201,205,"Attest invokes license enforcement before reading format."),
     (None,227,243,"Json/Scitt print JSON to that same stdout.")],
    ["License failure exits nonzero; this does not protect successful machine-readable output."])
add("0368", "Confirmed serial AF_UNIX request handling: after accepting a matching UID, read blocks before another connection can be accepted. An idle permitted client can stall all later requests. This is a local same-UID availability flaw, not a remotely reachable unauthenticated server claim.",
    [(None,386,419,"UID check and socket 0600 precede a serial blocking stream.read."),
     (None,501,509,"Response write and loop iteration are also synchronous; no worker dispatch.")],
    ["Unix socket permissions and peer UID restriction narrow the attacker to permitted local clients.",
     "Scoped search of this main.rs found no read timeout, nonblocking mode or thread dispatch."])
add("0369", "Confirmed license-policy inconsistency. CLI Attest checks quota/expiry; Serve enters without that gate, and authorized JSON POST calls append_event directly. append_event only constructs and writes the block. A valid configured bearer token can therefore be used with an exhausted/expired license. No server, request or ledger mutation was executed.",
    [(None,143,178,"CLI license policy rejects exhausted, expired and invalid licenses."),
     (None,361,365,"Serve starts without enforce_license_policy."),
     (None,436,491,"Token comparison and object JSON validation lead directly to append_event."),
     ("crates/babylon-attest/src/ledger.rs",120,168,"Append implementation contains no license enforcement.")],
    ["Same-UID peer check, socket 0600, configured nonempty token and JSON-object requirement remain effective.",
     "GET /status reports license status but reporting is not write authorization."])
add("0055", "Confirmed at the public PyO3 boundary: unrecognized obligation strings are discarded, and an all-unrecognized list becomes empty and verifies true. The current Autodidact caller supplies enum values and first performs Python verification, so this finding is limited to direct API callers or future free-form inputs; it does not establish bypass through that guarded caller.",
    [(None,154,182,"Wildcard obligation match ignores unknown strings and invokes omega0::verify."),
     ("00_ABZU_KERNEL/crates/strike-rs/src/omega0.rs",133,145,"Empty obligation lists return true."),
     ("01_KISH_ENGINE/babylon60/autodidact/engine.py",89,104,"Existing consumer verifies first and converts enum obligations to their values.")],
    ["Invalid modality is rejected.", "Existing Autodidact consumer supplies typed obligation values; public binding still accepts Vec<String>."])
add("0056", "Confirmed that verify_statement_content cannot consult recorded contradictions: it calls omega0::verify, which explicitly creates an empty nogoods set. contradict_knowledge writes both ledger nogoods and ATMS state, but neither is read by this method. The observed Python consumer has its own nogoods verification, so no end-to-end protected authorization bypass is claimed.",
    [(None,94,118,"contradict_knowledge persists and installs the contradiction."),
     (None,154,182,"Verification never uses self.atms or self.ledger."),
     ("00_ABZU_KERNEL/crates/strike-rs/src/omega0.rs",133,154,"Wrapper supplies empty set; Contradiction only tests set membership."),
     ("01_KISH_ENGINE/babylon60/autodidact/engine.py",96,104,"Python consumer rejects against its own falsifier nogoods first.")],
    ["The separate is_believed method reads ATMS, but verify_statement_content does not call it.",
     "Confirmed API correctness flaw; guarded consumer lowers demonstrated reachability."])
add("0243", "Reproduced using the actual transformer and transmute_file on a newly created temporary file. A function containing only a docstring was written back as 'def f():' and failed compilation with IndentationError. Only the temporary specimen was changed; no generated code or kill handler ran.",
    [(None,16,19,"Every constant-expression statement is removed."),
     (None,79,87,"Unparsed AST is written without inserting pass or parsing output."),
     (None,90,100,"CLI feeds requested paths directly to transmute_file.")],
    ["Original ast.parse validates only input.", "CLI exception handling cannot detect a syntactically invalid output when ast.unparse succeeds."], "REPRODUCED")
add("0244", "Reproduced the actual AST transformation on input importing os as operating and signal as sig. The resulting module retained only those aliases but injected os.kill(os.getpid(), signal.SIGKILL). The missing bare bindings are therefore present in emitted code; the dangerous handler was never executed.",
    [(None,21,49,"Broad handlers are replaced using bare os and signal names."),
     (None,52,75,"Import detection uses alias.name and suppresses required bare imports even when asname is different.")],
    ["Module-level import scan recognizes normal bare imports and future-import placement.", "No output binding-resolution or execution validation exists."], "REPRODUCED")
add("0310", "Confirmed EOF loop: read_line returning Ok(0) passes the is_err check, eval_line returns an empty string, and the next iteration prints another prompt without terminating. The CLI Repl branch directly invokes this loop. Native binary execution was intentionally omitted.",
    [(None,30,34,"Empty input yields an empty response, not EXIT."),
     (None,159,183,"Only read errors or literal EXIT terminate; Ok(0) is ignored."),
     ("crates/b60-lang/src/main.rs",267,269,"CLI Repl invokes run_interactive.")],
    ["Explicit quit/exit and IO errors break the loop; stdin EOF is neither."])
add("0311", "Confirmed unchecked u64 arithmetic for accepted operands. For example s1=u64::MAX, s2=1, f1=f2=0 reaches s1+s2; f1=u64::MAX and f2=1 overflows even earlier. Depending on overflow-check build settings this panics or wraps; no correct overflow error is returned. No native runtime was executed.",
    [(None,51,64,"All four operands parse as u64 and are added without checked_add or bounds."),
     (None,39,40,"Help advertises exact Q60 addition."),
     ("crates/b60-lang/src/main.rs",267,269,"REPL is a CLI-accessible path.")],
    ["Token count and operation name are checked; neither constrains accepted numeric range.", "Invalid parses default to zero but valid maximal u64 parses remain accepted."])
add("0413", "Confirmed fail-open scanner prerequisite: absence of gitleaks only emits a warning and execution proceeds toward the push after other checks and biometric authorization. This contradicts the script's claimed strict zero-finding scan. No secret, leak or publication was observed; no publication script was run.",
    [(None,8,12,"Header declares strict Gitleaks scanning as a verified invariant."),
     (None,82,93,"Missing scanner only warns; scanner failures when installed do abort."),
     (None,107,145,"Biometric gate and remote handling lead to git push without another scan.")],
    ["Non-dry tracked cleanliness, forbidden extensions and archive-size gates can block a run.",
     "Biometric gate is mandatory for push but does not inspect tree secrets.", "Claim is conditional on earlier gates passing; current workspace was not published."])
add("0414", "The ref mutation is confirmed, but the defect classification needs a product contract decision: line 23 explicitly defines DRY-RUN as checking without git push, and lines 101-105 plus 130 deliberately prepare and advertise a local release branch. Thus local ref changes do not contradict the inspected documented mode. Overwriting an existing release tip may still be undesirable; preserve-ref requirements or an agreed no-mutation preview contract are needed before certifying this as a bug. No Git mutation was executed.",
    [(None,19,24,"DRY-RUN is explicitly described as omitting git push."),
     (None,101,105,"commit-tree and branch -f intentionally prepare the named local release branch."),
     (None,126,132,"Dry-run exit reports that local branch as ready.")],
    ["Dry-run exits before remote lookup/push and skips biometric dispatch.",
     "Earlier tree/content gates can abort before branch creation.", "Existing-branch overwrite has no preservation guard, but intended preview semantics remain unresolved."], "NEEDS_VALIDATION")
add("0387", "Confirmed destructive WAL selection: every regular *.db-wal and *.db-shm below the workspace, outside three substring exclusions, is unlinked in ordinary mode. There is no base-database, open-connection or checkpoint check; CANONICAL_PROTECTED_DIRS is declared but unused. This can remove committed uncheckpointed database data. No purge or database operation was run.",
    [(None,39,53,"Protected directories are declared."),
     (None,178,190,"WAL/SHM deletion depends only on suffix, is_file and dry_run."),
     (None,241,258,"CLI defaults to destructive mode unless --dry-run is present.")],
    [".venv, node_modules and .git substring exclusions narrow traversal but do not establish orphan status.",
     "--dry-run prevents unlink; it is not the default."])
add("0388", "Confirmed cross-workspace state mutation: purge_anergy derives the conversation database from Path.home, not its workspace argument, and updates every RUNNING or not_fully_idle row. It does not establish that a chat is stale or belongs to this workspace. Static review only; the operator's database was neither inspected nor opened.",
    [(None,67,67,"Function takes workspace_path and defaults dry_run to false."),
     (None,192,208,"Global home database selection and broad status predicate have no workspace/session filter."),
     (None,241,258,"Ordinary workspace CLI invocation reaches that same purge function.")],
    ["Database existence and nonzero matching count are checked.", "--dry-run suppresses UPDATE, but ordinary cleanup does not require explicit listener-reset selection."])
add("0346", "Reproduced with the current pure Python pool: a positive-weight opinion {yes:0.8,no:0.2} becomes {yes:0,no:1} when an agent with weight zero reports yes=0. Omitting that agent's weight has the same effect; removing the excluded agent restores yes=0.8. The veto runs before the zero weight can neutralize its contribution.",
    [(None,47,64,"Optional weights default uniformly only when no mapping is supplied."),
     (None,73,105,"Missing weights default zero, but nonpositive probability veto happens before multiplication."),
     (None,31,40,"Async wrapper forwards weights without filtering zero-weight opinions.")],
    ["Empty opinions return an empty distribution.", "Async mutex only serializes updates; it does not change the pooling rule."], "REPRODUCED")
add("0330", "Confirmed plaintext serialization and persistence within bootstrap_genesis: PKCS8 NoEncryption output is inserted verbatim into private_key_enc and committed. A targeted search of babylon60 located only the definition/internal generation call, so active production invocation and actual key exposure are unproven. This finding concerns the callable bootstrap API's storage behavior, not an observed leaked key.",
    [(None,24,40,"Ed25519 key is serialized as unencrypted PEM."),
     (None,43,65,"Empty-ledger guard leads to direct insertion of that PEM into private_key_enc."),
     (None,80,97,"Genesis and identity changes are committed together.")],
    ["Nonempty ledgers skip bootstrap.", "The caller supplies the SQLite connection; no encryption-at-rest contract or caller was established in the scoped package search."])
add("0209", "Confirmed arbiter-level false attestation: nonempty content/host plus derivation EXECUTION_RECEIPT, a runtime label and receipt digest 'b3:' satisfy the runtime scope branch. Integrity only checks that prefix; the claim defaults to minimum CLAIMED, and origin is true when no platform is requested. No receipt bytes, signature or content/runtime binding are verified. Package export exists, but no protected runtime consumer was located; this is not demonstrated deployment authorization bypass.",
    [(None,131,177,"Public envelope accepts receipt labels and verify_integrity only checks b3: prefix."),
     (None,179,203,"Presence of other labels promotes effective provenance level."),
     (None,270,275,"Claim minimum defaults to CLAIMED."),
     (None,311,339,"Only envelope integrity is checked; origin starts true for an unspecified platform."),
     (None,407,447,"Runtime guard requires presence/derivation and then returns ATTESTED."),
     ("01_KISH_ENGINE/babylon60/memory/__init__.py",30,40,"Evaluator is publicly imported by memory package.")],
    ["Missing receipt/runtime, wrong derivation, requested platform mismatch and optional expected-content mismatch reject/abstain.",
     "Those guards do not verify the supplied receipt digest's content or authenticity."])
add("0348", "Confirmed framing defect against the supported LSP Content-Type header: after Content-Length this parser discards exactly one line, so a subsequent Content-Type occupies the presumed delimiter slot. It then reads the blank-line bytes plus an incomplete JSON body and rejects parsing, leaving trailing bytes in the stream. Microsoft LSP base-protocol documentation confirms both headers are valid. No native server was launched.",
    [(None,28,64,"Parser reads one assumed delimiter line and then exactly content_length bytes; JSON failures continue.")],
    ["EOF is handled and invalid lengths/UTF-8/JSON are rejected.", "None of these validate the header terminator or consume all header lines."])
add("0522", "Confirmed process-status propagation error: when launchctl is spawned but exits nonzero, the installer only logs stderr and returns Ok. main returns that result directly for install, giving successful CLI termination despite activation failure. No service installation or launchctl command was run.",
    [(None,18,25,"Install CLI returns install_launchd_service result directly."),
     (None,197,225,"Spawn failure propagates via ?, but nonzero child exit falls through to Ok.")],
    ["File-write errors and command-spawn IO errors propagate as errors.", "The missing guard is specifically child status.success()==false."])
add("0495", "Confirmed an inadequate example oracle, not a demonstrated torn-read defect in the implementation. The stress reader calls snapshots valid whenever two floating fields are not NaN; it does not compare any fields to the published epoch. Final success asserts only zero counted NaNs and ignores valid/exhausted totals, so finite mixed/initial snapshots or no successful reads satisfy it. Native stress was not run.",
    [(None,370,397,"Reader counts only NaN energy/enstrophy as torn; RetryExhausted does not fail."),
     (None,402,415,"Writer publishes finite epoch-derived values that could be cross-checked."),
     (None,419,440,"Valid/exhausted totals are unused; final coherence claim depends only on zero torn count.")],
    ["Thread panics fail on join and NaN values fail the final assertion.", "These do not establish coherence or successful observation coverage."])
add("0598", "Confirmed example/evidence overclaim. The demo text claims real hardware authorization and fail-stop, while it derives operator identity from USER, uses fixed MOCK key/signature strings, hardcodes successful deletion and only prints the poisoned transition. Its SQLite tamper/hash exercise is real code but cannot establish the claimed biometric/dispatch/kernel guarantees. The demo was not executed.",
    [(None,3,19,"Header describes physical authorization, Secure Enclave signature and kernel transition."),
     (None,87,114,"Biometric output and ATTESTED identity are printed; fixed bytes and hardcoded effect replace those mechanisms."),
     (None,164,189,"Tamper mismatch prints a kernel transition and unconditional broad final proof claim.")],
    ["Names mock_tee_key/mock_der_sig and the demo filename indicate a demonstration internally.",
     "Rendered claims do not clearly delimit simulation; no production bypass is inferred."])
add("0320", "Confirmed verification-order gap in the stress demo: integrity audit completes after sequential runs but before ten concurrent installer calls. Those later results are only return-code booleans; the final idempotency/safety claim does not inspect final targets. No installer or home configuration was invoked or read; no actual concurrent corruption is claimed.",
    [(None,42,52,"Injection success means subprocess return code zero only."),
     (None,137,160,"Integrity audit precedes concurrent mutations, and final success checks only failures counts.")],
    ["Pre-concurrency integrity errors exit nonzero.", "Concurrent child errors also fail; successful but corrupt output is not checked afterward."])
add("0510", "Confirmed history-loss condition in the simulation ledger. The state digest excludes epoch, while state_hash is UNIQUE and persistence uses INSERT OR REPLACE. Repeating an identical state under a new epoch conflicts on that unique digest and replaces the earlier row. simulate_subnet_epochs passes each computed digest directly to persistence. No database or simulation was executed.",
    [(None,95,105,"Digest contains normalized ranks/trust/consensus/dividends, no epoch."),
     (None,147,179,"Schema declares UNIQUE state_hash and INSERT OR REPLACE commits the new epoch."),
     (None,203,208,"Each simulated epoch is persisted with that state digest.")],
    ["Epoch primary key prevents duplicate epoch identifiers but does not preserve distinct epochs sharing a state.", "Scope is this example ledger; no production consensus impact asserted."])
add("0261", "Confirmed path arithmetic at the committed location: SCRIPT_DIR is <repo>/scripts/c5_setup, so one dirname yields <repo>/scripts and the check seeks scripts/.agents. The missing directory merely skips copying, followed by an unconditional environment-ready message. No setup script or home directory mutation was executed.",
    [(None,20,27,"One dirname selects scripts as REPO_ROOT; missing .agents silently skips synchronization."),
     (None,29,42,"Subsequent command checks only warn and final readiness is unconditional.")],
    ["set -e stops unhandled shell failures, but a false if condition does not fail.", "Copy failures are also explicitly swallowed with || true."])
add("0569", "Reproduced the actual extraction/generation functions with 'Teorema 1: Every natural number equals zero'. Generated Lean theorem concludes only True by trivial; the input statement survives merely as a comment/name. The writer labels such output Formal Verification and an isomorphic bridge. This confirms an evidence-labeling defect; no Lean runtime or source rewrite was performed.",
    [(None,24,47,"Extractor retains theorem headings as strings."),
     (None,49,85,"Generator emits the same True proposition for every theorem/axiom."),
     (None,87,115,"Writer presents generated stubs as Verificación Formal/Puente Isomorfo.")],
    ["Script/header calls these stubs and --dry-run prevents writes.", "Those scaffold labels do not make the generated True theorem prove the extracted claim."], "REPRODUCED")
add("0377", "Confirmed conditional multi-writer logical race in the exported safe API. Starting from seq=0, writer A fetch_add gives 1 and writer B gives 2; a reader can observe stable even 2 while payload stores from either publication interleave. All payload fields are atomics, so this is inconsistent snapshot semantics, not evidence of Rust memory unsafety. Header declares SPMC and scoped src/tests/examples search found no active consumer, so severity is reduced to P2; production exposure is not established.",
    [(None,10,23,"Header assumes SPMC but public atomics and shared-reference API do not encode writer ownership."),
     (None,49,63,"publish increments seq without exclusion or an odd-sequence CAS guard."),
     (None,66,94,"read accepts equal even sequence surrounding payload reads."),
     ("src/lib.rs",113,114,"Module is publicly exported.")],
    ["SPMC is a documented single-writer assumption, under which this particular two-writer scenario is excluded.",
     "POISONED check and bounded read retries do not serialize writers.", "No native/concurrent test was run and no production caller was established."], severity="P2")
add("0137", "Confirmed grammar defect in the fenced example: onStart() is declared without async and contains await. After replacing the illustrative auth ellipsis with an ordinary object, the method still cannot parse as JavaScript/TypeScript. This is independent of the current Cloudflare MCP API behavior; no SDK claim or deployment was tested.",
    [(None,94,103,"Suggested reconnection example has synchronous onStart with await inside its body.")],
    ["The surrounding heading presents it as a solution, not an intentionally invalid example.", "The auth {...} placeholder is a separate illustrative abbreviation and does not remove the missing async."])
add("0546", "Reproduced a pure mathematical counterexample to the exact documented gain formula. For the below-Nyquist signal x(t)=1.2 sin(pi t/2+pi/4), integer sample peak is 0.848528 < the -1 dB ceiling 0.891251, so g=1; reconstructed true peak remains 1.2. The formula therefore guarantees neither -1 dBTP nor zero intersample saturation. Official ITU true-peak guidance supports reconstructing/oversampling for such measurement. No audio engine or device was executed.",
    [(None,449,455,"Discrete max(abs(x)) scalar ceiling is labeled True Peak and guarantees zero inter-sample saturation.")],
    ["Scalar attenuation bounds the supplied sample maxima.", "No reconstructed/oversampled peak measurement is specified in this procedure."], "REPRODUCED")
add("0281", "Confirmed fail-open documented shell example: curl failure is assigned without checking exit/HTTP status; empty or unrelated error-body responses yield no grep match and the else prints OK. The standalone snippet enables neither errexit nor a response-validation guard. No request, password or operator credential was used.",
    [(None,36,52,"curl -s result flows directly to grep; all absent matches print success.")],
    ["Nonempty matching suffix triggers the alert.", "There is no separate unavailable/error result, HTTP failure handling or range-response validation."])
add("0085", "Confirmed unimplemented self-contained wizard: the entire async createGroup body only logs a creation-in-progress message. Imports are unused fs/path; no Baileys client, network call or group creation exists. Nonempty arguments invoke that body and naturally finish successfully. This establishes a misleading executable stub, not an observed WhatsApp mutation; the script was not run.",
    [(None,1,15,"Complete file shows logging-only createGroup and direct invocation for any nonempty args.")],
    ["Empty arguments return usage and exit 1.", "A nonempty participant list has no implementation/error reporting path beyond the log."])

assert len(reviews) == 29 and set(reviews) == set(by_id)
result = {"reviewer": "15", "candidates": [reviews[item["candidate_id"]] for item in assignments]}
(BASE / "reviews").mkdir(exist_ok=True)
(BASE / "reviews/15.json").write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n")

sources = {}
for review in result["candidates"]:
    for check in review["source_checks"]:
        path = check["path"]
        full_path = ROOT / path
        raw = full_path.read_bytes()
        lines = raw.decode().splitlines()
        assert 1 <= check["start_line"] <= check["end_line"] <= len(lines), check
        key = f'{path}:{check["start_line"]}-{check["end_line"]}'
        sources[key] = {**check, "sha256": hashlib.sha256(raw).hexdigest(),
                        "excerpt": "\n".join(f"{i}: {lines[i-1]}" for i in range(check["start_line"], check["end_line"] + 1))}
evidence = {
    "reviewer": "15", "date": "2026-10-28", "repository": str(ROOT),
    "scope": "29 assigned candidates; static source/caller review and five isolated stdlib checks. No native protected runtime, operator data, service startup, remote mutation, deployment or product source edit.",
    "discovery": "No graph search/index tools exposed in ALL_TOOLS; scoped source reads and rg used. Current cited source hashes all match assignment hashes; matching hash itself was not treated as proof of correctness.",
    "external_references": [
        {"candidate_id": "SW100-C0348", "url": "https://github.com/microsoft/language-server-protocol/blob/gh-pages/_specifications/lsp/3.18/specification.md", "observation": "Microsoft base protocol supports required Content-Length and optional Content-Type, with CRLF separation after all header fields."},
        {"candidate_id": "SW100-C0546", "url": "https://www.itu.int/dms_pubrec/itu-r/rec/bs/R-REC-BS.1770-3-201208-S%21%21PDF-E.pdf", "observation": "ITU explains intersample reconstruction/oversampling for true-peak metering; analytic counterexample independently demonstrates the candidate formula defect."}],
    "scoped_searches": [
        "rg bootstrap_genesis|IdentityBootstrap in 01_KISH_ENGINE/babylon60: only definition and internal call found.",
        "rg evaluate_provenance_claim in 01_KISH_ENGINE/babylon60: definition and package export found; protected runtime consumer not established.",
        "rg AttestationContract|attestation_contract in src tests examples: definition and src/lib.rs export only.",
        "rg verify_statement_content in strike-rs and babylon60: definition plus Autodidact typed/guarded caller.",
        "rg read_timeout|nonblocking|thread::spawn in crates/babylon-attest/src/main.rs: none found.",
        "rg CANONICAL_PROTECTED_DIRS in anergy_purge.py: declaration only."],
    "source_checks": list(sources.values())}
(BASE / "15-source-evidence.json").write_text(json.dumps(evidence, indent=2, ensure_ascii=False) + "\n")
print(json.dumps({"reviewer": "15", "count": len(reviews), "decisions": {d: sum(r["decision"] == d for r in reviews.values()) for d in sorted({r["decision"] for r in reviews.values()})}}))
