---
title: BABYLON-60 — Infrastructure and evidence boundaries
status: Technical documentation
version: 5.0.0
---

# BABYLON-60: Infrastructure for Verifiable AI Agent Records

[Sources and declared claims](../CLAIMS.toml) ·
[Formal trace model](../proof/lean/BabylonTrace.lean) ·
[Cryptographic profiles](01_spec/spec_cryptographic_profile.md)

**Technical whitepaper — documentation revision, 30 October 2026**

> Borja Moskv · babylon60.com
>
> This document distinguishes source implementations, formal models, design
> proposals and historical test reports. Its documentation checks do not certify
> a running deployment, hardware isolation or legal conformity.

## Implementation Status

| Mechanism | Source or model | Evidence boundary |
| --- | --- | --- |
| SharedManifest and Seqlock | [manifest.rs](../src/manifest.rs), [seqlock.rs](../src/seqlock.rs) | Layout and protocol implementations; hardware traffic and latency require measurements. |
| Fail-stop admission | [halt.rs](../src/halt.rs) | An explicit rejection path; not proof that every possible violation is detected. |
| Formal trace validation | [BabylonTrace.lean](../proof/lean/BabylonTrace.lean) | Theorems about the model under its hypotheses; not a proof of the entire implementation. |
| Python SQLite ledger | [cortex_persist_ledger.py](../01_KISH_ENGINE/babylon60/bft/cortex_persist_ledger.py) | Local chain consistency and row-invariant checks. |
| Evidence exporter | [eu_ai_act.py](../01_KISH_ENGINE/babylon60/compliance_exporter/eu_ai_act.py) | Cryptographic evidence status; other article assessments remain pending. |
| B60 interpreter and compiler | [src/babylon60.rs](../src/babylon60.rs), [b60-lang](../crates/b60-lang/) | Distinct implementations; supported examples and limits are identified in the [tutorial](03_guides/tutorial_hello_causal.md). |
| Distributed multi-writer consensus | Architecture proposal | Local verification quorum and a single-writer ledger do not demonstrate network BFT. |

Current results require a command, revision, environment and retained output.
[CLAIMS.toml](../CLAIMS.toml) records declared claims and evidence commands; a
listed claim is not a newly executed test result.

## Abstract

BABYLON-60 combines a Rust state and authorization substrate, formal trace models,
Python hash-chained records and evidence export. These mechanisms support specific
checks on recorded state and admitted operations. Their guarantees depend on the
entry point, trust boundary, key custody, observation path and deployment. Hash
integrity does not establish semantic truth, completeness of an execution history
or universal control over an agent's effects.

## 1. Introduction

### 1.1 The Problem: Similarity Is Not Lineage

Similarity retrieval alone does not specify event order, derivation or integrity.
Those properties require explicit records and validation rules. A hash chain
provides a consistency relation over recorded bytes; independent observation and
trusted commitments are needed to connect those records to real effects.

### 1.2 Context and Execution Limits

The project uses terms such as context rot and reasoning loops to describe agent
failure modes. They are operational concerns, not measurements of thermodynamic
energy. Comparisons with other frameworks require a common workload and benchmark;
Landauer's bound does not establish that a software framework is unusable.

### 1.3 Architecture and Trust Boundaries

The repository labels kernel, engine and swarm responsibilities as rings. These
labels do not establish OS privilege levels or hardware virtualization. Rust,
Python and Lean operate in the permissions and isolation supplied by the host.
The [security model](01_spec/spec_security_model.md) states which actors and
properties each record mechanism covers.

### 1.4 Contributions

The source provides concrete mechanisms for state publication, authorization,
record hashing and model validation. Evaluation must address each mechanism
separately. Compilation, a valid hash and a successful model check are distinct
observations; none substitutes for an independently observed protected effect.

## 2. SharedManifest and Seqlock

### 2.1 Physical Layout

[src/manifest.rs](../src/manifest.rs) defines a 64-byte, 64-byte-aligned
`SharedManifest` with `status_flag`, `seq`, `epoch_id`, four atomic payload words
and padding. The hash field stores bytes selected by its producer; it does not
choose a cryptographic profile by itself. Layout alone does not establish a
cache-line size on every processor, absence of false sharing or access latency.

### 2.2 Protocol States

The Seqlock uses sequence parity to distinguish a publication in progress from
an even-sequence snapshot. Readers must apply the implemented ordering and retry
rules. A spinning reader consumes resources. Claims about RFO traffic, contention,
latency or power require measurements on the target hardware and workload.

The formula `k_B T ln(2)` bounds idealized logically irreversible bit erasure.
A source constant derived from it is not a measurement of CPU energy per
publication or proof that only the writer dissipates energy.

### 2.3 Formal Verification in Lean 4

[BabylonTrace.lean](../proof/lean/BabylonTrace.lean) contains
`no_torn_reads_universal`:

```lean
-- Signature of the theorem defined and proved in the linked source.
-- The hypothesis concerns acceptance by the model's trace validator.
-- validateTrace trace = true → TraceReadsEven trace
```

The theorem concerns the definitions and hypotheses of that model. Establishing
correspondence with a Rust implementation also requires checking event capture,
emission, memory ordering and assumptions. This documentation revision did not
run Lean and does not publish a fresh compiler-success claim.

### 2.4 Fail-Stop Admission

[src/halt.rs](../src/halt.rs) implements halt paths selected by features and
signer availability. Receipt states distinguish signed evidence, unsigned evidence
and persistence failure. A missing error string does not attest that all
invariants held; error handling and the observed effect must be checked directly.

## 3. F60 and Exact Arithmetic

The project explores rational and sexagesimal representations for exact values.
Exactness is bounded by the chosen representation, supported operations and
overflow rules. An illustrative type or formula does not establish that all
interpreter paths reject approximation or that every fraction is representable.
The [tutorial](03_guides/tutorial_hello_causal.md) specifies the executable and
example supported by the current checkout. Interpreter output is not a Lean proof.

## 4. Tamper-Evident Hash-Chained Ledger

### 4.1 Architecture

[CortexPersistLedger](../01_KISH_ENGINE/babylon60/bft/cortex_persist_ledger.py)
implements a local SQLite/WAL record chain. Its BFT Python profile computes
**SHA3-256 over canonical JSON**, not SHA-256 over CBOR. The hash body includes
sequence, identifiers, payload JSON, attribution, Lamport clock, previous hash and
`timestamp`; the inner payload remains a JSON string in the outer envelope.

### 4.2 Integrity Properties

| Check | Mechanism | Scope |
| --- | --- | --- |
| Chain consistency | Recompute SHA3-256 entries and check row invariants | Detect mismatch against the chain being read. |
| Root attestation | Verify a signature against an identified trusted key | Authenticate the signed statement, subject to key custody and identity binding. |
| Completeness and provenance | Independent observation and retained trusted roots | Not established by recomputing an internally consistent database. |
| Durability | SQLite connection policy and storage behavior | Not physical WORM protection against an administrator replacing the database. |

The [cryptographic profile](01_spec/spec_cryptographic_profile.md) specifies the
Python encoding and Merkle construction, a reproducible vector and distinct
Rust SHA-256 and BLAKE3 profiles. These profiles are not interchangeable.
`verify_integrity()` validates chain consistency; it does not prove that every
execution was recorded, that a signature is trusted or that an action was legal.

### 4.3 Temporal Domain Separation

Logical ordering and physical time serve different purposes. In this Python
profile `timestamp` is included in the digest. Its behavior must not be inferred
from a separate Rust format or from a proposed logical-clock-only protocol.

### 4.4 Scalability Architecture

Distributed consensus is a separate protocol requirement. Local heterogeneous
verification, single-writer serialization and network BFT require different
failure models and evidence. No zero-downtime migration guarantee is established
by this document.

## 5. Validation and Rejection

The repository contains runtime checks and source-quality tests. Static checks
for a prohibited pattern do not prove that the deployed process mediates every
effect or detects every failure. A rejection result must be checked together with
independent evidence that the protected effect did not occur.

For a new evaluation, run the relevant commands with the lockfiles and retain
actual output. Historical counts are not expected output for a later revision:

```sh
uv run --locked pytest tests/test_c5_invariants.py -q
cargo test --workspace --locked
```

These commands are test instructions, not results of this documentation change.
They are unnecessary for a documentation-only check unless runtime behavior is
also being evaluated.

## 6. Proof IR and Lean 4 Backend

### 6.1 Formal Models

The actual theorem definitions and dependencies are in
[proof/lean](../proof/lean/). Review their hypotheses and used axioms, and compile
the selected targets before reporting a result. A theorem whose only conclusion
is `True` supplies no evidence about concurrency, authorization or execution.

### 6.2 Trace Pipeline

[crates/b60-lang](../crates/b60-lang/) contains compiler and emission code.
The [kernel audit](security/kernel-audit-2026-10-15.md) describes specific trace,
framing and emitter tests together with their limits. Exporting `proof.ir` from
an interpreter does not itself invoke a proof checker.

### 6.3 Correspondence Obligation

A one-to-one correspondence between an observed execution and an exported trace
requires a validated observation and translation path. Successful termination,
ledger verification and compilation of a model are insufficient by themselves.
The relationship must be established for the identified program and semantics.

## 7. Routing and Resource Budgets

A bounded agent execution needs explicit limits for steps, time, memory and
external effects. Proposed exergy-routing terminology is a design description;
without a measurement protocol it does not provide energy units or a physical
budget. Each opcode and scheduler guarantee must be evaluated in its selected
interpreter or compiler, rather than inferred from an ISA table.

## 8. Compliance and Regulatory Alignment

### 8.1 EU AI Act

The documentation follows the published timetable: obligations for high-risk
systems in Annex III apply from **2 December 2027**, and Article 50 transparency
rules apply from 2 August 2026. Consult the
[European Commission](https://digital-strategy.ec.europa.eu/en/policies/regulatory-framework-ai)
and the [compliance guide](05_compliance_eu_ai_act.md) for sources and scope.

The exporter records cryptographic evidence status. Even with a verified ledger,
its assessments of Articles 9, 10, 11, 14 and 15 remain
`EVIDENCE_SECURED_PENDING_AUDIT`. An integrity check contributes evidence for
record-keeping; it does not certify complete compliance with Article 12 or the
Regulation. Purpose, risk classification, organizational measures and applicable
assessment procedures remain external obligations.

### 8.2 Sector-Specific Assessment

A hash-chain verifier does not establish explainability, suitability for trading,
clinical validation or sector-specific legal conformity. Those claims require
a separate assessment of the actual system and intended use.

### 8.3 Biometric Attestation

The [declared hardware claim](../CLAIMS.toml) distinguishes software P-256
verification from an interactive Secure Enclave and Touch ID invocation. A
software test or shadow-mode sidecar is not evidence of biometric authorization
or complete mediation of every possible agent effect.

## 9. Historical Results

The earlier v4.3 note reported 84 Rust tests, 19 Python passes, one skip, one
expected failure and a Lean build without diagnostics. Those numbers are
historical assertions and are **NO_VERIFICADO** for this documentation revision.
Use a revision-bound report and retained output for an acceptance decision. The
[kernel audit](security/kernel-audit-2026-10-15.md) provides a more specific example
of commands, observations and stated limitations; its results also belong to its
identified revision.

## 10. Conclusion

BABYLON-60 supplies source implementations and formal models for specific record
and execution checks. Assess each property at its own boundary, with explicit
hypotheses, independent observations and reproducible evidence. This document
provides navigation to those sources; it does not certify a deployment.

## References

- Repository: [github.com/borjamoskv/BABYLON-60](https://github.com/borjamoskv/BABYLON-60)
- Formal source: [BabylonTrace.lean](../proof/lean/BabylonTrace.lean)
- Cryptographic formats and vector: [spec_cryptographic_profile.md](01_spec/spec_cryptographic_profile.md)
- Threat boundaries: [spec_security_model.md](01_spec/spec_security_model.md)
- Declared claims and commands: [CLAIMS.toml](../CLAIMS.toml)
- License: [LICENSE](../LICENSE)
