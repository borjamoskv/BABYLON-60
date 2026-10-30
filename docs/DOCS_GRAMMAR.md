# BABYLON-60 — Documentation Grammar v1.0

<div align="center">

[![C5-REAL Verified](https://img.shields.io/badge/C5--REAL-Verified-00F0FF?style=for-the-badge&logo=shield)](https://github.com/borjamoskv/BABYLON-60)
[![Régimen](https://img.shields.io/badge/Régimen-Causal--Determinist-7B1FA2?style=for-the-badge)](https://github.com/borjamoskv/BABYLON-60)

</div>


> **Operative Rule:** A documentation unit compresses reality if and only if its
> Kolmogorov length is strictly shorter than an exhaustive enumeration of its referent.
>
> $$\text{TermCost}(\sigma) < \Delta K(\text{Territory}) \implies \text{Emit}(\sigma) \quad \text{else} \quad \text{Purge}(\sigma)$$

---

## 1. Canonical Sentence Grammar

Every prose sentence follows exactly one of three forms:

```
Form A (State):    [Entity]     IS       [Invariant]
Form B (Mutation): [Entity]     VERBS    [Object]         [→ State]?
Form C (Contract): [Condition]  IMPLIES  [Outcome]        (typed)
```

**Prohibited:** adverbs of degree (`effectively`, `significantly`, `seamlessly`),
adjectives of quality (`powerful`, `blazing`, `intuitive`, `revolutionary`),
and modal hedges (`can help`, `may enable`, `allows you to`).

**Required:** causal verbs with bounded objects:
`maps`, `writes`, `reads`, `aborts`, `signs`, `routes`, `poisons`, `enclaves`,
`emits`, `transitions`, `invalidates`, `seals`, `compiles`, `deserializes`.

---

## 2. Algebra Admission Gate (Ley B5)

An algebraic expression is admitted only when it satisfies:

```
admitted(σ) ↔ ∃ struct | type | syscall | clock_cycle | byte_offset
              such that σ maps 1:1 to it AND |prose(referent)| > |σ|
```

### Admitted (compresses real territory)

| Symbol | Maps to | Lines saved |
| :--- | :--- | :--- |
| `align(64)` | CPU cache line boundary, zero false-sharing | ∼8 prose lines |
| `RFO = 0` | MESI Shared state, no ownership transfer on reader path | ∼12 prose lines |
| `POISONED = 0xDEAD_6060` | Irreversible apoptosis sentinel value in `SharedManifest.state` | ∼4 prose lines |
| $\text{AX-0}: \text{LLM} \neq \text{Authority}$ | Root axiom: stochastic output cannot authorize `abort()` or disk mutation | ∼20 prose lines |
| $I \notin \Sigma_{\text{safe}} \implies S' = \texttt{POISONED}$ | Fail-stop transition function for illegal inputs | ∼6 prose lines |
| $\Delta t_{\text{reuse}} = 0$ | Touch ID `allowableReuseDuration = 0` in `c5_biometric_gate.swift` | ∼3 prose lines |
| $K_{\text{Landauer}} = k_B T \ln 2 \approx 2.87 \text{ zJ}$ (at 300 K) | Physical dissipation lower bound per bit erasure (Landauer, 1961) | ∼15 prose lines |

### Rejected (cargo-cult / no physical anchor)

| Expression | Rejection reason |
| :--- | :--- |
| `⟨ψ\|φ⟩` on a Python dict | No Hilbert space in scope; BJR-E091 (PHYSICAL without SI dimensions) |
| `entropy(system) ↓` without $H$ definition | BJR-E091 (FORMAL without rigorous definition) |
| `revolutionary O(1) memory` | No benchmark, no `CLAIMS.toml` entry; overclaim (BJR-E013) |

---

## 3. Document Layer Protocol

Every document in `docs/` maps to exactly one layer. Mixing layers in a single file requires an explicit `[LAYER N]` boundary marker.

```
Layer 0 — Axiomatic Header     (≤ 10 lines)
  Purpose : Root axiom + causal invariants in algebra.
  Audience: LLMs, automated linters, `CLAIMS.toml` verifier.
  Rules   : Zero adjectives. Zero modals. Algebra only.

Layer 1 — Kinetic Ignition     (≤ 20 lines)
  Purpose : Exact command to fire the system.
  Audience: Engineers at a terminal.
  Rules   : Commands verbatim. Prereqs as typed constraints.
            No marketing. No "you can also".

Layer 2 — State Machine Spec   (unbounded, structured)
  Purpose : Formal transition table / invariant list / API contract.
  Audience: Implementors, formal verification tools.
  Rules   : Every claim links to a test in CLAIMS.toml or a
            Lean 4 / Rust proof. BJR-B2: definition ≠ evidence.

Layer 3 — Evidence Manifest    (CLAIMS.toml link)
  Purpose : 1:1 mapping of architectural claims → silicon tests.
  Audience: Auditors, compliance tools.
  Rules   : No free text. Only rows: Claim | Test | Status.
```

---

## 4. Audit Linter Rules (`docs-lint`)

Run the local Markdown checks with `python3 scripts/docs_lint.py docs/`.
The `docs/` argument is optional; the default scans that directory and checks the
root README grammar. Use `--repo-root <path>` when checking an isolated fixture.

Run `make docs-check` for the complete documentary gate: generated indexes,
semantic contracts, workspace token budget and topology. It does not execute
runtime claims, contact LAYA, inspect global configuration or read operator telemetry.
The optional `--system1` probe is separate and is never part of this target.

The linter implements the vocabulary rules DL-001, DL-006 and DL-007, corruption
checks DL-008/DL-009, local destinations (including nested image badges and
reference links), GFM heading anchors and index coverage. External URL availability,
physical claims and mathematical truth require separate review. DL-002 through
DL-005 below are review criteria unless an executable check is explicitly named.

| Rule ID | Trigger | Action |
| :--- | :--- | :--- |
| `DL-001` | Adjective detected in Layer 0 or Layer 1 | `ERROR` — purge |
| `DL-002` | Algebraic symbol with no `CLAIMS.toml` entry or SI unit | `ERROR` — BJR-E091 |
| `DL-003` | Sentence lacking subject + causal verb + object | `WARNING` |
| `DL-004` | Claim without `[VERIFIED]` or `[ROADMAP]` tag | `ERROR` — BJR-E013 |
| `DL-005` | Synonym introduced without formal definition | `WARNING` — BJR-B5 |
| `DL-006` | Modal verb (`may`, `can`, `allows`) in specification context | `ERROR` |
| `DL-007` | Metaphor used as evidence (e.g., "thermodynamic" without $J/K$) | `ERROR` — BJR-E034 |

---

## 5. Synonym Registry (Admitted Compression Terms)

A synonym is admitted only when it designates the same invariant across multiple
representational domains with no ambiguity.

| Canonical Term | Domain: Hardware | Domain: Concurrency | Domain: Formal |
| :--- | :--- | :--- | :--- |
| `SharedManifest` | 64-byte L1 cache line | Seqlock SPMC bus | `struct SharedManifest { state: AtomicU64, ... }` |
| `Apoptosis` | `abort()` syscall | Irreversible state `→ POISONED` | $S \xrightarrow{I \notin \Sigma} \texttt{POISONED}$ |
| `Causal Gate` | Touch ID Secure Enclave | `allowableReuseDuration = 0` | Biometric predicate $\mathcal{B}$ gating mutation $\mu$ |
| `Ring-0 / Ring-1 / Ring-2` | OS privilege level (conceptual) | Trust boundary between kernel / engine / swarms | $\text{Ring}_i \subset \text{Ring}_{i+1}$ (containment lattice) |
| `Fail-Stop` | Hardware watchdog | `abort()` on invariant breach | $\neg \text{Safe}(S) \implies \text{Halt}$ |

---

## 6. Refactoring Checklist

Before merging any `docs/` change, confirm:

- [ ] Every sentence in Layer 0–1 passes `DL-001`, `DL-004`, `DL-006`.
- [ ] Every algebraic symbol has a row in §2 Admitted table or `CLAIMS.toml`.
- [ ] Every synonym maps to ≥ 2 representational domains in §5.
- [ ] No free-form changelog prose; use `CHANGELOG.md` (Layer 3 only).
- [ ] `python3 scripts/c5_quality_gates/sync_docs_index.py --check` matches the saved documents; omit `--check` to regenerate stale indexes.
- [ ] `make docs-check` exits 0 and its recorded output identifies the checkout checked.
- [ ] Changes to a technical claim identify the relevant evidence suite and its latest result. `python3 scripts/verify_claims.py` only lists declarations; its exit code does not verify any claim. Explicit `--execute`/`--strict` runs evidence commands and belongs to the affected runtime/release verification, not every documentation edit.

---

*Grammar version pinned to: `BABYLON-60 v5.0.0` · `docs/DOCS_GRAMMAR.md`*
