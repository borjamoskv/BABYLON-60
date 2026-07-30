<!-- C5-REAL EXERGY CERTIFIED -->
# SECURITY MODEL — cortex-persist

## Scope

This document defines the **threat model**, **security boundaries**, and **explicit guarantees** of the cortex-persist ledger.

---

## What the Ledger Guarantees

| Property | Mechanism | What It Proves |
|:---|:---|:---|
| **Integrity** | BLAKE3 hash-chain | Entry content was not altered after write |
| **Provenance** | Causal taint + agent_id | Who wrote an entry and under what context |
| **Ordering** | Lamport clock + WAL journal | Writes are serialized and reproducible |
| **Non-duplication** | UUID v5 idempotency key | Same logical write cannot be inserted twice |
| **Temporal anchor** | Git Sentinel (local) | Entry existed before a given commit timestamp |

## What the Ledger Does NOT Guarantee

| Property | Why |
|:---|:---|
| **Semantic correctness** | A hash proves content was not changed — not that it was true |
| **Authorization** | The ledger records who wrote; it does not enforce who is allowed to write without an external auth layer |
| **Tamper-proof storage** | An attacker with write access to the filesystem can delete or replace the entire database file. Hash-chains only detect this after the fact |
| **Global consensus** | L1–L3 levels provide local consistency only. BFT (L4) is not production-ready |
| **Regulatory compliance** | This is not a certified audit trail for GDPR, SOC2, or PCI-DSS |

---

## Threat Model

### In-Scope Threats

| Threat | Mitigation |
|:---|:---|
| Silent bit-rot or accidental modification of historical entries | BLAKE3 chain breaks on read — detected at verification time |
| Duplicate write injection by a buggy agent | UUID v5 idempotency key rejects duplicates |
| Race condition between concurrent writers | Single-writer `asyncio.Queue` + WAL journal serializes all writes |
| SQLite lock contention | `busy_timeout=5000ms` + WAL mode prevents reader/writer deadlock |
| Partial write on process kill | WAL journal rolls back automatically on restart |
| Unattributed writes | `causal_taint` + `agent_id` mandatory on every entry |

### Out-of-Scope Threats

| Threat | Reason |
|:---|:---|
| Attacker with OS-level filesystem access | Full DB replacement bypasses hash-chain detection |
| Compromised cryptographic primitives (BLAKE3 / SHA3-256) | Outside scope of this system |
| Byzantine agents in distributed swarm | Requires L4 BFT — prototype only |
| Supply-chain compromise of dependencies | Standard Python packaging risks apply |

---

## Cryptographic Primitives

| Use | Algorithm | Status |
|:---|:---|:---|
| Entry hash-chain | BLAKE3 | Active (Python `blake3` or Rust `strike_rs`) |
| Receipt / audit hash | SHA3-256 | Active |
| Optional signing | Ed25519 via `pynacl` | Optional `[crypto]` extra |
| Password / key derivation | Argon2 via `argon2-cffi` | Optional `[crypto]` extra |
| Timestamp witness (external) | OpenTimestamps / BTC OP_RETURN | Research — not implemented |

---

## Integrity Verification

To verify the full chain from any stored ledger:

```python
from babylon60.bft.ledger_actor import verify_chain

result = verify_chain(db_path="master_ledger.db")
print(result)  # {"valid": True, "entries": 4821, "broken_at": None}
```

A broken chain returns the exact entry index and both the expected and actual hash values.

---

## Data Separation

- Each tenant/workspace uses an isolated `.db` file.
- No shared tables exist between tenants.
- The central `cortex.db` (if present from BABYLON-60 legacy) is **read-only** and must not be written to by agent SDK calls. Use sidecar databases (`nexus_anchors.db`, `master_ledger.db`) for all mutations.

---

## Reporting Security Issues

Security vulnerabilities should be reported privately to the repository owner via the contact information in `SECURITY.md`. Do not open public issues for unpatched vulnerabilities.
