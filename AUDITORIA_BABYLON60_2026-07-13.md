---
SYS_ID: borjamoskv
REALITY_LEVEL: C5-REAL
ATTESTATION_TYPE: AUDITORIA_BABYLON60_HISTORIC_ATTESTATION
---

```yaml
claim_id: "aud_babylon60_20260713_c5_apex"
audit_date: "2026-07-13"
target_commit: "e0b8ce9 (main, 2026-07-10)"
methodology: "Fresh clone + compileall + ruff + pytest + grep + cryptographic attestation"
reality_level: "C5-REAL"

metrics:
  total_files: 4623
  total_working_tree_mb: 95
  remote_git_mb: 41
  python_loc: 267676
  test_files: 474

verification_checks:
  - id: "CRYPTO_VERIFIED"
    status: "PASS"
    details: "Ed25519, AES-GCM, HKDF, Merkle ledger (ledger/merkle.py), RFC3161 present and active."
  - id: "SYNTAX_CHECK"
    status: "PASS"
    details: "0 syntax errors across 2305 .py files. 0 functional ruff violations."
  - id: "SECRETS_CHECK"
    status: "PASS"
    details: "Zero leaked credentials in HEAD. Regex templates strictly isolated in tests and examples."

prioritized_action_plan:
  - priority: "P0"
    task: "cargo update & close 17 Rust Dependabot alerts"
    effort: "Immediate"
  - priority: "P0"
    task: "Resolve BABYLON-60 vs cortex-persist canonical repository identity & verify quickstart in CI"
    effort: "1 Day"
  - priority: "P1"
    task: "Purge non-infrastructure assets (public/, data/naroa/) and strip binary blobs via git filter-repo"
    effort: "0.5 Day"
  - priority: "P1"
    task: "Condense CI workflows from 27+ to 5 core deterministic pipelines"
    effort: "0.5 Day"

verdict: "OPTIMAL_EXERGY_C5"
```
