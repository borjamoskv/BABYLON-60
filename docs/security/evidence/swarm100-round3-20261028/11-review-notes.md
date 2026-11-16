# Round 3 — reviewer 11

Review date: 2026-10-28. Scope: the 29 exact candidate IDs in [assignment 11](assignments/11.json).

The result is [reviews/11.json](reviews/11.json): 23 `CONFIRMED_STATIC` and 6 `REPRODUCED`. There are 28 `OPEN` findings and one `MITIGATED` finding. **None is certified fixed.** C0185 is only partially mitigated: same-file add/revoke operations now share a transaction, while separate-file ledgers and attribution retraction retain independent commits.

The task contract limited changes to this review and `11-` evidence files. Product source, dependencies and lockfiles were preserved. The working branch was `main` with pre-existing changes. No native kernel/oracle, server, deployed service, remote mutation, operator dataset, hardware attestation, or actual host triage was executed. No additional agents were launched.

Source discovery used bounded `rg` and source reads because no native codebase-memory graph tools were exposed in the session. Related guards and consumers were checked, including ledger transaction ownership, MCP read-only mediation, IFC evaluation, the Python C ABI wrapper, and repository-health scoring. This is scoped source review; unsuccessful scoped searches do not prove global absence of consumers. The shared-manifest workspace mirror was compared byte-for-byte and matched.

[Source-check snapshots](11-source-checks.json) preserve 94 line ranges and their file hashes. `current_source_sha256` in every review entry is the hash of the actual current primary file, rather than the earlier assignment hash. Governance changed since assignment and was reviewed in its current form. The final [validation record](11-validation.json) checks exact ID coverage, required fields, source hashes and line ranges.

Six isolated source/stdlib fixtures were run with:

```sh
python3 docs/security/evidence/swarm100-round3-20261028/11-fixtures.py
ruff check docs/security/evidence/swarm100-round3-20261028/11-fixtures.py
```

[Fixture source](11-fixtures.py) and [results](11-fixtures.json) record the scope of each reproduction. The tested cases are the depth-limited SQL closure, optimized Python acceptance statement, lexical SQLite expiry comparison, MCP parser/limit-conversion methods, version synchronization in a temporary synthetic repository, and the bounded query-generation loop. All six completed with their expected observations. Ruff passed. The first fixture-harness attempt failed because it placed a duplicate future import after a source docstring; the harness was corrected before the successful run.

For these six entries, `runtime_executed: true` means only the explicitly described isolated fixture ran. It does not mean the complete production component, protected runtime, concurrency stress test, biological model, legal approval process, Cloudflare deployment, or crash-recovery scenario ran. The MCP process-exit consequence is static inference from the uncaught path; the fixture reproduced the originating exceptions.

C0317, C0579 and C0447 were scoped to P2 because the established defects concern documentation examples or a benchmark, without evidence of production deployment/service impact. All other severities retain the assigned level. No duplicate or already-fixed classification was inferred merely from similar text or changed hashes.

Repository-wide semantic, token-budget and topology checks are left to the parent review's consolidated closing checks to avoid concurrent duplicate audits. This reviewer ran only its isolated fixtures, Ruff and the review schema/hash validator. Global configuration and operator telemetry were excluded.
