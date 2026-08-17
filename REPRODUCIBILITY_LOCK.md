# REPRODUCIBILITY_LOCK.md — Frozen Environment & Provenance Manifest

> **STATUS: FROZEN / NORMATIVE**  
> **Repository**: `borjamoskv/teorema-robinson-moskv`  

This document specifies the exact environment specifications and cryptographic provenance pipeline required for 100% reproducible execution of experiments within the Teorema Robinson-Moskv repository.

---

## 1. Frozen Environment Lock Manifest

```yaml
environment:
  python: "3.11.10"
  lean: "4.13.0"
  lake: "4.13.0"
  rust: "1.82.0"
  compiler: "clang-1600.0.26.4"
  os: "Darwin 24.0.0 arm64"
  cpu: "Apple M Series / x86_64 deterministic execution"
  model: "claude-3-5-sonnet-20241022"
  model_revision: "rev_20241022_v1"
  dependencies_lock: "uv.lock:SHA256 / Cargo.lock:SHA256"
  git_commit: "GIT_SHA_AT_RUN_EXECUTION"
  benchmark_commit: "BENCHMARK_SHA_AT_RUN_EXECUTION"
```

---

## 2. Immutable Provenance Pipeline Chain

Every experimental run must produce a cryptographic attestation manifest linking all execution inputs to the resulting output hashes:

```text
               +-----------------------------------+
               |           experiment_id           |
               +-----------------------------------+
                                 |
                                 v
               +-----------------------------------+
               |              git SHA              |
               +-----------------------------------+
                                 |
                                 v
               +-----------------------------------+
               |          toolchain hash           |
               +-----------------------------------+
                                 |
                                 v
               +-----------------------------------+
               |           dataset hash            |
               +-----------------------------------+
                                 |
                                 v
               +-----------------------------------+
               |            prompt hash            |
               +-----------------------------------+
                                 |
                                 v
               +-----------------------------------+
               |            result hash            |
               +-----------------------------------+
```

---

## 3. Cryptographic Lock Verification Algorithm

To verify experimental integrity post-execution:

1. Re-compute `SHA256(toolchain_config \parallel dependencies_lock \parallel git_commit)`.
2. Ensure `result_hash == SHA256(canonical_traces_json \parallel metrics_summary_json)`.
3. If any hash mismatch occurs along the chain, the experimental run is flagged as **COMPROMISED** and rejected from official benchmark registries.
