# EXECUTION_LOCK.md — Frozen Code Execution Attestation (LOCK-12)

> **STATUS: FROZEN / NORMATIVE**  
> **Repository**: `borjamoskv/teorema-robinson-moskv`  
> **Lock Identifier**: LOCK-12  

This document specifies the execution attestation requirements binding benchmark results to the exact source code commit and binary build.

---

## 1. Frozen Execution Schema

```yaml
execution_lock:
  version: "1.0.0"
  git_commit_sha_required: true
  git_dirty_allowed: false
  binary_build_hash_required: true
  entrypoint_script_hash_required: true
```

---

## 2. Execution Binding Rules

1. **Clean Repository Enforced (`git_dirty: false`)**: Benchmark runs executed on uncommitted code or dirty working trees are invalid and rejected from official results.
2. **Execution Attestation Bundle**: Each benchmark output bundle must contain an execution manifest linking:
   - `git_commit_sha`: Exact 40-character hex commit digest.
   - `binary_hash`: SHA-256 digest of compiled native binaries (e.g. Rust static core).
   - `entrypoint_hash`: SHA-256 digest of execution entrypoint (e.g., `LUNA_SOL_GAP_BENCHMARK/run.py`).
