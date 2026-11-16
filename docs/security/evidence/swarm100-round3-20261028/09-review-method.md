# Review 09 evidence and scope

Expected result: adjudicate the 29 exact candidate IDs in `assignments/09.json` against current source. Allowed writes: `reviews/09.json` and `09-` evidence files in this directory. Preserve the existing dirty worktree on `main`; no production edits, protected or native execution, deployments, remote mutations, or operator-data access.

Acceptance: 29 unique assigned IDs, required decision fields, concrete current-source ranges, SHA-256 of each cited primary file, explicit guard analysis, and JSON schema/coverage validation. Hash equality alone is not an adjudication.

Codebase-memory graph tools were not exposed in the native session tool inventory. Discovery therefore used bounded source reads and targeted `rg`. All 29 primary files were read, along with relevant producer, consumer, fixture, import and guard code. No claim is made about deployed reachability or native behavior.

## Rejected candidate SW100-C0361

The generated source opens `namespace Babylon60.Oncology` and does not emit an explicit `end`. That is valid namespace termination at end of a Lean file. The [official Lean reference, Namespaces and Sections](https://lean-lang.org/doc/reference/latest/Namespaces-and-Sections/) explicitly permits omitting the terminator at EOF. Consulted 2026-10-28. Context7 resolution to `/leanprover/lean4` succeeded, but its focused query returned an unrelated LSP excerpt; the official reference supplied the relevant language rule. No Lean compiler was executed. This rejection does not certify the whole generated module or refute the separate inconsistent axiom in SW100-C0360.

## Narrowed candidate SW100-C0398

Current `src/secure_fs.rs:2057-2064` rejects the compatibility `secure_delete` API with `MissingAuthorization`. Therefore the original one-worker/one-iteration trigger cannot produce the claimed successful deletion now. The acceptance defect remains for two workers and two total iterations: both workers execute only iteration zero, worker one takes the direct `NativeSecureFs::secure_mutate` branch, and any successful clean mutation satisfies the pass predicate without an attack against that backend. This is static control-flow evidence, not an observed native run. The separate naive baseline always attempts attacks; its result is not required by the verdict.

## Isolated Python probes

`python3 docs/security/evidence/swarm100-round3-20261028/09-source-probes.py`

The script extracts named current AST definitions without importing the application. It runs the pure failover demonstration, and routes the scaffolder writer into memory before parsing the generated source. It invokes no native kernel, database, server, synthesis, or network operation.

- SW100-C0234: all three simulated tiers down returned `RESOLVED` / `Tier1:Antigravity`; the `calls_resolved` counter remained zero.
- SW100-C0106: a description containing a triple-quote sequence returned a successful generated-artifact path, but `ast.parse` rejected the captured artifact with an unterminated triple-quoted string.

The two records set `runtime_executed: true` only for these isolated Python probes. All other records are static. Protected runtime execution is false throughout this review.

Workspace-wide semantic, token-budget and topology checks belong to the coordinating audit; this review validates its restricted JSON/evidence outputs and does not claim global gates or runtime certification.
