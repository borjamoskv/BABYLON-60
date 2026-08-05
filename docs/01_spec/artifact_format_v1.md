# BABYLON-60 Artifact Format v1

## 1. Introduction
This is the normative specification for the BABYLON-60 Artifact Bundle. Any conforming implementation of the Phase 0 (Runtime Bootstrap) must emit this exact canonical structure. The purpose of this format is to guarantee that identical logical states produce identical hashes, enabling reproducible verification via Lean and Coq.

## 2. Artifact Bundle Layout

The Artifact Bundle MUST be a directory (or compressed archive) structured exactly as follows:

```text
Artifact Bundle
├── manifest.json
├── graph.canonical
├── trace.bin
├── proof.ir
├── metadata.json
├── hashes/
│   ├── graph.sha256
│   ├── trace.sha256
│   └── bundle.sha256
└── signature
```

### 2.1. manifest.json
A JSON object indicating the version and structural hashes. It must contain the following keys exactly:
- `"version"`: MUST be `"1.0"`.
- `"components"`: Array of paths included in the bundle.
- `"global_hash"`: The overall hash of the bundle, calculated as the SHA-256 of the concatenated contents of `hashes/bundle.sha256`.

### 2.2. Canonical Serialization (`graph.canonical`)
The Ledger DAG MUST be serialized canonically before hashing. The rules for canonical serialization are:
1. **Topological Sort**: All events in the Ledger MUST be sorted topologically.
2. **Tie-Breaking**: If two events $E_a$ and $E_b$ have no causal dependency between them, they MUST be sorted lexicographically by their string-encoded event IDs.
3. **Format**: The `graph.canonical` file contains one event per line. Each line MUST strictly follow this format (UTF-8 encoded):
   `{event_id}|{parent1,parent2,...}|{logical_tick}|{payload}|{signature}`
   Parents MUST be sorted lexicographically.

### 2.3. Proof IR (`proof.ir`)
This file contains the Intermediate Representation of the execution trace and invariants, stripped of any Lean or Coq-specific syntax. The backend translators will parse this IR to generate native proofs.

### 2.4. Hashes
All hashes MUST be SHA-256 encoded in lowercase hexadecimal format.
- `graph.sha256`: Hash of `graph.canonical`.
- `trace.sha256`: Hash of `trace.bin`.
- `bundle.sha256`: A manifest of the hashes of all components.

## 3. Conformity
An implementation is only considered conformant if the `graph.sha256` produced for a given script matches the reference interpreter bit-for-bit.
