# THREAT_MODEL.md — Frozen Systemic & Experimental Threat Model

> **STATUS: FROZEN / NORMATIVE**  
> **Repository**: `borjamoskv/teorema-robinson-moskv`  

This document formalizes the threat model, failure modes, attack vectors, and mitigation matrices for both the executable runtime system and the empirical evaluation protocol.

---

## 1. Catalog of Systemic & Experimental Threats

```yaml
threats:
  - runtime_lies
  - trace_tampering
  - trace_reordering
  - state_hash_collision
  - parser_bug
  - semantic_gap
  - cost_mismatch
  - benchmark_leakage
  - prompt_leakage
  - adaptive_stopping
  - multiple_testing
  - selection_bias
  - ceiling_effect
  - implementation_bug
```

---

## 2. Threat Mitigation Matrix

| Threat ID | Threat Name | Mitigation Mechanism | Verified By | Remaining Assumption |
|---|---|---|---|---|
| **T-01** | `runtime_lies` | Authority prohibition: Runtime cannot declare `certified: true` or `is_valid: true`. Verification is performed externally. | `TRACE_CONTRACT_v1.0.0.json` validation engine | Independent evaluator code is bug-free. |
| **T-02** | `trace_tampering` | Immutable append-only log signed with SHA-256 and stored in canonical RFC8785 JSON format. | Merkle tree log audit | Cryptographic hash pre-image resistance (SHA-256). |
| **T-03** | `trace_reordering` | Monotonic sequence counters and parent step hash chaining inside state descriptors. | Cryptographic trace verifier | Timestamp or sequence clock monotonicity. |
| **T-04** | `state_hash_collision` | 256-bit hash collisions prevented by SHA-256 over canonicalized state representations. | AST serialization tests | Collision resistance of SHA-256. |
| **T-05** | `parser_bug` | Formal specification of trace grammar validated via independent JSON Schema validators. | Schema validation test suite | JSON Schema validator engine compliance. |
| **T-06** | `semantic_gap` | Explicit refinement proof obligations bridging Lean 4 transition functions to executable code. | Lean 4 refinement specs | Refinement bridge assumptions hold. |
| **T-07** | `cost_mismatch` | Monotonic step and token counters instrumented at API boundary rather than model self-reporting. | Independent API proxy log auditor | Proxy log recording accuracy. |
| **T-08** | `benchmark_leakage` | Pre-registered dataset cryptographic hash locking (`dataset_hash`) prior to run execution. | Preregistration lock verifier | Benchmark problems do not appear in base LLM training set. |
| **T-09** | `prompt_leakage` | Prompt hashes pre-registered and held constant across all treatment arms ($D, C, B, F$). | `BENCHMARK_PROTOCOL_v1.0.0.md` audit | Fixed prompt string equality. |
| **T-10** | `adaptive_stopping` | Strict prohibition of early stopping rules based on intermediate $p$-value monitoring. | Fixed sample size protocol enforcer | Run execution engine runs to full completion $N$. |
| **T-11** | `multiple_testing` | Single primary comparison ($D$ vs $C$) pre-registered at $\alpha = 0.05$. Secondary tests labeled exploratory. | Statistical analysis pipeline | Investigator adheres to primary test precedence. |
| **T-12** | `selection_bias` | Deterministic ChaCha20 PRNG sample allocation pre-seeded before benchmark launch. | `RANDOMIZATION_PROTOCOL.md` audit | Deterministic seed generator compliance. |
| **T-13** | `ceiling_effect` | Task difficulty calibration ensuring control coverage $\text{Coverage}(C) \in [0.20, 0.80]$. | Pilot dataset calibration | Task difficulty distribution remains constant. |
| **T-14** | `implementation_bug` | Multi-language cross-verification (Lean 4, Rust, Python) with independent unit tests. | CI/CD automated test runner | Test coverage sufficiency across boundaries. |

---

## 3. Threat Model Epistemic Conclusion

> By explicitly cataloging failure modes and mapping each to a mitigation mechanism and residual assumption, the project shifts from claiming ungrounded absolute certainty to maintaining an **explicit, verifiable model of potential error**.
