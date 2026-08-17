# PROVENANCE_LOCK.md — Frozen Data Provenance & Custody Lock (LOCK-11)

> **STATUS: FROZEN / NORMATIVE**  
> **Repository**: `borjamoskv/teorema-robinson-moskv`  
> **Lock Identifier**: LOCK-11  

This document specifies the cryptographic provenance rules governing all raw experimental outputs, trace files, and benchmark evaluations within the Teorema Robinson-Moskv framework.

---

## 1. Frozen Provenance Schema

```yaml
provenance_lock:
  version: "1.0.0"
  required_fields:
    - datum_id
    - timestamp_iso8601_utc
    - raw_payload_sha256
    - environment_hash
    - generator_identity
  cryptographic_custody:
    hash_algorithm: "SHA-256"
    merkle_tree_root_required: true
    append_only_enforced: true
```

---

## 2. Provenance Standards

1. **Origin Attestation**: Every raw experimental output must include a deterministic payload hash `raw_payload_sha256 = SHA256(raw_bytes)` and a unique UUIDv4 `datum_id`.
2. **Timestamp Monotonicity**: Timestamps must be recorded in ISO 8601 UTC format (`YYYY-MM-DDTHH:MM:SSZ`) and adhere strictly to monotonic sequence ordering.
3. **Merkle Custody Chain**: Individual trace records must be linked into an append-only Merkle tree structure where each block header includes the hash of the preceding block:
   $$H_k = \text{SHA256}(H_{k-1} \parallel \text{Payload}_k)$$

---

## 3. Epistemic Violation Rules

- Any raw dataset item lacking a verifiable `raw_payload_sha256` or exhibiting broken Merkle sequence hashes is **REJECTED** from benchmark aggregation.
