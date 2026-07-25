# SECURITY MODEL — cortex-persist (SOTA 2026 Overhaul)

## Scope

This document defines the **threat model**, **security boundaries**, **SOTA vulnerability taxonomy**, and **explicit guarantees** of the cortex-persist and BABYLON-60 ledgers.

---

## What the Ledger Guarantees

| Property | Mechanism | What It Proves |
|:---|:---|:---|
| **Integrity** | BLAKE3 hash-chain | Entry content was not altered after write |
| **Provenance** | Causal taint + agent_id | Who wrote an entry and under what context |
| **Ordering** | Lamport clock + WAL journal | Writes are serialized and reproducible |
| **Non-duplication** | UUID v5 idempotency key | Same logical write cannot be inserted twice |
| **Temporal anchor** | Git Sentinel (local) | Entry existed before a given commit timestamp |
| **Sandboxed AST Safety** | `babylon60.guards.ast_sandbox` | Code execution payloads are free of dunder traversal and introspection exploits |
| **Smart Contract Locking** | EIP-1153 Transient Storage (`tstore`/`tload`) | EVM transactions are protected against reentrancy callbacks |
| **BFT Determinism** | IEEE 754 Float Exclusion (`INV_C5_18`) | Ledger state payloads use exact integer/canonical CBOR types |

---

## What the Ledger Does NOT Guarantee

| Property | Why |
|:---|:---|
| **Semantic correctness** | A hash proves content was not changed — not that it was true |
| **Authorization** | The ledger records who wrote; it does not enforce who is allowed to write without an external auth layer |
| **Tamper-proof storage** | An attacker with physical write access to the filesystem can replace the database file. Hash-chains detect this post-hoc |
| **Global consensus** | L1–L3 levels provide local consistency. BFT (L4) requires multi-node validator consensus |
| **Regulatory compliance** | This is a sovereign technical ledger, not a certified SOC2/GDPR compliance suite |

---

## Enhanced SOTA 2026 Threat Model

### In-Scope Threats & Hardened Mitigations

| Threat Vector | Mitigation Strategy | Physical Execution Invariant |
|:---|:---|:---|
| Silent bit-rot or historical manipulation | BLAKE3 chain verification breaks on read | `INV_C5_01` (Cryptographic Truth) |
| Duplicate write injection | UUID v5 idempotency key rejects duplicates silently | `INV_BFT_04` (Idempotency Key) |
| Concurrent writer race conditions | Single-writer `asyncio.Queue` + WAL journal serialization | `INV_BFT_02` (Async WAL Mode) |
| SQLite lock contention & deadlocks | `busy_timeout=5000ms` + WAL mode on all connections | `INV_BFT_02` |
| AST Sandbox evasion & introspection | `babylon60.guards.ast_sandbox` static AST verification | AST Sandbox Guard |
| EVM cross-function reentrancy | EIP-1153 `tload`/`tstore` transient locks | `INV_C5_08` (Transient Storage) |
| PyNaCl key attribute leakage | Explicit byte serialization (`bytes(sk)`) | `INV_C5_10` (PyNaCl Serialization) |
| Sandboxed Git commit failures | Autonomous `-c commit.gpgsign=false` fallback | `INV_C5_24` (Git Signature Fallback) |
| Process reward hacking / LLM slop | GELABP Exergy Score evaluation ($S \ge 700.0/1000.0$) | `INV_C5_14` (Exergy Matrix) |

---

## Cryptographic Primitives & Standards

| Purpose | Algorithm / Standard | Status / Implementation |
|:---|:---|:---|
| Entry Hash-Chain | BLAKE3 | Active (`blake3` / Rust `strike_rs`) |
| Audit Verification | SHA3-256 | Active |
| Signature Verification | Ed25519 via PyNaCl | Active (`bytes(sk)` serialized) |
| Smart Contract Transient Locking | EIP-1153 (`tstore`/`tload`) | Active (`contracts/test/SecureHook.sol`) |
| Static Vulnerability Interchange | SARIF 2.1.0 | Active (`secret_audit.sarif`) |

---

## Integrity Verification Protocol

To verify ledger integrity programmatically:

```python
from babylon60.bft.ledger_actor import verify_chain

result = verify_chain(db_path="master_ledger.db")
print(result)  # {"valid": True, "entries": 4821, "broken_at": None}
```

---

## Data & Vault Separation

- Each workspace maintains an isolated `.db` file in sidecar mode.
- Direct multi-threaded synchronous writes to `cortex.db` are strictly prohibited.
- Mutations MUST route through `BFTLedgerActor` using WAL mode and `busy_timeout=5000ms`.

---

## Reporting Vulnerabilities

Security issues should be reported privately following the protocol specified in [SECURITY.md](file:///Users/borjafernandezangulo/30_BABYLON-60/SECURITY.md).
