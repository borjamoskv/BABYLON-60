# ENVIRONMENT_LOCK.md — Frozen Hardware & Software Environment Lock (LOCK-13)

> **STATUS: FROZEN / NORMATIVE**  
> **Repository**: `borjamoskv/teorema-robinson-moskv`  
> **Lock Identifier**: LOCK-13  

This document formalizes the environment lock requirements ensuring complete software stack, hardware instruction set, and dependency lockfile identification.

---

## 1. Frozen Environment Pinning Schema

```yaml
environment_lock:
  version: "1.0.0"
  software_stack:
    python: "3.11.10"
    lean4: "4.13.0"
    lake: "4.13.0"
    rust: "1.82.0"
  lockfiles:
    uv_lock: "uv.lock"
    cargo_lock: "Cargo.lock"
  hardware_spec:
    os: "Darwin 24.0.0"
    arch: "arm64"
```

---

## 2. Environment Verification Protocol

1. **Dependency Lock Compliance**: SHA-256 digests of `uv.lock` and `Cargo.lock` must be verified prior to launching benchmark runs.
2. **Toolchain Version Match**: Python, Lean 4, and Rust versions must match the pinned versions exactly; unexpected toolchain updates invalidate benchmark reproducibility.
